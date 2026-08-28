"""MRMS: observed hourly QPE per basin, with the covariate that qualifies it.

Assertions run against real captured bytes (a full-CONUS Pass2 QPE, its gauge-influence
companion, and one day's S3 listing). The load-bearing facts, each measured before being pinned:

- publication lag: LastModified sits ~57 min after the accumulation ends, and that instant — not
  the fetch time — is what ``available_at`` must carry;
- every seed basin aggregates at 100.00 % valid coverage on the real grid (MRMS gauge/model fill
  covers the BC headwaters), so the coverage policy treats anything less as a signal;
- the Skagit mask area reproduces the WBD/hypsometry figure, tying three independent
  area computations (masks, DEM pixel sum, equal-area projection) to one another.
"""

from __future__ import annotations

import gzip
import json
from datetime import UTC, datetime, timedelta

import httpx
import pytest
import respx
from sqlalchemy import func, select

from cascade_core.db import create_schema, make_engine, make_session_factory
from cascade_core.fetch import ArchivingFetcher, HostRateLimiter
from cascade_core.models import DerivedFeature, GridMask
from cascade_core.objectstore import LocalFilesystemStore
from cascade_core.registry import PRODUCT_MRMS_GAUGEINFL, PRODUCT_MRMS_QPE
from cascade_core.seed import seed_all
from cascade_core.settings import SEED_FILE
from cascade_geo.latlon import LatLonGridSpec
from cascade_geo.masks import build_basin_mask
from cascade_providers_mrms import jobs as mrms_jobs
from cascade_providers_mrms.client import BUCKET_URL, parse_listing
from cascade_providers_mrms.parser import MrmsParseError, parse_mrms_grib
from tests.conftest import FIXTURES, GEO

MRMS = FIXTURES / "mrms"
LISTING = (MRMS / "listing_qpe_day.xml").read_bytes()
QPE_GZ = (MRMS / "qpe_pass2_conus.grib2.gz").read_bytes()
GAUGE_GZ = (MRMS / "gaugeinfl_pass2_conus.grib2.gz").read_bytes()
NOW = datetime(2026, 8, 28, 4, 20, tzinfo=UTC)

BASINS = {
    "basin:cedar", "basin:green-duwamish", "basin:nooksack",
    "basin:puyallup-white", "basin:skagit", "basin:snohomish-snoqualmie",
}


# --- listing ------------------------------------------------------------------------------


def test_the_listing_yields_keys_and_the_true_publication_instant() -> None:
    objects = parse_listing(LISTING)
    assert len(objects) == 4
    newest = max(objects, key=lambda o: o.valid_time)
    lag = newest.last_modified - newest.valid_time
    # the measured ~57 min Pass2 latency; available_at carries THIS, never the fetch time
    assert timedelta(minutes=40) < lag < timedelta(minutes=90)
    assert newest.key.endswith(".grib2.gz")
    assert newest.valid_time.tzinfo is not None


def test_garbage_between_listing_tags_does_not_break_or_fabricate_entries() -> None:
    assert parse_listing(b"<xml>nothing useful</xml>") == ()
    # a NEW unknown tag between LastModified and Size must be skipped, not fatal: the checksum
    # tags appeared exactly this way once already
    doc = LISTING.replace(b"<Size>", b"<FutureTag>x</FutureTag><Size>", 1)
    assert len(parse_listing(doc)) == 4


# --- parser -------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def qpe_field():
    return parse_mrms_grib(QPE_GZ)


def test_the_real_grid_decodes_with_a_stable_identity(qpe_field) -> None:
    grid = qpe_field.grid
    assert (grid.nx, grid.ny) == (7000, 3500)
    assert grid.dlon == pytest.approx(0.01) and grid.dlat == pytest.approx(0.01)
    assert grid.la1 == pytest.approx(54.995)
    assert grid.lo1 == pytest.approx(230.005)  # the provider's 0..360 convention, kept
    assert qpe_field.values.size == grid.size
    # identity is the Section 3 bytes: a second parse of the same bytes must agree exactly
    assert parse_mrms_grib(QPE_GZ).grid.definition_hash == grid.definition_hash


def test_truncated_or_non_grib_payloads_are_refused() -> None:
    with pytest.raises(MrmsParseError, match="not_gzip"):
        parse_mrms_grib(b"not even gzip")
    truncated = gzip.compress(gzip.decompress(QPE_GZ)[:5000])
    with pytest.raises(MrmsParseError):
        parse_mrms_grib(truncated)


# --- aggregation --------------------------------------------------------------------------


def _wedge_grid() -> LatLonGridSpec:
    """A 40x40 tenth-degree grid over a synthetic square basin of ~900 interior cells.

    Big enough that ONE poisoned cell sits well under the 0.5 % coverage threshold — the
    flag-but-keep case — while poisoning half the interior forces the refusal case. The real
    basins are 1,700-10,600 cells, so this is the small end of realistic, not a toy.
    """
    return LatLonGridSpec(nx=40, ny=40, la1=50.0, lo1=230.0, dlon=0.1, dlat=0.1,
                          earth_radius_m=6371229.0, definition_hash="synthetic")


def _square_mask(grid: LatLonGridSpec):
    # 3 x 3 degrees = 30 x 30 cells inside a 4-degree grid
    ring = [[-129.5, 46.2], [-126.5, 46.2], [-126.5, 49.2], [-129.5, 49.2], [-129.5, 46.2]]
    return build_basin_mask(basin_id="basin:test", polygons=[[ring]], grid=grid, polygon_source="synthetic")


def test_sentinels_shape_the_mean_and_the_flags() -> None:
    import numpy as np

    grid = _wedge_grid()
    mask = _square_mask(grid)
    values = np.full(grid.size, 2.0)
    stats = mrms_jobs._aggregate(mask, values)
    assert stats["mean"] == pytest.approx(2.0)
    assert stats["valid_fraction"] == pytest.approx(1.0)
    assert mrms_jobs._flags(stats) == []

    # one interior cell of no-coverage: flagged, excluded from the mean, coverage still enough
    poisoned = values.copy()
    inside = [c for c, w in mask.cells if w == 1.0]
    poisoned[inside[0]] = -3.0
    stats = mrms_jobs._aggregate(mask, poisoned)
    assert stats["mean"] == pytest.approx(2.0)  # remaining valid cells all read 2.0
    assert 0 < stats["no_coverage_fraction"] < 0.005
    assert mrms_jobs.NO_COVERAGE_PRESENT in mrms_jobs._flags(stats)

    # most of the basin dark: the mean is REFUSED, not computed over the visible part
    dark = values.copy()
    for cell in inside[: len(inside) // 2]:
        dark[cell] = -3.0
    stats = mrms_jobs._aggregate(mask, dark)
    assert stats["mean"] is None
    assert mrms_jobs.INSUFFICIENT_COVERAGE in mrms_jobs._flags(stats)


def test_every_seed_basin_reads_full_coverage_on_the_real_grid(qpe_field) -> None:
    """The measured fact the coverage policy stands on, pinned against the real bytes."""
    geo = json.loads(gzip.decompress((GEO / "basins_seed_full.geojson.gz").read_bytes()))
    areas = {}
    for feature in geo["features"]:
        basin_id = feature["properties"]["id"]
        mask = build_basin_mask(
            basin_id=basin_id,
            polygons=mrms_jobs._polygons_of(feature["geometry"]),
            grid=qpe_field.grid,
            polygon_source="full",
        )
        stats = mrms_jobs._aggregate(mask, qpe_field.values)
        assert stats["valid_fraction"] == pytest.approx(1.0, abs=1e-4), basin_id
        assert stats["mean"] is not None and stats["mean"] >= 0.0
        areas[basin_id] = mask.masked_area_km2
    assert set(areas) == BASINS
    # three independent area computations agree: this mask, the DEM pixel sum (8250.0), WBD (8275)
    assert areas["basin:skagit"] == pytest.approx(8250, rel=0.005)


# --- the job ------------------------------------------------------------------------------


@pytest.fixture
async def sessions(tmp_path):
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path}/mrms.db")
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


def _one_object_listing(product_dir: str, stamp: str, last_modified: str) -> bytes:
    key = f"CONUS/{product_dir}/20260828/MRMS_{product_dir.rsplit('_', 1)[0]}_00.00_{stamp}.grib2.gz"
    return (
        '<?xml version="1.0" encoding="UTF-8"?><ListBucketResult>'
        f"<Contents><Key>{key}</Key><LastModified>{last_modified}</LastModified>"
        f"<ETag>&quot;x&quot;</ETag><Size>1</Size></Contents></ListBucketResult>"
    ).encode()


def _mock_s3(qpe_missing: bool = False) -> None:
    def answer(request: httpx.Request) -> httpx.Response:
        prefix = request.url.params.get("prefix", "")
        if prefix:
            product_dir = prefix.split("/")[1]
            body = _one_object_listing(product_dir, "20260828-030000", "2026-08-28T03:57:19.000Z")
            return httpx.Response(200, content=body, headers={"content-type": "application/xml"})
        if "GaugeInflIndex" in str(request.url):
            return httpx.Response(200, content=GAUGE_GZ, headers={"content-type": "binary/octet-stream"})
        if qpe_missing:
            return httpx.Response(404, content=b"gone")
        return httpx.Response(200, content=QPE_GZ, headers={"content-type": "binary/octet-stream"})

    respx.get(url__startswith=BUCKET_URL).mock(side_effect=answer)


@respx.mock
async def test_the_job_stores_both_features_with_the_published_instant(sessions, tmp_path) -> None:
    _mock_s3()
    async with sessions() as s:
        written = await mrms_jobs.run_fetch_qpe(s, _fetcher(tmp_path), geo_dir=GEO, now=NOW)
        await s.commit()
        rows = list((await s.execute(select(DerivedFeature))).scalars())
    qpe = [r for r in rows if r.feature == mrms_jobs.FEATURE_QPE]
    gauge = [r for r in rows if r.feature == mrms_jobs.FEATURE_GAUGEINFL]
    assert written == 13 and len(qpe) == 6 and len(gauge) == 6  # 12 basin rows + 1 window raster
    for r in qpe:
        assert r.value is not None and r.value >= 0.0
        assert r.unit == "mm" and r.window == "1h"
        assert r.product_id == PRODUCT_MRMS_QPE
        assert r.issued_at is None, "an observation forecasts nothing"
        assert r.valid_time.replace(tzinfo=UTC) == datetime(2026, 8, 28, 3, 0, tzinfo=UTC)  # accumulation END, from the key
        # the knowledge time is NODD's LastModified, NOT our fetch clock
        assert r.available_at.replace(tzinfo=UTC) == datetime(2026, 8, 28, 3, 57, 19, tzinfo=UTC)
        assert r.values_json["valid_fraction"] == pytest.approx(1.0, abs=1e-4)
    for r in gauge:
        assert r.product_id == PRODUCT_MRMS_GAUGEINFL and r.unit == "index"


@respx.mock
async def test_a_second_run_writes_nothing_and_reuses_the_stored_masks(sessions, tmp_path) -> None:
    _mock_s3()
    async with sessions() as s:
        first = await mrms_jobs.run_fetch_qpe(s, _fetcher(tmp_path), geo_dir=GEO, now=NOW)
        await s.commit()
    async with sessions() as s:
        second = await mrms_jobs.run_fetch_qpe(s, _fetcher(tmp_path), geo_dir=GEO, now=NOW)
        await s.commit()
        n_masks = (await s.execute(select(func.count()).select_from(GridMask))).scalar_one()
    assert first == 13 and second == 0  # 12 basin rows + 1 window raster; a rerun re-stores neither
    assert n_masks == 6, "one mask per basin per grid definition; a rerun must not duplicate them"


@respx.mock
async def test_a_missing_qpe_object_is_isolated_not_fatal(sessions, tmp_path) -> None:
    _mock_s3(qpe_missing=True)
    async with sessions() as s:
        written = await mrms_jobs.run_fetch_qpe(s, _fetcher(tmp_path), geo_dir=GEO, now=NOW)
        await s.commit()
    assert written == 0  # nothing stored, but the run reports rather than raising mid-loop


@respx.mock
async def test_an_empty_listing_is_a_retryable_failure_not_an_empty_success(sessions, tmp_path) -> None:
    respx.get(url__startswith=BUCKET_URL).mock(
        return_value=httpx.Response(200, content=b"<?xml version=\"1.0\"?><ListBucketResult></ListBucketResult>")
    )
    async with sessions() as s:
        with pytest.raises(mrms_jobs.NoListingError, match="stopped publishing or the listing shape changed"):
            await mrms_jobs.run_fetch_qpe(s, _fetcher(tmp_path), geo_dir=GEO, now=NOW)
        await s.rollback()


@respx.mock
async def test_a_mask_from_another_grid_definition_is_never_borrowed(sessions, tmp_path) -> None:
    """The whole point of hashing Section 3: a stale mask must MISS, and the job must rebuild.

    Six poison masks are stored under a different grid hash, each pointing at the ocean corner
    of the grid. If the lookup ever ignores the hash, those are "found", nothing new is built,
    and the aggregation runs over cells that are not the basin. The correct behaviour is to
    treat them as absent: build fresh masks under the real hash (count 6 -> 12) and aggregate
    every basin at full coverage.
    """
    from cascade_core.models import Basin
    from cascade_core.timeutils import utcnow

    _mock_s3()
    async with sessions() as s:
        for (basin_id,) in await s.execute(select(Basin.id)):
            s.add(GridMask(
                basin_id=basin_id, grid_definition_hash="stale-grid-definition",
                method_id="method:basin-grid-mask@1.0.0", cells=[[0, 1.0]], cell_count=1,
                masked_area_km2=1.0, polygon_source="poison", computed_at=utcnow(),
            ))
        await s.commit()
    async with sessions() as s:
        await mrms_jobs.run_fetch_qpe(s, _fetcher(tmp_path), geo_dir=GEO, now=NOW)
        await s.commit()
        n_masks = (await s.execute(select(func.count()).select_from(GridMask))).scalar_one()
        rows = list((await s.execute(
            select(DerivedFeature).where(DerivedFeature.feature == mrms_jobs.FEATURE_QPE)
        )).scalars())
    assert n_masks == 12, "fresh masks under the real hash; the stale ones left alone, not reused"
    for r in rows:
        assert r.values_json["valid_fraction"] == pytest.approx(1.0, abs=1e-4)
        assert r.values_json["masked_area_km2"] > 100, "aggregated over the basin, not the ocean corner"


@respx.mock
async def test_the_window_raster_stores_the_cut_plane_and_prunes_on_retention(sessions, tmp_path) -> None:
    """ADR-0020 end to end at the job: the stored raster decodes back to exactly the values the
    plane held over the window (quantized), carries its own georeferencing and the published
    instant, and rows older than retention are pruned by the same job that writes."""
    import gzip as _gzip

    import numpy as np

    from cascade_core.models import FieldRaster
    from cascade_providers_mrms.parser import parse_mrms_grib
    from cascade_providers_mrms.raster import SENTINEL, cut_window

    _mock_s3()
    async with sessions() as s:
        await mrms_jobs.run_fetch_qpe(s, _fetcher(tmp_path), geo_dir=GEO, now=NOW)
        await s.commit()
        row = (await s.execute(select(FieldRaster))).scalars().one()

    # georeferencing rides in the row, and the knowledge time is NODD's LastModified
    assert (row.nx, row.ny) == (237, 283)
    assert row.available_at.replace(tzinfo=UTC) == datetime(2026, 8, 28, 3, 57, 19, tzinfo=UTC)
    assert row.unit == "mm" and row.scale == 0.1 and row.method_id == mrms_jobs.METHOD_RASTER

    # round trip: the stored bytes are the quantized window of the very plane the job decoded
    field = parse_mrms_grib(QPE_GZ)
    expected = cut_window(field)
    got = np.frombuffer(_gzip.decompress(row.cells), dtype="<u2")
    want = np.frombuffer(_gzip.decompress(expected.cells), dtype="<u2")
    assert np.array_equal(got, want) and row.max_value == expected.max_value
    assert SENTINEL not in got, "the fixture hour has full coverage; a sentinel here is a packing bug"

    # retention: the same hour is pruned once `now` moves past RASTER_RETENTION (the prune is
    # called at the end of every run; exercised directly because a listing 3 days stale is a
    # NoListingError before the run would reach it — correct, and a different test's subject)
    async with sessions() as s:
        pruned = await mrms_jobs._prune_rasters(s, NOW + mrms_jobs.RASTER_RETENTION + timedelta(hours=2))
        await s.commit()
        left = list((await s.execute(select(FieldRaster.valid_time))).scalars())
    assert pruned == 1 and left == [], "the writer prunes its own rows past retention"


@respx.mock
async def test_the_field_endpoint_serves_the_raster_and_a_reasoned_404_before_it(tmp_path) -> None:
    """`/viz/fields/precip_observed` end to end: ingest one mocked hour, read it back through
    the API, decode, and match the plane. Before ingestion (and past the 6 h freshness bound)
    the answer is a 404 with a reason — UNKNOWN is never an empty raster (ADR-0020 §4)."""
    import base64
    import gzip as _gzip

    import numpy as np

    from cascade_api.main import create_app
    from cascade_contracts import FieldRasterState
    from cascade_core.settings import Settings
    from cascade_providers_mrms.raster import cut_window

    settings = Settings(db_url=f"sqlite+aiosqlite:///{tmp_path}/mrms_api.db", raw_dir=tmp_path / "raw", geo_dir=GEO)
    engine = make_engine(settings.db_url)
    await create_schema(engine)
    factory = make_session_factory(engine)
    _mock_s3()
    async with factory() as s:
        await seed_all(s, geo_dir=GEO, seed_file=SEED_FILE)
        await mrms_jobs.run_fetch_qpe(s, _fetcher(tmp_path), geo_dir=GEO, now=NOW)
        await s.commit()

    app = create_app(settings, engine=engine)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/viz/fields/precip_observed", params={"as_of": NOW.isoformat()})
        assert r.status_code == 200
        state = FieldRasterState.model_validate(r.json())
        assert state.truth == "observation" and state.kind == "observed" and state.unit == "mm"
        assert (state.spec.nx, state.spec.ny) == (237, 283)
        got = np.frombuffer(_gzip.decompress(base64.b64decode(state.cells_b64)), dtype="<u2")
        want = np.frombuffer(_gzip.decompress(cut_window(parse_mrms_grib(QPE_GZ)).cells), dtype="<u2")
        assert np.array_equal(got, want)
        assert state.provenance_refs[state.prov].freshness.state == "current"

        # before the bytes existed: a reasoned 404, never an empty plane
        early = await c.get("/viz/fields/precip_observed", params={"as_of": "2026-08-28T02:00:00Z"})
        assert early.status_code == 404 and "nothing current to draw" in early.json()["detail"]
        # and a layer the catalogue does not know names the catalogue
        unknown = await c.get("/viz/fields/snow_depth", params={"as_of": NOW.isoformat()})
        assert unknown.status_code == 404 and "precip_observed" in unknown.json()["detail"]
    await engine.dispose()
