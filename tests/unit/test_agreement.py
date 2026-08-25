"""Agreement v0 and the two read-path defects it depends on (design §3, §4 items 1–2, §5).

The two regression tests at the top of this file are the point of the whole exercise. Before
P3, `forecast_run` held exactly one forecast product, so "the latest run at this point" and "the
official NWRFC forecast" were the same sentence, and `forecast_run_ref` spelled
`source_kind=OFFICIAL_FORECAST` beside every run it described. Putting the NWM ensemble into the
same table turns both of those into a mechanism for showing a model run under the authority of
the National Weather Service. These tests fail if either fix is reverted.

Offline: SQLite + checked-in fixtures + respx. No network (docs/TESTING.md).
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest
import respx
from sqlalchemy import select

from cascade_api.main import create_app
from cascade_contracts import FloodCategory, SourceKind
from cascade_contracts.visualization import AgreementLevel
from cascade_core.db import create_schema, make_engine, make_session_factory
from cascade_core.fetch import ArchivingFetcher
from cascade_core.knowledge import OFFICIAL_FORECAST_PRODUCTS, as_known_at
from cascade_core.models import DerivedFeature, ForecastPoint, ForecastRun, ForecastValue, RawArtifact, SourceProduct
from cascade_core.objectstore import LocalFilesystemStore
from cascade_core.registry import (
    PRODUCT_NWM_MR,
    PRODUCT_NWPS_FORECAST,
    PRODUCT_NWS_FLS_CREST,
    PRODUCTS,
    SOURCES,
    SRC_NWM,
)
from cascade_core.seed import seed_all
from cascade_core.settings import SEED_FILE, Settings
from cascade_hydrology import agreement
from cascade_hydrology.agreement import (
    BANDS,
    Hydrograph,
    MemberCrest,
    ModelEnsembleWindow,
    compare,
    comparison_window,
    member_exceedance,
    read_hydrograph,
)
from cascade_hydrology.assemble import assess_point, forecast_run_ref, resolved_source_kind
from cascade_hydrology.category import ThresholdSet
from cascade_hydrology.surfaces import forecast_crest
from cascade_providers_nwps.normalize import forecast_from_stageflow, thresholds_from_gauge
from cascade_providers_nwps.parser import parse_gauge, parse_stageflow
from cascade_providers_nwps.reaches_jobs import (
    FEATURE_MEMBER_SERIES,
    METHOD_MEMBER_SERIES,
    EmptyCycleError,
    run_fetch_medium_range,
)
from cascade_providers_nwps.reaches_normalize import (
    COVERAGE_HORIZON_H,
    ENCODING_GRID,
    ENCODING_POINTS,
    SERIES_SCHEMA,
    NormalizeError,
    encode_series,
    member_window,
    model_run_from_ensemble,
)
from cascade_providers_nwps.reaches_parser import ParseError, parse_medium_range
from tests.conftest import FIXTURES, GEO

NWM = FIXTURES / "nwm-via-nwps"
OFFICIAL = FIXTURES / "nwps"

LIDS = ("RNTW1", "CRNW1", "MVEW1", "NKSW1", "AUBW1", "WRAW1")
REACHES = {
    "RNTW1": "24537890", "CRNW1": "23970199", "MVEW1": "24270288",
    "NKSW1": "23955772", "AUBW1": "23977634", "WRAW1": "23981235",
}
#: The NWM cycle in the fixtures is 2026-08-24T12:00Z and it was retrieved at 22:05Z; the
#: official runs in tests/fixtures/providers/nwps were issued 2026-08-21T15:0xZ. Reading at 23:00Z
#: on the 24th puts both inside the hazard window, which is the situation agreement is for.
RETRIEVED_OFFICIAL = datetime(2026, 8, 21, 15, 30, tzinfo=UTC)
RETRIEVED_NWM = datetime(2026, 8, 24, 22, 5, tzinfo=UTC)
AS_OF = datetime(2026, 8, 24, 23, 0, tzinfo=UTC)

AUBW1_FLOW_THRESHOLDS = ThresholdSet(basis="flow", unit="cfs", datum=None, action=6000.0, minor=9000.0, moderate=12000.0, major=14000.0)
MVEW1_STAGE_THRESHOLDS = ThresholdSet(basis="stage", unit="ft", datum="NGVD29", action=23.5, minor=28.0, moderate=30.0, major=32.0)


# --------------------------------------------------------------------------------------
# fixtures
# --------------------------------------------------------------------------------------
@pytest.fixture
async def sessions(tmp_path):
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path}/agreement.db")
    await create_schema(engine)
    factory = make_session_factory(engine)
    async with factory() as session:
        await seed_all(session, geo_dir=GEO, seed_file=SEED_FILE)
        await session.commit()
    yield factory
    await engine.dispose()


async def _artifact(session, product_id: str, url: str) -> RawArtifact:
    art = RawArtifact(
        sha256="b" * 64, object_key="test/agreement", product_id=product_id, fetched_at=RETRIEVED_OFFICIAL,
        request_url=url, bytes=1, http_status=200, content_type="application/json",
    )
    session.add(art)
    await session.flush()
    return art


async def _store_official(session, lid: str) -> ForecastRun:
    """The real NWRFC run for `lid`, from the checked-in /gauges/{lid}/stageflow fixture."""
    sf = parse_stageflow((OFFICIAL / f"stageflow_{lid}.json").read_bytes())
    datum = "NGVD29" if lid in {"RNTW1", "MVEW1", "AUBW1", "WRAW1"} else "NAVD88"
    rec = forecast_from_stageflow(sf.forecast, retrieved_at=RETRIEVED_OFFICIAL, issuer="NWRFC", datum=datum)
    assert rec is not None
    art = await _artifact(session, PRODUCT_NWPS_FORECAST, f"https://api.water.noaa.gov/nwps/v1/gauges/{lid}/stageflow")
    run = ForecastRun(
        product_id=PRODUCT_NWPS_FORECAST, fp_id=f"fp:nwps:{lid}", issued_at=rec.issued_at,
        retrieved_at=rec.retrieved_at, available_at=rec.available_at, issuer=rec.issuer,
        primary_variable=rec.primary_variable, unit=rec.unit, stage_unit=rec.stage_unit,
        flow_unit=rec.flow_unit, datum=rec.datum, raw_artifact_id=art.id,
    )
    session.add(run)
    await session.flush()
    for v in rec.values:
        session.add(ForecastValue(run_id=run.id, valid_time=v.valid_time, stage=v.stage, flow=v.flow))
    await session.flush()
    return run


def _mock_reaches() -> None:
    """respx routes serving the checked-in NWM payloads; nothing here touches the network."""
    for lid, reach in REACHES.items():
        respx.get(f"https://api.water.noaa.gov/nwps/v1/reaches/{reach}/streamflow").mock(
            return_value=httpx.Response(
                200, content=(NWM / f"medium_range_{lid}.json").read_bytes(),
                headers={"content-type": "application/json"},
            )
        )


async def _points_with_reach(session) -> list[str]:
    q = select(ForecastPoint.id).where(ForecastPoint.reach_id.is_not(None))
    return list((await session.execute(q)).scalars().all())


async def _ingest_nwm(session, tmp_path) -> int:
    fetcher = ArchivingFetcher(store=LocalFilesystemStore(tmp_path), user_agent="test", clock=lambda: RETRIEVED_NWM)
    return await run_fetch_medium_range(session, fetcher)


# --------------------------------------------------------------------------------------
# §4 item 1 + §5 agreement exit test 3 — the product filter on the read path
# --------------------------------------------------------------------------------------
async def test_a_later_nwm_run_never_becomes_the_official_forecast(sessions) -> None:
    """Both runs stored at MVEW1, the NWM one issued LATER. The official surface must not move.

    This is design §3.4 defect 1 in one test: before the product filter, `latest_forecast_run`
    ordered by issued_at over every product, so on any cycle where NWM was newer the basin's
    `official_forecast` would have been an NWM run wearing the NWRFC's provenance."""
    async with sessions() as s:
        official = await _store_official(s, "MVEW1")
        nwm_art = await _artifact(s, PRODUCT_NWM_MR, "https://api.water.noaa.gov/nwps/v1/reaches/24270288/streamflow")
        later = official.issued_at + timedelta(hours=6)
        nwm = ForecastRun(
            product_id=PRODUCT_NWM_MR, fp_id="fp:nwps:MVEW1", issued_at=later, retrieved_at=later,
            available_at=later, issuer="NOAA OWP (National Water Model v3.1)", primary_variable="flow",
            unit="cfs", stage_unit=None, flow_unit="cfs", datum=None, raw_artifact_id=nwm_art.id,
        )
        s.add(nwm)
        await s.flush()
        s.add(ForecastValue(run_id=nwm.id, valid_time=later + timedelta(hours=6), stage=None, flow=999_999.0))
        await s.commit()
        nwm_id, official_id, official_issued = nwm.id, official.id, official.issued_at

    async with sessions() as s:
        k = as_known_at(s, AS_OF)
        # the default read is the registry-resolved OFFICIAL set, so the newer model run loses
        assert (await k.latest_forecast_run("fp:nwps:MVEW1")).id == official_id
        assert (await k.latest_forecast_run("fp:nwps:MVEW1", product_ids=OFFICIAL_FORECAST_PRODUCTS)).id == official_id
        # ...and the filter is what is doing the work: unfiltered, the model run IS the newest
        assert (await k.latest_forecast_run("fp:nwps:MVEW1", product_ids=None)).id == nwm_id
        assert (await k.latest_forecast_run("fp:nwps:MVEW1", product_ids=frozenset({PRODUCT_NWM_MR}))).id == nwm_id

        products = await k.products()
        fp = await k.forecast_point_by_lid("MVEW1")
        basin = await k.basin(fp.basin_id)
        pa = await assess_point(k, fp, basin, products)
        assert pa.item.official_forecast is not None
        assert pa.item.official_forecast.issued_at == official_issued
        assert pa.item.official_forecast.issuer == "NWRFC"
        ref = pa.refs["nwps-forecast-mvew1"]
        assert (ref.product_id, ref.source_kind) == (PRODUCT_NWPS_FORECAST, SourceKind.OFFICIAL_FORECAST)
        # the crest the basin shows is the NWRFC's, not the model's 999,999 cfs
        assert pa.item.official_forecast.crest is not None and pa.item.official_forecast.crest.value < 100_000

        # and the same run described through forecast_run_ref is MODELED, with NWM's own identity
        nwm_run = await k.latest_forecast_run("fp:nwps:MVEW1", product_ids=frozenset({PRODUCT_NWM_MR}))
        model_ref = forecast_run_ref(nwm_run, products, now=AS_OF)
        assert model_ref.source_kind is SourceKind.MODELED
        assert model_ref.source_id == SRC_NWM and model_ref.product_id == PRODUCT_NWM_MR
        # the two refs agree about nothing that matters: different source, product and kind
        assert (model_ref.source_id, model_ref.product_id, model_ref.source_kind) != (ref.source_id, ref.product_id, ref.source_kind)
        assert model_ref.label == products[PRODUCT_NWM_MR].label


async def test_forecast_runs_window_still_returns_every_product(sessions) -> None:
    """The evolution read stays multi-product on purpose: each run carries its own badge.

    Hiding the model run here would be the opposite failure — a second opinion the platform has
    and does not show. What must be true is that each item's kind is resolved, not assumed."""
    async with sessions() as s:
        official = await _store_official(s, "MVEW1")
        art = await _artifact(s, PRODUCT_NWM_MR, "https://api.water.noaa.gov/nwps/v1/reaches/24270288/streamflow")
        s.add(ForecastRun(
            product_id=PRODUCT_NWM_MR, fp_id="fp:nwps:MVEW1", issued_at=official.issued_at + timedelta(hours=6),
            retrieved_at=RETRIEVED_NWM, available_at=RETRIEVED_NWM, issuer="NOAA OWP (National Water Model v3.1)",
            primary_variable="flow", unit="cfs", stage_unit=None, flow_unit="cfs", datum=None, raw_artifact_id=art.id,
        ))
        await s.commit()
    async with sessions() as s:
        k = as_known_at(s, AS_OF)
        products = await k.products()
        runs = await k.forecast_runs("fp:nwps:MVEW1", AS_OF - timedelta(days=7), AS_OF)
        kinds = {r.product_id: forecast_run_ref(r, products, now=AS_OF).source_kind for r in runs}
        assert kinds == {PRODUCT_NWPS_FORECAST: SourceKind.OFFICIAL_FORECAST, PRODUCT_NWM_MR: SourceKind.MODELED}
        assert len(await k.forecast_runs("fp:nwps:MVEW1", AS_OF - timedelta(days=7), AS_OF, product_ids=OFFICIAL_FORECAST_PRODUCTS)) == 1


# --------------------------------------------------------------------------------------
# §4 item 2 + §5 agreement exit test 3 (the property) — source_kind comes from the registry
# --------------------------------------------------------------------------------------
def test_no_nwm_provenance_ref_may_ever_be_official_forecast(sessions) -> None:
    """The property test design §5 asks for, stated over the registry rather than one example.

    Every product of `src:nwm-v3.1` is MODELED, and `forecast_run_ref` reproduces that for a run
    of any of them. There is no code path — and no product id — that makes an NWM run official."""
    nwm_products = [p["id"] for p in PRODUCTS if p["source_id"] == SRC_NWM]
    assert nwm_products, "the NWM source must have at least one registered product"
    assert {s["kind"] for s in SOURCES if s["id"] == SRC_NWM} == {"MODELED"}
    for product_id in nwm_products:
        product = _FakeProduct(id=str(product_id), source_id=SRC_NWM, label="NWM")
        assert resolved_source_kind(product) is SourceKind.MODELED
        ref = forecast_run_ref(_FakeRun(str(product_id)), {str(product_id): product}, now=AS_OF)
        assert ref.source_kind is not SourceKind.OFFICIAL_FORECAST
        assert (ref.source_kind, ref.source_id) == (SourceKind.MODELED, SRC_NWM)


def test_every_registered_product_resolves_to_its_registered_kind() -> None:
    """No product's badge is a guess, and an unregistered source is UNKNOWN — never OFFICIAL."""
    kinds = {s["id"]: s["kind"] for s in SOURCES}
    for p in PRODUCTS:
        product = _FakeProduct(id=str(p["id"]), source_id=str(p["source_id"]), label=str(p["label"]))
        ref = forecast_run_ref(_FakeRun(str(p["id"])), {str(p["id"]): product}, now=AS_OF)
        assert ref.source_kind.value == kinds[p["source_id"]]
    stranger = _FakeProduct(id="product:mystery", source_id="src:not-registered", label="?")
    assert resolved_source_kind(stranger) is SourceKind.UNKNOWN
    assert resolved_source_kind(None) is SourceKind.UNKNOWN
    unknown_ref = forecast_run_ref(_FakeRun("product:mystery"), {}, now=AS_OF)
    assert unknown_ref.source_kind is SourceKind.UNKNOWN and unknown_ref.source_id == "src:unknown"
    # the fallback label names the unregistered product; it does not assert an authority
    assert "product:mystery" in unknown_ref.label and "NWRFC" not in unknown_ref.label


def test_official_forecast_products_are_resolved_from_the_registry() -> None:
    """The default filter is derived, not typed out: it is exactly the OFFICIAL_FORECAST sources."""
    expected = {
        str(p["id"])
        for p in PRODUCTS
        if next(s["kind"] for s in SOURCES if s["id"] == p["source_id"]) == "OFFICIAL_FORECAST"
    }
    assert OFFICIAL_FORECAST_PRODUCTS == expected
    assert {PRODUCT_NWPS_FORECAST, PRODUCT_NWS_FLS_CREST} <= OFFICIAL_FORECAST_PRODUCTS
    assert PRODUCT_NWM_MR not in OFFICIAL_FORECAST_PRODUCTS


def _FakeProduct(*, id: str, source_id: str, label: str) -> SourceProduct:
    """An unattached SourceProduct row — the real shape, without a database."""
    return SourceProduct(id=id, source_id=source_id, label=label, variables=[], expected_cadence_seconds=21600, grace_seconds=28800)


class _FakeRun:
    def __init__(self, product_id: str) -> None:
        self.product_id = product_id
        self.issued_at = AS_OF - timedelta(hours=6)
        self.retrieved_at = AS_OF - timedelta(hours=5)
        self.issuer = "issuer"
        self.raw_artifact_id = 1


# --------------------------------------------------------------------------------------
# the provider: parsing and normalizing the NWM ensemble
# --------------------------------------------------------------------------------------
@pytest.mark.parametrize("lid", LIDS)
def test_every_captured_reach_parses_with_its_members_read_from_the_payload(lid: str) -> None:
    e = parse_medium_range((NWM / f"medium_range_{lid}.json").read_bytes())
    assert e.reach.reach_id == REACHES[lid]
    assert e.reference_time == datetime(2026, 8, 24, 12, tzinfo=UTC)
    assert [m.name for m in e.members] == [f"member{i}" for i in range(1, 7)]
    assert e.member_count == 6  # observed today; the code reads it, the fixture pins it
    assert e.mean is not None and e.mean.name not in {m.name for m in e.members}  # mean is not a member
    assert {s.unit for s in (e.mean, *e.members)} == {"cfs"}  # ft³/s recognised, not converted
    assert len(e.mean.points) == 240 and all(len(m.points) in (204, 240) for m in e.members)


def test_the_stored_run_is_flow_only_truncated_to_the_hazard_window() -> None:
    e = parse_medium_range((NWM / "medium_range_MVEW1.json").read_bytes())
    run = model_run_from_ensemble(e, retrieved_at=RETRIEVED_NWM)
    assert run is not None
    assert (run.primary_variable, run.unit, run.flow_unit) == ("flow", "cfs", "cfs")
    assert run.stage_unit is None and run.datum is None  # ADR-0014: flow never carries a datum
    assert run.issued_at == datetime(2026, 8, 24, 12, tzinfo=UTC)
    assert run.available_at == RETRIEVED_NWM  # knowledge time is the retrieval, not the cycle
    assert len(run.values) == 72  # 240 published hours, 72 stored (design §3.4 volume control)
    assert run.values[-1].valid_time == run.issued_at + timedelta(hours=72)
    assert run.series_name == "mean"


def test_ingest_stores_member_series_and_freezes_no_crest() -> None:
    """Finding B, at the ingest boundary: a crest needs a window, so none is written here.

    The stored coverage is 96 h from the cycle rather than 72 — the read-time window ends at
    `as_of + 72 h`, which is `cycle_age` hours past `cycle + 72 h`, so a 72-hour store leaves the
    model side short of the official window by exactly the cycle age. That shortfall is what made
    the last hours of the official horizon invisible to the model."""
    e = parse_medium_range((NWM / "medium_range_MVEW1.json").read_bytes())
    window = member_window(e)
    assert window is not None and window.member_count == 6
    assert window.coverage_h == COVERAGE_HORIZON_H == 96
    assert window.hazard_window_h == 72 and window.coverage_h > window.hazard_window_h
    cycle = datetime(2026, 8, 24, 12, tzinfo=UTC)
    for m in window.members:
        assert m.points[0][0] == cycle + timedelta(hours=1)
        assert m.points[-1][0] == cycle + timedelta(hours=96)
        assert len(m.points) == 96
    # the mean is the provider's average of its own members: not a member, and not in here
    assert "mean" not in {m.member for m in window.members}
    # and nothing on this object is a crest, a median or a central value
    assert not [f for f in vars(window) if "crest" in f or "median" in f]


def test_the_median_is_a_member_chosen_at_read_time_and_the_mean_is_never_one() -> None:
    """The lower-median rule on the diverged fixture: crests 5000…15000, median member = 9500.

    The rule lives on the read side now, because which member is central depends on the window
    the crests were taken over, and the window is only known at `as_of`."""
    e = parse_medium_range((NWM / "medium_range_AUBW1_diverged.json").read_bytes())
    stored = member_window(e)
    assert stored is not None and stored.member_count == 6
    cycle = datetime(2026, 8, 24, 12, tzinfo=UTC)
    window = comparison_window(as_of=cycle + timedelta(hours=1), issued_at=cycle, coverage_h=96)
    ensemble = agreement.ensemble_from_feature(
        {"schema": agreement.SERIES_SCHEMA, "coverage_h": 96, "unit": "cfs",
         "series": {m.member: encode_series(m.points) for m in stored.members}},
        issued_at=cycle, window=window,
    )
    assert ensemble is not None and ensemble.member_count == 6
    assert sorted(c.value for c in ensemble.crests) == [5000.0, 8000.0, 9500.0, 11000.0, 13000.0, 15000.0]
    median = ensemble.median_member
    assert median is not None and (median.name, median.crest.value) == ("member3", 9500.0)
    # the provider's mean crest (10250) is a different number and is not a member of this ladder
    assert 10250.0 not in {c.value for c in ensemble.crests}
    assert median.crest.valid_time in {c.valid_time for c in ensemble.crests}


def test_provider_negative_fixtures() -> None:
    empty = parse_medium_range((NWM / "medium_range_MVEW1_no_series.json").read_bytes())
    assert empty.members == () and empty.mean is None and empty.reference_time is None
    assert model_run_from_ensemble(empty, retrieved_at=RETRIEVED_NWM) is None
    assert member_window(empty) is None
    with pytest.raises(ParseError, match="cubic-feet-per-second"):
        parse_medium_range((NWM / "medium_range_MVEW1_bad_units.json").read_bytes())
    with pytest.raises(ParseError, match="not JSON"):
        parse_medium_range((NWM / "malformed.json").read_bytes())
    mixed = parse_medium_range((NWM / "medium_range_MVEW1_mixed_cycle.json").read_bytes())
    with pytest.raises(NormalizeError, match="mixed-cycle"):
        model_run_from_ensemble(mixed, retrieved_at=RETRIEVED_NWM)
    with pytest.raises(NormalizeError, match="mixed-cycle"):
        member_window(mixed)
    sentinel = parse_medium_range((NWM / "medium_range_MVEW1_sentinel.json").read_bytes())
    assert [p.flow for p in sentinel.mean.points[:3]] == [None, None, None]  # -9999 -> None, never 0
    run = model_run_from_ensemble(sentinel, retrieved_at=RETRIEVED_NWM)
    assert run is not None and len(run.values) == 69 and all(v.flow is not None for v in run.values)
    # a sentinel keeps its slot in the stored series, so the grid never shifts under a gap
    stored = member_window(sentinel)
    assert stored is not None
    first = stored.members[0]
    assert first.observed_count < len(first.points)
    assert any(v is None for _, v in first.points)
    # the grid is intact: consecutive points are still one hour apart across the gap
    steps = {(first.points[i + 1][0] - first.points[i][0]).total_seconds() for i in range(len(first.points) - 1)}
    assert steps == {3600.0}


def test_series_encoding_round_trips_and_an_unknown_encoding_is_refused() -> None:
    """The compact grid form is only used when the series really is on one uniform step."""
    grid = tuple((T0 + timedelta(hours=h), None if h == 3 else 100.0 + h) for h in range(6))
    encoded = encode_series(grid)
    assert encoded["encoding"] == "grid" and encoded["step_h"] == 1.0
    assert agreement.decode_series(encoded) == grid
    ragged = ((T0, 1.0), (T0 + timedelta(hours=1), 2.0), (T0 + timedelta(hours=5), 3.0))
    fallback = encode_series(ragged)
    assert fallback["encoding"] == "points"  # never resampled onto a grid it is not on
    assert agreement.decode_series(fallback) == ragged
    # an encoding this version does not implement is refused rather than half-understood
    assert agreement.decode_series({"encoding": "rle@9", "flow": [1, 2]}) is None
    assert agreement.decode_series(None) is None


def test_feature_vocabulary_matches_the_writer() -> None:
    """Hydrology does not import provider packages, so the shared names are pinned by a test."""
    assert agreement.FEATURE_MEMBER_SERIES == FEATURE_MEMBER_SERIES
    assert agreement.METHOD_MEMBER_SERIES == METHOD_MEMBER_SERIES
    assert agreement.SERIES_SCHEMA == SERIES_SCHEMA
    assert (agreement.ENCODING_GRID, agreement.ENCODING_POINTS) == (ENCODING_GRID, ENCODING_POINTS)


# --------------------------------------------------------------------------------------
# the method: compare() — bands, UNKNOWN paths, member fraction
# --------------------------------------------------------------------------------------
T0 = datetime(2026, 12, 10, 12, tzinfo=UTC)


def _peak(crest: float, at_h: int, *, span_h: int | None = None, rel_base: float = 0.5) -> tuple[tuple[datetime, float], ...]:
    """A hydrograph that genuinely crests: rises from half the peak to `crest` at T0+at_h, falls back.

    Relative prominence is 50 %, far above the 5 % the method asks for, so these series are
    unambiguously "there is a crest here" and the timing axis is assessable on them."""
    span = span_h if span_h is not None else at_h + 24
    out = []
    base = crest * rel_base
    for h in range(span + 1):
        v = base + (crest - base) * (h / at_h) if h <= at_h else crest - (crest - base) * ((h - at_h) / (span - at_h))
        out.append((T0 + timedelta(hours=h), v))
    return tuple(out)


def _recession(start: float, *, span_h: int = 48, end_fraction: float = 0.6) -> tuple[tuple[datetime, float], ...]:
    """A monotone recession: the window maximum is its first point, so there is no crest to time."""
    end = start * end_fraction
    return tuple((T0 + timedelta(hours=h), start - (start - end) * h / span_h) for h in range(span_h + 1))


def _flat(value: float, *, span_h: int = 48, wobble: float = 0.0) -> tuple[tuple[datetime, float], ...]:
    """A line whose whole range is under the flat threshold: no crest, and no trend either."""
    return tuple(
        (T0 + timedelta(hours=h), value * (1 + wobble * (h % 3 - 1))) for h in range(span_h + 1)
    )


def _hydro(points: tuple[tuple[datetime, float], ...], name: str = "nwrfc-official-flow") -> Hydrograph:
    h = read_hydrograph(name, points)
    assert h is not None
    return h


def _ensemble_of(members: dict[str, tuple[tuple[datetime, float], ...]]) -> ModelEnsembleWindow:
    """{member: hydrograph} -> the read-time ensemble; every crest is taken here, not at ingest."""
    return ModelEnsembleWindow(
        issued_at=T0, coverage_h=96, unit="cfs",
        members=tuple(_hydro(pts, m) for m, pts in sorted(members.items())),
    )


def _ensemble(values: dict[str, tuple[float, int]]) -> ModelEnsembleWindow:
    """{member: (crest cfs, hours after T0)} -> members that each genuinely crest at that hour."""
    return _ensemble_of({m: _peak(v, h) for m, (v, h) in values.items()})


def test_bands_are_reproducible_and_monotone() -> None:
    """Both sides genuinely crest here, so the timing axis has something to measure."""
    official = _hydro(_peak(10_000.0, 24))
    near = compare(lid="AUBW1", official=official, ensemble=_ensemble({"m1": (10_500.0, 26), "m2": (11_000.0, 27), "m3": (11_500.0, 28)}))
    assert near.state is AgreementLevel.HIGH and near.timing_assessable
    assert near.magnitude_divergence == pytest.approx(0.10) and near.timing_divergence_h == pytest.approx(3.0)
    mid = compare(lid="AUBW1", official=official, ensemble=_ensemble({"m1": (14_000.0, 36), "m2": (14_500.0, 38), "m3": (15_000.0, 40)}))
    assert mid.state is AgreementLevel.MODERATE
    far = compare(lid="AUBW1", official=official, ensemble=_ensemble({"m1": (20_000.0, 60), "m2": (21_000.0, 62), "m3": (22_000.0, 64)}))
    assert far.state is AgreementLevel.LOW and far.reason is not None and "%" in far.reason
    # timing alone is enough to break agreement, at any magnitude — but only when both crest
    late = compare(lid="AUBW1", official=official, ensemble=_ensemble({"m1": (10_000.0, 60), "m2": (10_000.0, 61), "m3": (10_000.0, 62)}))
    assert late.state is AgreementLevel.LOW and late.magnitude_divergence == pytest.approx(0.0)
    assert late.timing_assessable and late.timing_divergence_h == pytest.approx(37.0)
    # and the bands themselves are the versioned parameter block, carrying their assumption
    assert (BANDS.high_magnitude, BANDS.moderate_magnitude) == (0.25, 0.60)
    assert (BANDS.high_timing_h, BANDS.moderate_timing_h) == (6.0, 18.0)
    assert (BANDS.crest_prominence, BANDS.flat_amplitude) == (0.05, 0.05)
    assert "not calibrated" in BANDS.assumption or "uncalibrated" in BANDS.assumption
    assert near.method_record["bands"]["assumption"] == BANDS.assumption


def test_unknown_paths_each_name_their_missing_input() -> None:
    ens = _ensemble({"m1": (100.0, 4), "m2": (110.0, 5), "m3": (120.0, 6)})
    no_official = compare(lid="MVEW1", official=None, ensemble=ens)
    assert no_official.state is AgreementLevel.UNKNOWN and "hazard window" in no_official.reason
    no_model = compare(lid="MVEW1", official=_hydro(_peak(100.0, 4)), ensemble=None)
    assert no_model.state is AgreementLevel.UNKNOWN and "NWM" in no_model.reason
    empty = ModelEnsembleWindow(issued_at=T0, coverage_h=96, unit="cfs", members=())
    assert compare(lid="MVEW1", official=_hydro(_peak(100.0, 4)), ensemble=empty).state is AgreementLevel.UNKNOWN
    zero = compare(lid="MVEW1", official=_hydro(_flat(0.0)), ensemble=ens)
    assert zero.state is AgreementLevel.UNKNOWN and "denominator" in zero.reason
    assert zero.magnitude_divergence is None  # refused, not computed and hidden
    # and read_hydrograph itself refuses an empty window rather than inventing a crest for it
    assert read_hydrograph("empty", ()) is None


def test_the_floor_stops_a_small_official_crest_manufacturing_disagreement() -> None:
    """A 300 cfs summer official crest against a 380 cfs model crest is a 25% ratio and nothing
    else; against the official ACTION flow it is 1%. The floor is the honest denominator."""
    official, ens = _hydro(_peak(300.0, 2)), _ensemble({"m1": (370.0, 1), "m2": (380.0, 2), "m3": (390.0, 3)})
    unfloored = compare(lid="AUBW1", official=official, ensemble=ens)
    floored = compare(lid="AUBW1", official=official, ensemble=ens, thresholds=AUBW1_FLOW_THRESHOLDS, floor=AUBW1_FLOW_THRESHOLDS.action)
    assert unfloored.magnitude_divergence == pytest.approx(80 / 300)
    assert floored.magnitude_divergence == pytest.approx(80 / 6000)
    assert "no_divergence_floor" in unfloored.quality and floored.quality == ()


def test_the_sampling_asymmetry_is_recorded_even_when_neither_side_crests() -> None:
    """Two maxima over the same window are not the same measurement when one series has 6x the
    samples of the other.

    Measured live 2026-08-25 at all five comparable points: the NWRFC run is 6-hourly (13 points
    in the 78 h window) and the NWM members hourly (78 points). The flag used to be recorded only
    when the timing axis was assessable, so on live data it was recorded NOWHERE — while the
    magnitude comparison, which is what the level actually rested on, was the asymmetric one. On a
    peaked hydrograph the coarser series can step over a crest the finer one resolves, biasing the
    difference toward "the model exceeds the official forecast" (§P3.9).
    """
    six_hourly = tuple((T0 + timedelta(hours=h), 300.0 + h) for h in range(0, 73, 6))
    hourly = tuple((T0 + timedelta(hours=h), 300.0 + h) for h in range(0, 73))
    r = compare(lid="MVEW1", official=_hydro(six_hourly), ensemble=_ensemble_of({"m1": hourly}),
                thresholds=MVEW1_STAGE_THRESHOLDS)
    assert not r.timing_assessable  # neither side crests: both are monotone rises
    assert agreement.QUALITY_COARSE_OFFICIAL_STEP in r.quality
    assert any("step over a crest" in n for n in r.method_record["notes"])
    assert r.method_record["official"]["step_h"] == 6.0 and r.method_record["model"]["step_h"] == 1.0

    # Equal steps: nothing to record.
    same = compare(lid="MVEW1", official=_hydro(hourly), ensemble=_ensemble_of({"m1": hourly}),
                   thresholds=MVEW1_STAGE_THRESHOLDS)
    assert agreement.QUALITY_COARSE_OFFICIAL_STEP not in same.quality


def test_the_percentage_in_the_reason_names_the_denominator_it_was_divided_by() -> None:
    """A percentage attributed to the wrong denominator is a wrong number, not a rounding.

    Measured live on 2026-08-25 at AUBW1 (`pg-migration-verification-2026-08-24` §P3.9): the
    official crest was 294.7 cfs and the NWM median member 379.3 cfs — **28.7 % of the official
    crest apart** — and the surface printed "The NWM median member peaks 1% above the NWRFC
    forecast" and read HIGH. The 1 % was true of the 6,000 cfs action flow the divergence is
    floored against, and the sentence attributed it to the forecast, off by a factor of 20. The
    LEVEL is right (85 cfs on a river that acts at 6,000 cfs is nothing); the SENTENCE was not.

    So: where the floor is the denominator the sentence states the difference in cfs and names
    the action flow the percentage is a fraction of; where the official crest is the denominator
    — every stage-threshold point, and any flow point whose crest is above its action flow — the
    percentage really is a fraction of the forecast and the wording is unchanged.
    """
    official, ens = _hydro(_peak(294.7, 2)), _ensemble({"m1": (379.3, 3)})
    floored = compare(lid="AUBW1", official=official, ensemble=ens,
                      thresholds=AUBW1_FLOW_THRESHOLDS, floor=AUBW1_FLOW_THRESHOLDS.action)
    assert floored.magnitude_divergence == pytest.approx(84.6 / 6000, rel=1e-3)
    assert "85 cfs above the NWRFC forecast" in floored.reason
    assert "1% of this point's 6,000 cfs action flow" in floored.reason
    assert "1% above the NWRFC forecast" not in floored.reason
    assert floored.method_record["magnitude"]["denominator_basis"] == "action_flow"
    assert floored.method_record["magnitude"]["denominator_cfs"] == pytest.approx(6000.0)
    assert floored.method_record["magnitude"]["difference_cfs"] == pytest.approx(84.6, rel=1e-3)

    # No floor: the percentage IS a fraction of the official crest, so nothing changes.
    unfloored = compare(lid="MVEW1", official=_hydro(_peak(120.0, 2)), ensemble=_ensemble({"m1": (195.6, 3)}),
                        thresholds=MVEW1_STAGE_THRESHOLDS)
    assert "63% above the NWRFC forecast" in unfloored.reason
    assert "action flow)" not in unfloored.reason
    assert unfloored.method_record["magnitude"]["denominator_basis"] == "official_crest"

    # A flow point whose crest is ABOVE its action flow: the floor loses the max, so the official
    # crest is the denominator again and the sentence must not claim an action-flow basis.
    big = compare(lid="AUBW1", official=_hydro(_peak(9400.0, 2)), ensemble=_ensemble({"m1": (10_340.0, 3)}),
                  thresholds=AUBW1_FLOW_THRESHOLDS, floor=AUBW1_FLOW_THRESHOLDS.action)
    assert big.method_record["magnitude"]["denominator_basis"] == "official_crest"
    assert "10% above the NWRFC forecast" in big.reason and "action flow)" not in big.reason


def test_a_limitation_that_stays_in_the_dataclass_has_not_travelled_with_its_number() -> None:
    """Every quality flag has to leave `AgreementResult` — as a clause, or in the method record.

    Measured live 2026-08-24 on the real 12Z cycle: all six NWM members carried ONE distinct
    crest at all six seed reaches, so `fraction: k/6` was a binary indicator dressed as an
    empirical frequency; and at the three stage-threshold points there is no official action
    FLOW to floor the divergence denominator with, so a 120 cfs summer crest made "63% above"
    out of 76 cfs. Neither fact reached the client before these caveats existed.

    What changed with this pass is *where* the long form lives. Stacking every caveat verbatim
    into `reason` produced 742 characters at RNTW1, which the panel renders in full and nobody
    finishes reading. The reason is now one sentence carrying at most two short clauses; the full
    text of every flag is in `method_record["notes"]`, which is what an explanation view serves.
    """
    official = _hydro(_peak(9400.0, 3))
    identical = _ensemble({f"m{i}": (9500.0, 3) for i in range(1, 7)})
    degenerate = compare(lid="AUBW1", official=official, ensemble=identical,
                         thresholds=AUBW1_FLOW_THRESHOLDS, floor=AUBW1_FLOW_THRESHOLDS.action)
    assert agreement.QUALITY_DEGENERATE_ENSEMBLE in degenerate.quality
    assert degenerate.model_probability["distinct_member_crests"] == 1.0
    assert degenerate.model_probability["members"] == 6.0  # the count is still the observed one
    assert "all 6 NWM members reach the same peak" in degenerate.reason
    assert any("n independent opinions" in n for n in degenerate.method_record["notes"])

    spread = _ensemble({"m1": (9000.0, 3), "m2": (9500.0, 4), "m3": (10_000.0, 5)})
    assert agreement.QUALITY_DEGENERATE_ENSEMBLE not in compare(
        lid="AUBW1", official=official, ensemble=spread,
        thresholds=AUBW1_FLOW_THRESHOLDS, floor=AUBW1_FLOW_THRESHOLDS.action).quality
    assert member_exceedance(spread.crests, AUBW1_FLOW_THRESHOLDS)["distinct_member_crests"] == 3.0

    # the floor caveat, and the category one, each reach a reader too
    unfloored = compare(lid="MVEW1", official=_hydro(_peak(120.0, 3)), ensemble=identical,
                        thresholds=MVEW1_STAGE_THRESHOLDS)
    assert agreement.QUALITY_NO_FLOOR in unfloored.quality
    assert "rather than an action flow" in unfloored.reason
    assert "stage-only" in unfloored.reason
    assert any("action FLOW threshold" in n for n in unfloored.method_record["notes"])
    assert any("defined in stage" in n for n in unfloored.method_record["notes"])


def test_the_reason_is_one_sentence_a_reader_can_finish() -> None:
    """742 characters of stacked caveats is not a reason; it is a place a reason used to be.

    The bound is on the rendered string because that is what the panel puts on screen. Two short
    clauses at most: everything else is in `method_record`, which is what `explanation_ref` names.
    """
    every_caveat = compare(
        lid="MVEW1",
        official=_hydro(_recession(120.0)),
        ensemble=_ensemble_of({f"m{i}": _recession(196.0) for i in range(1, 7)}),
        thresholds=MVEW1_STAGE_THRESHOLDS,
        window=comparison_window(as_of=T0 + timedelta(hours=30), issued_at=T0, coverage_h=48),
    )
    assert {agreement.QUALITY_NO_FLOOR, agreement.QUALITY_DEGENERATE_ENSEMBLE,
            agreement.QUALITY_WINDOW_TRUNCATED} <= set(every_caveat.quality)
    assert every_caveat.reason.count(".") == 1 and every_caveat.reason.endswith(".")
    assert len(every_caveat.reason) <= 280, every_caveat.reason
    assert every_caveat.reason.count(";") <= 1
    # nothing was silently dropped: what is not in the sentence is in the record
    assert len(every_caveat.method_record["notes"]) >= len(every_caveat.quality)


def test_category_is_compared_only_where_official_thresholds_are_flow() -> None:
    official = _hydro(_peak(9500.0, 2))
    ens = _ensemble({"m1": (12_500.0, 3), "m2": (12_600.0, 4), "m3": (12_700.0, 5)})
    flow = compare(lid="AUBW1", official=official, ensemble=ens, thresholds=AUBW1_FLOW_THRESHOLDS, floor=6000.0)
    assert (flow.official_category, flow.model_category) == (FloodCategory.MINOR, FloodCategory.MODERATE)
    assert flow.category_steps == 1 and flow.category_note is None
    assert flow.state is AgreementLevel.MODERATE  # one category apart is never HIGH
    stage = compare(lid="MVEW1", official=official, ensemble=ens, thresholds=MVEW1_STAGE_THRESHOLDS)
    assert stage.category_steps is None and "defined in stage" in stage.category_note
    assert stage.official_category is FloodCategory.UNKNOWN  # refused, never converted
    none = compare(lid="MVEW1", official=official, ensemble=ens, thresholds=None)
    assert none.category_steps is None and "No official flood categories" in none.category_note


def test_member_fraction_denominator_is_the_observed_member_count() -> None:
    six = tuple(MemberCrest(f"member{i}", v, T0) for i, v in enumerate([5000.0, 8000.0, 9500.0, 11000.0, 13000.0, 15000.0], start=1))
    p6 = member_exceedance(six, AUBW1_FLOW_THRESHOLDS)
    assert p6 == {
        "model": "nwm-v3.1-medium-range", "exceeds": "major", "fraction": 1 / 6, "members": 6.0,
        "exceeding": 1.0, "distinct_member_crests": 6.0,
    }
    five = six[:5]  # a version that ships five members must not report sixths
    p5 = member_exceedance(five, AUBW1_FLOW_THRESHOLDS)
    assert p5["members"] == 5.0 and p5["exceeds"] == "moderate" and p5["fraction"] == pytest.approx(1 / 5)
    quiet = tuple(MemberCrest(f"member{i}", 100.0, T0) for i in range(1, 7))
    # six IDENTICAL members: the fraction is still 0/6, but `distinct_member_crests` says out
    # loud that it is one number counted six times rather than six independent draws (measured
    # live 2026-08-24: 1 distinct crest across 6 members at every seed reach).
    assert member_exceedance(quiet, AUBW1_FLOW_THRESHOLDS) == {
        "model": "nwm-v3.1-medium-range", "exceeds": "action", "fraction": 0.0, "members": 6.0,
        "exceeding": 0.0, "distinct_member_crests": 1.0,
    }
    # stage thresholds: no flow equivalent may be invented (ADR-0011), so there is no fraction
    assert member_exceedance(six, MVEW1_STAGE_THRESHOLDS) is None
    assert member_exceedance(six, None) is None
    assert member_exceedance((), AUBW1_FLOW_THRESHOLDS) is None


# --------------------------------------------------------------------------------------
# §5 agreement exit tests, end to end on stored rows
# --------------------------------------------------------------------------------------
def _official_thresholds(lid: str) -> ThresholdSet | None:
    """The point's real official thresholds, from the checked-in /gauges/{lid} fixture."""
    rows = thresholds_from_gauge(parse_gauge((OFFICIAL / f"gauge_{lid}.json").read_bytes()))
    if not rows:
        return None
    return ThresholdSet(
        basis=rows[0].basis, unit=rows[0].unit, datum=rows[0].datum,
        **{r.category: r.value for r in rows},
    )


@respx.mock
async def test_ingest_writes_one_run_and_one_series_row_per_reach(sessions, tmp_path) -> None:
    """Design §3.4 volume control, asserted: 72 mean values + ONE member-series row.

    Seven rows became one because the six frozen member crests were the finding-B defect: a crest
    over a cycle-anchored window is not comparable with an `as_of`-anchored official crest, and a
    row that exists only to be misread is worse than no row. The series it is replaced by is
    bigger in bytes and smaller in rows, and it is the only form from which a same-window crest
    can be taken at read time."""
    _mock_reaches()
    async with sessions() as s:
        assert len(await _points_with_reach(s)) == 6  # the seed addendum landed all five ids
        written = await _ingest_nwm(s, tmp_path)
        await s.commit()
    assert written == 6 * (1 + 72 + 1)
    async with sessions() as s:
        k = as_known_at(s, AS_OF)
        run, stored = await agreement.latest_model_cycle(k, "fp:nwps:MVEW1")
        assert run is not None and run.product_id == PRODUCT_NWM_MR and run.datum is None
        assert stored is not None and stored["schema"] == SERIES_SCHEMA
        assert stored["member_count"] == 6 and stored["coverage_h"] == 96
        assert sorted(stored["series"]) == [f"member{i}" for i in range(1, 7)]
        assert all(b["encoding"] == ENCODING_GRID and len(b["flow"]) == 96 for b in stored["series"].values())
        assert len(await k.forecast_values(run.id)) == 72
        rows = await k.derived_features(FEATURE_MEMBER_SERIES, "fp:nwps:MVEW1", method_id=METHOD_MEMBER_SERIES,
                                        valid_from=run.issued_at, valid_until=run.issued_at)
        assert len(rows) == 1 and rows[0].product_id == PRODUCT_NWM_MR and rows[0].unit == "cfs"
        assert rows[0].value is None and rows[0].window == "96h"  # no crest is frozen here
        assert rows[0].valid_time == run.issued_at and rows[0].raw_inputs_hash
        # re-running the job on the same cycle writes nothing (idempotent)
    async with sessions() as s:
        assert await _ingest_nwm(s, tmp_path) == 0


@respx.mock
async def test_agreement_at_all_six_points(sessions, tmp_path) -> None:
    """Exit test 1: five points compare; CRNW1 is UNKNOWN and that UNKNOWN is the correct answer.

    The fixtures pair a 2026-08-21 official forecast with the 2026-08-24 12Z NWM cycle — a real
    three-day-old NWRFC run against a fresh model cycle, which is why several points read LOW.
    The assertion is not that agreement is good; it is that every point produces a defensible
    level or a specific UNKNOWN, and that no number is invented where one is missing."""
    _mock_reaches()
    async with sessions() as s:
        for lid in LIDS:
            await _store_official(s, lid)
        await _ingest_nwm(s, tmp_path)
        await s.commit()

    async with sessions() as s:
        k = as_known_at(s, AS_OF)
        out = {}
        for lid in LIDS:
            fp = await k.forecast_point_by_lid(lid)
            out[lid] = await agreement.assess(k, fp, thresholds=_official_thresholds(lid))

        # FINDING B, at every comparable point: one window, and both maxima taken inside it.
        for lid in ("RNTW1", "MVEW1", "NKSW1", "AUBW1", "WRAW1"):
            r = out[lid].result
            window = r.window
            assert window is not None
            assert window.contains(r.official_crest.valid_time), lid
            assert window.contains(r.model_crest.valid_time), lid
            # the cycle is 11 h old here, so a 72-hour store would have ended 11 h short of the
            # official window; 96 h of coverage means nothing is lost off the end
            assert window.cycle_age_h == pytest.approx(11.0)
            assert window.lost_tail_h == 0.0 and window.end == window.hazard_end
            assert window.hours == pytest.approx(78.0)
            # Δt, when it exists at all, can no longer exceed the window it is measured inside
            assert r.timing_divergence_h is None or r.timing_divergence_h <= window.hours

        # CRNW1: the NWRFC run carries no flow column at all (0 of 40 points)
        crnw1 = out["CRNW1"]
        assert crnw1.state.state is AgreementLevel.UNKNOWN
        assert "no flow column" in crnw1.state.reason and "sentinel" in crnw1.state.reason
        assert crnw1.drivers == () and crnw1.model_probability is None
        assert crnw1.result.magnitude_divergence is None  # nothing was computed from a stage column

        # every other point produces a level with both crests present and separately provenanced
        for lid in ("RNTW1", "MVEW1", "NKSW1", "AUBW1", "WRAW1"):
            a = out[lid]
            assert a.state.state is not AgreementLevel.UNKNOWN, lid
            assert a.result.official_crest is not None and a.result.model_crest is not None
            assert set(a.runs_by_prov_key) == {f"nwps-forecast-{lid.lower()}", f"nwm-mr-{lid.lower()}"}
            assert a.state.prov == tuple(a.runs_by_prov_key)
            assert {d.feature for d in a.drivers} == {
                "agreement_crest_flow_official", "agreement_crest_flow_nwm_median", "agreement_crest_timing_delta_h",
            }
            official_driver = next(d for d in a.drivers if d.feature == "agreement_crest_flow_official")
            model_driver = next(d for d in a.drivers if d.feature == "agreement_crest_flow_nwm_median")
            assert official_driver.prov != model_driver.prov  # two sources, two provenance refs

        # exit test 2: the member fraction exists only where official FLOW thresholds do
        assert {lid for lid, a in out.items() if a.model_probability is not None} == {"AUBW1", "WRAW1"}
        for lid in ("AUBW1", "WRAW1"):
            assert out[lid].model_probability["members"] == 6.0
            assert 0.0 <= float(out[lid].model_probability["fraction"]) <= 1.0
        for lid in ("MVEW1", "NKSW1", "RNTW1"):
            # the caveat still travels — as a clause in the sentence, in full in the record
            assert "stage-only" in out[lid].state.reason
            assert any("defined in stage" in n for n in out[lid].result.method_record["notes"])
            assert len(out[lid].state.reason) <= 280, out[lid].state.reason

        # and the levels themselves, from real numbers (see the docstring)
        assert out["NKSW1"].state.state is AgreementLevel.HIGH
        assert out["WRAW1"].state.state is AgreementLevel.HIGH
        # MVEW1 is finding A in one assertion. Before this pass it read LOW off a 75 h Δt taken
        # between the ends of two recessions — while the two forecasts agreed on magnitude to a
        # fraction of a percent. Neither hydrograph crests inside the window, so there is no
        # crest time; what IS comparable agrees, and the level now says so.
        mvew1 = out["MVEW1"].result
        assert mvew1.official_shape == mvew1.model_shape == agreement.SHAPE_RECEDING
        assert not mvew1.timing_assessable and mvew1.timing_divergence_h is None
        assert abs(mvew1.magnitude_divergence) < 0.05
        assert out["MVEW1"].state.state is AgreementLevel.HIGH
        assert "neither crests inside this window" in out["MVEW1"].state.reason
        # RNTW1 is the opposite case and stays LOW: NWM crests inside the window (37 % relative
        # prominence), the official run is flat, and the magnitudes are 61 % apart.
        rntw1 = out["RNTW1"].result
        assert rntw1.model_shape == agreement.SHAPE_CREST and rntw1.official_shape != agreement.SHAPE_CREST
        assert agreement.QUALITY_SHAPE_DISAGREEMENT in rntw1.quality
        assert out["RNTW1"].state.state is AgreementLevel.LOW


@respx.mock
async def test_agreement_is_unknown_before_the_model_run_was_retrieved(sessions, tmp_path) -> None:
    """Knowledge time still rules: replayed one second before the NWM fetch, there is no model."""
    _mock_reaches()
    async with sessions() as s:
        await _store_official(s, "NKSW1")
        await _ingest_nwm(s, tmp_path)
        await s.commit()
    async with sessions() as s:
        earlier = as_known_at(s, RETRIEVED_NWM - timedelta(seconds=1))
        fp = await earlier.forecast_point_by_lid("NKSW1")
        a = await agreement.assess(earlier, fp, thresholds=_official_thresholds("NKSW1"))
        assert a.state.state is AgreementLevel.UNKNOWN
        assert "No NWM medium-range run" in a.state.reason
        assert set(a.runs_by_prov_key) == {"nwps-forecast-nksw1"}  # only refs for rows that exist


async def test_nothing_in_the_agreement_path_averages_an_official_with_a_model_value(sessions) -> None:
    """Exit test 4, as a check rather than a promise: structural, behavioural and grep-level."""
    source = Path(agreement.__file__).read_text()
    assert not re.search(r"\(\s*\w+\s*\+\s*\w+\s*\)\s*/\s*2", source)  # no midpoint anywhere
    assert "statistics" not in source and "fmean" not in source
    assert "median" in source  # the central value is a member statistic, chosen not averaged

    official, ens = _hydro(_peak(10_000.0, 2)), _ensemble({"m1": (20_000.0, 1), "m2": (20_000.0, 2), "m3": (20_000.0, 3)})
    r = compare(lid="AUBW1", official=official, ensemble=ens)
    midpoint = 15_000.0
    assert r.official_crest.value == 10_000.0 and r.model_crest.value == 20_000.0
    assert midpoint not in {r.official_crest.value, r.model_crest.value, r.magnitude_divergence}
    # the model crest is a member's own number, never a value derived from the official one
    assert r.model_crest.value in {c.value for c in ens.crests}


@respx.mock
async def test_an_all_empty_cycle_is_a_retryable_failure_not_a_silent_success(sessions, tmp_path) -> None:
    """NWPS answers 200 with `mediumRange: {}` intermittently (measured 2026-08-24; see
    reaches_jobs). Writing nothing and reporting success would hide that; the job fails so the
    queue retries, and a partial cycle still succeeds."""
    empty = (NWM / "medium_range_MVEW1_no_series.json").read_bytes()
    for reach in REACHES.values():
        respx.get(f"https://api.water.noaa.gov/nwps/v1/reaches/{reach}/streamflow").mock(
            return_value=httpx.Response(200, content=empty, headers={"content-type": "application/json"})
        )
    async with sessions() as s:
        with pytest.raises(EmptyCycleError, match="empty medium_range series"):
            await _ingest_nwm(s, tmp_path)
        await s.rollback()

    respx.get("https://api.water.noaa.gov/nwps/v1/reaches/24270288/streamflow").mock(
        return_value=httpx.Response(200, content=(NWM / "medium_range_MVEW1.json").read_bytes(),
                                    headers={"content-type": "application/json"})
    )
    async with sessions() as s:
        assert await _ingest_nwm(s, tmp_path) == 1 + 72 + 1  # one reach answered; that is enough
        await s.commit()


def test_a_stored_payload_this_version_does_not_understand_is_refused_not_guessed() -> None:
    """A half-understood stored series produces a crest at the wrong time — finding B's class."""
    window = comparison_window(as_of=T0 + timedelta(hours=6), issued_at=T0, coverage_h=96)
    good = {
        "schema": SERIES_SCHEMA, "coverage_h": 96, "unit": "cfs", "member_count": 3,
        "series": {m: encode_series(_peak(v, 8)) for m, v in
                   (("member1", 100.0), ("member2", 200.0), ("member3", 300.0))},
    }
    ensemble = agreement.ensemble_from_feature(good, issued_at=T0, window=window)
    assert ensemble is not None and ensemble.member_count == 3
    assert ensemble.median_member.name == "member2"  # lower median, chosen here and not at ingest
    assert ensemble.median_rule == "lower_median_member"
    # a schema this version does not implement, and the old @1 crest ladder, are both refused
    assert agreement.ensemble_from_feature({**good, "schema": "nwm-member-series@9"}, issued_at=T0, window=window) is None
    legacy = {"window_h": 72, "unit": "cfs", "median_member": "member2",
              "members": {"member2": {"crest": 200.0, "valid_time": T0.isoformat()}}}
    assert agreement.ensemble_from_feature(legacy, issued_at=T0, window=window) is None
    assert agreement.ensemble_from_feature(None, issued_at=T0, window=window) is None
    assert agreement.ensemble_from_feature(good, issued_at=None, window=window) is None


@respx.mock
async def test_the_public_latest_run_endpoint_never_serves_the_model_run(sessions, tmp_path) -> None:
    """`GET /forecast-points/{lid}/runs/latest` documents itself as the latest OFFICIAL run.

    It is the endpoint where the defect would have been visible in production: it returns one
    run's points and, beside them, the `nwps-forecast-<lid>` ProvenanceRef built from the
    official run. Unfiltered, those two would have come from different forecasts — model values
    under NWRFC provenance. Asserted here rather than left to the integrator, because this is the
    surface the defect actually reaches."""
    _mock_reaches()
    db_url = f"sqlite+aiosqlite:///{tmp_path}/agreement.db"
    async with sessions() as s:
        official = await _store_official(s, "MVEW1")
        await _ingest_nwm(s, tmp_path)
        await s.commit()
        official_issued = official.issued_at

    engine = make_engine(db_url)
    app = create_app(Settings(db_url=db_url, raw_dir=tmp_path / "raw", geo_dir=GEO), engine=engine)
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
            response = await c.get("/forecast-points/MVEW1/runs/latest", params={"as_of": AS_OF.isoformat()})
    finally:
        await engine.dispose()
    body = response.json()
    assert response.status_code == 200
    assert body["issued_at"].startswith(official_issued.isoformat()[:16])
    assert (body["primary"], body["unit"]) == ("stage", "ft")  # the NWM run is flow-only, in cfs
    assert body["provenance"]["source_kind"] == "OFFICIAL_FORECAST"
    assert body["provenance"]["product_id"] == PRODUCT_NWPS_FORECAST
    # the returned points and the returned provenance describe the SAME forecast
    assert body["points"] and all(p["stage"] is not None for p in body["points"])


# --------------------------------------------------------------------------------------
# finding B — the window both crests come from
# --------------------------------------------------------------------------------------
def test_agreement_and_hazard_mean_the_same_window() -> None:
    """`hazard_window` must BE `surfaces.forecast_crest`'s window, not a second copy of it.

    Design §3.2 asks for one window "so hazard and agreement are talking about the same event".
    A constant repeated in two modules is a constant that drifts, so the equality is asserted
    against the hazard surface's own function rather than against the numbers 6 and 72."""
    as_of = datetime(2026, 8, 24, 23, 0, tzinfo=UTC)
    start, end = agreement.hazard_window(as_of)
    values = [
        (start, 900.0),                                    # exactly on the open edge: excluded
        (start + timedelta(seconds=1), 100.0),
        (end, 300.0),                                      # exactly on the closed edge: included
        (end + timedelta(seconds=1), 999.0),               # past the horizon: excluded
    ]
    hazard = forecast_crest(values, as_of=as_of)
    mine = read_hydrograph("official", agreement.clip(values, comparison_window(
        as_of=as_of, issued_at=as_of - timedelta(hours=1), coverage_h=96)))
    assert mine is not None
    assert (mine.crest.value, mine.crest.valid_time) == (hazard.value, hazard.valid_time)
    assert mine.crest.value == 300.0  # 900 and 999 are both outside, on opposite edges


def test_a_frozen_cycle_anchored_crest_is_not_the_same_number_as_a_read_time_one() -> None:
    """The defect, reproduced and then not reproduced: this is what the old ingest froze.

    The model recedes from its first hour, so its maximum over the CYCLE window `(cycle,
    cycle + 72 h]` sits at `cycle + 1 h` — 5 hours before the official window even opens when the
    cycle is 6 h old. Over the shared window the same series maximises at the first hour that is
    actually inside it, and that is the number the comparison uses."""
    cycle = datetime(2026, 8, 24, 12, tzinfo=UTC)
    as_of = cycle + timedelta(hours=12)  # a 12-hour-old cycle: the official window opens at +6 h
    series = tuple((cycle + timedelta(hours=h), 1000.0 - 4.0 * h) for h in range(1, 97))
    cycle_window_crest = max(
        (p for p in series if cycle < p[0] <= cycle + timedelta(hours=72)), key=lambda p: p[1]
    )
    assert cycle_window_crest[0] == cycle + timedelta(hours=1)

    window = comparison_window(as_of=as_of, issued_at=cycle, coverage_h=96)
    assert window.start == as_of - timedelta(hours=6) == cycle + timedelta(hours=6)
    assert cycle_window_crest[0] < window.start  # the frozen crest is outside the shared window
    read = read_hydrograph("member1", agreement.clip(list(series), window))
    assert read is not None
    assert read.crest.valid_time == cycle + timedelta(hours=7)
    assert window.contains(read.crest.valid_time)
    # and the shared window reaches the full hazard horizon, which a 72-hour store would not
    assert window.end == window.hazard_end and window.lost_tail_h == 0.0
    assert comparison_window(as_of=as_of, issued_at=cycle, coverage_h=72).lost_tail_h == pytest.approx(12.0)


def test_a_stale_cycle_narrows_the_shared_window_and_says_so() -> None:
    """Coverage runs out before the horizon does. Both maxima still come from ONE window."""
    cycle = datetime(2026, 8, 24, 12, tzinfo=UTC)
    as_of = cycle + timedelta(hours=40)  # older than the 24 h of headroom the store is sized for
    window = comparison_window(as_of=as_of, issued_at=cycle, coverage_h=96)
    assert window.lost_tail_h == pytest.approx(16.0) and window.hours == pytest.approx(62.0)
    official = _hydro([(window.start + timedelta(hours=h), 500.0 + h) for h in range(1, 62)])
    ensemble = _ensemble_of({
        f"member{i}": tuple((window.start + timedelta(hours=h), 500.0 + h + i) for h in range(1, 62))
        for i in range(1, 4)
    })
    result = compare(lid="MVEW1", official=official, ensemble=ensemble, window=window)
    assert agreement.QUALITY_WINDOW_TRUNCATED in result.quality
    assert "covers only the first 62 h" in result.reason
    assert window.contains(result.official_crest.valid_time)
    assert window.contains(result.model_crest.valid_time)


@respx.mock
async def test_a_cycle_too_old_to_share_a_window_is_unknown_with_the_age_in_it(sessions, tmp_path) -> None:
    """Past the point where a shared window means anything, the answer is UNKNOWN, not a level."""
    _mock_reaches()
    async with sessions() as s:
        await _store_official(s, "MVEW1")
        await _ingest_nwm(s, tmp_path)
        await s.commit()
    async with sessions() as s:
        k = as_known_at(s, datetime(2026, 8, 24, 12, tzinfo=UTC) + timedelta(hours=90))
        fp = await k.forecast_point_by_lid("MVEW1")
        a = await agreement.assess(k, fp, thresholds=_official_thresholds("MVEW1"))
        assert a.state.state is AgreementLevel.UNKNOWN
        assert "90 h old" in a.state.reason and "share only 12 h" in a.state.reason
        assert a.drivers == ()


# --------------------------------------------------------------------------------------
# finding A — a timing term is only assessable when there is a crest to time
# --------------------------------------------------------------------------------------
def test_the_shape_test_separates_a_crest_from_the_higher_end_of_a_line() -> None:
    """What counts as "there is a crest here": interior, and materially above both edges."""
    assert _hydro(_peak(1000.0, 24)).shape == agreement.SHAPE_CREST
    assert _hydro(_recession(1000.0)).shape == agreement.SHAPE_RECEDING
    assert _hydro(tuple(reversed(_recession(1000.0)))[:1] + tuple(
        (T0 + timedelta(hours=h), 600.0 + 8.0 * h) for h in range(1, 49)
    )).shape == agreement.SHAPE_RISING
    assert _hydro(_flat(1000.0)).shape == agreement.SHAPE_FLAT
    # a 3 % wobble on a flat line is not a crest, however interior its maximum happens to be
    wobbly = _hydro(_flat(1000.0, wobble=0.015))
    assert wobbly.interior and wobbly.shape == agreement.SHAPE_FLAT
    # and neither is a 2 % bump on a 30 % recession: prominence is measured against the edges
    bumped = list(_recession(1000.0))
    bumped[20] = (bumped[20][0], bumped[19][1] * 1.02)
    assert _hydro(tuple(bumped)).shape == agreement.SHAPE_RECEDING


def test_when_neither_forecast_crests_the_timing_term_is_not_invented() -> None:
    """Finding A, isolated: two recessions that agree to 0.6 % must not read as disagreement.

    The live numbers this reproduces (MVEW1, 2026-08-24): official crest 6,780.0 cfs, NWM median
    member 6,740.2 cfs — 0.6 % apart — reported `low` off a Δt of 75 h taken between the ends of
    two flat recessions inside a window only 78 h wide."""
    official = _hydro(_recession(6780.0))
    ensemble = _ensemble_of({f"member{i}": _recession(6740.2) for i in range(1, 7)})
    result = compare(lid="MVEW1", official=official, ensemble=ensemble, thresholds=MVEW1_STAGE_THRESHOLDS)
    assert abs(result.magnitude_divergence) < 0.006
    assert result.timing_divergence_h is None and not result.timing_assessable
    assert agreement.QUALITY_TIMING_NOT_ASSESSABLE in result.quality
    assert result.state is AgreementLevel.HIGH
    assert "neither crests inside this window" in result.reason
    assert "disagree" not in result.reason
    assert any("width of the window" in n for n in result.method_record["notes"])
    # the driver says the same thing: no number, and the reason for there being no number
    drivers = agreement._drivers(result, official_key="off", model_key="mod")
    timing = next(d for d in drivers if d.feature == "agreement_crest_timing_delta_h")
    assert timing.value is None and timing.direction == "neither_forecast_crests_in_window"


def test_a_one_sided_crest_is_a_shape_disagreement_and_caps_the_level() -> None:
    """One forecast peaks in the window and the other does not. That is a real difference —
    but it is a difference in shape, not an offset in timing, so it is never expressed as Δt."""
    official = _hydro(_flat(1000.0))
    ensemble = _ensemble_of({f"member{i}": _peak(1020.0 + i, 30) for i in range(1, 4)})
    result = compare(lid="AUBW1", official=official, ensemble=ensemble,
                     thresholds=AUBW1_FLOW_THRESHOLDS, floor=AUBW1_FLOW_THRESHOLDS.action)
    assert abs(result.magnitude_divergence) < 0.01  # magnitudes agree to well under 1 %
    assert result.timing_divergence_h is None and not result.timing_assessable
    assert agreement.QUALITY_SHAPE_DISAGREEMENT in result.quality
    assert result.state is AgreementLevel.MODERATE  # capped: agreement, but not full agreement
    assert "only NWM crests inside this window" in result.reason
    timing = next(d for d in agreement._drivers(result, official_key="off", model_key="mod")
                  if d.feature == "agreement_crest_timing_delta_h")
    assert timing.direction == "only_one_forecast_crests_in_window"


def test_a_genuine_disagreement_still_reads_low() -> None:
    """The other half of finding A: making `low` mean something requires it to still happen."""
    official = _hydro(_peak(6000.0, 12))
    ensemble = _ensemble_of({f"member{i}": _peak(15_000.0 + 500 * i, 60) for i in range(1, 4)})
    result = compare(lid="AUBW1", official=official, ensemble=ensemble,
                     thresholds=AUBW1_FLOW_THRESHOLDS, floor=AUBW1_FLOW_THRESHOLDS.action)
    assert result.state is AgreementLevel.LOW
    assert result.timing_assessable and result.timing_divergence_h == pytest.approx(48.0)
    assert result.magnitude_divergence == pytest.approx((16_000.0 - 6000.0) / 6000.0)
    assert result.category_steps == 3  # action -> major: three official categories apart
    assert (result.official_category, result.model_category) == (FloodCategory.ACTION, FloodCategory.MAJOR)
    assert "167% above" in result.reason and "48 h later" in result.reason
    # and a large timing gap alone is enough, even when both crest at the same height
    same_height = compare(
        lid="AUBW1", official=official,
        ensemble=_ensemble_of({f"member{i}": _peak(6000.0, 60) for i in range(1, 4)}),
        thresholds=AUBW1_FLOW_THRESHOLDS, floor=AUBW1_FLOW_THRESHOLDS.action,
    )
    assert same_height.state is AgreementLevel.LOW and same_height.timing_divergence_h == pytest.approx(48.0)


def test_opposite_trends_without_a_crest_are_not_high_agreement_and_not_disagreement() -> None:
    """Two maxima 0.5 % apart, one hydrograph rising and the other receding.

    Measured live 2026-08-24 at MVEW1 and WRAW1: the official run rises across the window while
    NWM recedes across it. Neither places a crest inside the window, so there is still no timing
    to compare — but "HIGH agreement" would claim the two forecasts point the same way when they
    do not. MODERATE, with both shapes named, is what the inputs support."""
    official = _hydro(tuple((T0 + timedelta(hours=h), 1000.0 + 6.0 * h) for h in range(49)))
    ensemble = _ensemble_of({f"member{i}": _recession(1290.0) for i in range(1, 4)})
    result = compare(lid="MVEW1", official=official, ensemble=ensemble, thresholds=MVEW1_STAGE_THRESHOLDS)
    assert (result.official_shape, result.model_shape) == (agreement.SHAPE_RISING, agreement.SHAPE_RECEDING)
    assert abs(result.magnitude_divergence) < 0.006
    assert not result.timing_assessable and result.timing_divergence_h is None
    assert agreement.QUALITY_TREND_DISAGREEMENT in result.quality
    assert result.state is AgreementLevel.MODERATE  # not HIGH, and emphatically not LOW
    assert "official rising, NWM receding" in result.reason
    assert any("point in opposite directions" in n for n in result.method_record["notes"])

    # a flat hydrograph has no trend to contradict, so it never triggers the cap
    flat = compare(lid="MVEW1", official=_hydro(_flat(1290.0)), ensemble=ensemble,
                   thresholds=MVEW1_STAGE_THRESHOLDS)
    assert agreement.QUALITY_TREND_DISAGREEMENT not in flat.quality
    assert flat.state is AgreementLevel.HIGH


@respx.mock
async def test_a_stored_cycle_this_version_cannot_read_is_unknown_not_a_partial_ensemble(sessions, tmp_path) -> None:
    """Half of a decodable ensemble is not an ensemble: the median moves and the denominator lies."""
    _mock_reaches()
    async with sessions() as s:
        await _store_official(s, "MVEW1")
        await _ingest_nwm(s, tmp_path)
        await s.commit()
    async with sessions() as s:
        row = (
            await s.execute(
                select(DerivedFeature).where(
                    DerivedFeature.feature == FEATURE_MEMBER_SERIES,
                    DerivedFeature.scope_id == "fp:nwps:MVEW1",
                )
            )
        ).scalars().one()
        payload = dict(row.values_json)
        payload["series"] = {**payload["series"], "member4": {"encoding": "rle@9", "flow": [1, 2]}}
        row.values_json = payload
        await s.commit()
    async with sessions() as s:
        k = as_known_at(s, AS_OF)
        fp = await k.forecast_point_by_lid("MVEW1")
        a = await agreement.assess(k, fp, thresholds=_official_thresholds("MVEW1"))
        assert a.state.state is AgreementLevel.UNKNOWN
        assert "no member values" in a.state.reason
        assert a.drivers == () and a.model_probability is None

    async with sessions() as s:
        row = (
            await s.execute(
                select(DerivedFeature).where(
                    DerivedFeature.feature == FEATURE_MEMBER_SERIES,
                    DerivedFeature.scope_id == "fp:nwps:MVEW1",
                )
            )
        ).scalars().one()
        row.values_json = {**row.values_json, "schema": "nwm-member-series@9"}
        await s.commit()
    async with sessions() as s:
        k = as_known_at(s, AS_OF)
        fp = await k.forecast_point_by_lid("MVEW1")
        a = await agreement.assess(k, fp, thresholds=_official_thresholds("MVEW1"))
        assert a.state.state is AgreementLevel.UNKNOWN
        assert "nwm-member-series@9" in a.state.reason and "does not read" in a.state.reason
