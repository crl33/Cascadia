"""Candidate robust trend estimators — PROTOTYPE, not wired in (Tier 0 brief §3 / §4).

`trend.py` ships `rate = (pts[-1] - pts[0]) / span_h`, an endpoint difference that
`HYDROLOGY.md` §9 already forbids in words ("trend never comes from the two endpoints of a
response window"). This module holds the candidates that were measured against real hydrographs
in `docs/research/trend-estimator-selection-2026-08-26.md`, plus the metadata envelope and the
tidal guard the same document specifies.

**Nothing here is called by `assemble.py`.** This phase decides; the next phase implements.
`trend.py` is untouched so the A/B in the research note compares the shipped code against the
candidates, not against a half-migrated version of itself.

What is here
------------
- four slope estimators over ``(hours, value)`` pairs built from **actual timestamps**
  (`endpoint_slope`, `ols_slope`, `theil_sen_slope`, `repeated_median_slope`);
- `pairwise_slope_spread` — the interquartile range of the Theil-Sen pair slopes, a
  *dispersion*, never a probability;
- `TidalClass` + `tidal_refusal` — the method-level refusal of brief §4, keyed on an explicit
  per-station marker that fails **closed** when the marker is absent;
- `TrendEstimate` — the full metadata envelope (method id + version, window, sample count,
  actual span, slope, slope unit, valid time, quality condition, input provenance);
- `estimate_trend` — the candidate assembly, showing how the pieces compose.

Doctrine held here
------------------
- **Stage and discharge never mix.** `basis` is carried, the unit is carried, and no function
  in this module converts one into the other (`HYDROLOGY.md` §9).
- **Native units only.** These estimators are for the observed stage/flow series. Applying a
  slope estimator to a *percentile* series inherits that ladder's p95 clamp and reads +0
  through a crest (`research/tier0-measured-basis-2026-08-26.md` §3). See
  `PERCENTILE_SPACE_WARNING`.
- **UNKNOWN with a machine-readable reason** beats a number nobody can defend.
- The STEADY epsilons are **imported from `trend.py` unchanged**. This change does not
  recalibrate them; an A/B fitted to Event Zero would prove nothing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Literal

from cascade_hydrology.trend import (
    FALLING,
    RISING,
    STEADY,
    UNKNOWN,
    steady_epsilon,
)

__all__ = [
    "PERCENTILE_SPACE_WARNING",
    "METHOD_ID",
    "Basis",
    "TidalClass",
    "TrendQuality",
    "TrendRefusal",
    "TrendEstimate",
    "endpoint_slope",
    "ols_slope",
    "theil_sen_slope",
    "repeated_median_slope",
    "pairwise_slope_spread",
    "tidal_refusal",
    "estimate_trend",
]

#: The identity a wired-in version would publish. Bumped from `method:rate-of-rise@1.0.0`
#: because the *estimator* changes, not merely its parameters — a consumer comparing two
#: stored trends must be able to see that they were computed by different mathematics.
METHOD_ID = "method:rate-of-rise@2.0.0-candidate"

PERCENTILE_SPACE_WARNING = (
    "These estimators operate on native-unit observations (ft, cfs). Do not apply them to a "
    "day-of-year percentile series: the stored ladders clamp at p95, so every value above the "
    "p95 flow ranks 95.0 and any slope through the crest is identically +0 "
    "(research/tier0-measured-basis-2026-08-26.md §3). The percentile-space derivative is a "
    "different quantity and cannot ship until the high tail is fixed alongside it."
)

Basis = Literal["stage", "flow"]


# ---------------------------------------------------------------------------
# Slope estimators. Each takes hours-since-window-start and values, already
# cleaned of sentinels, sorted by time, and with duplicate timestamps removed.
# `xs` is built from ACTUAL timestamps; nothing here assumes regular spacing.
# ---------------------------------------------------------------------------


def endpoint_slope(xs: list[float], ys: list[float]) -> float:
    """The shipped estimator, kept here only so the A/B can call it (`trend.py` §rate)."""
    span = xs[-1] - xs[0]
    return (ys[-1] - ys[0]) / span


def ols_slope(xs: list[float], ys: list[float]) -> float:
    """Ordinary least squares slope of y on x. O(n), breakdown point 0."""
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) * (x - mx) for x in xs)
    if sxx == 0.0:
        raise ValueError("degenerate design: all timestamps identical")
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True))
    return sxy / sxx


def _median(vals: list[float]) -> float:
    s = sorted(vals)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 else 0.5 * (s[mid - 1] + s[mid])


def _pair_slopes(xs: list[float], ys: list[float]) -> list[float]:
    out: list[float] = []
    n = len(xs)
    for i in range(n - 1):
        xi, yi = xs[i], ys[i]
        for j in range(i + 1, n):
            dx = xs[j] - xi
            if dx > 0.0:  # duplicate timestamps contribute no slope, they do not blow up
                out.append((ys[j] - yi) / dx)
    return out


def theil_sen_slope(xs: list[float], ys: list[float]) -> float:
    """Median of all pairwise slopes. O(n^2) pairs; breakdown point 1 - 1/sqrt(2) ~ 29.3 %."""
    slopes = _pair_slopes(xs, ys)
    if not slopes:
        raise ValueError("degenerate design: no pair spans a positive time interval")
    return _median(slopes)


def repeated_median_slope(xs: list[float], ys: list[float]) -> float:
    """Siegel's repeated median: median over i of (median over j != i of the (i,j) slope).

    Breakdown point 50 %. Kept as a candidate because the realistic telemetry failure at a
    USGS gauge is a *run* of bad values (a frozen sensor, an ice-affected stage, a datalogger
    holding its last reading), not an isolated spike, and a run longer than ~29 % of the
    window defeats Theil-Sen.

    MEASURED, and this is the estimator the selection note chose: on a 40 % held run it errs by
    0.14 STEADY epsilons against Theil-Sen's 0.24, and on a corrupted endpoint reading by 0.00
    against the shipped endpoint difference's 45.69 (selection note §3).
    """
    n = len(xs)
    inner: list[float] = []
    for i in range(n):
        xi, yi = xs[i], ys[i]
        row = [(ys[j] - yi) / (xs[j] - xi) for j in range(n) if xs[j] != xi]
        if row:
            inner.append(_median(row))
    if not inner:
        raise ValueError("degenerate design: no pair spans a positive time interval")
    return _median(inner)


def pairwise_slope_spread(xs: list[float], ys: list[float]) -> tuple[float, float, float]:
    """(q25, q50, q75) of the Theil-Sen pair slopes — a **dispersion**, not a probability.

    Free once the pairs exist, distribution-free, and in the slope's own units. It answers
    "how much do the sub-intervals of this window disagree about the rate", which is the
    honest thing to publish beside a rate. It is NOT a confidence interval and must never be
    presented as one.
    """
    slopes = sorted(_pair_slopes(xs, ys))
    if not slopes:
        raise ValueError("degenerate design: no pair spans a positive time interval")

    def q(p: float) -> float:
        if len(slopes) == 1:
            return slopes[0]
        pos = p * (len(slopes) - 1)
        lo = int(pos)
        hi = min(lo + 1, len(slopes) - 1)
        return slopes[lo] + (pos - lo) * (slopes[hi] - slopes[lo])

    return q(0.25), q(0.50), q(0.75)


# ---------------------------------------------------------------------------
# Tidal guard (brief §4). A refusal keyed on an explicit marker — NOT a de-tiding
# subsystem, which the 2026-08-26 verification showed no seeded gauge needs.
# ---------------------------------------------------------------------------


class TidalClass(str, Enum):
    """Per-station tidal marker. The default is the one that refuses.

    `FLUVIAL` is a **measurement**, not an assumption: it may only be set for a station whose
    semidiurnal (M2) amplitude has been measured against a coastal reference with a known
    non-tidal control gauge carried through the same pipeline
    (`research/tidal-gauge-verification-2026-08-26.md` §3). All six seeded points carry it on
    that evidence (M2 <= 0.008 ft; injected 6 h rate <= 0.025 ft/h against a 0.05 ft/h STEADY
    epsilon). SNAW1 12155500 would carry `TIDAL` (M2 2.97 ft at low flow) — it is not seeded.
    """

    FLUVIAL = "FLUVIAL"
    TIDAL = "TIDAL"
    UNVERIFIED = "UNVERIFIED"


#: Refusal reasons, machine-readable. A consumer switches on these; the prose is for humans.
REASON_INSUFFICIENT_OBSERVATIONS = "INSUFFICIENT_OBSERVATIONS"
REASON_GAP_EXCEEDS_TOLERANCE = "GAP_EXCEEDS_TOLERANCE"
REASON_SPAN_BELOW_MINIMUM = "SPAN_BELOW_MINIMUM"
REASON_TIDAL_CONTAMINATION = "TIDAL_CONTAMINATION"
REASON_TIDAL_CLASS_UNVERIFIED = "TIDAL_CLASS_UNVERIFIED"


@dataclass(frozen=True)
class TrendRefusal:
    reason: str  # one of the REASON_* constants
    detail: str  # human prose, may name numbers; never the only thing a consumer reads


def tidal_refusal(tidal_class: TidalClass | None) -> TrendRefusal | None:
    """The whole guard. Two lines of logic and one property: it fails **closed**.

    - `TIDAL`  -> refuse, `TIDAL_CONTAMINATION`. Rate of rise at a tidal gauge is not noisy,
      it is meaningless: a pure M2 tide of amplitude A injects a false endpoint rate of
      A/3 to A/2 ft/h at any window shorter than half a tidal cycle, and no robust estimator
      removes it (verification §5.1, and §5 of the selection note injects a 1.0 ft M2 tide onto a real
      record: every candidate reports 4.6-6.5x the STEADY epsilon, and the most robust one is
      the WORST of them).
    - `None` / `UNVERIFIED` -> refuse, `TIDAL_CLASS_UNVERIFIED`. This is the property the
      brief asks for: a future tidally-affected station **cannot silently bypass** the guard,
      because there is no code path in which an unmarked station is treated as fluvial.
      Seeding a station therefore requires the M2 measurement first, which is exactly what
      the verification's §7 item 6 already demands.
    - `FLUVIAL` -> no refusal. All six seeded points are FLUVIAL on measured evidence, so the
      guard does not fire for anything the platform serves today.

    The guard is basis-independent: the tidal wave contaminates a stage record and a discharge
    record alike (SNAW1 has no published discharge, so there is no counter-example to test).
    """
    if tidal_class is TidalClass.FLUVIAL:
        return None
    if tidal_class is TidalClass.TIDAL:
        return TrendRefusal(
            REASON_TIDAL_CONTAMINATION,
            "station is marked TIDAL: a semidiurnal water-level signal makes rate of rise, "
            "and any time-to-threshold derived from it, meaningless without de-tiding",
        )
    return TrendRefusal(
        REASON_TIDAL_CLASS_UNVERIFIED,
        "station carries no measured tidal class; trend is refused until the semidiurnal "
        "amplitude has been measured against a coastal reference with a non-tidal control",
    )


# ---------------------------------------------------------------------------
# The metadata envelope.
# ---------------------------------------------------------------------------


class TrendQuality(str, Enum):
    """A *condition*, attached to every non-refused estimate. Not a score, not a weight."""

    OK = "OK"
    #: Fewer points than the window's nominal cadence implies, but above the hard minimum.
    SPARSE_SUPPORT = "SPARSE_SUPPORT"
    #: The pair-slope IQR is wide relative to |slope| — sub-intervals disagree about the rate.
    WIDE_SLOPE_SPREAD = "WIDE_SLOPE_SPREAD"


@dataclass(frozen=True)
class TrendEstimate:
    """Everything a displayed rate must carry to answer the one rule (CLAUDE.md)."""

    # identity
    method_id: str  # e.g. method:rate-of-rise@2.0.0
    estimator: str  # theil_sen | ols | repeated_median | endpoint
    # what was asked
    basis: Basis  # stage | flow — never converted into the other
    window_h: float  # the window requested
    window_end: datetime  # the trailing edge; the knowledge-time `as_of` of the caller
    # what was found
    n: int  # sample count actually used
    span_h: float  # ACTUAL first-to-last span, which is <= window_h
    max_gap_h: float  # largest gap between consecutive samples used
    first_valid_time: datetime
    last_valid_time: datetime  # the estimate's own valid time
    # the answer
    slope: float | None
    slope_unit: str | None  # e.g. "ft/h", "cfs/h" — always <basis unit>/h
    direction: str  # rising | falling | steady | unknown
    steady_eps: float | None  # the epsilon this direction was decided against
    slope_q25: float | None  # pair-slope dispersion, NOT a confidence interval
    slope_q75: float | None
    # honesty
    quality: TrendQuality | None
    refusal: TrendRefusal | None
    # provenance of the inputs
    tidal_class: TidalClass | None
    station_id: str
    input_product_ids: tuple[str, ...] = ()
    input_revision_seqs: tuple[int, ...] = ()
    input_quality_flags: tuple[str, ...] = ()
    raw_artifact_ids: tuple[int, ...] = ()
    notes: tuple[str, ...] = field(default_factory=tuple)


#: Windows are named, per `HYDROLOGY.md` §9. The live surface uses 6 h (`assemble.py`).
NAMED_WINDOWS_H = (1.0, 3.0, 6.0)

#: Minimum samples. Three, not two: with two points every estimator in this module collapses
#: to the endpoint difference, which is the defect being removed.
MIN_SAMPLES = 3

#: How wide the pair-slope IQR may be, as a multiple of |slope|, before the estimate is marked
#: WIDE_SLOPE_SPREAD. This is a **labelling** rule, not a suppression rule: nothing is hidden
#: and no direction changes. It is deliberately not a calibrated cutoff.
WIDE_SPREAD_RATIO = 2.0


def estimate_trend(
    points: list[tuple[datetime, float]],
    *,
    station_id: str,
    basis: Basis,
    unit: str,
    end: datetime,
    tidal_class: TidalClass | None,
    window_h: float = 6.0,
    max_gap_h: float = 2.0,
    min_span_fraction: float = 0.5,
    estimator: str = "theil_sen",
    expected_cadence_h: float = 0.25,
) -> TrendEstimate:
    """Candidate assembly. Same refusal ladder as `trend.py`, plus the tidal guard first.

    The tidal guard runs **before** anything is computed: a refusal that depends on the data
    would be a guard the data could talk its way out of.
    """
    empty = dict(
        method_id=METHOD_ID,
        estimator=estimator,
        basis=basis,
        window_h=window_h,
        window_end=end,
        slope=None,
        slope_unit=None,
        direction=UNKNOWN,
        steady_eps=None,
        slope_q25=None,
        slope_q75=None,
        quality=None,
        tidal_class=tidal_class,
        station_id=station_id,
    )

    guard = tidal_refusal(tidal_class)
    if guard is not None:
        return TrendEstimate(
            n=0, span_h=0.0, max_gap_h=0.0, first_valid_time=end, last_valid_time=end,
            refusal=guard, **empty,
        )

    start = end - timedelta(hours=window_h)
    pts = sorted((t, v) for t, v in points if start <= t <= end and v is not None)
    # collapse duplicate timestamps to the last value seen at that instant
    dedup: list[tuple[datetime, float]] = []
    for t, v in pts:
        if dedup and dedup[-1][0] == t:
            dedup[-1] = (t, v)
        else:
            dedup.append((t, v))
    pts = dedup

    if len(pts) < MIN_SAMPLES:
        return TrendEstimate(
            n=len(pts), span_h=0.0, max_gap_h=0.0,
            first_valid_time=pts[0][0] if pts else end, last_valid_time=pts[-1][0] if pts else end,
            refusal=TrendRefusal(
                REASON_INSUFFICIENT_OBSERVATIONS,
                f"{len(pts)} usable observations in the last {window_h:g} h; {MIN_SAMPLES} required",
            ),
            **empty,
        )

    gaps = [(b[0] - a[0]).total_seconds() / 3600 for a, b in zip(pts, pts[1:], strict=False)]
    worst = max(gaps)
    span_h = (pts[-1][0] - pts[0][0]).total_seconds() / 3600
    if worst > max_gap_h:
        return TrendEstimate(
            n=len(pts), span_h=span_h, max_gap_h=worst,
            first_valid_time=pts[0][0], last_valid_time=pts[-1][0],
            refusal=TrendRefusal(
                REASON_GAP_EXCEEDS_TOLERANCE,
                f"gap of {worst:.2f} h between observations exceeds the {max_gap_h:g} h tolerance",
            ),
            **empty,
        )
    if span_h < min_span_fraction * window_h:
        return TrendEstimate(
            n=len(pts), span_h=span_h, max_gap_h=worst,
            first_valid_time=pts[0][0], last_valid_time=pts[-1][0],
            refusal=TrendRefusal(
                REASON_SPAN_BELOW_MINIMUM,
                f"observations span only {span_h:.2f} h of the {window_h:g} h window",
            ),
            **empty,
        )

    t0 = pts[0][0]
    xs = [(t - t0).total_seconds() / 3600 for t, _ in pts]
    ys = [v for _, v in pts]

    fn = {
        "endpoint": endpoint_slope,
        "ols": ols_slope,
        "theil_sen": theil_sen_slope,
        "repeated_median": repeated_median_slope,
    }[estimator]
    slope = fn(xs, ys)
    q25, _, q75 = pairwise_slope_spread(xs, ys)

    eps = steady_epsilon(basis, ys[-1])
    direction = STEADY if abs(slope) <= eps else (RISING if slope > 0 else FALLING)

    expected_n = max(MIN_SAMPLES, int(span_h / expected_cadence_h))
    if len(pts) < 0.75 * expected_n:
        quality = TrendQuality.SPARSE_SUPPORT
    elif abs(slope) > 0 and (q75 - q25) > WIDE_SPREAD_RATIO * abs(slope):
        quality = TrendQuality.WIDE_SLOPE_SPREAD
    else:
        quality = TrendQuality.OK

    return TrendEstimate(
        n=len(pts), span_h=span_h, max_gap_h=worst,
        first_valid_time=pts[0][0], last_valid_time=pts[-1][0],
        refusal=None,
        **{
            **empty,
            "slope": slope,
            "slope_unit": f"{unit}/h",
            "direction": direction,
            "steady_eps": eps,
            "slope_q25": q25,
            "slope_q75": q75,
            "quality": quality,
        },
    )
