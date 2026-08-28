"""Cutting the seeded window out of a decoded MRMS plane and packing it for storage.

ADR-0020: the field the map renders is the plane `mrms.fetch_qpe` already decoded, cut to the
basin-union window and quantized — never a second fetch, never a second decode. Pure functions
over `MrmsField`; the job stores what these return.

Packing: little-endian uint16, row-major from the NW corner (the provider's own scan order),
value = raw * SCALE_MM. 0xFFFF is the sentinel for the parser's negative codes (missing and
radar-no-coverage alike — for a display raster both mean "cannot say", and the basin means
keep the finer distinction); real values clip at 0xFFFE, i.e. 6553.4 mm, which no hourly
accumulation approaches. gzip then does the real work: a dry hour is a run of zeros.
"""

from __future__ import annotations

import gzip
from dataclasses import dataclass

from cascade_geo.latlon import LatLonGridSpec, lon360

from cascade_providers_mrms.parser import MrmsField

#: The seeded window (ADR-0020): the six-basin union bbox padded 0.15 deg. A DECISION carried
#: into every stored row's own spec columns — readers must georeference from the row, never
#: from this constant.
WINDOW_WEST = -122.87
WINDOW_SOUTH = 46.63
WINDOW_EAST = -120.50
WINDOW_NORTH = 49.46

SCALE_MM = 0.1
SENTINEL = 0xFFFF
MAX_RAW = 0xFFFE
METHOD_RASTER = "method:field-raster-window@1.0.0"
FIELD_QPE = "qpe_01h"


class WindowOutsideGridError(ValueError):
    """The provider's grid no longer covers the seeded window — refuse, never crop silently."""


@dataclass(frozen=True)
class WindowRaster:
    """One packed window cut. `lo1`/`la1` are the window's own NW cell center, lon in the
    -180..180 convention the contract speaks (the provider's 0..360 stays in the provider)."""

    lo1: float
    la1: float
    dlon: float
    dlat: float
    nx: int
    ny: int
    unit: str
    scale: float
    max_value: float
    cells: bytes  # gzip(uint16 LE, row-major, NW origin)


def cut_window(field: MrmsField) -> WindowRaster:
    import numpy as np

    grid: LatLonGridSpec = field.grid
    # Fractional window corners in grid coordinates; ceil/floor INWARD so every kept cell
    # center lies inside the window.
    i0 = int(np.ceil((lon360(WINDOW_WEST) - grid.lo1) / grid.dlon))
    i1 = int(np.floor((lon360(WINDOW_EAST) - grid.lo1) / grid.dlon))
    j0 = int(np.ceil((grid.la1 - WINDOW_NORTH) / grid.dlat))  # rows scan SOUTH
    j1 = int(np.floor((grid.la1 - WINDOW_SOUTH) / grid.dlat))
    if i0 < 0 or j0 < 0 or i1 >= grid.nx or j1 >= grid.ny or i0 > i1 or j0 > j1:
        raise WindowOutsideGridError(
            f"seeded window not inside the provider grid (i {i0}..{i1} of {grid.nx}, "
            f"j {j0}..{j1} of {grid.ny}) — the grid changed; refusing to crop silently"
        )
    plane = np.asarray(field.values, dtype=np.float64).reshape(grid.ny, grid.nx)
    cut = plane[j0 : j1 + 1, i0 : i1 + 1]
    valid = cut >= 0.0
    raw = np.where(
        valid,
        np.clip(np.rint(cut / SCALE_MM), 0, MAX_RAW).astype(np.uint16),
        np.uint16(SENTINEL),
    ).astype("<u2")
    max_value = float(cut[valid].max()) if bool(valid.any()) else 0.0
    lo1 = grid.lo1 + i0 * grid.dlon
    return WindowRaster(
        lo1=lo1 - 360.0 if lo1 > 180.0 else lo1,
        la1=grid.la1 - j0 * grid.dlat,
        dlon=grid.dlon,
        dlat=grid.dlat,
        nx=i1 - i0 + 1,
        ny=j1 - j0 + 1,
        unit="mm",
        scale=SCALE_MM,
        max_value=round(max_value, 1),
        cells=gzip.compress(raw.tobytes(), 6),
    )
