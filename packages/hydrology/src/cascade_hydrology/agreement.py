"""Model agreement v0 — `method:model-agreement@0.1.0` (design §3.2, docs/HYDROLOGY.md §6).

What this surface answers: *does an independent model see the same event the official forecast
sees?* It compares the NWRFC's official river forecast with the NWM v3.1 medium-range ensemble
at the same forecast point, over the same 72-hour hazard window, on the same variable (flow, in
cfs). It answers on three axes — magnitude, timing and, where official **flow** thresholds
exist, category.

The rules that are not negotiable, and are enforced by construction here:

- **Nothing is averaged across sources.** The official crest and the model crest are carried as
  two separate numbers with two separate ProvenanceRefs of two different `source_kind`s. There
  is no consensus value, no blend, no "best estimate" (docs/DATA_DOCTRINE.md §10). Disagreement
  is the information.
- **The model's central value is a member, not a mean.** `C_nwm` is the lower-median *member*
  crest — a hydrograph the model actually produced — so the crest and its timing come from the
  same series. The NWPS-computed `mean` series is stored and displayed as the model hydrograph
  but is never the comparison value and never a member.
- **UNKNOWN is a real answer.** Five distinct preconditions each produce UNKNOWN with a specific
  reason. At CRNW1 the official run carries no usable flow column at all (0 of 40 points; every
  secondary value is the −9999 sentinel), so agreement there is UNKNOWN *correctly* and must
  never regress into a fabricated comparison.
- **Category agreement exists only where official flow thresholds exist** — AUBW1 and WRAW1 of
  the six seed points. At the other four the official categories are defined in stage and ADR-0011
  forbids inventing flow equivalents, so category is reported as not comparable, not as agreement.
- **The bands are an ASSUMPTION, stated as one.** 0.25/0.60 and 6 h/18 h are a first cut carried
  in `BANDS` with that sentence attached; they are not calibrated against outcomes and the exit
  tests check reproducibility and the UNKNOWN paths, never correctness. Calibration is hindcast
  work (ADR-0008).

`AgreementLevel` is a level of *agreement between two forecasts*, never a probability and never
a statement that either forecast is right.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from cascade_contracts import FloodCategory
from cascade_contracts.visualization import AgreementLevel, AgreementState, Driver
from cascade_core.knowledge import Knowledge
from cascade_core.models import ForecastPoint, ForecastRun
from cascade_core.registry import PRODUCT_NWM_MR
from cascade_core.timeutils import parse_iso
from cascade_hydrology.category import ORDER, Measure, ThresholdSet, categorize
from cascade_hydrology.surfaces import HAZARD_HORIZON_H, Crest, forecast_crest

METHOD_ID = "method:model-agreement@0.1.0"
MODEL_LABEL = "nwm-v3.1-medium-range"

#: Read-side copies of the vocabulary `cascade_providers_nwps.reaches_jobs` writes. Hydrology
#: does not import provider packages, so the constants are declared on both sides and pinned
#: together by a test (tests/unit/test_agreement.py::test_feature_vocabulary_matches_the_writer).
FEATURE_CREST_SUMMARY = "nwm_mr_crest_flow_members"
METHOD_MEMBER_CREST = "method:nwm-member-crest@1.0.0"

OFFICIAL_PROV_PREFIX = "nwps-forecast-"
MODEL_PROV_PREFIX = "nwm-mr-"


@dataclass(frozen=True)
class AgreementBands:
    """Method parameters, versioned with the method id — never spelled inline in the logic.

    ASSUMPTION, and it travels with the numbers: these boundaries are a stated first cut for
    western-Washington basins. They are **not calibrated**. Nothing downstream may present an
    agreement level as a likelihood that either forecast verifies.
    """

    high_magnitude: float = 0.25
    high_timing_h: float = 6.0
    moderate_magnitude: float = 0.60
    moderate_timing_h: float = 18.0
    moderate_category_steps: int = 1
    assumption: str = (
        "Agreement bands (|Δ| 0.25/0.60, Δt 6 h/18 h, category 0/1 steps) are an uncalibrated "
        "first cut stated as an assumption; they are not a verified skill measure (ADR-0008)."
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
REASON_NO_MEMBERS = "The stored NWM cycle for {lid} carries no member crests, so no member statistic can be formed."
REASON_NO_OVERLAP = (
    "The official forecast and the NWM cycle do not overlap inside the {horizon}-hour hazard window."
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

#: Caveats rendered into `AgreementState.reason`. A limitation that stays inside a dataclass has
#: not travelled with its number; these are what makes it reach a reader.
CAVEAT_NO_FLOOR = (
    "The divergence is measured against the official crest itself: this point has no official "
    "action FLOW threshold to floor the denominator with, so a small crest turns a small "
    "difference into a large percentage."
)
CAVEAT_DEGENERATE_ENSEMBLE = (
    "All {n:.0f} NWM members crest at the same value inside this window — medium-range members "
    "share one forcing early in the run — so the median member is not the centre of a spread, "
    "and any member fraction here counts one forecast {n:.0f} times rather than {n:.0f} "
    "independent opinions."
)


@dataclass(frozen=True)
class MemberCrest:
    member: str
    value: float  # cfs
    valid_time: datetime


@dataclass(frozen=True)
class ModelEnsembleCrest:
    """What the ingest job stored about one NWM cycle at one point: member crests and the median."""

    issued_at: datetime
    window_h: int
    unit: str
    members: tuple[MemberCrest, ...]
    median_member: MemberCrest | None
    median_rule: str

    @property
    def member_count(self) -> int:
        return len(self.members)


@dataclass(frozen=True)
class AgreementResult:
    """The numbers behind the level. Official and model values never merge into one field."""

    state: AgreementLevel
    reason: str | None
    official_crest: Crest | None = None
    model_crest: MemberCrest | None = None
    magnitude_divergence: float | None = None  # (C_nwm − C_off) / max(C_off, floor), signed
    timing_divergence_h: float | None = None
    official_category: FloodCategory | None = None
    model_category: FloodCategory | None = None
    category_steps: int | None = None
    category_note: str | None = None
    model_probability: dict[str, str | float] | None = None
    member_count: int = 0
    quality: tuple[str, ...] = ()


def _hours(a: datetime, b: datetime) -> float:
    return abs((a - b).total_seconds()) / 3600.0


def official_flow_crest(
    values: list[tuple[datetime, float | None]], *, as_of: datetime, horizon_h: int = HAZARD_HORIZON_H
) -> Crest | None:
    """The official run's crest on the FLOW column, over the same window the hazard surface uses.

    Reusing `surfaces.forecast_crest` is deliberate: if agreement and hazard ever disagreed about
    which window they mean, the platform would be comparing two different events (design §3.2)."""
    return forecast_crest(values, as_of=as_of, horizon_h=horizon_h)


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


def compare(
    *,
    lid: str,
    official: Crest | None,
    ensemble: ModelEnsembleCrest | None,
    thresholds: ThresholdSet | None = None,
    floor: float | None = None,
    horizon_h: int = HAZARD_HORIZON_H,
    bands: AgreementBands = BANDS,
) -> AgreementResult:
    """Compare one official crest with one NWM member ensemble. Pure; every branch is testable.

    `floor` guards the divergence denominator: a ratio taken against a near-zero official crest
    manufactures disagreement out of arithmetic. The official **action** flow is the floor where
    it exists; where it does not, the quality flag `no_divergence_floor` is recorded on the
    result so the limitation travels with the number instead of being lost.
    """
    if official is None:
        return AgreementResult(AgreementLevel.UNKNOWN, REASON_NO_OFFICIAL_CREST.format(lid=lid, horizon=horizon_h))
    if ensemble is None:
        return AgreementResult(AgreementLevel.UNKNOWN, REASON_NO_MODEL_RUN)
    if not ensemble.members or ensemble.median_member is None:
        return AgreementResult(AgreementLevel.UNKNOWN, REASON_NO_MEMBERS.format(lid=lid))

    model = ensemble.median_member
    denominator = max(official.value, floor or 0.0)
    quality: tuple[str, ...] = () if floor is not None else (QUALITY_NO_FLOOR,)
    if len({m.value for m in ensemble.members}) == 1:
        quality += (QUALITY_DEGENERATE_ENSEMBLE,)
    if denominator <= 0:
        return AgreementResult(
            AgreementLevel.UNKNOWN,
            REASON_NON_POSITIVE.format(lid=lid),
            official_crest=official,
            model_crest=model,
            member_count=ensemble.member_count,
            quality=quality,
        )

    delta = (model.value - official.value) / denominator
    delta_t = _hours(model.valid_time, official.valid_time)
    official_category, note = _category_of(official.value, thresholds)
    model_category, _ = _category_of(model.value, thresholds)
    steps = None if note is not None else _steps(official_category, model_category)
    probability = member_exceedance(ensemble.members, thresholds)

    within_high = abs(delta) <= bands.high_magnitude and delta_t <= bands.high_timing_h and steps in (0, None)
    within_moderate = (
        abs(delta) <= bands.moderate_magnitude
        and delta_t <= bands.moderate_timing_h
        and (steps is None or steps <= bands.moderate_category_steps)
    )
    state = AgreementLevel.HIGH if within_high else (AgreementLevel.MODERATE if within_moderate else AgreementLevel.LOW)
    reason = None
    if state is AgreementLevel.LOW:
        magnitude = (
            "at the same magnitude as"
            if delta == 0
            else f"{abs(delta) * 100:.0f}% {'above' if delta > 0 else 'below'}"
        )
        step_note = "" if steps in (0, None) else f", {steps} flood-category step(s) apart"
        reason = (
            f"The NWM median member crests {magnitude} the NWRFC forecast and {delta_t:.0f} h "
            f"apart{step_note}. Both forecasts are shown; neither is corrected by the other."
        )
    return AgreementResult(
        state=state,
        reason=reason,
        official_crest=official,
        model_crest=model,
        magnitude_divergence=delta,
        timing_divergence_h=delta_t,
        official_category=official_category,
        model_category=model_category,
        category_steps=steps,
        category_note=note,
        model_probability=probability,
        member_count=ensemble.member_count,
        quality=quality,
    )


def ensemble_from_feature(values_json: dict | None, *, issued_at: datetime | None) -> ModelEnsembleCrest | None:
    """Rebuild the member ladder from a stored `derived_feature.values_json` row."""
    if not isinstance(values_json, dict) or issued_at is None:
        return None
    raw = values_json.get("members")
    if not isinstance(raw, dict) or not raw:
        return None
    members = tuple(
        MemberCrest(member=name, value=float(v["crest"]), valid_time=parse_iso(str(v["valid_time"])))
        for name, v in sorted(raw.items())
        if isinstance(v, dict) and v.get("crest") is not None
    )
    if not members:
        return None
    median_name = values_json.get("median_member")
    median = next((m for m in members if m.member == median_name), None)
    rule = str(values_json.get("median_rule") or "unknown")
    if median is None and rule == "lower_median_member":
        # The named member is missing but the ladder and the rule are both stored, so the median
        # is recoverable deterministically. Any OTHER rule is left as None on purpose: this
        # module will not re-derive a central value under a rule it does not implement.
        ordered = sorted(members, key=lambda c: (c.value, c.valid_time))
        median = ordered[(len(ordered) - 1) // 2]
    return ModelEnsembleCrest(
        issued_at=issued_at,
        window_h=int(values_json.get("window_h") or HAZARD_HORIZON_H),
        unit=str(values_json.get("unit") or "cfs"),
        members=members,
        median_member=median,
        median_rule=rule,
    )


async def latest_model_ensemble(k: Knowledge, fp_id: str) -> tuple[ForecastRun | None, ModelEnsembleCrest | None]:
    """The latest NWM cycle known at T at this point, with the crest summary written beside it.

    The run is read **by product id**: `forecast_run` holds the official forecast too, and asking
    for "the latest run" without saying which product is the defect this whole surface depends on
    not existing (design §3.4 defect 1)."""
    run = await k.latest_forecast_run(fp_id, product_ids=frozenset({PRODUCT_NWM_MR}))
    if run is None:
        return None, None
    rows = await k.derived_features(
        FEATURE_CREST_SUMMARY,
        fp_id,
        method_id=METHOD_MEMBER_CREST,
        valid_from=run.issued_at,
        valid_until=run.issued_at + timedelta(hours=HAZARD_HORIZON_H * 2),
    )
    same_cycle = [r for r in rows if r.issued_at == run.issued_at]
    if not same_cycle:
        return run, None
    return run, ensemble_from_feature(same_cycle[-1].values_json, issued_at=run.issued_at)


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


def _drivers(result: AgreementResult, *, official_key: str, model_key: str) -> tuple[Driver, ...]:
    if result.official_crest is None or result.model_crest is None:
        return ()
    delta = result.magnitude_divergence or 0.0
    later = (result.model_crest.valid_time - result.official_crest.valid_time).total_seconds()
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
        Driver(
            feature="agreement_crest_timing_delta_h",
            value=round(result.timing_divergence_h or 0.0, 2),
            unit="h",
            direction="model_later" if later > 0 else ("model_earlier" if later < 0 else "model_same_time"),
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
) -> AgreementAssessment:
    """Agreement at one forecast point, read at knowledge time T.

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
    official = official_flow_crest(flows, as_of=k.as_of, horizon_h=horizon_h)
    if official is None:
        return _unknown(REASON_NO_OFFICIAL_CREST.format(lid=lid, horizon=horizon_h), runs)

    model_run, ensemble = await latest_model_ensemble(k, fp.id)
    if model_run is None:
        return _unknown(REASON_NO_MODEL_RUN, runs)
    runs[model_key] = model_run
    if ensemble is None:
        return _unknown(REASON_NO_MEMBERS.format(lid=lid), runs)
    # The stored member crests cover (cycle, cycle + horizon]. If that window has already ended
    # before the hazard window opens, the two forecasts describe different events and the only
    # honest answer is UNKNOWN — not a comparison of a stale crest with a current one.
    if model_run.issued_at + timedelta(hours=horizon_h) <= k.as_of - timedelta(hours=6):
        return _unknown(REASON_NO_OVERLAP.format(horizon=horizon_h), runs)

    floor = thresholds.action if thresholds is not None and thresholds.basis == "flow" else None
    result = compare(
        lid=lid, official=official, ensemble=ensemble, thresholds=thresholds, floor=floor, horizon_h=horizon_h
    )
    # The category caveat rides with the level even when the level is HIGH: "high agreement on
    # magnitude and timing" must not read as "high agreement, full stop", when category could
    # not be compared at all (design §7, must-stay-UNKNOWN table).
    reason = " ".join(x for x in (result.reason, result.category_note, *_caveats(result)) if x) or None
    return AgreementAssessment(
        state=AgreementState(
            state=result.state,
            reason=reason,
            explanation_ref=f"/explanations/{fp.basin_id or fp.id}/agreement",
            prov=tuple(runs),
        ),
        result=result,
        drivers=_drivers(result, official_key=official_key, model_key=model_key),
        runs_by_prov_key=runs,
        model_probability=result.model_probability,
    )


def _caveats(result: AgreementResult) -> tuple[str, ...]:
    """The quality flags on a computed comparison, as sentences a reader can act on.

    `AgreementResult.quality` was previously computed and then dropped at the contract
    boundary, which is the same as not recording it: design §3.2 requires the limitation to
    travel with the number."""
    out: list[str] = []
    if QUALITY_NO_FLOOR in result.quality:
        out.append(CAVEAT_NO_FLOOR)
    if QUALITY_DEGENERATE_ENSEMBLE in result.quality:
        out.append(CAVEAT_DEGENERATE_ENSEMBLE.format(n=float(result.member_count)))
    return tuple(out)


def _unknown(reason: str, runs: dict[str, ForecastRun]) -> AgreementAssessment:
    return AgreementAssessment(
        state=AgreementState(state=AgreementLevel.UNKNOWN, reason=reason, prov=tuple(runs)),
        result=AgreementResult(AgreementLevel.UNKNOWN, reason),
        drivers=(),
        runs_by_prov_key=runs,
        model_probability=None,
    )
