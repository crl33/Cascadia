"""Regular latitude/longitude grids (MRMS QPE and kin), presented to the mask machinery.

The Lambert module earned its forty lines of Snyder; this one is even smaller, because a regular
lat/lon grid's "projection" is affine in each axis. What still deserves care:

- **Longitude convention.** MRMS Section 3 speaks 0..360 (`lo1 = 230.005` for -129.995), the
  basin polygons speak -180..180. The conversion lives HERE and nowhere else, so no caller can
  get it half right.
- **Row direction.** MRMS scans from the northwest corner southward (`la1 = 54.995`, latitudes
  DECREASING with j). ``to_grid`` encodes that; a sign slip here would silently mirror
  Washington into Mexico and every mask would still "work".
- **Cell area is latitude-dependent.** The same authalic-sphere formula the hypsometry build
  uses: a cell at 49°N is ~34 % smaller than its equator-sized self, and a basin mean weighted
  without the cosine would lean south.

Like ``GridSpec``, ``definition_hash`` is carried, not derived: the provider hashes the bytes of
GRIB2 Section 3, and a mask stored against one definition MISSES when the provider changes grid,
rather than aggregating with the wrong weights.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

_D2R = math.pi / 180.0


def lon360(lon: float) -> float:
    """-129.995 -> 230.005. The one place the two longitude conventions meet."""
    return lon + 360.0 if lon < 0 else lon


@dataclass(frozen=True)
class LatLonGridSpec:
    """A regular lat/lon grid scanning east and (by MRMS convention) SOUTH from (la1, lo1)."""

    nx: int
    ny: int
    la1: float  # latitude of the FIRST row (northernmost for MRMS)
    lo1: float  # longitude of the first column, in the 0..360 convention the provider uses
    dlon: float
    dlat: float
    earth_radius_m: float
    definition_hash: str

    @property
    def size(self) -> int:
        return self.nx * self.ny

    def flat_index(self, i: int, j: int) -> int:
        return j * self.nx + i


class RegularLatLon:
    """Forward map and true cell area for one :class:`LatLonGridSpec`.

    The same two-method surface :class:`LambertConformalConic` offers, which is everything the
    mask builder consumes.
    """

    def __init__(self, grid: LatLonGridSpec) -> None:
        if grid.dlon <= 0 or grid.dlat <= 0:
            raise ValueError(f"non-positive grid step dlon={grid.dlon} dlat={grid.dlat}")
        self.grid = grid

    def to_grid(self, lon: float, lat: float) -> tuple[float, float]:
        """(lon, lat) in degrees (either longitude convention) -> fractional (i, j)."""
        g = self.grid
        i = (lon360(lon) - g.lo1) / g.dlon
        j = (g.la1 - lat) / g.dlat  # rows scan SOUTH: larger j is further south
        return i, j

    def cell_area_km2(self, i: int, j: int) -> float:
        g = self.grid
        lat = g.la1 - j * g.dlat
        r_km = g.earth_radius_m / 1000.0
        return (g.dlon * _D2R * r_km) * (g.dlat * _D2R * r_km) * math.cos(lat * _D2R)
