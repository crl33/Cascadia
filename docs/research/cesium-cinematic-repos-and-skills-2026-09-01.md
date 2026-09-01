# Cesium cinematic work — repos, libraries and Claude Code skills: inventory with verified links and quoted licenses

Research date: 2026-09-01. Lens: REPOS. Target: `apps/web` on CesiumJS **1.144.0** (verified:
`apps/web/node_modules/cesium/package.json` `"version": "1.144.0"`, `"license": "Apache-2.0"`;
`@cesium/engine` 26.2.0, `@cesium/widgets` 16.1.1, both `"license": "Apache-2.0"`). Builds on
`cesium-continuity-camera-2026-08-31.md` (imagery/camera API facts — not repeated here) and
`imagery-providers-2026-08-28.md` (USGS/Esri/EOX/NAIP terms — referenced, not repeated).

Doctrine this inventory is filtered through: pure nadir at every band; bounded PNW domain
(`camera/envelope.ts:31` `HARD_DOMAIN = {west:-128, south:44, east:-116.5, north:51.5}`,
`:36` `ZOOM_FLOOR_M = 600`, `:40` `ZOOM_CEILING_M = 1_250_000`); satellite-first public-domain
imagery; a boot-time regional warm (`layers/basemap/domain-warmer.ts`); a snapshot
`TransitionPlate` for post-gesture refinement; and "cinematic = nothing breaks the illusion,
not more animation". Every adopt/adapt/skip verdict below is a verdict against *that*, not
against the library's general quality.

Verification legend
- **[dts:N]** — `apps/web/node_modules/cesium/Source/Cesium.d.ts` line N (public API; identical
  line numbers in `@cesium/engine/index.d.ts` for the symbols cited)
- **[src:File:N]** — `apps/web/node_modules/@cesium/engine/Source/<path>` line N
- **[gh]** — GitHub REST API (`gh api repos/<owner>/<repo>` and `/license`), fetched 2026-09-01;
  stars and `pushed_at` are as returned that day
- **[npm]** — `registry.npmjs.org/-/v1/search`, fetched 2026-09-01
- **[fetch]** — page fetched 2026-09-01, URL given
- **[probe]** — curl from this machine, 2026-09-01
- **UNVERIFIED** — could not be confirmed today; treat as unknown

Star counts are a maturity signal only; licenses are quoted from the repo's LICENSE file (first
lines) or from the package manifest, never assumed from the SPDX badge alone.

---

## 0. Verdicts in one screen

| Need | Verdict | Why |
|---|---|---|
| Camera tour / keyframe library | **skip all external; keep `CameraController`** | No maintained library exists on npm or GitHub (§2); Cesium core `Camera.flyTo` + 1.144's new `Controller` framework cover it |
| Pure-nadir map camera | **adapt Cesium 1.144's own `ScreenSpaceMapCameraController`** (§1) | Ships in the installed version; a pan-only, pick-anchored controller *preserves* whatever orientation the camera has (it never enforces nadir, and it has no zoom — pair it with `ScreenSpaceZoomCameraController`) |
| Post-processing packs | **skip packs; adopt core `PostProcessStage`** for a GPU vignette/grade (§3) | Core has the stage API + FXAA/bloom/AO/tonemap; third-party packs are demo-grade |
| Water / ocean shaders | **skip** (§4) | Satellite-first imagery *is* the water; core `Material.WaterType` exists if ever needed |
| Wind / precipitation fields | **adapt-gated: `cesium-wind-layer` (MIT)** only when an AR-wind layer is on the roadmap (§5) | Best-maintained option, but it is animation — gate behind "at rest, on demand" |
| Per-tile imagery fade (cesium#8581) | **still open, zero activity since 2020** (§6) | `TransitionPlate` remains the right answer |
| React wrapper (resium) | **skip** (§7) | 1.25.0 tracks React 19 + Cesium 1.144, but the repo's controller architecture forbids Cesium types crossing into React |
| Regional tile pyramid | **adopt GDAL `gdal raster tile` (3.11+) / `gdal2tiles` → `pmtiles convert` → R2 + PMTiles Worker** if a self-hosted mirror is ever built (§8, §10) | All BSD/MIT/Apache; the repo already fronts R2 through the same gateway for terrain |
| Extra imagery sources | **adopt NASA GIBS Blue Marble (EPSG:3857, z≤8, CORS `*`) as the coarse base plate** (§9) | Public domain, keyless, uniform tone — exactly the "coarse base plate" role |
| Claude Code skills | **nothing worth installing**; read `isaaccorley/geospatial-skills` `gdal` skill as reference (§11) | No Cesium/map-design skill exists anywhere queried; repo policy is to vendor, not install |

---

## 1. What the installed Cesium 1.144 already gives (verified locally — the baseline every repo below is measured against)

| Surface | Verified | What it gives us | Verdict |
|---|---|---|---|
| `PostProcessStage` constructor `{ fragmentShader, uniforms?, textureScale?, sampleMode?, clearColor?, scissorRectangle?, name? }` | [dts:42912-42924]; shader contract "The default `sampler2D` uniforms are `colorTexture` and `depthTexture` … a `vec2` varying named `v_textureCoordinates`" [src:Scene/PostProcessStage.js:30] | A custom full-frame fragment stage: the natural home for a **GPU domain vignette + grade** (replaces the canvas-drawn `SingleTileImageryProvider` vignette recipe from the 08-31 doc, with zero extra tile requests). Runs on the WebGL canvas only — DOM glass is untouched | **adopt** |
| `PostProcessStageLibrary.createBlurStage/createDepthOfFieldStage/createEdgeDetectionStage/createSilhouetteStage/createBlackAndWhiteStage/createBrightnessStage/createNightVisionStage` (+ `is*Supported`) | [dts:43300+; functions at offsets 14, 33, 72, 97, 123, 131, 136 within the namespace] | Built-in composites; none is cinematic for a nadir map except possibly brightness | skip (grade lives in `ImageryLayer.brightness/contrast/…`, already used by `graded()`) |
| `scene.postProcessStages` accessors `fxaa`, `ambientOcclusion`, `bloom`, `tonemapper`, `exposure`, `add()`, `remove()` | [dts:44180]; collection members at offsets 13, 38, 65, 76, 82, 88, 94 inside `PostProcessStageCollection` | FXAA is the only one that serves continuity (edge shimmer during pan). Bloom/AO are 3D-tileset tools | adopt FXAA check; skip bloom/AO |
| `scene.highDynamicRange`, `scene.msaaSamples` | [dts:44406, 44418] | MSAA reduces aliasing on the imagery/terrain edge under motion | adapt (measure cost on the slow-runner budget) |
| `Material.WaterType` fabric — uniforms `baseWaterColor, blendColor, specularMap, normalMap, frequency, animationSpeed, amplitude, specularIntensity, fadeFactor` | [dts:39067]; [src:Scene/Material.js:1669-1684] | Core animated water for polygons/primitives | skip (see §4) |
| `Globe.showWaterEffect`, `Globe.oceanNormalMapUrl` | [dts:34837, 34919] | The globe's own ocean specular. ~~Only visible with `enableLighting`~~ **Correction (verification 2026-09-01):** it is gated by a terrain **water mask**, not by lighting — `showReflectiveOcean = hasWaterMask && tileProvider.showWaterEffect` [src:Scene/GlobeSurfaceTileProvider.js:2389-2390], shader guard `#if defined(HAS_WATER_MASK) && defined(SHOW_REFLECTIVE_OCEAN)` [src:Shaders/GlobeFS.glsl:52,396]; the `enableLighting` defines are independent [src:Scene/GlobeSurfaceShaderSet.js:303-329]. The repo's R2 terrain `layer.json` declares `extensions: ["octvertexnormals"]` only (no `watermask`, probed 2026-09-01), so the effect can never render here regardless of `enableLighting` (`SceneController.ts:109` sets that `false` anyway) | skip |
| `ParticleSystem` constructor (emitter, bursts, image, lifetimes, …) | [dts:41766-41800] | CPU billboard particles — rain/snow demos use it | skip (doctrine: no more animation) |
| `Fog` — `enabled`, `density` (default `0.0006`), `heightScalar` (`0.001`), `maxHeight`, `visualDensityScalar`, `screenSpaceErrorFactor` | [dts:34345+]; defaults [src:Scene/Fog.js:25,49,55] | Distance fog is a horizon effect; at nadir there is no horizon | skip |
| `Atmosphere` / `SkyAtmosphere` / `Globe.showGroundAtmosphere` | [dts:26486, 43998, 34782] | Already disabled at `SceneController.ts:134-135` (skybox + sky atmosphere off, `backgroundColor` = canvas dark at `:133`) | keep off |
| **`ScreenSpaceMapCameraController`** (+ `ControllerHost`, `Viewer.addController`) — "Added a minimal set of alternative camera controllers … `ScreenSpaceMapCameraController` … Added a composable `Controller` framework" — **new in 1.144** | CHANGES.md `## 1.144 - 2026-08-01` [gh: CesiumGS/cesium CHANGES.md lines 50-51, PR #13604]; [dts:32907] class, [dts:32659] `ControllerHost`, options `dragInputs`, `pickWorldPosition`, "The speed in meters per pixel at which the camera pans"; widgets `Viewer.addController(controller: Controller)` [`@cesium/widgets/index.d.ts:2497`]; exported from `cesium/Source/Cesium.js:1021` | A **pan-only map controller that anchors panning to a picked world position** — the doc example disables the legacy controller first: `viewer.scene.screenSpaceCameraController.enableInputs = false; viewer.addController(new Cesium.ScreenSpaceMapCameraController())`. ~~This is the nadir doctrine implemented upstream~~ **Precision (verification 2026-09-01):** its only option is `dragInputs` [dts:32880-32886]; it pans by `camera.move()` along the camera's own right/up axes [src:Scene/Controllers/ScreenSpaceMapCameraController.js:271-279], so it *preserves* the current orientation (nadir stays nadir) but does not *enforce* it, and it has **no zoom at all** — zoom is a separate `ScreenSpaceZoomCameraController({ dragInputs?, scrollInputs? })` [dts:33117-33140] whose example also sets `enableCollisionDetection = false`. CHANGES scopes the whole set "for an asset inspection use case" [gh CHANGES.md:50]. No tilt gesture exists to cap, no heading twist to spring back from — but the zoom floor/ceiling (`ZOOM_FLOOR_M`/`ZOOM_CEILING_M`) would have to be enforced by the repo, not the controller | **adapt — highest-value single finding.** Spike it (map + zoom controllers together) against `CameraController` + `CameraEnvelope`: keep the repo's flights, replace the gesture layer. Risk: 1.144-new API, no community mileage yet; the zoom controller's bounds behaviour is unread |
| `Texture.defaultColor` — "to avoid white flashes when a new Material is constructed" (1.144, PR #13597) | CHANGES.md 1.144 line 55; exists at [src:Renderer/Texture.js:1135] `Texture.defaultColor = Color.WHITE`. ~~Not exported from `Cesium.js`~~ **Correction (verification 2026-09-01):** `Texture` **is** exported — `cesium/Source/Cesium.js:434` `export { Texture } from '@cesium/engine'` and `@cesium/engine/index.d.ts:34`; what is missing is a *type declaration* in `Cesium.d.ts` (no `class Texture`, zero hits for `defaultColor`), so `Cesium.Texture` is reachable at runtime but untyped | Would let placeholder textures default to the canvas dark instead of white — settable as `(Cesium as any).Texture.defaultColor = …` with no deep import | adapt (cheap, one line; type it locally; only affects `Material` placeholder textures, not imagery tiles) |
| Cesium **1.145.0** — CHANGES header `## 1.145 - 2026-09-02`, npm shows `cesium 1.145.0` dated 2026-09-01 [npm] | [gh CHANGES.md line 3]; [npm] | Additions are ClippingPolygons, vector-tile draping, `Scene.snap`; **nothing touching imagery fade, post-processing or the globe pipeline** | no reason to bump this week; when bumping, note the `ClippingPolygons` positions-frozen breaking change (irrelevant to this app) |

---

## 2. Camera tour / path / keyframe libraries

Search record: GitHub REST `search/repositories` for `cesium camera path`, `cesium camera tour`,
`cesium flythrough`, `cesium keyframe`, `cesium animation camera` (sorted by stars) returned only
0-star personal projects or nothing [gh]; npm search `cesium camera`, `cesium tour`, `cesium fly
path` returned no library (only `cesium`, `@cesium/*`, `vite-plugin-cesium`, `vue-cesium`,
`@macrostrat/cesium-martini`) [npm]; the web search surfaced only Cesium's own tutorial, forum
threads, and a 2018 gist.

| Name | URL | License (quoted) | Maturity | What it gives us | Verdict |
|---|---|---|---|---|---|
| Cesium core `Camera.flyTo` — options `complete`, `cancel`, `maximumHeight`, `pitchAdjustHeight`, `flyOverLongitude(+Weight)`, `easingFunction` | https://cesium.com/learn/cesiumjs/ref-doc/Camera.html | Apache-2.0 (package manifest) | in the installed 1.144 [dts:29084-29110] | Everything a two-keyframe flight needs; the repo's `CameraController` already drives it with minimum-jerk easing and `flyToBoundingSphere` | **keep** |
| Cesium 1.144 `Controller` framework (see §1) | https://github.com/CesiumGS/cesium/pull/13604 | Apache-2.0 | shipped 2026-08-01 | Composable gesture controllers; not a tour library, but the gesture half of a "cinematic camera" | **adapt** (spike) |
| OmarShehata "CesiumJS Experimental Camera Tracking Class" (gist) | https://gist.github.com/OmarShehata/eeaa2fae407739f27a5cc27cdb6679ab | **no license stated** [fetch] | gist, 2018-07-31 | Follow-cam with exponential smoothing via `lookAtTransform`; game-oriented | skip (unlicensed, oblique-only use case) |
| `zouyaoji/vue-cesium` | https://github.com/zouyaoji/vue-cesium | MIT [gh] | 1,911 stars, pushed 2026-07-30 [gh]; npm 3.2.12 (2025-11-28) | Vue 3 components; irrelevant framework | skip |
| `TerriaJS/terriajs` (has "stories"/scene tours) | https://github.com/TerriaJS/terriajs | Apache-2.0 [gh] | 1,362 stars, pushed 2026-09-01 [gh]; pins its own `terriajs-cesium` 26.0.0 fork [npm] | A whole data-platform framework; its story mechanism is not separable | skip (read `terriajs` story code for ideas only) |

Conclusion: there is no library to adopt. The repo's own `CameraController` (+ the 08-31 doc's
`CameraEnvelope` spring-back) is already ahead of anything published.

---

## 3. Post-processing / shader packs

| Name | URL | License (quoted) | Maturity | What it gives us | Verdict |
|---|---|---|---|---|---|
| Cesium core `PostProcessStage` + library (§1) | https://cesium.com/learn/cesiumjs/ref-doc/PostProcessStage.html | Apache-2.0 | in 1.144 | Custom full-frame fragment stage; FXAA; tonemapper/exposure | **adopt** for a GPU vignette/grade stage |
| `dengxiaoning/cesium_dev_kit` | https://github.com/dengxiaoning/cesium_dev_kit | "MIT License / Copyright (c) 2022-present dengxiaoning" [gh license] | 259 stars, pushed 2026-08-10 [gh] | Grab-bag: "rain, snow, fog", materials/shaders, post-processing, camera roaming, analysis tools; Vue 3 + Three.js coupling; README notes "Extended classes not using type detection (TS)" and "No exception catching and handling" [fetch] | **adapt as reading material only** — copy the fog/vignette fragment shader pattern into our own `PostProcessStage`; never take the dependency (Vue/Three coupling, untyped, weather effects are animation) |
| `WaterSeeding/CesiumFogEffect` / `WaterSeeding/CesiumPostProcess` | https://github.com/WaterSeeding/CesiumFogEffect | **NONE** (no license file) [gh] | 7 / 1 stars, pushed 2023-08 [gh] | Demo of a fog `PostProcessStage` | skip (unlicensed) |
| Cesium issue #5808 "Post process framework roadmap" | https://github.com/CesiumGS/cesium/issues/5808 | — | open; last comment 2024-04-08 (a Godot link) [gh] | Confirms no upstream roadmap movement; the stage API is what there is | context |

---

## 4. Water / wave / ocean shaders

| Name | URL | License (quoted) | Maturity | What it gives us | Verdict |
|---|---|---|---|---|---|
| Core `Material.WaterType` (§1) | https://cesium.com/learn/cesiumjs/ref-doc/Material.html | Apache-2.0 | in 1.144 [src:Scene/Material.js:1669-1684] | Animated normal-map water for polygons (e.g. inundation extents) | skip now; the only sanctioned future use is a **static** (`animationSpeed: 0`) inundation fill |
| CesiumGS wiki "Ocean Details" | https://github.com/CesiumGS/cesium/wiki/Ocean-Details | wiki text | design notes only [fetch] | Explains the Fresnel/specular-map design behind the globe ocean; no code to adopt | context |
| `JSeungHO/my-wave-engine` (Gerstner ocean w/ Cesium adapter) | https://github.com/JSeungHO/my-wave-engine | **none** [gh] | 0 stars, pushed 2026-06-01 [gh] | Gerstner waves | skip (unlicensed, 0 stars) |
| Cesium Community "water effects" threads | https://community.cesium.com/t/water-effects-and-animation/7725 | forum | — | Fabric snippets | context only |

Doctrine check: at nadir, over public-domain orthoimagery, the water is already in the pixels.
A shader ocean would *replace* real imagery with a synthetic one — the definition of breaking
the illusion.

---

## 5. Cloud / atmosphere / weather-field renderers (wind particles, precipitation rasters)

| Name | URL | License (quoted) | Maturity | What it gives us | Verdict |
|---|---|---|---|---|---|
| `hongfaqiu/cesium-wind-layer` | https://github.com/hongfaqiu/cesium-wind-layer | "MIT License / Copyright (c) 2024 Hongfa Qiu" [gh license] | 123 stars, pushed 2026-04-26; npm `cesium-wind-layer` 0.10.1 (2026-04-26); `peerDependencies.cesium: "^1.127.0"`, devDep `cesium ^1.136.0` [gh package.json] | GPU particle advection from `u/v` `Float32Array` grids + bounds; "terrain occlusion support, particles are blocked by terrain"; options `particlesTextureSize`, `speedFactor`, `lineWidth`, `colors`, `flipY`, `useViewerBounds`; README warns Vite needs an alias to avoid duplicate `@cesium/engine` instances [fetch] | **adapt-gated**: the best-maintained Cesium wind layer, compatible with 1.144 by peer range. Only if an AR moisture-flux/wind layer enters the roadmap, and only as an at-rest, user-invoked layer (it is motion by definition) |
| `QJvic/cesium-wind` | https://github.com/QJvic/cesium-wind | "MIT License / Copyright (c) 2020 QJvic" [gh license] | 103 stars, pushed 2026-04-28; npm 1.0.5 [npm] | Thin Cesium binding over `sakitam-fdd/wind-layer` (MIT: "The MIT License (MIT) / Copyright (c) 2017 sakitam-fdd" [gh license], 708 stars); GFS-JSON input; 2D canvas particles | skip in favour of the GPU one above |
| `RaymanNg/3D-Wind-Field` | https://github.com/RaymanNg/3D-Wind-Field | "MIT License / Copyright (c) 2019 RaymanNg" [gh license] | 497 stars, pushed 2025-06-18 [gh]; not an npm package | The original GPU-particle reference (NetCDF v3 input, custom primitives); an app, not a library | skip (read for technique) |
| `lby0101/cesium-wind-layer-3d` | https://github.com/lby0101/cesium-wind-layer-3d | MIT [gh] | 6 stars, pushed 2026-08-21; npm 0.1.2 [npm] | WebGL2 3D-texture wind volume | skip (too young) |
| `CesiumChina/cesium-wind-layer` | https://github.com/CesiumChina/cesium-wind-layer | MIT [gh] | 1 star, pushed 2021-07-02 | dead fork | skip |
| `hongfaqiu/cesium-particle` | https://github.com/hongfaqiu/cesium-particle | — | README: "no longer maintained" (per search summary; UNVERIFIED first-hand) | superseded by cesium-wind-layer | skip |
| `cwdaniel/RadrView` | https://github.com/cwdaniel/RadrView | MIT [gh] | 11 stars, pushed 2026-06-19 [gh] | Self-hosted radar app (NEXRAD L2, MRMS composites), not a Cesium layer | skip; the MRMS *data* path is already in `precipitation-observations.json` |
| `immiao/cesium-weather` | https://github.com/immiao/cesium-weather | MIT [gh] | 9 stars, pushed 2018-01-09 | abandoned | skip |
| `mapbox/webgl-wind` | https://github.com/mapbox/webgl-wind | ISC [gh] | 1,105 stars, pushed 2026-08-06 | The canonical GPU particle technique (not Cesium) | context |
| Precipitation rasters (MRMS/QPE) as imagery | core `WebMapTileServiceImageryProvider` [dts:47397], `TimeDynamicImagery` [dts:45914], `WebMapServiceImageryProvider` | Apache-2.0 | in 1.144 | A precipitation raster is just another `ImageryLayer` with `alpha` — whole-layer crossfade per the 08-31 doc §1b; no third-party code needed | **adopt core** when the QPE/QPF layer ships |

---

## 6. Imagery smoothing / per-tile fade — upstream status (cesium#8581 et al.)

| Item | URL | State (2026-09-01) | Evidence |
|---|---|---|---|
| #8581 "Make time dynamic imagery smoother" | https://github.com/CesiumGS/cesium/issues/8581 | **open, 0 comments, `updated_at` 2020-01-30** | [gh] |
| #8140 "Alpha blending for imagery layers LODs" — "It would be nice to have imagery layers fade in/out instead of popping in when loading levels of detail." | https://github.com/CesiumGS/cesium/issues/8140 | **open, 0 comments, `updated_at` 2020-10-05**; labels `category - terrain and imagery`, `type - enhancement`; no linked PR | [gh], [fetch] |
| #526 "Terrain and imagery roadmap" | https://github.com/CesiumGS/cesium/issues/526 | **closed 2026-08-13** by ggetz: "some of this has become stale … closing in favor of discrete issues such as #11786, #3877, and #6531" — those are EGM96/MSL lookup, "different projections", and "Support many imagery layers with transformations and terrain". **None is a fade.** | [gh comments] |
| Any PR titled with imagery fade | `search/issues q=repo:CesiumGS/cesium imagery fade in:title` and `is:pr fade tiles` | **zero matching PRs**; the only hits are unrelated closed PRs (HDR, sky atmosphere, particle systems, fog) | [gh] |
| Forks implementing per-tile fade | GitHub search `cesium imagery fade` | **no repositories** | [gh] |

Conclusion: six years, no movement, no fork. The repo's `TransitionPlate` (snapshot-and-crossfade
above the renderer, `scene/TransitionPlate.ts:1-16`) remains the only per-refinement fade that
exists for globe imagery, and it is the correct layer to own it.

---

## 7. React wrappers

| Name | URL | License (quoted) | Maturity | What it gives us | Verdict |
|---|---|---|---|---|---|
| `reearth/resium` | https://github.com/reearth/resium | "The MIT License (MIT) / Copyright (c) 2022 Re:Earth contributors" [gh license] | 884 stars, pushed 2026-09-01; latest release **v1.25.0 (2026-08-07)**; package.json `peerDependencies`: `cesium: "1.x"`, `react: ">=18.2.0"`; devDeps `cesium 1.144.0`, `react 19.2.8` [gh package.json] | Declarative `<Viewer>`, `<ImageryLayer>`, `<Camera>` etc. — puts Cesium objects into React props | **skip.** `docs/CINEMATIC_ARCHITECTURE.md` §2-4 (plain-TS controllers own the scene; React never holds Cesium types) is the opposite architecture. Resium would also fight `TransitionPlate`/`CameraController` for the render loop |
| `Vizzuality/react-cesium` | https://github.com/Vizzuality/react-cesium | UNVERIFIED (not fetched) | UNVERIFIED | older wrapper | skip |

---

## 8. Regional tile-pyramid tooling (for a self-hosted PNW mirror, if ever)

| Name | URL | License (quoted) | Maturity | What it gives us | Verdict |
|---|---|---|---|---|---|
| GDAL — `gdal2tiles.py`; **`gdal raster tile`** ("Added in version 3.11") | https://gdal.org/en/latest/programs/gdal_raster_tile.html | LICENSE.TXT: "In general GDAL/OGR is licensed under an MIT style license with the …" (multi-license file; `spdx: NOASSERTION` at repo level) [gh license] | 6,041 stars, pushed 2026-09-01 [gh]; doc page confirms "Added in version 3.11." / "3.11.1." [fetch] | Cut an XYZ/WebMercator pyramid from any raster (NAIP COGs) with resampling control; the new `gdal raster tile` is the modern, parallel replacement for gdal2tiles | **adopt** (build-side only, never in the browser) |
| `cogeotiff/rio-cogeo` | https://github.com/cogeotiff/rio-cogeo | "BSD 3-Clause License / Copyright (c) 2021, cogeotiff" [gh license] | 394 stars, pushed 2026-06-23 [gh] | COG creation/validation (overviews, web-optimized profile) | adopt if we ever re-encode NAIP |
| `cogeotiff/rio-tiler` | https://github.com/cogeotiff/rio-tiler | "BSD 3-Clause License / Copyright (c) 2021, cogeotiff" [gh license] | 592 stars, pushed 2026-09-01 [gh] | Read tiles from COGs dynamically (Python) | adopt only inside a batch pyramid job |
| `developmentseed/titiler` — "A modern dynamic tile server built on top of FastAPI and Rasterio/GDAL." | https://github.com/developmentseed/titiler | "MIT License / Copyright (c) 2019 Development Seed" [gh license] | 1,155 stars, pushed 2026-09-01 [gh]; COG/STAC/MosaicJSON/Xarray [fetch] | A **dynamic** raster tile API (Lambda/ECS/K8s/Docker) | **skip for the basemap** — doctrine wants pre-cut, cache-warmable, immutable tiles; a dynamic tiler in the render loop is a new failure surface (same reasoning as ADR-0021 rejecting keyed terrain). Maybe later for QPE/forecast rasters served from the API |
| `protomaps/PMTiles` | https://github.com/protomaps/PMTiles | LICENSE: "The below license (BSD-3) applies to the reference implementations in this repository. The PMTiles specification itself is public domain, or CC0 where applicable." [gh license] | 3,027 stars, pushed 2026-08-19 [gh] | Single-file tile archive on R2; JS client + serverless workers (`serverless/cloudflare`) | **adopt** as the R2 packaging for any self-hosted raster pyramid |
| `protomaps/go-pmtiles` (`pmtiles convert`, `pmtiles extract`) | https://github.com/protomaps/go-pmtiles | BSD-3-Clause [gh] | 591 stars, pushed 2026-07-22 [gh] | mbtiles→pmtiles, **bbox extract** (cut a PNW window out of any archive) | adopt |
| `stadiamaps/pmtiles-rs` | https://github.com/stadiamaps/pmtiles-rs | Apache-2.0 [gh] | 107 stars, pushed 2026-08-15 | Rust reader | skip (no Rust in stack) |
| `maplibre/martin` | https://github.com/maplibre/martin | Apache-2.0 [gh] | 3,888 stars, pushed 2026-09-01 | PostGIS/MBTiles/PMTiles tile server | skip (Pages gateway + R2 already serve static tiles; no server needed) |
| `onthegomap/planetiler` | https://github.com/onthegomap/planetiler | "Apache License / Version 2.0" [gh license] | 2,162 stars, pushed 2026-08-18 | OSM **vector** tiles at planet scale | skip (satellite-first; vectors come from the API's PostGIS) |
| `felt/tippecanoe` | https://github.com/felt/tippecanoe | BSD-2-Clause: "Copyright (c) 2022, Protomaps LLC / Copyright (c) 2014, Mapbox Inc." [gh license] | 1,590 stars, pushed 2026-08-31 | GeoJSON→vector tiles | adapt only if basin/river geometry ever moves to vector tiles |
| `mapbox/mbutil` | https://github.com/mapbox/mbutil | BSD-3-Clause [gh] | 826 stars, **archived**, pushed 2025-10-07 [gh] | mbtiles↔directory | skip (archived; `pmtiles convert` covers it) |

Order-of-magnitude arithmetic for a full-domain mirror (not a measurement): WebMercator
`HARD_DOMAIN` at z16 spans ≈2,093 columns × ≈2,036 rows ≈ 4.3 M tiles; z≤16 total ≈ 5.7 M; at the
18.6–35.7 KB/tile the USGS probes returned (imagery-providers doc §1: 18,589 / 21,334 / 35,665 B)
that is a **~100–200 GB** object store (5,689,166 tiles × 18–36 KB = 102–205 GB; re-derived
2026-09-01), roughly half of it ocean/Canada that could be excluded by a land mask. The
existing warm (`domain-warmer.ts` `bootTiles()`, z5–z9) is the cheap end of the same idea —
~~≈ 260 tiles~~ **434 tiles** (4 + 9 + 25 + 90 + 306, computed by calling `domainTiles()` on
2026-09-01; the "~260" in the file's own comments at `domain-warmer.ts:8` and `:78` is stale),
≈ 8–16 MB. Decide by measuring, not by this estimate.

---

## 9. Public imagery mosaics (only what the 08-28 doc did not already settle)

| Source | URL | License / terms (quoted) | Verified today | What it gives us | Verdict |
|---|---|---|---|---|---|
| USGS `USGSImageryOnly` | see `imagery-providers-2026-08-28.md` §1/§1a | "Map services and data downloaded from The National Map are free and in the public domain." | 08-28 | current workhorse, z≤16 | keep |
| **NASA GIBS Blue Marble** — `BlueMarble_ShadedRelief_Bathymetry`, `BlueMarble_NextGeneration`, `BlueMarble_ShadedRelief` on **EPSG:3857** | capabilities https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/1.0.0/WMTSCapabilities.xml ; template `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/BlueMarble_ShadedRelief_Bathymetry/default/{TileMatrixSet}/{TileMatrix}/{TileRow}/{TileCol}.jpeg` | Capabilities: `<ows:Fees>none</ows:Fees>`, `<ows:AccessConstraints>none</ows:AccessConstraints>` [probe]; NASA: "NASA content – images … generally are not subject to copyright in the United States" and "NASA should be acknowledged as the source of the material." [fetch nasa.gov brand center]; GIBS requested credit: "We acknowledge the use of imagery provided by services from NASA's Global Imagery Browse Services (GIBS), part of NASA's Earth Science Data and Information System (ESDIS)." [fetch gibs-api-docs] | `TileMatrixSet` **`GoogleMapsCompatible_Level8`**, `image/jpeg` [probe capabilities]; tile probes z5 and z8 over the PNW → `200 image/jpeg` 19,025 B / 13,531 B; headers `access-control-allow-origin: *`, `cache-control: public, max-age=259200` [probe] | A cloud-free, uniform-tone, keyless, public-domain **coarse base plate** for z0–8 under the USGS layer (`ImageryLayer` at index 0, USGS above with its own `rectangle`); VIIRS true-colour daily layers exist at `GoogleMapsCompatible_Level9` for a "today's sky" variant | **adopt** for the base plate; wire with `WebMapTileServiceImageryProvider` or `UrlTemplateImageryProvider` (`{z}/{y}/{x}` order per template), `maximumLevel: 8` |
| NAIP on AWS Registry of Open Data | https://registry.opendata.aws/naip/ | "Public Domain with Attribution"; buckets `naip-analytic`, `naip-source`, `naip-visualization` — all "(Requester Pays)"; "overall update cycle of every two to three years for each state"; "30 centimeters to 100 centimeters" [fetch] | today | Source rasters for a self-cut z10–16(+) pyramid (§8); no XYZ endpoint | adopt **only** as input to §8 |
| EOX Sentinel-2 cloudless | `imagery-providers-2026-08-28.md` §4/§4a | "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License" (2018–2025 layers) | 08-28 | better ocean/mountain look to ~z13 | skip unless NC sign-off or purchased licence |
| Esri World Imagery | `imagery-providers-2026-08-28.md` §3/§3a | "This work is licensed under the Esri Master License Agreement." / "This layer is not intended to be used to export tiles for offline." ; E300 fn.10: "Programmatic use of session tokens (e.g., exporting volumes of basemap tiles) is not permitted." | 08-28 (reconfirmed by 2026 search results pointing to the same item terms) | z19 over WA | skip keyless; **never** as prefetch/warm input (the warm is exactly the programmatic bulk fetch the terms forbid) |
| MapTiler Cloud Satellite | https://www.maptiler.com/cloud/pricing/ | Free: "5k/month" sessions, "100k/month" API requests, "Suitable for testing, personal or non-commercial use.", "MapTiler logo on the map"; Flex "$30/month (USD)" [fetch] | today | Keyed satellite tiles | skip (key in render loop; ADR-0021's reasoning) |
| Planet Basemaps | https://docs.planet.com/develop/apis/basemaps/ | "You will need your Planet API key and an active plan with Mosaics access to view and download these products." [fetch]; pricing page is a JS shell — **pricing UNVERIFIED** | today | Monthly mosaics, XYZ/WMTS behind key + plan | skip |

---

## 10. Cloudflare R2 / Workers tile serving

| Name | URL | License (quoted) | Maturity | What it gives us | Verdict |
|---|---|---|---|---|---|
| **This repo's gateway** — `functions/[[path]].js` | repo | — | in production since ADR-0021 | `/terrain/*` proxied to an R2 public bucket (`TERRAIN_ORIGIN` default `https://pub-…r2.dev`, `'off'` disables) with `Cache-Control: public, max-age=31536000, immutable` for `.terrain` and a stated `Content-Encoding: gzip` because "R2 keeps the uploaded Content-Type but DROPS Content-Encoding" (`functions/[[path]].js:93-119`; ADR-0021 "Measurements") | **the pattern to extend** — an `/imagery/v1/{z}/{x}/{y}` branch is a copy of the terrain branch |
| Protomaps `serverless/cloudflare` worker | https://github.com/protomaps/PMTiles/tree/main/serverless/cloudflare ; docs https://docs.protomaps.com/deploy/cloudflare | BSD-3 (PMTiles LICENSE above) | part of the 3,027-star repo | Bindings `BUCKET` (R2), `PMTILES_PATH` (default `{name}.pmtiles`), `ALLOWED_ORIGINS`, `CACHE_CONTROL` (default "public, max-age=86400"); maps `/TILESET/{z}/{x}/{y}.<mvt \| png>` to **range requests** into one PMTiles archive; docs verify caching via `Cf-Cache-Status: HIT` and note cache is zone-wide [fetch]. Raster shown as `png` on the docs page; **JPEG/WebP/AVIF confirmed from the worker source** (verification 2026-09-01): `serverless/cloudflare/src/index.ts:174-179` maps `mvt/pbf/png/jpg/webp/avif` extensions and sets `Content-Type: image/jpeg` / `image/webp` at `:206-209`; the R2 read is `bucket.get(key, { range: { offset, length } })` at `:67` | **adopt** if a self-hosted pyramid is built: one archive object instead of millions of R2 objects; folds into the existing gateway as a route |
| `kotx/render`, `DownUnderCTF/r2-public-worker`, `DavidJKTofan/r2-cache-workers-check` | https://github.com/kotx/render etc. | UNVERIFIED (not fetched) | UNVERIFIED | Generic R2 proxy-with-Cache-API workers | skip (the repo already has one) |
| Cloudflare docs skill (installed, `~/.claude/skills/cloudflare`, `wrangler`, `workers-best-practices`) | local | — | present | Retrieval-first guidance for the Worker/R2 work | use when touching the gateway |

---

## 11. Claude Code skills and plugins

**Installed today** (`ls`): project `.claude/skills/` = `icm-architect`, `react-quality`,
`vibesec`; user `~/.claude/skills/` = `agents-sdk`, `cloudflare`, `cloudflare-email-service`,
`cloudflare-one`, `cloudflare-one-migrations`, `durable-objects`, `frontend-design`,
`sandbox-sdk`, `scroll-scrubbed-visual-sequence`, `turnstile-spin`, `ui-ux-pro-max`, `web-perf`,
`workers-best-practices`, `wrangler`. **None is geospatial, GDAL, Cesium or cartographic.**
`SearchSkills(["geospatial","GDAL","cesium","map design","cartography","tiles"])` and
`SearchPlugins([...])` against the claude.ai catalog both returned **zero results** (2026-09-01).

| Name | URL | License (quoted) | Maturity | What it gives us | Verdict |
|---|---|---|---|---|---|
| `anthropics/skills` | https://github.com/anthropics/skills | README: "Many skills in this repo are open source (Apache 2.0)"; docx/pdf/pptx/xlsx "are source-available, not open source" [fetch]; repo-level SPDX NONE [gh] | 173,000 stars, pushed 2026-09-01 [gh] | Creative/design, dev, enterprise, document skills; **no maps, geospatial, GDAL, Cesium or WebGL skill** [fetch] | skip for this work (already available as `anthropic-skills:*` in the session) |
| `isaaccorley/geospatial-skills` | https://github.com/isaaccorley/geospatial-skills | "Apache License / Version 2.0" [gh license]; README: aggregates upstream skills "under Apache-2.0 and MIT licenses" [fetch] | 71 stars, pushed 2026-08-07 [gh]; install `npx skills add isaaccorley/geospatial-skills[/<skill>]` | Skills: `gdal` (raster/vector CLI workflows), `pmtiles-pipeline` ("Raster predictions to global PMTiles archive via tippecanoe"), `geospatial-frontend` ("MapLibre globe + DuckDB-WASM" — not Cesium), `geoparquet-validation`, `geozarr`, `search-stac`, `overture-data`, `detect-objects`, … [fetch] | **adapt, do not install**: if §8 is ever executed, read `gdal` and `pmtiles-pipeline` SKILL.md files and vendor what applies into `.claude/skills/` the way `vibesec` was vendored (with LICENSE). Nothing here helps the renderer |
| `vercel-labs/skills` (`npx skills`) + skills.sh | https://github.com/vercel-labs/skills ; https://skills.sh/ | "MIT License / Copyright (c) 2026 Vercel, Inc." [gh license] | 30,189 stars, pushed 2026-08-18 [gh]; skills.sh: "The Open Agent Skills Ecosystem", "Made with care by Vercel. Skills are open source on GitHub" — leaderboard shows **no gdal/geospatial/cesium/map/cartography listing** [fetch] | The installer + directory; community-ranked by installs, no vetting statement found | skip (no relevant skill to install through it) |
| mcpmarket.com / claudemarketplaces.com "GDAL", "GeoMaster", "Geospatial Visualization" skill pages | (aggregator pages seen via search) | UNVERIFIED — licenses and provenance not fetched; the pages are re-listings of GitHub skills | UNVERIFIED | Aggregators, not sources | skip; go to the upstream repo when one is named |
| `rohitg00/awesome-claude-code-toolkit` `geospatial-engineer.md` agent | https://github.com/rohitg00/awesome-claude-code-toolkit | UNVERIFIED (not fetched) | UNVERIFIED | A persona prompt, not tooling | skip |

Policy fit: the repo vendors skills with their LICENSE (`.claude/skills/vibesec/LICENSE`,
`icm-architect/LICENSE`) and CLAUDE.md routes React work through `react-quality`. Nothing found
today earns a fourth vendored skill for the cinematic renderer work; the Cesium knowledge lives
in `docs/research/cesium-*.md` and the code, which is where the doctrine says it belongs.

---

## 12. Recommendations (ranked by leverage per risk)

1. **Spike `ScreenSpaceMapCameraController` (Cesium 1.144, `[dts:32907]`)** behind a flag: disable
   `screenSpaceCameraController.enableInputs`, `viewer.addController(new
   ScreenSpaceMapCameraController({ dragInputs }))` **plus `new ScreenSpaceZoomCameraController()`
   [dts:33117]** (the map controller has no zoom of its own — verified 2026-09-01), keep
   `CameraController` flights and the `CameraEnvelope` spring-back. If pan feels right at every
   band, the whole tilt-cap / heading-twist machinery from the 08-31 doc becomes unnecessary.
   Exit test: no gesture can leave nadir; wheel zoom still honours `ZOOM_FLOOR_M`/`ZOOM_CEILING_M`
   (the zoom controller's bounds behaviour is unread — expect to clamp it in the repo).
2. **Move the domain vignette to a core `PostProcessStage`** (fragment shader over `colorTexture`
   with a `HARD_DOMAIN`-derived screen rectangle uniform updated in `preRender`). Zero tile
   traffic, square-edged, resolution-independent, and it composes with `TransitionPlate`
   because the plate copies the *post-processed* canvas. Check `scene.postProcessStages.fxaa`
   on while you are there.
3. **Add NASA GIBS `BlueMarble_ShadedRelief_Bathymetry` (EPSG:3857, `GoogleMapsCompatible_Level8`)
   as imagery layer 0** with the USGS layer above it; add both credit strings. Public domain,
   keyless, CORS `*`, 3-day cache — the coarse base plate the doctrine already names, now
   cloud-free and tonally uniform. Warm it in the same boot stage (z0–8 over the domain is a
   few dozen tiles).
4. **Leave #8581/#8140 alone** — no upstream movement in six years; do not budget for it.
5. **Do not adopt resium, cesium_dev_kit, vue-cesium, or any post-processing/water pack.**
   Read `cesium_dev_kit`'s fog shader as a reference for (2) and nothing more.
6. **Wind particles (`cesium-wind-layer`, MIT) only when an AR-wind layer is a roadmap item**,
   and then as an on-demand, at-rest layer; note its Vite duplicate-`@cesium/engine` alias
   requirement before installing.
7. **If a self-hosted PNW pyramid is ever decided** (measure first — §8's ~100 GB-class
   estimate): NAIP COGs (Requester Pays) → `gdal raster tile` → `pmtiles convert` →
   `pmtiles extract --bbox` → one archive in the existing R2 bucket → Protomaps Cloudflare
   worker logic folded into `functions/[[path]].js` next to the terrain branch. All BSD/MIT/
   Apache/public-domain; no keys in the render loop. Record it as an ADR before building.
8. **Skills: install nothing.** If (7) happens, vendor the relevant parts of
   `isaaccorley/geospatial-skills` (`gdal`, `pmtiles-pipeline`) with their Apache-2.0 LICENSE.

## 13. Not verified today

- Planet pricing/terms (JS shell); MapTiler satellite resolution/coverage; ~~whether the
  Protomaps Cloudflare worker serves JPEG/WebP~~ (resolved: yes, from source — §10);
  `hongfaqiu/cesium-particle` "no longer maintained" note first-hand; `Vizzuality/react-cesium`,
  `kotx/render`, `r2-public-worker` licenses and stars; `ScreenSpaceZoomCameraController`
  bounds/inertia semantics (the map controller itself was read in full — pan only, §1).
- The ~100–200 GB pyramid figure is arithmetic on tile counts × probed tile sizes, not a build.

---

## Verification (adversarial pass, 2026-09-01)

Method: every Cesium-API claim re-grepped against `apps/web/node_modules/cesium/Source/Cesium.d.ts`
and `apps/web/node_modules/@cesium/engine/Source` (1.144.0 / engine 26.2.0); every external claim
re-fetched (`gh api`, `curl`, page fetch) the same day; every number re-derived. ✓ = supported as
written; ✗ = wrong or materially imprecise (the body above was corrected inline, strike-through
kept).

| # | Claim | Verdict | Note |
|---|---|---|---|
| 1 | 1.144 `Controller` framework, pan-only pick-anchored `ScreenSpaceMapCameraController`, `enableInputs = false` + `viewer.addController(...)` example | ✓ (with precision) | All symbols and lines confirmed: class `[dts:32907]`, `ControllerHost` `[dts:32659]`, example `[dts:32895-32898]`, `Viewer.addController` `@cesium/widgets/index.d.ts:2497` (+ `Viewer.js:2013`), export `Cesium.js:1021`, CHANGES.md lines 50-51 / PR #13604. Pan-only is exact: sole option `dragInputs`, source has no zoom/tilt path. But "pure-nadir doctrine implemented upstream" overstates it — it preserves orientation via `camera.move()` rather than enforcing nadir, ships no zoom (that is `ScreenSpaceZoomCameraController`), and CHANGES scopes the set "for an asset inspection use case" |
| 2 | `PostProcessStage` options, `colorTexture`/`depthTexture`/`v_textureCoordinates`, `scene.postProcessStages` with `fxaa`/`ambientOcclusion`/`bloom`/`tonemapper`/`exposure` | ✓ | Constructor `[dts:42912-42924]` lists exactly those (+ `forcePowerOfTwo`, `pixelFormat`, `pixelDatatype`, `name`); uniform contract `PostProcessStage.js:30`; accessor `[dts:44180]`; members `[dts:43055, 43080, 43107, 43118, 43124]` |
| 3 | `Material.WaterType` uniforms; `Globe.showWaterEffect`/`oceanNormalMapUrl` "only matter with `enableLighting`" | ✗ | Uniforms exact (`Material.js:1669-1682`; `[dts:39067]`); Globe props at `[dts:34837, 34919]` ✓. The gating is **wrong**: the reflective ocean needs a terrain **water mask** (`GlobeSurfaceTileProvider.js:2389-2390`; `GlobeFS.glsl:52,396`), and lighting defines are independent (`GlobeSurfaceShaderSet.js:303-329`). Moot for a different reason: R2 `terrain/v1/layer.json` has `extensions: ["octvertexnormals"]` only — no `watermask`. Corrected in §1 |
| 4 | 1.145.0 published (CHANGES `## 1.145 - 2026-09-02`, npm 2026-09-01), additions only ClippingPolygons / vector draping / `Scene.snap`; `Texture.defaultColor` exists but `Texture` not exported | ✗ (half) | Release facts ✓: CHANGES line 3, npm `cesium@1.145.0` 2026-09-01T19:56Z; additions/fixes touch nothing in imagery fade, post-processing or globe ✓. `Texture.defaultColor = Color.WHITE` at `Texture.js:1135` ✓. **`Texture` is exported** — `Cesium.js:434`, `@cesium/engine/index.d.ts:34`; only the `Cesium.d.ts` typing is absent. Corrected in §1 (verdict changed skip → adapt) |
| 5 | cesium#8581 / #8140 open, 0 comments, `updated_at` 2020-01-30 / 2020-10-05; #526 closed 2026-08-13 for #11786/#3877/#6531; zero fade PRs/forks | ✓ | All reproduced exactly via `gh api`; the three successor issues are "Add support for EGM96 / EGM2008 / MSL lookup", "different projections", "Support many imagery layers with transformations and terrain" — none a fade; both searches return `total_count: 0` |
| 6 | No maintained camera tour/keyframe library; `Camera.flyTo` options | ✓ | Five GitHub searches → 0-star personal repos or nothing; three npm searches → only `cesium`, `@cesium/*`, `vite-plugin-cesium`, `vue-cesium`, `@macrostrat/cesium-martini`, `terriajs-cesium`, `mars3d-cesium`; `flyTo` options `[dts:29084-29110]` include `complete`, `cancel`, `maximumHeight`, `pitchAdjustHeight`, `flyOverLongitude(+Weight)`, `easingFunction` |
| 7 | `hongfaqiu/cesium-wind-layer` MIT (2024 Hongfa Qiu), 123 stars, pushed 2026-04-26, npm 0.10.1, peer `cesium ^1.127.0`, GPU u/v `Float32Array`, terrain occlusion, Vite alias warning | ✓ | LICENSE first lines match verbatim; repo/package.json/npm all reproduced; README quotes the Vite alias fix and `u/v: { array: Float32Array }` |
| 8 | resium 1.25.0 (2026-08-07), MIT "Copyright (c) 2022 Re:Earth contributors", 884 stars, pushed 2026-09-01, peer `cesium 1.x` / `react >=18.2.0`, devDeps cesium 1.144.0 / react 19.2.8; contrary to CINEMATIC_ARCHITECTURE §2-4 | ✓ | All reproduced; `docs/CINEMATIC_ARCHITECTURE.md` §2 at line 54, §3 at 99, §4 at 140, §5 at 223 |
| 9 | NASA GIBS Blue Marble ×3 on EPSG:3857 `GoogleMapsCompatible_Level8` `image/jpeg`, Fees/AccessConstraints `none`, z5/z8 probes 200 jpeg 19,025 / 13,531 B, CORS `*`, `max-age=259200`; NASA copyright quotes | ✓ | Capabilities parsed per layer: all three `['image/jpeg']` / `['GoogleMapsCompatible_Level8']`; `<ows:Fees>none</ows:Fees>` and `<ows:AccessConstraints>none</ows:AccessConstraints>` present; z5 `5/11/5` → 200, 19,025 B (exact); z8 re-probe (`8/89/42`) → 200, 13,943 B — the doc's 13,531 B tile address was not recorded, so that byte count is unreproduced but the same order; headers exact; NASA and GIBS quotes confirmed on the cited pages |
| 10 | PMTiles LICENSE text, 3,027 stars, pushed 2026-08-19; go-pmtiles BSD-3 591; worker bindings/defaults and `/TILESET/{z}/{x}/{y}.<mvt|png>`; JPEG/WebP unverified | ✓ (upgraded) | LICENSE quoted verbatim; stars/dates exact; docs page lists `BUCKET`, `PMTILES_PATH` (`{name}.pmtiles`), `ALLOWED_ORIGINS`, `CACHE_CONTROL` (`public, max-age=86400`) and `/NAME/0/0/0.<mvt \| png>`. Range requests and `jpg/webp/avif` are not on the docs page but **are** in `serverless/cloudflare/src/index.ts:67, 174-179, 206-209` — §10/§13 updated |
| 11 | `functions/[[path]].js:93-119` terrain proxy, `TERRAIN_ORIGIN` default `pub-*.r2.dev`, `'off'`, immutable cache header, stated `Content-Encoding: gzip`; ADR-0021 Measurements | ✓ | Branch spans lines 89-121; every quoted string present; ADR-0021 line 56-58 states the R2 Content-Encoding lesson |
| 12 | Tooling licenses: GDAL "MIT style", `gdal raster tile` 3.11; rio-cogeo/rio-tiler BSD-3 2021 cogeotiff; titiler MIT 2019 Development Seed; planetiler Apache-2.0; tippecanoe BSD-2 (Protomaps 2022 / Mapbox 2014); mbutil archived | ✓ | GDAL LICENSE.TXT line 15: "In general GDAL/OGR is licensed under an MIT style license with the following terms:"; gdal.org page: "Added in version 3.11."; all other LICENSE first lines and `archived: true` for mbutil reproduced |
| 13 | No Cesium/GDAL/map skill installed or in the catalog; anthropics/skills 173,000 stars with quoted license text; skills.sh has no such listing | ✓ | `ls` matches (3 project, 14 user); `SearchSkills`/`SearchPlugins` re-run → `[]`; 173,004 stars; README quotes verbatim; skills.sh renders a 275+ entry leaderboard with no gdal/geospatial/cesium/map/cartography entry |
| 14 | `isaaccorley/geospatial-skills` Apache-2.0, 71 stars, pushed 2026-08-07, `npx skills add …`, skill list, MapLibre not Cesium; vendoring precedent | ✓ | All reproduced; README lists `gdal`, `pmtiles-pipeline`, `geospatial-frontend` (MapLibre globe), `geoparquet-validation`, `geozarr`, `search-stac`, `overture-data` among 24; `.claude/skills/vibesec/LICENSE` exists |
| 15 | z≤16 ≈ 5.7 M tiles (z16 ≈ 2,093 × 2,036 ≈ 4.3 M), ~100 GB-class at 18-36 KB; boot warm z5-z9 ≈ 260 tiles ≈ 10-15 MB | ✗ (partial) | Re-derived with the repo's `domainTiles()` math: z16 = 2,094 × 2,037 = 4,265,478; z≤16 = 5,689,166 — both ✓ to the stated precision. USGS §1 sizes are 18,589 / 21,334 / 35,665 B ✓, giving 102-205 GB — "~100 GB-class" is the floor; corrected to 100-200 GB. **z5-z9 is 434 tiles** (4+9+25+90+306), not ≈260 — the doc repeated a stale comment in `domain-warmer.ts:8`/`:78`. Corrected in §8 |
