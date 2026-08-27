"""IvSeries -> Observation records.

`to_observations` is RETIRED FROM PRODUCTION (2026-08-27) and exists only for the transport
comparator — see `client.py`. `ObservationRecord` and `QUALIFIER_FLAGS` are NOT retired:
`ogc_normalize.py` builds the same record type and extends the same quality vocabulary, which is
exactly why the two transports produce comparable rows.

Original notes: Sentinels (provider-declared noDataValue) and unparseable
strings become `value=None` with a quality flag; qualifiers are preserved both mapped
(P->provisional, A->approved, e->estimated, Ice, Eqp) and raw. Unit is the registry spelling;
flow arrives as ft3/s and is recorded as `cfs` (same quantity, explicit spelling)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

from cascade_core.timeutils import available_at
from cascade_providers_usgs.parser import IvSeries

QUALIFIER_FLAGS = {"P": "provisional", "A": "approved", "e": "estimated", "E": "estimated", "Ice": "ice", "Eqp": "equipment", "Ssn": "seasonal", "Dis": "discontinued", "***": "suspect"}


@dataclass(frozen=True)
class ObservationRecord:
    station_id: str
    variable: str
    value: float | None
    unit: str
    datum: str | None
    valid_time: datetime
    retrieved_at: datetime
    available_at: datetime
    quality: tuple[str, ...]
    qualifier_raw: str | None


def _number(raw: str, no_data: float | None) -> tuple[float | None, tuple[str, ...]]:
    try:
        x = float(raw)
    except (TypeError, ValueError):
        return None, ("unparseable",)
    if not math.isfinite(x):
        return None, ("unparseable",)
    if no_data is not None and x == no_data:
        return None, ("sentinel",)
    return x, ()


def to_observations(series: IvSeries, *, retrieved_at: datetime, station_id: str, datum: str | None) -> list[ObservationRecord]:
    out: list[ObservationRecord] = []
    for v in series.values:
        value, flags = _number(v.raw_value, series.no_data_value)
        quality = list(flags)
        for q in v.qualifiers:
            quality.append(QUALIFIER_FLAGS.get(q, q))
        if value is not None and series.variable == "flow" and value < 0:
            quality.append("out_of_range")
        out.append(
            ObservationRecord(
                station_id=station_id,
                variable=series.variable,
                value=value,
                unit=series.unit,
                datum=datum if series.variable == "stage" else None,
                valid_time=v.time,
                retrieved_at=retrieved_at,
                available_at=available_at(valid_time=v.time, retrieved_at=retrieved_at),
                quality=tuple(dict.fromkeys(quality)),
                qualifier_raw=",".join(v.qualifiers) or None,
            )
        )
    return out
