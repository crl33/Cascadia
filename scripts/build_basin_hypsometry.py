"""Derive per-basin hypsometry (elevation-area curves) from USGS 3DEP — one-time, offline.

Produces ``tests/fixtures/geo/basin_hypsometry.json``, the analytical input that turns the live
forecast snow level (`method:basin-snow-level@1.0.0`) into a rain-exposed area fraction. This is
the one blocker HYDROLOGY §7 still names.

**Why 3DEP 1-arc-second, and why nothing finer.** The DEM had to cover British Columbia: the
Skagit and Nooksack headwaters cross 49°N, and a US-clipped DEM would silently bias both basins'
curves low. Probed 2026-08-28: the staged 3DEP n50 tiles carry full valid data across the BC
side (0.000 nodata over the all-Canada tile n50w122), so the USGS bare-earth product covers the
whole domain and no mixed-source compromise is needed. Resolution is bounded by the science, not
by appetite: the snow level this curve is intersected with has a measured p10-p90 spread of
**241 m median** (HYDROLOGY §7), so 1-arc-second (~20x30 m) is already far past the point where
more resolution could change the answer. The 20 m elevation bins are likewise ~12x finer than the
median snow-level spread.

**Why this is a script and not a job.** Terrain does not change on an ingestion cadence, and the
raster dependencies (tifffile/imagecodecs/shapely) stay out of the worker image. The output JSON
ships with the container in CASCADE_GEO_DIR like every other geometry fixture, and the runtime
loader (`cascade_geo.hypsometry`) is stdlib-only.

**Overlap discipline.** Staged tiles are 3612x3612 with a 6-pixel collar beyond the nominal
1-degree cell. Every pixel is attributed to exactly one tile by keeping only centres inside the
nominal cell [lon0, lon0+1) x [lat0, lat0+1), so tile seams are counted once.

**Geometry honesty.** The polygons are the seeded HUC8 unions (`basins_seed_full.geojson.gz`) —
the same full-resolution geometry the NBM masks use, NOT outlet-delineated contributing areas.
Every consumer label must carry that caveat; the JSON records it in `_provenance`.

Usage: .venv/bin/python scripts/build_basin_hypsometry.py [--dem-dir DIR] [--out PATH]
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import shapely
import tifffile
from shapely.geometry import shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
GEO = ROOT / "tests" / "fixtures" / "geo"
POLYGON_SOURCE = GEO / "basins_seed_full.geojson.gz"

METHOD_ID = "method:basin-hypsometry@1.0.0"
DEM_PRODUCT = "USGS 3DEP 1 arc-second DEM (staged GeoTIFF, bare earth)"
DEM_URL = "https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1/TIFF/current/{tile}/USGS_1_{tile}.tif"
NODATA = -999999.0

BIN_M = 20.0
BIN_MAX_M = 4420.0  # Rainier is 4,392 m; overflow above this is recorded, not lost
R_KM = 6371.0088  # authalic sphere radius; area error vs the ellipsoid < 0.3 %

#: Independent WBD-derived areas the masks already reproduce to ~0.3 % (masks.py, design §1.4).
#: Used as a cross-check on the pixel sum — a disagreement past 1.5 % fails the build.
KNOWN_AREA_KM2 = {"basin:skagit": 8275.0}


def polygons_of(geometry: dict) -> list:
    if geometry["type"] == "Polygon":
        return [geometry]
    if geometry["type"] == "MultiPolygon":
        return [{"type": "Polygon", "coordinates": c} for c in geometry["coordinates"]]
    if geometry["type"] == "GeometryCollection":
        out: list = []
        for sub in geometry["geometries"]:
            out.extend(polygons_of(sub))
        return out
    if geometry["type"] in ("LineString", "MultiLineString", "Point", "MultiPoint"):
        # The seed collections mix rivers and points in with the basin polygons; the PostGIS
        # seed extracts polygons the same way (ST_CollectionExtract(..., 3), seed.py).
        return []
    raise ValueError(f"unsupported geometry type {geometry['type']!r}")


def sinusoidal_area_km2(geom) -> float:
    """Equal-area check independent of the pixel sum: project to sinusoidal, take planar area."""
    def project(g):
        return shapely.transform(
            g,
            lambda coords: np.column_stack(
                [
                    np.radians(coords[:, 0]) * R_KM * np.cos(np.radians(coords[:, 1])),
                    np.radians(coords[:, 1]) * R_KM,
                ]
            ),
        )
    return float(project(geom).area)


def tile_name(lat_floor: int, lon_floor: int) -> str:
    return f"n{lat_floor + 1}w{abs(lon_floor)}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dem-dir", type=Path, required=True, help="directory holding USGS_1_<tile>.tif files")
    ap.add_argument("--out", type=Path, default=GEO / "basin_hypsometry.json")
    args = ap.parse_args()

    poly_bytes = POLYGON_SOURCE.read_bytes()
    geo = json.loads(gzip.decompress(poly_bytes))

    basins: dict[str, dict] = {}
    tiles_needed: set[tuple[int, int]] = set()
    for feature in geo["features"]:
        basin_id = feature["properties"]["id"]
        geom = unary_union([shape(p) for p in polygons_of(feature["geometry"])])
        shapely.prepare(geom)
        lon0, lat0, lon1, lat1 = geom.bounds
        cells = {
            (la, lo)
            for la in range(math.floor(lat0), math.floor(lat1) + 1)
            for lo in range(math.floor(lon0), math.floor(lon1) + 1)
        }
        tiles_needed |= cells
        basins[basin_id] = {"geom": geom, "cells": cells}

    edges = np.arange(0.0, BIN_MAX_M + BIN_M, BIN_M)
    n_bins = len(edges) - 1
    hist = {b: np.zeros(n_bins) for b in basins}
    under = dict.fromkeys(basins, 0.0)
    over = dict.fromkeys(basins, 0.0)
    lo_elev = dict.fromkeys(basins, math.inf)
    hi_elev = dict.fromkeys(basins, -math.inf)
    nodata_km2 = dict.fromkeys(basins, 0.0)
    tile_meta: list[dict] = []

    for lat_floor, lon_floor in sorted(tiles_needed):
        tile = tile_name(lat_floor, lon_floor)
        path = args.dem_dir / f"USGS_1_{tile}.tif"
        if not path.exists():
            print(f"FATAL: missing DEM tile {path}", file=sys.stderr)
            return 2
        with tifffile.TiffFile(path) as tf:
            page = tf.pages[0]
            scale = page.tags["ModelPixelScaleTag"].value
            tie = page.tags["ModelTiepointTag"].value
            arr = tf.asarray()
        dx, dy = float(scale[0]), float(scale[1])
        # tiepoint maps raster (0,0) corner to (lon, lat) of the top-left corner
        lon_ul, lat_ul = float(tie[3]), float(tie[4])
        rows, cols = arr.shape
        lons = lon_ul + (np.arange(cols) + 0.5) * dx
        lats = lat_ul - (np.arange(rows) + 0.5) * dy
        # keep only centres inside THIS tile's nominal 1-degree cell — seams counted exactly once
        col_keep = (lons >= lon_floor) & (lons < lon_floor + 1)
        row_keep = (lats >= lat_floor) & (lats < lat_floor + 1)
        lons_k, lats_k = lons[col_keep], lats[row_keep]
        sub = arr[np.ix_(row_keep, col_keep)]
        # per-row pixel area on the authalic sphere
        px_area = (math.radians(dx) * R_KM) * (math.radians(dy) * R_KM) * np.cos(np.radians(lats_k))
        tile_meta.append(
            {
                "tile": tile,
                "url": DEM_URL.format(tile=tile),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
            }
        )
        lon_grid, lat_grid = np.meshgrid(lons_k, lats_k)
        for basin_id, info in basins.items():
            if (lat_floor, lon_floor) not in info["cells"]:
                continue
            geom = info["geom"]
            b_lon0, b_lat0, b_lon1, b_lat1 = geom.bounds
            box = (
                (lon_grid >= b_lon0) & (lon_grid <= b_lon1) & (lat_grid >= b_lat0) & (lat_grid <= b_lat1)
            )
            if not box.any():
                continue
            inside = np.zeros_like(box)
            inside[box] = shapely.contains_xy(geom, lon_grid[box], lat_grid[box])
            if not inside.any():
                continue
            elev = sub[inside]
            area = np.broadcast_to(px_area[:, None], sub.shape)[inside]
            bad = (elev == NODATA) | ~np.isfinite(elev)
            if bad.any():
                nodata_km2[basin_id] += float(area[bad].sum())
                elev, area = elev[~bad], area[~bad]
            if elev.size == 0:
                continue
            lo_elev[basin_id] = min(lo_elev[basin_id], float(elev.min()))
            hi_elev[basin_id] = max(hi_elev[basin_id], float(elev.max()))
            under[basin_id] += float(area[elev < edges[0]].sum())
            over[basin_id] += float(area[elev >= edges[-1]].sum())
            in_range = (elev >= edges[0]) & (elev < edges[-1])
            hist[basin_id] += np.histogram(elev[in_range], bins=edges, weights=area[in_range])[0]
        print(f"  {tile}: done")

    out: dict = {
        "_provenance": {
            "method_id": METHOD_ID,
            "derived_at": datetime.now(UTC).isoformat(),
            "dem": {"product": DEM_PRODUCT, "nodata": NODATA, "tiles": tile_meta},
            "polygon_source": {
                "path": "tests/fixtures/geo/basins_seed_full.geojson.gz",
                "sha256": hashlib.sha256(poly_bytes).hexdigest(),
                "caveat": (
                    "Seeded HUC8-union basin geometry, NOT an outlet-delineated contributing "
                    "area. Every fraction computed from these curves inherits that caveat and "
                    "must say so."
                ),
            },
            "bins": {"origin_m": 0.0, "width_m": BIN_M, "max_m": BIN_MAX_M},
            "area_model": f"authalic sphere R={R_KM} km; pixel area = (dx*dy rad^2)*R^2*cos(lat)",
            "pixel_rule": "pixel centres inside the tile's nominal 1-degree cell only (collar dropped)",
            "script": "scripts/build_basin_hypsometry.py",
        },
        "basins": {},
    }

    failures: list[str] = []
    for basin_id, info in sorted(basins.items()):
        counts = hist[basin_id]
        total = float(counts.sum()) + under[basin_id] + over[basin_id]
        check = sinusoidal_area_km2(info["geom"])
        rel = abs(total - check) / check
        known = KNOWN_AREA_KM2.get(basin_id)
        known_rel = abs(total - known) / known if known else None
        if rel > 0.015:
            failures.append(f"{basin_id}: pixel sum {total:.0f} vs equal-area {check:.0f} km2 ({rel:.2%})")
        if known_rel is not None and known_rel > 0.015:
            failures.append(f"{basin_id}: pixel sum {total:.0f} vs WBD {known:.0f} km2 ({known_rel:.2%})")
        if nodata_km2[basin_id] > 0.001 * total:
            failures.append(f"{basin_id}: {nodata_km2[basin_id]:.1f} km2 of nodata inside the polygon")
        out["basins"][basin_id] = {
            "total_km2": round(total, 3),
            "under_km2": round(under[basin_id], 3),
            "over_km2": round(over[basin_id], 3),
            "nodata_km2": round(nodata_km2[basin_id], 4),
            "min_m": round(lo_elev[basin_id], 1),
            "max_m": round(hi_elev[basin_id], 1),
            "counts_km2": [round(float(c), 4) for c in counts],
            "equal_area_check_km2": round(check, 3),
        }
        print(
            f"  {basin_id:<28} {total:8.1f} km2 (equal-area {check:8.1f}, "
            f"{rel:.2%}) elev {lo_elev[basin_id]:6.1f}..{hi_elev[basin_id]:6.1f} m"
        )

    if failures:
        print("BUILD FAILED:", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        return 1

    args.out.write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {args.out} ({args.out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
