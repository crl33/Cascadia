# Atmospheric rivers: structure, scale, and landfall

*Corpus entry, 2026-08-24. Part of the Cascadia Papsukkal flood-science corpus.*

*Claim labels follow `docs/DATA_DOCTRINE.md` conventions: **FACT** = read on a page or dataset I
fetched in this pass (URL in §9); **INFERENCE** = reasoned from cited facts; **ASSUMPTION** = a
working simplification; **OPEN QUESTION** = unresolved. Where a source was paywalled or blocked, the
claim says "not independently fetched" and is downgraded to INFERENCE. Nothing in the repository was
modified except this file.*

---

## 1. Headline

**The atmospheric river is the necessary cause of western Washington flooding and a poor sufficient
one: essentially every flood here is an AR, and most ARs here are not floods.** Over WY1980–2009,
*every* peak daily flow exceeding a 5-year return period in four unregulated western-Washington
basins occurred with a landfalling AR, and 46 of 48 annual peak daily flows in WY1998–2009 did — yet
the same study is explicit that *not all* ARs in that period generated flooding (Neiman et al. 2011,
FACT — the paper's wording is "not all"; that most ARs here are non-floods is an INFERENCE, supported
by the Russian River category-to-flood rates in §2.8 rather than by Neiman et al. directly). The information that separates the two is not IVT magnitude. It is a **conjunction of five
conditions**, of which magnitude is one: *orientation* of the low-level flow into the specific basin,
*strength* of the onshore low-level vapour flux, *stationarity* (whether the AR stalls), *melting
level* (how much of the basin is rain-exposed), and *antecedent soil wetness* (Neiman et al. 2011,
FACT). Because Cascadia Papsukkal's forcing surface currently bands on basin-mean QPF alone, it is
measuring the one term of that conjunction that models are *worst* at, and none of the four terms
whose predictive value is published with variance-explained numbers.

The two AR variables with published skill against *runoff*, not against precipitation, are
**storm-total upslope IVT** (74 % of the variance in storm-total rainfall and 61 % of storm-total
runoff volume) and **duration of AR conditions** (doubling the mean duration multiplied peak
streamflow by ~6× and storm-total runoff volume by >7×) (Ralph et al. 2013, FACT). Neither exists in
the repository today.

---

## 2. Mechanisms — the physics, stated properly

### 2.1 What an AR is, and why the measurement variable is IVT and not IWV

The AMS *Glossary of Meteorology* definition, adopted in 2018 after a community debate and reproduced
in the AR-scale paper, describes an AR as a long, narrow, transient corridor of strong horizontal
water-vapour transport, typically associated with a low-level jet stream ahead of the cold front of an
extratropical cyclone (Ralph et al. 2018, 2019, FACT). Three parts of that sentence are load-bearing
and are routinely dropped in operational usage:

- **transient corridor** — an AR is a feature in a flow, not a fixed pipe; its Eulerian signature at a
  point is a *time series*, which is why the standard scale is defined at a point (§2.8);
- **horizontal transport** — the quantity is a flux, not a reservoir. IWV (precipitable water) is a
  reservoir;
- **ahead of the cold front** — the AR is a warm-sector, *pre-cold-frontal* structure. Its position
  relative to the front is what fixes where the low-level jet and the strongest upslope forcing are.

The intensity variable is **integrated vapour transport**:

```
        1   ∫ p_b
IVT =  ---       q · V_h  dp          p_b = 1000 hPa, p_t = 200 hPa
        g   ┘ p_t
```

where `q` is specific humidity (kg kg⁻¹), `V_h` the horizontal wind vector (m s⁻¹), `g` gravity; the
result has units kg m⁻¹ s⁻¹ (Ralph et al. 2019 appendix, FACT — MERRA implementation integrates every
25 hPa from 1000 to 700 hPa and every 50 hPa from 700 to 200 hPa).

IVT is preferred over IWV for four documented reasons (Ralph et al. 2019, FACT): it is less dependent
on surface elevation; it relates more directly to precipitation; NWP models predict IVT more skilfully
than they predict precipitation (Lavers et al. 2016); and it carries wind, which is half of the
orographic forcing. The choice is not cosmetic. Ralph et al. 2019 note that the IWV of their example
Cat 5 event was *smaller* than that of their Cat 3 and Cat 4 examples (FACT) — IWV and IVT do not
co-rank events.

**The choice moves the map, and it moves it against Washington.** Rutz et al. 2014 computed AR
frequency two ways over the same ERA-Interim record: using IVT ≥ 250 kg m⁻¹ s⁻¹, the maximum sits
along the **Oregon–Washington coast** (>15 % of 6-h analysis times); using IWV ≥ 20 mm, the maximum
sits along the **Northern California coast** and *declines* northward into Oregon and Washington
(FACT). Any statement of the form "Washington is the AR maximum of the West Coast" is conditional on
using a transport threshold rather than a moisture threshold. This is the single most important
detection-methodology fact for this platform's latitude.

Reassuringly, at the level of a single storm's *total* transport the two edge definitions nearly
agree: across 21 ARs sampled by 304 dropsondes, mean total IVT computed with IVT-threshold edges
versus IWV-threshold edges differed by less than 10 % (Ralph et al. 2017, FACT). So the variable
choice is second-order for the transport in one storm and first-order for the climatology of where
storms are counted.

### 2.2 Detection: ARTMIP, and how much the algorithm matters

There is no single AR detection algorithm. ARTMIP (Atmospheric River Tracking Method Intercomparison
Project) applied 20+ published AR identification and tracking methods (ARDTs) to a single dataset
(MERRA-2), a single period (Jan 1980 – Jun 2017) and overlapping regions, precisely to quantify the
uncertainty attributable to method alone (Shields et al. 2018; Rutz et al. 2019, FACT).

Findings that matter operationally:

- AR **frequency, duration and seasonality span a wide range** across methods; the **meridional
  distribution along coastal transects is comparatively similar** across methods (Rutz et al. 2019,
  FACT — this is the good news for a coastal-basin platform).
- Methods with **more restrictive identification criteria produce weaker climatological statistics**;
  less restrictive methods identify more ARs and give more robust statistics (Rutz et al. 2019, FACT).
- Threshold choice **self-selects intensity**: methods with higher moisture thresholds report higher
  mean AR intensity by construction (Shields et al. 2018, FACT).
- Methods split into two families — "condition" algorithms that flag grid points meeting criteria at
  an instant, and "tracking" algorithms that follow objects through time; thresholds range from
  absolute (250 kg m⁻¹ s⁻¹) to statistical (85th percentile) to climate-relative (Shields et al. 2018,
  FACT).
- In a single February-2017 case, on some days most methods agreed there was an AR at a California
  point and on other days only a handful did (Shields et al. 2018, FACT).
- A Bayesian detector ensemble (TECA-BARD) built by sampling detector parameters consistent with
  expert hand-labelling found that **even the sign of the correlation between global AR count and
  ENSO depends on which plausible parameter set is used** (O'Brien et al. 2020 — abstract read, full
  text not independently fetched; INFERENCE at that strength).

**Consequence for this platform (INFERENCE).** "Is there an AR?" is not an observation; it is a
*method output*. Under `DATA_DOCTRINE.md` §2 any AR flag or AR category the platform computes is
`DERIVED`/`EXPERIMENTAL` and must carry the detector's parameters (variable, threshold, grid, geometry
test, temporal continuity rule) as part of `method_version`. Two products disagreeing about whether an
AR is present is *not* a data fault and must not be rendered as one.

### 2.3 Vertical structure: the low-level jet and the orographic controlling layer

The composite vertical structure over the four western-Washington flood basins (top-10 annual peak
daily flows, WY1980–2009, NARR composites at an offshore point at 46.84 °N, 124.42 °W) is (Neiman et
al. 2011, FACT):

- strong frictional **clockwise turning of wind direction in the lowest ~1 km**, with the near-surface
  flow generally from the south–southwest inside a stably stratified surface layer;
- a **low-level jet at ~0.8–1.0 km MSL**, at the top of that directional-shear layer;
- **maximum water-vapour flux just below 1 km MSL**, i.e. above boundary-layer effects — the same
  altitude at which upslope forcing of orographic precipitation is statistically most robust in
  California coastal storms (Neiman et al. 2002, 2009, via Neiman et al. 2011);
- **weak moist stratification in the 1–2 km MSL layer**, vertically adjacent to the strongest inbound
  vapour flux — the combination that most favours orographic enhancement;
- relative humidity > 80 % through the lowest 2.5–5 km;
- above 2 km, clockwise directional shear in strong speed shear and stable stratification, i.e. warm
  advection in a baroclinic environment; that warm advection is stronger on the day *before* the peak.

Two structural consequences. First, **the forcing layer is 0.8–2 km MSL**, and western-Washington
catchments extend into or through it — so a basin's hypsometry decides how much of it is exposed to
the jet, not only how much is above the snow level. Second, the **stable marine boundary layer beneath
the AR decouples the ocean surface from the AR winds aloft**; this is a known data-assimilation
failure mode, because surface pressure/wind information cannot be distributed vertically correctly
(Ralph et al. 2020, FACT; characterised with 1054 dropsonde profiles across 99 AR transects in Ralph
et al. 2024, cited in AR Recon BAMS 2025, FACT-by-citation).

### 2.4 Horizontal structure and scale

- Typical landfalling AR: order **2000 km long, 800 km wide** (Ralph et al. 2020, FACT).
- Dropsonde-measured **mean AR width 890 ± 270 km** across 21 ARs / 304 sondes (Ralph et al. 2017,
  FACT).
- **Total IVT (TIVT) integrated across the AR cross-section: 4.7 × 10⁸ ± 2 × 10⁸ kg s⁻¹**, about
  **2.6× the mean discharge of the Amazon** (Ralph et al. 2017, FACT).
- ARs carry **>90 % of midlatitude poleward water-vapour transport in <10 % of the zonal
  circumference** (Zhu & Newell 1998, as quoted in Rutz et al. 2014 and Neiman et al. 2011, FACT).
- The *precipitating* region is narrower than the AR. For PNW coastal extremes the precipitation area
  of a major event is roughly **200 km wide** (Warner, Mass & Salathé 2012, FACT). In the March 2005
  Pacific-Northwest case, the region of AR conditions adjacent to and on the warm side of the surface
  front was taken as ~400 km wide, and the SSM/I-derived AR width as ~500 km (Ralph et al. 2011, FACT).

**INFERENCE.** An 800-km-wide AR whose heavy-precipitation core is ~200 km wide, landing on a coast
whose basins are 30–80 km apart, means that *which* western-Washington basin floods is decided at a
scale finer than the AR object. Basin-resolved forcing is not a refinement of AR-scale forcing; it is
a different question.

### 2.5 The orographic transfer function, and where it fails

Precipitation is not IVT; it is what happens when IVT is forced to ascend. The empirical form is the
upslope model: precipitation rate scales with the component of the low-level moisture flux **projected
onto the terrain gradient**. Quantitatively, at a coastal atmospheric river observatory, differences in
**storm-total water-vapour transport directed up the mountain slope explained 74 % of the variance in
storm-total rainfall and 61 % of the variance in storm-total runoff volume** across 91 events (Ralph et
al. 2013, FACT). Ralph et al. 2019 restate the same result as the justification for putting duration
into the scale (FACT).

Two failure modes, both documented for this coast:

1. **Blocking.** When the Froude number `Fr = U/(N h)` is small (weak cross-barrier wind `U`, strong
   static stability `N`, tall barrier `h`), the flow is dammed and diverted along the barrier rather
   than lifted over it, and the linear upslope prediction degrades badly (established in the prior
   solo pass, `flood-genesis-mechanisms-2026-08-24.md` §2.3, FACT-by-citation there). Neiman et al.
   2011's finding that flood composites have **weak moist static stability** in the 1–2 km layer is the
   same statement from the other side: the flooding cases are the *unblocked*, high-Froude cases.
2. **Rain shadowing by upstream terrain.** In western Washington the Olympics and the Vancouver Island
   mountains stand between the Pacific and the Cascade basins. Neiman et al. 2011 quantified the
   consequence per basin (§5.1).

### 2.6 Duration and stationarity

**Duration is a first-class variable, not a modifier.**

- Mean duration of AR conditions at a coastal point: **20 h** (91 observed events, Bodega Bay 2004–10;
  Ralph et al. 2013, FACT), independently reproduced as **~20 h** at a nearby ERA-Interim grid point
  (Rutz et al. 2014, FACT). **12 % of events exceeded 30 h** (Ralph et al. 2013, FACT).
- Along the coast, mean AR duration is greatest on the **Oregon coast at 23–24 h**, falls to **~19 h at
  the north-west tip of the Washington coast**, ~17 h near Point Conception, and ~12 h in the Great
  Basin (Rutz et al. 2014, FACT). About **50 % of coastal AR events last more than 12 h**, versus
  20–40 % at interior locations (Rutz et al. 2014, FACT).
- The **top-decile-duration events average ~40 h**; the 7× figure below is storm-total *runoff volume*,
  not streamflow
  (Ralph et al. 2013a as summarised in Rutz et al. 2014, FACT).
- Directly: **ARs with double the composite mean duration produced nearly 6× greater peak streamflow
  and more than 7× the storm-total runoff volume** (Ralph et al. 2013, FACT).

Duration at a point is produced by three things: the AR's own width, its translation speed, and
whether it **stalls**. "The AR stalled over the basin" is one of Neiman et al. 2011's five flood
attributes (FACT). Stalling is a synoptic-scale condition — Fish et al. 2019 found AR families are
favoured when the North Pacific synoptic features are **semi-stationary** (FACT).

### 2.7 Mesoscale frontal waves — the PNW amplifier and the predictability wall

A **mesoscale frontal wave (MFW)** is a meso-α-scale (≈500–1000 km wavelength) wave that develops on
the primary cold front, often deepening into a secondary cyclone (Ralph et al. 2011, FACT). MFWs
modify the AR's **position, strength, propagation and duration** at landfall (Ralph et al. 2011;
Neiman et al. 2016; Martin et al. 2018; Michaelis et al. 2021 — as summarised in AR Recon BAMS 2025,
FACT).

The Pacific-Northwest case that established this:

- **March 2005, north-west Oregon / south-west Washington.** A long-lived MFW held AR conditions
  (IWV > 2 cm) and heavy rain over north-west Oregon for **at least ~34 h**; at a site farther
  south-east the wave staying north prolonged deep AR moisture by **nine additional hours**. A frontal
  isochrone method mapped a **maximum AR duration of 28–30 h centred exactly over the heaviest
  precipitation** (Ralph et al. 2011, FACT). The same case had a documented **tropical moisture
  entrainment near Hawaii** driven by planetary-scale phasing (§2.9).

The predictability cost is measured:

- Forecasts skilfully predicted secondary cyclogenesis **only at lead times shorter than 36 h**;
  skill in the large-scale pressure pattern and IVT was **lost by 96 h**. Beyond 36 h, failure to
  predict the secondary cyclone produced significant uncertainty in forecast AR *intensity* and a
  **long bias in forecast AR duration**; inside 36 h, failing the associated warm front produced
  **large over-prediction of upslope water-vapour flux** (Martin et al. 2019, FACT).
- Latent heating is what makes MFWs exist. In MPAS-A simulations with latent heating switched off:
  one event's AR conditions over the watershed were **6 h shorter**, peak IVT **~17 % weaker and 6 h
  earlier**, and precipitation totals **~64 % lower**; the second event was **24 h shorter**, maximum
  IVT **~42 % weaker and 18 h later**, precipitation **~49 % lower** (Michaelis et al. 2021, FACT).

**INFERENCE.** The MFW is the mechanism by which two ARs of identical peak IVT produce a 34-h event in
one basin and a 12-h event next door. It is also the reason a 3–5 day AR forecast can be right about
intensity and wrong about *everything the hydrology cares about*. Any platform that displays a 72-h
QPF without displaying its run-to-run volatility is hiding this.

### 2.8 The AR scale (Ralph et al. 2019) — exact definition and its stated limits

Definition (Ralph et al. 2019, BAMS 100(2), 269–289, FACT):

| Max IVT (kg m⁻¹ s⁻¹) — *maximum instantaneous*, per Table 2 / Fig. 4 | Label | Duration < 24 h | 24–48 h | ≥ 48 h |
|---|---|---|---|---|
| ≥250 and <500 | weak | *unranked* (needs ≥12 h) | AR 1 | AR 2 |
| ≥500 and <750 | moderate | AR 1 | AR 2 | AR 3 |
| ≥750 and <1000 | strong | AR 2 | AR 3 | AR 4 |
| ≥1000 and <1250 | extreme | AR 3 | AR 4 | AR 5 |
| ≥1250 | exceptional | AR 4 | AR 5 | AR 5 (capped) |

Mechanics that are usually lost in transmission and that a provenance-carrying platform must record:

- The scale is **Eulerian at a point**, computed from a time series of IVT; it has **no shape or
  geometry requirement** and does not track the AR as an object (FACT). It is therefore *not* an AR
  detection algorithm in the ARTMIP sense.
- CW3E computes it on a **0.5° × 0.5° grid**, a resolution the authors describe as somewhat arbitrary
  and chosen for situational awareness (FACT).
- "AR conditions" means IVT ≥ 250 kg m⁻¹ s⁻¹; an "AR event" is one **continuous** period of AR
  conditions at that point (FACT). **A sequence of ARs separated by sub-threshold gaps is not one
  event and cannot be scored as one category.**
- **Promotion is common.** At Bodega Bay the mean of the maximum 3-h IVT for Cats 3–5 came out
  *slightly below* the nominal IVT threshold for those categories, meaning a material share of high-
  category events got there by lasting ≥48 h rather than by reaching the IVT threshold (FACT). An
  "AR 4" is therefore not a statement that IVT reached 1000.
- Duration ≥48 h promotes only **one** category, and Cat 5 is the cap (FACT).

Scale characteristics at one well-observed point (Bodega Bay, MERRA, Jan 1980 – Apr 2017; Ralph et al.
2019 Table 4, FACT):

| Category | Events | Mean duration | Mean max 3-h IVT |
|---|---|---|---|
| AR 1 | 268 | 21 h | 480 kg m⁻¹ s⁻¹ |
| AR 5 | 10 | 72 h | 1118 kg m⁻¹ s⁻¹ |

(Cats 2–4 increase monotonically between these; the paper reports steady progression in duration,
maximum IVT and storm-total IVT from Cat 1 to Cat 5.)

**Limits the authors themselves state** (Ralph et al. 2019, FACT):

1. The duration requirement **under-recognises short, very intense rate events** (e.g. debris-flow
   producers).
2. Impacts vary with **column temperature and the rain/snow line**, which the scale does not contain.
3. The scale is **not linked to a location**, so its impact meaning varies with topography, land
   surface and antecedent conditions.
4. It is **only as good as the model that produced the IVT**. This is not in the enumerated list of
   three shortcomings but the authors state it explicitly in the forecast-example section: the scale
   "is dependent on an accurately modeled atmospheric forecast, and will only be as reliable as the
   forecast model being used" (FACT, verbatim). In their own forecast example (GFS, 60–180 h lead,
   February 2017), verification came in **~1 category stronger than forecast over much of the West
   and 1–2 categories stronger from coastal California north-eastward** (FACT).

### 2.9 Moisture sources and tropical moisture exports

- Some ARs entrain tropical water vapour, but **this is not a trait of all ARs** (Ralph et al. 2019,
  FACT). "Pineapple Express" is a subset, not a synonym.
- A 40-year global climatology combining deep-learning AR detection with Lagrangian moisture tracking
  finds a robust asymmetry: **along western continental boundaries — which includes western North
  America — tropical contributions to AR precipitation are typically 30–40 %**, versus 60–70 % on
  eastern boundaries; tropical contribution correlates negatively with latitude; tropical moisture
  mainly **preconditions AR formation** while the water that actually falls is progressively replaced
  by extratropical uptake along the poleward path (Crespo-Otero et al. 2026, FACT).
- Water-vapour tracer modelling shows that when an AR is present, a **higher fraction of vapour from
  remote southerly sources coincides with more intense precipitation**; ARs are built from a sequence
  of meridional excursions and **can persist through more than one cyclone life cycle** (Sodemann &
  Stohl 2013, FACT — North Atlantic case; transferability to the North Pacific is INFERENCE).
- Winter West Coast AR composites extend north-eastward from the tropical eastern Pacific; summer
  composites are zonal and lack that tropical origin (Neiman et al. 2008b, FACT).
- The March 2005 PNW flood AR had **direct entrainment of tropical water vapour near Hawaii**, enabled
  by phasing of planetary-scale tropical–extratropical interactions, documented by dropsondes
  (Ralph et al. 2011, FACT).

**INFERENCE for the platform.** A "tropical connection" is a narrative attribute, not a hazard
attribute. The 30–40 % figure says the tropics are a *precondition* term, not a mass-balance term, on
this coast. Do not badge an event as more dangerous because imagery shows a tropical tail.

### 2.10 Landfall latitude and orientation

- **Latitude climatology.** From SSM/I 1997–2005, the northern West Coast recorded **301 AR days**
  versus **115** on the southern West Coast (Neiman et al. 2008b, FACT). AR frequency by IVT250 peaks
  along the Oregon–Washington coast (Rutz et al. 2014, FACT).
- **Intensity climatology.** IVT return periods along the coast: **750, 1000 and 1250 kg m⁻¹ s⁻¹
  recur roughly every 1, 3 and 20 years** at 25–40 °N landfall points; more comprehensively, IVT of
  1000 kg m⁻¹ s⁻¹ is reached about **once a year on the Oregon coast, once every 2 years on the
  Washington coast**, once every 3 years at San Francisco and once every 10 years at Los Angeles
  (Dettinger et al. 2018 via Ralph et al. 2019, FACT).
- **Why the maximum sits at Oregon.** IWV increases equatorward and AR low-level winds increase
  poleward; the Oregon coast is the most favourable geographic overlap of the two, which is where the
  Cat 5 local maximum appears (Ralph et al. 2019, FACT).
- **Orientation is basin-specific and statistically separable** (Neiman et al. 2011, FACT) — see §5.1.
- **ENSO shifts landfall latitude** (El Niño equatorward, La Niña poleward toward Washington) but does
  not control the tail (established in the prior pass, `flood-genesis-mechanisms-2026-08-24.md` §5.2).
- Climate modes also modulate AR **orientation**, with ENSO particularly affecting the orientation of
  temporally clustered ARs (Zhang et al. 2024 Comms. Earth Environ., FACT).

### 2.11 AR families, clusters, and temporal compounding

- **Definition and counts.** At Bodega Bay, 228 AR events; with a 5-day aggregation period there were
  **109 AR families averaging 2.7 ARs each**; across plausible aggregation periods, families typically
  contain **2–6 ARs** (Fish, Wilson & Ralph 2019, FACT). About **half of all ARs belong to a family**
  (Fish et al., as cited by Zhang et al. 2024, FACT-by-citation).
- **Synoptics.** Families are associated with lower geopotential heights across the midlatitude North
  Pacific, an enhanced subtropical high, a stronger zonal North Pacific jet, and **semi-stationary**
  synoptic features (Fish et al. 2019, FACT).
- **The aggregation window is regional.** The time window within which clustering exceeds random
  chance varies by location (Zhou, Wehner & Collins 2024, FACT) — so a single hard-coded gap threshold
  is a per-basin parameter, not a constant.
- **Density matters more than count.** Clusters of equal AR count differ mainly in the *spacing*
  between landfalls. Dense clusters (≥50th percentile of the AR-condition time fraction) contain
  higher-category ARs on average, and (Zhou, Wehner & Collins 2024, FACT):
  - **20–50 %** of top-2 % precipitation days on the US West Coast fall in dense clusters versus
    10–20 % in sparse clusters;
  - **more than 60–65 %** of West Coast AR precipitation is attributable to dense clusters;
  - over **Oregon and Washington**, AR precipitation intensity in dense clusters is **120–140 %** of
    that in sparse clusters;
  - runoff associated with AR clusters is about **60 %** of total coastal runoff, and over the
    **Cascade Range the extra runoff from dense clusters is 150–300 % more than from sparse clusters**;
  - dense clusters peak in **November** and are most active October–January.
- **Economic signature.** Temporally clustered ARs produce **more than three times** the expected
  losses in California relative to isolated AR occurrence (Bowers et al., as cited by Zhang et al.
  2024 — primary not independently fetched; INFERENCE at that strength).
- **Projection.** Cluster density and category are projected to increase with warming level (Zhou,
  Wehner & Collins 2024, FACT).

**The mechanism** is the one the prior pass named: the earlier ARs remove the basin's remaining
storage so the later one cannot be absorbed (fill-and-spill, `flood-genesis-mechanisms-2026-08-24.md`
§1.3). The Cascade Range 150–300 % runoff figure is the strongest region-specific evidence that this
matters *here*, not only in California.

---

## 3. Quantitative anchors

| Quantity | Value | Context | Source |
|---|---|---|---|
| AR condition threshold | IVT ≥ 250 kg m⁻¹ s⁻¹ | definition used by the AR scale and most ARDTs | Ralph et al. 2019 |
| AR scale IVT thresholds | 250 / 500 / 750 / 1000 / 1250 kg m⁻¹ s⁻¹ (max 3-h mean) | Cats 1–5 before duration adjustment | Ralph et al. 2019 |
| AR scale duration rule | <24 h demote one; ≥48 h promote one; Cat 5 cap; weak+<24 h unranked; ≥12 h minimum | applied per point | Ralph et al. 2019 |
| AR scale grid | 0.5° × 0.5°, Eulerian at a point | CW3E implementation | Ralph et al. 2019 |
| Mean AR duration, coastal point | 20 h (91 events); 12 % > 30 h | Bodega Bay ARO, 2004–10 | Ralph et al. 2013 |
| Mean AR duration, Oregon coast | 23–24 h | ERA-Interim, Nov–Apr | Rutz et al. 2014 |
| Mean AR duration, NW Washington coast | ~19 h | ERA-Interim, Nov–Apr | Rutz et al. 2014 |
| Top-decile AR duration | ~40 h (the 7× figure is storm-total runoff volume, not streamflow — see row below) | Bodega Bay | Ralph et al. 2013a via Rutz et al. 2014 |
| Duration → runoff scaling | 2× mean duration ⇒ ~6× peak streamflow, >7× storm-total runoff volume | Russian River | Ralph et al. 2013 |
| Upslope IVT → rainfall | 74 % of variance in storm-total rainfall | 91 events, storm-total upslope IVT | Ralph et al. 2013 |
| Upslope IVT → runoff | 61 % of variance in storm-total runoff volume | same | Ralph et al. 2013 |
| Antecedent soil-moisture floor | < 20 % precursor soil moisture ⇒ even heavy rainfall produced no significant streamflow | Russian River | Ralph et al. 2013 |
| AR frequency, OR–WA coast | > 15 % of 6-h analysis times (IVT250), Nov–Apr | vs < 5 % deep interior | Rutz et al. 2014 |
| Detection-variable sensitivity | IVT250 max on OR–WA coast; IWV20 max on N. California coast | same reanalysis, same period | Rutz et al. 2014 |
| AR days, north vs south West Coast | 301 vs 115 | SSM/I, 1997–2005 | Neiman et al. 2008b |
| AR precipitation multiplier | winter ARs produce roughly 2× the precipitation of all storms | near-coast | Neiman et al. 2008b |
| AR contribution to cool-season precip | 20–50 % at most COOP sites in CA/OR/WA | WY1998–2008 | Dettinger et al. 2011 via Rutz et al. 2014 |
| AR contribution, British Columbia | ~90 % of annual extreme precipitation; > 33 % of annual total | BC | Sharma & Déry 2020 via Grgas-Svirac et al. 2026 |
| IVT return period, Washington coast | IVT 1000 kg m⁻¹ s⁻¹ ≈ once per 2 years (Oregon ≈ once per year) | MERRA 1948–2015 | Dettinger et al. 2018 via Ralph et al. 2019 |
| AR width (dropsonde) | 890 ± 270 km | 21 ARs, 304 sondes | Ralph et al. 2017 |
| AR typical dimensions | ~2000 km × ~800 km | general | Ralph et al. 2020 |
| Total IVT across an AR | 4.7 × 10⁸ ± 2 × 10⁸ kg s⁻¹ ≈ 2.6× Amazon discharge | 21 ARs | Ralph et al. 2017 |
| IVT / IWV edge-definition agreement | < 10 % difference in TIVT | 21 ARs | Ralph et al. 2017 |
| Poleward vapour transport in ARs | > 90 % of midlatitude transport in < 10 % of circumference | global | Zhu & Newell 1998 |
| PNW extreme precipitation area width | ~200 km | top-50 2-day events, 6 coastal stations, 60 years | Warner, Mass & Salathé 2012 |
| Cat 5 event characteristics (BBY) | 10 events; mean duration 72 h; mean max 3-h IVT 1118 kg m⁻¹ s⁻¹ | MERRA 1980–2017 | Ralph et al. 2019 |
| Cat 1 event characteristics (BBY) | 268 events; mean duration 21 h; mean max 3-h IVT 480 kg m⁻¹ s⁻¹ | same | Ralph et al. 2019 |
| Category ⇒ major flood (Russian R.) | Cat 5: 3/10 (33 %); Cat 4: 6/22 (30 %); Cat 3: 2/78 (3 %) | ≥12.2 m at Guerneville, 1980–2017 | Ralph et al. 2019 |
| Floods ⇒ AR (Russian R.) | 11/11 major floods AR-associated | 1980–2017 | Ralph et al. 2019 |
| Cat 5 events with major flooding | 6 of 10; 3 of the non-flooding ones struck early season or in drought with dry soils | Bodega Bay / Guerneville | Ralph et al. 2019 Table 5 |
| Cat 5 3-day precipitation | many N. California sites > 150 mm, some 250–300 mm; per-site maxima > 300 mm and some > 500 mm | 10 Cat 5 events | Ralph et al. 2019 |
| Rarity of 400 mm/3 day | only ~4 COOP sites per year nationally | US | Ralph & Dettinger 2012 via Ralph et al. 2019 |
| AR flood damages | 84 % of flood damages in the 11 western states; **> 90 % in California, Oregon and Washington**; > $1 B yr⁻¹ (2019 $), $1.27 B yr⁻¹ (2025 $) | NFIP 1978–2017 | Corringham et al. 2019 via AR Recon BAMS 2025 |
| Damage scaling with category | roughly an order of magnitude per category step | NFIP | Corringham et al. 2019 (press summary; primary not fetched) |
| DVT → runoff probability | P(50 mm/d runoff) 12 % at DVT > 300 → 54 % at DVT > 600 kg m⁻¹ s⁻¹ | Pacific Coast rivers, 5477 gauges, 1949–2015 | Konrad & Dettinger 2017 |
| DVT → extreme runoff | 99th-quantile daily runoff doubles, 80 → 160 mm/d, as DVT goes 300 → 500 | same | Konrad & Dettinger 2017 |
| AR families (5-day aggregation) | 109 families from 228 events; mean 2.7 ARs per family; typically 2–6 | Bodega Bay | Fish, Wilson & Ralph 2019 |
| Dense-cluster precipitation, OR/WA | 120–140 % of sparse-cluster intensity | ERA5, 44 cool seasons | Zhou, Wehner & Collins 2024 |
| Dense-cluster runoff, Cascade Range | 150–300 % more than sparse clusters | same | Zhou, Wehner & Collins 2024 |
| AR cluster runoff share | ~60 % of total runoff along the US coastal region | same | Zhou, Wehner & Collins 2024 |
| Tropical share of AR precipitation, western boundaries | 30–40 % (eastern boundaries 60–70 %) | 40-yr global Lagrangian climatology | Crespo-Otero et al. 2026 |
| Western WA flood composite melting level | ~1.9 km MSL (range 1.5–2.3), vs ~0.95 km MSL climatology | top-10 APDFs, 4 basins, WY1980–2009 | Neiman et al. 2011; Minder 2010 |
| Melting level vs 0 °C isotherm | melting level ≈ 0 °C altitude − 200–400 m (300 m used) | observational basis | Stewart et al. 1984; White et al. 2002 via Neiman et al. 2011 |
| Western WA flood composite warmth | 925-hPa temperature 4–6 °C above normal | same | Neiman et al. 2011 |
| Western WA flood composite IVT | composite core 450–600; individual cases ~500–1300 kg m⁻¹ s⁻¹ | same | Neiman et al. 2011 |
| Western WA flood 2-day precipitation | 85–150 mm (Cascades); 100–175 mm (Olympics) | NARR composites | Neiman et al. 2011 |
| AR ⇒ annual peak flow, western WA | 46 of 48 annual peak daily flows | 4 basins, WY1998–2009 | Neiman et al. 2011 |
| AR ⇒ all floods, western WA | every peak daily flow above a 5-year return period | 4 basins, WY1980–2009 | Neiman et al. 2011 |
| Green River wind-direction window | 245°–275° only | terrain-unobstructed onshore flow | Neiman et al. 2011 |
| Low-elevation tributary share below dams | can exceed 50 % of total flow, beyond dam management | western WA, USACE Seattle RCC | Neiman et al. 2011 |
| Peak-flow seasonality (computed 2026-08-24) | Oct–Mar 86–95 % of annual peaks; Nov–Jan 63–70 % | USGS annual peak record, 4 WA gauges | USGS NWIS peak service |
| Secondary-cyclogenesis predictability | skilful only < 36 h lead; IVT/large-scale skill lost by 96 h | extreme AR, N. California | Martin et al. 2019 |
| Latent heating removed (MFW cases) | AR duration −6 h / −24 h; peak IVT −17 % / −42 %; precipitation −64 % / −49 % | MPAS-A, Russian River | Michaelis et al. 2021 |
| MFW duration effect, PNW | AR conditions prolonged to ≥ 34 h; mapped maximum 28–30 h over the heaviest precipitation | March 2005, NW Oregon | Ralph et al. 2011 |
| AR forecast skill saturation | ~7–10 days; +15–20 % at 7-day lead in boreal winter vs summer (NH oceans) | ECMWF S2S hindcasts | DeFlorio et al. 2018 |
| Landfall-location bias | northward landfall errors favoured in California, Oregon and Washington; occurrence skill ≈ climatology at 14 days | 9 operational models, Nov–Feb reforecasts | Nardi et al. 2018 |
| Ensemble spread structure | highest IVT standard deviation on the **poleward** side of the AR core | GEFS and IFS, Jan 2023 case | AR Recon BAMS 2025 |
| AR Recon forecast impact | strongest QPF and IVT benefit in the first 3 days over coastal states; some benefit days 4–6; sequential flights better | multi-study synthesis | AR Recon BAMS 2025 |
| Airborne radio occultation impact | +3 % precipitation forecast improvement for a **Washington State** AR event, beyond conventional + dropsonde data | preliminary | Do et al. 2025 via AR Recon BAMS 2025 |
| AR Recon 2024–25 campaign | 52 flights, > 1400 dropsondes | one season | Scripps news release |
| IVT vs precipitation forecast product | EFI for IVT more skilful than EFI for precipitation at days 7–9 in locating observed heavy totals | Storm Dennis | Ralph et al. 2020 |
| End-of-century AR change | IWV and IVT increase, lower-tropospheric winds change little; west-coast winter mean precipitation +11–18 %; precipitation on extreme-IVT days +15–39 %; days above historical 99th-percentile IVT up to +290 % | CMIP5 RCP8.5, 10 models | Warner, Mass & Salathé 2015 |
| AR share of future precipitation | AR contribution to total precipitation up ~15 % in the Pacific Northwest (~20 % coastal California) | LOCA-downscaled "Real-5" ensemble | Gershunov et al. 2019 |
| Chehalis basin (WA) projection | heavy (90–99th) and extreme (>99th) precipitation day frequency increases, and the increase is due to ARs | same | Gershunov et al. 2019 |

---

## 4. What is settled, what is emerging, what is contested

### Settled (established)

1. **ARs cause essentially all western Washington floods.** 46/48 annual peak daily flows; all
   >5-year peak daily flows over 30 years (Neiman et al. 2011). Corroborated regionally by
   ~80–100 % AR-generated annual peaks in the PNW (Barth et al. 2017, prior pass) and by damage
   attribution (>90 % of flood damages in CA/OR/WA; Corringham et al. 2019).
2. **IVT, not IWV, is the operational intensity variable**, for reasons of elevation independence,
   precipitation relevance and forecast skill.
3. **Duration is co-equal with intensity** in setting hydrologic outcome. This is why it is half of
   the AR scale, and the runoff scalings (6×/7×) are large.
4. **Storm-total upslope IVT is the best single scalar predictor of storm-total rainfall and runoff**
   available from the atmospheric side (74 % / 61 % variance explained).
5. **The AR scale is a storm scale, not a flood scale**, by the authors' own statement of its limits
   and by the Russian River statistics (33 % of Cat 5 and 30 % of Cat 4 events produced major flooding).
6. **AR frequency and duration peak on the Oregon–Washington coast** under an IVT-based definition.
7. **Detection method is a first-order uncertainty** in any AR climatology (ARTMIP).
8. **Warm, high-melting-level conditions are intrinsic to western Washington flood ARs** (~1.9 km MSL
   composite melting level; 925 hPa +4–6 °C).

### Emerging

1. **Temporal compounding as a quantified hazard class.** AR families were named in 2019; cluster
   *density* (not count) as the discriminating variable, and the Cascade-Range 150–300 % runoff
   amplification, date from 2024. The regional dependence of the correct aggregation window is
   recognised but not tabulated per basin.
2. **Antecedent-moisture-modified AR scale.** The SSPI promotion/demotion recipe (Webb et al. 2026,
   established in the prior pass) is publication-backed, one year old, and explicitly weaker in cooler,
   snow-influenced catchments.
3. **Mesoscale frontal waves as a routine operational target.** AR Recon now designs flights around
   them; the quantitative latent-heating experiments date from 2021 and the predictability limits from
   2019. A Washington-specific quantification does exist but is grey literature: Riedl (2022, Portland
   State MS thesis, `doi:10.15760/etd.4038`) built a 1999–2019 catalogue of MFWs on U.S. West Coast
   landfalling ARs and applied it to the Upper Green River Watershed, WA — of 56 extreme-precipitation
   ARs, the 26 with an MFW had +34.1 mm total-event precipitation, +25.7 h duration, +138 kg m⁻¹ s⁻¹
   maximum IVT and +0.9 AR-scale category versus the 30 without, with **no** difference in maximum
   daily-accumulated precipitation. Not peer-reviewed; not re-derived here.
4. **Moisture-source attribution converging.** The 30–40 % tropical share on western boundaries
   (Crespo-Otero et al. 2026) is presented as reconciling previously divergent Eulerian and Lagrangian
   estimates; it is four months old.
5. **AR forecast improvement from targeted observations.** The AR Recon synthesis (2025) reports
   consistent benefit in days 1–3, contrasting with earlier neutral results from generic winter storm
   reconnaissance.

### Contested

1. **Are western-Washington flood events short or long?** Warner, Mass & Salathé 2012 find most
   regional flooding events are associated with precipitation periods of **24 h or less**, and that
   2-day totals capture nearly all major events. Jennings & Jones 2015 (prior pass) find the largest
   western-Cascades floods are produced by **sustained, moderate-intensity** rain (2.7 ± 0.9 mm h⁻¹),
   i.e. duration-driven. These are not necessarily inconsistent — different basins (small coastal vs
   western Cascades), different response times, different metrics (precipitation window vs intensity)
   — but they support opposite design choices for a forcing surface. **Unresolved for Cascadia
   Papsukkal's specific basins.**
2. **Does the AR scale add information over IVT alone for flood purposes?** The promotion/demotion
   mechanic means a Cat 4 may have max IVT below 1000 kg m⁻¹ s⁻¹; the category therefore mixes two
   physically distinct quantities into one ordinal. Ralph et al. 2019 defend this as capturing what
   drives outcomes; Webb et al. 2026 show the category alone flags only 63 % of flood-generating ARs
   in California. No published verification exists for Washington.
3. **Whether AR frequency at Washington's latitude increases or decreases under warming.** Warner et
   al. 2015 project large increases in extreme-IVT day frequency (up to +290 %); the seasonal-mean
   picture is complicated by a poleward-shifting storm track and a more anticyclonic north-east
   Pacific (Gershunov et al. 2019). The *intensity* signal is robust; the *frequency at a fixed
   latitude* signal is not.
4. **Whether the intensification is thermodynamic only.** Warner et al. 2015 find IWV and IVT increase
   while lower-tropospheric winds change little. Since orographic forcing is wind × moisture, a
   moisture-only intensification changes the upslope flux sub-linearly relative to a wind-plus-moisture
   one. Not all studies agree that winds are unchanged (not independently checked here).
5. **Corringham's per-category damage scaling.** The order-of-magnitude-per-category figure comes from
   press summaries of a paywalled paper; the 84 %/>90 % damage shares are confirmed by a second
   peer-reviewed source (AR Recon BAMS 2025). Treat the scaling as INFERENCE until the primary is read.

---

## 5. Western Washington specificity — what transfers and what does not

### 5.1 Orientation: the finding that is genuinely local and genuinely quantitative

Neiman et al. 2011 composited the meteorology of the top-10 annual peak daily flows in four
unregulated western-Washington basins (WY1980–2009). The composites for the four basins are *not* the
same storm (FACT):

| Basin | Location | Optimal low-level flow | Hypsometry | Note |
|---|---|---|---|---|
| Queets | west flank, Olympics | west–south-westerly (near due west in the low-level composite) | only ~20 % above 750 m MSL | most consistent year-to-year peaks (factor 3.5) |
| Satsop | south flank, Olympics | south–south-westerly / south-westerly | ~75 % below 250 m MSL | partly sheltered by the Olympics |
| **Sauk** | north Cascades (Skagit basin) | **south-westerly only** | ~60 % above 1 km; two-thirds between ~0.7 and 1.8 km | rain-shadowed by the Olympics **and** Vancouver Island for every onshore direction except SW |
| Green | central Cascades | **245°–275° only** — the most restrictive window studied | two-thirds between 0.7 and 1.3 km; three-quarters below 1.2 km | shadowed by the Olympics and Mt Rainier; peak flows vary by an order of magnitude year to year |

A one-sided Student's *t* test separates the Green–Queets low-level wind directions from the
Sauk–Satsop ones at >95 % confidence (FACT). Composite AR orientation was **near-zonal** for the
Green and Queets flood cases and **south-west-to-north-east** for the Sauk and Satsop (FACT).

**But orientation is not sufficient, and the paper says so with a number.** *Within* each
same-orientation pair the top-10 lists share only three dates or consecutive days — Green∩Queets =
{7 Jan 2009, 6–7 Nov 2006, 23–24 Nov 1986}, Sauk∩Satsop = {24 Nov 1990, 29 Nov 1995, 18 Dec 1979}
(verified against Neiman et al. 2011 Table 2, 2026-08-24). Neiman et al. draw the opposite of a
separation conclusion from this: two basins that share an optimal wind direction still flood on
different dates, which "suggest[s] that the other factors listed above can also be important" — i.e.
strength, stationarity, melting level and antecedent soil moisture. Cross-pair overlap is *not*
smaller (Queets∩Satsop = 4 dates), so this statistic must not be cited as evidence that the pairs
are hydrologically distinct. It is evidence that orientation alone under-determines which basin
floods (FACT).

The Green's own history makes the point twice over: its peak flows vary by an order of magnitude
between years, which Neiman et al. attribute to the narrowness of its wind-direction window, and its
top-10 flood composites have the **weakest** vapour fluxes and **coldest** θₑ of the four basins —
i.e. **flooding on the Green is more sensitive to flow orientation than to the magnitude of the
incoming vapour flux** (FACT).

**This is the single most transferable result in this corpus entry to the platform's design**, and it
is the one thing about western Washington that does *not* transfer from California.

### 5.2 What transfers from California and the wider West

| Result | Transferability |
|---|---|
| IVT definition, AR scale mechanics, detection-method uncertainty | Fully — these are definitional, not regional |
| Duration → runoff scalings (6× / 7×) | **Directionally yes, numerically unverified here.** The Russian River is a 1,485 km² coastal basin with a Mediterranean regime and a strong antecedent-moisture switch; western Washington basins are wetter, steeper, snow-influenced and partly regulated |
| Precursor soil moisture < 20 % ⇒ no significant streamflow | **Weakly.** In a maritime regime the basins are above any such floor for most of the flood season (see prior pass §3). The threshold is likely reached by default from ~November to ~March, so its discriminating power is concentrated in October and March |
| AR scale ⇒ major flood rates (33 % / 30 % / 3 %) | **Not directly.** Basin, threshold definition and antecedent regime all differ. No equivalent published statistic exists for Washington |
| Upslope-IVT variance explained (74 % / 61 %) | **Likely higher here, not lower** (INFERENCE): western Washington orography is steeper and wetter, and the same upslope physics is the documented control (Neiman et al. 2011) |
| Mesoscale frontal wave effects | **Yes and specifically documented here** — the March 2005 PNW case is one of the founding studies |
| AR families / cluster density | **Yes, with the strongest regional amplification in the record**: 150–300 % more dense-cluster runoff over the Cascade Range |
| Landfall-latitude ENSO shifts | Yes, but as seasonal context only (prior pass §5.2) |
| Damage share by AR | **Directly measured for Washington**: > 90 % of flood damages in CA/OR/WA |

### 5.3 Season, computed from primary data

Computed 2026-08-24 from the USGS annual peak-flow record (`nwis.waterdata.usgs.gov/nwis/peak`) —
this is an original computation, not a citation (FACT):

| Gauge | Record | n peaks | Oct–Mar | Nov–Jan | Largest peaks |
|---|---|---|---|---|---|
| Sauk R. near Sauk (12189500) | from 1911 | 98 | 86 % | 64 % | 106,000 cfs 2003-10-21; 98,600 1980-12-26; 86,400 2006-11-06 |
| Skykomish R. near Gold Bar (12134500) | from 1928 | 97 | **95 %** | 70 % | 129,000 cfs 2006-11-06; 102,000 1990-11-24; 95,900 2015-11-17 |
| Snoqualmie R. near Snoqualmie (12144500) | from 1958 | 66 | 94 % | 65 % | 74,300 cfs 1990-11-24; 61,000 1959-11-23; 60,700 2009-01-07 |
| Skagit R. near Mount Vernon (12200500) | from 1906 | 86 | 86 % | 63 % | 180,000 cfs 1906-11; 152,000 1990-11-25; 144,000 1951-02-11 |

Two readings. (a) The flood season is Oct–Mar with a Nov–Jan core, matching `HYDROLOGY.md` §2 and
matching the AR climatology (dense AR clusters peak in November; Ralph et al. 2019 finds Cats 4–5
restricted to October–March at a coastal point). (b) **The dates recur across basins**: 1990-11-24/25
and 2006-11-06/07 appear in the top three at three of the four gauges. Regionally simultaneous
loading, not basin-by-basin independence, is the extreme signature — which is exactly what a wide AR
with an optimally oriented low-level jet does.

### 5.4 Regulation interacts with AR structure

Neiman et al. 2011 record an operational fact that belongs in this platform's regulation doctrine:
downstream of the flood-control reservoirs in western Washington, **low-elevation tributaries can
contribute more than 50 % of total flow, beyond the reach of dam management** (FACT). Because those
tributaries are the *most* rain-exposed part of the basin under a high melting level, a warm AR shifts
flood generation into precisely the area the dams do not control. The USACE Seattle strategy of storing
the peak and then releasing as fast as prudent **to make room for a possible subsequent rain event**
(FACT) is an explicit acknowledgement of AR families in operational practice.

---

## 6. What this means for Cascadia Papsukkal

### 6.1 The gap, stated plainly

`packages/hydrology/src/cascade_hydrology/forcing.py` bands the forcing surface on one number: the
basin-area-weighted mean of the NBM pointwise 50th-percentile QPF over 0–72 h, with `FORCING_BANDS`
edges at 25 / 75 / 150 mm. The module's own docstring is scrupulous about what that number is not.
This corpus entry adds a second thing it is not: **it contains no orientation, no duration, no
melting level and no sequence information** — that is, none of the four non-magnitude terms in the
only published five-term description of what makes a western-Washington AR flood (Neiman et al. 2011).

### 6.2 Doctrine changes

- **D1 (`HYDROLOGY.md` §2).** Replace "IVT and storm orientation (a proxy for orographic
  precipitation)" with the specific quantity the literature actually validates: **storm-total
  terrain-projected (upslope) IVT**, with the 74 % / 61 % variance-explained numbers and the
  citation. State that IVT magnitude alone is *not* the forcing variable.
- **D2 (`HYDROLOGY.md` §2 and §5).** Record that an AR category is **Eulerian at a point on a 0.5°
  grid**, that promotion by duration means a Cat 4 may never have reached 1000 kg m⁻¹ s⁻¹, and that
  the scale is explicitly **not location-linked** — so a category can never be rendered as a basin
  hazard level.
- **D3 (`HYDROLOGY.md` §12, Event Zero).** The current text reads "a CW3E AR-4 (coastal WA) / AR-3
  (Cascade foothills) event with ~96 h of AR conditions". Under the scale's own definition an AR event
  is one *continuous* period of AR conditions at a point; three ARs across Dec 3–11 2025 are an **AR
  family**, and 96 h across the family is not a single event's duration. Restate Event Zero as a
  family, with per-AR categories and the inter-event gaps recorded, and cite Fish et al. 2019 for the
  concept. This is a correctness fix, not a stylistic one.
- **D4 (`DATA_DOCTRINE.md` §2).** Add an explicit rule: **AR presence and AR category are DERIVED
  quantities whose `method_version` must encode the detector parameters** (variable, threshold, grid,
  geometry test, temporal continuity, promotion rule). ARTMIP is the justification. Two sources
  disagreeing about AR presence is information, never a fault.
- **D5 (`HYDROLOGY.md` §6).** Extend the model-agreement doctrine: ensemble disagreement about ARs is
  **structured, not isotropic** — spread is largest on the poleward flank of the AR core, and
  operational models favour **northward** landfall-location errors on this coast. An agreement metric
  computed only on crest magnitude and timing misses the dominant error mode, which is a latitudinal
  displacement of the loading.
- **D6 (`HYDROLOGY.md` §7).** The repo's snow-level ASSUMPTION (freezing level − ~1000 ft ≈ 305 m)
  now has a peer-reviewed anchor from this region: Neiman et al. 2011 compute melting level as the
  0 °C altitude minus 300 m, citing observations that the melting level sits 200–400 m below the
  0 °C isotherm. Add the citation and the 200–400 m range; keep it a parameter.
- **D7 (`HYDROLOGY.md` §13).** Add to "what Cascadia Papsukkal will not claim": *an AR category
  sourced from imagery*. CW3E's AR scale products are image-only and research-use-only (confirmed
  again 2026-08-24: the `/arscale/` page exposes no data endpoint). A category read off a picture has
  no `valid_time`, no `issued_at`, no model identity and no unit, and cannot satisfy §1.

### 6.3 Methods and features to build

Ordered by evidence strength per unit of engineering.

| # | Feature | Definition | Why | Priority |
|---|---|---|---|---|
| M1 | `ivt_magnitude`, `ivt_direction` | IVT from GFS/GEFS pressure-level SPFH/UGRD/VGRD, 1000→200 hPa, per basin's coastal reference point and basin mean | the atmospheric intensity variable the whole field uses; the repo already established GFS `pgrb2` carries the needed fields and that `pgrb2a` does not carry SPFH | **P0** |
| M2 | `upslope_ivt` | IVT projected onto the basin's terrain gradient (or onto a per-basin unit vector derived from the DEM), instantaneous and **time-integrated over the event** | 74 % of rainfall variance, 61 % of runoff variance — the strongest published atmospheric predictor of runoff | **P0** |
| M3 | `ar_duration_h` | hours of continuous IVT ≥ 250 kg m⁻¹ s⁻¹ at the basin's reference point, forecast and observed-analysis | co-equal with intensity; 2× duration ⇒ ~6× peak flow | **P0** |
| M4 | `orientation_favourability` | angular distance between forecast low-level (≈900–950 hPa or 1 km MSL) wind direction and a per-basin CONFIGURED optimal window | the only western-WA-specific, statistically significant flood discriminator in the literature | **P0** |
| M5 | `ar_category` | Ralph et al. 2019 scale computed by Cascadia Papsukkal from M1 and M3, badged DERIVED/EXPERIMENTAL, with detector parameters in `method_version` | lets the platform show a category with provenance instead of ingesting an image | P1 |
| M6 | `ar_sequence` | family identification with an explicit `aggregation_period_d` parameter (default 5 d per Fish et al. 2019) and an inter-event `recovery_gap_h` | dense clusters produce 150–300 % more Cascade runoff; Event Zero was a family | P1 |
| M7 | `melting_level_m` | 0 °C isotherm height minus a parameterised 200–400 m offset, plus the derived rain-exposed basin fraction (already planned in Phase 3) | the western-WA flood composite is a ~1.9 km melting level against a ~0.95 km climatology — this is a *percentile-against-climatology* feature, not an absolute one | P1 |
| M8 | `landfall_latitude_spread` | ensemble spread of the latitude of maximum coastal IVT | the dominant error mode; models are biased northward here | P2 |
| M9 | `duration_above_rate` | hours of basin QPF above a moderate rate, and basin fraction simultaneously above it | carries the western-Cascades "long and moderate" signature better than a 72-h total (prior pass §2.4); also the honest way to reconcile the Warner-vs-Jennings contest in §4 | P2 |

### 6.4 Data sources

| Source | Status | Note |
|---|---|---|
| GFS / GEFS `pgrb2b` pressure levels (SPFH, UGRD, VGRD) | available, AWS Open Data | the only free path to computed IVT; `pgrb2a` lacks SPFH (repo research file, 2026-08-22) |
| CW3E AR scale / IVT tools | **image only**, research-use-only, no API | re-confirmed 2026-08-24; the `/arscale/` page exposes no `.nc`/`.json`/`.csv` endpoint. **Do not ingest.** |
| NOAA PSL AR portal | image only | same |
| CW3E AR Recon dropsonde archive (`cw3e.ucsd.edu/arrecon_data/`) | exists | research value for Event-Zero-class reanalysis, not operational |
| ARTMIP Tier 1 catalogues (NCAR Climate Data Gateway, doi 10.5065/D6R78D1M) | available | the honest way to quantify detector uncertainty on historical events |
| ERA5 vertical integrals of eastward/northward water-vapour flux | **unverified** | if present, this is the cheapest hindcast IVT for Event Zero replay. OPEN QUESTION §8 |
| ECMWF open data (IFS/AIFS 0.25°) | **unverified** whether `viwve`/`viwvn` are in the open stream | fetch attempt returned a redirect, not read. OPEN QUESTION §8 |

### 6.5 Contract implications

- `Driver` entries for the forcing surface must be able to carry an **angular** quantity (wind
  direction, orientation offset) and a **duration** quantity, not only scalars with bands. The current
  `BandTable` shape assumes a scalar with monotone bands; orientation favourability is periodic and
  peaks in an interval.
- Any AR category rendered anywhere needs three extra provenance fields beyond the standard record:
  the **reference point** (lat/lon), the **grid resolution**, and the **model run** it was computed
  from. Without those, "AR 4" is not a value under `DATA_DOCTRINE.md` §1.
- An `ar_sequence` assessment needs a stable identity across model cycles so forecast evolution of a
  *family* (not just of a crest) is queryable.

---

## 7. What this domain contradicts or qualifies in the current repo doctrine

1. **`HYDROLOGY.md` §1 — "forcing determines how much water enters; state determines how the basin
   reacts."** *Qualified.* Neiman et al. 2011's five flood attributes put three terms —
   orientation, stationarity and melting level — on the *forcing* side, none of which is a "how much"
   quantity. The clean forcing/state split hides the fact that most of the forcing-side information is
   geometric and temporal, not volumetric.
2. **`HYDROLOGY.md` §2 — the AR scale description.** *Incomplete.* It states magnitude and duration
   but omits the promotion/demotion mechanic, the Eulerian point definition, the 0.5° grid, and the
   authors' explicit statement that the scale is not location-linked. As written, the doctrine would
   permit rendering a category as a basin hazard, which the source forbids.
3. **`HYDROLOGY.md` §2 — "IVT and storm orientation (a proxy for orographic precipitation)."**
   *Understated and unimplemented.* The validated quantity is upslope IVT integrated over the event,
   and `forcing.py` contains no IVT at all. The doctrine currently promises something the code does
   not attempt.
4. **`HYDROLOGY.md` §4 — forcing feature table lists "IVT magnitude, direction, duration; AR scale"
   with sources "GFS/GEFS (derived), CW3E products."** *Half wrong.* CW3E publishes no machine-readable
   product; "CW3E products" must be struck from the source column and replaced with "Cascadia-derived
   from GFS/GEFS (or ECMWF open data if verified)".
5. **`HYDROLOGY.md` §12 — Event Zero as "a CW3E AR-4 / AR-3 event with ~96 h of AR conditions."**
   *Category error.* Three ARs over Dec 3–11 2025 constitute an AR family; 96 h is the family span,
   not an event duration, and the AR scale cannot be applied to it as a single event. The categories
   themselves came from CW3E imagery and therefore fail §1 provenance unless recorded as
   CONFIGURED-from-narrative.
6. **`HYDROLOGY.md` §6 — "Disagreement between NWPS, NWM configurations, ensemble spread ... computed
   from crest magnitude, crest timing, and category differences."** *Incomplete.* The dominant
   upstream error is a **latitudinal displacement of AR landfall**, with a documented **northward
   bias** in Washington. A downstream agreement metric on crest magnitude will register this as
   ordinary spread rather than as a directional bias.
7. **`forcing.py` `FORCING_BANDS` (25 / 75 / 150 mm per 72 h).** *Wrong shape, not just uncalibrated.*
   Two ARs with identical basin 72-h QPF and different orientation, duration and melting level have
   documented flood responses differing by nearly an order of magnitude. A single scalar banded four
   ways cannot express that, and the module's `score_cap` (200 mm) makes the top band saturate exactly
   where the discriminating information lives.
8. **`HYDROLOGY.md` §7 — snow-level assumption.** *Supported, and now citable.* Neiman et al. 2011's
   melting-level construction (0 °C altitude − 300 m, from a 200–400 m observational range) is
   independent confirmation of the repo's ~1000 ft working offset, and adds a regional climatological
   anchor (~0.95 km MSL at Quillayute) that the repo currently lacks.
9. **`HYDROLOGY.md` §2 — regulation.** *Extended.* Neiman et al. 2011 records that low-elevation
   tributaries below western-Washington flood-control dams can contribute more than half the total
   flow. That belongs in §2's regulation paragraph, because it bounds what a `regulation_class` of
   "regulated" can mean during a warm AR.

---

## 8. Open questions

1. **Is there any published AR-category-to-flood verification for Washington?** I found none. The only
   category-to-flood mapping in the literature is the Russian River (33 % of Cat 5, 30 % of Cat 4, 3 %
   of Cat 3 producing major flooding). Building the Washington equivalent from the platform's own
   history — AR category at a coastal reference point versus NWS category exceedance at Mount Vernon,
   Concrete, Gold Bar, Carnation, Snohomish, Ferndale — is a bounded, high-value hindcast experiment
   and would be a genuine contribution.
2. **Do the Ralph et al. 2013 duration→runoff scalings (≈6× peak, >7× volume for 2× duration) hold in
   Cascade basins?** Testable against the platform's own record once M1–M3 exist.
3. **Where should the Eulerian reference point be for each Washington basin?** The scale is defined at
   a point; the natural candidates are the coastal landfall point upstream of the basin's optimal wind
   window, not the basin centroid. Unresolved, and it changes every category the platform would compute.
4. **What is the per-basin optimal onshore wind-direction window?** Neiman et al. 2011 gives Green
   (245°–275°), Sauk (SW quadrant), Queets (WSW) and Satsop (SSW/SW) from ten cases each. **Nooksack,
   Skykomish, Snoqualmie, Stillaguamish, White and Cedar have no published window.** Deriving them
   from the platform's own record is P1 work.
5. **What fraction of flooding ARs in western Washington involve a mesoscale frontal wave?** In the
   peer-reviewed literature, only case studies (March 2005; CalWater-2014 for California). One grey-
   literature catalogue does exist — Riedl 2022 (Portland State MS thesis, `doi:10.15760/etd.4038`),
   1999–2019 MFWs on West Coast landfalling ARs, applied to the Upper Green River Watershed, WA:
   26 of 56 extreme-precipitation ARs there carried an MFW. That ~46 % is the only western-Washington
   number available and is unverified by this pass. A peer-reviewed climatology is still missing.
6. **Does the Webb et al. 2026 SSPI-modified AR scale help at all in a maritime always-wet regime?**
   The paper itself reports that the small set of catchments showing no improvement were the cooler
   ones. Western Washington is a candidate null result, and a null result is worth publishing in the
   repo (prior pass §3 raised the same question from the antecedent-moisture side).
7. **Does ERA5 publish vertical integrals of eastward/northward water-vapour flux, and does ECMWF's
   open data stream carry them?** If yes, hindcast IVT for Event Zero is nearly free. Both fetches
   failed in this pass.
8. **Can the Warner 2012 (≤24 h) and Jennings & Jones 2015 (long, moderate) descriptions of PNW flood
   precipitation be reconciled by basin scale and response time?** This determines whether M9
   (`duration_above_rate`) or a short-window peak metric is the right second forcing feature.
9. **How does the documented northward landfall bias (Nardi et al. 2018) interact with Washington's
   position at the northern end of the well-sampled domain?** If forecasts systematically place
   landfall too far north, Washington basins may be systematically over-forecast and southern
   Washington / Oregon under-forecast — but Nardi's domain includes British Columbia, where skill is
   lower, so the sign at 48–49 °N is not established. INFERENCE, needs verification against the
   platform's own forecast archive.
10. **Is the AR intensification thermodynamic only?** Warner et al. 2015 report little change in
    lower-tropospheric winds. Since upslope forcing is wind × moisture, this materially changes how
    orographic precipitation scales with warming. Not independently checked against later literature.

---

## 9. Sources

Fetched and read in this pass:

- [Ralph et al. 2019 — A Scale to Characterize the Strength and Impacts of Atmospheric Rivers, *BAMS* 100(2), 269–289](https://journals.ametsoc.org/view/journals/bams/100/2/bams-d-18-0023.1.xml)
- [Neiman, Schick, Ralph, Abel & Wick 2011 — Flooding in Western Washington: The Connection to Atmospheric Rivers, *J. Hydrometeor.* 12(6)](https://journals.ametsoc.org/view/journals/hydr/12/6/2011jhm1358_1.xml)
- [Ralph, Coleman, Neiman, Zamora & Dettinger 2013 — Observed Impacts of Duration and Seasonality of Atmospheric-River Landfalls on Soil Moisture and Runoff in Coastal Northern California, *J. Hydrometeor.* 14(2)](https://journals.ametsoc.org/view/journals/hydr/14/2/jhm-d-12-076_1.xml)
- [Rutz, Steenburgh & Ralph 2014 — Climatological Characteristics of Atmospheric Rivers and Their Inland Penetration over the Western United States, *MWR* 142](https://cw3e.ucsd.edu/wp-content/uploads/2014/05/Rutz_etal_2014_MWR.pdf)
- [Neiman, Ralph, Wick, Lundquist & Dettinger 2008 — Meteorological Characteristics and Overland Precipitation Impacts of Atmospheric Rivers Affecting the West Coast of North America, *J. Hydrometeor.* 9(1)](https://journals.ametsoc.org/view/journals/hydr/9/1/2007jhm855_1.xml)
- [Ralph, Neiman, Kiladis, Weickmann & Reynolds 2011 — A Multiscale Observational Case Study of a Pacific Atmospheric River Exhibiting Tropical–Extratropical Connections and a Mesoscale Frontal Wave, *MWR* 139(4)](https://journals.ametsoc.org/view/journals/mwre/139/4/2010mwr3596.1.xml)
- [Martin, Ralph, Wilson, DeHaan & Kawzenuk 2019 — Rapid Cyclogenesis from a Mesoscale Frontal Wave on an Atmospheric River, *J. Hydrometeor.* 20(9)](https://journals.ametsoc.org/jhm/article/20/9/1779/344247/Rapid-Cyclogenesis-from-a-Mesoscale-Frontal-Wave)
- [Michaelis, Martin, Fish, Hecht & Ralph 2021 — Modulation of Atmospheric Rivers by Mesoscale Frontal Waves and Latent Heating, *MWR* 149(8)](https://journals.ametsoc.org/view/journals/mwre/149/8/MWR-D-20-0364.1.xml)
- [Fish, Wilson & Ralph 2019 — Atmospheric River Families: Definition and Associated Synoptic Conditions, *J. Hydrometeor.* 20(10)](https://journals.ametsoc.org/view/journals/hydr/20/10/jhm-d-18-0217_1.xml)
- [Zhou, Wehner & Collins 2024 — Back-to-back high category atmospheric river landfalls occur more often on the west coast of the United States, *Commun. Earth Environ.* 5](https://www.nature.com/articles/s43247-024-01368-w)
- [Zhang et al. 2024 — Seasonality and climate modes influence the temporal clustering of unique atmospheric rivers in the Western U.S., *Commun. Earth Environ.*](https://www.nature.com/articles/s43247-024-01890-x)
- [Warner, Mass & Salathé 2012 — Wintertime Extreme Precipitation Events along the Pacific Northwest Coast: Climatology and Synoptic Evolution, *MWR* 140(7)](https://journals.ametsoc.org/view/journals/mwre/140/7/mwr-d-11-00197.1.xml)
- [Warner, Mass & Salathé 2015 — Changes in Winter Atmospheric Rivers along the North American West Coast in CMIP5 Climate Models, *J. Hydrometeor.* 16(1)](https://journals.ametsoc.org/view/journals/hydr/16/1/jhm-d-14-0080_1.xml)
- [Gershunov et al. 2019 — Precipitation regime change in Western North America: The role of Atmospheric Rivers, *Sci. Rep.* 9](https://www.nature.com/articles/s41598-019-46169-w)
- [Zheng et al. 2025 — Atmospheric River Reconnaissance: Mission Planning, Execution, and Incorporation of Operational and Science Objectives, *BAMS* 106(11)](https://journals.ametsoc.org/view/journals/bams/106/11/BAMS-D-24-0160.1.xml)
- [Ralph, Cordeira, Neiman et al. 2020 — Improved forecasts of atmospheric rivers through systematic reconnaissance, better modelling, and insights on conversion of rain to flooding, *Commun. Earth Environ.* 1](https://www.nature.com/articles/s43247-020-00042-1)
- [Shields et al. 2018 — Atmospheric River Tracking Method Intercomparison Project (ARTMIP): project goals and experimental design, *GMD* 11](https://gmd.copernicus.org/articles/11/2455/2018/)
- [CW3E publication notice for Rutz et al. 2019 — ARTMIP: Quantifying Uncertainties in Atmospheric River Climatology, *JGR-Atmos.* 124](https://cw3e.ucsd.edu/cw3e-publication-notice-the-atmospheric-river-tracking-method-intercomparison-project-artmip-quantifying-uncertainties-in-atmospheric-river-climatology/)
- [Sodemann & Stohl 2013 — Moisture Origin and Meridional Transport in Atmospheric Rivers and Their Association with Multiple Cyclones, *MWR* 141(8)](https://journals.ametsoc.org/view/journals/mwre/141/8/mwr-d-12-00256.1.xml)
- [Crespo-Otero, Insua-Costa, Deman, Hernández-García, López & Míguez-Macho 2026 — Global asymmetries in the moisture origins of atmospheric river precipitation, *npj Clim. Atmos. Sci.*](https://www.nature.com/articles/s41612-026-01408-6)
- [Grgas-Svirac, Fereshtehpour, Najafi, Cannon & Shirkhani 2026 — Atmospheric Rivers as Triggers of Compound Flooding, *NHESS* 26, 901–923](https://nhess.copernicus.org/articles/26/901/2026/)
- [CW3E AR Scale product page (checked for a data endpoint; none found)](https://cw3e.ucsd.edu/arscale/)
- USGS annual peak-flow service, sites 12189500 / 12134500 / 12144500 / 12200500 — `https://nwis.waterdata.usgs.gov/nwis/peak` (computed 2026-08-24)
- USGS site service for station names — `https://waterservices.usgs.gov/nwis/site/`

Read via abstract, secondary citation, or press summary only — **not independently fetched in full**:

- Ralph et al. 2017, *Dropsonde Observations of Total Integrated Water Vapor Transport within North Pacific Atmospheric Rivers*, *J. Hydrometeor.* 18 — numbers (890 ± 270 km; 4.7 × 10⁸ kg s⁻¹; <10 %) taken from the publisher abstract and from citations inside fetched papers.
- Nardi, Barnes & Ralph 2018, *Assessment of Numerical Weather Prediction Model Reforecasts of the Occurrence, Intensity, and Location of Atmospheric Rivers*, *MWR* 146(10) — full text blocked; findings taken from the publisher abstract.
- DeFlorio et al. 2018, *Global Assessment of Atmospheric River Prediction Skill*, *J. Hydrometeor.* 19(2) — abstract only.
- Konrad & Dettinger 2017, *Flood Runoff in Relation to Water Vapor Transport by Atmospheric Rivers over the Western United States, 1949–2015*, *GRL* 44 — publisher blocked; the 12 %→54 % and 80→160 mm/d numbers are from the publisher abstract.
- Corringham, Ralph, Gershunov, Cayan & Talbot 2019, *Atmospheric rivers drive flood damages in the western United States*, *Sci. Adv.* 5 — Cloudflare-blocked; the 84 % / >90 % / $1 B figures are corroborated in the fetched AR Recon BAMS 2025 paper; the order-of-magnitude-per-category scaling is from a press summary only.
- Bowers, Serafin, Tseng & Baker 2023, *Atmospheric River Sequences as Indicators of Hydrologic Hazard*, *Earth's Future* 11 — publisher and NOAA repository both blocked; the >3× loss figure is quoted from Zhang et al. 2024.
- O'Brien et al. 2020, *Detection of atmospheric rivers with inline uncertainty quantification: TECA-BARD v1.0.1*, *GMD* 13 — abstract only.
- Dettinger et al. 2018 (IVT return periods), Lavers et al. 2016 (IVT vs precipitation skill), Zhu & Newell 1998, Minder 2010, Stewart et al. 1984, White et al. 2002, Guan et al. 2010, Dettinger et al. 2011, Sharma & Déry 2020, Ralph & Dettinger 2012 — cited **inside** fetched papers, not fetched themselves.
- Webb et al. 2025, 2026; Barth et al. 2017; Jennings & Jones 2015 — fetched in the prior solo pass and recorded in [`docs/research/flood-genesis-mechanisms-2026-08-24.md`](../flood-genesis-mechanisms-2026-08-24.md); not re-fetched here.
