"""Derive the river network per basin — the map's first-class hydrologic objects.

One-time, network (Overpass). "Rivers as first-class visual objects" (design direction
2026-08-28) needs actual river GEOMETRY, which nothing in the platform held: the `rivers`
layer renders forecast-point markers, and reach ids have no shapes. This fetches OSM
``waterway=river`` ways per basin bbox, merges segments by name, CLIPS to the seeded basin
polygon, simplifies for the state/basin bands, and writes
``tests/fixtures/geo/river_network.json.gz``:

- register: CARTOGRAPHIC. These are where the rivers ARE, not what they are doing; any state
  (flow, trend, category) stays on separate truth-classed elements.
- geometry caveat carried verbatim from the basin seed: clipped against the HUC8-union
  approximation, not outlet-delineated basins.
- ``mainstem``: the longest named river per basin (plus any river whose name contains the
  basin's own), so the renderer can weight the spine without inventing hydrology.
- attribution: OpenStreetMap — the same family as the basemap; the provenance block carries
  the query, date and per-basin counts.

Usage: .venv/bin/python scripts/build_river_network.py
"""

from __future__ import annotations

import gzip
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

import shapely
from shapely.geometry import LineString, shape
from shapely.ops import linemerge, unary_union

ROOT = Path(__file__).resolve().parents[1]
GEO = ROOT / "tests" / "fixtures" / "geo"
POLYGON_SOURCE = GEO / "basins_seed_full.geojson.gz"
OUT = GEO / "river_network.json.gz"

METHOD_ID = "method:river-network-osm@1.0.0"
OVERPASS = "https://overpass-api.de/api/interpreter"
UA = "CascadiaPapsukkal/0.1 (one-time river-network derivation)"
#: ~35 m at this latitude: invisible at the bands this is drawn at; the fixture lands ~4x smaller.
SIMPLIFY_DEG = 0.0004
#: fragments shorter than this (degrees, ~2 km) are clipping crumbs, not rivers
MIN_LENGTH_DEG = 0.02


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


def fetch_rivers(bbox: tuple[float, float, float, float]) -> list[dict]:
    south, west, north, east = bbox
    query = f'[out:json][timeout:90];way["waterway"="river"]({south},{west},{north},{east});out geom;'
    req = urllib.request.Request(
        OVERPASS, data=("data=" + urllib.parse.quote(query)).encode(), headers={"User-Agent": UA}
    )
    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read()).get("elements", [])
        except Exception as e:  # one polite retry; Overpass sheds load with 429/504
            if attempt == 2:
                raise
            print(f"  overpass retry after {type(e).__name__}", file=sys.stderr)
            time.sleep(20)
    return []


def main() -> int:
    geo = json.loads(gzip.decompress(POLYGON_SOURCE.read_bytes()))
    out_basins: dict[str, dict] = {}
    for feature in geo["features"]:
        basin_id = feature["properties"]["id"]
        basin_name = str(feature["properties"].get("name", ""))
        poly = unary_union([shape(p) for p in polygons_of(feature["geometry"])])
        west, south, east, north = poly.bounds
        ways = fetch_rivers((south, west, north, east))
        by_name: dict[str, list[LineString]] = {}
        for way in ways:
            coords = [(p["lon"], p["lat"]) for p in way.get("geometry", [])]
            if len(coords) < 2:
                continue
            name = (way.get("tags") or {}).get("name") or "(unnamed)"
            by_name.setdefault(name, []).append(LineString(coords))
        rivers = []
        for name, lines in by_name.items():
            unioned = unary_union(lines)
            merged = unioned if isinstance(unioned, LineString) else linemerge(unioned)
            clipped = merged.intersection(poly)
            if clipped.is_empty:
                continue
            parts = (
                [clipped] if isinstance(clipped, LineString)
                else [g for g in getattr(clipped, "geoms", []) if isinstance(g, LineString)]
            )
            kept = [
                shapely.simplify(part, SIMPLIFY_DEG)
                for part in parts
                if part.length >= MIN_LENGTH_DEG
            ]
            if not kept:
                continue
            total = sum(p.length for p in kept)
            rivers.append({
                "name": name,
                "length_deg": round(total, 4),
                "paths": [[[round(x, 5), round(y, 5)] for x, y in p.coords] for p in kept],
            })
        rivers.sort(key=lambda r: -r["length_deg"])
        longest = rivers[0]["name"] if rivers else None
        stem_word = basin_name.split("/")[0].split("-")[0].strip().lower()
        for r in rivers:
            r["mainstem"] = bool(
                r["name"] == longest
                or (stem_word and stem_word in r["name"].lower() and r["length_deg"] >= MIN_LENGTH_DEG * 5)
            )
        out_basins[basin_id] = {"rivers": rivers}
        n_stem = sum(1 for r in rivers if r["mainstem"])
        print(f"{basin_id}: {len(ways)} ways -> {len(rivers)} named rivers ({n_stem} mainstem)")
        time.sleep(3)  # Overpass politeness between basins

    doc = {
        "_provenance": {
            "method_id": METHOD_ID,
            "derived_at": datetime.now(UTC).isoformat(),
            "source": "OpenStreetMap via overpass-api.de, way[waterway=river] per basin bbox",
            "attribution": "© OpenStreetMap contributors",
            "register": "cartographic — where the rivers ARE; every state stays on truth-classed elements",
            "polygon_source": {
                "path": "tests/fixtures/geo/basins_seed_full.geojson.gz",
                "caveat": "Clipped against the seeded HUC8-union basin geometry, not outlet-delineated basins.",
            },
            "simplify_deg": SIMPLIFY_DEG,
            "min_length_deg": MIN_LENGTH_DEG,
            "mainstem_rule": "longest named river per basin, plus rivers carrying the basin's own name at >=5x the fragment floor",
        },
        "basins": out_basins,
    }
    OUT.write_bytes(gzip.compress((json.dumps(doc, separators=(",", ":")) + "\n").encode(), 9))
    print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes gz)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
