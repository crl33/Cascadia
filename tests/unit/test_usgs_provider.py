"""USGS fixture tests: valid, missing field, malformed, timeout, 5xx, sentinel, schema evolution, DST ordering."""

from datetime import UTC, datetime

import httpx
import pytest
import respx

from cascade_core.fetch import ArchivingFetcher, FetchError
from cascade_core.objectstore import LocalFilesystemStore
from cascade_providers_usgs.client import ALLOWED_HOSTS, BASE_URL, fetch_iv
from cascade_providers_usgs.normalize import to_observations
from cascade_providers_usgs.parser import ParseError, parse_iv

NOW = datetime(2026, 8, 22, 13, 30, tzinfo=UTC)


def test_valid_all_six_sites(fixtures) -> None:
    series = parse_iv((fixtures / "usgs/valid.json").read_bytes())
    assert {s.site for s in series} == {"12119000", "12149000", "12200500", "12213100", "12113000", "12100490"}
    assert {s.variable for s in series} == {"stage", "flow"}
    assert {s.unit for s in series} == {"ft", "cfs"}
    sk = next(s for s in series if s.site == "12200500" and s.variable == "stage")
    assert sk.no_data_value == -999999.0 and sk.values[-1].qualifiers == ("P",)
    obs = to_observations(sk, retrieved_at=NOW, station_id="station:usgs:12200500", datum="NGVD29")
    last = obs[-1]
    assert last.value is not None and last.unit == "ft" and last.datum == "NGVD29" and "provisional" in last.quality
    assert last.available_at == NOW and last.valid_time.tzinfo is not None
    flow = next(s for s in series if s.site == "12200500" and s.variable == "flow")
    assert to_observations(flow, retrieved_at=NOW, station_id="x", datum="NGVD29")[-1].datum is None


def test_missing_field_and_malformed(fixtures) -> None:
    with pytest.raises(ParseError, match="unit"):
        parse_iv((fixtures / "usgs/missing_field.json").read_bytes())
    with pytest.raises(ParseError, match="not JSON"):
        parse_iv((fixtures / "usgs/malformed.json").read_bytes())


def test_sentinel_and_qualifiers(fixtures) -> None:
    series = parse_iv((fixtures / "usgs/sentinel.json").read_bytes())
    obs = to_observations(series[0], retrieved_at=NOW, station_id="s", datum="NGVD29")
    assert obs[1].value is None and "sentinel" in obs[1].quality
    assert obs[2].value is None and "unparseable" in obs[2].quality
    assert obs[3].value is not None and {"provisional", "ice"} <= set(obs[3].quality) and obs[3].qualifier_raw == "P,Ice"


def test_empty_and_schema_evolution(fixtures) -> None:
    assert parse_iv((fixtures / "usgs/empty_timeseries.json").read_bytes()) == []
    series = parse_iv((fixtures / "usgs/schema_evolution.json").read_bytes())
    assert len(series) == 2 and all(len(s.values) == 6 for s in series)


def test_dst_offsets_order_by_instant_not_string(fixtures) -> None:
    s = parse_iv((fixtures / "usgs/dst_offsets.json").read_bytes())[0]
    assert [v.raw_value for v in s.values] == ["10.20", "10.10", "10.00", "10.05"]
    assert s.values[0].time == datetime(2026, 11, 1, 8, 30, tzinfo=UTC)
    assert s.values[-1].time == datetime(2026, 11, 1, 9, 15, tzinfo=UTC)


class _Session:
    def __init__(self) -> None:
        self.added = []

    def add(self, obj) -> None:
        self.added.append(obj)
        obj.id = len(self.added)

    async def flush(self) -> None:
        pass


def _fetcher(tmp_path) -> ArchivingFetcher:
    return ArchivingFetcher(store=LocalFilesystemStore(tmp_path), user_agent="test", clock=lambda: NOW)


@respx.mock
async def test_timeout_is_a_fetch_error(tmp_path) -> None:
    respx.get(BASE_URL).mock(side_effect=httpx.ReadTimeout("slow"))
    with pytest.raises(FetchError, match="timeout"):
        await fetch_iv(_fetcher(tmp_path), _Session(), sites=["12200500"], hours=2)


@respx.mock
async def test_5xx_outage_is_a_fetch_error_and_nothing_archived(tmp_path) -> None:
    respx.get(BASE_URL).mock(return_value=httpx.Response(503, text="outage"))
    with pytest.raises(FetchError, match="http_status"):
        await fetch_iv(_fetcher(tmp_path), _Session(), sites=["12200500"], hours=2)
    assert not any(tmp_path.rglob("*.json"))


@respx.mock
async def test_redirect_to_allowlisted_host_is_followed_and_archived(tmp_path, fixtures) -> None:
    body = (fixtures / "usgs/valid.json").read_bytes()
    respx.get(BASE_URL).mock(return_value=httpx.Response(301, headers={"location": "https://nwis.waterservices.usgs.gov/nwis/iv/?format=json"}))
    respx.get("https://nwis.waterservices.usgs.gov/nwis/iv/").mock(return_value=httpx.Response(200, content=body, headers={"content-type": "application/json"}))
    session = _Session()
    result = await fetch_iv(_fetcher(tmp_path), session, sites=["12200500"], hours=2)
    assert "nwis.waterservices.usgs.gov" in result.url and "nwis.waterservices.usgs.gov" in ALLOWED_HOSTS
    assert (tmp_path / result.object_key).read_bytes() == body and session.added[0].sha256 == result.sha256
