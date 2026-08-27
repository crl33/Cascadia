"""`method:susceptibility-index@0.2.0` — antecedent wetness, and what the ladder's ceiling hid.

**The claim this surface makes, stated exactly:** *the river that drains this basin is currently
at the Nth percentile of its own recorded flow for this day of the year* — plus, since 0.2.0,
*how it ranks against that whole record*, *how many times the seasonal reference flow it is*,
and *how fast it is moving*. That is the standard antecedent-wetness proxy — an observed
integrator of soil water, groundwater and channel storage (`HYDROLOGY.md` §8) — extended where
it was measurably blind. It is **not** a soil-moisture estimate, **not** a snow statement,
**not** a forecast, and **never** a probability. The banded index is EXPERIMENTAL: uncalibrated,
un-hindcast, badged (ADR-0008).

Why 0.2.0 exists (three defects, all measured on production data)
----------------------------------------------------------------
`research/tier0-measured-basis-2026-08-26.md` and `research/high-tail-selection-2026-08-27.md`:

1. **The level lags the deterioration by 1-3 days.** Every one of the six basins exceeded
   +40 percentile points in 48 h *before* its level reached p90 (skagit +54 in 24 h).
2. **The percentile collapses at p95.** The stored ladders end at `p95`, so 24,976 cfs and
   72,440 cfs on the Sauk both read `95.0` — one indistinguishable state across a 2.9x flow
   ratio, and 5.77x against that day's own reference.
3. **The collapse also silences the derivative.** Between two clamped days a percentile change
   is identically `+0`, so a velocity computed in percentile space goes blind through the crest
   — exactly the hours it exists to cover.

(3) is why the tail and the velocity are ONE change and not two: a derivative against a
representation that silences it at the top is not worth shipping.

What 0.2.0 adds, and what it deliberately does not
--------------------------------------------------
Three separately-provenanced statements, and **no fourth summarising them**:

- the **percentile and its band, unchanged** — same ladder, same `BAND_EDGES`, same
  `calibrated: False`, same clamp, same `outside_climatology_range` flag. Nothing here is
  recalibrated, so Event Zero cannot become a training target (brief §8) and register X8 (which
  ladder vintage?) is left exactly as open as it was;
- the **rank in the day-of-year window** and the **seasonal multiple** `Q / p95(DOY)` — the
  first says how unusual, the second how big, and only the second is unbounded;
- the **state change** `Q(t) / Q(t - 24 h)` and `/ Q(t - 48 h)`, computed on the observation and
  never on the percentile.

**No composite, no weighting, no probability.** `SurfaceState.score` is still `percentile / 100`
and nothing else feeds it; the new drivers carry directions that say out loud that they are not
scored. A client may not colour, size or order one of these by another. This is the same
doctrinal move `HYDROLOGY.md` §7 already makes for snow — *shown, never scored* — for a
different reason: snow is context because more SWE is not more risk, and the state change is
unscored because **no evidence exists for a weight** and inventing one would be the flood-risk
score the doctrine forbids.

Versioning (brief §22)
----------------------
`assess(..., version=...)` runs either method at the same knowledge time, deterministically.
:data:`SURFACE_METHOD_V1` is the surface that shipped until 2026-08-26 — same bands, same
percentile, no tail, no velocity, no spread — and it stays callable so the A/B compares against
the deployed code rather than a reconstruction of it. Note that `PERCENTILE_ROW_METHOD_ID` is
NOT the surface version: it is the id the *ingest* stamps on the ranking row, it is unchanged at
`@0.1.0`, and **both surface versions read the same stored rows**. Bumping it would have made
every historical percentile unreadable to the new surface for no gain.

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

import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from cascade_contracts import (
    BandBoundary,
    ConfidenceLabel,
    Freshness,
    FreshnessState,
    HydrologicState,
    ProvenanceRef,
    Quantity,
    RecordRank,
    ReferenceWindow,
    SeasonalMultiple,
    SourceKind,
    StateChange,
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
from cascade_hydrology.trend import (
    FALLING,
    FLOW_STEADY_FRACTION_PER_H,
    RISING,
    STEADY,
    UNKNOWN,
)

# --- method identity -------------------------------------------------------------------------

#: The surface as it shipped until 2026-08-26. Preserved and callable (brief §22).
SURFACE_METHOD_V1 = "method:susceptibility-index@0.1.0"
#: The surface that ships now: same bands, plus the tail state, the velocity and the boundary
#: condition. A MINOR bump because everything 0.1.0 published is published unchanged.
SURFACE_METHOD_V2 = "method:susceptibility-index@0.2.0"
METHOD_ID = SURFACE_METHOD_V2
SHIPPED_VERSION = "0.2.0"
VERSIONS: tuple[str, ...] = ("0.1.0", "0.2.0")
_SURFACE_METHOD_BY_VERSION = {"0.1.0": SURFACE_METHOD_V1, "0.2.0": SURFACE_METHOD_V2}

#: The id the INGEST stamps on the stored ranking row (`cascade_providers_usgs.stats_jobs`).
#: Deliberately NOT bumped with the surface: both surface versions read the same rows, and
#: bumping it would have orphaned every percentile already stored.
PERCENTILE_ROW_METHOD_ID = "method:susceptibility-index@0.1.0"

CLIMATOLOGY_METHOD_ID = "method:streamflow-doy-climatology@1.0.0"
PUBLISHED_CLIMATOLOGY_METHOD_ID = "method:usgs-published-doy-stats@1.0.0"
RECORD_CONTEXT_METHOD_ID = "method:streamflow-record-context@1.0.0"
SWE_METHOD_ID = "method:snotel-basin-swe-context@1.0.0"
PRECIP_METHOD_ID = "method:snotel-precip-14d-context@1.0.0"
#: The level statement above the ladder's ceiling: rank + multiple. Exact arithmetic over the
#: stored record — no fit, no interpolation, no distributional assumption anywhere.
TAIL_STATE_METHOD_ID = "method:streamflow-tail-state@0.1.0"
#: The velocity: a multiplicative growth of the daily mean over a named window.
STATE_CHANGE_METHOD_ID = "method:streamflow-state-change@0.1.0"

PERCENTILE_FEATURE = "streamflow_doy_percentile"
CLIMATOLOGY_FEATURE = "streamflow_doy_climatology"
RECORD_CONTEXT_FEATURE = "streamflow_record_context"
SWE_FEATURE = "basin_swe_percent_of_median"
PRECIP_FEATURE = "snotel_precip_14d_percent_of_median"
SOIL_FEATURE = "soil_saturation_percentile"
MULTIPLE_FEATURE = "streamflow_seasonal_multiple"
GROWTH_FEATURE_TEMPLATE = "streamflow_growth_{window}h"

# --- driver directions -----------------------------------------------------------------------
# Four directions, and only ONE of them is scored. That is the whole guard against a composite:
# a reader of `headline_drivers` can see, per driver, whether it moved the index.

# HYDROLOGY §7. The ONLY direction a snow or point-precipitation driver may carry; a driver that
# scores SWE is a doctrine violation, not a tuning choice.
CONTEXT_DIRECTION = "context_not_scored"
UNAVAILABLE_DIRECTION = "unavailable"
SCORED_DIRECTION = "increases_susceptibility"
#: Part of the LEVEL statement, contributing nothing to the index. The seasonal multiple says
#: how big the flow is against a named reference; the score stays `percentile / 100`.
LEVEL_DIRECTION = "level_not_scored"
#: The VELOCITY. Unscored because no evidence exists for a weight against the level — not
#: because the number is weak (`high-tail-selection-2026-08-27.md` §9).
STATE_CHANGE_DIRECTION = "state_change_not_scored"

# --- windows and lookbacks -------------------------------------------------------------------

# A daily mean older than this makes the surface UNKNOWN. The 15-minute instantaneous value is
# NOT a substitute: a daily mean belongs against a daily-mean climatology (design §2.2 step 3).
MAX_DAILY_MEAN_AGE = timedelta(hours=48)
CLIMATOLOGY_LOOKBACK = timedelta(days=3650)  # a ladder is rebuilt annually; it is reference data
CONTEXT_LOOKBACK = timedelta(days=7)

#: The named windows the state change is computed over: fixed in advance and not a sweep, but
#: **chosen on Event Zero**, which is the one thing a reader must know before quoting a lead time
#: measured with them. `research/tier0-measured-basis-2026-08-26.md` §2 measured a 1-3 day lead
#: across exactly these two, and they were adopted because of it.
#:
#: They carry NO independent authority. `HYDROLOGY.md` §9 names 1 h, 3 h and 6 h — for the rate
#: of rise on the instantaneous record, a different quantity on a different cadence — and says
#: nothing about 24 h or 48 h on a daily mean. An earlier version of this comment cited §9 here;
#: that citation was false (the document contains no occurrence of either window) and is removed
#: rather than repaired, because a borrowed authority is worse than a stated assumption.
STATE_CHANGE_WINDOWS_H: tuple[int, ...] = (24, 48)
#: How far a stored daily mean may sit from its target instant and still be that endpoint. A
#: daily mean is labelled by a calendar day whose boundary is the station's LOCAL midnight, so
#: +/-6 h absorbs the DST step and the UTC-vs-local boundary without admitting a different day.
STATE_CHANGE_TOLERANCE_H = 6.0
#: How far back the daily-mean history is read. The latest daily mean may itself be up to
#: MAX_DAILY_MEAN_AGE old, so the 48 h endpoint can sit almost four days behind the knowledge
#: time. `prefetch` must read at least this far or the velocity costs a statement per gauge.
STATE_CHANGE_LOOKBACK = MAX_DAILY_MEAN_AGE + timedelta(hours=max(STATE_CHANGE_WINDOWS_H) + STATE_CHANGE_TOLERANCE_H)

#: The +/-day-of-year smoothing window the stored ladders were built with. RESTATED rather than
#: imported (`cascade_hydrology` may not import a provider adapter — see the module docstring),
#: and `tests/unit/test_susceptibility.py` asserts it equals the builder's own constant, so the
#: duplication is checked instead of assumed. It matters here because it is the deflation
#: between "values in the sample" and "independent years behind the sample".
DOY_WINDOW_DAYS = 2

#: The ladder breakpoint the multiple is referenced to. p95 and not p90 or p50 for one reason
#: that is checkable rather than aesthetic: it is the TOP stored breakpoint, so `multiple >= 1.0`
#: is exactly the condition under which the shipped percentile clamps. The multiple begins
#: precisely where the percentile stops discriminating, and the two never disagree about where
#: that is.
REFERENCE_PERCENTILE = 95

#: Above this percentile the stored record context is read so an exact rank can be published.
#: Not a science threshold and not a band edge of its own — it is the existing top band edge
#: reused as a READ rule: below it the ladder resolves perfectly well and a rank adds nothing,
#: at or above it the ladder is within one breakpoint of clamping.
RANK_READ_EDGE = 90.0

#: A tail statement whose exceedance set spans fewer than this many distinct water years is
#: LABELLED thin — never suppressed, never adjusted. Measured: at cedar the entire p99
#: exceedance set is a single water year (December 2015), and a leave-one-water-year-out
#: jackknife moves p99 by up to 19.2 % (`high-tail-selection-2026-08-27.md` §4).
MIN_TAIL_YEARS = 5

# --- quality vocabulary ----------------------------------------------------------------------

OUTSIDE_CLIMATOLOGY_RANGE = "outside_climatology_range"  # the shipped flag, preserved verbatim
EXCEEDS_WINDOW_RECORD = "exceeds_window_record"
THIN_TAIL_SUPPORT = "thin_tail_support"
NO_RECORD_CONTEXT = "no_record_context"

# ASSUMPTION, and it travels with the method: these are the USGS WaterWatch conventions for
# below-normal / above-normal / much-above-normal (25 / 75 / 90). They are NOT calibrated to
# flood response in Washington basins. Calibration is Phase 7 work behind hindcast evaluation
# (ADR-0008). The exit test checks that the banding is monotone and reproducible, never right.
#
# 0.2.0 DOES NOT TOUCH THEM. Recalibrating the bands in the same change that adds the tail and
# the velocity would fit the surface to Event Zero and make the A/B meaningless (brief §8).
BAND_EDGES: tuple[tuple[float, SurfaceLevel], ...] = (
    (25.0, SurfaceLevel.LOW),
    (75.0, SurfaceLevel.MODERATE),
    (90.0, SurfaceLevel.HIGH),
)
BAND_TOP = SurfaceLevel.VERY_HIGH
BAND_ORDER: tuple[SurfaceLevel, ...] = (SurfaceLevel.LOW, SurfaceLevel.MODERATE, SurfaceLevel.HIGH, SurfaceLevel.VERY_HIGH)

METHOD_PARAMETERS: dict[str, object] = {
    "band_edges_percentile": [25, 75, 90],
    "band_citation": "USGS WaterWatch below-normal / above-normal / much-above-normal convention",
    "calibrated": False,
    "max_daily_mean_age_h": int(MAX_DAILY_MEAN_AGE.total_seconds() // 3600),
    "reference_percentile": REFERENCE_PERCENTILE,
    "state_change_windows_h": list(STATE_CHANGE_WINDOWS_H),
    "state_change_tolerance_h": STATE_CHANGE_TOLERANCE_H,
    "doy_window_days": DOY_WINDOW_DAYS,
    "ladder_vintage_open_question": (
        "register X8: whether a day-of-year ladder should be built from the longest homogeneous "
        "record or the most recent 30 years is unresolved, and every LEVEL statement here "
        "inherits it. The state change does not: it touches no ladder."
    ),
    "note": (
        "EXPERIMENTAL index. The day-of-year flow percentile of one gauge, banded on an "
        "uncalibrated convention, beside an exact rank, an exact seasonal multiple and an exact "
        "multiplicative state change. Never a probability; never a soil, snow or forecast claim; "
        "never combined into one number."
    ),
}

NO_GAUGE_REASON = "Basin has no susceptibility gauge configured"
STALE_REASON = "Latest approved/provisional daily mean is older than 48 h"
SOIL_UNAVAILABLE_REASON = (
    "No basin soil-moisture product is ingested. SNOTEL SMS is the only mountain soil "
    "observation in Washington and returns no climatology, inconsistent depths and `no profile` "
    "quality flags at most sites — it cannot support a percentile."
)
#: Why the LEVEL carries no exact rank below the read edge. It exists because the absence was
#: previously rendered as a bare `null`: `hydrologic_state.rank` was simply omitted, with no
#: reason anywhere, while the velocity's `growth_rank` refused in the same situation with a full
#: sentence. A reader cannot tell "nobody computed this" from "this gauge has no record" from
#: "the surface declined to look", and the project's one rule says every displayed number — and
#: every absent one — answers where it came from.
RANK_NOT_READ_REASON = (
    f"Not read: the exact rank is fetched only at or above p{int(RANK_READ_EDGE)}, where the "
    "stored ladder is within one breakpoint of clamping and the percentile stops "
    "discriminating. Below that edge the percentile resolves the value on its own and the rank "
    "would be a round trip bought for nothing. The value here is NOT unranked because the "
    "record is missing — see the seasonal multiple, computed from the same reference."
)

NO_RECORD_CONTEXT_REASON = (
    "No stored day-of-year record context for this gauge, so the exact rank cannot be computed. "
    "It is written by the annual `usgs.build_climatology` job under "
    "`method:streamflow-record-context@1.0.0`; until that has run, the level is the percentile "
    "and the multiple alone."
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


# =============================================================================================
# The high tail — where the value sits once the ladder has run out (brief §7 corrections 2)
# =============================================================================================


def independent_years(sample_count: int, *, window_days: int = DOY_WINDOW_DAYS) -> int:
    """How many INDEPENDENT years stand behind a day-of-year window sample.

    A +/-2-day window pools five consecutive days from each year of record, so a sample of 495
    values is 99 water years wearing 495 days' clothing. Every statement about the ladder's
    sampling error has to use this denominator and not `n`; using `n` would understate the
    error by a factor of sqrt(5).

    Exact on a complete record (the Sauk's 490-value December window deflates to 98, which is
    its measured water-year count) and conservative where the record has holes.
    """
    return max(1, sample_count // (2 * window_days + 1))


def seasonal_multiple(value: float, reference_flow: float | None) -> float | None:
    """`value / reference_flow`. Unbounded, monotone, and the only level statement with a live
    derivative in the tail.

    None when the reference is missing or non-positive — a division that cannot be defended is
    UNKNOWN with a reason, never a large number.

    It is a MULTIPLE OF A SEASONAL REFERENCE, never a flood magnitude: the largest multiples in
    these six records are late-summer flash events on a tiny denominator (green-duwamish reached
    8.91x on 1959-09-27 at 8,840 cfs, a flow that reads 1.3x against the 11 December reference).
    The absolute flow renders beside it always, and it is never banded on a year-round cutoff.
    """
    if reference_flow is None or not math.isfinite(reference_flow) or reference_flow <= 0:
        return None
    return value / reference_flow


def ordinal(n: int) -> str:
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


@dataclass(frozen=True)
class TailReading:
    """The exact rank of one value inside its day-of-year window sample, or the reason there is none.

    Deliberately NOT a plotting position: Gringorten on the Sauk's 490-value window renders
    24,976 cfs as "p99.48", advertising two decimals of resolution on a sample that is 99
    independent water years wearing 490 days' clothing. "3rd largest of 491, WY1911-WY2025" says
    the same thing and says its own sample size.

    Censored at 1 — the Sauk read rank 1 on 12-10 at 41,500 cfs and again on 12-11 at 62,600,
    and cedar read it for NINE consecutive days — which is the measured reason this cannot be
    the velocity's basis. But unlike the clamped percentile it saturates HONESTLY, naming the
    record it beat.
    """

    rank: int | None
    of: int
    exceeds_record: bool
    previous_max: float | None
    previous_max_day: date | None
    quality: tuple[str, ...]
    reason: str | None


def window_rank(value: float, key: str, context: dict | None) -> TailReading | None:
    """Rank ``value`` among the stored day-of-year window sample for ``key``.

    ``context`` is a stored `streamflow_record_context` blob. Returns None when there is no
    context at all (the caller says so once, with `NO_RECORD_CONTEXT_REASON`); returns a
    TailReading whose ``rank`` is None with a reason when the value sits below the stored tail
    floor, which is the honest answer — only the top decile of each window is persisted, and
    below it the percentile already resolves.
    """
    if not context:
        return None
    support = (context.get("keys") or {}).get(key)
    if not support:
        return None
    n = int(support["n"])
    floor = float(support["tail_floor"])
    peak = float(support["max"])
    peak_day = date.fromisoformat(support["max_day"])
    tail_years = int(support.get("tail_years", 0))
    flags: list[str] = []
    if tail_years < MIN_TAIL_YEARS:
        flags.append(THIN_TAIL_SUPPORT)
    if value < floor:
        return TailReading(
            rank=None, of=n + 1, exceeds_record=False, previous_max=peak, previous_max_day=peak_day,
            quality=tuple(flags),
            reason=(
                f"below the stored tail floor for {key} ({floor:,.0f}); only the window's top "
                "decile is persisted, and the day-of-year percentile resolves below it"
            ),
        )
    window_days = int(context.get("window_days", DOY_WINDOW_DAYS))
    wanted = _window_keys(key, window_days)
    above = 0
    for iso_day, tail_value in context.get("tail") or ():
        day = date.fromisoformat(iso_day)
        if f"{day.month:02d}-{day.day:02d}" in wanted and float(tail_value) > value:
            above += 1
    exceeds = value > peak
    if exceeds:
        flags.append(EXCEEDS_WINDOW_RECORD)
    return TailReading(
        rank=above + 1, of=n + 1, exceeds_record=exceeds, previous_max=peak, previous_max_day=peak_day,
        quality=tuple(flags), reason=None,
    )


#: The 366-day leap calendar the day-of-year keys run on, so 02-29 keeps its own smaller
#: sample rather than being folded into 03-01. Restated from the builder for the same reason the
#: method ids are (`cascade_hydrology` may not import a provider adapter), and checked against it
#: in `tests/unit/test_tail_state.py`.
DOY_KEYS: tuple[str, ...] = tuple(
    (date(2000, 1, 1) + timedelta(days=i)).strftime("%m-%d") for i in range(366)
)


def _window_keys(key: str, window_days: int) -> set[str]:
    """The +/-window day-of-year keys around ``key``, wrapping at the year boundary."""
    i = DOY_KEYS.index(key)
    return {DOY_KEYS[(i + d) % 366] for d in range(-window_days, window_days + 1)}


# =============================================================================================
# The boundary condition (brief §7 correction 4)
# =============================================================================================
#
# WHAT IS AND IS NOT QUANTIFIABLE HERE. The value is observed and effectively exact; what is
# uncertain is the REFERENCE — p25, p75 and p90 are sample quantiles estimated from a finite
# number of independent years, and their sampling error is what decides whether this value's
# band is really distinguishable from the next one.
#
# What the empirical reference distribution supports is the rank-space (binomial) standard
# error, `100 * sqrt(p(1-p)/m)` with `m` the INDEPENDENT years — distribution-free, needing no
# density estimate and no normality assumption about the flows themselves. The register already
# computes exactly this quantity ("+/-5.5-6.2 percentile points of sampling error at 30 years
# against band edges 15 points apart", X8), so this continues a measurement rather than
# inventing one.
#
# What it does NOT support is a numerical confidence. `+/-1 se` here carries NO coverage claim:
# the normal approximation that would turn it into 68 % is not asserted, the window sample is
# not iid within a year, and X8 disputes which record the ladder should have been built from at
# all. So the standard error is published as a named DISPERSION — the same status
# `trend.pairwise_slope_spread` has — and what the surface actually states is a CONDITION with
# three values, one of which is "cannot be answered". No new cutoff is introduced: the only
# edges compared against are the band edges that already exist.


def rank_standard_error_points(percentile: float, independent_year_count: int) -> float | None:
    """The binomial rank-space standard error of a sample quantile, in percentile POINTS.

    `100 * sqrt(p(1-p)/m)`. A dispersion, not a confidence interval and not a probability: see
    the section comment above for what it does and does not claim. None when `m` is unusable.
    """
    if independent_year_count < 1:
        return None
    p = min(max(percentile, 0.0), 100.0) / 100.0
    return 100.0 * math.sqrt(p * (1.0 - p) / independent_year_count)


def band_boundary(percentile: float, se_points: float | None) -> tuple[BandBoundary, tuple[SurfaceLevel, ...]]:
    """Can the reference distribution separate this value's band from its neighbour's?

    Returns the CONDITION and, where it cannot, the contiguous run of bands the record cannot
    tell apart here. `se_points is None` fails CLOSED to `unquantified` — which never means
    "separated", because a surface that could not check must not read as one that checked and
    was satisfied.
    """
    if se_points is None:
        return BandBoundary.UNQUANTIFIED, ()
    lo = band(max(0.0, percentile - se_points))
    hi = band(min(100.0, percentile + se_points))
    if lo is hi:
        return BandBoundary.SEPARATED, ()
    i, j = BAND_ORDER.index(lo), BAND_ORDER.index(hi)
    return BandBoundary.NEAR_BAND_EDGE, BAND_ORDER[i: j + 1]


# =============================================================================================
# The velocity (brief §7 correction 3) — computed on flow, NEVER on the percentile
# =============================================================================================


@dataclass(frozen=True)
class GrowthReading:
    """`Q(t) / Q(t - window_h)`, or UNKNOWN with a reason. Never interpolated."""

    window_h: int
    growth: float | None
    from_value: float | None
    to_value: float | None
    from_time: datetime | None
    to_time: datetime | None
    span_h: float | None
    direction: str
    reason: str | None


def state_change(
    points: Sequence[tuple[datetime, float]],
    *,
    end: datetime,
    window_h: int,
    tolerance_h: float = STATE_CHANGE_TOLERANCE_H,
) -> GrowthReading:
    """The multiplicative change in daily-mean flow over ``window_h``, or UNKNOWN with a reason.

    **Multiplicative, not additive, and that is the whole point.** An additive change in the
    seasonal multiple ranks the crest above the onset (Sauk, 24 h: +0.57 on 12-06 against +1.18
    on 12-11) while the multiplicative form ranks the onset above the crest (x3.00 against
    x1.51) — which is what a *rate* is supposed to do. Additive change is a magnitude wearing a
    derivative's name. The multiplicative form is scale-free, which is what makes the same
    number mean the same thing at 500 cfs and at 60,000 cfs.

    **It touches no ladder.** Not its vintage, not its period, not its breakpoints — so register
    X8 cannot move this number, it has no extrapolated region, and it stays exact while the
    LEVEL is censored. On 12-11 the Sauk read x1.51 in 24 h, rising, on a day the shipped
    percentile derivative read `+0.0`.

    Refuses rather than interpolates, on `trend.py`'s discipline: BOTH endpoints must exist
    within ``tolerance_h`` of their targets, both values must be positive (a ratio through zero
    is not a rate), and a missing endpoint is UNKNOWN rather than a silently shortened window —
    a "24 h growth" measured over 14 h is a different number wearing the same label.
    """
    if window_h <= 0:
        return GrowthReading(window_h, None, None, None, None, None, None, UNKNOWN, "window must be positive")
    ordered = sorted(points)
    tolerance = timedelta(hours=tolerance_h)
    latest = [(t, v) for t, v in ordered if t <= end and (end - t) <= tolerance]
    if not latest:
        return GrowthReading(
            window_h, None, None, None, None, None, None, UNKNOWN,
            f"no daily mean within {tolerance_h:g} h at or before {end.isoformat()}",
        )
    t_now, q_now = latest[-1]
    target = end - timedelta(hours=window_h)
    prior = [(t, v) for t, v in ordered if abs(t - target) <= tolerance]
    if not prior:
        return GrowthReading(
            window_h, None, None, q_now, None, t_now, None, UNKNOWN,
            f"no daily mean within {tolerance_h:g} h of {target.isoformat()}",
        )
    t_then, q_then = min(prior, key=lambda p: abs(p[0] - target))
    span_h = (t_now - t_then).total_seconds() / 3600.0
    if span_h <= 0:
        return GrowthReading(
            window_h, None, q_then, q_now, t_then, t_now, span_h, UNKNOWN,
            "the two daily means do not span any time",
        )
    if q_then <= 0 or q_now <= 0:
        return GrowthReading(
            window_h, None, q_then, q_now, t_then, t_now, span_h, UNKNOWN,
            "a zero or negative flow has no multiplicative rate",
        )
    growth = q_now / q_then
    # `trend.py`'s +/-1 %/h STEADY band, compounded over the ACTUAL span, so two surfaces cannot
    # call the same river steady and rising in the same breath. 1 %/h is x1.27 over 24 h.
    eps = (1.0 + FLOW_STEADY_FRACTION_PER_H) ** span_h
    direction = STEADY if (1.0 / eps) <= growth <= eps else (RISING if growth > 1.0 else FALLING)
    return GrowthReading(window_h, growth, q_then, q_now, t_then, t_now, span_h, direction, None)


NO_GROWTH_REFERENCE_READ_REASON = (
    "The gauge's own distribution of past changes lives in the day-of-year record context, "
    f"which is read only at or above p{int(RANK_READ_EDGE)} — where the ladder stops "
    "discriminating and the level needs a rank. Below it the change is published without one. "
    "The change itself is exact either way."
)


def growth_rank(
    growth: float, reference: dict | None, *, absent_reason: str | None = None
) -> tuple[int | None, int | None, str | None]:
    """Where ``growth`` sits among this gauge's own past changes over the same window.

    `(rank, of, reason)` — the descriptive answer to "is that fast?" that does not require a
    cutoff. Measured at the Sauk (35,976 day-pairs before WY2026): x3.00 on 12-06 ranks 200th,
    and x1.51 on 12-11 — a day the shipped derivative read `+0.0` — still ranks 1,514th, inside
    the top 5 %.

    What would justify a band instead of a rank: a probability-of-detection / false-alarm-ratio
    curve over a multi-event catalogue at all six basins (brief §18). Until that exists the rank
    is published and **no band is drawn on it**.

    ``absent_reason`` is the caller's account of WHY there is no reference to rank against, and
    the two accounts must stay distinct for the same reason the tidal guard's two refusals do:
    "nobody has built the record context for this gauge" is a gap somebody must close, and "the
    context was not read because this river is quiet" is the design working. Collapsing them
    would hide the first behind the second.
    """
    missing = absent_reason or "no growth reference stored for this gauge"
    if not reference:
        return None, None, missing
    n = int(reference.get("n") or 0)
    top = [float(v) for v in reference.get("top") or ()]
    if not top or n <= 0:
        return None, None, missing
    g = round(growth, 4)  # the stored ratios are rounded the same way, so the rank is reproducible
    if g < top[0]:
        return None, n, f"outside the largest 10 % of this gauge's {n:,} changes over this window, which is the only part stored"
    return 1 + sum(1 for t in top if t > g), n, None


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
    """What the basin assembler needs: one surface, its drivers, and the refs they point at.

    `hydrologic_state` and `state_changes` are `@0.2.0` and are absent under `@0.1.0`. They are
    carried BESIDE the surface, never inside it: nothing in the assembler may fold them into
    `SurfaceState.state`, `.score` or `.value`.
    """

    surface: SurfaceState
    drivers: tuple[Driver, ...] = ()
    refs: dict[str, ProvenanceRef] = field(default_factory=dict)
    hydrologic_state: HydrologicState | None = None
    state_changes: tuple[StateChange, ...] = ()
    version: str = SHIPPED_VERSION


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


def _unknown(
    reason: str, *, prov_key: str, refs: dict[str, ProvenanceRef], version: str, drivers: tuple[Driver, ...] = ()
) -> SusceptibilityAssessment:
    refs[prov_key] = ProvenanceRef(
        source_id=SRC_CASCADE,
        source_kind=SourceKind.EXPERIMENTAL,
        method_id=_SURFACE_METHOD_BY_VERSION[version],
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
    return SusceptibilityAssessment(surface=surface, drivers=tuple(_ordered(list(drivers))), refs=refs, version=version)


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
    (PERCENTILE_FEATURE, PERCENTILE_ROW_METHOD_ID, None),
    (SWE_FEATURE, SWE_METHOD_ID, None),
    (PRECIP_FEATURE, PRECIP_METHOD_ID, None),
)

#: The widest lookback any of :data:`READ_SPECS` is read over. The velocity's history read is
#: NARROWER than this, so it is answered by narrowing this same batch and costs no statement —
#: which is the only reason a 48-hour derivative is affordable at read time.
MAIN_LOOKBACK = max(MAX_DAILY_MEAN_AGE, CONTEXT_LOOKBACK, STATE_CHANGE_LOOKBACK)


async def prefetch(k: Knowledge, basins: Sequence[Basin], *, version: str = SHIPPED_VERSION) -> None:
    """Read every basin's susceptibility rows in ONE statement instead of three per basin.

    Pure warm-up, in the sense :mod:`cascade_hydrology.forcing` documents: the same features
    and methods :func:`assess` reads, asked once across all the scopes, landing in the
    request-scoped memo. Not calling it leaves `assess` reading for itself.

    Two scope kinds and one lookback go into the first statement. The scopes are a union because
    the percentile is keyed by the gauge STATION and the two SNOTEL context features by the
    basin, and a cell that cannot exist (SWE at a station id) simply comes back empty. The
    lookback is the widest any reader needs, and `assess` still asks for its own: `[T - 48 h, T]`
    and the velocity's `[T - 102 h, T]` both lie inside it, so those reads are answered by
    narrowing this batch to precisely the rows their own statements would have returned.
    :data:`MAX_DAILY_MEAN_AGE` stays where it belongs — the staleness rule below, applied to the
    rows `assess` asked for — and is not weakened by having been fetched alongside something
    with a longer memory.

    Two conditional statements follow, both keyed on predicates `assess` re-applies verbatim so
    the batch cannot decide a different set of gauges than the set that goes on to read:

    * the climatology, only where the percentile is missing or carries no number;
    * the record context, only where the percentile is at or above :data:`RANK_READ_EDGE` — the
      exact rank is wanted precisely where the ladder is about to stop discriminating, and
      reading a 100-year record's tail at every gauge on a quiet August day would be a round
      trip bought for nothing.
    """
    gauges = gauge_ids(basins)
    scopes = gauges + [b.id for b in basins]
    if not scopes:
        return
    await k.latest_derived_features(READ_SPECS, scopes, lookback=MAIN_LOOKBACK)
    rows = {g: await _percentile_row(k, g) for g in gauges}
    stale = [g for g in gauges if _needs_climatology(rows[g])]
    if stale:
        await k.latest_derived_features(
            [(CLIMATOLOGY_FEATURE, CLIMATOLOGY_METHOD_ID, None)], stale, lookback=CLIMATOLOGY_LOOKBACK
        )
    if version == "0.1.0":
        return  # 0.1.0 knows nothing about the record context and must not read it
    hot = [g for g in gauges if _needs_record_context(rows[g])]
    if hot:
        await k.latest_derived_features(
            [(RECORD_CONTEXT_FEATURE, RECORD_CONTEXT_METHOD_ID, None)], hot, lookback=CLIMATOLOGY_LOOKBACK
        )


async def _percentile_row(k: Knowledge, gauge_id: str) -> DerivedFeature | None:
    return await k.latest_derived_feature(
        PERCENTILE_FEATURE, gauge_id, method_id=PERCENTILE_ROW_METHOD_ID, lookback=MAX_DAILY_MEAN_AGE
    )


def _needs_climatology(row: DerivedFeature | None) -> bool:
    """The condition under which :func:`assess` falls back to the climatology row.

    One predicate, used by both `assess` and `prefetch`, so the batch cannot decide a different
    set of gauges needs the fallback than the set that goes on to read it.
    """
    return row is None or row.percentile is None


def _needs_record_context(row: DerivedFeature | None) -> bool:
    """The condition under which :func:`assess` reads the stored record context. Same contract."""
    # Rounded exactly as `assess` rounds it for display: a percentile that RENDERS as 90.0 must
    # not be one this rule treats as 89.96 and silently declines to rank.
    return row is not None and row.percentile is not None and round(float(row.percentile), 1) >= RANK_READ_EDGE


async def assess(
    k: Knowledge, basin: Basin, products: dict[str, SourceProduct], *, version: str = SHIPPED_VERSION
) -> SusceptibilityAssessment:
    """The susceptibility surface for one basin at the knowledge time `k.as_of`.

    ``version`` selects the method (brief §22). ``"0.1.0"`` is the surface that shipped until
    2026-08-26 — percentile, band, drivers, no tail, no velocity, no spread — and it runs the
    same code path minus the augmentation rather than a copy of it, so the two cannot silently
    drift apart. Both are deterministic at the same knowledge time.
    """
    if version not in _SURFACE_METHOD_BY_VERSION:
        raise ValueError(f"unknown susceptibility method version {version!r}; known: {VERSIONS}")
    extended = version != "0.1.0"
    slug = basin.id.split(":")[-1]
    prov_key = f"cascade-susceptibility-{slug}"
    soil_key = "cascade-soil-unavailable"
    refs: dict[str, ProvenanceRef] = {soil_key: soil_unavailable_ref()}
    now = k.as_of

    # The soil driver exists on EVERY branch, including the UNKNOWN ones: the absence of a soil
    # claim is itself information and must not disappear when the surface cannot be computed.
    soil_driver = Driver(feature=SOIL_FEATURE, value=None, unit="pct", direction=UNAVAILABLE_DIRECTION, rank=40, prov=soil_key)

    gauge_id = basin.susceptibility_gauge_id
    if not gauge_id:
        return _unknown(NO_GAUGE_REASON, prov_key=prov_key, refs=refs, drivers=(soil_driver,), version=version)

    row = await _percentile_row(k, gauge_id)
    if _needs_climatology(row):
        climatology = await k.latest_derived_feature(
            CLIMATOLOGY_FEATURE, gauge_id, method_id=CLIMATOLOGY_METHOD_ID, lookback=CLIMATOLOGY_LOOKBACK,
        )
        reason = STALE_REASON if climatology is not None else no_climatology_reason(gauge_id)
        return _unknown(reason, prov_key=prov_key, refs=refs, drivers=(soil_driver,), version=version)

    values = row.values_json or {}
    climatology_meta = values.get("climatology") or {}
    station = await k.station(gauge_id)
    site = station.external_id if station else gauge_id
    begin_year, end_year = climatology_meta.get("begin_year"), climatology_meta.get("end_year")
    span = f"{begin_year}–{end_year}" if begin_year and end_year else "period of record unknown"
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
        return _unknown(STALE_REASON, prov_key=prov_key, refs=refs, drivers=(soil_driver,), version=version)
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
        method_id=_SURFACE_METHOD_BY_VERSION[version],
        valid_time=row.valid_time,
        retrieved_at=row.computed_at,
        freshness=obs_freshness,
        quality=quality,
        label=label,
    )

    drivers: list[Driver] = [
        Driver(feature=PERCENTILE_FEATURE, value=percentile, unit="pct", direction=SCORED_DIRECTION, rank=1, prov=obs_key),
    ]

    hydrologic_state: HydrologicState | None = None
    state_changes: tuple[StateChange, ...] = ()
    spread: dict[str, float] | None = None
    if extended:
        hydrologic_state, tail_drivers, tail_spread = await _hydrologic_state(
            k, row, values, site=site, slug=slug, refs=refs, freshness=obs_freshness,
            percentile=percentile, sample_count=sample,
            begin_year=begin_year, end_year=end_year,
        )
        drivers.extend(tail_drivers)
        spread = tail_spread
        state_changes, change_drivers = await _state_changes(
            k, gauge_id, row, site=site, slug=slug, refs=refs, freshness=obs_freshness,
        )
        drivers.extend(change_drivers)

    # 3. SNOTEL context: shown, never scored (HYDROLOGY §7)
    swe_row = await k.latest_derived_feature(SWE_FEATURE, basin.id, method_id=SWE_METHOD_ID, lookback=CONTEXT_LOOKBACK)
    drivers.append(_context_driver(
        swe_row, feature=SWE_FEATURE, rank=20, prov_key=f"awdb-swe-{slug}", refs=refs, products=products, now=now,
        fallback_label="No SNOTEL snow-water-equivalent context ingested for this basin",
    ))
    precip_row = await k.latest_derived_feature(PRECIP_FEATURE, basin.id, method_id=PRECIP_METHOD_ID, lookback=CONTEXT_LOOKBACK)
    drivers.append(_context_driver(
        precip_row, feature=PRECIP_FEATURE, rank=30, prov_key=f"awdb-prec-{slug}", refs=refs, products=products, now=now,
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
            rank=50,
            prov=xkey,
        ))

    surface = SurfaceState(
        state=state,
        horizon_h=None,  # susceptibility is a present-state surface, not a horizon surface
        score=round(percentile / 100.0, 4),
        value=Quantity(value=percentile, unit="pct"),
        # 0.1.0 published no spread. 0.2.0 publishes the reference distribution's own rank-space
        # sampling error, in the SAME unit as `value` — a dispersion with no coverage claim, and
        # never a probability. See the boundary-condition section comment.
        spread=spread,
        prov=prov_key,
        truth=TruthClass.CASCADE_DERIVED,
        confidence=confidence,
        experimental=True,
        reason=None,
    )
    return SusceptibilityAssessment(
        surface=surface,
        drivers=tuple(_ordered(drivers)),
        refs=refs,
        hydrologic_state=hydrologic_state,
        state_changes=state_changes,
        version=version,
    )


def _ordered(drivers: list[Driver]) -> list[Driver]:
    """Renumber this surface's drivers 1..n in their declared order.

    The `rank=` values above are sparse on purpose (1, 2, 3, 20, 30, 40, 50) so a driver can be
    inserted between two others without renumbering every line, and so a `rank` collision cannot
    happen by accident. The assembler renumbers again across all three surfaces; this makes the
    surface's own list dense first so a caller reading it alone sees 1..n.
    """
    return [d.model_copy(update={"rank": i}) for i, d in enumerate(sorted(drivers, key=lambda d: d.rank), start=1)]


async def _hydrologic_state(
    k: Knowledge,
    row: DerivedFeature,
    values: dict,
    *,
    site: str,
    slug: str,
    refs: dict[str, ProvenanceRef],
    freshness: Freshness,
    percentile: float,
    sample_count: int | None,
    begin_year: int | None,
    end_year: int | None,
) -> tuple[HydrologicState | None, list[Driver], dict[str, float] | None]:
    """The `@0.2.0` level statement: percentile + rank + multiple, and the boundary condition.

    Three statements about one observation, none combined with another, each carrying the sample
    it came from. The percentile is the shipped number, untouched and still clamped.
    """
    key = str(values.get("doy_key") or "")
    day_iso = values.get("day")
    if not key or not day_iso or row.value is None:
        return None, [], None
    day = date.fromisoformat(str(day_iso))
    unit = row.unit or "cfs"
    observed = float(row.value)
    ladder = {k2: float(v) for k2, v in (values.get("ladder") or {}).items()}
    reference_flow = ladder.get(f"p{REFERENCE_PERCENTILE:02d}")
    # Clamped at EITHER end — the ladder ran out, so the percentile is a bound. The label
    # below only says "at or above p95" for the top end, which is the end this change exists
    # for; a value under p05 is equally clamped and equally worth saying so.
    clamped = OUTSIDE_CLIMATOLOGY_RANGE in tuple(row.quality)

    n = int(sample_count) if sample_count else 0
    m = independent_years(n) if n else 0
    # A CLAMPED percentile is a BOUND, not an estimate: the ladder ran out and the row already
    # says so. A standard error either side of it would assert exactly the resolution the clamp
    # exists to refuse — on the Sauk at 62,600 cfs the row would read "at or above p95, exceeds
    # the whole window record, rank 1 of 491" beside "the estimate could be 92.8". Those two
    # sentences cannot both be true, and the one with a number attached is the false one.
    #
    # So the dispersion is WITHHELD rather than clipped. Clipping to [95.0, 97.2] would still be
    # a claim about where in the tail the value sits, and the tail is precisely what the ladder
    # cannot resolve. Nothing is lost: on a clamped row the discrimination is carried by the
    # exact rank and the seasonal multiple, which are exact and need no reference sampling error.
    # `band_boundary(p, None)` fails closed to UNQUANTIFIED, which never reads as "separated".
    se = None if clamped else (rank_standard_error_points(percentile, m) if m else None)
    boundary, uncertain_bands = band_boundary(percentile, se)
    spread = None if se is None else {
        # Named for what they are: one rank-space standard error either side of the estimate,
        # in percentile points. Not a confidence interval — see the section comment.
        "p_minus_1_rank_se": round(max(0.0, percentile - se), 1),
        "p_plus_1_rank_se": round(min(100.0, percentile + se), 1),
    }
    reference = ReferenceWindow(
        doy_key=key,
        window_days=DOY_WINDOW_DAYS,
        n=n,
        independent_years=m,
        period_start=begin_year,
        period_end=end_year,
        method_id=CLIMATOLOGY_METHOD_ID,
    ) if n else None

    # --- the multiple: exact division, no assumption anywhere
    multiple_value = seasonal_multiple(observed, reference_flow)
    tail_key = f"cascade-tail-{slug}"
    drivers: list[Driver] = []
    multiple_model = None
    if multiple_value is not None and reference_flow is not None:
        multiple_model = SeasonalMultiple(
            multiple=round(multiple_value, 3),
            reference_percentile=REFERENCE_PERCENTILE,
            reference=Quantity(value=reference_flow, unit=unit),
            prov=tail_key,
        )
        drivers.append(Driver(
            feature=MULTIPLE_FEATURE, value=round(multiple_value, 3), unit="x",
            direction=LEVEL_DIRECTION, rank=2, prov=tail_key,
        ))

    # --- the rank: read only where the ladder is about to stop discriminating
    context_doc: dict | None = None
    if _needs_record_context(row):
        context_row = await k.latest_derived_feature(
            RECORD_CONTEXT_FEATURE, row.scope_id, method_id=RECORD_CONTEXT_METHOD_ID, lookback=CLIMATOLOGY_LOOKBACK,
        )
        context_doc = (context_row.values_json or {}) if context_row is not None else None
    reading = window_rank(observed, key, context_doc)
    rank_model = None
    tail_quality: tuple[str, ...] = ()
    if reading is not None:
        tail_quality = reading.quality
        rank_model = RecordRank(
            rank=reading.rank,
            of=reading.of,
            exceeds_record=reading.exceeds_record,
            previous_max=None if reading.previous_max is None else Quantity(value=reading.previous_max, unit=unit),
            previous_max_day=reading.previous_max_day,
            reason=reading.reason,
            prov=tail_key,
        )
    elif _needs_record_context(row):
        rank_model = RecordRank(rank=None, of=n + 1, reason=NO_RECORD_CONTEXT_REASON, prov=tail_key)
        tail_quality = (NO_RECORD_CONTEXT,)
    elif n:
        # Below the read edge. The rank is absent BY DESIGN, and the design says so rather than
        # leaving a bare null beside a statement that refuses out loud two fields away. `of` is
        # still published because the sample size IS known — what was not computed is the
        # position within it, which is exactly what the reason explains.
        rank_model = RecordRank(rank=None, of=n + 1, reason=RANK_NOT_READ_REASON, prov=tail_key)

    refs[tail_key] = ProvenanceRef(
        source_id=SRC_CASCADE,
        # DERIVED, not EXPERIMENTAL: unlike the banded index, nothing here is calibrated or
        # judged. A rank is a count and a multiple is a division, both exact over a named
        # sample. The uncalibrated claim lives on the band, and it stays there.
        source_kind=SourceKind.DERIVED,
        method_id=TAIL_STATE_METHOD_ID,
        valid_time=row.valid_time,
        retrieved_at=row.computed_at,
        freshness=freshness,
        quality=tuple(dict.fromkeys(tuple(row.quality) + tail_quality)),
        label=_tail_label(
            site=site, day=day, observed=observed, unit=unit, key=key, reference_flow=reference_flow,
            multiple=multiple_value, reading=reading, n=n, m=m, begin_year=begin_year, end_year=end_year,
            clamped_high=clamped and percentile >= float(REFERENCE_PERCENTILE),
        ),
        raw_artifact_id=None if row.raw_artifact_id is None else str(row.raw_artifact_id),
    )
    return (
        HydrologicState(
            prov=tail_key,
            truth=TruthClass.CASCADE_DERIVED,
            observed=Quantity(value=observed, unit=unit),
            day=day,
            percentile=percentile,
            percentile_clamped=clamped,
            reference=reference,
            rank=rank_model,
            multiple=multiple_model,
            boundary=boundary,
            bands_within_sampling_error=uncertain_bands,
            reason=None,
        ),
        drivers,
        spread,
    )


def _tail_label(
    *, site: str, day: date, observed: float, unit: str, key: str, reference_flow: float | None,
    multiple: float | None, reading: TailReading | None, n: int, m: int,
    begin_year: int | None, end_year: int | None, clamped_high: bool,
) -> str:
    """The sentence a reader sees. Every clause names the sample it is a clause about."""
    period = f"{begin_year}–{end_year}" if begin_year and end_year else "period of record unknown"
    parts = [f"{observed:,.0f} {unit} at {site} on {day.isoformat()}"]
    if multiple is not None and reference_flow is not None:
        parts.append(
            f"{multiple:.2f}× the p{REFERENCE_PERCENTILE} flow for {key} "
            f"({reference_flow:,.0f} {unit}; ±{DOY_WINDOW_DAYS}-day window, {period}, "
            f"n={n} values over ~{m} independent years)"
        )
    if reading is not None and reading.rank is not None:
        if reading.exceeds_record and reading.previous_max is not None and reading.previous_max_day is not None:
            parts.append(
                f"larger than all {reading.of - 1} daily means in this window "
                f"(previous maximum {reading.previous_max:,.0f} {unit} on {reading.previous_max_day.isoformat()})"
            )
        else:
            parts.append(f"{ordinal(reading.rank)} largest of {reading.of} daily means in this window")
    elif reading is not None and reading.reason:
        parts.append(reading.reason)
    if clamped_high:
        parts.append(
            f"day-of-year percentile at or above p{REFERENCE_PERCENTILE}; the ladder does not "
            "resolve further (outside_climatology_range)"
        )
    parts.append(
        "Cascade exact rank and seasonal multiple over the stored approved daily-mean record; "
        "the record's vintage is an open question (register X8) and every level statement here "
        "inherits it. Never a probability, a return period or an AEP."
    )
    return ". ".join(parts)


async def _state_changes(
    k: Knowledge,
    gauge_id: str,
    row: DerivedFeature,
    *,
    site: str,
    slug: str,
    refs: dict[str, ProvenanceRef],
    freshness: Freshness,
) -> tuple[tuple[StateChange, ...], list[Driver]]:
    """`Q(t) / Q(t - 24 h)` and `/ Q(t - 48 h)` from the stored daily means, with their ranks.

    The history read is NARROWER than :data:`MAIN_LOOKBACK`, so `prefetch` has already answered
    it and this costs no statement. It reads the same rows the percentile came from — the daily
    mean is `DerivedFeature.value` on those rows — so the velocity and the level are computed
    over one series and cannot disagree about what the river did.
    """
    history = await k.derived_features(
        PERCENTILE_FEATURE,
        gauge_id,
        method_id=PERCENTILE_ROW_METHOD_ID,
        valid_from=k.as_of - STATE_CHANGE_LOOKBACK,
        valid_until=k.as_of,
        latest_per_valid_time=True,
    )
    points = [(r.valid_time, float(r.value)) for r in history if r.value is not None]
    unit = row.unit or "cfs"

    # The growth reference lives in the record context, which is read only in the tail. Where it
    # is absent the growth still publishes; only its rank is refused, with its reason.
    looked = _needs_record_context(row)
    context_row = (
        await k.latest_derived_feature(
            RECORD_CONTEXT_FEATURE, gauge_id, method_id=RECORD_CONTEXT_METHOD_ID, lookback=CLIMATOLOGY_LOOKBACK,
        )
        if looked
        else None
    )
    growth_reference = ((context_row.values_json or {}).get("growth") or {}) if context_row is not None else {}
    absent = NO_RECORD_CONTEXT_REASON if looked else NO_GROWTH_REFERENCE_READ_REASON

    changes: list[StateChange] = []
    drivers: list[Driver] = []
    for i, window_h in enumerate(STATE_CHANGE_WINDOWS_H):
        reading = state_change(points, end=row.valid_time, window_h=window_h)
        rank, rank_of, rank_reason = (
            growth_rank(reading.growth, growth_reference.get(str(window_h)), absent_reason=absent)
            if reading.growth is not None
            else (None, None, None)
        )
        ckey = f"cascade-change-{slug}-{window_h}h"
        refs[ckey] = ProvenanceRef(
            source_id=SRC_CASCADE,
            # DERIVED: a ratio of two stored daily means. It touches no ladder and no band.
            source_kind=SourceKind.DERIVED,
            method_id=STATE_CHANGE_METHOD_ID,
            valid_time=reading.to_time or row.valid_time,
            retrieved_at=row.computed_at,
            freshness=freshness,
            label=_change_label(site=site, unit=unit, reading=reading, rank=rank, rank_of=rank_of, rank_reason=rank_reason),
        )
        changes.append(StateChange(
            window_h=window_h,
            growth=None if reading.growth is None else round(reading.growth, 4),
            direction=reading.direction,
            from_value=None if reading.from_value is None else Quantity(value=reading.from_value, unit=unit),
            to_value=None if reading.to_value is None else Quantity(value=reading.to_value, unit=unit),
            span_h=None if reading.span_h is None else round(reading.span_h, 2),
            rank=rank,
            rank_of=rank_of,
            rank_reason=rank_reason,
            reason=reading.reason,
            prov=ckey,
        ))
        if reading.growth is not None:
            drivers.append(Driver(
                feature=GROWTH_FEATURE_TEMPLATE.format(window=window_h),
                value=round(reading.growth, 3),
                unit="x",
                direction=STATE_CHANGE_DIRECTION,
                rank=3 + i,
                prov=ckey,
            ))
    return tuple(changes), drivers


def _change_label(
    *, site: str, unit: str, reading: GrowthReading, rank: int | None, rank_of: int | None, rank_reason: str | None
) -> str:
    if reading.growth is None:
        return (
            f"Cascade {reading.window_h} h state change at {site}: not computed — {reading.reason}. "
            "Refused rather than measured over a shortened window."
        )
    parts = [
        f"Cascade {reading.window_h} h state change at {site}: ×{reading.growth:.2f} "
        f"({(reading.growth - 1.0) * 100.0:+.0f} %), {reading.direction}",
        f"{reading.from_value:,.0f} → {reading.to_value:,.0f} {unit} over {reading.span_h:.1f} h",
    ]
    if rank is not None and rank_of is not None:
        parts.append(f"{ordinal(rank)} largest of {rank_of:,} changes over this window in this gauge's own record")
    elif rank_reason:
        parts.append(rank_reason)
    parts.append(
        "A multiplicative change in the observed daily mean. It depends on no climatology "
        "ladder and no band, it is not scored against the level, and no cutoff is drawn on it."
    )
    return ". ".join(parts)
