"""Strict parsers for NWPS /gauges/{lid} and /gauges/{lid}/stageflow.

Gauge: name, usgsId, reachId, upstream/downstream LIDs, rfc/wfo, vertical datums (first listed
is the primary gauge-zero datum), flood.categories with BOTH stage and flow (the -9999 sentinel
becomes None), historic crests retained raw. Stageflow: observed and forecast series with
issuedTime, pedts, primary/secondary names and units; -9999 values become None.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime

from cascade_core.timeutils import parse_iso
from cascade_core.units import normalize_unit

NWPS_SENTINEL = -9999.0
CATEGORIES = ("action", "minor", "moderate", "major")


class ParseError(ValueError):
    pass


def _req(obj, key: str, ctx: str):
    if not isinstance(obj, dict) or key not in obj:
        raise ParseError(f"missing required field {key!r} in {ctx}")
    return obj[key]


def _num(x, ctx: str) -> float | None:
    """Number or None (sentinel / null). Strings where numbers are expected are a parse error."""
    if x is None:
        return None
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ParseError(f"{ctx}: expected number, got {type(x).__name__}")
    if float(x) == NWPS_SENTINEL or x != x:  # -9999 or NaN
        return None
    return float(x)


@dataclass(frozen=True)
class CategoryValues:
    stage: float | None
    flow: float | None


@dataclass(frozen=True)
class GaugeRecord:
    lid: str
    name: str
    usgs_id: str | None
    reach_id: str | None
    upstream_lid: str | None
    downstream_lid: str | None
    rfc: str | None
    wfo: str | None
    datum: str | None  # primary vertical datum abbreviation
    datums: tuple[str, ...]
    stage_units: str
    flow_units: str
    categories: dict[str, CategoryValues]
    crests_historic: tuple[dict, ...]
    in_service: bool
    lon: float | None
    lat: float | None


def parse_gauge(content: bytes) -> GaugeRecord:
    try:
        g = json.loads(content)
    except (ValueError, UnicodeDecodeError) as e:
        raise ParseError(f"not JSON: {e}") from e
    lid = str(_req(g, "lid", "gauge"))
    flood = _req(g, "flood", "gauge")
    cats_raw = _req(flood, "categories", "gauge.flood")
    categories: dict[str, CategoryValues] = {}
    for cat in CATEGORIES:
        c = _req(cats_raw, cat, "gauge.flood.categories")
        categories[cat] = CategoryValues(stage=_num(c.get("stage"), f"{cat}.stage"), flow=_num(c.get("flow"), f"{cat}.flow"))
    datums_block = g.get("datums") or {}
    vertical = ((datums_block.get("vertical") or {}).get("value")) or []
    datums = tuple(str(d.get("abbrev")) for d in vertical if d.get("abbrev"))
    rfc = (g.get("rfc") or {}).get("abbreviation") if isinstance(g.get("rfc"), dict) else None
    wfo = (g.get("wfo") or {}).get("abbreviation") if isinstance(g.get("wfo"), dict) else None
    crests = ((flood.get("crests") or {}).get("historic")) or []
    in_service = bool(((g.get("inService") or {}).get("enabled", True)))
    return GaugeRecord(
        lid=lid,
        name=str(g.get("name", lid)),
        usgs_id=(str(g["usgsId"]) if g.get("usgsId") else None),
        reach_id=(str(g["reachId"]) if g.get("reachId") else None),
        upstream_lid=(str(g["upstreamLid"]) if g.get("upstreamLid") else None),
        downstream_lid=(str(g["downstreamLid"]) if g.get("downstreamLid") else None),
        rfc=rfc,
        wfo=wfo,
        datum=datums[0] if datums else None,
        datums=datums,
        stage_units=normalize_unit(str(_req(flood, "stageUnits", "gauge.flood"))),
        flow_units=normalize_unit(str(_req(flood, "flowUnits", "gauge.flood"))),
        categories=categories,
        crests_historic=tuple(dict(c) for c in crests if isinstance(c, dict)),
        in_service=in_service,
        lon=_num(g.get("longitude"), "longitude"),
        lat=_num(g.get("latitude"), "latitude"),
    )


@dataclass(frozen=True)
class SeriesPoint:
    valid_time: datetime
    generated_time: datetime | None
    primary: float | None
    secondary: float | None


@dataclass(frozen=True)
class StageFlowSeries:
    pedts: str | None
    issued_time: datetime | None
    primary_name: str  # Stage | Flow | River Discharge ...
    primary_units: str  # registry spelling (ft | kcfs | cfs)
    secondary_name: str | None
    secondary_units: str | None
    points: tuple[SeriesPoint, ...]

    @property
    def primary_variable(self) -> str:
        return "stage" if self.primary_name.lower().startswith("stage") else "flow"


@dataclass(frozen=True)
class StageFlow:
    observed: StageFlowSeries | None
    forecast: StageFlowSeries | None


def _series(block, ctx: str) -> StageFlowSeries | None:
    if not isinstance(block, dict) or not block.get("data"):
        return None
    issued = block.get("issuedTime")
    pts = []
    for i, p in enumerate(_req(block, "data", ctx)):
        gen = p.get("generatedTime")
        pts.append(
            SeriesPoint(
                valid_time=parse_iso(str(_req(p, "validTime", f"{ctx}.data[{i}]"))),
                generated_time=parse_iso(str(gen)) if gen else None,
                primary=_num(p.get("primary"), f"{ctx}.data[{i}].primary"),
                secondary=_num(p.get("secondary"), f"{ctx}.data[{i}].secondary"),
            )
        )
    pts.sort(key=lambda p: p.valid_time)
    sec_units = block.get("secondaryUnits")
    return StageFlowSeries(
        pedts=block.get("pedts"),
        issued_time=parse_iso(str(issued)) if issued else None,
        primary_name=str(_req(block, "primaryName", ctx)),
        primary_units=normalize_unit(str(_req(block, "primaryUnits", ctx))),
        secondary_name=block.get("secondaryName"),
        secondary_units=normalize_unit(str(sec_units)) if sec_units else None,
        points=tuple(pts),
    )


def parse_stageflow(content: bytes) -> StageFlow:
    try:
        doc = json.loads(content)
    except (ValueError, UnicodeDecodeError) as e:
        raise ParseError(f"not JSON: {e}") from e
    if not isinstance(doc, dict):
        raise ParseError("stageflow document is not an object")
    return StageFlow(observed=_series(doc.get("observed"), "observed"), forecast=_series(doc.get("forecast"), "forecast"))
