"""NWM medium-range ensemble -> the two things Cascadia Papsukkal stores (design §3.4).

Volume control, not laziness: the full payload is 157–161 KB per reach per cycle, and storing
all seven series × 240 hours × six reaches would write ~1.2 M `forecast_value` rows a month.
What is stored instead is

1. **one `ForecastRun`** carrying the provider's `mean` series truncated to the 72-hour hazard
   window (72 points), with `product_id = product:nwm-mr-via-nwps`, `primary_variable="flow"`,
   `unit="cfs"`, `stage_unit=None` and `datum=None` — a flow value never has a datum
   (ADR-0014); and
2. **the member hydrographs themselves**, clipped to `(referenceTime, referenceTime + 96 h]`
   and encoded into one `derived_feature.values_json` — which is what the agreement method
   reads.

The full JSON stays in the object store as the RawArtifact, so everything else is re-derivable.

**Why series and not crests — the defect this replaces (verification finding B, 2026-08-24).**
The first version of this module froze a *crest per member* at ingest, taken over the
cycle-anchored window `(referenceTime, referenceTime + 72 h]`. The official crest it was then
compared against is computed at **read** time over the `as_of`-anchored hazard window
`(as_of − 6 h, as_of + 72 h]`. Those are two different windows, offset by the cycle age (5–14 h
in practice), so the model's "crest" could sit at an instant *before the official window opened*
— measured 2 h 43 m before at MVEW1 — while the last hours of the official window were invisible
to the model side entirely. A `Δt` computed across that offset is not a timing disagreement, it
is the cycle age; on a rising hydrograph it biases the magnitude comparison too. The fix is
structural rather than arithmetic: **no crest is frozen here at all.** The member series is
stored, and every crest — official and model — is taken at read time over one shared window
(`cascade_hydrology.agreement`). A number that can only be computed correctly at read time must
not be precomputed at ingest.

`COVERAGE_HORIZON_H` is 96 h rather than 72 h for exactly that reason: the read-time window ends
at `as_of + 72 h`, which is `cycle_age` hours past `cycle + 72 h`, so the stored series must run
past the hazard horizon by at least the cycle age or the model side is short again. 96 h covers a
cycle up to 24 h old — four missed cycles — and the read path reports the shortfall rather than
hiding it when a cycle is older still.

Two doctrine rules are enforced here rather than left to callers:

- the `mean` series is the *provider's* read-time average of its own members. It is stored as
  the model hydrograph and labeled as such; it is never counted as a member and is never
  averaged with anything the NWRFC issued (docs/DATA_DOCTRINE.md §9, §10). It is not part of the
  stored member series and no comparison reads it.
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

#: How much of each member is stored, measured from the model cycle. See the module docstring:
#: the read-time window ends `cycle_age` hours past `cycle + HAZARD_HORIZON_H`, so anything less
#: than `HAZARD_HORIZON_H + max cycle age` leaves the model side short of the official window.
#: 24 h of headroom covers four missed 6-hourly cycles.
MAX_CYCLE_AGE_H = 24
COVERAGE_HORIZON_H = HAZARD_HORIZON_H + MAX_CYCLE_AGE_H

#: Version of the `values_json` payload shape. The reader refuses a schema it does not know
#: rather than guessing at the fields, so a future encoding change cannot be silently
#: half-understood.
SERIES_SCHEMA = "nwm-member-series@1"

#: Encodings the payload may use. `grid` is the normal case (NWM medium range is hourly and
#: gapless); `points` is the fallback for any cadence that is not a single uniform step, so an
#: irregular series is stored faithfully instead of being resampled onto a grid it is not on.
ENCODING_GRID = "grid"
ENCODING_POINTS = "points"

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
class MemberSeries:
    """One member's hydrograph inside the stored coverage window.

    `points` keeps the provider's sentinels as `None` rather than dropping them, so the series
    stays on its own time grid and a gap reads as a gap instead of shifting the neighbouring
    hours onto the wrong timestamps.
    """

    member: str
    points: tuple[tuple[datetime, float | None], ...]

    @property
    def observed_count(self) -> int:
        return sum(1 for _, v in self.points if v is not None)


@dataclass(frozen=True)
class EnsembleWindow:
    """Every member of one NWM cycle, clipped to `(cycle, cycle + coverage_h]`.

    There is deliberately no crest, no median and no central value on this object. Choosing a
    crest requires a window, the window is only known at read time, and a value that cannot be
    computed correctly here is not computed here (see the module docstring).
    """

    issued_at: datetime
    coverage_h: int
    hazard_window_h: int
    unit: str
    members: tuple[MemberSeries, ...]

    @property
    def member_count(self) -> int:
        return len(self.members)


def _window(
    series: ReachSeries, *, horizon_h: int, keep_sentinels: bool = False
) -> tuple[tuple[datetime, float | None], ...]:
    """Points with valid_time in (referenceTime, referenceTime + horizon].

    `keep_sentinels` decides what a `-9999` becomes: dropped (the `ForecastRun` path, where a
    row with no value is not a forecast) or kept as `None` (the series path, where the grid must
    stay intact). Neither path ever turns a sentinel into a number.
    """
    lo = series.reference_time
    hi = lo + timedelta(hours=horizon_h)
    return tuple(
        (p.valid_time, p.flow)
        for p in series.points
        if lo < p.valid_time <= hi and (keep_sentinels or p.flow is not None)
    )


def _uniform_step_h(times: tuple[datetime, ...]) -> float | None:
    """The single time step of a series, or None when the series is not on one uniform grid."""
    if len(times) < 2:
        return None
    steps = {(times[i + 1] - times[i]).total_seconds() for i in range(len(times) - 1)}
    if len(steps) != 1:
        return None
    step = steps.pop()
    return step / 3600.0 if step > 0 else None


def encode_series(points: tuple[tuple[datetime, float | None], ...]) -> dict[str, object]:
    """One member's hydrograph as JSON, in the most compact encoding that is exactly faithful.

    `grid` stores the first timestamp, the step and the flows; every other timestamp is implied,
    which is the whole saving. It is used only when the series really is on one uniform step —
    otherwise the explicit `points` form is written, because inferring a grid a series is not on
    would move values to times the model never gave them.
    """
    if not points:
        return {"encoding": ENCODING_POINTS, "points": []}
    times = tuple(t for t, _ in points)
    step = _uniform_step_h(times)
    if step is None:
        return {"encoding": ENCODING_POINTS, "points": [[t.isoformat(), v] for t, v in points]}
    return {
        "encoding": ENCODING_GRID,
        "t0": times[0].isoformat(),
        "step_h": step,
        "flow": [v for _, v in points],
    }


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
    caller must be able to see, never an empty run that looks like a forecast of nothing.

    This series exists to be *displayed* as the model hydrograph and to anchor the cycle in
    `forecast_run`. It is never a comparison basis: the mean is the provider's average of its own
    members, and averaging is not a thing this platform does across sources
    (docs/DATA_DOCTRINE.md §10). The comparison reads the member series instead.
    """
    if ensemble.mean is None:
        return None
    issued_at = _check_one_cycle(ensemble)
    values = tuple(
        ModelForecastValue(valid_time=t, flow=v)
        for t, v in _window(ensemble.mean, horizon_h=horizon_h)
        if v is not None
    )
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


def member_window(
    ensemble: MediumRangeEnsemble,
    *,
    coverage_h: int = COVERAGE_HORIZON_H,
    hazard_window_h: int = HAZARD_HORIZON_H,
) -> EnsembleWindow | None:
    """Every member's hydrograph over `(cycle, cycle + coverage_h]`, with no crest taken.

    The member list is whatever the payload shipped — the count is a version-dependent fact
    (design §7 item 4) and is never assumed — and the mean is not among them.
    """
    if not ensemble.members:
        return None
    issued_at = _check_one_cycle(ensemble)
    members = tuple(
        MemberSeries(member=s.name, points=_window(s, horizon_h=coverage_h, keep_sentinels=True))
        for s in ensemble.members
    )
    members = tuple(m for m in members if m.observed_count)
    if not members:
        return None
    return EnsembleWindow(
        issued_at=issued_at,
        coverage_h=coverage_h,
        hazard_window_h=hazard_window_h,
        unit=FLOW_UNIT,
        members=members,
    )
