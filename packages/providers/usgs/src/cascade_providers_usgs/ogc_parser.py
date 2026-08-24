"""Strict parser for the OGC API `continuous` items page (GeoJSON FeatureCollection).

Uses only the fields we need; tolerates extras; raises ParseError on a missing required field.
Values stay strings here (the API serves them as strings); ogc_normalize.py decides number vs
quality flag. Timestamps are parsed WITH their offset. Parameter codes outside stage/flow are
ignored by design (mirror of parser.parse_iv)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime

from cascade_core.timeutils import parse_iso
from cascade_core.units import normalize_unit
from cascade_providers_usgs.parser import VARIABLE_BY_CODE, ParseError


@dataclass(frozen=True)
class OgcValue:
    site: str  # bare site number, "USGS-" prefix stripped
    variable: str  # stage | flow
    parameter_code: str
    statistic_id: str | None  # "00011" = instantaneous
    time: datetime  # aware UTC
    raw_value: str | None  # None when the API serves null
    unit: str  # registry spelling: ft | cfs
    approval_status: str | None  # verbatim: "Approved" | "Provisional" | ...
    qualifiers: tuple[str, ...]


@dataclass(frozen=True)
class OgcPage:
    values: tuple[OgcValue, ...]
    next_url: str | None
    number_returned: int


def _req(obj: dict, key: str, ctx: str):
    if not isinstance(obj, dict) or key not in obj:
        raise ParseError(f"missing required field {key!r} in {ctx}")
    return obj[key]


def parse_continuous(content: bytes) -> OgcPage:
    try:
        doc = json.loads(content)
    except (ValueError, UnicodeDecodeError) as e:
        raise ParseError(f"not JSON: {e}") from e
    features = _req(doc, "features", "document")
    if not isinstance(features, list):
        raise ParseError("features is not a list")
    next_url: str | None = None
    links = doc.get("links", [])
    if isinstance(links, list):
        for link in links:
            if isinstance(link, dict) and link.get("rel") == "next" and isinstance(link.get("href"), str):
                next_url = link["href"]
                break
    out: list[OgcValue] = []
    for i, feature in enumerate(features):
        ctx = f"features[{i}]"
        props = _req(feature, "properties", ctx)
        code = str(_req(props, "parameter_code", ctx))
        if code not in VARIABLE_BY_CODE:
            continue  # other parameters are ignored by design
        loc = str(_req(props, "monitoring_location_id", ctx))
        site = loc.removeprefix("USGS-")
        time = parse_iso(str(_req(props, "time", ctx)))
        raw = _req(props, "value", ctx)  # key must exist; null is a legal value
        unit = normalize_unit(str(_req(props, "unit_of_measure", ctx)))
        approval = _req(props, "approval_status", ctx)
        qualifier = props.get("qualifier")
        if qualifier is None:
            qualifiers: tuple[str, ...] = ()
        elif isinstance(qualifier, list):
            qualifiers = tuple(str(q) for q in qualifier)
        else:
            qualifiers = (str(qualifier),)
        statistic = props.get("statistic_id")
        out.append(
            OgcValue(
                site=site,
                variable=VARIABLE_BY_CODE[code],
                parameter_code=code,
                statistic_id=None if statistic is None else str(statistic),
                time=time,
                raw_value=None if raw is None else str(raw),
                unit=unit,
                approval_status=None if approval is None else str(approval),
                qualifiers=qualifiers,
            )
        )
    nr = doc.get("numberReturned")
    return OgcPage(values=tuple(out), next_url=next_url, number_returned=nr if isinstance(nr, int) else len(features))
