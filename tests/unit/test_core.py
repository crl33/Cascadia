"""Core: time parsing with offsets, available_at, freshness arithmetic, object store keys, fetcher rules."""

from datetime import UTC, datetime, timedelta

import httpx
import pytest
import respx

from cascade_contracts import FreshnessState
from cascade_core.fetch import ArchivingFetcher, FetchError
from cascade_core.freshness import compute_freshness
from cascade_core.objectstore import LocalFilesystemStore, object_key_for
from cascade_core.timeutils import available_at, iso_z, parse_iso
from cascade_core.units import convert, normalize_unit

NOW = datetime(2026, 8, 22, 13, 30, tzinfo=UTC)


def test_parse_iso_keeps_offset_semantics() -> None:
    pdt = parse_iso("2026-08-22T01:15:00.000-07:00")
    assert pdt == datetime(2026, 8, 22, 8, 15, tzinfo=UTC)
    assert parse_iso("2026-08-22T08:15:00Z") == pdt
    with pytest.raises(ValueError):
        parse_iso("2026-08-22T08:15:00")  # naive timestamps are defects


def test_available_at_is_max_of_anchor_and_retrieval() -> None:
    v, r = NOW - timedelta(hours=1), NOW
    assert available_at(valid_time=v, retrieved_at=r) == r
    assert available_at(valid_time=v, retrieved_at=r, issued_at=NOW + timedelta(hours=1)) == NOW + timedelta(hours=1)
    assert iso_z(NOW) == "2026-08-22T13:30:00Z"


def test_freshness_states_from_cadence_and_grace() -> None:
    kw = dict(expected_cadence_seconds=900, grace_seconds=4500)
    assert compute_freshness(**kw, valid_time=NOW - timedelta(minutes=45), retrieved_at=NOW - timedelta(minutes=5), now=NOW).state == FreshnessState.CURRENT
    assert compute_freshness(**kw, valid_time=NOW - timedelta(minutes=91), retrieved_at=NOW - timedelta(minutes=5), now=NOW).state == FreshnessState.STALE
    assert compute_freshness(**kw, valid_time=NOW - timedelta(minutes=30), retrieved_at=NOW - timedelta(hours=2), now=NOW).state == FreshnessState.DEGRADED
    assert compute_freshness(**kw, valid_time=None, retrieved_at=None, now=NOW).state == FreshnessState.MISSING
    f = compute_freshness(expected_cadence_seconds=86400, grace_seconds=64800, valid_time=NOW - timedelta(seconds=64500), retrieved_at=NOW - timedelta(hours=5), now=NOW)
    assert f.state == FreshnessState.CURRENT and f.age_seconds == 64500


def test_units_explicit_conversion() -> None:
    assert normalize_unit("ft3/s") == "cfs"
    assert convert(6.67, "kcfs", "cfs") == pytest.approx(6670.0)
    assert convert(10.5, "ft", "ft") == 10.5


def test_object_store_is_content_addressed(tmp_path) -> None:
    store = LocalFilesystemStore(tmp_path)
    key = store.put(b'{"a":1}')
    assert key == object_key_for(b'{"a":1}') and store.exists(key)
    assert store.put(b'{"a":1}') == key and store.get(key) == b'{"a":1}'


@respx.mock
async def test_fetcher_refuses_disallowed_redirect_host(tmp_path) -> None:
    respx.get("https://waterservices.usgs.gov/nwis/iv/").mock(return_value=httpx.Response(301, headers={"location": "https://evil.example/x"}))
    fetcher = ArchivingFetcher(store=LocalFilesystemStore(tmp_path), user_agent="t", clock=lambda: NOW)

    class Fake:
        def add(self, *_):
            pass

        async def flush(self):
            pass

    with pytest.raises(FetchError, match="disallowed_host"):
        await fetcher.fetch(Fake(), url="https://waterservices.usgs.gov/nwis/iv/", params=None, allowed_hosts=frozenset({"waterservices.usgs.gov"}), product_id="product:usgs-iv")
