"""Live canary (network; never in CI) for the MRMS QPE path.

Three questions, in the order they would break the surface:

1. Is NODD still publishing hourly Pass2, and at what latency? The cron at :20 assumes the
   measured ~57 min; a drift past ~80 min starts missing the freshest hour every run.
2. Does the newest file still decode to the SAME grid definition? A changed Section 3 hash means
   every stored mask misses and the job rebuilds from geometry — by design, but worth seeing
   coming.
3. Do the seed basins still aggregate at full valid coverage? The coverage policy stands on that
   measurement; a Canadian-radar dropout or product change shows up here first.

Usage: .venv/bin/python -m cascade_providers_mrms.canary
"""

from __future__ import annotations

import asyncio
import gzip
import json
import sys
from datetime import UTC, datetime

import httpx

from cascade_providers_mrms.client import BUCKET_URL, QPE_PRODUCT_DIR, parse_listing
from cascade_providers_mrms.parser import parse_mrms_grib

GEO_HINT = "tests/fixtures/geo/basins_seed_full.geojson.gz"


async def check(contact: str = "cascadia-papsukkal@example.invalid") -> dict:
    report: dict = {"checked_at": datetime.now(UTC).isoformat(), "bucket": BUCKET_URL}
    try:
        async with httpx.AsyncClient(
            headers={"User-Agent": f"CascadiaPapsukkal/0.1 (canary; {contact})"}, timeout=120.0
        ) as c:
            day = datetime.now(UTC)
            r = await c.get(BUCKET_URL, params={
                "list-type": "2", "prefix": f"CONUS/{QPE_PRODUCT_DIR}/{day:%Y%m%d}/", "max-keys": "100"})
            objects = parse_listing(r.content) if r.status_code == 200 else ()
            report["listing"] = {"http_status": r.status_code, "objects_today": len(objects)}
            if not objects:
                report["error"] = "no QPE objects listed for today"
                return report
            newest = max(objects, key=lambda o: o.valid_time)
            report["newest"] = {
                "valid_time": newest.valid_time.isoformat(),
                "published": newest.last_modified.isoformat(),
                "publication_lag_min": round((newest.last_modified - newest.valid_time).total_seconds() / 60, 1),
                "age_min": round((datetime.now(UTC) - newest.last_modified).total_seconds() / 60, 1),
                "bytes": newest.size,
            }
            f = await c.get(f"{BUCKET_URL}{newest.key}")
            field = parse_mrms_grib(f.content)
            report["grid"] = {
                "nx": field.grid.nx, "ny": field.grid.ny,
                "definition_hash": field.grid.definition_hash[:16],
            }
            # per-basin coverage against the checked-in full-resolution geometry
            from cascade_geo.masks import build_basin_mask
            from cascade_providers_mrms.jobs import _aggregate, _polygons_of

            geo = json.loads(gzip.decompress(open(GEO_HINT, "rb").read()))
            coverage = {}
            for feature in geo["features"]:
                basin_id = feature["properties"]["id"]
                mask = build_basin_mask(
                    basin_id=basin_id, polygons=_polygons_of(feature["geometry"]),
                    grid=field.grid, polygon_source="full",
                )
                stats = _aggregate(mask, field.values)
                coverage[basin_id] = {
                    "valid_fraction": stats["valid_fraction"],
                    "mean_mm": None if stats["mean"] is None else round(stats["mean"], 3),
                }
            report["basins"] = coverage
            report["schema_ok"] = True
    except Exception as e:  # canaries report, never raise
        report["error"] = repr(e)
    return report


if __name__ == "__main__":
    print(json.dumps(asyncio.run(check()), indent=1))
    sys.exit(0)
