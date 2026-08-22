# LAYER SYSTEM — scene layers: contracts in, pixels out

Canonical as of 2026-08-22. Governs `apps/web/src/layers/` and the layer registry in
`apps/web/src/scene/`. A *layer* is a plain TypeScript class that turns visualization contracts
([VISUALIZATION_CONTRACTS.md](VISUALIZATION_CONTRACTS.md)) and static geography into renderer
primitives under the boundary rules of
[cesium-react-boundary.md](../.claude/skills/react-quality/references/cesium-react-boundary.md).
Siblings own what this document only references: truth classes, registers and the inspector
([VISUAL_TRUTH_DOCTRINE.md](VISUAL_TRUTH_DOCTRINE.md), "VTD"); bands, the visibility matrix and
labels ([SEMANTIC_ZOOM.md](SEMANTIC_ZOOM.md), "SZ"); budgets, caps, scheduler and caches
([PERFORMANCE.md](PERFORMANCE.md), "PERF"); folder layout and controllers
([CINEMATIC_ARCHITECTURE.md](CINEMATIC_ARCHITECTURE.md), "CA"); camera, lighting and tours
([CAMERA_SYSTEM.md](CAMERA_SYSTEM.md), "CAMERA"); phases ([CINEMATIC_ROADMAP.md](CINEMATIC_ROADMAP.md)). Core doctrine:
[DATA_DOCTRINE.md](DATA_DOCTRINE.md), [HYDROLOGY.md](HYDROLOGY.md), [ARCHITECTURE.md](ARCHITECTURE.md),
[ROADMAP.md](ROADMAP.md). Claims are labeled per [CONTEXT.md](CONTEXT.md).

## 0. Position and invariants

```
 Zustand store (semantic only)                 TanStack Query (server state)
   time · asOf · band · selection · layerIntents   keys ['scene', dataBand, extentKey, t, asOf, layersHash]  (SZ §5)
   qualityTier · reducedMotion · eventMode            │
            │ scene/bridge.ts (only subscriber)        ▼
            ▼                                   scene/requests.ts  RequestScheduler  P0–P4 · AbortSignal · caches (PERF §4, §6)
   scene/SceneController ──► scene/LayerRegistry ──► layers/<domain>/<Name>Layer.ts  (implements SceneLayer, layers/contract.ts)
   setTime · setLayerVisible · setData(layerId, doc)      │  style.ts: semantic state → presentation (the only place)
   setQuality · select · hitTest fan-out                  ▼
   emits picked(id) · layerDegraded(id, reason)    renderer primitives (terrain, imagery, ground geometry, rasters, tiles)
```

Invariants (each is a test in §12):

1. **Contracts in, pixels out.** Inputs are contract documents and static geography by stable id
   ([DOMAIN_MODEL.md](DOMAIN_MODEL.md) §1). A layer computes no hydrologic quantity.
2. **No layer owns a clock.** `setTime` is the only way time enters a layer (§2).
3. **Provenance is mandatory.** Every layer answers `provenance()`; a scientific value without a
   `prov` ref is a type error, not a default (VTD invariant 1).
4. **Presentation mapping lives in `layers/<domain>/style.ts`** — colours, materials, shader
   names — and never in a contract (ADR-0007).
5. **Failure is isolated.** A throwing layer is disposed and marked `degraded`; the scene survives (§7).
6. **Cinematic is labeled.** Everything that is not observation, authoritative model, Cascade-derived
   or cartographic is class E / `truth: 'cinematic'` and names its driver (VTD §1.1).

## 1. The `SceneLayer` interface

`apps/web/src/layers/contract.ts` (CA §12). Contract types are generated into `apps/web/src/contracts/`.

```ts
import type { VisualTruthClass, ProvenanceRef } from '../contracts';
import type { Band, LodKey } from '../scene/SemanticZoomController';             // 'orbital'|'state'|'basin'|'river'|'local'|'ground' (SZ §5)
import type { LayerTruthStatus, LayerDataState } from './truth';                  // VTD §5.1: current|stale|degraded|missing|partial|unknown
import type { InspectorRecord } from './inspector';                              // VTD §6 fields (SOURCE … QUALITY)

export type IsoInstant = string;                      // ISO 8601 UTC
export type LayerId = string;                         // ids of SZ §4 plus §4.2 additions, e.g. 'rivers', 'snow_level'
export type EntityId = string;                        // 'basin:skagit', 'fp:nwps:MVEW1', 'station:usgs:12200500'
export type QualityTier = 'ultra' | 'high' | 'balanced' | 'low';
export type LayerStatus = LayerDataState | 'loading' | 'error';   // six data states + two lifecycle states (§1.1)
export type ContractName = 'BasinVisualizationState' | 'RiverVisualizationState' | 'ReservoirVisualizationState'
  | 'SnowVisualizationState' | 'WeatherVisualizationState' | 'HazardVisualizationState' | 'Explanation' | 'SceneSummary'
  | 'StaticGeography';                                // client-side envelope for the geography family + tiles (ARCHITECTURE §6), keyed by id and dataset release; not a VISUALIZATION_CONTRACTS document
export type BandVisibility = 'full' | 'reduced' | 'hidden';       // SZ §4 ● ◐ ·
export type RenderGroup = 'ground' | 'surface' | 'water' | 'state' | 'field' | 'hazard' | 'atmosphere' | 'labels';

export interface TimeMode { kind: 'now' | 'past' | 'forecast'; asOf: IsoInstant | null }   // envelope time.mode + replay clock
export interface LayerDependency { layerId: LayerId; reason: string }                       // { 'terrain', 'plane is clamped to terrain' }
export interface TruthChannel { channel: string; truth: VisualTruthClass; driver?: string }  // cinematic channels name their driver
export interface InterpolationDeclaration {
  kind: 'none' | 'hold' | 'crossfade' | 'parametric';
  purpose: 'cinematic_continuity';                    // the only permitted purpose (§2.4)
  affectsPanels: false;                               // literal type: a panel never reads an interpolated value
}
export interface PresentationContext {
  reducedMotion: boolean; eventMode: boolean; presentationMode: boolean; nightMode: boolean;
  lightingMode: 'solar' | 'analytical';               // VTD §3.8: overlays render independent of lighting
  viewportClass: 'desktop' | 'tablet' | 'phone';
}
export interface SelectionState {
  selected: EntityId | null; hovered: EntityId | null; focused: EntityId | null;
  related: { upstream: readonly EntityId[]; downstream: readonly EntityId[] };   // from the API; never computed here
}
export interface ContractDocument {
  contract: ContractName; version: string; generated_at: IsoInstant; as_of: IsoInstant;
  time: { valid: IsoInstant; mode: TimeMode['kind'] }; items: readonly unknown[];
  provenance_refs: Record<string, ProvenanceRef>;
  removed?: readonly EntityId[];                      // eviction marker from the scheduler (§6.3)
}
export interface RendererHit { layerId: LayerId; entityId: EntityId; channel?: string }   // the tag a layer wrote on its primitive
export interface LayerHit { entityId: EntityId; channel: string; truth: VisualTruthClass; textEquivalent: string }
export interface FocusTarget { entityId: EntityId; label: string; priority: number }
export interface LayerBudget { entities: number; labels: number; rasterLayers: number; bytes: number }   // PERF §7
export interface SceneHandle { /* opaque; owned by SceneController; renderer types never cross it */ }

export interface LayerProvenance {
  status: LayerTruthStatus;                                         // VTD §5.1 (state, ageSeconds, lastKnownValidTime, reason, coverageFraction, renderFailure)
  channels: readonly (InspectorRecord & { channel: string; interpolation: { active: boolean; between: [IsoInstant, IsoInstant] | null } })[];
  contracts: readonly { name: ContractName; version: string; generated_at: IsoInstant; as_of: IsoInstant }[];
  hiddenBy: 'altitude' | 'dependency' | 'tier' | 'intent' | 'cap' | null;   // "hidden at this altitude" etc. (SZ §8)
}

export interface SceneLayer {
  readonly id: LayerId;
  readonly displayName: string;
  readonly truthClass: VisualTruthClass;              // dominant class; drives the inspector TYPE line
  readonly truthChannels: readonly TruthChannel[];    // every class present (§3.2)
  readonly bands: Record<Band, BandVisibility>;       // this layer's row of the SZ §4 matrix
  readonly dependencies: readonly LayerDependency[];  // topological mount order (§4.6)
  readonly dataContracts: readonly ContractName[];    // what setData accepts; anything else ⇒ 'error'
  readonly interpolation: InterpolationDeclaration;
  readonly renderGroup: RenderGroup;

  mount(scene: SceneHandle): void;                    // allocate primitives; idempotent
  unmount(): void;                                    // remove from scene, keep caches; re-mountable
  dispose(): void;                                    // release GPU/CPU resources; terminal for this instance

  setTime(valid: IsoInstant, mode: TimeMode): void;   // select a slice; never starts a clock (§2)
  setVisible(visible: boolean): void;                 // result of the resolver (§4.1), never a raw user toggle
  setData(doc: ContractDocument): void;               // diff by stable id, update in place (PERF §7.1)
  setQualityTier(tier: QualityTier): void;
  setInteractive(interactive: boolean): void;         // pickable/focusable vs purely visual
  setPresentation(ctx: PresentationContext): void;
  setSelection(sel: SelectionState): void;
  setBand?(band: Band, lod: LodKey): void;            // optional; SZ §5 `layerVisibilityChanged.lod`

  readonly status: LayerStatus;
  readonly statusReason: string | null;               // 'dependency:terrain' · 'no mapping configured' · 'contract_version'
  onStatusChange(cb: (status: LayerStatus, reason: string | null) => void): () => void;
  provenance(): LayerProvenance;                      // §3
  textEquivalent(): string;                           // §11
  budget(): LayerBudget;                              // registry enforces PERF §2 caps at mount

  hitTest(hit: RendererHit): LayerHit | null;         // SceneController picks; the layer resolves its own tags
  focusables(): readonly FocusTarget[];               // keyboard ring order (§11)
}
```

### 1.1 Status reduction

Worst-wins, from the layer's lifecycle and from the `freshness` of the provenance refs of the
items it is actually showing. The six data states and their rendering are VTD §5.1; a render
failure is `degraded` with `renderFailure: true`; `error` is reserved for protocol faults.

```
error    ← doc.contract ∉ dataContracts, or major version mismatch (VISUALIZATION_CONTRACTS §10 rule 4)
loading  ← no slice for the current (band, t, asOf) key and a request is in flight; nothing retained to show
degraded ← threw (renderFailure), a dependency is degraded/error, or freshness.state = degraded on the dominant channel
missing  ← freshness.state = missing for every shown item, or "no mapping configured" (DATA_DOCTRINE §4)
partial  ← some items missing/unknown, raster coverage < extent, or an entity cap truncated the set
stale    ← the shown slice's freshness.state = stale (age from the contract, §6.5 for the one-way client escalation)
unknown  ← the contract reports unknown — rendered UNKNOWN with reason, never calm (DATA_DOCTRINE §12)
current  ← otherwise
```

Lifecycle: `created → mounted ⇄ unmounted → disposed`. `setData`/`setTime` are legal while
unmounted (they update caches) and illegal after `dispose` (throws in dev, no-op in prod).

OPEN QUESTION: CA §8 sketches the layer's quality method as `setQuality(tier)` and the boundary
document sketches untyped `setTime(t)` / `setData(contract)`; PERF §3 and §7 already use
`setQualityTier` and defer to this section. This document's signatures are the canonical set;
CA §8 is reconciled to it in the same-day pass PERF's header calls for.

## 2. Temporal behaviour

### 2.1 One clock

The timeline writes `time` and `asOf` to the store; `scene/bridge.ts` coalesces store changes
per animation frame and forwards them to `SceneController.setTime`, which calls every mounted
layer in render-group order (PERF §7.4: a layer that cannot keep up skips to the latest time).
`SceneClock` drives the renderer's clock from the store (CA §4.1); its only consumer is solar
lighting (CAMERA §11) — no layer reads that clock. A layer
holding a timer, a frame-time accumulator that advances data time, or its own "now" fails review.
Flow and transport animations advance a *phase*, not data time.

### 2.2 Time-slice selection

Slice selection is implemented once in the shared `TemporalLayer` base (CA §8); a concrete layer
declares its channels and their kind. `setTime` selects; it never fetches synchronously — a miss
asks the scheduler (§6) and leaves the retained slice on screen with its mark.

```
observed channel:   slice = max{ s : s.valid_time ≤ t }                         none → 'missing for t'
                    distance = t − slice.valid_time   (label only: "observed 3 h before the timeline cursor")
forecast channel:   run   = max{ r : r.issued_at ≤ (asOf ?? now) }             server already filtered by as_of;
                                                                                 issued_at > asOf ⇒ contract violation: drop, status 'partial'
                    slice = argmin{ |s.valid_time − t| : s ∈ run, |Δ| ≤ step/2 }   none → 'no value at t'
superseded runs:    selectable only in the forecast-evolution view (CA §7.4), drawn in the superseded treatment
static channel:     the single display geometry for the band's LOD
```

### 2.3 Observed / forecast-valid / forecast-issued semantics per layer class

| Layer class | Timeline cursor moves | Run selector moves | Printed beside the value |
|---|---|---|---|
| observed (gauges, precip_observed, snow_points, reservoir pool) | `valid_time` | — | "observed HH:MM"; STALE mark when the contract says so |
| official forecast (rivers forecast channel, official_alerts) | `valid_time` within the run | `issued_at` | "valid HH:MM · issued HH:MM by NWRFC" (DATA_DOCTRINE §3) |
| official thresholds (thresholds) | nothing (versioned rows, DATA_DOCTRINE §7) | threshold version (`effective_from`) | "OFFICIAL · NWPS" + basis, unit, datum, `retrieved_at` |
| modeled (precip_forecast, atmosphere_ivt, snow_cover, snow_level) | `valid_time` within the cycle | cycle `issued_at` | model name, cycle, valid (KIND from the ref — `snow_level` may be DERIVED, VTD §3.2) |
| Cascade-derived (fractions, trend, susceptibility, agreement) | `valid_time` / `computed_at` | `method_id` version | DERIVED or EXPERIMENTAL badge + method pointer |
| cartographic (terrain, boundaries, reaches, levees, communities) | nothing | dataset release | dataset + release (VTD §1.2) |
| cinematic (atmosphere_haze, flow phase) | solar position only | — | "visualization — driver: <value or clock>" |

A layer with both observed and forecast channels (rivers) shows the observed slice for
`t ≤ now` (or `t ≤ asOf` in replay) and the forecast slice beyond; the seam is drawn, never
smoothed (VTD §2 "never intentionally blur classes").

### 2.4 Interpolation is declared and cinematic only

Interpolation between slices exists to keep motion continuous during a scrub or a flight. It is
never a value: panels, the inspector and `textEquivalent()` read the selected slice, and the
inspector names the bracketing slices whenever interpolation is active ("between 06:00 and
07:00 — cinematic"). `hold` (default; also the reduced-motion form of every other kind),
`crossfade` (opacity blend of two rasters: precipitation fields, SCA — visibility fades, values
do not; SZ §2.1), `parametric` (snow-level plane elevation, river flow phase), `none` (anything
read as a number: gauges, thresholds, alerts, envelopes). Frames between slices are class E in
the inspector (CA §2).

### 2.5 Replay

`asOf` is part of every query and cache key; a layer never mixes slices from two `as_of` values
and discards a document whose `as_of` differs from the store's. SSE is unsubscribed in replay
(CA §7.3). The "reveal outcome" overlay is fetched without `as_of`, drawn in the hindsight
treatment, and never merged into a layer's slice index. Every channel prints "as known at T".

## 3. Provenance

### 3.1 Inspector fields

`provenance()` returns the VTD §5.1 `LayerTruthStatus` for the layer and one VTD §6
`InspectorRecord` per shown channel — SOURCE, TYPE, KIND, VALID TIME, ISSUED TIME, RETRIEVED,
FRESHNESS, CONFIDENCE, MODEL VERSION, RESOLUTION, CASCADE TRANSFORMATION, QUALITY — produced by
the pure `toInspectorRecord(item, provenanceRefs, layerDescriptor)` and extended with the
channel name and the interpolation state. KIND is printed from `source_kind`; "OFFICIAL" appears
only for `OFFICIAL_FORECAST` (vibesec addendum §7). Cartographic channels show dataset + release
and no kind badge; cinematic channels show "visualization" and their driver. For `terrain` the
record states both the displayed mesh and the science DEM (CA §10).

### 3.2 Mixed truth classes

A layer declares every class it contains, per channel, and a hit reports the channel hit.
`rivers`: geometry → `cartographic` (NHDPlus/NWM flowlines), observed state → `observation`,
trend → `cascade_derived`, official forecast → `authoritative_model` (OFFICIAL_FORECAST), model
forecasts → `authoritative_model` (MODELED), flow phase → `cinematic` (driver
`flow_visual_intensity`). `snow_level`: elevation → `authoritative_model`; the two fractions →
`cascade_derived`; rise animation → `cinematic`. `reservoirs`: pool polygon → `cartographic`,
pool elevation/storage → `observation`, buffer → `cascade_derived`. `floodplain` is one layer
per inundation kind, never one layer with three channels (VTD §3.1).

## 4. Visibility rules

### 4.1 Resolver

Composition order is SZ §12 — matrix → tier → viewport → event → presentation → user intent —
and the registry appends two gates of its own:

```
eligible(layer) = compose(SZ matrix row, tier, viewport, event, presentation)[band] ≠ 'hidden'
visible(layer)  = eligible ∧ layerIntents[layer] ∧ dependenciesResolved(layer) ∧ withinCaps(layer)
reduced(layer)  = compose(…)[band] = 'reduced'
```

`SemanticZoomController` emits `layerVisibilityChanged`; `SceneController` applies dependency
and cap gates and calls `setVisible` only on transitions. A vetoed layer reports `hiddenBy` in
the inspector ("hidden at this altitude", "dependency: terrain", "raster cap reached").

### 4.2 Band matrix

The canonical matrix is SZ §4 (`scene/layerMatrix.ts`, data not code). Rows this document adds,
in SZ notation (● full · ◐ reduced · · hidden), to be merged into that file:

| Layer id | truth | orbital | state | basin | river | local | ground |
|---|---|---|---|---|---|---|---|
| `atmosphere_haze` | cinematic | ● | ● | ◐ | ◐ | · | · |
| `precip_observed` / `precip_forecast` (the two halves of SZ's `precip_field`, separate layers) | observation / authoritative_model | ● coarse | ● | ● basin scope | · | · | · |
| `temperature_rain_snow` | authoritative_model + cascade_derived | · | · | ● | ◐ | · | · |
| `model_disagreement` | authoritative_model + cascade_derived | · | · | ◐ | ● | ◐ | · |
| `local_detail` (= SZ `roads_buildings`, `lidar`, `canopy`) | cartographic | · | · | · | · | ● where supported | ● |
| `labels` (budgets 8/14/18/22/16/8, SZ §6) | cartographic | ● | ● | ● | ● | ● | ● |

### 4.3 User toggles

A toggle is a semantic intent (`layerIntents: Record<LayerId, boolean>`), persisted, ANDed with
the matrix (SZ §8). Turning a layer off does not dispose it; its caches stay under the eviction
budget (§6.3). Toggle groups ("snow", "weather") are a panel convenience that expands to layer
ids; the registry knows no groups.

### 4.4 Event-mode overrides

Event mode is SZ §10 (live event focus or replay of an `event:*`); the Major-event scene state
is triggered only by official evidence or the user opening Event Mode, never by `tension` alone
(VTD §7.4). Overrides are rows in `scene/overrides.ts`: `official_alerts` and `hazard_summary`
pinned on at orbital/state; `basin_susceptibility` pinned on at basin; `ar_corridor` pinned on
while `ar.present`; `local_detail` off unless the selection is at local/ground; label budget
tilted to P1. Event mode pins layers on; it never hides a scientific layer. The panel shows
"pinned by event mode".

### 4.5 Quality tier

Tier consequences are PERF §3 (rasters 4/3/2/1; flow animation static from `balanced`;
atmosphere off and no custom shaders on `low`; 3D Tiles only `high`/`ultra`) and SZ §12 (ground
band disabled on `low`). Layer rule: a layer reads the tier through `setQualityTier` and degrades
internally — fewer entities, coarser LOD, static instead of animated — and may never change what
is known. Panels, timeline, inspector and badges are identical on every tier (boundary rule 8).

### 4.6 Dependency resolution

The registry mounts in topological order of `dependencies` and unmounts in reverse; cycles are
rejected at registration. A dependency in `degraded`/`error` puts dependents in `degraded` with
`statusReason: 'dependency:<id>'` and hides them. Declared: `snow_level`, `floodplain`, `levees`,
`local_detail`, `water_surface_local` → `terrain`; `model_disagreement`, `thresholds`,
`topology_arrows` → `gauges`/`rivers`; `labels` → the layer owning each labeled entity. Terrain
falling back to the ellipsoid (PERF §13) is `degraded` with reason, not `error`, so dependents
re-clamp rather than vanish.

### 4.7 Reduced motion

`prefers-reduced-motion` or the user setting sets `reducedMotion`. It never hides data: flow and
transport phases freeze at 0, crossfades become cuts, the snow-level plane jumps, label fades are
instant, auto-orbit is off (SZ §12). Emphasis that motion carried is carried by the non-colour
cue of §11 instead.

## 5. Level of detail

| Band | Vector geometry (`display_geom_lod`, DOMAIN_MODEL §2.1) | Rivers | Rasters / tiles | Labels (SZ §6) |
|---|---|---|---|---|
| orbital | `regional` basins; no reaches | major only (◐) | region-scale fields, one zoom | 8 |
| state | `state` basins | stream order ≥ 5 (ASSUMPTION, SZ §2.2) | state-scale | 14 |
| basin | `basin` for the focus basin, `state` for neighbours | tributaries ≥ order 3 | basin-scale | 18 |
| river | full flowlines of the focus basin | all reaches | full; floodplain polygons | 22 |
| local / ground | `basin` LOD reused (PERF §8) + optional 3D Tiles | channel | screen-space-error per tier | 16 / 8 |

Rules: geometry LOD is chosen from `geometry_ref.lod` and the dataset release, never
re-simplified client-side (topology would change). Entity caps are PERF §2 (point entities
3,000/1,500/500 by tier; polyline vertices 300 k / 100 k; visible labels ≤ 48; scientific rasters
4/3/2/1) and are enforced by the registry through `budget()`; a cap truncates by ascending
`display.label_priority` and the inspector says so (`partial: 120 of 400 shown`). Labels are the
`labels` layer fed by `labelSetChanged` (SZ §6): priority classes P0–P6, class-level dropping,
28 px spacing, clustering, hysteresis. A label that loses its slot is still focusable and still
present in `textEquivalent()`.

## 6. Loading

`scene/requests.ts` (`RequestScheduler`, SZ §7) is the only module that turns layer needs
into requests; PERF §4.1 specifies the same broker as `LayerDataBroker` in
`scene/layer-data-broker.ts` — one module, one name to settle (§13). Layers never fetch.

### 6.1 Priority queue

```
P0  camera-visible region, current band, coarsest LOD that fills the viewport  (SceneSummary per band)
P1  selected entity: its Basin/River/Snow/Reservoir states and explanation      (exempt from extent invalidation)
P2  near-camera geometry at the next finer LOD (terrain, vector tiles, reaches, levees, places)
P3  active scientific layers for the visible region at the current time slice (raster refs)
P4  likely next destination: next-lower band's P0 at the view centre while descending, hovered
    search result, next timeline slice in scrub direction — prefetch, bounded by §6.4
```

In-flight requests are capped per tier — 8 / 6 / 4 / 2 for ultra / high / balanced / low
(ASSUMPTION, PERF §4.1); P0/P1 preempt; a P3 older than 5 s is promoted
one level; the scheduler yields while the renderer's own tile queue is deep.

### 6.2 Abortable fetches and cancellation

Every request carries an `AbortSignal` under its key. `bandChanged` aborts every request under
the previous `dataBand` prefix; a time change aborts the previous `t` and coalesces intermediate
scrub values (only the latest in flight); an `asOf` change aborts everything; a selection change
aborts the previous selection's P1; an extent change > 30 % of the viewport (ASSUMPTION, PERF
§4.2) invalidates the previous extent cell. Late responses for a non-current key are discarded by
key equality, never applied. Aborts have no visible side effect: the layer keeps its retained slice.

### 6.3 Memory eviction

Caches are byte-LRUs under tier ceilings (PERF §2, §4.6): at 80 % of the heap ceiling prefetch
stops and non-visible time slices go; at 90 % non-visible extent cells go and layers are asked to
drop their finest LOD (OPEN QUESTION: via `setBand(band, coarserLod)`; confirm same day); at the
ceiling auto mode drops one tier. Pinned: the selected basin's static geography, the selected
entity's current slice, every visible layer's current slice, official alerts. A layer learns of
eviction through `setData({ …, removed })` so its slice index and the scheduler never disagree.

### 6.4 Prefetch limits — no unlimited prefetch

Prefetch is adjacent only — the next time slice in scrub direction, one adjacent band (the
declared flight target), the hovered basin or search result (CA §13) — and capped by PERF §4.5
(ASSUMPTIONs): ≤ 2 in flight, ≤ 8 per minute, ≤ 10 % of the tier's byte budget, ≤ 20 MB per
trigger, ≤ 30 MB per session beyond visible need, only ±2 slices around `t`, idle-only, frame
sampler above target, never across an `asOf` boundary, never for `local_detail`, disabled on
`low`, on slow connections and on phones. A request over a bound is dropped, never queued or retried.

### 6.5 Client cache and the freshness rule

Cache classes are PERF §6: stable geography (id + release, ETag), static geometry
(content-hashed URL, immutable), recent terrain/imagery tiles (renderer LRU), recent scientific
raster slices (±2 around the cursor prefetched, older only under the byte budget, ASSUMPTION),
contract documents (`(contract, scope, band, t, as_of, layers)`, a ring of ±12 slices around `t`,
SSE-invalidated — PERF §2, §6), series pages. Every key includes `asOf`.

**Browser cache is not freshness.** A cache hit says nothing about currency. A layer's status
comes from the document's `ProvenanceRef.freshness` as the backend computed it plus the
document's own age ("view generated 42 s ago"); nothing in the client ever *promotes* a value to
current. While the API is unreachable the client re-derives `ageSeconds` against the local clock
and escalates one way to stale/degraded (VTD §5.2, PERF §6); only a new document from the
backend clears a mark. SSE `{kind, scope, at}` invalidates the affected keys (ARCHITECTURE §6).

## 7. Error states

### 7.1 Failure isolation

`LayerRegistry` wraps `mount`, `setData`, `setTime`, `setVisible`, `setSelection` and `hitTest`
in a guard. A throw disposes the instance, marks the layer id `degraded` with
`renderFailure: true` and the error class, emits `layerDegraded(id, reason)` and a PERF §9 event,
and continues the frame. The scene, camera, timeline and panels never remount. The registry
constructs a fresh instance from the layer's factory with backoff at most 3 times; after that the
layer panel offers a manual retry. Invalid geometry from a contract or tile is validated before
upload, skipped and counted in the inspector (PERF §13). React error boundaries wrap panel trees
only (boundary rule 7).

### 7.2 Last-known-data retention

On fetch failure, abort or eviction of a newer slice, the layer keeps the last slice it has: the
rendering is retained, dimmed, and marked STALE/DEGRADED with age and last valid time (VTD §5.1
— the SNODAS rule: never silent removal, never a blank basin that reads as "no snow"). A
"retained since HH:MM" line is added. Retained data is subject to eviction like any slice.

### 7.3 Missing-source messaging

`missing` keeps the two cases DATA_DOCTRINE §4 separates distinct: "no mapping configured for
this basin" (configuration state; the inspector names the mapping) versus "product not
published / source failed" (freshness reason). Both render the unknown/missing register
(hatched or outlined placeholder in scope, MISSING badge, reason), never the calm state and never
an empty map. Floodplain absence reads "no authoritative floodplain data", not dry land (SZ §2.4).

### 7.4 Partial coverage

`partial` covers basins without an assessment (those basins get the UNKNOWN treatment with a
reason), rasters covering part of the extent (a coverage mask elsewhere, PARTIAL badge with
fraction — never unpainted area that reads as calm), cap truncation (§5), and mixed freshness
inside one layer (per-item marks; layer status is the worst item of the dominant channel).

## 8. Layer registry and catalogue

### 8.1 Registry

`scene/LayerRegistry.ts` (ASSUMPTION on the file name; CA §12 places the registry in `scene/`)
registers layer factories by id, validates the dependency graph, fixes render order
(`ground → surface → water → state → field → hazard → atmosphere → labels`, then registration
order), applies the §4.1 gates, enforces PERF §2 caps at mount through `budget()` (a refused
mount is a UI notice, never a silent drop), aggregates statuses for the layer panel, feeds the
inspector, and fans out `hitTest` in reverse render order so the topmost hit wins. Adding a
layer = one folder `layers/<domain>/{<Name>Layer.ts, style.ts, state.ts, *.test.ts}` plus one
registration line and one matrix row; no other file changes (CA §14 criterion 11).

### 8.2 Catalogue (initial set; VTD class letters A–E beside the contract truth class)

| id (SZ §4 unless marked +) | truth | bands | contracts consumed | notes |
|---|---|---|---|---|
| `imagery` | cartographic D | all | — | `BasemapProvider` (CA §10); the keyless OSM default keeps the app runnable without accounts but is dev/demo-only by OSM policy (ADR-0006 evidence); vendor failure or quota steps down the PERF §11 chain — production default basemap, then keyless — with a cartographic notice |
| `terrain` | cartographic D | all | — | `TerrainProvider` hierarchy; visual mesh ≠ science DEM (CA §10); dependency root |
| `atmosphere_haze` + | cinematic E | orbital–river | — | driver = clock (solar lighting); procedural clouds "conceptual" until a cloud-cover variable exists (VTD §3.6) |
| `cascadia_context` | cartographic D | orbital, state | StaticGeography | coastline, region outline |
| `watershed_boundaries` | cartographic D | orbital–river | StaticGeography (`display_geom_lod`) | basins and subbasins (`parent_basin_id`; subbasins at basin band only); §9.3 |
| `basin_susceptibility` | cascade_derived C-EXP | orbital–basin | BasinVisualizationState, HazardVisualizationState (orbital) | environmental tint; EXPERIMENTAL badge; `tension` = wake-up only |
| `rivers` | D + A + C + B + E | all | RiverVisualizationState, StaticGeography | channels §3.2; state ladder §9.4 |
| `topology_arrows` | cartographic D | river, local | StaticGeography (`from_node → to_node`) | direction, never velocity (SZ §2.4); routing illumination §9.4 |
| `gauges` | A + B + C | basin–ground | RiverVisualizationState (+ Snow `points`, reservoir stations by `station_type`) | `station:usgs:*`, `fp:nwps:*`; category, headroom, trend, regulation flag |
| `thresholds` | B-official | river–ground | RiverVisualizationState.thresholds | basis, unit, datum always; CONFIGURED never colours a category (ADR-0011) |
| `reservoirs` | D + A + C | state–ground | ReservoirVisualizationState, StaticGeography | pool polygon, dam point (`dam:nid:*`), storage envelope §9.5 |
| `levees` | cartographic D (NLD attributes verbatim) | river–ground | StaticGeography | every `FloodDefense.kind`; never "protects" (VTD §3.5) |
| `floodplain_regulatory` · `floodplain_modeled` · `floodplain_observed` | D · B · A | river–ground | StaticGeography (NFHL) · authoritative inundation model keyed to forecast stage · observed extent (SAR/satellite/verified reports) | the three kinds of VTD §3.1; each its own layer and language; kind 2 absent where no authoritative model exists |
| `snow_cover` | B (A for dated SCA scenes) + C | state, basin | SnowVisualizationState (`sca_raster_ref`, `swe.by_band`, `anomaly_pct_of_median`) | SCA raster; SWE by elevation band and anomaly as hypsometric band overlay |
| `snow_points` | A | basin, river | SnowVisualizationState.points | SNOTEL kept visually distinct from gridded SWE (HYDROLOGY §7) |
| `snow_level` | B + C + E | basin, river | SnowVisualizationState (`snow_level`, two fractions) | §8.3 |
| `soil_state` | C over B/A | basin | BasinVisualizationState.headline_drivers | §8.3; SZ OQ-4 |
| `precip_observed` + | A | orbital–basin | WeatherVisualizationState `qpe_*` | windows 1/3/6/12/24/48/72 h (ROADMAP Phase 2 "1–72 h"; only `qpe_1h` is a named contract variable today, §13); solid, grounded register |
| `precip_forecast` + | B | orbital–basin | WeatherVisualizationState `qpf_*`, `basin_aggregates.spread` | windows 6/12/24/48/72/120 h (HYDROLOGY §4; `qpf_6h` and `qpf_mm_by_window` today, §13); spread from `basin_aggregates.spread` as a p10/p90 band on the basin value — no spread raster exists — never noise (VTD §2) |
| `atmosphere_ivt` | B + E | orbital, state | WeatherVisualizationState `ivt` | §8.3 |
| `ar_corridor` | B | orbital–basin | WeatherVisualizationState.ar | corridor, scale, orientation, duration; no invented track (SZ OQ-3) |
| `temperature_rain_snow` + | B + C | basin, river | Weather `temperature_2m`, `freezing_level`; Snow `snow_level`, fractions | per-band rain fraction is not a contract field (§13) |
| `official_alerts` | B-official | all | BasinVisualizationState.official_alerts, `/alerts` | verbatim, issuer, times, OFFICIAL; never restyled (VTD §8) |
| `model_disagreement` + | B + C | basin–local | RiverVisualizationState (`official_forecast`, `model_forecasts`, `agreement`), Explanation.model_agreement | §8.3 |
| `hazard_summary` | B + C | orbital, state | HazardVisualizationState | official category word, forcing, susceptibility, agreement per basin |
| `communities` | cartographic D | state–ground | StaticGeography (`place:census:*`, `area:*`, `downstream_of_reach_ids`) | exposure attributes in later phases (DOMAIN_MODEL §2.1) |
| `local_detail` + (`roads_buildings`, `lidar`, `canopy`) | cartographic D | local, ground | 3D Tiles / imagery refs from `/config/public` | optional, `high`/`ultra`; never required (CA §10) |
| `water_surface_local` | D + E | local, ground | StaticGeography (mapped channel extent) | §9.6 |
| `labels` + | cartographic D | all | every contract's `name`, `display.label_priority` | SZ §6; no data values in labels except official category words and badged values of the band template |

### 8.3 Notes on the non-obvious layers

- **snow_level.** A terrain-intersecting surface (contour when reduced) at the contract's
  `snow_level.elevation`; terrain below it is the rain-exposed elevation band, and its
  intersection with the SCA raster is the rain-on-snow exposed band — highlighted bands on the
  hypsometry (VTD §3.2). The plane rises and falls parametrically between slices (declared
  cinematic). The fractions printed anywhere are the contract's `rain_exposed_fraction` and
  `rain_on_snow_exposed_fraction`; the client never integrates the plane against terrain, and
  the displayed mesh is not the science DEM (CA §10). **The plane never removes snow**
  (HYDROLOGY §7): SCA and SWE are drawn identically above and below it; no melt animation.
  `offset_from_freezing_level_m` is printed, never assumed. Trend wording waits on SZ OQ-5.
- **soil_state.** Subtle analytical modes: basin tint by saturation-percentile class, ground
  translucency (a wetter, darker reading of the landscape), percentile contour from the gridded
  product, optional raster overlay. Inspectable: current, normal (climatology reference),
  anomaly, each fusion source with its freshness, and the disagreement between sources
  (HYDROLOGY §8). Until a `SoilVisualizationState` exists (SZ OQ-4, CA §17) the layer renders
  tint only from `headline_drivers.soil_saturation_percentile`.
- **atmosphere_ivt / ar_corridor.** A volumetric (tier `high`+) or semi-transparent moisture
  field from the `ivt` raster (`display_range` normalizes; the ramp is style.ts), intensity
  gradient, transport animation (phase only, class E, driver = the field), and a forecast cone
  only when a spread field exists. Direction comes from `ar.orientation_deg` alone: streamlines
  wait for IVT vector components in the contract (§13) — the gradient of a magnitude raster is
  not transport direction and is never computed client-side. Never cartoon arrows. Regional
  framing at orbital/state (the whole corridor against the Cascade crest using `orientation_deg`);
  basin framing at basin band (the part over the basin; windward slopes only if geography ever
  supplies a terrain-aspect attribute — none exists today, §13 — never from the displayed mesh).
  The forecast storm path is the time sequence of forecast `ivt` fields labeled with the model (SZ §2.2).
- **model_disagreement.** At each forecast point a layered envelope between the official crest
  and each named model crest: tight (agreement high) or wide (low), one band per model, stacked,
  never averaged (DATA_DOCTRINE §10). Selectable models: NWPS, NWM configurations by name, HEFS
  where machine-accessible (ROADMAP "what would change this roadmap"), other named sources, and
  Cascade experimental — only after Phase 7, always in the experimental register and never red
  (VTD §7.1). `agreement.state` is printed as a word. In Event Mode the river band shows three
  distinct crest-marker classes (SZ §10).
- **hazard_summary.** Orbital/state glyphs per basin; `tension` raises presence up to the
  Elevated scene state only (VTD §7.4) and the inspector states it is not a probability.

## 9. Styling

### 9.1 `style.ts` contract

Pure, total, memoized functions from semantic state to presentation (PERF §7.6); no I/O, no
renderer calls; named tokens come from `design-system/tokens` (CA §12) and every mapping from
a semantic state to a token, material or shader lives in the layer's `style.ts`:

```ts
export const riverTreatment = (s: RiverSemantic, sel: SelectionRelation, ctx: PresentationContext): RiverStyle => …
export const basinEdge      = (s: BasinSemantic, sel: SelectionRelation): EdgeStyle => …
```

Every function handles `unknown` explicitly; a missing case is a type error, not a default
colour. Registers (VTD §2) are the first key of every mapping; state is the second.

### 9.2 Colour system

VTD §7 governs; this is the layer-level consequence. Natural Earth base — imagery, terrain, sky
and water geometry keep their own colour at every state. Nominal hydrology information in the
deep navy / cyan family; amber as tension rises (elevated states, Watch-level official products,
shrinking headroom, disagreement); red earned only by class A/B evidence — observed exceedance
of an official moderate/major threshold, an official major forecast category, an official
Warning — and never by C-class or EXPERIMENTAL values. Forecast treatments differ from observed
by register (translucent, softer, issued-time marker), not by hue alone; EXPERIMENTAL carries a
badge and pattern wherever it appears; UNKNOWN is neutral and incomplete-looking, never calm,
green or zero. No state is distinguished by saturation alone (§11). No neon, no emergency-TV
graphics, no threat metaphors (VTD §7.3). Night mode swaps tokens, not rules (VTD §3.8).

### 9.3 Basin boundaries

Embedded in the landscape, never thick GIS outlines. Normal: invisible or nearly (a faint
terrain-following hairline at most). Hover: a soft edge. Selected: a gentle terrain-following
boundary. High susceptibility (`basin_susceptibility`): a subtle environmental tint inside the
basin — wetter, darker ground — badged EXPERIMENTAL until the index is promoted (HYDROLOGY §3).
`tension` may raise the tint's presence; it never changes its family.

### 9.4 Rivers

Rivers are *state visualization, not physical level*: no treatment implies depth, width,
velocity or extent, and the river is never raised or extruded (VTD §3.3). The ladder is a
`style.ts` decision; the inputs are contract fields only:

| Treatment | From contract | Look |
|---|---|---|
| calm | `observed_category = none`, low `flow_visual_intensity` | natural water; slow flow phase |
| elevated | `none` with high intensity, or `trend.direction = rising` | subtly increased animation; same family |
| watch | `action` | restrained amber |
| flood | `minor` → strongest amber; `moderate` / `major` → hazard (red) family, graded | hazard treatment; category word printed |
| unknown | `unknown`, or no official threshold on the reach (ADR-0011) | neutral, static, UNKNOWN badge |

The forecast category is drawn as a distinct forward treatment on the reach below the point
(§2.3 seam), never as current water; there only an official *major* forecast category reaches
the red family (VTD §7.1) — forecast `moderate` stays amber. **Direction and routing:** selecting a gauge softly
illuminates the upstream contributing network and, differently, the downstream affected
reaches; `topology_arrows` give direction (`from_node → to_node`, cartographic); the flow phase
is the cinematic channel. Upstream/downstream sets come from the API (`topology` plus the reach
graph, DOMAIN_MODEL §4) — the client maps ids to geometry and computes no topology. Regulated
reaches always carry the regulation mark beside headroom (HYDROLOGY §9).

### 9.5 Reservoir storage envelope

An envelope anchored to the pool: current storage against the rule-curve maximum and
flood-control bounds, `available_buffer.fraction` with the rule curve's provenance, inflow/outflow
as a restrained trend mark from `flows.trend`. The pool polygon is cartographic; no 3D water
surface moves with pool elevation (VTD §3.4). `forecast_inflow = null` prints "future state
UNKNOWN", never an extrapolation (HYDROLOGY §10).

### 9.6 Water rendering

Realistic base water — imagery, water mask, the mapped channel extent of `water_surface_local`
(cartographic; shimmer is class E) — is a separate channel from any modeled hydraulic water
surface, which exists only as `floodplain_modeled` (class B, authoritative model, issued/valid
time, model name). When hydraulic data exists the scene enters a distinct, badged "hydraulic
surface" mode; the two are never blended, and base water never rises to suggest a level.

## 10. Shaders and GPU

Custom shaders are permitted only for the six uses below. Each must serve spatial
comprehension, state comprehension, cinematic realism or information hierarchy — never
futurism (no holograms, scan lines, grids, pulsing rings, VTD §7.3). Each has a non-shader
fallback (`low` has no custom shaders, CA §11) and a reduced-motion form; an animated shader
requests continuous rendering only while visible (PERF §7.5).

| Use | Serves | Truth channel | `balanced` / `low` fallback | reduced motion |
|---|---|---|---|---|
| river flow | state comprehension + realism | E over A state (driver `flow_visual_intensity`) | static width/intensity (PERF §3) | phase 0 |
| precipitation fields | spatial comprehension | A / B raster | static raster | hold |
| atmospheric effects | cinematic realism | E | simplified / off | static |
| subtle basin highlighting | information hierarchy | C tint | flat tint | static |
| forecast envelopes | state comprehension (uncertainty) | B (+ C agreement) | outlined polygons | static |
| snow visualization | spatial comprehension | B / A raster + plane | raster + contour | plane jumps |

A shader reads only the hint fields the contracts allow (`display_range`, `tension`,
`flow_visual_intensity`), style tokens and a time phase; it never receives a raw scientific value
to threshold (CA §15: a threshold or percentile in a uniform is a refactoring trigger). INFERENCE:
the renderer's per-primitive custom-shader facility suffices; if not, the fallback column is the
implementation.

## 11. Accessibility

- **Non-colour cues.** Every state in §9 also differs by form — stroke pattern, fill pattern,
  outline weight, icon — and by a badge word in the panel; every register and category is
  distinguishable in greyscale (VTD §7.2; tested in §12).
- **Keyboard focus for selectable layers.** Layers with `setInteractive(true)` expose
  `focusables()`; `SceneController` keeps one roving focus across layers ordered by render group,
  then `priority`, then distance to the camera target. The focused entity is drawn with a focus
  outline (a non-colour cue) and announced; Enter selects, Escape clears, arrows move within a
  layer, Tab moves across layers. The docked panel, inspector and search are the only overlays
  and are keyboard-reachable (SZ §8).
- **Text equivalents exposed to panels.** `textEquivalent()` returns one paragraph describing
  what the layer shows at `t` ("Rivers: 6 forecast points; Skagit at Mount Vernon observed
  10.6 ft NGVD29, below action 23.5 ft, rising 0.12 ft/h over 6 h [OBSERVED · 14 min]; official
  forecast crest 11.1 ft, category none [OFFICIAL · NWRFC]; 1 point STALE"). The scene
  description region concatenates visible layers' equivalents on band, time, selection and
  status changes.
- **Screen-readable intelligence.** The canvas is never the only carrier: every category,
  freshness mark, alert and disagreement visible on the map exists as text with badges in a
  panel or the inspector. Transitions to stale/degraded/missing are announced. Reduced motion
  per §4.7; contrast on dark glass per the react-quality skill.

## 12. Testing

Per [TESTING.md](TESTING.md) §6: deterministic, fixture contracts from `packages/contracts/fixtures/`,
fixed clock, fixed camera, no renderer instantiated in unit tests, never live data.

| Level | Test | Asserts |
|---|---|---|
| unit | layer visibility matrix | table-driven over SZ §4 + §4.2 rows × tier × viewport × event × presentation × intent × dependency status: `setVisible` transitions equal the resolver; a layer is never visible outside its bands; `low` never enables cinematic-only layers; `hiddenBy` reported |
| unit | state-to-style mapping | every `style.ts` function total; `unknown` never maps to calm; forecast ≠ observed by register; C-class never red; greyscale-distinguishable tokens; memoization stable on equal semantic input |
| unit | time-slice selection (`TemporalLayer`) | observed ≤ t; forecast nearest valid within the run issued ≤ asOf; seam at now/asOf; replay never mixes `as_of`; superseded runs only in evolution view; interpolation declared and absent from every channel `validTime` |
| unit | error isolation | a layer throwing in each lifecycle method is disposed, `degraded` + `renderFailure`, retried ≤ 3 with a fresh instance; other layers still receive `setTime`; dependents go `degraded` with reason |
| unit | provenance presentation | `toInspectorRecord` fields complete per shown channel; mixed-class layers list every channel; "OFFICIAL" only for `OFFICIAL_FORECAST`; EXPERIMENTAL badge on experimental methods; cartographic shows dataset + release |
| unit | scheduler | priority order, abort on band/time/asOf/selection change, prefetch bounds (§6.4), keys include `asOf`, cached slice keeps its STALE mark, one-way client escalation |
| contract | generated types vs fixtures | CI drift check (TESTING §4) |
| e2e | inspector and keyboard | degraded source shows STALE, not calm; keyboard path search → selection → panel → inspector |
| visual regression | scenes below | pixel diff under review override; label counts ≤ budget; badges present |

Visual regression scenes (fixed camera, fixed clock, fixture contracts; each also under
`reducedMotion` and on `low`): **Cascadia overview** (orbital: `hazard_summary`,
`atmosphere_ivt`, `official_alerts`), **Skagit basin** (basin: boundaries, rivers calm/watch mix,
`reservoirs`, `snow_cover`), **river selection** (`fp:nwps:MVEW1` selected: upstream/downstream
illumination, `thresholds`, `model_disagreement`), **snow layer** (`snow_cover`, `snow_points`,
`snow_level` with both fractions in the panel), **storm layer** (`precip_observed` 24 h,
`precip_forecast` 72 h with spread, `ar_corridor`), **event mode** (Event Zero replay; ASSUMPTION:
`as_of` 2025-12-11T18:00Z, before the 2025-12-12 08:15Z crest at Mount Vernon, HYDROLOGY §12),
**night mode** (Skagit scene with night tokens and analytical lighting), **degraded data** (one
source missing with reason, one stale-retained, one partial raster; UNKNOWN treatments visible).

## 13. Open questions (consolidated)

1. Names across the set, this document canonical, reconcile same day: layer `setQualityTier`
   (here, PERF §3/§7) vs `setQuality` (CA §8); `layers/contract.ts` (here, CA §12) vs
   `layers/types.ts` (CINEMATIC_ROADMAP §5.3); `RequestScheduler` in `scene/requests.ts` (here,
   SZ §7) vs `LayerDataBroker` in `scene/layer-data-broker.ts` (PERF §4.1); layer ids — this
   document and SZ §4 use `rivers`, `gauges`, `precip_observed`, `snow_level`, `local_detail`,
   while CINEMATIC_ROADMAP §1/§14 cite "LAYER_SYSTEM §8.2" for `river-network`,
   `gauges-forecast-points`, `precip-observed`, `snow-level-plane`, `ar-ivt-field` and PERF writes
   `local-detail`. Settled here for PERF's record: `budget()` is in §1 (PERF §7 OQ); the P3 wording
   matches PERF §4.1; cached documents age one-way in the client (§6.5; PERF §6 OQ).
2. Contract gaps shared with siblings: no `SoilVisualizationState` (SZ OQ-4, CA §17); no
   `snow_level.trend` (SZ OQ-5); no per-elevation-band rain fraction (HYDROLOGY §4) for
   `temperature_rain_snow`; no IVT spread raster for the AR forecast cone; no IVT vector components
   or terrain-aspect attribute for `ar_corridor` (§8.3); only `qpe_1h` / `qpf_6h` are named raster
   variables although §8.2 lists the 1–72 h and 6–120 h windows of ROADMAP Phase 2 and HYDROLOGY
   §4; no cloud-cover variable (VTD §3.6). Each is an additive minor bump proposed against
   VISUALIZATION_CONTRACTS.md.
3. ARCHITECTURE §6 lists `/basins/{id}/reaches` but no upstream/downstream-of-station query;
   routing illumination needs one, because the client must not compute topology.
4. `floodplain_modeled` depends on an authoritative inundation product being machine-accessible
   for these forecast points; until DATA_SOURCES.md records one the layer is absent, not approximated.
5. HEFS availability for `model_disagreement` (ROADMAP "what would change this roadmap").
6. `local_detail` sources and licensing (WA LiDAR, photogrammetry) are unrecorded until chosen.
7. SZ §4 matrix rows for the layers added in §4.2 must be merged into `scene/layerMatrix.ts`.
