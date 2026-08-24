# CAMERA SYSTEM — the camera as a product feature

The camera is how Cascadia Papsukkal turns "the world is the interface" into something a person can
operate. It is owned by `apps/web/src/camera/` (a plain TypeScript module, not React — see
[`.claude/skills/react-quality/references/cesium-react-boundary.md`](../.claude/skills/react-quality/references/cesium-react-boundary.md)),
it consumes only stable ids, geometry and the semantic contracts in
[VISUALIZATION_CONTRACTS.md](VISUALIZATION_CONTRACTS.md), and it emits nothing upstream. No
backend contract contains a camera instruction (ADR-0007); camera changes never trigger scientific
recomputation; every cinematic effect it drives is labeled `cinematic` in the layer inspector.

Status 2026-08-22: Phase 0 design; ASSUMPTION numbers are starting values. Labels follow
[CONTEXT.md](CONTEXT.md). Siblings own: bands [SEMANTIC_ZOOM.md](SEMANTIC_ZOOM.md); layer ids and
fades [LAYER_SYSTEM.md](LAYER_SYSTEM.md); budgets and tiers [PERFORMANCE.md](PERFORMANCE.md); truth
classes [VISUAL_TRUTH_DOCTRINE.md](VISUAL_TRUTH_DOCTRINE.md); layout [CINEMATIC_ARCHITECTURE.md](CINEMATIC_ARCHITECTURE.md) §12.

## 1. Principles

1. **The camera moves only on user intent** — selection, search, deep link, bookmark, keyboard,
   a user-started tour. Never because data changed, never idling in motion, never shaking.
2. **Restraint over speed.** When framing and a motion budget conflict, framing relaxes (§4).
3. **Orientation is never lost.** Continuous descent, bounded rotation, horizon never crossed,
   target acquired before arrival, compass and scale always visible.
4. **Animation carries no information.** Every animated cue has a static equivalent; the
   reduced-motion path is complete (§8). Camera motion itself is class E, `cinematic`, driver =
   user intent ([VISUAL_TRUTH_DOCTRINE.md](VISUAL_TRUTH_DOCTRINE.md) §1.1 lists camera motion as E;
   its driver vocabulary has no entry for user input — §13).
5. **Reproducible by URL.** Any settled view is a short deep link (§7).
6. **Presentation stays on the client.** Colours, materials, exaggeration, atmosphere, lighting
   live in `layers/*/style.ts`, `camera/` and `layers/cinematic/`; contracts carry none of them.

## 2. Camera state model

The controller owns the live pose (updated per frame); the store's `camera` slice holds the coarse
projection — `band`, `extentKey`, `reducedMotion` (CINEMATIC_ARCHITECTURE.md) plus `mode`, `focus`,
`lighting` proposed here — updated on change, never per frame. `scene/bridge.ts` is the only bridge.

```ts
// apps/web/src/camera/types.ts — our own module; no renderer types appear here.
export type EntityId = string;            // DOMAIN_MODEL.md §1: "basin:skagit", "fp:nwps:MVEW1", "station:usgs:12200500"
export type SemanticBand = 'orbital' | 'state' | 'basin' | 'river' | 'local';   // VISUALIZATION_CONTRACTS.md §8
export type CameraMode = 'free' | 'fly' | 'orbit' | 'follow-river' | 'playback' | 'presentation';
export type MotionPreference = 'full' | 'reduced';                               // resolved, §8
export type LightingMode = 'analytical' | 'solar';                               // §11

export interface GeoPoint { lat: number; lon: number }                           // WGS84 degrees

export type CameraTarget =
  | { kind: 'entity'; id: EntityId }                   // geometry resolved from the client geography cache
  | { kind: 'point'; point: GeoPoint }
  | { kind: 'reaches'; reachIds: EntityId[] };         // contiguous in flow order (validated, §5.3)

/** Look-at parametrization. Position is derived from (target, range, heading, pitch) + terrain. */
export interface CameraPose {
  target: GeoPoint;          // ground point under the view centre; its terrain height is sampled, never stored
  rangeM: number;            // camera-to-target distance along the view ray
  headingDeg: number;        // [0, 360): 0 = north, clockwise
  pitchDeg: number;          // [-90, PITCH_MAX_DEG]: -90 = straight down (PITCH_MAX_DEG = -12, ASSUMPTION)
  rollDeg: 0;                // constrained to 0 in every mode; present so tests can assert it
}

export interface CameraState {
  pose: CameraPose;
  position: GeoPoint & { heightAboveTerrainM: number; heightAboveEllipsoidM: number };  // derived
  focus: CameraTarget | null;       // what the camera is framing semantically (an id or a point)
  band: SemanticBand;               // SEMANTIC_ZOOM.md §1 band math, derived once (`scene/bands.ts`); ownership §13
  mode: CameraMode;
  motion: MotionPreference;
  lighting: LightingMode;
  flight: { id: string; target: CameraTarget; progress: number; resumable: boolean } | null;
}
```

Mode semantics:

| Mode | Camera driven by | Leaves on |
|---|---|---|
| `free` | user input (pointer, touch, keyboard) | any programmatic flight |
| `fly` | an active flight tween | settle or interrupt (transient; never persisted or deep-linked) |
| `orbit` | slow circular path around `focus` at fixed range/pitch | user input, flight |
| `follow-river` | traversal along a reach path (§5.3) | user input, end of path, flight |
| `playback` | keyframes keyed by timeline valid time (§3.3) | user input (unbinds; timeline keeps playing) |
| `presentation` | a tour (§10) | user input pauses; `resume()` continues |

Height above terrain is the controlled variable everywhere; with ellipsoid terrain (the keyless
default of ADR-0006, and `low`) it equals height above ellipsoid, and the HUD says so.

## 3. CameraController API

```ts
export interface FlightOptions {
  durationMs?: number;                 // override; still clamped to [MOTION.flight.minMs, MOTION.flight.maxMs]
  heading?: number | 'keep' | 'north' | 'downstream';   // 'downstream' only for river/station targets (§5.2)
  pitch?: number | 'keep';             // default: per-band default (§5.1)
  rangeM?: number;                     // overrides framing range
  paddingFactor?: number;              // framing padding; default per band
  arc?: 'auto' | 'none';               // pull back before descending when the target is out of view (§4.3)
  sequence?: 'basin-select' | 'entity-select' | 'none';  // motion-system composition bound to progress (§4.5)
  settleMode?: Exclude<CameraMode, 'fly'>;               // mode after settle; default 'free'
  reason: 'selection' | 'search' | 'deep-link' | 'bookmark' | 'tour' | 'keyboard' | 'restore';
  signal?: AbortSignal;                // programmatic cancellation (tours); user input needs no signal
}

export interface FlightHandle {
  id: string;
  settled: Promise<FlightResult>;      // resolves on settle OR interrupt; never rejects; React never awaits it
  interrupt(reason?: InterruptReason): void;
}
export interface FlightResult { outcome: 'settled' | 'interrupted'; pose: CameraPose; band: SemanticBand; cut: boolean }

export interface OrbitParams { rangeM?: number; pitchDeg?: number; degPerSecond?: number /* ≤ MOTION.orbit.maxDegPerS (§9) */ }
export interface FollowParams { speedMPerS?: number; heightAboveTerrainM?: number; pitchDeg?: number; dwellAtForecastPointsMs?: number }
export interface Bookmark { id: string; name: string; pose: CameraPose; focus: CameraTarget | null; mode: 'free' | 'orbit' | 'follow-river'; createdAt: string }
export interface CameraKeyframe { validTime: string; pose: CameraPose; focus?: CameraTarget }   // ISO 8601 UTC
export type InterruptReason = 'user-input' | 'superseded' | 'tour-paused' | 'abort-signal' | 'reduced-motion-change';

export interface CameraController {
  getState(): CameraState;
  flyTo(target: CameraTarget, options: FlightOptions): FlightHandle;
  frame(id: EntityId, options?: Partial<FlightOptions>): FlightHandle;         // dispatches on id namespace (CINEMATIC_ARCHITECTURE.md §4.1)
  frameEntity(id: EntityId, options?: Partial<FlightOptions>): FlightHandle;   // station/fp/reach/reservoir/place
  frameBasin(id: EntityId, options?: Partial<FlightOptions>): FlightHandle;    // basin:* only; sequence 'basin-select' by default
  orbit(target: CameraTarget, params?: OrbitParams): void;
  setHeading(deg: number, tween?: boolean): void;        // tween: MOTION.duration.ui with easing.calm; cut under reduced motion
  setPitch(deg: number, tween?: boolean): void;          // clamped to [-90, PITCH_MAX_DEG]
  setTilt(degFromNadir: number, tween?: boolean): void;  // alias: setPitch(degFromNadir - 90)
  followRiver(reachIds: EntityId[], direction: 'downstream' | 'upstream', params?: FollowParams): FlightHandle;
  descendTo(heightAboveTerrainM: number, options?: Partial<FlightOptions>): FlightHandle;   // terrain-following, same target
  restorePrevious(): FlightHandle | null;                // pops the pose history (§3.2)
  bookmarks: { save(name: string): Bookmark; restore(id: string): FlightHandle | null; list(): Bookmark[]; remove(id: string): void };
  bindPlayback(keyframes: CameraKeyframe[]): void;       // mode 'playback'; §3.3
  unbindPlayback(): void;
  interrupt(reason: InterruptReason): void;              // §6
  resume(): FlightHandle | null;                         // re-targets the last resumable flight from the current pose
  setMotionPreference(p: MotionPreference): void;
  setLighting(mode: LightingMode): void;
  on<E extends keyof CameraEvents>(event: E, handler: (e: CameraEvents[E]) => void): () => void;
}

export interface CameraEvents {
  started:     { flightId: string; target: CameraTarget; durationMs: number; cut: boolean; reason: FlightOptions['reason'] };
  progress:    { flightId: string; progress: number; band: SemanticBand };        // ≤ 10 Hz or on 5 % steps, never per frame; `band` feeds the HUD label only, never a fetch (§3.1)
  settled:     { flightId: string; pose: CameraPose; band: SemanticBand; cut: boolean };
  interrupted: { flightId: string; progress: number; pose: CameraPose; reason: InterruptReason; resumable: boolean };
  cameraSample: { pose: CameraPose; heightAboveTerrainM: number; pitchDeg: number; moving: boolean };   // ≤ 10 Hz while moving, plus on settle; SemanticZoomController derives the band from it (DECIDED, §13)
  modeChange:  { from: CameraMode; to: CameraMode };
}
```

### 3.1 Method semantics

`frame*` compute the pose with the pure functions of §5.1 from client geography only, then call
`flyTo`. `descendTo` keeps `pose.target` and lowers height above terrain monotonically. Band
emission follows SEMANTIC_ZOOM.md §5: in free navigation each threshold crossing emits once; a
programmatic flight emits **one** band event for its destination band (`cause: 'jump'`) — at
`started`, so the destination band's `SceneSummary` is in flight during the descent (§4.5
prefetch row; previous key aborted — boundary rule 6) and intermediate bands are never fetched.
The camera never fetches; it declares targets and emits events. Single-axis setters tween over `MOTION.duration.ui`
(cuts under reduced motion). Every moving method is interruptible; nothing can lock a flight (§6).

### 3.2 Pose history and bookmarks

A bounded history (depth 20, ASSUMPTION) of *resting* poses: pushed on `settled` of programmatic
flights and after 1,000 ms (ASSUMPTION) of idle free navigation. `restorePrevious()` flies to the
top entry with `reason: 'restore'` and pops it. Bookmarks are client-local, serialize to exactly
the `cam=` grammar of §7, and are not a sharing mechanism — deep links are.

### 3.3 Playback binding

`bindPlayback(keyframes)` attaches the camera to the timeline's valid time. Between keyframes the
pose is interpolated with `MOTION.profile.flight`; at a scrub (non-monotonic or large time jump)
the camera cuts to the keyframe pose — scrubbing never produces a flight. Time remains data
(boundary rule 5): the store's `time` drives both the layers' `setTime` and the camera; the camera
never sets time.

## 4. Cinematic flight behaviour

### 4.1 Style

Weighted, intentional, smooth, physically plausible, restrained. The references are a scientific
documentary, satellite reconnaissance, and high-end geographic visualization: the camera is a
heavy instrument on a stable mount, not a drone. Explicitly excluded: spinning or more than one
half-turn per flight, snap zoom (high initial velocity), constant auto motion (idle drift, "breathing"
camera), dramatic shake, game-like effects (FOV punch, motion blur, speed lines), gimmicky drone
moves (barrel rolls, whip pans, orbit-on-arrival). Roll is 0 always.

### 4.2 Easing and velocity profiles

- **Path progress** uses a minimum-jerk quintic `s(u) = 10u³ − 15u⁴ + 6u⁵` (zero velocity and
  acceleration at both ends; peak velocity 1.875× the mean). It is chosen over the V1 cubic-bezier
  tokens for the camera because those are ease-out-dominant (`standard` starts near full speed) and
  would read as snap zoom on a 3D camera. It is `MOTION.profile.flight` (§9), not a per-component choice.
  INFERENCE: this profile, the separate tracks below and the C¹ superseding of §6 need a
  controller-owned per-frame tween driven from the renderer's pre-render hook, not the renderer's
  built-in flight; PERFORMANCE.md §7 rule 3 lists flights among renderer-native mechanisms (§13).
- **Orientation (heading, pitch)** blends with `MOTION.easing.calm` over its own track, so
  rotation settles before translation does.
- **Height above terrain** follows its own monotone track (descents never bounce); with `arc:
  'auto'` the track is a single smooth hump (§4.3).
- Peak angular rates (ASSUMPTION): heading ≤ 40°/s, pitch ≤ 20°/s. A flight may rotate at most
  180° (shortest signed arc). If the preferred heading cannot be reached within
  `sequence.headingPhaseEnd × durationMs` (§4.4) at those rates, the framing policy accepts a
  heading up to 45° from preferred rather than rotating faster.

### 4.3 Duration as a function of distance

```ts
export function computeFlightDuration(from: CameraPose, to: CameraPose, f = MOTION.flight): number {
  const groundKm = greatCircleKm(from.target, to.target);
  const heightKm = Math.abs(heightAboveTerrainM(from) - heightAboveTerrainM(to)) / 1000;
  const effectiveKm = groundKm + f.heightWeight * heightKm;                   // heightWeight = 2
  const raw = f.baseMs + f.perDoublingMs * Math.log2(1 + effectiveKm / f.scaleKm);   // 600 + 550·log2(1 + d/5)
  return clamp(raw, f.minMs, f.maxMs);                                        // [600, 4200] ms
}
```

| Effective distance | Duration | Typical case |
|---|---|---|
| 1 km | ≈ 750 ms | nudge between two gauges on one reach |
| 10 km | ≈ 1.5 s | gauge → downstream forecast point |
| 50 km | ≈ 2.5 s | basin → neighbouring basin at basin band |
| 200 km | ≈ 3.5 s | Nooksack → Puyallup at state band |
| orbital (≈ 900 km; SEMANTIC_ZOOM.md clamps at 1000 km) → basin | 4.2 s (cap) | the basin-selection descent |

All constants are ASSUMPTION. Tiers (PERFORMANCE.md §3): `balanced` × 0.8 and no `arc`; `low` cuts (§8).
Arc rule: when the destination footprint is outside the current view, the height track rises until
both footprints fit (bounded by the next band up, never orbital for an intra-state hop), then
descends — pull back, re-acquire, descend. Short hops (`arc: 'none'`) translate without climbing.

### 4.4 Orientation preservation

- Pitch stays within `[-90°, PITCH_MAX_DEG]`; the horizon is never crossed; sky-only frames are
  impossible by construction.
- The target enters the frame by progress 0.6 (the *acquisition point*) and stays; the selected
  entity's boundary starts fading in ahead of it (p ≈ 0.35, §4.5) so the eye has an anchor
  before arrival.
- The heading track completes first (0–0.55, `sequence.headingPhaseEnd`) when |Δheading| > 15°:
  the camera is turned toward the basin by acquisition, while translation and descent run over
  the whole flight (§4.2: orientation settles before translation does).
- Compass, scale bar and band label are always rendered and update continuously.
- **No map jumps.** A flight is a continuous function of progress; the scene is never torn down
  mid-flight; bands change by threshold crossing, not by reloading a view. The only discontinuity
  is the reduced-motion cut (§8), and it is veiled.

### 4.5 The basin-selection sequence

Triggered by `frameBasin(id)` (selection, search, deep link with `sel=basin:*` and no `cam`): the
camera rotates toward the basin, descends, terrain exaggeration subtly increases, the basin boundary
fades in, the atmospheric layer reduces, the river network resolves, the intelligence panel appears.
Tracks are keyed to flight progress `p`, not wall-clock, so interruption and reduced motion map
cleanly; the motion system (§9) owns the composition — no layer or panel times itself.

```
p            0       .15      .35      .55      .75      .90     1.0  settle
heading      [rotate toward basin, calm]                                              (settled by .55)
path         [translate + descend, minimum-jerk, terrain-following ....................]
prefetch     [target declared at `started` → query-layer prefetch, bounded (PERFORMANCE.md §4.5)]
exaggeration                  [terrain ×1.00 → ×1.35, easing.calm .....................]   cinematic; HUD: "terrain ×1.35"
basin bound.                  [`watershed_boundaries` fade in, duration.state, calm ...]   cartographic
atmosphere                             [`atmosphere_haze`: state-band → basin-band `reduced`, calm]  cinematic (LAYER_SYSTEM.md §4.2)
rivers                                          [`rivers`, `gauges` LOD resolve + fade in, duration.state]   (ids: LAYER_SYSTEM.md §8.2)
panel                                                                        [duration.panel, easing.standard]
```

Rules: the panel is driven by `selectedEntityId` (state), not by the camera — it appears at settle
for continuity, but an interrupted flight still shows it. The camera never fetches (a fetch inside a
flight is a named anti-pattern in CINEMATIC_ARCHITECTURE.md §15). Terrain exaggeration is class E: while
the factor ≠ 1, every terrain-relative scientific element (the `snow_level` plane, station elevations,
hypsometric bands) is transformed by the same factor, HUD and inspector show it, and it resets to
×1.0 on leaving the basin band (doctrine ruling requested, §13). Snow, storm and river layers are
never faded as a function of the camera in a way that could read as data changing (HYDROLOGY.md §7).

## 5. Focus behaviour

### 5.1 Automatic framing (pure functions)

```ts
export interface ViewParams { fovYRad: number; aspect: number }
export interface BoundingSphere { center: GeoPoint; radiusM: number }

export function rangeForSphere(s: BoundingSphere, v: ViewParams, padding: number): number {
  const halfH = Math.atan(Math.tan(v.fovYRad / 2) * v.aspect);
  const halfFov = Math.min(v.fovYRad / 2, halfH);
  return (s.radiusM * padding) / Math.sin(halfFov);
}
export function framePose(s: BoundingSphere, v: ViewParams, band: SemanticBand, headingDeg: number): CameraPose
```

| Target kind | Geometry source | Band | Default pitch | Padding | Heading policy |
|---|---|---|---|---|---|
| `basin:*` | display polygon at `basin` LOD (`geometry_ref`) | basin | −38° | 1.25 | keep if within 60° of north-up, else north |
| `station:*`, `fp:*` | point + downstream context (§5.2) | river | −28° | 1.4 | `downstream` (flow azimuth at the gauge) |
| `reach:*` / reach set | polyline bounding sphere | river | −28° | 1.3 | principal axis, oriented downstream |
| `reservoir:*`, `dam:*` | pool polygon / point | river | −32° | 1.3 | keep |
| `place:*`, `area:*` | polygon | local | −24° | 1.2 | keep |
| region (no selection) | Washington extent | state/orbital | −75° | 1.0 | north |

Values are ASSUMPTION. The range is validated against terrain (`MIN_CLEARANCE_M`, 120 m,
ASSUMPTION), relaxing pitch toward the band default if clearance fails. Framing needs geometry
only, never fetched science, so the camera can move while the `SceneSummary` is still in flight.

### 5.2 Gauge selection with downstream awareness

Selecting `station:usgs:12200500` (or its `fp:nwps:MVEW1`) frames not the point but the *context
set*: the gauge plus its ordered downstream reaches as the API serves them (the reach-graph walk
is server-side, DOMAIN_MODEL.md §4; the client maps ids to geometry and walks no graph,
LAYER_SYSTEM.md §9.4), truncated at the next forecast point from `topology.downstream` or at
`DOWNSTREAM_CONTEXT_KM = 15` of summed reach `length_km`, ASSUMPTION, whichever comes first. No
upstream/downstream-of-station endpoint exists yet (LAYER_SYSTEM.md §13 item 3; §13 here). The
camera sits upstream looking downstream (heading = flow azimuth), so the gauge rests in the
lower third of the frame and the water's direction reads as "ahead".

Network context cues (presentation-only, `layers/rivers/style.ts`): the upstream contributing
network softly emphasizes ("what feeds this gauge"); downstream reaches emphasize differently
("where this water goes"), decaying with graph distance to the next forecast point. Both are
read from served topology (`RiverVisualizationState.topology`, the API's reach lists); neither uses the hazard
category mapping, and the legend says "network context — topology, not a forecast". In full
motion the downstream cue resolves once along flow direction over `duration.state`; it never
loops. A regulated reach (`regulation.class`) keeps its regulation badge inside the cue.

### 5.3 River-follow mode

`followRiver(reachIds, 'downstream')`: validate contiguity in flow order (typed error otherwise);
build a smoothed path through the reach vertices (a spline; interpolant is an implementation
choice); move the ground target along it at `speedMPerS` (river band 60, local 25 — ASSUMPTION) with
minimum-jerk ramps; heading = low-pass-filtered tangent (500 m window); pitch fixed; height above
terrain constant. `progress` events carry the reach id under the target so the panel follows.
Optional dwell at forecast points. `'upstream'` reverses the path; heading still points along travel.

## 6. Interruptions

```
free ──flyTo──▶ fly ──settled──▶ settleMode (free | orbit | follow-river)
 ▲               │
 │          user input / superseded / abort
 │               ▼
 └──────── interrupted (camera stays exactly where it is; flight.resumable = true) ──resume()──▶ fly
```

Guarantees:

1. **Immediate.** Any pointer, wheel, touch or navigation key calls `interrupt('user-input')` on
   the same frame; the tween stops; the camera holds its current interpolated pose — no snap back,
   no snap forward. Exactly one `interrupted` is emitted; no `settled` follows.
2. **Never blocking.** Flights are per-frame tweens with a cancel token; input handlers are live
   throughout; `FlightHandle.settled` serves tours (with their `AbortSignal`); React never awaits it.
3. **Resumable.** The interrupted target stays in `state.flight` until the next programmatic
   flight or selection change; `resume()` re-plans from the current pose. Never auto-resumes.
4. **Superseding.** A new `flyTo` mid-flight interrupts the old one (`'superseded'`) and starts
   from the current pose *and velocity*: the first 15 % of the new path blends from the inherited
   velocity, so direction changes are C¹-continuous.
5. **Sequence tracks:** past 0.5 complete over `duration.ui`, before 0.5 revert over `duration.ui`;
   prefetches belong to the query layer and are cancelled by its own key rules (PERFORMANCE.md §4).
6. **Selection is independent.** Interrupting never deselects; the panel stays.

## 7. Deep linking

A settled view is a short URL. Path = primary scope; query = time, mode, layers, selection, camera.
No session blobs, bookmark lists, panel scroll, styling or quality tier. Target total length
< 512 characters (ASSUMPTION).

| Part | Grammar | Meaning | Absent ⇒ |
|---|---|---|---|
| path | `/` · `/basin/<slug>` · `/event/<yyyy-mm>-<slug>` | scope: region, `basin:<slug>`, `event:<…>` | region |
| `t` | ISO 8601 UTC | valid time shown (`time.valid` of the contracts) | live now (not reproducible) |
| `as_of` | ISO 8601 UTC | knowledge time for replay (`as_known_at`, ARCHITECTURE.md §6) | now |
| `mode` | `now` · `past` · `forecast` · `event` · `presentation` | view mode; first three equal contract `time.mode`; `event` implies replay of the path's event; `presentation` starts the tour (§10) | derived from `t` |
| `layers` | comma list of layer ids ([LAYER_SYSTEM.md](LAYER_SYSTEM.md) §8.2, e.g. `rivers`, `gauges`, `snow_level`) or panel group aliases (`snow` → `snow_cover,snow_points,snow_level`), expanded client-side before the registry (LAYER_SYSTEM.md §4.3: the registry knows no groups) | visible layers | band defaults |
| `sel` | one `EntityId` | selected entity (panel subject) | none |
| `cam` | `1~<anchor>~<rangeM>~<headingDeg>~<pitchDeg>[~<mode>]` | compact camera target, version 1 | frame `sel`, else scope |

`anchor` is `e:<EntityId>` (look-at an entity's framing centre) or `g:<lat>,<lon>` (4 decimals ≈ 11 m;
free views only — anything entity-shaped uses `e:`).
`rangeM` has 3 significant figures; heading and pitch are integer degrees; `mode` ∈ `orbit` ·
`follow` and is omitted for `free`. `fly`, `playback` and `presentation` are never encoded as
camera modes. Examples:

```
/basin/skagit?t=2026-08-22T09:00:00Z&mode=forecast&layers=snow,rivers&cam=1~e:basin:skagit~95000~180~-40
/basin/skagit?t=2025-12-12T08:15:00Z&as_of=2025-12-12T08:15:00Z&mode=past&layers=rivers&sel=fp:nwps:MVEW1&cam=1~e:fp:nwps:MVEW1~18000~205~-32
```

Rules: **stable ids only** — `basin:skagit` is `/basin/skagit`, every other entity its full
namespaced id, display labels never. **Load is a cut** regardless of motion preference (screenshots
and debugging need the first frame to be the final frame); later actions fly normally. **`cam` wins
over `sel`** when both are present; `sel` alone frames the entity. **Round trip:**
`decode(encode(state))` re-frames within 1 % of range and 1° (property test, §12); encoding is a
pure function in `camera/deep-link.ts`. **Pin for sharing:** "copy link" offers "pin time", writing
`t` and `as_of = now` so the link is a pure function of the database at that instant
(VISUALIZATION_CONTRACTS.md §10 rule 3). **Versioned:** the leading `1` is the grammar version;
unknown versions fall back to `sel`. **No personal data:** ids, times, layer ids and numbers only.

## 8. Reduced motion

`motion` resolves as `userSetting ?? (prefers-reduced-motion ? 'reduced' : 'full')`, where the
setting is tri-state `system | reduced | full` and an explicit choice wins. Changing it mid-flight
interrupts with `'reduced-motion-change'` and completes by cut. Quality tier `low` shares the cut
path; reduced motion never changes the tier ([PERFORMANCE.md](PERFORMANCE.md) §3).

| Transition | Full motion | Reduced motion |
|---|---|---|
| `flyTo` / `frame*` / `descendTo` | flight (§4) | veil in (`duration.micro`) → cut → veil out (`duration.ui`); opacity only |
| basin-selection sequence | tracks bound to progress | cut behind the veil; layer tracks instant (LAYER_SYSTEM.md §4.7: camera-coupled fades become instant); panel fades in (`duration.panel`, opacity only) |
| `orbit` | continuous orbit | disabled; heading steps of 45° by keyboard, each a cut |
| `followRiver` | traversal | stepwise: cut per reach or forecast point with veil; the panel lists the stops |
| tour (§10) | flights between stops | slideshow of cuts with veil; advance by key/button or dwell timer |
| `setHeading` / `setPitch` | `duration.ui` tween | cut |
| risk-state change | `duration.state` | instant; opacity/contrast change only (V1 rule, `v1/design_guidelines.md` `motion.reduced_motion`) |
| ambient shimmer | `duration.ambient` loop on panel accents | off |
| timeline scrub | always a cut | cut |

Scientific information never depends on animation: the downstream cue has a legend entry and a
panel list of downstream ids; `tension` drives a static accent as well as the pulse; freshness and
STALE marks are static text; the tour's captions are readable without the flights. Reduced motion
is an E2E scenario, not a branch (TESTING.md §6).

## 9. Motion system

One module, `apps/web/src/design-system/motion.ts` (CINEMATIC_ARCHITECTURE.md §12 layout), is the
only place a duration or easing may be written.
Components, layers and the camera import tokens; a numeric duration elsewhere fails review
(proposed line for the react-quality pre-commit checklist, `SKILL.md` §6, which today covers only
the reduced-motion path). Tokens are carried forward from V1 per [V1_AUDIT.md](V1_AUDIT.md) §7
item 5 ("restrained motion … reduced-motion rule"); the literal values are FACT from
`v1/design_guidelines.md` (`motion.easing`, `motion.duration_ms`), adopted unchanged.

```ts
export const MOTION = {
  easing: {
    standard: [0.22, 1, 0.36, 1],   // default for UI and risk-state transitions
    snappy:   [0.2, 0.9, 0.2, 1],   // micro feedback (hover, selection tick)
    calm:     [0.16, 1, 0.3, 1],    // layer fades, orientation blends, anything large on screen
  },
  duration: { micro: 140, ui: 220, panel: 320, state: 520, ambient: 2400 },   // ms
  profile: { flight: 'minimum-jerk' },                                         // §4.2; path progress only
  flight: { minMs: 600, maxMs: 4200, baseMs: 600, perDoublingMs: 550, scaleKm: 5, heightWeight: 2,
            headingMaxDegPerS: 40, pitchMaxDegPerS: 20, balancedTierScale: 0.8 },   // ASSUMPTION
  sequence: { acquisitionPoint: 0.6, headingPhaseEnd: 0.55 },
  orbit: { maxDegPerS: 6 },                                                    // ASSUMPTION: at most one turn per minute
} as const;
export type MotionTokens = typeof MOTION;
```

| Transition | Duration | Easing | Owner |
|---|---|---|---|
| camera flight path | `computeFlightDuration` | `profile.flight` | `camera/` |
| camera orientation track | same flight | `easing.calm` | `camera/` |
| keyboard camera step | `ui` | `calm` | `camera/` |
| panel open / close / swap | `panel` | `standard` | panels |
| selection highlight, hover | `micro` | `snappy` | layers, panels |
| layer show / hide / LOD fade | `state` | `calm` | `layers/*` |
| risk-state change (badge, rim, basin fill) | `state` | `standard` | `layers/basins/style.ts`, panels |
| timeline play: time-slice change | cut (≤ `ui` opacity crossfade) | — | layers (`setTime`) |
| timeline scrub feedback | `ui` | `snappy` | timeline |
| ambient accent shimmer (panels only) | `ambient` | `calm` | panels |

Rules: (1) **hierarchy** — the larger the change, the longer the token (`state` > `panel` > `ui` >
`micro`); (2) **continuity** — an element present before and after a transition moves or fades
in place, it is never unmounted and remounted; (3) **one primary motion** — while the camera
flies, every other animation is subordinate and gated to its progress; (4) **time slices are never
interpolated as values** — a crossfade between two valid times is opacity only; the parametric
forms LAYER_SYSTEM.md §2.4 permits (snow-level plane, flow phase) are declared
`cinematic_continuity` and never reach a panel, label or number; (5) **persistent motion is bounded** — the camera
never carries it; `ambient` governs panel accents; layer-level animation (animated river texture,
transport fields) is class E with a declared driver (VISUAL_TRUTH_DOCTRINE.md) and freezes under
reduced motion (LAYER_SYSTEM.md §4.7).

## 10. Event Mode and Presentation Mode

Both are *tours*: ordered stops, each a camera target, band, layer set and dwell. They use the same
`SceneSummary` requests and the same contracts as interactive use — there is no separate
scientific pipeline, no pre-rendered video, no narration audio (ROADMAP.md rejects audio). Captions
are rendered from the structured explanation payload (HYDROLOGY.md §11; VISUALIZATION_CONTRACTS.md
§9), never free text, and every caption keeps its `source_kind` badge, freshness and `as_of`.

```ts
export interface TourStop { id: string; target: Exclude<CameraTarget, { kind: 'point' }>;   // ids, never raw coordinates (CINEMATIC_ROADMAP.md C6)
                            band: SemanticBand; layers: string[]; dwellMs: number;
                            follow?: { reachIds: EntityId[]; direction: 'downstream' | 'upstream' };   // stop 5
                            captionRef?: { scope: EntityId; surface: 'susceptibility' | 'forcing' | 'hazard' | 'model_agreement' } }
export interface TourDefinition { id: string; stops: TourStop[]; time: { t: string; asOf?: string }; loop: false }
```

Default auto-tour (stops are skipped, not faked, when the basin lacks the entity):

| # | Stop | Target / band | Data shown |
|---|---|---|---|
| 1 | regional system | Washington extent, `orbital` | `HazardVisualizationState`, weather region fields, `ar` if present |
| 2 | affected basin | `basin:<id>`, `basin` (sequence §4.5) | `BasinVisualizationState` surfaces and `headline_drivers` |
| 3 | storm field | basin, `basin`, pitch −55° | `WeatherVisualizationState` `qpf`/`ivt` fields with `issued_at` |
| 4 | snowline | basin, `basin`, focus on the transient band | `SnowVisualizationState` `snow_level`, rain-on-snow fraction |
| 5 | river | outlet `fp:*`, `river`, short `followRiver` | `RiverVisualizationState` observed + official forecast |
| 6 | reservoir | `reservoir:*` if `regulation_class ≠ natural`, `river` | `ReservoirVisualizationState` buffer |
| 7 | downstream community | `place:*`/`area:*` downstream of the outlet, `local` | exposure attributes only; no depth, extent or impact claim (HYDROLOGY.md §13) |

Event Mode: `mode=event`, time from the event's `EventTimelineEntry` rows, every fetch with
`as_of` (ADR-0010); the camera is bound via `bindPlayback` to keyframes at entry times, so
scrubbing the event timeline moves both time and view. Presentation Mode: the same tour with
`t = now`, hidden chrome, larger type, solar lighting permitted (§11); a dwell at an orbital,
state or basin stop may use `orbit` (SEMANTIC_ZOOM.md §10; ≤ `MOTION.orbit.maxDegPerS`, never at
local, off under reduced motion) — entering the mode is the user intent of principle 1. Authored
stops reference entity ids and bands, never raw coordinates (CINEMATIC_ROADMAP.md C6). Both are
interruptible: any input pauses (`'tour-paused'`), the camera stays, "Resume tour" continues
from the current stop. Tours never loop and never start without a user action.

## 11. Lighting and time coupling

`lighting` is a frontend presentation mode, labeled `cinematic`:

- `analytical` (the default; the default again whenever the scene is in elevated or event state;
  the only mode on `low`, where lighting is off —
  [VISUAL_TRUTH_DOCTRINE.md](VISUAL_TRUTH_DOCTRINE.md) §3.8): fixed, even lighting; scientific
  overlays render independent of scene lighting so legibility never depends on the sun.
- `solar`: sun direction computed from the selected valid time `t` — current, historical event
  (Event Zero crest 2025-12-12 08:15Z is 00:15 PST, night), or forecast valid time. Deterministic
  from time (astronomy, FACT); INFERENCE that the renderer can take a sun direction, otherwise our
  own solar-position utility supplies it.

Rules: the HUD states the lighting mode and the time it derives from ("lighting: solar, forecast
valid 2026-08-23 15:00 PDT") so night shading is never mistaken for data; lighting never encodes
risk or any scientific value; no clouds, rain or snow are synthesized from lighting or from the
time of day — weather appears only as fields with provenance; the **readability floor** keeps
overlays and labels at full contrast in every lighting mode (verified at both lighting extremes in
visual regression, VISUAL_TRUTH_DOCTRINE.md §3.8); `solar` is a user toggle or a
Presentation Mode default, never automatic in analysis.

## 12. Testing

Per [TESTING.md](TESTING.md) §1 and §6; camera logic is pure TypeScript wherever it can be.

- **Unit (pure functions):** `rangeForSphere`, `framePose`, `computeFlightDuration`, shortest-arc
  heading, pitch clamping, `minimumJerk`, sequence gates, downstream context set, follow-path
  contiguity, `encode`/`decode` of `cam`.
- **Property tests:** duration monotone in distance and within `[minMs, maxMs]`; |Δheading| ≤ 180°;
  roll 0 and pitch in bounds for every pose; the framed sphere fits the view for aspect 0.5–3;
  `decode(encode(x))` within 1 % range and 1°; an `UNKNOWN`-only scene still frames (geometry, not
  science, drives framing).
- **Interruption:** interrupt at every 5 % of progress ⇒ pose equals the interpolated pose (no
  jump), exactly one `interrupted`, no `settled`; `resume()` reaches the target; superseding flights
  keep C¹ continuity (finite-difference velocity check).
- **Deep-link round trips:** table-driven over the six seed basins and their forecast points;
  unknown grammar versions fall back to `sel`; labels never appear.
- **Reduced motion:** every flight resolves within `duration.micro + duration.ui + 50 ms` with
  `cut: true`; the E2E "search Skagit → cuts" path passes; no `orbit`/`follow` animation runs.
- **Visual regression:** fixed scenes are deep links with `t`, `as_of`, `cam` pinned; fixture
  contracts; fixed clock.
- **Performance** ([PERFORMANCE.md](PERFORMANCE.md) §2; budgets `flight_frame_time`, `band_settle`,
  `tile_requests_per_band`): flights wrapped in `performance.measure`; on `high`, Tier A: frame time
  p50 ≤ 16.7 ms (60 fps) during flight and free orbit, floor p95 ≤ 33 ms; ≤ 350 tile requests per
  `orbital → basin` flight; idle frame cost ≤ 4 ms (a still camera renders nothing).
- **Accessibility:** keyboard path (arrows pan, `+`/`−` zoom step, `[`/`]` heading step) reaches
  every band; focus never lands in the canvas without a visible outline.

## 13. Open questions

- RESOLVED 2026-08-22: the boundary reference now uses `station:usgs:<site_no>` ids (DOMAIN_MODEL.md §1).
- DECIDED 2026-08-22: `SemanticBand` includes `ground`; the contract enum gains it in the 1.1.0 bump
  (CINEMATIC_ARCHITECTURE.md §17). The camera reports the derived band only for HUD labels.
- OPEN QUESTION: VISUAL_TRUTH_DOCTRINE.md does not rule on terrain exaggeration, and ×1.35 sits
  uneasily beside its §7.1 "the Earth still looks like Earth" and this document's own "physically
  plausible" (§4.1). This document treats it as class E with the same-factor rule of §4.5; the
  doctrine should confirm it (with a ceiling) or forbid it.
- OPEN QUESTION: the `mode` query parameter extends the contract's `time.mode` (`now|past|forecast`)
  with `event` and `presentation`; if the API grows a view-mode notion the vocabularies must merge.
- OPEN QUESTION: V1_AUDIT.md §2 says the design tokens are to be "re-authored" into a clean
  design-system spec; `design-system/motion.ts` is the interim source of truth.
- OPEN QUESTION: `ExposureArea`/community geometry is a later-phase entity (DOMAIN_MODEL.md §2.1);
  tour stop 7 is conditional until it exists.
- OPEN QUESTION: `cam` ranges encoded against real terrain decode slightly differently on the
  keyless ellipsoid tier; the look-at form bounds the error, but the tolerance should be measured.
- DECIDED 2026-08-22: band ownership. `CameraController` emits `cameraSample` (≤ 10 Hz + on settle)
  and never a band; `SemanticZoomController` derives the band (`scene/bands.ts`, hysteresis) and
  emits `bandChanged`. CINEMATIC_ARCHITECTURE.md §4.1/§17 and PERFORMANCE.md §4.2 say the same.
- OPEN QUESTION: layer ids. LAYER_SYSTEM.md §8.2 uses `rivers`, `gauges`, `snow_level`,
  `atmosphere_haze`; CINEMATIC_ROADMAP.md §14 uses `river-network`, `gauges-forecast-points`,
  `snow-level-plane`, `atmosphere-haze`. This document follows LAYER_SYSTEM, its declared owner.
- OPEN QUESTION: deep-link grammar. SEMANTIC_ZOOM.md §8 and CINEMATIC_ROADMAP.md C2 sketch
  `?e=<EntityId>&band=`; §7 here uses `sel` and `cam` because a band alone does not reproduce a
  view. One grammar must win before C2.
- OPEN QUESTION: SEMANTIC_ZOOM.md §8 frames a selection at the log-midpoint of its home band in
  ≤ 2.5 s; §5.1 here frames by bounding-sphere fit with padding and §4.3 caps at 4.2 s. Either the
  sphere fit is constrained to land inside the home band or SZ adopts the fit; durations reconcile
  on C1 telemetry.
- OPEN QUESTION: PERFORMANCE.md §7 rule 3 lists camera flights as renderer-native; §4.2 here needs
  a controller-owned tween (INFERENCE on the pre-render hook). CINEMATIC_ROADMAP.md §5.3 sketches
  `flyTo(bbox, { reducedMotion }): Promise<…>`; the SPIKE should implement §3 of this document.
- OPEN QUESTION: VISUAL_TRUTH_DOCTRINE.md §1.1 lists camera motion as class E, but its driver
  vocabulary is "a value of class A/B/C, or the clock"; user intent needs an entry.
- OPEN QUESTION: the downstream context set of §5.2 needs the upstream/downstream-of-station query
  that LAYER_SYSTEM.md §13 item 3 asks of ARCHITECTURE.md §6; until it exists the set is the gauge alone.

## 14. Cross-references

[HYDROLOGY.md](HYDROLOGY.md) §7, §11, §13 · [DATA_DOCTRINE.md](DATA_DOCTRINE.md) §5, §12 ·
[DOMAIN_MODEL.md](DOMAIN_MODEL.md) §1 · [ARCHITECTURE.md](ARCHITECTURE.md) §6–7 ·
[VISUALIZATION_CONTRACTS.md](VISUALIZATION_CONTRACTS.md) §8, §10 · [TESTING.md](TESTING.md) §6 ·
[ROADMAP.md](ROADMAP.md) Phase 8 · [CINEMATIC_ROADMAP.md](CINEMATIC_ROADMAP.md) · [V1_AUDIT.md](V1_AUDIT.md) §7 ·
[ADR-0006](adr/ADR-0006-web-stack-vite-react-typescript-cesium.md) · [ADR-0007](adr/ADR-0007-renderer-boundary-and-visualization-contracts.md) ·
[ADR-0010](adr/ADR-0010-knowledge-time-bitemporality.md) · [cesium-react-boundary.md](../.claude/skills/react-quality/references/cesium-react-boundary.md)
