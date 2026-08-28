"""Basin x grid masks: exact fractional cell weights for zonal aggregation.

A mask answers one question — *how much of grid cell c lies inside basin b* — and it is the
only honest way to turn a gridded forecast into a basin number. Two rules are load-bearing:

1. **Full-resolution geometry, never a display LOD.** Cell-centre containment against the
   display-LOD Skagit polygon gave 1,544 cells = 9,961 km^2 against a WBD area of 8,275 km^2,
   a 20 % over-count (measured, p3-surfaces-design §1.4). The masks here are built from
   ``tests/fixtures/geo/basins_seed_full.geojson.gz`` and reproduce WBD areas to ~0.3 %.
2. **A mask belongs to a grid definition.** ``GridSpec.definition_hash`` is part of the mask's
   identity, so if the provider changes its grid the mask lookup MISSES. The caller must then
   refuse and report UNKNOWN — never area-weight the new grid with the old weights.

The clipping is exact: each polygon ring is projected into fractional cell-index space (where
every cell is the unit square), then swept row band by row band and column by column with
Sutherland-Hodgman clipping, accumulating signed area so interior rings (holes) subtract. No
sampling, no cell-centre approximation, no raster.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import math
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path

from cascade_geo.latlon import LatLonGridSpec, RegularLatLon
from cascade_geo.lcc import GridSpec, LambertConformalConic

#: Fractions below this are dropped: a cell touched along an edge to one part in a million
#: contributes nothing but noise to a basin mean.
MIN_WEIGHT = 1e-6

METHOD_GRID_MASK = "method:basin-grid-mask@1.0.0"

Ring = Sequence[Sequence[float]]
Polygon = Sequence[Ring]


class MaskError(Exception):
    """A mask could not be built or applied. Never returns a number instead."""

    def __init__(self, kind: str, detail: str) -> None:
        super().__init__(f"{kind}: {detail}")
        self.kind = kind
        self.detail = detail


@dataclass(frozen=True)
class BasinMask:
    """Fractional cell weights for one basin on one grid definition."""

    basin_id: str
    grid_definition_hash: str
    cells: tuple[tuple[int, float], ...]  # (flat_index, fraction in (0, 1])
    masked_area_km2: float
    polygon_source: str
    method_id: str = METHOD_GRID_MASK

    @property
    def cell_count(self) -> int:
        return len(self.cells)

    def as_rows(self) -> list[list[float]]:
        """JSON shape stored in ``grid_mask.cells``: ``[[flat_index, weight], ...]``."""
        return [[float(i), w] for i, w in self.cells]

    @classmethod
    def from_rows(
        cls,
        rows: Iterable[Sequence[float]],
        *,
        basin_id: str,
        grid_definition_hash: str,
        masked_area_km2: float,
        polygon_source: str,
        method_id: str = METHOD_GRID_MASK,
    ) -> BasinMask:
        return cls(
            basin_id=basin_id,
            grid_definition_hash=grid_definition_hash,
            cells=tuple((int(r[0]), float(r[1])) for r in rows),
            masked_area_km2=masked_area_km2,
            polygon_source=polygon_source,
            method_id=method_id,
        )


# --------------------------------------------------------------------------- geometry input


def polygons_of(geometry: dict) -> Iterator[Polygon]:
    """Every Polygon in a GeoJSON geometry, ignoring non-areal parts.

    The seed basin features are GeometryCollections that also carry LineStrings (shared
    boundaries digitized as lines); a line has no area and must not contribute one.
    """
    kind = geometry.get("type")
    if kind == "Polygon":
        yield geometry["coordinates"]
    elif kind == "MultiPolygon":
        yield from geometry["coordinates"]
    elif kind == "GeometryCollection":
        for part in geometry.get("geometries", ()):
            yield from polygons_of(part)
    elif kind in ("LineString", "MultiLineString", "Point", "MultiPoint", None):
        return
    else:
        raise MaskError("unsupported_geometry", f"{kind!r} is not an areal geometry")


def load_basin_polygons(path: str | Path) -> tuple[dict[str, list[Polygon]], dict[str, float], str]:
    """Read a (optionally gzipped) GeoJSON FeatureCollection of basins.

    Returns ``(polygons_by_basin_id, wbd_area_km2_by_basin_id, polygon_source)`` where
    ``polygon_source`` is ``"<filename>@<sha256>"`` — the provenance string stored on every
    mask, so a regenerated geometry file makes the stored masks visibly stale.
    """
    p = Path(path)
    raw = p.read_bytes()
    text = gzip.decompress(raw) if p.suffix == ".gz" else raw
    doc = json.loads(text)
    if doc.get("type") != "FeatureCollection":
        raise MaskError("not_a_feature_collection", f"{p.name}: type={doc.get('type')!r}")
    polys: dict[str, list[Polygon]] = {}
    areas: dict[str, float] = {}
    for feature in doc.get("features", ()):
        props = feature.get("properties") or {}
        basin_id = props.get("id")
        if not basin_id:
            raise MaskError("missing_basin_id", f"{p.name}: a feature has no properties.id")
        polys[basin_id] = list(polygons_of(feature.get("geometry") or {}))
        if props.get("area_km2_wbd_sum") is not None:
            areas[basin_id] = float(props["area_km2_wbd_sum"])
    return polys, areas, f"{p.name}@{hashlib.sha256(raw).hexdigest()}"


# ------------------------------------------------------------------------------- clipping


def _signed_area(pts: Sequence[tuple[float, float]]) -> float:
    total = 0.0
    n = len(pts)
    for idx in range(n):
        x1, y1 = pts[idx]
        x2, y2 = pts[(idx + 1) % n]
        total += x1 * y2 - x2 * y1
    return total / 2.0


def _clip_half_plane(pts: Sequence[tuple[float, float]], axis: int, value: float, keep_greater: bool) -> list[tuple[float, float]]:
    """Sutherland-Hodgman against one axis-aligned half plane; orientation is preserved."""
    out: list[tuple[float, float]] = []
    n = len(pts)
    for idx in range(n):
        a = pts[idx]
        b = pts[(idx + 1) % n]
        ka = a[axis] >= value if keep_greater else a[axis] <= value
        kb = b[axis] >= value if keep_greater else b[axis] <= value
        if ka:
            out.append(a)
        if ka != kb:
            t = (value - a[axis]) / (b[axis] - a[axis])
            out.append((value, a[1] + t * (b[1] - a[1])) if axis == 0 else (a[0] + t * (b[0] - a[0]), value))
    return out


def _accumulate_ring(ring_xy: list[tuple[float, float]], grid: GridSpec | LatLonGridSpec, coverage: dict[int, float]) -> None:
    """Add one oriented ring's signed area, cell by cell, into ``coverage``.

    The caller guarantees the ring lies inside the grid domain (:func:`build_basin_mask`
    refuses otherwise), so the sweep bounds below need no clamping — clamping is exactly how
    area from outside the subset would get smeared onto the edge row or column.
    """
    ys = [p[1] for p in ring_xy]
    xs = [p[0] for p in ring_xy]
    j_lo = int(math.floor(min(ys) + 0.5))
    j_hi = int(math.ceil(max(ys) + 0.5))
    i_lo_all = int(math.floor(min(xs) + 0.5))
    i_hi_all = int(math.ceil(max(xs) + 0.5))
    if j_lo > j_hi or i_lo_all > i_hi_all:
        return
    remainder = ring_xy
    for j in range(j_lo, j_hi + 1):
        if not remainder:
            break
        top = j + 0.5
        band = _clip_half_plane(remainder, 1, top, keep_greater=False)
        remainder = _clip_half_plane(remainder, 1, top, keep_greater=True)
        if len(band) < 3:
            continue
        row_remainder = band
        bxs = [p[0] for p in band]
        i_lo = max(i_lo_all, int(math.floor(min(bxs) + 0.5)))
        i_hi = min(i_hi_all, int(math.ceil(max(bxs) + 0.5)))
        for i in range(i_lo, i_hi + 1):
            if not row_remainder:
                break
            right = i + 0.5
            cell = _clip_half_plane(row_remainder, 0, right, keep_greater=False)
            row_remainder = _clip_half_plane(row_remainder, 0, right, keep_greater=True)
            if len(cell) < 3:
                continue
            area = _signed_area(cell)
            if area:
                flat = grid.flat_index(i, j)
                coverage[flat] = coverage.get(flat, 0.0) + area


def build_basin_mask(
    *,
    basin_id: str,
    polygons: Iterable[Polygon],
    grid: GridSpec | LatLonGridSpec,
    polygon_source: str,
) -> BasinMask:
    """Exact fractional cell weights for one basin on ``grid``.

    Weights are the fraction of each cell inside the basin, so a basin mean is
    ``sum(w_i * v_i) / sum(w_i)`` and the masked area is ``sum(w_i * area(cell_i))`` with
    each cell's TRUE ground area (the projection's scale factor applied — see
    :meth:`LambertConformalConic.cell_area_km2`).

    The clipping is identical for every grid family; only the (lon, lat) -> (i, j) map and the
    cell-area formula differ, so the dispatch lives here and the sweep below never knows which
    projection produced its coordinates.
    """
    projection = RegularLatLon(grid) if isinstance(grid, LatLonGridSpec) else LambertConformalConic(grid)
    rings: list[list[tuple[float, float]]] = []
    parts = 0
    for polygon in polygons:
        parts += 1
        for ring_index, ring in enumerate(polygon):
            pts = [projection.to_grid(float(lon), float(lat)) for lon, lat, *_ in ring]
            if len(pts) > 1 and pts[0] == pts[-1]:
                pts.pop()
            if len(pts) < 3:
                continue
            # Exterior ring counts positive, interior rings (holes) negative, whatever
            # winding order the source file happens to use.
            area = _signed_area(pts)
            if (ring_index == 0 and area < 0) or (ring_index > 0 and area > 0):
                pts.reverse()
            rings.append(pts)
    if not parts:
        raise MaskError("no_polygons", f"{basin_id}: geometry carries no areal parts")
    if not rings:
        raise MaskError("no_polygons", f"{basin_id}: no ring of this geometry has three points")
    # A basin that reaches past the edge of the subset cannot have an honest basin mean: the
    # part outside was never fetched. Refuse instead of aggregating the part that was.
    lo_i = min(p[0] for r in rings for p in r)
    hi_i = max(p[0] for r in rings for p in r)
    lo_j = min(p[1] for r in rings for p in r)
    hi_j = max(p[1] for r in rings for p in r)
    if lo_i < -0.5 or lo_j < -0.5 or hi_i > grid.nx - 0.5 or hi_j > grid.ny - 0.5:
        raise MaskError(
            "basin_outside_grid",
            f"{basin_id} spans cells i {lo_i:.1f}..{hi_i:.1f}, j {lo_j:.1f}..{hi_j:.1f} of a "
            f"{grid.nx}x{grid.ny} grid; the subset does not cover the whole basin",
        )
    coverage: dict[int, float] = {}
    for pts in rings:
        _accumulate_ring(pts, grid, coverage)
    cells: list[tuple[int, float]] = []
    area_km2 = 0.0
    for flat in sorted(coverage):
        weight = coverage[flat]
        if weight <= MIN_WEIGHT:
            continue
        weight = min(weight, 1.0)
        j, i = divmod(flat, grid.nx)
        cells.append((flat, weight))
        area_km2 += weight * projection.cell_area_km2(i, j)
    if not cells:
        raise MaskError("empty_mask", f"{basin_id}: no cell of this grid intersects the basin")
    return BasinMask(
        basin_id=basin_id,
        grid_definition_hash=grid.definition_hash,
        cells=tuple(cells),
        masked_area_km2=area_km2,
        polygon_source=polygon_source,
    )


# --------------------------------------------------------------------------- aggregation


@dataclass(frozen=True)
class ZonalMean:
    value: float
    weight_sum: float
    cell_count: int


def weighted_mean(values: Sequence[float | None], mask: BasinMask, *, grid: GridSpec, missing: float | None = None) -> ZonalMean:
    """Area-weighted mean of a flat value array over a mask.

    Refuses rather than approximates: a mask whose flat indices do not fit the value array is
    a grid mismatch, and a single missing value inside the basin makes the mean a mean of a
    different area — both raise :class:`MaskError` so the caller can report UNKNOWN with the
    reason instead of publishing a number computed over whatever happened to be present.
    """
    if len(values) != grid.size:
        raise MaskError("grid_size_mismatch", f"{len(values)} values for a {grid.nx}x{grid.ny} grid")
    total = 0.0
    weight_sum = 0.0
    missing_cells = 0
    for flat, weight in mask.cells:
        if flat < 0 or flat >= len(values):
            raise MaskError("cell_out_of_range", f"flat index {flat} outside a {len(values)}-value grid")
        v = values[flat]
        if v is None or (missing is not None and v == missing) or (isinstance(v, float) and math.isnan(v)):
            missing_cells += 1
            continue
        total += weight * float(v)
        weight_sum += weight
    if missing_cells:
        raise MaskError("missing_values", f"{missing_cells} of {len(mask.cells)} masked cells have no value")
    if weight_sum <= 0:
        raise MaskError("empty_weight", f"{mask.basin_id}: mask weights sum to zero")
    return ZonalMean(value=total / weight_sum, weight_sum=weight_sum, cell_count=len(mask.cells))
