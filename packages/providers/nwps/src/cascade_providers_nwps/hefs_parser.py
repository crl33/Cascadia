"""Strict parsers for the three HEFS payloads. Values stay strings until the number decision.

Every shape assertion here was measured against real bytes on 2026-08-27 and is checked in under
`tests/fixtures/providers/nwps_hefs/`. The API is documented by its own operators as experimental
and subject to change without notice, which is exactly why these parsers refuse rather than adapt:
a silently changed shape must fail a job, not quietly produce a thinner ensemble.

Two knowledge-time facts the rest of the platform depends on, and which this module is the only
place to get right (DATA_DOCTRINE §3, ADR-0010):

- ``forecast_datetime`` is the model cycle          -> ``issued_at``
- ``creation_datetime`` is when NWS published it    -> ``available_at``

They differ by 3-4 hours in practice. Inferring one from the other would put knowledge in the
system before the provider had it, which is precisely the look-ahead bias the replay audit exists
to catch.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime

from cascade_providers_nwps.reaches_parser import ParseError

#: The step every seed location serves (FACT: `time_step_multiplier` "21600", unit "second").
#: Read from the payload rather than assumed; this is only the sanity bound.
MAX_STEP_SECONDS = 24 * 3600

__all__ = [
    "HefsEnsemble",
    "HefsHeader",
    "HefsMember",
    "HefsQuantiles",
    "parse_ensembles",
    "parse_headers",
    "parse_quantiles",
]


@dataclass(frozen=True)
class HefsHeader:
    """One retained cycle at one location — what `headers/` advertises."""

    location_id: str
    parameter_id: str
    ensemble_id: str
    forecast_datetime: datetime  # the model cycle -> issued_at
    creation_datetime: datetime  # when NWS published it -> available_at
    units: str
    step_seconds: int
    station_name: str | None


@dataclass(frozen=True)
class HefsMember:
    """One ensemble trace. `index` is a WEATHER YEAR (1981..2025), not a member number."""

    index: int
    values: tuple[tuple[datetime, float | None], ...]


@dataclass(frozen=True)
class HefsEnsemble:
    header: HefsHeader
    members: tuple[HefsMember, ...]


@dataclass(frozen=True)
class HefsQuantiles:
    """The provider's OWN exceedance quantiles — official guidance, never Cascade-derived."""

    location_id: str
    parameter_id: str
    forecast_datetime: datetime | None
    creation_datetime: datetime | None
    units: str | None
    levels: tuple[float, ...]
    #: (valid_time, values-in-level-order, max, min)
    rows: tuple[tuple[datetime, tuple[float | None, ...], float | None, float | None], ...]


def _doc(content: bytes, what: str):
    try:
        return json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise ParseError(f"not JSON {what}: {e}") from e


def _req(obj: dict, key: str, ctx: str):
    if not isinstance(obj, dict) or key not in obj:
        raise ParseError(f"missing required field {key!r} in {ctx}")
    return obj[key]


def _instant(raw, ctx: str) -> datetime:
    """`2026-08-27T12:00:00Z` -> aware UTC. A naive result would be a silent local-time bug."""
    try:
        when = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError as e:
        raise ParseError(f"{ctx}: {raw!r} is not an ISO instant") from e
    if when.tzinfo is None:
        raise ParseError(f"{ctx}: {raw!r} carries no offset; refusing to assume UTC")
    return when.astimezone(UTC)


def _header(row: dict, ctx: str) -> HefsHeader:
    step = _req(row, "time_step_multiplier", ctx)
    unit = _req(row, "time_step_unit", ctx)
    if str(unit) != "second":
        raise ParseError(f"{ctx}: unexpected time_step_unit {unit!r}; only 'second' is understood")
    try:
        step_s = int(step)
    except (TypeError, ValueError) as e:
        raise ParseError(f"{ctx}: time_step_multiplier {step!r} is not an integer") from e
    if not 0 < step_s <= MAX_STEP_SECONDS:
        raise ParseError(f"{ctx}: implausible time step {step_s} s")
    return HefsHeader(
        location_id=str(_req(row, "location_id", ctx)),
        parameter_id=str(_req(row, "parameter_id", ctx)),
        ensemble_id=str(_req(row, "ensemble_id", ctx)),
        forecast_datetime=_instant(_req(row, "forecast_datetime", ctx), f"{ctx} forecast_datetime"),
        creation_datetime=_instant(_req(row, "creation_datetime", ctx), f"{ctx} creation_datetime"),
        units=str(_req(row, "units", ctx)),
        step_seconds=step_s,
        station_name=row.get("station_name"),
    )


def parse_headers(content: bytes) -> tuple[HefsHeader, ...]:
    """The retained cycles. An EMPTY list is a legitimate answer, not an error.

    An unknown location answers HTTP 200 with `[]` rather than 404 (FACT, checked in as
    `headers_unknown_location.json`). Raising here would make a quiet location look like an
    outage; returning `()` lets the caller say "nothing to collect" and move on.
    """
    doc = _doc(content, "HEFS headers")
    if not isinstance(doc, list):
        raise ParseError(f"HEFS headers must be a JSON list, got {type(doc).__name__}")
    return tuple(_header(row, f"header {i}") for i, row in enumerate(doc))


def parse_ensembles(content: bytes) -> tuple[HefsEnsemble, ...]:
    """`[[member, member, ...]]` — a list of cycles, each a list of members.

    The doubly-nested shape is the provider's, not a mistake: one query may match several cycles,
    and each match carries its whole member set.
    """
    doc = _doc(content, "HEFS ensembles")
    if not isinstance(doc, list):
        raise ParseError(f"HEFS ensembles must be a JSON list, got {type(doc).__name__}")
    out: list[HefsEnsemble] = []
    for i, group in enumerate(doc):
        if not isinstance(group, list):
            raise ParseError(f"ensemble group {i} must be a list of members, got {type(group).__name__}")
        if not group:
            continue
        members: list[HefsMember] = []
        headers = set()
        for j, row in enumerate(group):
            ctx = f"ensemble {i} member {j}"
            head = _header(row, ctx)
            headers.add((head.location_id, head.forecast_datetime, head.ensemble_id, head.units))
            raw_index = _req(row, "ensemble_member_index", ctx)
            try:
                index = int(raw_index)
            except (TypeError, ValueError) as e:
                raise ParseError(f"{ctx}: ensemble_member_index {raw_index!r} is not an integer") from e
            events = _req(row, "events", ctx)
            if not isinstance(events, list):
                raise ParseError(f"{ctx}: events must be a list, got {type(events).__name__}")
            miss = row.get("miss_val")
            values: list[tuple[datetime, float | None]] = []
            for k, ev in enumerate(events):
                ectx = f"{ctx} event {k}"
                when = _instant(_req(ev, "valid_datetime", ectx), ectx)
                raw = _req(ev, "value", ectx)
                values.append((when, _value(raw, miss, ectx)))
            members.append(HefsMember(index=index, values=tuple(values)))
        if len(headers) != 1:
            raise ParseError(
                f"ensemble group {i} mixes cycles/locations {sorted(map(str, headers))}; refusing to "
                "store members that do not belong to one forecast"
            )
        out.append(HefsEnsemble(header=_header(group[0], f"ensemble {i} member 0"), members=tuple(members)))
    return tuple(out)


def _value(raw, miss_val, ctx: str) -> float | None:
    """A missing value is None, never a number. `miss_val` is the provider's own sentinel."""
    if raw is None:
        return None
    if miss_val is not None and str(raw) == str(miss_val):
        return None
    try:
        number = float(raw)
    except (TypeError, ValueError) as e:
        raise ParseError(f"{ctx}: value {raw!r} is not a number") from e
    if number != number or number in (float("inf"), float("-inf")):
        raise ParseError(f"{ctx}: value {raw!r} is not finite")
    return number


def parse_quantiles(content: bytes) -> HefsQuantiles:
    """`{metadata, value_set}` — the published exceedance quantiles for the latest cycle."""
    doc = _doc(content, "HEFS quantiles")
    if not isinstance(doc, dict):
        raise ParseError(f"HEFS quantiles must be a JSON object, got {type(doc).__name__}")
    meta = _req(doc, "metadata", "HEFS quantiles")
    rows_in = _req(doc, "value_set", "HEFS quantiles")
    if not isinstance(rows_in, list):
        raise ParseError("HEFS quantiles value_set must be a list")
    levels_raw = meta.get("exceedance_quantiles") or ()
    try:
        levels = tuple(float(x) for x in levels_raw)
    except (TypeError, ValueError) as e:
        raise ParseError(f"exceedance_quantiles {levels_raw!r} are not numbers") from e
    if not levels:
        raise ParseError("HEFS quantiles carry no exceedance_quantiles; the values would be unlabelled")
    rows = []
    for i, row in enumerate(rows_in):
        ctx = f"quantile row {i}"
        when = _instant(_req(row, "valid_datetime", ctx), ctx)
        vals = _req(row, "quantile_values", ctx)
        if not isinstance(vals, list) or len(vals) != len(levels):
            raise ParseError(
                f"{ctx}: {len(vals) if isinstance(vals, list) else '?'} values for {len(levels)} "
                "exceedance levels; a zip here would mislabel every quantile"
            )
        rows.append(
            (
                when,
                tuple(_value(v, None, f"{ctx} value {j}") for j, v in enumerate(vals)),
                _value(row.get("max_value"), None, f"{ctx} max"),
                _value(row.get("min_value"), None, f"{ctx} min"),
            )
        )
    fdt = meta.get("forecast_datetime")
    cdt = meta.get("creation_datetime")
    return HefsQuantiles(
        location_id=str(_req(meta, "location_id", "HEFS quantiles metadata")),
        parameter_id=str(meta.get("parameter_id") or ""),
        forecast_datetime=_instant(fdt, "quantiles forecast_datetime") if fdt else None,
        creation_datetime=_instant(cdt, "quantiles creation_datetime") if cdt else None,
        units=meta.get("units"),
        levels=levels,
        rows=tuple(rows),
    )
