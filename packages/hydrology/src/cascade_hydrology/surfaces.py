"""The risk surfaces at spike scope (docs/HYDROLOGY.md §3–§6, CONTEXT.md "never collapsed").

Susceptibility, forcing and agreement are UNKNOWN with explicit reasons: not implemented, not
defaulted to calm. Hazard is the official NWRFC forecast crest category over the horizon,
computed with the same official-threshold function as the observed category."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from cascade_contracts import FloodCategory
from cascade_hydrology.category import CategoryResult, Measure, ThresholdSet, categorize

SUSCEPTIBILITY_REASON = "Susceptibility index not implemented in the spike (ROADMAP Phase 3)."
FORCING_REASON = "Meteorological forcing not ingested in the spike (ROADMAP Phase 2)."
AGREEMENT_REASON = "Model agreement requires a second authoritative forecast source (NWM not ingested in the spike)."
HAZARD_HORIZON_H = 72


@dataclass(frozen=True)
class Crest:
    value: float
    valid_time: datetime


def forecast_crest(values: list[tuple[datetime, float | None]], *, as_of: datetime, horizon_h: int = HAZARD_HORIZON_H) -> Crest | None:
    """Maximum forecast value with valid_time in (as_of - 6 h, as_of + horizon]; None when nothing falls inside."""
    lo, hi = as_of - timedelta(hours=6), as_of + timedelta(hours=horizon_h)
    inside = [(t, v) for t, v in values if v is not None and lo < t <= hi]
    if not inside:
        return None
    t, v = max(inside, key=lambda tv: (tv[1], -tv[0].timestamp()))
    return Crest(value=v, valid_time=t)


def hazard_category(crest: Crest | None, *, basis: str, unit: str, datum: str | None, thresholds: ThresholdSet | None) -> CategoryResult:
    if crest is None:
        return CategoryResult(FloodCategory.UNKNOWN, "no official forecast values inside the hazard horizon")
    return categorize(Measure(basis=basis, value=crest.value, unit=unit, datum=datum), thresholds, label="Official forecast crest")
