"""P3 Stage 0 foundation: derived_feature/grid_mask, the knowledge-time reader for them, the
registry ids the surfaces resolve provenance through, per-call Accept + host ceiling on the
fetcher, the contract 1.2.0 additions, and the seed addendum.

Offline: SQLite + respx only, no network (docs/TESTING.md).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import pytest
import respx
from sqlalchemy import select

from cascade_contracts import ContractEnvelope, SourceKind, TruthClass
from cascade_contracts.common import CONTRACT_VERSION
from cascade_contracts.visualization import SurfaceLevel, SurfaceState
from cascade_core.db import create_schema, make_engine, make_session_factory
from cascade_core.fetch import PROVIDER_HOSTS, ArchivingFetcher, FetchError
from cascade_core.knowledge import as_known_at
from cascade_core.models import Basin, DerivedFeature, ForecastPoint, GridMask, RawArtifact, Station
from cascade_core.objectstore import LocalFilesystemStore
from cascade_core.registry import (
    PRODUCT_AWDB_DAILY,
    PRODUCT_NBM_CORE,
    PRODUCT_NBM_QMD,
    PRODUCT_NWM_MR,
    PRODUCT_USGS_DAILY_STATS,
    PRODUCT_USGS_OGC_DAILY,
    PRODUCTS,
    SOURCES,
    SRC_NBM,
    SRC_NWM,
)
from cascade_core.seed import PACIFIC_TIME_ZONE, SEEDABLE_TIME_ZONES, load_addenda, seed_all
from cascade_core.settings import SEED_FILE
from tests.conftest import GEO

NOW = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)


@pytest.fixture
async def sessions(tmp_path):
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path}/p3.db")
    await create_schema(engine)
    factory = make_session_factory(engine)
    async with factory() as session:
        await seed_all(session, geo_dir=GEO, seed_file=SEED_FILE)
    yield factory
    await engine.dispose()


async def _artifact(session, product_id: str, *, retention_class: str | None = None) -> RawArtifact:
    art = RawArtifact(
        sha256="a" * 64, object_key="test/p3", product_id=product_id, fetched_at=NOW,
        request_url="https://example.invalid/p3", bytes=1, http_status=200,
        content_type="application/json", retention_class=retention_class,
    )
    session.add(art)
    await session.flush()
    return art


def _feature(**kw) -> DerivedFeature:
    base = dict(
        feature="basin_qpf_72h_p50", scope_kind="basin", scope_id="basin:skagit", window="72h",
        valid_time=NOW, issued_at=None, computed_at=NOW, available_at=NOW,
        method_id="method:basin-qpf@1.0.0", product_id=None, value=1.0, unit="mm",
        percentile=None, climatology_ref=None, confidence_label="moderate", quality=[], inputs=[],
    )
    base.update(kw)
    return DerivedFeature(**base)


# --- schema -----------------------------------------------------------------------------


async def test_derived_feature_round_trips_with_its_provenance(sessions) -> None:
    async with sessions() as s:
        art = await _artifact(s, PRODUCT_NBM_QMD, retention_class="gridded-90d")
        s.add(
            _feature(
                issued_at=NOW - timedelta(hours=7), valid_time=NOW + timedelta(hours=72),
                value=142.0, product_id=PRODUCT_NBM_QMD, raw_artifact_id=art.id,
                values_json={"p10": 88.0, "p50": 142.0, "p90": 211.0},
                inputs=[{"table": "raw_artifact", "id": art.id}],
                raw_inputs_hash="b" * 64, quality=["pointwise_percentile_not_basin_percentile"],
            )
        )
        await s.commit()
    async with sessions() as s:
        row = (await s.execute(select(DerivedFeature))).scalar_one()
        assert row.product_id == PRODUCT_NBM_QMD and row.raw_artifact_id is not None
        assert row.values_json == {"p10": 88.0, "p50": 142.0, "p90": 211.0}
        assert row.inputs[0]["table"] == "raw_artifact"
        assert row.valid_time == NOW + timedelta(hours=72) and row.valid_time.tzinfo is not None
        art = await s.get(RawArtifact, row.raw_artifact_id)
        # The row outlives the bytes: a 90-day lifecycle rule may expire the grid, and
        # provenance must be able to say so rather than 404 (DATA_DOCTRINE §13).
        assert art.retention_class == "gridded-90d"


async def test_grid_mask_is_keyed_by_grid_definition_so_a_grid_change_misses(sessions) -> None:
    async with sessions() as s:
        s.add(
            GridMask(
                basin_id="basin:skagit", grid_definition_hash="c" * 64,
                method_id="method:basin-grid-mask@1.0.0", cells=[[0, 0.5], [1, 1.0]],
                cell_count=2, masked_area_km2=8213.0,
                polygon_source="basins_seed_full.geojson.gz@deadbeef", computed_at=NOW,
            )
        )
        await s.commit()
    async with sessions() as s:
        assert await s.get(GridMask, ("basin:skagit", "c" * 64)) is not None
        # A silently changed provider grid must MISS the mask, never reuse it.
        assert await s.get(GridMask, ("basin:skagit", "d" * 64)) is None


# --- knowledge-time reader --------------------------------------------------------------


async def test_derived_features_are_knowledge_filtered_but_valid_time_is_not_clamped(sessions) -> None:
    async with sessions() as s:
        s.add_all(
            [
                _feature(valid_time=NOW + timedelta(hours=72), value=142.0),  # forecast: future
                _feature(valid_time=NOW + timedelta(hours=48), value=90.0, window="48h"),
                _feature(valid_time=NOW + timedelta(hours=72), value=999.0,
                         issued_at=NOW, available_at=NOW + timedelta(hours=1)),  # not yet known
            ]
        )
        await s.commit()
    async with sessions() as s:
        k = as_known_at(s, NOW)
        rows = await k.derived_features("basin_qpf_72h_p50", "basin:skagit", window="72h")
        assert [r.value for r in rows] == [142.0], "a row available_at > T must be invisible"
        later = await as_known_at(s, NOW + timedelta(hours=2)).derived_features(
            "basin_qpf_72h_p50", "basin:skagit", window="72h"
        )
        assert [r.value for r in later] == [142.0, 999.0]
        assert len(await k.derived_features("basin_qpf_72h_p50", "basin:skagit")) == 2  # both windows


async def test_latest_per_valid_time_keeps_the_recomputation_and_lookback_bounds_staleness(sessions) -> None:
    async with sessions() as s:
        s.add_all(
            [
                _feature(feature="streamflow_doy_percentile", window=None, valid_time=NOW - timedelta(days=1),
                         value=40.0, available_at=NOW - timedelta(days=1)),
                _feature(feature="streamflow_doy_percentile", window=None, valid_time=NOW - timedelta(days=1),
                         value=44.0, available_at=NOW - timedelta(hours=2)),  # recomputed, append-only
                _feature(feature="streamflow_doy_percentile", window=None, valid_time=NOW - timedelta(days=90),
                         value=10.0, available_at=NOW - timedelta(days=90)),
            ]
        )
        await s.commit()
    async with sessions() as s:
        k = as_known_at(s, NOW)
        rows = await k.derived_features("streamflow_doy_percentile", "basin:skagit", latest_per_valid_time=True)
        assert [r.value for r in rows] == [10.0, 44.0], "the later write for a valid_time wins"
        latest = await k.latest_derived_feature("streamflow_doy_percentile", "basin:skagit")
        assert latest is not None and latest.value == 44.0
        stale = await k.latest_derived_feature(
            "streamflow_doy_percentile", "basin:skagit", lookback=timedelta(hours=6)
        )
        assert stale is None, "outside the lookback the caller must get None, not an old value"


# --- registry ---------------------------------------------------------------------------


def test_every_product_resolves_to_a_registered_source() -> None:
    kinds = {s["id"]: s["kind"] for s in SOURCES}
    for product in PRODUCTS:
        assert product["source_id"] in kinds, product["id"]


def test_no_model_source_may_be_badged_official(): 
    """DATA_DOCTRINE §2: NBM and NWM are MODELED. Nothing may resolve them to OFFICIAL_FORECAST."""
    kinds = {s["id"]: s["kind"] for s in SOURCES}
    for src in (SRC_NBM, SRC_NWM):
        assert kinds[src] == SourceKind.MODELED.value
    by_id = {p["id"]: p for p in PRODUCTS}
    for product_id in (PRODUCT_NBM_QMD, PRODUCT_NBM_CORE, PRODUCT_NWM_MR):
        assert kinds[by_id[product_id]["source_id"]] != SourceKind.OFFICIAL_FORECAST.value


def test_p3_product_cadences_match_the_measured_design_values() -> None:
    """Cadence describes how often the STORED anchor refreshes, not how often NOAA publishes.

    `product:nbm-v5-core` was pinned at PT1H here because NBM `core` is published hourly. But
    `nbm.fetch_core_snowlvl` runs 6-hourly and takes its cycle 7.5 h in arrears
    (`client.latest_qmd_cycle`), so the anchor Cascade stores is 7.5–13.5 h old at all times and
    the product was STALE on every cycle: measured live 2026-08-25 on a fresh database with every
    job green, `/system/health` answered `degraded` naming this product alone, 47,760 s against a
    3,600 s cadence (pg-migration-verification-2026-08-24 §P3.9). It now matches qmd, which the
    same job cadence and the same cycle selector make the right comparison.
    """
    by_id = {p["id"]: p for p in PRODUCTS}
    # qmd is 12-hourly, not 6: measured live 2026-08-25, only the 00Z/12Z cycles publish the
    # 0-2/0-3 day cumulative windows (06Z/18Z carry 0-1 day alone), so a 6-hourly cadence
    # would call the surface late every other cycle for a file that was never coming.
    assert (by_id[PRODUCT_NBM_QMD]["expected_cadence_seconds"], by_id[PRODUCT_NBM_QMD]["grace_seconds"]) == (43200, 32400)
    assert (by_id[PRODUCT_NBM_CORE]["expected_cadence_seconds"], by_id[PRODUCT_NBM_CORE]["grace_seconds"]) == (21600, 28800)
    assert (by_id[PRODUCT_NWM_MR]["expected_cadence_seconds"], by_id[PRODUCT_NWM_MR]["grace_seconds"]) == (21600, 43200)  # grace covers the ~6.5 h publication latency; 8 h made stale unreachable
    assert by_id[PRODUCT_USGS_OGC_DAILY]["expected_cadence_seconds"] == 86400
    assert by_id[PRODUCT_AWDB_DAILY]["expected_cadence_seconds"] == 86400
    assert by_id[PRODUCT_USGS_DAILY_STATS]["expected_cadence_seconds"] == 31536000


async def test_registry_products_are_seeded_so_freshness_can_be_computed(sessions) -> None:
    from cascade_core.models import SourceProduct

    async with sessions() as s:
        stored = {p.id for p in (await s.execute(select(SourceProduct))).scalars()}
    assert {PRODUCT_NBM_QMD, PRODUCT_NBM_CORE, PRODUCT_NWM_MR, PRODUCT_USGS_OGC_DAILY,
            PRODUCT_USGS_DAILY_STATS, PRODUCT_AWDB_DAILY} <= stored


# --- fetcher ----------------------------------------------------------------------------


class _FakeSession:
    def __init__(self) -> None:
        self.added: list[RawArtifact] = []

    def add(self, obj) -> None:
        self.added.append(obj)

    async def flush(self) -> None:
        for i, obj in enumerate(self.added, start=1):
            obj.id = i


def test_p3_hosts_are_registered_in_the_ceiling() -> None:
    assert {"nomads.ncep.noaa.gov", "noaa-nbm-grib2-pds.s3.amazonaws.com", "wcc.sc.egov.usda.gov"} <= PROVIDER_HOSTS


@respx.mock
async def test_fetch_refuses_a_host_outside_the_registered_ceiling(tmp_path) -> None:
    fetcher = ArchivingFetcher(store=LocalFilesystemStore(tmp_path), user_agent="t", clock=lambda: NOW)
    with pytest.raises(FetchError, match="unregistered_host"):
        await fetcher.fetch(
            _FakeSession(), url="https://grib.example/x", params=None,
            allowed_hosts=frozenset({"grib.example"}), product_id=PRODUCT_NBM_QMD,
        )


@respx.mock
async def test_accept_header_is_per_call_and_retention_class_is_recorded(tmp_path) -> None:
    route = respx.get("https://nomads.ncep.noaa.gov/cgi-bin/filter_blend.pl").mock(
        return_value=httpx.Response(200, content=b"GRIB\x00\x007777", headers={"content-type": "application/octet-stream"})
    )
    fetcher = ArchivingFetcher(store=LocalFilesystemStore(tmp_path), user_agent="t", clock=lambda: NOW)
    session = _FakeSession()
    result = await fetcher.fetch(
        session, url="https://nomads.ncep.noaa.gov/cgi-bin/filter_blend.pl", params={"var_APCP": "on"},
        allowed_hosts=frozenset({"nomads.ncep.noaa.gov"}), product_id=PRODUCT_NBM_QMD,
        suffix=".grib2", accept="application/octet-stream", retention_class="gridded-90d",
    )
    assert route.calls.last.request.headers["accept"] == "application/octet-stream"
    assert result.content.startswith(b"GRIB") and result.object_key.endswith(".grib2")
    assert session.added[0].retention_class == "gridded-90d"


@respx.mock
async def test_accept_still_defaults_to_json(tmp_path) -> None:
    route = respx.get("https://api.water.noaa.gov/nwps/v1/reaches/24270288").mock(
        return_value=httpx.Response(200, content=b"{}", headers={"content-type": "application/json"})
    )
    fetcher = ArchivingFetcher(store=LocalFilesystemStore(tmp_path), user_agent="t", clock=lambda: NOW)
    await fetcher.fetch(
        _FakeSession(), url="https://api.water.noaa.gov/nwps/v1/reaches/24270288", params=None,
        allowed_hosts=frozenset({"api.water.noaa.gov"}), product_id=PRODUCT_NWM_MR,
    )
    assert route.calls.last.request.headers["accept"] == "application/json"
    assert route.calls.last.request.headers["user-agent"] == "t"


# --- contracts 1.3.0 --------------------------------------------------------------------


def test_contract_version_is_1_3_0_and_the_additions_are_optional() -> None:
    assert CONTRACT_VERSION == "1.3.0"
    # A 1.1.0-shaped payload (no value, no spread) must keep validating: the bump is additive.
    old = SurfaceState(prov="p", truth=TruthClass.CASCADE_DERIVED, state=SurfaceLevel.UNKNOWN, reason="no cycle")
    assert old.value is None and old.spread is None


def test_the_tail_and_the_velocity_are_additive_and_never_inside_the_surface() -> None:
    """1.3.0: a 1.2.0 basin item keeps validating, and the new fields hang BESIDE the surfaces.

    Putting the high-tail level or the state change inside `SurfaceState` would have made them
    look like inputs to the band. They are not: `SurfaceState.score` is still the percentile and
    nothing else, and the contract keeps them in separate objects so no client can fuse them.
    """
    from cascade_contracts import BandBoundary, HydrologicState, StateChange
    from cascade_contracts.visualization import BasinVisualizationState

    assert "hydrologic_state" not in SurfaceState.model_fields
    assert "state_change" not in SurfaceState.model_fields
    fields = BasinVisualizationState.model_fields
    assert fields["hydrologic_state"].default is None and fields["state_change"].default == ()

    # the boundary condition fails closed: its default is the one that says "cannot be answered"
    state = HydrologicState(
        prov="p", truth=TruthClass.CASCADE_DERIVED,
        observed={"value": 72440.0, "unit": "cfs"}, day="2025-12-11",
    )
    assert state.boundary is BandBoundary.UNQUANTIFIED
    assert state.rank is None and state.multiple is None and state.bands_within_sampling_error == ()

    # a growth is a positive multiple or absent; zero and negative are not rates
    with pytest.raises(ValueError):
        StateChange(window_h=24, growth=0.0, direction="rising", prov="p")
    with pytest.raises(ValueError):
        StateChange(window_h=24, growth=1.5, direction="accelerating", prov="p")


def test_surface_state_carries_the_headline_value_and_its_spread() -> None:
    s = SurfaceState(
        prov="nbm-forcing-skagit", truth=TruthClass.CASCADE_DERIVED, state=SurfaceLevel.HIGH,
        horizon_h=72, score=0.71, value={"value": 142.0, "unit": "mm"},
        spread={"p10": 88.0, "p90": 211.0}, confidence="moderate", experimental=True,
    )
    assert s.value.value == 142.0 and s.value.unit == "mm" and s.value.datum is None
    assert s.spread == {"p10": 88.0, "p90": 211.0}
    # The doctrine is carried in the schema itself, so a generated client sees it.
    schema = SurfaceState.model_json_schema()
    for field in ("value", "spread", "score"):
        assert "never a probability" in schema["properties"][field]["description"].lower(), field


def test_score_is_still_bounded_and_never_takes_a_probability_like_excursion() -> None:
    with pytest.raises(ValueError):
        SurfaceState(prov="p", truth=TruthClass.CASCADE_DERIVED, state=SurfaceLevel.HIGH, score=1.4)


def test_shipped_envelope_fixtures_still_validate_under_1_2_0() -> None:
    from pathlib import Path

    fixtures = Path(__file__).resolve().parents[2] / "packages" / "contracts" / "fixtures"
    for path in sorted(fixtures.glob("*_envelope.json")):
        ContractEnvelope.model_validate_json(path.read_text())


# --- seed -------------------------------------------------------------------------------


async def test_every_forecast_point_has_the_reach_id_agreement_needs(sessions) -> None:
    async with sessions() as s:
        points = {p.lid: p.reach_id for p in (await s.execute(select(ForecastPoint))).scalars()}
    assert points == {
        "RNTW1": "reach:nwm:24537890",
        "CRNW1": "reach:nwm:23970199",
        "MVEW1": "reach:nwm:24270288",
        "NKSW1": "reach:nwm:23955772",
        "AUBW1": "reach:nwm:23977634",
        "WRAW1": "reach:nwm:23981235",
    }


async def test_susceptibility_gauges_are_configured_with_their_ceilings(sessions) -> None:
    async with sessions() as s:
        basins = {b.id: b for b in (await s.execute(select(Basin))).scalars()}
        sauk = await s.get(Station, "station:usgs:12189500")
    # The Skagit is read at the unregulated Sauk, not at its regulated outlet (HYDROLOGY §2).
    assert basins["basin:skagit"].susceptibility_gauge_id == "station:usgs:12189500"
    assert sauk is not None and sauk.basin_id == "basin:skagit" and sauk.vertical_datum is None
    # Regulated basins may never claim more than low confidence: below the dam the percentile
    # partly measures reservoir operations, not basin wetness (design §2.3).
    assert basins["basin:green-duwamish"].susceptibility_confidence_ceiling == "low"
    assert basins["basin:puyallup-white"].susceptibility_confidence_ceiling == "low"
    assert basins["basin:skagit"].susceptibility_confidence_ceiling == "moderate"
    assert basins["basin:nooksack"].susceptibility_confidence_ceiling == "moderate"  # tidal, design §7
    for basin in basins.values():
        assert basin.susceptibility_gauge_id and basin.susceptibility_note, basin.id


def test_addendum_gauges_all_name_a_real_station() -> None:
    addenda = load_addenda(SEED_FILE)
    seed = json.loads(SEED_FILE.read_text())
    known = {fp["station_id"] for fp in seed["forecast_points"]} | {st["id"] for st in addenda["stations"]}
    for basin_id, cfg in addenda["basin_susceptibility_gauges"].items():
        assert cfg["gauge_station_id"] in known, basin_id
        assert cfg["confidence_ceiling"] in {"high", "moderate", "low", "unknown"}, basin_id


async def test_a_legacy_time_zone_alias_is_refused_at_seed_time(tmp_path) -> None:
    """`PST8PDT` names Pacific time and a laptop resolves it. The deployment image does not.

    `python:3.14-slim` ships tzdata without tzdata-legacy, so the alias raises there while the
    canonical `America/Los_Angeles` resolves. Seeding the alias therefore stamped every daily mean
    at UTC midnight in production — flagged `day_boundary_assumed_utc`, honest, and silent enough
    that every basin's 24 h `state_change` published `growth: null` for three days before anyone
    read the flag
    (ADR-0017). The seed refuses the alias outright now, on a check that does not consult the
    running host's tz database, so the refusal is the same on a laptop and in the container.
    """
    seed = json.loads(SEED_FILE.read_text())
    (tmp_path / "stations.json").write_text(json.dumps(seed))
    addendum = json.loads((SEED_FILE.parent / "p3_surfaces.json").read_text())
    addendum["stations"][0]["time_zone"] = "PST8PDT"
    (tmp_path / "p3_surfaces.json").write_text(json.dumps(addendum))
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path}/tz.db")
    await create_schema(engine)
    factory = make_session_factory(engine)
    try:
        async with factory() as session:
            with pytest.raises(ValueError, match="SEEDABLE_TIME_ZONES"):
                await seed_all(session, geo_dir=GEO, seed_file=tmp_path / "stations.json")
    finally:
        await engine.dispose()


#: The directories a geographic IANA zone lives under. `python:3.14-slim` ships exactly these plus
#: `Etc`, which holds fixed-offset zones that can never be a station's civil time. Anything outside
#: this set — bare POSIX names (`PST8PDT`), country prefixes (`US/Pacific`), `Etc/*` — is either
#: absent from that image or wrong for a gauge.
_IANA_AREAS = frozenset(
    {"Africa", "America", "Antarctica", "Arctic", "Asia", "Atlantic", "Australia", "Europe", "Indian", "Pacific"}
)


def test_every_seedable_time_zone_resolves_and_is_not_a_legacy_alias() -> None:
    """The allowlist is only worth anything if every entry in it actually resolves.

    The membership check in `_validate_time_zones` is runtime-independent by design; this is the
    other half — the entries themselves must be real, geographic, canonical zones.

    The area check is the load-bearing one, and a bare `"/" in zone` is NOT enough: `US/Pacific`
    contains a slash and resolves on a developer laptop, while `python:3.14-slim` cannot resolve it
    at all. Testing only the slash would let exactly the kind of key this ADR exists to keep out
    pass CI and then degrade in production — the same shape of hole as the original defect.
    """
    assert SEEDABLE_TIME_ZONES, "anti-vacuity: an empty allowlist would permit nothing and prove nothing"
    for zone in SEEDABLE_TIME_ZONES:
        area, _, location = zone.partition("/")
        assert location, f"{zone!r} is not an Area/Location IANA name"
        assert area in _IANA_AREAS, (
            f"{zone!r} is not under a geographic IANA area {sorted(_IANA_AREAS)}; legacy prefixes "
            "such as 'US/' are absent from the deployment image's tz database"
        )
        ZoneInfo(zone)  # raises ZoneInfoNotFoundError if this runtime cannot resolve it
    assert PACIFIC_TIME_ZONE in SEEDABLE_TIME_ZONES


async def test_a_mistyped_addendum_key_raises_instead_of_seeding_nothing(tmp_path) -> None:
    seed = json.loads(SEED_FILE.read_text())
    (tmp_path / "stations.json").write_text(json.dumps(seed))
    (tmp_path / "p3_surfaces.json").write_text(
        json.dumps({"basin_susceptibility_gauges": {"basin:typo": {"gauge_station_id": "station:usgs:12189500", "confidence_ceiling": "low", "note": "x"}}})
    )
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path}/typo.db")
    await create_schema(engine)
    factory = make_session_factory(engine)
    try:
        async with factory() as session:
            with pytest.raises(ValueError, match="unknown basins"):
                await seed_all(session, geo_dir=GEO, seed_file=tmp_path / "stations.json")
    finally:
        await engine.dispose()


# --- migration 0004: the seeded time-zone correction, offline scope guard -------------------


def test_the_time_zone_migration_touches_only_that_one_column() -> None:
    """0004 corrects seeded data on the path the deployment already runs (ADR-0017).

    Offline half of `tests/integration/test_tz_data_migration_pg.py`, which proves the behaviour
    against a real database. This one guards the SHAPE, because the danger with a data migration
    is not that it fails — it is that someone later widens it. A migration that swept a second
    column, or dropped the `WHERE`, would move hydrologic values on every deployment and no
    schema test would notice.

    It also pins the two literals. They are deliberately duplicated from `cascade_core.seed`
    rather than imported: a migration records a database state and must keep meaning the same
    thing after the application constant moves on.
    """
    import re

    root = Path(__file__).resolve().parents[2]
    source = (root / "infra/migrations/versions/0004_canonical_station_time_zone.py").read_text()

    statements = re.findall(r'sa\.text\(\s*"([^"]+)"', source)
    assert len(statements) == 1, f"0004 should issue exactly one statement, found {statements}"
    sql = statements[0]
    assert sql.startswith("UPDATE station SET time_zone = "), sql
    assert "WHERE time_zone = :legacy" in sql, "the WHERE clause is what makes it idempotent"
    assert sql.count("=") == 2, f"one SET and one WHERE comparison only: {sql}"
    for forbidden in ("DELETE", "DROP", "INSERT", "ALTER", "derived_feature", "observation"):
        assert forbidden not in sql.upper() if forbidden.isupper() else forbidden not in sql, sql

    assert 'LEGACY_ALIAS = "PST8PDT"' in source
    assert f'CANONICAL_ZONE = "{PACIFIC_TIME_ZONE}"' in source
    assert PACIFIC_TIME_ZONE in SEEDABLE_TIME_ZONES
    # the migration must not import the application constant it duplicates
    assert "from cascade_core" not in source and "import cascade_core" not in source

    # Parsed, not grepped: the docstring contains the words "no-op", so a substring check for
    # "op." matches its own explanation. The body must contain nothing but that docstring.
    import ast

    tree = ast.parse(source)
    down = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "downgrade")
    assert len(down.body) == 1 and isinstance(down.body[0], ast.Expr), (
        "downgrade must stay a no-op; writing the alias back recreates the defect"
    )
    assert isinstance(down.body[0].value, ast.Constant) and isinstance(down.body[0].value.value, str)

    up = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "upgrade")
    calls = {
        ast.unparse(n.func) for n in ast.walk(up) if isinstance(n, ast.Call) and not isinstance(n.func, ast.Name)
    }
    assert calls == {"op.get_bind", "op.get_bind().execute", "sa.text"}, f"upgrade should do one thing: {calls}"
