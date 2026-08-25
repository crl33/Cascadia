# packages/geo — geometry, projections, masks

One job: turn polygons and grid definitions into the *weights* other packages aggregate with.
Nothing here knows what is being aggregated — no provider, no hydrology, no science. The
import-linter contract `cascade_geo is geometry only` enforces that.

## Inputs
- Reference: `../../docs/DOMAIN_MODEL.md` §3 (display geometries are materialized and
  regenerable), `../../docs/ARCHITECTURE.md` §2 (`geo/` = basins, hypsometry, topology, zonal
  aggregation, LOD geometry).
- Working: `../../tests/fixtures/geo/basins_seed_full.geojson.gz` — the FULL-resolution basin
  polygons. The `*_lod.geojson` files are for display and must never build a mask.

Do NOT load: provider adapters, hydrology methods, the web app.

## What is here
| File | Holds |
|---|---|
| `lcc.py` | `GridSpec` (a grid description) and `LambertConformalConic` (forward/inverse map, point scale factor). Owned rather than depended on: GEOS/PROJ would add tens of MB to the worker image for forty lines of Snyder. |
| `masks.py` | `build_basin_mask` (exact fractional cell weights by Sutherland-Hodgman clipping in index space), `load_basin_polygons`, `weighted_mean` (zonal aggregation that refuses rather than approximates). |

## The two rules a mask must obey
1. **Full resolution, exact fractions, true cell areas.** Counting whole cells whose centre
   falls inside the basin, at the grid's nominal spacing, over-counts by **20 %** (measured:
   1,548 cells × 6.450 km² = 9,985 km² against a WBD Cedar/Skagit area). Two errors compound —
   partial edge cells counted whole, and the Lambert scale factor ignored (a nominal 6.450 km²
   NBM cell is 5.395 km² on the ground at 48 N). The masks here reproduce WBD areas to ~0.3 %.
2. **A mask belongs to one grid definition.** `GridSpec.definition_hash` (for GRIB2, the
   sha256 of Section 3) is part of the mask's identity. If a provider silently changes its
   grid, the lookup MISSES and the caller must report UNKNOWN with the reason — never
   area-weight new values with old weights.

## Human check
Sum the mask weights, multiply by the cell areas, and compare with the basin's published WBD
area. Within a few tenths of a percent is right; anything near +20 % means whole cells are
being counted or the scale factor is missing. `tests/unit/test_forcing.py` asserts both, and
cross-checks the clipping against shapely cell by cell.
