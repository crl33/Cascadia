"""ContractEnvelope assembly from rows read through `as_known_at` (docs/VISUALIZATION_CONTRACTS.md).

Every scientific value gets a ProvenanceRef with freshness computed at read time relative to the
knowledge time; UNKNOWN states carry reasons; official thresholds/forecasts keep their basis,
unit and datum; the basin's hazard is the outlet forecast point's official forecast crest
category. No colour, camera or renderer concept is produced here."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from cascade_contracts import (
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
    Driver,
    GeometryRef,
    HazardState,
    ObservedRiverState,
    Regulation,
    SurfaceLevel,
    SurfaceState,
    Topology,
)
from cascade_core.freshness import compute_freshness
from cascade_core.knowledge import OFFICIAL_FORECAST_PRODUCTS, Knowledge
from cascade_core.models import (
    Basin,
    ForecastPoint,
    ForecastRun,
    SourceProduct,
    Threshold,
)
from cascade_core.registry import (
    PRODUCT_NWPS_FORECAST,
    PRODUCT_NWPS_THRESHOLDS,
    PRODUCT_USGS_IV,
    SOURCES,
    SRC_CASCADE,
    SRC_NWPS,
    SRC_USGS,
)
from cascade_geo.hypsometry import BasinHypsometry
from cascade_hydrology import agreement, forcing, surfaces, susceptibility
from cascade_hydrology.category import CategoryResult, Measure, ThresholdSet, categorize
from cascade_hydrology.headroom import headroom as compute_headroom
from cascade_hydrology.surfaces import SurfaceReason, require_reason
from cascade_hydrology.trend import METHOD_ID as TREND_METHOD_ID
from cascade_hydrology.trend import TidalClass, estimate_trend

RIVER_REGULATION = {"regulated_upper": "regulated", "regulated": "regulated", "partially_regulated": "partially_regulated", "natural": "natural"}

# SourceKind per source id, read from the registry (cascade_core.registry declares it once and
# the seeded `data_source` rows are merged from the same tuple). Nothing in this module may
# spell a kind out beside a value: that is exactly how an NWM run would end up badged as the
# NWRFC forecast (design §3.4 defect 2, docs/DATA_DOCTRINE.md §2).
_SOURCE_KIND_BY_ID: dict[str, str] = {str(s["id"]): str(s["kind"]) for s in SOURCES}
UNKNOWN_SOURCE_ID = "src:unknown"


def resolved_source_kind(product: SourceProduct | None) -> SourceKind:
    """The SourceKind of a product's source, resolved from the registry; UNKNOWN when it misses.

    UNKNOWN is the only safe default. Defaulting to OFFICIAL_FORECAST — which this module did
    until P3 — means an unrecognised product silently inherits the authority of the National
    Weather Service; defaulting to UNKNOWN means the client shows an unbadged value and someone
    goes and registers the source."""
    if product is None:
        return SourceKind.UNKNOWN
    try:
        return SourceKind(_SOURCE_KIND_BY_ID[product.source_id])
    except (KeyError, ValueError):
        return SourceKind.UNKNOWN


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


def forecast_run_ref(run: ForecastRun, products: dict[str, SourceProduct], *, now: datetime, valid_time: datetime | None = None) -> ProvenanceRef:
    """The provenance record of one stored forecast run, wherever the run is displayed.

    Identity comes from the run's own SourceProduct — a run reconstructed from archived FLS
    text is not an NWPS forecast and must not claim to be one, and an NWM medium-range run is
    MODELED, never OFFICIAL_FORECAST. **`source_kind` is resolved from the registry** through
    `SourceProduct.source_id`; it is never spelled out here, because `forecast_run` holds more
    than one forecast product from P3 on and a hardcoded kind would badge every one of them as
    the National Weather Service's official forecast (design §3.4 defect 2).

    Freshness is computed at read time against the knowledge clock; `raw_artifact_id` points at
    the stored bytes the run was parsed from. The `products` lookup cannot miss
    (ForecastRun.product_id is a FK into source_product); if it somehow does, the ref stays
    constructible but claims nothing — UNKNOWN source, UNKNOWN kind, a label that names the
    product id instead of asserting an issuer."""
    product = products.get(run.product_id)
    return ProvenanceRef(
        source_id=product.source_id if product else UNKNOWN_SOURCE_ID,
        source_kind=resolved_source_kind(product),
        product_id=run.product_id,
        issued_at=run.issued_at,
        valid_time=valid_time,
        retrieved_at=run.retrieved_at,
        freshness=_fresh(products, run.product_id, valid_time=run.issued_at, retrieved_at=run.retrieved_at, now=now),
        label=product.label if product else f"Unregistered forecast product {run.product_id!r} issued by {run.issuer}",
        raw_artifact_id=str(run.raw_artifact_id),
    )


#: The window `assess_point` takes its rate of rise over, ending at the knowledge time. Named
#: because `prefetch_points` has to batch exactly this window for the batch to be the same read.
TREND_WINDOW_H = 6
TREND_WINDOW = timedelta(hours=TREND_WINDOW_H)


def observed_basis(tset: ThresholdSet | None) -> str:
    """The variable an observed value is judged on: the official thresholds' basis, else stage.

    One function, because `prefetch_points` has to know which variable a point will be read on
    in order to batch that read, and a second copy of this rule would be a way for the batch to
    fetch one variable while `assess_point` went on to read the other.
    """
    return tset.basis if tset is not None else "stage"


def other_variable(basis: str) -> str:
    return "flow" if basis == "stage" else "stage"


async def prefetch_points(k: Knowledge, fps: Sequence[ForecastPoint]) -> None:
    """Read everything `assess_point` needs for ``fps`` in six statements instead of seven each.

    Pure warm-up: every read below is one the per-point path would issue anyway, asked once
    across all the points, and the answers land in the request-scoped memo `Knowledge` keys by
    exactly those arguments. `assess_point` is unchanged and still reads for itself, so nothing
    here can change what it returns and no caller is obliged to call this first.

    The last two are ordered, not batched together, because the second depends on the first:
    the instant at which the *secondary* variable is wanted is the valid_time of the *primary*
    observation, and which variable is primary is the official thresholds' basis. So the
    thresholds and the latest observations are read first, and the exact windows they imply are
    then asked for in one statement covering every point.
    """
    fps = [fp for fp in fps if fp is not None]
    if not fps:
        return
    ids = [fp.id for fp in fps]
    thresholds = await k.thresholds_for(ids)
    runs = await k.latest_forecast_runs(ids, product_ids=OFFICIAL_FORECAST_PRODUCTS)
    await k.forecast_values_for([run.id for run in runs.values()])
    await k.stations_by_id([fp.station_id for fp in fps if fp.station_id])

    stations = [fp.station_id for fp in fps if fp.station_id]
    if not stations:
        return
    latest = await k.latest_observations(stations, ("stage", "flow"))
    specs: list[tuple[str, str, datetime, datetime | None]] = []
    for fp in fps:
        if not fp.station_id:
            continue
        basis = observed_basis(threshold_set(thresholds.get(fp.id, {})))
        primary = latest.get((fp.station_id, basis))
        if primary is None:
            continue  # `assess_point` reads neither of the two below without a primary value
        specs.append((fp.station_id, other_variable(basis), primary.valid_time, primary.valid_time))
        specs.append((fp.station_id, basis, k.as_of - TREND_WINDOW, k.as_of))
    if specs:
        await k.observations_for(specs)


@dataclass
class PointAssessment:
    item: RiverVisualizationState
    refs: dict[str, ProvenanceRef] = field(default_factory=dict)
    hazard: CategoryResult = field(default_factory=lambda: CategoryResult(FloodCategory.UNKNOWN, "not assessed"))
    hazard_ref: str = ""
    #: The OFFICIAL threshold set this point was categorized against, carried out so the basin
    #: assembler can hand the same object to `agreement.assess` instead of re-reading the
    #: thresholds and risking a different answer for the same point in the same envelope.
    thresholds: ThresholdSet | None = None


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
    basis = observed_basis(tset)
    other = other_variable(basis)

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
        window = await k.observations(fp.station_id, basis, since=now - TREND_WINDOW)
        station = await k.station(fp.station_id)
        # The tidal class is READ, never inferred. A station the seed has not marked produces a
        # refusal, because no estimator removes a tide — the most robust one is the worst of the
        # four measured (research/trend-estimator-selection-2026-08-26.md §5).
        try:
            tidal = TidalClass(station.tidal_class) if station is not None and station.tidal_class else None
        except ValueError:
            tidal = TidalClass.UNVERIFIED  # an unrecognised marker is not a licence to proceed
        trend = estimate_trend(
            [(o.valid_time, o.value) for o in window if o.value is not None],
            station_id=fp.station_id, basis=basis, unit=primary.unit, end=now,
            tidal_class=tidal, window_h=TREND_WINDOW_H,
        )
        tkey = f"cascade-trend-{lid}"
        # The pair-slope IQR is a DISPERSION and never a confidence interval; it rides in the
        # label because `Trend` carries one rate, and widening the contract to hold it is a
        # separate decision from replacing the estimator.
        detail = "" if trend.refusal is None else f" — {trend.refusal.reason}: {trend.refusal.detail}"
        if trend.refusal is None and trend.slope_q25 is not None:
            detail = (
                f" (repeated median of {trend.n} observations spanning {trend.span_h:.2f} h; "
                f"pair-slope IQR {trend.slope_q25:.4f}..{trend.slope_q75:.4f} {trend.slope_unit}, "
                f"a dispersion and not a confidence interval; condition {trend.quality.value})"
            )
        refs[tkey] = ProvenanceRef(
            source_id=SRC_CASCADE,
            source_kind=SourceKind.DERIVED,
            method_id=TREND_METHOD_ID,
            valid_time=trend.last_valid_time if trend.refusal is None else primary.valid_time,
            retrieved_at=primary.retrieved_at,
            freshness=refs[obs_key].freshness,
            label=f"Cascade rate of rise over {TREND_WINDOW_H} h from stored USGS observations{detail}",
        )
        rate_q = None if trend.slope is None else Quantity(value=round(trend.slope, 4), unit=trend.slope_unit or f"{primary.unit}/h")
        trend_model = Trend(prov=tkey, truth=TruthClass.CASCADE_DERIVED, window_h=TREND_WINDOW_H, rate=rate_q, direction=trend.direction)

    # 4. headroom to the next official category
    headroom_model: Headroom | None = None
    hr = compute_headroom(measure, tset, rate_per_h=None if trend is None else trend.slope, direction="unknown" if trend is None else trend.direction)
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
    # explicit: this surface is the OFFICIAL forecast, so it asks for official products by id
    # (design §3.4 defect 1 — the same set is the reader's default, said out loud here).
    run = await k.latest_forecast_run(fp.id, product_ids=OFFICIAL_FORECAST_PRODUCTS)
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
        refs[fkey] = forecast_run_ref(run, products, now=now, valid_time=None if crest is None else crest.valid_time)
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
    return PointAssessment(item=item, refs=refs, hazard=hazard, hazard_ref=fkey, thresholds=tset)


def _envelope(contract: str, items: list, refs: dict[str, ProvenanceRef], *, as_of: datetime, generated_at: datetime) -> ContractEnvelope:
    mode = "now" if abs((generated_at - as_of).total_seconds()) <= 300 else "past"
    return ContractEnvelope(contract=contract, generated_at=generated_at, as_of=as_of, time=TimeContext(valid=as_of, mode=mode), items=tuple(items), provenance_refs=refs)


async def river_envelope(k: Knowledge, fps: list[ForecastPoint], *, generated_at: datetime) -> ContractEnvelope:
    products = await k.products()
    await prefetch_points(k, fps)
    items, refs = [], {}
    for fp in fps:
        basin = await k.basin(fp.basin_id) if fp.basin_id else None
        pa = await assess_point(k, fp, basin, products)
        items.append(pa.item)
        refs.update(pa.refs)
    return _envelope("RiverVisualizationState", items, refs, as_of=k.as_of, generated_at=generated_at)


def _renumbered(*groups: tuple[Driver, ...]) -> tuple[Driver, ...]:
    """One ordered `headline_drivers` list out of the per-surface driver lists.

    Each surface numbers its own drivers from 1 (`susceptibility` p1 is the flow percentile,
    `forcing` p1 is the 72-h QPF, `agreement` p1 is the official crest), so merging them
    verbatim would put three "#1"s in one list. `Driver.rank` on a basin item is the display
    order of that single list, so the ranks are renumbered here while each surface's own
    ordering is preserved. Nothing else about a driver is touched — not its feature id, not its
    value, not its unit, and not the provenance key it points at.
    """
    out: list[Driver] = []
    for group in groups:
        for driver in sorted(group, key=lambda d: d.rank):
            out.append(driver.model_copy(update={"rank": len(out) + 1}))
    return tuple(out)


def _explained(surface: SurfaceState, *, name: str) -> SurfaceState:
    """An UNKNOWN surface always leaves here with a reason (docs/DATA_DOCTRINE.md §12)."""
    if surface.state is not SurfaceLevel.UNKNOWN or surface.reason:
        return surface
    return surface.model_copy(update={"reason": SurfaceReason.unexplained(name)})


def _outlet_lid(basin: Basin) -> str | None:
    return basin.outlet_fp_id.split(":")[-1] if basin.outlet_fp_id else None


async def _prefetch_basins(k: Knowledge, basins: Sequence[Basin]) -> None:
    """Ask each of this envelope's questions once, for every basin, before the loop starts.

    The loop below is unchanged and each surface still reads for itself; this only means that
    by the time it runs, the answers are already in the request-scoped memo. Nine reads per
    basin and eleven per forecast point — the same nine and eleven questions, asked of six
    different ids — become one set-based statement each, eleven for the whole request however
    many basins are in it.

    Each surface owns its own prefetch, for the same reason each owns its own reads: the
    features, methods, lookbacks and product ids a surface asks for are its business, and a
    batch assembled out here would be a second declaration of them, free to drift.

    The one thing assembled here rather than delegated is the station set, because two
    different surfaces read stations and they are frequently the SAME stations: the outlet
    gauges `assess_point` names and the susceptibility gauges, which are deliberately not
    always the outlet. Reading their union first means one statement rather than two
    overlapping ones — and the later per-surface calls simply find their rows already read.
    """
    outlets = await k.forecast_points_by_lid([lid for b in basins if (lid := _outlet_lid(b))])
    points = list(outlets.values())
    await k.stations_by_id([fp.station_id for fp in points if fp.station_id] + susceptibility.gauge_ids(basins))
    await prefetch_points(k, points)
    await agreement.prefetch(k, points)
    await susceptibility.prefetch(k, basins)
    await forcing.prefetch(k, basins)


async def basin_envelope(
    k: Knowledge,
    basins: list[Basin],
    *,
    generated_at: datetime,
    hypsometry: Mapping[str, BasinHypsometry] | None = None,
) -> ContractEnvelope:
    """The basin envelope: four surfaces per basin, each computed by its own method module.

    P3 wiring (docs/research/p3-surfaces-design-2026-08-24.md §6 stage 2). Every surface here
    is now the output of a versioned method that reads stored rows through the knowledge clock;
    the placeholder `cascade-susceptibility` / `cascade-forcing` refs that said "not yet
    computed" are gone. What has *not* changed is the doctrine: a surface with no input is
    UNKNOWN with a reason that names the input, never a value; official and model forecasts are
    carried as two numbers with two `source_kind`s and are never averaged; and the only
    probability that may appear is a counted fraction of model members.
    """
    products = await k.products()
    await _prefetch_basins(k, basins)
    items: list[BasinVisualizationState] = []
    refs: dict[str, ProvenanceRef] = {}
    for basin in basins:
        outlet = await k.forecast_point_by_lid(basin.outlet_fp_id.split(":")[-1]) if basin.outlet_fp_id else None
        agreement_drivers: tuple[Driver, ...] = ()
        model_probability: dict[str, str | float] | None = None
        model_probability_note: str | None = None
        if outlet is not None:
            pa = await assess_point(k, outlet, basin, products)
            hazard, hazard_ref = pa.hazard, pa.hazard_ref
            refs[hazard_ref] = pa.refs[hazard_ref]

            # AGREEMENT: the official run and the NWM run, compared, never blended. The refs are
            # built here (not in `agreement`) so both go through `forecast_run_ref`, which
            # resolves `source_kind` from the registry — that is what keeps an NWM run from
            # being badged OFFICIAL_FORECAST (design §3.4 defect 2).
            ag = await agreement.assess(k, outlet, thresholds=pa.thresholds)
            for key, run in ag.runs_by_prov_key.items():
                # Merge, never overwrite: `assess_point` already registered the official run
                # under this same key with the crest's valid_time on it, which is the more
                # informative ref of the two.
                if key not in refs:
                    refs[key] = forecast_run_ref(run, products, now=k.as_of)
            agreement_state = ag.state.model_copy(
                update={"reason": require_reason(ag.state.reason, surface="agreement")}
                if ag.state.state is AgreementLevel.UNKNOWN
                else {}
            )
            agreement_drivers = ag.drivers
            model_probability = ag.model_probability
            if model_probability is None and hazard.category is not FloodCategory.UNKNOWN:
                # The hazard category is known, so the *absence* of a member fraction beside it
                # is the fact worth stating: usually that the official categories are in stage.
                why = ag.result.category_note or ag.state.reason
                model_probability_note = None if why is None else SurfaceReason.no_model_probability(why)
        else:
            hazard_ref = f"missing-outlet-{basin.id.split(':')[-1]}"
            hazard = CategoryResult(FloodCategory.UNKNOWN, SurfaceReason.no_outlet_point(basin.id))
            refs[hazard_ref] = ProvenanceRef(source_id=SRC_CASCADE, source_kind=SourceKind.UNKNOWN, freshness=Freshness(state=FreshnessState.MISSING), label="No outlet forecast point")
            agreement_state = AgreementState(state=AgreementLevel.UNKNOWN, reason=SurfaceReason.agreement_needs_an_outlet(basin.id), prov=())

        # SUSCEPTIBILITY: day-of-year flow percentile at the basin's configured gauge.
        sus = await susceptibility.assess(k, basin, products)
        refs.update(sus.refs)
        # FORCING: basin-mean NBM QPF, banded. EXPERIMENTAL, and the spread is pointwise.
        frc = await forcing.assess(k, basin, products, hypsometry=(hypsometry or {}).get(basin.id))
        refs.update(frc.refs)

        hazard_reason = " ".join(x for x in (hazard.reason, model_probability_note) if x) or None
        items.append(
            BasinVisualizationState(
                id=basin.id,
                name=basin.name,
                regulation_class=basin.regulation_class,
                surfaces=BasinSurfaces(
                    susceptibility=_explained(sus.surface, name="susceptibility"),
                    forcing=_explained(frc.surface, name="forcing"),
                    hazard=HazardState(
                        horizon_h=surfaces.HAZARD_HORIZON_H,
                        official_category=hazard.category,
                        official_prov=hazard_ref,
                        prov=hazard_ref,
                        truth=TruthClass.AUTHORITATIVE_MODEL,
                        model_probability=model_probability,
                        reason=hazard_reason,
                    ),
                    agreement=agreement_state,
                ),
                tension=None,
                # BESIDE the banded surface, never inside it. `SurfaceState.score` is still the
                # percentile and nothing else; no arithmetic here combines the level with the
                # velocity, and there is no field in which a HIGH band and a fast change resolve
                # into one symbol (research/high-tail-selection-2026-08-27.md §9).
                hydrologic_state=sus.hydrologic_state,
                state_change=sus.state_changes,
                headline_drivers=_renumbered(sus.drivers, frc.drivers, agreement_drivers),
                official_alerts=(),
                outlet_forecast_point_id=basin.outlet_fp_id,
                geometry_ref=GeometryRef(lod="basin", feature_id=basin.id, url=f"/basins/{basin.id}/geometry?lod=basin"),
                label_priority=2,
            )
        )
    return _envelope("BasinVisualizationState", items, refs, as_of=k.as_of, generated_at=generated_at)
