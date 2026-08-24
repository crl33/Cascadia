"""ContractEnvelope assembly from rows read through `as_known_at` (docs/VISUALIZATION_CONTRACTS.md).

Every scientific value gets a ProvenanceRef with freshness computed at read time relative to the
knowledge time; UNKNOWN states carry reasons; official thresholds/forecasts keep their basis,
unit and datum; the basin's hazard is the outlet forecast point's official forecast crest
category. No colour, camera or renderer concept is produced here."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from cascade_contracts import (
    ConfidenceLabel,
    ContractEnvelope,
    FloodCategory,
    Freshness,
    FreshnessState,
    Headroom,
    OfficialForecastSummary,
    ProvenanceRef,
    Quantity,
    RiverVisualizationState,
    SourceKind,
    Thresholds,
    TimeContext,
    Trend,
    TruthClass,
)
from cascade_contracts.visualization import (
    AgreementLevel,
    AgreementState,
    BasinSurfaces,
    BasinVisualizationState,
    GeometryRef,
    HazardState,
    ObservedRiverState,
    Regulation,
    SurfaceLevel,
    SurfaceState,
    Topology,
)
from cascade_core.freshness import compute_freshness
from cascade_core.knowledge import Knowledge
from cascade_core.models import Basin, ForecastPoint, SourceProduct, Threshold
from cascade_core.registry import (
    PRODUCT_NWPS_FORECAST,
    PRODUCT_NWPS_THRESHOLDS,
    PRODUCT_USGS_IV,
    SRC_CASCADE,
    SRC_NWPS,
    SRC_USGS,
)
from cascade_hydrology import surfaces
from cascade_hydrology.category import CategoryResult, Measure, ThresholdSet, categorize
from cascade_hydrology.headroom import headroom as compute_headroom
from cascade_hydrology.trend import rate_of_rise

RIVER_REGULATION = {"regulated_upper": "regulated", "regulated": "regulated", "partially_regulated": "partially_regulated", "natural": "natural"}


def threshold_set(rows: dict[str, Threshold]) -> ThresholdSet | None:
    """Only OFFICIAL rows may form a ThresholdSet; CONFIGURED rows are refused by type here."""
    official = {c: r for c, r in rows.items() if r.source_kind == "OFFICIAL_FORECAST"}
    if not official:
        return None
    bases = {(r.basis, r.unit, r.datum) for r in official.values()}
    if len(bases) != 1:
        return None  # inconsistent basis/unit/datum across categories is UNKNOWN, never a guess
    basis, unit, datum = next(iter(bases))
    return ThresholdSet(basis=basis, unit=unit, datum=datum, **{c: r.value for c, r in official.items()})


def _fresh(products: dict[str, SourceProduct], product_id: str, *, valid_time: datetime | None, retrieved_at: datetime | None, now: datetime) -> Freshness:
    p = products.get(product_id)
    return compute_freshness(
        expected_cadence_seconds=p.expected_cadence_seconds if p else None,
        grace_seconds=p.grace_seconds if p else None,
        valid_time=valid_time,
        retrieved_at=retrieved_at,
        now=now,
    )


@dataclass
class PointAssessment:
    item: RiverVisualizationState
    refs: dict[str, ProvenanceRef] = field(default_factory=dict)
    hazard: CategoryResult = field(default_factory=lambda: CategoryResult(FloodCategory.UNKNOWN, "not assessed"))
    hazard_ref: str = ""


async def assess_point(k: Knowledge, fp: ForecastPoint, basin: Basin | None, products: dict[str, SourceProduct]) -> PointAssessment:
    lid = fp.lid.lower()
    refs: dict[str, ProvenanceRef] = {}
    now = k.as_of

    # 1. official thresholds known at T
    th_rows = await k.thresholds(fp.id)
    tset = threshold_set(th_rows)
    thresholds_model: Thresholds | None = None
    if tset is not None:
        key = f"nwps-thresholds-{lid}"
        latest = max(th_rows.values(), key=lambda r: r.retrieved_at)
        refs[key] = ProvenanceRef(
            source_id=SRC_NWPS,
            source_kind=SourceKind.OFFICIAL_FORECAST,
            product_id=PRODUCT_NWPS_THRESHOLDS,
            retrieved_at=latest.retrieved_at,
            freshness=_fresh(products, PRODUCT_NWPS_THRESHOLDS, valid_time=None, retrieved_at=latest.retrieved_at, now=now),
            label="Official NWS flood categories (NWPS)",
            raw_artifact_id=str(latest.raw_artifact_id),
        )
        thresholds_model = Thresholds(basis=tset.basis, unit=tset.unit, datum=tset.datum, action=tset.action, minor=tset.minor, moderate=tset.moderate, major=tset.major, prov=key)
    basis = tset.basis if tset else "stage"
    other = "flow" if basis == "stage" else "stage"

    # 2. latest observation known at T (USGS), primary = threshold basis
    observed: ObservedRiverState | None = None
    measure: Measure | None = None
    obs_key = ""
    primary = await k.latest_observation(fp.station_id, basis) if fp.station_id else None
    if primary is not None:
        station = await k.station(primary.station_id)
        site = station.external_id if station else primary.station_id
        obs_key = f"usgs-iv-{site}"
        refs[obs_key] = ProvenanceRef(
            source_id=SRC_USGS,
            source_kind=SourceKind.OBSERVED,
            product_id=PRODUCT_USGS_IV,
            valid_time=primary.valid_time,
            retrieved_at=primary.retrieved_at,
            freshness=_fresh(products, PRODUCT_USGS_IV, valid_time=primary.valid_time, retrieved_at=primary.retrieved_at, now=now),
            quality=tuple(primary.quality),
            label="USGS instantaneous values" + (" (provisional)" if "provisional" in primary.quality else ""),
            raw_artifact_id=str(primary.raw_artifact_id),
        )
        same_time = await k.observations(fp.station_id, other, since=primary.valid_time, until=primary.valid_time)
        secondary = same_time[0] if same_time and same_time[0].value is not None else None
        quantities: dict[str, Quantity | None] = {basis: None, other: None}
        if primary.value is not None:
            quantities[basis] = Quantity(value=primary.value, unit=primary.unit, datum=primary.datum)
            measure = Measure(basis=basis, value=primary.value, unit=primary.unit, datum=primary.datum)
        if secondary is not None:
            quantities[other] = Quantity(value=secondary.value, unit=secondary.unit, datum=secondary.datum)
        observed = ObservedRiverState(prov=obs_key, truth=TruthClass.OBSERVATION, stage=quantities["stage"], flow=quantities["flow"], valid_time=primary.valid_time)

    cat = categorize(measure, tset, label=f"Observed {basis}")
    if primary is not None and primary.value is None:
        cat = CategoryResult(FloodCategory.UNKNOWN, f"latest observation carries no number (quality: {', '.join(primary.quality) or 'none'})")

    # 3. trend over 6 h ending at T, from stored observations
    trend_model: Trend | None = None
    trend = None
    if primary is not None and fp.station_id:
        window = await k.observations(fp.station_id, basis, since=now - timedelta(hours=6))
        trend = rate_of_rise([(o.valid_time, o.value) for o in window if o.value is not None], basis=basis, unit=primary.unit, end=now, window_h=6)
        tkey = f"cascade-trend-{lid}"
        refs[tkey] = ProvenanceRef(
            source_id=SRC_CASCADE,
            source_kind=SourceKind.DERIVED,
            method_id="method:rate-of-rise@1.0.0",
            valid_time=primary.valid_time,
            retrieved_at=primary.retrieved_at,
            freshness=refs[obs_key].freshness,
            label=f"Cascade rate of rise over 6 h from stored USGS observations{'' if trend.reason is None else ' — ' + trend.reason}",
        )
        rate_q = None if trend.rate is None else Quantity(value=round(trend.rate, 4), unit=trend.unit or f"{primary.unit}/h")
        trend_model = Trend(prov=tkey, truth=TruthClass.CASCADE_DERIVED, window_h=6, rate=rate_q, direction=trend.direction)

    # 4. headroom to the next official category
    headroom_model: Headroom | None = None
    hr = compute_headroom(measure, tset, rate_per_h=None if trend is None else trend.rate, direction="unknown" if trend is None else trend.direction)
    if hr is not None:
        hkey = f"cascade-headroom-{lid}"
        refs[hkey] = ProvenanceRef(
            source_id=SRC_CASCADE,
            source_kind=SourceKind.DERIVED,
            method_id=f"method:{hr.basis}-headroom@1.0.0",
            valid_time=primary.valid_time if primary else None,
            freshness=refs[obs_key].freshness if obs_key else Freshness(state=FreshnessState.MISSING),
            label=f"Cascade {hr.basis} headroom to official {hr.to_category.value} threshold",
        )
        headroom_model = Headroom(
            basis=hr.basis,
            to_category=hr.to_category,
            value=None if hr.value is None else Quantity(value=round(hr.value, 3), unit=hr.unit, datum=hr.datum),
            time_to_threshold_h=None if hr.time_to_threshold_h is None else round(hr.time_to_threshold_h, 2),
            prov=hkey,
            reason=hr.reason,
        )

    # 5. official forecast known at T and the 72 h hazard
    fkey = f"nwps-forecast-{lid}"
    forecast_model: OfficialForecastSummary | None = None
    run = await k.latest_forecast_run(fp.id)
    if run is None:
        hazard = CategoryResult(FloodCategory.UNKNOWN, "no official NWRFC forecast known at this knowledge time")
        refs[fkey] = ProvenanceRef(source_id=SRC_NWPS, source_kind=SourceKind.UNKNOWN, product_id=PRODUCT_NWPS_FORECAST, freshness=Freshness(state=FreshnessState.MISSING), label="No NWRFC forecast known at this knowledge time")
    else:
        values = await k.forecast_values(run.id)
        fbasis = tset.basis if tset else run.primary_variable
        funit, fdatum = ("ft", run.datum) if fbasis == "stage" else ("cfs", None)
        series = [(v.valid_time, v.stage if fbasis == "stage" else v.flow) for v in values]
        crest = surfaces.forecast_crest(series, as_of=now)
        hazard = surfaces.hazard_category(crest, basis=fbasis, unit=funit, datum=fdatum, thresholds=tset)
        refs[fkey] = ProvenanceRef(
            source_id=SRC_NWPS,
            source_kind=SourceKind.OFFICIAL_FORECAST,
            product_id=PRODUCT_NWPS_FORECAST,
            issued_at=run.issued_at,
            valid_time=None if crest is None else crest.valid_time,
            retrieved_at=run.retrieved_at,
            freshness=_fresh(products, PRODUCT_NWPS_FORECAST, valid_time=run.issued_at, retrieved_at=run.retrieved_at, now=now),
            label=f"{run.issuer} official river forecast via NOAA NWPS",
            raw_artifact_id=str(run.raw_artifact_id),
        )
        forecast_model = OfficialForecastSummary(
            prov=fkey,
            truth=TruthClass.AUTHORITATIVE_MODEL,
            issued_at=run.issued_at,
            issuer=run.issuer,
            crest=None if crest is None else Quantity(value=crest.value, unit=funit, datum=fdatum),
            crest_valid_time=None if crest is None else crest.valid_time,
            category=hazard.category,
            points=len(values),
        )

    reg_class = RIVER_REGULATION.get(basin.regulation_class if basin else "", "unknown")
    item = RiverVisualizationState(
        id=fp.id,
        name=fp.name,
        station_id=fp.station_id,
        reach_id=fp.reach_id,
        basin_id=fp.basin_id or "basin:unknown",
        observed=observed,
        observed_category=cat.category,
        observed_category_reason=cat.reason,
        trend=trend_model,
        headroom=headroom_model,
        official_forecast=forecast_model,
        thresholds=thresholds_model,
        topology=Topology(upstream=tuple(f"fp:nwps:{u}" for u in fp.upstream_lids), downstream=tuple(f"fp:nwps:{d}" for d in fp.downstream_lids)),
        regulation=Regulation(class_=reg_class, regulated_by=tuple(basin.regulated_by) if basin else ()),
        location=(fp.lon, fp.lat) if fp.lon is not None and fp.lat is not None else None,
        flow_visual_intensity=None,
    )
    return PointAssessment(item=item, refs=refs, hazard=hazard, hazard_ref=fkey)


def _envelope(contract: str, items: list, refs: dict[str, ProvenanceRef], *, as_of: datetime, generated_at: datetime) -> ContractEnvelope:
    mode = "now" if abs((generated_at - as_of).total_seconds()) <= 300 else "past"
    return ContractEnvelope(contract=contract, generated_at=generated_at, as_of=as_of, time=TimeContext(valid=as_of, mode=mode), items=tuple(items), provenance_refs=refs)


async def river_envelope(k: Knowledge, fps: list[ForecastPoint], *, generated_at: datetime) -> ContractEnvelope:
    products = await k.products()
    items, refs = [], {}
    for fp in fps:
        basin = await k.basin(fp.basin_id) if fp.basin_id else None
        pa = await assess_point(k, fp, basin, products)
        items.append(pa.item)
        refs.update(pa.refs)
    return _envelope("RiverVisualizationState", items, refs, as_of=k.as_of, generated_at=generated_at)


CASCADE_REFS = {
    "cascade-susceptibility": ProvenanceRef(source_id=SRC_CASCADE, source_kind=SourceKind.EXPERIMENTAL, method_id="method:susceptibility-index@0.0.0", freshness=Freshness(state=FreshnessState.MISSING), label="Cascade experimental susceptibility index (not yet computed)"),
    "cascade-forcing": ProvenanceRef(source_id=SRC_CASCADE, source_kind=SourceKind.EXPERIMENTAL, method_id="method:forcing-assessment@0.0.0", freshness=Freshness(state=FreshnessState.MISSING), label="Cascade forcing assessment (not yet computed)"),
}


async def basin_envelope(k: Knowledge, basins: list[Basin], *, generated_at: datetime) -> ContractEnvelope:
    products = await k.products()
    items, refs = [], dict(CASCADE_REFS)
    for basin in basins:
        outlet = await k.forecast_point_by_lid(basin.outlet_fp_id.split(":")[-1]) if basin.outlet_fp_id else None
        if outlet is not None:
            pa = await assess_point(k, outlet, basin, products)
            hazard, hazard_ref = pa.hazard, pa.hazard_ref
            refs[hazard_ref] = pa.refs[hazard_ref]
        else:
            hazard_ref = f"missing-outlet-{basin.id.split(':')[-1]}"
            hazard = CategoryResult(FloodCategory.UNKNOWN, "basin has no outlet forecast point configured")
            refs[hazard_ref] = ProvenanceRef(source_id=SRC_CASCADE, source_kind=SourceKind.UNKNOWN, freshness=Freshness(state=FreshnessState.MISSING), label="No outlet forecast point")
        items.append(
            BasinVisualizationState(
                id=basin.id,
                name=basin.name,
                regulation_class=basin.regulation_class,
                surfaces=BasinSurfaces(
                    susceptibility=SurfaceState(state=SurfaceLevel.UNKNOWN, prov="cascade-susceptibility", truth=TruthClass.CASCADE_DERIVED, confidence=ConfidenceLabel.UNKNOWN, experimental=True, reason=surfaces.SUSCEPTIBILITY_REASON),
                    forcing=SurfaceState(state=SurfaceLevel.UNKNOWN, horizon_h=72, prov="cascade-forcing", truth=TruthClass.CASCADE_DERIVED, confidence=ConfidenceLabel.UNKNOWN, experimental=True, reason=surfaces.FORCING_REASON),
                    hazard=HazardState(horizon_h=surfaces.HAZARD_HORIZON_H, official_category=hazard.category, official_prov=hazard_ref, prov=hazard_ref, truth=TruthClass.AUTHORITATIVE_MODEL, reason=hazard.reason),
                    agreement=AgreementState(state=AgreementLevel.UNKNOWN, prov=()),  # reason: surfaces.AGREEMENT_REASON (contract has no reason field yet)
                ),
                tension=None,
                headline_drivers=(),
                official_alerts=(),
                outlet_forecast_point_id=basin.outlet_fp_id,
                geometry_ref=GeometryRef(lod="basin", feature_id=basin.id, url=f"/basins/{basin.id}/geometry?lod=basin"),
                label_priority=2,
            )
        )
    return _envelope("BasinVisualizationState", items, refs, as_of=k.as_of, generated_at=generated_at)
