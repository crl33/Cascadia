"""Gauge -> Threshold records (basis stage when stage values exist, else flow in cfs; stage rows
carry the datum). Stageflow forecast -> ForecastRun/ForecastValue records with flow converted
kcfs -> cfs explicitly (ADR-0009) and stage left in ft."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from cascade_core.timeutils import available_at
from cascade_core.units import convert
from cascade_providers_nwps.parser import CATEGORIES, GaugeRecord, StageFlowSeries


class NormalizeError(ValueError):
    pass


@dataclass(frozen=True)
class ThresholdRecord:
    category: str
    value: float
    unit: str
    basis: str
    datum: str | None


def thresholds_from_gauge(g: GaugeRecord) -> list[ThresholdRecord]:
    """Official categories only. Basis = stage if any stage value exists, else flow; both absent => []."""
    has_stage = any(c.stage is not None for c in g.categories.values())
    has_flow = any(c.flow is not None for c in g.categories.values())
    if has_stage:
        if g.datum is None:
            raise NormalizeError(f"{g.lid}: stage thresholds without a vertical datum are not storable (ADR-0009)")
        return [ThresholdRecord(cat, c.stage, g.stage_units, "stage", g.datum) for cat in CATEGORIES if (c := g.categories[cat]).stage is not None]
    if has_flow:
        return [ThresholdRecord(cat, convert(c.flow, g.flow_units, "cfs"), "cfs", "flow", None) for cat in CATEGORIES if (c := g.categories[cat]).flow is not None]
    return []


@dataclass(frozen=True)
class ForecastPointValue:
    valid_time: datetime
    stage: float | None  # ft
    flow: float | None  # cfs


@dataclass(frozen=True)
class ForecastRunRecord:
    issued_at: datetime
    retrieved_at: datetime
    available_at: datetime
    issuer: str
    primary_variable: str
    unit: str
    stage_unit: str | None
    flow_unit: str | None
    datum: str | None
    values: tuple[ForecastPointValue, ...]


def _split(series: StageFlowSeries) -> tuple[str | None, str | None]:
    """Return (stage_unit, flow_unit) in provider spelling by looking at names/units."""
    if series.primary_variable == "stage":
        return series.primary_units, series.secondary_units
    return series.secondary_units, series.primary_units


def forecast_from_stageflow(series: StageFlowSeries | None, *, retrieved_at: datetime, issuer: str, datum: str | None) -> ForecastRunRecord | None:
    if series is None or not series.points:
        return None
    if series.issued_time is None:
        raise NormalizeError("forecast series without issuedTime cannot be stored as a run")
    stage_unit, flow_unit_in = _split(series)
    if stage_unit is not None and stage_unit != "ft":
        raise NormalizeError(f"unexpected stage unit {stage_unit!r}")
    values = []
    for p in series.points:
        stage_v, flow_v = (p.primary, p.secondary) if series.primary_variable == "stage" else (p.secondary, p.primary)
        flow_cfs = None if flow_v is None or flow_unit_in is None else convert(flow_v, flow_unit_in, "cfs")
        values.append(ForecastPointValue(valid_time=p.valid_time, stage=stage_v, flow=flow_cfs))
    primary = series.primary_variable
    return ForecastRunRecord(
        issued_at=series.issued_time,
        retrieved_at=retrieved_at,
        available_at=available_at(valid_time=series.issued_time, retrieved_at=retrieved_at, issued_at=series.issued_time),
        issuer=issuer,
        primary_variable=primary,
        unit="ft" if primary == "stage" else "cfs",
        stage_unit="ft" if stage_unit is not None else None,
        flow_unit="cfs" if flow_unit_in is not None else None,
        datum=datum if stage_unit is not None else None,
        values=tuple(values),
    )
