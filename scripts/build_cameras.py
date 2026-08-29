"""Derive the flood-observation camera fixture — instruments with eyes, not a webcam list.

Sources (verified live 2026-08-28 — docs/research/camera-sources-2026-08-28.md):

- USGS HIVIS/NIMS cameras (`api.waterdata.usgs.gov/nims/cameras`): public-domain federal
  cameras AT USGS gauges, keyless, imagery on a CORS-open public S3 bucket, per-camera
  capture interval. `hideCam: true` records are excluded — USGS hid them for a reason.
- WSDOT public ArcGIS camera layer (`TravelInfoCamerasWeather/FeatureServer/0`): 1,701
  cameras, keyless, CORS-open metadata; stills hotlink from images.wsdot.wa.gov (~5 min
  refresh, "low volume use only" terms — the client refreshes only visible cameras).

RELEVANCE IS TIERS WITH REASONS, never a numeric score (mission rule). Assignments here are
computed from the platform's own fixtures — distance to the derived mainstem network,
distance to seeded gauges, containment in FEMA SFHA/floodway rings (when the flood-geography
fixture exists) — plus the one provider-stated fact worth trusting: a camera whose OFFICIAL
title names the river it watches. Orientation: WSDOT's CompassDirection is stored verbatim
when present; nothing is ever invented (no heading, no FOV).

Curated WSDOT seeds are the four flood-corridor cameras verified BY IMAGE AND RECORD on
2026-08-28 (I-5 Stillaguamish, SR 532 Stillaguamish, SR 529 Snohomish N+S, US 2 Ebey
Slough). The Kent Green River levee cameras were probed and are DEAD (one frozen at
2025-12-11, one 404) — excluded, with the lesson recorded: HTTP 200 is not freshness.

Usage: .venv/bin/python scripts/build_cameras.py
"""

from __future__ import annotations

import gzip
import json
import math
import sys
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEO = ROOT / "tests" / "fixtures" / "geo"
OUT = GEO / "cameras.json"

NIMS = "https://api.waterdata.usgs.gov/nims/cameras"
WSDOT_LAYER = "https://data.wsdot.wa.gov/arcgis/rest/services/TravelInformation/TravelInfoCamerasWeather/FeatureServer/0/query"
UA = "CascadiaPapsukkal/0.1 (one-time camera-fixture derivation)"
METHOD_ID = "method:flood-cameras@1.0.0"

#: WSDOT cameras verified by record AND image on 2026-08-28 (evidence file §1).
WSDOT_CURATED = {
    9240: "I-5 MP 209.3 — Stillaguamish River",
    9187: "SR 532 MP 3.3 — Stillaguamish River",
    9316: "SR 529 MP 4.1 — Snohomish River South",
    9317: "SR 529 MP 4.1 — Snohomish River North",
    9357: "US 2 MP 2 — Ebey Slough",
}
RIVER_WORDS = ("river", "slough", "creek")


def fetch(url: str, params: dict | None = None) -> dict | list:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read())


def deg_m(lat: float) -> float:
    return 111_320 * math.cos(math.radians(lat))


def point_to_paths_m(lon: float, lat: float, paths: list[list[list[float]]]) -> float:
    """Distance in metres from a point to the nearest vertex of any path (vertex spacing after
    simplification is ~40-100 m, so vertex distance approximates segment distance well enough
    for tiering at 150/300 m thresholds)."""
    best = math.inf
    kx = deg_m(lat)
    for path in paths:
        for px, py in path:
            d = math.hypot((px - lon) * kx, (py - lat) * 111_320)
            if d < best:
                best = d
    return best


def ring_contains(lon: float, lat: float, ring: list[list[float]]) -> bool:
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def main() -> int:
    basins = json.loads(gzip.decompress((GEO / "basins_seed_full.geojson.gz").read_bytes()))
    bboxes: dict[str, tuple[float, float, float, float]] = {}
    for f in basins["features"]:
        from shapely.geometry import shape
        west, south, east, north = shape(f["geometry"]).bounds
        bboxes[f["properties"]["id"]] = (west - 0.02, south - 0.02, east + 0.02, north + 0.02)

    network = json.loads(gzip.decompress((GEO / "river_network.json.gz").read_bytes()))
    mainstems: dict[str, list[list[list[float]]]] = {
        bid: [p for r in b["rivers"] if r["mainstem"] for p in r["paths"]]
        for bid, b in network["basins"].items()
    }

    flood_path = GEO / "flood_geography.json.gz"
    flood = json.loads(gzip.decompress(flood_path.read_bytes()))["basins"] if flood_path.exists() else None
    if flood is None:
        print("flood_geography.json.gz absent — SFHA/floodway reasons unavailable this build", file=sys.stderr)

    from cascade_core.settings import SEED_FILE

    seed = json.loads(Path(SEED_FILE).read_text())
    gauges: list[tuple[str, str, float, float]] = []  # (station_id, usgs_site, lon, lat)
    for fp in seed.get("forecast_points", []):
        if fp.get("lon") is not None:
            gauges.append((fp["station_id"], str(fp.get("usgs_site") or ""), fp["lon"], fp["lat"]))

    def basin_of(lon: float, lat: float) -> str | None:
        for bid, (w, s, e, n) in bboxes.items():
            if w <= lon <= e and s <= lat <= n:
                return bid
        return None

    def relevance(lon: float, lat: float, name: str, basin_id: str | None, at_gauge: bool) -> tuple[str, list[str]]:
        reasons: list[str] = []
        if at_gauge:
            reasons.append("at_usgs_gauge")
        if any(w in name.lower() for w in RIVER_WORDS):
            reasons.append("river_named_in_camera_title")
        if basin_id and basin_id in mainstems and mainstems[basin_id]:
            d = point_to_paths_m(lon, lat, mainstems[basin_id])
            if d < 5000:
                reasons.append(f"{int(round(d, -1))}_m_from_mainstem_river")
        if flood and basin_id and basin_id in flood:
            entry = flood[basin_id]
            if any(ring_contains(lon, lat, ring) for ring in entry.get("floodway", [])):
                reasons.append("inside_floodway")
            elif any(ring_contains(lon, lat, ring) for ring in entry.get("sfha", [])):
                reasons.append("inside_1pct_floodplain")
        for _sid, _ext, glon, glat in gauges:
            d = math.hypot((glon - lon) * deg_m(lat), (glat - lat) * 111_320)
            if d < 1000:
                reasons.append(f"{int(round(d, -1))}_m_from_gauge")
                break
        near_river = any(r.endswith("_m_from_mainstem_river") and int(r.split("_")[0]) < 400 for r in reasons)
        named = "river_named_in_camera_title" in reasons
        if at_gauge or (named and near_river) or "inside_floodway" in reasons:
            return "A", reasons
        if "inside_1pct_floodplain" in reasons or near_river or named:
            return "B", reasons
        return "C", reasons

    cameras: list[dict] = []

    # --- USGS NIMS ---------------------------------------------------------------------------
    nims = fetch(NIMS)
    seeded_nwis = {ext for _sid, ext, _lon, _lat in gauges}
    for cam in nims:
        if cam.get("stateAbrv") != "WA" or cam.get("hideCam"):
            continue
        lon, lat = float(cam["lng"]), float(cam["lat"])
        bid = basin_of(lon, lat)
        at_gauge = str(cam.get("nwisId")) in seeded_nwis
        if bid is None and not at_gauge:
            continue
        tier, reasons = relevance(lon, lat, cam.get("camName") or cam["camId"], bid, at_gauge)
        interval_min = int((cam.get("ingest") or {}).get("intr") or 60)
        cameras.append({
            "id": f"cam:usgs:{cam['camId']}",
            "provider": "usgs-nims",
            "name": cam.get("camName") or cam["camId"].replace("_", " "),
            "lon": round(lon, 5), "lat": round(lat, 5),
            "feed": "still",
            "image": {"kind": "usgs-s3", "cam_id": cam["camId"]},
            "refresh_seconds": interval_min * 60,
            "basin_id": bid,
            "nwis_id": str(cam.get("nwisId") or "") or None,
            "tier": tier, "reasons": reasons,
            "orientation": None,
            "attribution": "USGS Hydrologic Imagery Visualization and Information System (public domain)",
        })

    # --- WSDOT: curated seeds + machine-verified river-named cameras -------------------------
    # Coverage expansion (2026-08-29): beyond the 4 image-verified seeds, EVERY camera in the
    # live WSDOT layer whose OFFICIAL title names flowing water (river/slough/creek) AND whose
    # imagery is WSDOT-hosted (images.wsdot.wa.gov — the layer mixes in third-party cameras
    # identifiable only by URL host) AND whose point falls in a seeded basin bbox. The title
    # is provider metadata, not our guess; image verification remains pending for non-seeds,
    # which the tiering already expresses (named-but-unverified ranks below at-gauge).
    west = min(b[0] for b in bboxes.values()); south = min(b[1] for b in bboxes.values())
    east = max(b[2] for b in bboxes.values()); north = max(b[3] for b in bboxes.values())
    doc = fetch(WSDOT_LAYER, {
        "where": "1=1",
        "geometry": json.dumps({"xmin": west, "ymin": south, "xmax": east, "ymax": north,
                                "spatialReference": {"wkid": 4326}}),
        "geometryType": "esriGeometryEnvelope", "inSR": 4326, "spatialRel": "esriSpatialRelIntersects",
        "outFields": "OBJECTID,CameraTitle,ImageURL,CompassDirection",
        "returnGeometry": "true", "outSR": 4326, "f": "json", "resultRecordCount": 2000,
    })
    features = []
    seen_ids = set()
    for f in doc.get("features", []):
        a = f["attributes"]
        oid = a["OBJECTID"]
        title = (a.get("CameraTitle") or "").lower()
        url = a.get("ImageURL") or ""
        lon, lat = f["geometry"]["x"], f["geometry"]["y"]
        named = any(w in title for w in RIVER_WORDS)
        wsdot_hosted = url.startswith("https://images.wsdot.wa.gov/")
        in_basin = basin_of(lon, lat) is not None
        if oid in WSDOT_CURATED or (named and wsdot_hosted and in_basin):
            if oid not in seen_ids:
                features.append(f)
                seen_ids.add(oid)
    missing = set(WSDOT_CURATED) - seen_ids
    if missing:
        print(f"curated WSDOT cameras missing from the live layer: {sorted(missing)} — fix the curation", file=sys.stderr)
        return 1
    for f in features:
        a = f["attributes"]
        lon, lat = f["geometry"]["x"], f["geometry"]["y"]
        bid = basin_of(lon, lat)
        tier, reasons = relevance(lon, lat, a["CameraTitle"] or "", bid, at_gauge=False)
        heading = (a.get("CompassDirection") or "").strip() or None
        if heading:
            reasons.append("orientation_provider_stated")
        else:
            reasons.append("orientation_unknown")
        cameras.append({
            "id": f"cam:wsdot:{a['OBJECTID']}",
            "provider": "wsdot",
            "name": a["CameraTitle"] or WSDOT_CURATED[a["OBJECTID"]],
            "lon": round(lon, 5), "lat": round(lat, 5),
            "feed": "still",
            "image": {"kind": "static-url", "url": a["ImageURL"]},
            "refresh_seconds": 300,
            "basin_id": bid,
            "nwis_id": None,
            "tier": tier, "reasons": reasons,
            "orientation": {"cardinal": heading} if heading and heading != "B" else None,
            "attribution": "WSDOT Traveler Information (low-volume use; hold-harmless terms)",
        })

    doc_out = {
        "_provenance": {
            "method_id": METHOD_ID,
            "derived_at": datetime.now(UTC).isoformat(),
            "sources": {
                "usgs": f"{NIMS} (public domain; imagery: usgs-nims-images S3, CORS-open)",
                "wsdot": f"{WSDOT_LAYER} ('low volume use only' + hold-harmless licenseInfo, fetched 2026-08-28)",
            },
            "relevance_note": (
                "Tiers carry their reasons and never a numeric score. A: at a USGS gauge, or "
                "river-named title near the mainstem, or inside a mapped floodway. B: inside the "
                "1% floodplain, near the mainstem, or river-named. C: in-basin, coverage "
                "unverified. Orientation only when the provider states it; unknown stays unknown."
            ),
            "privacy_note": "Environmental/infrastructure context only. No face, person, plate or biometric processing, ever.",
            "excluded": "Kent Green River levee cameras (probed 2026-08-28: frozen at 2025-12-11 / 404 — HTTP 200 is not freshness).",
        },
        "cameras": cameras,
    }
    OUT.write_text(json.dumps(doc_out, indent=1) + "\n")
    tiers: dict[str, int] = {}
    for c in cameras:
        tiers[c["tier"]] = tiers.get(c["tier"], 0) + 1
    print(f"wrote {OUT} ({OUT.stat().st_size:,} B): {len(cameras)} cameras, tiers {tiers}")
    for c in cameras:
        print(f"  {c['tier']} {c['id']}: {c['name']} — {', '.join(c['reasons'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
