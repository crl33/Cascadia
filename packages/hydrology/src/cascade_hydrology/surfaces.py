"""The basin risk surfaces (docs/HYDROLOGY.md §3–§6, CONTEXT.md "never collapsed").

Hazard is the official NWRFC forecast crest category over the horizon, computed with the same
official-threshold function as the observed category. Susceptibility, forcing and agreement are
computed by their own modules — `cascade_hydrology.susceptibility`, `.forcing`, `.agreement` —
and this module holds what they share: the hazard window, the crest function they all measure
over, and the assembler's UNKNOWN vocabulary.

**On reasons.** Until P3 this module held three constants — `SUSCEPTIBILITY_REASON`,
`FORCING_REASON`, `AGREEMENT_REASON` — each a variant of *"not implemented in the spike"*. Those
are gone. A constant reason cannot tell apart the three situations an operator has to act on
differently:

1. the method does not exist yet — nothing to do but build it;
2. the method exists and the input it reads is missing *today* — a provider outage or a job that
   has not run, actionable now;
3. the method exists and this basin is not configured for it — a seed edit.

So every UNKNOWN names the input that is absent (docs/DATA_DOCTRINE.md §12: UNKNOWN is a
legitimate state; an *unexplained* UNKNOWN is not — it is indistinguishable from calm).

The per-surface vocabularies live with the methods that own the inputs, because only they know
what they read: `forcing.ForcingReason`, `susceptibility.STALE_REASON` /
`susceptibility.no_climatology_reason()` / `susceptibility.NO_GAUGE_REASON`, and the `REASON_*`
strings in `agreement`. :class:`SurfaceReason` here covers what is left over — the cases where a
surface could not be *attempted*, which only the assembler can see.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from cascade_contracts import FloodCategory
from cascade_hydrology.category import CategoryResult, Measure, ThresholdSet, categorize

HAZARD_HORIZON_H = 72


class SurfaceReason:
    """The assembler's UNKNOWN vocabulary: every reason is a function of the missing input.

    Nothing here is a constant string standing in for "not built": each method takes the thing
    that is actually absent and says so, so the sentence a reader sees identifies what would
    have to change for the surface to have a value.
    """

    @staticmethod
    def no_outlet_point(basin_id: str) -> str:
        """The basin names no outlet forecast point, so there is no official forecast to read."""
        return (
            f"{basin_id} has no outlet forecast point configured, so no official river forecast "
            "can be read for it. This is a seed-data gap, not a quiet river."
        )

    @staticmethod
    def agreement_needs_an_outlet(basin_id: str) -> str:
        """Agreement is a comparison at a point; without the point there is nothing to compare."""
        return (
            f"{basin_id} has no outlet forecast point configured, so there is no location at "
            "which an official forecast and an independent model forecast could be compared."
        )

    @staticmethod
    def no_model_probability(why: str) -> str:
        """Why `HazardState.model_probability` is absent beside a known official category.

        The fraction is only ever *counted* model members over an official **flow** threshold
        (docs/DATA_DOCTRINE.md §9(b)). Where the official categories are defined in stage,
        ADR-0011 forbids inventing the flow equivalent, so the fraction is absent and says so
        rather than being replaced by a Cascade-computed likelihood.
        """
        return f"No model exceedance fraction is shown: {why}"

    @staticmethod
    def unexplained(surface: str) -> str:
        """A surface module returned UNKNOWN with no reason — a defect, reported as a defect.

        The assembler will not forward a blank UNKNOWN to a client: without a reason the reader
        cannot tell "we do not know" from "there is nothing happening".
        """
        return (
            f"The {surface} surface reported UNKNOWN without naming a missing input. That is a "
            f"defect in cascade_hydrology.{surface}, not a statement about this basin."
        )


def require_reason(reason: str | None, *, surface: str) -> str:
    """The reason a surface gave, or the defect notice if it gave none. Never an empty UNKNOWN."""
    return reason if reason else SurfaceReason.unexplained(surface)


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
