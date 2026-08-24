"""USGS OGC `continuous` fixtures (Event Zero backfill): real captured day page, real cursor
pagination pair, derived missing-field/edge cases, backfilled doctrine on every record."""

from datetime import UTC, datetime

import pytest

from cascade_core.objectstore import LocalFilesystemStore
from cascade_providers_usgs.ogc_client import BACKFILL_MAX_BYTES, build_backfill_fetcher, close_fetcher
from cascade_providers_usgs.ogc_normalize import to_observation_records
from cascade_providers_usgs.ogc_parser import parse_continuous
from cascade_providers_usgs.parser import ParseError

NOW = datetime(2026, 8, 24, 13, 0, tzinfo=UTC)  # shortly after the fixtures were captured
CREST_T = datetime(2025, 12, 12, 8, 15, tzinfo=UTC)


def test_real_day_page(fixtures) -> None:
    page = parse_continuous((fixtures / "usgs_ogc/day_12200500.json").read_bytes())
    assert page.next_url is None and page.number_returned == 194 and len(page.values) == 194
    stage = [v for v in page.values if v.variable == "stage"]
    flow = [v for v in page.values if v.variable == "flow"]
    assert len(stage) == 97 and len(flow) == 97
    assert {v.unit for v in stage} == {"ft"} and {v.unit for v in flow} == {"cfs"}
    assert {v.approval_status for v in page.values} == {"Approved"}
    assert {v.statistic_id for v in page.values} == {"00011"}
    assert {v.site for v in page.values} == {"12200500"}
    assert all(v.time.tzinfo is not None for v in page.values)
    # EVENT_ZERO.md §3 golden peaks are inside the captured payload
    peak = max(stage, key=lambda v: float(v.raw_value))
    assert float(peak.raw_value) == 37.73 and peak.time == CREST_T
    flow_max = max(float(v.raw_value) for v in flow)
    assert flow_max == 133000.0
    # the payload holds a 133,000 cfs plateau; §3's crest time 09:00Z is inside it
    assert datetime(2025, 12, 12, 9, 0, tzinfo=UTC) in {v.time for v in flow if float(v.raw_value) == flow_max}


def test_real_pagination_links(fixtures) -> None:
    p1 = parse_continuous((fixtures / "usgs_ogc/paged_12200500_p1.json").read_bytes())
    assert p1.number_returned == 120 and len(p1.values) == 120
    assert p1.next_url is not None and p1.next_url.startswith("https://api.waterdata.usgs.gov/") and "cursor=" in p1.next_url
    p2 = parse_continuous((fixtures / "usgs_ogc/paged_12200500_p2.json").read_bytes())
    assert p2.next_url is None and p2.number_returned == 74
    keys = {(v.variable, v.time) for v in p1.values} | {(v.variable, v.time) for v in p2.values}
    assert len(keys) == 194  # the cursor pages tile the day exactly: no overlap, no gap


def test_missing_field_and_malformed(fixtures) -> None:
    with pytest.raises(ParseError, match="unit_of_measure"):
        parse_continuous((fixtures / "usgs_ogc/derived_missing_field.json").read_bytes())
    with pytest.raises(ParseError, match="not JSON"):
        parse_continuous(b"{nope")


def test_normalize_backfilled_doctrine(fixtures) -> None:
    page = parse_continuous((fixtures / "usgs_ogc/day_12200500.json").read_bytes())
    records, skipped = to_observation_records(page.values, retrieved_at=NOW, station_id="station:usgs:12200500", datum="NGVD29")
    assert len(records) == 194 and skipped == {"non_instantaneous": 0}
    # ADR-0010: available_at = retrieval time, NEVER the historical valid time
    assert all(r.available_at == NOW and r.retrieved_at == NOW for r in records)
    assert all("backfilled" in r.quality for r in records)
    assert all(r.qualifier_raw == "Approved" and "approved" in r.quality for r in records)
    stage = [r for r in records if r.variable == "stage"]
    assert all(r.datum == "NGVD29" for r in stage)
    assert all(r.datum is None for r in records if r.variable == "flow")
    peak = max(stage, key=lambda r: r.value)
    assert peak.value == 37.73 and peak.valid_time == CREST_T


def test_edge_cases(fixtures) -> None:
    page = parse_continuous((fixtures / "usgs_ogc/derived_edge_cases.json").read_bytes())
    assert len(page.values) == 7
    records, skipped = to_observation_records(page.values, retrieved_at=NOW, station_id="s", datum="NGVD29")
    assert skipped == {"non_instantaneous": 1} and len(records) == 6  # statistic 00003 never stored
    by_minute = {r.valid_time.minute + 60 * (r.valid_time.hour): r for r in records}
    unparseable = by_minute[0]
    assert unparseable.value is None and "unparseable" in unparseable.quality and "backfilled" in unparseable.quality
    negative = by_minute[15]
    assert negative.value == -9.0 and "out_of_range" in negative.quality and negative.variable == "flow"
    provisional = by_minute[30]
    assert {"provisional", "ice", "backfilled"} <= set(provisional.quality)
    assert provisional.qualifier_raw == "Provisional,Ice"
    null_value = by_minute[45]
    assert null_value.value is None and "unparseable" in null_value.quality
    plain = by_minute[75]
    assert plain.value == 12.34 and "approved" in plain.quality and plain.datum == "NGVD29"
    estimated = by_minute[90]  # the caps spelling the OGC API serves, mapped onto the vocabulary
    assert {"provisional", "estimated", "backfilled"} <= set(estimated.quality)
    assert estimated.qualifier_raw == "Provisional,ESTIMATED"


async def test_backfill_fetcher_keyed_and_anonymous(tmp_path) -> None:
    keyed = build_backfill_fetcher(LocalFilesystemStore(tmp_path), user_agent="test-ua", api_key="not-a-real-key")
    try:
        assert keyed.max_bytes == BACKFILL_MAX_BYTES == 16_000_000
        assert keyed._client.headers["X-Api-Key"] == "not-a-real-key"
        assert keyed._client.headers["User-Agent"] == "test-ua"
    finally:
        await close_fetcher(keyed)
    anonymous = build_backfill_fetcher(LocalFilesystemStore(tmp_path), user_agent="test-ua", api_key=None)
    try:
        assert "X-Api-Key" not in anonymous._client.headers  # degrade politely, never send an empty key
    finally:
        await close_fetcher(anonymous)
