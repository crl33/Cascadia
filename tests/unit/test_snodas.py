"""SNODAS: modeled SWE per basin from the real 2026-08-27 unmasked file (SWE member only).

Load-bearing measured facts pinned here:

- late August truth: snow ONLY on the glaciers — Puyallup-White (Rainier) ~78 mm land mean
  at ~1 % cover, Nooksack (Baker) ~20 mm, and the three low basins at 0.0, which is a VALUE,
  not a gap. Both glacier basins carry SATURATED cells (32767, the documented artifact),
  excluded from the mean and flagged — a naive average reads 125/34 mm instead;
- the −9999 pattern is static water/domain (in-basin cells are lakes), so the land mean stands
  and the water fraction is flagged, not fabricated over;
- the snapshot instant comes from the header (06:00 UTC), and availability is the origin's
  ~13:15 UTC Last-Modified — a 7.25 h lag a replay must respect.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import httpx
import pytest
import respx
from sqlalchemy import select

from cascade_core.db import create_schema, make_engine, make_session_factory
from cascade_core.fetch import ArchivingFetcher, HostRateLimiter
from cascade_core.models import DerivedFeature, GridMask
from cascade_core.objectstore import LocalFilesystemStore
from cascade_core.seed import seed_all
from cascade_core.settings import SEED_FILE
from cascade_providers_snodas import jobs as snodas_jobs
from cascade_providers_snodas.client import day_tar_url
from cascade_providers_snodas.parser import SnodasParseError, parse_snodas_swe
from tests.conftest import FIXTURES, GEO

TAR = (FIXTURES / "snodas" / "SNODAS_unmasked_20260827_swe_only.tar").read_bytes()
SNAPSHOT = datetime(2026, 8, 27, 6, 0, tzinfo=UTC)
PUBLISHED = "Thu, 27 Aug 2026 13:15:00 GMT"
NOW = datetime(2026, 8, 27, 13, 40, tzinfo=UTC)


# --- parser -------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def field():
    return parse_snodas_swe(TAR)


def test_the_header_describes_the_grid_and_the_instant(field) -> None:
    assert (field.grid.nx, field.grid.ny) == (8192, 4096)
    assert field.grid.dlat == pytest.approx(1 / 120, abs=1e-9)
    # first cell CENTRE: the header's edge extents shifted in by the offsets
    assert field.grid.la1 == pytest.approx(58.229166666, abs=1e-6)
    assert field.grid.lo1 == pytest.approx(360 - 130.5125, abs=1e-6)
    assert field.valid_time == SNAPSHOT
    assert field.values.size == field.grid.size
    assert parse_snodas_swe(TAR).grid.definition_hash == field.grid.definition_hash


def test_error_pages_and_broken_tars_are_refused() -> None:
    with pytest.raises(SnodasParseError, match="not_tar"):
        parse_snodas_swe(b"<?xml version=\"1.0\"?><html>Server error!</html>" + b"\x00" * 300)
    with pytest.raises(SnodasParseError, match="not_tar|swe_absent"):
        parse_snodas_swe(TAR[: 512 * 3])


def test_a_tar_without_the_swe_member_is_a_refusal(tmp_path) -> None:
    import io
    import tarfile

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as t:
        info = tarfile.TarInfo("zz_ssmv11036tS__T0001TTNATS2026082705HP001.dat.gz")
        info.size = 4
        t.addfile(info, io.BytesIO(b"\x1f\x8b\x00\x00"))
    with pytest.raises(SnodasParseError, match="swe_absent"):
        parse_snodas_swe(buf.getvalue())


# --- the job ------------------------------------------------------------------------------


@pytest.fixture
async def sessions(tmp_path):
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path}/snodas.db")
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


@respx.mock
async def test_one_day_lands_as_twelve_rows_with_the_glacier_truth(sessions, tmp_path) -> None:
    respx.get(day_tar_url(date(2026, 8, 27))).mock(
        return_value=httpx.Response(200, content=TAR, headers={"Last-Modified": PUBLISHED}))
    respx.get(url__startswith="https://noaadata.apps.nsidc.org/").mock(
        return_value=httpx.Response(404))
    async with sessions() as s:
        written = await snodas_jobs.run_fetch_swe(s, _fetcher(tmp_path), geo_dir=GEO, now=NOW)
        await s.commit()
        rows = list((await s.execute(select(DerivedFeature).where(
            DerivedFeature.feature.in_([snodas_jobs.FEATURE_SWE, snodas_jobs.FEATURE_SCF])))).scalars())
        masks = list((await s.execute(select(GridMask))).scalars())
    assert written == 12 and len(rows) == 12  # 6 basins x (SWE + fraction)
    assert len(masks) == 6
    swe = {r.scope_id: r for r in rows if r.feature == snodas_jobs.FEATURE_SWE}
    scf = {r.scope_id: r for r in rows if r.feature == snodas_jobs.FEATURE_SCF}
    # late-August physical truth: glaciers only. The Puyallup-White carries Rainier's
    # SATURATED cells (32767 = the documented unbounded-growth artifact): the first probe
    # naively averaged them and read 125 mm; the honest land mean with them EXCLUDED and
    # flagged is ~78 mm. The artifact is real, present, and visibly handled.
    assert swe["basin:puyallup-white"].value == pytest.approx(77.8, abs=1.0)
    assert swe["basin:puyallup-white"].values_json["saturated_fraction"] > 0
    assert snodas_jobs.SATURATED_CELLS in swe["basin:puyallup-white"].quality
    # Baker's glacier cells saturate too: the probe's naive 34 mm is honestly 20.2 mm
    assert swe["basin:nooksack"].value == pytest.approx(20.2, abs=1.0)
    assert snodas_jobs.SATURATED_CELLS in swe["basin:nooksack"].quality
    assert swe["basin:cedar"].value == 0.0, "zero snow is a VALUE, not a gap"
    assert 0.004 < scf["basin:puyallup-white"].value < 0.02
    for r in rows:
        assert r.valid_time.replace(tzinfo=UTC) == SNAPSHOT
        assert r.issued_at is None, "a daily analysis, not a forecast cycle"
        assert r.available_at.replace(tzinfo=UTC) == datetime(2026, 8, 27, 13, 15, tzinfo=UTC)
        assert r.confidence_label == "low", "assimilates the pillows we already carry"
    # the static lakes show up as a flagged water fraction, and the mean is the LAND mean
    nook = swe["basin:nooksack"]
    assert nook.values_json["water_fraction"] > 0.01
    assert snodas_jobs.WATER_CELLS in nook.quality


@respx.mock
async def test_a_second_run_writes_nothing(sessions, tmp_path) -> None:
    respx.get(day_tar_url(date(2026, 8, 27))).mock(
        return_value=httpx.Response(200, content=TAR, headers={"Last-Modified": PUBLISHED}))
    respx.get(url__startswith="https://noaadata.apps.nsidc.org/").mock(
        return_value=httpx.Response(404))
    async with sessions() as s:
        first = await snodas_jobs.run_fetch_swe(s, _fetcher(tmp_path), geo_dir=GEO, now=NOW)
        await s.commit()
    async with sessions() as s:
        second = await snodas_jobs.run_fetch_swe(s, _fetcher(tmp_path), geo_dir=GEO, now=NOW)
        await s.commit()
    assert first == 12 and second == 0


@respx.mock
async def test_a_missing_day_is_skipped_not_fabricated(sessions, tmp_path) -> None:
    """NSIDC 500s intermittently (measured): the day is skipped with a log line; nothing is
    written for it, and the next cron simply finds it inside the lookback."""
    respx.get(url__startswith="https://noaadata.apps.nsidc.org/").mock(
        return_value=httpx.Response(500, text="Server error!"))
    async with sessions() as s:
        written = await snodas_jobs.run_fetch_swe(s, _fetcher(tmp_path), geo_dir=GEO, now=NOW)
        await s.commit()
        rows = (await s.execute(select(DerivedFeature))).scalars().all()
    assert written == 0 and rows == []


@respx.mock
async def test_a_file_under_the_wrong_day_name_is_refused(sessions, tmp_path) -> None:
    respx.get(day_tar_url(date(2026, 8, 26))).mock(
        return_value=httpx.Response(200, content=TAR, headers={"Last-Modified": PUBLISHED}))
    respx.get(url__startswith="https://noaadata.apps.nsidc.org/").mock(
        return_value=httpx.Response(404))
    async with sessions() as s:
        with pytest.raises(ValueError, match="says snapshot"):
            await snodas_jobs.run_fetch_swe(s, _fetcher(tmp_path), geo_dir=GEO,
                                            now=datetime(2026, 8, 26, 13, 40, tzinfo=UTC))
