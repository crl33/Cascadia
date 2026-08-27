"""Candidate high-tail representations for the day-of-year flow state — PROTOTYPE, nothing shipped.

`susceptibility.py` is deliberately untouched by this module. This is the decision phase for
`docs/research/high-tail-selection-2026-08-27.md`: the candidates are written out so the numbers in
that document are reproducible from code rather than from a scratch script, and so the choice can be
argued with before anything renders.

THE DEFECT THIS ANSWERS (measured, `docs/research/tier0-measured-basis-2026-08-26.md` §3). The stored
`method:streamflow-doy-climatology@1.0.0` ladder ends at `p95`, so every flow above the p95 breakpoint
ranks as exactly 95.0 — 24,976 cfs and 72,440 cfs on the Sauk read the same state — and a percentile
derivative between two clamped days is therefore identically +0 through the crest.

THE FIRST QUESTION, ANSWERED BEFORE ANY SOPHISTICATION (§2 of the research doc). The ceiling is an
IMPLEMENTATION choice: `PERCENTILES = (5, 10, 25, 50, 75, 90, 95)`. The record knows more. At the
Sauk's 12-11 key the ±2-day window holds 495 approved daily means from 99 water years, 25 of them
strictly above p95, reaching 62,600 cfs — 4.6× the p95 breakpoint. So the empirical rank CAN be
continued, and continuing it is preferred over any fitted tail.

THE SECOND QUESTION, WHICH DECIDES THE DESIGN. Continuing it is **not enough**. Event Zero's crest
exceeded the entire window sample at all four demonstration basins, so every rank-shaped answer —
an extended ladder point, a plotting position, an exact rank — saturates at the top of the record
exactly where the velocity is needed. Measured Δ over 12-09 → 12-11:

    representation                  skagit        snoh-snoq     cedar         nooksack
    shipped ladder (p05..p95)       +0.0 pts      +0.0 pts      +0.0 pts      +0.0 pts
    ladder extended to p98/p99      +0.0 pts      +1.0 pts      +0.0 pts      +0.0 pts
    exact rank in the window        3 -> 1        8 -> 1        13 -> 1       6 -> 1
    seasonal multiple Q / p95       2.37x->5.77x  1.66x->4.65x  1.39x->4.37x  1.27x->2.88x
    flow growth over the 48 h       x2.90         x3.35         x3.68         x2.70

A percentile is bounded by 100 and censored at the record maximum; a rank is bounded by 1. Only a
magnitude ratio is unbounded, and only a magnitude ratio carries a derivative through a crest. That
is why the chosen representation reports a rank AND a multiple, and why the velocity is computed on
the multiple rather than on the rank.

WHAT IS DELIBERATELY NOT HERE. No band edges, no cutoff, no score, no probability, no return period,
no weighting of anything against anything. `candidate_c_pot_gpd` exists only to return the
diagnostics that refuse it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta

# PROPOSED method ids. Nothing writes a `derived_feature` under these yet; they exist so the
# research document and any later ADR can name the same objects.
TAIL_STATE_METHOD_ID = "method:streamflow-tail-state@0.1.0"
STATE_CHANGE_METHOD_ID = "method:streamflow-state-change@0.1.0"

#: The ladder breakpoint the multiple is referenced to. p95 and not p90 or p50 for one reason that
#: is checkable rather than aesthetic: it is the TOP stored breakpoint, so `multiple >= 1.0` is
#: exactly the condition under which the shipped percentile clamps. The multiple begins precisely
#: where the percentile stops discriminating, and the two never disagree about where that is.
REFERENCE_PERCENTILE = 95

#: Quality flags. These are the vocabulary a `DerivedFeature.quality` tuple would carry; they are
#: strings here because `cascade_hydrology` may not import a provider adapter (see
#: `susceptibility.py`'s module docstring and the `lint-imports` contract).
OUTSIDE_CLIMATOLOGY_RANGE = "outside_climatology_range"  # the shipped flag, preserved verbatim
EXCEEDS_WINDOW_RECORD = "exceeds_window_record"
THIN_TAIL_SUPPORT = "thin_tail_support"
NO_REFERENCE = "no_reference_percentile"

#: A tail statement is refused unless its exceedance set spans this many distinct water years.
#: Justification, measured (research doc §4): the ±2-day window's n is days, not independent
#: events — 495 values at the Sauk are 99 water years × 5 consecutive days, and a December flood
#: contributes up to 5 of them. Jackknifing one water year out moves p99 by 0.9–19.2 %, and at
#: cedar the whole p99 exceedance set is a SINGLE water year (December 2015), which makes that
#: "climatological quantile" a description of one flood. Five is the smallest count at which the
#: point survives losing any one year; it is a support rule, not a hydrologic threshold.
MIN_TAIL_YEARS = 5

#: Below this many independent (declustered) tail events, a peaks-over-threshold fit is refused
#: outright rather than reported with wide bars. 30 is the conventional floor for a two-parameter
#: GPD; §6 of the research doc shows the fit fails on threshold sensitivity well before it fails
#: on count, so this is the weaker of the two refusals.
MIN_POT_EVENTS = 30

RISING = "rising"
FALLING = "falling"
STEADY = "steady"
UNKNOWN = "unknown"

#: `trend.py` already calls a flow steady inside ±1 %/h of its own value. Carried over unchanged so
#: two surfaces cannot call the same river steady and rising in the same breath: 1 %/h compounded is
#: ×1.27 over 24 h and ×1.61 over 48 h.
FLOW_STEADY_FRACTION_PER_H = 0.01

#: The Driver direction a state-change term carries. NOT `increases_susceptibility`: the velocity is
#: not a susceptibility input and contributes nothing to the index score, exactly as the SWE context
#: driver contributes nothing (HYDROLOGY §7's pattern, applied to a different reason).
STATE_CHANGE_DIRECTION = "state_change_not_scored"


@dataclass(frozen=True)
class WindowSample:
    """The day-of-year window sample a ladder was built from, kept whole instead of summarised.

    The shipped climatology stores seven breakpoints and throws the sample away. Every candidate
    below except (A) needs the sample itself — the rank needs the count, the support rule needs the
    water years, the refusal needs the maximum and its date. This is the object a `@2.0.0` ladder
    would have to persist; here it is built in memory so the research numbers are reproducible.

    `values` is ascending. `days` is parallel to it. `period_start` / `period_end` are the first and
    last WATER years the sample reaches — the reference period that must be printed beside every
    number derived from it, and water years rather than calendar years because a December flood
    belongs to the winter it happened in.
    """

    key: str  # the "MM-DD" day-of-year key
    values: tuple[float, ...]
    days: tuple[date, ...]
    window_days: int
    period_start: int
    period_end: int
    unit: str = "cfs"

    @staticmethod
    def from_pairs(pairs: list[tuple[date, float]], *, key: str, window_days: int, unit: str = "cfs") -> WindowSample:
        ordered = sorted(pairs, key=lambda p: p[1])
        if not ordered:
            raise ValueError(f"empty window sample for {key!r}")
        years = [water_year(d) for d, _ in ordered]
        return WindowSample(
            key=key,
            values=tuple(v for _, v in ordered),
            days=tuple(d for d, _ in ordered),
            window_days=window_days,
            period_start=min(years),
            period_end=max(years),
            unit=unit,
        )

    @property
    def n(self) -> int:
        return len(self.values)

    @property
    def n_water_years(self) -> int:
        return len({water_year(d) for d in self.days})

    @property
    def maximum(self) -> float:
        return self.values[-1]

    @property
    def maximum_day(self) -> date:
        return self.days[-1]

    def quantile(self, p: float) -> float:
        """The p-th percentile of the sample, R type 7 — the same estimator the shipped ladder uses.

        Restated rather than imported: `cascade_hydrology` may not import the USGS package, and
        `tests/unit/test_tail_candidates.py` asserts the two agree so the duplication is checked
        instead of assumed.
        """
        if self.n == 1:
            return float(self.values[0])
        rank = (self.n - 1) * (p / 100.0)
        lo = math.floor(rank)
        hi = min(lo + 1, self.n - 1)
        return float(self.values[lo] + (rank - lo) * (self.values[hi] - self.values[lo]))

    def exceedance_years(self, level: float) -> int:
        """How many distinct water years hold a value strictly above ``level``.

        The honest denominator for anything said about the tail: consecutive days of one flood are
        one piece of evidence, not five.
        """
        return len({water_year(d) for d, v in zip(self.days, self.values, strict=True) if v > level})


def water_year(day: date) -> int:
    """USGS convention: water year N runs 1 Oct N−1 → 30 Sep N."""
    return day.year + 1 if day.month >= 10 else day.year


# --------------------------------------------------------------------------------------------
# Candidate A — extend the stored ladder with more percentile breakpoints
# --------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class LadderReading:
    percentile: float
    clamped: bool
    top_breakpoint: int
    quality: tuple[str, ...]


def candidate_a_ladder_percentile(value: float, ladder: dict[int, float]) -> LadderReading:
    """Rank ``value`` between stored breakpoints, clamping at the ends — the shipped behaviour.

    Passing an extended ladder (…, 98, 99) is candidate A. It is a real improvement to the LEVEL:
    the shelf between p95 and the record maximum stops being one state. It is measurably NOT a fix
    for the velocity — with the water-year support rule applied the four Event Zero pairs move
    +0.0 / +1.0 / +0.0 / +0.0 points under it, because both endpoints still land above the highest
    breakpoint the record can carry at three of the four basins, and cedar can carry none at all.
    """
    points = sorted(ladder.items())
    if not points:
        raise ValueError("empty ladder")
    top = points[-1][0]
    if value <= points[0][1]:
        flags = (OUTSIDE_CLIMATOLOGY_RANGE,) if value < points[0][1] else ()
        return LadderReading(float(points[0][0]), True, top, flags)
    if value >= points[-1][1]:
        flags = (OUTSIDE_CLIMATOLOGY_RANGE,) if value > points[-1][1] else ()
        return LadderReading(float(points[-1][0]), True, top, flags)
    for (p_lo, v_lo), (p_hi, v_hi) in zip(points, points[1:], strict=False):
        if v_lo <= value <= v_hi:
            if v_hi == v_lo:
                return LadderReading(float(p_hi), False, top, ())
            frac = (value - v_lo) / (v_hi - v_lo)
            return LadderReading(p_lo + frac * (p_hi - p_lo), False, top, ())
    raise ValueError(f"ladder is not monotone: {points}")


def supported_breakpoints(sample: WindowSample, candidates: tuple[float, ...]) -> dict[float, float]:
    """The subset of ``candidates`` this sample can carry, by the water-year support rule.

    A breakpoint is published only where at least :data:`MIN_TAIL_YEARS` distinct water years lie
    above it. Measured consequence at the 12-11 key, ladder built from the approved record before
    WY2026: distinct water years above p98 are 8 (skagit), 8 (snoh-snoq), 6 (nooksack), 6
    (green-duwamish), 3 (cedar), 1 (puyallup-white), so p98 publishes at four gauges and is refused
    at two; above p99 they are 4 / 5 / 3 / 3 / 1 / 1, so p99 publishes at snoh-snoq alone.
    Puyallup-white — record from WY2009 — supports nothing above p90 at all. Refusing per gauge is
    the point: a uniform ladder would publish cedar's p99, whose entire exceedance set is one
    flood, December 2015.
    """
    out: dict[float, float] = {}
    for p in candidates:
        level = sample.quantile(p)
        if sample.exceedance_years(level) >= MIN_TAIL_YEARS:
            out[p] = level
    return out


# --------------------------------------------------------------------------------------------
# Candidate A′ — continue the empirical rank as an exact count, with no estimator at all
# --------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class WindowRank:
    """Where ``value`` sits among the window sample, stated as a count and nothing more.

    Deliberately NOT a plotting position. Gringorten on the Sauk's 490-value window would render
    24,976 cfs as "p99.48", advertising two decimals of resolution on a sample that is 99
    independent water years wearing 490 days' clothing. "3rd largest of 491, WY1911–WY2025" says
    the same thing and says its own sample size. This is `method:rank-in-record@1.0.0`'s device
    (register X6, method-spec M0.5) applied to the day-of-year window instead of to annual crests.
    """

    rank: int  # 1 = largest
    of: int  # sample size INCLUDING the value being ranked
    period_start: int
    period_end: int
    window_days: int
    exceeds_record: bool
    previous_max: float
    previous_max_day: date
    quality: tuple[str, ...]

    @property
    def label(self) -> str:
        span = f"WY{self.period_start}–WY{self.period_end}"
        window = f"±{self.window_days}-day window"
        if self.exceeds_record:
            return (
                f"larger than all {self.of - 1} daily means in this {window} over {span} "
                f"(previous maximum {self.previous_max:,.0f} on {self.previous_max_day.isoformat()})"
            )
        return f"{ordinal(self.rank)} largest of {self.of} daily means in this {window} over {span}"


def ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def candidate_a_prime_window_rank(value: float, sample: WindowSample) -> WindowRank:
    """The exact rank of ``value`` in the window sample. Monotone, integer, reproducible, censored.

    Censored at 1: a value above the record maximum is "the largest", and so is a value twice that.
    In the USGS approved daily series the Sauk read `rank 1` on 12-10 (41,500 cfs) and again on
    12-11 (62,600 cfs), and cedar read it for NINE consecutive days, 12-10 through 12-18, across a
    flow range of 5,160 to 10,100 cfs. That saturation is the measured reason this cannot be the
    velocity's basis — but unlike the clamped percentile it saturates HONESTLY, naming the record
    it beat.
    """
    above = sum(1 for v in sample.values if v > value)
    flags: tuple[str, ...] = ()
    if above == 0 and value > sample.maximum:
        flags = (EXCEEDS_WINDOW_RECORD,)
    return WindowRank(
        rank=above + 1,
        of=sample.n + 1,
        period_start=sample.period_start,
        period_end=sample.period_end,
        window_days=sample.window_days,
        exceeds_record=bool(flags),
        previous_max=sample.maximum,
        previous_max_day=sample.maximum_day,
        quality=flags,
    )


# --------------------------------------------------------------------------------------------
# Candidate B — the seasonal high-flow multiple
# --------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class SeasonalMultiple:
    """``value ÷ p95(day-of-year)``. Unbounded, monotone, and the only candidate with a live
    derivative in the tail.

    It is a MULTIPLE OF A SEASONAL REFERENCE, never a flood magnitude, and the label has to keep
    saying so. Measured (research doc §7): the largest multiples in these six records are late-
    summer flash events on a tiny reference — Green-Duwamish reached 8.91× on 1959-09-27 at
    8,840 cfs, a flow that against the 11 December reference reads 1.3×. The absolute flow must be rendered
    beside the multiple always, and the multiple must never be banded on a year-round cutoff.
    """

    multiple: float | None
    reference_flow: float | None
    reference_percentile: int
    key: str
    period_start: int
    period_end: int
    window_days: int
    n: int
    n_water_years: int
    unit: str
    quality: tuple[str, ...]
    reason: str | None = None

    @property
    def label(self) -> str:
        if self.multiple is None:
            return self.reason or "no reference percentile"
        return (
            f"{self.multiple:.2f}× the p{self.reference_percentile} flow for {self.key} "
            f"({self.reference_flow:,.0f} {self.unit}; ±{self.window_days}-day window, "
            f"WY{self.period_start}–WY{self.period_end}, n={self.n} over "
            f"{self.n_water_years} water years)"
        )


def candidate_b_seasonal_multiple(
    value: float, sample: WindowSample, *, reference_percentile: int = REFERENCE_PERCENTILE
) -> SeasonalMultiple:
    """The multiple of the day-of-year reference flow. No distributional assumption anywhere.

    `multiple >= 1.0` is exactly the shipped percentile's clamp condition, so this extends the
    surface rather than competing with it. UNKNOWN — with its reason — when the sample cannot
    support the reference at all, which is the honest answer at a short-record gauge.
    """
    meta = {
        "reference_percentile": reference_percentile,
        "key": sample.key,
        "period_start": sample.period_start,
        "period_end": sample.period_end,
        "window_days": sample.window_days,
        "n": sample.n,
        "n_water_years": sample.n_water_years,
        "unit": sample.unit,
    }
    reference = sample.quantile(reference_percentile)
    if not math.isfinite(reference) or reference <= 0:
        return SeasonalMultiple(
            None, None, quality=(NO_REFERENCE,), reason="reference percentile is zero or undefined", **meta
        )
    flags: list[str] = []
    if sample.exceedance_years(reference) < MIN_TAIL_YEARS:
        flags.append(THIN_TAIL_SUPPORT)
    if value > sample.maximum:
        flags.append(EXCEEDS_WINDOW_RECORD)
    return SeasonalMultiple(value / reference, reference, quality=tuple(flags), **meta)


# --------------------------------------------------------------------------------------------
# Candidate C — peaks over threshold / generalized Pareto. Evaluated in order to refuse it.
# --------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class PotDiagnostics:
    """What a POT/GPD fit would rest on, computed so the refusal is evidence and not taste."""

    threshold: float
    n_exceedances: int
    n_independent: int
    n_water_years: int
    shape: float | None
    scale: float | None
    refused: bool
    reason: str | None


def decluster(pairs: list[tuple[date, float]], threshold: float, *, separation_days: int = 7) -> list[tuple[date, float]]:
    """One peak per cluster of exceedances separated by at least ``separation_days``.

    Without this the "sample size" counts the same flood five times, which is precisely the error
    the raw window count invites.
    """
    peaks: list[tuple[date, float]] = []
    cluster: list[tuple[date, float]] = []
    for day, value in sorted(p for p in pairs if p[1] > threshold):
        if cluster and (day - cluster[-1][0]).days > separation_days:
            peaks.append(max(cluster, key=lambda t: t[1]))
            cluster = []
        cluster.append((day, value))
    if cluster:
        peaks.append(max(cluster, key=lambda t: t[1]))
    return peaks


def gpd_pwm(excesses: list[float]) -> tuple[float, float] | None:
    """Hosking probability-weighted-moment fit of a generalized Pareto to threshold excesses.

    Closed form and deterministic — chosen over MLE so the diagnostic cannot depend on an optimiser
    seed, and because the argument this supports is about threshold sensitivity, not about the
    estimator. Returns ``(shape ξ, scale σ)`` for ``F(z) = 1 − (1 + ξz/σ)^(−1/ξ)``.
    """
    y = sorted(excesses)
    n = len(y)
    if n < 5:
        return None
    a0 = sum(y) / n
    a1 = sum(y[i] * ((n - i - 1) / (n - 1)) for i in range(n)) / n
    denom = a0 - 2 * a1
    if denom == 0:
        return None
    k = a0 / denom - 2.0
    return (-k, 2 * a0 * a1 / denom)


def candidate_c_pot_gpd(
    pairs: list[tuple[date, float]], threshold: float, *, separation_days: int = 7
) -> PotDiagnostics:
    """Fit diagnostics for a peaks-over-threshold tail — and the reason this is not the answer.

    Not refused for lack of data: 7-day declustering above the cool-season p95 leaves 57–121
    independent exceedances at the five deep-record gauges (13 at puyallup-white), which is enough
    to fit. It is refused on three measured grounds (research doc §6):

    1. **The threshold choice moves the answer.** At cedar ξ runs +0.488 at p95 → +0.194 at p98 →
       −0.062 at p99: the fitted tail changes from heavy to bounded on an arbitrary choice.
    2. **Parameter uncertainty swamps the signal.** At the Sauk the 95 % bootstrap interval on ξ
       alone is 0.33–0.59 wide, and it widens as the threshold rises toward the region of interest.
    3. **Its natural output is a forbidden object.** A GPD's answer is an exceedance probability,
       from which a return period is one division away. Register X6 settles that the platform
       computes no recurrence interval, return period or AEP for any reach, ever.

    And it does not even buy the velocity: fitted non-exceedance over the four demonstration pairs
    moves +0.26 to +0.83 in probability — expressed as a percentile of all days, +1.3 to +4.1
    points — because a probability is bounded above by 1 in the same way a percentile is bounded by
    100. The unbounded quantity was the requirement, and only candidate B has one.
    """
    exceedances = [p for p in pairs if p[1] > threshold]
    peaks = decluster(pairs, threshold, separation_days=separation_days)
    years = len({water_year(d) for d, _ in peaks})
    fit = gpd_pwm([v - threshold for _, v in peaks])
    reason = (
        "peaks-over-threshold is refused: the fitted shape moves with an arbitrary threshold, its "
        "uncertainty exceeds the signal, and its output is an exceedance probability — register X6 "
        "forbids recurrence intervals, return periods and AEP for any reach"
    )
    if len(peaks) < MIN_POT_EVENTS:
        reason = f"{len(peaks)} independent exceedances is below the {MIN_POT_EVENTS}-event floor for a two-parameter fit"
    return PotDiagnostics(
        threshold=threshold,
        n_exceedances=len(exceedances),
        n_independent=len(peaks),
        n_water_years=years,
        shape=None if fit is None else fit[0],
        scale=None if fit is None else fit[1],
        refused=True,
        reason=reason,
    )


# --------------------------------------------------------------------------------------------
# The chosen representation: HYDROLOGIC STATE
# --------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class TailState:
    """Where the river is. Three statements about one observation, none combined with another.

    `percentile` is the shipped number, unchanged and still clamped — the uncalibrated bands keep
    their uncalibrated status, and no ladder vintage is decided here (register X8 stays open).
    `rank` says how unusual against a named record. `multiple` says how big against a named
    reference. There is no fourth field summarising the three, and there must never be one.
    """

    value: float
    unit: str
    percentile: LadderReading
    rank: WindowRank
    multiple: SeasonalMultiple

    @property
    def quality(self) -> tuple[str, ...]:
        seen: list[str] = []
        for flag in self.percentile.quality + self.rank.quality + self.multiple.quality:
            if flag not in seen:
                seen.append(flag)
        return tuple(seen)

    @property
    def in_extrapolated_region(self) -> bool:
        """True when the record has run out under this value — the one state that needs saying.

        Note what this does NOT mean: nothing here is extrapolated. The percentile is clamped, the
        rank is censored at 1, the multiple is an exact division. The flag says the RECORD stopped,
        not that the platform started guessing.
        """
        return self.rank.exceeds_record

    @property
    def label(self) -> str:
        return f"{self.value:,.0f} {self.unit} — {self.multiple.label}; {self.rank.label}"


def tail_state(value: float, sample: WindowSample, ladder: dict[int, float]) -> TailState:
    """Assemble the level statement. Pure; every field carries the sample it came from."""
    return TailState(
        value=value,
        unit=sample.unit,
        percentile=candidate_a_ladder_percentile(value, ladder),
        rank=candidate_a_prime_window_rank(value, sample),
        multiple=candidate_b_seasonal_multiple(value, sample),
    )


# --------------------------------------------------------------------------------------------
# The chosen velocity: STATE CHANGE
# --------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class StateChange:
    """How fast the river is moving, and which way. Computed on flow, never on the percentile.

    `growth` is Q(t) ÷ Q(t − window). It is identical to the ratio of the seasonal multiples at the
    two times taken against the SAME reference, because the reference divides out:

        R(t)/R(t−Δ) = (Q(t)/ref) / (Q(t−Δ)/ref) = Q(t)/Q(t−Δ)

    Three consequences, all load-bearing:

    * **It does not depend on the ladder.** Not on its vintage, not on its period, not on its
      breakpoints. Register X8 disputes which record a ladder should be built from; that dispute
      cannot move this number. X8 is NOT thereby resolved — the level (percentile, rank, multiple)
      still depends on the ladder entirely, and says so.
    * **It has no extrapolated region.** It is arithmetic on two observations. When the LEVEL is
      censored (`exceeds_window_record`) the change is still exact, which is the whole point: the
      Sauk read ×1.51 over 24 h on 12-11 while the shipped percentile derivative read +0.0.
    * **It keeps the measured lead.** At a matched historical base rate, first firing day in
      December 2025 is the same as the percentile-velocity convention at five of six basins and one
      day earlier at cedar (research doc §8). Nothing is given up in the body to gain the tail.
    """

    window_h: int
    growth: float | None  # Q(t) / Q(t - window_h)
    from_value: float | None
    to_value: float | None
    direction: str
    reason: str | None
    span_h: float | None = None  # the span actually covered, which is what `growth` is over

    @property
    def percent_change(self) -> float | None:
        return None if self.growth is None else (self.growth - 1.0) * 100.0

    @property
    def label(self) -> str:
        if self.growth is None:
            return f"{self.window_h} h change unknown: {self.reason}"
        return f"×{self.growth:.2f} in {self.window_h} h ({(self.growth - 1.0) * 100.0:+.0f} %), {self.direction}"


def state_change(
    points: list[tuple[datetime, float]],
    *,
    end: datetime,
    window_h: int,
    tolerance_h: float = 6.0,
) -> StateChange:
    """The multiplicative change in daily-mean flow over ``window_h``, or UNKNOWN with a reason.

    Refuses rather than interpolates, on `trend.py`'s discipline: BOTH endpoints must exist within
    ``tolerance_h`` of their targets (`end` and `end − window_h`), both values must be positive (a
    ratio through zero is not a rate), and a missing endpoint is UNKNOWN rather than a silently
    shortened window — a "24 h growth" measured over 14 h is a different number wearing the same
    label. `tolerance_h` defaults to 6 h because a daily mean is labelled by a calendar day whose
    boundary is the station's local midnight, so ±6 h absorbs the DST step and the UTC-vs-local
    boundary without admitting a different day.
    """
    if window_h <= 0:
        return StateChange(window_h, None, None, None, UNKNOWN, "window must be positive")
    ordered = sorted(points)
    if not ordered:
        return StateChange(window_h, None, None, None, UNKNOWN, f"no observation at or before {end.isoformat()}")
    tolerance = timedelta(hours=tolerance_h)
    latest = [(t, v) for t, v in ordered if t <= end and (end - t) <= tolerance]
    if not latest:
        return StateChange(
            window_h, None, None, None, UNKNOWN,
            f"no observation at or before {end.isoformat()} within {tolerance_h:g} h of it",
        )
    t_now, q_now = latest[-1]
    target = end - timedelta(hours=window_h)
    prior = [(t, v) for t, v in ordered if abs(t - target) <= tolerance]
    if not prior:
        return StateChange(
            window_h, None, None, q_now, UNKNOWN,
            f"no observation within {tolerance_h:g} h of {target.isoformat()}",
        )
    t_then, q_then = min(prior, key=lambda p: abs(p[0] - target))
    span_h = (t_now - t_then).total_seconds() / 3600.0
    if span_h <= 0:
        return StateChange(window_h, None, q_then, q_now, UNKNOWN, "the two observations do not span any time")
    if q_then <= 0 or q_now <= 0:
        return StateChange(
            window_h, None, q_then, q_now, UNKNOWN,
            "a zero or negative flow has no multiplicative rate", span_h,
        )
    growth = q_now / q_then
    # The steady band is `trend.py`'s ±1 %/h compounded over the ACTUAL span, so a 24 h and a 48 h
    # term cannot disagree about whether the same river is steady.
    eps = (1.0 + FLOW_STEADY_FRACTION_PER_H) ** span_h
    direction = STEADY if (1.0 / eps) <= growth <= eps else (RISING if growth > 1.0 else FALLING)
    return StateChange(window_h, growth, q_then, q_now, direction, None, span_h)


def growth_rank(growth: float, history: list[float]) -> tuple[int, int]:
    """Where ``growth`` sits among this gauge's own past changes over the same window.

    The descriptive answer to "is that fast?" that does not require a cutoff. Returns
    ``(rank, n)`` with rank 1 = largest. Measured: the Sauk's ×3.00 on 12-06 ranks 200th of 35,976
    day-pairs, and its ×1.51 on 12-11 — a day the shipped derivative read +0.0 — still ranks
    1,514th, inside the top 5 %.

    What would justify a cutoff instead of a rank: a probability-of-detection / false-alarm-ratio
    curve over a multi-event catalogue at all six basins (milestone brief §18). Until that exists,
    the rank is published and no band is drawn on it.
    """
    return (sum(1 for g in history if g > growth) + 1, len(history))
