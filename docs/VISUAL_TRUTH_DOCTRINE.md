# VISUAL TRUTH DOCTRINE — what a pixel is allowed to claim

The world is the interface. That sentence is only acceptable if every element in the world can
answer *what kind of truth are you?* This document defines the truth classes a visual element
may belong to, what each class may look like, what may never be drawn, how degraded data is
shown, what the layer inspector must expose, and the colour/tension language. It binds
`apps/web` (and any future renderer). It adds nothing to the backend: every rule here is a
presentation rule applied to the semantic contracts in
[VISUALIZATION_CONTRACTS.md](VISUALIZATION_CONTRACTS.md), under the renderer boundary of
[ARCHITECTURE.md](ARCHITECTURE.md) §7 and [adr/ADR-0007](adr/ADR-0007-renderer-boundary-and-visualization-contracts.md).

Two invariants everything below reduces to:

1. **A visual element either carries a value or it is representation.** If it carries a
   value, it inherits that value's provenance (`prov`, `source_kind`, three timestamps,
   freshness) and must be inspectable. If it is representation, it is labeled representation
   and names the value that drives it.
2. **Nothing on screen may assert more than [HYDROLOGY.md](HYDROLOGY.md) and
   [DATA_DOCTRINE.md](DATA_DOCTRINE.md) allow.** The renderer cannot upgrade a MODELED value to
   observed, an EXPERIMENTAL index to a probability, or a design height to protection.

Presentation mapping (colour families, stroke registers, materials, animation) exists only in
`apps/web/src/layers/*/style.ts` ([cesium-react-boundary](../.claude/skills/react-quality/references/cesium-react-boundary.md) rule 4).
No colour, material, shader, CSS or camera instruction in this document is, or may become, a
backend contract field (VISUALIZATION_CONTRACTS §10 rule 2).

## 1. The visual truth taxonomy

### 1.1 Classes

| Class | Name | What it is | Examples | Who owns it |
|---|---|---|---|---|
| **A** | DIRECT OBSERVATION | a measurement by an instrument or sensor network, including observed-derived products | USGS stage/discharge (`station:usgs:12200500`), SNOTEL SWE (`station:snotel:515:WA:SNTL`), MRMS radar QPE (`method=radar_qpe`), reservoir pool elevation from the operator, satellite snow-covered area / dated satellite scenes used *as evidence* | backend value + provenance |
| **B** | AUTHORITATIVE MODEL / OFFICIAL FORECAST | output of an authority's model or an official forecast/alert. Sub-class **B-official** (NWPS/NWRFC river forecasts, NWS/WPC QPF, NWS alerts) may be labeled OFFICIAL; sub-class **B-model** (NWM, SNODAS, SMAP L4, NBM, HRRR, GFS/GEFS) is labeled with the model name | official forecast crest at `fp:nwps:MVEW1`, NWM reach forecast for `reach:nwm:24270288`, SNODAS SWE grid, HRRR QPF field, forecast snow level, Flood Watch | backend value + provenance |
| **C** | CASCADE-DERIVED INTELLIGENCE | computed by Cascade Oracle from A/B with a versioned `Method`. Sub-class **C-EXPERIMENTAL**: method not yet hindcast-evaluated | headroom, rate of rise, rain-exposed fraction (`method:rain-exposed-fraction@1.0.0`), basin-mean SWE, model agreement, explanation drivers (the presentation hints `tension` and `flow_visual_intensity` are DERIVED scalars with a documented method but carry no meaning beyond scaling, §2); EXPERIMENTAL: susceptibility index | backend value + method + lineage |
| **D** | CARTOGRAPHIC REPRESENTATION | the static stage on which values are shown | basemap imagery, terrain mesh, river flowline geometry (NHDPlus HR), basin outlines (WBD/NLDI), labels, levee lines (NLD), dam points (NID), reservoir pool polygons, regulatory floodplain polygons (NFHL) | backend geography (versioned datasets) + client cartography |
| **E** | CINEMATIC REPRESENTATION | procedural or animated effects that exist for legibility, orientation and mood; never values | procedural clouds, animated river textures, rain/snow particles, haze, solar lighting, glow, camera motion | client only; each effect declares its **driver** (a value of class A/B/C, or the clock) |

Plus the data states that any element of class A–C (and, for dataset versions, D) can be in:
**current · stale · degraded · missing · partial · unknown** (§5).

### 1.2 Mapping to backend vocabulary

| Class | `source_kind` (DATA_DOCTRINE §2) | contract `truth` (`VisualTruthClass`) | may be labeled OFFICIAL |
|---|---|---|---|
| A | OBSERVED | `observation` | no — labeled *observed* (with method where observed-derived) |
| B-official | OFFICIAL_FORECAST | `authoritative_model` | **yes** |
| B-model | MODELED | `authoritative_model` | no — labeled with the model name |
| C | DERIVED | `cascade_derived` | no — badged DERIVED + method pointer |
| C-EXPERIMENTAL | EXPERIMENTAL | `cascade_derived` with `experimental: true` | no — badged EXPERIMENTAL |
| D | (dataset release, see OPEN QUESTION below) | `cartographic` | n/a |
| E | none — never emitted by the backend | `cinematic` (client-assigned) | never |
| CONFIGURED values | CONFIGURED | any; always badged *configured*; never drives hazard | never |
| states | `quality=missing/sentinel/…`, `Freshness.state` | `freshness` on the `ProvenanceRef` | n/a |

- FACT: the contract's `VisualTruthClass` enumerates all five classes, but backend items carry
  only `observation`, `authoritative_model`, `cascade_derived`. INFERENCE: `cartographic` and
  `cinematic` are in the enum so the client's layer inspector uses one vocabulary for elements
  it owns. The client may never assign the first three classes to anything it computes.
- OPEN QUESTION: DATA_DOCTRINE §2 has no kind for authoritative *static* geography (WBD,
  NHDPlus, NLD, NID, NFHL), while DOMAIN_MODEL §2.2 gives `DataSource.kind` a `static` value.
  Until reconciled, D elements show *dataset + release/retrieval date* in the inspector and no
  `source_kind` badge; they are never badged CONFIGURED (that kind is hand-entered metadata).
- OPEN QUESTION: `ProvenanceRef.freshness.state` in VISUALIZATION_CONTRACTS §1 lists five states
  while the `Freshness` type lists six (adds `partial`). This doctrine requires all six on
  every layer (§5); the contract should converge on the six-state set.
- The B-official / B-model split is **not** carried by `truth` (both are
  `authoritative_model`); it is carried by `source_kind` on the referenced `ProvenanceRef`.
  The renderer must read `source_kind` before printing the word OFFICIAL.

### 1.3 Worked examples

| Element on screen | Class | driving value's `source_kind` | `truth` | Register (§2) and inspector TYPE line |
|---|---|---|---|---|
| Basemap satellite imagery (undated composite) | D | dataset release | `cartographic` | cartographic; "imagery composite, date unknown/varies — not an observation of any valid time" |
| Dated satellite scene shown as evidence (e.g. snow cover on a given day) | A | OBSERVED | `observation` | observed register with sensor + valid time |
| Procedural storm cloud driven by modeled cloud-cover percent | E | driver MODELED | `cinematic` | "cloud visualization — driven by <model> cloud cover, valid <t>"; never an observed cloud |
| NWM river forecast hydrograph / crest | B-model | MODELED | `authoritative_model` | modeled register; "National Water Model <config>, issued <t>" |
| NWRFC official forecast crest and category | B-official | OFFICIAL_FORECAST | `authoritative_model` | official register; "OFFICIAL — NWRFC, issued <t>" |
| Cascade susceptibility state | C-EXPERIMENTAL | EXPERIMENTAL | `cascade_derived` | experimental register; "EXPERIMENTAL index — method:<name>@<ver>; not a probability" |
| Animated river texture | E | driver `flow_visual_intensity` (DERIVED from observed percentile) | `cinematic` | "flow animation — representation of observed percentile; not depth or velocity" |
| MRMS radar mosaic / QPE accumulation | A | OBSERVED (`method=radar_qpe`) | `observation` | observed register; "observed (radar-derived), valid <t>" |
| Snow-level plane / contour | visualization of B | MODELED when the provider publishes snow level; DERIVED (input: MODELED freezing level) when Cascade applies the offset — §3.2 | `authoritative_model` (see §3.2) | modeled register; "forecast snow level <elev>, offset <n> m from freezing level (parameter with provenance)" |
| Levee line from the National Levee Database | D geometry; attributes authoritative static (B-class provenance, not a forecast) | dataset release | `cartographic` | "NLD system <id>; design height <h> (design attribute, not a guarantee)" |
| Basin-mean SWE number | C (from B) | DERIVED (input MODELED) | `cascade_derived` | see §6 example |
| Headroom to minor at `fp:nwps:MVEW1` | C | DERIVED (inputs OBSERVED + OFFICIAL threshold) | `cascade_derived` | "derived — threshold_stage − current_stage, datum NGVD29" |
| Flood Watch polygon/banner | B-official | OFFICIAL_FORECAST | `authoritative_model` | official register, verbatim text, issuer, issued/expires |
| Solar lighting at the selected time | E | driver = timeline clock | `cinematic` | "lighting — solar position for <t>; no data content" |
| Night-lights basemap | D | dataset release | `cartographic` | "night-lights composite (dataset, date)" |
| Reservoir flood-buffer envelope | C over A | DERIVED (inputs OBSERVED storage + rule curve with provenance) | `cascade_derived` | "available buffer <fraction> of rule-curve maximum; rule curve provenance <src>" |

## 2. How each class may be rendered — the registers

A *register* is the set of visual properties that identify a class at a glance. `style.ts`
chooses exact values; the invariants are fixed here. Every register must remain distinguishable
in greyscale and with animation disabled (reduced-motion path, [TESTING.md](TESTING.md) §6).

| Register | Used for | Invariants |
|---|---|---|
| **observed** | A | solid, grounded, crisp edges; the value and its valid time printed; no softening, no halo |
| **official** | B-official | translucent/softer than observed; OFFICIAL badge with issuer and issued time; verbatim category words (action/minor/moderate/major) |
| **modeled** | B-model | translucent/softer than observed; model name badge; visibly distinct edge treatment from official (e.g. a different stroke pattern — the exact pattern is a `style.ts` choice) |
| **derived** | C | the value shown beside its inputs where space allows; DERIVED badge + one-line method pointer |
| **experimental** | C-EXPERIMENTAL | derived register plus an EXPERIMENTAL badge and a distinct stroke/pattern; never the red family (§7.1); never a number formatted as a probability |
| **cartographic** | D | neutral, photographic/naturalistic, unbadged on the map; inspectable with dataset + release |
| **cinematic** | E | never carries a number or a scale; toggleable; drops first under quality tiers; labeled "visualization" in the inspector with its driver |
| **unknown / missing** | any | neutral, incomplete-looking (hatched/outlined, no fill saturation); reason text; never calm, green or zero |
| **stale / degraded / partial** | any | last-known rendering retained, dimmed *and* marked with age and a STALE/DEGRADED/PARTIAL badge |

Rules that apply across registers:

- **Never intentionally blur classes.** A composite element (e.g. a hydrograph with observed
  and forecast segments) switches register at the valid-time boundary; the boundary is marked.
- **Observed vs forecast precipitation.** Observed QPE is solid and grounded on the terrain;
  forecast QPF is softer and translucent and carries issued time; they may share a scale
  (`display_range`) but never a register. Uncertainty is drawn as spread — a percentile band,
  a halo, or p10/p90 envelopes from `spread` — never as grain, noise, flicker or particle
  density that could be mistaken for data.
- **Observed, forecast, modeled, derived stay distinct** semantically *and* visually: at no
  zoom level, time, lighting mode or quality tier may two registers collapse into one.
- **Presentation hints are hints.** `display_range`, `label_priority`, `tension`,
  `flow_visual_intensity` scale or prioritize; they never add meaning.

## 3. Element-specific rules

### 3.1 The three inundation kinds never share a visual language

| Kind | Class | Register | What it is allowed to say |
|---|---|---|---|
| Regulatory / historical floodplain (NFHL zones, mapped historical extents) | D with authoritative static attributes | outline or subdued hatch, **never a water fill** | "mapped flood zone <designation>, dataset <release>" |
| Modeled potential inundation (an authoritative inundation model where published for the reach) | B | translucent projected extent with soft edge, issued/valid time, model name; depth only if the model publishes depth | "modeled extent for forecast stage <s> at <fp>, issued <t>" |
| Observed inundation (satellite/SAR-derived extent, verified reports) | A | stronger, evidence-backed fill with sensor and observation time; drawn only within the sensor footprint | "observed extent, <sensor>, <t>" |

No two kinds may share fill, edge and label treatment; switching a layer between kinds is a
different layer, not a style change. Where no authoritative model exists, kind 2 is absent —
not approximated from stage (HYDROLOGY §13).

### 3.2 Snow: phase versus melt

- The snow-level plane/contour is a visualization of a B value (forecast snow level; the
  offset from freezing level is a stored parameter with provenance, HYDROLOGY §7).
  OPEN QUESTION: the contract gives `snow_level` `truth: authoritative_model`, but if Cascade
  computes it as freezing level − offset the value is DERIVED with lineage to the MODELED
  freezing level (DATA_DOCTRINE §2); only a provider-published snow level is MODELED. The
  inspector prints whichever `source_kind` the `ProvenanceRef` carries and never assumes MODELED.
- Snow-covered area (A from SCA, or B from SNODAS) and SWE stay exactly where the data put
  them. **A rising snow level never makes snow disappear.** It changes only the rain/snow
  partition: the rain-exposed and rain-on-snow exposed fractions (C) are shown as highlighted
  elevation bands on the basin hypsometry and as numbers, not as snow vanishing.
- Melt is shown only as a change in an SWE series (A/B) between valid times, rendered as a
  value change with both timestamps. No "melting" animation.

### 3.3 Rivers: state, not depth

- River geometry is D. The observed/forecast state of a reach or forecast point is drawn *on*
  the geometry: stroke weight, brightness, animation energy scaled by `flow_visual_intensity`
  (a normalized hint from percentile, "not a depth" — VISUALIZATION_CONTRACTS §3).
- The river is never raised vertically, widened to imply bank overtopping, or extruded, unless
  an authoritative water-surface or inundation model for that reach is loaded as a B layer
  (§3.1 kind 2). Otherwise the river is a **state visualization**, and the inspector says so.
- Category colouring of a reach requires an official threshold on that point (ADR-0011). A
  reach without a forecast point carries no category and is not coloured as if it had one
  until a clearly-labeled reach-level derivation exists (HYDROLOGY §5) — and then in the
  derived register, never the official one.

### 3.4 Reservoirs: an envelope, never invented water

- The pool polygon is D. The reservoir state is an **envelope**: current storage against the
  rule-curve maximum and the flood-control bounds, rendered as a gauge/band anchored to the
  pool, with `available_buffer.fraction` (C) and the rule curve's provenance.
- No 3D water surface is raised or lowered on the terrain from pool elevation; pool elevation
  is printed with its datum. Forecast inflow is shown only when `forecast_inflow` is non-null;
  otherwise the future state is UNKNOWN and says so (HYDROLOGY §10).

### 3.5 Levees and flood defenses

NLD geometry with verbatim attributes. A levee line never clips, blocks or masks a modeled
inundation extent, never changes register with hazard, and is never captioned with "protects",
"protected" or "safe". A design height is a design height (HYDROLOGY §10).

### 3.6 Clouds and atmosphere

Procedural clouds, haze and sky are E. They are captioned "cloud/atmosphere visualization
driven by <model> cloud cover, valid <t>" unless the layer is actual observed imagery (then it
is A with sensor and time). Procedural geometry never follows a radar or QPF field closely
enough to be read as its shape. OPEN QUESTION: `WeatherVisualizationState.fields[].variable`
does not yet include a cloud-cover variable; until it does, procedural clouds may be driven
only by QPF/QPE presence and must be captioned "conceptual".

### 3.7 Cinematic precipitation versus the quantitative field

Rain and snow particles are E, driven by the presence/intensity band of a QPE (A) or QPF (B)
field. The quantitative field itself (raster with `display_range`, basin aggregates with
units) is a separate, always-available layer; particles never replace it, never vary in a way
that reads as amount, and carry no legend.

### 3.8 Lighting, sunsets, night

- Solar lighting positioned by the timeline's selected time is allowed (E; driver = clock).
- An **analytical lighting mode** (neutral, even illumination) exists and is the default
  whenever the scene is in elevated or event state (§7.4) or the user selects it; on the `low`
  quality tier, where lighting is off ([PERFORMANCE.md](PERFORMANCE.md) §3), it is the only mode. In every
  mode, hazard overlays (registers observed/official/modeled/derived) render independent of
  scene lighting so that a sunset, low sun angle or terrain shadow can never dim, tint or
  occlude hazard information. Contrast of overlays is checked against both lighting extremes
  in visual regression.
- **Night mode** is allowed: night-lights basemap (D), dark terrain, river geometry (D) with
  state (C hints), precipitation fields (A/B), basin boundaries (D), storm clouds (E). Same
  registers, same badges, no neon palette, no glow that changes a register's meaning.

### 3.9 Sound

No sound in the MVP (ARCHITECTURE §11; ROADMAP rejections). If audio is ever added by ADR, it
is never a channel for critical state: no state, category, alert or freshness is conveyed only
by sound.

## 4. The no-visual-fabrication list

Render it only if a value of class A/B/C with provenance exists for it. Otherwise **omit it,
or render it as clearly conceptual** — captioned "conceptual", no numeric axis, no legend,
cinematic register, inspector TYPE = "conceptual (no data)".

| Never fabricate | Why | What is allowed instead |
|---|---|---|
| Flood depths / water-surface elevations | no authoritative model → HYDROLOGY §13 | headroom in stage/flow (C); modeled extent only from an authoritative inundation model (B) |
| River elevations / rising river geometry | stage is relative to gauge datum; not a 3D surface | state visualization on D geometry (§3.3) |
| Exact cloud geometry | models give cover fraction, not shapes | procedural clouds captioned as visualization (§3.6) |
| Rainfall amounts from particles | particles are E | the QPE/QPF raster and basin aggregates with units (§3.7) |
| Reservoir water levels in 3D | pool elevation is a number with a datum | envelope with provenance (§3.4) |
| Snowmelt animation | melt is an energy balance, not a snow-line move | SWE series change between valid times (§3.2) |
| Infrastructure failure (levee breach, dam overtopping) | the platform never infers operations or failure | verbatim attributes; `EventTimelineEntry` of kind `levee_incident` when evidenced (D/A) |
| Forecast probabilities | only (a) authority-issued, (b) named-ensemble fractions, (c) hindcast-evaluated Cascade methods (DATA_DOCTRINE §9) | categorical states and indices, badged; "11 of 21 members exceed minor" when that is the data |

## 5. Degraded-data doctrine

### 5.1 Every layer supports every state

```
                      ┌──────── a newer document (newer valid_time) returns any state here ────────┐
                      ▼                                                                            │
 ┌─────────┐  first  ┌─────────┐  now − valid_time > cadence + grace                          ┌─────────┐
 │ unknown │ ───────►│ current │ ────────────────────────────────────────────────────────────►│  stale  │
 └─────────┘  doc    └─────────┘                                                              └─────────┘
                          │  (the three below are also reachable from stale)
                          ├─ now − retrieved_at > cadence × k · provider `down` · layer threw ────► degraded
                          ├─ quality=missing + reason (product should exist, does not) ───────────► missing
                          └─ coverage < scope (data where present, coverage mask elsewhere) ──────► partial
 unknown also holds whenever the state or its reason cannot be classified; only a new document
 moves a layer back to current (§5.2: local ageing is one-way, current → stale/degraded).
```

Staleness is computed from `valid_time`/`retrieved_at` and the product's cadence and grace
(DATA_DOCTRINE §5); the client takes `freshness.state` and `age_seconds` from the contract and
never stores a stale boolean of its own (while disconnected it re-ages the last document, §5.2).
The client-side status a layer exposes to the inspector and the scene:

```ts
// apps/web/src/layers/truth.ts — pure TS, no renderer types
export type LayerDataState = 'current' | 'stale' | 'degraded' | 'missing' | 'partial' | 'unknown';

export interface LayerTruthStatus {
  layerId: string;                       // e.g. "snow.swe.basin-mean"
  truth: VisualTruthClass;               // generated from the contract enum
  sourceKind?: SourceKind;               // absent for cartographic/cinematic
  state: LayerDataState;
  ageSeconds: number | null;
  expectedCadenceSeconds: number | null;
  lastKnownValidTime: string | null;     // ISO 8601; what the retained rendering depicts
  retrievedAt: string | null;
  reason: string | null;                 // backend-supplied reason for missing/degraded/unknown
  coverageFraction: number | null;       // partial: share of scope with data
  renderFailure: boolean;                // cesium-react-boundary rule 7: layer threw → degraded
}
```

| State | Rendering | Inspector line |
|---|---|---|
| current | register as normal | "current — age <n>, cadence <c>" |
| stale | **last known rendering retained**, dimmed, STALE badge, age, last valid time, "source unavailable since <retrieved_at>" where applicable | "STALE — valid <t>, age <n> > cadence+grace" |
| degraded | rendering retained, DEGRADED badge; ingestion behind or layer render failure | "DEGRADED — <reason>" |
| missing | placeholder outline/hatch in scope, MISSING badge, reason | "MISSING — <reason> (e.g. no mapping configured / product not published)" |
| partial | rendered where data exist, coverage mask elsewhere, PARTIAL badge with fraction | "PARTIAL — <fraction> of scope" |
| unknown | neutral incomplete rendering, UNKNOWN badge, reason | "UNKNOWN — <reason>" |

Worked rule: **SNODAS unavailable** ⇒ the last known snow layer stays on screen, dimmed, with
STALE, the last `valid_time`, and "SNODAS unavailable since <retrieved_at>". Never silent
removal; never a blank basin that reads as "no snow". The same applies to every A/B/C layer.

### 5.2 Partial backend outage

- D layers (basemap, terrain, static geography from object storage/CDN) remain navigable.
- Scientific layers (A/B/C) are flagged per §5.1 from the last contract the client holds; the
  client re-derives `ageSeconds` from `retrieved_at`/`generated_at` against the local clock
  while the API is unreachable and escalates to stale/degraded on its own — it never displays
  "current" from a cached document older than `expected_cadence_seconds`. The escalation is
  one-way: nothing returns to current without a new document (PERFORMANCE §6). `Freshness`
  carries no grace, so the client escalates at cadence alone (conservative). OPEN QUESTION:
  add `grace_seconds` to `Freshness` so client and backend agree on the stale boundary.
- SSE disconnect shows "live updates paused since <t>" on the timeline; reconnection refetches
  (ARCHITECTURE §6: no payloads over the stream).
- `/system/health` drives a scene-level provider health strip; a provider `down` marks its
  layers DEGRADED in `LayerTruthStatus` even when cached values are within cadence — the
  contract's `freshness` is never rewritten by the client.
- **No stale state masquerades as live.** Anything not current is marked, everywhere it
  appears: map, panel, timeline, export.

## 6. Layer inspector specification

Every element of class A–E is inspectable (click, keyboard focus, or layer list). The inspector
is built purely from the item's `truth`, its `ProvenanceRef`, method metadata and, for D/E, the
client's own layer descriptor. It never computes science.

| Field | Source | Rule |
|---|---|---|
| SOURCE | `ProvenanceRef.source_id`, `product_id`, `label` | authority name as the backend labels it |
| TYPE | `truth` (+ `experimental`) | the class letter and name; for E also the driver's class |
| KIND | `source_kind` | exactly one of OBSERVED / OFFICIAL_FORECAST / MODELED / DERIVED / EXPERIMENTAL / CONFIGURED / UNKNOWN, printed as observed / official forecast / modeled / derived / experimental / configured / unknown |
| VALID TIME | `valid_time` | always shown; for daily products the provider's day boundary |
| ISSUED TIME | `issued_at` | shown for forecasts/models; "n/a (observation)" for A |
| RETRIEVED | `retrieved_at` | always shown |
| FRESHNESS | `freshness.state`, `age_seconds`, `expected_cadence_seconds` | state word + age + cadence; never a decimal "freshness score" |
| CONFIDENCE | `ConfidenceLabel` | high / moderate / low / unknown — a label, never a decimal unless calibrated (DATA_DOCTRINE §9) |
| MODEL VERSION | `ForecastRun.model_version` / product version string | as published; "not versioned by provider" when absent |
| RESOLUTION | `SourceProduct.spatial_scope` / `GridProduct.resolution` | native resolution and the scope it was aggregated to |
| CASCADE TRANSFORMATION | `method_id`, `lineage`/`inputs`, unit conversion | method id with version, inputs listed, conversions named; "none" for untransformed values |
| QUALITY | `quality[]` | the DATA_DOCTRINE §1 flags (provisional / approved / estimated / ice / equipment / suspect / sentinel / out-of-range / missing) verbatim |

Example — basin-average SWE for `basin:skagit` (illustrative values, 2026-01-14):

```
SOURCE                  NOHRSC SNODAS  (src:snodas · product:snodas-daily)
TYPE                    C · Cascade-derived aggregate of a B · authoritative model
KIND                    derived  (input: modeled)
VALID TIME              2026-01-14 06:00 UTC  (SNODAS daily; provider day boundary)
ISSUED TIME             2026-01-14 (daily product publication)
RETRIEVED               2026-01-14 13:02 UTC
FRESHNESS               current — age 7 h · cadence 24 h  (grace is backend-side, DATA_DOCTRINE §5; not in `Freshness`)
CONFIDENCE              moderate (label) — maritime-pack bias, HYDROLOGY §7; SNOTEL points shown beside it
MODEL VERSION           not versioned by provider; product version string as retrieved
RESOLUTION              ~1 km grid (ASSUMPTION; confirm in DATA_SOURCES.md) → basin polygon mean
CASCADE TRANSFORMATION  method:basin-mean-swe@1.0.0 — zonal mean over the basin:skagit mask
                        (precomputed per grid definition); unit mm (native), displayed as in beside mm (DATA_DOCTRINE §6);
                        inputs: GridProduct <id>, basin geometry release <ver>; lineage → <ids>
QUALITY                 —
```

Inspector derivation in TS is a pure function `toInspectorRecord(item, provenanceRefs,
layerDescriptor): InspectorRecord` and is unit-tested against contract fixtures
(TESTING §4, §6: "layer inspector shows provenance").

## 7. Colour, risk language and progressive wake-up

All of this section is `style.ts` territory. It constrains; it does not enter contracts.

### 7.1 Palette doctrine

- **The Earth still looks like Earth.** Natural Earth tones for terrain, imagery, sky and
  water geometry. Risk modifies the *information layer* — strokes, fills of overlays, badges,
  panels — never the landscape's own colour.
- **Nominal hydrology information** sits in a deep navy / cyan family (water geometry state,
  observed values, quiet telemetry).
- **Amber** enters as tension rises: elevated susceptibility/forcing states, Watch-level
  official products, headroom shrinking, disagreement.
- **Red is earned, not assumed.** Justified only by class A or B evidence: observed stage/flow
  at or above an official moderate/major threshold, an official forecast category of major, or
  an official Warning. C-class values — and EXPERIMENTAL above all — never reach the red family
  (ASSUMPTION on the exact thresholds; the A/B-only rule is not negotiable).
- **Forecast visually distinct from observation** (§2); **experimental identifiable** by badge
  and pattern; **unknown neutral and incomplete** — never calm, green or zero (DATA_DOCTRINE §12).

### 7.2 Non-colour cues are mandatory

Scientific meaning is never encoded solely through hue or saturation. Every semantic state has
at least one non-colour carrier: a badge word, a stroke pattern, a fill pattern, an icon, a
label, or a position on a scale with printed units. Acceptance test: a greyscale screenshot of
every visual-regression scene still distinguishes observed / official / modeled / derived /
experimental / unknown and every category.

### 7.3 What we avoid, and why

| Avoided | Reason |
|---|---|
| constant red, traffic-light UI everywhere | red loses meaning; categories are official words, not lights |
| neon / cyberpunk | fabricates drama; breaks "Earth looks like Earth" |
| emergency-TV graphics (flashing, sirens, tickers) | implies alert authority Cascade does not hold |
| militaristic threat visualization (targets, radar sweeps, "threat levels") | wrong mental model; hazard is hydrology, not an adversary |
| saturation as a proxy for confidence | confidence is a label (DATA_DOCTRINE §9) |
| noise/grain/flicker as "uncertainty" | mistakable for data (§2) |

### 7.4 Progressive wake-up

The scene's energy follows `BasinVisualizationState.tension` (a documented derived scalar,
never a probability) and official evidence. Bands are client presentation thresholds
(ASSUMPTION: initial cut points to be tuned in visual review), not science.

| Scene state | Trigger | What changes |
|---|---|---|
| **Calm** | low tension across the extent; no official alerts | near-pure Earth; minimal overlays; quiet labels (`label_priority` high only); low animation energy; observatory-like stillness; provenance still one click away |
| **Elevated** | tension rising in any basin in view, or an official Watch / observed stage or flow at or above the official action threshold | telemetry appears around the affected basin; the basin outline resolves; river highlights strengthen; forecast, snow and reservoir layers become available; analytical lighting becomes the default (§3.8) |
| **Major event** | official Warning, official forecast category ≥ minor, or observed stage or flow at or above the official minor threshold — **never tension alone** (ASSUMPTION, consistent with DATA_DOCTRINE §12) — or the user opens Event Mode | forecast field prominent; timeline central; river network animates on the affected reaches; model disagreement surfaces as a first-class panel; infrastructure (reservoirs, levees, dams) visible with attributes; event mode layout |

Calm days remain tranquil: wake-up never raises baseline energy, and de-escalation follows
the same evidence downward. `tension` may raise the scene to Elevated but not to Major event.
Animation energy respects the reduced-motion preference; on the `low` quality tier the core
intelligence (panels, timeline, provenance) stays complete while E elements drop first
(cesium-react-boundary rule 8).

## 8. Official versus Cascade claims

- Official warnings, watches, advisories and evacuation instructions are shown **verbatim**
  with issuer and issued/expires time, badged OFFICIAL, linked to the issuer
  (`OfficialAlert.raw`, `official_alerts[]`). They are never paraphrased, summarized or
  re-severitied by the client.
- Cascade Oracle never implies alert authority: no sirens, no "alert" wording for C-class
  states, no push-notification style banners for indices, no countdowns. Time-to-threshold is
  an indicator with its window and nonlinearity caveat (HYDROLOGY §9), never a countdown clock.
- Copy rules (DATA_DOCTRINE §12): never "will flood", "safe", "protected"; use "official
  forecast crest", "exceeds", "remains below", "experimental index", "model disagreement".
  UNKNOWN is written UNKNOWN with its reason. Explanation text is rendered from the structured
  drivers (HYDROLOGY §11), never free-form narrative.
- Every C value, everywhere (map, panel, timeline, export, screenshot), carries DERIVED or
  EXPERIMENTAL and a one-line method pointer. Exports and screenshots embed the badges and the
  `as_of` time so the image cannot be separated from its provenance.
- Replay (`as_of`) scenes show the knowledge time prominently; nothing in a replay is styled
  as live.

## 9. Compliance checklist for any new visual element

A PR adding or changing a visual element answers every line; a "no" without an ADR or an
OPEN QUESTION fails review.

```
  new element
      │
      ├─ does it carry a value? ── no ──► is it geometry/label/imagery? ── yes ──► class D
      │                                      └── no ──► class E: name the driver (A/B/C/clock)
      └─ yes ──► what is its source_kind?
                  OBSERVED → A · OFFICIAL_FORECAST/MODELED → B · DERIVED → C · EXPERIMENTAL → C-EXP
                  CONFIGURED → badge "configured", never hazard · UNKNOWN → unknown register
```

1. Truth class assigned (A–E) and `truth` read from the contract, never inferred client-side
   for A/B/C.
2. Register matches the class (§2); distinguishable in greyscale and with animation off.
3. OFFICIAL appears only when `source_kind == OFFICIAL_FORECAST`.
4. EXPERIMENTAL badge and pattern present for any `experimental: true` item; no red family.
5. Inspector fields (§6) all populated or explicitly "n/a"; `toInspectorRecord` fixture added.
6. All six data states (§5) rendered and screenshot-tested, including stale-retained and
   missing-with-reason; no silent removal path.
7. No fabrication (§4): no depth, elevation, amount, level, melt, failure or probability
   without a class A/B/C value behind it; conceptual elements captioned.
8. Forecast and observed never share a register; uncertainty drawn as spread/band, not noise.
9. Inundation kind (if any) is one of the three in §3.1 with its own layer and language.
10. Rivers not raised/extruded; reservoirs as envelopes; levees without protection semantics.
11. E elements: captioned "visualization", driver named, toggleable, dropped on `low` tier,
    reduced-motion path implemented.
12. Overlays readable in solar, sunset and night lighting; analytical mode unaffected.
13. Copy audited against DATA_DOCTRINE §12 words; UNKNOWN shown with reason.
14. No colour/material/camera field requested from or added to a contract; mapping lives in
    `layers/<name>/style.ts` only; no renderer types in stores or props.
15. Wake-up behaviour: the element does not raise scene state beyond what §7.4 triggers allow.
16. Visual regression scene(s) updated (Cascadia overview, basin, river, snow, storm, event,
    night, degraded — TESTING §6) with fixed clock and fixture contracts.
17. No sound; no critical state conveyed only by motion, colour or audio.

## 10. Open questions (consolidated)

- OPEN QUESTION: no `source_kind` for authoritative static geography (DATA_DOCTRINE §2 vs
  DOMAIN_MODEL §2.2 `static`); D elements currently show dataset + release without a kind badge.
- OPEN QUESTION: `ProvenanceRef.freshness.state` (5 states) vs `Freshness` (6 states) in
  VISUALIZATION_CONTRACTS §1; this doctrine requires `partial` everywhere.
- OPEN QUESTION: `WeatherVisualizationState` lacks a cloud-cover variable; procedural clouds
  are "conceptual" until one exists.
- OPEN QUESTION: `BasinVisualizationState.surfaces.hazard.truth` is `authoritative_model`
  while the item reserves `cascade_index` (Phase 7). When it becomes non-null the hazard item
  needs per-field `truth` so the index renders in the experimental register, not the official one.
- OPEN QUESTION: wake-up band cut points and the A/B-only justification for the red family are
  ASSUMPTIONS pending visual review; they must be recorded in `style.ts` with a comment linking
  here, not tuned silently.
- OPEN QUESTION: `Freshness` carries `expected_cadence_seconds` but no grace; the client's
  offline escalation (§5.2) therefore uses cadence alone. Add `grace_seconds` or accept the asymmetry.
- OPEN QUESTION: `snow_level` `source_kind` — MODELED only if provider-published; DERIVED if
  Cascade applies the freezing-level offset (§3.2). The contract's `truth` does not settle this.
- OPEN QUESTION: `DATA_SOURCES.md` is listed in CONTEXT.md and ROADMAP.md Phase 0 but is not
  present in `docs/`; the SNODAS resolution in §6 stays an ASSUMPTION until it exists.

## 11. Cross-references

- [HYDROLOGY.md](HYDROLOGY.md) §7 (snow level vs melt), §9 (rivers, headroom), §10 (reservoirs,
  levees), §11 (explanation), §13 (what we will not claim).
- [DATA_DOCTRINE.md](DATA_DOCTRINE.md) §2 (source kinds), §3 (three-valued time), §5
  (staleness), §9 (uncertainty/confidence), §12 (claims and copy).
- [DOMAIN_MODEL.md](DOMAIN_MODEL.md) §1 (ids), §2.1 (geography incl. FloodDefense), §2.4
  (Assessment, OfficialAlert).
- [VISUALIZATION_CONTRACTS.md](VISUALIZATION_CONTRACTS.md) §1 (`ProvenanceRef`, `Freshness`,
  `ConfidenceLabel`, `VisualTruthClass`), §2–§7 (per-layer items), §10 (rules).
- [ARCHITECTURE.md](ARCHITECTURE.md) §6 (SSE, `/system/health`), §7 (client boundary), §11.
- [ROADMAP.md](ROADMAP.md) (phases that unlock each layer; audio rejection);
  [TESTING.md](TESTING.md) §4, §6 (contract, E2E, visual regression, accessibility).
- [adr/ADR-0007](adr/ADR-0007-renderer-boundary-and-visualization-contracts.md),
  [adr/ADR-0008](adr/ADR-0008-official-models-first.md),
  [adr/ADR-0011](adr/ADR-0011-thresholds-official-only.md).
- [CINEMATIC_ARCHITECTURE.md](CINEMATIC_ARCHITECTURE.md) §10 (visual terrain ≠ science DEM;
  basemap kinds incl. `low_light_analytical`), §11 (quality tiers);
  [PERFORMANCE.md](PERFORMANCE.md) §3 (tier table: cinematic drops first, core intelligence
  always), §6 (client-side ageing), §13 (failure handling). Still planned, per
  [CONTEXT.md](CONTEXT.md): `LAYER_SYSTEM.md`, `CAMERA_SYSTEM.md`, `SEMANTIC_ZOOM.md`. All of
  them implement, and may not relax, this doctrine.
