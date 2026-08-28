"""Antecedent precipitation: how much rain a basin has ALREADY had, summed honestly.

Reads the stored hourly MRMS basin means (``basin_qpe_01h``) through the knowledge clock and
sums them over trailing windows. Three rules keep the arithmetic honest:

- **The window ends at the newest observed hour, not the wall clock.** The radar-gauge product
  reaches the archive ~an hour after the fact (measured 57 min), so a wall-clock window would
  report every recent hour as missing on a perfectly healthy feed. ``window_end`` names the
  anchor so nobody has to guess.
- **A partial window is a KNOWN UNDERESTIMATE, never an estimate.** The total is the sum of
  exactly the hours that exist; missing hours are counted and said out loud in ``reason``.
  Scaling the sum up to "fill" a gap would be a fabricated number wearing an observed truth
  class.
- **An hour whose own coverage was refused is an absent hour.** The MRMS job stores value=None
  when the valid fraction fails its floor; that row proves the hour was LOOKED AT, but it
  contributes nothing to a sum.

This module never imports a provider adapter (import contract). The feature and method names
are shared *data*: ``tests/unit/test_antecedent.py`` pins them to the constants the MRMS job
writes, so a drift fails a test rather than silently reading nothing.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Sequence

from cascade_contracts.common import Quantity, TruthClass
from cascade_contracts.visualization import AntecedentPrecip

if TYPE_CHECKING:
    from cascade_core.models import DerivedFeature

#: Written by the MRMS provider job (cascade_providers_mrms.jobs.FEATURE_QPE); pinned by test.
FEATURE_QPE_01H = "basin_qpe_01h"
METHOD_QPE = "method:basin-qpe@1.0.0"
#: 6 h answers "is it raining hard right now", 24 h the storm, 72 h the wet-up — the AR-event
#: duration scales of docs/HYDROLOGY.md §2 (the regime section). Nothing here scores or fuses.
WINDOWS_H = (6, 24, 72)
#: Widest window plus the measured archive lag, rounded up: how far back the reader must ask.
LOOKBACK = timedelta(hours=max(WINDOWS_H) + 2)


def antecedent_ref_key(basin_id: str) -> str:
    return f"qpe-antecedent-{basin_id.split(':', 1)[-1]}"


@dataclass(frozen=True)
class AntecedentAssessment:
    entries: tuple[AntecedentPrecip, ...]
    #: The newest hourly row, for the ProvenanceRef the entries' `prov` must resolve to;
    #: None exactly when no row is known — the caller then registers an UNKNOWN/MISSING ref
    #: under the same key (the no-forecast pattern), never a dangling one.
    newest: DerivedFeature | None


def assess_antecedent(rows: Sequence[DerivedFeature], *, ref_key: str) -> AntecedentAssessment:
    """Sum hourly basin-mean QPE over each window, ending at the newest known hour.

    ``rows`` are the last-known row per valid_time, ascending — exactly what
    ``derived_features(..., latest_per_valid_time=True)`` returns for ``basin_qpe_01h``.
    """
    if not rows:
        return AntecedentAssessment(
            entries=tuple(
                AntecedentPrecip(
                    window_h=w,
                    window_end=None,
                    total=None,
                    hours_present=0,
                    hours_expected=w,
                    truth=TruthClass.OBSERVATION,
                    prov=ref_key,
                    reason="no observed QPE hour is known at this knowledge time",
                )
                for w in WINDOWS_H
            ),
            newest=None,
        )
    newest = rows[-1]
    t_end: datetime = newest.valid_time
    entries: list[AntecedentPrecip] = []
    for w in WINDOWS_H:
        t_lo = t_end - timedelta(hours=w)
        in_window = [r for r in rows if t_lo < r.valid_time <= t_end]
        present = [r for r in in_window if r.value is not None]
        refused = len(in_window) - len(present)
        missing = w - len(present)
        if present:
            total = Quantity(value=round(sum(r.value for r in present), 3), unit="mm")
            reason = None
            if missing > 0:
                parts = [f"{missing} of {w} hours missing at this knowledge time"]
                if refused:
                    parts.append(f"{refused} of them looked at but refused for coverage")
                reason = "; ".join(parts) + " — the total covers only the hours that exist"
        else:
            total = None
            reason = (
                "every hour in the window was looked at and refused for coverage"
                if refused == len(in_window) and refused > 0
                else f"no QPE hour inside the trailing {w} h is known at this knowledge time"
            )
        entries.append(
            AntecedentPrecip(
                window_h=w,
                window_end=t_end,
                total=total,
                hours_present=len(present),
                hours_expected=w,
                truth=TruthClass.OBSERVATION,
                prov=ref_key,
                reason=reason,
            )
        )
    return AntecedentAssessment(entries=tuple(entries), newest=newest)
