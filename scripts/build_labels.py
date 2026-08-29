"""Derive the app-owned geographic label fixture — names the platform can stand behind.

The satellite-first world (design direction 2026-08-28) stops borrowing place names from a
road-map raster, so the platform must own them. Coordinates and official names come from USGS
GNIS Domestic Names (public domain, keyless S3 download, probed live 2026-08-28); WHICH names
appear at WHICH semantic band is an EDITORIAL decision recorded here, not data — a label
hierarchy is cartographic judgment, and this script is where that judgment lives and is
reviewed.

Every curated entry is qualified (name, GNIS class, county) because GNIS names collide hard:
Washington holds a "Mount Baker" Populated Place in Seattle and the 3,286 m Summit in Whatcom
County, three "Ross Lakes", four "Baker Lakes". A required entry that fails to resolve stops
the build; an optional one (some reservoirs carry unstable names) drops with a printed
warning, never silently.

Rivers are NOT taken from GNIS points: their anchors are the midpoints of the mainstem
geometry the platform already derived (river_network.json.gz), so a river's label sits on the
river that is actually drawn. Basin labels anchor at the seed centroids.

Usage: .venv/bin/python scripts/build_labels.py
"""

from __future__ import annotations

import csv
import gzip
import io
import json
import sys
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEO = ROOT / "tests" / "fixtures" / "geo"
OUT = GEO / "labels.json"

GNIS_URL = "https://prd-tnm.s3.amazonaws.com/StagedProducts/GeographicNames/DomesticNames/DomesticNames_WA_Text.zip"
METHOD_ID = "method:labels-gnis@1.0.0"

# --- the editorial hierarchy (name, gnis_class, county, kind, tier) --------------------------
# tier semantics (consumed by layers/labels/select.ts):
#   1 = state band and down (the orientation set)   2 = basin band and down
#   3 = river band and down                          4 = local band only
REQUIRED = [
    # State-tier cities: the orientation set the doctrine names (SEMANTIC_ZOOM §2).
    ("Seattle", "Populated Place", "King", "city", 1),
    ("Tacoma", "Populated Place", "Pierce", "city", 1),
    ("Everett", "Populated Place", "Snohomish", "city", 1),
    ("Olympia", "Populated Place", "Thurston", "city", 1),
    ("Bellingham", "Populated Place", "Whatcom", "city", 1),
    # Flood-corridor towns, per seeded basin (basin band).
    ("Ferndale", "Populated Place", "Whatcom", "town", 2),
    ("Lynden", "Populated Place", "Whatcom", "town", 2),
    ("Deming", "Populated Place", "Whatcom", "town", 3),
    ("Everson", "Populated Place", "Whatcom", "town", 3),
    ("Mount Vernon", "Populated Place", "Skagit", "town", 2),
    ("Burlington", "Populated Place", "Skagit", "town", 3),
    ("Sedro-Woolley", "Populated Place", "Skagit", "town", 2),
    ("Concrete", "Populated Place", "Skagit", "town", 3),
    ("Marblemount", "Populated Place", "Skagit", "town", 3),
    ("Monroe", "Populated Place", "Snohomish", "town", 2),
    ("Snohomish", "Populated Place", "Snohomish", "town", 2),
    ("Sultan", "Populated Place", "Snohomish", "town", 3),
    ("Gold Bar", "Populated Place", "Snohomish", "town", 3),
    ("Index", "Populated Place", "Snohomish", "town", 4),
    ("Duvall", "Populated Place", "King", "town", 3),
    ("Carnation", "Populated Place", "King", "town", 2),
    ("Fall City", "Populated Place", "King", "town", 3),
    ("Snoqualmie", "Populated Place", "King", "town", 2),
    ("North Bend", "Populated Place", "King", "town", 3),
    ("Renton", "Populated Place", "King", "town", 2),
    ("Maple Valley", "Populated Place", "King", "town", 3),
    ("Auburn", "Populated Place", "King", "town", 2),
    ("Kent", "Populated Place", "King", "town", 2),
    ("Tukwila", "Populated Place", "King", "town", 3),
    ("Puyallup", "Populated Place", "Pierce", "town", 2),
    ("Sumner", "Populated Place", "Pierce", "town", 3),
    ("Orting", "Populated Place", "Pierce", "town", 2),
    ("Pacific", "Populated Place", "King", "town", 3),
    ("Buckley", "Populated Place", "Pierce", "town", 3),
    ("Enumclaw", "Populated Place", "King", "town", 3),
    # Peaks: the hydrologic skyline (rain/snow partition happens on these slopes).
    ("Mount Baker", "Summit", "Whatcom", "peak", 2),
    ("Glacier Peak", "Summit", "Snohomish", "peak", 2),
    ("Mount Rainier", "Summit", "Pierce", "peak", 1),
]
OPTIONAL = [
    # Reservoirs/lakes the reservoir intelligence already speaks about (river band).
    ("Ross Lake", "Reservoir", "Whatcom", "water", 3),
    ("Baker Lake", "Reservoir", "Whatcom", "water", 3),
    ("Lake Shannon", "Reservoir", "Skagit", "water", 3),
    ("Chester Morse Lake", "Reservoir", "King", "water", 3),
    ("Howard A Hanson Reservoir", "Reservoir", "King", "water", 3),
    ("Mud Mountain Lake", "Reservoir", "King", "water", 3),
    ("Lake Tapps", "Reservoir", "Pierce", "water", 3),
    ("Spada Lake", "Reservoir", "Snohomish", "water", 3),
    ("Lake Washington", "Lake", "King", "water", 2),
]


def gnis_rows() -> dict[tuple[str, str, str], tuple[float, float]]:
    req = urllib.request.Request(GNIS_URL, headers={"User-Agent": "CascadiaPapsukkal/0.1 (labels derivation)"})
    with urllib.request.urlopen(req, timeout=120) as r:
        blob = r.read()
    zf = zipfile.ZipFile(io.BytesIO(blob))
    txt = next(n for n in zf.namelist() if n.endswith("DomesticNames_WA.txt"))
    out: dict[tuple[str, str, str], tuple[float, float]] = {}
    with zf.open(txt) as fh:
        reader = csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8-sig"), delimiter="|")
        for row in reader:
            key = (row["feature_name"], row["feature_class"], row["county_name"])
            if key not in out:  # first occurrence wins; duplicates within a county are rare
                out[key] = (float(row["prim_long_dec"]), float(row["prim_lat_dec"]))
    return out


def main() -> int:
    gnis = gnis_rows()
    labels: list[dict] = []
    missing: list[str] = []
    for name, cls, county, kind, tier in REQUIRED:
        key = (name, cls, county)
        if key not in gnis:
            missing.append(f"{name} ({cls}, {county} County)")
            continue
        lon, lat = gnis[key]
        labels.append({"name": name, "kind": kind, "tier": tier, "lon": round(lon, 5), "lat": round(lat, 5)})
    if missing:
        print("REQUIRED names missing from GNIS — fix the curation:", *missing, sep="\n  ", file=sys.stderr)
        return 1
    for name, cls, county, kind, tier in OPTIONAL:
        key = (name, cls, county)
        if key not in gnis:
            print(f"optional label dropped (not in GNIS): {name} ({cls}, {county} County)", file=sys.stderr)
            continue
        lon, lat = gnis[key]
        labels.append({"name": name, "kind": kind, "tier": tier, "lon": round(lon, 5), "lat": round(lat, 5)})

    # Rivers: midpoint of each mainstem's longest path, from the platform's own network.
    network = json.loads(gzip.decompress((GEO / "river_network.json.gz").read_bytes()))
    n_rivers = 0
    for basin_id, basin in network["basins"].items():
        for river in basin["rivers"]:
            if not river["mainstem"]:
                continue
            path = max(river["paths"], key=len)
            lon, lat = path[len(path) // 2]
            labels.append({
                "name": river["name"], "kind": "river", "tier": 2 if river == basin["rivers"][0] else 3,
                "lon": round(lon, 5), "lat": round(lat, 5), "basin_id": basin_id,
            })
            n_rivers += 1

    # Basins: CURATED editorial anchors (visual-continuity pass 2026-08-29). A basin label is
    # analytical region context, not a place — the raw representative point landed labels in
    # the populated lowlands where they collided with cities and read as misplaced towns
    # ("CEDAR / LAKE WASHINGTON" overlapping Seattle, measured in the 2026-08-29 baseline).
    # These anchors sit in each basin's open upper country, away from its cities, rivers'
    # label anchors and neighbors. There is no mathematically correct point; this is
    # cartographic judgment, verified inside the basin geometry at build time (a curated
    # point that drifts outside the polygon falls back to representative_point, loudly).
    from shapely.geometry import Point, shape
    from shapely.ops import unary_union

    BASIN_ANCHORS = {
        "basin:skagit": (-121.30, 48.62),               # upper Skagit high country
        "basin:nooksack": (-121.95, 48.87),             # middle-fork foothills east of Deming
        "basin:snohomish-snoqualmie": (-121.45, 47.78), # Cascade front east of Sultan
        "basin:cedar": (-121.72, 47.37),                # Cedar watershed uplands
        "basin:green-duwamish": (-121.60, 47.22),       # upper Green gorge country
        "basin:puyallup-white": (-121.75, 46.98),       # upper basin toward the Rainier flank
    }

    seed = json.loads(gzip.decompress((GEO / "basins_seed_full.geojson.gz").read_bytes()))
    for feature in seed["features"]:
        props = feature["properties"]
        geom = unary_union(shape(feature["geometry"]))
        curated = BASIN_ANCHORS.get(props["id"])
        if curated and geom.contains(Point(curated)):
            lon, lat = curated
        else:
            fallback = geom.representative_point()
            lon, lat = fallback.x, fallback.y
            if curated:
                print(f"curated anchor for {props['id']} fell outside its geometry; representative_point used", file=sys.stderr)
        labels.append({
            "name": str(props.get("name", props["id"])), "kind": "basin", "tier": 1,
            "lon": round(lon, 5), "lat": round(lat, 5), "basin_id": props["id"],
        })

    doc = {
        "_provenance": {
            "method_id": METHOD_ID,
            "derived_at": datetime.now(UTC).isoformat(),
            "sources": {
                "names_coordinates": f"USGS GNIS Domestic Names (public domain), {GNIS_URL}",
                "river_anchors": "tests/fixtures/geo/river_network.json.gz mainstem midpoints (method:river-network-osm@1.0.0)",
                "basin_anchors": "curated editorial anchors in each basin's open upper country (cartographic judgment, contains-verified; fallback representative_point)",
            },
            "editorial_note": (
                "Which names label at which band is cartographic judgment recorded in "
                "scripts/build_labels.py, not derived data; every curated entry resolved against "
                "GNIS by (name, class, county) at build time."
            ),
        },
        "labels": labels,
    }
    OUT.write_text(json.dumps(doc, indent=1) + "\n")
    kinds: dict[str, int] = {}
    for label in labels:
        kinds[label["kind"]] = kinds.get(label["kind"], 0) + 1
    print(f"wrote {OUT} ({OUT.stat().st_size:,} B): {kinds} ({n_rivers} river anchors)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
