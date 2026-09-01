# Cinematic showcase — what others have achieved, and what Cascadia can take at nadir

Research date: 2026-09-01. Lens: SHOWCASE. Question: what specifically makes the best
CesiumJS and comparable-engine work *feel* cinematic, and which of those techniques survive
Cascadia's doctrine — pure nadir at every band (owner 2026-09-01: "no angles"), bounded PNW
domain (`camera/envelope.ts` HARD_DOMAIN `[-128, 44, -116.5, 51.5]`, zoom 600 m – 1,250 km),
satellite-first public-domain imagery, glass design system, and the working definition that
*cinematic means nothing breaks the illusion (continuity, composition, light, material), not
more animation.*

Builds on, and does not repeat, `docs/research/cesium-continuity-camera-2026-08-31.md`
(tile refinement, crossfades, discard policy, envelope mechanics) and
`docs/research/liquid-glass-decision-2026-08-31.md` (glass material). Read those first.

Verification legend:

- **[dts:NNNNN]** — `apps/web/node_modules/cesium/Source/Cesium.d.ts` line NNNNN (Cesium 1.144.0,
  `license: Apache-2.0` per `node_modules/cesium/package.json:3,6`)
- **[src:path:NN]** — `apps/web/node_modules/@cesium/engine/Source/<path>` line NN
- **[repo:path:NN]** — a file in this repository
- **[web]** — fetched 2026-09-01; quotes are verbatim from the fetched page
- **UNVERIFIED** — could not be fetched or confirmed at research time; treat as a lead, not a fact

Repo doctrine reminder: copied claims are input to investigate. Every row below says how it was
verified. Licenses are quoted, not assumed.

---

## 0. The frame: "cinematic" is the absence of discontinuity

Two outside statements say the thing Cascadia's owner is asking for better than any effect list.

Felt, explaining why they replaced their raster renderer ([web] https://felt.com/blog/maplibre-rendering-engine):
> "With raster maps, zooming necessarily introduces discontinuities whenever items on the map have to resize. Every time there's a sudden size discontinuity, it breaks the illusion that you're looking at the world with a magic eye."

Google Earth Studio, on why a mathematically constant zoom looks wrong ([web] https://earth.google.com/studio/docs/advanced-features/logarithmic-adaptation/):
> "A camera, moving at a constant speed towards Earth, will seem to move much faster the closer it gets to Earth." … "When enabled, logarithmic altitude will move the camera faster out in space and slower as it approaches the Earth." … "The resulting motion compensates for our perceptual deficiencies and appears perfectly linear / constant."

Everything cinematic in the inventory below is one of four things: (1) motion whose *perceived*
velocity is constant, (2) continuity across tile/LOD/frame boundaries, (3) light and material
that are consistent from frame to frame, (4) narrative choreography (a camera that goes where
the story goes, and layers that fade rather than switch). None of the four requires an oblique
camera. Several of the flashiest Cesium demos (clouds, fog, tilt-orbit tours) do — and those are
called out as **not adoptable** rather than bent to fit.

---

## 1. Technique inventory

| # | Technique | Seen where | Evidence | Adoptable at nadir? | How (repo mapping) |
|---|---|---|---|---|---|
| 1 | **Zoom-out-then-in optimal path** (van Wijk & Nuij 2003): pan and zoom solved jointly so perceived velocity is constant; one curvature parameter ρ, one speed parameter V | Mapbox GL / MapLibre `flyTo`, deck.gl `FlyToInterpolator`, d3 `interpolateZoom` | MapLibre camera.ts JSDoc [web]: "1.42 is the average value selected by participants in the user study discussed in van Wijk (2003)"; `speed` default 1.2 "screenfulls" of `curve` per second; deck.gl defaults `curve: 1.414, speed: 1.2` [web]; d3: "The default curvature is sqrt(2)" and the interpolator "exposes a *interpolate*.duration property … based on the path length of the curved trajectory" [web] | **YES — this is the single best fit.** At pure nadir + north-up, the camera state *is* van Wijk's `(cx, cy, w)` triple; the 2-D formulation applies literally, with no pitch/heading to reconcile | Replace the height/position interpolation inside `CameraController.fly` [repo:apps/web/src/camera/CameraController.ts:127-177] with a van Wijk path (see §3.2). Keep `minimumJerk` for the time-warp only |
| 2 | **Logarithmic altitude** — interpolate log(height), not height, on pure zooms | Google Earth Studio "Animating from Space" | [web] quotes above; enabled per project under "Animation > Advanced" | **YES.** Cascadia's most common flight (basin → forecast point, 450 km → 12 km) is a pure nadir zoom — the exact case GES fixes | Same custom path as #1: ρ→0 in van Wijk degenerates to a log-height zoom. Cesium's own path lerps height linearly when no arc applies [src:Scene/CameraFlightPath.js:124] |
| 3 | **Easing with zero velocity *and* acceleration at both ends**, easing "synced across attributes" | Google Earth Studio curve editor | [web] "smooth curves equal smooth motion"; "easing handles to be perfectly horizontal" for smooth stops; keep "easing synced across attributes" | **Already adopted.** `minimumJerk` 10t³−15t⁴+6t⁵ has zero velocity *and* acceleration at both ends [repo:apps/web/src/design-system/motion.ts:24-28] <!-- verification 2026-09-01: was cited as :26-30; the function is at :24-28 -->; Cesium's default would be `QUINTIC_IN_OUT`, or `CUBIC_OUT` when descending from above 11.5 km [src:Scene/CameraFlightPath.js:548-558] | Keep. The GES "synced" rule is the argument for #1: one time-warp over one joint path, never separate curves for position and height |
| 4 | **Interruptible, velocity-continuous retargeting** — when the target changes mid-flight the new path starts from the current velocity, not from rest | Research successor to van Wijk (arXiv 1801.09358) | [web] abstract: "the animations produced by our technique are smooth at the endpoints and when interrupted by a change of target" (contrasted with van Wijk) | **YES, partial.** Cascadia already interrupts on `pointerdown/wheel/keydown` and supersedes flights [repo:CameraController.ts:41-51,128]; a superseding *programmatic* flight today restarts from rest (`cancelFlight` then new tween) | When implementing #1, seed the new path's initial velocity from the current tween's derivative; the paper's hyperbolic-space formulation is the reference, the cheap approximation is a short velocity-blend at the start of the new tween |
| 5 | **Distance-derived duration with a hard cap** (a long flight is not proportionally slower) | Mapbox `maxDuration`, d3 `duration` from path length, Apple MapKit ("custom durations based on distance traveled") | MapLibre: "The animation's maximum duration, measured in milliseconds" [web]; WWDC13 s309 transcript [web] | **Already adopted.** `computeFlightDuration` with `minMs 500 / maxMs 2400 / perDoublingMs 420` [repo:motion.ts:14] | Keep, but derive the distance from the van Wijk path length `S` (in ρ-screenfuls) instead of Euclidean metres once #1 lands — the path length is what the eye travels |
| 6 | **Hold the last good frame, reveal detail as one event** | Google Earth Timelapse (overlapping video-tile pyramid), Google Maps, Felt | Google Research [web]: "sibling tiles overlap with their neighbors to provide a seamless transition between tiles while panning and zooming"; Felt quote in §0 | **Already adopted, in principle.** `TransitionPlate` [repo:apps/web/src/scene/TransitionPlate.ts:1-15] plus uniform-generation SSE during gestures [repo:SceneController.ts:169-207] | No new work; §7 lists two refinements that came out of comparing against Timelapse |
| 7 | **Opacity, never visibility, when a layer enters or leaves a chapter** | Mapbox storytelling template | [web] "you should toggle the layer's opacity (**NOT the visibility**)"; chapters carry `onChapterEnter`/`onChapterExit` opacity lists; `mapAnimation: flyTo | easeTo | jumpTo`; `rotateAnimation` | **YES** (minus `rotateAnimation`, which is a heading spin) | Event Zero replay chapters (`docs/EVENT_ZERO.md`): each chapter = camera keyframe (#1 path) + per-layer target alpha; `ImageryLayer.alpha` [dts:37105] for rasters, entity/primitive alpha for vectors, all eased from `scene.preRender` (prior research §1b) |
| 8 | **Scroll-scrubbed camera ("moviescroller")** — scroll position drives the camera or a pre-rendered sequence, reversible | NYT "How a Massive Bomb Came Together in Beirut's Port" (2020), NYT Sunisa Lee (2021) | data.europa.eu guide [web]: "In a moviescroller the scrolling controls the advancement of a video or the movement of the camera in a 3D-rendered graphic" | **YES for replay, NO for the live instrument.** A scrubbed camera at nadir is a zoom/pan timeline — fine for a narrated Event Zero page; the live map's scroll is zoom | A replay route where scroll progress `p∈[0,1]` maps to (a) the timeline `t` and (b) a piecewise van Wijk camera path evaluated at `p` via `camera.setView` per frame (no flight, no easing — the hand is the easing). The `scroll-scrubbed-visual-sequence` skill exists in this workspace for the DOM half |
| 9 | **Time-dynamic imagery driven by the scene clock** | Cesium Sandcastle "Web Map Tile Service with Time" (NASA GIBS, daily MODIS) | [web] raw gallery source: `TimeIntervalCollection.fromIso8601({ iso8601: "2015-07-30/2017-06-16/P1D", … dataCallback })`, provider options `clock: viewer.clock, times: times`, `clock.multiplier = 7200`; API: `WebMapTileServiceImageryProvider` [dts:47397] with `clock` [dts:47473] and `times` [dts:47479] | **YES, mechanism only.** The mechanism is right; the *driver* must be the store's `time`, never the renderer clock (`CINEMATIC_ARCHITECTURE.md` §4.1 `SceneClock`, §7.4 "no layer reads wall-clock time") | `WeatherFieldLayer` already selects a slice per `setTime`; the Cesium `times` collection is an alternative to hand-swapping `UrlTemplateImageryProvider`s. Either way the frame between two valid times is `cinematic` (§4.2 interpolation rule) |
| 10 | **Per-frame tile pyramids + client-side interpolation between forecast hours** | MapTiler Weather, Windy | MapTiler [web]: "Each time frame of the weather data … is processed as a separate tile pyramid, which allows us to load additional frames into the existing client-side animation as soon as they are available" … "interpolate the data values between the available forecasted time frames to achieve beautiful smooth animations" | **YES for presentation, with the label.** Blending two valid-time rasters is exactly the "client may tween presentation" allowance; it is never a value. Windy's own users flag the cost: interpolated frames read as data | Two-`ImageryLayer` alpha crossfade (prior research §1b) between adjacent valid times; the inspector entry for the blended frame says `cinematic`; never sample a blended pixel into a panel |
| 11 | **Particle continuity across frame changes** — do not reset particles when the field advances | Windy (complaint), MapTiler, nullschool, mapbox/webgl-wind, RaymanNg/3D-Wind-Field | Windy community [web]: "when jumping between frames of the animation (eg between 1am and 4am), all the particles completely disappear, and it takes a second for the new particles to emerge / grow long tails" (no staff reply); MapTiler: particles "smoothly change course as the wind starts blowing from the other direction" | **YES, if a flow field ever ships** (IVT/AR corridor is a class-B field per `CINEMATIC_ARCHITECTURE.md` §1). At nadir a 2-D screen-space particle layer is the natural form — nullschool is nadir-equivalent by construction | Keep particle state across `setTime`; interpolate the *vector field* the particles sample, never teleport them. Implementation options and licenses in §5 |
| 12 | **Trail persistence by fading the previous frame** rather than drawing trails | nullschool (canvas), mapbox/webgl-wind (GPU) | nullschool README [web]: SVG map + one canvas for particles + one canvas for the colour overlay; earth.nullschool.net/about [web] credits D3 + Natural Earth + GFS "updated every three hours"; webgl-wind [web]: "rendering up to 1 million wind particles at 60fps", ISC license | YES (same as #11) | A 2-D canvas/WebGL overlay above the Cesium canvas, positioned by `SceneTransforms.worldToWindowCoordinates` (already used for camera cards [repo:SceneController.ts:457-476]); it must drop instantly on gesture like `TransitionPlate` does |
| 13 | **Consistent solar light as a time cue** ("Time of Day") | Google Earth Studio; Cesium `Globe.enableLighting` + `Scene.light` | GES [web]: "When enabled, Earth Studio renders realistic lighting, stars, and atmospherics based on the position of the sun" and "Time of Day is a powerful cinematic effect"; Cesium: `enableLighting` [dts:34761], `lambertDiffuseMultiplier` [dts:34767], `dynamicAtmosphereLighting` [dts:34772], `Scene.light` "Defaults to a directional light from the Sun" [dts:44206-44208], `SunLight` [dts:45541], `DirectionalLight` [dts:33813] | **MAYBE — A/B only.** At nadir over ortho-imagery the sun already lives in the pixels (NAIP is flown near local noon); adding a second light double-shades relief. Where it *could* pay: the timeline's valid time is often night in a December AR event, and a subtle ambient dim tied to `SceneClock` is honest and cinematic | Repo has `enableLighting = false` [repo:SceneController.ts:109]. Trial: `enableLighting = true`, `lambertDiffuseMultiplier` low, `Scene.light = new DirectionalLight` whose direction is the *real* sun for the store's `time` — as a `layers/cinematic/solar` layer with `truthClass: cinematic`. Screenshot A/B at basin band; reject if terrain reads as "wrong shadows" |
| 14 | **Physically based ground atmosphere with colour grading knobs** | Cesium Sandcastle "Atmosphere" (1.93+) | Cesium blog [web]: 1.93 exposed "Rayleigh and Mie scattering constants, Mie anisotropy, and light intensity … for the Globe and the SkyAtmosphere", single scattering per Nishita 1993; API: `Atmosphere` [dts:26486] with `lightIntensity`, `rayleighCoefficient`, `mieCoefficient`, `mieAnisotropy`, `hueShift`, `saturationShift`, `brightnessShift`; `Globe.showGroundAtmosphere` [dts:34782]; gallery `atmosphere/main.js` exposes all of these [web] | **NO for the sky, MAYBE for the ground haze.** Sky is off by doctrine (repo sets `skyAtmosphere.show = false` [repo:SceneController.ts:135]). Ground atmosphere at 1,150 km nadir would add a bluish distance haze that competes with the filmic imagery grade | Leave off. If ever revisited, `brightnessShift`/`saturationShift` at −0.x can make the haze read as the canvas dark rather than sky blue — but the domain vignette already does this job without a physical model |
| 15 | **Procedural cumulus clouds** | Cesium Sandcastle "Clouds" (`CloudCollection`, 1.85+) | `CloudCollection` [dts:32384], `CumulusCloud` [dts:33421]; ref doc [web]: "A cumulus cloud billboard positioned in the 3D scene"; gallery `clouds/main.js` places clouds "in the mountains" and "in front" [web] | **NO.** They are billboards composed to be seen from the side; at nadir they are flat discs. Also a fabricated sky over a hydrologic instrument is the wrong kind of cinematic | — |
| 16 | **Depth-based fog / distance haze** | Cesium `Fog`, Sandcastle "Fog Post Process" | `Fog` [dts:34345] `density`, `visualDensityScalar`, `minimumBrightness`, `screenSpaceErrorFactor`; gallery `fog-post-process/main.js` uses a custom `PostProcessStage` with `colorTexture`/`depthTexture` uniforms blending fog by distance [web]; `PostProcessStage({ fragmentShader, uniforms, textureScale })` [dts:42912-42916] | **NO.** At nadir every pixel is at nearly the same depth; fog becomes a uniform tint | — |
| 17 | **Post-process glow (bloom), DoF, silhouette, lens flare** | Cesium `PostProcessStageLibrary` | `postProcessStages.bloom` [dts:43107], `.ambientOcclusion` [dts:43080], `.fxaa` [dts:43055], `createDepthOfFieldStage` [dts:43332], `createSilhouetteStage` [dts:43396], `createLensFlareStage` [dts:43454]; HDR `Scene.highDynamicRange` [dts:44406] | **Mostly NO; bloom MAYBE-NO.** Whole-frame bloom would bloom the snowpack and NAIP urban whites, not just the river glow. DoF/lens flare are camera fictions | Glow belongs on the primitive (`PolylineGlowMaterialProperty` [dts:24242]), not the frame. `fxaa` stays default. Custom `PostProcessStage` is the escape hatch for a *frame-wide* film grade if the per-layer `ImageryLayer` grade ever proves insufficient — a fragment shader over `colorTexture` only, with `truthClass: cinematic` |
| 18 | **Scene-clock keyframed camera tours** | Cesium `KmlTour` / `KmlTourFlyTo`, Cesium Stories "Capture view" | `KmlTour` [dts:22730], `KmlTourFlyTo` [dts:22800]; Cesium Stories tutorial [web]: "Camera views save only when you click **Capture view**" | **Mechanism NO, idea YES.** KML tours carry heading/tilt semantics. The *idea* — a list of captured views the reader steps through — is #7 | Chapters are data (`{ lon, lat, heightM, t, layers }`), never KML |
| 19 | **Map-style pan with inertial decay** (screen-space, tangent to the ellipsoid) | CesiumJS 1.144 `ScreenSpaceMapCameraController` (new Controller framework) | `CHANGES.md` 1.144 line 11: "Added a minimal set of alternative camera controllers … `HybridScreenSpacePanCameraController`, `ScreenSpaceElevatorCameraController`, `ScreenSpaceMapCameraController` and `ScreenSpaceTiltOrbitCameraController`"; class [dts:32907]; source doc: "A camera controller that allows panning the camera tangential to the ellipsoid in screen space by clicking and dragging" [src:Scene/Controllers/ScreenSpaceMapCameraController.js:20-21] <!-- verification 2026-09-01: was cited as :8-9 (those are imports) -->; `panSpeed = 1.0`, `inertiaEnabled`, `inertialDecay = 6.0`, `damping = exp(-inertialDecay·dt)` [src:…:99-113,201]; `ScreenSpaceZoomCameraController` [dts:33139] — **its own `maximumZoomDistance` defaults to 100,000 m and `minimumZoomDistance` to 0** [src:Scene/Controllers/ScreenSpaceZoomCameraController.js:144,151], so the repo's 1,250 km ceiling must be set on it explicitly; `viewer.addController` [dts:47989]; usage pattern `screenSpaceCameraController.enableInputs = false` then `addController` is the class's own JSDoc example [src:Scene/Controllers/ScreenSpaceMapCameraController.js:25-28]. ~~[web gallery `camera-controllers/main.js`]~~ — verification 2026-09-01: the gallery does **not** construct `ScreenSpaceMapCameraController`; it uses `HybridScreenSpacePanCameraController` + `ScreenSpaceTiltOrbitCameraController` + `ScreenSpaceZoomCameraController` [web] | **YES — and it is the first Cesium controller that matches the doctrine natively.** A nadir map pans in screen space; the stock `ScreenSpaceCameraController` orbits the globe (heading drift, pole handling, the whole reason `constrainedAxis`, `enableTilt=false` and the heading spring-back exist) | Trial in `SceneController`: disable stock inputs, add `ScreenSpaceMapCameraController` + `ScreenSpaceZoomCameraController`; measure whether `CameraEnvelope`'s heading correction becomes dead code. Cesium marks the framework as designed for "asset inspection use cases" [web Cesium Aug-2026 release post] — treat as new API, pin 1.144, keep the stock path behind a flag |
| 20 | **Overlapping sibling video tiles** so no tile edge is ever on screen during motion | Google Earth Timelapse (CMU Time Machine) | [web] quotes in row 6; ~~"keeping up to 16 videos in sync"~~ — verification 2026-09-01: the "16 videos in sync" sentence describes the *problem* with a standard tile pyramid ("it requires a web browser to keep up to 16 videos in sync while interacting with the visualization"); the Time Machine *solution* is whole-screen overlapping tiles, "only show one whole-screen tile at a time" [web] | **Idea only.** Cesium's quadtree cannot overlap tiles | The nadir analog is already the base-plate + preloadSiblings + plate hold. The one transferable idea: **pre-warm one LOD deeper than the landing band** before a flight lands (§7) |
| 21 | **Photorealistic 3-D (Flyover, Gaussian splats, photogrammetry tours)** | Apple Maps Flyover (WWDC 2026 radiance-field upgrade), Cesium 2025 showcases (Berlin/Barcelona/Belém tours), Cesium OSM flood simulators | radiancefields.com [web]: Flyover's 300+ cities to get radiance-field visuals, WWDC 2026; Cesium/Bentley "5 great 3D visualizations" **UNVERIFIED** (page behind a sign-in wall at fetch time); OSM US "Rising Waters" [web]: "a flood simulator using Cesium's 3D OSM tiles and dynamic water modeling", no code link | **NO.** Every one of these is oblique by nature | — |
| 22 | **Time-dynamic water level via CZML interpolated properties** | ISPRS 2018 "Dynamic 3D visualization of floods: case of the Netherlands" (Cesium + CityJSON→glTF + CZML); Cesium CZML time-animation blog | PDF abstract [web, extracted]: "We propose using CZML (Cesium Language) to represent time dynamic properties, water levels in our case"; Cesium blog [web]: availability windows + `clockViewModel.multiplier` | **NO as shown (3-D water surfaces = inundation claims, forbidden by `HYDROLOGY.md` §13); YES as a pattern for *time-keyed presentation*.** | Cascadia's equivalent is already `TemporalLayer.setTime` from store time; CZML would put time on the renderer clock, which §4.1 forbids |
| 23 | **Satellite loop with "Fast / Smooth" playback and fixed loop lengths** | Zoom Earth | [web] settings: "Satellite Loop Duration" 3/6/12/24 h and "Satellite Animation Style" "Fast" / "Smooth" | **YES as UX.** A bounded, user-chosen loop window with two pacing modes is a good model for the −72 h MRMS QPE loop | Playback presets in `TimelineController`: loop length and a `smooth` mode that enables the crossfade (#10); `fast` steps hard |
| 24 | **Streamlines / animated arcs instead of particles for direction+magnitude** | Ventusky (wind streamlines, wave arcs) | [web]: "we utilise current lines that are used to illustrate the movement of particles in liquids"; waves via "animated arcs" | **YES, and cheaper than particles.** At nadir a static streamline texture with a slow phase animation reads as flow with no per-particle state | For rivers: `PolylineDashMaterialProperty` [dts:24060] `dashPattern` phase animated from `preRender` on `flow_visual_intensity` — **caveat (verification 2026-09-01): the property exposes only `color`, `gapColor`, `dashLength`, `dashPattern` [dts:24053-24058]; there is no phase/offset uniform, so "phase" means rotating the 16-bit `dashPattern` per frame (16 discrete steps) or a custom `Material` fabric** — the repo already uses dashes for flood outlines [repo:apps/web/src/layers/flood/FloodHazardLayer.ts:138,172]; the network join already carries `flow_visual_intensity` [repo:layers/network/match.ts:21-33] |

---

## 2. Showcase notes by source

### 2.1 Cesium-native demos (what the engine itself can do)

- **Atmosphere** (Sandcastle `?id=atmosphere`, from 1.93). Verified knobs in 1.144: `Atmosphere`
  [dts:26486-26530] and per-globe `showGroundAtmosphere` / `atmosphereLightIntensity` /
  `atmosphereRayleighCoefficient` [dts:34782-34790]; `DynamicAtmosphereLightingType`
  NONE / SCENE_LIGHT / SUNLIGHT [dts:33892-33905]. The blog's own description of the model:
  single scattering after Nishita 1993 [web]. What makes it read as cinematic is *consistency
  of light with the sky* when the camera tilts toward the horizon — a condition Cascadia never
  enters. Verdict in row 14.
- **Clouds** (`CloudCollection`, 1.85). Row 15. Not adoptable at nadir.
- **Fog post-process** (custom `PostProcessStage`). Row 16. The demo is the cleanest public
  example of a custom frame shader in Cesium — the pattern (not the fog) is the escape hatch
  for a frame-wide grade [dts:42912-42916].
- **Web Map Tile Service with Time** (NASA GIBS). Row 9. Verified against the live gallery
  source: `iso8601: "2015-07-30/2017-06-16/P1D"`, `leadingInterval/trailingInterval: true`,
  `clock.multiplier = 7200`, and the comment "Make the weather layer semi-transparent to see
  the underlying geography" [web]. This is the closest Cesium first-party demo to Cascadia's
  precipitation layer, and it is nadir-agnostic.
- **Camera controllers** (1.144, `?id=camera-controllers`). Row 19. This is new in the exact
  version the repo runs, and it is the first time Cesium has shipped a *map* pan rather than a
  globe orbit. The gallery disables the stock controller with `enableInputs = false` and
  `enableCollisionDetection = false` before adding controllers [web] — but note (verification
  2026-09-01) the gallery's pan controller is `HybridScreenSpacePanCameraController`, not the
  Map controller; the Map controller's own JSDoc example shows the same `enableInputs = false`
  + `addController` pattern [src:Scene/Controllers/ScreenSpaceMapCameraController.js:25-28].
  Note the second flag: the prior research (§2, caveat 1) established that
  `minimumZoomDistance`/`maximumZoomDistance` are ignored when collision detection is off
  (confirmed: [src:Scene/ScreenSpaceCameraController.js:268] and the clamp block at
  [src:…:598-616] is skipped) — so a trial must re-establish the zoom band through the zoom
  controller (`ScreenSpaceZoomCameraController.maximumZoomDistance` defaults to **100 km**
  [src:Scene/Controllers/ScreenSpaceZoomCameraController.js:151]) or `CameraEnvelope`, not
  assume the SSCC clamps still hold.
- **KmlTour / Cesium Stories**. Row 18. Stories' "Capture view" is a curation model, not a
  motion model; the tutorial has no statement about transition timing [web].
- **Cesium's flight physics** — see §3.1; it matters because it is what the repo runs today.

### 2.2 Cesium-ecosystem applications (flood, weather, hydrology)

| Project | What it achieves | License (quoted) | Relevance at nadir |
|---|---|---|---|
| RaymanNg/3D-Wind-Field (Cesium blog "GPU Powered Wind Visualization With Cesium", 2019) | GPGPU particle wind on the globe via custom `DrawCommand`s injected as a primitive (blog: `Cesium.DrawCommand` is "the key object of the rendering procedure"); blog: ~~CPU attempts "failed beyond 10,000 particles"~~ verbatim is "the performance was not satisfying when I placed more than 10,000 particles" (verification 2026-09-01); GPU path "similar to doing custom rendering; just use a fullscreen quad as vertex shader" [web] | "MIT" per repo page [web] | Proves particles are feasible *inside* Cesium, but through the private renderer module (`DrawCommand`, framebuffers) — outside the public d.ts. For a nadir instrument the 2-D overlay route (row 12) is simpler and public |
| cambecc/earth (nullschool) | Layered canvases over a D3 SVG map; particles advected by bilinear-interpolated GFS; site updated "every three hours" | "MIT license" [web] | The reference for pacing and for the *fade-previous-frame* trail technique; nadir-equivalent by construction |
| mapbox/webgl-wind | "rendering up to 1 million wind particles at 60fps"; state in textures | "ISC license" [web] | The GPU version of the same idea; the Mapbox blog post explaining it returned 403 at fetch time (UNVERIFIED details: fade opacity, drop rate) |
| ISPRS 2018 NL floods (Cesium + CZML) | Time-dynamic water levels as CZML properties over CityJSON→glTF buildings | Paper; code license not stated (UNVERIFIED) | Pattern only (row 22); 3-D water is doctrinally out |
| Cesium × UNOOSA Commonwealth Digital Twin (2025) | Flood / sea-level-rise scenes in Cesium Stories, "Tap + drag to interact" | n/a (blog) [web] | Curated views + narrative; row 7/18 |
| OSM US "Rising Waters, 3D Worlds" (2025) | "flood simulator using Cesium's 3D OSM tiles and dynamic water modeling" | no code link [web] | Oblique, 3-D water; not adoptable |
| Hydro3DJS (Env. Modelling & Software, 2025) | Browser-native 3-D watershed dynamics with USGS/NOAA feeds — **built on the Google Maps API, not Cesium** [web search abstract] | UNVERIFIED (paywalled) | Listed to prevent a false lead: it is not a Cesium showcase |
| J. Hydroinformatics 25(5) watershed flow platform (2023) | Web platform for visualizing flow in a watershed; search abstract says CesiumJS is the renderer | UNVERIFIED (403 at fetch) | Lead only |

No public Cesium app was found that does what Cascadia is doing — a nadir, bounded-domain,
satellite-first hydrologic instrument. The nearest relatives are nullschool (nadir, field
animation, D3 not Cesium) and the GIBS time-WMTS demo (Cesium, nadir-agnostic, imagery-in-time).

### 2.3 Benchmarks for feel outside Cesium

- **Google Earth Studio.** Easing (row 3), logarithmic altitude (row 2), Time of Day (row 13),
  and the best-practices page's framing rules (avoid extreme close-ups; keep tilt 40–60° for
  3-D city quality; render 4K then downscale to reduce moiré [web]). The tilt advice does not
  apply; the render advice does: **Cascadia's equivalent of "render at 4K" is not fighting
  `devicePixelRatio`** — `useBrowserRecommendedResolution` defaults to `true` [dts:47782],
  which renders at the browser's recommended resolution "and ignore[s] `window.devicePixelRatio`"
  [dts:47782]; `resolutionScale` [dts:47920] is the knob. The repo sets neither (grep of
  `apps/web/src` for `resolutionScale|useBrowserRecommendedResolution|msaaSamples`: only
  `enableLighting` appears). At nadir over ortho-imagery, sub-pixel crispness *is* the
  cinematic material — this is measurable and cheap to A/B (§8 rec 6).
- **Google Earth Timelapse.** Overlapping video-tile pyramid (rows 6, 20).
- **Apple Maps.** WWDC13 s309 [web]: `MKMapCamera` = center coordinate, altitude, heading,
  pitch; "MKMapView's method setCamera: is animatable"; and the operational note "use map view
  region did change animated … to figure out when an animation has completed. Don't use the
  completion handler." The lesson for Cascadia is already embodied: settle is
  `flyTo.complete` **plus** `tileLoadProgressEvent`→0 sustained [repo:SceneController.ts:243-264],
  not the flight callback alone. Flyover's 2026 radiance-field upgrade [web] is oblique
  photorealism — not adoptable.
- **Mapbox GL / MapLibre / deck.gl / d3.** Row 1. All four implement the same paper; three of
  the four use ρ≈1.42 and speed 1.2 by default. This is the most-replicated camera-motion
  design in web mapping, and the repo does not use it yet.
- **Mapbox storytelling template** ("BSD 3-Clause License" [web]). Rows 7, 8. Built with
  "Mapbox GL JS" and "Scrollama.js" [web].
- **NYT moviescroller.** Row 8. The NYT R&D write-up itself could not be fetched
  (rd.nytimes.com blocked); the data.europa.eu guide's description is the citation.
- **Reuters Graphics.** No specific Cesium- or terrain-based cinematic piece could be
  identified with a fetchable primary source at research time. UNVERIFIED; no claim made.
- **Felt.** §0 quote; the rest of the post is the vector-vs-raster argument, which does not
  transfer (Cascadia's ground is raster by choice).
- **Windy / Ventusky / Zoom Earth / MapTiler Weather.** Rows 10, 11, 23, 24. The community
  thread "Artificial frames / animation smoothing" has a Windy staff reply calling motion
  interpolation in replay "rather a bug than a feature" [web] — worth quoting to the owner when
  the crossfade ships: smoothing that *changes what a frame appears to show* is a bug in a
  weather product; smoothing that only blends two real frames, labeled, is not.

---

## 3. Camera motion, in detail

### 3.1 What Cesium's flight actually does (verified in 1.144 source)

- The height profile is chosen in `createHeightFunction` [src:Scene/CameraFlightPath.js:75-126].
  If no `maximumHeight` is given, the peak is computed from the frustum: the altitude at which
  the whole start→end displacement would fit the view, times **0.2**, capped at 1e9 m
  [src:…:104-106]. If `max(startHeight, endHeight) < altitude` the path is a flat-topped arc
  `−x⁸/1e6 + altitude` [src:…:110-119]; otherwise height is a plain `lerp` [src:…:124].
- Default easing: `CUBIC_OUT` when descending from above 11,500 m, else `QUINTIC_IN_OUT`
  [src:…:548-558]. The repo overrides with `minimumJerk` [repo:CameraController.ts:160].
- `pitchAdjustHeight` bends pitch toward nadir at the arc's peak [src:…:45-72] — irrelevant
  when pitch is already −90.
- `flyToBoundingSphere` clamps the range to the SSCC zoom band **only when it computed the range
  itself** [src:Scene/Camera.js:3573-3585]; the repo always passes a range, so the envelope is
  enforced in `CameraEnvelope`, as the prior research concluded.
- `flyOverLongitude` / `flyOverLongitudeWeight` [dts:29079-29080] choose the long way round the
  globe — meaningless inside a 12°-wide domain.

Consequence: today a basin→point zoom is a *linear* height interpolation warped by
minimum-jerk. That is precisely the "seems to accelerate near the surface" motion GES corrects,
and Cesium's arc heuristic (0.2 × fit altitude, x⁸ plateau) is a fixed shape rather than a
perceptual optimum.

### 3.2 Why nadir makes van Wijk exact — and how to adopt it

With pitch −90 and heading 0 the camera is fully described by `(lon, lat, height)`, and at
these scales `height` is proportional to the visible ground width `w`. That is van Wijk's
`(cx, cy, w)` state, which d3's `interpolateZoom` implements directly and MapLibre's `flyTo`
implements with `rho = min(rho, sqrt(wMax / u1 * 2))`, `w(s)`, `u(s)`, `S` [web camera.ts].

Adoption sketch (no Cesium API beyond what the repo uses):

1. In `CameraController.fly`, compute the path from the current `(lon, lat, h)` to the target
   using the van Wijk equations with ρ = 1.42 (the user-study mean the whole ecosystem adopted),
   in a local metric frame (metres east/north from the current position; the domain is small
   enough that Mercator vs geodesic is irrelevant at ρ-screenful scale).
2. Duration from the path length `S` (in ρ-screenfuls) at ~1.2 screenfuls/s, then clamp with
   the existing `MOTION.flight` min/max — the cap survives, the *shape* changes.
3. Drive it per frame from `scene.preRender` with `camera.setView({ destination:
   Cartesian3.fromDegrees(lon, lat, h), orientation: { heading: 0, pitch: −π/2, roll: 0 } })`,
   time-warped by `minimumJerk`. Keep the `started/settled/interrupted` events and the
   `pointerdown/wheel` interruption exactly as they are; keep `camera.cancelFlight()` semantics
   by owning the tween (no Cesium tween is involved, so `scene.tweens` being private — prior
   research "not possible" #10 — no longer matters).
4. Reduced motion: unchanged (`cutTo` + veil).
5. Pure zoom (target under the current centre) degenerates to a log-height zoom — row 2 for free.
6. Row 4: when a flight supersedes another, start the new tween's `t` so its initial velocity
   matches the old tween's current velocity (a one-line derivative match on `minimumJerk`), or
   accept the tiny hitch and note it.

The prior research's soft spring-back (`CameraEnvelope`) should use the same path function so
the "correction" flight and a user-initiated flight are indistinguishable in feel.

**Lower-effort half-step:** keep `flyToBoundingSphere` and pass `maximumHeight` computed from
the van Wijk peak width. The arc peak then matches the perceptual optimum, but Cesium's x⁸
plateau and linear-height descent remain. Try this first only if the full path is deferred.

---

## 4. Time and fields

- **Crossfade, don't cut, between valid times** (row 10), and say so in the inspector. Windy's
  own staff line about interpolation being "rather a bug than a feature" [web] is the honest
  framing: a blend is presentation, the two source frames are the data.
- **Bounded loops with a pace choice** (row 23): Zoom Earth's 3/6/12/24 h loop lengths and
  Fast/Smooth toggle are a good, small UI.
- **Keep particle/streamline state across frame changes** (rows 11, 24). Prefer Ventusky-style
  streamlines for rivers (dash-phase animation on existing polylines, driven by
  `flow_visual_intensity`; note `PolylineDashMaterialProperty` has no phase uniform — rotate
  `dashPattern` or write a custom `Material`, row 24 caveat) over a particle system: cheaper, public API only, and reads
  unambiguously as *direction and relative intensity*, never as a measured discharge.
- **Do not drive anything from the renderer clock.** The GIBS demo's `clock.multiplier`
  pattern is exactly what `CINEMATIC_ARCHITECTURE.md` §4.1/§7.4 forbid; use the `times`
  collection if convenient, with `clock` set to a `Clock` whose `currentTime` `SceneClock`
  writes from the store.

---

## 5. Light and material at nadir

- **Solar light** (row 13): A/B only, as a `layers/cinematic/solar` layer. The honest form is
  *ambient level*, not directional shadows: lower `lambertDiffuseMultiplier` so relief shading
  stays subordinate to the baked NAIP shading; dim toward a night grade when the store's valid
  time is after sunset at the view centre. This is the one place where "Time of Day" survives
  the doctrine, because the timeline is a real clock.
- **Grade, not post-process** (row 17): the per-layer `brightness/contrast/saturation/gamma`
  grade already in `BasemapProvider.ts` is the cheapest, least-leaky film grade; keep it there.
  A frame-wide `PostProcessStage` is the fallback for effects the layer grade cannot do
  (e.g., a vignette that also affects overlays), and must be registered as a `cinematic` layer.
- **Crispness is material** (§2.3 GES note): verify the canvas is rendering at device pixels
  before touching any effect. Blurry ortho-imagery at nadir is the most common reason a
  satellite map looks "like a map" instead of "like the ground".
- **Glass over ground**: the liquid-glass decision stands (prior research); no change proposed.

---

## 6. Narrative (Event Zero) at nadir

Row 7 + row 8: chapters as data, opacity transitions, van Wijk camera between chapters, a
scroll-scrubbed variant for the narrated page. The Mapbox template's `rotateAnimation` and
`pitch` are the only fields dropped; everything else maps 1:1. The replay doctrine
(`as_of`, no look-ahead, hindsight overlay never merged) is untouched because chapters only set
camera + layer alpha + `t`.

---

## 7. Continuity refinements learned from Timelapse / Google Maps / Apple

1. **Warm the landing LOD before landing.** ~~Timelapse keeps "up to 16 videos in sync" so the
   next zoom level is present before the zoom finishes [web].~~ Verification 2026-09-01: the
   "16 videos in sync" line is the *cost* Timelapse avoided, not its technique; what it does is
   show one whole-screen video tile at a time with overlapping siblings [web]. The transferable
   idea below (prefetch the landing LOD) stands on the repo's own numbers, not on Timelapse.
   Cascadia's boot warm covers z5–z9
   and z10 post-reveal [repo:apps/web/src/layers/basemap/domain-warmer.ts:45-50,93-97], but a
   flight to the local band (12 km range ≈ z13–z14) lands on cold tiles and holds the plate up to
   `MAX_HOLD_MS = 8000` [repo:TransitionPlate.ts:22]. Since the destination is known at flight
   start, `domainTiles(z, bboxOfLanding)` can be fetched **during** the flight (2.4 s is a lot
   of tile fetches), so the plate's hold after landing is short or zero. Pure `fetch()` into the
   HTTP cache, same as the warmer; no Cesium internals.
2. **Settle = camera complete AND ground composed.** Apple's "don't use the completion handler"
   [web] is the same lesson the repo already encodes with `GROUND_SUSTAINED_ZERO_MS`
   [repo:SceneController.ts:36]; keep the plate's release gated on the queue, never on the
   flight callback.

---

## 8. Recommendations (ranked)

1. **Implement the van Wijk/Nuij camera path at nadir** (rows 1–5, §3.2). Highest
   cinematic return per line of code; it is what Mapbox, MapLibre, deck.gl and d3 all ship, it
   is exact under the "no angles" doctrine, and it fixes the linear-height zoom that Cesium
   uses today. Public API only (`setView` per frame). A/B against the current
   `flyToBoundingSphere` on the two canonical flights: state→basin, basin→forecast point.
2. **Trial Cesium 1.144's `ScreenSpaceMapCameraController` + `ScreenSpaceZoomCameraController`**
   (row 19) behind a flag. If it holds north-up and nadir natively, `CameraEnvelope`'s
   heading/pitch corrections shrink to position and height only. Re-establish the zoom band
   explicitly (collision detection off ⇒ SSCC clamps off; the zoom controller's own
   `maximumZoomDistance` defaults to 100 km, below the 1,250 km ceiling).
3. **Fetch the landing LOD during the flight** (§7.1). Turns the post-landing plate hold into
   a formality on warm networks.
4. **Ship the valid-time crossfade with the Zoom-Earth-style loop presets** (rows 10, 23) and
   the `cinematic` inspector label on the blended frame.
5. **Streamline (dash-phase) river flow** driven by `flow_visual_intensity` (row 24) — before
   any particle system. Public API, zero new render passes.
6. **Measure device-pixel rendering** (§2.3, §5): confirm the canvas is at DPR and A/B
   `resolutionScale`; this is the cheapest "material" win on retina displays and is currently
   unset.
7. **A/B a solar ambient layer** (row 13) tied to the store time — accept only if the basin
   band screenshot reads as *the same ground, later in the day*, not as re-lit terrain.
8. **Do not pursue** clouds, sky atmosphere, fog, DoF, lens flare, bloom, KML tours, 3-D water,
   Flyover-style photorealism (rows 14–18, 21–22). Each either needs an oblique camera or
   fabricates a sky/surface the instrument cannot vouch for.

---

## 9. Not verified / not found (so nobody re-chases them as facts)

- van Wijk & Nuij 2003 PDF (`vanwijk.win.tue.nl/zoompan.pdf`) returned 503 twice; the TU/e
  portal confirms "two free parameters: animation speed and zoom/pan trade off" but no values
  [web]; the 1.42 / 1.2 figures are cited via MapLibre's and deck.gl's documentation.
  Verification 2026-09-01: MapLibre's JSDoc and d3's page cite the paper by URL; **deck.gl's
  FlyToInterpolator page states `curve: 1.414`, `speed: 1.2` but does not mention van Wijk**;
  Mapbox GL's own source was not fetched (MapLibre's JSDoc is its fork-inherited text). A TU Wien course summary of the paper [web] says its 26-person study showed
  values "distributed quite broadly with no clear tendency" — i.e., 1.42 is a mean, not a law.
- Mapbox "How I built a wind map with WebGL" (403) and Google Design "Prototyping a Smoother
  Map" (403): not fetched; no claims made from them.
- Bentley "5 great 3D visualizations from Cesium in 2025": sign-in wall; not fetched.
- NYT R&D 3-D reconstruction write-up: host blocked; described via data.europa.eu.
- Reuters Graphics: no fetchable Cesium/terrain cinematic example identified.
- Hydro3DJS / J. Hydroinformatics: abstracts only; rendering stack of the latter unconfirmed.
- Cesium Sandcastle IDs verified by fetching raw gallery sources on `main`
  (`clouds`, `atmosphere`, `fog-post-process`, `camera-controllers`,
  `web-map-tile-service-with-time`); `camera-tutorial` on `main` no longer contains the
  `flyTo`-with-easing handlers the search snippets describe (it is a keyboard/mouse controls
  demo) — flight options were verified from the local source instead.

---

## Verification

Adversarial pass, 2026-09-01. Method: every `[dts:]` / `[src:]` / `[repo:]` line number was
printed from the installed tree (`cesium@1.144.0`, `license: Apache-2.0`,
`node_modules/cesium/package.json`); every `[web]` URL was re-fetched and the quoted text
compared verbatim. Corrections were applied inline above (marked "verification 2026-09-01",
with strikethrough where the original sentence was wrong).

### Cesium-API claims

| # | Claim | Verdict | Note |
|---|---|---|---|
| A1 | Default flight lerps height on pure zooms; arc only when `max(start,end) < 0.2 × fit altitude`; x⁸ plateau | ✓ | `CameraFlightPath.js:104-106` (`getAltitude(...) * 0.2`, cap 1e9), `:110-119` (`power = 8`), `:124` (`CesiumMath.lerp`). The fit altitude is computed from the displacement's components along `camera.up`/`camera.right` (`:88-101`), so a pure nadir zoom yields altitude≈0 → lerp branch; a pan+zoom arcs only if both endpoint heights are under the 0.2× fit. GES quotes verbatim on the fetched page. |
| A2 | Default easing `CUBIC_OUT` when descending from >11,500 m, else `QUINTIC_IN_OUT`; repo overrides with `minimumJerk` | ✓ | `CameraFlightPath.js:548-558` exact; `CameraController.ts:160` `easingFunction: minimumJerk`. **Line fix:** `minimumJerk` lives at `motion.ts:24-28`, not `:26-30`. GES easing quotes ("perfectly horizontal", "smooth curves equal smooth motion", "synced across attributes") verbatim. |
| A3 | 1.144 adds `ScreenSpaceMapCameraController` + Controller framework; panSpeed 1.0 / inertialDecay 6.0 / `exp(-decay·dt)`; gallery disables `enableInputs` and `enableCollisionDetection`, which disables SSCC zoom clamps | ✓ with corrections | `CHANGES.md:11-12`; `Cesium.d.ts:32907,33139,47989`; `ScreenSpaceMapCameraController.js:99,106,113,201` exact. **Fixes:** the class doc is at `:20-21` (not `:8-9`); the gallery `camera-controllers/main.js` never constructs `ScreenSpaceMapCameraController` — it uses `HybridScreenSpacePanCameraController` + tilt-orbit + zoom (the Map controller's own `@example` at `:25-28` shows the pattern). SSCC clamp bypass confirmed at `ScreenSpaceCameraController.js:268` and `:598-616`. **New finding:** `ScreenSpaceZoomCameraController.maximumZoomDistance` defaults to 100,000 m (`:151`), below the repo's 1,250 km ceiling. The Aug-2026 release post confirms "asset inspection use cases" but names only the framework, not the Map controller. |
| A4 | `flyToBoundingSphere` clamps range to SSCC band only when the caller passes no range; repo always passes one | ✓ | `Camera.js:3573-3585` (`!defined(range) \|\| range === 0.0` → compute + clamp); `flyToBoundingSphere` calls `adjustBoundingSphereOffset` at `:3671`. `CameraController.ts:96-97` (computed `framingRange`), `:103` (`FORECAST_POINT_FRAMING.rangeM`). Envelope enforcement is therefore the repo's job. |
| A5 | GIBS demo: `TimeIntervalCollection.fromIso8601` + `dataCallback`, WMTS `{clock, times}`, `clock.multiplier = 7200`; driver must be store time via `SceneClock` | ✓ | Gallery source fetched verbatim (`iso8601: "2015-07-30/2017-06-16/P1D"`, `clock: viewer.clock`, `times: times`, `clock.multiplier = 7200`, GIBS endpoint). `Cesium.d.ts:47397,47473,47479,17480-17490` exact. `CINEMATIC_ARCHITECTURE.md:150` (§4.1 `SceneClock`), `:374-375` ("no layer reads wall-clock time"). |
| A6 | Clouds, Fog, Atmosphere, DoF, lens flare, KmlTour exist but are not adoptable at nadir | ✓ | All d.ts lines exact (`32384, 33421, 34345, 26486, 43107, 43332, 43454, 22730`). "A cumulus cloud billboard positioned in the 3D scene" is verbatim both in `Cesium.d.ts:33414` and the ref-doc page. `SceneController.ts:134-135` sets `skyBox.show`/`skyAtmosphere.show = false`. The nadir-unsuitability argument is reasoning, not API fact; the API facts underneath it hold. |
| A7 | Solar lighting: `enableLighting`, `lambertDiffuseMultiplier`, `dynamicAtmosphereLighting`, `Scene.light` "directional light from the Sun"; repo sets `enableLighting=false` | ✓ | `Cesium.d.ts:34761,34767,34772,44206-44208,45541,33813,33892` exact; `SceneController.ts:109` exact; GES "Time of Day is a powerful cinematic effect" and "renders realistic lighting, stars, and atmospherics based on the position of the sun" verbatim. Caveat: "NAIP carries baked sun shading" is an inference — the repo's `BasemapProvider.ts:85` comment confirms the USGSImageryOnly service is NAIP-based at fine zooms, but no source measures the shading; treat the A/B framing, not the premise, as the deliverable. |

### External claims

| # | Claim | Verdict | Note |
|---|---|---|---|
| B1 | MapLibre / deck.gl / d3 van Wijk defaults (1.42 / 1.2; 1.414 / 1.2; √2 + path-length duration) | ✓ with correction | MapLibre `camera.ts` JSDoc verbatim (incl. "1.42 is the average value selected by participants in the user study discussed in van Wijk (2003)", `speed` default 1.2, `rho = Math.min(rho, Math.sqrt(wMax / u1 * 2))`); MapLibre docs page defaults 1.42 / 1.2; deck.gl page "Default `1.414`" / "Default `1.2`"; d3 page "The default curvature is sqrt(2)" and the `interpolate.duration` sentence verbatim. **Correction (§9):** deck.gl's page does not cite van Wijk; only MapLibre and d3 do. Mapbox GL's own source not fetched (MapLibre's text is fork-inherited). The 503 on the primary PDF is the author's report; not re-tested. |
| B2 | Nadir + north-up collapses camera state to `(lon, lat, height)`; drivable via public `camera.setView` from `preRender`; `scene.tweens` private | ✓ | `envelope.ts:45-51` (all `TILT_CAP` 0; comment at 42-44), `CameraController.ts:16-18` (`pitchDeg: -90` on all three framings), `SceneController.ts:145-147` (`enableLook=false`, `enableTilt=false`, `constrainedAxis = UNIT_Z`). `Scene.js:1188-1200` marks `tweens` `@private`; zero hits in `Cesium.d.ts`; prior research item #10 at its line 322. `w = 2h·tan(fov/2)` is exact for a flat ground plane — the ellipsoid deviation across a 12°-wide domain is negligible for path shape. |
| B3 | Repo sets no `resolutionScale`/`useBrowserRecommendedResolution`/`msaaSamples`; default `true` ignores DPR | ✓ (stronger than stated) | grep of `apps/web/src` returns only `SceneController.ts:109`; `Cesium.d.ts:47782` (`useBrowserRecommendedResolution = true`, "ignore `window.devicePixelRatio`"), `:47920`, `:43952` (`msaaSamples = 4`). `CesiumWidget.js:92-94` shows `pixelRatio = useBrowserRecommendedResolution ? 1.0 : window.devicePixelRatio` — so on any DPR>1 display the canvas *is* (not "may be") rendering below device pixels today. |
| B4 | Mapbox storytelling: BSD 3-Clause; `mapAnimation` flyTo/easeTo/jumpTo; `onChapterEnter`/`onChapterExit` opacity lists; "opacity (NOT the visibility)"; only `rotateAnimation` and `pitch` are doctrine-incompatible | ✓ | Repo shows "BSD 3-Clause License"; README describes `mapAnimation` ("Options: flyTo, easeTo, jumpTo"), `rotateAnimation` ("Rotates 90 degrees over 24 seconds"), `onChapterEnter/Exit` ("layer name, opacity, duration"), `pitch` ("0 is straight down"); "Built With: Mapbox GL JS, Scrollama.js". Blog sentence "toggle the layer's opacity (**NOT the visibility**)" verbatim. Note: the chapter location config also carries a `bearing` (heading) field in that template — not re-fetched here; if present it must be pinned to 0 alongside `pitch`. |
| B5 | Windy "completely disappear" report; Windy staff "rather a bug than a feature"; MapTiler per-frame pyramids + client interpolation | ✓ | Topic 7755: "when jumping between frames of the animation (eg between 1am and 4am), all the particles completely disappear, and it takes a second for the new particles to emerge / grow long tails" verbatim, no staff reply. Topic 38403: Suty (Windy Staff) "I am afraid that this is rather a bug than a feature." MapTiler: both sentences ("processed as a separate tile pyramid, which allows us to load additional frames into the existing client-side animation as soon as they are available"; "interpolate the data values between the available forecasted time frames to achieve beautiful smooth animations") verbatim. |
| B6 | Licenses: cambecc/earth "MIT license", mapbox/webgl-wind "ISC license", RaymanNg/3D-Wind-Field "MIT"; 3D-Wind-Field uses private `DrawCommand` | ✓ with misquote fixed | All three license strings verbatim on the repo pages; webgl-wind "Capable of rendering up to 1 million wind particles at 60fps". Cesium blog links RaymanNg/3D-Wind-Field and calls `Cesium.DrawCommand` "the key object of the rendering procedure"; `DrawCommand` appears in `Cesium.d.ts` only inside a doc comment (`:40729`), never as an export; `Framebuffer` has no class export. **Fix (§2.2):** the blog's CPU line is "the performance was not satisfying when I placed more than 10,000 particles", not "failed beyond 10,000 particles". `SceneTransforms.worldToWindowCoordinates` at `SceneController.ts:463`. |
| B7 | Timelapse "keeps up to 16 videos in sync" with overlapping siblings; repo lands cold at 12 km above the z10 warm and can hold the plate 8 s | ✗ (mechanism misattributed; repo half ✓) | The fetched sentence is "it requires a web browser to keep up to 16 videos in sync while interacting with the visualization" — the *problem* with a normal pyramid, which Time Machine solves by showing "only … one whole-screen tile at a time" with overlapping siblings. Rows 6/20 and §7.1 corrected inline. Repo citations hold: `domain-warmer.ts:45-50` (z5–z9 boot), `:93-97` (z10 deep warm), `TransitionPlate.ts:22` (`MAX_HOLD_MS = 8_000`), `CameraController.ts:18` (12 km). The prefetch-during-flight idea survives on the repo's own numbers. |
| B8 | Ventusky "current lines"; `PolylineDashMaterialProperty`/`dashPattern`; repo dash usage; `flow_visual_intensity` in the join | ✓ with caveat | Ventusky: "we utilise current lines that are used to illustrate the movement of particles in liquids" and "animated arcs" verbatim. `Cesium.d.ts:24060` / `:24058` exact; `FloodHazardLayer.ts:138,172` both `new PolylineDashMaterialProperty(...)`; `match.ts:21` `flow_visual_intensity`. **Caveat (row 24, §4):** the material has no phase/offset uniform (`Cesium.d.ts:24053-24058` lists only `color`, `gapColor`, `dashLength`, `dashPattern`), so a "dash phase" is 16 discrete `dashPattern` rotations or a custom `Material`. |

Net: 14 of 15 claims stand; one (B7) is reversed on attribution; five carry line-number or
quotation fixes; two new facts surfaced that change recommendations 2 and 5 (zoom controller
100 km default; no dash-phase uniform).
