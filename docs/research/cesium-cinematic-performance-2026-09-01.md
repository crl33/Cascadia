# Cinematic performance: real-GPU measurement + budget regime (Cesium 1.144, ordinary laptops)

Research date: 2026-09-01. Lens: PERF. Scope: `apps/web` (Cesium **1.144.0**, `@cesium/engine`
26.2.0, Playwright **1.62.1**, bundled Chromium **151.0.7922.34**; verified from
`apps/web/node_modules/{cesium,@cesium/engine,@playwright/test}/package.json` and
`~/Library/Caches/ms-playwright/`). Builds on
[cesium-continuity-camera-2026-08-31.md](cesium-continuity-camera-2026-08-31.md) (imagery/camera
API facts are not repeated here) and on [PERFORMANCE.md](../PERFORMANCE.md) §1–3, §9–10 whose
budgets were written as ASSUMPTION/INFERENCE before any real-GPU number existed.

**The one-line finding.** Until today every frame-time number in this repo came from headless
SwiftShader (`tests/e2e/playwright.config.ts:27-30`). Measured today on the owner's own MacBook Pro
(Intel UHD 630 integrated GPU + AMD Radeon Pro 5300M, 3072×1920 retina, macOS 15.7.9): the app as
built renders at **one quarter of native resolution** (Cesium's `useBrowserRecommendedResolution`
default pins `pixelRatio = 1.0`), and even so the integrated GPU spends **15.5 ms of GPU time per
idle frame** — 4× MSAA alone is half of it — while the discrete GPU spends 3.7 ms. A retina-native
backing store would put the integrated GPU at ~59 ms/frame (≈12 fps). No cinematic feature can be
added or budgeted until the tier regime below is in place; the harness that produced these numbers
runs on the owner's machine in ~45 s per configuration and needs no source change.

Verification legend:
- **[src:File.js:NN]** — `apps/web/node_modules/@cesium/engine/Source/<path>` line NN
- **[dts:NNNNN]** — `apps/web/node_modules/cesium/Source/Cesium.d.ts` line NNNNN
- **[pw:coreBundle.js:NN]** / **[pw:types.d.ts:NN]** — `apps/web/node_modules/playwright-core/lib/coreBundle.js` / `.../types/types.d.ts`
- **[repo:path:NN]** — a file in this repository
- **[measured]** — produced today by the harness in §7 on the owner's machine; raw JSON kept in the session scratchpad (`before.*.json`, `msaa-off.*.json`, `defines.*.json`)
- **[url]** — external document, fetched today
- **UNVERIFIED** — stated by a source not independently checked, or not checked at all

---

## 0. Measured baseline (owner's machine, scratch build of current `main`)

Scenario (identical in every run): boot to `loading-veil` detached → tile queue empty 0.8 s →
3 s idle → 14-step wheel zoom-in → settle → 24-step drag pan → settle → 14-step zoom-out → settle
→ 3 s idle. Stub API fixtures on :8000, `vite preview` of a scratch build on :4173 with COOP/COEP,
live USGS imagery, production R2 terrain proxied same-origin through Playwright's route layer
(the R2 domain sends no CORS header, checked with `curl -H Origin`). New-headless Chromium
(`channel: 'chromium'`), viewport 1280×800 CSS px. One run per configuration — these are
*indicative*; the harness protocol (§7) prescribes 5 runs and the median before any number
becomes a gate.

| Configuration | Backing store | GPU ms/frame idle p50 | GPU ms zoom-in p95 | rAF Δ zoom-in p95 (ms) | CPU rAF-callback p95 zoom-in (ms) | LoAF during zoom-in | `measureUserAgentSpecificMemory` after run | JS heap used |
|---|---|---|---|---|---|---|---|---|
| **Intel UHD 630**, as built (MSAA 4, pixelRatio 1) | 1280×800 | **15.5** | **36.5** | 116.7 | 110 | 11 | 188 MB | 119 MB |
| Intel UHD 630, MSAA off (harness patch) | 1280×800 | **7.95** | 14.1 | 66.7 | 56 | 5 | 160 MB | 105 MB |
| Intel UHD 630, retina-native proxy (2560×1600@1×), MSAA 4 | 2560×1600 | **58.7** | 89.7 | 166.7 | 157 | 35 | 366 MB | 99 MB |
| Intel UHD 630, retina-native proxy, MSAA off | 2560×1600 | 25.3 | 31.1 | 100 | 75 | 8 | 258 MB | 102 MB |
| AMD Radeon Pro 5300M, as built | 1280×800 | 3.73 | 7.8 | 66.7 | 60 | 7 | 185 MB | 99 MB |
| AMD Radeon Pro 5300M, retina-native proxy | 2560×1600 | 7.56 | 17.6 | 66.7 | 58 | 6 | 371 MB | 118 MB |

Other measured facts from the same runs [measured]:
- Cesium renders **every** rAF at idle (no camera motion): 34–37 draw calls and the GPU cost
  above, 60 times a second, because `requestRenderMode` is off (the app never sets it; see §4).
- Imagery requests to `basemap.nationalmap.gov` per scenario: 128–149 at the 1280×800 backing
  store, 237–417 at the retina-native proxy (a finer backing store raises the SSE-selected level).
- The globe fragment shader compiled with defines `GROUND_ATMOSPHERE`,
  `DYNAMIC_ATMOSPHERE_LIGHTING`, `APPLY_BRIGHTNESS/CONTRAST/SATURATION`, `LOG_DEPTH`,
  `TILE_LIMIT_RECTANGLE`, `INCLUDE_WEB_MERCATOR_Y`, `TEXTURE_UNITS` — and **not** `FOG`,
  `PER_FRAGMENT_GROUND_ATMOSPHERE`, `ENABLE_VERTEX_LIGHTING`. The app hides the sky atmosphere
  but is still paying for the *ground* atmosphere path in every globe fragment (§4).
- Retina-native proxy caveat: 2560×1600@1× gives the same backing pixel count Cesium would
  produce at 1280×800@2× with `useBrowserRecommendedResolution = false` (`width *= pixelRatio`
  [src:Widget/CesiumWidget.js:103-116]), but the CSS viewport differs, so tile selection can differ
  slightly. It is a proxy for cost, not a pixel-identical run.
- LoAF (long-animation-frame) counts on a GPU-saturated run are inflated by GPU back-pressure
  (the frame is long even when the rAF callback was short — compare the 2560 Intel row: LoAF 35,
  CPU p95 157 ms during zoom, but only 5.8 ms at idle). Read CPU-callback p95 and GPU p95 as the
  two independent axes; LoAF as the user-visible symptom.

---

## 1. Where the repo stands

- `tests/e2e/playwright.config.ts:27-30` [repo]: `--use-gl=angle --use-angle=swiftshader
  --enable-unsafe-swiftshader --ignore-gpu-blocklist`, `headless: true` (line 24) — every e2e and
  every "measured" checkpoint so far ran on SwiftShader. ~~Under the headless *shell* the rAF
  cadence is **33.3 ms p50 / 50 ms p95** with a trivial clear per frame [measured, §2], so nothing
  timed there says anything about a laptop.~~ **Corrected by the verification pass (§10):** the
  33.3/50 ms shell cadence did not reproduce — three re-runs of the same probe gave 16.66 ms p50
  and 16.67/16.67/33.33 ms p95. The shell is a *software rasteriser* (SwiftShader, no GPU timer
  query), which is reason enough that nothing timed there says anything about a laptop; it is
  **not** an inherently 30 Hz path.
- `docs/PERFORMANCE.md` §2 fixes `flight_frame_time` (`high` 60 fps target, p95 floors), idle
  frame cost ≤ 4 ms, `scene_memory` ≤ 500 MB heap, and admits "INFERENCE: GPU timer-query
  extensions exist but are not reliably available" (§2 row "GPU utilization guidance") and
  "INFERENCE for the hook name" for the frame sampler (§9). Both inferences are resolved below:
  the timer query **is** available on the real GPU in this Chromium, and the hook is the rAF
  callback that wraps `CesiumWidget.render()` [src:Widget/CesiumWidget.js:57-63].
- `SceneController.ts` [repo:apps/web/src/scene/SceneController.ts:97-106,114-116,133-135]:
  `preserveDrawingBuffer: true`, `tileCacheSize = 800`, `skyBox/skyAtmosphere.show = false`,
  `shadows: false`; no `requestRenderMode`, `msaaSamples`, `resolutionScale`,
  `useBrowserRecommendedResolution`, `globe.showGroundAtmosphere`, or `scene.fog` setting
  anywhere under `apps/web/src` (grep today).
- `store.ts:97` [repo]: `qualityTier: 'balanced'` default; `App.tsx:31-32` stamps it on the
  document and feeds the glass refraction quality — **the renderer receives no tier at all today.**

---

## 2. Getting the real GPU out of Playwright on macOS — verified by running it

Probe: a page created a WebGL2 context, read `WEBGL_debug_renderer_info`, `MAX_SAMPLES`, the
timer-query extension, `crossOriginIsolated` + `performance.measureUserAgentSpecificMemory()`
(page served with COOP/COEP through `page.route`), and 80 rAF deltas; `SystemInfo.getInfo` was
read on a browser-level CDP session. Same Chromium build (151.0.7922.34) in all modes [measured].

| Launch | Binary actually run (from `SystemInfo.getInfo().commandLine`) | `UNMASKED_RENDERER` | `MAX_SAMPLES` | `EXT_disjoint_timer_query_webgl2` | rAF Δ p50 / p95 | `measureUserAgentSpecificMemory` |
|---|---|---|---|---|---|---|
| `headless: true` (default) | `chromium_headless_shell-1234/…/chrome-headless-shell --headless --use-gl=angle --use-angle=swiftshader-webgl` (the shell binary appends the two GL switches itself; Playwright does not) | ANGLE (Google, Vulkan 1.3.0 (**SwiftShader** Device (Subzero))) | 4 | **absent** | ~~33.3 / 50 ms~~ **16.66 / 16.67–33.33 ms** on three verification re-runs (§10); the first reading did not reproduce | throws `SecurityError … is not available` even with `crossOriginIsolated === true` |
| `headless: true, args: ['--use-angle=metal']` | headless shell | ANGLE (AMD, ANGLE **Metal** Renderer: AMD Radeon Pro 5300M) | 8 | present | 16.7 / 16.7 | still throws `SecurityError` |
| **`headless: true, channel: 'chromium'`** (new headless) | `chromium-1234/chrome-mac-x64/Google Testing.app … --headless` | ANGLE (AMD, ANGLE Metal Renderer: AMD Radeon Pro 5300M) | **8** | **present** | **16.67 / 16.67** | **works** (37.5 MB on the probe page; buckets `DOM`, `Canvas`, `Shared`, `JavaScript`) |
| same + WebGL `powerPreference: 'low-power'` | same | ANGLE (**Intel**, ANGLE Metal Renderer: Intel(R) UHD Graphics 630) | 8 | present | 16.67 / 16.67 | works |
| `headless: false` | full Chromium, no `--headless` | AMD (Intel with `low-power`) | 8 | present | **20.0 / 21.0 ms** (window unfocused, on-screen) | works |

Mechanism, verified in Playwright's own bundle:
- Playwright *always* appends `--enable-unsafe-swiftshader` and, when `headless`, `--headless
  --hide-scrollbars --mute-audio …` [pw:coreBundle.js:43066-43072]; it never adds `--use-gl` /
  `--use-angle` / `--disable-gpu` (grep of `coreBundle.js` today; re-grepped across all of
  `playwright-core/lib` in §10 — zero hits). Which GPU you get is therefore
  decided by **which binary** runs: the separate `chromium-headless-shell` download (registry
  entries [pw:coreBundle.js:32403-32410]) initialises SwiftShader-on-Vulkan — its own process
  command line, read back through `SystemInfo.getInfo`, carries `--use-gl=angle
  --use-angle=swiftshader-webgl` that nobody passed in, i.e. the shell defaults itself to
  software GL [measured, §10]; the real Chromium
  binary selected by `channel: 'chromium'` initialises ANGLE-Metal on the hardware GPU even with
  `--headless`. Playwright's docs say the same in prose: new headless "is the real Chrome browser"
  [url: https://playwright.dev/docs/browsers]; Chrome's blog frames `--headless=new` (Chrome ≥ 112)
  versus `chrome-headless-shell` identically [url: https://developer.chrome.com/blog/chrome-headless-shell].
- `--use-angle=metal` on the shell also reaches the hardware GPU (row 2) but keeps the shell's
  restrictions (memory API throws). Chromium documents `use-angle` values and
  `enable-unsafe-swiftshader` in `ui/gl/gl_switches.cc` (`kUseANGLE` line 93, `kUseGL` 118,
  `kEnableUnsafeSwiftShader` 159, `kDisableGpuVsync` 77; fetched from chromium.googlesource.com
  today). The e2e config's `--use-gl=angle --use-angle=swiftshader` is therefore the *explicit*
  software path and stays correct for determinism; it must never be reused for timing.
- **Selecting the integrated GPU on a dual-GPU Mac.** Cesium sets `powerPreference =
  'high-performance'` unless told otherwise [src:Renderer/Context.js:57-58, doc at 460], so the
  app always lands on the discrete GPU where one exists. Passing `'low-power'` selects the Intel
  UHD 630 (rows 4–5). The harness injects it by wrapping `HTMLCanvasElement.prototype.getContext`
  in an init script (§7) — no source change, and the production default is untouched. This is
  the switch that turns the owner's workstation into the "ordinary laptop" of the brief.
  (Chrome 80 made the *browser* default `low-power` on dual-GPU machines [url:
  https://groups.google.com/g/webgl-dev-list/c/ZDms8ZQGl3o, UNVERIFIED beyond the search
  summary]; Cesium overrides it, which is why the override matters.)
- No Chromium switch was found that forces the low-power GPU for all contexts
  (`gl_switches.cc`, `gpu_switches.cc`, `content_switches.cc` grepped today); the WebGL
  `powerPreference` attribute is the supported lever.
- Headed mode is *worse* for timing than new headless on this machine (20 ms rAF cadence in an
  unfocused window; cause not investigated — UNVERIFIED whether focus or display sync). Use new
  headless for numbers; use headed only to look.

---

## 3. Instruments — what each one gives, and its verified availability

| Instrument | Gives | Availability (verified) | Notes |
|---|---|---|---|
| rAF wrapper around Cesium's render loop | frame-to-frame Δ (p50/p95/worst), CPU time inside `CesiumWidget.render()` | Cesium's default loop is exactly one `requestAnimationFrame(render)` callback that calls `widget.resize(); widget.render()` [src:Widget/CesiumWidget.js:50-63]; with `targetFrameRate` set it skips frames by `delta > 1000/targetFrameRate` [src:…:64-72] | Wrap `window.requestAnimationFrame` before the app boots (init script). Δ p95 is the honest "fps" number; PERFORMANCE.md's `flight_frame_time` maps to it directly. |
| `EXT_disjoint_timer_query_webgl2` (`TIME_ELAPSED_EXT` around the render callback) | **GPU ms per frame** | Present on both hardware GPUs in Chromium 151 (new headless and headed), absent on SwiftShader [measured, §2]. Spec: [url: https://registry.khronos.org/webgl/extensions/EXT_disjoint_timer_query_webgl2/]. History: disabled in 2021 for Rowhammer/Spectre concerns and re-enabled behind `chrome://flags/#enable-webgl-developer-extensions` in Canary 93 [url: https://groups.google.com/a/chromium.org/g/chromium-discuss/c/B9zBnC96t0I]; the thread itself notes it worked without the flag. Today it is exposed with **no flag** in Chrome-for-Testing 151. Whether stable consumer Chrome, Safari or Firefox expose it: UNVERIFIED here — treat it as a lab instrument, never as a runtime dependency. | One query in flight per target; read `QUERY_RESULT_AVAILABLE` a few frames later; discard the batch when `GPU_DISJOINT_EXT` is set. Cesium exposes no timer-query support of its own (grep of `Renderer/` for `disjoint`/`TIME_ELAPSED`: zero hits). |
| Draw-call counter (prototype wrap of `drawElements*`/`drawArrays*`) | draws per frame | trivial | 34–37 at rest on the home view, 77–94 at the retina proxy [measured]. |
| `PerformanceObserver` `long-animation-frame` | frames > 50 ms with `blockingDuration`, `renderStart`, `scripts[]` attribution | `supportedEntryTypes` includes it in Chromium 151 [measured]; semantics [url: https://developer.mozilla.org/en-US/docs/Web/API/Performance_API/Long_animation_frame_timing] | Better than `longtask` because it attributes the script; inflated by GPU back-pressure (§0). |
| `PerformanceObserver` `longtask` | main-thread tasks > 50 ms | supported [measured] | Keep for Safari/Firefox parity. |
| `performance.measureUserAgentSpecificMemory()` | process-attributed bytes with `breakdown[].types` (`DOM`, `JavaScript`, `Canvas`, `Shared`) | Requires secure + cross-origin-isolated context [url: https://developer.mozilla.org/en-US/docs/Web/API/Performance/measureUserAgentSpecificMemory]; **works in new headless and headed, throws in the headless shell even when isolated** [measured] | The `Canvas` bucket is the only standard signal that moved with the WebGL backing store (188 → 366 MB when the backing store quadrupled) — observed behaviour, not a spec guarantee; MDN does not document GPU inclusion. Needs `Cross-Origin-Opener-Policy: same-origin` + `Cross-Origin-Embedder-Policy: credentialless` on the *preview* server (Vite `preview.headers` [url: https://vite.dev/config/preview-options.html]); `credentialless` keeps cross-origin tile fetches working. Never ship these headers to production without a separate decision. |
| CDP `Performance.enable` + `Performance.getMetrics` | `JSHeapUsedSize`, `JSHeapTotalSize`, `Nodes`, … | [url: https://chromedevtools.github.io/devtools-protocol/tot/Performance/] (metric *names* come from the live result, the doc only types them) [measured] | No isolation needed. Matches PERFORMANCE.md §2 "Playwright via DevTools protocol heap metrics". |
| CDP `SystemInfo.getInfo` | `gpu.devices[]` (vendor/device ids), `auxAttributes`, `featureStatus.webgl2`, `commandLine` | Browser-level session only — `context.newCDPSession(page)` fails with "only supported on the browser target"; use `browser.newBrowserCDPSession()` [measured]; fields [url: https://chromedevtools.github.io/devtools-protocol/tot/SystemInfo/] | The provenance stamp for every run: which binary, which GPU. |
| Chrome tracing | compositor/GPU-side frame pipeline | `browser.startTracing(page, { categories, path, screenshots })` [pw:types.d.ts:11532-11544]; CDP `Tracing.start` takes `categories`/`traceConfig.includedCategories`, delivers `dataCollected` then `tracingComplete` [url: https://chromedevtools.github.io/devtools-protocol/tot/Tracing/] | Category names for the frame pipeline (`disabled-by-default-devtools.timeline.frame`, `benchmark`, `viz`, `cc`, `gpu`; `PipelineReporter` events for dropped frames) are reported by community sources and Chromium's jank docs (search results today) — **UNVERIFIED by parsing a trace in this pass**. The harness records a trace as a supplementary artifact; nothing in the budget table depends on it. |
| Cesium `FrameRateMonitor.fromScene(scene)` | `lastFramesPerSecond`, `lowFrameRate`/`nominalFrameRate` events; defaults `samplingWindow` 5 s, `quietPeriod` 2 s, `warmupPeriod` 5 s, floors 4/8 fps [src:Scene/FrameRateMonitor.js:19-29,154-157] | public [dts:34428] | The right *runtime* auto-downgrade trigger (PERFORMANCE.md §3 "3 s under the floor") — set `minimumFrameRateAfterWarmup` to the tier floor and listen to `lowFrameRate`. Sampling windows are too coarse for lab numbers. |
| Cesium `scene.debugShowFramesPerSecond` / `PerformanceDisplay` | on-screen fps + ms; shows "(throttled)" when `requestRenderMode` is on [src:Scene/PerformanceDisplay.js:52-67; Scene.js:4427] | public [dts:44104] | Eyeball tool only. |
| `globe.tileLoadProgressEvent` → `data-tiles-pending` | settle detection | already wired [repo:SceneController.ts:243-270] | The harness's settle criterion (queue empty ≥ 0.8 s). |

---

## 4. Cesium's own performance knobs — verified against 1.144 source, with the app's current state

| Knob | Default / current | What it really does (source) | Measured or expected effect here |
|---|---|---|---|
| `useBrowserRecommendedResolution` | default **true** [src:Widget/CesiumWidget.js:276-277]; app: untouched | `pixelRatio = useBrowserRecommendedResolution ? 1.0 : window.devicePixelRatio; pixelRatio *= resolutionScale; canvas.width = clientWidth * pixelRatio` [src:…:91-116] | **The app renders 1280×800 device pixels on a 2× display** (harness read `canvas.width === 1280` at DPR 2 [measured]). Every retina laptop sees a bilinear-upscaled globe. This is the single largest "cinematic" defect and the single largest budget lever: ×4 pixels = ×3.8 GPU time on Intel, ×2.0 on AMD [measured, §0]. |
| `resolutionScale` | 1.0 [dts:47920; src:…:291,761-775] | multiplies the pixel ratio; setting it forces a canvas resize | The tier lever. `useBrowserRecommendedResolution=false` + `resolutionScale` ∈ {1.0, 0.75, 0.5} gives native, 0.56×, 0.25× pixel counts. |
| `requestRenderMode` + `maximumRenderTimeChange` | false / 0.0 [dts:43949-43950; src:Scene/Scene.js:681,698]; app: untouched | A frame renders only if `_renderRequested \|\| cameraChanged \|\| logDepth/hdr dirty \|\| morphing`, or the clock moved more than `maximumRenderTimeChange` [src:Scene.js:4590-4606]. Renders are auto-requested after every completed request (`RequestScheduler.requestCompletedEvent`), worker task (`TaskProcessor.taskCompletedEvent`), `imageryLayersUpdatedEvent`, `terrainProviderChanged` [src:Scene.js:702-710,806-815]; entity/primitive edits need `scene.requestRender()` (Cesium blog: idle CPU 25.1 % → 3.0 % on an i7 laptop [url: https://cesium.com/blog/2018/01/24/cesium-scene-rendering-performance/]). | At idle the app burns 15.5 ms GPU + 2–4 ms CPU per frame at 60 Hz on Intel for nothing [measured]. With request-render on, idle GPU cost → ~0, which also hands the compositor the headroom the glass surfaces need (the liquid-glass research already found five backdrop-filter surfaces can stall the compositor). `SceneController` already calls `requestRender()` in the places that change the scene ([repo:SceneController.ts:187,397,474]); layers that animate must do the same or use `maximumRenderTimeChange`. |
| `targetFrameRate` | undefined [src:…:411-412, 705-717] | frame-skipping in the default loop [src:…:64-72] | A BALANCED/LOW cap at 30 turns a 33 ms p95 into a steady 33 ms — smoother than 16/33 alternation. |
| `msaaSamples` | **4**, assigned in the constructor **without** the `maximumSamples` clamp [src:Scene.js:251]; setter clamps [src:…:1701-1710]; requires WebGL2 (`context.msaa === webgl2` [src:Renderer/Context.js:652-655]); `MAX_SAMPLES` = 8 on both GPUs, 4 on SwiftShader [measured] | multisampled globe-depth, OIT and scene framebuffers [src:Scene.js:3941-3947,3957-3963,3977-3982] | **Half of the Intel frame**: idle 15.5 → 7.95 ms, zoom p95 36.5 → 14.1 ms at 1280×800; 58.7 → 25.3 ms at the retina proxy [measured, harness `--msaa=off` which single-samples the renderbuffers]. Also note the context is created with `antialias: true` [src:Context.js:142,457] on top of Cesium's own MSAA — redundant; `contextOptions.webgl.antialias=false` is free (UNMEASURED). |
| `tileCacheSize` | 100 [src:Scene/Globe.js:116; QuadtreePrimitive.js:120]; app: **800** | a **count**, not bytes: `TileReplacementQueue.trimTiles(max)` frees LRU tiles that were not rendered this frame [src:Scene/TileReplacementQueue.js:25-53; QuadtreePrimitive.js:1326]; tiles used last frame are never trimmed | Memory bound per cached tile: imagery texture RGBA 256² = 262 KB (`hasAlphaChannel` defaults true on `UrlTemplateImageryProvider` [src:Scene/UrlTemplateImageryProvider.js:237] → `PixelFormat.RGBA` [src:Scene/ImageryLayer.js:1211-1216]) + mipmaps ×1.33 (generated when LINEAR/LINEAR and power-of-two [src:ImageryLayer.js:1286-1327]) ≈ **350 KB per imagery tile per layer**, and up to two textures per tile while the Web-Mercator source and the reprojected geographic texture coexist [src:ImageryLayer.js:1363-1412; Imagery.js:70-77]. With two textured layers (base plate + main) an 800-tile cache bounds at roughly 800 × 2 × 350 KB ≈ **560 MB** of texture memory before terrain vertex arrays — consistent with the 185 → 366 MB `Canvas`-inclusive measurement moving with resolution. Tier the count: 800 is an ULTRA/HIGH number. *Verification caveats (§10):* this is an estimate, not a strict bound — `tileCacheSize` counts quadtree (terrain) tiles, imagery textures are reference-counted and shared between them, and a terrain tile can reference more than one imagery tile per layer; the reprojection (and therefore the second texture) only happens when the tile's pixel spacing exceeds 1e-5 rad [src:ImageryLayer.js:1379-1384] — coarse levels only, roughly z ≤ 11 for 256-px tiles — and once it has happened both textures persist until the `Imagery` is released [src:Imagery.js:70-77], not merely "while" they coexist; and `PixelFormat.RGB` (`hasAlphaChannel:false`) is commonly padded to 4 bytes by drivers, so it is UNVERIFIED that it would save memory. |
| `Globe.showGroundAtmosphere` | **true** on WGS84 [src:Scene/Globe.js:203]; app: untouched (only `skyAtmosphere.show=false`) | compiles `GROUND_ATMOSPHERE` (+`DYNAMIC_ATMOSPHERE_LIGHTING`) into every globe shader [src:Scene/GlobeSurfaceShaderSet.js:340-347; GlobeSurfaceTileProvider.js:2399-2422,2548]; per-fragment variant only when camera distance > `nightFadeOutDistance` = π/2·R ≈ 10 Mm [src:Globe.js:282] — never inside the 1.25 Mm zoom ceiling | Observed compiled in [measured, §0]. The app pays a per-vertex scattering term it does not display. Setting it false is a free win and matches the "no atmosphere" decision already made. UNMEASURED delta; likely small but non-zero on Intel. *Precision (§10):* `DYNAMIC_ATMOSPHERE_LIGHTING` is pushed independently of `showGroundAtmosphere` (`Globe.dynamicAtmosphereLighting` defaults true [src:Globe.js:185]; [src:GlobeSurfaceShaderSet.js:331-338]) and its shader branches are guarded by `ENABLE_DAYNIGHT_SHADING`/`ENABLE_VERTEX_LIGHTING` [src:Shaders/GlobeVS.glsl:247; GlobeFS.glsl:86], so with `enableLighting=false` it is inert; only the `GROUND_ATMOSPHERE` term is live. |
| `scene.fog` | `enabled` true, `density` 0.0006, `screenSpaceErrorFactor` 2.0, `minimumBrightness` 0.03 [src:Scene/Fog.js:25-89] | `FOG` define only when `CesiumMath.fog(tileDistance, density) > 1e-3` [src:GlobeSurfaceTileProvider.js:2797-2801]; fog also *raises* SSE for distant tiles (fewer loads) [src:GlobeSurfaceTileProvider.js:707] | `FOG` was **not** compiled during the scenario [measured] — at nadir the tile distances never reach the threshold. Cost ≈ 0 today; its SSE relaxation is a LOW-tier ally at oblique pitches only, which the doctrine forbids. |
| `logarithmicDepthBuffer` | `Scene.defaultLogDepthBuffer = true` && fragmentDepth [src:Scene.js:193,796] | `LOG_DEPTH` observed [measured]; fewer frustums | Leave on. |
| `verticalExaggeration` | 1.0 [src:Scene.js:398] | baked into tile *mesh creation* (`createMeshOptions.exaggeration` [src:Scene/GlobeSurfaceTile.js:992-994]) → changing it rebuilds meshes in workers | Zero per-frame cost; a one-off CPU/worker burst on change. Not a nadir-map feature anyway (relief only reads at oblique pitch). |
| `preserveDrawingBuffer` | app: **true** [repo:SceneController.ts:105] for TransitionPlate/deep-link capture | forces the browser to keep the back buffer readable | UNMEASURED cost on ANGLE-Metal. A/B is one harness flag away (patch attrs in the init script). |
| `Globe.showWaterEffect` | true [src:Globe.js:303] | needs `terrainProvider.hasWaterMask` [src:Globe.js:996-1001] | The production `layer.json` declares `extensions: ["octvertexnormals"]` only (fetched today) — **no water mask exists**, the effect is inert here. |
| `postProcessStages.fxaa/ao/bloom` | all **disabled** by default [src:Scene/PostProcessStageCollection.js:53-55] | any enabled stage (or HDR) switches the whole frame into the `sceneFramebuffer` + post-process path [src:Scene.js:3970-3990] | Zero today. Every stage added is at least one full-screen pass at backing resolution — see §5. |

---

## 5. Cost class of each cinematic feature (Cesium 1.144, nadir map, this app)

"Passes" = full-screen fragment passes at the backing-store resolution; on the Intel GPU one such
pass is the unit the tier table is built on (a 2560×1600 MSAA resolve was ~33 ms of the 59 ms
frame [measured, §0]). Cost classes: **A** ≈ 0 per frame · **B** < 1 ms on Intel at 1280×800 ·
**C** 1–4 ms · **D** > 4 ms or unbounded · **X** structurally unfit for a pure-nadir map.

| Feature | Mechanism (verified) | GPU | CPU/main thread | Memory | Class | Fit with "nothing breaks the illusion" |
|---|---|---|---|---|---|---|
| Ground atmosphere (currently on) | per-vertex scattering define [src:GlobeSurfaceShaderSet.js:340-347] | extra ALU in every globe fragment/vertex | 0 | 0 | B–C | Turn **off**; it is not displayed and contradicts the black-void domain edge. |
| Sky atmosphere | `SkyAtmosphere` [dts:45200], `perFragmentAtmosphere` false [src:Scene/SkyAtmosphere.js:60]; app off | one full-sphere pass | 0 | 0 | C | Off by doctrine (no horizon at nadir). |
| Fog | §4 | 0 at nadir | 0 | 0 | A | Inert. |
| Lighting (`enableLighting`) + vertex normals | `ENABLE_VERTEX_LIGHTING` when `hasVertexNormals` [src:GlobeSurfaceShaderSet.js:322-327]; R2 terrain ships `octvertexnormals` | extra ALU per fragment | 0 | 0 | B | Would make relief legible at nadir — the only "light" lever available; `dynamicAtmosphereLighting` must stay off. Candidate for HIGH+ only after a measured A/B. |
| Shadows | `ShadowMap` default `size` 2048, 4 cascades, `maximumDistance` 5000 m, `softShadows` false [src:Scene/ShadowMap.js:68-75,283]; app `shadows:false` | +4 depth passes of the terrain per frame, 4×2048² depth | 0 | 4 × 2048² × 4 B ≈ 64 MB | D | X — at nadir a shadow is a dark smear on flood plains; never. |
| FXAA | 1 pass [src:PostProcessStageLibrary.js:611] | 1 pass | 0 | 1 RT | C | Alternative to MSAA on BALANCED if aliasing is visible after MSAA-off (UNMEASURED). |
| Bloom | contrast/bias → blurX → blurY → composite = **4 passes** [src:PostProcessStageLibrary.js:388-470; blur 119-133] | 4 passes + scene RT | 0 | 3–4 RTs | D | Bloom on satellite imagery blows out snowfields and rivers; the design language's glow lives in the DOM glass, not the globe. ULTRA opt-in at most, `glowOnly` never. |
| Depth of field | blur (2) + dof composite (1) = **3 passes** + depth texture; `isDepthOfFieldSupported` needs `depthTexture` [src:PostProcessStageLibrary.js:141-190,207] | 3 passes | 0 | 3 RTs | D | X at nadir — every point is at the same depth; a tilt-shift look is exactly the miniature illusion the doctrine forbids. |
| Ambient occlusion | ~~generate + blur + composite~~ **generate + composite = 2 passes** (`czm_ambient_occlusion_generate` → `czm_ambient_occlusion_composite`; there is no blur stage in 1.144 — corrected in §10) [src:PostProcessStageLibrary.js:496-520,580-586]; needs `depthTexture` [src:…:600-602] | 2 passes, the generate pass samples depth `directionCount × stepCount` = 8 × 32 times per fragment | 0 | 2 RTs | D | X — no vertical geometry to occlude. |
| HDR + tonemapping | `highDynamicRange` requires `depthTexture && (colorBufferFloat \|\| colorBufferHalfFloat)` [src:Scene.js:1650-1685]; float scene framebuffer + tonemap stage [src:Scene.js:3970-3985; PostProcessStageCollection.js:328-377] | float-buffer bandwidth on every draw + 1 pass | 0 | ×2 RT bytes | D | Only meaningful with lighting/sun; off. |
| Clouds | `CloudCollection` generates a noise texture (`noiseDetail` 16 → slices packed `textureSliceWidth²/4 × textureSliceWidth·4` [src:Scene/CloudCollection.js:146,700-729]) and ray-marches per cloud billboard | per-cloud raymarch | 0 | noise texture | D | X — occludes the instrument; weather is data (MRMS/QPF rasters), never décor. |
| Particle systems | CPU-updated billboard pool [src:Scene/ParticleSystem.js:138,522-575] | billboards | per-particle JS per frame | pool | C–D (count-bound) | X for rain/snow; a bounded pool (< 200) is acceptable only for a data-driven marker pulse, labelled `cinematic`. |
| Water effect | needs water mask [src:Globe.js:996-1001] | — | — | — | A (inert) | No mask in the R2 pyramid. |
| Terrain exaggeration | mesh rebuild [src:GlobeSurfaceTile.js:992] | 0 | worker burst | 0 | A / burst | Illegible at nadir; off. |
| MSAA 4× (currently on) | §4 | ~½ of Intel frame [measured] | 0 | ×4 depth/colour samples | D on Intel, C on AMD | The lever with the best cinematic-per-ms ratio on discrete GPUs, the first to cut on integrated ones. |
| Native-resolution backing store (currently off) | §4 | ×3.8 on Intel, ×2 on AMD [measured] | tile decode ×~2 (requests 128 → 237–417 [measured]) | `Canvas` 188 → 366 MB [measured] | D | The *actual* cinematic upgrade the owner will see; gate it by tier, never by default. |
| Glass surfaces (`backdrop-filter`) | DOM compositor, not Cesium | compositor GPU, unmeasured here | 0 | 0 | C–D per surface [liquid-glass research: 5 three-pass surfaces stalled capture] | Competes with Cesium for the same GPU; a reason for `requestRenderMode` at every tier. |
| TransitionPlate capture | `drawImage` of the WebGL canvas [repo:TransitionPlate.ts:108-134] | one readback per gesture end | one copy | one 2D canvas at backing size (8.2 MB at 1280×800, 16 MB at 2560×1600) | B (event-bound) | Fine; scales with backing store. |

---

## 6. Quality-tier gating table with concrete budgets

Budgets are per **tier**, measured with the §7 harness on the owner's machine (Intel row =
"ordinary laptop"), and phrased as p95 of the scenario phases in §0 unless stated. A tier is
*allowed* on a machine when the tier's own budget holds for 5-run medians. Names keep
`ultra / high / balanced / low` (PERFORMANCE.md §3, store `qualityTier`).

| | ULTRA | HIGH | BALANCED | LOW |
|---|---|---|---|---|
| Reference class (measured anchor) | discrete GPU at native DPR (AMD 5300M: idle 7.6 ms, zoom p95 17.6 ms at 2560×1600 [measured]) | discrete GPU or strong integrated (Apple M-class: UNMEASURED); AMD at native DPR fits | **Intel UHD 630 class**: 1280×800 MSAA-off idle 7.95 ms, zoom p95 14.1 ms [measured] | anything that fails BALANCED, tablets, SwiftShader-class |
| Backing store | native (`useBrowserRecommendedResolution=false`, `resolutionScale` 1.0) | native, `resolutionScale` 1.0 (0.75 if the probe says so) | `resolutionScale` chosen so the backing store ≤ **2.1 MP** (1280×800 at 2× → 0.5; a 1440×900 2× laptop → 0.75) | backing ≤ 1.2 MP (`resolutionScale` ≤ 0.5 on 2× displays) |
| `msaaSamples` | 4 (8 opt-in; `MAX_SAMPLES` 8 measured) | 4 | **1** (2 only if measured ≤ 10 ms idle) | 1 |
| `requestRenderMode` | on, `maximumRenderTimeChange` per animated layer | on | on | on, `maximumRenderTimeChange = Infinity` (nothing time-driven) |
| `targetFrameRate` | — | — | 30 if p95 > 20 ms after resolution/MSAA cuts | 30 |
| `tileCacheSize` | 800 | 600 | 400 | 200 |
| `globe.showGroundAtmosphere` | off (all tiers) | off | off | off |
| Lighting with vertex normals | allowed after A/B | allowed after A/B | off | off |
| Post-process (FXAA / bloom / DOF / AO / HDR) | FXAA off (MSAA), bloom **opt-in only**, DOF/AO/HDR never | none | FXAA only if MSAA-off aliasing is visible and it fits | none |
| Clouds / particles / shadows / exaggeration | never (X in §5) | never | never | never |
| Raster scientific layers (existing PERFORMANCE §2 cap) | 4 | 3 | 2 | 1 |
| **Frame budget** — rAF Δ p95 during a gesture / during refine / idle | 16.7 / 16.7 / 16.7 ms | 16.7 / 20 / 16.7 | 33.3 / 33.3 / 16.7 | 50 / 50 / 33.3 |
| **GPU budget** — timer-query ms p95 during gesture / p50 idle (before request-render) | ≤ 12 / ≤ 8 | ≤ 13 / ≤ 9 | ≤ 14 / ≤ 9 | ≤ 25 / ≤ 16 |
| CPU rAF-callback p95 during a gesture | ≤ 50 ms | ≤ 50 ms | ≤ 60 ms | ≤ 80 ms |
| LoAF count per gesture phase (≈ 2 s) | ≤ 3 | ≤ 4 | ≤ 6 | ≤ 10 |
| **GPU memory** (texture bound from §4 math; `Canvas`-inclusive `measureUserAgentSpecificMemory` as the proxy) | ≤ 700 MB bound / ≤ 450 MB measured | ≤ 560 MB / ≤ 400 MB | ≤ 350 MB / ≤ 260 MB | ≤ 200 MB / ≤ 180 MB |
| **RAM** — JS heap used (CDP) | ≤ 250 MB | ≤ 250 MB | ≤ 200 MB | ≤ 150 MB |
| **Requests** — imagery tiles per §0 scenario (boot + zoom + pan + zoom) | ≤ 450 | ≤ 350 | ≤ 250 | ≤ 150 |
| Today's build, as measured | AMD native: rAF ✓, GPU ✓ (17.6 zoom p95 > 12 — fails ULTRA gesture GPU, passes HIGH) | AMD @1×: ✓ | Intel @1× **fails** (MSAA on → 36.5 ms zoom p95; 15.5 idle); passes only with MSAA off | Intel retina-native MSAA-on: 59 ms idle — fails even LOW |

Why these numbers: the frame budgets are PERFORMANCE.md §2's targets/floors restated per tier
(60 target, 30 floor for `high`/`balanced`, 20 for `low`); the GPU-ms columns are set so that
GPU + CPU-callback p95 leave ≥ 3 ms for the compositor and glass at 60 Hz (BALANCED renders at
30 Hz cadence when it must, so its 14 ms GPU column is a 60 Hz *median* target with a 33 ms p95
floor); the memory columns come from the §4 texture math times the tier's `tileCacheSize` and
layer count, sanity-checked against the two measured `Canvas`-inclusive readings; the request
columns bracket the measured 128–149 (1×) and 237–417 (2×) tile counts with the existing
"≤ 350 per flight" row. Everything in this table is a first calibration from one machine and
becomes a gate only after the 5-run protocol in §7 has been run on it twice (before/after).

**Auto-detection** (replaces PERFORMANCE.md §3's synthetic "probe scene"): after
`onGroundComposed`, run 90 idle frames with the timer query where available and classify by GPU
p50 (≤ 5 ms → ULTRA-capable, ≤ 9 → HIGH, ≤ 16 → BALANCED, else LOW) *at the native backing
store*; without a timer query (Safari/Firefox — UNVERIFIED availability) fall back to rAF Δ p95
over the same window (≤ 17 → HIGH, ≤ 34 → BALANCED, else LOW). Then arm
`FrameRateMonitor.fromScene` with `minimumFrameRateAfterWarmup` = the tier floor for the runtime
downgrade. The user override in `SettingsMenu` stays.

---

## 7. The measurement harness — design and the runnable script

**Where it lives (proposal).** `tests/perf/perf-harness.mjs`, `tests/perf/vite.perf.config.mjs`,
npm script `perf:owner` in `apps/web/package.json`. It is *not* a Playwright Test spec: it needs
one browser per run, explicit GPU selection and a JSON artifact, and it must never run under the
SwiftShader e2e config. CI may run it on a self-hosted runner for *relative* regression
(PERFORMANCE.md §10 already says CI FPS is not comparable); absolute gates come from the owner's
machine.

**Inputs.** `--url` (preview on :4173 — the stub API's CORS allowlist is `:5173`/`:4173` only
[repo:apps/web/dev/stub-api.mjs:13]; a run on any other port silently loses every vector layer),
`--gpu=low-power|high-performance` (integrated vs discrete), `--viewport=WxH --dpr=N`,
`--mode=newheadless|headed`, `--msaa=off` (A/B lever), `--terrain=<origin>/terrain/v1`
(same-origin proxy of production terrain), `--label=before|after`.

**Instrumentation** (all in one `page.addInitScript`, installed before the app boots; nothing in
`apps/web/src` changes):
1. wrap `HTMLCanvasElement.prototype.getContext` → inject `powerPreference`, capture the GL,
   grab `EXT_disjoint_timer_query_webgl2` and `WEBGL_debug_renderer_info`, count draw calls,
   record `#define`s of any shader that references `u_dayTextures` (the globe shader);
2. wrap `window.requestAnimationFrame` → per frame `{t, cpuMs, draws, gpuMs}` with a
   `TIME_ELAPSED_EXT` query around the callback, resolved asynchronously, discarded on
   `GPU_DISJOINT_EXT`;
3. `PerformanceObserver` for `long-animation-frame` and `longtask`;
4. `window.__perf.mark(name)` phase markers.
Outside the page: `page.on('request')` per host, CDP `Performance.getMetrics` heap, browser-level
`SystemInfo.getInfo` for the provenance stamp, optional `browser.startTracing`.

**Scenario.** As §0 (boot → idle → zoom-in → settle → pan → settle → zoom-out → settle → idle),
settle = `[data-tiles-pending="0"]` for 0.8 s (max 20 s). Add named flights later
(`orbital → basin:skagit`, `basin → fp:nwps:MVEW1`) by clicking search results, the way
`skagit-flight.spec.ts` does.

**Protocol.** 5 runs per configuration, first discarded, median reported; a configuration = (gpu,
viewport@dpr, msaa, label). Before/after = same configuration, two labels, diff of the medians.
The matrix that must hold for a cinematic change to merge: Intel@1280×800@2 with the tier's
settings, Intel retina proxy, AMD retina proxy.

**Outputs.** `<label>.<gpu>.<mode>.<WxH@dpr>.json` with `info` (renderer, defines, canvas size),
heap before/after, `measureUserAgentSpecificMemory`, requests by host, and per-phase
`{frames, rafDeltaMs{p50,p95,max}, cpuCbMs{…}, gpuMs{…,n}, drawCalls, loaf{n,maxMs,blockingMs}}`;
a console table for the eye.

**Preview config** (COOP/COEP so the memory API works; scratch build dir, never `dist/`):
```js
// tests/perf/vite.perf.config.mjs
export default {
  preview: { port: 4173, strictPort: true,
    headers: { 'Cross-Origin-Opener-Policy': 'same-origin', 'Cross-Origin-Embedder-Policy': 'credentialless' } },
  build: { outDir: '<scratch>/dist-perf' },
};
```
Run: `VITE_API_BASE=http://localhost:8000 VITE_DOMAIN_WARM=off npx vite build --outDir <scratch>/dist-perf`
· `node dev/stub-api.mjs` · `npx vite preview --config tests/perf/vite.perf.config.mjs` ·
`node tests/perf/perf-harness.mjs --url=http://localhost:4173/ --gpu=low-power --viewport=1280x800 --dpr=2 --label=before --terrain=https://cascadia.papsukkal.com/terrain/v1`.
(`VITE_DOMAIN_WARM=off` keeps the 260-tile boot warm out of the numbers; run a second
configuration with it on when the warm itself is the subject.)

**The script** (as run today; trimmed only of argument parsing and the console table):
```js
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
// args: url, gpu, viewport, dpr, mode, label, msaa, terrain  (see above)
const browser = await chromium.launch(mode === 'headed' ? { headless: false } : { headless: true, channel: 'chromium' });
const context = await browser.newContext({ viewport: { width: vw, height: vh }, deviceScaleFactor: dpr });
const page = await context.newPage();

await page.addInitScript(({ forcedPower, msaaOff }) => {
  const P = (window.__perf = { frames: [], marks: [], loaf: [], longtasks: [], gl: null, ext: null, renderer: null, drawCalls: 0, globeDefines: new Set() });
  const getContext = HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext = function (type, attrs) {
    if (type !== 'webgl2' && type !== 'webgl') return getContext.call(this, type, attrs);
    attrs = { ...(attrs ?? {}), powerPreference: forcedPower };          // integrated vs discrete GPU
    if (msaaOff) attrs.antialias = false;
    const gl = getContext.call(this, type, attrs);
    if (gl && msaaOff) {                                                  // A/B lever: single-sample every MS renderbuffer
      const og = gl.getParameter.bind(gl);
      gl.getParameter = (p) => (p === gl.MAX_SAMPLES ? 0 : og(p));
      gl.renderbufferStorageMultisample = (target, _s, fmt, w, h) => gl.renderbufferStorage(target, fmt, w, h);
    }
    if (gl && !P.gl) {
      P.gl = gl; P.ext = gl.getExtension('EXT_disjoint_timer_query_webgl2');
      const dbg = gl.getExtension('WEBGL_debug_renderer_info');
      P.renderer = dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
      const ss = gl.shaderSource.bind(gl);
      gl.shaderSource = (sh, src) => { if (src.includes('u_dayTextures')) for (const m of src.matchAll(/^#define\s+(\w+)/gm)) P.globeDefines.add(m[1]); return ss(sh, src); };
      for (const m of ['drawElements', 'drawArrays', 'drawElementsInstanced', 'drawArraysInstanced']) { const o = gl[m]; gl[m] = function (...a) { P.drawCalls++; return o.apply(this, a); }; }
    }
    return gl;
  };
  const pending = []; let active = false; const raf = window.requestAnimationFrame;
  window.requestAnimationFrame = (cb) => raf.call(window, (t) => {
    const gl = P.gl, ext = P.ext, rec = { t, cpuMs: 0, gpuMs: null, draws: 0 }, d0 = P.drawCalls; let q = null;
    if (gl && ext && !active) { q = gl.createQuery(); gl.beginQuery(ext.TIME_ELAPSED_EXT, q); active = true; }
    const c0 = performance.now();
    try { cb(t); } finally { rec.cpuMs = performance.now() - c0; rec.draws = P.drawCalls - d0;
      if (q) { gl.endQuery(ext.TIME_ELAPSED_EXT); active = false; pending.push({ q, rec }); } P.frames.push(rec); }
  });
  setInterval(() => { const gl = P.gl, ext = P.ext; if (!gl || !ext) return; const disjoint = gl.getParameter(ext.GPU_DISJOINT_EXT);
    while (pending.length && gl.getQueryParameter(pending[0].q, gl.QUERY_RESULT_AVAILABLE)) { const { q, rec } = pending.shift();
      rec.gpuMs = disjoint ? null : gl.getQueryParameter(q, gl.QUERY_RESULT) / 1e6; gl.deleteQuery(q); } }, 50);
  new PerformanceObserver((l) => l.getEntries().forEach((e) => P.loaf.push({ t: e.startTime, d: e.duration, blocking: e.blockingDuration }))).observe({ type: 'long-animation-frame', buffered: true });
  new PerformanceObserver((l) => l.getEntries().forEach((e) => P.longtasks.push({ t: e.startTime, d: e.duration }))).observe({ type: 'longtask', buffered: true });
  P.mark = (name) => P.marks.push({ name, t: performance.now() });
}, { forcedPower: gpu, msaaOff: msaa === 'off' });

if (terrain) await page.route('**/terrain/v1/**', async (route) => {            // same-origin proxy of R2 terrain
  const u = new URL(route.request().url()); const target = terrain + u.pathname.replace(/^.*\/terrain\/v1/, '') + u.search;
  try { await route.fulfill({ response: await route.fetch({ url: target }) }); } catch { await route.abort(); } });
const requests = {}; page.on('request', (r) => { const h = new URL(r.url()).host; requests[h] = (requests[h] ?? 0) + 1; });
const cdp = await context.newCDPSession(page); await cdp.send('Performance.enable');
const heap = async () => { const { metrics } = await cdp.send('Performance.getMetrics'); const g = (n) => metrics.find((m) => m.name === n)?.value; return { usedMB: g('JSHeapUsedSize') / 1048576, totalMB: g('JSHeapTotalSize') / 1048576 }; };
const mark = (n) => page.evaluate((n) => window.__perf.mark(n), n);
const settled = async (label, maxMs = 20000) => { await mark(`${label}:settle-start`); const t0 = Date.now(); let zero = null;
  while (Date.now() - t0 < maxMs) { const p = await page.evaluate(() => Number(document.querySelector('[data-tiles-pending]')?.dataset.tilesPending ?? '0'));
    if (p === 0) { zero ??= Date.now(); if (Date.now() - zero > 800) break; } else zero = null; await page.waitForTimeout(100); }
  await mark(`${label}:settled`); };

await page.goto(url, { waitUntil: 'load' }); await mark('boot');            // init script installs on navigation: mark AFTER goto
await page.getByTestId('loading-veil').waitFor({ state: 'detached', timeout: 90000 }); await settled('boot');
const heapAfterBoot = await heap();
await mark('idle-home'); await page.waitForTimeout(3000);
const cx = vw / 2, cy = vh / 2; await page.mouse.move(cx, cy);
await mark('zoom-in'); for (let i = 0; i < 14; i++) { await page.mouse.wheel(0, -240); await page.waitForTimeout(60); } await settled('zoom-in');
await mark('pan'); await page.mouse.down(); for (let i = 1; i <= 24; i++) { await page.mouse.move(cx + i * 12, cy + i * 6); await page.waitForTimeout(16); } await page.mouse.up(); await settled('pan');
await mark('zoom-out'); for (let i = 0; i < 14; i++) { await page.mouse.wheel(0, 240); await page.waitForTimeout(60); } await settled('zoom-out');
await mark('idle-final'); await page.waitForTimeout(3000); await mark('end'); await page.waitForTimeout(300);
const raw = await page.evaluate(() => ({ frames: window.__perf.frames, marks: window.__perf.marks, loaf: window.__perf.loaf, renderer: window.__perf.renderer, defines: [...window.__perf.globeDefines], canvas: [document.querySelector('canvas').width, document.querySelector('canvas').height] }));
const heapEnd = await heap();
const uaMem = await page.evaluate(async () => self.crossOriginIsolated ? (await performance.measureUserAgentSpecificMemory()).bytes : null);
const sys = await (await browser.newBrowserCDPSession()).send('SystemInfo.getInfo');           // provenance: binary + GPU devices
await browser.close();
// per-phase percentiles between consecutive marks → JSON + console.table (see the scratch copy for the exact reducer)
writeFileSync(`${label}.${gpu}.${mode}.${vw}x${vh}@${dpr}.json`, JSON.stringify({ label, gpu, raw, heapAfterBoot, heapEnd, uaMem, requests, sys: sys.gpu.devices }, null, 2));
```

Two things the harness taught today that the script encodes: `__perf` only exists after the
first navigation (init scripts run per document), and the stub's CORS allowlist means the preview
**must** be on :4173 — a run on :4199 measured a globe with no basins, rivers or labels and would
have looked ~~~20 %~~ **~13 % cheaper on idle GPU time** (15.49 → 13.45 ms on Intel; idle draw
calls 34 → 22 — corrected in §10; the JSON records requests per host, 18–19 to `:8000`, not the
refusals themselves, which are inferred from the stub's CORS code and the missing draw calls).

---

## 8. Gaps and unverified items (do not build on these until closed)

1. Timer-query availability in *shipping* Chrome (not Chrome-for-Testing), Safari and Firefox —
   UNVERIFIED; the auto-detector needs the rAF fallback regardless.
2. Trace category names for the compositor frame pipeline (§3) — reported by community sources,
   not parsed here. The harness records a trace as an artifact; no budget depends on it.
3. `preserveDrawingBuffer`, `antialias: true` context attribute, `showGroundAtmosphere`, vertex
   lighting — each one is a single-flag A/B in the harness; UNMEASURED today.
4. The headed 20 ms rAF cadence — cause unknown; new headless is the reference mode.
5. The `Canvas` bucket of `measureUserAgentSpecificMemory` as a GPU-memory proxy — observed to
   track the backing store; not specified to. Keep the §4 texture arithmetic as the bound.
6. Apple-silicon integrated GPUs (the likeliest "ordinary laptop" among stakeholders) — no
   number exists; the BALANCED/HIGH boundary for them is an open measurement.
7. One run per configuration today; the 5-run protocol has not been executed yet.
8. Playwright's `channel: 'chromium'` requires the full Chromium download (not `--only-shell`);
   CI images built with `--only-shell` will silently fall back to SwiftShader — assert the
   renderer string in the harness (it does) and fail loudly.

---

## 9. Recommendations, ranked

1. **Adopt the harness as the gate for every cinematic change** (`tests/perf/`, `perf:owner`),
   with the §7 protocol and the `channel: 'chromium'` + `powerPreference` mechanism; keep the
   SwiftShader e2e config for determinism only and forbid citing its timings.
2. **Wire the tier into the renderer** — `SceneController.setQuality(tier)` does not exist yet;
   implement it as: `useBrowserRecommendedResolution = false` + `resolutionScale` per §6,
   `msaaSamples` per §6, `requestRenderMode = true`, `tileCacheSize` per §6,
   `globe.showGroundAtmosphere = false` at all tiers. Default `balanced` stays until the
   auto-detector ships; the store already has the field.
3. **Turn on `requestRenderMode` first** (every tier): it removes 15.5 ms of GPU work per idle
   frame on the integrated GPU and gives the glass compositor the headroom the liquid-glass
   research showed it needs. Audit layers for time-driven animation and route them through
   `requestRender()`/`maximumRenderTimeChange`.
4. **Make MSAA a tier decision**: keep 4× on HIGH/ULTRA, 1× on BALANCED/LOW — measured as half
   the Intel frame. Also drop the redundant `antialias: true` context attribute (A/B first).
5. **Native-resolution rendering is the cinematic upgrade the owner will actually see** — ship it
   on HIGH/ULTRA only, gated by the probe; on Intel-class GPUs it is 59 ms/frame with MSAA and
   25 ms without.
6. **Keep bloom/DOF/AO/HDR/shadows/clouds/particles/exaggeration out of the plan** for a pure-nadir
   map (§5 "X"); the only globe-side "light" worth an A/B is vertex lighting from the terrain's
   octvertexnormals on HIGH+.
7. **Retire the PERFORMANCE.md inferences** with these facts: the frame hook is the rAF callback,
   the GPU timer *is* available in the lab, CI runners must use `channel: 'chromium'` on a GPU
   runner or measure relative only; add the §6 table as the calibrated budget set and cite this
   file as its measurement method.
8. **Do not add COOP/COEP to production** for the memory API without its own decision; it is a
   preview-server setting for the harness.

---

## 10. Verification (adversarial pass, 2026-09-01)

Method: every Cesium claim re-grepped against `apps/web/node_modules/@cesium/engine/Source`
(engine 26.2.0 / cesium 1.144.0) and `cesium/Source/Cesium.d.ts`; every measured number re-read
from the JSON artifacts in the session scratchpad; the GPU probe (`gpu-probe.mjs`) **re-run**
in `shell`, `newheadless` and `newheadless-lowpower` modes (shell ×3); external URLs re-fetched;
`layer.json` re-curled with an `Origin` header. Legend: ✓ holds as written · ✓* holds with a
caveat now folded into the body · ✗ wrong or not reproduced (body corrected inline).

| # | Claim | Verdict | Note |
|---|---|---|---|
| C1 | Cesium forces `powerPreference` to `high-performance` unless overridden; `low-power` selects the Intel UHD 630; harness injects it via `getContext` wrap, no source change | ✓ | `Renderer/Context.js:57-58` (`?? "high-performance"`), doc line 460. Harness wrap at scratchpad `perf-harness.mjs:26-29`. Re-run today: `newheadless` → AMD Radeon Pro 5300M, `newheadless-lowpower` → Intel UHD 630. |
| C2 | Every rAF renders because `requestRenderMode` is off; the shouldRender predicate and the four auto-request events | ✓ | `Scene.js:681,698` defaults; predicate `4590-4606` exactly as stated (`_renderRequested`, `cameraChanged`, `_logDepthBufferDirty`, `_hdrDirty`, `MORPHING`, then `maximumRenderTimeChange`); listeners `703-709` (`RequestScheduler.requestCompletedEvent`, `TaskProcessor.taskCompletedEvent`) and `807-813` (`imageryLayersUpdatedEvent`, `terrainProviderChanged`), all via `requestRenderAfterFrame`. Render loop `Widget/CesiumWidget.js:46-63`. Blog: "averaged 25.1% … now averages 3.0%" on an Intel i7 laptop. No `requestRenderMode` under `apps/web/src`. |
| C3 | Globe shader compiled with `GROUND_ATMOSPHERE` + `DYNAMIC_ATMOSPHERE_LIGHTING`, not `FOG`/`PER_FRAGMENT_GROUND_ATMOSPHERE`/`ENABLE_VERTEX_LIGHTING`; per-fragment only beyond `nightFadeOutDistance` = π/2·R | ✓* | Defines list in `defines.low-power.newheadless.1280x800@2.json` matches. `Globe.js:203` (`showGroundAtmosphere = WGS84.equals(ellipsoid)`), `:282` (`PI_OVER_TWO * minimumRadius` ≈ 9,985 km), `GlobeSurfaceTileProvider.js:2399-2400` (3D only), `2419-2422` (per-fragment when `cameraDistance > nightFadeOutDistance`), `2797-2801` + `3051` (`enableFog = applyFog`). Caveat folded into §4: `DYNAMIC_ATMOSPHERE_LIGHTING` comes from `Globe.dynamicAtmosphereLighting` (default true, `Globe.js:185`), not from the ground-atmosphere flag, and is inert without lighting. |
| C4 | `tileCacheSize` is a count trimmed LRU; ≈350 KB per RGBA 256² mipmapped tile per layer; two textures per tile during reprojection; 800 × 2 layers ≈ 560 MB | ✓* | `TileReplacementQueue.js:32-53`, `QuadtreePrimitive.js:1326`, `Globe.js:116` (default 100), `UrlTemplateImageryProvider.js:237` (`hasAlphaChannel ?? true`), `ImageryLayer.js:1211-1216` (RGBA/RGB), `1286-1327` (mipmaps when LINEAR/LINEAR + power-of-two), `1363-1412`, `Imagery.js:70-77`. Arithmetic: 256²×4 = 262 KB × 1.33 = 349 KB. Caveats folded into §4: estimate not bound (shared, ref-counted imagery; >1 imagery tile per terrain tile possible); reprojection only for pixel spacing > 1e-5 rad (coarse levels); both textures persist after reprojection. |
| C5 | Bloom 4 passes; DOF 3 passes + depth texture; **AO generate+blur+composite**; any stage/HDR switches to `sceneFramebuffer`; all disabled by default; shadows 2048²/4 cascades; water effect needs a water mask the R2 `layer.json` lacks | ✗ (AO part) | Bloom ✓: `createBlur` = `_x_direction` + `_y_direction` stages (`PostProcessStageLibrary.js:38-70`), bloom = contrastBias → blur → composite (`388-470`). DOF ✓: `blur` (2) + `czm_depth_of_field_composite` (`141-190`), `isDepthOfFieldSupported → context.depthTexture` (`207`). **AO ✗**: `createAmbientOcclusionStage` builds only `czm_ambient_occlusion_generate` and `czm_ambient_occlusion_composite` (`496-520`, composite `stages: [generate, ambientOcclusionModulate]` at `580-586`) — no blur stage in 1.144; §5 corrected to 2 passes. Post-process path ✓ `Scene.js:3969-3990`; defaults ✓ `PostProcessStageCollection.js:53-56`; HDR ✓ `Scene.js:1650-1685`; shadows ✓ `ShadowMap.js:68-75` (doc) and `283` (`size ?? 2048`); water ✓ `Globe.js:303,996-1001`. `layer.json` re-curled: `extensions: ["octvertexnormals"]`, `format quantized-mesh-1.0`, and no `Access-Control-Allow-Origin` even with `Origin: http://localhost:4173`. |
| C6 | `FrameRateMonitor.fromScene` with the stated defaults is the runtime downgrade trigger; `PerformanceDisplay` shows "(throttled)" under `requestRenderMode` | ✓ | `FrameRateMonitor.js:168` (`fromScene`), `153-159` (defaults 5.0/2.0/5.0/4/8), `206-231` (events), `Cesium.d.ts:34428`; `PerformanceDisplay.js:57-67` (`"(throttled)"`), `Scene.js:4427` (`throttled = scene.requestRenderMode`), `Cesium.d.ts:44104`. "Supported trigger" is a recommendation, not a Cesium statement. Renderer grep for `disjoint`/`TIME_ELAPSED`: zero hits, as claimed. |
| E1 | Default headless = `chromium-headless-shell`, SwiftShader, no timer query, **rAF 33.3/50 ms**, memory API throws even when isolated | ✗ (cadence) | Re-run ×3 today: binary `chromium_headless_shell-1234/…/chrome-headless-shell --headless --use-gl=angle --use-angle=swiftshader-webgl`; renderer "ANGLE (Google, Vulkan 1.3.0 (SwiftShader Device (Subzero)…))"; `MAX_SAMPLES` 4; `EXT_disjoint_timer_query_webgl2` absent; `crossOriginIsolated === true` yet `SecurityError … is not available` — all ✓. **rAF cadence was 16.66 ms p50 in all three re-runs (p95 16.67 / 16.67 / 33.33)**; the 33.3/50 ms reading is not reproducible and §1/§2 are corrected. Registry entries `coreBundle.js:32403-32410` ✓. |
| E2 | `channel: 'chromium'` = real Chromium with `--headless`, hardware GPU via ANGLE-Metal, `MAX_SAMPLES` 8, timer query present, rAF 16.67, memory API works; Playwright adds only `--enable-unsafe-swiftshader` (+ headless trio) and never `--use-gl`/`--use-angle`/`--disable-gpu` | ✓ | Re-run: `chromium-1234/chrome-mac-x64/Google Testing.app/…/Google … --headless`, AMD ANGLE Metal, `MAX_SAMPLES` 8, timer query true, rAF 16.67/16.67/16.67, `measureUserAgentSpecificMemory` 37.5 MB with buckets JavaScript/DOM/Canvas/Shared. `coreBundle.js:43066-43072` ✓; grep of all `playwright-core/lib` for `use-angle|use-gl|swiftshader-webgl|disable-gpu`: zero hits. playwright.dev/docs/browsers: "New Headless on the other hand is the real Chrome browser". |
| E3 | App renders at ¼ native pixels on retina: `useBrowserRecommendedResolution` defaults true → `pixelRatio = 1.0`; nothing in `apps/web/src` sets it; canvas 1280×800 at DPR 2 | ✓ | `CesiumWidget.js:91-116` (`pixelRatio = _useBrowserRecommendedResolution ? 1.0 : devicePixelRatio; *= _resolutionScale; width *= pixelRatio`), `276-277` (`?? true`). Grep of `apps/web/src` for `useBrowserRecommendedResolution|resolutionScale|requestRenderMode|msaaSamples|showGroundAtmosphere`: no hits. `info.canvas: [1280,800]` with `dpr: 2` in every 1280×800@2 artifact. |
| E4 | Intel: 15.5 ms idle GPU, zoom-in GPU p95 36.5, rAF p95 116.7 at 1280×800; 58.7 ms idle at 2560×1600; AMD 3.73 / 7.56 | ✓ | Re-read from the artifacts (idle = `idle-final` p50): Intel 1280 `15.49` / zoom `36.46` / rAF `116.66`; Intel 2560 `58.66`; AMD 1280 `3.73`, AMD 2560 `7.56`. All other §0 cells (CPU p95, LoAF, uaMem 188.5/160.1/366.2/258.2/185.2/370.5 MB, heap) match to rounding; runs are single-shot, as §0 already says. |
| E5 | MSAA off halves the Intel frame: 15.5 → 7.95 idle, 36.5 → 14.1 zoom p95 (1280), 58.7 → 25.3 (2560); constructor assigns `_msaaSamples = 4` without the clamp the setter applies | ✓ | `msaa-off.*` artifacts: `7.95` / `14.09` / `25.25`, `ctxAttrs.antialias:false`, `maxSamplesSeen: 0` (patch active). `Scene.js:251` (`options.msaaSamples ?? 4`, no clamp), `1701-1710` (`Math.min(value, ContextLimits.maximumSamples)`), `3941-3982` (globeDepth/OIT/sceneFramebuffer take `scene.msaaSamples`), `Renderbuffer.js:61-70` (`renderbufferStorageMultisample` when `numSamples > 1`). `maxSamplesSeen: 8` in the defines run. |
| E6 | `measureUserAgentSpecificMemory` needs secure + cross-origin-isolated context; Vite `preview.headers` exists; `Canvas` bucket moved with the backing store — observed, not documented as GPU memory | ✓ | MDN: "your document must be in a secure context and cross-origin isolated"; breakdown `types` are "implementation-defined" (examples show only DOM/JS) and the page never mentions GPU memory — so the `Canvas` bucket is indeed an observation. Vite docs: `preview.headers`, type `OutgoingHttpHeaders`, "Specify server response headers." Probe re-run confirms the four buckets. `credentialless` keeping cross-origin fetches working is consistent with the 129–149 `basemap.nationalmap.gov` requests in the :4173 artifacts (not separately tested). |
| E7 | Stub API CORS allowlist is `:5173`/`:4173` only; a run on another port silently drops basins/rivers/labels (~20 % cheaper); `__perf` exists only after `goto` | ✓* | `apps/web/dev/stub-api.mjs:13` ✓. The two `before.*.newheadless.json` artifacts have `url: http://localhost:4199/`, 18–19 requests to `:8000`, idle draw calls 22 vs 34 on `:4173` — consistent with missing vector layers; the JSON does not record refusals. **"~20 % cheaper" overstated**: idle GPU 13.45 vs 15.49 ms = ~13 %; §7 corrected. Init-script-per-document behaviour is Playwright's documented semantics; the quoted failure is not in an artifact (accepted as the author's log). |
| E8 | PERFORMANCE.md budgets carry two inferences (GPU timer query "not reliably available", frame-sampler hook name) and every prior "measured" checkpoint used the SwiftShader e2e config, a **30 Hz software path** | ✓* / ✗ (30 Hz) | `docs/PERFORMANCE.md:68` (§2 "GPU utilization guidance": "INFERENCE: GPU timer-query extensions exist but are not reliably available") ✓; `:395` (§9: "INFERENCE for the hook name") ✓ (also `:321` in §7). `tests/e2e/playwright.config.ts:24` (`headless: true`) and `:30` (the four args) — the doc's `:25-28` citation was off by two lines and is corrected. **"30 Hz software path" ✗** — see E1; it is a software path, not a 30 Hz one. Whether prior checkpoints in other docs used this config was not audited here. |

Net effect on the recommendations (§9): none of the eight change. The corrections are to the
AO pass count (§5), the shell rAF cadence (§1, §2), a citation line number, the `:4199` cost
delta (§7), and three caveats on the texture-memory arithmetic (§4).
