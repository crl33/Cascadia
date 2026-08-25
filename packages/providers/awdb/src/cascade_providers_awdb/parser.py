"""Strict parsers for the AWDB `stations` and `data` responses.

Uses only the fields the context drivers need; tolerates extras; raises ParseError on a missing
required field. Numbers stay numbers here (AWDB serves JSON numbers, unlike USGS); normalize.py
decides what is usable. The `median` key is treated as OPTIONAL on purpose: AWDB omits it
entirely for some series even when `centralTendencyType=MEDIAN` was requested, and a missing
median must arrive as None so the normalizer can refuse the site instead of dividing by zero.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date


class ParseError(ValueError):
    pass


@dataclass(frozen=True)
class AwdbStation:
    triplet: str
    station_id: str
    name: str
    huc: str | None  # HUC12 as served
    elevation_ft: float | None
    lat: float | None
    lon: float | None
    utc_offset_hours: float | None  # AWDB `dataTimeZone`, e.g. -8.0 (PST, no DST)
    associated_hucs: tuple[str, ...]

    @property
    def huc8(self) -> str | None:
        return self.huc[:8] if self.huc and len(self.huc) >= 8 else None


@dataclass(frozen=True)
class AwdbValue:
    day: date
    value: float | None
    qc_flag: str | None  # V valid, E edit, K estimate, C correction, B back-estimate, X external, S suspect, N no profile
    qa_flag: str | None  # U unknown, R raw, P provisional, A approved
    median: float | None  # absent for some series even when MEDIAN was requested


@dataclass(frozen=True)
class AwdbSeries:
    triplet: str
    element_code: str
    ordinal: int | None
    height_depth: int | None  # inches, negative = below surface (soil probes)
    duration: str
    unit: str | None  # AWDB is English-units only: in, degF, pct
    values: tuple[AwdbValue, ...]


def _req(obj: dict, key: str, ctx: str):
    if not isinstance(obj, dict) or key not in obj:
        raise ParseError(f"missing required field {key!r} in {ctx}")
    return obj[key]


def _float_or_none(raw) -> float | None:
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def parse_stations(content: bytes) -> tuple[AwdbStation, ...]:
    try:
        doc = json.loads(content)
    except (ValueError, UnicodeDecodeError) as e:
        raise ParseError(f"not JSON: {e}") from e
    if not isinstance(doc, list):
        raise ParseError("stations response is not a list")
    out: list[AwdbStation] = []
    for i, station in enumerate(doc):
        ctx = f"stations[{i}]"
        huc = station.get("huc")
        associated = station.get("associatedHucs") or []
        out.append(
            AwdbStation(
                triplet=str(_req(station, "stationTriplet", ctx)),
                station_id=str(station.get("stationId", "")),
                name=str(_req(station, "name", ctx)),
                huc=None if huc is None else str(huc),
                elevation_ft=_float_or_none(station.get("elevation")),
                lat=_float_or_none(station.get("latitude")),
                lon=_float_or_none(station.get("longitude")),
                utc_offset_hours=_float_or_none(station.get("dataTimeZone")),
                associated_hucs=tuple(str(h) for h in associated) if isinstance(associated, list) else (),
            )
        )
    return tuple(out)


def parse_data(content: bytes) -> tuple[AwdbSeries, ...]:
    try:
        doc = json.loads(content)
    except (ValueError, UnicodeDecodeError) as e:
        raise ParseError(f"not JSON: {e}") from e
    if not isinstance(doc, list):
        raise ParseError("data response is not a list")
    out: list[AwdbSeries] = []
    for i, station in enumerate(doc):
        ctx = f"data[{i}]"
        triplet = str(_req(station, "stationTriplet", ctx))
        for j, block in enumerate(_req(station, "data", ctx) or []):
            bctx = f"{ctx}.data[{j}]"
            element = _req(block, "stationElement", bctx)
            values: list[AwdbValue] = []
            for k, value in enumerate(block.get("values") or []):
                vctx = f"{bctx}.values[{k}]"
                raw_day = str(_req(value, "date", vctx))
                try:
                    day = date.fromisoformat(raw_day)
                except ValueError as e:
                    raise ParseError(f"{vctx}: not an ISO date: {raw_day!r}") from e
                values.append(
                    AwdbValue(
                        day=day,
                        value=_float_or_none(value.get("value")),
                        qc_flag=None if value.get("qcFlag") is None else str(value["qcFlag"]),
                        qa_flag=None if value.get("qaFlag") is None else str(value["qaFlag"]),
                        median=_float_or_none(value.get("median")),
                    )
                )
            values.sort(key=lambda v: v.day)
            height = element.get("heightDepth")
            out.append(
                AwdbSeries(
                    triplet=triplet,
                    element_code=str(_req(element, "elementCode", bctx)),
                    ordinal=None if element.get("ordinal") is None else int(element["ordinal"]),
                    height_depth=None if height is None else int(height),
                    duration=str(element.get("durationName", "")),
                    unit=None if element.get("storedUnitCode") is None else str(element["storedUnitCode"]),
                    values=tuple(values),
                )
            )
    return tuple(out)
