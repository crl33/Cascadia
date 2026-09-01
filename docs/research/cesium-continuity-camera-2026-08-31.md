# CesiumJS 1.144 — imagery continuity + PNW operating envelope: verified options

Research date: 2026-08-31. Target: `apps/web` (Cesium **1.144.0** exact — verified in
`/Users/cy/Desktop/Cascade Oracle/apps/web/package.json` and
`node_modules/cesium/package.json`). All symbols verified against the locally installed
package. Verification legend:

- **[dts:NNNNN]** — `apps/web/node_modules/cesium/Source/Cesium.d.ts` line NNNNN (public API surface)
- **[src:File.js:NN]** — `apps/web/node_modules/@cesium/engine/Source/<path>` line NN (implementation; the npm `cesium` package re-exports `@cesium/engine`)
- **[doc]** — live ref doc at cesium.com, confirmed to be the 1.144 page:
  https://cesium.com/learn/cesiumjs/ref-doc/Globe.html ·
  https://cesium.com/learn/cesiumjs/ref-doc/ImageryLayer.html ·
  https://cesium.com/learn/cesiumjs/ref-doc/ScreenSpaceCameraController.html

Repo files referenced (read, not modified):
- `/Users/cy/Desktop/Cascade Oracle/apps/web/src/scene/SceneController.ts`
- `/Users/cy/Desktop/Cascade Oracle/apps/web/src/layers/basemap/BasemapProvider.ts`
- `/Users/cy/Desktop/Cascade Oracle/apps/web/src/camera/CameraController.ts` (+ `types.ts`, `flight-math.ts`)
- `/Users/cy/Desktop/Cascade Oracle/apps/web/src/scene/SemanticZoomController.ts`, `src/scene/bands.ts`
- `/Users/cy/Desktop/Cascade Oracle/tests/fixtures/geo/basins_seed_state_lod.geojson`

---

## PROBLEM 1 — imagery that never looks like tiles

### 1a. Controlling ancestor-vs-child replacement

| API | In 1.144? | How verified | What it does / expected visual result |
|---|---|---|---|
| `Globe.loadingDescendantLimit` (default **20**) | YES, public | [dts:34737], [src:Scene/Globe.js:129], [src:Scene/QuadtreePrimitive.js:938] | If a tile has more than this many loading descendants, the *ancestor* renders first. Raising it (e.g. 100+) suppresses intermediate refinement steps: the doc string says a large value will "make detail appear all at once after a long wait". **This is the single most direct public knob against tile-by-tile refinement.** Cost: the view stays coarse (ancestor imagery) longer before snapping to full detail in one pass. |
| `Globe.preloadAncestors` (default true) / `Globe.preloadSiblings` (default false) | YES, public | [dts:34743, 34750], [src:Scene/Globe.js:138,148] | Already set in `SceneController.ts:102-104`. Keeps composed lower-res ground under pans/zooms. No further headroom here. |
| `Globe.maximumScreenSpaceError` (default 2) | YES, public | [dts:34720], [doc] | Refinement threshold in screen pixels. **Dynamic use is the lever**: raise to ~3–4 while a flight is in progress (nothing refines mid-motion; the pre-loaded ancestors carry the frame), restore to 2 in the flight `complete`/`settled` handler so the landing view refines once, in place. Perceived result: motion shows a stable coarse picture; detail resolves after arrival instead of churning under the moving camera. |
| `Globe.tileCacheSize` (default 100) | YES, public | [dts:34727] | Already 600 in the repo. |
| `Globe.tileLoadProgressEvent` | YES, public | [src:Scene/Globe.js:558-568], [doc] | Exact semantics (from source doc comment): "raised when the length of the tile load queue has changed since the last render frame. When the load queue is empty, all terrain and imagery **for the current view** have been loaded. The event passes the new length of the tile load queue." The repo's `onGroundComposed` usage is correct. The same event can gate the SSE-restore trick above (restore SSE, wait for queue→0, then lift any veil). |
| `Globe.progressiveResolutionHeightFraction` | **NO — does not exist on Globe** | grep of `Scene/Globe.js` and `Scene/QuadtreePrimitive.js`: zero hits; [doc] Globe page confirms absent | It is a `Cesium3DTileset` constructor option only [dts:30806]. Do not chase it for the globe. |
| `immediatelyLoadDesiredLevelOfDetail` | **NO — 3D Tiles only** | [dts:30816, 31206] (only inside `Cesium3DTileset`); absent from Globe.js / terrain providers | Not available for globe imagery/terrain. |

### 1b. Whole-layer crossfades

| API | In 1.144? | How verified | Notes |
|---|---|---|---|
| `ImageryLayer.alpha` (0–1) | YES, public | [dts:37110 region], [doc] | Per-layer uniform, cheap to animate per frame. There is **no built-in tween**: `scene.tweens` is not in the public d.ts (grep: zero hits) — drive alpha from a `scene.preRender` listener or rAF. |
| Second `ImageryLayer` over the same provider, fade, remove | YES (pattern) | `viewer.imageryLayers.add(layer, index)` public; two layers may share one provider instance (each layer keeps its own imagery cache) | The clean crossfade: add the new layer at alpha 0 above the old, wait for `readyEvent` + a `tileLoadProgressEvent`→0 pass, ramp alpha 0→1 over ~400 ms in preRender, then remove the old layer. Use it for grade changes or provider swaps. Memory doubles during the fade. |
| `ImageryLayer.readyEvent` / `.ready` | YES, public | [dts:37125-37136 region], [doc] | Fires when the provider is created; combine with tile queue for "fully composed". |
| `ImageryLayer.dayAlpha` / `nightAlpha` | YES, public | [dts:36966-36972] | Only meaningful with `globe.enableLighting` (repo has it false). Not useful here. |
| `ImageryLayer.splitDirection` + `scene.splitPosition` | YES, public | [dts:37142], [doc] | A/B vertical split, hard line — a comparison tool, not a fade. Not recommended for production visuals. |
| `ImageryLayer.minificationFilter` / `magnificationFilter` | YES, public but **restricted** | [dts:37151, 37160]; runtime check [src:Scene/ImageryLayer.js:1255-1261] throws unless NEAREST or LINEAR | Only `NEAREST` and `LINEAR` are legal (mipmap filters throw a DeveloperError). Default LINEAR is already the smooth option — there is no filtering headroom for hiding seams. |
| `ImageryLayer.brightness/contrast/hue/saturation/gamma` | YES, public | [dts], already used by `graded()` in BasemapProvider.ts | Whole-layer only. Animatable per frame (they are uniforms) — a grade change can be eased rather than stepped. Cannot fix per-tile tone seams (those are baked into the source JPEGs, as BasemapProvider.ts:72-77 already documents). |

### 1c. Per-tile fade-in

**Does Cesium fade globe imagery tiles in? NO — and there is no private ramp to reach for either.**

- Verified by grepping the whole surface pipeline: the only "fade" symbols in
  `Scene/GlobeSurfaceTileProvider.js` are `lightingFadeOutDistance` / `nightFadeDistance`
  (atmosphere/lighting distance fades, lines 99-100, 1774-1778, 2013-2014). Zero fade
  code in `Scene/GlobeSurfaceTile.js`, `Scene/TileImagery.js` (no `alpha` at all), or
  `Scene/ImageryLayer.js`. Tiles pop when a texture swaps in.
- This is a long-standing open request upstream, not a hidden knob:
  [CesiumGS/cesium#8581 "Make time dynamic imagery smoother"](https://github.com/CesiumGS/cesium/issues/8581)
  (asks for a configurable fade), [CesiumGS/3d-tiles#343 "Load tiles with fade-in"](https://github.com/CesiumGS/3d-tiles/issues/343),
  and [CesiumGS/cesium#526 terrain/imagery roadmap](https://github.com/CesiumGS/cesium/issues/526).
- Approximations that ARE public: the SSE freeze-during-motion (1a), high
  `loadingDescendantLimit` (1a), the whole-layer crossfade (1b), and the repo's existing
  veil for cuts.

### 1d. Limiting rendered extent

| API | In 1.144? | How verified | Visual behavior at the edge |
|---|---|---|---|
| `ImageryLayer` constructor option `rectangle` (default = provider rectangle) | YES, public | [dts:36958], [doc] "can limit the visible portion of the imagery provider" | Imagery simply isn't requested/drawn outside — the globe still renders there and shows `globe.baseColor` (repo's dark hsl(222,52%,6%)). Edge is a hard imagery cut on tile boundaries of the layer's texture coordinates; no feathering built in. Bonus: eliminates all offshore/out-of-state tile requests. |
| `ImageryLayer.cutoutRectangle` | YES, public | [dts:37168], [doc] | Inverse tool — punches a hole in a layer. Useful if you ever want the base imagery visible only *outside* a focus region, not needed here. |
| `Globe.cartographicLimitRectangle` | YES, public | [dts:34914], [src:Scene/GlobeSurfaceTileProvider.js:216,732-746,1890], [doc] | The globe itself stops: implemented as a **hard fragment `discard`** in the globe fragment shader ([src:Shaders/GlobeFS.js:334-338] — texcoords outside the uniform rectangle are discarded). Outside the rectangle you see whatever is behind the globe: skybox/atmosphere/`scene.backgroundColor`. There is **no falloff knob** — the edge is a razor cut, and it also culls tile loads outside the rectangle (clipped in `computeTileVisibility`). |
| Feathered edge (composite recipe) | YES (composition of public APIs) | `SingleTileImageryProvider` exported [Cesium.js:798], [dts:45092]; data-URI/canvas URL accepted via `Resource` | Cesium cannot feather the limit edge, but you can hide it: (1) stack a **vignette ImageryLayer** on top — a `SingleTileImageryProvider` whose image is a canvas-generated frame (transparent center → opaque `baseColor`-dark at the border), with layer `rectangle` = the envelope; it drapes on the globe and fades the world out before the hard edge; (2) set `scene.skyBox.show=false`, `scene.skyAtmosphere.show=false`, `scene.backgroundColor` = the same dark token, so the discarded region beyond the edge is the same color the vignette fades into. Result: the world dissolves into the design's canvas instead of ending at a polygon edge. At the top-down operating pitches of Problem 2 the edge is rarely on screen anyway. |
| `Globe.translucency` (`GlobeTranslucency`, has its own `rectangle`) | YES, public | [dts:34960, 35003+] | Makes the globe surface translucent within a rectangle — for underground/x-ray views. Not a fit for domain limiting (it reveals the void, doesn't mask it). Listed for completeness. |

### 1e. Treating known-bad (all-white offshore) tiles

Ranked recommendation order:

**1. `tileDiscardPolicy: new DiscardMissingTileImagePolicy(...)` — the built-in, designed-for-this mechanism.**
- `UrlTemplateImageryProvider` accepts `tileDiscardPolicy` in its constructor
  [src:Scene/UrlTemplateImageryProvider.js:136,230,450]. `DiscardMissingTileImagePolicy`
  is exported [Cesium.js:613], public [dts:33868].
- Flow, verified in source: a discarded image is marked `ImageryState.INVALID` with the
  in-source comment "Mark discarded imagery tiles invalid. **Parent imagery will be used
  instead.**" [src:Scene/ImageryLayer.js:1245-1248]; `GlobeSurfaceTile` then treats it
  like FAILED and upsamples from the ancestor [src:Scene/GlobeSurfaceTile.js:369-371].
  **Exactly the owner-desired result: the white square is replaced by the parent's real
  (lower-res) imagery, not by a void.**
- Usage sketch:
  ```ts
  new UrlTemplateImageryProvider({
    url: USGS_URL, maximumLevel: 16, credit,
    tileDiscardPolicy: new DiscardMissingTileImagePolicy({
      // the known white tile documented in BasemapProvider.ts (San Juans, z11)
      missingImageUrl: `${BASE}/tile/11/324/705`,   // {z}/{y}/{x} order per template
      pixelsToCheck: [new Cartesian2(0, 0), new Cartesian2(120, 120), new Cartesian2(200, 20)],
    }),
  })
  ```
- Cost model (from source): when a discard policy exists, `ImageryProvider.loadImage`
  fetches with `preferBlob: true` [src:Scene/ImageryProvider.js:253-259] so every tile
  goes blob→ImageBitmap (small constant overhead). `shouldDiscardImage` first compares
  **blob byte length** against the missing image [src:Scene/DiscardMissingTileImagePolicy.js:128-130]
  — only tiles whose encoded size exactly matches the reference white JPEG get the full
  `getImagePixels` (canvas draw + readback) check. Identical white JPEGs from the same
  server are byte-identical, so the fast path does almost all the work.
- **Quirk to know:** the pixel index math is `pos.x * 4 + pos.y * width`
  [src:Scene/DiscardMissingTileImagePolicy.js:135-138] — NOT `(y*width+x)*4`. It compares
  the same odd offsets in both images, so it is self-consistent, but the coordinates you
  pass are not literal (x, y) pixels. Using several spread-out `pixelsToCheck` values is
  still robust; just don't reason about them as exact positions.
- Residual risk: a *different-sized* white tile (other campaign, other zoom) escapes the
  byte-length fast path and, if its bytes differ, is kept. Add one `missingImageUrl` per
  distinct white-tile variant if more are found (one policy per provider — pick the most
  common variant; the wrapper in option 3 is the fallback for the general case).

**2. `ImageryLayer.colorToAlpha = Color.WHITE` with a tight `colorToAlphaThreshold`.**
- Public, GPU-side, zero per-tile CPU [dts:37172, 37176; default threshold 0.004], [doc]
  "Color value that should be set to transparent."
- Visual result: near-pure-white pixels become transparent → the dark `globe.baseColor`
  shows through. That means the white square becomes a **dark square**, not parent
  imagery — less good than option 1 — and, critically, **glacier/snow pixels on Rainier
  and the North Cascades can hit pure white in summer NAIP** and would punch dark holes
  in mountains. Usable only as a stopgap, with the threshold left at its tiny default and
  verified against Rainier at river band. Not the primary fix.

**3. Custom wrapping `ImageryProvider` (decode-and-inspect).**
- Feasible and fully public: an object satisfying the `ImageryProvider` duck type whose
  `requestImage(x, y, level, request)` [dts:35473 signature — returns
  `Promise<ImageryTypes> | undefined`, where ImageryTypes includes HTMLCanvasElement]
  delegates to an inner `UrlTemplateImageryProvider`, draws the result to an offscreen
  canvas, samples ~16 pixels, and on "all white" either returns a 1×1 transparent canvas
  (renders as baseColor) or throws/returns a rejected promise (renders as FAILED → the
  quadtree upsamples the parent, same as option 1).
- Cost: one 256×256 canvas draw + `getImageData` per *loaded* tile — roughly 0.3–2 ms
  each on the main thread, on every tile, forever. Verdict: **works but unnecessary**;
  the discard policy achieves the same end state through supported machinery with a
  byte-length fast path. Reach for the wrapper only if multiple white variants defeat
  the single-reference discard policy.

**4. `provider.errorEvent` / `TileProviderError`** — public ([dts:17005], provider
`errorEvent` getters) but only for *failed requests* (network/HTTP). The white tiles are
HTTP 200 with bad content, so this surface never fires for them. Use it only for the
retry/telemetry story, not for content policing. There is no API to substitute a
different image from an errorEvent handler.

### Recommended architecture, Problem 1 (mapped to real files)

1. **`BasemapProvider.ts` (`usgsImagery.createImagery`)** — add the
   `DiscardMissingTileImagePolicy` to the `UrlTemplateImageryProvider` options (1e-1),
   and pass `rectangle: Rectangle.fromDegrees(-128, 44, -116.5, 51.5)` on the
   `ImageryLayer` constructor so no tile outside the operating envelope is ever fetched
   or drawn (1d). Both are provider-level facts, so this file is their home per the
   repo's own registry doctrine.
2. **`SceneController.ts` constructor** — raise `globe.loadingDescendantLimit` (start at
   ~64; A/B at basin band) next to the existing preload/tileCacheSize block; set
   `globe.cartographicLimitRectangle` to the same envelope; kill skybox/atmosphere and
   set `scene.backgroundColor` to the canvas dark so the limit edge dissolves (1d).
3. **`CameraController` events → SSE freeze**: in `SceneController`, subscribe to the
   camera `started`/`settled`/`interrupted` events it already emits; on `started` set
   `globe.maximumScreenSpaceError = 3.5`, on `settled`/`interrupted` restore `2` and let
   the existing `tileLoadProgressEvent` hook observe the single refine-in-place pass
   (1a). No new module needed — it is ~10 lines in SceneController.
4. **Optional polish**: the vignette `SingleTileImageryProvider` frame layer (1d) if the
   envelope edge is ever visible at orbital band; a preRender-driven alpha crossfade
   helper (1b) when a grade or provider swap ships.

---

## PROBLEM 2 — PNW operating envelope + top-down camera

### Public constraint mechanisms (all verified in 1.144)

| Mechanism | API | How verified | Semantics and limits |
|---|---|---|---|
| Zoom range (user gesture) | `scene.screenSpaceCameraController.minimumZoomDistance` / `maximumZoomDistance` | [dts:44868, 44872], [src:Scene/ScreenSpaceCameraController.js:132,138,575-615], [doc] | Heights above the ellipsoid clamped during the zoom gesture. The approach is already "soft": the zoom rate decays as the camera nears `minimumZoomDistance` (source comment "the zoomRate slows and stops minimumZoomDistance above it"). **Caveat 1:** the clamps are honored only when `enableCollisionDetection` is true (default) — the d.ts says explicitly "When disabled, the values of maximumZoomDistance and minimumZoomDistance are ignored" [dts:44940-44944]. **Caveat 2:** they constrain gestures, not code: `camera.setView` ignores them entirely, and `flyToBoundingSphere` clamps only a range it computed itself — an explicit `offset.range` (which `CameraController.fly` always passes) bypasses the clamp [src:Scene/Camera.js:3563-3586]. |
| Tilt/pitch limit (user gesture) | `scene.screenSpaceCameraController.maximumTiltAngle` | [dts:44951], [src:Scene/ScreenSpaceCameraController.js:284,2070-2077], CHANGES.md ("Added ScreenSpaceCameraController.maximumTiltAngle", PR #12169), [doc] | **Yes, 1.144 has a public pitch limit for the tilt gesture.** Units: radians of tilt **measured from nadir at the tilt pivot** — verified from source: tilt3D builds an east-north-up frame at the picked point [src:2466+ uses `Transforms.eastNorthUpToFixedFrame` then `rotate3D(..., Cartesian3.UNIT_Z)`], and the cap computes `tilt = π − acos(dot(camera.direction, localUp))`, so 0 = straight down, π/2 = horizontal. Example in the docs: `maximumTiltAngle = Math.PI / 2` prevents tilting below the surface. To allow at most 45° off nadir: `maximumTiltAngle = Math.PI / 4`. **Limits:** caps only further *increase* via the gesture (a camera already past the cap isn't pushed back), and does not constrain programmatic flights. There is **no minimumTiltAngle** (cannot force obliqueness publicly — not needed here). |
| Disable gestures | `enableTilt`, `enableRotate`, `enableLook`, `enableTranslate`, `enableZoom`, and the `tiltEventTypes`/`rotateEventTypes`/`zoomEventTypes`/`lookEventTypes`/`translateEventTypes` arrays | [dts:44817-44836, 44885-44921], [doc] | In 3D: **rotate** = left-drag orbiting the globe (this is how users pan in 3D); **tilt** = middle-drag / ctrl-drag / pinch changing pitch around a picked point; **look** = free-look (changes view direction without moving — off by default outside space). `enableLook = false` is safe and recommended. `enableTilt = false` locks pitch AND heading changes from the tilt gesture ("camera is locked to the current heading" per doc). The `*EventTypes` arrays let you re-map or remove individual inputs (e.g. drop CTRL_DRAG from tiltEventTypes). |
| North-up | `camera.constrainedAxis = Cartesian3.UNIT_Z` | [dts:28609] "If set, the camera will not be able to rotate past this axis in either direction"; [src:Scene/ScreenSpaceCameraController.js:2040-2042, 2229-2250] | With the axis set, the left-drag rotate gesture orbits about the pole axis, keeping north up and preventing pole-crossing rolls. **Caveat:** the tilt gesture's *horizontal* component still rotates heading around the local up (rotate3D is called for both axes inside tilt3D, and there is no public flag to suppress just the twist — see not-possible list). Heading correction on `moveEnd` remains necessary if tilt is enabled anywhere. |
| Position constraint | none built-in — `camera.percentageChanged`/`changed`/`moveEnd` + custom controller | [dts:28618, 28693]; repo already wires exactly this in `CameraController` constructor (percentageChanged = 0.05, changed + moveEnd listeners) | There is no public "camera bounds rectangle". The soft-constraint controller below is the supported pattern. |
| Hiding out-of-domain globe | `globe.cartographicLimitRectangle` | (see 1d) | Doubles as a *physical* domain statement: outside it there is literally nothing to look at, which itself discourages wandering. |

### Where the repo stands today (real symbols)

- `CameraController` (`apps/web/src/camera/CameraController.ts`) owns every programmatic
  move: `CASCADIA_VIEW = { lon: −122.3, lat: 47.6, rangeM: 1_500_000, pitchDeg: −55 }`,
  `BASIN_FRAMING = { pitchDeg: −60 }`, `FORECAST_POINT_FRAMING = { rangeM: 12_000,
  pitchDeg: −45 }`. Flights go through `flyToBoundingSphere` with explicit range
  (`framingRange` from `flight-math.ts`), minimum-jerk easing, and interruption on
  pointerdown/wheel/keydown. It already publishes throttled `CameraSample`s
  (`heightAboveTerrainM`, `pitchDeg`, `settled`) and emits `started/settled/interrupted`.
- `SemanticZoomController` + `bands.ts`: bands from effective height with ±12 %
  hysteresis — tops at state 900 km, basin 450 km, river 90 km, local 8 km.
- `SceneController.applyBand(band)` already fans band changes out to layers — the natural
  seam for band-dependent camera policy too.

### Envelope numbers (grounded in fixtures)

From `tests/fixtures/geo/basins_seed_state_lod.geojson` (6 seed basins, bboxes in
properties): union of basin bboxes = **[−122.71, 46.78] → [−120.65, 49.31]** (Skagit,
Nooksack, Snohomish/Snoqualmie, Cedar/Lake Washington, Green-Duwamish, Puyallup/White —
all Puget Sound drainages). Recommended:

- **Hard domain** (cartographicLimitRectangle + imagery-layer rectangle):
  `Rectangle.fromDegrees(-128, 44, -116.5, 51.5)` — the full-WA envelope from the brief;
  keeps eastern-WA basins addressable later without touching the renderer.
- **Soft camera envelope** (spring-back rectangle for the camera *target*):
  `[-124.8, 45.8, -119.8, 49.6]` — seed-basin union plus ~2° margin west/south for
  coastal context and the Columbia; widen when non-Puget basins ship. Keep both
  rectangles as named constants in a new `apps/web/src/camera/envelope.ts` so the soft
  one can follow geography without renderer edits.
- **Zoom band** — one honest conflict to surface: the brief's "~200 km-ish orbital"
  ceiling contradicts the repo's own datum. `CASCADIA_VIEW.rangeM` is **1,500 km** and
  `bands.ts` places the state band at 450–900 km with orbital above it; a 200 km max
  would make three of five bands unreachable. Recommendation: `minimumZoomDistance = 600`
  (the brief's local floor), `maximumZoomDistance = 1_800_000` (home view at 1.5 Mm plus
  headroom; the gesture's built-in rate decay makes both ends feel soft). If the owner
  truly wants a 200 km ceiling, that is a bands.ts + CASCADIA_VIEW retune first, not a
  camera-controller decision. Keep `enableCollisionDetection = true` (default) or the
  clamps silently turn off.
- **Pitch policy per band** (near-nadir by default, oblique only local):
  - orbital/state/basin/river: flights at −85° (retune `CASCADIA_VIEW.pitchDeg`,
    `BASIN_FRAMING.pitchDeg` to −85); user tilt cap `maximumTiltAngle = toRadians(15)`.
  - local: `FORECAST_POINT_FRAMING.pitchDeg` −55 to −45 (controlled oblique); user cap
    `toRadians(50)`.
  - Note `effectiveHeight` in `SemanticZoomController` divides by sin|pitch| — moving the
    defaults toward nadir *lowers* effective heights ~10–25 % versus today's −55/−60, so
    re-check band boundaries against the new framing (the −60° basin framing currently
    inflates effective height by ~1.15×).

### Recommended implementation (mapped to real files/symbols)

**1. `SceneController` constructor — static physics (~8 lines).** After the globe block:
```ts
const sscc = this.viewer.scene.screenSpaceCameraController;
sscc.minimumZoomDistance = ZOOM_FLOOR_M;        // 600
sscc.maximumZoomDistance = ZOOM_CEILING_M;      // 1_800_000
sscc.enableLook = false;
this.viewer.camera.constrainedAxis = Cartesian3.UNIT_Z;   // north-up rotate gesture
this.viewer.scene.globe.cartographicLimitRectangle = HARD_DOMAIN_RECT;
```

**2. Band-dependent tilt cap — extend `applyBand`.** `SceneController.applyBand(band)`
already runs on every `bandChanged`; add one line setting
`sscc.maximumTiltAngle = TILT_CAP_BY_BAND[band]` from a table in `envelope.ts`
(15° for orbital→river, 50° for local). This keeps "band ⇒ meaning" in the one place
that already owns it.

**3. New `apps/web/src/camera/CameraEnvelope.ts` — the soft spring-back.** A small class
in the CameraController mold (no React, owns its listeners, disposer):
- Constructed by `SceneController` with the `Viewer` and the `CameraController`;
  subscribes to `viewer.camera.moveEnd` (idle-edge, same event CameraController already
  uses for samples).
- On moveEnd, if `camera` has no active flight (`CameraController` exposes this via its
  `started/settled` events — track a boolean; do NOT spring back mid-flight): read
  `camera.positionCartographic`; clamp lon/lat into the soft rectangle and height into
  [ZOOM_FLOOR, ZOOM_CEILING]; read `camera.pitch`/`camera.heading` and clamp pitch into
  the band's range, heading toward 0 when |heading| > ~2°.
- If anything was clamped, issue one corrective flight: `camera.flyTo({ destination:
  Cartesian3.fromRadians(clampedLon, clampedLat, clampedHeight), orientation: { heading: 0,
  pitch: clampedPitch, roll: 0 }, duration: 0.7, easingFunction: minimumJerk })` —
  reusing the repo's `minimumJerk` from `design-system/motion`. Set a `correcting` flag
  so the flight's own moveEnd doesn't re-trigger, and let user `pointerdown` cancel it
  through the same `camera.cancelFlight()` path CameraController uses (spring-back must
  always lose to the user's hand; it simply re-arms on the next idle).
- Reduced-motion path: `setView` cut instead of flight, mirroring
  `CameraController.cutTo` + veil.
- Why moveEnd and not a per-frame clamp: a hard per-frame `setView` fights the inertia
  system and reads as jitter; the idle spring-back is the "cinematic" behavior the brief
  asks for and matches how the repo already treats the camera (flights own motion, users
  own interruptions).

**4. `CameraController` touch-ups.** Retune the three framing constants' pitches (above);
optionally export the active-flight boolean for CameraEnvelope instead of duplicating
event subscriptions. `flyToBasin`/`frameForecastPoint` stay untouched — programmatic
targets come from basin bboxes that are inside the envelope by construction.

**5. Tests.** `flight-math.test.ts` shows the house style; `envelope.ts` clamps are pure
functions (`clampToEnvelope(sample) → correction | null`) and unit-testable without a
Viewer — same pattern as `SemanticZoomController.test.ts`.

---

## NOT publicly possible in 1.144 (verified absent — do not chase)

1. **Per-tile imagery/terrain fade-in.** No fade code exists anywhere in the globe
   surface pipeline (grep of GlobeSurfaceTileProvider/GlobeSurfaceTile/TileImagery/
   ImageryLayer — only atmosphere distance fades). Not even a private knob. Open
   upstream: [cesium#8581](https://github.com/CesiumGS/cesium/issues/8581),
   [3d-tiles#343](https://github.com/CesiumGS/3d-tiles/issues/343).
2. **`progressiveResolutionHeightFraction` / `immediatelyLoadDesiredLevelOfDetail` on the
   globe** — `Cesium3DTileset`-only options [dts:30806, 30816]; zero hits in Globe.js /
   QuadtreePrimitive.js.
3. **Per-quadtree readiness thresholds / per-tile load callbacks.** `QuadtreePrimitive`'s
   queues and per-tile states are private (`_tileLoadQueueHigh` etc., no d.ts surface).
   The only public signals are `tileLoadProgressEvent` (aggregate count) and
   `globe.tilesLoaded`.
4. **Feathered `cartographicLimitRectangle` edge.** The shader does a binary `discard`
   [src:Shaders/GlobeFS.js:334-338]; no falloff parameter. Feathering requires the
   stacked-vignette recipe (1d).
5. **Per-tile tone normalization / seam blending.** ImageryLayer color controls are
   whole-layer uniforms; there is no per-tile shader hook. Fixing NAIP campaign seams
   in-client means a custom provider re-encoding every tile on canvas (possible, but a
   product decision the repo has already ruled out in BasemapProvider.ts:77 —
   "recolouring another agency's imagery per-tile is out of scope").
6. **Suppressing heading twist inside the tilt gesture.** tilt3D always performs the
   horizontal (heading) rotation with no flag to disable only that component — the
   vertical/horizontal split in rotate3D (rotateOnlyVertical/rotateOnlyHorizontal
   params) is internal. North-up therefore needs the moveEnd heading spring-back (or
   `enableTilt = false` outside the local band).
7. **A minimum tilt / forced-oblique constraint, or any pitch constraint on programmatic
   moves.** `maximumTiltAngle` is a one-sided cap on the user gesture only, and only
   while the gesture is increasing tilt.
8. **SSCC zoom limits applying to `setView`/`flyTo`.** `setView` bypasses them entirely;
   `flyToBoundingSphere` clamps only when it computes the range itself
   [src:Scene/Camera.js:3563-3586] — the repo always passes explicit ranges, so
   programmatic envelope discipline lives in CameraController/CameraEnvelope, not Cesium.
9. **A camera position-bounds rectangle.** No such public API; the custom soft-constraint
   controller is the supported pattern.
10. **Built-in animation/tween for ImageryLayer.alpha or grades.** `scene.tweens` is not
    public API (absent from Cesium.d.ts); animate uniforms from `scene.preRender`.
11. **Substituting replacement imagery from `errorEvent`/`TileProviderError`.** The error
    path supports retry semantics only; content substitution requires the discard policy
    (drop to ancestor) or a wrapping provider.
