"""Strict decode of one WPC 5-km QPF GRIB2 to an LCC grid plus its value plane.

One file is one 24-hour accumulation window of the human-drawn national QPF, on the same
Lambert-conformal family NBM uses, so the whole mask/aggregation machinery is shared. Identity
is structural (the MRMS convention): the filename names the cycle and window, Section 3 is
hashed byte-for-byte so a changed grid MISSES every stored mask, and the missing value (9999
under the file's own bitmap, covering the off-CONUS corners of the LCC rectangle) passes
through for the aggregation to refuse — it is geography, not damage.

One decoding fact that is not damage either: the files are ``grid_jpeg`` packed, and JPEG-2000
reconstruction leaves tiny NEGATIVE values (measured −0.0099 mm on the probe file) where the
field is zero. The parser passes them through; the aggregation clamps them at zero rather than
discarding the cells, because "no rain" is a value, not a gap.

``eccodes`` is imported lazily so the API image never loads GRIB libraries (the NBM precedent).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any

from cascade_geo.lcc import GridSpec

#: eccodes substitutes this for bitmap-missing cells; anything at or above it is off-domain.
MISSING_FLOOR = 9998.0
#: JPEG reconstruction noise floor: values in [-NEGATIVE_NOISE, 0) clamp to zero, anything more
#: negative is refused as damage — a real QPF is never negative.
NEGATIVE_NOISE = 0.1

__all__ = ["MISSING_FLOOR", "NEGATIVE_NOISE", "WpcField", "WpcParseError", "parse_wpc_qpf"]


class WpcParseError(Exception):
    def __init__(self, kind: str, detail: str) -> None:
        super().__init__(f"{kind}: {detail}")
        self.kind = kind
        self.detail = detail


@dataclass(frozen=True)
class WpcField:
    grid: GridSpec
    values: Any  # numpy float64, flat, in the provider's own order (kg m-2 == mm)
    reference_time: datetime  # the cycle (00Z / 12Z), from the message itself
    step_start_h: int  # accumulation window [reference + start, reference + end]
    step_end_h: int


def parse_wpc_qpf(content: bytes) -> WpcField:
    """Decode exactly one total-precipitation message; anything else is a refusal."""
    import eccodes  # lazy: worker-only dependency
    import numpy as np

    if len(content) < 16 or content[:4] != b"GRIB":
        raise WpcParseError("not_grib", "no GRIB magic in payload")
    try:
        handle = eccodes.codes_new_from_message(content)
    except Exception as e:  # gribapi raises its own hierarchy; a broken payload is one refusal
        raise WpcParseError("not_grib", f"payload did not decode as GRIB: {e}") from e
    if handle is None:
        raise WpcParseError("not_grib", "payload is not a GRIB message")
    try:
        edition = eccodes.codes_get(handle, "edition")
        if edition != 2:
            raise WpcParseError("wrong_edition", f"GRIB edition {edition}, expected 2")
        grid_type = eccodes.codes_get(handle, "gridType")
        if grid_type != "lambert":
            raise WpcParseError("wrong_grid_type", f"{grid_type!r}, expected lambert")
        short_name = eccodes.codes_get(handle, "shortName")
        if short_name != "tp":
            raise WpcParseError("wrong_parameter", f"{short_name!r}, expected tp")
        step = str(eccodes.codes_get(handle, "stepRange"))
        try:
            start_s, end_s = step.split("-")
            step_start_h, step_end_h = int(start_s), int(end_s)
        except ValueError as e:
            raise WpcParseError("bad_step", f"stepRange {step!r} is not 'start-end' hours") from e
        if step_end_h - step_start_h != 24:
            raise WpcParseError("bad_step", f"stepRange {step!r} is not a 24-hour window")
        date = int(eccodes.codes_get(handle, "dataDate"))
        time_hhmm = int(eccodes.codes_get(handle, "dataTime"))
        reference_time = datetime(
            date // 10000, (date // 100) % 100, date % 100,
            time_hhmm // 100, time_hhmm % 100, tzinfo=UTC,
        )
        offset = int(eccodes.codes_get(handle, "offsetSection3"))
        length = int(eccodes.codes_get(handle, "section3Length"))
        section3 = content[offset : offset + length]
        if len(section3) != length:
            raise WpcParseError("truncated_section3", f"declares {length} bytes, {len(section3)} present")
        grid = GridSpec(
            nx=int(eccodes.codes_get(handle, "Ni")),
            ny=int(eccodes.codes_get(handle, "Nj")),
            la1=float(eccodes.codes_get(handle, "latitudeOfFirstGridPointInDegrees")),
            lo1=float(eccodes.codes_get(handle, "longitudeOfFirstGridPointInDegrees")),
            lov=float(eccodes.codes_get(handle, "LoVInDegrees")),
            lad=float(eccodes.codes_get(handle, "LaDInDegrees")),
            latin1=float(eccodes.codes_get(handle, "Latin1InDegrees")),
            latin2=float(eccodes.codes_get(handle, "Latin2InDegrees")),
            dx_m=float(eccodes.codes_get(handle, "DxInMetres")),
            dy_m=float(eccodes.codes_get(handle, "DyInMetres")),
            earth_radius_m=float(eccodes.codes_get(handle, "radius")),
            definition_hash=sha256(section3).hexdigest(),
            i_scans_negatively=bool(eccodes.codes_get(handle, "iScansNegatively")),
            j_scans_positively=bool(eccodes.codes_get(handle, "jScansPositively")),
        )
        values = np.asarray(eccodes.codes_get_values(handle))
        if values.size != grid.size:
            raise WpcParseError("value_count", f"{values.size} values for a {grid.nx}x{grid.ny} grid")
    except WpcParseError:
        raise
    except Exception as e:  # a truncated message fails deep inside eccodes; still one refusal
        raise WpcParseError("decode_failed", str(e)) from e
    finally:
        eccodes.codes_release(handle)

    remainder = content[_message_length(content):]
    if remainder.lstrip(b"\x00").startswith(b"GRIB"):
        raise WpcParseError("multi_message", "file carries more than one GRIB message")
    return WpcField(
        grid=grid, values=values,
        reference_time=reference_time, step_start_h=step_start_h, step_end_h=step_end_h,
    )


def _message_length(raw: bytes) -> int:
    """Total length of the first GRIB2 message, from its own Section 0 (bytes 8..16, big-endian)."""
    if len(raw) < 16 or raw[:4] != b"GRIB":
        raise WpcParseError("not_grib", "no GRIB magic in payload")
    return int.from_bytes(raw[8:16], "big")
