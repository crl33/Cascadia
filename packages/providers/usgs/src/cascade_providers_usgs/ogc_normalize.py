"""OgcValue -> ObservationRecord for the Event Zero backfill (ADR-0010 bitemporal honesty).

Every record's quality carries 'backfilled': these rows are written months after their valid
times, and available_at = retrieved_at (the existing timeutils.available_at already produces
this for historical data — max(valid_time, retrieved_at)). approval_status is preserved both
mapped ('Approved'->approved, 'Provisional'->provisional) and verbatim in qualifier_raw, which
keeps the EVENT_ZERO §3 A/P audit trail without inventing NWIS letter codes. Unparseable or
null values become value=None + 'unparseable'; negative flow -> 'out_of_range' (mirror
normalize.py). Non-instantaneous statistics (statistic_id != 00011) are a different product:
skipped and counted, never stored."""

from __future__ import annotations

import math
from collections.abc import Iterable
from datetime import datetime

from cascade_core.timeutils import available_at
from cascade_providers_usgs.normalize import QUALIFIER_FLAGS, ObservationRecord
from cascade_providers_usgs.ogc_parser import OgcValue

APPROVAL_FLAGS = {"Approved": "approved", "Provisional": "provisional"}
# The OGC API spells qualifiers in caps ("ESTIMATED" observed Dec 2025, site 12149000);
# map only observed spellings onto the established quality vocabulary, keep the rest verbatim.
OGC_QUALIFIER_FLAGS = {**QUALIFIER_FLAGS, "ESTIMATED": "estimated"}
INSTANTANEOUS_STATISTIC = "00011"
BACKFILLED_FLAG = "backfilled"


def _number(raw: str | None) -> tuple[float | None, tuple[str, ...]]:
    try:
        x = float(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None, ("unparseable",)
    if not math.isfinite(x):
        return None, ("unparseable",)
    return x, ()


def to_observation_records(
    values: Iterable[OgcValue],
    *,
    retrieved_at: datetime,
    station_id: str,
    datum: str | None,
) -> tuple[list[ObservationRecord], dict[str, int]]:
    """Normalize one page's values for one station. Returns (records, skip counts)."""
    out: list[ObservationRecord] = []
    skipped = {"non_instantaneous": 0}
    for v in values:
        if v.statistic_id is not None and v.statistic_id != INSTANTANEOUS_STATISTIC:
            skipped["non_instantaneous"] += 1
            continue
        value, flags = _number(v.raw_value)
        quality = list(flags)
        if v.approval_status is not None:
            quality.append(APPROVAL_FLAGS.get(v.approval_status, v.approval_status))
        for q in v.qualifiers:
            quality.append(OGC_QUALIFIER_FLAGS.get(q, q))
        if value is not None and v.variable == "flow" and value < 0:
            quality.append("out_of_range")
        quality.append(BACKFILLED_FLAG)  # always, for this adapter: rows written long after valid time
        raw_bits = ([] if v.approval_status is None else [v.approval_status]) + list(v.qualifiers)
        out.append(
            ObservationRecord(
                station_id=station_id,
                variable=v.variable,
                value=value,
                unit=v.unit,
                datum=datum if v.variable == "stage" else None,
                valid_time=v.time,
                retrieved_at=retrieved_at,
                available_at=available_at(valid_time=v.time, retrieved_at=retrieved_at),
                quality=tuple(dict.fromkeys(quality)),
                qualifier_raw=",".join(raw_bits) or None,
            )
        )
    out.sort(key=lambda r: (r.variable, r.valid_time))
    return out, skipped
