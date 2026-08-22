# HYDROLOGY — the causal model Cascade Oracle reasons with

This document states the science the platform is allowed to encode. It is deliberately
conservative: where the literature is settled it says FACT; where Cascade Oracle adopts a
working simplification it says ASSUMPTION; where we do not yet know, OPEN QUESTION. Nothing
in the software may assert more than this document does.

## 1. The problem, stated as state estimation

A watershed at time *t* holds water in a small number of stores. Weather adds water to the
stores; the stores release it to the channel network at rates that depend on how full they
are; the channel network routes it downstream, delayed and attenuated, through lakes and
reservoirs whose operators may hold or release it. Gauges, satellites, snow pillows, soil
probes, radar and models observe this system imperfectly.

```
state  S(t) = { soil water storage per elevation band,
                groundwater / baseflow state,
                snow storage per elevation band (SWE, cold content, snow-covered area),
                channel storage per reach,
                lake / reservoir storage,
                frozen-ground / ice state (rarely material in western WA) }

forcing F(t) = { precipitation rate and phase per elevation band,
                 air temperature, humidity, wind (energy for melt),
                 freezing level / snow level,
                 IVT and storm orientation (a proxy for orographic precipitation) }

observations y(t) = h(S(t), F(t)) + noise      (gauges, SNOTEL, SNODAS, SMAP, MRMS, …)

question: P( Q_reach(t+h) > threshold | y(≤t), forecast distribution of F(t..t+h) ),  h ∈ {6,12,24,48,72,120} h
```

The distinction the brief makes is the one we keep: **forcing determines how much water
enters; state determines how the basin reacts.** Extreme Western Washington floods are
forcing-driven (FACT — large events require sustained, intense, orographically enhanced
precipitation, nearly always from atmospheric rivers); antecedent state modulates the
response, sometimes strongly, and it never substitutes for the forcing.

## 2. The Western Washington regime (what makes this region specific)

- **Season.** Flood season is roughly October–February, peaking November–January, when
  atmospheric rivers (ARs) are most frequent and most moisture-laden (FACT).
- **Atmospheric rivers.** ARs are long, narrow corridors of concentrated water-vapour
  transport; integrated vapour transport (IVT, kg m⁻¹ s⁻¹) is the standard measure, and the
  AR scale (Ralph et al. 2019) rates events 1–5 by IVT magnitude and duration (FACT). For
  the Cascades, what matters beyond IVT is **orientation relative to terrain**
  (south-westerly flow loads the western slopes), **duration** (how long the IVT core sits on
  one basin), and **temperature** (warm ARs raise snow levels and melt snow).
- **Orographic enhancement.** Precipitation increases steeply with elevation on windward
  slopes; basin-average QPF from a coarse model can be badly wrong in the mountains (FACT).
  Basin-aggregated precipitation must therefore be computed from the highest-resolution
  product available and carry its own uncertainty.
- **Transient snow zone.** In the Cascades, terrain between roughly 1,000 and 4,000 ft
  alternates between rain and snow within a single winter and often within a single storm
  (ASSUMPTION for the exact band — it varies with latitude and season; confirm per basin from
  SNOTEL/SNODAS climatology). Rain-on-snow events concentrate here.
- **Basin response.** Snoqualmie, Skykomish, Stillaguamish, Sauk and Nooksack respond within
  hours to a day; the lower Skagit integrates a 3,093 mi² basin (USGS drainage area at
  Mount Vernon) and crests roughly a day after the upper-basin peaks (INFERENCE from
  routing distance; calibrate from history). Travel times are a first-class quantity to
  derive, not a constant to guess.
- **Regulation.** The region mixes near-natural and heavily controlled rivers (FACT for the
  operators; operational details vary):
  - Skagit: Ross, Diablo and Gorge (Seattle City Light) control the upper Skagit; Upper and
    Lower Baker (Puget Sound Energy) control the Baker. The **Sauk** is unregulated and is a
    major, often dominant, flood contributor at Concrete and Mount Vernon.
  - Green: Howard A. Hanson Dam (USACE) provides flood control above Auburn; this is why
    NWS defines Auburn's flood categories by **flow**.
  - White: Mud Mountain Dam (USACE) provides flood control above Auburn; flow-defined categories.
  - Cedar: Chester Morse Lake / Masonry Dam (Seattle Public Utilities) — a water-supply
    reservoir with limited flood-control role; Renton's stage thresholds are official.
  - Snoqualmie: essentially unregulated on the main stem; the South Fork Tolt reservoir (SPU)
    is a small upstream control on the Tolt tributary.
  - Nooksack: unregulated; the lower river is tidally influenced at Ferndale.
  A basin's `regulation_class` (natural / partially regulated / regulated) is a domain attribute
  that changes how every downstream quantity is interpreted.

## 3. Surface I — BASIN SUSCEPTIBILITY

*How primed is the watershed to respond strongly if significant precipitation arrives?*

Inputs (each a `DerivedFeature` with provenance and percentile context):

| Feature | Meaning | Primary sources (see DATA_SOURCES) |
|---|---|---|
| soil water storage / saturation percentile | remaining storage before saturation-excess runoff dominates | NWM land output (modeled), SMAP L4 root-zone (assimilated), SNOTEL SMS (point), API proxy |
| antecedent precipitation index (API, 7/14/30 d) | recency-weighted prior rainfall | MRMS/Stage IV (observed), SNOTEL PREC |
| baseflow / groundwater proxy | how high the slow store sits | gauge baseflow separation (derived), NWM |
| river state percentile | current flow vs seasonal climatology at each gauge | USGS (observed), NWPS |
| snow storage & state | SWE by elevation band, snow-covered fraction, ripeness | SNODAS (modeled/assimilated), SNOTEL (point), MODIS/VIIRS SCA |
| reservoir storage state | fraction of flood-control pool already used | operator data (USACE CWMS, SCL, PSE, SPU) |
| seasonal context | where in the climatological year we are | static |

Output: a categorical state (LOW / MODERATE / HIGH / VERY HIGH / UNKNOWN) plus the
contributing features, each with its value, percentile, direction of contribution, and
freshness. Until calibrated against history it is labeled an **experimental susceptibility
index**, never a probability.

What it is not: it is not a flood forecast. A basin can be VERY HIGH susceptibility in a dry
forecast and the hazard is LOW.

## 4. Surface II — METEOROLOGICAL FORCING

*How much hydrologically significant water is likely to arrive, and in what form?*

| Feature | Meaning | Sources |
|---|---|---|
| basin-average QPF per window (6/12/24/48/72/120 h) | liquid-equivalent precipitation forecast, area-weighted over the basin polygon | NBM, HRRR, GFS/GEFS, WPC QPF |
| precipitation intensity and duration | peak rate and hours above a rate | same, hourly |
| rain/snow partition per elevation band | fraction of QPF falling as rain, using forecast snow level and hypsometry | NBM/HRRR freezing level + DEM |
| **rain-exposed basin fraction** | share of basin area below forecast snow level | derived |
| **rain-on-snow exposed fraction** | share of currently snow-covered area below forecast snow level | derived (SNODAS/SCA ∩ snow level) |
| IVT magnitude, direction, duration; AR scale | moisture transport proxy for orographic precipitation | GFS/GEFS (derived), CW3E products |
| temperature / dewpoint / wind at band elevations | melt energy proxies | HRRR/NBM |
| forecast spread | ensemble disagreement on the above | GEFS, NBM percentiles |

Output: per horizon, a categorical forcing level plus the numbers behind it and their spread.
Forecast values always carry `issued_at` and `valid_time`; a newer run supersedes, never
overwrites, an older one.

## 5. Surface III — FLOOD HAZARD

*Given susceptibility, forcing, routing, regulation and model uncertainty — what is the chance
meaningful thresholds are crossed, per horizon?*

Ordered by authority:

1. **Official forecast category** (NWPS/NWRFC deterministic forecast vs official categories):
   the forecast crest and its category, when issued, by whom. This is always shown and always
   labeled OFFICIAL.
2. **Official or authoritative probabilities** where they exist (HEFS/ESP ensembles, NWM
   medium-range ensemble exceedance fractions): shown as *model probabilities* with the model
   named.
3. **Model agreement** (Surface IV below): a first-class signal.
4. **Cascade experimental hazard index**: only after hindcast evaluation demonstrates skill
   (`TESTING.md` §7); until then the platform shows 1–3 and the susceptibility/forcing
   surfaces, and does not print a Cascade-derived percentage.

Thresholds are official NWS categories (action / minor / moderate / major), in stage or flow
as NWS defines them per forecast point, with datum recorded. Reach-level thresholds without an
official forecast point are a later, clearly-labeled derivation.

## 6. Surface IV — MODEL AGREEMENT (meta-signal)

Disagreement between NWPS (NWRFC), NWM configurations, ensemble spread, and Cascade features
is information, never averaged away. Agreement levels: HIGH / MODERATE / LOW / UNKNOWN,
computed from crest magnitude, crest timing, and category differences, explained with the
specific divergence ("NWM medium-range produces a stronger runoff response than the official
forecast under similar basin QPF"). Model skill is evaluated per basin and per regime
(AR-driven rain, rain-on-snow, spring melt, summer low flow) as history accumulates.

## 7. Snow doctrine

- SWE is storage, not hazard. More SWE can buffer a storm (cold, deep pack absorbing rain)
  or amplify it (warm, ripe pack releasing meltwater) — the sign depends on temperature,
  pack state, and elevation distribution (FACT).
- Precipitation phase is set by the **snow level**, which sits below the freezing level.
  Working assumption: snow level ≈ freezing level − ~1,000 ft (ASSUMPTION; NWS Seattle
  guidance commonly uses 500–1,000 ft; the offset varies with precipitation intensity — store
  it as a parameter with provenance, never hard-code it).
- **Rain-on-snow** runoff enhancement comes mostly from turbulent sensible and latent heat
  fluxes of warm, humid, windy air over the pack, plus the liquid water that the pack can no
  longer hold; the heat content of the rain itself is a minor term (FACT — e.g. Marks et al.
  1998 on the February 1996 Pacific Northwest flood). Therefore temperature, humidity and wind
  at snowpack elevations are forcing inputs, not just precipitation.
- Snow level rising does **not** remove snow. It changes what falls on it. Melt requires an
  energy balance; the visualization must never depict snow disappearing because the snow
  line moved (`VISUAL_TRUTH_DOCTRINE.md`).
- Basin hypsometry (area per elevation band from the DEM) is the pivot that turns a snow level
  into *rain-exposed basin fraction* and, intersected with snow-covered area, into
  *rain-on-snow exposed fraction*. These two fractions are the first derived snow features
  Cascade Oracle computes (`ROADMAP.md` Phase 3).
- Point observations (SNOTEL) are ground truth for their elevation and aspect; gridded
  products (SNODAS) give spatial structure but assimilate those same points and have known
  biases in maritime packs. Fuse; do not pick one.

## 8. Soil doctrine

- The useful quantity is **remaining storage**, not a binary "saturated". As storage fills,
  saturation-excess runoff generation expands (variable source areas), interflow accelerates,
  and a given rainfall produces a larger, faster hydrograph (FACT for forested PNW soils;
  infiltration-excess runoff is rare there).
- No single product observes basin soil water. Cascade Oracle fuses: modeled soil moisture
  (NWM, climatological percentiles), satellite root-zone estimates (SMAP L4, 9 km, coarse but
  spatially honest), point probes where present (SNOTEL SMS), and an antecedent precipitation
  index as a transparent fallback. Each contributes a percentile; disagreement between them is
  reported, not hidden.
- Percentiles require climatology; the platform builds its own from stored history and, until
  enough history exists, labels percentiles as derived from the product's own reanalysis with
  the period stated.

## 9. River / hydraulic doctrine

- Stage and discharge are different observations related by a site-specific rating curve
  that USGS shifts and revises (FACT). Store both; never derive one from the other in the
  platform.
- Vertical datums: stage is relative to gauge datum; thresholds are defined on that gauge's
  datum. Record the datum on every stage series and every threshold; comparisons across
  unrecorded or mismatched datums are refused, not approximated (V1 lesson, `V1_AUDIT.md` §4.5).
- **Hydraulic headroom** is expressed three ways, each labeled:
  - stage headroom: `threshold_stage − current_stage` (simple, datum-checked);
  - flow headroom: `threshold_flow − current_flow` (the only valid form on flow-defined points);
  - **time-to-threshold**: headroom ÷ current rate of rise, with the rate's window and the
    caveat that rise is nonlinear — an indicator, not a prediction.
- Rate of rise and acceleration are computed over named windows (1 h, 3 h, 6 h) from stored
  history with gap handling; trend never comes from the two endpoints of a response window.
- Routing: upstream/downstream relationships come from NWPS `upstreamLid`/`downstreamLid`
  and NHDPlus/NWM topology; travel time is estimated from history (crest-to-crest lag) and
  from NWM, and carried as a distribution.
- Regulated reaches: headroom below a flood-control dam depends on the operator's release
  plan; the platform shows the reservoir surface (§10) beside the reach and never presents
  natural-flow reasoning on a regulated reach without the regulation flag.

## 10. Reservoir, dam and flood-defense doctrine

- Reservoirs are first-class entities with: pool elevation, storage, flood-control pool
  bounds (seasonal rule curve), inflow, outflow, rate of change, operator, data source and
  freshness. **Flood-buffer capacity** = available flood-control storage (rule-curve maximum
  − current storage), with the rule curve's provenance; when inflow > outflow the buffer is
  being consumed at a computable rate.
- The platform never infers dam operations; it reports them. Forecast inflow comes from
  official sources where published; otherwise the reservoir's future state is UNKNOWN.
- Levees, dikes, floodwalls and channel works are displayed with their authoritative
  attributes (National Levee Database, local districts) and never as guarantees. A design
  height is a design height.

## 11. Explanation doctrine

Every change in a surface is attributable to named features with before/after values. The
explanation layer emits structured drivers (`feature`, `value`, `delta`, `direction`,
`weight_or_rank`, `source`, `as_of`) and mitigating factors; text is rendered from that
structure. No free-text causal reasoning is generated by a language model and presented as
hydrology. If an LLM is ever used to verbalize, it verbalizes the structure and is labeled.

## 12. Historical intelligence and hindcasting

The defining test of every intelligence output is: *what would Cascade Oracle have shown at
time T with only what was knowable at T?* The platform therefore stores, for every value, its
**knowledge time** (`available_at` — when it was retrievable, not merely when it was valid),
keeps superseded forecasts, and keeps revised observations as revisions. Replays use
knowledge time exclusively. Event Zero is the December 2025 flood: a three-AR sequence (Dec 3–5,
Dec 7, Dec 8–11) culminating in a CW3E AR-4 (coastal WA) / AR-3 (Cascade foothills) event with
~96 h of AR conditions, snow levels of 6,000–9,000 ft, and near record-low statewide snowpack —
so the response was rain on saturated soils, not snowmelt (FACT, CW3E event summary and UW OWSC
analyses cited in `docs/research/event-zero-december-2025-western-washington-floods.json`).
The Skagit at Mount Vernon crested at a preliminary record 37.73 ft / ~133,000 cfs on
2025-12-12 08:15Z (NWPS crests; USGS IV), above the 1990 record of 37.37 ft despite a lower flow
(~152,000 cfs in 1990); Snohomish at Snohomish and Cedar at Renton also set records; Ross Dam
held back ~99 % of inflow under USACE Section 7 control from Dec 8 and Howard Hanson reached a
record pool (1,189.3 ft, ~75 % of flood storage) — regulation dominated the Green, White/Puyallup
and Skagit outcomes. The first NWS Seattle Flood Watch was issued 2025-12-05 16:10 PST, about
2.5 days before the main AR and 6.5 days before the Mount Vernon crest; the Mount Vernon forecast
crest evolved 36.9 → 41.5 → 42.3 → 39.1 → 38.26 ft before the 37.73 ft observation — exactly the
forecast-evolution signal the platform must be able to replay. Every one of these facts is an
evidence row for the hindcast dataset described in `EVENT_ZERO.md`; reconstruction tasks are in
`ROADMAP.md` Phase 6.

## 13. What Cascade Oracle will not claim

- A probability without a calibrated, hindcast-evaluated method behind it.
- Flood depth, inundation extent or water-surface elevation without an authoritative model.
- That a levee or dam "will hold".
- That a source is current when it is stale, or official when it is configured.
- Any evacuation, warning or life-safety instruction. Those come from NWS and emergency
  management; Cascade Oracle links to them and labels them OFFICIAL.

## 14. Glossary

| Term | Definition |
|---|---|
| AR / IVT | atmospheric river / integrated vapour transport (kg m⁻¹ s⁻¹) |
| QPF / QPE | quantitative precipitation forecast / estimate |
| SWE | snow water equivalent (depth of liquid water held in the snowpack) |
| snow level | elevation of the rain/snow transition in precipitation; below the freezing level |
| freezing level | elevation of the 0 °C isotherm in the free atmosphere |
| hypsometry | distribution of basin area by elevation |
| rain-exposed fraction | share of basin area below the forecast snow level |
| rain-on-snow exposed fraction | share of snow-covered area below the forecast snow level |
| API | antecedent precipitation index — recency-weighted sum of past precipitation |
| headroom | distance to an official threshold, in stage, flow, or time |
| knowledge time | when a value became retrievable by the system (hindcast clock) |
| regulation class | natural / partially regulated / regulated, per reach |
