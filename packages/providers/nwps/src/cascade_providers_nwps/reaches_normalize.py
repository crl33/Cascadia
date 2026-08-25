"""NWM medium-range ensemble -> the two things Cascadia Papsukkal stores (design §3.4).

Volume control, not laziness: the full payload is 157–161 KB per reach per cycle, and storing
all seven series × 240 hours × six reaches would write ~1.2 M `forecast_value` rows a month.
What is stored instead is

1. **one `ForecastRun`** carrying the provider's `mean` series truncated to the 72-hour hazard
   window (72 points), with `product_id = product:nwm-mr-via-nwps`, `primary_variable="flow"`,
   `unit="cfs"`, `stage_unit=None` and `datum=None` — a flow value never has a datum
   (ADR-0014); and
2. **crest summaries per member**, which is all the agreement method reads.

The full JSON stays in the object store as the RawArtifact, so everything else is re-derivable.

Two doctrine rules are enforced here rather than left to callers:

- the `mean` series is the *provider's* read-time average of its own members. It is stored as
  the model hydrograph and labeled as such; it is never counted as a member and is never
  averaged with anything the NWRFC issued (docs/DATA_DOCTRINE.md §9, §10).
- every member of one stored ensemble must carry the same `referenceTime`. A payload whose
  members mix cycles is refused: a mixed-cycle ensemble is a fabricated ensemble.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from cascade_core.timeutils import available_at
from cascade_providers_nwps.reaches_parser import (
    FLOW_UNIT,
    MediumRangeEnsemble,
    ReachSeries,
)

#: The hazard horizon the official forecast is already summarized over
#: (`cascade_hydrology.surfaces.HAZARD_HORIZON_H`), repeated here as a constant rather than
#: imported, because a provider adapter does not depend on the hydrology package. Agreement is
#: only meaningful if both sides are talking about the same event window (design §3.2).
HAZARD_HORIZON_H = 72

ISSUER = "NOAA OWP (National Water Model v3.1)"


class NormalizeError(ValueError):
    pass


@dataclass(frozen=True)
class ModelForecastValue:
    valid_time: datetime
    flow: float  # cfs


@dataclass(frozen=True)
class ModelRunRecord:
    """A `ForecastRun` row's worth of NWM output. Flow only, cfs, no stage column, no datum."""

    issued_at: datetime
    retrieved_at: datetime
    available_at: datetime
    issuer: str
    primary_variable: str
    unit: str
    stage_unit: str | None
    flow_unit: str | None
    datum: str | None
    series_name: str
    values: tuple[ModelForecastValue, ...]


@dataclass(frozen=True)
class MemberCrest:
    member: str
    value: float  # cfs
    valid_time: datetime


@dataclass(frozen=True)
class EnsembleCrestSummary:
    """Member crests inside the hazard window, plus which member is the median.

    ``median_member`` is the **lower median member** — for an even member count the lower of the
    two central members, i.e. always a member the model actually produced. The alternative (the
    arithmetic mean of the two central crests) would invent a value no member forecast and would
    leave `Δt` without a member to take its crest time from, which design §3.2 step 4 assumes it
    has. The rule is part of the method id, so changing it is a new method version.
    """

    issued_at: datetime
    window_h: int
    unit: str
    members: tuple[MemberCrest, ...]
    median_member: MemberCrest | None
    provider_mean_crest: MemberCrest | None

    @property
    def member_count(self) -> int:
        return len(self.members)


def _window(series: ReachSeries, *, horizon_h: int) -> tuple[tuple[datetime, float], ...]:
    """Points with valid_time in (referenceTime, referenceTime + horizon]; sentinels dropped."""
    lo = series.reference_time
    hi = lo + timedelta(hours=horizon_h)
    return tuple((p.valid_time, p.flow) for p in series.points if p.flow is not None and lo < p.valid_time <= hi)


def _crest(series: ReachSeries, *, horizon_h: int) -> MemberCrest | None:
    inside = _window(series, horizon_h=horizon_h)
    if not inside:
        return None
    t, v = max(inside, key=lambda tv: (tv[1], -tv[0].timestamp()))  # earliest time wins a tie
    return MemberCrest(member=series.name, value=v, valid_time=t)


def _check_one_cycle(ensemble: MediumRangeEnsemble) -> datetime:
    reference = ensemble.reference_time
    if reference is None:
        raise NormalizeError("ensemble carries no series and therefore no reference time")
    mixed = sorted(
        {s.reference_time.isoformat() for s in ((ensemble.mean,) if ensemble.mean else ()) + ensemble.members}
    )
    if len(mixed) != 1:
        raise NormalizeError(f"members mix model cycles {mixed}; refusing to store a mixed-cycle ensemble")
    return reference


def model_run_from_ensemble(
    ensemble: MediumRangeEnsemble, *, retrieved_at: datetime, horizon_h: int = HAZARD_HORIZON_H
) -> ModelRunRecord | None:
    """The stored run: the provider's `mean` series, truncated to the hazard window.

    Returns None when the payload carries no usable mean series — "no NWM cycle" is a state the
    caller must be able to see, never an empty run that looks like a forecast of nothing."""
    if ensemble.mean is None:
        return None
    issued_at = _check_one_cycle(ensemble)
    values = tuple(ModelForecastValue(valid_time=t, flow=v) for t, v in _window(ensemble.mean, horizon_h=horizon_h))
    if not values:
        return None
    return ModelRunRecord(
        issued_at=issued_at,
        retrieved_at=retrieved_at,
        available_at=available_at(valid_time=issued_at, retrieved_at=retrieved_at, issued_at=issued_at),
        issuer=ISSUER,
        primary_variable="flow",
        unit=FLOW_UNIT,
        stage_unit=None,  # NWM produces flow only
        flow_unit=FLOW_UNIT,
        datum=None,  # ADR-0014: a flow value never carries a vertical datum
        series_name=ensemble.mean.name,
        values=values,
    )


def crest_summary(
    ensemble: MediumRangeEnsemble, *, horizon_h: int = HAZARD_HORIZON_H
) -> EnsembleCrestSummary | None:
    """Per-member crest inside the hazard window, with the lower-median member identified."""
    if not ensemble.members:
        return None
    issued_at = _check_one_cycle(ensemble)
    crests = tuple(c for c in (_crest(s, horizon_h=horizon_h) for s in ensemble.members) if c is not None)
    ordered = sorted(crests, key=lambda c: (c.value, c.valid_time))
    median = ordered[(len(ordered) - 1) // 2] if ordered else None
    return EnsembleCrestSummary(
        issued_at=issued_at,
        window_h=horizon_h,
        unit=FLOW_UNIT,
        members=crests,
        median_member=median,
        provider_mean_crest=None if ensemble.mean is None else _crest(ensemble.mean, horizon_h=horizon_h),
    )
