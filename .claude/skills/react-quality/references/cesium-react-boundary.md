# The Cesium ↔ React boundary

Cascade Oracle's web app is a planetary-scale 3D observatory. React must never become the
graphics engine. These patterns keep the renderer fast and the science honest.

## Ownership

| Concern | Owner | Mechanism |
|---|---|---|
| Viewer lifecycle, scene, clock | `scene/SceneController` (plain TS class) | created once in a ref; disposed on unmount |
| Camera flights, orbit, follow | `camera/CameraController` | imperative API; emits `settled`/`interrupted` events |
| Layers (basins, rivers, snow…) | `layers/<name>/Layer` implementing `SceneLayer` | `mount(scene)`, `setTime(t)`, `setVisible(b)`, `setData(contract)`, `dispose()` |
| Semantic zoom | `scene/SemanticZoomController` | derives the altitude band from camera samples (hysteresis), emits `bandChanged`, toggles layer LOD |
| App state (selection, time, layers, quality) | Zustand store | semantic values only |
| Server data | TanStack Query | keyed by entity/time/layer/extent band |
| Panels, timeline UI, search | React components | read store + query; call controller methods |

## Rules with examples

**1. No per-frame React state.**

```ts
// BAD — setState on every camera move (60 Hz)
viewer.camera.changed.addEventListener(() => setAltitude(camera.positionCartographic.height))

// GOOD — controller quantizes to an altitude band and emits only on change
cameraController.onBandChange((band) => useSceneStore.getState().setAltitudeBand(band))
```

**2. No Cesium types in stores or props.**

```ts
// BAD
interface SceneState { selected: Cesium.Entity | null }

// GOOD
interface SceneState { selectedEntityId: EntityId | null }   // e.g. "station:usgs:12200500" or "fp:nwps:MVEW1"
```

**3. Bridge state → renderer in one place.**

```ts
// scene/bridge.ts — the only module that subscribes the store to the controllers
useSceneStore.subscribe(s => s.selectedEntityId, id => sceneController.select(id))
useSceneStore.subscribe(s => s.time, t => sceneController.setTime(t))
```

**4. Contracts in, pixels out.** A layer receives a backend visualization contract
(`BasinVisualizationState[]`) and maps semantic state to presentation through a single
per-layer `style.ts` module. RGB values, materials and shader names exist only in `layers/*/style.ts`.

```ts
// layers/basins/style.ts
export const basinFill = (state: SusceptibilityState, selected: boolean): Color => …
```

**5. Time is data, not animation.** The timeline sets `time` in the store; layers implement
`setTime` by selecting the correct time slice from already-fetched data or requesting the slice
through the query layer. Cesium's clock is driven from the store, not the other way around.

**6. Cancel obsolete work.** Every fetch triggered by camera extent or time carries an
`AbortSignal`; a band or time change aborts in-flight requests for the previous key.

**7. Failure isolation.** A layer that throws is unmounted and shown as `degraded` in the layer
inspector; it never unmounts the scene. Wrap panel trees in error boundaries; never wrap the
scene in one that would remount the viewer.

**8. Quality tiers are configuration.** `qualityTier` (ultra/high/balanced/low) is store
state; layers read it through the controller and degrade (fewer entities, no shaders, 2.5D).
Core intelligence (panels, timeline, provenance) must work on `low`.

## Testing the boundary

- Unit: `SemanticZoomController` band math, `CameraController` target framing, style
  mapping (semantic state → presentation), timeline math, provenance formatting — all pure TS.
- Contract: generated types match backend JSON Schema (`packages/contracts`), checked in CI.
- Visual regression: Playwright screenshots of fixed scenes with deterministic fixture data
  and a fixed clock; never against live data.
- Performance: Playwright + `performance.measure` around flights; FPS and tile counts logged;
  budgets in `docs/PERFORMANCE.md`.
