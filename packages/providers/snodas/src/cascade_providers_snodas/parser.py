"""Strict decode of one SNODAS daily tar to the SWE plane on its 1 km lat/lon grid.

The tar carries up to eight variables as gzipped flat binary + NOHRSC text headers; this reads
exactly ONE — product code 1034, "Modeled snow water equivalent, total of snow layers" — and
lets the header say everything: dimensions, cell size, origin, no-data value, units and the
snapshot instant all come from the provider's own text, verified against the constants this
platform depends on rather than assumed from them.

Grid identity: there is no GRIB Section 3 here, so the hash is over the CANONICAL SUBSET of
header lines that define the grid (dimensions, resolutions, extents, datum) — same property,
different bytes: a silently changed grid misses every stored mask.

Sentinels and failure modes, all measured 2026-08-28:

- ``-9999`` no-data is a STATIC land/water/domain mask (bit-identical across days, 15.6 M
  cells); in-basin instances are permanent water (reservoirs, lakes), so a mean over valid
  cells is the basin LAND mean, which is the honest statistic.
- ``32767`` is int16 saturation (32.767 m SWE) — the user guide's documented unbounded-growth
  failure in unobserved alpine cells (26 such cells CONUS-wide, stable). Passed through for
  the aggregation to exclude and FLAG, never averaged: a 32 m SWE is an artifact, not water.
- NSIDC intermittently serves an HTML "Server error!" page; the tar magic check refuses it
  before any decode (the NBM HTML-as-200 lesson).
"""

from __future__ import annotations

import gzip
import io
import tarfile
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any

from cascade_geo.latlon import LatLonGridSpec, lon360

SWE_PRODUCT_CODE = "1034"
NODATA = -9999.0
#: int16 saturation — the documented unbounded-growth artifact, excluded and flagged.
SATURATED = 32767.0

#: The header lines whose values define the grid; hashed in this order.
_GRID_KEYS = (
    "Number of columns", "Number of rows",
    "X-axis resolution", "Y-axis resolution",
    "Minimum x-axis coordinate", "Maximum x-axis coordinate",
    "Minimum y-axis coordinate", "Maximum y-axis coordinate",
    "X-axis offset", "Y-axis offset",
    "Horizontal datum",
)

__all__ = ["NODATA", "SATURATED", "SnodasField", "SnodasParseError", "parse_snodas_swe"]


class SnodasParseError(Exception):
    def __init__(self, kind: str, detail: str) -> None:
        super().__init__(f"{kind}: {detail}")
        self.kind = kind
        self.detail = detail


@dataclass(frozen=True)
class SnodasField:
    grid: LatLonGridSpec
    values: Any  # numpy float64, flat, NW-origin row-major; RAW integers (mm, since m/1000)
    valid_time: datetime  # the 06:00 UTC snapshot, from the header's own Start fields


def _headers(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            out[key.strip()] = value.strip()
    return out


def parse_snodas_swe(content: bytes) -> SnodasField:
    import numpy as np

    if not content.startswith(b"zz_ssmv") and (len(content) < 265 or content[257:262] != b"ustar"):
        # a tar's magic sits at offset 257; an NSIDC HTML error page fails here, loudly
        raise SnodasParseError("not_tar", "payload is not a tar archive")
    try:
        tar = tarfile.open(fileobj=io.BytesIO(content))
    except tarfile.TarError as e:
        raise SnodasParseError("not_tar", str(e)) from e
    dat_bytes: bytes | None = None
    txt: str | None = None
    try:
        members = list(tar.getmembers())
    except tarfile.TarError as e:  # truncation surfaces here, not at open()
        tar.close()
        raise SnodasParseError("not_tar", str(e)) from e
    with tar:
        for member in members:
            name = member.name.rsplit("/", 1)[-1]
            # the members are named zz_ssmv1<code>...; anything else (directories, archiver
            # metadata such as AppleDouble "._" entries) is not a data member
            if not (member.isfile() and name.startswith("zz_ssmv") and SWE_PRODUCT_CODE in name[:14]):
                continue
            payload = tar.extractfile(member)
            if payload is None:
                continue
            try:
                raw = gzip.decompress(payload.read())
            except (OSError, EOFError) as e:
                raise SnodasParseError("bad_gzip", f"{name}: {e}") from e
            if name.endswith(".dat.gz"):
                dat_bytes = raw
            elif name.endswith(".txt.gz"):
                txt = raw.decode("ascii", errors="replace")
    if dat_bytes is None or txt is None:
        raise SnodasParseError("swe_absent", "tar carries no 1034 SWE .dat.gz + .txt.gz pair")

    h = _headers(txt)
    try:
        nx, ny = int(h["Number of columns"]), int(h["Number of rows"])
        dlon, dlat = float(h["X-axis resolution"]), float(h["Y-axis resolution"])
        x_off, y_off = float(h["X-axis offset"]), float(h["Y-axis offset"])
        min_x, max_y = float(h["Minimum x-axis coordinate"]), float(h["Maximum y-axis coordinate"])
        nodata = float(h["No data value"])
        units = h["Data units"]
        valid_time = datetime(
            int(h["Start year"]), int(h["Start month"]), int(h["Start day"]),
            int(h["Start hour"]), int(h["Start minute"]), tzinfo=UTC,
        )
        stop = (h["Stop year"], h["Stop month"], h["Stop day"], h["Stop hour"], h["Stop minute"])
    except (KeyError, ValueError) as e:
        raise SnodasParseError("bad_header", f"header lacks or mangles {e!r}") from e
    if nodata != NODATA:
        raise SnodasParseError("bad_header", f"no-data {nodata}, expected {NODATA}")
    if not units.startswith("Meters / 1000"):
        # m/1000 == mm; a changed unit would silently rescale every basin mean
        raise SnodasParseError("bad_header", f"units {units!r}, expected Meters / 1000")
    if stop != (h["Start year"], h["Start month"], h["Start day"], h["Start hour"], h["Start minute"]):
        raise SnodasParseError("bad_header", "SWE must be a snapshot: Start != Stop")
    if len(dat_bytes) != nx * ny * 2:
        raise SnodasParseError("value_count", f"{len(dat_bytes)} bytes for a {nx}x{ny} int16 grid")

    grid = LatLonGridSpec(
        nx=nx, ny=ny,
        la1=max_y - y_off,  # header extents are cell EDGES; the spec wants the first cell CENTRE
        lo1=lon360(min_x + x_off),
        dlon=dlon, dlat=dlat,
        earth_radius_m=6371229.0,
        definition_hash=sha256("\n".join(f"{k}: {h[k]}" for k in _GRID_KEYS).encode()).hexdigest(),
    )
    values = np.frombuffer(dat_bytes, dtype=">i2").astype(np.float64)
    return SnodasField(grid=grid, values=values, valid_time=valid_time)
