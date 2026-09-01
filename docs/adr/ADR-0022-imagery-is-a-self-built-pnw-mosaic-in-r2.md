# ADR-0022: Imagery is a self-built PNW mosaic in R2

- Status: Proposed → owner-approved 2026-09-01 (plan §10, Q4: "mosaic ADR + tiles hostname
  APPROVED"); moves to Accepted when exit tests E3.1–E3.5 below are green on the deployed scene.
- Serves: CINEMATIC_ROADMAP's "the world is the interface" (a ground that is continuous across
  the whole PNW envelope); CINEMATIC_ARCHITECTURE §10's keyless, ion-free default; the one rule
  in CLAUDE.md applied to pixels ("where did it come from, when, from which version").
- Precedent: [ADR-0021](ADR-0021-ion-free-terrain.md) — public-domain inputs, an R2 prefix
  versioned by vintage, gateway lessons. This decision is the imagery half of the same shape.
- Evidence: [cesium-cinematic-imagery-foundation-2026-09-01.md](../research/cesium-cinematic-imagery-foundation-2026-09-01.md)
  (lens I; every quote below is from its §1, every number from its §3) and the synthesis
  [cesium-cinematic-plan-2026-09-01.md](../research/cesium-cinematic-plan-2026-09-01.md) (§4,
  Phase 3, §10).

## Context

The production basemap is the live USGS `USGSImageryOnly` service: keyless, public domain, and
the right choice for Washington land. The camera envelope is not Washington. `HARD_DOMAIN` spans
`[-128, 44, -116.5, 51.5]` and every state/basin-band frame of the Nooksack and Skagit looks at
British Columbia and open water — and the service has no orthoimagery north of the 49th parallel
or offshore. Measured 2026-09-01 (lens I §0): Vancouver BC and Kamloops BC return baked-white
tiles (2,419 B) at z10–z12 and 404 at z14+; the Pacific offshore returns white (872 B) at z10
and 404 from z12. A 150-tile random sample of the domain at z12 came back 127 × 200 / 23 × 404,
with 68 of the 200s under 3 KB (white): **only 59/150 = 39 % of the domain at z12 carries real
imagery — 61 % is void.** A same-day re-sample (n = 100) measured 44 % real, 56 % void.

The client already does everything a client can — `WhiteTileDiscardPolicy` hunts both white
encodings, discards fall to the parent, the parent falls to the z7 plate, the boot warm fills
the HTTP cache to z9. What that produces north of 49° and offshore at basin band is z7–z9
imagery upsampled 8–128× beside 1.6 m NAIP. Expanding the warm cannot fix it: the warm is a
latency tool that puts tiles the service *has* into the cache, and above z9 the service does not
have the north third of the domain or the ocean. A z5–z12 warm would be 22,745 requests (~20 min
on the visible boot screen, repeated per visitor against shared public infrastructure) and would
still draw z7–z9 pixels over BC. This is the only cinematic-lens finding that is *availability*,
not rendering: **the data must be built.**

What exists to build it from, without an ion account or a keyed vendor in the render loop:

- **Live USGS + plate + discard + warm (today)** — ceiling reached; the 61 % void is structural.
- **Hosted imagery (Esri World Imagery, MapTiler, Planet)** — keys in the render loop, and the
  terms forbid the export a mosaic is (§ licences below). Rejected.
- **EOX Sentinel-2 cloudless** — the right pixels under the wrong licence (BY-NC-SA; ShareAlike
  would force the whole composite to BY-NC-SA). Rejected.
- **Self-built mosaic from public-domain and CC-BY sources** — NASA Blue Marble as the ocean
  floor, Sentinel-2 (Copernicus terms / CC-BY) as the whole-domain plate and the BC/ocean fill,
  the USGS pyramid harvested once for US land, NAIP COGs for the local band later; graded and
  tone-matched at build time; hosted as static objects in the R2 bucket that already holds the
  terrain pyramid. The same shelf ADR-0021 built.

## Decision

1. **Build option C now: a z0–z14 WebMercator raster pyramid over `HARD_DOMAIN`**, composed
   bottom-up — z0–z8 Blue Marble NG 500 m (ocean floor, tone anchor) → z5–z10 Sentinel Hub S2
   L2A 120 m cloud-free mosaic (whole domain) → z11–z13 CDSE S2 quarterly 10 m mosaic *only
   where NAIP/USGS is void* (BC, ocean, Idaho gaps) → z10–z14 USGS `USGSImageryOnly` harvest
   for US land (throttled, ≤ 8 concurrent; whites and 404s fall through to the layer below).
   Each z/x/y cell stores the highest-priority present tile; a cell with no source at z ≤ 10
   fails the build. One output pyramid, one tile format (WebP), one grade.
2. **Host it in the existing R2 bucket (`cascadia-terrain`) under `imagery/v1/`**, as plain
   `{z}/{x}/{y}.webp` objects. A rebuild is a new prefix (`imagery/v2/`), never an overwrite —
   the `terrain/v1/` precedent.
3. **Serve it from a custom domain on the bucket, `tiles.papsukkal.com`**, directly — not from
   `r2.dev` ("rate-limited and should only be used for development purposes") and not through a
   Pages Function per tile (Functions share the 100,000/day free quota; static objects are free).
   Terrain moves onto the same host, which retires the r2.dev hazard ADR-0021 shipped with. The
   host joins `BasemapProvider.cspHosts`; bucket CORS allows `GET, HEAD` from the app origin.
4. **Register a `cascadia-mosaic` provider in `BasemapProvider.ts`**: `UrlTemplateImageryProvider`
   with `minimumLevel 0`, `maximumLevel` read from the manifest (14 now, 16 after option D),
   `rectangle: HARD_DOMAIN`, `hasAlphaChannel: false`, **no** `tileDiscardPolicy` (the build
   guarantees no voids), identity client grade (the grade is baked), `createBasePlate → null`
   (the pyramid *is* the plate; the edge vignette stays). Default via `VITE_BASEMAP`;
   `usgs-imagery` stays registered as the live fallback — the mosaic is an enhancement of the
   ground, never a dependency of the app.
5. **Option D next: NAIP WA 2023 (0.6 m) / OR 2022 (0.3 m) → z15–z16**, built in-cloud in
   us-west-2 next to the `naip-visualization` COGs (WA alone is ≈ 2.25 TB at MPC size; the home
   uplink measured 1.35 MB/s — a 19-day download, so the build never runs here). Land only; the
   fill stops at z14 and z15–16 over sea/BC upsample the z14 parent through Cesium's normal
   404 path. Ships only after C has proved the pipeline; bumps `maximumLevel` to 16.
6. **Attribution** is one on-screen line carrying every source, and a `manifest.json` beside
   the tiles carrying the full per-source licence text: "USDA NAIP · USGS The National Map ·
   Contains modified Copernicus Sentinel data 2025 · NASA Blue Marble". Where the Sentinel Hub
   120 m mosaic is in the stack, its CC-BY credit form ("Contains modified Copernicus data
   [year] processed by Sentinel Hub") is the one printed; the year is the vintage recorded in
   the manifest, not a constant.

## Sources and licences (quoted from lens I §1, never assumed)

| Source | Role in the pyramid | Licence, as quoted | Credit line requested |
|---|---|---|---|
| NAIP (USDA FPAC), `naip-visualization` on AWS | z15–z16 land (option D) | AWS Registry: "Public Domain with Attribution"; data.gov licence `https://www.usa.gov/publicdomain/label/1.0/` | FSA: "use of appropriate byline/photo/image credits is requested" — "U. S. Department of Agriculture, Farm Service Agency." |
| USGS `USGSImageryOnly` (The National Map) | z10–z14 US land, harvested once, throttled | "Map services and data downloaded from The National Map are free and in the public domain." … "There are no restrictions" | "Map services and data available from U.S. Geological Survey, National Geospatial Program." |
| Sentinel Hub S2 L2A 120 m mosaic (`sentinel-s2-l2a-mosaic-120`, eu-central-1) | z5–z10 whole-domain cloud-free plate | "CC-BY 4.0, Credit: Contains modified Copernicus data [year] processed by Sentinel Hub" | as licensed: "Contains modified Copernicus data [year] processed by Sentinel Hub" |
| CDSE Sentinel-2 quarterly 10 m mosaic (Copernicus) | z11–z13 fill where USGS/NAIP is void (BC, ocean, Idaho gaps); tone reference | Copernicus Sentinel Data Legal Notice: "free, full and open access … (a) reproduction; (b) distribution; (c) communication to the public; (d) adaptation, modification and combination with other data and information; (e) any combination of points (a) to (d)." | Required notice: "'Contains modified Copernicus Sentinel data [Year]' for Sentinel data" |
| NASA Blue Marble Next Generation (500 m; GIBS for the interim live layer) | z0–z8 ocean floor and tone anchor | NASA media policy: "NASA content – images, audio, video, and media files … generally are not subject to copyright in the United States." | "NASA should be acknowledged as the source of the material." GIBS: "We acknowledge the use of imagery provided by services from NASA's Global Imagery Browse Services (GIBS), part of NASA's Earth Science Data and Information System (ESDIS)." |
| **EXCLUDED — EOX Sentinel-2 cloudless** | — | 2018–2025 layers "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License". A re-tiled, re-graded copy is "Adapted Material"; the grant is to "produce, reproduce, and Share Adapted Material for NonCommercial purposes only"; ShareAlike: "The Adapter's License You apply must be a Creative Commons license with the same License Elements" — which would force the whole NAIP + Sentinel + Blue Marble composite to BY-NC-SA. The same pixels are available under Copernicus/CC-BY terms with no NC or SA string. | never in a derivative |
| **EXCLUDED — Esri World Imagery** | — | "licensed under the Esri Master License Agreement"; "This layer is not intended to be used to export tiles for offline"; E300 fn.10 "Programmatic use of session tokens (e.g., exporting volumes of basemap tiles) is not permitted." A mosaic is by definition an export. | — |

## Build invariants (these ARE the continuity)

1. **Never white, never transparent.** Every stored tile is opaque and derived from real earth.
   Voids are decided at build time by the same 3×3 ≥ 252 rule the client's `white-discard.ts`
   uses, plus 404s; a void falls to the next layer down, never to a colour. The build asserts:
   every tile z0..14 exists, is opaque, mean luminance in [12, 235], no 3×3 region ≥ 252.
2. **Graded once.** `IMAGERY_GRADE` (`saturation 0.88, brightness 0.94, contrast 1.04,
   gamma 1.0`, `BasemapProvider.ts`) is applied to pixels in the build; the mosaic provider's
   client grade becomes identity. JPEG/WebP quantisation therefore happens *after* grading, and
   the plate, the fill and the land share one tone by construction.
3. **Per-source histogram match.** Each source layer's luminance and chroma histograms are
   matched to the co-registered Sentinel-2 mosaic under it at z10 (whole-domain reference)
   before re-tiling — per quad for NAIP, per tile for the USGS harvest. This is the one place
   the "per-tile tone normalisation is not possible in the client" finding becomes possible:
   at build time.
4. **Ocean is data, not absence.** Below z14 the sea is the S2 / Blue Marble pixel; above z14
   it is the z14 parent by upsampling.
5. **Deterministic, pinned, and provenance-carrying.** Inputs are named by vintage
   (`wa_060cm_2023`, the S2 mosaic period, the Blue Marble month); `imagery/v1/manifest.json`
   records, per zoom range, the source, vintage, licence line, grade parameters and build
   commit. The credit line on screen is derived from it. The repo's provenance rule applies to
   pixels too.

## Serving

- **Plain `z/x/y` objects**, one per tile, on the bucket's custom domain. Cloudflare's default
  cache covers WEBP and JPG extensions and honours the origin `max-age`; there is no code in the
  path.
- **Cache headers set at upload**: `imagery/v1/{z}/{x}/{y}.webp` → `public, max-age=31536000,
  immutable` (pinned by prefix); `imagery/v1/manifest.json` → `public, max-age=300` (the one
  file republished in place — the terrain `layer.json` precedent); 404s at z15–16 over sea/BC
  → Cloudflare's short default. R2 keeps `Content-Type` on upload; WebP tiles carry no
  `Content-Encoding`, so ADR-0021's gzip lesson does not recur.
- **Not PMTiles** for raster. Cesium 1.144 has no PMTiles provider (a custom one is ~80 lines
  and a second imagery code path to keep alive); the edge cannot cache what a Function assembles
  from `206 Partial Content`; R2 egress is free and per-object Class B cost is identical per
  tile served. PMTiles' only win here is upload op count. PMTiles stays the plan for the
  *vector* layers in CINEMATIC_ARCHITECTURE §5.
- **Not a Pages Function proxy** per tile: 1,000 visitors × 300 tiles = 300 k/day, over the free
  plan. The `/terrain/*` proxy pattern was right for 8.8 k objects; it is wrong for 357 k.

## Cost (lens I §3 arithmetic on measured tile means; WebP ≈ 0.7 × JPEG is an assumption)

| Build | Objects | Size | R2 storage / month | Upload (Class A, $4.50/M) |
|---|---|---|---|---|
| C: z0–z14, every tile, fill included | 356,795 | ≈ 4.1 GB JPEG / ≈ 2.9 GB WebP | **$0** — $0.06 list, inside the 10 GB-month free tier | **≈ $1.61** one-time |
| D: + land to z16 (fill stops at z14) | 2,756,361 | ≈ 55.6 GB JPEG / ≈ 38.9 GB WebP (z14/z16 means UNVERIFIED ± 40 %) | ≈ $0.6–0.9 list (≈ $0.43–0.68 after the free tier) | ≈ $12.40 list (≈ $7.90 within one month, after the 1 M free ops) |

Serving is Class B (GetObject): 1 M tile fetches/month = $0.36 and the free tier covers 10 M;
egress is "Free". Standing cost after C: **$0/month**. After D: ≤ $1/month. Build time: option C
≈ 3–5 h of throttled harvest plus minutes of local tiling; option D one cloud day, single-digit
dollars — never on the home uplink.

## Exit tests (gate Accepted; verbatim from the plan, Phase 3)

- E3.1 `curl -sI https://tiles.papsukkal.com/imagery/v1/12/647/1402.webp` (the z12 `{x}/{y}` cell
  over Vancouver BC, 49.25°N −123.1°E, computed with the repo's `lonToX`/`latToY`
  [repo:domain-warmer.ts:28-32]; a baked-white cell today [I §0]) returns `200`, `content-type: image/webp`,
  `cache-control: public, max-age=31536000, immutable`, and on the second request
  `cf-cache-status: HIT`.
- E3.2 The I §0 random-sample script re-run against the mosaic: 150 random z12 tiles, **150/150
  opaque and non-white** (today 59/150 real); the build's own assertion (every tile 0..14
  exists, mean luminance in [12, 235], no 3×3 region ≥ 252) is green.
- E3.3 Basin-band screenshot of the Nooksack (north edge at 49.3°N) shows no visible resolution
  step at the 49th parallel (owner sign-off on a before/after pair).
- E3.4 Harness imagery requests per scenario on BALANCED ≤ 250 [X §6], all to the tiles host,
  zero to `basemap.nationalmap.gov`; boot warm completes in ≤ 15 s on the owner's link (434
  tiles, all real, edge-cached).
- E3.5 R2 dashboard after 30 days: storage < 10 GB (free tier) for C; Class B ops in line with
  visitor counts; standing cost ≤ $1/month after D.

## Consequences

- **The ground stops drifting.** "Data refreshed June, 2024" no longer changes under the grade;
  a re-tuned `IMAGERY_GRADE` is a rebuild to `imagery/v2/`, reviewed like any other version.
- **The client gets simpler**: no discard policy, no base plate layer, identity grade, and the
  deep z10 idle warm (`warmDomainDeep`) is dropped — the z5–z9 warm becomes 434 real tiles
  (≈ 8 MB) from the edge. `domain-warmer.ts` re-points `TILE_URL`; the GIBS Blue Marble interim
  layer (plan row 10) is subsumed.
- **A new host in the CSP** and a second R2 custom domain to operate; terrain moves with it, so
  the r2.dev default in `functions/[[path]].js` becomes dead code once verified.
- **One-time build tooling under `infra/imagery/`** (GDAL ≥ 3.11 `gdal raster tile`, a Python
  harvester/composer, rclone) that must be reproducible from the manifest's build commit. Not
  verified today: the exact WEBP quality option spelling for `gdal raster tile`, CDSE S3
  prerequisites and the 10 m mosaic size over the domain, the Sentinel Hub bucket key layout,
  NAIP 2024/2025 flights for WA/OR — each is re-checked at build time, not assumed.
- **Licence hygiene becomes a build gate**: the composer refuses any input whose manifest line is
  not one of the five above. EOX and Esri pixels never enter the pipeline.
- **Visual truth**: the mosaic is `cartographic` — a composite of vintages (NAIP 2022/2023,
  Sentinel-2 2025, Blue Marble monthly). The inspector states the vintage under the camera from
  the manifest; nothing scientific is ever sampled from these pixels.
