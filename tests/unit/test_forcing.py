"""Forcing v0 — NBM WA subsets, basin masks, basin QPF and the banded surface.

Deterministic and offline (docs/TESTING.md): every byte comes from the checked-in NOMADS
capture in ``tests/fixtures/providers/nbm/`` (real 2026-08-24 12Z subsets), the network is
mocked with respx, and no assertion depends on the weather — the goldens are what THIS cycle
says, and they change only when the mask, the projection or the aggregation changes.

The exit tests of p3-surfaces-design §5 "Forcing" live here:
1. the archived qmd.f072 subset decodes to 161 messages, and the Skagit basin mean is golden;
2. masked area is within 3 % of the WBD area for every basin;
3. a mutated grid definition hash makes the job REFUSE and the surface UNKNOWN with the
   reason, rather than producing a number with the wrong weights;
4. every driver resolves to a ProvenanceRef whose kind comes from the registry — MODELED for
   the QPF, EXPERIMENTAL for the assessment, never OFFICIAL_FORECAST;
5. a knowledge time before ingestion returns UNKNOWN with the "no cycle" reason.
"""

from __future__ import annotations

import gzip
import json
from datetime import UTC, datetime, timedelta

import httpx
import pytest
import respx
from sqlalchemy import select

from cascade_contracts import ContractEnvelope, ProvenanceRef, SourceKind, TruthClass
from cascade_contracts.visualization import (
    AgreementLevel,
    AgreementState,
    BasinSurfaces,
    BasinVisualizationState,
    FloodCategory,
    GeometryRef,
    HazardState,
    SurfaceLevel,
    SurfaceState,
    TimeContext,
)
from cascade_core.db import create_schema, make_engine, make_session_factory
from cascade_core.fetch import ArchivingFetcher
from cascade_core.knowledge import as_known_at
from cascade_core.models import Basin, DerivedFeature, GridMask, SourceProduct
from cascade_core.objectstore import LocalFilesystemStore, object_key_for
from cascade_core.registry import PRODUCT_NBM_CORE, PRODUCT_NBM_QMD, SRC_CASCADE, SRC_NBM
from cascade_core.seed import seed_all
from cascade_core.settings import SEED_FILE
from cascade_geo import (
    GridSpec,
    LambertConformalConic,
    MaskError,
    build_basin_mask,
    load_basin_polygons,
    weighted_mean,
)
from cascade_hydrology import forcing
from cascade_providers_nbm import client, jobs, parser
from cascade_providers_nbm.normalize import Refusal, basin_mean, stored_unit
from tests.conftest import FIXTURES, GEO

NBM = FIXTURES / "nbm"
CYCLE = client.Cycle(2026, 8, 24, 12)
#: A clock a few hours after the 12Z qmd cycle landed (it lands at ~cycle + 7 h 20 m).
NOW = datetime(2026, 8, 24, 22, 10, tzinfo=UTC)

QMD_URL = "https://nomads.ncep.noaa.gov/cgi-bin/filter_blend.pl"


# --------------------------------------------------------------------------- fixtures


@pytest.fixture(scope="module")
def qmd72() -> bytes:
    return (NBM / "qmd_f072_wa.grib2").read_bytes()


@pytest.fixture(scope="module")
def qmd24() -> bytes:
    return (NBM / "qmd_f024_wa.grib2").read_bytes()


@pytest.fixture(scope="module")
def core24() -> bytes:
    return (NBM / "core_f024_snowlvl_wa.grib2").read_bytes()


@pytest.fixture(scope="module")
def grid(qmd72: bytes) -> GridSpec:
    return parser.decode(qmd72, want=parser.cumulative_apcp(hours=72, percentile=50))[0].grid


@pytest.fixture(scope="module")
def polygons():
    return load_basin_polygons(GEO / jobs.BASIN_GEOMETRY_FILE)


@pytest.fixture(scope="module")
def masks(grid: GridSpec, polygons):
    """Built once for the whole module: exact clipping over ~110 k Skagit vertices is the
    expensive part of the pipeline, and it is precomputed reference data in production too."""
    polys, _areas, source = polygons
    return {bid: build_basin_mask(basin_id=bid, polygons=p, grid=grid, polygon_source=source) for bid, p in polys.items()}


@pytest.fixture
async def sessions(tmp_path):
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path}/forcing.db")
    await create_schema(engine)
    factory = make_session_factory(engine)
    async with factory() as session:
        await seed_all(session, geo_dir=GEO, seed_file=SEED_FILE)
    yield factory
    await engine.dispose()


def _fetcher(tmp_path) -> ArchivingFetcher:
    return ArchivingFetcher(store=LocalFilesystemStore(tmp_path), user_agent="CascadiaPapsukkal/0.1 (test)", clock=lambda: NOW)


def _mock_nomads(qmd_bytes: dict[int, bytes] | None = None, core_bytes: bytes | None = None) -> None:
    """Route the CGI by its `file` query parameter, exactly as the real service keys off it."""

    def handler(request: httpx.Request) -> httpx.Response:
        name = request.url.params["file"]
        if ".core." in name and core_bytes is not None:
            return httpx.Response(200, content=core_bytes, headers={"content-type": "application/octet-stream"})
        if qmd_bytes is not None:
            fhour = int(name.split(".f")[1][:3])
            body = qmd_bytes.get(fhour)
            if body is not None:
                return httpx.Response(200, content=body, headers={"content-type": "application/octet-stream"})
        return httpx.Response(404, content=b"not found")

    respx.get(QMD_URL).mock(side_effect=handler)


async def _install_masks(session, masks) -> None:
    for mask in masks.values():
        session.add(
            GridMask(
                basin_id=mask.basin_id, grid_definition_hash=mask.grid_definition_hash, method_id=mask.method_id,
                cells=mask.as_rows(), cell_count=mask.cell_count, masked_area_km2=mask.masked_area_km2,
                polygon_source=mask.polygon_source, computed_at=NOW,
            )
        )
    await session.flush()


async def _products(session) -> dict[str, SourceProduct]:
    return {p.id: p for p in (await session.execute(select(SourceProduct))).scalars()}


# ------------------------------------------------------------------------ 1. the payload


def test_the_captured_wa_subset_is_the_shape_the_design_measured(qmd72: bytes, core24: bytes) -> None:
    keys = parser.scan(qmd72)
    assert len(keys) == 161  # exit test §5.2: 161 messages
    assert (0, 72) in parser.windows(keys, parameter=parser.APCP)  # the 0-3 day cumulative window
    assert parser.percentile_levels(keys, parameter=parser.APCP, hours=72) == list(range(0, 101, 5))
    assert len(parser.scan(core24)) == 16  # 15 SNOWLVL percentiles + the deterministic field


def test_snowlvl_is_selected_by_grib_numbers_never_by_shortname(core24: bytes) -> None:
    """eccodes 2.48 has no name for this NCEP local-table parameter (DATA_SOURCES open 12)."""
    fields = parser.decode(core24, want=parser.snow_level(percentile=50), with_values=False)
    field = parser.one(fields, what="SNOWLVL p50")
    assert field.key.parameter == (0, 19, 236) and field.key.percentile == 50
    assert parser.percentile_levels(parser.scan(core24), parameter=parser.SNOWLVL) == [1, 5, 10, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90, 95, 99]
    # The name is useless on purpose: selecting on it would silently match nothing.
    assert field.units in ("unknown", "")


def test_a_variable_absent_from_a_cycle_is_a_typed_error_not_an_empty_number(qmd72: bytes) -> None:
    """TESTING §3 case 8: a GRIB variable missing from a cycle. qmd carries no SNOWLVL."""
    with pytest.raises(parser.NbmParseError, match="field_missing"):
        parser.one(parser.decode(qmd72, want=parser.snow_level(percentile=50), with_values=False), what="SNOWLVL p50")


def test_truncated_html_and_empty_payloads_raise_before_any_decode() -> None:
    with pytest.raises(parser.NbmParseError, match="truncated"):
        parser.split_messages((NBM / "truncated.grib2").read_bytes())
    with pytest.raises(parser.NbmParseError, match="not_grib2"):
        parser.split_messages((NBM / "html_error.html").read_bytes())
    with pytest.raises(parser.NbmParseError, match="empty_payload"):
        parser.split_messages(b"")
    with pytest.raises(parser.NbmParseError, match="bad_trailer"):
        parser.split_messages(b"GRIB\x00\x00\x00\x02" + (16).to_bytes(8, "big") + b"XXXX"[:0] + b"NOPE"[:0] + b"")


@respx.mock
async def test_a_timeout_and_a_provider_outage_are_typed_errors_and_write_nothing(sessions, tmp_path) -> None:
    """TESTING §3 cases 4 and 5: no partial write, no substituted cycle, no silent zero."""
    from cascade_core.fetch import FetchError
    from cascade_core.models import RawArtifact

    respx.get(QMD_URL).mock(side_effect=httpx.ConnectTimeout("nomads timed out"))
    async with sessions() as session:
        with pytest.raises(FetchError, match="timeout"):
            await jobs.run_fetch_qmd(session, _fetcher(tmp_path), cycle=CYCLE, horizons=(72,))
        assert (await session.execute(select(RawArtifact))).scalars().all() == []
        assert (await session.execute(select(DerivedFeature))).scalars().all() == []

    respx.get(QMD_URL).mock(return_value=httpx.Response(503, content=b"service unavailable"))
    async with sessions() as session:
        with pytest.raises(FetchError, match="http_status"):
            await jobs.run_fetch_qmd(session, _fetcher(tmp_path), cycle=CYCLE, horizons=(72,))
        assert (await session.execute(select(DerivedFeature))).scalars().all() == []


@respx.mock
async def test_an_html_error_page_served_as_http_200_never_reaches_the_decoder(sessions, tmp_path, masks) -> None:
    respx.get(QMD_URL).mock(
        return_value=httpx.Response(200, content=(NBM / "html_error.html").read_bytes(), headers={"content-type": "text/html"})
    )
    async with sessions() as session:
        await _install_masks(session, masks)
        with pytest.raises(parser.NbmParseError, match="not_grib2"):
            await jobs.run_fetch_qmd(session, _fetcher(tmp_path), cycle=CYCLE, horizons=(72,))
        # The raw bytes are archived anyway: a parse failure must never lose the payload.
        from cascade_core.models import RawArtifact

        assert len((await session.execute(select(RawArtifact))).scalars().all()) == 1
        assert (await session.execute(select(DerivedFeature))).scalars().all() == []


def test_units_are_asserted_from_the_payload_and_never_converted(qmd72: bytes, core24: bytes) -> None:
    apcp = parser.decode(qmd72, want=parser.cumulative_apcp(hours=72, percentile=50), with_values=False)[0]
    unit, native, flags = stored_unit(apcp)
    assert (unit, native, flags) == ("mm", "kg m**-2", ())  # kg m-2 of water IS mm of depth
    snow = parser.decode(core24, want=parser.snow_level(percentile=50), with_values=False)[0]
    unit, native, flags = stored_unit(snow)
    assert unit == "m" and flags == (parser.UNIT_FROM_DOCUMENTATION,)  # eccodes cannot name it


# ------------------------------------------------------------ 2. projection and masks


def test_the_projection_reproduces_the_providers_own_coordinates(qmd72: bytes, grid: GridSpec) -> None:
    """The mask depends entirely on this map, so it is checked against eccodes' own lat/lon."""
    eccodes = pytest.importorskip("eccodes")
    message = parser.split_messages(qmd72)[0]
    handle = eccodes.codes_new_from_message(message)
    try:
        lats = eccodes.codes_get_array(handle, "latitudes")
        lons = eccodes.codes_get_array(handle, "longitudes")
    finally:
        eccodes.codes_release(handle)
    projection = LambertConformalConic(grid)
    worst = 0.0
    for flat in range(0, grid.size, 37):
        j, i = divmod(flat, grid.nx)
        fi, fj = projection.to_grid(float(lons[flat]), float(lats[flat]))
        worst = max(worst, abs(fi - i), abs(fj - j))
    assert worst < 1e-6, f"projection disagrees with the provider by {worst} of a cell"
    assert grid.nx == 99 and grid.ny == 142 and round(grid.dx_m, 3) == 2539.703


def test_masked_area_is_within_three_percent_of_the_wbd_area(masks, polygons) -> None:
    """Exit test §5.3. Measured margin today is ~0.3 %; the sphere the model uses is slightly
    smaller than the ellipsoid WBD measures on, which is where the consistent bias comes from."""
    _polys, wbd, _source = polygons
    assert set(masks) == set(wbd) and len(masks) == 6
    for basin_id, mask in masks.items():
        error = abs(mask.masked_area_km2 - wbd[basin_id]) / wbd[basin_id]
        assert error < 0.03, f"{basin_id}: {mask.masked_area_km2:.1f} km2 vs WBD {wbd[basin_id]} km2"
        assert all(0.0 < w <= 1.0 for _flat, w in mask.cells)
        assert all(0 <= flat < 99 * 142 for flat, _w in mask.cells)


def test_the_hand_rolled_clipping_agrees_with_an_independent_geometry_library(masks, grid: GridSpec, polygons) -> None:
    """cascade_geo owns its polygon clipping so GEOS never enters the worker image; that only
    holds up if the arithmetic is right, so it is checked cell by cell against shapely (a dev
    dependency, offline) on a whole basin."""
    shapely_geometry = pytest.importorskip("shapely.geometry")
    shapely_ops = pytest.importorskip("shapely.ops")
    polys, _wbd, _source = polygons
    projection = LambertConformalConic(grid)
    parts = [
        shapely_geometry.Polygon(rings[0], rings[1:])
        for polygon in polys["basin:cedar"]
        for rings in [[[projection.to_grid(float(x), float(y)) for x, y, *_ in ring] for ring in polygon]]
    ]
    geometry = shapely_ops.unary_union([p.buffer(0) for p in parts])
    mask = masks["basin:cedar"]
    worst = 0.0
    for flat, weight in mask.cells:
        j, i = divmod(flat, grid.nx)
        independent = geometry.intersection(shapely_geometry.box(i - 0.5, j - 0.5, i + 0.5, j + 0.5)).area
        worst = max(worst, abs(independent - weight))
    assert worst < 1e-9, f"clipping disagrees with shapely by {worst} of a cell"


def test_cell_centre_counting_with_a_nominal_cell_area_overcounts_by_a_fifth(masks, grid: GridSpec, polygons) -> None:
    """The measured reason this module does exact fractional clipping (design §1.4).

    Counting whole cells whose CENTRE falls inside the basin, at the grid's nominal 2.5397 km
    spacing, over-counts by ~20 % — the design measured 1,544 cells = 9,961 km2 for a Skagit
    of 8,275 km2. Two errors compound: partial edge cells counted whole, and the Lambert scale
    factor ignored (a nominal 6.450 km2 cell is 5.39 km2 on the ground at 48 N).
    """
    shapely_geometry = pytest.importorskip("shapely.geometry")
    shapely_ops = pytest.importorskip("shapely.ops")
    polys, wbd, _source = polygons
    projection = LambertConformalConic(grid)
    parts = [
        shapely_geometry.Polygon(rings[0], rings[1:])
        for polygon in polys["basin:cedar"]
        for rings in [[[projection.to_grid(float(x), float(y)) for x, y, *_ in ring] for ring in polygon]]
    ]
    geometry = shapely_ops.unary_union([p.buffer(0) for p in parts])
    mask = masks["basin:cedar"]
    centres_inside = sum(1 for flat, _w in mask.cells if geometry.contains(shapely_geometry.Point(flat % grid.nx, flat // grid.nx)))
    naive_km2 = centres_inside * grid.dx_m * grid.dy_m / 1e6
    assert naive_km2 / wbd["basin:cedar"] > 1.15, "the naive estimate stopped over-counting; re-check the scale factor"
    assert abs(mask.masked_area_km2 - wbd["basin:cedar"]) / wbd["basin:cedar"] < 0.01


def test_a_basin_reaching_past_the_subset_edge_is_refused_not_partly_aggregated(grid: GridSpec, polygons) -> None:
    """The part outside the WA box was never fetched, so a mean over the part inside would be
    a mean of a different basin. The mask build refuses instead."""
    from dataclasses import replace

    polys, _wbd, source = polygons
    narrow = replace(grid, nx=20, ny=20, definition_hash="narrow")
    with pytest.raises(MaskError, match="basin_outside_grid"):
        build_basin_mask(basin_id="basin:skagit", polygons=polys["basin:skagit"], grid=narrow, polygon_source=source)


def test_weighted_mean_refuses_rather_than_averaging_what_is_present(masks, grid: GridSpec) -> None:
    mask = masks["basin:cedar"]
    values: list[float | None] = [1.0] * grid.size
    assert weighted_mean(values, mask, grid=grid).value == pytest.approx(1.0)
    values[mask.cells[0][0]] = None
    with pytest.raises(MaskError, match="missing_values"):
        weighted_mean(values, mask, grid=grid)
    with pytest.raises(MaskError, match="grid_size_mismatch"):
        weighted_mean([1.0] * (grid.size - 1), mask, grid=grid)


# --------------------------------------------------------------- 3. golden basin means

#: Golden basin means for the real 2026-08-24 12Z cycle, 0-72 h cumulative APCP, in mm.
#: Late August: the median is genuinely 0 mm, which is a value and not a missing number. The
#: upper percentiles are the discriminating goldens — they vary across the basin, so a wrong
#: projection, a display-LOD polygon or an off-by-one flat index all move them.
SKAGIT_GOLDEN = {50: 0.0, 75: 0.000809, 90: 0.030071, 95: 0.427208}
NOOKSACK_GOLDEN_P95 = 0.024077


def test_skagit_basin_mean_is_golden_to_a_hundredth_of_a_millimetre(qmd72: bytes, masks, grid: GridSpec) -> None:
    mask = masks["basin:skagit"]
    for percentile, expected in SKAGIT_GOLDEN.items():
        field = parser.one(parser.decode(qmd72, want=parser.cumulative_apcp(hours=72, percentile=percentile)), what=f"APCP 0-72 p{percentile}")
        out = basin_mean(field, mask, basin_id="basin:skagit")
        assert not isinstance(out, Refusal)
        assert out.value == pytest.approx(expected, abs=0.01)  # exit test §5.2
        assert out.value == pytest.approx(expected, abs=1e-6)  # and much tighter than that
        assert out.unit == "mm" and out.native_unit == "kg m**-2"
        assert out.feature == f"basin_qpf_72h_pointwise_p{percentile}"
        assert forcing.POINTWISE_FLAG in out.quality
    assert mask.cell_count == 1742 and mask.masked_area_km2 == pytest.approx(8250.57, abs=0.01)


def test_the_24_hour_horizon_is_its_own_file_with_its_own_window_and_valid_time(qmd24: bytes, masks) -> None:
    """One file per horizon, not one per forecast hour: f024 carries the 0-1 day cumulative
    window and nothing longer, and its valid time is the cycle plus 24 h."""
    keys = parser.scan(qmd24)
    assert len(keys) == 97
    assert parser.windows(keys, parameter=parser.APCP) == [(0, 24), (12, 24), (18, 24), (23, 24)]
    field = parser.one(parser.decode(qmd24, want=parser.cumulative_apcp(hours=24, percentile=100)), what="APCP 0-24 p100")
    assert field.valid_time == CYCLE.issued_at + timedelta(hours=24)
    out = basin_mean(field, masks["basin:skagit"], basin_id="basin:skagit")
    assert not isinstance(out, Refusal)
    assert out.value == pytest.approx(0.118617, abs=1e-6) and out.window_h == 24
    assert out.feature == "basin_qpf_24h_pointwise_p100"


def test_a_second_basin_is_golden_too_so_the_mask_is_not_accidentally_shared(qmd72: bytes, masks) -> None:
    field = parser.one(parser.decode(qmd72, want=parser.cumulative_apcp(hours=72, percentile=95)), what="APCP 0-72 p95")
    out = basin_mean(field, masks["basin:nooksack"], basin_id="basin:nooksack")
    assert not isinstance(out, Refusal) and out.value == pytest.approx(NOOKSACK_GOLDEN_P95, abs=1e-6)


def test_a_mask_from_another_grid_is_refused_not_applied(qmd72: bytes, masks) -> None:
    """Exit test §5.3, at the aggregation level: a wrong-grid mask yields a Refusal."""
    field = parser.one(parser.decode(qmd72, want=parser.cumulative_apcp(hours=72, percentile=50)), what="APCP 0-72 p50")
    from dataclasses import replace

    stale = replace(masks["basin:skagit"], grid_definition_hash="0" * 64)
    out = basin_mean(field, stale, basin_id="basin:skagit")
    assert isinstance(out, Refusal) and out.kind == "grid_definition_changed"


# ------------------------------------------------------------------- 4. the band table


def test_banding_is_monotone_reproducible_and_edge_exact() -> None:
    order = {SurfaceLevel.LOW: 0, SurfaceLevel.MODERATE: 1, SurfaceLevel.HIGH: 2, SurfaceLevel.VERY_HIGH: 3}
    previous_level, previous_score = -1, -1.0
    for tenths in range(0, 3000):
        value = tenths / 10.0
        level = order[forcing.FORCING_BANDS.level(value)]
        score = forcing.FORCING_BANDS.score(value)
        assert level >= previous_level and score >= previous_score - 1e-12
        assert 0.0 <= score <= 1.0
        previous_level, previous_score = level, score
    assert forcing.FORCING_BANDS.level(24.9) is SurfaceLevel.LOW
    assert forcing.FORCING_BANDS.level(25.0) is SurfaceLevel.MODERATE
    assert forcing.FORCING_BANDS.level(150.0) is SurfaceLevel.VERY_HIGH
    assert forcing.FORCING_BANDS.score(0.0) == 0.0 and forcing.FORCING_BANDS.score(200.0) == 1.0
    assert forcing.FORCING_BANDS.score(400.0) == 1.0  # capped, and still not a probability
    # The band edges are an ASSUMPTION and say so wherever they are explained.
    assert "ASSUMPTION" in forcing.FORCING_BANDS.assumption and "not a calibrated" in forcing.FORCING_BANDS.assumption


def test_feature_ids_say_pointwise_because_that_is_what_they_are() -> None:
    assert forcing.qpf_feature(72, 90) == "basin_qpf_72h_pointwise_p90"
    assert "pointwise" in forcing.qpf_label(72, 90)
    assert forcing.qpf_feature(72, None) == "basin_qpf_72h_deterministic"  # not "p50"
    assert forcing.snow_level_feature(50) == "basin_snow_level_pointwise_p50"


# ------------------------------------------------------------------------- 5. the jobs


@respx.mock
async def test_build_masks_stores_one_mask_per_basin_and_is_idempotent(sessions, tmp_path, core24: bytes) -> None:
    _mock_nomads(core_bytes=core24)
    async with sessions() as session:
        reports = await jobs.run_build_grid_masks(session, _fetcher(tmp_path), geo_dir=GEO, cycle=CYCLE)
        assert len(reports) == 6 and all(r.built for r in reports)
        again = await jobs.run_build_grid_masks(session, _fetcher(tmp_path), geo_dir=GEO, cycle=CYCLE)
        assert all(not r.built for r in again)
        rows = (await session.execute(select(GridMask))).scalars().all()
        assert len(rows) == 6
        assert {r.method_id for r in rows} == {"method:basin-grid-mask@1.0.0"}
        assert all(r.polygon_source.startswith("basins_seed_full.geojson.gz@") for r in rows)
        assert all(len(r.grid_definition_hash) == 64 for r in rows)


@respx.mock
async def test_qmd_ingest_writes_provenance_carrying_rows_and_re_running_writes_nothing(sessions, tmp_path, masks, qmd72: bytes) -> None:
    async with sessions() as session:
        await _install_masks(session, masks)
        _mock_nomads({72: qmd72})
        written = await jobs.run_fetch_qmd(session, _fetcher(tmp_path), cycle=CYCLE, horizons=(72,))
        assert written == 6 * 6  # six basins x (five percentiles + the deterministic field)
        assert await jobs.run_fetch_qmd(session, _fetcher(tmp_path), cycle=CYCLE, horizons=(72,)) == 0
        rows = (await session.execute(select(DerivedFeature).where(DerivedFeature.scope_id == "basin:skagit"))).scalars().all()
        by_feature = {r.feature: r for r in rows}
        headline = by_feature["basin_qpf_72h_pointwise_p50"]
        assert headline.window == "72h" and headline.unit == "mm"
        assert headline.issued_at == CYCLE.issued_at
        assert headline.valid_time == CYCLE.issued_at + timedelta(hours=72)
        assert headline.available_at == NOW  # knowledge time is when we fetched, not the cycle
        assert headline.method_id == forcing.METHOD_BASIN_QPF and headline.product_id == PRODUCT_NBM_QMD
        assert headline.percentile is None  # a model percentile level is not a climatological one
        assert headline.raw_artifact_id is not None and headline.raw_inputs_hash
        assert headline.values_json["cell_count"] == 1742
        assert forcing.POINTWISE_FLAG in headline.quality
        assert by_feature["basin_qpf_72h_deterministic"].quality == []


@respx.mock
async def test_the_raw_grib_is_archived_under_the_lifecycle_prefix_before_it_is_parsed(sessions, tmp_path, masks, qmd72: bytes) -> None:
    """The R2 rule `expire-nbm-90d` only expires objects under `nbm/`; if the key has no
    prefix the rule matches nothing and the archive grows ~400 MB/month forever."""
    from cascade_core.models import RawArtifact

    async with sessions() as session:
        await _install_masks(session, masks)
        _mock_nomads({72: qmd72})
        await jobs.run_fetch_qmd(session, _fetcher(tmp_path), cycle=CYCLE, horizons=(72,))
        artifact = (await session.execute(select(RawArtifact))).scalars().one()
        assert artifact.object_key.startswith("nbm/") and artifact.object_key.endswith(".grib2")
        assert artifact.retention_class == "gridded-90d"
        assert artifact.bytes == len(qmd72) and artifact.product_id == PRODUCT_NBM_QMD
        assert (tmp_path / artifact.object_key).read_bytes() == qmd72
        assert artifact.object_key == object_key_for(qmd72, ".grib2", "nbm/")


@respx.mock
async def test_snow_level_rows_are_stored_as_context_with_their_own_product(sessions, tmp_path, masks, core24: bytes) -> None:
    async with sessions() as session:
        await _install_masks(session, masks)
        _mock_nomads(core_bytes=core24)
        written = await jobs.run_fetch_core_snowlvl(session, _fetcher(tmp_path), cycle=CYCLE, horizons=(24,))
        assert written == 6 * 3  # six basins x p10/p50/p90
        row = (
            await session.execute(
                select(DerivedFeature).where(DerivedFeature.feature == "basin_snow_level_pointwise_p50", DerivedFeature.scope_id == "basin:skagit")
            )
        ).scalars().one()
        assert row.unit == "m" and row.window is None and row.product_id == PRODUCT_NBM_CORE
        assert row.valid_time == CYCLE.issued_at + timedelta(hours=24)
        assert row.method_id == forcing.METHOD_BASIN_SNOW_LEVEL  # not "basin-qpf" over a snow level
        assert parser.UNIT_FROM_DOCUMENTATION in row.quality and forcing.POINTWISE_FLAG in row.quality
        assert row.value is not None and 0.0 < row.value < 6000.0  # an elevation in metres MSL


@respx.mock
async def test_a_lead_time_without_percentiles_costs_that_lead_only_not_the_whole_cycle(
    sessions, tmp_path, masks, core24: bytes, qmd72: bytes
) -> None:
    """NBM `core` publishes SNOWLVL PERCENTILE levels through f048 and no further.

    Verified live 2026-08-24 on the 18Z core `.idx` sidecars: f024/f036/f042/f048 carry 16
    SNOWLVL records (15 percentiles + the deterministic field); f054/f060/f066/f072 carry the
    deterministic `SNOWLVL:0 m above mean sea level` record ALONE. The job used to raise on the
    first such lead, and because `run_job` discards the session on a raise, one structurally
    empty lead threw away the leads that HAD decoded — `nbm.fetch_core_snowlvl` failed on every
    real cycle and the snow-level context driver never existed in production. Here the qmd
    payload stands in for a percentile-less core file (it carries APCP and no SNOWLVL at all).
    """

    def handler(request: httpx.Request) -> httpx.Response:
        name = request.url.params["file"]
        body = qmd72 if ".f072." in name else core24
        return httpx.Response(200, content=body, headers={"content-type": "application/octet-stream"})

    respx.get(QMD_URL).mock(side_effect=handler)
    async with sessions() as session:
        await _install_masks(session, masks)
        written = await jobs.run_fetch_core_snowlvl(session, _fetcher(tmp_path), cycle=CYCLE, horizons=(24, 72))
        assert written == 6 * 3  # the f024 rows survive; f072 contributes nothing and costs nothing
        # ...but a cycle where NO requested lead carries a percentile is a real break, not a
        # quiet success that stored nothing.
        with pytest.raises(parser.NbmParseError):
            await jobs.run_fetch_core_snowlvl(session, _fetcher(tmp_path), cycle=CYCLE, horizons=(72,))


def test_the_snow_level_leads_stop_where_the_providers_percentiles_stop() -> None:
    assert client.CORE_HORIZONS_H == (24, 48)
    assert max(client.CORE_HORIZONS_H) <= 48  # f054+ carry the deterministic field only


# ------------------------------------------------------------------- 6. the assessment


@respx.mock
async def test_the_surface_is_banded_with_pointwise_named_spread_and_registry_kinds(sessions, tmp_path, masks, qmd72: bytes, core24: bytes) -> None:
    async with sessions() as session:
        await _install_masks(session, masks)
        _mock_nomads({72: qmd72}, core_bytes=core24)
        await jobs.run_fetch_qmd(session, _fetcher(tmp_path), cycle=CYCLE, horizons=(72,))
        await jobs.run_fetch_core_snowlvl(session, _fetcher(tmp_path), cycle=CYCLE, horizons=(24,))
        products = await _products(session)
        knowledge = as_known_at(session, NOW + timedelta(minutes=5))
        basin = await session.get(Basin, "basin:skagit")
        out = await forcing.assess(knowledge, basin, products, now=NOW + timedelta(minutes=5))

    surface = out.surface
    assert surface.state is SurfaceLevel.LOW and surface.reason is None
    assert surface.value is not None and surface.value.unit == "mm"
    assert surface.value.value == pytest.approx(SKAGIT_GOLDEN[50], abs=1e-6)
    assert surface.horizon_h == 72 and surface.experimental is True
    assert surface.truth is TruthClass.CASCADE_DERIVED
    # Capped at moderate while the spread is a pointwise percentile (design §1.4).
    assert surface.confidence.value == "moderate"
    assert set(surface.spread or {}) == {"pointwise_p10", "pointwise_p90"}, "spread keys must not claim a basin-scale percentile"
    assert surface.score is not None and 0.0 <= surface.score <= 1.0

    # Exit test §5.4: kinds come from the registry, and the assessment is EXPERIMENTAL.
    assert out.refs[surface.prov].source_kind is SourceKind.EXPERIMENTAL
    assert out.refs[surface.prov].source_id == SRC_CASCADE
    assert out.refs[surface.prov].method_id == forcing.METHOD_FORCING_ASSESSMENT
    qpf_ref = out.refs[forcing.qpf_ref_key("basin:skagit")]
    assert qpf_ref.source_kind is SourceKind.MODELED and qpf_ref.source_id == SRC_NBM
    assert qpf_ref.product_id == PRODUCT_NBM_QMD and qpf_ref.method_id == forcing.METHOD_BASIN_QPF
    assert "pointwise" in qpf_ref.label
    assert all(ref.source_kind is not SourceKind.OFFICIAL_FORECAST for ref in out.refs.values())

    features = [d.feature for d in out.drivers]
    assert features[0] == "basin_qpf_72h_pointwise_p50"
    assert "basin_qpf_72h_pointwise_p90" in features and "basin_qpf_72h_pointwise_p10" in features
    snow = next(d for d in out.drivers if d.feature.startswith("basin_snow_level"))
    # HYDROLOGY snow doctrine: snow is context. Nothing here scores it in either direction.
    assert snow.direction == forcing.DIRECTION_CONTEXT and snow.unit == "m"
    assert {d.direction for d in out.drivers} <= {forcing.DIRECTION_INCREASES, forcing.DIRECTION_DECREASES, forcing.DIRECTION_CONTEXT}
    assert [d.rank for d in out.drivers] == sorted(d.rank for d in out.drivers)
    assert all(d.prov in out.refs for d in out.drivers)

    _envelope_validates(out)


def _envelope_validates(out: forcing.ForcingAssessment) -> None:
    """The contract validator fails on any provenance key a driver or surface cannot resolve."""
    unknown = SurfaceState(state=SurfaceLevel.UNKNOWN, prov="x", truth=TruthClass.CASCADE_DERIVED, reason="not this test")
    envelope = ContractEnvelope(
        contract="BasinVisualizationState",
        generated_at=NOW,
        as_of=NOW,
        time=TimeContext(valid=NOW, mode="now"),
        items=(
            BasinVisualizationState(
                id="basin:skagit",
                name="Skagit",
                regulation_class="regulated_upper",
                surfaces=BasinSurfaces(
                    susceptibility=unknown,
                    forcing=out.surface,
                    hazard=HazardState(horizon_h=72, official_category=FloodCategory.UNKNOWN, prov="x", truth=TruthClass.AUTHORITATIVE_MODEL),
                    agreement=AgreementState(state=AgreementLevel.UNKNOWN, prov=()),
                ),
                headline_drivers=out.drivers,
                geometry_ref=GeometryRef(lod="basin", feature_id="basin:skagit"),
            ),
        ),
        provenance_refs={
            **out.refs,
            "x": ProvenanceRef(source_id=SRC_CASCADE, source_kind=SourceKind.UNKNOWN, freshness=out.refs[out.surface.prov].freshness, label="placeholder"),
        },
    )
    assert envelope.items[0].surfaces.forcing.state is out.surface.state


@respx.mock
async def test_a_stale_cycle_keeps_the_value_but_drops_the_confidence(sessions, tmp_path, masks, qmd72: bytes) -> None:
    """A 12Z cycle read a day later is still the real forecast; it is just old, and the badge
    has to say so instead of the grace window hiding it (design §1.1, §1.5)."""
    async with sessions() as session:
        await _install_masks(session, masks)
        _mock_nomads({72: qmd72})
        await jobs.run_fetch_qmd(session, _fetcher(tmp_path), cycle=CYCLE, horizons=(72,))
        products = await _products(session)
        basin = await session.get(Basin, "basin:skagit")
        late = CYCLE.issued_at + timedelta(hours=24)  # past cadence (12 h) + grace (9 h)
        out = await forcing.assess(as_known_at(session, late), basin, products, now=late)
    assert out.surface.state is SurfaceLevel.LOW and out.surface.value is not None
    assert out.surface.confidence.value == "low"
    assert out.refs[out.surface.prov].freshness.state.value in ("stale", "degraded")


@respx.mock
async def test_a_grid_change_makes_the_job_refuse_and_the_surface_say_so(sessions, tmp_path, masks, qmd72: bytes) -> None:
    """Exit test §5.3: the mask misses, the number is refused, the reason is specific."""
    from dataclasses import replace

    async with sessions() as session:
        await _install_masks(session, {bid: replace(m, grid_definition_hash="f" * 64) for bid, m in masks.items()})
        _mock_nomads({72: qmd72})
        written = await jobs.run_fetch_qmd(session, _fetcher(tmp_path), cycle=CYCLE, horizons=(72,))
        assert written == 6  # one refusal row per basin, and no fabricated means
        rows = (await session.execute(select(DerivedFeature))).scalars().all()
        assert all(r.value is None for r in rows)
        assert all(forcing.GRID_CHANGED_FLAG in r.quality for r in rows)
        products = await _products(session)
        knowledge = as_known_at(session, NOW + timedelta(minutes=5))
        basin = await session.get(Basin, "basin:skagit")
        out = await forcing.assess(knowledge, basin, products, now=NOW + timedelta(minutes=5))
    assert out.surface.state is SurfaceLevel.UNKNOWN
    assert out.surface.value is None and out.surface.score is None and out.drivers == ()
    assert "grid definition changed" in (out.surface.reason or "").lower()
    assert "refused" in (out.surface.reason or "")
    assert out.surface.reason in out.refs[out.surface.prov].label  # the popover says it too


@respx.mock
async def test_a_knowledge_time_before_ingestion_is_unknown_with_the_no_cycle_reason(sessions, tmp_path, masks, qmd72: bytes) -> None:
    """Exit test §5.5, the same knowledge-time boundary P1 proved for observations."""
    async with sessions() as session:
        await _install_masks(session, masks)
        _mock_nomads({72: qmd72})
        await jobs.run_fetch_qmd(session, _fetcher(tmp_path), cycle=CYCLE, horizons=(72,))
        products = await _products(session)
        basin = await session.get(Basin, "basin:skagit")
        before = NOW - timedelta(hours=1)
        out = await forcing.assess(as_known_at(session, before), basin, products, now=before)
        assert out.surface.state is SurfaceLevel.UNKNOWN
        assert out.surface.reason == forcing.ForcingReason.NO_CYCLE
        assert out.refs[out.surface.prov].source_kind is SourceKind.EXPERIMENTAL

        # ... and a cycle older than the read window is not silently presented as current.
        stale = NOW + forcing.MAX_CYCLE_AGE + timedelta(days=1)
        out = await forcing.assess(as_known_at(session, stale), basin, products, now=stale)
        assert out.surface.state is SurfaceLevel.UNKNOWN and out.surface.reason == forcing.ForcingReason.NO_CYCLE


async def test_an_empty_store_is_unknown_for_every_basin(sessions) -> None:
    async with sessions() as session:
        products = await _products(session)
        for basin in (await session.execute(select(Basin))).scalars().all():
            out = await forcing.assess(as_known_at(session, NOW), basin, products, now=NOW)
            assert out.surface.state is SurfaceLevel.UNKNOWN and out.surface.reason == forcing.ForcingReason.NO_CYCLE
            assert out.surface.experimental is True and out.drivers == ()


# ----------------------------------------------------------------------- 7. the client


def test_the_request_is_the_url_the_design_verified() -> None:
    params = client.subset_url_params(kind="qmd", cycle=CYCLE, fhour=72, variable="APCP", region=client.WA_BASINS)
    url = str(httpx.URL(client.BASE_URL, params=params))
    assert "dir=%2Fblend.20260824%2F12%2Fqmd" in url  # the CGI requires the encoded slash
    assert "file=blend.t12z.qmd.f072.co.grib2" in url and "var_APCP=on" in url
    assert "subregion=&toplat=49.40&leftlon=-122.90&rightlon=-120.55&bottomlat=46.70" in url
    with pytest.raises(ValueError):
        client.subset_url_params(kind="qmd", cycle=CYCLE, fhour=72, variable="../etc", region=client.WA_BASINS)


def test_the_latest_cycle_respects_the_measured_qmd_latency() -> None:
    """Latency AND the main-cycle rule: 06Z/18Z are never selected at all.

    They publish `0-1 day` acc only — no `0-2`/`0-3 day` window — so a subset from them cannot
    contain the field the 72-hour basin QPF is defined on (measured live 2026-08-25; see
    `client.QMD_CYCLE_HOURS`).
    """
    # qmd f072 landed at cycle + 7 h 20 m; at 18:00Z the 12Z cycle is not there yet, and 06Z is
    # not a candidate at all, so the newest usable cycle is 00Z.
    assert str(client.latest_qmd_cycle(datetime(2026, 8, 24, 18, 0, tzinfo=UTC))) == "20260824T00Z"
    assert str(client.latest_qmd_cycle(datetime(2026, 8, 24, 20, 0, tzinfo=UTC))) == "20260824T12Z"
    assert client.latest_qmd_cycle(NOW).issued_at == CYCLE.issued_at


def test_the_seed_geometry_the_masks_are_built_from_is_the_full_resolution_one() -> None:
    """A guard on the input, not the output: this file is 6 features at full WBD resolution."""
    doc = json.loads(gzip.decompress((GEO / jobs.BASIN_GEOMETRY_FILE).read_bytes()))
    assert len(doc["features"]) == 6
    vertices = sum(
        len(ring)
        for feature in doc["features"]
        for polygon in __import__("cascade_geo").polygons_of(feature["geometry"])
        for ring in polygon
    )
    assert vertices > 100_000, "the full-resolution geometry lost detail; masks would over-count"


# --------------------------------------------------------------------------------------
# the provider publishes the cumulative windows on the MAIN cycles only
# --------------------------------------------------------------------------------------
def test_qmd_is_only_asked_of_cycles_that_publish_the_cumulative_window() -> None:
    """00Z/12Z carry `0-1/0-2/0-3 day` acc; 06Z/18Z carry `0-1 day` only.

    Measured live 2026-08-25 over six cycles x three leads. Production found this by failing on
    an 18Z cycle with "qmd f048 carries no 0-48 h APCP field" — the same class of error as asking
    `core` f072 for a SNOWLVL percentile it does not publish. The fix is the same: never ask a
    cycle for a field it cannot contain, and never sum per-day quantiles into a total (the p90 of
    a three-day total is not the sum of three daily p90s).
    """
    from datetime import UTC, datetime

    from cascade_providers_nbm.client import QMD_CYCLE_HOURS, latest_qmd_cycle

    assert QMD_CYCLE_HOURS == (0, 12)
    # every hour of the day selects a main cycle, never an intermediate one
    for hour in range(24):
        chosen = latest_qmd_cycle(datetime(2026, 8, 25, hour, 30, tzinfo=UTC))
        assert chosen.hour in QMD_CYCLE_HOURS, f"{hour:02d}Z selected {chosen}"
    # and it is a real cycle in the past, never a future one
    now = datetime(2026, 8, 25, 14, 0, tzinfo=UTC)
    assert latest_qmd_cycle(now).hour == 0  # 12Z has not landed by 14:00Z (7.5 h latency)
