"""The hindcast harness — replay a named event at a named clock, under a named method.

Brief §21. It exists so that "did the corrected method see it earlier?" is answered by
*running the shipped code at a past knowledge time* rather than by reasoning about it, and so
that the answer for the next event costs a configuration entry instead of a second script.

What it is a structure over
---------------------------
Seven things, and it holds exactly these seven because they are what a replay needs to be
reproducible and honest — no more:

1. the **event** (:class:`HindcastEvent`) — which basins, which evaluation times, and the
   observed eventual outcome, recorded once and never consulted while a signal is computed;
2. the **evaluation time** — one clock, carried explicitly (:class:`Clocks`);
3. the **method version** (:class:`MethodArm`) — both arms of an A/B are *the shipped code at a
   version*, never a reconstruction of a version;
4. the **reference distribution** (:class:`ReferenceDefinition`) — what the level is a rank in,
   including whether the event lies inside its own reference;
5. the **knowledge cutoff and its mode** (:class:`ReplayMode`, :class:`Projection`) — see the
   next section, which is the part of this module that matters most;
6. the **derived signals** — the compact :class:`Evaluation` record, which stores *what the
   surfaces said*, never a copy of the rows they read;
7. the **observed eventual outcome** (:class:`BasinOutcome`) — held beside the run, not inside
   it, so no rule can be fitted to it without that being visible in the code.

The two knowledge times, and why they must never be confused (brief §20)
------------------------------------------------------------------------
`DATA_DOCTRINE §11` / `ADR-0010`: a replay at T may read only rows with `available_at <= T`.
Our December-2025 rows were backfilled in 2026, so their `available_at` is 2026 and a strict
replay at 2025-12-06 **correctly returns nothing at all**. That is not a bug to be worked
around; it is the doctrine reporting the truth, which is that this platform did not exist during
Event Zero.

So a hindcast has to answer a *different, weaker, still useful* question — and has to say out
loud that it is the weaker one:

- :attr:`ReplayMode.KNOWLEDGE_TIME` — "what did **this deployed system** know at T?" Reads the
  archive exactly as production does. For a backfilled event the answer is UNKNOWN everywhere,
  and the harness reports that rather than hiding it.
- :attr:`ReplayMode.RETROSPECTIVE` — "what is **reconstructable at T from evidence that
  existed at T**?" Rows are selected by their own evidence clock (`valid_time`, `issued_at`,
  `effective_from`) instead of by the clock at which *we* fetched them. This is what the Event
  Zero product mode does, and it is the only mode in which a December 2025 A/B has content.

Every :class:`Evaluation` carries its :attr:`Evaluation.mode`, and every RETROSPECTIVE run
carries the :class:`Projection` that produced it — the per-row-family rule that decided when a
row became visible, and how optimistic that rule is. A retrospective result presented as a
knowledge-time result would be a claim that the platform issued a warning it never issued;
:func:`Projection.disclosure` is the sentence that must travel with any published figure.

What it deliberately is not
---------------------------
Not a framework. There is no plugin registry, no scheduler, no storage layer, no generalised
metric algebra. Adding an event is a :class:`HindcastEvent` literal; adding a comparison is a
:class:`MethodArm`; adding a criterion is an :class:`EscalationRule`. If a third event needs a
shape this does not have, widen it then.

It also computes **no score**. There is no composite, no weighting between level and velocity,
and no probability anywhere in this module — the prohibitions of `HYDROLOGY.md` §7 and the
milestone brief hold in the evaluation harness exactly as they hold in the surface, because a
harness that scored what the surface refuses to score would smuggle the forbidden number in
through the back door of "just for measurement".

The one rule that keeps a lead-time claim honest
------------------------------------------------
:class:`EscalationRule` carries :attr:`EscalationRule.fixed_independently_of_outcome` and
:attr:`EscalationRule.constant_provenance`, and neither has a default. A rule whose constant was
chosen after looking at Event Zero is not evidence about Event Zero, and
:func:`compare_arms` refuses to label such a comparison a lead time — it reports the difference
under a different name and says why. That is the whole guard, and it is deliberately a
data-carrying one rather than a convention: a future author adding a rule must answer the
question in the constructor.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any

from cascade_contracts import FloodCategory
from cascade_contracts.visualization import SurfaceLevel
from cascade_core.knowledge import Knowledge
from cascade_core.models import Basin, ForecastPoint, SourceProduct
from cascade_hydrology import agreement as agreement_mod
from cascade_hydrology import assemble, forcing, susceptibility
from cascade_hydrology.trend import (
    UNKNOWN,
    TidalClass,
    TrendEstimate,
    estimate_trend,
    rate_of_rise,
)

# =============================================================================================
# 1. The knowledge cutoff and its mode (brief §20)
# =============================================================================================


class ReplayMode(str, Enum):
    """Which of the two knowledge questions a replay is answering. Never a display detail.

    The distinction is the difference between "we would have shown this" and "this was derivable
    from evidence that existed"; the second does not imply the first, and only the first is a
    claim about the platform.
    """

    #: `available_at <= T` on unmodified archive rows: what the deployed system knew at T.
    KNOWLEDGE_TIME = "KNOWLEDGE_TIME"
    #: Rows made visible by their own evidence clock: what was reconstructable at T.
    RETROSPECTIVE = "RETROSPECTIVE"


@dataclass(frozen=True)
class ProjectionRule:
    """How ONE family of rows was made visible to a retrospective replay, and at what cost.

    ``optimism`` is the part a reader needs and a summary would drop: the amount by which this
    rule credits the replay with knowledge slightly earlier than any real retrieval could have
    delivered it. Stating it per family is the only way a reader can tell a rule that is
    optimistic by minutes (a gauge reading) from one that is optimistic by months (a reference
    distribution built after the event).
    """

    row_family: str  # e.g. "observation", "derived_feature:streamflow_doy_climatology"
    visibility_clock: str  # the column the replay selects on instead of available_at
    rule: str  # the transformation, stated as an equation
    optimism: str  # how much earlier than reality this makes the row visible, and why
    anachronism: bool = False  # True when the row could NOT have existed at T in any form


@dataclass(frozen=True)
class Projection:
    """The complete account of how a RETROSPECTIVE replay database differs from the archive.

    Carried into every output. :meth:`disclosure` is the sentence that must accompany any number
    this run produces; :attr:`anachronistic_families` is the shorter, sharper list of the rows
    that did not merely arrive early but could not have existed at all.
    """

    name: str
    mode: ReplayMode
    rules: tuple[ProjectionRule, ...] = ()
    note: str = ""

    @property
    def anachronistic_families(self) -> tuple[str, ...]:
        return tuple(r.row_family for r in self.rules if r.anachronism)

    def disclosure(self) -> str:
        if self.mode is ReplayMode.KNOWLEDGE_TIME:
            return (
                "KNOWLEDGE_TIME replay: rows were read exactly as the deployed system reads them "
                "(available_at <= as_of). Anything UNKNOWN here was genuinely unknown to this "
                "platform at that instant."
            )
        stale = self.anachronistic_families
        tail = (
            ""
            if not stale
            else (
                " Of these, "
                + ", ".join(stale)
                + " could not have existed at the evaluation time in any form and are a stated "
                "anachronism, not an early arrival."
            )
        )
        return (
            "RETROSPECTIVE replay: rows were made visible by their own evidence clock rather "
            "than by the time this platform fetched them, so these figures say what was "
            "RECONSTRUCTABLE from evidence that existed then — NOT what this deployed system "
            "knew or would have shown. This platform did not exist during the event." + tail
        )


@dataclass(frozen=True)
class Clocks:
    """The five instants a replayed number sits between, kept distinct (`CLAUDE.md`).

    Collapsing any two of these is how a hindcast starts leaking the future, so they are one
    object with five named fields rather than a `datetime` passed around and reinterpreted.
    """

    as_of: datetime  # the knowledge time the surfaces were asked at
    cursor: date | None = None  # the event cursor: which day of the event this is
    valid_at: datetime | None = None  # when the observation the answer rests on was true
    issued_at: datetime | None = None  # when its issuer published it, where that differs
    available_at: datetime | None = None  # when THIS platform could first have read it
    system_now: datetime | None = None  # wall clock of the replay process itself

    def as_dict(self) -> dict[str, str | None]:
        def iso(v: datetime | date | None) -> str | None:
            return None if v is None else v.isoformat()

        return {
            "as_of": iso(self.as_of),
            "event_cursor": iso(self.cursor),
            "valid_at": iso(self.valid_at),
            "issued_at": iso(self.issued_at),
            "available_at": iso(self.available_at),
            "system_now": iso(self.system_now),
        }


# =============================================================================================
# 2. The event and its outcome
# =============================================================================================


@dataclass(frozen=True)
class BasinOutcome:
    """What actually happened, per basin. Held so it can be REPORTED, never so it can be fitted.

    Nothing in :func:`evaluate` reads this object. It is attached to the run afterwards, which
    is what makes it safe to put an outcome in the same file as an escalation rule.
    """

    basin_id: str
    crest_valid_time: datetime | None = None
    crest_value: float | None = None
    crest_unit: str | None = None
    category_reached: FloodCategory | str | None = None
    record_status: str | None = None
    source: str = ""  # where this outcome was read, e.g. "docs/EVENT_ZERO.md §3"

    def as_dict(self) -> dict[str, Any]:
        return {
            "basin_id": self.basin_id,
            "crest_valid_time": None if self.crest_valid_time is None else self.crest_valid_time.isoformat(),
            "crest_value": self.crest_value,
            "crest_unit": self.crest_unit,
            "category_reached": _enum(self.category_reached),
            "record_status": self.record_status,
            "source": self.source,
        }


@dataclass(frozen=True)
class HindcastEvent:
    """One replayable event: which basins, which clocks, and what happened.

    ``control_times`` is not decoration and not an afterthought — it is half of the governing
    question. "Did it reveal deterioration earlier" is only half of "…while remaining quiet when
    no meaningful deterioration existed", and an event with no quiet window cannot answer the
    second half. A :class:`HindcastEvent` with an empty ``control_times`` is legal and
    :func:`compare_arms` says so in its output rather than silently reporting half an answer.
    """

    id: str
    label: str
    basin_ids: tuple[str, ...]
    evaluation_times: tuple[datetime, ...]
    control_times: tuple[datetime, ...] = ()
    outcomes: tuple[BasinOutcome, ...] = ()
    source: str = ""

    def outcome(self, basin_id: str) -> BasinOutcome | None:
        return next((o for o in self.outcomes if o.basin_id == basin_id), None)

    def all_times(self) -> tuple[tuple[datetime, bool], ...]:
        """Every evaluation instant, tagged with whether it belongs to the control window."""
        return tuple(
            sorted(
                [(t, False) for t in self.evaluation_times] + [(t, True) for t in self.control_times],
                key=lambda p: p[0],
            )
        )


# =============================================================================================
# 3. The method arms
# =============================================================================================


@dataclass(frozen=True)
class MethodArm:
    """One side of an A/B: a version of the shipped code, addressed by version, not copied.

    ``susceptibility_version`` selects between `method:susceptibility-index@0.1.0` (what shipped
    until 2026-08-26) and `@0.2.0`. ``trend_estimator`` selects between the preserved endpoint
    difference `method:rate-of-rise@1.0.0` and the shipped repeated median `@2.0.0`. Both live
    in the method modules and both are reached by argument, so an arm cannot drift away from the
    code it claims to be.
    """

    id: str
    label: str
    susceptibility_version: str
    trend_method_id: str  # method:rate-of-rise@1.0.0 | @2.0.0
    #: True for the arm whose trend is `rate_of_rise` — the endpoint difference kept callable
    #: precisely so the comparison runs against the deployed code and not a reconstruction.
    trend_is_endpoint_difference: bool = False


#: The two arms of the Tier 0 A/B, named once so a script cannot spell a version differently
#: from the report.
ARM_OLD = MethodArm(
    id="old",
    label="as shipped until 2026-08-26",
    susceptibility_version="0.1.0",
    trend_method_id="method:rate-of-rise@1.0.0",
    trend_is_endpoint_difference=True,
)
ARM_NEW = MethodArm(
    id="new",
    label="Tier 0 corrected",
    susceptibility_version=susceptibility.SHIPPED_VERSION,
    trend_method_id="method:rate-of-rise@2.0.0",
)


# =============================================================================================
# 4. The reference distribution
# =============================================================================================


@dataclass(frozen=True)
class ReferenceDefinition:
    """What the level statement is a rank IN, said completely enough to be checked.

    ``contains_event`` is the field that stops a hindcast quietly grading itself: a ladder built
    from a record that includes the event ranks that event against a distribution it helped
    make. Register X8 claim D says five of six seeded gauges carry approved WY2026 data inside
    the ranking window, so for Event Zero this is `True` unless the reference was deliberately
    truncated — and the harness reports which.
    """

    method_id: str
    doy_key: str | None
    window_days: int | None
    n: int | None
    independent_years: int | None
    period_start: int | None
    period_end: int | None
    contains_event: bool | None = None
    truncated_at: date | None = None  # set when the record was cut before the event on purpose

    def as_dict(self) -> dict[str, Any]:
        return {
            "method_id": self.method_id,
            "doy_key": self.doy_key,
            "window_days": self.window_days,
            "n": self.n,
            "independent_years": self.independent_years,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "contains_event": self.contains_event,
            "truncated_at": None if self.truncated_at is None else self.truncated_at.isoformat(),
        }


# =============================================================================================
# 5. The compact evaluation record
# =============================================================================================
#
# COMPACT, deliberately (brief §21): what the surfaces SAID, never the rows they read. A
# 62 KiB record-context blob and 36,000 daily means stay in the database; what lands here is the
# handful of numbers a comparison needs, so a full six-basin replay is kilobytes and a
# regression fixture is a file a human can read.


@dataclass(frozen=True)
class LevelReading:
    """Where the river is, as the arm under test states it."""

    percentile: float | None
    band: str | None
    clamped: bool
    # @0.2.0 only — absent (None) under @0.1.0, which published no tail statement at all
    rank: int | None = None
    rank_of: int | None = None
    rank_reason: str | None = None
    exceeds_record: bool | None = None
    previous_max: float | None = None
    multiple: float | None = None
    reference_flow: float | None = None
    boundary: str | None = None
    bands_within_sampling_error: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "percentile": self.percentile,
            "band": self.band,
            "percentile_clamped": self.clamped,
            "rank": self.rank,
            "rank_of": self.rank_of,
            "rank_reason": self.rank_reason,
            "exceeds_record": self.exceeds_record,
            "previous_max": self.previous_max,
            "seasonal_multiple": self.multiple,
            "reference_flow": self.reference_flow,
            "boundary": self.boundary,
            "bands_within_sampling_error": list(self.bands_within_sampling_error),
        }


@dataclass(frozen=True)
class VelocityReading:
    """How fast it is moving, over one named window, in BOTH representations.

    ``percentile_delta`` is the change in the *shipped percentile* over the same window. It is a
    **diagnostic and was never published by `@0.1.0`** — the deployed surface had no velocity at
    all. It is computed here because it is the quantity `tier0-measured-basis-2026-08-26.md` §3
    measured going to `+0` through the crest, and a comparison that omitted it would be arguing
    against a straw man rather than against the thing that was measured.
    """

    window_h: int
    growth: float | None  # multiplicative, @0.2.0
    growth_direction: str | None
    growth_rank: int | None
    growth_rank_of: int | None
    growth_rank_reason: str | None
    growth_reason: str | None
    span_h: float | None
    percentile_delta: float | None  # diagnostic, both arms
    percentile_delta_reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "window_h": self.window_h,
            "growth": self.growth,
            "growth_direction": self.growth_direction,
            "growth_rank": self.growth_rank,
            "growth_rank_of": self.growth_rank_of,
            "growth_rank_reason": self.growth_rank_reason,
            "growth_reason": self.growth_reason,
            "span_h": self.span_h,
            "percentile_delta_diagnostic": self.percentile_delta,
            "percentile_delta_reason": self.percentile_delta_reason,
        }


@dataclass(frozen=True)
class TrendReading:
    """The rate of rise the arm's estimator reports, with its refusal ladder intact."""

    method_id: str
    estimator: str | None
    basis: str | None
    window_h: float | None
    slope: float | None
    slope_unit: str | None
    direction: str
    n: int | None
    span_h: float | None
    quality: str | None
    refusal_reason: str | None
    slope_q25: float | None = None
    slope_q75: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "method_id": self.method_id,
            "estimator": self.estimator,
            "basis": self.basis,
            "window_h": self.window_h,
            "slope": self.slope,
            "slope_unit": self.slope_unit,
            "direction": self.direction,
            "n": self.n,
            "span_h": self.span_h,
            "quality": self.quality,
            "refusal_reason": self.refusal_reason,
            "pair_slope_q25": self.slope_q25,
            "pair_slope_q75": self.slope_q75,
        }


@dataclass(frozen=True)
class Evaluation:
    """ONE basin, at ONE knowledge time, under ONE arm. The unit of everything below."""

    event_id: str
    arm_id: str
    mode: ReplayMode
    basin_id: str
    basin_name: str
    gauge_id: str | None
    gauge_site: str | None
    is_control: bool
    clocks: Clocks

    # the level
    flow: float | None
    flow_unit: str | None
    daily_mean_day: date | None
    level: LevelReading
    surface_state: str
    surface_reason: str | None
    confidence: str | None

    # the velocity
    velocity: tuple[VelocityReading, ...]

    # the point surfaces
    trend: TrendReading
    observed_category: str | None
    observed_category_reason: str | None
    threshold_basis: str | None
    headroom_to: str | None
    headroom_value: float | None
    headroom_unit: str | None
    headroom_time_to_threshold_h: float | None
    headroom_reason: str | None
    official_forecast_category: str | None
    official_forecast_crest: float | None
    official_forecast_issued_at: datetime | None
    forcing_state: str | None
    forcing_reason: str | None
    agreement_state: str | None
    agreement_reason: str | None

    # the honesty fields
    reference: ReferenceDefinition | None
    quality_flags: tuple[str, ...]
    method_ids: tuple[str, ...]
    raw_artifact_ids: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "arm_id": self.arm_id,
            "mode": self.mode.value,
            "basin_id": self.basin_id,
            "basin_name": self.basin_name,
            "gauge_id": self.gauge_id,
            "gauge_site": self.gauge_site,
            "is_control": self.is_control,
            "clocks": self.clocks.as_dict(),
            "flow": self.flow,
            "flow_unit": self.flow_unit,
            "daily_mean_day": None if self.daily_mean_day is None else self.daily_mean_day.isoformat(),
            "level": self.level.as_dict(),
            "surface_state": self.surface_state,
            "surface_reason": self.surface_reason,
            "confidence": self.confidence,
            "velocity": [v.as_dict() for v in self.velocity],
            "trend": self.trend.as_dict(),
            "observed_category": self.observed_category,
            "observed_category_reason": self.observed_category_reason,
            "threshold_basis": self.threshold_basis,
            "headroom": {
                "to_category": self.headroom_to,
                "value": self.headroom_value,
                "unit": self.headroom_unit,
                "time_to_threshold_h": self.headroom_time_to_threshold_h,
                "reason": self.headroom_reason,
            },
            "official_forecast": {
                "category": self.official_forecast_category,
                "crest": self.official_forecast_crest,
                "issued_at": None
                if self.official_forecast_issued_at is None
                else self.official_forecast_issued_at.isoformat(),
            },
            "forcing": {"state": self.forcing_state, "reason": self.forcing_reason},
            "agreement": {"state": self.agreement_state, "reason": self.agreement_reason},
            "reference": None if self.reference is None else self.reference.as_dict(),
            "quality_flags": list(self.quality_flags),
            "method_ids": list(self.method_ids),
            "raw_artifact_ids": list(self.raw_artifact_ids),
        }

    # -- convenience accessors used by the escalation rules; None-safe on purpose ---------

    def window(self, window_h: int) -> VelocityReading | None:
        return next((v for v in self.velocity if v.window_h == window_h), None)

    @property
    def band_order(self) -> int | None:
        """The band's position in `susceptibility.BAND_ORDER`, or None when UNKNOWN."""
        try:
            return susceptibility.BAND_ORDER.index(SurfaceLevel(self.level.band))
        except (ValueError, TypeError):
            return None


def _enum(value: Any) -> Any:
    return value.value if isinstance(value, Enum) else value


def _dt(value: str | None) -> datetime | None:
    return None if value is None else datetime.fromisoformat(value)


def evaluation_from_dict(doc: dict[str, Any]) -> Evaluation:
    """Rebuild one :class:`Evaluation` from its serialised form.

    This is what makes a stored run document a first-class input rather than a report artefact:
    the escalation rules and :func:`compare_arms` can be re-run months later, against a run
    nobody can reproduce because the scratch database is gone, and a regression test can check
    that today's rules still produce yesterday's verdicts with no database and no network.

    Only the fields the rules and the comparison read are rehydrated as typed values; the rest
    stay exactly as they were written, because a lossy round trip that silently dropped a
    provenance field would be worse than not having one at all.
    """
    clocks = doc["clocks"]
    level = doc["level"]
    trend = doc["trend"]
    head = doc.get("headroom") or {}
    forecast = doc.get("official_forecast") or {}
    reference = doc.get("reference")
    return Evaluation(
        event_id=doc["event_id"],
        arm_id=doc["arm_id"],
        mode=ReplayMode(doc["mode"]),
        basin_id=doc["basin_id"],
        basin_name=doc["basin_name"],
        gauge_id=doc.get("gauge_id"),
        gauge_site=doc.get("gauge_site"),
        is_control=bool(doc["is_control"]),
        clocks=Clocks(
            as_of=datetime.fromisoformat(clocks["as_of"]),
            cursor=None if clocks.get("event_cursor") is None else date.fromisoformat(clocks["event_cursor"]),
            valid_at=_dt(clocks.get("valid_at")),
            issued_at=_dt(clocks.get("issued_at")),
            available_at=_dt(clocks.get("available_at")),
            system_now=_dt(clocks.get("system_now")),
        ),
        flow=doc.get("flow"),
        flow_unit=doc.get("flow_unit"),
        daily_mean_day=None if doc.get("daily_mean_day") is None else date.fromisoformat(doc["daily_mean_day"]),
        level=LevelReading(
            percentile=level.get("percentile"),
            band=level.get("band"),
            clamped=bool(level.get("percentile_clamped")),
            rank=level.get("rank"),
            rank_of=level.get("rank_of"),
            rank_reason=level.get("rank_reason"),
            exceeds_record=level.get("exceeds_record"),
            previous_max=level.get("previous_max"),
            multiple=level.get("seasonal_multiple"),
            reference_flow=level.get("reference_flow"),
            boundary=level.get("boundary"),
            bands_within_sampling_error=tuple(level.get("bands_within_sampling_error") or ()),
        ),
        surface_state=doc["surface_state"],
        surface_reason=doc.get("surface_reason"),
        confidence=doc.get("confidence"),
        velocity=tuple(
            VelocityReading(
                window_h=v["window_h"],
                growth=v.get("growth"),
                growth_direction=v.get("growth_direction"),
                growth_rank=v.get("growth_rank"),
                growth_rank_of=v.get("growth_rank_of"),
                growth_rank_reason=v.get("growth_rank_reason"),
                growth_reason=v.get("growth_reason"),
                span_h=v.get("span_h"),
                percentile_delta=v.get("percentile_delta_diagnostic"),
                percentile_delta_reason=v.get("percentile_delta_reason"),
            )
            for v in doc.get("velocity") or ()
        ),
        trend=TrendReading(
            method_id=trend["method_id"],
            estimator=trend.get("estimator"),
            basis=trend.get("basis"),
            window_h=trend.get("window_h"),
            slope=trend.get("slope"),
            slope_unit=trend.get("slope_unit"),
            direction=trend["direction"],
            n=trend.get("n"),
            span_h=trend.get("span_h"),
            quality=trend.get("quality"),
            refusal_reason=trend.get("refusal_reason"),
            slope_q25=trend.get("pair_slope_q25"),
            slope_q75=trend.get("pair_slope_q75"),
        ),
        observed_category=doc.get("observed_category"),
        observed_category_reason=doc.get("observed_category_reason"),
        threshold_basis=doc.get("threshold_basis"),
        headroom_to=head.get("to_category"),
        headroom_value=head.get("value"),
        headroom_unit=head.get("unit"),
        headroom_time_to_threshold_h=head.get("time_to_threshold_h"),
        headroom_reason=head.get("reason"),
        official_forecast_category=forecast.get("category"),
        official_forecast_crest=forecast.get("crest"),
        official_forecast_issued_at=_dt(forecast.get("issued_at")),
        forcing_state=(doc.get("forcing") or {}).get("state"),
        forcing_reason=(doc.get("forcing") or {}).get("reason"),
        agreement_state=(doc.get("agreement") or {}).get("state"),
        agreement_reason=(doc.get("agreement") or {}).get("reason"),
        reference=None
        if reference is None
        else ReferenceDefinition(
            method_id=reference["method_id"],
            doy_key=reference.get("doy_key"),
            window_days=reference.get("window_days"),
            n=reference.get("n"),
            independent_years=reference.get("independent_years"),
            period_start=reference.get("period_start"),
            period_end=reference.get("period_end"),
            contains_event=reference.get("contains_event"),
            truncated_at=None
            if reference.get("truncated_at") is None
            else date.fromisoformat(reference["truncated_at"]),
        ),
        quality_flags=tuple(doc.get("quality_flags") or ()),
        method_ids=tuple(doc.get("method_ids") or ()),
        raw_artifact_ids=tuple(doc.get("raw_artifact_ids") or ()),
    )


def evaluations_from_document(doc: dict[str, Any]) -> list[Evaluation]:
    """Every evaluation in a stored run document, ready to be re-ruled."""
    return [evaluation_from_dict(e) for e in doc.get("evaluations") or ()]


# =============================================================================================
# 6. Running the replay
# =============================================================================================


async def evaluate(
    k: Knowledge,
    *,
    event: HindcastEvent,
    arm: MethodArm,
    basin: Basin,
    products: dict[str, SourceProduct],
    mode: ReplayMode,
    cursor: date | None = None,
    is_control: bool = False,
    outlet: ForecastPoint | None = None,
    tidal_class: TidalClass | None = None,
    system_now: datetime | None = None,
    reference_contains_event: bool | None = None,
    reference_truncated_at: date | None = None,
) -> Evaluation:
    """Ask every surface for one basin at ``k.as_of``, under ``arm``, and compact the answer.

    Business logic is **called, never reimplemented**: :func:`susceptibility.assess` with the
    arm's version, :func:`assemble.assess_point` for the observed category, the headroom and the
    official forecast, :func:`agreement.assess` and :func:`forcing.assess` for the remaining two
    surfaces. The only thing computed here is the *old* trend, because the deployed endpoint
    difference is no longer on any read path — :func:`trend.rate_of_rise` is called directly on
    the same window `assess_point` hands its estimator, so the two arms differ in the estimator
    and in nothing else.
    """
    sus = await susceptibility.assess(k, basin, products, version=arm.susceptibility_version)
    surface = sus.surface
    state = sus.hydrologic_state
    gauge_id = basin.susceptibility_gauge_id
    station = await k.station(gauge_id) if gauge_id else None
    site = station.external_id if station else gauge_id

    # --- the level, in whichever vocabulary this arm publishes -------------------------------
    percentile = None if surface.value is None else surface.value.value
    level = LevelReading(
        percentile=percentile,
        band=_enum(surface.state),
        clamped=bool(state.percentile_clamped) if state is not None else False,
        rank=None if state is None or state.rank is None else state.rank.rank,
        rank_of=None if state is None or state.rank is None else state.rank.of,
        rank_reason=None if state is None or state.rank is None else state.rank.reason,
        exceeds_record=None if state is None or state.rank is None else state.rank.exceeds_record,
        previous_max=(
            None
            if state is None or state.rank is None or state.rank.previous_max is None
            else state.rank.previous_max.value
        ),
        multiple=None if state is None or state.multiple is None else state.multiple.multiple,
        reference_flow=(
            None if state is None or state.multiple is None else state.multiple.reference.value
        ),
        boundary=None if state is None else _enum(state.boundary),
        bands_within_sampling_error=(
            () if state is None else tuple(_enum(b) for b in state.bands_within_sampling_error)
        ),
    )

    # --- the velocity, in both representations ----------------------------------------------
    percentile_history = await _percentile_history(k, gauge_id) if gauge_id else []
    # The percentile diagnostic is anchored on the SAME instant `susceptibility._state_changes`
    # anchors the published growth on — the latest ranked daily mean's valid time, not `as_of` —
    # so the two never refuse on different days and a difference between them can only come from
    # the representation, which is the thing under test.
    anchor = percentile_history[-1][0] if percentile_history else None
    valid_at = anchor
    velocity: list[VelocityReading] = []
    for window_h in susceptibility.STATE_CHANGE_WINDOWS_H:
        change = next((c for c in sus.state_changes if c.window_h == window_h), None)
        delta, delta_reason = _percentile_delta(percentile_history, anchor=anchor, window_h=window_h)
        velocity.append(
            VelocityReading(
                window_h=window_h,
                growth=None if change is None else change.growth,
                growth_direction=None if change is None else change.direction,
                growth_rank=None if change is None else change.rank,
                growth_rank_of=None if change is None else change.rank_of,
                growth_rank_reason=None if change is None else change.rank_reason,
                growth_reason=None if change is None else change.reason,
                span_h=None if change is None else change.span_h,
                percentile_delta=delta,
                percentile_delta_reason=delta_reason,
            )
        )

    # --- the point surfaces ------------------------------------------------------------------
    point = None if outlet is None else await assemble.assess_point(k, outlet, basin, products)
    trend = await _trend_for_arm(k, arm=arm, outlet=outlet, point=point, tidal_class=tidal_class)
    ag_state = ag_reason = None
    if outlet is not None and point is not None:
        ag = await agreement_mod.assess(k, outlet, thresholds=point.thresholds)
        ag_state, ag_reason = _enum(ag.state.state), ag.state.reason
    frc = await forcing.assess(k, basin, products)

    item = None if point is None else point.item
    headroom = None if item is None else item.headroom
    official = None if item is None else item.official_forecast
    thresholds = None if item is None else item.thresholds

    # --- honesty ------------------------------------------------------------------------------
    ref = None
    if state is not None and state.reference is not None:
        r = state.reference
        ref = ReferenceDefinition(
            method_id=r.method_id,
            doy_key=r.doy_key,
            window_days=r.window_days,
            n=r.n,
            independent_years=r.independent_years,
            period_start=r.period_start,
            period_end=r.period_end,
            contains_event=reference_contains_event,
            truncated_at=reference_truncated_at,
        )
    refs = sus.refs
    prov = refs.get(surface.prov)
    quality = tuple(prov.quality) if prov is not None else ()
    method_ids = tuple(
        dict.fromkeys(
            [m for m in (r.method_id for r in refs.values()) if m]
            + [trend.method_id, susceptibility.PERCENTILE_ROW_METHOD_ID]
        )
    )
    artifacts = tuple(dict.fromkeys(r.raw_artifact_id for r in refs.values() if r.raw_artifact_id))

    return Evaluation(
        event_id=event.id,
        arm_id=arm.id,
        mode=mode,
        basin_id=basin.id,
        basin_name=basin.name,
        gauge_id=gauge_id,
        gauge_site=site,
        is_control=is_control,
        clocks=Clocks(
            as_of=k.as_of,
            cursor=cursor,
            valid_at=valid_at,
            issued_at=None if official is None else official.issued_at,
            available_at=None if prov is None else prov.retrieved_at,
            system_now=system_now,
        ),
        flow=None if state is None else state.observed.value,
        flow_unit=None if state is None else state.observed.unit,
        daily_mean_day=None if state is None else state.day,
        level=level,
        surface_state=_enum(surface.state),
        surface_reason=surface.reason,
        confidence=_enum(surface.confidence),
        velocity=tuple(velocity),
        trend=trend,
        observed_category=None if item is None else _enum(item.observed_category),
        observed_category_reason=None if item is None else item.observed_category_reason,
        threshold_basis=None if thresholds is None else thresholds.basis,
        headroom_to=None if headroom is None else _enum(headroom.to_category),
        headroom_value=None if headroom is None or headroom.value is None else headroom.value.value,
        headroom_unit=None if headroom is None or headroom.value is None else headroom.value.unit,
        headroom_time_to_threshold_h=None if headroom is None else headroom.time_to_threshold_h,
        headroom_reason=None if headroom is None else headroom.reason,
        official_forecast_category=None if official is None else _enum(official.category),
        official_forecast_crest=None if official is None or official.crest is None else official.crest.value,
        official_forecast_issued_at=None if official is None else official.issued_at,
        forcing_state=_enum(frc.surface.state),
        forcing_reason=frc.surface.reason,
        agreement_state=ag_state,
        agreement_reason=ag_reason,
        reference=ref,
        quality_flags=quality,
        method_ids=method_ids,
        raw_artifact_ids=artifacts,
    )


async def _percentile_history(k: Knowledge, gauge_id: str) -> list[tuple[datetime, float, float | None]]:
    """`(valid_time, flow, percentile)` for the stored daily-mean rows visible at `k.as_of`.

    Read over :data:`susceptibility.STATE_CHANGE_LOOKBACK` — the same window the surface's own
    velocity reads — so this costs no extra statement after `susceptibility.prefetch`.
    """
    rows = await k.derived_features(
        susceptibility.PERCENTILE_FEATURE,
        gauge_id,
        method_id=susceptibility.PERCENTILE_ROW_METHOD_ID,
        valid_from=k.as_of - susceptibility.STATE_CHANGE_LOOKBACK,
        valid_until=k.as_of,
        latest_per_valid_time=True,
    )
    return [(r.valid_time, float(r.value), None if r.percentile is None else float(r.percentile)) for r in rows if r.value is not None]


def _percentile_delta(
    history: Sequence[tuple[datetime, float, float | None]],
    *,
    anchor: datetime | None,
    window_h: int,
    tolerance_h: float = susceptibility.STATE_CHANGE_TOLERANCE_H,
) -> tuple[float | None, str | None]:
    """The change in the SHIPPED percentile over ``window_h``, or None with a reason.

    The endpoint discipline is deliberately :func:`susceptibility.state_change`'s — the prior
    endpoint must exist within ``tolerance_h`` of its target or the answer is UNKNOWN rather
    than a silently shortened window — and ``anchor`` is the same instant the surface passes as
    that function's ``end`` (the latest ranked daily mean's valid time). So the diagnostic and
    the published growth refuse on exactly the same days, and any difference between them comes
    from the representation rather than from one being more permissive about missing data.
    """
    if anchor is None:
        return None, "no ranked daily mean at or before the knowledge time"
    now = [p for t, _v, p in history if t == anchor and p is not None]
    if not now:
        return None, f"the daily mean at {anchor.isoformat()} carries no percentile"
    target = anchor - timedelta(hours=window_h)
    tol = timedelta(hours=tolerance_h)
    prior = [(t, p) for t, _v, p in history if abs(t - target) <= tol and p is not None]
    if not prior:
        return None, f"no ranked daily mean within {tolerance_h:g} h of {target.isoformat()}"
    _t_then, p_then = min(prior, key=lambda pair: abs(pair[0] - target))
    return round(now[-1] - p_then, 2), None


async def _trend_for_arm(
    k: Knowledge,
    *,
    arm: MethodArm,
    outlet: ForecastPoint | None,
    point: assemble.PointAssessment | None,
    tidal_class: TidalClass | None = None,
) -> TrendReading:
    """The arm's rate of rise over the same window, from the same observations.

    Both arms are handed the SAME window, the same basis and the same unit; they differ in the
    estimator and in nothing else. The old arm re-runs the preserved
    `method:rate-of-rise@1.0.0` — kept callable in `trend.py` precisely so the comparison runs
    against the code that was deployed rather than a reconstruction of it.

    `rate_of_rise` has no tidal guard — it never had one — so the old arm will report a rate at a
    station the new arm refuses. That difference is a *finding*, not something to be equalised
    away, and the tidal class is READ from the seeded station exactly as `assemble` reads it
    rather than being assumed by a caller.
    """
    if outlet is None or point is None or outlet.station_id is None:
        return TrendReading(
            method_id=arm.trend_method_id, estimator=None, basis=None, window_h=None, slope=None,
            slope_unit=None, direction=UNKNOWN, n=None, span_h=None, quality=None,
            refusal_reason="no outlet forecast point with a station",
        )
    if tidal_class is None:
        station = await k.station(outlet.station_id)
        try:
            tidal_class = TidalClass(station.tidal_class) if station is not None and station.tidal_class else None
        except ValueError:
            tidal_class = TidalClass.UNVERIFIED
    basis = assemble.observed_basis(point.thresholds)
    window = await k.observations(outlet.station_id, basis, since=k.as_of - assemble.TREND_WINDOW)
    points = [(o.valid_time, o.value) for o in window if o.value is not None]
    unit = next((o.unit for o in window if o.unit), "ft" if basis == "stage" else "cfs")
    if arm.trend_is_endpoint_difference:
        v1 = rate_of_rise(points, basis=basis, unit=unit, end=k.as_of, window_h=int(assemble.TREND_WINDOW_H))
        return TrendReading(
            method_id=arm.trend_method_id, estimator="endpoint", basis=basis,
            window_h=float(v1.window_h), slope=None if v1.rate is None else round(v1.rate, 4),
            slope_unit=v1.unit, direction=v1.direction, n=len(points), span_h=None,
            quality=None, refusal_reason=v1.reason,
        )
    est: TrendEstimate = estimate_trend(
        points, station_id=outlet.station_id, basis=basis, unit=unit, end=k.as_of,
        tidal_class=tidal_class, window_h=assemble.TREND_WINDOW_H,
    )
    return TrendReading(
        method_id=arm.trend_method_id, estimator=est.estimator, basis=est.basis, window_h=est.window_h,
        slope=None if est.slope is None else round(est.slope, 4), slope_unit=est.slope_unit,
        direction=est.direction, n=est.n, span_h=round(est.span_h, 3),
        quality=None if est.quality is None else est.quality.value,
        refusal_reason=None if est.refusal is None else est.refusal.reason,
        slope_q25=None if est.slope_q25 is None else round(est.slope_q25, 4),
        slope_q75=None if est.slope_q75 is None else round(est.slope_q75, 4),
    )


# =============================================================================================
# 7. Escalation, and the rule that keeps a lead-time claim honest (brief §13)
# =============================================================================================


@dataclass(frozen=True)
class EscalationRule:
    """A predicate over one :class:`Evaluation`, plus the provenance of every constant in it.

    Neither :attr:`fixed_independently_of_outcome` nor :attr:`constant_provenance` has a
    default, and that is the entire safeguard. "Earliest escalation" is only a lead time if the
    bar was set before anyone knew where the event crossed it; a rule whose constant came out of
    an Event Zero table is a description of Event Zero and cannot also be evidence about it.
    :func:`compare_arms` reads this field and refuses the phrase where it is False.

    ``applies_to`` names the arms that can even be asked. A rule over the seasonal multiple is
    not "false" under `@0.1.0` — it is unanswerable, because that surface publishes no multiple,
    and scoring it as a non-detection would flatter the new arm by construction.
    """

    id: str
    label: str
    predicate: Callable[[Evaluation], bool]
    fixed_independently_of_outcome: bool
    constant_provenance: str
    applies_to: tuple[str, ...] = ("old", "new")
    note: str = ""

    def holds(self, ev: Evaluation) -> bool:
        if ev.arm_id not in self.applies_to:
            return False
        try:
            return bool(self.predicate(ev))
        except (TypeError, ValueError):  # a None where a number was expected is "not escalated"
            return False


def _band_at_least(ev: Evaluation, level: SurfaceLevel) -> bool:
    order = ev.band_order
    return order is not None and order >= susceptibility.BAND_ORDER.index(level)


def _rising(ev: Evaluation, window_h: int) -> bool:
    w = ev.window(window_h)
    return w is not None and w.growth_direction == "rising"


def _growth_rank_within(ev: Evaluation, window_h: int, fraction: float) -> bool:
    w = ev.window(window_h)
    if w is None or w.growth_rank is None or not w.growth_rank_of:
        return False
    return w.growth_rank <= max(1, math.ceil(fraction * w.growth_rank_of))


#: The rules used for the Tier 0 A/B. Each one's constant is either a band edge that predates
#: this change or an epsilon the change explicitly did NOT touch; none was chosen by looking at
#: where Event Zero crossed it. Additional rank-fraction rules are built by
#: :func:`growth_rank_rules` and are marked as NOT independently fixed, because choosing the
#: fraction is choosing the answer.
BAND_ESCALATION = EscalationRule(
    id="band_very_high",
    label="the banded susceptibility surface first reads VERY_HIGH (day-of-year percentile ≥ p90)",
    predicate=lambda ev: _band_at_least(ev, SurfaceLevel.VERY_HIGH),
    fixed_independently_of_outcome=True,
    constant_provenance=(
        "susceptibility.BAND_EDGES = (25, 75, 90), the USGS WaterWatch below-normal / "
        "above-normal / much-above-normal convention. Present in the surface before this change, "
        "explicitly NOT recalibrated by it (METHOD_PARAMETERS['calibrated'] is still False), and "
        "identical in both arms."
    ),
)

BAND_HIGH_ESCALATION = EscalationRule(
    id="band_high",
    label="the banded susceptibility surface first reads HIGH or above (percentile ≥ p75)",
    predicate=lambda ev: _band_at_least(ev, SurfaceLevel.HIGH),
    fixed_independently_of_outcome=True,
    constant_provenance="susceptibility.BAND_EDGES, second edge. Same provenance as band_very_high.",
)

RISING_24H = EscalationRule(
    id="rising_24h",
    label="the 24 h state change first reads RISING",
    predicate=lambda ev: _rising(ev, 24),
    fixed_independently_of_outcome=True,
    constant_provenance=(
        "TWO constants, both named because this predicate reads both. (1) "
        "trend.FLOW_STEADY_FRACTION_PER_H = 0.01, compounded over the actual span "
        "(susceptibility.state_change). This is the STEADY band the deployed rate-of-rise "
        "already decided direction against; trend.py states that it is unchanged between v1 and "
        "v2 precisely so that an A/B cannot be fitted to Event Zero. (2) "
        "susceptibility.STATE_CHANGE_WINDOWS_H = (24, 48), the window this rule reads. Its "
        "independence rests on CADENCE, not on a citation: the series is a daily mean, so 24 h "
        "is the shortest computable window and 48 h the next -- there is no continuum to sweep "
        "and no shorter alternative that was rejected. Both are reported, neither is selected "
        "post hoc. That argument is what licenses fixed_independently_of_outcome here; the "
        "windows were nonetheless ADOPTED after tier0 §2 measured a 1-3 day lead across them, "
        "which susceptibility.STATE_CHANGE_WINDOWS_H states, and a reader who rejects the "
        "cadence argument should read this rule's lead time as a sweep of size two."
    ),
    applies_to=("new",),
    note=(
        "Unanswerable under @0.1.0: that surface publishes no state change at all. Reported as "
        "'the old arm has no such statement', never as a non-detection."
    ),
)

RISING_48H = EscalationRule(
    id="rising_48h",
    label="the 48 h state change first reads RISING",
    predicate=lambda ev: _rising(ev, 48),
    fixed_independently_of_outcome=True,
    constant_provenance="trend.FLOW_STEADY_FRACTION_PER_H, as rising_24h.",
    applies_to=("new",),
)

def _any_escalation(ev: Evaluation) -> bool:
    return _band_at_least(ev, SurfaceLevel.VERY_HIGH) or _rising(ev, 24)


ANY_ESCALATION = EscalationRule(
    id="any_escalation",
    label="the method first publishes ANY escalation it has the vocabulary for: VERY_HIGH, or a RISING 24 h state change",
    predicate=_any_escalation,
    fixed_independently_of_outcome=True,
    constant_provenance=(
        "A disjunction over THREE constants, all named because the predicate reads all three: "
        "susceptibility.BAND_EDGES's top edge (p90, USGS WaterWatch convention), "
        "trend.FLOW_STEADY_FRACTION_PER_H (1 %/h, the STEADY band v1 and v2 share), and "
        "susceptibility.STATE_CHANGE_WINDOWS_H's 24 h window, whose independence rests on the "
        "daily-mean cadence rather than on a citation (see RISING_24H). The first two predate "
        "this change and neither was chosen by looking at where Event Zero crossed it; the third "
        "was adopted after tier0 §2, and the cadence argument is what licenses it. An earlier "
        "version of this string named only the first two, while the predicate read all three."
    ),
    note=(
        "This is the arm-level question — EARLIEST ESCALATION OF ANY KIND — and it is the only "
        "rule here under which a lead time is meaningful, because the two arms do not have the "
        "same vocabulary. Under @0.1.0 the second disjunct is unanswerable and the rule reduces "
        "to the band, which is not a handicap imposed by the harness: having no velocity "
        "statement at all is the defect under test. A reader must still see the per-rule "
        "breakdown, because the two disjuncts are different KINDS of statement — a level and a "
        "rate — and a single earliest-instant number hides which one fired."
    ),
)

TREND_RISING = EscalationRule(
    id="trend_rising_6h",
    label="the 6 h rate of rise at the outlet first reads RISING",
    predicate=lambda ev: ev.trend.direction == "rising",
    fixed_independently_of_outcome=True,
    constant_provenance=(
        "trend.steady_epsilon — 0.05 ft/h on stage, 1 %/h on flow. Unchanged between "
        "method:rate-of-rise@1.0.0 and @2.0.0, so the two arms differ only in the estimator."
    ),
)


def growth_rank_rules(fraction: float, *, window_h: int = 24) -> EscalationRule:
    """A rule of the form "this change is in the gauge's own top ``fraction`` of changes".

    Marked NOT independently fixed, on purpose. The *rank* is a fact about the record and needs
    no cutoff; the moment a fraction is chosen to declare an escalation, a cutoff has been drawn
    — and `high-tail-selection-2026-08-27.md` §9 is explicit that drawing one needs brief §18's
    multi-event POD/FAR curve, which does not exist. These rules are therefore reported as a
    SENSITIVITY SWEEP — several fractions side by side, with the false-warning count beside each
    — and never as the harness's answer.
    """
    def _predicate(ev: Evaluation) -> bool:
        return _growth_rank_within(ev, window_h, fraction)

    return EscalationRule(
        id=f"growth_rank_top_{fraction:g}_{window_h}h",
        label=f"the {window_h} h growth ranks in this gauge's own largest {fraction:.1%} of changes",
        predicate=_predicate,
        fixed_independently_of_outcome=False,
        constant_provenance=(
            f"{fraction:g} is CHOSEN HERE and validated nowhere. No band may be drawn on the "
            "growth until brief §18's multi-event POD/FAR curve exists."
        ),
        applies_to=("new",),
    )


@dataclass(frozen=True)
class EscalationResult:
    rule_id: str
    arm_id: str
    basin_id: str
    applicable: bool
    first_time: datetime | None
    first_cursor: date | None
    evaluations: int
    control_firings: int
    control_evaluations: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "arm_id": self.arm_id,
            "basin_id": self.basin_id,
            "applicable": self.applicable,
            "first_time": None if self.first_time is None else self.first_time.isoformat(),
            "first_cursor": None if self.first_cursor is None else self.first_cursor.isoformat(),
            "evaluations": self.evaluations,
            "control_firings": self.control_firings,
            "control_evaluations": self.control_evaluations,
        }


def earliest_escalation(rows: Sequence[Evaluation], rule: EscalationRule, *, arm_id: str, basin_id: str) -> EscalationResult:
    """First event-window instant at which ``rule`` holds, plus how often it held in the control.

    The two are returned together and never separately: an escalation time without its
    false-warning count answers half the governing question, and the half it answers is the
    flattering one.
    """
    mine = [r for r in rows if r.arm_id == arm_id and r.basin_id == basin_id]
    event_rows = sorted((r for r in mine if not r.is_control), key=lambda r: r.clocks.as_of)
    control_rows = [r for r in mine if r.is_control]
    hit = next((r for r in event_rows if rule.holds(r)), None)
    return EscalationResult(
        rule_id=rule.id,
        arm_id=arm_id,
        basin_id=basin_id,
        applicable=arm_id in rule.applies_to,
        first_time=None if hit is None else hit.clocks.as_of,
        first_cursor=None if hit is None else hit.clocks.cursor,
        evaluations=len(event_rows),
        control_firings=sum(1 for r in control_rows if rule.holds(r)),
        control_evaluations=len(control_rows),
    )


@dataclass(frozen=True)
class ArmComparison:
    """One rule, one basin, both arms — and the verdict, with the phrase policed."""

    rule_id: str
    basin_id: str
    old: EscalationResult
    new: EscalationResult
    difference_h: float | None
    verdict: str
    legitimate_lead_time: bool
    caveat: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "basin_id": self.basin_id,
            "old": self.old.as_dict(),
            "new": self.new.as_dict(),
            "difference_h": self.difference_h,
            "verdict": self.verdict,
            "legitimate_lead_time": self.legitimate_lead_time,
            "caveat": self.caveat,
        }


def compare_arms(
    rows: Sequence[Evaluation],
    rule: EscalationRule,
    *,
    basin_id: str,
    old_arm: str = ARM_OLD.id,
    new_arm: str = ARM_NEW.id,
) -> ArmComparison:
    """Both arms under one rule, with the words "lead time" available only when they are earned.

    Three verdicts and nothing else may be produced here:

    - ``lead_time`` — both arms answer the rule, the new one fires earlier, and the rule's
      constant was fixed independently of the outcome;
    - ``earlier_but_not_a_lead_time`` — the new arm fires earlier under a rule whose constant
      was chosen after the fact, or under a rule the old arm cannot answer at all. A real and
      reportable difference; not evidence of skill;
    - ``no_difference`` / ``later`` — said plainly, including when that is the answer for the
      change we shipped.
    """
    old = earliest_escalation(rows, rule, arm_id=old_arm, basin_id=basin_id)
    new = earliest_escalation(rows, rule, arm_id=new_arm, basin_id=basin_id)
    diff = None
    if old.first_time is not None and new.first_time is not None:
        diff = round((old.first_time - new.first_time).total_seconds() / 3600.0, 2)

    if not new.applicable and not old.applicable:
        return ArmComparison(rule.id, basin_id, old, new, None, "not_applicable", False,
                             "neither arm publishes a statement this rule can read")
    if old.applicable and new.applicable:
        caveat: str | None
        if old.first_time is None and new.first_time is None:
            verdict, legit, caveat = "no_difference", False, "neither arm escalated in the event window"
        elif new.first_time is None:
            verdict, legit, caveat = "later", False, "the new arm never escalated where the old one did"
        elif old.first_time is None:
            verdict = "earlier_but_not_a_lead_time"
            legit = False
            caveat = "the old arm never escalated at all, so there is no baseline instant to subtract from"
        elif diff and diff > 0:
            legit = rule.fixed_independently_of_outcome
            verdict = "lead_time" if legit else "earlier_but_not_a_lead_time"
            caveat = None if legit else f"rule constant not fixed independently of the outcome: {rule.constant_provenance}"
        elif diff and diff < 0:
            verdict, legit, caveat = "later", False, None
        else:
            verdict, legit, caveat = "no_difference", False, "both arms escalated at the same instant"
    else:
        answering, silent = (new, old) if new.applicable else (old, new)
        verdict = "earlier_but_not_a_lead_time" if answering.first_time is not None else "no_difference"
        legit = False
        caveat = (
            f"only the {answering.arm_id} arm publishes a statement this rule can read; the "
            f"{silent.arm_id} arm is unanswerable, not a non-detection. {rule.note}".strip()
        )
    return ArmComparison(rule.id, basin_id, old, new, diff, verdict, legit, caveat)


# =============================================================================================
# 8. The run document
# =============================================================================================


@dataclass
class HindcastRun:
    """Everything one replay produced, in the shape a report and a fixture both read.

    Compact by construction: :attr:`evaluations` holds surface outputs, never source rows, and
    the whole six-basin Event Zero run is a few hundred kilobytes of JSON rather than a copy of
    a 36,000-row daily record.
    """

    event: HindcastEvent
    projection: Projection
    arms: tuple[MethodArm, ...]
    evaluations: list[Evaluation] = field(default_factory=list)
    rules: tuple[EscalationRule, ...] = ()
    generated_at: datetime | None = None
    notes: tuple[str, ...] = ()

    def comparisons(self) -> list[ArmComparison]:
        return [
            compare_arms(self.evaluations, rule, basin_id=basin_id)
            for rule in self.rules
            for basin_id in self.event.basin_ids
        ]

    def as_dict(self) -> dict[str, Any]:
        return {
            "event": {
                "id": self.event.id,
                "label": self.event.label,
                "source": self.event.source,
                "basins": list(self.event.basin_ids),
                "evaluation_times": [t.isoformat() for t in self.event.evaluation_times],
                "control_times": [t.isoformat() for t in self.event.control_times],
                "outcomes": [o.as_dict() for o in self.event.outcomes],
            },
            "projection": {
                "name": self.projection.name,
                "mode": self.projection.mode.value,
                "disclosure": self.projection.disclosure(),
                "note": self.projection.note,
                "rules": [
                    {
                        "row_family": r.row_family,
                        "visibility_clock": r.visibility_clock,
                        "rule": r.rule,
                        "optimism": r.optimism,
                        "anachronism": r.anachronism,
                    }
                    for r in self.projection.rules
                ],
            },
            "arms": [
                {
                    "id": a.id,
                    "label": a.label,
                    "susceptibility_version": a.susceptibility_version,
                    "trend_method_id": a.trend_method_id,
                }
                for a in self.arms
            ],
            "rules": [
                {
                    "id": r.id,
                    "label": r.label,
                    "fixed_independently_of_outcome": r.fixed_independently_of_outcome,
                    "constant_provenance": r.constant_provenance,
                    "applies_to": list(r.applies_to),
                    "note": r.note,
                }
                for r in self.rules
            ],
            "generated_at": None if self.generated_at is None else self.generated_at.isoformat(),
            "notes": list(self.notes),
            "evaluations": [e.as_dict() for e in self.evaluations],
            "comparisons": [c.as_dict() for c in self.comparisons()],
        }


__all__ = [
    "ANY_ESCALATION",
    "ARM_NEW",
    "ARM_OLD",
    "BAND_ESCALATION",
    "BAND_HIGH_ESCALATION",
    "RISING_24H",
    "RISING_48H",
    "TREND_RISING",
    "ArmComparison",
    "BasinOutcome",
    "Clocks",
    "Evaluation",
    "EscalationResult",
    "EscalationRule",
    "HindcastEvent",
    "HindcastRun",
    "LevelReading",
    "MethodArm",
    "Projection",
    "ProjectionRule",
    "ReferenceDefinition",
    "ReplayMode",
    "TrendReading",
    "VelocityReading",
    "compare_arms",
    "earliest_escalation",
    "evaluate",
    "evaluation_from_dict",
    "evaluations_from_document",
    "growth_rank_rules",
]
