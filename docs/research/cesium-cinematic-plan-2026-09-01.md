# Deeply cinematic, at nadir — the plan (synthesis of six verified lenses)

Research date: 2026-09-01. Type: **decision document** for the owner. Synthesises, ranks and
phases the six lens reports written the same day; it does not repeat their evidence, it cites
it. Target: `apps/web` on CesiumJS **1.144.0** (`apps/web/node_modules/cesium/package.json`;
`@cesium/engine` 26.2.0), React 19 + TS + Vite, Cloudflare Pages gateway + R2, Railway API.

Lens keys used in every citation below:

| Key | Document | What it settled |
|---|---|---|
| **R** | [cesium-cinematic-render-surface-2026-09-01.md](cesium-cinematic-render-surface-2026-09-01.md) | what the renderer is doing today; post-processing, light, fog, ortho/2D |
| **S** | [cesium-cinematic-showcase-2026-09-01.md](cesium-cinematic-showcase-2026-09-01.md) | what the best work outside does; camera motion (van Wijk), time, controllers |
| **P** | [cesium-cinematic-repos-and-skills-2026-09-01.md](cesium-cinematic-repos-and-skills-2026-09-01.md) | libraries, licenses, upstream issue status, tooling, skills |
| **I** | [cesium-cinematic-imagery-foundation-2026-09-01.md](cesium-cinematic-imagery-foundation-2026-09-01.md) | the data gap north of 49° / offshore; mosaic build + serving |
| **F** | [cesium-cinematic-film-language-2026-09-01.md](cesium-cinematic-film-language-2026-09-01.md) | the fifteen rules, composition at nadir, the shot list |
| **X** | [cesium-cinematic-performance-2026-09-01.md](cesium-cinematic-performance-2026-09-01.md) | real-GPU numbers on the owner's machine; tier budgets; the harness |
| **C** | [cesium-continuity-camera-2026-08-31.md](cesium-continuity-camera-2026-08-31.md) | prior: tile continuity, envelope, the "not possible" list |
| **G** | [liquid-glass-decision-2026-08-31.md](liquid-glass-decision-2026-08-31.md) | prior: the glass material (verdict C, reproduce with primitives) |

Verification legend: **[src:File.js:NN]** = `apps/web/node_modules/@cesium/engine/Source/<path>`;
**[dts:NNNNN]** = `apps/web/node_modules/cesium/Source/Cesium.d.ts`; **[repo:path:NN]** = this
repository. Every Cesium API this plan leans on was re-grepped in the installed package today
(§9); the eleven refuted claims from the lens verification passes are treated as false throughout
and are listed in §9 so nobody re-imports them.

---

## 1. Executive read — what "deeply cinematic" can honestly mean here

The owner's three words are *deeply cinematic*, *no angles*, and *one reveal at rest*. The six
lenses agree on the definition that makes those compatible: **cinematic = nothing breaks the
illusion; it is not more motion** [F §0; S §0; R preamble]. At pure nadir the map is a still
photograph that occasionally moves [F rule 1]. There are exactly four illusions to keep intact —
continuity, composition, light/material, and time — and every candidate move below serves one of
them or is rejected.

**What the renderer is actually doing today, and why it does not look cinematic yet.** Measured
on the owner's own MacBook Pro [X §0]: the satellite map is drawn at **one quarter of native
pixels** (`useBrowserRecommendedResolution` defaults true ⇒ `pixelRatio = 1.0`
[src:Widget/CesiumWidget.js:92-95,276-277]); the integrated GPU spends **15.5 ms per idle frame
for a still picture** because `requestRenderMode` is off [src:Scene/Scene.js:681] and 4× MSAA is
on by default [src:Scene/Scene.js:251]; and two tints nobody chose — ground atmosphere
[src:Scene/Globe.js:203] and distance fog [src:Scene/Fog.js:25,62] — are blended into an imagery
grade that was tuned around them without knowing [R §0, §4]. None of this is a design flaw; it
is Cesium's globe defaults applied to a nadir instrument.

**The three things that would change what the owner sees, in order of visible effect:**

1. **Crispness is the material** [S §5; R §3; X §4]. Rendering at device pixels on capable GPUs
   is the single largest visible gain and needs no design work. It costs ×3.8 GPU time on
   Intel-class hardware [X §0], so it ships only through a tier system that does not exist in
   the renderer yet (`store.qualityTier` never reaches `SceneController` [X §1;
   repo:apps/web/src/state/store.ts:97]).
2. **Composition** [F rule 5, §3]. Selection is the reward for a click; today the basin is framed
   to the whole canvas and then covered by a 420 px panel that mounts mid-flight
   [F §7.1-7.2; repo:apps/web/src/app/App.tsx:41-42; repo:apps/web/src/camera/CameraController.ts:92-98].
   Framing to the *stage* and gating the panel on `settled` are zero-motion, one-day wins.
3. **The ground itself** [I §0]. USGS orthoimagery stops at the 49th parallel and the coast:
   61 % of z12 tiles in the domain are white or 404, so every state/basin frame of the Nooksack
   and Skagit shows z7–z9 pixels upsampled 8–128× beside 1.6 m NAIP. No client knob reaches
   this; a self-built, public-domain/CC-BY mosaic in R2 does (≈ 4 GB, $0/month inside the free
   tier, one build day). This is the only lens finding that is *availability*, not rendering.

**What "cinematic" must NOT mean here.** Bloom, depth of field, ambient occlusion, HDR
tonemapping, procedural clouds, particle rain, animated water, shadows, a clock-driven sun,
camera tours — each either does nothing at nadir, fabricates weather or water under the
visual-truth doctrine, or costs full-screen passes on a frame that is already over budget on
integrated GPUs [R §1-6, §10; X §5; S row 14-18, 21-22; F rule 14]. The one "light" that
survives is a *fixed* hillshade from the terrain's own normals — an owner-taste A/B, not a plan
item, and only after the 2D-vs-3D decision in §7.

**The honest camera.** The most-replicated camera design in web mapping — van Wijk & Nuij's
joint pan-zoom path (Mapbox/MapLibre ρ = 1.42, deck.gl, d3) — becomes *exact* under "no angles"
because nadir + north-up collapses the camera to `(lon, lat, height)` [S §3.2, B2]. Cesium's own
flight lerps height linearly [src:Scene/CameraFlightPath.js:124], which is the "accelerates near
the ground" motion Google Earth Studio corrects. Implementing the path from `scene.preRender` with
public `camera.setView` is the highest cinematic return per line in this document, and it needs
no library [P §2].

**Cost of the whole plan.** Roughly 12–16 engineering days across three phases plus one cloud
build day, gated by a measurement harness that already ran on the owner's machine in ~45 s per
configuration [X §7]. Standing cost after Phase 3: ≈ $0–1/month of R2.

---

## 2. Ranked opportunity table

Scores are 1–5. **Impact** = visible cinematic gain at nadir. **Feasibility** = how surely
Cesium 1.144 does it through public API (5 = one documented call). **Cost** = engineering days
(5 = ≤ ½ day, 4 = 1 day, 3 = 2–3 days, 2 = 4–6 days, 1 = a migration). **Runtime** = GPU/RAM/network
per frame (5 = free or negative, 1 = unbounded). **Doctrine** = nadir, no gratuitous motion,
provenance honesty, visual-truth doctrine (5 = strengthens it). Total /25. Ties broken by impact.

| # | Move | Lens | Impact | Feas. | Cost | Runtime | Doctrine | **Total** | Why (one line) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **Rule-3 gates**: mount `BasinPanel`/`RiverPanel` and apply weather `setData` only on `flightState === 'settled'`; add a 400 ms arrival hold before the panel | F rules 3, 9; §7.1, §7.4 | 4 | 5 | 5 | 5 | 5 | **24** | The panel over Central America mid-flight is the most-photographed break of "one primary motion"; the fix is a gate in the panel host, no renderer change [repo:App.tsx:41-42; store.ts:66] |
| 2 | **Turn the hidden tints off, make the world's colour a decision**: `globe.showGroundAtmosphere = false`, `scene.fog.renderable = false` (keep `enabled` for culling), `sun.show = moon.show = false`, `globe.showWaterEffect = false`, explicit `msaaSamples`; re-tune `IMAGERY_GRADE` once against the same screenshots | R §10.1; X §4; F M16 | 3 | 5 | 5 | 5 | 5 | **23** | The grade in `BasemapProvider.ts:63` was tuned *around* a scattering veil and a distance fog it never knew about; the GROUND_ATMOSPHERE define is compiled into every globe fragment today [X §0] |
| 3 | **Cap the flight apex**: pass `maximumHeight ≤ ZOOM_CEILING_M` to `flyToBoundingSphere` | R §7, §10.5 | 3 | 5 | 5 | 5 | 5 | **23** | A basin→basin arc must never rise above the composed home frame mid-flight, where the discard boundary and vignette edge flash into view; `Camera.js:3756` passes it straight through |
| 4 | **Stage-composed framing**: frame the basin/point to the canvas minus chrome (left ~60 % desktop, top ~54 % phone), padding 1.1 against the *stage's* half-angle | F rule 5, §3.1-3.4, M6 | 5 | 4 | 4 | 5 | 5 | **23** | The single largest compositional win at zero motion cost; `flyToBasin` frames the whole frustum today [CameraController.ts:92-98]. Use the shifted-destination form (M6a): the orthographic frustum in row 9 has **no** `xOffset`/`yOffset` (grep of `Core/OrthographicFrustum.js`: zero hits, today), so the frustum-offset form (M6b) is perspective-only |
| 5 | **Explicit rendering**: `scene.requestRenderMode = true`; audit every time-driven layer for `requestRender()` | R §7, §10.4; X §4, §9.3 | 3 | 5 | 4 | 5 | 5 | **22** | A still nadir map draws the same frame 60×/s: 15.5 ms GPU per idle frame on Intel for nothing [X §0]; the repo already calls `requestRender()` at its mutation points [SceneController.ts:187,397,474; CameraController.ts:182]; it also hands the glass compositor its headroom [G; X §5] |
| 6 | **Wire the quality tier into the renderer** (`SceneController.setQuality`): `useBrowserRecommendedResolution=false` + `resolutionScale`, `msaaSamples` (4 on HIGH/ULTRA, 1 on BALANCED/LOW), `tileCacheSize`, `targetFrameRate` per X §6; auto-detect by 90 idle frames after `onGroundComposed`, runtime downgrade via `FrameRateMonitor.fromScene` | X §6, §9.2, §9.4; R §3 | 4 | 5 | 3 | 5 | 5 | **22** | The prerequisite for every visible upgrade; MSAA alone is half the Intel frame (15.5→7.95 ms idle) [X §0]; today the tier only styles the glass [X §1] |
| 7 | **Weather wash crossfade**: second `ImageryLayer` at alpha 0 → 1 in `scene.preRender`, remove the old; bound at `--dur-ui` while dragging, `--dur-state` on release; inspector labels the blended frame `cinematic`; Zoom-Earth-style loop presets (Fast/Smooth) | F S5, M7; S rows 10, 23; C §1b | 4 | 5 | 4 | 4 | 5 | **22** | Scrubbing pops today (`detach(); new ImageryLayer; attach`) [WeatherFieldLayer.ts:171-173]; only *opacity* crosses between two real slices — values never interpolate (Windy staff's own "rather a bug than a feature") |
| 8 | **Prefetch the landing LOD during the flight**: `domainTiles(z, bboxOfLanding)` via plain `fetch()` at flight start | S §7.1, rec 3 | 4 | 5 | 4 | 4 | 5 | **22** | A basin→point flight lands on cold tiles above the z10 warm and can hold the plate up to `MAX_HOLD_MS = 8000` [TransitionPlate.ts:22]; 2.4 s of flight is a lot of tile fetches; no Cesium internals |
| 9 | **Cut-vs-fly decision**: fly when the destination footprint is inside the frame; arc (≤ next band up) when not; veil-cut when the duration clamps at `maxMs` | F §4.3 | 3 | 5 | 4 | 5 | 5 | **22** | A clamped 2.4 s smear across the state reads as a loading glitch; deep links are already cuts [bridge.ts:15-18] — extend the same treatment |
| 10 | **NASA GIBS Blue Marble as imagery layer 0** (`GoogleMapsCompatible_Level8`, JPEG, CORS `*`, 3-day cache), USGS above it | P §9, rec 3; I §1.5 | 3 | 5 | 4 | 5 | 5 | **22** | Cloud-free, tonally uniform, keyless, public domain — the "coarse base plate" the doctrine already names; interim until row 13's mosaic (which bakes Blue Marble in) |
| 11 | **Adopt the real-GPU harness as the merge gate** (`tests/perf/perf-harness.mjs`, `channel: 'chromium'`, `powerPreference` injection, 5-run medians) | X §7, §9.1 | 2 | 5 | 4 | 5 | 5 | **21** | Every prior "measured" number came from SwiftShader; the timer query and the memory API both work in new-headless Chromium 151 [X §2]. Note `tests/perf/` already exists as the Python query-budget harness — the browser harness sits beside it |
| 12 | **Orthographic frustum in 3D**: `camera.switchToOrthographicFrustum()` after the initial view; patch `narrowestHalfAngle()`/`framingRange` for the ortho case; re-check band thresholds | R §8, §10.3 | 4 | 4 | 3 | 5 | 5 | **21** | Removes the ×1.33 perspective footprint gradient and edge parallax that make max-out read as a globe close-up; the keystone (0.865 north/south edge ratio) remains — only SCENE2D removes that (row 21). `Camera.js:4008`; width follows every move via `_adjustOrthographicFrustum` [Camera.js:1249,1300,1335,1791,2048,2491] |
| 13 | **Van Wijk/Nuij camera path at nadir** (ρ = 1.42, ~1.2 screenfuls/s, duration from path length S, clamped by `MOTION.flight`), driven per frame from `preRender` via `camera.setView`; log-height on pure zooms for free; velocity-matched retargeting when a flight supersedes | S rows 1-5, §3.2, rec 1; F §1 (van Wijk row) | 5 | 4 | 2 | 5 | 5 | **21** | Cesium's default lerps height on pure zooms [CameraFlightPath.js:124]; the whole web-map ecosystem ships this path; it is exact under "no angles". Reconcile with F: the arc peak is clamped to the band above / `ZOOM_CEILING_M`, so ρ shapes the path but never lifts the camera out of the envelope. **Half-step first** (½ day): keep `flyToBoundingSphere`, pass `maximumHeight` from the van Wijk peak |
| 14 | **Imagery mosaic, option C** (z0–z14 in R2: Blue Marble → Sentinel-2 120 m plate → CDSE S2 10 m fill for BC/ocean → throttled USGS harvest; graded once, tone-matched, opaque by assertion; **R2 custom domain first**; `cascadia-mosaic` provider; ADR) | I §2, §4, §5, §8 | 5 | 4 | 2 | 5 | 5 | **21** | The only fix for the 61 % void north of 49° and offshore at z ≥ 10 [I §0]; ≈ 357 k objects, ≈ 4 GB, $0/month inside the free tier, ≈ $1.61 upload; also retires the deep z10 idle warm. Details §4 |
| 15 | **Native-DPR rendering on HIGH/ULTRA** (`useBrowserRecommendedResolution=false`, `resolutionScale 1.0`, MSAA 1 when DPR ≥ 2) | R §3, §10.2; X §0, §9.5; S §2.3, rec 6 | 5 | 5 | 3 | 2 | 5 | **20** | The upgrade the owner will actually *see*: the tiles already contain twice the detail being drawn. ×3.8 GPU on Intel (59 ms/frame with MSAA) — ships only through row 6's tiers and row 11's gate |
| 16 | `Texture.defaultColor` = canvas dark (`(Cesium as any).Texture.defaultColor`; exported at `Cesium.js:434`, untyped in `Cesium.d.ts`) | P §1 (corrected) | 1 | 4 | 5 | 5 | 5 | **20** | One line; placeholder material textures default to white today [src:Renderer/Texture.js:1135]; only affects `Material` placeholders, not imagery tiles |
| 17 | **Mosaic option D**: NAIP WA 2023 (0.6 m) / OR 2022 (0.3 m) → z15–z16, built in us-west-2 next to the data | I §1.1, §4.4 | 3 | 3 | 2 | 5 | 5 | **18** | Local band only; WA source is ≈ 2.25 TB, so the build must run in-cloud (one day, single-digit dollars); ≈ $0.6–0.9/month standing; z14/z16 tile means are UNVERIFIED ±40 % |
| 18 | **Spike Cesium 1.144's `ScreenSpaceMapCameraController` + `ScreenSpaceZoomCameraController`** behind a flag | S row 19, rec 2; P §1, rec 1 | 3 | 3 | 3 | 5 | 4 | **18** | The first upstream *map* pan (screen-space, tangent to the ellipsoid) — could make the heading spring-back dead code. But: pan-only, preserves rather than enforces nadir, and the zoom controller's `maximumZoomDistance` defaults to **100 km** [src:Scene/Controllers/ScreenSpaceZoomCameraController.js:151] below the 1,250 km ceiling; SSCC clamps vanish with `enableCollisionDetection=false` [C Problem 2 caveat 1]. New API scoped "for an asset inspection use case" |
| 19 | **Fixed-sun hillshade at basin/river/local**: `CesiumTerrainProvider.fromUrl(root, { requestVertexNormals: true })` in `upgradeTerrain()`, `globe.enableLighting = true`, `scene.light = new DirectionalLight({ direction: NW ~45° })`, low `lambertDiffuseMultiplier`, optional `verticalExaggeration ≈ 1.3` | R §4, §5, §10.6 (corrected); F rule 8, M15; X §5 | 4 | 4 | 3 | 3 | 3 | **17** | Relief is the one true thing nadir hides, and the R2 pyramid carries `octvertexnormals` — but the client never *requests* them today [SceneController.ts:394; src:Core/CesiumTerrainProvider.js:1062-1066], so `enableLighting` would silently take the day/night-terminator path. It also double-shades NAIP's baked sun, tile bytes grow, and it is incompatible with SCENE2D (row 21). **A/B only, after §7 Q1** |
| 20 | **Custom `PostProcessStage` film grade / GPU vignette** (one pass over `colorTexture`) | R §1; P §3, rec 2; F M18 | 2 | 5 | 3 | 3 | 3 | **16** | The one post-process worth owning — but it grades labels and glyphs too, forces the scene-framebuffer round trip [src:Scene/Scene.js:3969-3990], and F rule 14 forbids stacking it on the existing vignette layer. Defer until the per-layer grade is judged insufficient |
| 21 | **SCENE2D + `WebMercatorProjection` migration** | R §8, §11 | 4 | 3 | 1 | 4 | 4 | **16** | The honest end state if "no angles" is permanent: a true rectangle domain, no keystone, tile-native look; but relief, hillshade, exaggeration and `Globe.material` slope all vanish (heights are zeroed in 2D [src:Shaders/GlobeVS.js:100-103]), the framing/band plumbing needs rewriting, and the envelope math was validated in 3D only. **Owner decision, §7 Q1** |
| 22 | **Streamline (dash-phase) river flow** from `flow_visual_intensity` | S row 24, rec 5 | 3 | 3 | 3 | 2 | 3 | **14** | Public API, no particles — but `PolylineDashMaterialProperty` has no phase uniform (16 discrete `dashPattern` steps or a custom `Material`), and any per-frame motion defeats row 5's explicit rendering. Defer to the "at rest, on demand" layer class |

Not scored, because a lens verdict already rejects them: everything in §6.

**Contradictions between lenses, resolved here.**
- PMTiles for the raster mirror (P §8, §10: adopt) vs z/x/y objects (I §5.3: not for raster) →
  **objects for raster imagery**, PMTiles only for the vector layers already planned. The imagery
  lens's reasoning is deeper (no Cesium PMTiles provider; the edge cannot cache 206s; Class B cost
  is identical) and the repos lens's own verification upgraded the worker to "if built".
- van Wijk ρ tunable (S) vs "ρ is not a tunable here" (F §1) → the *shape* is adopted, the peak is
  clamped to the band above / `ZOOM_CEILING_M` (row 13). Both lenses' facts stand.
- FXAA "adopt check" (P §1) vs "REJECT while MSAA 4× is on" (R §1) → per X §6: FXAA only on
  BALANCED, only if MSAA-off aliasing is visible and it fits. No FXAA on top of MSAA.
- Solar light A/B (S row 13, rec 7) vs F rule 8 ("light is a constant, not a clock") → any
  time-of-day mood is a *grade* in Presentation Mode only (F M17), never a moving light; the A/B
  that survives is the fixed hillshade (row 19).
- Fog "TUNE off" (R §4) vs "FOG define never compiled at nadir, cost ≈ 0" (X §4) → both true
  (enabled below 800 km, blend negligible at nadir); set `fog.renderable = false` for determinism
  [src:Scene/Fog.js:36] and keep `enabled` for the culling economy.
- Boot warm "~260 tiles" (comments at `domain-warmer.ts:8,78`) → **434** (P §8 correction;
  I §6 table says 439 including z≤4 — same set). Fix the comment when touching the file.
- GIBS Blue Marble as a live layer (P rec 3) vs baked into the mosaic (I §4.1) → row 10 is the
  interim; row 14 subsumes it.

---

## 3. Phased mission proposal

Three phases, each with exit tests that run on the owner's machine (Intel UHD 630 via
`powerPreference: 'low-power'` = the "ordinary laptop"; AMD 5300M = discrete) [X §2]. Files are
the repo's real files. The mosaic build (Phase 3) touches no renderer code and can start on day
one in parallel; it is placed last only because its *client* cut-over depends on Phase 1's tiers.

### Phase 1 — The honest baseline (≈ 4–5 days)

Purpose: stop paying for what is not displayed; make every later change measurable; close the two
open film-rule violations that need no renderer work.

| Step | Files | Rows |
|---|---|---|
| 1.1 Land the browser perf harness beside the Python one: `tests/perf/perf-harness.mjs`, `tests/perf/vite.perf.config.mjs`, `apps/web/package.json` script `perf:owner`; document in `tests/perf/README.md` that SwiftShader timings are never cited | X §7 | 11 |
| 1.2 Hygiene block in the `SceneController` constructor after the atmosphere lines: `globe.showGroundAtmosphere = false`; `scene.fog.renderable = false`; `scene.sun.show = false`; `scene.moon.show = false`; `globe.showWaterEffect = false`; `scene.msaaSamples` explicit; then one `IMAGERY_GRADE` re-tune in `BasemapProvider.ts` against the e2e screenshot set | `apps/web/src/scene/SceneController.ts:133-135`, `apps/web/src/layers/basemap/BasemapProvider.ts:63` | 2 |
| 1.3 `scene.requestRenderMode = true` behind `VITE_REQUEST_RENDER` (default on after 1.5 passes); audit `layers/**` for time-driven work (PolylineGlow is static; `TransitionPlate` is DOM; `WeatherFieldLayer` already calls `requestRender`) | `SceneController.ts:97-106` (Viewer options), `apps/web/src/layers/**` | 5 |
| 1.4 `SceneController.setQuality(tier)` + `viewer.useBrowserRecommendedResolution` / `resolutionScale` / `msaaSamples` / `tileCacheSize` / `targetFrameRate` per X §6; store → controller wiring in `SceneView`; auto-detect after `onGroundComposed`; `FrameRateMonitor.fromScene` downgrade; keep `SettingsMenu` override | new `apps/web/src/scene/quality.ts`; `SceneController.ts`; `apps/web/src/app/SceneView.tsx`; `state/store.ts:97,113` | 6 |
| 1.5 Native DPR on HIGH/ULTRA only (through 1.4) | same | 15 |
| 1.6 Rule-3 gates: panel host reads `flightState`; 400 ms hold; `SceneDataBridge` defers weather `setData` while a flight is active | `apps/web/src/app/App.tsx:41-42`, `apps/web/src/panels/*`, `apps/web/src/scene/bridge.ts` | 1 |
| 1.7 `maximumHeight: ZOOM_CEILING_M` on `flyToBoundingSphere` | `apps/web/src/camera/CameraController.ts:157-174` | 3 |
| 1.8 `Texture.defaultColor` hygiene; fix the stale "~260" comments | `SceneController.ts`; `apps/web/src/layers/basemap/domain-warmer.ts:8,78` | 16 |

**Exit tests (owner's machine, 5-run medians, `perf:owner`):**
- E1.1 The harness prints `UNMASKED_RENDERER` containing "Intel" in `--gpu=low-power` mode and
  "AMD" otherwise, and refuses to run when the renderer string contains "SwiftShader".
- E1.2 `defines` recorded by the harness no longer contain `GROUND_ATMOSPHERE`; screenshot diff of
  the home frame vs the pre-change baseline shows only the expected tint shift (re-tuned grade
  approved by the owner on the Skagit and Puyallup basin frames).
- E1.3 During the 3 s `idle-final` phase, frames rendered ≤ 5 (was ~180) and Intel idle GPU p50
  ≤ 1 ms (was 15.5 ms); no "stuck frame" in the e2e screenshot suite (all specs green under
  `VITE_REQUEST_RENDER=on`).
- E1.4 BALANCED on Intel@1280×800@2 (MSAA 1, `resolutionScale` 0.5): zoom-in GPU p95 ≤ 14 ms,
  rAF Δ p95 ≤ 33.3 ms, JS heap ≤ 200 MB [X §6 table]. HIGH on AMD at native DPR: zoom-in GPU p95
  ≤ 13 ms, rAF p95 ≤ 16.7 ms. Today's build fails BALANCED on Intel (36.5 ms) — the test must
  flip from red to green.
- E1.5 `document.querySelector('canvas').width === 2560` at DPR 2 on HIGH; `=== 1280` on
  BALANCED.
- E1.6 Playwright spec: select Skagit from orbital; assert the basin panel's first paint time is
  ≥ `flight.settled + 400 ms` and that no weather layer `setData` occurred between `started` and
  `settled` (instrument via `data-*` attributes, as `data-tiles-pending` is today).
- E1.7 Log the flight's maximum `positionCartographic.height` on a Nooksack → Puyallup flight;
  assert ≤ 1,250,000 m.

### Phase 2 — Composition and motion (≈ 5–6 days)

Purpose: the arrival is the shot; the flight is the cut between shots [F rule 5].

| Step | Files | Rows |
|---|---|---|
| 2.1 Stage-composed framing: a pure `stageOffset(range, halfAngle, coveredFraction)` in `flight-math.ts`; `flyToBasin`/`frameForecastPoint` shift the destination (M6a); follow-select samples the *stage* centre; phone stage = top ~54 % | `apps/web/src/camera/flight-math.ts`, `CameraController.ts:92-104`, `SceneController.ts:315-342` | 4 |
| 2.2 Orthographic frustum: `switchToOrthographicFrustum()` after `setInitialView()`; ortho branch in `narrowestHalfAngle()`/`framingRange` (width from bbox); re-check `BAND_CONFIG` thresholds (apparent zoom at a given height is wider under ortho) | `CameraController.ts:87-90,185-189`, `apps/web/src/scene/bands.ts:18` | 12 |
| 2.3 Van Wijk path, half-step first (`maximumHeight` from the van Wijk peak, clamped to band-above / ceiling); then the full path from `preRender` with `camera.setView`, `minimumJerk` as the time-warp, duration from path length S, velocity-matched supersede; reduced motion unchanged | `CameraController.ts:127-177`, `apps/web/src/design-system/motion.ts:14`, new `apps/web/src/camera/zoom-pan-path.ts` + unit tests | 13 |
| 2.4 Cut-vs-fly decision (`Camera.computeViewRectangle` for "in view"; veil-cut when the duration clamps) | `CameraController.ts`, `flight-math.ts` | 9 |
| 2.5 Landing-LOD prefetch at flight start (`domainTiles(z, landingBbox)`, concurrency 6, aborted on interrupt) | `apps/web/src/layers/basemap/domain-warmer.ts`, `SceneController.ts:163` | 8 |
| 2.6 Weather wash crossfade + loop presets | `apps/web/src/layers/fields/WeatherFieldLayer.ts:160-180`, `apps/web/src/timeline/TimelineController.ts` | 7 |
| 2.7 GIBS Blue Marble as layer 0 with both credit strings (interim until Phase 3) | `BasemapProvider.ts:116-128` (`createBasePlate`) | 10 |

**Exit tests:**
- E2.1 Screenshot: Skagit selected on desktop 1440×900 — the basin's bounding-sphere projection
  lies entirely inside the left `100vw − min(420px, 40vw)` stage with ≥ 12 % headroom at the
  top; on the 375×812 mobile preset it lies inside the top 54 %.
- E2.2 Under ortho, the ground-metre-per-pixel measured at the frame centre and at the frame
  edge (two `pickEllipsoid` pairs, 10 px apart) differ by < 2 % at the 1,250 km ceiling (today
  ≈ 33 %); `flyToBasin` still lands with the basin filling the stage (E2.1 holds under ortho).
- E2.3 Basin → forecast-point flight (450 km → 12 km): per-frame apparent ground speed (frame-to-
  frame change of visible ground width, in screen widths/s) has coefficient of variation < 0.25
  over the middle 80 % of the flight (linear-height lerp today produces a > 1.0 spike near the
  ground). Both canonical flights (state→basin, basin→point) pass the owner's side-by-side A/B.
- E2.4 Selecting a basin whose footprint is outside the current frame with a clamped 2,400 ms
  duration produces a veil-cut, never a flight (`started` event carries `cut: true`).
- E2.5 After the basin→point flight, `TransitionPlate` hold time (capture → release) ≤ 1,000 ms on
  a warm network (today up to 8,000 ms); measured by a `data-plate-hold-ms` attribute.
- E2.6 Scrubbing the −72 h MRMS loop at 10 Hz: no frame shows a detached wash (screenshot every
  100 ms during a scripted scrub, all frames contain the layer), BALANCED rAF p95 ≤ 33 ms
  during the scrub; the inspector shows `cinematic` on the blended frame.
- E2.7 No pixel of the home frame shows `globe.baseColor` inside HARD_DOMAIN (the plate covers
  every void at z ≤ 8).

### Phase 3 — The ground itself (≈ 1 build day + 2 client days, plus a cloud day for D)

Purpose: continuity as a property of the data [I title]. Full recipe in §4.

| Step | Files | Rows |
|---|---|---|
| 3.1 Attach a custom domain to the R2 bucket (e.g. `tiles.papsukkal.com`); move terrain onto it too (r2.dev is rate-limited and "should only be used for development purposes" [I §5.1]); add the host to `cspHosts`; bucket CORS `GET,HEAD` for the app origin | `functions/[[path]].js:98` (terrain default), Cloudflare dashboard, `BasemapProvider.ts:94` | 14 |
| 3.2 Build option C outside the repo (`build/` per I §4.3), upload to `cascadia-terrain/imagery/v1/` with immutable headers; `manifest.json` records sources, vintages, licence lines, grade, build commit | build scripts (new, under `infra/imagery/`), rclone | 14 |
| 3.3 Register `cascadia-mosaic` in `BasemapProvider.ts`: `UrlTemplateImageryProvider` `{z}/{x}/{y}.webp`, `maximumLevel` from the manifest, `rectangle: HARD_DOMAIN`, `hasAlphaChannel: false`, **no** `tileDiscardPolicy`, identity grade, `createBasePlate → null`; default via `VITE_BASEMAP`; keep `usgs-imagery` registered as the live fallback; re-point `domain-warmer.ts` `TILE_URL`; drop `warmDomainDeep` | `BasemapProvider.ts`, `domain-warmer.ts:19-20,93-97`, `SceneController.ts:136-141` | 14 |
| 3.4 ADR-0022 "Imagery is a self-built PNW mosaic in R2" in the ADR-0021 mould; credit line "USDA NAIP · USGS The National Map · Contains modified Copernicus Sentinel data 2025 · NASA Blue Marble" | `docs/adr/ADR-0022-*.md`, `apps/web/src/scene/credits.ts` | 14 |
| 3.5 Option D (NAIP z15–z16) on a us-west-2 spot box; bump `maximumLevel` to 16 | `infra/imagery/`, manifest | 17 |
| 3.6 Only after §7 Q1 is answered "3D stays": hillshade A/B on Skagit and Puyallup river-band screenshots (`requestVertexNormals: true`, `DirectionalLight`), accept only if the ground reads as *the same ground with relief*, not re-lit terrain | `SceneController.ts:391-401`, `applyBand` | 19 |

**Exit tests:**
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
- E3.6 (hillshade, if attempted) River-band A/B: the owner picks the lit frame blind on both
  basins, and BALANCED zoom-in GPU p95 stays ≤ 14 ms with normals requested (tile bytes measured
  before/after).

---

## 4. The imagery-foundation decision: mosaic vs expanded warm

**Decision: build the mosaic (option C now, D next). Do not expand the warm beyond z9.**

Why the warm cannot do it [I §0, §6]: the warm is a *latency* tool — it puts tiles the service
*has* into the HTTP cache. Above z9 the service does not have the north third of the domain or
the ocean: 55–61 % of z10–z12 requests there return baked white (2,419 B / 872 B) or 404. A
z5–z12 warm would be 22,745 requests, ~20 minutes on the visible boot screen, repeated by every
new visitor against shared public infrastructure, and it would still render z7–z9 pixels over
British Columbia at basin band. The mosaic is an *availability* tool: every stored tile is
opaque, derived from real earth, graded once, tone-matched, pinned by vintage, and served from the
edge for free (R2 egress is "Free" [I §3]).

Numbers (all from I §3, corrections applied): z0–z14 is 356,795 tiles, ≈ 4.1 GB JPEG / ≈ 2.9 GB
WebP (WebP ratio is an assumption — measure on the first 1,000 land tiles), **$0/month inside the
10 GB free tier**, ≈ $1.61 one-time upload. Option D adds ≈ 2.4 M land tiles at z15–z16:
56–78 GB JPEG (the z14/z16 tile means are UNVERIFIED ±40 %), ≈ $0.6–0.9/month, ≈ $12 upload.

Licences, quoted in I §1 (never assumed): NAIP "Public Domain with Attribution"; USGS National
Map "free and in the public domain … no restrictions"; Sentinel Hub 120 m mosaic "CC-BY 4.0,
Credit: Contains modified Copernicus data [year] processed by Sentinel Hub"; Copernicus legal
notice grants "(d) adaptation, modification and combination with other data"; NASA content
"generally … not subject to copyright in the United States". **Excluded:** EOX cloudless (CC
BY-NC-SA 4.0 — ShareAlike would force the whole composite to BY-NC-SA) and Esri World Imagery
("not intended to be used to export tiles for offline"; "Programmatic use of session tokens …
is not permitted") [I §1.4, §1.6].

Build recipe, summarised (full commands in I §4.3–4.4; none was run — GDAL/rio/rclone are
absent on this Mac and Docker is stopped):

1. **Layer stack, bottom-up:** z0–z8 Blue Marble NG 500 m (ocean floor, tone anchor) → z5–z10
   Sentinel Hub S2 L2A 120 m mosaic (whole domain, cloud-free) → z11–z13 CDSE S2 quarterly 10 m
   mosaic *only where NAIP/USGS is void* (BC, ocean, Idaho gaps) → z10–z14 USGS ImageryOnly
   harvest (US land; throttled ≤ 8 concurrent, ≈ 3–5 h; whites/404 fall through) → z15–z16 NAIP
   COGs (option D, in-cloud).
2. **Invariants the build enforces:** never white, never transparent (void test = the client's
   own 3×3 ≥ 252 rule [repo:apps/web/src/layers/basemap/white-discard.ts:24-36]); grade once
   with `IMAGERY_GRADE` and set the client grade to identity; per-source histogram match to the
   S2 plate at z10; ocean is data, not absence; deterministic and pinned (`imagery/v1/`, a
   rebuild is `v2`).
3. **Tools:** `gdalwarp` to EPSG:3857 COG; `gdal raster tile --tiling-scheme WebMercatorQuad
   --convention xyz -f WEBP` (GDAL ≥ 3.11; the WEBP quality option spelling is UNVERIFIED —
   check `--help`); a small Python harvester/composer; `rclone copy` with
   `Cache-Control: public, max-age=31536000, immutable` and `Content-Type: image/webp`.
4. **Serving:** R2 custom domain, direct (`https://tiles.papsukkal.com/imagery/v1/{z}/{x}/{y}.webp`)
   — zero Pages Function invocations (Functions share the 100 k/day free quota [I §5.2]),
   Cloudflare's default cache covers WEBP/JPG; not PMTiles (no Cesium provider, 206s cannot be
   edge-cached, §2 contradictions).
5. **Client:** the `UrlTemplateImageryProvider` block in I §5.4, verified against
   [dts:46188-46253]; WebP decoding is the browser's (`createImageBitmap`
   [src:Core/Resource.js:874-881,937-949]); omitting `tileDiscardPolicy` saves **no** decode
   step (refuted claim) — it is omitted because the build guarantees no voids.
6. **Provenance:** `manifest.json` beside the tiles and the credit line on screen — "where did
   it come from, when, from which version" applies to pixels too [CLAUDE.md, the one rule].

Interim while the build runs: row 10 (GIBS Blue Marble as layer 0) costs half a day and removes
the bare-canvas void at z ≤ 8; it is subsumed when the mosaic lands.

---

## 5. Repos, libraries and skills — adopt, adapt, skip

Licences are quoted from the lens that fetched them (P unless stated); "—" means the lens
recorded none.

| Name | Licence (quoted) | Verdict | Why / conditions | Lens |
|---|---|---|---|---|
| CesiumJS 1.144.0 core: `PostProcessStage`, `Controller` framework, `Camera.flyTo` options, `FrameRateMonitor`, `ImageryLayer` uniforms | "Apache-2.0" (`cesium/package.json`) | **adopt** (already) | Everything the plan uses is public API in the installed version; no bump to 1.145.0 — its additions (ClippingPolygons, vector draping, `Scene.snap`) touch nothing here | P §1 |
| `ScreenSpaceMapCameraController` + `ScreenSpaceZoomCameraController` (1.144) | Apache-2.0 | **adapt — spike behind a flag** | Row 18; must re-establish the 600 m–1,250 km band in the repo | P §1, rec 1; S row 19 |
| van Wijk & Nuij path (implement from the equations; parameters cited via MapLibre JSDoc "1.42 … van Wijk (2003)", `speed` 1.2; d3 "sqrt(2)") | n/a (an algorithm; no code copied) | **adopt** | Row 13. Do not vendor MapLibre/deck.gl/d3 code — ~60 lines of owned math | S row 1, B1 |
| GDAL (`gdal raster tile`, 3.11+) | "In general GDAL/OGR is licensed under an MIT style license" | **adopt** (build side only) | Phase 3 | P §8 |
| `protomaps/PMTiles` + `go-pmtiles` | "The below license (BSD-3) applies to the reference implementations … The PMTiles specification itself is public domain, or CC0" | **adopt for vector layers only** | Not for raster imagery (§2 contradictions; I §5.3) | P §8, §10; I §5.3 |
| rclone (R2 upload) | — (config recipe quoted from Cloudflare docs) | adopt | Phase 3 upload | I §4.3 |
| NASA GIBS Blue Marble (EPSG:3857, z ≤ 8) | `<ows:Fees>none</ows:Fees>`; NASA "should be acknowledged as the source" | **adopt** | Row 10 interim; baked into the mosaic | P §9; I §1.5 |
| Sentinel Hub S2 120 m mosaic / CDSE 10 m quarterly / NAIP / USGS | quoted in §4 | **adopt as mosaic inputs** | Phase 3 | I §1 |
| `isaaccorley/geospatial-skills` (`gdal`, `pmtiles-pipeline`) | "Apache License / Version 2.0" | **adapt, do not install** | If Phase 3 proceeds, read the two SKILL.md files and vendor what applies into `.claude/skills/` with LICENSE, the way `vibesec` was vendored | P §11 |
| `hongfaqiu/cesium-wind-layer` | "MIT License / Copyright (c) 2024 Hongfa Qiu"; peer `cesium ^1.127.0` | **adapt-gated** | Only if an AR wind/IVT layer enters the roadmap, and then as an at-rest, user-invoked layer; note its Vite duplicate-`@cesium/engine` alias requirement | P §5 |
| `dengxiaoning/cesium_dev_kit` | "MIT License / Copyright (c) 2022-present dengxiaoning" | **read only** | Reference for a fog/vignette fragment shader if row 20 is ever built; Vue/Three coupling, untyped — never a dependency | P §3 |
| Mapbox storytelling template | "BSD 3-Clause License" | **pattern only** | Chapters-as-data for Event Zero replay (drop `rotateAnimation`, pin `pitch`/`bearing`) — a feature decision after this plan | S rows 7-8, B4 |
| `cambecc/earth` (MIT), `mapbox/webgl-wind` (ISC), `RaymanNg/3D-Wind-Field` (MIT) | as quoted | **context only** | Particle technique references; the 3D-Wind-Field path uses private `DrawCommand` | S §2.2; P §5 |
| `reearth/resium` 1.25.0 | "The MIT License (MIT) / Copyright (c) 2022 Re:Earth contributors" | **skip** | Puts Cesium objects in React props — the opposite of `CINEMATIC_ARCHITECTURE.md` §2–4; would fight `TransitionPlate`/`CameraController` for the loop | P §7 |
| `WaterSeeding/CesiumFogEffect`, `JSeungHO/my-wave-engine`, OmarShehata camera gist | **no licence** | **skip** | Unlicensed | P §3, §4, §2 |
| `zouyaoji/vue-cesium`, `TerriaJS/terriajs`, `maplibre/martin`, `onthegomap/planetiler`, `mapbox/mbutil` (archived) | MIT / Apache-2.0 / Apache-2.0 / Apache-2.0 / BSD-3 | **skip** | Wrong framework, not separable, no server needed, vector-only, archived | P §2, §8 |
| `developmentseed/titiler` | "MIT License / Copyright (c) 2019 Development Seed" | **skip for the basemap** | A dynamic tiler in the render loop is a new failure surface (ADR-0021's reasoning); maybe later for QPE/QPF rasters from the API | P §8 |
| EOX Sentinel-2 cloudless | "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License" | **skip / never in a derivative** | ShareAlike infects the whole mosaic | I §1.4 |
| Esri World Imagery, MapTiler Cloud, Planet Basemaps | Esri MLA; MapTiler "Suitable for testing, personal or non-commercial use"; Planet "You will need your Planet API key and an active plan" | **skip** | Terms forbid export/warm; keys in the render loop | P §9; I §1.6 |
| `anthropics/skills`, `vercel-labs/skills` / skills.sh, marketplace "GDAL"/"GeoMaster" pages | Apache-2.0 (most) / MIT / UNVERIFIED | **skip** | No Cesium, GDAL, map-design or cartography skill exists in any catalog queried; the Cesium knowledge lives in `docs/research/cesium-*.md` | P §11 |

---

## 6. Do not chase — verified absent in 1.144, or breaks doctrine

Each line names the lens that closed it, so nobody re-researches it.

**Cesium cannot do it (verified absent):**
1. Per-tile imagery fade-in — no fade code anywhere in the globe surface pipeline; upstream
   #8581 / #8140 open with zero activity since 2020, no fork [C §1c; P §6]. `TransitionPlate` is
   the answer.
2. A custom shader on the globe other than `Globe.material` (`CustomShader` is Models/3D Tiles
   only) [R §9.2].
3. Per-layer post-processing — a stage always grades the whole frame; `selected` filters picked
   primitives, not imagery [R §9.3].
4. The water effect — gated on a terrain water mask the R2 pyramid does not have
   (`extensions: ["octvertexnormals"]` only) [R §5; P §1 corrected; X §4] — and rejected even
   with one (fabricated water surface, animates Puget Sound while rivers are sub-pixel).
5. Shadows beyond 5 km without degrading every cascade (`maximumDistance` is a hard clip, not a
   fade) [R §5 corrected].
6. A built-in spline camera "player", a camera position-bounds API, a feathered
   `cartographicLimitRectangle`, per-tile tone normalisation in the client, suppressing the tilt
   gesture's heading twist, SSCC zoom limits on programmatic moves, a public tween for
   `ImageryLayer.alpha` [C not-possible 1–11; R §9].
7. Fog or atmosphere with a stable look across bands — both are functions of camera height by
   design [R §9.7].
8. Rendering at physical pixels without the tile-load cost — SSE is measured in drawing-buffer
   pixels; requests rose 128–149 → 237–417 at the retina proxy [X §0].
9. A `ScreenSpaceZoomCameraController` that honours the 1,250 km ceiling by default — it ships
   with `maximumZoomDistance = 100000` [src:…/ScreenSpaceZoomCameraController.js:151].
10. `PerspectiveFrustum.xOffset`/`yOffset` under an orthographic frustum — `OrthographicFrustum`
    has no such fields (grep today); compose by shifting the destination.

**Breaks doctrine (nadir, no gratuitous motion, visual truth):**
11. Bloom (hazes snowfields and urban concrete, not rivers; 4 passes), depth of field (fabricated
    focal plane on a flat map; 3 passes + depth), ambient occlusion (nothing to occlude at nadir;
    2 passes), HDR + tonemapping (remaps the USGS product's colours), silhouette/edge, lens flare,
    night vision [R §1-2; X §5; F M18].
12. Procedural cumulus clouds, particle rain/snow, animated `Water` material on polygons —
    invented weather or an inundation claim under VISUAL_TRUTH_DOCTRINE [R §6; S rows 15, 21-22].
13. A clock-driven `SunLight`, "Time of Day" as a moving light, terrain exaggeration without
    shading [R §4; F rule 8, M17]. December floods would go black.
14. Camera tours (KML or spline), orbit/spiral rigs, Flyover-style photorealism, Columbus View
    on its own [S rows 18, 21; R §8].
15. Fog as a depth cue or a second vignette (rule 14 forbids stacking) [F M16].
16. Elastic/back/bounce easings; any ease that continues after the hand moves [F rule 6, 13].
17. Expanding the boot warm past z9 as a continuity fix — it warms voids [I §6].
18. EOX or Esri pixels in the mosaic; PMTiles for raster; a dynamic tiler in the render loop
    [I §1.4, §1.6, §5.3; P §8].
19. Timing anything on the SwiftShader e2e config, or shipping COOP/COEP to production for the
    memory API without its own decision [X §1, §9.8].
20. Bumping to Cesium 1.145.0 for cinematic reasons — nothing in it touches imagery, post-
    processing or the globe [P §1].

---

## 7. Open decisions for the owner (the plan branches on these)

- **Q1. Is "no angles" permanent?** If yes, SCENE2D + WebMercator (row 21) is the honest end
  state and the 3D-only investments — hillshade, exaggeration, slope materials, tilt plumbing —
  should not be made; the orthographic frustum (row 12) is the reversible first step either way.
  If a local-band oblique may ever return, stay in 3D + ortho and keep row 19 as an A/B [R §11].
- **Q2. Which machine defines BALANCED?** Intel UHD 630 is the measured anchor; Apple-silicon
  integrated GPUs are unmeasured and likelier among stakeholders [X §8.6]. One harness run on an
  M-class laptop settles the HIGH/BALANCED boundary.
- **Q3. Hillshade taste.** A fixed NW light deepens valleys the way every topographic sheet does,
  but it double-shades NAIP's own noon sun. Blind A/B on two basins, after Q1.
- **Q4. The mosaic ADR and the tiles hostname.** ADR-0022 in the ADR-0021 mould; `tiles.
  papsukkal.com` (or move terrain under it too, which also retires the r2.dev hazard).
- **Q5. Grade ownership** once the tints are off: stay in per-layer uniforms (three layers, three
  grades) or one custom stage (row 20). Recommendation: per-layer until proven insufficient.

---

## 8. What this plan deliberately leaves out

Event Zero chapters-as-data, the scroll-scrubbed replay page, the forecast half of the timeline,
streamline river flow and any particle field are *feature* decisions the renderer plan does not
pre-empt; the mechanisms they need (rows 7, 13, 22; S rows 7-8, 11-12, 24) are recorded so they
cost nothing to pick up later. The glass system is untouched: the liquid-glass verdict stands
(reproduce with primitives, ≈ 150 lines), and rule 12 (no transform on a glass ancestor) is the
only interaction with this plan [G §(c); F rule 12].

---

## 9. Verification notes for this synthesis

**Re-grepped today in the installed package** (the API facts this plan's rows stand on):
`switchToOrthographicFrustum` [src:Scene/Camera.js:4008] and `_adjustOrthographicFrustum`
[src:Scene/Camera.js:1249,1300,1335,1791,2048,2491]; `requestRenderMode ?? false` and
`maximumRenderTimeChange ?? 0.0` [src:Scene/Scene.js:681,698]; `useBrowserRecommendedResolution`
default and the `pixelRatio` formula [src:Widget/CesiumWidget.js:92-95,276-277,291-292], mirrored
on the Viewer [`@cesium/widgets/Source/Viewer/Viewer.js:530,1436-1438`];
`showGroundAtmosphere = Ellipsoid.WGS84.equals(ellipsoid)` and `dynamicAtmosphereLighting = true`
[src:Scene/Globe.js:203,185]; `Fog.enabled/renderable/density/maxHeight` [src:Scene/Fog.js:25,36,49,62,128];
`requestVertexNormals` default false, extension appended only when requested, and the
`hasVertexNormals` getter [src:Core/CesiumTerrainProvider.js:46,62,494,932,1065]; the
`ENABLE_VERTEX_LIGHTING` / `ENABLE_DAYNIGHT_SHADING` gate [src:Scene/GlobeSurfaceShaderSet.js:321-329]
and `hasVertexNormals` read from the terrain provider [src:Scene/GlobeSurfaceTileProvider.js:2394-2396];
`_msaaSamples = options.msaaSamples ?? 4` [src:Scene/Scene.js:251]; the `PostProcessStage`
`colorTexture`/`depthTexture` contract [src:Scene/PostProcessStage.js:30]; `ScreenSpaceMapCameraController`
and `ScreenSpaceZoomCameraController` classes [dts:32907, 33139] with the zoom controller's
`minimumZoomDistance = 0.0` / `maximumZoomDistance = 100000.0`
[src:Scene/Controllers/ScreenSpaceZoomCameraController.js:144,151]; `PerspectiveFrustum.xOffset/yOffset`
[src:Core/PerspectiveFrustum.js:22-23,82-91] and their **absence** from `OrthographicFrustum.js` /
`OrthographicOffCenterFrustum.js` (zero hits — new finding, row 4 and §6.10); `maximumHeight`
passthrough in `flyToBoundingSphere` [src:Scene/Camera.js:3494,3756]; `this.light = new SunLight()`
[src:Scene/Scene.js:766]; `showWaterEffect = true` and `oceanNormalMapUrl` [src:Scene/Globe.js:303,501];
`Sun.show = true` / `Moon.show ?? true` [src:Scene/Sun.js:49; src:Scene/Moon.js:46];
`export { Texture }` [`cesium/Source/Cesium.js:434`] and `Texture.defaultColor = Color.WHITE`
[src:Renderer/Texture.js:1135]; versions `cesium 1.144.0` / `@cesium/engine 26.2.0`.

**Re-read in the repo:** `SceneController.ts` (Viewer options :97-106, lighting :109, cache :116,
domain :130-135, plate :162-163, motion SSE :176-188, `upgradeTerrain` :391-401),
`CameraController.ts` (framings :16-18, `flyToBasin` :92-98, `fly` :127-177,
`narrowestHalfAngle` :185-189), `envelope.ts` (:31,34,36,40,45-51), `BasemapProvider.ts`
(:63,93-94,98-128), `domain-warmer.ts` (:8,19-20,45-50,78,93-97), `TransitionPlate.ts`
(:18-22), `bands.ts` (:18), `flight-math.ts`, `motion.ts` (:14,24-28), `edge-vignette.ts`
(:15-16), `CameraEnvelope.ts`, `store.ts` (:65,97,113), `App.tsx` (:40-44),
`WeatherFieldLayer.ts` (:171-175), `functions/[[path]].js` (:93-121), `tests/perf/` (exists:
Python harness), `docs/PERFORMANCE.md` §3, `docs/CINEMATIC_ARCHITECTURE.md` §11, and the ADR
list (next number is 0022).

**Refuted claims treated as false throughout** (from the six lens verification passes):
(1) the live pyramid's normals reach the shader today — no, `requestVertexNormals` is never set;
(2) Timelapse "keeps 16 videos in sync" as a technique — it was the problem, not the solution;
(3) the ocean effect is gated by `enableLighting` — it is gated by a water mask; (4) `Texture` is
not exported — it is, only untyped; (5) the boot warm is ~260 tiles — it is 434; (6) omitting
`tileDiscardPolicy` saves a decode step — it does not; (7) z14/z16 mean tile sizes 22.6/21.8 KB —
unreproduced, ±40 %; (8) Oregon 2022 is 3,712 quads statewide — that is the in-domain count,
statewide is 7,471; (9) AO is three passes — two; (10) the headless shell runs rAF at 33/50 ms —
16.66 ms p50; (11) the SwiftShader path is "30 Hz" — software, not 30 Hz. None changes a verdict
here; (1) adds the `requestVertexNormals` prerequisite to row 19 and (5) fixes a comment.

**Not verified in this synthesis** (inherited as the lenses marked them): any wall-time figure
derived from the 19.3 tiles/s USGS rate (the service varied 2× within a day); the WebP ≈ 0.7 ×
JPEG ratio; timer-query availability in shipping Chrome/Safari/Firefox; Apple-silicon numbers;
CDSE S3 prerequisites and mosaic sizes; the WEBP quality option name for `gdal raster tile`.

---

## 10. Owner decisions (2026-09-01)

The five open questions in §7 were answered by the owner on 2026-09-01. Each answer is
recorded verbatim in intent, followed by what it changes in the plan above. Where an answer
reframes the question (Q2), the reframing is the decision.

| Q | Owner's answer | What changes in this plan |
|---|---|---|
| **Q1** Is "no angles" permanent? | **3D stays. No SCENE2D.** "No angles" is temporary — until the ground can carry angles (terrain + hillshade + the mosaic must read as one ground before a local-band oblique returns). | Rows 12 (orthographic frustum in 3D) and 19 (fixed-sun hillshade) **stay**; row 12 remains the reversible first step. **Row 21 (SCENE2D + WebMercator migration) is withdrawn** — its line in §2 and §6.10's "compose by shifting the destination" note remain as the record of why. The 3D-only investments §7 Q1 warned against (relief, hillshade, exaggeration, slope materials, tilt plumbing) are no longer at risk of being thrown away; tilt plumbing itself stays out of scope until the ground carries angles. |
| **Q2** Which machine defines BALANCED? | Reframed: **the product exposes exactly two experiences — "Essential" (stripped) and "Cinematic" (full).** Internal tiers map onto them. | Row 6's four internal tiers (ULTRA / HIGH / BALANCED / LOW) stay as the renderer's vocabulary but **surface as two product modes**: Essential (LOW + BALANCED budgets: MSAA 1, `resolutionScale` 0.5, no hillshade, no native DPR) and Cinematic (HIGH + ULTRA: native DPR, MSAA 4, hillshade, full effects). **Auto-detect picks the default** (the 90-idle-frame probe after `onGroundComposed` plus `FrameRateMonitor.fromScene` downgrade, step 1.4); **Settings overrides** it with a two-way switch, not a four-way one. The Intel UHD 630 measurement remains the anchor for what Essential must hold (E1.4); the M-class harness run still settles where auto-detect draws the line, but it no longer blocks shipping. |
| **Q3** Hillshade taste | **The most-cinematic option, on Cinematic.** | Row 19 (fixed-sun hillshade: `requestVertexNormals: true`, `DirectionalLight` from the NW, low `lambertDiffuseMultiplier`, optional `verticalExaggeration ≈ 1.3`) **ships on the Cinematic mode after the harness A/B** (step 3.6, E3.6 — the blind pick on Skagit and Puyallup and the BALANCED GPU p95 ≤ 14 ms budget still gate it). Essential never lights the terrain. The "double-shades NAIP's noon sun" concern is now a grading question for the mosaic build (per-source histogram match, ADR-0022 invariant 3), not a reason to withhold relief. |
| **Q4** The mosaic ADR and the tiles hostname | **Approved**, both. | **Phase 3 is approved as written.** [ADR-0022](../adr/ADR-0022-imagery-is-a-self-built-pnw-mosaic-in-r2.md) records the decision (option C now, z0–z14; option D next, NAIP z15–z16), the licence table, the build invariants, serving (plain z/x/y objects on `tiles.papsukkal.com`, immutable headers, not PMTiles), cost, and E3.1–E3.5 as its Accepted gate. Terrain moves onto the same host (step 3.1), retiring the r2.dev hazard. Row 14 is now the plan's largest approved item; row 10 (GIBS Blue Marble live layer) stays the interim only while the build runs. |
| **Q5** Grade ownership | **Grades stay per-layer uniforms.** | **Row 20 (custom `PostProcessStage` film grade / GPU vignette) is withdrawn.** The three layers keep their three grades (`ImageryLayer` saturation/brightness/contrast/gamma uniforms); once the mosaic ships, the imagery grade is baked at build time and the client uniform becomes identity (ADR-0022 invariant 2), so the per-layer surface shrinks rather than grows. The existing edge-vignette layer stays the only vignette (F rule 14). `cesium_dev_kit` moves from "read only, for row 20" to "not needed". |

Net effect on the phases: Phase 1 step 1.4 gains the two-mode product surface (store field,
`SettingsMenu` two-way switch, auto-detect default) on top of the four internal tiers; Phase 2 is
unchanged; Phase 3 proceeds in parallel from day one as §3 already allowed, with 3.6 (hillshade)
now a Cinematic-mode deliverable rather than a conditional A/B. Rows 20 and 21 leave the ranked
table's live set; nothing else moves.

## 11. Phase 1 landed (2026-09-01)

Everything in the §9 Phase 1 step table shipped in one commit, verified on the owner's Mac with
the new real-GPU harness path (full Chromium channel, ANGLE-Metal on the Intel UHD 630 — the
BALANCED anchor of X §6). Measured, not inferred:

| Step | What landed | Evidence |
|---|---|---|
| 1.1 | `tests/perf/perf-harness.mjs` + `npm run perf:owner`; refuses SwiftShader (exit 2) | probe path: Intel on `--gpu=low-power`, AMD 5300M on `high-performance`, refusal on the headless shell — all three printed |
| 1.2 | Hygiene block: ground atmosphere off, fog not renderable (culling kept), sun/moon hidden, water effect off | A/B at the orbital home frame, 2880×1800: **60 of 5,184,000 pixels differ by more than 8/255** (0.001 %, mean 0.000) — the two tints contributed nothing visible at nadir over the domain, so `IMAGERY_GRADE` is unchanged by measurement, not by omission |
| 1.3 | `scene.requestRenderMode = true` (`VITE_REQUEST_RENDER=off` restores the loop), `maximumRenderTimeChange = ∞`; every controller mutation point and the basin fade (a rAF pump in `BasinsLayer`) request their own frames | idle 3 s at the composed home frame: **0 frames rendered**; a 10-tick wheel gesture: 80 frames, band ORBITAL → RIVER, tiles settled |
| 1.4 | `scene/quality.ts` (pure) + `scene/render-quality.ts` (Cesium-facing): four tiers, two experiences, probe, gesture-window monitor; store `experience` / `detectedTier` / `qualityTier`; Settings two-way switch with an automatic reset | probe on the Intel: GPU p50 7.8 ms, CPU 1.8 ms, frame-delta p95 18.2 ms → BALANCED (the doc's anchor). Switch to Cinematic: backing store 1440×900 → **2880×1800**, MSAA 1 → 4, cache 400 → 600; back to Essential restores; choice persists across reload (e2e `quality.spec.ts`) |
| 1.5 | Native DPR on HIGH/ULTRA only | the 2880×1800 above; Essential stays at CSS pixels |
| 1.6 | Arrival gate (`panels/arrival-gate.ts`, 400 ms) + weather hold (`app/weather-hold.ts`) | e2e `arrival.spec.ts` (a) panel mounts 410 ms after settle, (b) no weather `setData` between started and settled |
| 1.7 | `maximumHeight` on `flyToBoundingSphere` = Cesium's own default apex clamped to `ZOOM_CEILING_M` | the skeptic caught the builder's swapped axes against `CameraFlightPath.js` (UP first, RIGHT second); fixed, pinned by `flight-apex.test.ts` with Cesium's own numbers (43,301 m / 69,282 m) |
| 1.8 | stale "~260" comments were already 434 in the tree; `Texture.defaultColor` left at Cesium's default — no black rectangle was reproducible after the plate landed | — |

Two notes for whoever runs the harness next. The in-app browser pane is hidden while an agent
works and throttles rAF to a few frames per minute; every renderer conclusion must come from the
headless full-Chromium path (the pane showed a black world and "12 frames in 30 s" that were
entirely its own). And the probe's classification on this machine sits right at the HIGH/BALANCED
boundary by frame arrival (18.2 ms vs the 17 ms cap) while its GPU time (7.8 ms) is HIGH-class;
the discrete AMD path is expected to classify HIGH — the first `perf:owner` run on
`--gpu=high-performance` decides whether the delta cap is too tight for Cinematic by default.

First harness baseline (`npm run perf:owner -- --runs=1 --warmup=0`, 1280×800 @ DPR 1, vite-dev
server so CPU numbers are not the production build's; the app's own probe picked the tier, so the
Intel row ran BALANCED/MSAA 1 and the AMD row whatever it classified; ms, p95 unless noted):

| GPU | boot | idle-home drawn/frames | zoom-in rAF p95 · GPU p50 | pan p95 | zoom-out p95 | basin-flight p95 · GPU p50 | scrub p95 | imagery req/run | heap end |
|---|---|---|---|---|---|---|---|---|---|
| Intel UHD 630 (low-power) | 8.4 s | **1 / 182** | 50.1 · 11.8 | 33.3 | 33.4 | 16.8 · 8.6 | 16.8 | 1,738 | 154 MB |
| AMD 5300M (high-performance) | 7.8 s | **1 / 182** | 33.3 · 3.3 | 16.7 | 16.8 | 16.7 · 2.4 | 16.8 | 1,777 | 141 MB |

Read against X §6: the AMD row passes every HIGH gesture budget except zoom-in's 16.7 ms rAF
(33.3 — inside the BALANCED floor, so a HIGH classification holds and the monitor would not
step it down); the Intel row's zoom-in (50.1) sits exactly at the LOW frame floor and its
GPU p50 (11.8) is BALANCED-class — the probe's BALANCED verdict is the right one. Both rows
show the explicit-rendering dividend directly: one drawn frame in 182 at rest. Single runs, one
machine, dev server: a calibration point, not a gate — the 5-run protocol in X §7 turns it into
one. The artefacts are in `tests/e2e/.results/perf/` (gitignored).

Next: Phase 2 (§9) — stage-composed framing, the orthographic frustum, the van Wijk path,
cut-versus-fly, landing-LOD prefetch, the weather crossfade, the GIBS plate — and Phase 3's
mosaic build under ADR-0022.
