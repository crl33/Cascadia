"""Lambert conformal conic projection for gridded model products (docs/ARCHITECTURE.md §2).

Why this exists rather than a dependency: the NBM CONUS grid is one Lambert conformal grid on
a sphere, and the only thing the platform needs from a projection library is a forward and an
inverse map plus the point scale factor. That is forty lines of textbook mathematics (Snyder,
*Map Projections — A Working Manual*, USGS PP 1395, §15), and owning it keeps GEOS/PROJ — tens
of megabytes of native libraries — out of the worker image for six basins against one 99x142
subgrid. The implementation is checked against the provider's own coordinates: the
``latitudes``/``longitudes`` arrays eccodes computes from the GRIB2 grid definition are
reproduced to ~1e-12 of a grid cell (tests/unit/test_forcing.py).

Nothing here knows about GRIB, providers or hydrology; :class:`GridSpec` is a plain
description of a grid that a provider adapter fills in.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

_D2R = math.pi / 180.0


@dataclass(frozen=True)
class GridSpec:
    """A regular projected grid: enough to map (lon, lat) to a cell index and back.

    ``definition_hash`` identifies the grid definition the values came with (for GRIB2, a
    hash of Section 3). It is carried here, not derived here, because the provider owns the
    bytes; a mask is stored against it so that a silently changed grid MISSES its mask
    instead of being aggregated with the wrong weights.

    Index convention: ``flat_index = j * nx + i``, matching the order of the provider's own
    value array, with ``(i, j) = (0, 0)`` at the first grid point (``la1``, ``lo1``) and the
    grid point at the CENTRE of its cell.
    """

    nx: int
    ny: int
    la1: float
    lo1: float
    lov: float
    lad: float
    latin1: float
    latin2: float
    dx_m: float
    dy_m: float
    earth_radius_m: float
    definition_hash: str
    i_scans_negatively: bool = False
    j_scans_positively: bool = True

    @property
    def size(self) -> int:
        return self.nx * self.ny

    def flat_index(self, i: int, j: int) -> int:
        return j * self.nx + i


class LambertConformalConic:
    """Forward/inverse map and point scale factor for one :class:`GridSpec` (spherical earth).

    Grid coordinates are FRACTIONAL cell indices: ``(0.0, 0.0)`` is the first grid point and
    ``(1.0, 0.0)`` is its eastward neighbour, so a cell covers ``[i-0.5, i+0.5] x [j-0.5,
    j+0.5]``. Working in index space is what makes exact polygon-cell clipping cheap: every
    cell is the unit square.
    """

    def __init__(self, grid: GridSpec) -> None:
        if grid.i_scans_negatively or not grid.j_scans_positively:
            # NBM CONUS scans +i/+j (scanningMode 64). Other modes are refused rather than
            # guessed: a wrong sign silently mirrors every basin mask.
            raise ValueError("only +i/+j scanning is supported; refusing to guess the index order")
        self.grid = grid
        p1, p2 = grid.latin1 * _D2R, grid.latin2 * _D2R
        if abs(p1 - p2) < 1e-12:
            self.n = math.sin(p1)
        else:
            self.n = math.log(math.cos(p1) / math.cos(p2)) / math.log(
                math.tan(math.pi / 4 + p2 / 2) / math.tan(math.pi / 4 + p1 / 2)
            )
        if self.n == 0:
            raise ValueError("degenerate Lambert cone (n = 0)")
        self.f = math.cos(p1) * math.tan(math.pi / 4 + p1 / 2) ** self.n / self.n
        self.r = grid.earth_radius_m
        self.rho0 = self._rho(grid.lad)
        self._x0, self._y0 = self._project(grid.lo1, grid.la1)

    def _rho(self, lat_deg: float) -> float:
        return self.r * self.f / math.tan(math.pi / 4 + lat_deg * _D2R / 2) ** self.n

    def _project(self, lon_deg: float, lat_deg: float) -> tuple[float, float]:
        dlon = ((lon_deg - self.grid.lov + 180.0) % 360.0) - 180.0
        theta = self.n * dlon * _D2R
        rho = self._rho(lat_deg)
        return rho * math.sin(theta), self.rho0 - rho * math.cos(theta)

    def to_grid(self, lon_deg: float, lat_deg: float) -> tuple[float, float]:
        """(lon, lat) in degrees -> fractional (i, j) cell index."""
        x, y = self._project(lon_deg, lat_deg)
        return (x - self._x0) / self.grid.dx_m, (y - self._y0) / self.grid.dy_m

    def to_lonlat(self, i: float, j: float) -> tuple[float, float]:
        """Fractional (i, j) cell index -> (lon, lat) in degrees, lon in [-180, 180)."""
        x = self._x0 + i * self.grid.dx_m
        y = self._y0 + j * self.grid.dy_m
        dy = self.rho0 - y
        rho = math.copysign(math.hypot(x, dy), self.n)
        lat = (2.0 * math.atan((self.r * self.f / rho) ** (1.0 / self.n)) - math.pi / 2) / _D2R
        lon = self.grid.lov + math.atan2(x, dy) / self.n / _D2R
        return ((lon + 180.0) % 360.0) - 180.0, lat

    def scale_factor(self, lat_deg: float) -> float:
        """Point scale factor k: projected lengths are k times true lengths at this latitude.

        Conformal, so areas scale by k^2. At 48 N on the NBM grid (standard parallel 25 N)
        k = 1.0934, i.e. a nominally 2.5397 km cell covers 5.395 km^2 on the ground, not
        6.450. Ignoring this would inflate every basin area by ~20 %.
        """
        return self.n * self._rho(lat_deg) / (self.r * math.cos(lat_deg * _D2R))

    def cell_area_km2(self, i: int, j: int) -> float:
        """True ground area of one whole grid cell, in km^2."""
        _lon, lat = self.to_lonlat(i, j)
        k = self.scale_factor(lat)
        return (self.grid.dx_m * self.grid.dy_m / (k * k)) / 1e6
