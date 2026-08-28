"""Cutting the seeded window out of a decoded provider plane and packing it for storage.

ADR-0020: the field the map renders is a plane an ingest job already decoded — cut to the
basin-union window and quantized, never a second fetch or decode. Grid-agnostic across the
providers that speak :class:`LatLonGridSpec` (MRMS QPE at 0.01 deg, SNODAS at ~0.0083 deg):
the only assumptions are the spec's own — rows scan EAST then SOUTH from (la1, lo1), and
negative values are the provider's not-a-measurement codes.

Packing: little-endian uint16, row-major from the NW corner (the provider's own scan order),
value = raw * ``scale``. 0xFFFF is the sentinel for every negative code — for a display
raster "missing" and "no coverage" alike mean "cannot say", and the basin means keep the
finer distinction; real values clip at 0xFFFE * scale. gzip then does the real work: a dry
(or snow-free) window is a run of zeros.
"""

from __future__ import annotations

import gzip
from dataclasses import dataclass

from cascade_geo.latlon import LatLonGridSpec, lon360

#: The seeded window (ADR-0020): the six-basin union bbox padded 0.15 deg. A DECISION carried
#: into every stored row's own spec columns — readers must georeference from the row, never
#: from this constant.
WINDOW_WEST = -122.87
WINDOW_SOUTH = 46.63
WINDOW_EAST = -120.50
WINDOW_NORTH = 49.46

SENTINEL = 0xFFFF
MAX_RAW = 0xFFFE
METHOD_RASTER = "method:field-raster-window@1.0.0"


class WindowOutsideGridError(ValueError):
    """The provider's grid no longer covers the seeded window — refuse, never crop silently."""


@dataclass(frozen=True)
class WindowRaster:
    """One packed window cut. ``lo1``/``la1`` are the window's own NW cell center, lon in the
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


def cut_window(
    grid: LatLonGridSpec, values, *, scale: float, unit: str, invalid_values: tuple[float, ...] = ()
) -> WindowRaster:
    """Cut the seeded window out of ``values`` (flat, NW-origin row-major on ``grid``).

    ``invalid_values`` names the provider's POSITIVE not-a-measurement codes (SNODAS 32767 is
    int16 saturation, a documented artifact its own basin means exclude); negatives are
    already sentinels everywhere. Both become the packed SENTINEL — absence, never a value.
    """
    import numpy as np

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
    plane = np.asarray(values, dtype=np.float64).reshape(grid.ny, grid.nx)
    cut = plane[j0 : j1 + 1, i0 : i1 + 1]
    valid = cut >= 0.0
    for code in invalid_values:
        valid &= cut != code
    raw = np.where(
        valid,
        np.clip(np.rint(cut / scale), 0, MAX_RAW).astype(np.uint16),
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
        unit=unit,
        scale=scale,
        max_value=round(max_value, 1),
        cells=gzip.compress(raw.tobytes(), 6),
    )
