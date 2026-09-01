# Regional imagery foundation: continuity as a property of the DATA

Research date: 2026-09-01. Lens: IMAGERY. Builds on
`docs/research/cesium-continuity-camera-2026-08-31.md` (renderer knobs, verified absent
per-tile fades) and `docs/research/imagery-providers-2026-08-28.md` (provider terms +
probes); neither is repeated here — only cited.

Verification legend — every claim is one of:
- **[measured]** probe or computation run today from this machine (commands recorded in-line)
- **[dts:NNNNN]** `apps/web/node_modules/cesium/Source/Cesium.d.ts` line NNNNN (Cesium 1.144.0)
- **[src:File.js:NN]** `apps/web/node_modules/@cesium/engine/Source/<path>` line NN
- **[repo:file:line]** a file in this repository
- **[URL]** a page fetched today; quoted text is verbatim
- **[estimate]** derived arithmetic, assumptions stated; NOT a measurement
- **UNVERIFIED** could not be confirmed today

---

## 0. The finding that reframes the question

The repo's own premise (commit a955f12 "availability, not rendering") is correct, and today's
probes sharpen it: **the current source cannot make the PNW domain continuous at any zoom
above 9, because it has no data for a third of the domain.**

**[measured]** USGS `USGSImageryOnly` probes, 2026-09-01 (`curl -w "%{http_code}/%{size_download}"`,
tile path `/tile/{z}/{y}/{x}`):

| Point | z7 | z8 | z10 | z12 | z14 | z16 |
|---|---|---|---|---|---|---|
| Vancouver BC (49.25, −123.1) | 200/29,277 | 200/21,363 | **200/2,419 (white)** | **200/2,419 (white)** | **404** | **404** |
| Kamloops BC (50.67, −120.33) | 200/23,575 | 200/19,356 | **200/2,419 (white)** | **200/2,419 (white)** | **404** | **404** |
| Pacific offshore (47.5, −126.5) | 200/10,504 | 200/4,032 | **200/872 (white)** | **404** | **404** | **404** |
| Bellingham WA (48.75, −122.48) | 200/24,757 | 200/20,894 | 200/28,581 | 200/27,585 | 200/36,035 | 200/41,425 |
| Portland OR (45.52, −122.68) | 200/17,315 | 200/15,140 | 200/29,730 | 200/29,092 | 200/36,325 | 200/33,011 |

(872 B and 2,419 B are the two baked-white encodings the repo's `WhiteTileDiscardPolicy`
already hunts — [repo:apps/web/src/layers/basemap/white-discard.ts:4-9].)

**[measured]** 150 uniformly random z12 tiles across HARD_DOMAIN `[-128,44,-116.5,51.5]`
[repo:apps/web/src/camera/envelope.ts:31]: **127 × 200, 23 × 404; of the 200s, 68 were
< 3 KB (white)** → only **59/150 = 39 %** of the domain at z12 carries real imagery. Real
tiles average 17.7 KB. Throughput at concurrency 8: **19.3 tiles/s**, mean latency 0.33 s.
(Verification re-sample, same day, n=100, seed 7: 82 × 200, 18 × 404, 38 white, **44 % real**,
mean real 16.7 KB — consistent; but **37 t/s at 0.21 s** — the service rate varies by a
factor of two within a day, so every wall-time figure derived from 19.3 t/s below is an
upper bound, not a constant.)

So: HARD_DOMAIN spans 44–51.5 °N; USGS orthoimagery ends at the 49th parallel and at the
coast. British Columbia (2.5° of the 7.5° latitude span) is white at z10–12 and 404 at z14+;
the ocean (≈ 3.5° of the 11.5° longitude span) is white at z10 and 404 above. The existing
client fallback chain (discard → parent → z7 plate) is doing exactly what it should — and
what it produces north of 49° and offshore at basin band is z7–z9 imagery upsampled 8–128×
next to 1.6 m NAIP. That is the discontinuity, and no client knob reaches it: **the data
must be built.**

USGS's own description confirms the design: the service is "orthoimagery in The National
Map … Blue Marble: Next Generation and Landsat" at small scales
[measured: `MapServer?f=json`, `copyrightText` still "Data refreshed June, 2024",
`maxScale 9027.977411`].

---

## 1. Sources for the domain — terms quoted, not assumed

### 1.1 NAIP (USDA FPAC) — the z12–z16 land source. Public domain.

- **License, AWS Registry** [https://registry.opendata.aws/naip/]: `"Public Domain with
  Attribution"`. Buckets `naip-analytic`, `naip-source`, `naip-visualization` — all
  "Requester Pays", region **us-west-2**. "NAIP data is provided state by state at varying
  time intervals" with "an overall update cycle of every two to three years for each state."
- **License, data.gov** [https://catalog.data.gov/dataset/national-agriculture-imagery-program-naip-imagery]:
  License `"https://www.usa.gov/publicdomain/label/1.0/"`, access level `"public"`,
  publisher "Farm Production and Conservation Business Center". Resolution: "In 2018, the
  ground sample distance standard changed to 0.6 meter with the option for 0.3 meter. The
  2025 acquisition consists of approximately half of the states delivered at 60cm and the
  other half at 30cm ground sample distance."
- **Credit request, FSA** [https://www.fsa.usda.gov/help/policies-and-links/] (the license
  link the Planetary Computer collection points at): "Most information presented on the FSA
  Web site is considered public domain information. Public domain information may be freely
  distributed or copied, but use of appropriate byline/photo/image credits is requested." —
  credit form "U. S. Department of Agriculture, Farm Service Agency."
- **naip-visualization layout** [https://github.com/awslabs/open-data-docs/tree/main/docs/naip]:
  path `"state/YYYY/resolution*/bands_cog/SE_Reference_point_of_1_DegreeBlock/.tif files"`;
  "3-band COG's in this bucket have been compressed using YCbCr JPEG with quality 85 and are
  provided as 512x512 tiles"; index via `aws s3 cp s3://naip-visualization/manifest.txt … --request-payer`;
  "NAIP imagery on AWS is available ranging from 2010 to 2023"; "users can access it freely
  within the us-west-2 region, but will incur charges when accessing/downloading outside the
  region".
- **Most recent campaigns in the domain** [measured, Planetary Computer STAC
  `POST /api/stac/v1/search`, collection `naip`, paged counts, 2026-09-01]:
  - **Washington: 2023 at 0.6 m — 5,720 quarter-quads** (2021: 3,184; 2019: 5,012).
  - **Oregon: 2022 at 0.3 m — 3,712 quarter-quads *inside HARD_DOMAIN* (bbox lat 44–46.4)**;
    ~~3,712 statewide~~ **statewide the campaign is 7,471 items** (2020: 7,473; no 2023
    items) — corrected by the 2026-09-01 verification pass (distinct-id recount, 8 pages of
    1,000). A bbox query over Portland returned 2023/0.6 m items, but those are WA quads
    across the Columbia — with `naip:state=or, naip:year=2023` the count is 0.
  - MPC collection temporal extent ends 2023-12-31; license link title "Public Domain".
  - Whether WA/OR were flown in 2024 or 2025 is **UNVERIFIED** (the USDA hub is a JS shell,
    the FPAC coverage page shows "NAIP CONUS 2021-2022" downloads only; the USGS EROS page
    failed TLS today). Plan on 2023 WA / 2022 OR; re-check EarthExplorer before building.
- **[measured] One WA 2023 60 cm quad on Planetary Computer**: `HEAD …/naip/v002/wa/2023/wa_060cm_2023/47122/m_4712239_nw_10_060_20231007_20240209.tif`
  → `Content-Length: 394,524,348` (394 MB, 4-band deflate COG, `Accept-Ranges` exposed).
  Anonymous SAS token issued by `/api/sas/v1/token/naip`, 1-hour expiry. Blob account
  `naipeuwest` (Azure West Europe). **Measured downlink from here: 1.35 MB/s** → WA alone
  (5,720 × 394 MB ≈ 2.25 TB) is 19 days on this uplink — **the build must run in-cloud,
  next to the data** (§4).

### 1.2 USGS `USGSImageryOnly` — the z0–z14 land source we can harvest. Public domain, "no restrictions".

- Terms, quoted 2026-08-28 in `imagery-providers-2026-08-28.md` §1a from
  https://www.usgs.gov/faqs/what-are-terms-uselicensing-map-services-and-data-national-map:
  "Map services and data downloaded from The National Map are free and in the public domain."
  … "There are no restrictions". Requested credit: "Map services and data available from
  U.S. Geological Survey, National Geospatial Program."
- Hard z16 cap, keyless, CORS `*`, `cache-control: max-age=86400` (same file, §1).
- The repo's own provider record says `prefetchAllowed: true`
  [repo:apps/web/src/layers/basemap/BasemapProvider.ts:93]. A one-time throttled harvest of
  the pyramid is a bulk download of public-domain data, which the terms permit; throttle it
  anyway (§4.3) — the service is shared infrastructure.

### 1.3 Sentinel-2 — the ONLY clean fill for British Columbia and the ocean at z10–z13

Two routes, both licensed for adaptation and redistribution — unlike EOX (§1.4):

- **Copernicus Sentinel Data Legal Notice** [https://sentinels.copernicus.eu/documents/247904/690755/Sentinel_Data_Legal_Notice,
  PDF text extracted today]: "users shall have a free, full and open access to Copernicus
  Sentinel Data … EU law grants free access to Copernicus Sentinel Data and Service
  Information for the purpose of the following use in so far as it is lawful: (a)
  reproduction; (b) distribution; (c) communication to the public; (d) adaptation,
  modification and combination with other data and information; (e) any combination of
  points (a) to (d)." Required notice: "'Contains modified Copernicus Sentinel data [Year]'
  for Sentinel data".
- **Sentinel Hub 120 m L2A mosaic** [https://registry.opendata.aws/sentinel-s2-l2a-mosaic-120/]:
  "Best pixel values for 10-daily periods, modelled by removing the cloudy pixels and then
  performing interpolation among remaining values." License **"CC-BY 4.0, Credit: Contains
  modified Copernicus data [year] processed by Sentinel Hub"**; bucket
  `sentinel-s2-l2a-mosaic-120`, eu-central-1, not requester-pays. 120 m ≈ z10 (102 m/px at
  48 °N, table §3) — a ready-made **whole-domain plate for z0–z10**, cloud-free, one tone.
- **CDSE Sentinel-2 quarterly global mosaics** [https://documentation.dataspace.copernicus.eu/Data/SentinelMissions/Sentinel2.html]:
  "10m", bands "Red (B04), Green (B03), Blue (B02) and wide band Near Infrared (B08)",
  quarterly from three months of L2A, cloud-masked by the scene classification layer then
  "the first quartile of the distribution of the pixel values was taken as the output value";
  access via STAC/OData/S3 — a free CDSE account is required for S3 (UNVERIFIED today; the
  page does not say). 10 m ≈ z13 (12.8 m/px). This is the **z11–z13 fill for BC + ocean**,
  and the seam-reference for tone-matching NAIP (§4.2).
- Raw L2A COGs, if a custom composite is ever wanted: `sentinel-cogs`, us-west-2, not
  requester-pays, STAC at https://earth-search.aws.element84.com/v1
  [https://registry.opendata.aws/sentinel-2-l2a-cogs/]: "Access to Sentinel data is free,
  full and open".

### 1.4 EOX Sentinel-2 cloudless — NOT usable as a mosaic input

- License [https://cloudless.eox.at/license-non-commercial]: 2018–2025 layers "Creative
  Commons Attribution-NonCommercial-ShareAlike 4.0 International License"; attribution
  "displayed legibly and in proximity to the usage". The page says nothing about caching or
  derivatives — so the CC legal code governs.
- CC BY-NC-SA 4.0 legal code [https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode]:
  a re-tiled, re-graded copy is "Adapted Material" ("derived from or based upon the Licensed
  Material and in which the Licensed Material is translated, altered, arranged, transformed,
  or otherwise modified"); the grant is to "produce, reproduce, and Share Adapted Material
  **for NonCommercial purposes only**"; ShareAlike: "The Adapter's License You apply must be
  a Creative Commons license with the same License Elements". NonCommercial means "not
  primarily intended for or directed towards commercial advantage or monetary compensation".
- Verdict: a public non-commercial site *could* satisfy NC, but (a) that is a legal judgment
  the 08-28 file already flagged for the owner, (b) ShareAlike would force the **whole
  mosaic** (NAIP + Sentinel + Blue Marble composite) to be released BY-NC-SA, and (c) the
  same Sentinel-2 pixels are available under Copernicus terms / CC-BY with no NC or SA
  string (§1.3). **Do not use EOX in a derivative.**

### 1.5 NASA Blue Marble / GIBS — coarse plate and ocean

- NASA media policy [https://www.nasa.gov/nasa-brand-center/images-and-media/]: "NASA
  content – images, audio, video, and media files … generally are not subject to copyright
  in the United States." "NASA should be acknowledged as the source of the material."
- GIBS acknowledgement [https://nasa-gibs.github.io/gibs-api-docs/]: "We acknowledge the
  use of imagery provided by services from NASA's Global Imagery Browse Services (GIBS),
  part of NASA's Earth Science Data and Information System (ESDIS)." No rate limit or
  bulk-download restriction is published on the GIBS docs (they defer to
  earthdata-support@nasa.gov — UNVERIFIED beyond that).
- [measured] GIBS EPSG:3857 capabilities (5.79 MB XML): `BlueMarble_NextGeneration`,
  `BlueMarble_ShadedRelief`, `BlueMarble_ShadedRelief_Bathymetry`, each `image/jpeg`,
  TileMatrixSet **`GoogleMapsCompatible_Level8`** (i.e. z ≤ 8 only). Probe
  `…/BlueMarble_ShadedRelief_Bathymetry/default/GoogleMapsCompatible_Level8/6/22/9.jpg` →
  200, 5,168 B, `access-control-allow-origin: *`, `cache-control: public, max-age=259200`.
- Source rasters [https://science.nasa.gov/earth/earth-observatory/blue-marble-next-generation/base-topography-bathymetry]:
  monthly composites, "21600x21600" tiles at 500 m/px ("A1…D2"), plus 2 km and 8 km
  globals, JPEG and GeoTIFF. 500 m ≈ z8.
- Role: **ocean floor of the fallback chain (z0–z8)**, and the tone reference for deep
  water. Above z8 the Sentinel Hub 120 m mosaic takes over (it includes sea surface).

### 1.6 Esri World Imagery — no

Terms already quoted in the 08-28 file §3a: item "licensed under the Esri Master License
Agreement", "This layer is not intended to be used to export tiles for offline", E300 fn.10
"Programmatic use of session tokens (e.g., exporting volumes of basemap tiles) is not
permitted." A mosaic is by definition an export. Excluded.

---

## 2. Decision table

| Option | Continuity north of 49° / offshore | Grade applied once | Seams fixable | Pinned data (no upstream drift) | Build effort | Standing cost | Verdict |
|---|---|---|---|---|---|---|---|
| A. Today: USGS live + z7 plate + discard + warm z5–z9 | **No** — z10+ is white/404 there | No (per-layer uniforms only) | No | No ("Data refreshed" changes under us) | 0 | $0 | Ceiling reached |
| B. Expanded boot warm z5–z10/z11 | **No** — warms voids | No | No | No | tiny | $0 + visitor bandwidth (§6) | Only buys speed on land |
| C. **Mosaic z0–z14 in R2** (S2-120 m plate → S2-10 m BC/ocean → USGS harvest US land) | **Yes** | Yes | Partly (tone-match at build) | Yes | ~1 day + a throttled 5 h harvest | ≈ $0.06/mo | **Do first** |
| D. Mosaic to z16 (C + NAIP COGs → z15–16, built in us-west-2) | Yes | Yes | Yes (per-quad histogram match) | Yes | + ~1 cloud day | ≈ $0.6–0.9/mo + ~$12 one-time uploads | **Do second**, after C proves the pipeline |
| E. EOX cloudless in the mosaic | Yes | Yes | — | Yes | — | — | **Rejected** (NC + ShareAlike infects the whole product, §1.4) |
| F. Esri harvest | — | — | — | — | — | — | **Rejected** (terms, §1.6) |
| G. PMTiles instead of z/x/y objects | same data | same | same | same | +convert step | fewer objects, more range requests | Not for raster imagery here (§5.3) |

---

## 3. Numbers for the domain

**[measured]** WebMercator tile counts intersecting HARD_DOMAIN (same math as
`domainTiles()` [repo:apps/web/src/layers/basemap/domain-warmer.ts:28-43]); m/px at 48 °N:

| z | tiles | cumulative | m/px @48°N | Real-land share | Mean real tile (measured JPEG) |
|---|---|---|---|---|---|
| 5 | 4 | 9 | 3,273 | plate | — |
| 8 | 90 | 133 | 409 | plate | 14.8 KB |
| 9 | 306 | 439 | 205 | plate | — |
| 10 | 1,122 | 1,561 | 102 | ≈45 % | 35.0 KB |
| 11 | 4,288 | 5,849 | 51 | ≈45 % | — |
| 12 | 16,896 | 22,745 | 25.6 | 39 % measured | 17.7 KB |
| 13 | 66,810 | 89,555 | 12.8 | ≈45 % | — |
| 14 | 267,240 | 356,795 | 6.4 | ≈45 % | 22.6 KB |
| 15 | 1,066,893 | 1,423,688 | 3.2 | ≈45 % | — |
| 16 | 4,265,478 | 5,689,166 | 1.6 | ≈45 % | 21.8 KB |

"Real-land share" [estimate]: WA (184,661 km²) + OR north of 44 °N (≈130,000 km²) + the
Idaho sliver ≈ 335,000 km² of a ≈ 715,000 km² domain ≈ 47 %; the z12 random sample measured
39 %. 45 % is used below.

**Verification note on the z14/z16 means (2026-09-01):** a 10-point re-sample over WA/OR
land (Bellingham, Seattle, Yakima, Spokane, Portland, Tri-Cities, Olympic foothills,
Cascades, Rainier, Columbia Gorge) returned **31.2 KB (z14) and 30.8 KB (z16)**, not
22.6/21.8 KB. That sample is biased toward towns; the original sampling method is not
recorded. Treat the z14/z16 means as **UNVERIFIED ±40 %** and the z16 storage line below as
a floor (≈ 56–78 GB JPEG). The per-tile means do not change any verdict in §2.

**Storage and R2 cost** [estimate from the measured means; fill tiles (uniform sea / S2 at
BC) taken as 3 KB; WebP taken as 0.7 × JPEG — an assumption, not measured]:

| Build | Objects | JPEG | WebP (≈) | R2 storage/mo | Upload (Class A $4.50/M) |
|---|---|---|---|---|---|
| z0–z14, every tile (fill included) | 356,795 | 4.1 GB | 2.9 GB | **$0.06** (inside the 10 GB free tier → $0) | $1.61 |
| z0–z16, fill only to z14, land to z16 | 2,756,361 | 55.6 GB | 38.9 GB | **$0.58–0.83** (list; ≈ $0.43–0.68 after the 10 GB free tier) | $12.40 (list; ≈ $7.90 if uploaded within one month, after the 1 M free Class A ops) |

R2 prices [https://developers.cloudflare.com/r2/pricing/]: "$0.015 / GB-month", Class A
"$4.50 / million requests", Class B "$0.36 / million requests", free tier "10 GB-month /
month", "1 million" Class A, "10 million" Class B, and **"Egress (data transfer to Internet)
| Free"**. Class B (GetObject) is what serving costs: a cold visitor at river band pulls a
few hundred tiles; **1 M tile fetches/month = $0.36**, and the free tier covers 10 M.

Why the fill stops at z14: a `UrlTemplateImageryProvider` request that 404s is marked
failed and the quadtree upsamples the ancestor — the same path the 08-31 file verified for
discards [src:Scene/GlobeSurfaceTile.js:369-371]. A z14 fill tile (6.4 m/px) upsampled 4×
under open ocean or BC forest is invisible, and it saves 2.9 M objects. (One 404 per
tile per session is the price; Cloudflare's default TTL for 404 is short, so put a
1×1 ocean tile at z15–16 later only if the request log says the 404s matter.)

**Build time** [estimate]:
- Option C harvest: 356,795 USGS tiles at the **measured 19 tiles/s** (concurrency 8) ≈
  **5.2 h**; 55 % of those are voids that return instantly, so ≈ 3 h is realistic. Sentinel
  Hub 120 m plate: the domain is ≈ 5 GB of source (UNVERIFIED — the bucket layout was not
  listed today); CDSE 10 m quarterly mosaic for BC+ocean: ≈ 8 tiles of 10 m × 100 km …
  order 10–20 GB (UNVERIFIED size). Local tiling of these is minutes.
- Option D NAIP: WA 2023 ≈ 2.25 TB (measured quad size × measured quad count) from MPC
  (West Europe) — or the AWS `naip-visualization` JPEG-COGs, which at q85 YCbCr should be
  ≈ 4–6× smaller (≈ 0.4–0.6 TB; UNVERIFIED, requester-pays HEAD needs credentials). In
  us-west-2 the read is free and ~200 MB/s → **≈ 1 h of I/O for WA at JPEG size, ≈ 3 h at
  MPC size**; decode+warp+WebP-encode of ≈ 280 Gpx of output tiles is ≈ 5–8 core-hours →
  **15–30 min on a 32-vCPU spot instance**. Budget **one cloud day, single-digit dollars**
  for WA+OR. Do not attempt on the 1.35 MB/s home link.

---

## 4. The build pipeline (recommended: C now, D next)

### 4.1 Layering — what fills what, bottom-up

```
z0–z8    Blue Marble NG 500 m (ocean floor, tone anchor)            NASA, PD, credit NASA
z5–z10   Sentinel Hub S2 L2A 120 m mosaic (whole domain, cloud-free) CC-BY 4.0
z11–z13  CDSE S2 quarterly 10 m mosaic — ONLY where NAIP/USGS is void
         (BC, ocean, Idaho gaps)                                     Copernicus notice
z10–z14  USGS ImageryOnly harvest (US land; whites/404 → S2 below)   PD, "no restrictions"
z15–z16  NAIP 2023 WA 60 cm / 2022 OR 30 cm from COGs (option D)    PD with attribution
```
One output pyramid, one tile format, one grade. Each level's source is recorded in a
`manifest.json` next to the tiles (source, vintage, license line, grade parameters, build
commit) — the repo's provenance rule applies to pixels too.

### 4.2 Invariants the build enforces (these ARE the continuity)

1. **Never white, never transparent.** Every stored tile is opaque and derived from real
   earth. Voids are decided at build time by the same 3×3 ≥252 rule the client uses
   [repo:white-discard.ts:24-36], plus 404s; a void falls to the next layer down, not to a
   colour.
2. **Grade once.** `IMAGERY_GRADE = {saturation 0.88, brightness 0.94, contrast 1.04, gamma 1.0}`
   [repo:BasemapProvider.ts:63] is applied to pixels in the build, and the mosaic provider's
   client grade becomes identity — so JPEG/WebP quantisation happens after grading, not
   before, and the plate, the fill and the land share one tone by construction.
3. **Tone-match across sources and campaigns.** For each source layer, match its luminance
   and chroma histograms to the S2 mosaic under it at z10 (whole-domain reference) before
   re-tiling — a per-quad `skimage.exposure.match_histograms` against the co-registered S2
   raster is the simplest honest tool. This is the one place the 08-31 file's "not publicly
   possible" item 5 (per-tile tone normalization) becomes possible: at build time, not in
   the client.
4. **Ocean is data, not absence.** Below z14 the sea is the S2/Blue Marble pixel; above z14
   it is the z14 parent by upsampling (§3).
5. **Deterministic and pinned.** Inputs are named by vintage (`wa_060cm_2023`, S2 mosaic
   quarter, BM month); the output prefix is `imagery/v1/`; a rebuild is a new prefix, never
   an overwrite (the ADR-0021 terrain precedent: `terrain/v1/`).

### 4.3 Recipe — option C, runs on this Mac (no GDAL installed here today: `gdal*`, `rio`,
`pmtiles`, `rclone`, `aws` all absent [measured `which`]; Docker 29.5.3 is installed but not
running — start it, or `brew install gdal rclone pmtiles`)

```bash
# 0. Layout
mkdir -p build/{src,plate,fill,land,out} && cd build
export DOMAIN="-128 44 -116.5 51.5"           # HARD_DOMAIN, envelope.ts:31

# 1. Plate: Blue Marble NG (500 m) + Sentinel Hub 120 m mosaic, warped to 3857, graded.
#    BM: download the two 21600x21600 tiles covering the domain (A1/B1 columns, row 1 = northern
#    hemisphere) from the NASA page in §1.5; S2-120: aws s3 sync --no-sign-request
#    s3://sentinel-s2-l2a-mosaic-120/<chosen 10-day period>/<tiles over the domain>/ src/s2_120/
gdalbuildvrt src/bm.vrt src/world.topo.bathy.*.tif
gdalwarp -t_srs EPSG:3857 -te_srs EPSG:4326 -te $DOMAIN -r cubic -of COG \
  -co COMPRESS=JPEG -co QUALITY=90 src/bm.vrt plate/bm_3857.tif
gdalbuildvrt src/s2_120.vrt src/s2_120/*.tif           # B04,B03,B02 → -b 1 -b 2 -b 3 as needed
gdalwarp -t_srs EPSG:3857 -te_srs EPSG:4326 -te $DOMAIN -r cubic -of COG src/s2_120.vrt plate/s2_120_3857.tif

# 2. Fill: CDSE S2 quarterly 10 m mosaic tiles over BC + coastal water (STAC search on the
#    CDSE catalog for the quarter; S3 needs a free CDSE account). Warp+COG as above → fill/s2_10_3857.tif

# 3. Grade ONCE (python, rasterio + numpy; the same numbers as IMAGERY_GRADE):
#    rgb = rgb*0.94; rgb = (rgb-128)*1.04+128; desaturate 12 % toward luma; clip; write COG.
python grade.py plate/bm_3857.tif plate/bm_graded.tif
python grade.py plate/s2_120_3857.tif plate/s2_120_graded.tif
python grade.py fill/s2_10_3857.tif fill/s2_10_graded.tif

# 4. Tile the plate/fill pyramids (GDAL ≥ 3.11 `gdal raster tile`: WebMercatorQuad, xyz
#    convention, threads; docs: https://gdal.org/en/stable/programs/gdal_raster_tile.html)
gdal raster tile --tiling-scheme WebMercatorQuad --convention xyz --min-zoom 0 --max-zoom 8 \
  --resampling cubic -j ALL_CPUS -f WEBP plate/bm_graded.tif out/bm
gdal raster tile --tiling-scheme WebMercatorQuad --convention xyz --min-zoom 5 --max-zoom 10 \
  --resampling cubic -j ALL_CPUS -f WEBP plate/s2_120_graded.tif out/s2_120
gdal raster tile --tiling-scheme WebMercatorQuad --convention xyz --min-zoom 11 --max-zoom 13 \
  --resampling cubic -j ALL_CPUS -f WEBP fill/s2_10_graded.tif out/s2_10
#    (older GDAL: gdal2tiles.py --xyz --profile mercator --tiledriver WEBP --webp-quality 80
#     -z 0-8 --processes 8 in.tif out/  — flags verified at gdal.org gdal2tiles page.)

# 5. Harvest USGS z10–z14 for the domain, throttled (measured 19 tiles/s at c=8 — keep c≤8),
#    decode, void-test (3x3 ≥252 or 404), grade, tone-match to the S2 plate, encode WebP q80,
#    write out/usgs/{z}/{x}/{y}.webp.  ~357k requests, ≈3–5 h.  Pure python (PIL, httpx).
python harvest_usgs.py --domain "$DOMAIN" --zooms 10-14 --concurrency 8 --out out/usgs

# 6. Compose: for each z/x/y in the domain pick the highest-priority present tile
#    (usgs > s2_10 > s2_120 > bm); if none (should not happen ≤z10), FAIL the build.
python compose.py --domain "$DOMAIN" --zooms 0-14 --layers out/usgs out/s2_10 out/s2_120 out/bm \
  --out out/imagery_v1 --manifest out/imagery_v1/manifest.json
#    assert: every tile 0..14 exists, is opaque, mean luminance in [12,235], no 3x3 region ≥252.

# 7. Upload to R2 (rclone; conf per https://developers.cloudflare.com/r2/examples/rclone/):
#    [r2] type=s3 provider=Cloudflare access_key_id=… secret_access_key=…
#         endpoint=https://<accountid>.r2.cloudflarestorage.com acl=private
rclone copy out/imagery_v1 r2:cascadia-terrain/imagery/v1 --transfers 32 --checkers 32 \
  --header-upload "Cache-Control: public, max-age=31536000, immutable" \
  --header-upload "Content-Type: image/webp"
#    (R2 keeps Content-Type on upload — the terrain lesson [repo:functions/[[path]].js:112-115]
#     was Content-Encoding, which WebP tiles do not use.)
```

### 4.4 Recipe — option D, NAIP z15–z16, run in us-west-2 (or Azure West Europe for MPC)

```bash
# EC2 spot, 32 vCPU, 200 GB gp3, IAM role with s3:GetObject on naip-visualization (requester-pays)
aws s3 cp s3://naip-visualization/manifest.txt . --request-payer requester
grep -E '^wa/2023/60cm/rgb/' manifest.txt > wa.txt          # 5,720 quads (MPC count)
grep -E '^or/2022/30cm/rgb/' manifest.txt > or.txt          # 7,471 quads statewide; 3,712 inside the domain after the clip below
# clip OR to the domain (lat ≥ 44) using /index/ shapefiles, then:
gdalbuildvrt -input_file_list <(sed 's#^#/vsis3/naip-visualization/#' wa.txt) wa.vrt
gdalbuildvrt -input_file_list <(sed 's#^#/vsis3/naip-visualization/#' or.txt) or.vrt
export AWS_REQUEST_PAYER=requester GDAL_NUM_THREADS=ALL_CPUS GDAL_CACHEMAX=8192 VSI_CACHE=TRUE
# tone-match each quad to the S2 plate (python, per-quad, parallel) → wa_matched.vrt (graded)
gdal raster tile --tiling-scheme WebMercatorQuad --convention xyz --min-zoom 15 --max-zoom 16 \
  --resampling cubic -j ALL_CPUS -f WEBP wa_matched.vrt out/naip_wa
# same for or_matched.vrt; then compose.py --zooms 15-16 and rclone as in §4.3
```
(`gdal raster tile` synopsis, `--tiling-scheme WebMercatorQuad`, `--convention xyz|tms`,
`--min-zoom/--max-zoom`, `-j ALL_CPUS`, `-f` and "Added in version 3.11" verified at
https://gdal.org/en/stable/programs/gdal_raster_tile.html. The WEBP quality creation-option
name for this command is UNVERIFIED — check `gdal raster tile --help` on the box.)

An alternative container for the same output: `gdal_translate -of MBTILES -co TILE_FORMAT=WEBP
-co QUALITY=80` + `gdaladdo -r average x.mbtiles 2 4 8 16` (MBTiles driver options
"PNG, PNG8, JPEG or WEBP", QUALITY 1–100, EPSG:3857 tiling, verified at
https://gdal.org/en/stable/drivers/raster/mbtiles.html), then `pmtiles convert x.mbtiles
x.pmtiles` — only if §5.3 ever changes the serving decision.

---

## 5. Serving

### 5.1 The r2.dev hazard (applies to the terrain path already in production)

[https://developers.cloudflare.com/r2/buckets/public-buckets/]: "Public access through
`r2.dev` subdomains is rate-limited and should only be used for development purposes."
A custom domain "allows you to use Cloudflare Cache to accelerate access to your R2 bucket",
and "only certain file types are cached" by default unless a cache-everything rule is set.

The gateway's terrain default is `https://pub-1145121e012145ac8173711ab278c913.r2.dev`
[repo:functions/[[path]].js:98]. Terrain survives on it because the tile volume is small;
imagery at 4 M objects will not. **Before the mosaic ships, attach a custom domain
(`tiles.papsukkal.com`) to the bucket** — WebP and JPG are in Cloudflare's default-cached
extension list [https://developers.cloudflare.com/cache/concepts/default-cache-behavior/:
"…WEBP, BMP, EOT, JPG…"], origin `Cache-Control: max-age` is honoured ("max-age will be
used by Cloudflare"), so the immutable header set at upload does the rest.

### 5.2 Three ways to reach the bytes — pick 1

| Path | Function invocations | Edge cache | CORS | Verdict |
|---|---|---|---|---|
| **1. R2 custom domain, direct** `https://tiles.papsukkal.com/imagery/v1/{z}/{x}/{y}.webp` | none (static, not a Pages route) | yes (custom domain) | one extra origin → CSP `img-src`/`connect-src` entry via `cspHosts` [repo:BasemapProvider.ts:94]; R2 bucket CORS `GET,HEAD` for the app origin | **Recommended.** Zero Functions quota, zero proxy latency |
| 2. Pages gateway proxy `/imagery/v1/*` → R2 (the `/terrain/` pattern, `[[path]].js:93-121`, add to `_routes.json` include) | **one per tile.** Pages Functions share the Workers Free quota: "100,000 daily request usage" combined [https://developers.cloudflare.com/pages/functions/pricing/]; static assets are free and "A request is considered static when it does not invoke Functions" | only if the Function uses `caches.default` or `fetch(…, {cf:{cacheEverything:true, cacheTtl}})` ("forces Cloudflare to cache the response for this request" — https://developers.cloudflare.com/workers/runtime-apis/request/) | same-origin, no CSP change | Acceptable only with a **Pages R2 binding** (`context.env.BUCKET.get(key)` [https://developers.cloudflare.com/pages/functions/bindings/]) + `caches.default`; still burns quota: 1,000 visitors × 300 tiles = 300k/day > free plan |
| 3. PMTiles archive via range requests | 2–3 range requests per cold tile through a Function (or direct to R2 with `Range`) | partial — `cache.put` refuses 206 ("206 Partial Content" responses cannot be cached — https://developers.cloudflare.com/workers/runtime-apis/cache/); custom-domain edge cache does serve ranges from a cached full object, which for a 40 GB archive it will never hold | app origin only | **No** for raster imagery at this size (§5.3) |

### 5.3 Why not PMTiles here

PMTiles is "a single-file archive format for pyramids of tiled data" whose readers "use HTTP
Range Requests to fetch only the relevant tile or metadata"
[https://docs.protomaps.com/pmtiles/]; R2 is its recommended host precisely because "it does
not have bandwidth fees, only per-request fees" [https://docs.protomaps.com/pmtiles/cloud-storage].
Those are the wins for a *vector* basemap with hundreds of thousands of small tiles and no
CDN. Here they invert:
- Cesium has **no PMTiles provider** [measured: 0 hits for "pmtiles" in Cesium.d.ts]. A
  custom provider is legal — the duck type is `rectangle/tileWidth/tileHeight/maximumLevel/
  minimumLevel/tilingScheme/tileDiscardPolicy/errorEvent/credit/hasAlphaChannel/
  getTileCredits/requestImage` [dts:37575-37651], and `requestImage` may resolve an
  `ImageBitmap` [dts:37569 `ImageryTypes`] built from the range bytes with the `pmtiles`
  npm package (4.5.0, BSD-3-Clause [measured `npm view`]). It is ~80 lines — but it is a
  second imagery code path to keep alive.
- R2 egress is free either way; per-object Class B cost is identical per tile served.
- The edge cannot cache what a Function assembled from partial content; z/x/y objects cache
  as plain files with no code at all.
- The only PMTiles advantage left is upload op count (1 object vs 2.8 M ≈ $12 once).
Keep PMTiles for the vector layers `CINEMATIC_ARCHITECTURE.md` §5 already plans; serve
raster imagery as objects.

### 5.4 Cesium consumption (all verified 1.144)

```ts
// BasemapProvider.ts — new provider 'cascadia-mosaic', selected by VITE_BASEMAP
new ImageryLayer(
  new UrlTemplateImageryProvider({
    url: `${TILES_ORIGIN}/imagery/v1/{z}/{x}/{y}.webp`,   // {z}{x}{y}: dts:46188-46199
    minimumLevel: 0, maximumLevel: 14 /* 16 after option D */, // dts:46240, 46243
    rectangle: HARD_DOMAIN_RECT,                             // dts:46244
    tilingScheme: new WebMercatorTilingScheme(),             // dts:46245 (default)
    hasAlphaChannel: false,                                  // dts:46253 — opaque by contract
    credit: new Credit(MOSAIC_CREDIT, true),
    // NO tileDiscardPolicy: the build guarantees no voids; dropping it also drops the
    // preferBlob branch (src:Scene/ImageryProvider.js:251-259). CORRECTED 2026-09-01: that
    // is NOT "one less decode step" — with preferImageBitmap both branches do one XHR blob
    // fetch + one createImageBitmap (preferBlob: Resource.js:923-949; default:
    // _fetchImage → _Implementations.createImage, Resource.js:1006-1030, 1955-2010). The
    // only difference is which fetch path schedules the request; no decode is saved.
  }),
  { rectangle: HARD_DOMAIN_RECT },                           // dts:36958
)
// Client grade → identity for this provider (grade is baked): {1,1,1,1}.
// createBasePlate → null: the pyramid IS the plate. Keep the edge vignette layer.
```
- WebP: Cesium hands the bytes to `createImageBitmap`/`Image` — decoding is the browser's
  [src:Core/Resource.js:874-881, 937-949]; `FeatureDetection.supportsWebP` exists but is
  used only by the glTF loader [src:Scene/GltfLoader.js:578-583] and is not public
  [measured: no d.ts hit]. Every browser
  Cesium 1.144 supports decodes WebP; keep a `.jpg` fallback prefix only if analytics show
  otherwise.
- Attribution string (one line, all sources): "USDA NAIP · USGS The National Map ·
  Contains modified Copernicus Sentinel data 2025 · NASA Blue Marble".
- The domain warmer keeps working unchanged against the mosaic URL — and now warms real
  data north of 49° too. Re-point `TILE_URL` [repo:domain-warmer.ts:19-20].

### 5.5 Cache headers

| Object | Cache-Control | Why |
|---|---|---|
| `imagery/v1/{z}/{x}/{y}.webp` | `public, max-age=31536000, immutable` | pinned by prefix; a rebuild is `v2` |
| `imagery/v1/manifest.json` | `public, max-age=300` | the one file republished in place (terrain precedent, `[[path]].js:109-111`) |
| 404 (z15–16 over sea/BC) | Cloudflare default (short) | fine; revisit if logs show volume |

---

## 6. The client-side alternative, honestly

Expanded warm sets [measured counts × measured means]:

| Warm | tiles | bytes if all real | bytes at the real 39–45 % | wall time at 19 t/s |
|---|---|---|---|---|
| z5–z9 (today) | 439 | 8 MB | — | 23 s |
| z5–z10 | 1,561 | 47 MB | ~24 MB | 82 s |
| z5–z11 | 5,849 | ~130 MB | ~70 MB | 5 min |
| z5–z12 | 22,745 | ~450 MB | ~200 MB | 20 min |

Where the warm stops paying: it is bounded by the visitor's patience (the boot screen is
"real counts", so 82 s is visible), by the shared USGS service (every new visitor repeats
it), and above all by **what it warms — 55–61 % of those requests are white or 404 north of
49° and offshore**, so at basin band the warmed view is still z7–z9 there. The warm is a
latency tool. The mosaic is an availability tool. **The mosaic becomes necessary the moment
the camera can see BC or open water at z ≥ 10** — which, with `SOFT_ENVELOPE` north edge at
49.6 °N and the coast at ~−124.5 [repo:envelope.ts:34], is every state/basin-band frame of
the Nooksack and Skagit. Keep the z5–z9 warm (it becomes 439 mosaic tiles, all real, ≈ 8 MB,
served from the edge), drop the deep z10 idle warm once the mosaic ships.

---

## 7. What could not be verified today

- NAIP 2024/2025 flights for WA/OR (USDA hub is a JS shell; FPAC page lists 2021–22;
  USGS EROS page failed TLS). MPC/AWS catalogues stop at 2023.
- `naip-visualization` per-quad object size (requester-pays HEAD needs AWS credentials).
- CDSE S3 access prerequisites and the size of the 10 m quarterly mosaic over the domain.
- Sentinel Hub 120 m bucket key layout over the domain.
- The exact WEBP quality creation-option spelling for `gdal raster tile` (GDAL 3.11).
- WebP ≈ 0.7 × JPEG is an assumption; measure on the first 1,000 land tiles and re-run
  the §3 arithmetic.
- GIBS bulk-use policy beyond the published acknowledgement (docs defer to support email).
- No build was run here (no GDAL locally, Docker stopped): build-time figures are derived.

---

## 8. Recommendations, in order

1. **Ship option C this week**: S2-120 m plate (CC-BY) + CDSE S2 10 m fill for BC/ocean +
   throttled USGS harvest for US land, z0–z14, graded once, tone-matched, opaque by
   assertion, uploaded to `cascadia-terrain/imagery/v1/` as immutable WebP objects.
   ≈ 357k objects, ≈ 3–4 GB, $0/month inside the free tier, ≈ $1.61 of upload ops.
2. **Attach a custom domain to the R2 bucket first** and serve tiles (and terrain) from it,
   not r2.dev and not through Pages Functions. Add the host to `cspHosts`.
3. **Register `cascadia-mosaic` in `BasemapProvider.ts`** with identity grade, no discard
   policy, `hasAlphaChannel:false`, `maximumLevel` from the manifest; make it the default
   via `VITE_BASEMAP`; keep `usgs-imagery` registered as the live fallback.
4. **Then option D**: NAIP WA 2023 / OR 2022 → z15–z16 on a us-west-2 spot box (≈ 1 day,
   single-digit dollars, ≈ $0.6–0.9/month standing), bumping `maximumLevel` to 16.
5. **Never put EOX or Esri pixels into the mosaic**; Sentinel-2 under Copernicus/CC-BY terms
   covers the same need cleanly.
6. Record the layer stack, vintages and licence lines in `imagery/v1/manifest.json` and
   surface them in the credit line — the "where did it come from" rule applies to the
   ground itself.
7. Propose an ADR ("ADR-00xx: Imagery is a self-built PNW mosaic in R2") in the ADR-0021
   mould; the terrain decision is the precedent in every respect (PD inputs, R2 prefix
   versioning, gateway lessons).

---

## Verification

Adversarial pass, 2026-09-01, by a second agent whose brief was to refute. Every Cesium
claim was re-grepped in `apps/web/node_modules/cesium/Source/Cesium.d.ts` (package.json
`"version": "1.144.0"`; `@cesium/engine` 26.2.0); every external claim was re-fetched;
every measurement that could be re-run from this machine was re-run. Inline corrections in
the body are marked "CORRECTED 2026-09-01" or struck through.

| # | Claim | Verdict | Note |
|---|---|---|---|
| 1 | `UrlTemplateImageryProvider` options, `ImageryLayer` rectangle, `ImageryProvider` duck type / `ImageryTypes`, no PMTiles provider | ✓ | d.ts 46188-46199 (`{z}{x}{y}`), 46240 `minimumLevel`, 46243 `maximumLevel`, 46244 `rectangle`, 46245 `tilingScheme = WebMercatorTilingScheme`, 46253 `hasAlphaChannel`, 46268 `tileDiscardPolicy`; 36958 `ImageryLayer` `rectangle`; 37569 `ImageryTypes` includes `ImageBitmap`; 37575-37651 `ImageryProvider`. `grep -ci pmtiles` = 0. Duck-type check: `Scene/ImageryLayer.js` reads only `tilingScheme, rectangle, errorEvent, tileDiscardPolicy, minimumLevel, maximumLevel, getTileCredits, tileWidth, requestImage, hasAlphaChannel` plus optional `_default*`; `ImageryLayerCollection.js` reads `credit` and optional `_reload`. |
| 2 | WebP needs no Cesium support; `tileDiscardPolicy` forces `preferBlob`; omitting it "removes a decode step"; `supportsWebP` internal, glTF-only | ✗ (one part) | `ImageryProvider.js:240-265` and `Resource.js:874-881, 937-949` say what the doc says, and `supportsWebP` is absent from the d.ts and used only at `GltfLoader.js:578-583`. **But "one less decode step" is false**: with `preferImageBitmap` the default branch (`_fetchImage` → `_Implementations.createImage`, `Resource.js:1006-1030, 1955-2010`) also does XHR-blob + `createImageBitmapFromBlob` — the same one fetch and one decode as the `preferBlob` branch. Corrected in §5.4. |
| 3 | USGS has no orthoimagery north of 49° or offshore (white z10-z12, 404 z14-z16) | ✓ | Re-probed all 30 cells of the §0 table: byte-identical (Vancouver/Kamloops 2,419 B at z10/z12, 404 at z14/z16; Pacific 872 B at z10, 404 from z12; Bellingham/Portland real at every zoom). HARD_DOMAIN confirmed at `envelope.ts:31`. |
| 4 | 39 % real at z12, 17.7 KB mean, 19.3 t/s | ✓ (rate is not a constant) | Independent n=100 re-sample: 44 % real, 56 % white-or-404, mean real 16.7 KB — consistent. Throughput re-measured at **37 t/s** (0.21 s latency), so 19.3 t/s is a moment, not a property; §0 annotated, wall-times are upper bounds. |
| 5 | Tile counts, mean sizes, R2 storage/cost arithmetic | ✓ counts / ✗ means | Counts reproduced exactly with `domain-warmer.ts:28-43` math (356,795 through z14; 5,689,166 through z16; z14 267,240; z16 4,265,478). R2 prices quoted correctly. Arithmetic checks (4.1 GB; 2,756,361 objects; 55.6 GB; $0.83; $12.40). **The z14/z16 means did not reproduce**: 10 land points gave 31 KB at both zooms vs 22.6/21.8 KB — flagged in §3 as UNVERIFIED ±40 %; free-tier offsets added to the cost row. |
| 6 | NAIP public domain; AWS "Public Domain with Attribution"; data.gov license URL and the 2025 60/30 cm sentence; FSA credit line; three requester-pays buckets in us-west-2 | ✓ | All three pages fetched; every quoted string present verbatim. |
| 7 | WA 2023 0.6 m 5,720 quads; OR 2022 0.3 m 3,712; quad 394,524,348 B; 1.35 MB/s; JPEG q85 in `naip-visualization` | ✗ (Oregon count) | WA 2023 = 5,720 (distinct ids, 0.6 m) ✓; WA 2024/2025 and OR 2023/2024 = 0 ✓; HEAD → `Content-Length: 394524348`, `Accept-Ranges: bytes` ✓; 30 MB range download 1.26 MB/s ✓; open-data-docs quotes ✓. **OR 2022 statewide is 7,471 items** (2020: 7,473); 3,712 is the count inside the domain bbox (lat 44-46.4). Corrected in §1.1 and §4.4. |
| 8 | EOX is CC BY-NC-SA 4.0; CC legal-code quotes; ShareAlike would infect the mosaic | ✓ | cloudless.eox.at: 2018-2025 layers CC BY-NC-SA 4.0 (2016 is CC BY 4.0); CC legalcode Sections 1, 2(a)(1)(B), 3(b)(1) quoted correctly. |
| 9 | Copernicus legal notice (a)-(d) + "Contains modified Copernicus Sentinel data [Year]"; Sentinel Hub 120 m mosaic CC-BY 4.0, eu-central-1, not requester-pays; CDSE 10 m quarterly mosaics | ✓ | PDF re-extracted with pypdf: both passages verbatim. AWS registry page: license string verbatim, bucket/region verbatim, no Requester Pays field (doc's "not requester-pays" is an inference from absence — stated as such here). CDSE page: 10 m, B04/B03/B02/B08, SCL cloud mask, first quartile, STAC/OData/S3 — matches. |
| 10 | NASA copyright + acknowledgement; GIBS 3857 BlueMarble layers `GoogleMapsCompatible_Level8` only; tile 200/5,168 B/CORS *; 21600×21600 500 m tiles; GIBS acknowledgement text | ✓ | NASA sentences verbatim; re-fetched the 5.79 MB capabilities and parsed: all three BlueMarble layers `image/jpeg`, `GoogleMapsCompatible_Level8` only; probe tile `200`, `content-length: 5168`, `access-control-allow-origin: *`, `max-age=259200`; Earth Observatory page lists A1-D2 21600×21600 JPEG/GeoTIFF; GIBS acknowledgement verbatim. |
| 11 | USGS National Map public domain, "no restrictions", credit line; `prefetchAllowed: true`; maxScale 9027.977411, "Data refreshed June, 2024" | ✓ | usgs.gov FAQ fetched (needed a browser UA; the plain fetch was CloudFront-403): "free and in the public domain. There are no restrictions; however, we request…" verbatim; `BasemapProvider.ts:93` ✓; `MapServer?f=json` → `maxScale 9027.977411`, `copyrightText "USDA, USGS The National Map: Orthoimagery. Data refreshed June, 2024."` ✓; 08-28 doc §1a carries the same quotes. |
| 12 | r2.dev rate-limited / custom domain enables cache / WEBP+JPG default-cached / max-age honoured; gateway terrain default is a pub-*.r2.dev origin | ✓ | Both Cloudflare pages quoted verbatim (extension list includes WEBP and JPG; "max-age will be used by Cloudflare"); `functions/[[path]].js:98` is the r2.dev default. |
| 13 | Pages Functions share the 100k/day free quota; static requests free; R2 binding `context.env.BUCKET.get`; `cache.put` refuses 206; `cf.cacheEverything`/`cacheTtl` | ✓ | All four Cloudflare pages quoted verbatim (`cache.put` lists a 206 response under "Invalid parameters"). 404 default edge TTL is 3 minutes (configure-cache-status-code page) — supports the "short" in §3. |
| 14 | Expanded warm cannot substitute: 1,561 / 22,745 tiles, ~82 s / ~20 min, 55-61 % void, SOFT_ENVELOPE north 49.6 N | ✓ | Counts reproduced; 82 s and 20 min follow from 19.3 t/s (at today's 37 t/s they halve — the argument survives); re-sample void fraction 56 %; `envelope.ts:34` north 49.6. |
| 15 | GDAL 3.11 `gdal raster tile` flags and "Added in version 3.11"; gdal2tiles flags; MBTiles driver options; rclone R2 config; no GDAL/rio/pmtiles/rclone/aws here; Docker stopped | ✓ | gdal.org pages quoted verbatim (WebMercatorQuad default, `--convention xyz\|tms`, `-j ALL_CPUS`, `-f` incl. WEBP; gdal2tiles `--xyz`, `--tiledriver` PNG/WEBP/JPEG, `--webp-quality` 1-100, `--processes`, `-z`; MBTiles `TILE_FORMAT=[PNG/PNG8/JPEG/WEBP]`, `QUALITY=1-100`, EPSG:3857). rclone block verbatim. `which` confirms all five absent; `docker info` fails (daemon stopped). `pmtiles` npm 4.5.0 BSD-3-Clause also re-checked. |

Net effect on the recommendations in §8: none. Two numbers were wrong (Oregon statewide
count; the "decode step" saving) and two were under-sampled (z14/z16 means; the service
rate). Neither the licence conclusions nor the C-then-D ordering depends on any of them.
