"""Headroom: distance from the current value to the next official category above it, in the
threshold's own basis/unit/datum. `time_to_threshold_h` exists only when the trend is rising
with a positive rate (headroom / rate); otherwise it is None with a reason."""

from __future__ import annotations

from dataclasses import dataclass

from cascade_contracts import FloodCategory
from cascade_hydrology.category import Measure, ThresholdSet, compatibility_problem
from cascade_hydrology.trend import RISING


@dataclass(frozen=True)
class HeadroomResult:
    basis: str
    to_category: FloodCategory
    value: float | None
    unit: str
    datum: str | None
    time_to_threshold_h: float | None
    reason: str | None


def headroom(m: Measure | None, t: ThresholdSet | None, *, rate_per_h: float | None, direction: str) -> HeadroomResult | None:
    if t is None or m is None:
        return None
    if (problem := compatibility_problem(m, t)) is not None:
        return HeadroomResult(t.basis, FloodCategory.UNKNOWN, None, t.unit, t.datum, None, problem)
    above = [(c, v) for c, v in t.defined() if v > m.value]
    if not above:
        return HeadroomResult(t.basis, FloodCategory.MAJOR, None, t.unit, t.datum, None, "at or above the highest official category; no headroom")
    cat, thr = above[0]
    room = thr - m.value
    if direction == RISING and rate_per_h is not None and rate_per_h > 0:
        return HeadroomResult(t.basis, FloodCategory(cat), room, t.unit, t.datum, room / rate_per_h, None)
    return HeadroomResult(t.basis, FloodCategory(cat), room, t.unit, t.datum, None, "time_to_threshold requires a rising trend")
