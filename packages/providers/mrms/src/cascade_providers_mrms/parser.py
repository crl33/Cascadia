"""Strict decode of one MRMS grib2.gz to a lat/lon grid plus its value plane.

MRMS local products defeat name-based GRIB identity (eccodes reports ``shortName: unknown`` for
the NSSL local tables), so identity here is structural, in three layers:

1. the S3 KEY names the product, and the caller carries that context;
2. Section 3 is hashed byte-for-byte (the NBM convention) — a changed grid MISSES every stored
   mask and the aggregation refuses rather than weighting the wrong cells;
3. the sentinels are respected at aggregation, never here: −1 (missing) and −3 (no radar
   coverage) pass through as values, because turning them into NaN this early would erase the
   distinction between "radar could not see" and "the file did not say", and the two produce
   different quality flags downstream.

``eccodes`` is imported lazily so the API image never loads GRIB libraries (the NBM precedent).
"""

from __future__ import annotations

import gzip
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from cascade_geo.latlon import LatLonGridSpec

MISSING = -1.0
NO_COVERAGE = -3.0

__all__ = ["MISSING", "NO_COVERAGE", "MrmsField", "MrmsParseError", "parse_mrms_grib"]


class MrmsParseError(Exception):
    def __init__(self, kind: str, detail: str) -> None:
        super().__init__(f"{kind}: {detail}")
        self.kind = kind
        self.detail = detail


@dataclass(frozen=True)
class MrmsField:
    grid: LatLonGridSpec
    values: Any  # numpy float64, flat, in the provider's own row-major NW-origin order


def parse_mrms_grib(content: bytes) -> MrmsField:
    """gunzip + decode exactly one message; anything else in the file is a refusal."""
    import eccodes  # lazy: worker-only dependency
    import numpy as np

    try:
        raw = gzip.decompress(content)
    except (OSError, EOFError) as e:
        raise MrmsParseError("not_gzip", str(e)) from e

    try:
        handle = eccodes.codes_new_from_message(raw)
    except Exception as e:  # gribapi raises its own hierarchy; a broken payload is one refusal
        raise MrmsParseError("not_grib", f"gunzipped payload did not decode as GRIB: {e}") from e
    if handle is None:
        raise MrmsParseError("not_grib", "gunzipped payload is not a GRIB message")
    try:
        # one message per MRMS file, always; a second would mean the product changed shape
        edition = eccodes.codes_get(handle, "edition")
        if edition != 2:
            raise MrmsParseError("wrong_edition", f"GRIB edition {edition}, expected 2")
        grid_type = eccodes.codes_get(handle, "gridType")
        if grid_type != "regular_ll":
            raise MrmsParseError("wrong_grid_type", f"{grid_type!r}, expected regular_ll")
        offset = int(eccodes.codes_get(handle, "offsetSection3"))
        length = int(eccodes.codes_get(handle, "section3Length"))
        section3 = raw[offset : offset + length]
        if len(section3) != length:
            raise MrmsParseError("truncated_section3", f"declares {length} bytes, {len(section3)} present")
        grid = LatLonGridSpec(
            nx=int(eccodes.codes_get(handle, "Ni")),
            ny=int(eccodes.codes_get(handle, "Nj")),
            la1=float(eccodes.codes_get(handle, "latitudeOfFirstGridPointInDegrees")),
            lo1=float(eccodes.codes_get(handle, "longitudeOfFirstGridPointInDegrees")),
            dlon=float(eccodes.codes_get(handle, "iDirectionIncrementInDegrees")),
            dlat=float(eccodes.codes_get(handle, "jDirectionIncrementInDegrees")),
            earth_radius_m=6371229.0,
            definition_hash=sha256(section3).hexdigest(),
        )
        values = np.asarray(eccodes.codes_get_values(handle))
        if values.size != grid.size:
            raise MrmsParseError(
                "value_count", f"{values.size} values for a {grid.nx}x{grid.ny} grid"
            )
    except MrmsParseError:
        raise
    except Exception as e:  # a truncated message fails deep inside eccodes; still one refusal
        raise MrmsParseError("decode_failed", str(e)) from e
    finally:
        eccodes.codes_release(handle)

    # a second message is a product change, not extra data. Section 0 carries the first
    # message's total length; anything after it that still smells of GRIB is a refusal, and
    # trailing padding bytes are not (eccodes raises on empty input rather than returning None,
    # so the check is on the magic, not on a decode attempt).
    remainder = raw[_message_length(raw):]
    if remainder.lstrip(b"\x00").startswith(b"GRIB"):
        raise MrmsParseError("multi_message", "file carries more than one GRIB message")
    return MrmsField(grid=grid, values=values)


def _message_length(raw: bytes) -> int:
    """Total length of the first GRIB2 message, from its own Section 0 (bytes 8..16, big-endian)."""
    if len(raw) < 16 or raw[:4] != b"GRIB":
        raise MrmsParseError("not_grib", "no GRIB magic in gunzipped payload")
    return int.from_bytes(raw[8:16], "big")
