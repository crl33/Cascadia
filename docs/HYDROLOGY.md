# HYDROLOGY — the causal model Cascadia Papsukkal reasons with

This document states the science the platform is allowed to encode. It is deliberately
conservative: where the literature is settled it says FACT; where Cascadia Papsukkal adopts a
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
  - Nooksack: unregulated. **The Ferndale gauge is not tidal** — see the tidal paragraph below;
    the earlier doctrine sentence ("the lower river is tidally influenced at Ferndale") was
    corrected 2026-08-26 because Ferndale *is* the seeded forecast point NKSW1 (USGS 12213100)
    and at that gauge the tide is not measurable.
  A basin's `regulation_class` (natural / partially regulated / regulated) is a domain attribute
  that changes how every downstream quantity is interpreted.

**Tide at the seeded forecast points.** Measured 2026-08-26 from primary USGS OGC and NOAA
CO-OPS payloads, over two independent low-flow years plus Event Zero, with a known non-tidal
control gauge (Snohomish near Monroe 12150800, M2 = 0.0002 ft) carried through every
calculation:

- **FACT — no seeded forecast point is tidally affected at the gauge.** Whole-window harmonic M2
  amplitude is **≤ 0.008 ft** at all six (MVEW1 0.0077, CRNW1 0.0057, WRAW1 0.0036, RNTW1 0.0012,
  **NKSW1 0.0006**, AUBW1 0.0005) against a coastal M2 of **2.26–3.36 ft**. At Ferndale that is
  0.03 % of Cherry Point's 2.264 ft, with a band-limited slope of −0.0015 to +0.0048 ft/ft
  (r ≤ 0.29) — statistically indistinguishable from the non-tidal control
  (`research/tidal-gauge-verification-2026-08-26.md` §§4.2–4.3, 5.2).
- **FACT — and therefore no de-tiding is required for anything the platform currently serves.**
  Computed against the platform's own code path (endpoint difference,
  `STAGE_STEADY_EPS_FT_PER_H = 0.05`, live `window_h = 6`), the tidally-injected false
  rate-of-rise at the 6 h window is **≤ 0.025 ft/h** at every seeded gauge at low flow — under
  the STEADY epsilon — with 0.0 % of samples exceeding it at five of six (CRNW1 2.5 %). Rate of
  rise, headroom and time-to-threshold (§9) are sound as implemented at all six. *Operational
  applicability: full, today. Calibration status: measured, not calibrated — this is a gauge
  characteristic, not a tuned parameter, and no threshold is derived from it.*
- **The reach below the Ferndale gauge is a separate, untested claim (OPEN QUESTION).** Only the
  gauge was measured. Settling it needs either a water-level record between NKSW1 and Bellingham
  Bay (none is seeded) or a VDatum tie, which is itself blocked: Cherry Point and Port Townsend
  publish no NAVD88 datum, so a Ferndale elevation and a Cherry Point tide cannot be placed on a
  common datum by arithmetic (ibid. §§2.3, 7 items 3–4).
- **The genuinely tidal gauge is SNAW1 (Snohomish at Snohomish, 12155500) — and it is NOT
  seeded.** Its transmission is a **class, not a scalar**, and must never be quoted without its
  regime: phase-blind band-limited OLS **0.739 / 0.757 ft/ft** across two years, lag-corrected
  **0.892 / 0.919** at a **+1.25 h** lag, rms amplitude ratio 0.901 / 0.918 — and during Event
  Zero transmission **collapses to 0.223** (0.318 lag-corrected), M2 falling 2.97 → 1.08 ft, as
  open-channel hydraulics predicts when a high discharge steepens the water surface (FACT for
  the two regime points, ibid. §§4.2–4.5; INFERENCE that they trace a curve — the 3× collapse is
  one observation). A low-flow coefficient applied to a flood is 2.6–3.6× too large. Its Event
  Zero record stage is consequently a **compound** quantity: the 34.45 ft crest at
  2025-12-12T01:35Z arrived with Seattle at 4.723 ft MLLW, **6.64 ft below MHHW** (FACT, ibid.
  §6). If SNAW1 is ever seeded, the tidal-class machinery must exist first.
- **Method caution for any future tidal statistic in this repository.** Band-pass to the
  semidiurnal 10–16 h band and **exclude the diurnal band entirely**: during a flood a
  whole-window harmonic fit leaks hydrograph energy into it — the same fit assigned the
  *non-tidal* Monroe control **K1 = 0.786 ft** and P1 = 0.835 ft during Event Zero (FACT, ibid.
  §3). Carry a known non-tidal control gauge through the identical pipeline, and report the
  phase lag beside the slope.
- **The backwater term at Mount Vernon is underpowered, not absent (INFERENCE + OPEN QUESTION).**
  On the Q ≥ 40,000 cfs subset (n = 171) the sea-level coefficient is **+0.17 ± 0.10 ft/ft
  (t = +1.7)** — correctly signed, non-significant — and a Skagit crest has essentially never
  coincided with a high tide plus a large surge in the record, so the regression contains almost
  no observations of the regime that matters. "No backwater" must not be inherited: the tail's
  absence from the record is not evidence of its absence from the future
  (`CONTRADICTION_REGISTER.md` X9).

## 3. Surface I — BASIN SUSCEPTIBILITY

*How primed is the watershed to respond strongly if significant precipitation arrives?*

Inputs (each a `DerivedFeature` with provenance and percentile context):

| Feature | Meaning | Primary sources (see DATA_SOURCES) |
|---|---|---|
| soil water storage / saturation percentile | remaining storage before saturation-excess runoff dominates | NWM land output (modeled), SMAP L4 root-zone (assimilated), SNOTEL SMS (point), API proxy |
| antecedent precipitation index (API, 7/14/30 d) | recency-weighted prior rainfall | MRMS/Stage IV (observed), SNOTEL PREC |
| baseflow / groundwater proxy | how high the slow store sits | gauge baseflow separation (derived), NWM |
| river state percentile | current flow vs seasonal climatology at each gauge | USGS (observed), NWPS |
| snow storage & state | SWE by elevation band **where the pillow network supports a band — it does not everywhere; see §7**, snow-covered fraction, ripeness | SNODAS (modeled/assimilated), SNOTEL (point), MODIS/VIIRS SCA |
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

**Percentile terminology (binding, and it applies wherever this document states a percentile).**
A percentile field is **pointwise**. The basin mean of a p90 grid is *the basin mean of the
pointwise 90th percentile*, never "the basin p90" — the two are different quantities and the
second is not computed. The same rule governs any mean taken over points: a mean of per-cell or
per-site values is a **pointwise aggregate**, and its feature id, label and spread key must say
so. This is already how the shipped forcing surface is emitted (`method:basin-qpf@1.0.0`,
`DATA_SOURCES.md` NBM entry: pointwise p10/25/50/75/90 over `grid_mask` weights) — the entry
here is the doctrine that binds the rest.

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
- **Rain-on-snow melt energy is REGIME-DEPENDENT, and the partition is contested — the platform
  encodes neither side.** *(Corrected 2026-08-26; this bullet previously asserted turbulent
  dominance, and the minority of the rain-heat term, as FACT.)* Turbulent sensible + latent flux
  supplied **60–90 %** of melt energy at open, **wind-exposed** sites in a single event (FACT —
  Marks et al. 1998, February 1996 Pacific Northwest flood, Oregon Cascades). Across three
  H.J. Andrews sites over **eight years**, **net radiation was the largest term at 33–55 %**
  (turbulent max 42 %), and the authors explicitly *"question the general perception of turbulent
  energy exchange dominance of ROS and seasonal melt in the PNW"* (FACT — Mazurkiewicz, Callery &
  McDonnell 2008); a CONUS process model puts net radiation at **68 %**, longwave-dominated
  (FACT — Li et al. 2019). The **heat advected by the rain itself** is contested the same way:
  **< 10 %** (Trubilowicz & Moore 2017, 286 BC events over 10 yr), **10–15 %** (Mazurkiewicz
  2008), **29–44 % of the energy budget in persistent-melt events** (Jennings & Jones 2015) — and
  the high value belongs to precisely the persistent-melt events that produce floods, so "a minor
  term" is wrong for exactly the case this platform exists to detect. Sources and the full table:
  `research/corpus/snow-hydrology.md` §2.4, §4 contested #1–2; adjudicated at
  `CONTRADICTION_REGISTER.md` X4.
- **What both camps support, and it is the operational statement:** turbulence does not always
  dominate, but turbulence is what makes an *ordinary* rain-on-snow event an *extreme* one — so
  **wind and dewpoint at pack elevation are the discriminating variables** (INFERENCE, and a
  reconciliation rather than a resolution: `snow-hydrology.md` §2.4 labels it so). Temperature,
  humidity and wind at snowpack elevations are therefore forcing inputs, not just precipitation.
  *Calibration status: uncalibrated, and no weight, cutoff or partition may be encoded from any
  of the above. Operational applicability: none today — **no shipped surface computes a
  rain-on-snow term**, and wind and dewpoint at pack elevation are not ingested at all. This
  correction is doctrine hygiene, not an operational change; the rain-on-snow surface stays
  UNKNOWN with that reason until those inputs exist.* What would justify encoding a partition is
  the event-catalogue test named in X4 (hourly SNOTEL SWE decrements at the pillows bracketing
  the generating band, turbulent proxy versus radiative proxy, adjusted-R² difference with a
  block bootstrap) — a literature vote would not.
- Snow level rising does **not** remove snow. It changes what falls on it. Melt requires an
  energy balance; the visualization must never depict snow disappearing because the snow
  line moved (`VISUAL_TRUTH_DOCTRINE.md`).
- Basin hypsometry (area per elevation band from the DEM) is the pivot that turns a snow level
  into *rain-exposed basin fraction* and, intersected with snow-covered area, into
  *rain-on-snow exposed fraction*. These two fractions are the first derived snow features
  Cascadia Papsukkal computes (`ROADMAP.md` Phase 3).
- Point observations (SNOTEL) are ground truth for their elevation and aspect; gridded
  products (SNODAS) give spatial structure but assimilate those same points and have known
  biases in maritime packs. Fuse; do not pick one.

The next five bullets record what the pillow network can and cannot carry, measured 2026-08-26
from the AWDB payload the platform already fetches
(`research/snow-elevation-verification-2026-08-26.md`; adjudicated at `CONTRADICTION_REGISTER.md`
X13, X14, X16, X17).

- **Basin attribution is a live defect, and it is about half of the elevation gap (FACT).** Four
  sites currently mapped into seeded basins by their own primary `huc` have a *majority* of their
  `associatedHucs` in **HUC 1702\*** — the Columbia basin, east of the crest: **Harts Pass**
  6,490 ft (6/6), **Rainy Pass** 4,880 ft (5/5) and **Swamp Creek** 3,930 ft (4/6), all mapped to
  `basin:skagit`, and **Stevens Pass** 3,940 ft (4/6), mapped to `basin:snohomish-snoqualmie`
  (Thunder Basin 4,310 ft is borderline at 4/6). They are disproportionately the high-percentage
  sites: dropping them moves a 2025-12-11 pooled composite from **45.6 % to 28.9 %** (ratio-of-sums)
  **before any elevation banding**, against a further −19.0 points from banding — so basin
  misattribution, not elevation, is roughly half the gap, and it is the cheaper half to fix
  (ibid. §5). *Calibration status: the attribution is measured; the fix is an unmade policy
  decision. No exclusion rule, weight or cutoff is adopted here. Operational applicability:
  presentational — the SWE driver ships `direction: context_not_scored`, so a wrong composite
  moves no band and no 6–120 h statement; it moves a number rendered beside one.*
- **Elevation stratification is a PER-BASIN capability, not a universal band (FACT).** Site counts
  and elevation spreads inside the seeded HUC8s: **skagit** (n = 9, 1,680–6,490 ft) and
  **puyallup-white** (n = 5, 2,250–5,810 ft) can support an elevation-stratified SWE statistic;
  **nooksack** (n = 3) and **green-duwamish** (n = 4) can only with a **single-pillow upper band**,
  which must be flagged n = 1; **cedar** (n = 4, **2,930–3,810 ft**, spread 880 ft) and
  **snohomish-snoqualmie** (n = 4, **3,320–4,010 ft**, spread 690 ft) **cannot, at any band
  elevation — above their top pillow the honest output is UNKNOWN** (ibid. §§2–4). ASSUMPTION
  carried from that measurement: a band needs **≥ 2 reporting sites** to be a statistic rather
  than a point observation. **Do not write 4,500 ft, or any single universal band, into this
  platform**: at 4,500 ft the upper band is *empty* for those two basins, so stratification would
  return the unstratified number under a different name — a tautology that emits a number where
  UNKNOWN is correct, which is the dangerous failure mode. The band must be **data-driven and
  basin-aware**; what would justify a specific band is basin hypsometry from 3DEP (to know what
  area fraction a band stands for) plus a forecast snow level per basin per cycle.

  **Corrected 2026-08-28: the snow level now exists and is live.** `nbm.fetch_core_snowlvl` writes
  `basin_snow_level_pointwise_p{10,50,90}` under `method:basin-snow-level@1.0.0`, area-weighted
  over the basin mask, every 6 h — 120 rows per percentile in production, 1,876-3,765 m.

  **And later the same day, hypsometry landed too** (`method:basin-hypsometry@1.0.0`): per-basin
  elevation-area curves in 20 m bins, derived offline from USGS 3DEP 1-arc-second tiles over the
  full-resolution seeded polygons (`scripts/build_basin_hypsometry.py`), validated against the
  physical basins — Rainier caps the Puyallup-White at 4,388.8 m, Baker the Nooksack at 3,283 m,
  and the Skagit pixel sum reproduces the WBD area to 0.30 %. The 3DEP staged tiles carry full
  data north of 49°N (probed: zero nodata on the all-Canada tile), so the cross-border Skagit and
  Nooksack headwaters are in the curve rather than silently clipped at the border. The
  **rain-exposed fraction** — the surface below the forecast snow level, where precipitation
  arrives as rain — now ships as a `context_not_scored` driver on the forcing surface
  (`method:basin-rain-exposed-fraction@1.0.0`), its spread taken from the snow level's own
  p10-p90 and its label carrying the HUC8-union geometry caveat. Rain-ON-SNOW exposure remains
  open: it additionally needs observed snow-covered area, which no ingested product yet supplies.

  It also settles what resolution that hypsometry needs, which is less than it looks. Measured
  over 96 basin-hours of live rows, the snow level's OWN p10-p90 spread has a **median of 241 m**
  and reaches 908 m. An elevation model finer than that cannot improve a rain-exposed fraction,
  because the surface it is being intersected with is not known to better than that. A coarse DEM
  is therefore the scientifically honest choice as well as the cheap one; buying 30 m vertical
  fidelity to intersect against a 241 m uncertainty would be precision theatre. Until they do, the defensible statement is per basin and explicitly bounded: *"SWE
  at the N sites between X and Y ft is Z % of median (method, day, n, exclusions); no observation
  exists above Y ft."*
- **Elevation is not the only axis (FACT).** On 2025-12-11 Swamp Creek at 3,930 ft read **130.6 %**
  of median while Olallie Meadows at 4,010 ft and Burnt Mountain at 4,160 ft read **0.0 %** (ibid.
  §6.3). Windward/leeward exposure is a second, independent axis, and no elevation band separates
  those three sites.
- **A low-elevation SWE deficit LOWERS rain-on-snow potential; it does not raise it (INFERENCE,
  on mass balance).** Rain-on-snow requires snow to *exist* at the elevations rain falls on, and
  melt cannot exceed the snow available there. Below 4,500 ft on 2025-12-11, SWE was **13.8 % of
  median across 20 reporting sites, 10 of them at exactly 0.00 in** (FACT, ratio-of-sums, day, n
  and exclusions stated — ibid. §6.3). The defect a pooled percent-of-median composite creates is
  therefore **wrong-mechanism attribution, not understated magnitude**: a displayed "44 % of
  median snowpack" invites a reader to reason about a snow buffer and a melt contribution when
  the correct operational reading was *"there is effectively no snow below 4,500 ft — treat this
  as rain on wet soil"*. That is the same event characterisation §12 already carries. The
  narrower wording *"misleading in the direction of calm"* is the phrasing to keep; the reverse
  claim — that a low-band deficit *raises* rain-on-snow risk — is physically backwards.
- **Percent-of-median SWE is a POINTWISE aggregate, and the platform's estimator is
  mean-of-ratios.** `swe_percent_of_median` computes, per basin, the **mean of per-site ratios**
  over sites mapped by primary HUC8, excluding absent value, absent median, median ≤ 0 and
  suspect QC flag (FACT — reproduced from the shipped code path, ibid. §6). It is **not** a
  ratio-of-sums, and the two are not interchangeable: on 2025-12-08 in the Puyallup-White they
  differ by more than a factor of two (**48.7 %** ratio-of-sums against **23.3 %**
  mean-of-ratios). Per the §4 percentile rule, the number is a pointwise aggregate of point
  observations and must be labelled as one — never as "the basin snowpack". A composite without
  its **estimator, its `n` and its band** is not comparable to yesterday's composite and must not
  be rendered as if it were. Ratio-of-sums asks *"what fraction of normal basin storage is
  present"*; mean-of-ratios asks *"how anomalous is the typical site"*; both are legitimate and
  the error is quoting one while criticising the other. This is a **declaration**, not an
  experiment: no measurement settles it, and the choice belongs in the method id. A **pooled
  multi-basin composite is not a number this platform emits**, and should not start being one.

## 8. Soil doctrine

- The useful quantity is **remaining storage**, not a binary "saturated". As storage fills,
  saturation-excess runoff generation expands (variable source areas), interflow accelerates,
  and a given rainfall produces a larger, faster hydrograph (FACT for forested PNW soils;
  infiltration-excess runoff is rare there).
- No single product observes basin soil water. Cascadia Papsukkal fuses: modeled soil moisture
  (NWM, climatological percentiles), satellite root-zone estimates (SMAP L4, 9 km, coarse but
  spatially honest), point probes where present (SNOTEL SMS), and an antecedent precipitation
  index as a transparent fallback. Each contributes a percentile; disagreement between them is
  reported, not hidden.
- Percentiles require climatology; the platform builds its own from stored history and, until
  enough history exists, labels percentiles as derived from the product's own reanalysis with
  the period stated. The §4 pointwise rule binds these too: a percentile computed per cell or per
  site and then averaged over a basin is a **pointwise aggregate**, and the feature id and label
  must say so rather than implying a basin-level percentile was computed.

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

The defining test of every intelligence output is: *what would Cascadia Papsukkal have shown at
time T with only what was knowable at T?* The platform therefore stores, for every value, its
**knowledge time** (`available_at` — when it was retrievable, not merely when it was valid),
keeps superseded forecasts, and keeps revised observations as revisions. Replays use
knowledge time exclusively. Event Zero is the December 2025 flood: a three-AR sequence (Dec 3–5,
Dec 7, Dec 8–11) culminating in a CW3E AR-4 (coastal WA) / AR-3 (Cascade foothills) event with
~96 h of AR conditions, snow levels of 6,000–9,000 ft, and near record-low statewide snowpack —
so the response was rain on saturated soils, not snowmelt (FACT, CW3E event summary and UW OWSC
analyses cited in `docs/research/event-zero-december-2025-western-washington-floods.json`).
The Skagit at Mount Vernon crested at a preliminary record 37.73 ft / ~133,000 cfs on
2025-12-12 08:15Z (NWPS crests; USGS IV), above the 1990 crest of 37.37 ft / ~152,000 cfs — **but
that pair is not a homogeneous hydraulic comparison and must not be read as a measurement of
rating drift.** *(Corrected 2026-08-26; the sentence previously read "above the 1990 record of
37.37 ft despite a lower flow".)* The 1990 crest is **breach-depressed**: the Fir Island levee
failed ~3 miles below the gauge and "increased the river slope and velocity below Mount Vernon,
causing an artificially low crest stage at the Mount Vernon gage" (FACT — USACE Seattle District /
Skagit County, *Skagit River Basin Flood Risk Management Study — Hydrology Technical
Documentation*, August 2013, §2.4.9.4; the levee failed in the first November 1990 flood and
again during the second, which is the one that produced the 37.37 ft annual peak). Pairing a
levee-intact 2025 stage against it **exaggerates** the apparent drift. That the lower-Skagit
rating has drifted at all is supported and physically corroborated — bed aggradation in a
levee-confined sand-bed reach — but **its magnitude is disputed and this platform asserts none**:
the corpus carries four mutually incompatible estimates for the same reach (−29 %, now SUPERSEDED
because both its data points are contaminated; −9 to −11 % at a 33.00 ft reference; −4.4 % at
37 ft; and "not a trend at all but a destabilisation", residual sd 0.25 ft for 1948–2005 against
1.38 ft for 2006–2024). They are not the same quantity — different estimators, reference stages
and windows, and one is a variance claim (INFERENCE; `CONTRADICTION_REGISTER.md` X1). All four
agree on the part that would matter operationally: the **scatter** (±0.68 to ±1.4 ft) is
comparable to or larger than the trend, against **2 ft** NWS category spacing at that gauge.
*Calibration status: uncalibrated and unadopted. Operational applicability: none today — §9
forbids converting stage to flow or flow to stage, so no 6–120 h statement depends on the drift.*
A single figure may enter doctrine only with one declared estimator, window and reference stage.
Snohomish at Snohomish and Cedar at Renton also set records; Ross Dam
held back ~99 % of inflow under USACE Section 7 control from Dec 8 and Howard Hanson reached a
record pool (1,189.3 ft, ~75 % of flood storage) — regulation dominated the Green, White/Puyallup
and Skagit outcomes. The first NWS Seattle Flood Watch was issued 2025-12-05 16:10 PST, about
2.5 days before the main AR and 6.5 days before the Mount Vernon crest; the Mount Vernon forecast
crest evolved 36.9 → 41.5 → 42.3 → 39.1 → 38.26 ft before the 37.73 ft observation — exactly the
forecast-evolution signal the platform must be able to replay. Every one of these facts is an
evidence row for the hindcast dataset described in `EVENT_ZERO.md`; reconstruction tasks are in
`ROADMAP.md` Phase 6.

## 13. What Cascadia Papsukkal will not claim

- A probability without a calibrated, hindcast-evaluated method behind it.
- Flood depth, inundation extent or water-surface elevation without an authoritative model.
- That a levee or dam "will hold".
- That a source is current when it is stale, or official when it is configured.
- Any evacuation, warning or life-safety instruction. Those come from NWS and emergency
  management; Cascadia Papsukkal links to them and labels them OFFICIAL.

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
