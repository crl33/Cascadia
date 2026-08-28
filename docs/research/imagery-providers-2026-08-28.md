# Satellite/Aerial Imagery Providers for the Cesium Web Map — Evidence File

**Date:** 2026-08-28
**Scope:** Imagery providers usable as CesiumJS imagery layers over Washington State, production use,
ion-free preference, cost-conscious. Every claim below is tagged:

- **VERIFIED** — fetched today (2026-08-28) via curl or a web fetch; URL and probe recorded beside the claim.
- **REPORTED** — stated by a page read today, but not independently confirmed (e.g. a page describing another service).
- **UNVERIFIED** — could not be confirmed today; treat as unknown.

Probe tile used throughout (over the Sauk/Skagit country, lat 48.3 N, lon −121.5 W, WebMercator):
`z=10, x=166, y=354` (computed via the standard slippy-map formula; ArcGIS tile path order is `/tile/{z}/{y}/{x}`).

**Status: COMPLETE — all planned probes and terms fetches ran 2026-08-28; unresolved items are
listed in "What could NOT be verified today" at the end.**

---

## 1. USGS The National Map — `USGSImageryOnly` (probed)

**Endpoint (VERIFIED 2026-08-28, curl):**
`https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer`

- **Service metadata** (`?f=json`) — HTTP 200, `application/json`. `currentVersion: 11.3`,
  `singleFusedMapCache: true`, WebMercator (`wkid 102100 / latestWkid 3857`), 256×256 tiles,
  `tileInfo.format: MIXED` (probed tiles came back JPEG), LOD table lists levels 0–23 **but**
  `maxScale: 9027.977411` — i.e. cached only to **level 16** ("visible to the 1:9,028 zoom scale",
  per the service's own description text). VERIFIED.
- **Tile probes** (VERIFIED, curl, 2026-08-28):
  - `tile/10/354/166` (lat 48.3, lon −121.5) → **200**, `image/jpeg`, 18,589 B, real imagery.
  - `tile/16/22699/10649` (same area, z16) → **200**, `image/jpeg`, 21,334 B.
  - `tile/16/22888/10498` (downtown Seattle, z16) → **200**, `image/jpeg`, 35,665 B.
  - `tile/17/45398/21299` and `tile/17/45776/20996` (z17, rural + Seattle) → **404**.
  - **Conclusion: hard max zoom = 16 over Washington (everywhere).** VERIFIED.
- **Keyless:** yes — all probes made with zero credentials or keys. VERIFIED.
- **CORS:** `access-control-allow-origin: *` on both metadata and tile responses (probed with
  `Origin: https://example.org`). Served via CloudFront (`x-cache` headers), tile `cache-control: max-age=86400`. VERIFIED.
- **Copyright text in service metadata (VERIFIED):**
  `"USDA, USGS The National Map: Orthoimagery. Data refreshed June, 2024."`
- **Content:** service description says orthoimagery resolution 6 in–1 m, with Blue Marble/Landsat at
  small scales. VERIFIED (from the service's own JSON).
- Usage policy / attribution requirement from USGS pages: see §1a below.

**Cesium wiring:** `UrlTemplateImageryProvider` with
`https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}`,
`maximumLevel: 16` (or `ArcGisMapServerImageryProvider` pointed at the MapServer root — no token).

## 3. Esri World Imagery — `server.arcgisonline.com` (probed)

**Endpoint (VERIFIED 2026-08-28, curl):**
`https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer`

- **Service metadata** — HTTP 200. `currentVersion: 11.3`, `singleFusedMapCache: true`,
  `tileInfo.format: JPEG`, 256×256, LODs 0–23, capabilities `Map,Query,Data,Tilemap`.
  `copyrightText: "Source: Esri, Vantor, Earthstar Geographics, and the GIS User Community"`.
  Description: "one meter or better satellite and aerial imagery in many parts of the world…
  0.5m resolution across the United States". VERIFIED.
- **Tile probes** (VERIFIED, all keyless, all 200 `image/jpeg`):
  - `tile/10/354/166` (Sauk country) → 200, 13,828 B.
  - `tile/18/90797/42598` (rural z18) → 200, 14,171 B.
  - `tile/19/181595/85196` (rural z19) → 200, 12,867 B — and the `tilemap/19/…/8/8` query returns
    all-1s (`valid: true`), i.e. **real cached tiles exist at z19 even in the rural Sauk valley**.
  - `tile/19/183104/83985` (Seattle z19) → 200; `tile/20/366208/167970` (Seattle z20) → 200 but only
    2,521 B (visibly low-content; treat 19 as the reliable max over WA).
- **CORS:** `Access-Control-Allow-Origin: *` on metadata and tiles. `cache-control: max-age=86400`. VERIFIED.
- **Keyless at the HTTP level: yes — no token was needed for any probe today.** VERIFIED.
  Whether Esri's *terms* permit production use without an account/key is a separate question — §3a below.

## 4. EOX Sentinel-2 cloudless (probed)

**Endpoint (VERIFIED 2026-08-28, curl):** `https://tiles.maps.eox.at/wmts/1.0.0/WMTSCapabilities.xml`
(HTTP 200; capabilities parsed today).

- **Layers available (VERIFIED from capabilities):** `s2cloudless-2017` … `s2cloudless-2025`
  (plus unsuffixed `s2cloudless` = the original release), each in EPSG:4326 and `_3857` WebMercator
  variants. Note: **the 2016 layer no longer appears in the capabilities document.**
- **Tile template (VERIFIED, from the capabilities `ResourceURL` for `s2cloudless-2025_3857`):**
  `https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2025_3857/default/GoogleMapsCompatible/{TileMatrix}/{TileRow}/{TileCol}.jpg`
  — format `image/jpeg` only for the 3857 variant; TileMatrixSet `GoogleMapsCompatible` advertises
  **levels 0–21** with no per-layer limits.
- **Tile probes (VERIFIED):** z10/z13/z16/z18 over lat 48.3 −121.5 all → 200 `image/jpeg`
  (14,737 / 8,773 / 4,039 / 1,443 B). The shrinking payloads above z13–14 are upsampling: the source
  is 10 m Sentinel-2, so **useful max zoom ≈ 13–14**; the server will happily serve blurry tiles to 21.
- **CORS (VERIFIED):** echoes the request origin — `access-control-allow-origin: https://example.org`
  + `access-control-allow-credentials: true`, `vary: origin`. Fine for browser use.
- **License (VERIFIED — embedded in the capabilities abstract for the 2025 layer):**
  "EOxCloudless … by EOX IT Services GmbH (Contains modified Copernicus Sentinel data 2025) released
  under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License. For
  commercial usage please see https://cloudless.eox.at" — i.e. **CC BY-NC-SA 4.0; NOT licensed for
  commercial production use without a purchased license.** See §4a for the terms page.

## 2. USDA NAIP (probed routes)

- **`imagery.nationalmap.gov` (VERIFIED 2026-08-28):** services root lists exactly two image
  services: `USGSNAIPImagery:ImageServer` and `USGSNAIPPlus:ImageServer`.
- **`USGSNAIPPlus/ImageServer` metadata (VERIFIED):** dynamic ImageServer — `tileInfo` absent, no
  fused cache; `pixelSizeX/Y ≈ 0.3 m`; `maxImageWidth/Height 4000`; capabilities
  `Image,Metadata,Catalog,Mensuration`; `copyrightText: "USGS, USDA, The National Map: Orthoimagery.
  March 12, 2025."`
- **`exportImage` probe (VERIFIED):** 512×512 JPEG over WA (bbox in EPSG:3857) → 200 `image/jpeg`,
  38,965 B, keyless, **CORS `access-control-allow-origin: *`**. So NAIP-derived imagery is reachable
  as a *dynamic* (non-tiled) service — usable in Cesium via WMS-style providers but every pan/zoom
  hits the ArcGIS exporter; fine for reference, not a high-traffic basemap.
- **WMS facade (VERIFIED on retry):** first GetCapabilities attempt timed out at 30 s; a 45 s retry
  returned 200 `text/xml` (9,770 B) from
  `https://imagery.nationalmap.gov/arcgis/services/USGSNAIPPlus/ImageServer/WMSServer?request=GetCapabilities&service=WMS`
  with layers `USGSNAIPPlus:NaturalColor`, `USGSNAIPPlus:FalseColorComposite` (+ NDVI). The service
  is up but slow to cold-start — budget generous timeouts.
- **`USGSNAIPImagery/ImageServer` (VERIFIED):** same shape (dynamic, no tile cache, 4000 px max,
  ~0.3 m pixel size); description: "a mosaic primarily of 0.6 meter resolution 4-band imagery
  presented in natural color" with CIR/NDVI templates; `copyrightText: "USGS, USDA, The National
  Map: Orthoimagery. January 09, 2025."`
- **NAIP index probe (VERIFIED, odd result):**
  `https://index.nationalmap.gov/arcgis/rest/services/USGSNAIPImageryIndex/MapServer/0/query` at
  lat 48.3 / lon −121.5 returns two quarter-quads, both `State: WA, Year: 2017, resolution 1 METER`
  (`m_4812144_se_10_1_20171003`). Either the index is stale or TNM's index only carries a subset;
  do not read it as "the newest NAIP over the Sauk is 2017" without cross-checking EarthExplorer.
- The tiled national basemap that *contains* NAIP is `USGSImageryOnly` above (its own copyright line
  credits USDA; the service description names NAIP-class orthoimagery). VERIFIED via §1.
- NAIP on AWS + licensing/currency: see §2a below.

---

## 1a. USGS terms & attribution (fetched today)

- **The National Map terms FAQ** (VERIFIED —
  https://www.usgs.gov/faqs/what-are-terms-uselicensing-map-services-and-data-national-map,
  fetched 2026-08-28): "Map services and data downloaded from The National Map are free and in the
  public domain." … "There are no restrictions" (attribution is *requested*, not a license condition).
  Requested credit line: **"Map services and data available from U.S. Geological Survey, National
  Geospatial Program."**
- **USGS acknowledging/crediting page** (VERIFIED —
  https://www.usgs.gov/information-policies-and-instructions/acknowledging-or-crediting-usgs,
  fetched 2026-08-28): "Most U.S. Geological Survey (USGS) information resides in the Public Domain
  and may be used without restriction." … "we ask that proper credit be given"; suggested form
  "(Product or data name) courtesy of the U.S. Geological Survey". Caveat quoted on the page: some
  non-USGS images are used with permission and stay copyrighted.
- **No API key exists anywhere in the flow** — every probe in §1/§2 was keyless. VERIFIED.
- NOT verified: `https://apps.nationalmap.gov/services/` is a JS-rendered app; a plain fetch today
  returned only the page title, so any statements specific to that page are **UNVERIFIED**.

## 2a. NAIP licensing, currency, AWS route (fetched today)

- **License (VERIFIED — https://registry.opendata.aws/naip/, fetched 2026-08-28):** "Public Domain
  with Attribution". Buckets: `naip-analytic` (4-band MRF + COG), `naip-source` (uncompressed
  GeoTIFF), `naip-visualization` (3-band RGB COG) — **all Requester Pays**, catalog covers ~2010–2023.
  Resolution "from 30 centimeters to 100 centimeters"; states re-flown "every two to three years".
  → There is **no public NAIP XYZ tile endpoint on AWS**; the open-data buckets are source rasters,
  not web tiles. Serving them would mean building a tiling pipeline (COG → titiler-style dynamic
  tiles or pre-rendered PMTiles) and paying egress.
- **Currency for Washington:** the TNM NAIP services' own copyright lines say the *mosaics* were
  refreshed Jan 9 / Mar 12, 2025 (VERIFIED, §2). An Esri Living Atlas post reports NAIP **2023**
  covers ~half of CONUS at 0.3–0.6 m (REPORTED —
  https://www.esri.com/arcgis-blog/products/arcgis-living-atlas/imagery/naip-2023-imagery-is-now-available-in-the-naip-timeseries,
  seen via search today, page not fetched directly). A USGS EROS page seen in search results reports
  a **2025 acquisition** in progress (~half the states at 60 cm, half at 30 cm) (REPORTED).
  **The specific latest NAIP year flown for Washington could NOT be verified today** — the TNM index
  probe (§2) returned 2017-vintage quads at the probe point, which contradicts the 2025-refreshed
  mosaic statement and looks stale. UNVERIFIED; check EarthExplorer before quoting a WA NAIP vintage.
- **Practical web-tile routes for NAIP today:** (1) the tiled `USGSImageryOnly` basemap (§1), which
  is NAIP-derived at large scales — free, public domain, cached, z≤16; (2) the dynamic
  `USGSNAIPPlus`/`USGSNAIPImagery` ImageServers (§2) — free, public domain, CORS `*`, but
  per-request rendering with cold-start latency. Both VERIFIED working today.

## 3a. Esri World Imagery — current terms (fetched today)

- **Item license (VERIFIED — arcgis.com sharing REST,
  `https://www.arcgis.com/sharing/rest/content/items/10df2279f9684e4a9f6a7f08febac2a9?f=json`,
  fetched 2026-08-28):** `licenseInfo` says: "This work is licensed under the Esri Master License
  Agreement." plus "Export: This layer is not intended to be used to export tiles for offline."
  `accessInformation` (the attribution string): "Esri, Vantor, Earthstar Geographics, and the GIS
  User Community".
- **Esri Product-Specific Terms E300, dated November 13, 2025 (VERIFIED — PDF fetched and
  decrypted today, https://www.esri.com/content/dam/esrisites/en-us/media/legal/product-specific-terms-of-use/e300.pdf):**
  - Footnote 10: "Session tokens may only be used per Value Added Application / Customer Application
    per device. **Programmatic use of session tokens (e.g., exporting volumes of basemap tiles) is
    not permitted.**"
  - Footnote 89: "Customer may distribute directly, or through its sales channels, revenue-generating
    Value-Added Applications / Customer Application, that access ArcGIS Location Platform through
    Authentication, to third parties. **All revenue-generating Value-Added Applications / Customer
    Application are required to use Authentication when accessing ArcGIS Location Platform.**"
- **Esri developer docs (VERIFIED —
  https://developers.arcgis.com/documentation/mapping-and-location-services/mapping/basemaps/types-of-basemap-services/,
  fetched 2026-08-28):** for the current basemap services (Basemap Styles, Static Basemap Tiles):
  "**An ArcGIS Location Platform or ArcGIS Online account is required to use the services.**"
- **ArcGIS Location Platform pricing (VERIFIED — https://location.arcgis.com/pricing/, fetched
  2026-08-28):** Basemap tiles: "**2M free then $0.15 per 1,000 tiles**" per month (static/vector);
  basemap sessions "1K free then $4 per 1,000 sessions".
- **Lifecycle (REPORTED — Esri blog "Lifecycle for Esri's hosted raster basemap services" returned
  HTTP 403 to a direct fetch today; the following comes from search-result content):** most hosted
  raster basemaps went to Mature Support (June 30, 2021), but World Imagery is listed among
  foundational services that will **not** enter Mature Support; retirement waves for *legacy*
  basemaps: Oct 2026 (legacy globe services), Mar 2028 and Dec 2029 (legacy basemap phases).
- **Community answer (REPORTED — Esri Community thread "Inquiry About World Imagery", seen via
  search, page is JS-rendered):** claims the service "is not free, it can only be used with an
  ArcGIS Online or ArcGIS Enterprise license".
- **Honest synthesis:** the endpoint is technically open today (keyless 200s, CORS `*` — §3), but
  the governing documents Esri publishes in 2025/2026 route all sanctioned use through an ArcGIS
  account (free ArcGIS Location Platform tier included) with Authentication, and the item is
  licensed under the Master License Agreement, not a public-domain or CC license. **Keyless
  production use of `server.arcgisonline.com` is not legally clean.** The clean Esri route is a free
  ArcGIS Location Platform account + API key against the supported basemap services (2M tiles/month
  free), with Esri attribution displayed.

## 4a. EOX terms (fetched today)

- **Non-commercial license page (VERIFIED — https://cloudless.eox.at/license-non-commercial,
  fetched 2026-08-28):** for **2018–2025** layers: "EOxCloudless WM(T)S layers is licensed under the
  Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License." Attribution
  "shall be displayed legibly and in proximity to the usage"; 2025 attribution text: "EOxCloudless
  https://cloudless.eox.at by EOX IT Services GmbH (Contains modified Copernicus Sentinel data
  2025)". The page states 2016 data is CC BY 4.0 (attribution-only) — but the 2016 layer is absent
  from today's WMTS capabilities (§4), and the 2017 layer's exact license was not stated on the page
  I fetched (UNVERIFIED for 2017).
- **Commercial use:** requires purchasing an EOxCloudless license ("perpetual license" wording on
  https://cloudless.eox.at, fetched today; no prices published on the page I retrieved — pricing
  UNVERIFIED).
- **Fit:** Cascadia in production is public-benefit but "non-commercial" under CC BY-NC-SA is a
  legal judgment, not an engineering one. Treat EOX 2018–2025 layers as **usable only if the owner
  signs off on the NC determination or buys a license**; do not bake them in as the default basemap.

## 5. Paid fallbacks (official pricing pages, fetched today)

- **Mapbox Raster Tiles API (VERIFIED — https://www.mapbox.com/pricing, fetched 2026-08-28):**
  free tier "Up to 750,000" tile requests/month; then "$0.25 per 1,000" (750,001–2,000,000 band).
  Applies to Mapbox Satellite raster tiles. Requires access token; attribution per Mapbox TOS
  (attribution specifics not fetched today — UNVERIFIED).
- **Azure Maps (VERIFIED in part — https://azure.microsoft.com/en-us/pricing/details/azure-maps/,
  fetched 2026-08-28):** "Imagery Tiles: 1,000 free" transactions/month; the page then shows
  contact-sales pricing at 500K+ volumes; a standard per-1,000 overage rate could not be extracted
  from the page today — **UNVERIFIED**.
- **Bing Maps for Enterprise (VERIFIED —
  https://blogs.bing.com/maps/2025-01/What-are-my-options-regarding-Bing-Maps-for-Enterprise-Retirement,
  fetched 2026-08-28):** free/basic (and non-profit/education) accounts ended **June 30, 2025**;
  enterprise licensees can continue "until June 30, 2028"; Microsoft's stated migration path is
  Azure Maps. **Bing imagery is not a viable new integration.**
- Cesium ion (excluded by task constraint) remains the only other turnkey option; not evaluated.

---

## CORS observed today (all probed with `Origin: https://example.org`)

| Host | ACAO | Notes |
|---|---|---|
| basemap.nationalmap.gov | `*` | metadata + tiles; CloudFront, `max-age=86400` |
| imagery.nationalmap.gov | `*` (+ `access-control-allow-credentials: true`) | exportImage probe |
| server.arcgisonline.com | `*` | metadata + tiles; CloudFront, `max-age=86400` |
| tiles.maps.eox.at | echoes origin + `access-control-allow-credentials: true`, `Vary: Origin` | tiles, `max-age=604800` |

All four are directly consumable from a browser Cesium app with no proxy.

## Recommended multi-tier stack (cheapest legally-clean first)

**Tier O — orbital → state (Cesium imagery layer, levels 0–9).**
`USGSImageryOnly` already carries Blue Marble/Landsat at small scales (its own description, §1), so
the single USGS layer covers this band at $0, public domain. If the owner wants the EOX look for the
cinematic globe, add `s2cloudless-2025_3857` **only after** the NC sign-off or a purchased license
(§4a) — visually better over ocean/mountains, useful only to ~z13.

**Tier B — basin / river corridors (levels 10–16). Primary basemap.**
- Provider: `UrlTemplateImageryProvider`
- URL: `https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}`
- `maximumLevel: 16` (hard 404 above — §1), 256×256 JPEG, WebMercator, keyless, CORS `*`.
- Attribution (both lines): `USDA, USGS The National Map: Orthoimagery. Data refreshed June, 2024.`
  and `Map services and data available from U.S. Geological Survey, National Geospatial Program.`
- Cost: $0. License: public domain. This is the workhorse.

**Tier L — local close-ups (levels 17–19), pick ONE:**
1. **$0, cleanest: don't have one.** Cap the camera at z16 (≈2.4 m/px at 48°N) — adequate for
   reach-scale hydrology; gauges and river geometry stay legible.
2. **Public domain close-ups on demand:** NAIP dynamic ImageServer for a *focused basin view only*
   (not a pan-anywhere basemap): `WebMapServiceImageryProvider` on
   `https://imagery.nationalmap.gov/arcgis/services/USGSNAIPPlus/ImageServer/WMSServer`
   (layer `USGSNAIPPlus:NaturalColor`) or REST `exportImage`. ~0.3–0.6 m detail, CORS `*`, $0, slow
   cold-start (§2) — cache aggressively, keep viewports small.
3. **Esri, legally clean:** free ArcGIS Location Platform account + API key against the supported
   basemap services — 2M tiles/month free, then $0.15/1K (§3a); attribution
   `Esri, Vantor, Earthstar Geographics, and the GIS User Community` + Esri logo per their docs.
   Cached tiles verified to z19 across WA (§3). Do NOT ship the keyless
   `server.arcgisonline.com` URL in production (§3a).

**Paid fallback if a tiled sub-meter basemap becomes mandatory at scale:** Mapbox Satellite raster,
750K tiles/month free then $0.25/1K (§5) — cheaper entry than Esri only below ~750K tiles/month;
above that Esri's $0.15/1K wins on price.

**Wiring notes for `apps/web`:** all tiers are plain `UrlTemplateImageryProvider` /
`WebMapServiceImageryProvider` — no Cesium ion asset IDs, no tokens except the optional Tier L-3
key. Per `docs/VISUALIZATION_CONTRACTS.md` discipline, keep provider choice + attribution strings in
config, and surface each layer's attribution in the credit line (public-domain sources *request*
credit; Esri/EOX *require* it).

## What could NOT be verified today

- Latest NAIP acquisition year for Washington specifically (index probe contradicts refresh dates — §2a).
- Esri raster-service lifecycle blog content first-hand (403 to direct fetch; search-snippet only — §3a).
- The `apps.nationalmap.gov/services` page's own policy text (JS shell — §1a).
- EOX 2017 layer license, EOxCloudless commercial pricing (not published on fetched page — §4a).
- Azure Maps imagery overage rate per 1,000 transactions (page shows contact-sales — §5).
- Mapbox attribution requirements page (not fetched — §5).

*Compiled 2026-08-28. All probes: curl from a US-West network, keyless, no credentials sent.*
