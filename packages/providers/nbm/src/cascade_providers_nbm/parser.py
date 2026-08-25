"""Strict GRIB2 parse of an NBM subset: message framing here, field decoding via eccodes.

Two layers, deliberately:

- **Framing** (:func:`split_messages`) is pure Python over the GRIB2 envelope: the ``GRIB``
  magic, edition 2, the 64-bit total length in Section 0 and the ``7777`` trailer. It runs
  without the ``grib`` extra installed, and it is what turns a truncated download or an HTML
  error page served with HTTP 200 into a typed :class:`NbmParseError` before any native
  library sees the bytes.
- **Decoding** (:func:`decode`) uses ``eccodes``, imported lazily so this module — and the
  package — import cleanly in the API image, which never decodes a grid.

**Fields are identified by GRIB numbers, never by name.** ``SNOWLVL`` is an NCEP local-table
parameter that eccodes 2.48 reports as ``shortName='unknown'`` with ``units='unknown'``
(verified). Matching on a name would silently select nothing the day a local table is added,
so selection is on ``(discipline, parameterCategory, parameterNumber)`` plus the product
definition template and the percentile level. This closes DATA_SOURCES open item 12.
"""

from __future__ import annotations

import struct
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any

from cascade_geo import GridSpec

MAGIC = b"GRIB"
TRAILER = b"7777"
EDITION = 2

# (discipline, parameterCategory, parameterNumber) — GRIB2 Code Table 4.2.
APCP = (0, 1, 8)  # total precipitation, kg m-2
SNOWLVL = (0, 19, 236)  # NCEP local: snow level, m MSL (wet-bulb 0.5 C crossing)

# Product definition templates (GRIB2 Code Table 4.0) that appear in these files.
PDT_INSTANT = 0  # deterministic, instantaneous
PDT_PERCENTILE_INSTANT = 6  # percentile at a point in time (SNOWLVL)
PDT_INTERVAL = 8  # deterministic, statistically processed over an interval (APCP accum)
PDT_PROBABILITY_INTERVAL = 9  # probability of exceedance over an interval
PDT_PERCENTILE_INTERVAL = 10  # percentile over an interval (APCP accum percentiles)

#: Units as documented in docs/DATA_SOURCES.md W2. eccodes cannot name SNOWLVL's unit
#: (local table), so the unit is asserted from documentation and flagged as such; nothing is
#: ever converted (DATA_DOCTRINE: values are never converted between units or datums).
NATIVE_UNITS = {APCP: "kg m**-2", SNOWLVL: "m"}
UNIT_FROM_DOCUMENTATION = "unit_from_documentation"


class NbmParseError(Exception):
    def __init__(self, kind: str, detail: str) -> None:
        super().__init__(f"{kind}: {detail}")
        self.kind = kind
        self.detail = detail


@dataclass(frozen=True)
class FieldKey:
    """What a GRIB2 message is, in numbers only."""

    discipline: int
    category: int
    number: int
    pdt: int
    start_step_h: int
    end_step_h: int
    percentile: int | None
    surface_type: int

    @property
    def parameter(self) -> tuple[int, int, int]:
        return (self.discipline, self.category, self.number)

    @property
    def window_h(self) -> int:
        return self.end_step_h - self.start_step_h

    @property
    def is_cumulative_from_cycle(self) -> bool:
        """A ``0-N`` accumulation: the window the 24/48/72-h horizons are defined on."""
        return self.start_step_h == 0 and self.end_step_h > 0


@dataclass(frozen=True)
class Field:
    key: FieldKey
    units: str
    cycle: datetime
    valid_time: datetime
    grid: GridSpec
    values: Sequence[float] | None  # None when only metadata was requested


def split_messages(data: bytes) -> list[bytes]:
    """Frame a GRIB2 stream into whole messages, or raise a typed error.

    Every failure mode of a subset download is caught here: an HTML error page (no magic), a
    truncated file (declared length past the end, or a missing ``7777``), and trailing junk.
    """
    if not data:
        raise NbmParseError("empty_payload", "zero bytes")
    if not data.startswith(MAGIC):
        raise NbmParseError("not_grib2", f"payload starts with {data[:16]!r}, not {MAGIC!r}")
    messages: list[bytes] = []
    offset = 0
    total = len(data)
    while offset < total:
        if data[offset : offset + 4] != MAGIC:
            raise NbmParseError("trailing_bytes", f"{total - offset} bytes after message {len(messages)} do not start a GRIB message")
        if offset + 16 > total:
            raise NbmParseError("truncated", f"message {len(messages)} header cut off at byte {offset}")
        edition = data[offset + 7]
        if edition != EDITION:
            raise NbmParseError("wrong_edition", f"message {len(messages)} is GRIB edition {edition}, expected {EDITION}")
        (length,) = struct.unpack(">Q", data[offset + 8 : offset + 16])
        if length < 16 or offset + length > total:
            raise NbmParseError("truncated", f"message {len(messages)} declares {length} bytes, {total - offset} remain")
        if data[offset + length - 4 : offset + length] != TRAILER:
            raise NbmParseError("bad_trailer", f"message {len(messages)} does not end with {TRAILER!r}")
        messages.append(data[offset : offset + length])
        offset += length
    if not messages:
        raise NbmParseError("no_messages", "no GRIB2 message found")
    return messages


def _load_eccodes() -> Any:
    try:
        import eccodes
    except ImportError as exc:  # pragma: no cover - exercised by the API image, not by tests
        raise NbmParseError(
            "eccodes_missing",
            "GRIB2 decoding needs the worker's `grib` extra (pip install -e 'apps/worker[grib]')",
        ) from exc
    return eccodes


def _grid_definition_hash(message: bytes, eccodes: Any, handle: Any) -> str:
    """sha256 of GRIB2 Section 3 — the grid definition itself, byte for byte.

    Not a hash of a few keys: anything that changes the grid changes these bytes, including
    fields nobody thought to read. A changed hash makes every stored mask miss, which is the
    intended behaviour (docs/research/p3-surfaces-design-2026-08-24.md §1.4).
    """
    offset = int(eccodes.codes_get(handle, "offsetSection3", int))
    length = int(eccodes.codes_get(handle, "section3Length", int))
    section = message[offset : offset + length]
    if len(section) != length:
        raise NbmParseError("truncated_section3", f"section 3 declares {length} bytes, {len(section)} present")
    return sha256(section).hexdigest()


def _grid_of(message: bytes, eccodes: Any, handle: Any) -> GridSpec:
    grid_type = eccodes.codes_get(handle, "gridType")
    if grid_type != "lambert":
        raise NbmParseError("unsupported_grid", f"gridType={grid_type!r}; only 'lambert' is implemented")
    get = eccodes.codes_get
    lo1 = float(get(handle, "longitudeOfFirstGridPointInDegrees"))
    return GridSpec(
        nx=int(get(handle, "Ni", int)),
        ny=int(get(handle, "Nj", int)),
        la1=float(get(handle, "latitudeOfFirstGridPointInDegrees")),
        lo1=((lo1 + 180.0) % 360.0) - 180.0,
        lov=float(get(handle, "LoVInDegrees")),
        lad=float(get(handle, "LaDInDegrees")),
        latin1=float(get(handle, "Latin1InDegrees")),
        latin2=float(get(handle, "Latin2InDegrees")),
        dx_m=float(get(handle, "DxInMetres")),
        dy_m=float(get(handle, "DyInMetres")),
        earth_radius_m=float(get(handle, "radius")),
        definition_hash=_grid_definition_hash(message, eccodes, handle),
        i_scans_negatively=bool(int(get(handle, "iScansNegatively", int))),
        j_scans_positively=bool(int(get(handle, "jScansPositively", int))),
    )


def _key_of(eccodes: Any, handle: Any) -> FieldKey:
    get = eccodes.codes_get
    pdt = int(get(handle, "productDefinitionTemplateNumber", int))
    percentile: int | None = None
    if pdt in (PDT_PERCENTILE_INSTANT, PDT_PERCENTILE_INTERVAL):
        percentile = int(get(handle, "percentileValue", int))
    return FieldKey(
        discipline=int(get(handle, "discipline", int)),
        category=int(get(handle, "parameterCategory", int)),
        number=int(get(handle, "parameterNumber", int)),
        pdt=pdt,
        start_step_h=int(get(handle, "startStep", int)),
        end_step_h=int(get(handle, "endStep", int)),
        percentile=percentile,
        surface_type=int(get(handle, "typeOfFirstFixedSurface", int)),
    )


def _cycle_of(eccodes: Any, handle: Any) -> datetime:
    date = int(eccodes.codes_get(handle, "dataDate", int))
    time_hhmm = int(eccodes.codes_get(handle, "dataTime", int))
    return datetime(date // 10000, (date // 100) % 100, date % 100, time_hhmm // 100, time_hhmm % 100, tzinfo=UTC)


def decode(data: bytes, *, want: Callable[[FieldKey], bool] | None = None, with_values: bool = True) -> list[Field]:
    """Decode a subset, materializing values only for the fields ``want`` accepts.

    One 161-message WA subset decodes in well under a second, but its values are 2.3 M
    floats; ``want`` keeps the job's memory proportional to what it actually aggregates.
    All messages must share one grid definition — a mixed-grid payload is a defect, not
    something to aggregate around.
    """
    eccodes = _load_eccodes()
    fields: list[Field] = []
    grid: GridSpec | None = None
    for index, message in enumerate(split_messages(data)):
        handle = eccodes.codes_new_from_message(message)
        try:
            message_grid = _grid_of(message, eccodes, handle)
            if grid is None:
                grid = message_grid
            elif message_grid.definition_hash != grid.definition_hash:
                raise NbmParseError(
                    "mixed_grids",
                    f"message {index} carries grid {message_grid.definition_hash[:12]}, message 0 carries {grid.definition_hash[:12]}",
                )
            key = _key_of(eccodes, handle)
            if want is not None and not want(key):
                continue
            cycle = _cycle_of(eccodes, handle)
            values: Sequence[float] | None = None
            if with_values:
                missing = float(eccodes.codes_get(handle, "missingValue"))
                raw = eccodes.codes_get_array(handle, "values")
                values = [None if v == missing else float(v) for v in raw]  # type: ignore[misc]
            fields.append(
                Field(
                    key=key,
                    units=str(eccodes.codes_get(handle, "units")),
                    cycle=cycle,
                    valid_time=cycle + timedelta(hours=key.end_step_h),
                    grid=message_grid,
                    values=values,
                )
            )
        finally:
            eccodes.codes_release(handle)
    if grid is None:
        raise NbmParseError("no_messages", "payload framed but decoded no message")
    return fields


def scan(data: bytes) -> list[FieldKey]:
    """Every message's identity, without materializing any values."""
    return [f.key for f in decode(data, with_values=False)]


def cumulative_apcp(*, hours: int, percentile: int | None) -> Callable[[FieldKey], bool]:
    """Selector for the ``0-N`` cumulative APCP field at one percentile level.

    ``percentile=None`` selects the deterministic (single-valued) field, which is a different
    thing from the 50th percentile and is never treated as one.
    """

    def want(key: FieldKey) -> bool:
        if key.parameter != APCP or key.start_step_h != 0 or key.end_step_h != hours:
            return False
        if percentile is None:
            return key.pdt == PDT_INTERVAL
        return key.pdt == PDT_PERCENTILE_INTERVAL and key.percentile == percentile

    return want


def snow_level(*, percentile: int | None, fhour: int | None = None) -> Callable[[FieldKey], bool]:
    """Selector for SNOWLVL by GRIB identifiers — never by ``shortName``."""

    def want(key: FieldKey) -> bool:
        if key.parameter != SNOWLVL:
            return False
        if fhour is not None and key.end_step_h != fhour:
            return False
        if percentile is None:
            return key.pdt == PDT_INSTANT
        return key.pdt == PDT_PERCENTILE_INSTANT and key.percentile == percentile

    return want


def one(fields: Sequence[Field], *, what: str) -> Field:
    """Exactly one field, or a typed error naming what was missing or duplicated."""
    if not fields:
        raise NbmParseError("field_missing", f"{what} is not in this cycle")
    if len(fields) > 1:
        raise NbmParseError("field_ambiguous", f"{len(fields)} messages match {what}")
    return fields[0]


def percentile_levels(keys: Sequence[FieldKey], *, parameter: tuple[int, int, int], hours: int | None = None) -> list[int]:
    """The percentile levels actually present for a parameter — read, never assumed."""
    levels = {
        k.percentile
        for k in keys
        if k.parameter == parameter and k.percentile is not None and (hours is None or (k.start_step_h == 0 and k.end_step_h == hours))
    }
    return sorted(levels)


def windows(keys: Sequence[FieldKey], *, parameter: tuple[int, int, int]) -> list[tuple[int, int]]:
    return sorted({(k.start_step_h, k.end_step_h) for k in keys if k.parameter == parameter})

