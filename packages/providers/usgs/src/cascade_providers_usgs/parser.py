"""Strict parser for NWIS IV JSON (WaterML-ish).

`parse_iv`, `IvSeries` and `IvValue` are RETIRED FROM PRODUCTION (2026-08-27) and exist only for
the transport comparator — see `client.py`. `VARIABLE_BY_CODE` and `ParseError` are NOT retired:
`ogc_parser.py` imports both, so the two transports agree on which parameter codes matter and
raise the same error type.

Original notes: Uses only the fields we need; tolerates extras;
raises ParseError on a missing required field. Values stay strings here; normalize.py decides
sentinel/number. Timestamps are parsed WITH their offset (e.g. -07:00 PDT / -08:00 PST)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime

from cascade_core.timeutils import parse_iso
from cascade_core.units import normalize_unit

VARIABLE_BY_CODE = {"00065": "stage", "00060": "flow"}


class ParseError(ValueError):
    pass


@dataclass(frozen=True)
class IvValue:
    time: datetime  # aware UTC
    raw_value: str
    qualifiers: tuple[str, ...]


@dataclass(frozen=True)
class IvSeries:
    site: str
    site_name: str
    variable: str  # stage | flow
    variable_code: str
    unit: str  # registry spelling: ft | cfs
    no_data_value: float | None
    values: tuple[IvValue, ...]


def _req(obj: dict, key: str, ctx: str):
    if not isinstance(obj, dict) or key not in obj:
        raise ParseError(f"missing required field {key!r} in {ctx}")
    return obj[key]


def parse_iv(content: bytes) -> list[IvSeries]:
    try:
        doc = json.loads(content)
    except (ValueError, UnicodeDecodeError) as e:
        raise ParseError(f"not JSON: {e}") from e
    value = _req(doc, "value", "document")
    series_list = _req(value, "timeSeries", "value")
    if not isinstance(series_list, list):
        raise ParseError("value.timeSeries is not a list")
    out: list[IvSeries] = []
    for i, ts in enumerate(series_list):
        ctx = f"timeSeries[{i}]"
        source = _req(ts, "sourceInfo", ctx)
        site_codes = _req(source, "siteCode", ctx)
        if not site_codes:
            raise ParseError(f"{ctx}: empty siteCode")
        site = str(_req(site_codes[0], "value", ctx))
        variable = _req(ts, "variable", ctx)
        codes = _req(variable, "variableCode", ctx)
        if not codes:
            raise ParseError(f"{ctx}: empty variableCode")
        code = str(_req(codes[0], "value", ctx))
        if code not in VARIABLE_BY_CODE:
            continue  # other parameters are ignored by design
        unit = normalize_unit(str(_req(_req(variable, "unit", ctx), "unitCode", ctx)))
        ndv_raw = variable.get("noDataValue")
        no_data = float(ndv_raw) if isinstance(ndv_raw, (int, float)) else None
        values: list[IvValue] = []
        for block in _req(ts, "values", ctx):
            for v in _req(block, "value", ctx):
                t = parse_iso(str(_req(v, "dateTime", ctx)))
                q = v.get("qualifiers", [])
                values.append(IvValue(time=t, raw_value=str(_req(v, "value", ctx)), qualifiers=tuple(str(x) for x in q)))
        values.sort(key=lambda x: x.time)  # by aware datetime, never by string
        out.append(
            IvSeries(
                site=site,
                site_name=str(source.get("siteName", "")),
                variable=VARIABLE_BY_CODE[code],
                variable_code=code,
                unit=unit,
                no_data_value=no_data,
                values=tuple(values),
            )
        )
    return out
