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
    assert written == 13 and len(rows) == 12  # 6 basins x (SWE + fraction) + 1 window raster
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
    assert first == 13 and second == 0  # 12 basin rows + the window raster


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


@respx.mock
async def test_a_non_utc_now_neither_refetches_nor_wedges(sessions, tmp_path) -> None:
    """The review reproduced the wedge on real PostgreSQL: an America/Los_Angeles `now` made
    the membership probe never match the stored UTC instants, so every stored day re-inserted
    and tripped the identity constraint. `now` is normalized to UTC at entry."""
    from zoneinfo import ZoneInfo

    respx.get(day_tar_url(date(2026, 8, 27))).mock(
        return_value=httpx.Response(200, content=TAR, headers={"Last-Modified": PUBLISHED}))
    respx.get(url__startswith="https://noaadata.apps.nsidc.org/").mock(
        return_value=httpx.Response(404))
    async with sessions() as s:
        first = await snodas_jobs.run_fetch_swe(s, _fetcher(tmp_path), geo_dir=GEO, now=NOW)
        await s.commit()
    la_now = NOW.astimezone(ZoneInfo("America/Los_Angeles"))
    async with sessions() as s:
        second = await snodas_jobs.run_fetch_swe(s, _fetcher(tmp_path), geo_dir=GEO, now=la_now)
        await s.commit()
        total = len((await s.execute(select(DerivedFeature))).scalars().all())
    assert first == 13 and second == 0 and total == 12


@respx.mock
async def test_a_partial_day_is_completed_row_by_row_never_reinserted(sessions, tmp_path) -> None:
    """One basin's rows deleted (standing in for a basin seeded without geometry, then given
    it): the rerun writes ONLY the missing basin — a whole-day re-insert was the PostgreSQL
    crash-loop the review reproduced."""
    respx.get(day_tar_url(date(2026, 8, 27))).mock(
        return_value=httpx.Response(200, content=TAR, headers={"Last-Modified": PUBLISHED}))
    respx.get(url__startswith="https://noaadata.apps.nsidc.org/").mock(
        return_value=httpx.Response(404))
    async with sessions() as s:
        await snodas_jobs.run_fetch_swe(s, _fetcher(tmp_path), geo_dir=GEO, now=NOW)
        await s.commit()
        from sqlalchemy import delete

        await s.execute(delete(DerivedFeature).where(DerivedFeature.scope_id == "basin:cedar"))
        await s.commit()
    async with sessions() as s:
        written = await snodas_jobs.run_fetch_swe(s, _fetcher(tmp_path), geo_dir=GEO, now=NOW)
        await s.commit()
        rows = (await s.execute(select(DerivedFeature))).scalars().all()
    assert written == 2, "exactly the missing basin's two features, nothing re-inserted"
    assert len(rows) == 12


@respx.mock
async def test_the_swe_window_raster_round_trips_at_integer_millimetres(sessions, tmp_path) -> None:
    """ADR-0020 for SNODAS: the stored raster decodes back to the plane's window at 1 mm
    steps (the provider's own integers, nothing rounded), sentinels distinct from zero SWE."""
    import gzip as _gzip

    import numpy as np

    from cascade_core.models import FieldRaster
    from cascade_core.registry import PRODUCT_SNODAS_SWE
    from cascade_geo.window_raster import SENTINEL, cut_window
    from cascade_providers_snodas.parser import parse_snodas_swe

    respx.get(day_tar_url(date(2026, 8, 27))).mock(
        return_value=httpx.Response(200, content=TAR, headers={"Last-Modified": PUBLISHED}))
    respx.get(url__startswith="https://noaadata.apps.nsidc.org/").mock(
        return_value=httpx.Response(404))
    async with sessions() as s:
        await snodas_jobs.run_fetch_swe(s, _fetcher(tmp_path), geo_dir=GEO, now=NOW)
        await s.commit()
        row = (await s.execute(select(FieldRaster))).scalars().one()

    assert row.product_id == PRODUCT_SNODAS_SWE and row.field == snodas_jobs.FIELD_SWE_RASTER
    assert row.unit == "mm" and row.scale == 1.0 and row.method_id == "method:field-raster-window@1.0.0"

    field = parse_snodas_swe(TAR)
    from cascade_providers_snodas.parser import SATURATED

    expected = cut_window(field.grid, field.values, scale=1.0, unit="mm", invalid_values=(SATURATED,))
    got = np.frombuffer(_gzip.decompress(row.cells), dtype="<u2")
    want = np.frombuffer(_gzip.decompress(expected.cells), dtype="<u2")
    assert np.array_equal(got, want) and (row.nx, row.ny) == (expected.nx, expected.ny)
    # SNODAS marks off-grid/no-data negative; those must be SENTINEL in the packing, never 0
    assert (SENTINEL in got) == (SENTINEL in want)
    # 32767 (int16 saturation, the glacier artifact) is a CODE, not 32 metres of snow: it must
    # be SENTINEL in the packing and must never set max_value
    assert 32767 not in got[got != SENTINEL] and row.max_value < 32767
    assert row.max_value == expected.max_value


@respx.mock
async def test_the_snow_field_endpoint_serves_analysis_with_the_daily_freshness_bound(tmp_path) -> None:
    """/viz/fields/snow_cover: kind `analysis`, truth `authoritative_model`, and a 36 h bound —
    a daily snapshot 30 h old is current in a way an hourly accumulation never is; past the
    bound the answer is the reasoned 404, never yesterday presented as now."""
    import httpx as _httpx

    from datetime import timedelta

    from cascade_api.main import create_app
    from cascade_contracts import FieldRasterState
    from cascade_core.settings import Settings

    settings = Settings(db_url=f"sqlite+aiosqlite:///{tmp_path}/snodas_api.db", raw_dir=tmp_path / "raw", geo_dir=GEO)
    engine = make_engine(settings.db_url)
    await create_schema(engine)
    factory = make_session_factory(engine)
    respx.get(day_tar_url(date(2026, 8, 27))).mock(
        return_value=_httpx.Response(200, content=TAR, headers={"Last-Modified": PUBLISHED}))
    respx.get(url__startswith="https://noaadata.apps.nsidc.org/").mock(return_value=_httpx.Response(404))
    async with factory() as s:
        await seed_all(s, geo_dir=GEO, seed_file=SEED_FILE)
        await snodas_jobs.run_fetch_swe(s, _fetcher(tmp_path), geo_dir=GEO, now=NOW)
        await s.commit()

    app = create_app(settings, engine=engine)
    async with _httpx.AsyncClient(transport=_httpx.ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/viz/fields/snow_cover", params={"as_of": (NOW + timedelta(hours=20)).isoformat()})
        assert r.status_code == 200
        state = FieldRasterState.model_validate(r.json())
        assert state.kind == "analysis" and state.truth == "authoritative_model"
        assert state.window == "daily" and state.unit == "mm" and state.scale == 1.0
        assert "assimilation analysis" in state.provenance_refs[state.prov].label

        stale = await c.get("/viz/fields/snow_cover", params={"as_of": (NOW + timedelta(hours=40)).isoformat()})
        assert stale.status_code == 404 and "within 36 h" in stale.json()["detail"]
    await engine.dispose()
