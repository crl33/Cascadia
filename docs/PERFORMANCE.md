# PERFORMANCE — budgets, quality tiers, loading, render discipline, delivery, cost

Performance is architecture, not tuning. A 3D observatory that stutters, leaks, or waits on
the network loses the one thing it exists to give: an operator's attention during an event.
This document fixes the budgets, the mechanisms that keep them, the instruments that prove
them, and the tests that stop regressions. It binds `apps/web`, `apps/api`, `apps/worker`
(derivative generation) and the delivery path (object storage, CDN).

Scope and labels follow [CONTEXT.md](CONTEXT.md): **FACT** / **ASSUMPTION** / **INFERENCE**
/ **OPEN QUESTION**. Every numeric target below is an **ASSUMPTION** until calibrated on the
reference hardware of §1; the *measurement method* beside each number is the durable part.
Calibration is a deliverable of the cinematic sequence in
[CINEMATIC_ROADMAP.md](CINEMATIC_ROADMAP.md). The frontend set listed in CONTEXT.md
([CINEMATIC_ARCHITECTURE.md](CINEMATIC_ARCHITECTURE.md), [SEMANTIC_ZOOM.md](SEMANTIC_ZOOM.md),
[CAMERA_SYSTEM.md](CAMERA_SYSTEM.md), [LAYER_SYSTEM.md](LAYER_SYSTEM.md)) was written
concurrently with this document on 2026-08-22, and all seven cinematic documents are on disk;
the same-day reconciliation pass confirmed that tier names, the `SceneLayer` interface
([LAYER_SYSTEM.md](LAYER_SYSTEM.md) §1 is canonical) and the request-cancellation rules
(LAYER_SYSTEM §6.2) match this document; the residual mismatches are listed in §14.
Presentation rules for truth classes, degraded data and the
layer inspector are in [VISUAL_TRUTH_DOCTRINE.md](VISUAL_TRUTH_DOCTRINE.md); this document
defers to it wherever a failure or a tier changes what is drawn.

Vocabulary used exactly as defined elsewhere: camera **bands** `orbital / state / basin /
river / local` ([VISUALIZATION_CONTRACTS.md](VISUALIZATION_CONTRACTS.md) §8); quality tiers
`ultra / high / balanced / low` as store state (`qualityTier`, renderer-boundary rule 8);
`SceneLayer` exactly as [LAYER_SYSTEM.md](LAYER_SYSTEM.md) §1 defines it (`mount / unmount /
dispose / setTime / setVisible / setData / setQualityTier / budget()` among others); controllers
`SceneController`, `CameraController` (events `settled` / `interrupted`),
`SemanticZoomController`; `VisualTruthClass` `observation | authoritative_model |
cascade_derived | cartographic | cinematic`. Nothing here adds a field to a backend contract.

## 1. Reference hardware tiers

Budgets are stated against Tier A. Tier B confirms headroom; Tier C and D bound degradation.

| Tier | Definition (ASSUMPTION; fix exact SKUs in `infra/perf-lab.md` when purchased) | Default quality |
|---|---|---|
| **A — mainstream modern (primary)** | 2022+ laptop, integrated GPU, 16 GB RAM, current Chromium/Safari/Firefox, 1440p at DPR 2, 25 Mbps / 50 ms RTT | `high` |
| **B — workstation** | discrete GPU, 32 GB RAM, 100 Mbps / 20 ms RTT | `ultra` |
| **C — constrained desktop** | 2018-era laptop, integrated GPU, 8 GB RAM, 10 Mbps / 100 ms RTT | `balanced` or `low` |
| **D — tablet / phone** | current iPad-class tablet; phone is best-effort (§12) | `low` (tablet may reach `balanced`) |

Desktop is the primary target ([ARCHITECTURE.md](ARCHITECTURE.md) §11 lists mobile-first
layouts as a non-goal for Phases 0–2). Network conditions are part of the tier because tile
delivery, not rendering, dominates first-scene time on Tier A.

## 2. Budgets

All targets Tier A unless stated. "Flight" = a scripted camera move between two named bands
(e.g. `orbital → basin` on `basin:skagit`). Frame metrics use percentiles of frame time, never
an average alone (an average hides hitching). Scale assumption for API numbers: the Phase 1
seed set (6 basins with their seed gauges, forecast points and SNOTEL sites — roughly 20
stations, [DOMAIN_MODEL.md](DOMAIN_MODEL.md) §6) with warm caches.

| Metric | Target | Floor / per tier | Measurement method |
|---|---|---|---|
| JS transferred, shell (panels, search, store, query) | ≤ 250 KB brotli | hard cap 300 KB | Vite build manifest; CI bundle-size check on every PR ([TESTING.md](TESTING.md) §9) |
| JS transferred, shell + scene chunk (renderer + controllers + base layers) | ≤ 2.5 MB brotli | hard cap 3.0 MB | same |
| Time to interactive (shell): search and panels usable with server state, no globe | ≤ 2.5 s | Tier C ≤ 5 s | Playwright with throttled network; our User Timing mark `shell:interactive` |
| Globe first render ("first meaningful scene": globe + basin outlines at `orbital` + `HazardVisualizationState` applied) | ≤ 4.0 s | Tier C ≤ 8 s; `low` ≤ 3 s | mark `scene:first-meaningful`; screenshot diff confirms outlines present |
| Camera interaction FPS (during flight and free orbit) | `high` 60 | floors: `ultra` 45 (Tier B) · `high` 30 · `balanced` 30 · `low` 20 | frame-time sampler (§9): target = p50 ≤ 1000/target ms; floor = p95 ≤ 1000/floor ms over a flight; 3 s sustained under floor ⇒ auto-downgrade in auto mode (§3) |
| Idle frame cost (camera still, no animation) | ≤ 4 ms | `ultra` ≤ 8 ms | same sampler; with on-demand rendering (§7) idle should render ~0 frames |
| Band settle (`settled` event → P0–P2 for the new band applied) | ≤ 1.5 s | Tier C ≤ 3 s; `low` ≤ 1 s | mark pair `band:settled` → `band:applied` per flight; prefetch excluded |
| Timeline scrub frame time (10 Hz scrub, warm slice cache) | p95 ≤ 16 ms | `balanced`/`low` p95 ≤ 33 ms | sampler during a scripted scrub across the cached ±12-slice ring (§6); cache misses counted separately |
| JS heap, steady state at `basin` band with 3 scientific layers | ≤ 500 MB | hard ceiling 700 MB; `low` 300 MB | Playwright via DevTools protocol heap metrics; eviction (§4.6) triggers at 80 % of ceiling |
| Renderer tile / texture cache bytes | `high` 768 MB | `ultra` 1,024 · `balanced` 512 · `low` 256 MB | our fetch-layer byte counter for scientific layers; renderer cache statistics for terrain/imagery (INFERENCE: renderer exposes them; else estimate from tile count × bytes) |
| GPU utilization guidance | no standard browser API reports GPU utilization (INFERENCE: GPU timer-query extensions exist but are not reliably available and time commands, not load). Proxies: idle frame cost, flight p95 frame time, dropped-frame rate. Guidance: post-processing ≤ 3 ms/frame on `high`, 0 on `balanced`/`low`; first lever under pressure is render-resolution scaling, second is effect removal, never layer removal | — | proxies above; lab machine GPU counters weekly (§10) |
| Tile requests per flight (`orbital → basin`) | `high` ≤ 350 | `balanced` ≤ 200 · `low` ≤ 100; `basin → local` `high` ≤ 250 | Playwright request interception, counted per flight id by host class (terrain / imagery / vector / scientific raster) |
| Simultaneous scientific raster layers (basemap imagery not counted) | `high` 3 | `ultra` 4 · `balanced` 2 · `low` 1 | layer registry enforces at mount; attempt beyond cap is refused with a UI notice, never silently dropped |
| Simultaneous entities / labels | visible labels ≤ 48 at any band; point entities `high` ≤ 3,000 | `balanced` ≤ 1,500 · `low` ≤ 500; river polyline vertices `high` ≤ 300 k · `low` ≤ 100 k | counters in the layer registry; these are renderer-wide ceilings across all layers — the per-band data caps and label budgets of [LAYER_SYSTEM.md](LAYER_SYSTEM.md) §5 apply first; labels culled by `display.label_priority` |
| Panel responsiveness (input → visible response) | ≤ 100 ms p95 | ≤ 200 ms on Tier C | `PerformanceObserver` event-timing entries (standard API); long-task count per interaction |
| Panel data latency (cache hit / first network) | ≤ 200 ms / ≤ 800 ms p95 | — | query-layer timing around fetch, labeled cache/network |
| API p95, server-side (family → ms) | geography 100 (304: 20) · state 200 · assessments 200 · explanation 250 · series page 300 · thresholds & alerts 100 · visualization `SceneSummary` 300 · tile redirect 30 · system 50 · events timeline 300 | replay (`as_of`) adds ≤ 150 ms to the base family | OpenTelemetry histograms labeled by route family and `as_of` presence ([ARCHITECTURE.md](ARCHITECTURE.md) §8); excludes client network |
| SSE fan-out | 5,000 concurrent connections per API replica; commit → client receipt ≤ 2 s p95 | heartbeat every 25 s; reconnect with jittered backoff | load harness opening N connections and timestamping `{kind, scope, at}` events against the DB commit time |

Named budgets. [CAMERA_SYSTEM.md](CAMERA_SYSTEM.md) §12 refers to budgets by the ids below and
[CINEMATIC_ROADMAP.md](CINEMATIC_ROADMAP.md) §1 by the row names; ids resolve to rows above, and
phase exit criteria cite an id or a row name, never a number:

| Budget id | Row |
|---|---|
| `bundle_initial` | JS transferred, shell |
| `bundle_scene` (added here) | JS transferred, shell + scene chunk |
| `first_globe` | globe first render |
| `flight_frame_time` | camera interaction FPS, as p50 / p95 frame time |
| `band_settle` | band settle |
| `scene_memory` | JS heap + renderer tile / texture cache bytes |
| `tile_requests_per_band` | tile requests per flight into a band |
| `scrub_frame_time` | timeline scrub frame time |
| `idle_frame_cost` | idle frame cost |
| `raster_layer_cap` | simultaneous scientific raster layers |
| `entity_label_caps` | simultaneous entities / labels |
| `panel_latency` | panel responsiveness and panel data latency |

OPEN QUESTION: whether Tier A at DPR 2 can hold `high` at 60 fps with atmosphere on. If
calibration says no, `high` on Tier A renders at a reduced resolution scale rather than
dropping to `balanced`.

## 3. Quality tiers

Tiers are configuration (renderer-boundary rule 8). `SceneController.setQuality(tier)` fans
out to each layer's `setQualityTier` ([LAYER_SYSTEM.md](LAYER_SYSTEM.md) §1) and layers
degrade internally; no tier changes *what* is true, only how much of the cinematic
vocabulary is spent depicting it. Cinematic elements are `truth:
"cinematic"` and are the first to go.

| Capability | `ultra` | `high` | `balanced` | `low` |
|---|---|---|---|---|
| Terrain (`TerrainProvider.level`, [CINEMATIC_ARCHITECTURE.md](CINEMATIC_ARCHITECTURE.md) §10) | `lidar` where available, else `wa_product` | `wa_product` | `regional_dem`, coarser detail cap | `global` or ellipsoid; 2.5D |
| Basemap imagery | vendor satellite, highest zoom | vendor satellite | vendor or the production default basemap | production default basemap only (self-hosted or quota-bearing; the keyless OSM default is dev/demo-only per ADR-0006 evidence; OPEN QUESTION, §14: CINEMATIC_ARCHITECTURE §11 still lists `keyless` for LOW) |
| Atmosphere, sky, lighting | on, time-of-day lighting | on | restrained | off |
| Post-processing and custom shaders (cinematic) | all | most | restrained; crossfades become holds | none; no custom shaders |
| Cinematic weather depiction (driven by `WeatherVisualizationState` rasters) | volumetric AR field, animated | animated, lower resolution | 2D field, static | static field at one zoom lower, or basin aggregates only (OPEN QUESTION, §14) |
| River flow animation (`flow_visual_intensity`) | animated | animated | static width/intensity | plain terrain-clamped lines |
| 3D Tiles (`local-detail`, where licensed) | photogrammetry + point clouds near `local` | photogrammetry near `local` | off | off |
| Scientific raster layers (concurrent) | 4, full resolution | 3 | 2, key fields | 1, one zoom lower (OPEN QUESTION, §14) |
| Entities / labels | full caps (§2) | full caps | reduced | minimum |
| Camera | terrain-following flights with easing | same | shorter flights | cuts (also the reduced-motion path on every tier) |
| Render resolution | device DPR | DPR, scaled under pressure | ≤ 1.5× | 1× |
| **Core intelligence** (panels, timeline, search, selection, provenance badges, official categories, headroom, alerts, replay) | **always** | **always** | **always** | **always** |

The last row is the contract: everything a person needs to *read the basin* works on `low`,
including a globe that navigates. OPEN QUESTION (from ADR-0006): a 2.5D renderer for `low`
was kept as a candidate; the decision criterion is whether the `low` tier of the primary
renderer can meet the §2 `low` floors on Tier C/D. If yes, one renderer; if not, an ADR.

### 3.0 Product surface (2026-09-01)

The four tiers are the renderer's vocabulary; the product exposes **two experiences**
(owner decision, [cesium-cinematic-plan-2026-09-01.md](research/cesium-cinematic-plan-2026-09-01.md)
§10 Q2): **Essential** = BALANCED/LOW budgets (CSS-pixel backing store, MSAA off, no
lighting), **Cinematic** = HIGH/ULTRA (native device pixels, MSAA 4, and — after its A/B —
hillshade). Implementation: `apps/web/src/scene/quality.ts` (pure: budgets, `resolveTier`,
`classifyProbe`, the downgrade ladder) and `scene/render-quality.ts` (Cesium-facing:
`applyTierBudget`, `probeRenderCost`, `watchGestureFrames`). The store carries the user's
`experience` choice (persisted per browser), the `detectedTier`, and the effective
`qualityTier` that CSS and the glass system read.

Auto-detection replaces the synthetic probe scene in §3.1: in the boot's LAST stage
("MEASURING THIS DEVICE", 5 % of the manifest — after the ground, the regional warm, the data
queries and the live envelope have all settled, still under the opaque veil, so nothing contends
for the frame) the controller switches to Cinematic's real budget and measures ≈45 forced frames — GPU timer query where `EXT_disjoint_timer_query_webgl2` exists, CPU render
time and frame arrival everywhere; frames with tiles still uploading are not counted, and a
clearly slow machine exits after 20. Thresholds are the perf research §6 table (GPU p50
≤ 5 / 9 / 16 ms; frame-delta p95 ≤ 17 / 34 ms). The runtime downgrade is a gesture-window
monitor (p95 of rendered-frame deltas across one wheel/drag), stepping one tier after three
consecutive misses of the tier's floor — never across an explicit choice. Cesium's
`FrameRateMonitor` is not used: under `requestRenderMode` an idle scene renders nothing,
which it would read as 0 fps. A detection persists per device for 24 h (`cascadia.detectedTier`),
so the stage is instant on later visits; measured during the regional warm instead, the same
Intel machine classified LOW on one production boot and BALANCED on the next — the quiet stage is
the fix, not a wider threshold.

### 3.1 Automatic detection

```ts
interface CapabilityProbe {
  webgl2: boolean; maxTextureSize: number; deviceMemoryGb: number | null;   // INFERENCE: device memory hint is non-standard; null when absent
  hardwareConcurrency: number; dpr: number; reducedMotion: boolean;
  connection: "fast" | "slow" | "unknown";
  probeFrameMsP50: number;          // 60 frames of a fixed synthetic probe scene, first 10 discarded
}
type QualityTier = "ultra" | "high" | "balanced" | "low";
function detectTier(p: CapabilityProbe): QualityTier  // pure; unit-tested with fixture probes
```

Rules: no WebGL2 or probe p50 > 33 ms ⇒ `low`; probe p50 > 16 ms or `deviceMemoryGb ≤ 4` or
`slow` ⇒ `balanced`; default `high`; `ultra` only on opt-in or a probe p50 ≤ 6 ms at DPR ≥ 2.
Phones (§12) are capped at `low`, tablets at `balanced`. Reduced motion never changes the tier,
only the camera mode.

### 3.2 Runtime adaptation and user override

- Mode `auto` (default): the frame-time sampler downgrades one tier after 3 s under the floor
  and never upgrades automatically within a session (hysteresis: no oscillation). Each change
  emits a non-modal notice and a telemetry event.
- Mode `manual`: the user's choice is persisted locally and is never overridden; pressure
  triggers only a suggestion. Manual `ultra` on a Tier C machine is allowed and logged.
- Selected tier and mode are store state and appear in the layer inspector beside every
  layer's truth class, so a reader can see *why* a cinematic element is absent.

## 4. Progressive loading

Cascadia is never loaded at local resolution on startup (a V1-shaped mistake generalized:
never fetch what the camera cannot see). The client starts at the `orbital` band with the
coarsest LOD of everything and descends on demand.

### 4.1 Priority order

```
P0  camera-visible region, current band, coarsest LOD that fills the viewport
P1  selected entity (basin / forecast point / reservoir) — its contracts and its geometry band
P2  near-camera geometry at the next finer LOD (terrain, vector, rivers)
P3  active scientific layers for the visible region at the current time slice
P4  likely next camera destination (prefetch; capped, idle-only, §4.5)
```

A single scheduler (`scene/requests.ts`, `RequestScheduler` — the name used by
[LAYER_SYSTEM.md](LAYER_SYSTEM.md) §6 and [SEMANTIC_ZOOM.md](SEMANTIC_ZOOM.md) §7: priority
queue, `AbortSignal`, cache) owns every camera- or time-keyed fetch. The P0–P4 order above is
the acceptance-criteria order and matches the lists in LAYER_SYSTEM §6.1 and SEMANTIC_ZOOM §7.
Terrain and basemap imagery tiles are scheduled by the renderer
(INFERENCE: it has its own tile-request throttling); ours schedules scientific rasters,
vector geometry and contract documents and observes the renderer's queue depth so the two do
not compete for the per-host connection limit (INFERENCE for the exact numbers: browsers cap
concurrent HTTP/1.1 connections per host and multiplex many streams over one HTTP/2
connection).

```ts
interface SceneRequest<T> {
  key: RequestKey;                    // { layer, band, extentCell, validTime, issuedAt?, asOf? }
  priority: 0 | 1 | 2 | 3 | 4;
  estimateBytes: number;
  fetch(signal: AbortSignal): Promise<T>;
}
interface RequestScheduler {
  enqueue<T>(r: SceneRequest<T>): Promise<T>;            // de-duplicated by key; smaller first within a priority
  invalidate(pred: (k: RequestKey) => boolean): void;   // aborts in-flight + drops queued
  setMaxInFlight(n: number): void;                       // per tier: ultra 8 · high 6 · balanced 4 · low 2 (ASSUMPTION)
  stats(): { inFlight: number; queued: number; bytesThisSession: number; byHost: Record<string, number> };
}
```

### 4.2 Cancellation

`CameraController` emits `interrupted` when a flight is cut short and `cameraSample` (≤ 10 Hz
while moving, plus on settle) ([CAMERA_SYSTEM.md](CAMERA_SYSTEM.md) §3); `SemanticZoomController`
derives the band with hysteresis and emits `bandChanged`, on which the scheduler re-plans its
queue ([SEMANTIC_ZOOM.md](SEMANTIC_ZOOM.md) §5, §7) — the camera never emits a band (DECIDED
2026-08-22). A band change, a
time change, or an extent change of more than 30 % of the viewport (ASSUMPTION; tune) calls
`invalidate` for keys of the previous band/time/extent cell. Every fetch carries an
`AbortSignal` (renderer-boundary rule 6). A response that arrives for an invalidated key is
discarded, not applied. A replay `as_of` change aborts everything; a selection change aborts P1 for the previous
entity ([LAYER_SYSTEM.md](LAYER_SYSTEM.md) §6.2). Contract documents for the *selected*
entity are exempt from extent-based invalidation (the panel still needs them). Aborts have
no side effects: a layer keeps its last slice.

### 4.3 Tile LOD

Terrain, imagery and 3D Tiles use the renderer's screen-space-error selection (generic LOD
mechanism; INFERENCE for the knob names). Per tier we set a maximum detail level and a
screen-space-error tolerance; `balanced` and `low` raise the tolerance so fewer, coarser
tiles satisfy a view. Vector geometry uses the backend's per-band display LOD
(`display_geom_lod[]`, [DOMAIN_MODEL.md](DOMAIN_MODEL.md) §2.1) and never asks for a finer
band than the camera band. Scientific rasters are served as tile pyramids (§8) and request
the zoom that matches the band, capped by the tier's raster resolution.

### 4.4 Request prioritization and caps

- Concurrency: the scheduler drains at most `maxInFlight` requests (per tier, §4.1) and yields
  while the renderer's own tile queue is above a threshold.
- Starvation guard: P0/P1 always preempt; a P3 request older than 5 s is promoted one level.
- Per-session budgets (bytes, request counts) are tracked and exposed in the dev overlay.

### 4.5 Prefetching with caps

Prefetch only what the product makes likely: the camera's declared flight target, the hovered
basin or search result, and the next slice in the direction the timeline is being scrubbed.
Bounds, all of which must hold ([LAYER_SYSTEM.md](LAYER_SYSTEM.md) §6.4): at most 2 prefetch
requests in flight, at most 8 per minute, at most 10 % of the tier's byte budget, only while
the queue above P3 is empty and the frame sampler is above target, only ±2 slices around `t`,
never across an `as_of` boundary, never `local-detail`; plus caps of ≤ 40 tiles and ≤ 20 MB
per trigger and ≤ 30 MB per session beyond visible need (ASSUMPTION; the numbers LAYER_SYSTEM
§6.4 cites from here). Exceeding a bound drops the
request silently; nothing is retried from P4. Prefetch is off on `low`, on `slow`
connections, on Tier D, and for any basemap whose `BasemapProvider.usage.prefetchAllowed` is
false. There is no "warm the whole state" mode.

### 4.6 Memory eviction

Every in-memory cache in §6 is an LRU by bytes over `(layerId, key)` with a tier-based ceiling
(`scene_memory`). Pins that are never evicted ([LAYER_SYSTEM.md](LAYER_SYSTEM.md) §6.3):
static geography of the selected basin, the current slice of every visible layer, official
alerts. At 80 % of the ceiling the scheduler stops prefetching and evicts the oldest unpinned
time slices; at 90 % it evicts non-visible extent cells and asks layers to drop their finest
LOD; at the ceiling it downgrades one tier in auto mode. A layer is told to drop a slice
through `setData` with a removal marker, so the layer's slice index and the scheduler never
disagree. Eviction events are telemetry (§9).

## 5. Bundle strategy

ADR-0006 states the consequence: the renderer is large; code-split and lazy-load the scene.

| Chunk | Contents | Target (brotli) | Loaded when |
|---|---|---|---|
| `shell` | React, router, Zustand store, TanStack Query, generated contract types + Zod, search, panels, timeline UI, provenance formatting | ≤ 250 KB | immediately |
| `scene` | renderer, `SceneController`, `CameraController`, `SemanticZoomController`, `bridge.ts`, basemap provider, base layers (basins, rivers) | ≤ 2.25 MB (ASSUMPTION for the target; FACT per ADR-0006 evidence, retrieved 2026-08-22: the prebuilt renderer bundle alone measures ~1.73 MB gzip, so this chunk is mostly renderer; INFERENCE: a tree-shaken ESM build is smaller by an amount that depends on the bundler) | after `shell:interactive`, via a module-preload hint; the globe mounts when it lands |
| `layers/<name>` | one chunk per optional layer (snow, weather, reservoirs, levees, 3D tiles) | ≤ 60 KB each | on first enable |
| `charts` | series/hydrograph rendering | ≤ 120 KB | on first panel with a chart |
| `event-mode` | Event Mode (C6) and Presentation Mode (C8) controls ([CINEMATIC_ROADMAP.md](CINEMATIC_ROADMAP.md)) | ≤ 150 KB | on entry |

Rules: no third-party script tags (vibesec addendum §4); dependencies are reviewed for size
on addition; `dist/` is grepped for key-shaped strings. The renderer's own static assets
(Workers, ThirdParty, Assets, Widgets) are copied at build time and served from `CESIUM_BASE_URL` on the
same static host as the app (ADR-0006; [ARCHITECTURE.md](ARCHITECTURE.md) §9: static build
behind a CDN) under a version-stamped path with long-lived cache headers; they are never on
the critical path of `shell:interactive`. The loading sequence is itself a product guarantee:
**shell → core intelligence usable → scene → globe**; a failure to load `scene` leaves a
working application without a globe (§13).

## 6. Client cache

| Cache class | Keyed by | Store | Policy |
|---|---|---|---|
| Stable geographic metadata (basin, station, forecast point, reservoir records) | entity id + dataset release | TanStack Query + HTTP cache | long `staleTime`; revalidated by ETag ([ARCHITECTURE.md](ARCHITECTURE.md) §6) |
| Static geometry (display LOD polygons, river network, levees; vector tiles) | content-hashed URL | HTTP cache + in-memory LRU per layer | immutable; new dataset release = new URL |
| Recently visited terrain / imagery tiles | tile key + product valid time | renderer cache + HTTP cache | bounded LRU within the tier ceiling (§2) |
| Recent time slices of scientific rasters | `(product, issued_at, valid_time, zoom, tile)` | in-memory LRU per layer | ±2 slices prefetched around `t` (§4.5); older slices retained only under the byte budget |
| Contract documents (`SceneSummary`, `*VisualizationState`, explanation) | `(contract, scope, band, t, as_of, layers)` | TanStack Query | ring of ±12 slices around `t` (ASSUMPTION; OPEN QUESTION, §14: [LAYER_SYSTEM.md](LAYER_SYSTEM.md) §6.5 retains ±3 raster slices, and the two rings should be set together); `staleTime` from the product's cadence; invalidated by SSE `{kind, scope}` |
| Series pages | `(station, variable, from, to, cursor)` | TanStack Query | immutable for closed ranges; open-ended range refetches on SSE `observation` |

**Freshness is never inferred from the cache.** A cache hit says nothing about whether a
value is current. Every displayed value's freshness comes from the backend's
`ProvenanceRef.freshness` (`state`, `age_seconds`, computed at read time per
[DATA_DOCTRINE.md](DATA_DOCTRINE.md) §5) and the document's `generated_at`. The client shows
two things, separately: the value's freshness as the backend labeled it, and the age of the
document it came from ("view generated 42 s ago"). When the document age exceeds the
product's refresh interval the client refetches. While the API is unreachable the client
re-derives `ageSeconds` from `retrieved_at`/`generated_at` against the local clock and
escalates a layer to stale/degraded on its own at `expected_cadence_seconds` alone — the
contract carries no grace, so the client is conservative
([VISUAL_TRUTH_DOCTRINE.md](VISUAL_TRUTH_DOCTRINE.md) §5.2); the escalation is one-way — a
cached document can become stale in the client, but nothing becomes `current` again without
a new document from the backend. [LAYER_SYSTEM.md](LAYER_SYSTEM.md) §6.5 states the same
one-way rule (a cached slice may gain a STALE mark, never lose one), so the three documents
agree. Replay
documents (`as_of` set) are cached like any other key and are pure functions
of `as_of` (VISUALIZATION_CONTRACTS rule 3), so they never expire on SSE.

## 7. Render-loop discipline

The renderer owns the frame; React owns orchestration (renderer-boundary document; this
section adds the performance reasons and mechanisms).

1. **No React re-render of primitives.** Thousands of reaches, stations and labels are
   renderer-native collections owned by a layer; React never holds them as elements or state.
   A layer's `setData(contract)` diffs items by stable id and updates in place; it rebuilds a
   collection only when the id set changes.
2. **No per-frame React state.** Camera position, clock ticks and animation phase never enter
   the store. `CameraController` quantizes altitude to bands and emits on change only.
3. **Renderer-native mechanisms** for: camera flights (the renderer's own interpolated,
   terrain-aware flight; generic), entity/primitive batching (one batched geometry collection
   per layer per LOD; INFERENCE for the exact primitive types), time-dynamic values (the
   renderer's clock is driven *from* the store's `time`; layers implement `setTime` by
   selecting a slice, rule 5), shader-driven cinematic effects (uniforms updated from the
   renderer's pre-render event — INFERENCE for the hook name — never by React), tile selection (screen-space error).
4. **Batching of updates.** `bridge.ts` coalesces store changes within one animation frame
   and applies them to controllers in a single pass; a timeline scrub at 60 Hz produces one
   `setTime` per frame at most, and layers that cannot keep up skip to the latest time.
5. **On-demand rendering when idle.** When no flight, animation or data change is pending the
   scene renders only on demand (INFERENCE: the renderer supports an explicit-render mode;
   if it does not, the fallback is a frame-rate cap when idle). Cinematic animation on
   `ultra`/`high` requests continuous rendering only while an animated `cinematic` element
   is visible; in the Calm scene state of VISUAL_TRUTH_DOCTRINE that is close to zero, so a
   quiet day costs almost no GPU.
6. **Style mapping is pure and cached.** `layers/*/style.ts` functions are memoized on the
   semantic state; a contract update that changes no semantic value produces no GPU upload.
7. **Budget guard.** The layer registry refuses a mount that would exceed a §2 cap and
   reports it; a layer may lower its own LOD but may not exceed its allocation.

```ts
// SceneLayer is defined once, in LAYER_SYSTEM.md §1 (mount / unmount / dispose / setTime / setVisible /
// setData / setQualityTier / …). The one accessor the registry reads to enforce §2 is defined there too:
budget(): LayerBudget   // LayerBudget { entities; labels; rasterLayers; bytes } — LAYER_SYSTEM §1
```

Review rule: a PR that subscribes a React component to the camera or the clock, or that
maps over a contract's `items` to produce renderer children, fails review.

## 8. Backend and delivery performance

The API never calls a provider and never computes a raster at request time
([ARCHITECTURE.md](ARCHITECTURE.md) §1; vibesec addendum §3). Everything the client draws is
precomputed by workers and served as cacheable bytes.

- **Precomputed derivatives.** Workers emit, per product cycle: basin aggregates (PostgreSQL),
  COGs clipped to the Washington extent with internal overviews, tile pyramids for the
  zooms each band can request, and per-band display geometries. Derivative generation is
  asynchronous to ingestion and tracked as its own job with latency metrics.
- **COG range reads.** Where a tile pyramid is not yet built, tiles are cut from the COG by
  HTTP range reads against object storage, with a maximum zoom, a maximum request size, edge
  caching and per-IP rate limits (vibesec §3). Range-read tiling is a fallback path with its
  own p95, not the steady state.
- **Tile caching / CDN.** Tile and derivative keys are deterministic
  `product/issued/valid/variable/z/x/y` paths plus a content hash, so every tile URL is
  immutable and cacheable for a year; the API's tile endpoints are redirects to object
  storage/CDN. Edge cache hit rate is a first-class metric (§9, §11).
- **Vector-tile generalization per zoom.** Display geometries are materialized per band
  (`regional | state | basin`, the `geometry_ref.lod` values) with simplification tolerance
  and vertex caps per band recorded in `packages/geo`; the `local` band reuses the `basin`
  LOD (no finer generalization is generated unless a measured need appears — OPEN QUESTION
  once levee and channel-work geometry lands in Phase 4).
- **`SceneSummary` size limits.** Never one monolithic scene object (VISUALIZATION_CONTRACTS
  §8). Caps (ASSUMPTION): ≤ 256 KB uncompressed per response; `orbital`/`state` return
  `HazardVisualizationState` items for basins in the bbox plus region weather fields only;
  `basin`/`river`/`local` return the selected basin's states only; `provenance_refs` are
  deduplicated; bbox area and `layers[]` length are validated and rejected over limit.
- **Pagination.** Cursor pagination on series with a page cap of 2,000 points (ASSUMPTION);
  long display ranges are served from precomputed hourly/daily aggregates published as
  DERIVED with a `method_id`, never from on-the-fly decimation.
- **ETags.** Strong ETags on static geography and on contract documents, derived from
  `(as_of, latest assessment/observation ids in scope)` so an unchanged scene costs a 304.
  SSE tells the client *when* to revalidate; ETags make revalidation cheap.
- **Database.** Read-only API role, partitioned tables, "current" views indexed for the
  latest-row-per-key pattern ([DOMAIN_MODEL.md](DOMAIN_MODEL.md) §3); replay queries go
  through `as_known_at(T)` only and are measured separately.

## 9. Instrumentation of the visual system

First-party only; no third-party script (vibesec §4). The `telemetry/` module in `apps/web`
samples and buffers events; the dev overlay and console are always available; remote
reporting is **opt-in** and sends to a dedicated, rate-limited, schema-validated ingest
endpoint that writes to the metrics store, never to domain tables. OPEN QUESTION:
[ARCHITECTURE.md](ARCHITECTURE.md) §6 says there are no anonymous mutating endpoints; a
telemetry sink is a write. Resolve by ADR before remote reporting ships (candidates: a
separate ingest process outside `apps/api`; or a signed, rate-limited, non-domain endpoint).

| Signal | Source | Cadence |
|---|---|---|
| FPS / frame time p50, p95, p99; dropped frames | frame-time sampler hooked to the renderer's post-render event (INFERENCE for the hook name) | per flight and per 10 s idle window |
| memory pressure (JS heap, cache bytes, eviction events, tier downgrades) | §4.6 eviction hooks; heap where the browser exposes it (INFERENCE; optional) | on event + 30 s |
| tile failures, imagery-provider failures, terrain failures | our fetch layer and the renderer's error events, tagged by host class | on event |
| slow API responses (> family p95), 304 ratio | query layer timing | on event + summary |
| scene-state errors, invalid geometries, layer exceptions, animation failures | layer registry `try/catch` around `mount/setData/setTime`; geometry validation before upload | on event |
| request counts and bytes per flight, per host class; prefetch bytes | `RequestScheduler.stats()` | per flight + session summary |
| cache hit rate (query, raster slice LRU, HTTP 304s) | cache wrappers | session summary |
| quality tier, mode, probe result, capability flags | §3 | session start + change |

Events carry `session_id` (random, per load), `build_id`, tier, band, selected scope, and
never a user identifier. Server-side counterparts (API latency per family, tile redirect
rate, edge hit rate, SSE connection count, derivative-generation latency) join the existing
provider-health and freshness boards; a **visual health board** shows frame-time
distributions by tier, failure rates by host class, tile/request volumes per flight, and
tier-downgrade frequency. Alerting: imagery/terrain failure rate > 2 % over 15 min; p95 frame
time over floor on Tier A lab runs; edge hit rate < 90 % (ASSUMPTIONS).

**Rendering errors never silently crash the interface.** Every layer error is caught at the
registry boundary, the layer is marked `degraded` in the layer inspector with the error
class, the event is reported, and the scene continues (§13).

## 10. Regression testing

Performance regression is its own test level: nightly + on demand, advisory until
calibrated, then blocking ([TESTING.md](TESTING.md) §1). Everything runs against fixture
contracts, a fixed clock, and locally served fixture tiles — never live providers or vendor
imagery.

Representative scenes (fixed camera paths, fixed data; reuse the visual-regression scenes of
TESTING §6 where they coincide):

| Scene | Band(s) | Exercises |
|---|---|---|
| regional | `orbital → state` over Cascadia | hazard summary, label culling, coarse tiles |
| basin | `state → basin`, `basin:skagit` | basin/river/snow/reservoir states, LOD switch |
| local | `basin → river → local`, `fp:nwps:MVEW1` / `station:usgs:12200500` | finest terrain, labels, 3D Tiles where enabled |
| multi-layer | `basin`, snow + weather + rivers + reservoirs at `high` and at cap | raster cap, memory, eviction |
| event | Event Zero replay, `as_of` stepping through 2025-12-10T00:00Z → 2025-12-13T00:00Z | time-slice cache, timeline scrub batching, replay ETags |
| GPU stress | synthetic: max rasters + max entities + post-processing at `ultra` | worst-case frame time, resolution scaling |

Checks per scene: first meaningful scene render (mark), JS heap after settle, p50/p95 frame
time over the flight, tile count and request count by host class, bytes transferred, React
commit count during the flight (render-loop regression: must stay under a fixed small
number; a commit per frame is a failure), store updates per second, and per-layer budget
counters. Bundle size runs on every PR, not nightly.

CI gating (ASSUMPTION, revisit after calibration):

- Bundle size: blocking from day one; hard caps (§5) and a > 5 % growth without an approved
  note fail the build.
- Counts (tiles, requests, React commits, entities): blocking from day one; they are
  deterministic on any runner.
- Timing and memory: advisory until 30 nightly runs establish a baseline per runner class,
  then blocking at `min(absolute budget, baseline + 20 %)`.
- CI runners use software or virtualized GPUs, so absolute FPS there is not comparable to
  Tier A; CI measures *relative* regression on a fixed runner class, and a weekly run on a
  Tier A lab machine measures absolute budgets (OPEN QUESTION: owner and hardware of the lab
  machine).

Flakiness: each timed scene runs 5 iterations, the first is discarded as warm-up, the
median is compared; a single failing nightly opens an issue, two consecutive fail the gate;
network is local and clocks are fixed so the remaining variance is the runner, which is
tracked as its own metric.

## 11. Cost control

Cost is a performance property: every byte served and every vendor tile requested is paid
for, and the same mechanisms (LOD, caching, caps) control both latency and spend.

- **Instrumented:** provider requests per adapter (already a worker metric), object-storage
  egress by bucket and key class, CDN egress and hit rate, tile-generation CPU minutes per
  product cycle, storage GB by retention class ([DATA_DOCTRINE.md](DATA_DOCTRINE.md) §13),
  vendor imagery/terrain/3D-tile requests by key and tier, client prefetch bytes.
- **LOD and caching as cost architecture:** immutable derivative URLs make the CDN the
  primary server of bytes; the API serves redirects and small documents. A new product
  cycle invalidates nothing — it creates new keys — so hit rate is bounded only by first
  views. Per-band LOD means the orbital view of the whole state costs a few hundred KB.
- **No unlimited automatic prefetching:** the §4.5 caps are hard; a session has a prefetch
  budget and a total-bytes counter in the dev overlay and telemetry.
- **Vendor quotas and caching rules:** vendor keys are browser-scoped, domain-restricted and
  delivered via `/config/public` (vibesec §4). Each provider carries its limits in `BasemapProvider.usage`
  (`maxZoom`, `maxTileRequestsPerMinute`, `prefetchAllowed`;
  [CINEMATIC_ARCHITECTURE.md](CINEMATIC_ARCHITECTURE.md) §10) and each tier adds a
  vendor-request ceiling per session; a production default basemap that Cascadia Papsukkal controls (self-hosted vector tiles or a
  quota-bearing static-tile service; ADR-0006 evidence, retrieved 2026-08-22) is always
  mounted as the fallback, with the keyless OSM default behind it for dev/demo only (FACT per
  ADR-0006 evidence: OSM tiles are dev/demo-only by policy and heavy use is blocked); quota
  exhaustion or vendor failure steps down that chain with a `cartographic`-class notice and a
  telemetry event, never a blank globe. Vendor plan limits (a monthly streaming cap, a monthly
  free tile quota, a non-commercial restriction — ADR-0006 evidence) are recorded on the
  `BasemapProvider` / `TerrainProvider` object and alerted on. Vendor tiles are cached only as the vendor's terms
  allow (OPEN QUESTION per vendor; record the rule in `infra/` when a key is provisioned).
  Monthly vendor spend has an alert at 70 % and a hard stop that disables the vendor layer
  for new sessions at 100 % (ASSUMPTION on thresholds).
- **Derivative generation:** tile pyramids are built only for the zooms bands can request;
  deeper zooms are cut from COGs on demand and cached; grids outside the rolling retention
  window lose their pyramids first (regenerable; DATA_DOCTRINE §13).

## 12. Mobile and tablet

Desktop is primary. Tier D does not attempt desktop-equivalent complexity.

- Tier: phone ⇒ `low` (fixed); tablet ⇒ `low` default, `balanced` allowed by override.
- Layers: one scientific raster, basins, rivers at the coarser LOD, forecast points; snow
  points and reservoirs as entities without rasters; no 3D Tiles, no cinematic weather.
- Panels: reduced density — one panel at a time as a sheet; the selected entity's official
  category, observed value with badge and freshness, headroom, official alerts, and the
  explanation drivers remain; charts simplified; the layer inspector remains (provenance is
  not a desktop luxury).
- Navigation: search, select, fly/cut between bands, timeline scrub — all retained; the
  globe stays a globe.
- Budgets: JS heap ≤ 250 MB, scene chunk still lazy, prefetch off, tile requests per flight
  ≤ 80 (ASSUMPTIONS). Touch input latency uses the same §2 panel-responsiveness budget.
- Out of scope until an ADR: multi-layer compare, Event Mode cinematic playback,
  presentation mode, offline.

## 13. Failure handling

Failures are isolated per layer and per subsystem; the whole interface never goes down
because one thing did (renderer-boundary rule 7).

| Failure | Containment | User-visible result |
|---|---|---|
| layer throws in `mount/setData/setTime/setVisible` | the `SceneController` guard unmounts the layer, sets `status = 'degraded'` with the exception name, retries `mount` with backoff at most 3 times, then offers manual retry ([LAYER_SYSTEM.md](LAYER_SYSTEM.md) §7.1) | layer listed as degraded in the inspector; scene, camera, timeline and panels never remount |
| invalid geometry from a contract or tile | validated before upload; item skipped and reported | item absent; count shown in inspector; never a partial polygon |
| scientific raster tile failures above threshold | layer retains its last-known slice, dimmed, and may fall back to a coarser zoom of that same slice; never silent removal ([VISUAL_TRUTH_DOCTRINE.md](VISUAL_TRUTH_DOCTRINE.md) §5.1) | DEGRADED badge with reason and last valid time; never calm, green or zero ([DATA_DOCTRINE.md](DATA_DOCTRINE.md) §12) |
| imagery provider failure / quota | basemap provider steps down the §11 chain: production default basemap, then the keyless dev/demo default | cartographic notice; science unaffected |
| terrain failure | falls back to ellipsoid terrain at runtime | flat-earth notice; labels and vectors reposition; no crash |
| `scene` chunk fails to load or WebGL context is lost and not restored | scene container shows a retry control; app stays in "intelligence without globe" mode | panels, search, timeline, provenance fully usable |
| scene-state inconsistency (controller assertion) | `SceneController` resets camera and layer set from store state without remounting the viewer | brief re-settle; selection preserved |
| API family slow or failing | query layer serves the last document; the client ages it against the local clock and escalates stale/degraded (§6); SSE reconnects with backoff and the timeline shows "live updates paused since <t>" | STALE/DEGRADED badges with age; cartographic layers stay navigable; no fabricated freshness |
| panel crash | React error boundary around the panel tree only (never around the scene) | panel shows an error card with retry |

Every row above emits a §9 event. The only way to take the application down is to fail the
`shell` chunk, and that is a static-hosting outage, not a rendering one.

## 14. Open questions (collected)

- Tier A at DPR 2 holding `high` at 60 fps with atmosphere (§2).
- Single renderer for `low` vs a 2.5D renderer (§3; ADR-0006).
- Rasters on `low`: DECIDED 2026-08-22 — one raster at one zoom level lower, basin aggregates always
  (LAYER_SYSTEM §4.5; CINEMATIC_ARCHITECTURE §11 updated).
- Slice-ring sizes: ±12 contract documents here vs ±3 raster slices in LAYER_SYSTEM §6.5, and
  `grace_seconds` absent from `Freshness`, so client-side ageing escalates at cadence alone
  (VISUAL_TRUTH_DOCTRINE §5.2) (§6).
- Production basemap for `low`/`balanced`: §3 and §11 require a production default basemap
  that is not the keyless OSM tile service, while CINEMATIC_ARCHITECTURE §11 lists `keyless`
  for LOW; the choice (self-hosted PMTiles vs a quota-bearing vendor) is open question 10 in
  `research/rendering-stack-and-geodata-delivery.json` and needs an ADR-0006 follow-up.
- Telemetry ingest vs "no anonymous mutating endpoints" (§9) — needs an ADR.
- A finer-than-`basin` display LOD for Phase 4 levee/channel geometry (§8).
- Lab machine ownership for absolute-budget runs (§10).
- Vendor-specific tile caching terms (§11).

## 15. Cross-references

[ARCHITECTURE.md](ARCHITECTURE.md) (API families, SSE, deployment, observability) ·
[VISUALIZATION_CONTRACTS.md](VISUALIZATION_CONTRACTS.md) (bands, `SceneSummary`, hints) ·
[DATA_DOCTRINE.md](DATA_DOCTRINE.md) (freshness, staleness, retention, UNKNOWN rendering) ·
[DOMAIN_MODEL.md](DOMAIN_MODEL.md) (ids, display LOD, seed set) ·
[TESTING.md](TESTING.md) (test hierarchy, visual and performance levels) ·
[ROADMAP.md](ROADMAP.md) (derivative pipeline in Phase 2, Phase 8 visualization) ·
[HYDROLOGY.md](HYDROLOGY.md) §7 (snow must never be depicted as vanishing because a level
moved — a quality tier may drop the cinematic depiction, never change the science) ·
[adr/ADR-0006-web-stack-vite-react-typescript-cesium.md](adr/ADR-0006-web-stack-vite-react-typescript-cesium.md) ·
[adr/ADR-0007-renderer-boundary-and-visualization-contracts.md](adr/ADR-0007-renderer-boundary-and-visualization-contracts.md) ·
renderer boundary rules: [cesium-react-boundary.md](../.claude/skills/react-quality/references/cesium-react-boundary.md).
