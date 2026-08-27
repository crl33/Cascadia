"""`method:susceptibility-index@0.1.0` — antecedent wetness as a day-of-year flow percentile.

**The claim this surface makes, stated exactly:** *the river that drains this basin is currently
at the Nth percentile of its own recorded flow for this day of the year.* That is the standard
antecedent-wetness proxy — an observed integrator of soil water, groundwater and channel storage
(`HYDROLOGY.md` §8). It is **not** a soil-moisture estimate, **not** a snow statement, **not** a
forecast, and **never** a probability. It is EXPERIMENTAL: uncalibrated, un-hindcast, badged
(ADR-0008).

Read-only. Everything here comes from `derived_feature` rows a worker job already wrote, read
through `as_known_at` so a replay at an earlier knowledge time sees exactly what was known then.
No provider adapter is imported: the feature and method vocabulary is restated below and
`tests/unit/test_susceptibility.py` asserts it against the package that writes those rows, so
the coupling is checked instead of assumed.

Three doctrine constraints are load-bearing here and each has a test:

1. **Regulation.** On a regulated reach flow is an operator decision, not a basin state
   (`HYDROLOGY.md` §2, §9). Each basin's gauge and its confidence CEILING come from the seed;
   the Skagit reads the unregulated Sauk rather than its own outlet and says so in the label.
2. **Snow is context, never score.** More SWE is not more risk (`HYDROLOGY.md` §7), so the SWE
   driver carries `direction="context_not_scored"` and contributes nothing to the index.
3. **Soil is UNKNOWN, visibly.** `soil_saturation_percentile` is emitted with `value=None` and
   an unavailability provenance so the absence is rendered rather than quietly dropped.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import timedelta

from cascade_contracts import (
    ConfidenceLabel,
    Freshness,
    FreshnessState,
    ProvenanceRef,
    Quantity,
    SourceKind,
    TruthClass,
)
from cascade_contracts.visualization import Driver, SurfaceLevel, SurfaceState
from cascade_core.freshness import compute_freshness
from cascade_core.knowledge import Knowledge
from cascade_core.models import Basin, DerivedFeature, SourceProduct
from cascade_core.registry import (
    PRODUCT_AWDB_DAILY,
    PRODUCT_USGS_DAILY_STATS,
    PRODUCT_USGS_OGC_DAILY,
    SOURCES,
    SRC_AWDB,
    SRC_CASCADE,
    SRC_USGS_OGC,
    SRC_USGS_STATS,
)

METHOD_ID = "method:susceptibility-index@0.1.0"
CLIMATOLOGY_METHOD_ID = "method:streamflow-doy-climatology@1.0.0"
PUBLISHED_CLIMATOLOGY_METHOD_ID = "method:usgs-published-doy-stats@1.0.0"
SWE_METHOD_ID = "method:snotel-basin-swe-context@1.0.0"
PRECIP_METHOD_ID = "method:snotel-precip-14d-context@1.0.0"

PERCENTILE_FEATURE = "streamflow_doy_percentile"
CLIMATOLOGY_FEATURE = "streamflow_doy_climatology"
SWE_FEATURE = "basin_swe_percent_of_median"
PRECIP_FEATURE = "snotel_precip_14d_percent_of_median"
SOIL_FEATURE = "soil_saturation_percentile"

# HYDROLOGY §7. The ONLY direction a snow or point-precipitation driver may carry; a driver that
# scores SWE is a doctrine violation, not a tuning choice.
CONTEXT_DIRECTION = "context_not_scored"
UNAVAILABLE_DIRECTION = "unavailable"
SCORED_DIRECTION = "increases_susceptibility"

# A daily mean older than this makes the surface UNKNOWN. The 15-minute instantaneous value is
# NOT a substitute: a daily mean belongs against a daily-mean climatology (design §2.2 step 3).
MAX_DAILY_MEAN_AGE = timedelta(hours=48)
CLIMATOLOGY_LOOKBACK = timedelta(days=3650)  # a ladder is rebuilt annually; it is reference data
CONTEXT_LOOKBACK = timedelta(days=7)

# ASSUMPTION, and it travels with the method: these are the USGS WaterWatch conventions for
# below-normal / above-normal / much-above-normal (25 / 75 / 90). They are NOT calibrated to
# flood response in Washington basins. Calibration is Phase 7 work behind hindcast evaluation
# (ADR-0008). The exit test checks that the banding is monotone and reproducible, never right.
BAND_EDGES: tuple[tuple[float, SurfaceLevel], ...] = (
    (25.0, SurfaceLevel.LOW),
    (75.0, SurfaceLevel.MODERATE),
    (90.0, SurfaceLevel.HIGH),
)
BAND_TOP = SurfaceLevel.VERY_HIGH
METHOD_PARAMETERS: dict[str, object] = {
    "band_edges_percentile": [25, 75, 90],
    "band_citation": "USGS WaterWatch below-normal / above-normal / much-above-normal convention",
    "calibrated": False,
    "max_daily_mean_age_h": int(MAX_DAILY_MEAN_AGE.total_seconds() // 3600),
    "note": (
        "EXPERIMENTAL index. The day-of-year flow percentile of one gauge, banded on an "
        "uncalibrated convention. Never a probability; never a soil, snow or forecast claim."
    ),
}

NO_GAUGE_REASON = "Basin has no susceptibility gauge configured"
STALE_REASON = "Latest approved/provisional daily mean is older than 48 h"
SOIL_UNAVAILABLE_REASON = (
    "No basin soil-moisture product is ingested. SNOTEL SMS is the only mountain soil "
    "observation in Washington and returns no climatology, inconsistent depths and `no profile` "
    "quality flags at most sites — it cannot support a percentile."
)

_CONFIDENCE_ORDER = (ConfidenceLabel.UNKNOWN, ConfidenceLabel.LOW, ConfidenceLabel.MODERATE, ConfidenceLabel.HIGH)

# DATA_DOCTRINE §2: a ref's source_kind is LOOKED UP, never spelled out beside the value. The
# same rule assemble.forecast_run_ref follows; resolved here from the registry directly rather
# than imported from the assembler, because a method may not import its caller (and
# cascade_hydrology may not import a provider adapter at all — see the module docstring).
_SOURCE_KIND_BY_ID: dict[str, str] = {str(src["id"]): str(src["kind"]) for src in SOURCES}


def resolved_source_kind(source_id: str) -> SourceKind:
    """The registered SourceKind for a source id; UNKNOWN when the id is not registered.

    UNKNOWN is the only safe default: an unregistered source shows as unbadged and somebody
    goes and registers it, whereas any other default lends it an authority it never earned.
    """
    try:
        return SourceKind(_SOURCE_KIND_BY_ID[source_id])
    except (KeyError, ValueError):
        return SourceKind.UNKNOWN


def no_climatology_reason(station_id: str) -> str:
    return f"No day-of-year climatology stored for {station_id}"


def band(percentile: float) -> SurfaceLevel:
    """The banded state for a day-of-year percentile. Monotone by construction."""
    for edge, level in BAND_EDGES:
        if percentile < edge:
            return level
    return BAND_TOP


def _min_confidence(*labels: ConfidenceLabel) -> ConfidenceLabel:
    return min(labels, key=_CONFIDENCE_ORDER.index)


def _one_level_down(label: ConfidenceLabel) -> ConfidenceLabel:
    """Drop one confidence level, with LOW as the floor.

    UNKNOWN confidence is reserved for a surface that has no value at all. A computed
    percentile whose climatology is merely disputed is LOW confidence, not "we cannot say" —
    collapsing those two would hide the difference between a weak answer and no answer.
    """
    i = _CONFIDENCE_ORDER.index(label)
    return _CONFIDENCE_ORDER[max(_CONFIDENCE_ORDER.index(ConfidenceLabel.LOW), i - 1)]


def _ceiling(basin: Basin) -> ConfidenceLabel:
    """The seed's CONFIGURED cap for this basin's gauge; anything unrecognised caps at unknown."""
    raw = (basin.susceptibility_confidence_ceiling or "").strip().lower()
    try:
        return ConfidenceLabel(raw)
    except ValueError:
        return ConfidenceLabel.UNKNOWN


def _freshness_confidence(state: FreshnessState) -> ConfidenceLabel:
    if state is FreshnessState.CURRENT:
        return ConfidenceLabel.HIGH
    if state in (FreshnessState.STALE, FreshnessState.DEGRADED, FreshnessState.PARTIAL):
        return ConfidenceLabel.LOW
    return ConfidenceLabel.UNKNOWN


@dataclass
class SusceptibilityAssessment:
    """What the basin assembler needs: one surface, its drivers, and the refs they point at."""

    surface: SurfaceState
    drivers: tuple[Driver, ...] = ()
    refs: dict[str, ProvenanceRef] = field(default_factory=dict)


def soil_unavailable_ref() -> ProvenanceRef:
    """The provenance of a number the platform deliberately does not have.

    `source_kind=UNKNOWN` is the honest kind here: there is no source. This ref exists so the
    absence of a soil claim is rendered with its reason instead of a driver silently missing
    from the list (design §2.2 step 5, §7).
    """
    return ProvenanceRef(
        source_id=SRC_CASCADE,
        source_kind=SourceKind.UNKNOWN,
        freshness=Freshness(state=FreshnessState.MISSING),
        label=SOIL_UNAVAILABLE_REASON,
    )


def _unknown(reason: str, *, prov_key: str, refs: dict[str, ProvenanceRef], drivers: tuple[Driver, ...] = ()) -> SusceptibilityAssessment:
    refs[prov_key] = ProvenanceRef(
        source_id=SRC_CASCADE,
        source_kind=SourceKind.EXPERIMENTAL,
        method_id=METHOD_ID,
        freshness=Freshness(state=FreshnessState.MISSING),
        label=f"Cascade experimental susceptibility index — not computed: {reason}",
    )
    surface = SurfaceState(
        state=SurfaceLevel.UNKNOWN,
        horizon_h=None,
        score=None,
        value=None,
        spread=None,
        prov=prov_key,
        truth=TruthClass.CASCADE_DERIVED,
        confidence=ConfidenceLabel.UNKNOWN,
        experimental=True,
        reason=reason,
    )
    return SusceptibilityAssessment(surface=surface, drivers=drivers, refs=refs)


def _context_driver(
    row: DerivedFeature | None,
    *,
    feature: str,
    rank: int,
    prov_key: str,
    refs: dict[str, ProvenanceRef],
    products: dict[str, SourceProduct],
    now,
    fallback_label: str,
) -> Driver:
    """A SNOTEL context driver. Value may be None; direction is ALWAYS context_not_scored."""
    values = (row.values_json or {}) if row is not None else {}
    label = str(values.get("label") or fallback_label)
    reason = values.get("reason")
    product = products.get(PRODUCT_AWDB_DAILY)
    refs[prov_key] = ProvenanceRef(
        source_id=SRC_AWDB,
        source_kind=resolved_source_kind(SRC_AWDB) if row is not None else SourceKind.UNKNOWN,
        product_id=PRODUCT_AWDB_DAILY if row is not None else None,
        method_id=(row.method_id if row is not None else None),
        valid_time=row.valid_time if row is not None else None,
        retrieved_at=row.computed_at if row is not None else None,
        freshness=compute_freshness(
            expected_cadence_seconds=product.expected_cadence_seconds if product else None,
            grace_seconds=product.grace_seconds if product else None,
            valid_time=row.valid_time if row is not None else None,
            retrieved_at=row.computed_at if row is not None else None,
            now=now,
        ),
        quality=tuple(row.quality) if row is not None else (),
        label=label if reason is None else f"{label} — {reason}",
    )
    return Driver(
        feature=feature,
        value=None if row is None else row.value,
        unit="pct",
        direction=CONTEXT_DIRECTION,
        rank=rank,
        prov=prov_key,
    )


def gauge_ids(basins: Sequence[Basin]) -> list[str]:
    """The stations this surface will read for ``basins``.

    Exported because the gauge is deliberately NOT always the outlet (see the class docstring
    on `Basin`), so an assembler batching station reads cannot work the set out for itself
    without re-deciding something this module owns.
    """
    return [b.susceptibility_gauge_id for b in basins if b.susceptibility_gauge_id]


#: The specs :func:`assess` reads on its main path, declared once so :func:`prefetch` cannot ask
#: for a different family than `assess` goes on to read.
READ_SPECS: tuple[tuple[str, str, None], ...] = (
    (PERCENTILE_FEATURE, METHOD_ID, None),
    (SWE_FEATURE, SWE_METHOD_ID, None),
    (PRECIP_FEATURE, PRECIP_METHOD_ID, None),
)


async def prefetch(k: Knowledge, basins: Sequence[Basin]) -> None:
    """Read every basin's susceptibility rows in ONE statement instead of three per basin.

    Pure warm-up, in the sense :mod:`cascade_hydrology.forcing` documents: the same features
    and methods :func:`assess` reads, asked once across all the scopes, landing in the
    request-scoped memo. Not calling it leaves `assess` reading for itself.

    Two scope kinds and two lookbacks go into one statement. The scopes are a union because
    the percentile is keyed by the gauge STATION and the two SNOTEL context features by the
    basin, and a cell that cannot exist (SWE at a station id) simply comes back empty. The
    lookback is the wider of the two, and `assess` still asks for its own: `[T − 48 h, T]` lies
    inside `[T − 7 d, T]`, so the percentile read is answered by narrowing this batch to
    precisely the rows its own statement would have returned. :data:`MAX_DAILY_MEAN_AGE` stays
    where it belongs — the staleness rule below, applied to the rows `assess` asked for — and
    is not weakened by having been fetched alongside something with a longer memory.
    """
    gauges = gauge_ids(basins)
    scopes = gauges + [b.id for b in basins]
    if not scopes:
        return
    await k.latest_derived_features(READ_SPECS, scopes, lookback=max(MAX_DAILY_MEAN_AGE, CONTEXT_LOOKBACK))
    # The climatology is read only where the percentile is missing or carries no number. WHICH
    # gauges those are is now free to work out — the percentile read below costs no statement,
    # it narrows what has just been read — so the fallback is batched for exactly the gauges
    # that will take it, and a request where none does issues nothing here at all.
    stale = [g for g in gauges if _needs_climatology(await _percentile_row(k, g))]
    if stale:
        await k.latest_derived_features(
            [(CLIMATOLOGY_FEATURE, CLIMATOLOGY_METHOD_ID, None)], stale, lookback=CLIMATOLOGY_LOOKBACK
        )


async def _percentile_row(k: Knowledge, gauge_id: str) -> DerivedFeature | None:
    return await k.latest_derived_feature(PERCENTILE_FEATURE, gauge_id, method_id=METHOD_ID, lookback=MAX_DAILY_MEAN_AGE)


def _needs_climatology(row: DerivedFeature | None) -> bool:
    """The condition under which :func:`assess` falls back to the climatology row.

    One predicate, used by both `assess` and `prefetch`, so the batch cannot decide a different
    set of gauges needs the fallback than the set that goes on to read it.
    """
    return row is None or row.percentile is None


async def assess(k: Knowledge, basin: Basin, products: dict[str, SourceProduct]) -> SusceptibilityAssessment:
    """The susceptibility surface for one basin at the knowledge time `k.as_of`."""
    slug = basin.id.split(":")[-1]
    prov_key = f"cascade-susceptibility-{slug}"
    soil_key = "cascade-soil-unavailable"
    refs: dict[str, ProvenanceRef] = {soil_key: soil_unavailable_ref()}
    now = k.as_of

    # The soil driver exists on EVERY branch, including the UNKNOWN ones: the absence of a soil
    # claim is itself information and must not disappear when the surface cannot be computed.
    soil_driver = Driver(feature=SOIL_FEATURE, value=None, unit="pct", direction=UNAVAILABLE_DIRECTION, rank=4, prov=soil_key)

    gauge_id = basin.susceptibility_gauge_id
    if not gauge_id:
        return _unknown(NO_GAUGE_REASON, prov_key=prov_key, refs=refs, drivers=(soil_driver,))

    row = await _percentile_row(k, gauge_id)
    if _needs_climatology(row):
        climatology = await k.latest_derived_feature(
            CLIMATOLOGY_FEATURE, gauge_id, method_id=CLIMATOLOGY_METHOD_ID, lookback=CLIMATOLOGY_LOOKBACK,
        )
        reason = STALE_REASON if climatology is not None else no_climatology_reason(gauge_id)
        return _unknown(reason, prov_key=prov_key, refs=refs, drivers=(soil_driver,))

    values = row.values_json or {}
    climatology_meta = values.get("climatology") or {}
    station = await k.station(gauge_id)
    site = station.external_id if station else gauge_id
    begin_year, end_year = climatology_meta.get("begin_year"), climatology_meta.get("end_year")
    span = f"{begin_year}\u2013{end_year}" if begin_year and end_year else "period of record unknown"
    # A CALENDAR SPAN, deliberately not called "years of record". `end - begin + 1` counts the
    # years between the first and last approved daily mean, including the ones with no data in
    # them: the Sauk (12189500) has approved values in 1911-1912, then nothing until 1928, so a
    # 1911-2026 span is 116 calendar years but only 101 years with data (measured 2026-08-24
    # from the archived OGC `daily` CSV). Calling that "116 years of record" advertises 15 years
    # of evidence the gauge never produced. The honest depth statement is the sample size below
    # (`n=... values in the day-of-year window`), which counts what the ladder was actually
    # built from; the span is kept because it says how far back the record reaches.
    span_years = (end_year - begin_year + 1) if begin_year and end_year else None

    # 1. the observation the percentile is a rank of, with its own OBSERVED provenance
    obs_key = f"usgs-daily-{site}"
    obs_product = products.get(PRODUCT_USGS_OGC_DAILY)
    obs_freshness = compute_freshness(
        expected_cadence_seconds=obs_product.expected_cadence_seconds if obs_product else None,
        grace_seconds=obs_product.grace_seconds if obs_product else None,
        valid_time=row.valid_time,
        retrieved_at=row.computed_at,
        now=now,
    )
    refs[obs_key] = ProvenanceRef(
        source_id=SRC_USGS_OGC,
        source_kind=resolved_source_kind(SRC_USGS_OGC),
        product_id=PRODUCT_USGS_OGC_DAILY,
        valid_time=row.valid_time,
        retrieved_at=row.computed_at,
        freshness=obs_freshness,
        quality=tuple(row.quality),
        label=f"USGS daily mean discharge at {site} for {values.get('day')} ({values.get('approval_status') or 'approval unknown'})",
        raw_artifact_id=None if row.raw_artifact_id is None else str(row.raw_artifact_id),
    )

    # 2. the index itself: EXPERIMENTAL, and the label names the gauge it actually read
    if (now - row.valid_time) > MAX_DAILY_MEAN_AGE:
        return _unknown(STALE_REASON, prov_key=prov_key, refs=refs, drivers=(soil_driver,))
    # One rounded number, used for the state, the score and the displayed value alike: a score
    # that disagrees in the fourth decimal with the percentile printed beside it is a bug report
    # waiting to happen.
    percentile = round(float(row.percentile), 1)
    state = band(percentile)

    quality = tuple(row.quality)
    ceiling = _ceiling(basin)
    confidence = _min_confidence(ceiling, _freshness_confidence(obs_freshness.state))
    if "climatology_disagreement" in quality:
        confidence = _one_level_down(confidence)

    gauge_note = basin.susceptibility_note or ""
    sample = values.get("sample_count")
    label = (
        "Cascade experimental susceptibility index from the USGS daily-mean flow percentile at "
        f"{site} ({span}"
        + (f", spanning {span_years} calendar years" if span_years else "")
        + (f", n={sample} values in the day-of-year window" if sample else "")
        + ")"
    )
    if gauge_note:
        label = f"{label}. {gauge_note}"
    # EXPERIMENTAL, not the registry's DERIVED for src:cascade, and deliberately so: this is a
    # Cascadia Papsukkal method that has not passed hindcast evaluation, which ADR-0008 and
    # DATA_DOCTRINE §9 classify as EXPERIMENTAL. It is a STRICTER badge than the registry's, and
    # SurfaceState.experimental carries the same claim; no lookup may relax it.
    refs[prov_key] = ProvenanceRef(
        source_id=SRC_CASCADE,
        source_kind=SourceKind.EXPERIMENTAL,
        method_id=METHOD_ID,
        valid_time=row.valid_time,
        retrieved_at=row.computed_at,
        freshness=obs_freshness,
        quality=quality,
        label=label,
    )

    drivers: list[Driver] = [
        Driver(feature=PERCENTILE_FEATURE, value=percentile, unit="pct", direction=SCORED_DIRECTION, rank=1, prov=obs_key),
    ]

    # 3. SNOTEL context: shown, never scored (HYDROLOGY §7)
    swe_row = await k.latest_derived_feature(SWE_FEATURE, basin.id, method_id=SWE_METHOD_ID, lookback=CONTEXT_LOOKBACK)
    drivers.append(_context_driver(
        swe_row, feature=SWE_FEATURE, rank=2, prov_key=f"awdb-swe-{slug}", refs=refs, products=products, now=now,
        fallback_label="No SNOTEL snow-water-equivalent context ingested for this basin",
    ))
    precip_row = await k.latest_derived_feature(PRECIP_FEATURE, basin.id, method_id=PRECIP_METHOD_ID, lookback=CONTEXT_LOOKBACK)
    drivers.append(_context_driver(
        precip_row, feature=PRECIP_FEATURE, rank=3, prov_key=f"awdb-prec-{slug}", refs=refs, products=products, now=now,
        fallback_label="No SNOTEL precipitation context ingested for this basin",
    ))

    # 4. soil: always present, always null, always with its reason
    drivers.append(soil_driver)

    # 5. the climatology disagreement, when there is one — reported, never averaged away
    cross_check = values.get("cross_check") or {}
    fraction = cross_check.get("disagreement_fraction")
    if fraction is not None and abs(float(fraction)) > float(cross_check.get("threshold", 0.10)):
        xkey = f"usgs-published-stats-{site}"
        refs[xkey] = ProvenanceRef(
            source_id=SRC_USGS_STATS,
            source_kind=resolved_source_kind(SRC_USGS_STATS),
            product_id=PRODUCT_USGS_DAILY_STATS,
            method_id=PUBLISHED_CLIMATOLOGY_METHOD_ID,
            freshness=Freshness(state=FreshnessState.UNKNOWN),
            label=(
                "USGS published day-of-year statistics, held as an independent cross-check and "
                "never averaged with the Cascade-built climatology (disagreement is information)"
            ),
        )
        drivers.append(Driver(
            feature="climatology_p50_disagreement",
            value=round(float(fraction) * 100.0, 1),
            unit="pct",
            direction="lowers_confidence",
            rank=5,
            prov=xkey,
        ))

    surface = SurfaceState(
        state=state,
        horizon_h=None,  # susceptibility is a present-state surface, not a horizon surface
        score=round(percentile / 100.0, 4),
        value=Quantity(value=percentile, unit="pct"),
        spread=None,  # the ladder is in cfs and `spread` must share `value`'s unit
        prov=prov_key,
        truth=TruthClass.CASCADE_DERIVED,
        confidence=confidence,
        experimental=True,
        reason=None,
    )
    return SusceptibilityAssessment(surface=surface, drivers=tuple(drivers), refs=refs)
