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
from cascade_core.models import ForecastPoint, ForecastRun, ForecastValue, RawArtifact, SourceProduct
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
    MemberCrest,
    ModelEnsembleCrest,
    compare,
    member_exceedance,
)
from cascade_hydrology.assemble import assess_point, forecast_run_ref, resolved_source_kind
from cascade_hydrology.category import ThresholdSet
from cascade_hydrology.surfaces import Crest
from cascade_providers_nwps.normalize import forecast_from_stageflow, thresholds_from_gauge
from cascade_providers_nwps.parser import parse_gauge, parse_stageflow
from cascade_providers_nwps.reaches_jobs import (
    FEATURE_CREST_SUMMARY,
    METHOD_MEMBER_CREST,
    EmptyCycleError,
    run_fetch_medium_range,
)
from cascade_providers_nwps.reaches_normalize import NormalizeError, crest_summary, model_run_from_ensemble
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


def test_the_median_is_a_member_and_the_mean_is_never_one() -> None:
    """The lower-median rule on the diverged fixture: crests 5000…15000, median member = 9500."""
    e = parse_medium_range((NWM / "medium_range_AUBW1_diverged.json").read_bytes())
    summary = crest_summary(e)
    assert summary is not None and summary.member_count == 6
    assert [c.value for c in sorted(summary.members, key=lambda c: c.value)] == [5000.0, 8000.0, 9500.0, 11000.0, 13000.0, 15000.0]
    assert summary.median_member is not None
    assert (summary.median_member.member, summary.median_member.value) == ("member3", 9500.0)
    # the provider's mean crest (10250) is carried separately and is NOT the median member
    assert summary.provider_mean_crest is not None and summary.provider_mean_crest.value == 10250.0
    assert summary.median_member.value != summary.provider_mean_crest.value
    assert summary.median_member.valid_time in {c.valid_time for c in summary.members}


def test_provider_negative_fixtures() -> None:
    empty = parse_medium_range((NWM / "medium_range_MVEW1_no_series.json").read_bytes())
    assert empty.members == () and empty.mean is None and empty.reference_time is None
    assert model_run_from_ensemble(empty, retrieved_at=RETRIEVED_NWM) is None
    assert crest_summary(empty) is None
    with pytest.raises(ParseError, match="cubic-feet-per-second"):
        parse_medium_range((NWM / "medium_range_MVEW1_bad_units.json").read_bytes())
    with pytest.raises(ParseError, match="not JSON"):
        parse_medium_range((NWM / "malformed.json").read_bytes())
    mixed = parse_medium_range((NWM / "medium_range_MVEW1_mixed_cycle.json").read_bytes())
    with pytest.raises(NormalizeError, match="mixed-cycle"):
        model_run_from_ensemble(mixed, retrieved_at=RETRIEVED_NWM)
    with pytest.raises(NormalizeError, match="mixed-cycle"):
        crest_summary(mixed)
    sentinel = parse_medium_range((NWM / "medium_range_MVEW1_sentinel.json").read_bytes())
    assert [p.flow for p in sentinel.mean.points[:3]] == [None, None, None]  # -9999 -> None, never 0
    run = model_run_from_ensemble(sentinel, retrieved_at=RETRIEVED_NWM)
    assert run is not None and len(run.values) == 69 and all(v.flow is not None for v in run.values)


def test_feature_vocabulary_matches_the_writer() -> None:
    """Hydrology does not import provider packages, so the shared names are pinned by a test."""
    assert agreement.FEATURE_CREST_SUMMARY == FEATURE_CREST_SUMMARY
    assert agreement.METHOD_MEMBER_CREST == METHOD_MEMBER_CREST


# --------------------------------------------------------------------------------------
# the method: compare() — bands, UNKNOWN paths, member fraction
# --------------------------------------------------------------------------------------
T0 = datetime(2026, 12, 10, 12, tzinfo=UTC)


def _ensemble(values: dict[str, tuple[float, int]]) -> ModelEnsembleCrest:
    """{member: (crest cfs, hours after T0)} -> the stored ensemble shape, lower-median chosen."""
    members = tuple(MemberCrest(m, v, T0 + timedelta(hours=h)) for m, (v, h) in sorted(values.items()))
    ordered = sorted(members, key=lambda c: (c.value, c.valid_time))
    return ModelEnsembleCrest(
        issued_at=T0, window_h=72, unit="cfs", members=members,
        median_member=ordered[(len(ordered) - 1) // 2], median_rule="lower_median_member",
    )


def test_bands_are_reproducible_and_monotone() -> None:
    official = Crest(value=10_000.0, valid_time=T0 + timedelta(hours=24))
    near = compare(lid="AUBW1", official=official, ensemble=_ensemble({"m1": (10_500.0, 26), "m2": (11_000.0, 27), "m3": (11_500.0, 28)}))
    assert near.state is AgreementLevel.HIGH and near.reason is None
    assert near.magnitude_divergence == pytest.approx(0.10) and near.timing_divergence_h == pytest.approx(3.0)
    mid = compare(lid="AUBW1", official=official, ensemble=_ensemble({"m1": (14_000.0, 36), "m2": (14_500.0, 38), "m3": (15_000.0, 40)}))
    assert mid.state is AgreementLevel.MODERATE
    far = compare(lid="AUBW1", official=official, ensemble=_ensemble({"m1": (20_000.0, 60), "m2": (21_000.0, 62), "m3": (22_000.0, 64)}))
    assert far.state is AgreementLevel.LOW and far.reason is not None and "%" in far.reason
    # timing alone is enough to break agreement, at any magnitude
    late = compare(lid="AUBW1", official=official, ensemble=_ensemble({"m1": (10_000.0, 60), "m2": (10_000.0, 61), "m3": (10_000.0, 62)}))
    assert late.state is AgreementLevel.LOW and late.magnitude_divergence == pytest.approx(0.0)
    # and the bands themselves are the versioned parameter block, carrying their assumption
    assert (BANDS.high_magnitude, BANDS.moderate_magnitude) == (0.25, 0.60)
    assert (BANDS.high_timing_h, BANDS.moderate_timing_h) == (6.0, 18.0)
    assert "not calibrated" in BANDS.assumption or "uncalibrated" in BANDS.assumption


def test_unknown_paths_each_name_their_missing_input() -> None:
    ens = _ensemble({"m1": (100.0, 4), "m2": (110.0, 5), "m3": (120.0, 6)})
    no_official = compare(lid="MVEW1", official=None, ensemble=ens)
    assert no_official.state is AgreementLevel.UNKNOWN and "hazard window" in no_official.reason
    no_model = compare(lid="MVEW1", official=Crest(100.0, T0), ensemble=None)
    assert no_model.state is AgreementLevel.UNKNOWN and "NWM" in no_model.reason
    empty = ModelEnsembleCrest(issued_at=T0, window_h=72, unit="cfs", members=(), median_member=None, median_rule="lower_median_member")
    assert compare(lid="MVEW1", official=Crest(100.0, T0), ensemble=empty).state is AgreementLevel.UNKNOWN
    zero = compare(lid="MVEW1", official=Crest(0.0, T0), ensemble=ens)
    assert zero.state is AgreementLevel.UNKNOWN and "denominator" in zero.reason
    assert zero.magnitude_divergence is None  # refused, not computed and hidden


def test_the_floor_stops_a_small_official_crest_manufacturing_disagreement() -> None:
    """A 300 cfs summer official crest against a 380 cfs model crest is a 25% ratio and nothing
    else; against the official ACTION flow it is 1%. The floor is the honest denominator."""
    official, ens = Crest(300.0, T0), _ensemble({"m1": (370.0, 1), "m2": (380.0, 2), "m3": (390.0, 3)})
    unfloored = compare(lid="AUBW1", official=official, ensemble=ens)
    floored = compare(lid="AUBW1", official=official, ensemble=ens, thresholds=AUBW1_FLOW_THRESHOLDS, floor=AUBW1_FLOW_THRESHOLDS.action)
    assert unfloored.magnitude_divergence == pytest.approx(80 / 300)
    assert floored.magnitude_divergence == pytest.approx(80 / 6000)
    assert "no_divergence_floor" in unfloored.quality and floored.quality == ()


def test_a_limitation_that_stays_in_the_dataclass_has_not_travelled_with_its_number() -> None:
    """Both quality flags must reach `AgreementState.reason`, not stop at `AgreementResult`.

    Measured live 2026-08-24 on the real 12Z cycle: all six NWM members carried ONE distinct
    crest at all six seed reaches, so `fraction: k/6` was a binary indicator dressed as an
    empirical frequency; and at the three stage-threshold points there is no official action
    FLOW to floor the divergence denominator with, so a 120 cfs summer crest made "63% above"
    out of 76 cfs. Neither fact reached the client before these caveats existed."""
    identical = _ensemble({f"m{i}": (9500.0, 3) for i in range(1, 7)})
    degenerate = compare(lid="AUBW1", official=Crest(9400.0, T0 + timedelta(hours=3)), ensemble=identical,
                         thresholds=AUBW1_FLOW_THRESHOLDS, floor=AUBW1_FLOW_THRESHOLDS.action)
    assert agreement.QUALITY_DEGENERATE_ENSEMBLE in degenerate.quality
    assert degenerate.model_probability["distinct_member_crests"] == 1.0
    assert degenerate.model_probability["members"] == 6.0  # the count is still the observed one

    spread = _ensemble({"m1": (9000.0, 3), "m2": (9500.0, 4), "m3": (10_000.0, 5)})
    assert agreement.QUALITY_DEGENERATE_ENSEMBLE not in compare(
        lid="AUBW1", official=Crest(9400.0, T0 + timedelta(hours=3)), ensemble=spread,
        thresholds=AUBW1_FLOW_THRESHOLDS, floor=AUBW1_FLOW_THRESHOLDS.action).quality
    assert member_exceedance(spread.members, AUBW1_FLOW_THRESHOLDS)["distinct_member_crests"] == 3.0

    # and the sentences themselves: a flag that never becomes a sentence is a flag nobody reads
    unfloored = compare(lid="MVEW1", official=Crest(120.0, T0), ensemble=identical, thresholds=MVEW1_STAGE_THRESHOLDS)
    sentences = " ".join(agreement._caveats(unfloored))
    assert "floor the denominator" in sentences and "independent opinions" in sentences


def test_category_is_compared_only_where_official_thresholds_are_flow() -> None:
    official = Crest(9500.0, T0 + timedelta(hours=2))
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
async def test_ingest_writes_one_run_and_seven_derived_rows_per_reach(sessions, tmp_path) -> None:
    """Design §3.4 volume control, asserted: 72 forecast values + 6 member crests + 1 summary."""
    _mock_reaches()
    async with sessions() as s:
        assert len(await _points_with_reach(s)) == 6  # the seed addendum landed all five ids
        written = await _ingest_nwm(s, tmp_path)
        await s.commit()
    assert written == 6 * (1 + 72 + 6 + 1)
    async with sessions() as s:
        k = as_known_at(s, AS_OF)
        run, ensemble = await agreement.latest_model_ensemble(k, "fp:nwps:MVEW1")
        assert run is not None and run.product_id == PRODUCT_NWM_MR and run.datum is None
        assert ensemble is not None and ensemble.member_count == 6
        assert ensemble.median_rule == "lower_median_member"
        assert len(await k.forecast_values(run.id)) == 72
        rows = await k.derived_features(FEATURE_CREST_SUMMARY, "fp:nwps:MVEW1", method_id=METHOD_MEMBER_CREST,
                                        valid_from=run.issued_at, valid_until=run.issued_at + timedelta(days=4))
        assert len(rows) == 1 and rows[0].product_id == PRODUCT_NWM_MR and rows[0].unit == "cfs"
        assert rows[0].values_json["member_count"] == 6 and rows[0].raw_inputs_hash
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
            assert "defined in stage" in out[lid].state.reason  # the caveat is rendered, not dropped

        # and the levels themselves, from real numbers (see the docstring)
        assert out["NKSW1"].state.state is AgreementLevel.HIGH
        assert out["WRAW1"].state.state is AgreementLevel.HIGH
        assert out["MVEW1"].state.state is AgreementLevel.LOW  # 63 h apart on the crest timing
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

    official, ens = Crest(10_000.0, T0), _ensemble({"m1": (20_000.0, 1), "m2": (20_000.0, 2), "m3": (20_000.0, 3)})
    r = compare(lid="AUBW1", official=official, ensemble=ens)
    midpoint = 15_000.0
    assert r.official_crest.value == 10_000.0 and r.model_crest.value == 20_000.0
    assert midpoint not in {r.official_crest.value, r.model_crest.value, r.magnitude_divergence}
    # the model crest is a member's own number, never a value derived from the official one
    assert r.model_crest.value in {m.value for m in ens.members}


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
        assert await _ingest_nwm(s, tmp_path) == 1 + 72 + 6 + 1  # one reach answered; that is enough
        await s.commit()


def test_the_median_member_is_recoverable_but_only_under_the_rule_we_implement() -> None:
    """A stored ladder whose named median is missing is recoverable; an unknown rule is not."""
    ladder = {
        "window_h": 72, "unit": "cfs", "member_count": 3, "median_rule": "lower_median_member",
        "median_member": "member9_typo",
        "members": {
            "member1": {"crest": 100.0, "valid_time": "2026-12-10T13:00:00+00:00"},
            "member2": {"crest": 200.0, "valid_time": "2026-12-10T14:00:00+00:00"},
            "member3": {"crest": 300.0, "valid_time": "2026-12-10T15:00:00+00:00"},
        },
    }
    recovered = agreement.ensemble_from_feature(ladder, issued_at=T0)
    assert recovered is not None and recovered.median_member.member == "member2"
    other_rule = agreement.ensemble_from_feature({**ladder, "median_rule": "weighted_mean@2.0"}, issued_at=T0)
    assert other_rule is not None and other_rule.median_member is None
    assert compare(lid="MVEW1", official=Crest(150.0, T0), ensemble=other_rule).state is AgreementLevel.UNKNOWN
    assert agreement.ensemble_from_feature(None, issued_at=T0) is None
    assert agreement.ensemble_from_feature(ladder, issued_at=None) is None


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
