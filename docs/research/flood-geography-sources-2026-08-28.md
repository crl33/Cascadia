# Static flood-hazard geography for the six seeded basins — source verification

**Date:** 2026-08-28 (all probes run this day, keyless, via `curl` from this workstation)
**Scope:** authoritative, machine-readable static flood-hazard geography for the seeded basins
(Skagit, Snohomish–Snoqualmie, Cedar, Green–Duwamish, Puyallup–White, Nooksack).
**Method:** every claim below is tagged **VERIFIED** (endpoint fetched today, sample recorded),
**REPORTED** (stated by a page read today, not independently exercised), or **UNVERIFIED**.

---

## 1. FEMA NFHL — National Flood Hazard Layer REST service

### 1.1 Service directory — VERIFIED 2026-08-28

- URL: `https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer?f=json`
- HTTP 200, `application/json`. ArcGIS Server `currentVersion: 11.1`, document Version `2.9.0`.
- Capabilities: `Map,Query,Data`. `maxRecordCount: 2000`. Supported query formats: **JSON, geoJSON, PBF**.
- There is **no public NFHL FeatureServer** at this path: `.../public/NFHL/FeatureServer?f=json`
  returns HTTP 200 wrapping `{"error":{"code":500,"message":"...Server object extension
  'featureserver' not found."}}` (VERIFIED 2026-08-28). The MapServer's layer-level `/query`
  with `f=geojson` is the machine-readable route.

### 1.2 Layer ids that matter (from the service directory, VERIFIED 2026-08-28)

| Layer id | Name | Geometry | Relevance |
|---|---|---|---|
| **28** | Flood Hazard Zones (`S_FLD_HAZ_AR`) | polygon | THE layer: 1% zones, 0.2% zones, floodway are all rows here, distinguished by attributes |
| 27 | Flood Hazard Boundaries | polyline | zone boundary lines only |
| 23 | Levees | polyline | FEMA's accredited-levee lines (complement to USACE NLD) |
| 16 | Base Flood Elevations | polyline | BFE lines |
| 14 | Cross-Sections | polyline | stream cross-sections |
| 3 | FIRM Panels | polygon | panel footprints + effective dates |
| 1 | LOMRs | polygon | Letters of Map Revision footprints |
| 0 | NFHL Availability | polygon | where digital NFHL data exists at all — query this FIRST |

There is **no separate "floodway" or "0.2% annual chance" layer id**: both live inside
layer 28 as attribute values of `ZONE_SUBTY` (see §1.4).

### 1.3 Layer 28 schema — VERIFIED 2026-08-28

`https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28?f=json` → fields include
`DFIRM_ID`, `FLD_AR_ID`, `STUDY_TYP`, `FLD_ZONE`, `ZONE_SUBTY`, `SFHA_TF`, `STATIC_BFE`,
`V_DATUM`, `DEPTH`, `AR_REVERT`, `DUAL_ZONE`, `SOURCE_CIT`, `GlobalID`.
Note: **no effective-date field on layer 28 itself** — a query naming `EFF_DATE` in
`outFields` fails with HTTP 200 / `{"error":{"code":400,"message":"Failed to execute query."}}`
(VERIFIED today, first attempt). Effective dates live on FIRM Panels (layer 3) / LOMRs (layer 1).

### 1.4 Live GeoJSON query test — VERIFIED 2026-08-28

Small envelope over the Cedar basin at Renton (47.47–47.49 N, −122.22–−122.19 E):

```
POST https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query
  geometry={"xmin":-122.22,"ymin":47.47,"xmax":-122.19,"ymax":47.49,"spatialReference":{"wkid":4326}}
  geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects
  outFields=FLD_ZONE,ZONE_SUBTY,SFHA_TF,STATIC_BFE,DFIRM_ID
  returnGeometry=true&resultRecordCount=2&f=geojson
```

→ HTTP 200, `application/geo+json`, a real `FeatureCollection` with WGS-84 polygon rings and
properties e.g. `{"FLD_ZONE":"X","ZONE_SUBTY":"AREA OF MINIMAL FLOOD HAZARD","SFHA_TF":"F",
"STATIC_BFE":-9999,"DFIRM_ID":"53033C"}`. GeoJSON out: **confirmed**.

Attribute selection recipe (schema-derived; the floodway/0.2% value strings are exercised in §1.5):
- 1%-annual-chance (SFHA): `SFHA_TF='T'` (zones A, AE, AH, AO, VE…)
- Regulatory floodway: `ZONE_SUBTY='FLOODWAY'` on layer 28
- 0.2%-annual-chance: `FLD_ZONE='X'` with `ZONE_SUBTY='0.2 PCT ANNUAL CHANCE FLOOD HAZARD'`

### 1.5 Attribute selection — value strings exercised live, VERIFIED 2026-08-28

Same Renton-area envelope, `where` clause on layer 28:
- `ZONE_SUBTY='FLOODWAY'` → rows like `{"FLD_ZONE":"AE","ZONE_SUBTY":"FLOODWAY","SFHA_TF":"T"}`
- `ZONE_SUBTY LIKE '0.2 PCT%'` → rows `{"FLD_ZONE":"X","ZONE_SUBTY":"0.2 PCT ANNUAL CHANCE
  FLOOD HAZARD","SFHA_TF":"F"}`

Both value strings are exact and live. `SFHA_TF='T'` marks the 1%-annual-chance (SFHA) rows.

### 1.6 Basin coverage reality check — VERIFIED 2026-08-28

Layer 0 (NFHL Availability) polygon counts by envelope, identical query syntax throughout
(syntax proven good by the Renton hit):

| Envelope | Availability polygons | Reading |
|---|---|---|
| Mount Vernon (48.41–48.43, −122.34…−122.32) | **0** | no digital NFHL at all |
| Lower Skagit County wide (48.30–48.60, −122.60…−121.80) | 2 — `STUDY_ID` 53029C (Island Co.) and 530317 (extent −122.70…−122.53, 48.45–48.52 = Fidalgo Is./Anacortes area) | **neither touches the Skagit River floodplain** |
| Snohomish–Monroe (Snohomish basin) | 1 | covered |
| Renton (Cedar basin) | 1 | covered (DFIRM `53033C`, King Co.) |
| Kent–Auburn (Green–Duwamish) | 4 | covered |
| Puyallup–Orting (Puyallup–White) | 3 | covered |
| Ferndale–Lynden (Nooksack) | 1 | covered |

**Layer 28 at the Mount Vernon envelope returns an empty FeatureCollection.** Five of the six
seeded basins have digital NFHL coverage; **the Skagit River valley — the flagship basin, site
of the Dec-2025 record crest — has none.** (Skagit County's FIRMs are known to be old/paper;
the cause was not verified today — only the coverage absence was.)

### 1.7 Terms / limits — VERIFIED 2026-08-28

- VERIFIED (service metadata): `copyrightText` empty; `maxRecordCount` 2000 per query; no API
  key required for any query run today.
- VERIFIED (FEMA's own services page,
  `https://hazards.fema.gov/femaportal/resources/flood_map_svc.htm`, fetched today —
  `https://www.fema.gov/flood-maps/national-flood-hazard-layer` returns **403 to both WebFetch
  and curl**, so the hazards-portal page is the citable copy):
  - "The data depict **effective** flood hazard information" — this service is effective-only.
  - "**Not all effective Flood Insurance Rate Maps (FIRM) have geographic information system
    (GIS) data available.**" — FEMA's own words for the §1.6 Skagit gap.
  - hazards.fema.gov requires TLS 1.2 with modern cipher suites.
  - Mapping spec is 1:12,000-scale; NFHL stored in NAD83 (the availability layer answers in
    WKID 4269; `f=geojson` answers came back in WGS-84 lon/lat).
  - Bulk county/state downloads are via the FEMA Map Service Center ("Search All Products").

---

## 2. Washington Ecology's NFHL mirror

### 2.1 What exists — VERIFIED 2026-08-28

Ecology does NOT expose an `/arcgis/rest/services` root on `gis.ecology.wa.gov` or
`apps.ecology.wa.gov` (404 with browser UA; 403 from the Azure gateway without one — probed
today). Its flood data is reachable through the **Coastal Atlas** stack, discovered by walking
the "Flood Hazard Areas" web-app config
(`https://gis.ecology.wa.gov/portal/sharing/rest/content/items/7779e901b22340f8892c8dcb1181a677/data`,
webmap `31fd508e07314fe685bad60d2b0c5a32`, both fetched today):

- Tiles (render-only): `https://gis.ecology.wa.gov/hosting/rest/services/Hosted/TileLayer_Flood/MapServer`
- **Queryable feature layer:** `https://gis.ecology.wa.gov/serverext/rest/services/GIS/CoastalAtlas/MapServer/333`
  ("Flood (identify)", polygon, capabilities `Map,Query,Data`, formats **JSON, geoJSON, PBF**,
  `maxRecordCount` 2000 — all VERIFIED from its `?f=json` today).

### 2.2 Schema — better than FEMA's in one respect — VERIFIED 2026-08-28

Layer 333 carries the full `S_FLD_HAZ_AR` field set (`FLD_ZONE`, `ZONE_SUBTY`, `SFHA_TF`,
`STATIC_BFE`, …) **pre-joined to FIRM-panel fields including `EFF_DATE` and `PRE_DATE`** —
one query yields zone + effective date, which FEMA's layer 28 cannot do alone. Renton test
query returned e.g. `{"FLD_ZONE":"AE","SFHA_TF":"T","DFIRM_ID":"53033C","EFF_DATE":
2020-08-19 (epoch-ms 1597795200000),"STUDY_TYP":"NP"}`.

### 2.3 The Skagit difference — and its trap — VERIFIED 2026-08-28

At the Mount Vernon envelope, Ecology's layer 333 returns **1 polygon where FEMA returns 0**
— but it is **geometry-only**: every NFHL attribute is null (`OBJECTID` 76392,
`Shape_Area` ≈ 2.12e8 m², ≈212 km², clearly a digitized lower-Skagit floodplain outline).
No zone, no effective date, no source citation is recoverable from the API. Ecology's layer is
therefore **not a faithful NFHL mirror**: it is NFHL plus unattributed digitized areas.
Usable as *"a FEMA-derived floodplain outline exists here"* — never as a zone determination.
Provenance for that polygon is UNVERIFIED (Ecology's flood-download page says shapefiles are
distributed "as received"; which paper FIRM produced this outline could not be determined
from the API today).

---

## 3. USACE National Levee Database (NLD)

### 3.1 The API — VERIFIED 2026-08-28

- The NLD web app is backed by a **documented public REST API**: "NLD2 API", **v4.40.0**,
  OpenAPI 3.1.0, base `https://levees.sec.usace.army.mil/api-local/`. The interactive
  (Scalar) reference is at `https://levees.sec.usace.army.mil/developer/` — the full OpenAPI
  spec is embedded in that page (fetched and parsed today, **155 paths**).
- Sanity check VERIFIED: `GET /api-local/test/hello` → HTTP 200
  `{"message":"Hello, stranger!"}`. No key required for anything exercised today.
- Naive guesses (`/api-local/systems`, `/levees`, `/geodata`…) 404 — the real routes are
  below. Note the server rewrites `/api-local/*` to `/api/*` internally (visible in 404
  bodies).

### 3.2 Routes that matter (from the spec; each listed live-tested unless noted)

| Route | What it returns | Status today |
|---|---|---|
| `GET /systems/query?sy=@coords:[lon lat radius unit]` | levee systems near a point (redisearch syntax; unit `mi|ft|km|m`) | VERIFIED: `[-122.336 48.417 10 mi]` → **24 systems** incl. "North Fork Skagit River Levee" (systemId 2005100151), "Dry Slough Levee", "Big Indian Slough" |
| `GET /leveed-areas-{systemId}.geojson` | leveed areas as GeoJSON FeatureCollection | VERIFIED: systemId 2005100151 → HTTP 200, 1 MultiPolygon feature, props `leveedId`, `fcSystemId` |
| `GET /geometries/query?type=centerline&systemId=…&format=geojson&coll=true` | levee centerline GeoJSON | VERIFIED: same system → HTTP 200, MultiLineString FeatureCollection (3-D coords: lon, lat, z) |
| `GET /system/{id}/detail` | full system detail | in spec; not exercised today |
| `POST /download/dataset/geojson.zip` (also `gpkg`, `shapefile`, `csv`) | bulk dataset download | in spec; not exercised today |
| `GET /coordinate-lookup?type=system&longitude=…&latitude=…` | point-in-leveed-area lookup | probed today → **HTTP 500 "Database Error"** (either the `type` value or a server-side fault; treat as unreliable until re-probed) |
| `GET /systems/names?ids=…` | id→name map | VERIFIED to demand `ids` (HTTP 400 without it) |

### 3.3 Terms — VERIFIED 2026-08-28

`https://levees.sec.usace.army.mil/about/about-the-data/` (fetched today, HTTP 200), under
"Data Sharing": "Data within the National Levee Database can be downloaded, shared, and used
by anyone." Helpdesk: NLD@usace.army.mil / 1-877-538-3387.

---

## 4. NID — National Inventory of Dams

### 4.1 Endpoint — VERIFIED 2026-08-28

Base: `https://nid.sec.usace.army.mil/api` (keyless; probed today):

- `GET /api/query?sy=@stateKey:WA&format=json` → HTTP 200, JSON array of WA dams, each with
  `id`, `federalId`, `name`, `latitude`, `longitude`, `publicHazardId`, `nidHeight`, `eapId`,
  owner/purpose ids. (Same redisearch idiom as the NLD API — they share a platform.
  `sy=@state:(Washington)` also works.)
- `GET /api/suggestions?text=skagit` → HTTP 200; returns the Skagit-basin hydro dams:
  **Ross (WA00169), Diablo (WA00170), Gorge (WA00168)** in Whatcom Co., Skagit Lake Dam
  (WA00182), Judd… (truncated in sample).
- `GET /api/nation/csv` → HTTP 200, `application/octet-stream`, **67,284,928 bytes** — full
  national bulk CSV, no key.
- `GET /api/dams/{id}` → 404 (not a route); use `/api/query` or `/api/suggestions`.
- No OpenAPI spec found at `/api/openapi.json` (404). Terms page not fetched today —
  UNVERIFIED beyond the above; NID is USACE public data like NLD (REPORTED, same
  levees.sec.usace.army.mil "About the Data" family).

---

## 5. Data-currency caveats and honest UI language

### 5.1 Effective vs preliminary — VERIFIED 2026-08-28 (FEMA's services page + live services)

- The public NFHL service is **effective-only**; pre-effective data lives in a separate
  service, probed live today:
  `https://hazards.fema.gov/arcgis/rest/services/PrelimPending/Prelim_NFHL/MapServer`
  (layer 0 = Preliminary Data Availability, layer 28 = Preliminary Flood Hazard Zones —
  same layer-id scheme as the effective service).
- FEMA's page (fetched today, §1.7 URL): preliminary data "are for review and guidance
  purposes only … subject to change … cannot be used to rate flood insurance policies";
  "FEMA will remove preliminary data once pending data are available"; pending data likewise
  until effective. Layers "are updated as new preliminary and pending data becomes available."
- **Skagit is absent from BOTH**: the wide Skagit envelope returns 0 preliminary-availability
  polygons and the Mount Vernon envelope returns `{"count":0}` from Preliminary Flood Hazard
  Zones (both VERIFIED today). The Skagit gap is total on FEMA's machine-readable side:
  no effective, no preliminary.

### 5.2 Effective dates — VERIFIED 2026-08-28

- FEMA layer 28 has no date field; dates come from FIRM Panels (layer 3): Renton test →
  `FIRM_PAN 53033C0977G, EFF_DATE 2020-08-19, PANEL_TYP "Countywide, Panel Printed"`.
- Ecology's layer 333 has `EFF_DATE` pre-joined (same 2020-08-19 for King Co.) — convenient,
  but its unattributed areas (§2.3) carry NULL dates.
- LOMRs (FEMA layer 1) amend panels after their effective date — a zone polygon's panel date
  is not the last word; LOMR footprints must be checked for the "as amended" story.

### 5.3 What a UI must say about a 1%-annual-chance zone (house-rule-compliant language)

- "1% annual chance" ≠ "safe outside the line": each year is an independent ~1% draw
  (~26% chance over a 30-year mortgage), and the line is a regulatory boundary drawn from a
  study of a specific vintage — not a prediction for any particular flood.
- Honest caption for these polygons, given what was verified today:
  *"FEMA-mapped 1%-annual-chance flood zone (Special Flood Hazard Area). Regulatory map
  geometry, effective as of the panel date shown; it reflects the underlying flood study,
  not current conditions or any live forecast. Areas outside the zone also flood. Where no
  digital FEMA data exists (e.g. the Skagit valley floor), absence of shading means ABSENCE
  OF DATA, not absence of hazard."*
- The Dec-2025 Skagit record crest happened in the one seeded basin with **no** digital FEMA
  zone geometry — the strongest possible argument for the UNKNOWN-is-a-legitimate-state rule:
  render the Skagit gap as explicit UNKNOWN, never as blank/no-hazard.

---

## 6. Summary for the platform

| Need | Source | Machine-readable? | Verdict (2026-08-28) |
|---|---|---|---|
| 1% / 0.2% zones + floodway, 5 of 6 basins | FEMA NFHL MapServer layer 28, `f=geojson` | yes (GeoJSON/PBF, 2000 rec/query, keyless) | VERIFIED, use as primary |
| Effective dates | FEMA layer 3 (panels) + layer 1 (LOMRs); or Ecology layer 333 pre-joined | yes | VERIFIED |
| Skagit valley zones | none: FEMA effective 0, FEMA preliminary 0; Ecology has one geometry-only outline | outline only, zero attributes | VERIFIED GAP — render as UNKNOWN |
| Levee centerlines + leveed areas | NLD2 API v4.40.0 (`/api-local/`) | yes (GeoJSON, keyless) | VERIFIED, incl. Skagit-delta systems |
| Dam locations | NID `/api/query`, `/api/nation/csv` | yes (JSON/CSV, keyless) | VERIFIED |
| WA-state NFHL mirror as *authority* | Ecology CoastalAtlas layer 333 | yes, but hybrid provenance | use only as supplement; never as zone authority |

## 7. Retrieval log (all 2026-08-28, keyless)

- `https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer?f=json` — 200
- `.../public/NFHL/FeatureServer?f=json` — error 500 in 200 body (no FeatureServer)
- `.../NFHL/MapServer/28?f=json`, `/28/query` (Renton geojson; floodway; 0.2 PCT; Mount Vernon empty) — 200
- `.../NFHL/MapServer/0/query` (7 basin envelopes + STUDY_ID extent) — 200
- `.../NFHL/MapServer/3/query` (panel EFF_DATE) — 200
- `https://hazards.fema.gov/arcgis/rest/services/PrelimPending/Prelim_NFHL/MapServer?f=json`, `/0/query`, `/28/query` — 200
- `https://hazards.fema.gov/femaportal/resources/flood_map_svc.htm` — 200
- `https://www.fema.gov/flood-maps/national-flood-hazard-layer` — **403** (both fetch paths)
- `https://gis.ecology.wa.gov/portal/sharing/rest/content/items/{app,webmap}/data?f=json` — 200
- `https://gis.ecology.wa.gov/serverext/rest/services/GIS/CoastalAtlas/MapServer/333` (`?f=json` + queries) — 200
- `https://gis.ecology.wa.gov/arcgis/rest/services`, `apps.ecology…`, `…/serv/rest/services` — 403/404 (no such roots)
- `https://levees.sec.usace.army.mil/developer/` — 200 (OpenAPI 3.1.0 embedded, NLD2 API 4.40.0)
- `https://levees.sec.usace.army.mil/about/about-the-data/` — 200 (data-sharing terms)
- `https://levees.sec.usace.army.mil/api-local/test/hello`, `/systems/query`, `/leveed-areas-2005100151.geojson`, `/geometries/query` — 200; `/coordinate-lookup` — 500; `/systems/names` (no ids) — 400
- `https://nid.sec.usace.army.mil/api/query?sy=@stateKey:WA`, `/api/suggestions?text=skagit`, `/api/nation/csv` — 200; `/api/openapi.json`, `/api/dams/{id}` — 404

**Not verified today:** cause of the Skagit digital-map gap; NID formal terms-of-use page;
NLD `/coordinate-lookup` reliability; provenance of Ecology's geometry-only Skagit polygon;
NLD bulk `POST /download/dataset/*.zip` behavior.
