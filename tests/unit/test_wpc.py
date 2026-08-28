"""WPC official QPF: three real 24-h windows per cycle, aggregated on the shared LCC machinery.

Assertions run against the real captured cycle (2026-08-28 00Z, three files). Load-bearing
measured facts pinned here:

- the cycle publishes BEFORE its nominal hour (22:48Z the previous evening), so
  ``available_at`` is legitimately EARLIER than ``issued_at`` — a knowledge-time inversion
  that is the provider's real behaviour, not a bug;
- the seed-basin masks on the 5-km LCC grid aggregate with ZERO missing cells (the 9999
  sentinel is the off-CONUS corner geography);
- grid_jpeg packing leaves tiny negative values around zero (measured −0.0099 mm), which clamp
  to 0.0 rather than reducing coverage.
"""

from __future__ import annotations

import gzip
from datetime import UTC, datetime

import httpx
import pytest
import respx
from sqlalchemy import select

from cascade_core.db import create_schema, make_engine, make_session_factory
from cascade_core.fetch import ArchivingFetcher, FetchError, HostRateLimiter
from cascade_core.models import DerivedFeature, GridMask
from cascade_core.objectstore import LocalFilesystemStore
from cascade_core.seed import seed_all
from cascade_core.settings import SEED_FILE
from cascade_providers_wpc import jobs as wpc_jobs
from cascade_providers_wpc.client import BASE_URL, cycle_candidates, qpf_filename
from cascade_providers_wpc.parser import WpcParseError, parse_wpc_qpf
from tests.conftest import FIXTURES, GEO

WPC = FIXTURES / "wpc"
CYCLE = datetime(2026, 8, 28, 0, 0, tzinfo=UTC)
FILES = {
    24: gzip.decompress((WPC / "p24m_2026082800f024.grb.gz").read_bytes()),
    48: gzip.decompress((WPC / "p24m_2026082800f048.grb.gz").read_bytes()),
    72: gzip.decompress((WPC / "p24m_2026082800f072.grb.gz").read_bytes()),
}
#: The origin's real Last-Modified for this cycle — before the nominal 00Z hour.
PUBLISHED = "Thu, 27 Aug 2026 22:48:00 GMT"
NOW = datetime(2026, 8, 28, 23, 10, tzinfo=UTC)

BASINS = {
    "basin:cedar", "basin:green-duwamish", "basin:nooksack",
    "basin:puyallup-white", "basin:skagit", "basin:snohomish-snoqualmie",
}


# --- parser -------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def day1():
    return parse_wpc_qpf(FILES[24])


def test_the_real_grid_decodes_with_a_stable_identity(day1) -> None:
    grid = day1.grid
    assert (grid.nx, grid.ny) == (1073, 689)
    assert grid.dx_m == pytest.approx(5078.6, abs=0.1)
    assert grid.latin1 == grid.latin2 == 25.0 and grid.lov == 265.0
    assert day1.reference_time == CYCLE
    assert (day1.step_start_h, day1.step_end_h) == (0, 24)
    assert parse_wpc_qpf(FILES[24]).grid.definition_hash == grid.definition_hash
    # the three windows tile the 72 h with no gap and share one grid identity
    d2, d3 = parse_wpc_qpf(FILES[48]), parse_wpc_qpf(FILES[72])
    assert (d2.step_start_h, d2.step_end_h) == (24, 48)
    assert (d3.step_start_h, d3.step_end_h) == (48, 72)
    assert d2.grid.definition_hash == d3.grid.definition_hash == grid.definition_hash


def test_jpeg_reconstruction_noise_is_present_and_small(day1) -> None:
    """The measured fact the clamp exists for: tiny negatives, never large ones."""
    import numpy as np

    v = np.asarray(day1.values)
    from cascade_providers_wpc.parser import MISSING_FLOOR

    real = v[v < MISSING_FLOOR]
    assert float(real.min()) < 0.0, "the packing really does produce negatives"
    assert float(real.min()) > -0.1, "and they are noise around zero, not damage"


def test_broken_payloads_are_refused() -> None:
    with pytest.raises(WpcParseError, match="not_grib"):
        parse_wpc_qpf(b"not grib at all")
    with pytest.raises(WpcParseError, match="decode_failed|not_grib"):
        parse_wpc_qpf(FILES[24][:4000])
    with pytest.raises(WpcParseError, match="multi_message"):
        parse_wpc_qpf(FILES[24] + FILES[48])


# --- cycle discovery ----------------------------------------------------------------------


def test_candidates_include_the_cycle_published_ahead_of_the_clock() -> None:
    # 23:10Z: the NEXT day's 00Z cycle has been published for ~22 minutes (measured 22:48Z)
    cands = cycle_candidates(datetime(2026, 8, 27, 23, 10, tzinfo=UTC))
    assert cands[0] == CYCLE, "the not-yet-nominal 00Z cycle is the newest candidate"
    assert cands[1] == datetime(2026, 8, 27, 12, 0, tzinfo=UTC)
    # 11:10Z: today's 12Z (published 10:48Z) leads
    cands = cycle_candidates(datetime(2026, 8, 28, 11, 10, tzinfo=UTC))
    assert cands[0] == datetime(2026, 8, 28, 12, 0, tzinfo=UTC)


# --- the job ------------------------------------------------------------------------------


@pytest.fixture
async def sessions(tmp_path):
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path}/wpc.db")
    await create_schema(engine)
    factory = make_session_factory(engine)
    async with factory() as session:
        await seed_all(session, geo_dir=GEO, seed_file=SEED_FILE)
    yield factory
    await engine.dispose()


def _fetcher(tmp_path) -> ArchivingFetcher:
    return ArchivingFetcher(
        store=LocalFilesystemStore(tmp_path), user_agent="test", clock=lambda: NOW,
        limiter=HostRateLimiter(min_interval_s=0.0),
    )


def _mock_cycle(when: datetime = CYCLE) -> None:
    for fhour, content in FILES.items():
        respx.get(BASE_URL + qpf_filename(when, fhour)).mock(
            return_value=httpx.Response(200, content=content, headers={"Last-Modified": PUBLISHED})
        )


@respx.mock
async def test_one_cycle_lands_as_eighteen_qualified_rows(sessions, tmp_path) -> None:
    _mock_cycle()
    # newer candidates than the fixture cycle are not served
    respx.get(url__startswith=BASE_URL).mock(return_value=httpx.Response(404))
    async with sessions() as s:
        written = await wpc_jobs.run_fetch_qpf(s, _fetcher(tmp_path), geo_dir=GEO, now=NOW)
        await s.commit()
        rows = list((await s.execute(select(DerivedFeature).where(
            DerivedFeature.feature == wpc_jobs.FEATURE_QPF))).scalars())
        masks = list((await s.execute(select(GridMask))).scalars())
    assert written == 18 and len(rows) == 18  # 6 basins x 3 windows
    assert {r.scope_id for r in rows} == BASINS
    assert len(masks) == 6, "the 5-km LCC grid earned its own stored masks"
    for r in rows:
        assert r.issued_at.replace(tzinfo=UTC) == CYCLE and r.window == "24h"
    ends = sorted({r.valid_time.replace(tzinfo=UTC) for r in rows})
    assert [(e - CYCLE).total_seconds() / 3600 for e in ends] == [24.0, 48.0, 72.0]


@respx.mock
async def test_the_probed_means_and_the_knowledge_inversion_are_stored(sessions, tmp_path) -> None:
    _mock_cycle()
    respx.get(url__startswith=BASE_URL).mock(return_value=httpx.Response(404))
    async with sessions() as s:
        await wpc_jobs.run_fetch_qpf(s, _fetcher(tmp_path), geo_dir=GEO, now=NOW)
        await s.commit()
        rows = list((await s.execute(select(DerivedFeature).where(
            DerivedFeature.feature == wpc_jobs.FEATURE_QPF,
            DerivedFeature.scope_id == "basin:skagit"))).scalars())
    by_end = {r.valid_time.replace(tzinfo=UTC): r for r in rows}
    d1 = by_end[datetime(2026, 8, 28, 0, tzinfo=UTC).replace(day=29)]
    assert d1.value == pytest.approx(1.22, abs=0.01)  # the independently probed basin mean
    assert d1.unit == "mm" and d1.window == "24h"
    assert d1.issued_at.replace(tzinfo=UTC) == CYCLE
    # published 22:48Z on the 27th — BEFORE the 00Z cycle identity. Real, measured, honest.
    assert d1.available_at.replace(tzinfo=UTC) == datetime(2026, 8, 27, 22, 48, tzinfo=UTC)
    assert d1.available_at.replace(tzinfo=UTC) < d1.issued_at.replace(tzinfo=UTC)
    assert d1.values_json["valid_fraction"] == 1.0, "zero sentinel cells inside the basin"
    assert d1.values_json["window_start_h"] == 0 and d1.values_json["window_end_h"] == 24


@respx.mock
async def test_a_second_run_writes_nothing(sessions, tmp_path) -> None:
    _mock_cycle()
    respx.get(url__startswith=BASE_URL).mock(return_value=httpx.Response(404))
    async with sessions() as s:
        first = await wpc_jobs.run_fetch_qpf(s, _fetcher(tmp_path), geo_dir=GEO, now=NOW)
        await s.commit()
    async with sessions() as s:
        second = await wpc_jobs.run_fetch_qpf(s, _fetcher(tmp_path), geo_dir=GEO, now=NOW)
        await s.commit()
    assert first == 18 and second == 0


@respx.mock
async def test_a_half_published_cycle_is_refused_whole(sessions, tmp_path) -> None:
    """Day 1 up, Day 2 missing: no rows at all — a Day-1-only picture reads as dry Day 2/3."""
    respx.get(BASE_URL + qpf_filename(CYCLE, 24)).mock(
        return_value=httpx.Response(200, content=FILES[24], headers={"Last-Modified": PUBLISHED}))
    respx.get(url__startswith=BASE_URL).mock(return_value=httpx.Response(404))
    async with sessions() as s:
        with pytest.raises(FetchError):
            await wpc_jobs.run_fetch_qpf(s, _fetcher(tmp_path), geo_dir=GEO, now=NOW)
        await s.rollback()
        rows = (await s.execute(select(DerivedFeature).where(
            DerivedFeature.feature == wpc_jobs.FEATURE_QPF))).scalars().all()
        assert rows == []


@respx.mock
async def test_a_stale_file_under_a_fresh_name_is_refused(sessions, tmp_path) -> None:
    """The f024 URL for the NEXT cycle serving the previous cycle's bytes must not be stored
    under the new identity — the reference time inside the message is the authority."""
    wrong_cycle = datetime(2026, 8, 28, 12, 0, tzinfo=UTC)
    for fhour in (24, 48, 72):
        respx.get(BASE_URL + qpf_filename(wrong_cycle, fhour)).mock(
            return_value=httpx.Response(200, content=FILES[fhour], headers={"Last-Modified": PUBLISHED}))
    respx.get(url__startswith=BASE_URL).mock(return_value=httpx.Response(404))
    async with sessions() as s:
        with pytest.raises(ValueError, match="stale name"):
            await wpc_jobs.run_fetch_qpf(
                s, _fetcher(tmp_path), geo_dir=GEO, now=datetime(2026, 8, 28, 11, 10, tzinfo=UTC))
