"""Derive which NWS UGC zones cover each basin — the mapping that routes alerts to basins.

CAP alerts locate themselves by UGC codes (county `WAC057`, forecast zone `WAZ311`); the basins
are polygons. This intersects the two ONCE, offline, and writes
``tests/fixtures/geo/basin_ugc.json`` so the worker can tag an incoming alert with basin ids by
code lookup alone — no geometry library in the worker, and no per-alert geometry guesswork.

Both directions of the mapping carry an overlap fraction, because the honest questions differ:

- ``zone -> basins``: an alert for WAC057 concerns every basin the county touches;
- the fraction of the ZONE inside the basin is recorded so a reader can see that an alert for a
  county that merely clips a basin corner is a weaker spatial claim than one for a county the
  basin fills. The mapping records geometry facts; POLICY (which fraction merits display) stays
  with the consumer, versioned in code.

Zones whose overlap with every basin is below ``MIN_OVERLAP_KM2`` are dropped as slivers —
boundary digitisation noise, not coverage.

Usage: .venv/bin/python scripts/build_basin_ugc.py
"""

from __future__ import annotations

import gzip
import hashlib
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx
import numpy as np
import shapely
from shapely.geometry import shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
GEO = ROOT / "tests" / "fixtures" / "geo"
POLYGON_SOURCE = GEO / "basins_seed_full.geojson.gz"
OUT = GEO / "basin_ugc.json"

METHOD_ID = "method:basin-ugc-mapping@1.0.0"
API = "https://api.weather.gov"
UA = "CascadiaPapsukkal/0.1 (offline derivation; +https://cascadia.papsukkal.com)"
R_KM = 6371.0088
MIN_OVERLAP_KM2 = 2.0


def sinusoidal(geom):
    return shapely.transform(
        geom,
        lambda coords: np.column_stack(
            [
                np.radians(coords[:, 0]) * R_KM * np.cos(np.radians(coords[:, 1])),
                np.radians(coords[:, 1]) * R_KM,
            ]
        ),
    )


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
    return []


def main() -> int:
    poly_bytes = POLYGON_SOURCE.read_bytes()
    geo = json.loads(gzip.decompress(poly_bytes))
    basins = {}
    for feature in geo["features"]:
        geom = unary_union([shape(p) for p in polygons_of(feature["geometry"])])
        basins[feature["properties"]["id"]] = {
            "geom": geom,
            "eq": sinusoidal(geom),
        }

    zone_rows: dict[str, dict] = {}
    with httpx.Client(headers={"User-Agent": UA}, timeout=60.0) as c:
        for zone_type in ("county", "forecast"):
            listing = c.get(f"{API}/zones", params={"area": "WA", "type": zone_type})
            listing.raise_for_status()
            ids = [f["properties"]["id"] for f in listing.json()["features"]]
            print(f"{zone_type}: {len(ids)} zones")
            for zone_id in ids:
                time.sleep(0.6)  # the abusive-user page asks for restraint; this is a one-time walk
                r = c.get(f"{API}/zones/{zone_type}/{zone_id}")
                if r.status_code != 200:
                    print(f"  {zone_id}: HTTP {r.status_code}, skipped", file=sys.stderr)
                    continue
                doc = r.json()
                g = doc.get("geometry")
                if not g:
                    continue
                zgeom = shape(g)
                zeq = sinusoidal(zgeom)
                overlaps = {}
                for basin_id, b in basins.items():
                    if not zgeom.intersects(b["geom"]):
                        continue
                    inter_km2 = float(zeq.intersection(b["eq"]).area)
                    if inter_km2 < MIN_OVERLAP_KM2:
                        continue
                    overlaps[basin_id] = {
                        "overlap_km2": round(inter_km2, 2),
                        "fraction_of_zone": round(inter_km2 / float(zeq.area), 4),
                        "fraction_of_basin": round(inter_km2 / float(b["eq"].area), 4),
                    }
                if overlaps:
                    zone_rows[zone_id] = {
                        "name": doc["properties"].get("name"),
                        "type": zone_type,
                        "basins": overlaps,
                    }
                    print(f"  {zone_id} {doc['properties'].get('name'):<24} -> {sorted(overlaps)}")

    out = {
        "_provenance": {
            "method_id": METHOD_ID,
            "derived_at": datetime.now(UTC).isoformat(),
            "source": f"{API}/zones/{{county|forecast}}/{{id}} geometries, area=WA",
            "polygon_source": {
                "path": "tests/fixtures/geo/basins_seed_full.geojson.gz",
                "sha256": hashlib.sha256(poly_bytes).hexdigest(),
                "caveat": "Seeded HUC8-union basin geometry, not outlet-delineated.",
            },
            "area_model": f"sinusoidal equal-area on the authalic sphere R={R_KM} km",
            "min_overlap_km2": MIN_OVERLAP_KM2,
            "note": (
                "zone -> basins with overlap fractions. The mapping records geometry facts; "
                "which fraction merits display is the consumer's versioned policy."
            ),
        },
        "zones": dict(sorted(zone_rows.items())),
    }
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes, {len(zone_rows)} zones)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
