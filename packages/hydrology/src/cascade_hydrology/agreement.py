"""Model agreement v0 — `method:model-agreement@0.2.0` (design §3.2, docs/HYDROLOGY.md §6).

What this surface answers: *does an independent model see the same event the official forecast
sees?* It compares the NWRFC's official river forecast with the NWM v3.1 medium-range ensemble
at the same forecast point, over **one shared window**, on the same variable (flow, in cfs). It
answers on three axes — magnitude, timing and, where official **flow** thresholds exist,
category — and it says out loud when an axis has nothing to measure.

The rules that are not negotiable, and are enforced by construction here:

- **Nothing is averaged across sources.** The official crest and the model crest are carried as
  two separate numbers with two separate ProvenanceRefs of two different `source_kind`s. There
  is no consensus value, no blend, no "best estimate" (docs/DATA_DOCTRINE.md §10). Disagreement
  is the information.
- **The model's central value is a member, not a mean.** `C_nwm` is the lower-median *member*
  crest — a hydrograph the model actually produced — so the crest, its timing and its shape all
  come from the same series. The NWPS-computed `mean` series is stored and displayed as the
  model hydrograph but is never the comparison value and never a member.
- **UNKNOWN is a real answer.** Six distinct preconditions each produce UNKNOWN with a specific
  reason. At CRNW1 the official run carries no usable flow column at all (0 of 40 points; every
  secondary value is the −9999 sentinel), so agreement there is UNKNOWN *correctly* and must
  never regress into a fabricated comparison.
- **Category agreement exists only where official flow thresholds exist** — AUBW1 and WRAW1 of
  the six seed points. At the other four the official categories are defined in stage and
  ADR-0011 forbids inventing flow equivalents, so category is reported as not comparable.
- **The bands are an ASSUMPTION, stated as one.** 0.25/0.60, 6 h/18 h and the 5 % shape
  thresholds are a first cut carried in `BANDS` with that sentence attached; they are not
  calibrated against outcomes and the exit tests check reproducibility and the UNKNOWN paths,
  never correctness. Calibration is hindcast work (ADR-0008).

Two defects found by adversarial verification on 2026-08-24 are fixed here, and both were
*defects of meaning* rather than arithmetic — the numbers were computed correctly and did not
mean what the level said they meant.

**Finding B — the two crests were maxima over different windows.** Design §3.2 requires both
crests over `(as_of − 6 h, as_of + 72 h]` "so hazard and agreement are talking about the same
event". As built, the official crest was taken at read time over that `as_of`-anchored window
while the member crests were frozen at ingest over the cycle-anchored `(cycle, cycle + 72 h]`.
The two differ by the cycle age (5–14 h in practice): the model's crest could sit *before the
official window opened* (measured 2 h 43 m before at MVEW1) and the official window's final
hours were invisible to the model side. `Δt` was then partly a measurement of the cycle age, and
on a rising hydrograph the magnitude comparison was biased with it. The live "before" table made
it visible arithmetically: `Δt = 81 h` and `82 h` inside a window only 78 h wide. **The fix is
that no crest is frozen at ingest at all** — `reaches_jobs` stores the member hydrographs and
`comparison_window` + `read_hydrograph` take every maximum here, over one window that both sides
share by construction.

**Finding A — `agreement = low` was produced by a timing term with nothing to measure.** When
both hydrographs are recessions with no interior maximum, the "crest time" is just whichever end
of a nearly flat line is a hair higher, and `Δt` becomes the width of the window. At MVEW1 that
produced `Δt = 75 h` and a `low` level while the two forecasts agreed on magnitude to **0.6 %**.
In a dry Cascade summer that is the *normal* reading, so `low` was uninformative exactly when it
is shown most often — and, worse, it read as "the models disagree" about a river they agreed
about. The treatment here: **timing is only assessed when there is a crest to time.** A series
must have an interior maximum that rises materially above both window edges before its crest
time is a time at all (`read_hydrograph`). When neither forecast crests inside the window, the
timing term is not invented, not defaulted and not counted: agreement rests on magnitude and
category, and the reason says plainly that neither forecast expects a crest — which is itself
agreement about the hydrograph. When exactly *one* forecasts a crest, that is a real difference
in shape, so the level is capped at MODERATE and named. The same cap applies when neither
crests but one hydrograph rises across the window while the other recedes: the two maxima can
agree to a fraction of a percent while the forecasts point opposite ways about what happens
next, and "high agreement" would over-claim. Nothing here reports either case as disagreement —
MODERATE with a sentence naming both shapes is what the inputs support. What v0 deliberately
does NOT do is grade the *size* of a trend difference; the shape words are recorded and shown,
and a calibrated trend-agreement axis is a later method version.

**A third defect, found by re-verification on 2026-08-25 and fixed here — the percentage in the
sentence named the wrong denominator.** `Δ` is divided by `max(C_off, floor)`, and at the two
points that have an official action FLOW the floor wins that max by a wide margin. At AUBW1 the
official crest was 294.7 cfs and the median member 379.3 cfs — 28.7 % of the official crest apart
— while `Δ` was 1.4 % of the 6,000 cfs action flow, and the sentence read "The NWM median member
peaks 1% above the NWRFC forecast". The floor is the correct denominator for the *band* (85 cfs
on a river that acts at 6,000 cfs is hydrologically nothing) and the wrong thing to attribute to
the forecast. Worse, the clause that would have explained the scaling was emitted only when the
floor was ABSENT — exactly the case where the sentence was already true. The sentence now states
the difference in cfs and names the action flow the percentage is a fraction of, and
`method_record["magnitude"]` carries the denominator and its basis.

`AgreementLevel` is a level of *agreement between two forecasts*, never a probability and never
a statement that either forecast is right.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from cascade_contracts import FloodCategory
from cascade_contracts.visualization import AgreementLevel, AgreementState, Driver
from cascade_core.knowledge import Knowledge
from cascade_core.models import ForecastPoint, ForecastRun
from cascade_core.registry import PRODUCT_NWM_MR
from cascade_core.timeutils import parse_iso
from cascade_hydrology.category import ORDER, Measure, ThresholdSet, categorize
from cascade_hydrology.surfaces import HAZARD_HORIZON_H, Crest

METHOD_ID = "method:model-agreement@0.2.0"
MODEL_LABEL = "nwm-v3.1-medium-range"

#: The hazard window's look-back edge. `surfaces.forecast_crest` uses `(as_of − 6 h, as_of + H]`
#: and agreement must use the same one, so the constant is named rather than spelled twice.
LOOKBACK_H = 6.0

#: The central member is chosen by index, never by arithmetic: for an even member count the
#: lower of the two central crests, i.e. always a hydrograph the model actually produced. The
#: alternative (the mean of the two central crests) would invent a value no member forecast and
#: would leave the crest time and the crest's shape without a series to come from.
MEDIAN_RULE = "lower_median_member"

#: Read-side copies of the vocabulary `cascade_providers_nwps.reaches_jobs` writes. Hydrology
#: does not import provider packages, so the constants are declared on both sides and pinned
#: together by a test (tests/unit/test_agreement.py::test_feature_vocabulary_matches_the_writer).
FEATURE_MEMBER_SERIES = "nwm_mr_member_flow_series"
METHOD_MEMBER_SERIES = "method:nwm-member-series@2.0.0"
SERIES_SCHEMA = "nwm-member-series@1"
ENCODING_GRID = "grid"
ENCODING_POINTS = "points"

OFFICIAL_PROV_PREFIX = "nwps-forecast-"
MODEL_PROV_PREFIX = "nwm-mr-"

#: Hydrograph shapes inside the comparison window. Only `CREST` carries a crest *time*; the
#: other three are ways of having no crest, and they are distinguished because "flat" and
#: "still rising at the edge" are different facts about a river.
SHAPE_CREST = "crest"
SHAPE_RISING = "rising"
SHAPE_RECEDING = "receding"
SHAPE_FLAT = "flat"
SHAPE_WORDS = {
    SHAPE_CREST: "crests inside the window",
    SHAPE_RISING: "rising",
    SHAPE_RECEDING: "receding",
    SHAPE_FLAT: "flat",
}


@dataclass(frozen=True)
class AgreementBands:
    """Method parameters, versioned with the method id — never spelled inline in the logic.

    ASSUMPTION, and it travels with the numbers: these boundaries are a stated first cut for
    western-Washington basins. They are **not calibrated**. Nothing downstream may present an
    agreement level as a likelihood that either forecast verifies.

    `crest_prominence` and `flat_amplitude` are the shape test behind finding A. A window
    maximum is a *crest* only if it is interior and stands at least `crest_prominence` of itself
    above the higher of the two window edges; a hydrograph whose whole range across the window is
    under `flat_amplitude` is flat and has no trend to read either. Both are relative, so they
    mean the same thing on a 200 cfs creek and a 130 kcfs river.
    """

    high_magnitude: float = 0.25
    high_timing_h: float = 6.0
    moderate_magnitude: float = 0.60
    moderate_timing_h: float = 18.0
    moderate_category_steps: int = 1
    crest_prominence: float = 0.05
    flat_amplitude: float = 0.05
    #: Below this the shared window is a sliver of the hazard horizon and its maximum is not the
    #: event's crest on either side, so the answer is UNKNOWN rather than a comparison of ends.
    min_comparison_window_h: float = 24.0
    #: Losing less than this off the end of the hazard window is not worth a caveat; more is.
    truncation_tolerance_h: float = 1.0
    assumption: str = (
        "Agreement bands (|Δ| 0.25/0.60, Δt 6 h/18 h, category 0/1 steps, 5% crest prominence "
        "and 5% flat amplitude) are an uncalibrated first cut stated as an assumption; they are "
        "not a verified skill measure (ADR-0008)."
    )


BANDS = AgreementBands()

# Reason vocabulary. Each string names the missing input, because "unknown" without the reason
# is indistinguishable from "calm" to a reader (docs/DATA_DOCTRINE.md §12).
REASON_NO_OFFICIAL_RUN = "No official NWRFC forecast is known at this knowledge time, so there is nothing to compare against."
REASON_NO_OFFICIAL_FLOW = (
    "The NWRFC forecast for {lid} carries no flow column (every secondary value is the −9999 "
    "sentinel); NWM produces flow only, so the two cannot be compared without a rating "
    "conversion (not in v0)."
)
REASON_NO_OFFICIAL_CREST = (
    "The official NWRFC forecast for {lid} has no flow value inside the {horizon}-hour hazard window."
)
REASON_NO_MODEL_RUN = "No NWM medium-range run is known at this knowledge time for this point's reach."
REASON_NO_MEMBERS = "The stored NWM cycle for {lid} carries no member hydrographs, so no member statistic can be formed."
REASON_WINDOW_TOO_SHORT = (
    "The newest NWM cycle for {lid} is {age:.0f} h old, so it and the official forecast share "
    "only {shared:.0f} h of the {horizon}-hour hazard window — too little for either maximum to "
    "be the crest of the same event."
)
REASON_UNREADABLE_SERIES = (
    "The stored NWM cycle for {lid} is in payload format {schema}, which this version of the "
    "agreement method does not read; the archived response is still there to re-derive it from."
)
REASON_NO_MODEL_VALUES = (
    "The stored NWM cycle for {lid} has no member values inside the window it shares with the "
    "official forecast."
)
REASON_NON_POSITIVE = (
    "The official forecast crest at {lid} is not a positive flow, so a relative divergence would "
    "be an artefact of the denominator rather than a disagreement."
)
CATEGORY_STAGE_ONLY = (
    "Official flood categories at this point are defined in stage; NWM produces flow. Magnitude "
    "and timing are compared; category is not."
)
CATEGORY_NO_THRESHOLDS = (
    "No official flood categories are known for this point, so category agreement is not computed."
)

QUALITY_NO_FLOOR = "no_divergence_floor"
#: Every member crested at the SAME value inside the window. NWM medium-range members share one
#: forcing early in the run (design §3.1 measured them identical for roughly the first 48 h), and
#: on a recession the crest lands in the first hours — so `k of n members` can become `k of n
#: copies of one number`. Measured live 2026-08-24: 1 distinct crest across 6 members at all six
#: seed reaches. The fraction is still counted and reported (it is not fabricated), but a count
#: over identical members is not the independent evidence `k of n` normally implies, so the fact
#: is carried out with it (docs/DATA_DOCTRINE.md §9(b)).
QUALITY_DEGENERATE_ENSEMBLE = "members_identical_in_window"
#: Neither forecast has an interior maximum in the window: there is no crest to time, so the
#: timing axis is not assessed at all rather than assessed against the window's edges.
QUALITY_TIMING_NOT_ASSESSABLE = "timing_not_assessable_no_crest"
#: Exactly one of the two forecasts crests inside the window. That is a disagreement about the
#: shape of the hydrograph, not a timing offset, so it caps the level instead of feeding Δt.
QUALITY_SHAPE_DISAGREEMENT = "one_forecast_crests_the_other_does_not"
#: Neither crests, but one is rising across the window while the other recedes. The two maxima
#: can still be a fraction of a percent apart — that is agreement about the *level* — while the
#: forecasts point in opposite directions about where the river is going next. Not a
#: disagreement, and never reported as one; it caps the level at MODERATE and is named.
QUALITY_TREND_DISAGREEMENT = "trends_oppose_without_a_crest"
#: The NWM cycle's stored coverage ends before the hazard window does, so the shared window is
#: shorter than `(as_of − 6 h, as_of + 72 h]`. Both maxima are still taken over the SAME window;
#: what is lost is how far into the future that window reaches.
QUALITY_WINDOW_TRUNCATED = "window_truncated_by_model_coverage"
#: The official run is published on a coarser step than the model's hourly series. Recorded
#: whenever that is true, NOT only when the timing axis is assessable — the asymmetry is a fact
#: about the MAGNITUDE comparison first: a maximum taken over 13 six-hourly samples and a maximum
#: taken over 78 hourly samples of the same window are not the same measurement, and on a flashy
#: hydrograph the coarser series is the one that can step over the peak. Measured live 2026-08-25
#: at all five comparable points: official 6.0 h / 13 points against model 1.0 h / 78 points, and
#: under the old timing-only condition the flag was recorded at none of them (§P3.9).
QUALITY_COARSE_OFFICIAL_STEP = "official_series_coarser_than_model"

#: Long-form notes: what each quality flag means, in full, for the method record. The reason
#: string a reader sees is one sentence (`_reason`); these are what an explanation view serves
#: behind `AgreementState.explanation_ref`, and what a reviewer reads in `AgreementResult`.
METHOD_NOTES: dict[str, str] = {
    QUALITY_NO_FLOOR: (
        "The divergence is measured against the official crest itself: this point has no official "
        "action FLOW threshold to floor the denominator with, so a small summer crest turns a "
        "small absolute difference into a large percentage."
    ),
    QUALITY_DEGENERATE_ENSEMBLE: (
        "Every NWM member reaches the same maximum inside this window — medium-range members share "
        "one forcing early in the run — so the median member is not the centre of a spread, and any "
        "member fraction here counts one forecast n times rather than n independent opinions."
    ),
    QUALITY_TIMING_NOT_ASSESSABLE: (
        "Neither hydrograph has an interior maximum that rises materially above both edges of the "
        "window, so neither forecast places a crest inside it. There is no crest time to compare; "
        "the timing axis is not assessed rather than assessed against the window's edges, which "
        "would measure the width of the window and call it a disagreement."
    ),
    QUALITY_SHAPE_DISAGREEMENT: (
        "One forecast crests inside the window and the other does not. That is a difference in the "
        "shape of the hydrograph, not an offset in timing, so it is not expressed as a Δt; it caps "
        "the level at MODERATE and is stated in the reason."
    ),
    QUALITY_TREND_DISAGREEMENT: (
        "Neither forecast crests inside the window, but one rises across it while the other recedes. "
        "The two maxima may still agree closely, and that agreement about the level is reported as "
        "it stands; what the level may not claim is that the two forecasts agree outright while they "
        "point in opposite directions. The cap is MODERATE. A hydrograph whose whole range across "
        "the window is under the flat threshold has no trend to contradict and never triggers this."
    ),
    QUALITY_WINDOW_TRUNCATED: (
        "The stored NWM cycle does not reach the end of the hazard window, so both maxima are taken "
        "over the shorter window the two forecasts share. The comparison is still like-for-like; "
        "what it does not cover is the tail of the official horizon."
    ),
    QUALITY_COARSE_OFFICIAL_STEP: (
        "The official run is published on a coarser time step than the NWM series (6-hourly against "
        "hourly at every seed point measured so far). Both maxima are taken over the same window, "
        "but not over the same number of samples of it: on a peaked hydrograph the coarser series "
        "can step over a crest the finer one resolves, which biases the difference toward 'the "
        "model exceeds the official forecast'. Where a crest time is compared at all, Δt is only as "
        "precise as that step."
    ),
    CATEGORY_STAGE_ONLY: CATEGORY_STAGE_ONLY,
    CATEGORY_NO_THRESHOLDS: CATEGORY_NO_THRESHOLDS,
}

#: Short clauses, for the one sentence a reader gets. At most two are appended, chosen by the
#: order in `_CAVEAT_ORDER`: the full text of every flag is in the method record.
CAVEAT_CLAUSES: dict[str, str] = {
    QUALITY_WINDOW_TRUNCATED: "the NWM cycle covers only the first {shared:.0f} h of that window",
    QUALITY_NO_FLOOR: "the percentage is scaled by the official crest rather than an action flow",
    QUALITY_DEGENERATE_ENSEMBLE: "all {members:.0f} NWM members reach the same peak",
    CATEGORY_STAGE_ONLY: "official flood categories here are stage-only so none could be compared",
}
#: Priority, and it is an argument about how a reader misreads a level rather than about which
#: caveat is most technical. First the window the numbers describe; then what was NOT compared at
#: all, because "high agreement" read as "everything agrees" is the largest available error; then
#: what distorts the percentage; then what the ensemble is not. Only the first
#: `MAX_CAVEAT_CLAUSES` become clauses — the rest are in `method_record["notes"]` in full.
_CAVEAT_ORDER = (QUALITY_WINDOW_TRUNCATED, CATEGORY_STAGE_ONLY, QUALITY_NO_FLOOR, QUALITY_DEGENERATE_ENSEMBLE)
MAX_CAVEAT_CLAUSES = 2


@dataclass(frozen=True)
class MemberCrest:
    member: str
    value: float  # cfs
    valid_time: datetime


@dataclass(frozen=True)
class ComparisonWindow:
    """The one window both forecasts are maximised over, and what it cost to make it one.

    `hazard_start`/`hazard_end` are the window the hazard surface uses; `start`/`end` are that
    window intersected with the stored NWM coverage. In normal operation (cycle age under
    `MAX_CYCLE_AGE_H`) the two are the same apart from the look-back edge, and the intersection
    exists only so that a stale cycle degrades into a stated, narrower window instead of a silent
    comparison across two different spans.
    """

    start: datetime
    end: datetime
    hazard_start: datetime
    hazard_end: datetime
    cycle: datetime
    coverage_h: int

    @property
    def hours(self) -> float:
        return max((self.end - self.start).total_seconds() / 3600.0, 0.0)

    @property
    def hazard_hours(self) -> float:
        return (self.hazard_end - self.hazard_start).total_seconds() / 3600.0

    @property
    def lost_tail_h(self) -> float:
        """Hours of the hazard window the model cycle does not reach."""
        return max((self.hazard_end - self.end).total_seconds() / 3600.0, 0.0)

    @property
    def as_of(self) -> datetime:
        """The knowledge time this window was built for; the hazard window is anchored on it."""
        return self.hazard_start + timedelta(hours=LOOKBACK_H)

    @property
    def cycle_age_h(self) -> float:
        """How old the cycle is at `as_of` — the offset that used to corrupt Δt silently."""
        return (self.as_of - self.cycle).total_seconds() / 3600.0

    def contains(self, t: datetime) -> bool:
        return self.start < t <= self.end

    def describe(self) -> dict[str, object]:
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "hours": round(self.hours, 2),
            "hazard_start": self.hazard_start.isoformat(),
            "hazard_end": self.hazard_end.isoformat(),
            "model_cycle": self.cycle.isoformat(),
            "model_coverage_h": self.coverage_h,
            "cycle_age_h": round(self.cycle_age_h, 2),
            "lost_tail_h": round(self.lost_tail_h, 2),
        }


@dataclass(frozen=True)
class Hydrograph:
    """One forecast's flow series inside the comparison window, with its shape read off it.

    `crest` is the window maximum — always defined when there are points. `shape` says whether
    that maximum is a *crest* (an interior peak standing materially above both edges) or just
    the higher end of a line that is rising, receding or flat. Only a `crest` has a crest time
    worth comparing, and that distinction is the whole of finding A.
    """

    name: str
    points: tuple[tuple[datetime, float], ...]
    crest: Crest
    shape: str
    prominence: float
    amplitude: float
    interior: bool

    @property
    def crests_in_window(self) -> bool:
        return self.shape == SHAPE_CREST

    @property
    def step_h(self) -> float | None:
        if len(self.points) < 2:
            return None
        return min((self.points[i + 1][0] - self.points[i][0]).total_seconds() for i in range(len(self.points) - 1)) / 3600.0

    def describe(self) -> dict[str, object]:
        return {
            "series": self.name,
            "shape": self.shape,
            "crest": self.crest.value,
            "crest_time": self.crest.valid_time.isoformat(),
            "crest_is_interior": self.interior,
            "relative_prominence": round(self.prominence, 4),
            "relative_amplitude": round(self.amplitude, 4),
            "points": len(self.points),
            "step_h": self.step_h,
        }


@dataclass(frozen=True)
class ModelEnsembleWindow:
    """Every stored NWM member, clipped to the comparison window and classified.

    The median is chosen here rather than at ingest because it depends on the crests, and the
    crests depend on the window, and the window is only known at `as_of` (finding B).
    """

    issued_at: datetime
    coverage_h: int
    unit: str
    members: tuple[Hydrograph, ...]
    window: ComparisonWindow | None = None
    median_rule: str = MEDIAN_RULE

    @property
    def member_count(self) -> int:
        return len(self.members)

    @property
    def crests(self) -> tuple[MemberCrest, ...]:
        return tuple(MemberCrest(m.name, m.crest.value, m.crest.valid_time) for m in self.members)

    @property
    def median_member(self) -> Hydrograph | None:
        if not self.members:
            return None
        ordered = sorted(self.members, key=lambda m: (m.crest.value, m.crest.valid_time, m.name))
        return ordered[(len(ordered) - 1) // 2]


@dataclass(frozen=True)
class AgreementResult:
    """The numbers behind the level. Official and model values never merge into one field.

    `method_record` is the long form: the window both maxima came from, both hydrograph shapes,
    the band parameters with their assumption, and the full text of every quality flag. The
    reason a reader sees is one sentence; this is where the detail that would not fit lives.
    """

    state: AgreementLevel
    reason: str | None
    official_crest: Crest | None = None
    model_crest: MemberCrest | None = None
    magnitude_divergence: float | None = None  # (C_nwm − C_off) / max(C_off, floor), signed
    timing_divergence_h: float | None = None  # None when there is no crest to time
    timing_assessable: bool = False
    official_shape: str | None = None
    model_shape: str | None = None
    window: ComparisonWindow | None = None
    official_category: FloodCategory | None = None
    model_category: FloodCategory | None = None
    category_steps: int | None = None
    category_note: str | None = None
    model_probability: dict[str, str | float] | None = None
    member_count: int = 0
    quality: tuple[str, ...] = ()
    method_record: dict[str, object] = field(default_factory=dict)


# --------------------------------------------------------------------------------------
# the shared window, and reading a hydrograph inside it
# --------------------------------------------------------------------------------------
def hazard_window(as_of: datetime, horizon_h: int = HAZARD_HORIZON_H) -> tuple[datetime, datetime]:
    """`(as_of − 6 h, as_of + horizon]` — exactly the window `surfaces.forecast_crest` uses.

    Pinned by a test against `forecast_crest` itself, because agreement and hazard talking about
    different events is the defect this module exists to have fixed (design §3.2)."""
    return as_of - timedelta(hours=LOOKBACK_H), as_of + timedelta(hours=horizon_h)


def comparison_window(
    *, as_of: datetime, issued_at: datetime, coverage_h: int, horizon_h: int = HAZARD_HORIZON_H
) -> ComparisonWindow:
    """The hazard window intersected with what the stored NWM cycle actually covers.

    Both crests are taken over this one interval. When the cycle is fresh enough — which is the
    designed case, `reaches_normalize.COVERAGE_HORIZON_H` is sized for it — the intersection ends
    exactly where the hazard window ends and nothing is lost but the look-back hours before the
    cycle existed, which no model can speak to anyway.
    """
    hazard_start, hazard_end = hazard_window(as_of, horizon_h)
    coverage_end = issued_at + timedelta(hours=coverage_h)
    return ComparisonWindow(
        start=max(hazard_start, issued_at),
        end=min(hazard_end, coverage_end),
        hazard_start=hazard_start,
        hazard_end=hazard_end,
        cycle=issued_at,
        coverage_h=coverage_h,
    )


def clip(values: list[tuple[datetime, float | None]], window: ComparisonWindow) -> tuple[tuple[datetime, float], ...]:
    """Sentinel-free, ascending points inside the window. Nothing is interpolated onto the edges."""
    return tuple(sorted(((t, v) for t, v in values if v is not None and window.contains(t)), key=lambda tv: tv[0]))


def read_hydrograph(name: str, points: tuple[tuple[datetime, float], ...], *, bands: AgreementBands = BANDS) -> Hydrograph | None:
    """The window maximum, and whether that maximum is a crest or just the higher end of a line.

    A *crest* has to be somewhere a river actually peaks: an interior point (not the first or the
    last sample in the window) standing at least `crest_prominence` of itself above the higher of
    the two edges. Everything else is classified by what the series is doing — `flat` when its
    whole range is under `flat_amplitude`, otherwise `rising` or `receding` — and carries no crest
    time. Returns None only when there is nothing in the window to read.

    The tie rule matches `surfaces.forecast_crest`: on equal values the earliest time wins, so a
    flat maximum is reported at its first occurrence rather than at an arbitrary one.
    """
    if not points:
        return None
    values = [v for _, v in points]
    peak = max(values)
    index = values.index(peak)
    at = points[index][0]
    first, last = values[0], values[-1]
    interior = 0 < index < len(values) - 1
    prominence = (peak - max(first, last)) / peak if peak > 0 else 0.0
    amplitude = (peak - min(values)) / peak if peak > 0 else 0.0
    if amplitude < bands.flat_amplitude:
        shape = SHAPE_FLAT
    elif interior and prominence >= bands.crest_prominence:
        shape = SHAPE_CREST
    else:
        shape = SHAPE_RISING if last >= first else SHAPE_RECEDING
    return Hydrograph(
        name=name,
        points=points,
        crest=Crest(value=peak, valid_time=at),
        shape=shape,
        prominence=prominence,
        amplitude=amplitude,
        interior=interior,
    )


# --------------------------------------------------------------------------------------
# category and the member fraction
# --------------------------------------------------------------------------------------
def _category_of(value: float, thresholds: ThresholdSet | None) -> tuple[FloodCategory, str | None]:
    """Flood category of a flow value, or (UNKNOWN, why) when the official basis is not flow.

    The note distinguishes the two ways category can be unavailable, because they are different
    facts about the world: no official categories at all, versus categories that exist in stage
    while the model produces flow (ADR-0011 forbids inventing the flow equivalent)."""
    if thresholds is None:
        return FloodCategory.UNKNOWN, CATEGORY_NO_THRESHOLDS
    result = categorize(Measure(basis="flow", value=value, unit="cfs"), thresholds, label="Forecast crest")
    if result.category is FloodCategory.UNKNOWN:
        return FloodCategory.UNKNOWN, CATEGORY_STAGE_ONLY if thresholds.basis != "flow" else result.reason
    return result.category, None


def _steps(a: FloodCategory, b: FloodCategory) -> int | None:
    """Ordinal distance between two flood categories; None when either is not comparable."""
    ladder = (FloodCategory.NONE,) + tuple(FloodCategory(c) for c in ORDER)
    if a not in ladder or b not in ladder:
        return None
    return abs(ladder.index(a) - ladder.index(b))


def member_exceedance(
    members: tuple[MemberCrest, ...], thresholds: ThresholdSet | None
) -> dict[str, str | float] | None:
    """The one honestly probabilistic number v0 can print: *k of n members crest above C*.

    Only defined where the official thresholds are in **flow** — at the four stage-threshold
    points ADR-0011 forbids inventing a flow equivalent, so this returns None and the caller
    says why. The reported category is the highest official category any member reaches (the
    lowest defined category when none do), so the statement is the most specific one the members
    support and is fully reproducible. `members` is the observed count, never assumed
    (design §7 item 4); it is reported so the fraction can be checked.
    """
    if not members or thresholds is None or thresholds.basis != "flow" or thresholds.unit != "cfs":
        return None
    defined = thresholds.defined()
    if not defined:
        return None
    reached = [(c, v) for c, v in defined if any(m.value >= v for m in members)]
    category, level = reached[-1] if reached else defined[0]
    exceeding = sum(1 for m in members if m.value >= level)
    return {
        "model": MODEL_LABEL,
        "exceeds": category,
        "fraction": exceeding / len(members),
        "members": float(len(members)),
        "exceeding": float(exceeding),
        # How many of those members are actually distinct inside the window. When this is 1 the
        # fraction can only be 0 or 1 and is a binary indicator, not an empirical frequency —
        # the reader is told rather than left to assume n independent draws.
        "distinct_member_crests": float(len({m.value for m in members})),
    }


# --------------------------------------------------------------------------------------
# the comparison
# --------------------------------------------------------------------------------------
def _magnitude_phrase(delta: float, *, difference: float | None = None, floor: float | None = None) -> str:
    """How far apart the two crests are, stated on the basis the number was actually computed on.

    `delta` is `(C_nwm - C_off) / max(C_off, floor)`. Where the FLOOR won that max, a percentage
    read as a fraction "of the NWRFC forecast" is wrong by the ratio between the two denominators
    — measured live at AUBW1 on 2026-08-25 the two crests were 294.7 and 379.3 cfs, **28.7 % of
    the official crest apart**, while `delta` was 1.4 % of the 6,000 cfs action flow and the
    sentence said "peaks 1% above the NWRFC forecast". The floor is the right denominator for the
    BAND (a 85 cfs difference on a river that acts at 6,000 cfs is hydrologically nothing) and the
    wrong number to attribute to the forecast, so when it is in use the sentence states the
    difference in cfs and `_basis_phrase` names what the percentage is a fraction of.
    """
    if floor is not None and difference is not None:
        if round(abs(difference)) == 0:
            return "within 1 cfs of"
        return f"{abs(difference):,.0f} cfs {'above' if difference > 0 else 'below'}"
    pct = abs(delta) * 100
    if pct < 1:
        return "within 1% of"
    return f"{pct:.0f}% {'above' if delta > 0 else 'below'}"


def _basis_phrase(delta: float, floor: float | None) -> str:
    """Names the denominator when it is not the official crest. Empty when it is."""
    if floor is None:
        return ""
    pct = abs(delta) * 100
    shown = "under 1%" if pct < 1 else f"{pct:.0f}%"
    return f" ({shown} of this point's {floor:,.0f} cfs action flow)"


def _timing_phrase(official: Hydrograph, model: Hydrograph, delta_t: float | None) -> str:
    """The clause about *when*, and it never claims a comparison that was not made."""
    if delta_t is not None:
        if delta_t < 0.5:
            return " and crests at the same time"
        later = model.crest.valid_time > official.crest.valid_time
        return f" and crests {delta_t:.0f} h {'later' if later else 'earlier'}"
    if official.crests_in_window != model.crests_in_window:
        who = "the NWRFC forecast" if official.crests_in_window else "NWM"
        return f", and only {who} crests inside this window"
    if official.shape == model.shape:
        return f", and neither crests inside this window (both {SHAPE_WORDS[official.shape]})"
    return (
        f", and neither crests inside this window (official {SHAPE_WORDS[official.shape]}, "
        f"NWM {SHAPE_WORDS[model.shape]})"
    )


def _caveat_clauses(
    quality: tuple[str, ...], category_note: str | None, facts: dict[str, float], *, delta: float, bands: AgreementBands
) -> tuple[str, ...]:
    """At most `MAX_CAVEAT_CLAUSES` short clauses, chosen by priority. The rest is in the record.

    `no_divergence_floor` earns a clause only when the percentage is big enough for the missing
    denominator to be what made it big. At 0.6 % divergence the floor changes nothing a reader
    would act on, and spending one of two clauses on it would push out a caveat that does.
    """
    flags = list(quality) + ([category_note] if category_note == CATEGORY_STAGE_ONLY else [])
    if abs(delta) <= bands.high_magnitude:
        flags = [f for f in flags if f != QUALITY_NO_FLOOR]
    out = [CAVEAT_CLAUSES[f].format(**facts) for f in _CAVEAT_ORDER if f in flags]
    return tuple(out[:MAX_CAVEAT_CLAUSES])


def _reason(
    *,
    delta: float,
    official: Hydrograph,
    model: Hydrograph,
    delta_t: float | None,
    quality: tuple[str, ...],
    category_note: str | None,
    facts: dict[str, float],
    bands: AgreementBands,
    difference: float | None = None,
    floor_basis: float | None = None,
) -> str:
    """One sentence about this basin's state. Not a list of everything that could be said.

    The panel renders this verbatim, so it is written as prose a reader can finish: what the two
    forecasts say about magnitude, what they say about timing (including that they say nothing,
    when that is the truth), and at most two short qualifying clauses. Every limitation is still
    recorded in full in `AgreementResult.method_record` / `METHOD_NOTES`.
    """
    sentence = (
        f"The NWM median member peaks {_magnitude_phrase(delta, difference=difference, floor=floor_basis)} "
        f"the NWRFC forecast{_basis_phrase(delta, floor_basis)}"
        f"{_timing_phrase(official, model, delta_t)}"
    )
    clauses = _caveat_clauses(quality, category_note, facts, delta=delta, bands=bands)
    return f"{sentence}; {' and '.join(clauses)}." if clauses else f"{sentence}."


def compare(
    *,
    lid: str,
    official: Hydrograph | None,
    ensemble: ModelEnsembleWindow | None,
    window: ComparisonWindow | None = None,
    thresholds: ThresholdSet | None = None,
    floor: float | None = None,
    horizon_h: int = HAZARD_HORIZON_H,
    bands: AgreementBands = BANDS,
) -> AgreementResult:
    """Compare one official hydrograph with one NWM member ensemble. Pure; every branch testable.

    Both arguments are already clipped to the same window by the caller — that is the invariant
    this function cannot restore for itself and must not pretend to.

    `floor` guards the divergence denominator: a ratio taken against a near-zero official crest
    manufactures disagreement out of arithmetic. The official **action** flow is the floor where
    it exists; where it does not, the quality flag `no_divergence_floor` is recorded so the
    limitation travels with the number instead of being lost.
    """
    if official is None:
        return AgreementResult(AgreementLevel.UNKNOWN, REASON_NO_OFFICIAL_CREST.format(lid=lid, horizon=horizon_h), window=window)
    if ensemble is None:
        return AgreementResult(AgreementLevel.UNKNOWN, REASON_NO_MODEL_RUN, window=window)
    model = ensemble.median_member
    if model is None:
        return AgreementResult(AgreementLevel.UNKNOWN, REASON_NO_MEMBERS.format(lid=lid), window=window)

    crests = ensemble.crests
    model_crest = MemberCrest(model.name, model.crest.value, model.crest.valid_time)
    denominator = max(official.crest.value, floor or 0.0)
    quality: tuple[str, ...] = () if floor is not None else (QUALITY_NO_FLOOR,)
    if len({c.value for c in crests}) == 1 and len(crests) > 1:
        quality += (QUALITY_DEGENERATE_ENSEMBLE,)
    if window is not None and window.lost_tail_h > bands.truncation_tolerance_h:
        quality += (QUALITY_WINDOW_TRUNCATED,)
    if denominator <= 0:
        return AgreementResult(
            AgreementLevel.UNKNOWN,
            REASON_NON_POSITIVE.format(lid=lid),
            official_crest=official.crest,
            model_crest=model_crest,
            official_shape=official.shape,
            model_shape=model.shape,
            window=window,
            member_count=ensemble.member_count,
            quality=quality,
        )

    delta = (model.crest.value - official.crest.value) / denominator

    # --- the timing axis, assessed only when there is a crest to time (finding A) -----------
    timing_assessable = official.crests_in_window and model.crests_in_window
    shapes_disagree = official.crests_in_window != model.crests_in_window
    delta_t: float | None = None
    if (official.step_h or 0.0) > (model.step_h or 0.0):
        # Recorded on the MAGNITUDE axis, not just the timing one: the two maxima come from
        # series sampled 6 h and 1 h apart whether or not either of them is a crest.
        quality += (QUALITY_COARSE_OFFICIAL_STEP,)
    if timing_assessable:
        delta_t = abs((model.crest.valid_time - official.crest.valid_time).total_seconds()) / 3600.0
    elif shapes_disagree:
        quality += (QUALITY_SHAPE_DISAGREEMENT,)
    else:
        quality += (QUALITY_TIMING_NOT_ASSESSABLE,)
        if {official.shape, model.shape} == {SHAPE_RISING, SHAPE_RECEDING}:
            quality += (QUALITY_TREND_DISAGREEMENT,)

    official_category, note = _category_of(official.crest.value, thresholds)
    model_category, _ = _category_of(model.crest.value, thresholds)
    steps = None if note is not None else _steps(official_category, model_category)
    probability = member_exceedance(crests, thresholds)

    timing_high = delta_t is None or delta_t <= bands.high_timing_h
    timing_moderate = delta_t is None or delta_t <= bands.moderate_timing_h
    within_high = (
        abs(delta) <= bands.high_magnitude
        and timing_high
        and steps in (0, None)
        and not shapes_disagree
        and QUALITY_TREND_DISAGREEMENT not in quality
    )
    within_moderate = (
        abs(delta) <= bands.moderate_magnitude
        and timing_moderate
        and (steps is None or steps <= bands.moderate_category_steps)
    )
    state = AgreementLevel.HIGH if within_high else (AgreementLevel.MODERATE if within_moderate else AgreementLevel.LOW)

    facts = {"members": float(ensemble.member_count), "shared": window.hours if window else 0.0}
    difference = model.crest.value - official.crest.value
    # The floor is the denominator only when it WON the max. When the official crest is the
    # larger of the two, the percentage really is a fraction of the official crest and the
    # sentence needs no basis clause.
    floor_basis = floor if (floor is not None and floor > official.crest.value) else None
    reason = _reason(
        delta=delta,
        official=official,
        model=model,
        delta_t=delta_t,
        quality=quality,
        category_note=note,
        facts=facts,
        bands=bands,
        difference=difference,
        floor_basis=floor_basis,
    )
    record: dict[str, object] = {
        "method_id": METHOD_ID,
        "bands": {
            "high_magnitude": bands.high_magnitude,
            "moderate_magnitude": bands.moderate_magnitude,
            "high_timing_h": bands.high_timing_h,
            "moderate_timing_h": bands.moderate_timing_h,
            "crest_prominence": bands.crest_prominence,
            "flat_amplitude": bands.flat_amplitude,
            "assumption": bands.assumption,
        },
        # What Δ was divided by, in words and in cfs. Without it the record cannot tell a reader
        # (or a reviewer) whether "1%" is a fraction of a 295 cfs forecast or of a 6,000 cfs
        # action flow — the two differ by a factor of 20 at AUBW1.
        "magnitude": {
            "difference_cfs": difference,
            "denominator_cfs": denominator,
            "denominator_basis": "action_flow" if floor_basis is not None else "official_crest",
            "delta": delta,
        },
        "window": window.describe() if window is not None else None,
        "official": official.describe(),
        "model": {**model.describe(), "median_rule": ensemble.median_rule, "member_count": ensemble.member_count},
        "timing_assessable": timing_assessable,
        "notes": [METHOD_NOTES[f] for f in quality if f in METHOD_NOTES]
        + ([METHOD_NOTES[note]] if note in METHOD_NOTES else []),
    }
    return AgreementResult(
        state=state,
        reason=reason,
        official_crest=official.crest,
        model_crest=model_crest,
        magnitude_divergence=delta,
        timing_divergence_h=delta_t,
        timing_assessable=timing_assessable,
        official_shape=official.shape,
        model_shape=model.shape,
        window=window,
        official_category=official_category,
        model_category=model_category,
        category_steps=steps,
        category_note=note,
        model_probability=probability,
        member_count=ensemble.member_count,
        quality=quality,
        method_record=record,
    )


# --------------------------------------------------------------------------------------
# reading the stored cycle back
# --------------------------------------------------------------------------------------
def decode_series(block: object) -> tuple[tuple[datetime, float | None], ...] | None:
    """One member's stored hydrograph, or None for an encoding this version does not implement.

    Refusing an unknown encoding matters more than it looks: a half-understood series would
    produce a crest at the wrong time, which is precisely the class of error finding B was."""
    if not isinstance(block, dict):
        return None
    encoding = block.get("encoding")
    if encoding == ENCODING_GRID:
        t0 = block.get("t0")
        step = block.get("step_h")
        flows = block.get("flow")
        if not isinstance(flows, list) or t0 is None or not isinstance(step, (int, float)):
            return None
        start = parse_iso(str(t0))
        return tuple(
            (start + timedelta(hours=float(step) * i), None if v is None else float(v))
            for i, v in enumerate(flows)
        )
    if encoding == ENCODING_POINTS:
        raw = block.get("points")
        if not isinstance(raw, list):
            return None
        return tuple(
            (parse_iso(str(p[0])), None if p[1] is None else float(p[1]))
            for p in raw
            if isinstance(p, (list, tuple)) and len(p) == 2
        )
    return None


def ensemble_from_feature(
    values_json: dict | None,
    *,
    issued_at: datetime | None,
    window: ComparisonWindow,
    bands: AgreementBands = BANDS,
) -> ModelEnsembleWindow | None:
    """Rebuild the member hydrographs from a stored row and clip them to the comparison window.

    Every crest, the median member and both shapes are derived *here*, at read time, against the
    window the official forecast is being read over. Nothing about the ensemble is inherited from
    ingest except the member values themselves.
    """
    if not isinstance(values_json, dict) or issued_at is None:
        return None
    if values_json.get("schema") != SERIES_SCHEMA:
        return None  # an unrecognised payload shape is refused, never partially believed
    raw = values_json.get("series")
    if not isinstance(raw, dict) or not raw:
        return None
    members: list[Hydrograph] = []
    for name, block in sorted(raw.items()):
        points = decode_series(block)
        if points is None:
            # A partial ensemble is a fabricated ensemble: dropping the members this version
            # cannot read would move the median and quietly change the fraction's denominator.
            return None
        hydrograph = read_hydrograph(name, clip(list(points), window), bands=bands)
        if hydrograph is not None:
            members.append(hydrograph)
    if not members:
        return None
    return ModelEnsembleWindow(
        issued_at=issued_at,
        coverage_h=int(values_json.get("coverage_h") or window.coverage_h),
        unit=str(values_json.get("unit") or "cfs"),
        members=tuple(members),
        window=window,
    )


async def latest_model_cycle(k: Knowledge, fp_id: str) -> tuple[ForecastRun | None, dict | None]:
    """The latest NWM cycle known at T at this point, with the member series stored beside it.

    The run is read **by product id**: `forecast_run` holds the official forecast too, and asking
    for "the latest run" without saying which product is the defect this whole surface depends on
    not existing (design §3.4 defect 1)."""
    run = await k.latest_forecast_run(fp_id, product_ids=frozenset({PRODUCT_NWM_MR}))
    if run is None:
        return None, None
    rows = await k.derived_features(
        FEATURE_MEMBER_SERIES,
        fp_id,
        method_id=METHOD_MEMBER_SERIES,
        valid_from=run.issued_at,
        valid_until=run.issued_at,
    )
    same_cycle = [r for r in rows if r.issued_at == run.issued_at]
    if not same_cycle:
        return run, None
    return run, same_cycle[-1].values_json


@dataclass(frozen=True)
class AgreementAssessment:
    """What the assembler needs: the contract object, the drivers, and the runs to build refs for.

    `runs_by_prov_key` is deliberately the assembler's job to turn into ProvenanceRefs (through
    `assemble.forecast_run_ref`, which resolves `source_kind` from the registry). This module
    never constructs a ProvenanceRef, so it cannot get a badge wrong, and hydrology keeps a
    single place where run provenance is built.

    Two notes for the assembler:

    - the official key is the SAME key `assemble.assess_point` already registers for that point
      (`nwps-forecast-<lid>`) and refers to the same run, so it should be merged, not overwritten
      — `assess_point` sets `valid_time` on it to the official crest time, which is the more
      informative ref;
    - `model_probability` belongs on `HazardState.model_probability`, and the reason why it is
      absent at the four stage-threshold points is already carried in `state.reason`.
    """

    state: AgreementState
    result: AgreementResult
    drivers: tuple[Driver, ...]
    runs_by_prov_key: dict[str, ForecastRun]
    model_probability: dict[str, str | float] | None


def _timing_direction(result: AgreementResult) -> str:
    """What the timing driver is saying, including that it is saying nothing and why."""
    if not result.timing_assessable:
        if QUALITY_SHAPE_DISAGREEMENT in result.quality:
            return "only_one_forecast_crests_in_window"
        return "neither_forecast_crests_in_window"
    if result.official_crest is None or result.model_crest is None:
        return "unknown"
    later = (result.model_crest.valid_time - result.official_crest.valid_time).total_seconds()
    return "model_later" if later > 0 else ("model_earlier" if later < 0 else "model_same_time")


def _drivers(result: AgreementResult, *, official_key: str, model_key: str) -> tuple[Driver, ...]:
    if result.official_crest is None or result.model_crest is None:
        return ()
    delta = result.magnitude_divergence or 0.0
    return (
        Driver(feature="agreement_crest_flow_official", value=round(result.official_crest.value, 1), unit="cfs", direction="reference", rank=1, prov=official_key),
        Driver(
            feature="agreement_crest_flow_nwm_median",
            value=round(result.model_crest.value, 1),
            unit="cfs",
            direction="model_exceeds_official" if delta > 0 else ("model_below_official" if delta < 0 else "model_matches_official"),
            rank=2,
            prov=model_key,
        ),
        # A driver with no value renders as UNAVAILABLE beside its direction, which is exactly
        # what an unassessable timing term should look like: absent, and labeled with why.
        Driver(
            feature="agreement_crest_timing_delta_h",
            value=None if result.timing_divergence_h is None else round(result.timing_divergence_h, 2),
            unit="h",
            direction=_timing_direction(result),
            rank=3,
            prov=model_key,
        ),
    )


async def assess(
    k: Knowledge,
    fp: ForecastPoint,
    *,
    thresholds: ThresholdSet | None = None,
    horizon_h: int = HAZARD_HORIZON_H,
    bands: AgreementBands = BANDS,
) -> AgreementAssessment:
    """Agreement at one forecast point, read at knowledge time T.

    The order matters: the NWM cycle is located *before* either crest is taken, because the
    window both crests are taken over depends on that cycle's coverage. Taking the official crest
    first and the model crest later — over whatever window each happened to have — is finding B.

    Every early return is an honest UNKNOWN with the reason naming the missing input; none of
    them falls back to a comparison built out of something else."""
    lid = fp.lid
    official_key = f"{OFFICIAL_PROV_PREFIX}{lid.lower()}"
    model_key = f"{MODEL_PROV_PREFIX}{lid.lower()}"
    runs: dict[str, ForecastRun] = {}

    official_run = await k.latest_forecast_run(fp.id)  # registry-resolved OFFICIAL products only
    if official_run is None:
        return _unknown(REASON_NO_OFFICIAL_RUN, runs)
    runs[official_key] = official_run

    values = await k.forecast_values(official_run.id)
    flows = [(v.valid_time, v.flow) for v in values]
    if not any(v is not None for _, v in flows):
        return _unknown(REASON_NO_OFFICIAL_FLOW.format(lid=lid), runs)

    model_run, stored = await latest_model_cycle(k, fp.id)
    if model_run is None:
        return _unknown(REASON_NO_MODEL_RUN, runs)
    runs[model_key] = model_run
    if not isinstance(stored, dict):
        return _unknown(REASON_NO_MEMBERS.format(lid=lid), runs)
    if stored.get("schema") != SERIES_SCHEMA:
        # Refusing to read a payload shape this version does not implement is the same rule the
        # parser applies to an unrecognised unit: a half-understood series yields a crest at the
        # wrong time, which is the class of error finding B was.
        return _unknown(REASON_UNREADABLE_SERIES.format(lid=lid, schema=stored.get("schema") or "unlabelled"), runs)

    window = comparison_window(
        as_of=k.as_of,
        issued_at=model_run.issued_at,
        coverage_h=int(stored.get("coverage_h") or horizon_h),
        horizon_h=horizon_h,
    )
    if window.hours < bands.min_comparison_window_h:
        return _unknown(
            REASON_WINDOW_TOO_SHORT.format(
                lid=lid, age=window.cycle_age_h, shared=window.hours, horizon=horizon_h
            ),
            runs,
        )

    official = read_hydrograph("nwrfc-official-flow", clip(flows, window), bands=bands)
    if official is None:
        return _unknown(REASON_NO_OFFICIAL_CREST.format(lid=lid, horizon=horizon_h), runs)
    ensemble = ensemble_from_feature(stored, issued_at=model_run.issued_at, window=window, bands=bands)
    if ensemble is None:
        return _unknown(REASON_NO_MODEL_VALUES.format(lid=lid), runs)

    floor = thresholds.action if thresholds is not None and thresholds.basis == "flow" else None
    result = compare(
        lid=lid,
        official=official,
        ensemble=ensemble,
        window=window,
        thresholds=thresholds,
        floor=floor,
        horizon_h=horizon_h,
        bands=bands,
    )
    return AgreementAssessment(
        state=AgreementState(
            state=result.state,
            reason=result.reason,
            explanation_ref=f"/explanations/{fp.basin_id or fp.id}/agreement",
            prov=tuple(runs),
        ),
        result=result,
        drivers=_drivers(result, official_key=official_key, model_key=model_key),
        runs_by_prov_key=runs,
        model_probability=result.model_probability,
    )


def _unknown(reason: str, runs: dict[str, ForecastRun]) -> AgreementAssessment:
    return AgreementAssessment(
        state=AgreementState(state=AgreementLevel.UNKNOWN, reason=reason, prov=tuple(runs)),
        result=AgreementResult(AgreementLevel.UNKNOWN, reason),
        drivers=(),
        runs_by_prov_key=runs,
        model_probability=None,
    )
