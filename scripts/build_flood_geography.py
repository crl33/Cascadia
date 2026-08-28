"""Derive static flood-hazard geography for the seeded basins — STATIC HAZARD, never forecast.

Sources (every endpoint and attribute recipe verified live 2026-08-28 —
docs/research/flood-geography-sources-2026-08-28.md):

- FEMA NFHL MapServer layer 28 (`S_FLD_HAZ_AR`), `f=geojson`, keyless: regulatory floodway
  (`ZONE_SUBTY='FLOODWAY'`), 1%-annual-chance SFHA (`SFHA_TF='T'`), 0.2%-annual-chance
  (`ZONE_SUBTY LIKE '0.2 PCT%'`). Layer 0 answers WHERE digital data exists at all.
- USACE National Levee Database NLD2 API, keyless: levee systems near each basin, centerline
  GeoJSON per system. NLD's own terms page: data "can be downloaded, shared, and used by
  anyone" (fetched 2026-08-28).

THE SKAGIT GAP IS REAL AND MUST STAY VISIBLE: FEMA has no digital zone geometry — effective
or preliminary — for the Skagit valley floor (verified 2026-08-28), the seeded basin that
produced the December 2025 record crest. This build records `availability:
'no_digital_data'` for it, and the client renders that as explicit ABSENCE OF DATA, never as
absence of hazard.

These are REGULATORY MAP GEOMETRIES of a specific study vintage. Nothing here is a
prediction; a 1%-annual-chance zone is not "where the next flood goes"; a levee line is a
location, never a promise (VTD §3.5: never "protects").

Usage: .venv/bin/python scripts/build_flood_geography.py
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
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[1]
GEO = ROOT / "tests" / "fixtures" / "geo"
OUT = GEO / "flood_geography.json.gz"

NFHL = "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer"
NLD = "https://levees.sec.usace.army.mil/api-local"
UA = "CascadiaPapsukkal/0.1 (one-time flood-geography derivation)"
METHOD_ID = "method:flood-geography-nfhl-nld@1.0.0"

#: display simplification (~50 m) — regulatory boundaries drawn at overview scales;
#: the authoritative geometry stays at FEMA/USACE, never re-served from here.
SIMPLIFY_DEG = 0.0005
MIN_RING_AREA_DEG2 = 1e-6  # ~1 ha sliver floor after simplification
BBOX_MARGIN_DEG = 0.03

ZONE_QUERIES = {
    "floodway": "ZONE_SUBTY='FLOODWAY'",
    # NULL-subtype AE/A zones are the BULK of the SFHA; <> alone drops them (SQL null
    # semantics ate three basins' SFHA in the first honest build).
    "sfha": "SFHA_TF='T' AND (ZONE_SUBTY IS NULL OR ZONE_SUBTY<>'FLOODWAY')",
    "pct02": "ZONE_SUBTY LIKE '0.2 PCT%'",
}


def fetch_json(url: str, params: dict | None = None, retries: int = 3) -> dict:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read())
        except Exception as e:  # noqa: BLE001 — federal endpoints shed load; retry politely
            if attempt == retries:
                raise
            print(f"  retry {attempt} after {type(e).__name__}: {url[:100]}", file=sys.stderr)
            time.sleep(10 * attempt)
    raise RuntimeError("unreachable")


def nfhl_query(layer: int, bbox: tuple[float, float, float, float], where: str, *,
               geometry: bool, out_fields: str) -> list[dict]:
    """All pages of one NFHL layer query, honoring exceededTransferLimit. An ArcGIS error
    arrives as a 200 JSON body — surfaced loudly here, never read as an empty result (the
    first build passed layer-28 field names to layer 0, got errors back, and derived a
    perfectly wrong 'no coverage anywhere')."""
    west, south, east, north = bbox
    features: list[dict] = []
    offset = 0
    while True:
        doc = fetch_json(f"{NFHL}/{layer}/query", {
            "geometry": json.dumps({"xmin": west, "ymin": south, "xmax": east, "ymax": north,
                                    "spatialReference": {"wkid": 4326}}),
            "geometryType": "esriGeometryEnvelope", "inSR": 4326,
            "spatialRel": "esriSpatialRelIntersects",
            "where": where, "outFields": out_fields,
            "returnGeometry": str(geometry).lower(), "f": "geojson",
            "resultOffset": offset, "resultRecordCount": 2000,
        })
        if "error" in doc:
            raise RuntimeError(f"NFHL layer {layer} query failed: {json.dumps(doc['error'])[:300]}")
        page = doc.get("features", [])
        features.extend(page)
        if not (doc.get("exceededTransferLimit") or (doc.get("properties") or {}).get("exceededTransferLimit")):
            break
        offset += len(page)
        time.sleep(1)
    return features


def rings_of(features: list[dict]) -> list[list[list[float]]]:
    """Merge, simplify and quantize zone polygons into display rings (outer rings only —
    hole fidelity is not worth its bytes at a 50 m display simplification)."""
    geoms = []
    for f in features:
        try:
            geoms.append(shape(f["geometry"]))
        except Exception:  # noqa: BLE001 — a malformed member must not sink the class
            continue
    if not geoms:
        return []
    merged = shapely.union_all(geoms)
    merged = shapely.simplify(merged, SIMPLIFY_DEG)
    polys = getattr(merged, "geoms", [merged])
    rings: list[list[list[float]]] = []
    for poly in polys:
        if poly.is_empty or poly.area < MIN_RING_AREA_DEG2:
            continue
        rings.append([[round(x, 5), round(y, 5)] for x, y in poly.exterior.coords])
    return rings


_LEVEE_GEOMETRY_CACHE: dict[str, list[list[list[float]]]] = {}


def levees_near(lon: float, lat: float, radius_mi: int, bbox: tuple[float, float, float, float]) -> list[dict]:
    """Levee systems whose centerlines actually enter the basin bbox. The radius query casts
    wide (Puget Sound levee density is real); the bbox filter keeps only what belongs to this
    basin, and the geometry cache stops overlapping basins re-fetching the same system."""
    west, south, east, north = bbox
    systems = fetch_json(f"{NLD}/systems/query", {"sy": f"@coords:[{lon} {lat} {radius_mi} mi]"})
    out = []
    for system in systems if isinstance(systems, list) else systems.get("results", []):
        system_id = str(system.get("id") or system.get("systemId") or "")
        name = system.get("name") or system.get("systemName") or f"system {system_id}"
        if not system_id:
            continue
        if system_id not in _LEVEE_GEOMETRY_CACHE:
            try:
                geom = fetch_json(f"{NLD}/geometries/query", {
                    "type": "centerline", "systemId": system_id, "format": "geojson", "coll": "true",
                })
            except Exception as e:  # noqa: BLE001
                print(f"  levee centerline {system_id} unavailable ({type(e).__name__}); skipped", file=sys.stderr)
                _LEVEE_GEOMETRY_CACHE[system_id] = []
                continue
            paths: list[list[list[float]]] = []
            for f in geom.get("features", []):
                g = f.get("geometry") or {}
                lines = g.get("coordinates", [])
                if g.get("type") == "LineString":
                    lines = [lines]
                for line in lines:
                    pts = [[round(p[0], 5), round(p[1], 5)] for p in line if len(p) >= 2]
                    if len(pts) >= 2:
                        paths.append(pts)
            _LEVEE_GEOMETRY_CACHE[system_id] = paths
            time.sleep(0.3)
        in_bbox = [
            path for path in _LEVEE_GEOMETRY_CACHE[system_id]
            if any(west <= x <= east and south <= y <= north for x, y in path)
        ]
        if in_bbox:
            out.append({"name": str(name), "system_id": system_id, "paths": in_bbox})
    return out


_NETWORK = json.loads(gzip.decompress((GEO / "river_network.json.gz").read_bytes()))


def network_mainstem_midpoint(basin_id: str) -> tuple[float, float] | None:
    basin = _NETWORK["basins"].get(basin_id)
    if not basin:
        return None
    stems = [r for r in basin["rivers"] if r["mainstem"]]
    if not stems:
        return None
    path = max((p for r in stems for p in r["paths"]), key=len)
    lon, lat = path[len(path) // 2]
    return lon, lat


def main() -> int:
    from cascade_core.settings import SEED_FILE

    station_seed = json.loads(Path(SEED_FILE).read_text())
    outlet_coords: dict[str, tuple[float, float]] = {
        fp["basin_id"]: (fp["lon"], fp["lat"])
        for fp in station_seed.get("forecast_points", [])
        if fp.get("lon") is not None
    }
    seed = json.loads(gzip.decompress((GEO / "basins_seed_full.geojson.gz").read_bytes()))
    basins: dict[str, dict] = {}
    for feature in seed["features"]:
        basin_id = feature["properties"]["id"]
        geom = shape(feature["geometry"])
        west, south, east, north = geom.bounds
        bbox = (west - BBOX_MARGIN_DEG, south - BBOX_MARGIN_DEG, east + BBOX_MARGIN_DEG, north + BBOX_MARGIN_DEG)
        print(f"{basin_id}: bbox {tuple(round(v, 2) for v in bbox)}")

        availability = nfhl_query(0, bbox, "1=1", geometry=False, out_fields="OBJECTID")
        covered = len(availability) > 0
        # A bbox can clip a NEIGHBOR's FIRM while the basin's own valley floor is unmapped —
        # the Skagit does exactly this (coastal Anacortes/Island FIRMs at the bbox edge, zero
        # digital data on the river). The corridor probe asks layer 0 at the mainstem midpoint.
        valley_covered = covered
        if covered:
            # The floor that matters is the OUTLET reach — the lower-valley towns and
            # floodplain (the Skagit's mainstem midpoint sits in covered upper-canyon FIRMs
            # while Mount Vernon, 60 km downstream, has none — the first probe's lesson).
            probe_at = outlet_coords.get(basin_id) or network_mainstem_midpoint(basin_id)
            if probe_at is not None:
                mlon, mlat = probe_at
                probe = nfhl_query(0, (mlon - 0.02, mlat - 0.02, mlon + 0.02, mlat + 0.02),
                                   "1=1", geometry=False, out_fields="OBJECTID")
                valley_covered = len(probe) > 0
        entry: dict = {
            "availability": ("covered" if valley_covered else "partial_edges_only") if covered else "no_digital_data",
        }

        for key, where in ZONE_QUERIES.items():
            feats = nfhl_query(28, bbox, where, geometry=True, out_fields="FLD_ZONE,ZONE_SUBTY,SFHA_TF,DFIRM_ID") if covered else []
            entry[key] = rings_of(feats)
            print(f"  {key}: {len(feats)} features -> {len(entry[key])} rings")

        center = geom.representative_point()
        radius_mi = int(max(east - west, north - south) * 35) + 5  # half-span-ish at 48N
        entry["levees"] = levees_near(round(center.x, 4), round(center.y, 4), radius_mi, bbox)
        print(f"  levees: {len(entry['levees'])} systems with centerlines")
        basins[basin_id] = entry
        time.sleep(2)

    doc = {
        "_provenance": {
            "method_id": METHOD_ID,
            "derived_at": datetime.now(UTC).isoformat(),
            "sources": {
                "zones": f"FEMA NFHL MapServer layer 28 (effective only), {NFHL}",
                "availability": f"FEMA NFHL MapServer layer 0, {NFHL}",
                "levees": f"USACE National Levee Database NLD2 API, {NLD} (terms: 'can be downloaded, shared, and used by anyone', fetched 2026-08-28)",
            },
            "register": "STATIC FLOOD HAZARD — regulatory map geometry of a specific study vintage; never a prediction, never current hydrology",
            "availability_note": (
                "'partial_edges_only' means the basin bbox clips a neighbor's digital FIRM while "
                "the basin's own valley floor has no digital data (the Skagit's state, probed at "
                "the mainstem midpoint) — zones shown there belong to the bbox edges, and the "
                "valley's absence of shading is ABSENCE OF DATA."
            ),
            "caveat": (
                "FEMA-mapped zones are regulatory boundaries from studies of specific vintages; "
                "each year is an independent ~1% draw for an SFHA (~26% over 30 years); areas "
                "outside a zone also flood. Where no digital FEMA data exists (the Skagit valley "
                "floor as of 2026-08-28), absence of shading means ABSENCE OF DATA, not absence "
                "of hazard. Display geometry simplified ~50 m; the authoritative geometry is FEMA's."
            ),
            "levee_caveat": "Levee centerlines are locations from the NLD, as received. A levee line is never a statement of protection.",
            "simplify_deg": SIMPLIFY_DEG,
        },
        "basins": basins,
    }
    OUT.write_bytes(gzip.compress((json.dumps(doc, separators=(",", ":")) + "\n").encode(), 9))
    print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes gz)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
