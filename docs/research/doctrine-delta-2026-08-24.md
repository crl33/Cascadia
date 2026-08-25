# DOCTRINE DELTA for `docs/HYDROLOGY.md` — 2026-08-24

*A reviewable proposal, not an edit. `docs/HYDROLOGY.md` is unchanged. Prepared by the doctrine
editor from the twelve domain corpus files in `docs/research/corpus/` and the prior solo pass
`docs/research/flood-genesis-mechanisms-2026-08-24.md`.*

**Test of relevance applied to every item below:** does it improve a 6–120 h flood prediction for a
named western Washington basin? Items that do not are either dropped or marked
**NON-OPERATIONAL CONTEXT** and kept out of the doctrine text.

**Three categories held apart throughout, and never blurred:**

| | Admissibility |
|---|---|
| **MEASUREMENT** — observed trends in instrument records | Admissible, and preferred. |
| **PHYSICS** — e.g. Clausius–Clapeyron ~7 % K⁻¹ | Admissible as a constraint. Precipitation and flood response are **not required to follow it**; the measured AR record does not (IVT < +1 % over 1980–2023, Henny & Kim 2025). |
| **PROJECTION** — GCM/RCM-driven futures | **Not admissible operationally.** Fenced context only. |

The projection exclusion is the platform's own existing epistemics applied consistently, not a new
editorial rule: a century-scale projection cannot carry an `available_at` knowledge time
(`DATA_DOCTRINE.md` §11), cannot be verified at a 6–120 h lead (§9), and is MODELED at best (§2).

---

## 0. Files and material quarantined

Every corpus file was read in full. The following material was **quarantined** — read, understood,
and deliberately excluded from the doctrine text and from every proposed method. Nothing below may
enter a surface, a threshold, a percentile, a band edge or a hazard computation.

| Corpus file | Quarantined material | Note |
|---|---|---|
| `climate-change.md` | **Appendix P in its entirety** | The file had already self-quarantined its projection material and rebuilt itself around measurement. That fence is adopted wholesale. Everything in §§1–8 of that file — ladder sampling error, centre-of-timing shifts, tide-gauge trends, SNOTEL sensor steps, datum discontinuities — is MEASUREMENT and is carried forward. |
| `snow-hydrology.md` | Musselman et al. 2018 ROS runoff **+20 % to > +100 %** for the Cascades; "top-10 ROS events up to 3 months earlier"; Hao et al. 2025 **+44 % at +5 K** and **+59 % per K above 1,500 m** for the 1996 flood; Maina & Kumar 2025 | **RCP8.5 pseudo-global-warming, single scenario** in Musselman; storyline warming levels in Hao. See §0.1. The *measured* maritime snowmelt fraction (19–45 %) and the ROS outflow ceilings are MEASUREMENT and are carried forward. |
| `atmospheric-rivers.md` | Warner, Mass & Salathé 2015 end-of-century AR change (west-coast winter mean precipitation **+11–18 %**, precipitation on extreme-IVT days **+15–39 %**, days above the historical 99th-percentile IVT **up to +290 %**); Gershunov et al. 2019 AR share of future precipitation; Zhou et al. 2024's projected increase in cluster density | **CMIP5 RCP8.5.** See §0.1. The *observed* AR climatology, the AR scale mechanics, the duration→runoff scalings and the Neiman 2011 orientation result are carried forward. |
| `compound-coastal.md` | Miller et al. 2018 SLR projections (2100 central **2.0 ft**, 1 % exceedance 4.8 ft, 0.1 % 8.3 ft); Hamman et al. 2016 Skagit 2080s **+74 % inundation area**; Spicer et al. 2025's "+0.61 m SLR (AR6 SSP5-8.5, 2100) → flooded area more than doubles" | **RCP8.5 / SSP5-8.5.** See §0.1. The *measured* CO-OPS relative-sea-level trends, the measured skew-surge climatology, the measured tidal transmission coefficients and the TWL decomposition are MEASUREMENT and PHYSICS and are carried forward in full. |
| `orographic-precipitation.md` | Kirshbaum & Smith 2008 ("orographic precipitation becomes less efficient as the atmosphere warms"); Minder et al. 2011's snow-line-depression-increases-with-temperature buffering result | Both are model results about a future climate, stated conditionally by their own authors ("if present in nature"). The *present-day* melting-distance physics from the same paper (Δ_melt 60 m → >300 m) is PHYSICS and is carried forward. |
| `flood-statistics.md` | **NOAA Atlas 15 Volume 2** — future projections built by applying downscaled-climate-model adjustment factors to Volume 1 | Volume 2 is a projection product and is not admissible. **Volume 1** — present-day, trend-aware, observation-based — is admissible when published, with its vintage stated. |
| `regulation-operations.md` | The FIRO rationale "under a declining maritime snowpack that trade gets worse from both ends" | The FIRO *facts* (Lake Mendocino FVA results, Prado, the Howard Hanson PVA target of December 2026, the control fractions, the rule curves) are practice and measurement and are carried forward. The projected-snowpack motivation is fenced. |
| `runoff-generation.md`, `antecedent-conditions.md`, `routing-hydraulics.md`, `forecasting-verification.md`, `cascading-hazards.md` | **Nothing quarantined.** | These five files contain no century-scale projection material of consequence. |

### 0.1 RCP8.5 flag, applied where required

Every quarantined citation above that uses **RCP8.5 or SSP5-8.5 as its only or primary forcing** is
flagged with the [Hausfather & Peters (2020, *Nature* 577, 618–620)](https://www.nature.com/articles/d41586-020-00177-3)
critique: RCP8.5 was constructed as a high-risk exploratory scenario, not a business-as-usual one,
and current policy trajectories fall below it. [Schwalm et al. (2020, *PNAS* 117)](https://www.pnas.org/doi/10.1073/pnas.2007117117)
dissent, arguing RCP8.5 has tracked cumulative emissions well over the historical period. Neither
was independently fetched by the corpus authors; both are recorded as search summaries.

**Lower-scenario results reported alongside, where the same body of work provides them** (all
NON-OPERATIONAL CONTEXT, listed only to satisfy the scenario-discipline requirement):

- The Washington state tables in `climate-change.md` Appendix P are **global-warming-level indexed**
  (1.5 / 2 / 3 / 4 °C), which partially decouples them from scenario. At the **1.5 °C** level:
  state-average annual maximum daily runoff **+10 %** (western WA +11 %) against +24 % at 4 °C;
  2-year storm precipitation **+3 %** against +20 %; April 1 SWE **−21 %** against −67 %.
- Chegwidden et al. 2020 ran **RCP4.5 and RCP8.5**; the reported ranges (precipitation-driven annual
  maxima +29 to +36 %) span the GCM × hydrologic-model matrix across both.
- Musselman et al. 2018, Warner et al. 2015, the UW CIG Snohomish report and the Skagit AR4/A1B work
  provide **no lower scenario**; each is flagged single-scenario and must be read as an upper
  exploratory bound, never a central estimate.

**None of the above may be cited in `HYDROLOGY.md`.** They appear here once, fenced, so that a
reviewer can see that the exclusion was a decision rather than an omission.

---

## 1. Summary table — every existing claim, its verdict, and the action

Claims are identified by the section they appear in and their order within it. Where a claim is
labelled in the source document (FACT / ASSUMPTION / INFERENCE) that label is shown.

**Totals: 29 CONFIRMED · 29 QUALIFIED · 4 SUPERSEDED · 1 REFUTED.**

| # | Existing claim (abridged) | Label | Verdict | Action |
|---|---|---|---|---|
| **1.1** | State vector `S(t)` = soil water per band, groundwater/baseflow, snow per band, channel storage, reservoir storage, frozen ground | — | **QUALIFIED** | Add **channel conveyance state** (bed elevation / rating epoch) and, at delta points, the **coastal boundary condition**. Add that the one component of `S` that is directly measured is discharge itself, via `g(Q)`. §3.1 |
| **1.2** | Forcing vector `F(t)` = precipitation rate and phase per band, T/RH/wind, freezing level, IVT and storm orientation | — | **QUALIFIED** | IVT becomes **terrain-projected (upslope) IVT**; add the blocking parameter `M = Nh/U`, AR duration, wind and dewpoint at pack elevation, and short-duration intensity (I₁₅/I₆₀). §3.1 |
| **1.3** | The question is `P(Q_reach(t+h) > threshold | …)`, `h ∈ {6,12,24,48,72,120}` h | — | **CONFIRMED** | No change. This is the platform's whole test of relevance and the corpus reinforces it. |
| **1.4** | "Forcing determines how much water enters; state determines how the basin reacts" | — | **QUALIFIED, materially, in two opposite directions** | Rewrite. State sets a **measured gain of 7.6–11.1×** on these basins — "reacts" understates a factor of ten. But in the maritime flood season the state term has **small variance** (Washington is the low-responsiveness group, ≈2× not 4.5×), so its *discriminating power* here is smaller than the California-dominated literature implies. And three of the five flood conditions are forcing-side but **geometric and temporal, not volumetric**. §3.1 |
| **1.5** | Extreme western WA floods are forcing-driven; large events nearly always from ARs | FACT | **CONFIRMED, strongly** | Keep, with the numbers attached and one qualification: the AR is a **necessary and poor sufficient** cause. §3.1 |
| **1.6** | Antecedent state modulates the response, sometimes strongly, and never substitutes for the forcing | — | **CONFIRMED and quantified** | Keep, add the measured amplification and the measured counter-examples. §3.1 |
| **1.7** | The channel network "routes it downstream, delayed and attenuated" | — | **QUALIFIED** | Routing has **two signs**: Concrete → Mount Vernon peak change measured **−24.8 % to +27.8 %**, median −6.1 %. Amplification is documented by USACE, not exceptional. §3.1, §3.9 |
| **2.1** | Flood season roughly October–February, peaking November–January | FACT | **CONFIRMED** | Extend to **Oct–Mar** on primary data: 86–95 % of annual peaks Oct–Mar, 63–70 % Nov–Jan across four gauges. §3.2 |
| **2.2** | ARs are corridors of vapour transport; IVT is the standard measure; the AR scale rates 1–5 by magnitude and duration | FACT | **QUALIFIED — incomplete in a way that permits a misuse** | Record that the scale is **Eulerian at a point on a 0.5° grid**, that duration **promotes** a category (so an AR 4 may never have reached 1000 kg m⁻¹ s⁻¹), that an AR event is one *continuous* period of AR conditions, and that the authors state the scale is **not location-linked**. As written the doctrine would permit rendering a category as a basin hazard, which the source forbids. §3.2 |
| **2.3** | Beyond IVT: orientation relative to terrain, duration, temperature | — | **CONFIRMED, and now quantified with published skill** | Upgrade to Neiman's **five conditions** and attach the numbers: upslope IVT (r² = 0.85 warm-sector Olympics; 74 % of storm-total rainfall variance and 61 % of runoff-volume variance at the Russian River), duration (2× mean duration ⇒ ~6× peak streamflow, >7× storm-total runoff volume), melting level (flood composite ~1.9 km MSL against a ~0.95 km in-storm climatology), stationarity, antecedent wetness. §3.2 |
| **2.4** | "Precipitation increases steeply with elevation on windward slopes"; coarse-model basin QPF can be badly wrong | FACT | **QUALIFIED, materially** | The controlling geometry is the **terrain gradient along the flow and ridge-crest position**, not elevation. Washington's wettest recorded station is at 600 ft; Olympic ridge-crest maxima sit on ~800 m ridges. Add **blocking**: `M = Nh/U`, measured means 0.7 (warm sector) / 1.1 (warm frontal) / 2.5 (post-frontal) over the Olympics. §3.2 |
| **2.5** | Basin-aggregated precipitation must come from the highest-resolution product available and carry its own uncertainty | — | **CONFIRMED and strengthened** | The uncertainty is **signed and regime-dependent**, not random. Attach: radar QPE covers only ¼–⅓ of the coastal western US adequately and reads <50 % of gauge values in the heaviest precipitation; gauge undercatch is 5–15 % (lowland), 15–20 % (Cascade gaps), 25–40 % (above 1,500 m); MRMS cells filled by Mountain Mapper are **MODELED, not OBSERVED**. §3.2 |
| **2.6** | Transient snow zone ≈ 1,000–4,000 ft | ASSUMPTION | **SUPERSEDED** | Delete the band as a parameter; keep the derived dynamic fractions. Three independent reasons: the literature calls the concept inadequate ("implies a static area, when in fact the area undergoing melt is highly dynamic"); the observing network does not cover it (median western-WA SNOTEL 3,900 ft, **1 of 31 below 2,000 ft**); and the band is itself time-varying (centre-of-timing shifts of 2.3–4.6 days/decade at the snow-influenced gauges). §3.2 |
| **2.7** | The lower Skagit "crests roughly a day after the upper-basin peaks" | INFERENCE | **SUPERSEDED by measurement** | Median **16.9 h** Concrete → Mount Vernon (sd 3.5 h, range 9.5–23.8 h, n = 12, 2003–2025). Upgrade from INFERENCE to a measured distribution — and state that **response time is dominated by regulation, not basin size**: recession time constant at 1 mm h⁻¹ is 17.5–28.1 h unregulated, 42 h at Mount Vernon, 116 h on the Cedar, 264 h on the Green. §3.2 |
| **2.8** | The regulation table (Skagit / Green / White / Cedar / Snoqualmie / Nooksack) and `regulation_class` | FACT | **QUALIFIED — three factual corrections and three additions** | (a) **Lower Baker has no authorised flood storage**; it is constrained only against drawing down while Upper Baker stores. (b) Chester Morse's flood reduction is **incidental**, with no published rule curve located. (c) Add **control fractions**: Ross + Upper Baker control **39 %** of the drainage area at Mount Vernon (32 % of mean annual runoff); Howard Hanson **55 %** above Auburn; Mud Mountain **42 %** at Puyallup. (d) Add the saturation statement: the Skagit system holds the lower valley below damage only to about the **4–5 % exceedance (20–25-year) event**. (e) Add that **low-elevation tributaries below the dams can contribute more than 50 % of total flow**. §3.2 |
| **2.9** | "The lower [Nooksack] is tidally influenced at Ferndale" | — | **QUALIFIED — true but the wrong gauge is named** | Measured tidal transmission at low flow: Ferndale **0.019 ft/ft** (r = 0.33), Mount Vernon **0.010 ft/ft**, and **Snohomish at Snohomish 0.831 ft/ft (r = 0.94)** — ~83 % tidal, an ~11 ft diurnal swing against a 25 ft flood stage — and the doctrine does not mention it, even though §12 cites SNAW1 as an Event Zero record gauge. §3.2, new §10A |
| **3.1** | Susceptibility input feature table | — | **QUALIFIED** | SNOTEL soil moisture is **absent in four of eight basins and zero in the Sauk**; SMAP L4's own accuracy requirement **excludes mountainous topography, snow and frozen ground**; the NWM v3.0 retrospective `SOIL_M` (1 km, 4 layers, 1979–2023) sits unused on public S3. Add `g(Q)`, recession time constant, storage limb, the percentile's rate of change, and snow-drought state. §3.3 |
| **3.2** | Output is a categorical state plus contributing features; an experimental index, never a probability | — | **QUALIFIED — the resolution is asserted, not demonstrated** | A day-of-year percentile carries a sampling SD of **±5.5–6.2 points at a 30-year ladder** (±12 at 10 years) against band edges of 25/75/90; and the ladder **saturates at p95** across a 2.5× flow range during the December 2025 event. The band must be able to return UNKNOWN near an edge, and the tail must be extended or the saturation declared. §3.3, new §12A |
| **3.3** | "It is not a flood forecast … VERY HIGH susceptibility in a dry forecast and the hazard is LOW" | — | **CONFIRMED** | Keep, and add the converse, which is the dangerous half: **LOW is not an all-clear.** A LOW reading still carries 0.0–0.8 % probability of a top-1 % flow within a week against a 1.0 % base rate, and **24–25 % of annual maxima at unregulated gauges were preceded by a below-25th-percentile state at −7 days**. §3.3 |
| **4.1** | Forcing feature table, including "IVT magnitude, direction, duration; AR scale — GFS/GEFS (derived), CW3E products" | — | **QUALIFIED — one source is factually wrong** | **Strike "CW3E products"**: CW3E's AR-scale products are image-only, research-use-only, with no data endpoint (re-confirmed 2026-08-24). A category read off a picture has no `valid_time`, `issued_at`, model identity or unit. Replace "IVT direction" with **upslope IVT on a per-basin fitted bearing**. Add AR duration hours, orientation favourability, AR family/sequence, `M`, I₁₅/I₆₀, and the **HEFS MEFP basin-average MAP/MAT/SWE ensembles**. §3.4 |
| **4.2** | Output is a categorical forcing level per horizon with spread; forecasts carry `issued_at`/`valid_time` and supersede | — | **QUALIFIED** | The supersession mechanics are correct and unchanged. But a **single basin-mean scalar banded four ways cannot express** two ARs with identical 72-h QPF whose orientation, duration and melting level differ, whose documented flood responses differ by nearly an order of magnitude. §3.4 |
| **5.1** | Hazard ordered by authority; the official forecast is always shown and always labelled OFFICIAL | — | **CONFIRMED and strengthened** | New reason: NWRFC's CHPS chain carries SNOW-17 and SAC-SMA **state vectors per elevation zone, human-adjusted to match observations before each run** — the best antecedent-state-conditioned product in the region, and one the platform cannot reproduce. Two additions: the official forecast is **an observation of an authority's judgement**, not reproducible (forecaster MODs are unlogged); and at a regulated point it is **conditional on an assumed regulation plan**. §3.5 |
| **5.2** | "Official or authoritative probabilities where they exist (HEFS/ESP ensembles, NWM medium-range exceedance fractions)" | — | **QUALIFIED — they exist, and at four of six points they cannot be used** | HEFS is live and machine-readable at all six seed LIDs: **45 members indexed 1981–2025**, 6-hourly to 30 days, one 12Z cycle per day, **`QINE` (flow) only**. It is **MODELED, not OFFICIAL_FORECAST** (self-labelled EXPERIMENTAL; omits the MODs). At MVEW1, CRNW1, RNTW1 and NKSW1 the official categories are in **stage** and HEFS produces **flow**, so an exceedance fraction is not computable without a conversion ADR-0011 forbids. §3.5 |
| **5.3** | Model agreement is a first-class signal | — | **CONFIRMED** | No change here; see 6.2. |
| **5.4** | A Cascade hazard index only after hindcast evaluation demonstrates skill | — | **CONFIRMED and strengthened** | Minor-flood base rates at the six seed points are **0.16–0.77 % of days**; at AUBW1 *moderate* there are **2 instantaneous events since 1990** and *major* has **never occurred** post-dam. Some strata are permanently **UNVERIFIABLE**. And relative economic value peaks at α = base rate, so only actions costing under ~1 % of their loss have value. §3.5, new §12C |
| **5.5** | Thresholds are official NWS categories, in stage or flow as NWS defines them, with datum recorded | — | **QUALIFIED — necessary and no longer sufficient** | A stage threshold has a **discharge vintage**. Measured conveyance drift at Mount Vernon flood stage is **9–11 % over roughly three decades**; the Nooksack at Ferndale has gained **+0.139 ft per decade** of stage at a given peak discharge. Add: no recurrence intervals (new §12B). §3.5 |
| **6.1** | Disagreement is information, never averaged away | — | **CONFIRMED** | Keep verbatim. |
| **6.2** | Agreement computed from crest magnitude, crest timing and category differences | — | **QUALIFIED — misses the dominant error mode** | The dominant upstream error is a **latitudinal displacement of AR landfall**, with a documented **northward bias** on this coast and ensemble spread largest on the **poleward flank** of the AR core. A metric on crest magnitude registers this as ordinary spread. Two further additions: **NWM v3.1 (operational 2026-08-18) assimilates USGS observations into the leading forecast hours**, so inside that tail "agreement" is agreement between a forecast and a gauge; and every member fraction must carry the **member count and the distinct-value count** (45 vs 6 are not comparable evidence). §3.6 |
| **6.3** | Model skill "is evaluated per basin and per regime … as history accumulates" | — | **QUALIFIED — too optimistic at two of six points** | History will not accumulate at AUBW1 moderate/major. Add: at regulated points the upper categories may **never** acquire a verifiable sample; the evaluation returns **UNVERIFIABLE with the instantaneous event count**, and the agreement surface is the only meta-signal available there. §3.6, new §12C |
| **7.1** | "SWE is storage, not hazard … the sign depends on temperature, pack state, and elevation distribution" | FACT | **QUALIFIED — correct, and unquantified in a way that overstates the buffer** | Attach the magnitude: the maritime pack's combined cold-content and liquid-water buffer is **≈30–45 mm of water** (~2.5 mm cold content + ~27–37 mm liquid) against a **200–400 mm** AR — it absorbs roughly **8–20 % of the storm**. Add the snowmelt-fraction prior (**~19–45 %** of water reaching the ground in a maritime ROS flood) and hard outflow ceilings (**<3 mm h⁻¹ net, <10 mm h⁻¹ total, never above 14 mm h⁻¹**). §3.7 |
| **7.2** | "Snow level ≈ freezing level − ~1,000 ft"; NWS Seattle uses 500–1,000 ft; store as a parameter | ASSUMPTION | **QUALIFIED — right central value, wrong functional form** | 250–450 m (800–1,500 ft) is the right central range and now has a peer-reviewed anchor (melting level 200–400 m below the free-air 0 °C isotherm). But the offset is **precipitation-intensity dependent** (melting distance 60 m weak → ~150 m at 3.5 mm h⁻¹ → >300 m intense) and the storm-to-storm range spans a full kilometre — so a constant is biased **exactly during the heaviest AR hours**. And three elevations must be named separately, because the platform's own input (NBM `SNOWLVL`) is a **wet-bulb column level** to which the terrain depression has not been applied at all. §3.7 |
| **7.3** | "Rain-on-snow runoff enhancement comes **mostly** from turbulent sensible and latent heat fluxes … the heat content of the rain itself is a minor term (FACT)" | FACT | **REFUTED as a general FACT** | The partitioning is **contested and regime-dependent**. Net radiation (longwave-dominated) leads in the event population and in wind-sheltered forest: **33–55 %** across three H.J. Andrews sites over eight years, **68 %** for the mountainous western US. Turbulent dominance (**60–90 %**) is a single wind-exposed extreme event. Advected rain heat is minor in mass (~7.5 % of rain depth at ΔT = 6 K) but is **29–44 % of the energy budget in persistent-melt events** — precisely the events that flood. **Keep the operational conclusion** (temperature, humidity and wind at pack elevation are forcing inputs) but derive it from *turbulence discriminates the extremes*, not from *turbulence dominates*. §3.7 |
| **7.4** | Snow level rising does not remove snow; melt requires an energy balance; the visualization must never depict snow disappearing because the snow line moved | — | **CONFIRMED** | Keep verbatim, and add the observational trap: **a SNOTEL pillow that does not fall during a ROS event is not evidence that the pack did not deliver water** — liquid retention, preferential flow through 3–8 % of the pack cross-section, and intermittent snowfall can all hold SWE flat or rising while outflow occurs. §3.7 |
| **7.5** | Basin hypsometry is the pivot; rain-exposed and ROS-exposed fractions are the first derived snow features | — | **CONFIRMED — and currently blocked** | No hypsometry exists in the repository (basin geometry is HUC8 unions). This is the largest structural blocker in the snow domain. Add the reason it matters: on 2025-12-11 the western-WA SNOTEL composite read **44 % of median** while the flood-relevant band **below 4,500 ft read 14 %**, with 10 of 20 sites at exactly 0.0 in. §3.7 |
| **7.6** | SNOTEL is ground truth for its elevation and aspect; SNODAS gives structure with maritime biases; fuse, do not pick | — | **CONFIRMED, and the consequence is more severe than stated** | The network is ground truth for a band **above** the one that makes the floods. Three basins are effectively single-station; AWDB returns **no median at all** for Decline Creek (Sauk) or Deer Pass (Stillaguamish), so percent-of-median is **uncomputable** in those two basins today. §3.7 |
| **8.1** | Remaining storage, not binary saturation; as storage fills, saturation-excess expands and a given rainfall produces a larger, faster hydrograph (FACT); infiltration-excess is rare | FACT | **QUALIFIED — correct but under-specified** | The expansion is **threshold-gated, not gradual**: published storm-precipitation thresholds are **18–60 mm** (30 mm at the closest analogue site; 55 mm at Panola with a **>75×** connectivity multiplier). Name the anchor that licenses ignoring intensity: infiltration capacity **>200 mm h⁻¹** against a maximum rain rate of **~10 mm h⁻¹**, a factor of ~20. And quantify the store: the wet-season dynamic store is only **71–104 mm**, and these basins fill it **between 1 October and 5 November in every water year of WY2020–2024**. §3.8 |
| **8.2** | Fuse NWM, SMAP L4, SNOTEL SMS and API; each contributes a percentile; disagreement is reported | — | **QUALIFIED** | The available-products statement is now wrong in detail. SNOTEL SMS: **zero stations** in the Stillaguamish, Skykomish/Snohomish, Snoqualmie and Green basins and **none in the Sauk**; the single Nooksack station returned nothing at all before 2025-12-12 and 51 days of 0.0 %. SMAP L4 is outside its own claimed validity envelope in the Cascades in winter. The literature ranking is **SMA bucket (R² 0.90) > API (0.82) > antecedent discharge index (0.67) > 5-day antecedent rainfall (0.19)**. §3.8 |
| **8.3** | "Percentiles require climatology; the platform builds its own from stored history … with the period stated" | — | **QUALIFIED — materially incomplete** | A period is necessary and not sufficient. **12.8–17.4 %** of daily observations change susceptibility band purely from estimating the ladder over 20 years instead of ~90, with trend removed by construction; a **regulation-regime split moves the ranking by 9.9–11.1 percentile points and flips 29–32 % of days** — larger than any climate effect measured. Percentiles need a **sampling interval, an effective sample size, a homogeneity epoch and a regulation epoch**. §3.8, new §12A |
| **9.1** | Stage and discharge are different observations related by a rating USGS shifts and revises; store both, never derive one from the other | FACT | **CONFIRMED — and now numerically justified** | Attach the numbers that make it non-negotiable: at Mount Vernon the stage–discharge scatter about a log-Q fit has SD **0.68 ft** and range **4.08 ft** against **2 ft** NWS category spacing, with a measured inversion of **138,000 cfs at 33.85 ft (2006) versus 127,000 cfs at 36.99 ft (2021)**; and the current rating is **extrapolated above ~125,000 cfs**. §3.9 |
| **9.2** | Vertical datums recorded on every stage series and threshold; mismatched comparisons refused | — | **CONFIRMED and extended three ways** | (a) The refusal must apply **within a single station's history**: the annual-peak stage series at Snoqualmie near Carnation contains a **41.26 ft datum discontinuity** between WY1939 and WY1940. (b) **Tidal datums are a different family** with a 1983–2001 epoch, and four relevant Puget Sound stations have **no published NAVD88 tie**; conversion requires VDatum, not arithmetic. (c) **Reservoir pool datum must be CONFIGURED per project**: every USACE A2W series returns `vertical_datum: NGVD29`, which contradicts the projects' own documents (Upper Baker NAVD88, Ross SCL datum). §3.9, new §9A, new §10A |
| **9.3** | Hydraulic headroom expressed three ways: stage, flow, and time-to-threshold | — | **QUALIFIED** | Four additions. Unsteady flow puts a **floor of roughly ±2–4 % on discharge** during fast rises and recessions on the lower Skagit, before any rating error — so **stage headroom is the more robust basis during a fast rise** and flow headroom inherits the rating loop. On an aggrading reach, stage headroom carries a **conveyance-drift uncertainty**. On a regulated reach, flow headroom is headroom **under a release decision that can change on the next forecast cycle**. At a `TIDAL` point, rate of rise over a 1/3/6 h window is dominated by the tide and time-to-threshold is meaningless unless the series is de-tided. §3.9, new §10A |
| **9.4** | "Rate of rise and acceleration are computed over named windows … trend never comes from the two endpoints of a response window" | — | **CONFIRMED as doctrine — and contradicted by the implementation** | The doctrine sentence is right and should stand. `cascade_hydrology.trend.rate_of_rise` computes `(pts[-1] − pts[0]) / span_h`, which is exactly the two endpoints. This is a code defect, not a doctrine defect. Add: the physically motivated denominator scale is the **recession time constant τ(Q)**, not a hand-chosen window. §3.9, new §8A |
| **9.5** | Routing topology from NWPS and NHDPlus/NWM; travel time estimated from history and NWM and carried as a distribution | — | **QUALIFIED — correct in intent, and the distribution now exists** | Seed it: median **16.9 h**, sd 3.5 h, range 9.5–23.8 h. And record two things the naive reading gets wrong: crest-to-crest lag is **not wave celerity** on this reach (it is 1.3–4× slower than βV, so it measures storage and local inflow), and it **lengthens with flood magnitude** — the opposite of kinematic expectation, and in disagreement with USACE's own stated hydraulic travel time, so it must be carried as INFERENCE. §3.9 |
| **9.6** | Regulated reaches: headroom depends on the operator's release plan; show the reservoir surface beside the reach; never natural-flow reasoning without the regulation flag | — | **CONFIRMED** | Keep, and extend with the three-buffer definition and `hours_to_top_of_flood` from §3.10. |
| **10.1** | Reservoirs are first-class entities with pool elevation, storage, rule-curve bounds, inflow, outflow, rate of change, operator, source and freshness | — | **CONFIRMED** | Extend the attribute set: `control_fraction`, `control_point_lid`, `objective_flow`, `channel_capacity`, `travel_time_h`, `section7_status`, `operating_authority`. §3.10 |
| **10.2** | "Flood-buffer capacity = available flood-control storage (rule-curve maximum − current storage)" | — | **SUPERSEDED** | One formula, three different questions. In December 2025 that formula puts Ross at **≈22 % of its designated flood pool** while Ross **absorbed 110,900 acre-feet — 92 % of a full design flood pool**. Replace with three signed volumes: `required_buffer` (may be negative — encroachment), `available_buffer` (what physically remains), and `pool_below_curve` (discretionary buffer the operator is not obliged to hold). §3.10 |
| **10.3** | "The platform never infers dam operations; it reports them. Forecast inflow comes from official sources where published; otherwise the reservoir's future state is UNKNOWN" | — | **QUALIFIED in three places** | (a) Official NWRFC **inflow forecasts are published** as ordinary NWPS gauge objects for RODW1, MORW1, TLRW1, and outflow for MMRW1 — but **UBDW1 and HHDW1 currently serve empty `data` arrays with three-week-old `issuedTime`s**, the exact shape that silently renders as "no flood risk". (b) The **rule curve is machine-readable** as a CWMS seasonal array, and the live Upper Baker and Howard Hanson curves **disagree with the published manuals**. (c) The prohibition on inferring operations is right, but the **official downstream forecast already embeds an assumed operating plan** made by NWRFC, so it must be labelled conditional. §3.10 |
| **10.4** | Levees, dikes and floodwalls displayed with authoritative attributes, never as guarantees; a design height is a design height | — | **QUALIFIED — correct and incomplete** | A levee failure **changes the gauge reading itself**: the Fir Island failure in November 1990 "increased the river slope and velocity below Mount Vernon, causing an artificially low crest stage at the Mount Vernon gage". The doctrine needs an **observability clause**, not just a disclaimer. §3.10, §3.9 |
| **11.1** | Structured drivers only; no free-text LLM causal reasoning presented as hydrology | — | **CONFIRMED** | Keep verbatim, with one new prohibition: the **HEFS member index is a historical year used for rank ordering, not a weather analogue**, and the explanation layer must not attribute a year's meteorology to a member. §3.11 |
| **12.1** | Knowledge-time replay; store `available_at`; keep superseded forecasts and revisions | — | **CONFIRMED — and there is a live bug class** | `as_known_at(T)` guarantees the *values* known at T. It does not guarantee the **reference distribution** known at T (an annually rebuilt ladder back-dates a better baseline into a replay), nor the **product version** (AORC/MRMS reprocessing), nor the **model version** (NWM v3.0 → v3.1 on 2026-08-18), nor **archive survivorship** (the HEFS API retains ~10 cycles; purged rows are invisible rather than `quality=missing`). §3.12, new §12A |
| **12.2** | Event Zero was "a CW3E AR-4 (coastal WA) / AR-3 (Cascade foothills) event with ~96 h of AR conditions" | FACT | **SUPERSEDED — category error** | Under the AR scale's own definition an AR *event* is one **continuous** period of AR conditions at a point. Three ARs across Dec 3–11 2025 are an **AR family**; 96 h is the family span, not an event duration, and the scale cannot be applied to it as a single event. The categories themselves came from CW3E imagery and fail the platform's §1 provenance rule unless recorded as CONFIGURED-from-narrative. §3.12 |
| **12.3** | "Near record-low statewide snowpack — so the response was rain on saturated soils, not snowmelt" | FACT | **CONFIRMED and sharpened with primary data** | Upgrade from "near record-low statewide" to a basin-band measurement: on 2025-12-11 the twenty western-WA Cascade SNOTEL sites **below 4,500 ft held 14 % of median SWE, with 10 of 20 at exactly 0.0 in**, while the all-station composite read 44 % because three crest/leeward sites were at 128–174 %. §3.12 |
| **12.4** | Mount Vernon crested at a preliminary record 37.73 ft / ~133,000 cfs, above the 1990 record of 37.37 ft despite a lower flow | — | **QUALIFIED** | True as recorded, and it teaches a stronger drift than the evidence supports unless three qualifications travel with it: the **1990 stage is breach-depressed** (Fir Island failed twice); the December 2025 peak is **preliminary and not yet in the USGS annual peak series**; and the drift is **9–11 % at flood stage over ~three decades** (population-level, −4.4 % at 37 ft), **not the ~29 % the prior pass reported** from a two-point comparison against a 1906 indirect estimate whose peak day is unknown. §3.12 |
| **12.5** | Snohomish at Snohomish and Cedar at Renton also set records | — | **QUALIFIED** | SNAW1's record stage is a **compound quantity** — the gauge transmits 0.831 ft of stage per ft of Seattle tide at low flow. On the day it crested the tide happened to be **6.64 ft below MHHW**, so the record is a river record that arrived at a benign coastal boundary. That must be recorded, or the first crest that lands on a king tide will be a surprise. §3.12, new §10A |
| **12.6** | Ross held back ~99 % of inflow under Section 7 from Dec 8; Howard Hanson reached a record pool (1,189.3 ft, ~75 % of flood storage); regulation dominated the Green, White/Puyallup and Skagit outcomes | — | **QUALIFIED** | "~99 %" is confirmed **at the instantaneous peak** (50,099 cfs in, 389 cfs out) and should be stated that way; **event-integrated, Ross passed roughly 20 % of the inflow volume**. Howard Hanson's live storage series reads **75,171 ac-ft** where USACE's release used the capacity table's **77,700** — a 3.3 % disagreement that must be reported, not reconciled. And "regulation dominated" needs its bound attached: the dams control **39 % / 55 % / 42 %** of the drainage area at the three control points. §3.12, §3.10 |
| **12.7** | The first NWS Seattle Flood Watch was issued 2025-12-05 16:10 PST, ~2.5 days before the main AR and 6.5 days before the crest | — | **CONFIRMED** | Keep, and add the replay result that gives it meaning: on that day the susceptibility surface would have read **MODERATE in all six basins**, and two days earlier **LOW in four of six**. The signal was in the derivative — the Sauk moved **64 percentile points in 48 hours** — which is not currently a driver. §3.12, §3.3 |
| **12.8** | The Mount Vernon forecast crest evolved 36.9 → 41.5 → 42.3 → 39.1 → 38.26 ft before the 37.73 ft observation | — | **CONFIRMED — and should be elevated** | This is a textbook **flip-flop** with a **+4.57 ft peak over-forecast**, and it is the platform's first and best consistency benchmark. It sets the scale of what the official forecast can be wrong by in this region and is the honest counterweight to badging it OFFICIAL. §3.12, new §12C |
| **13.1** | Will not claim: a probability without a calibrated, hindcast-evaluated method | — | **CONFIRMED — strengthened** | At base rates of 0.0016–0.008, a probability that has not passed a reliability check with a stated *n* is not merely unproven; it is very likely **uncheckable** with the data the platform will hold for years. §3.13 |
| **13.2** | Will not claim: flood depth, inundation extent or water-surface elevation without an authoritative model | — | **CONFIRMED** | Keep verbatim. |
| **13.3** | Will not claim: that a levee or dam "will hold" | — | **CONFIRMED** | Keep, and extend: never render a reservoir as **"protecting"** a place (the Corps' own manuals state total control is impossible at 42–55 % control fraction), and never display **"damages prevented"**. §3.13 |
| **13.4** | Will not claim: that a source is current when it is stale, or official when it is configured | — | **CONFIRMED** | Keep, and add the newly-found failure shape: an **empty forecast array with a live-looking metadata block** is a staleness event, not an absence of hazard. §3.13 |
| **13.5** | Will not claim: any evacuation, warning or life-safety instruction | — | **CONFIRMED** | Keep verbatim. Nothing in the corpus touches it. |
| **14** | Glossary (13 terms) | — | **QUALIFIED — incomplete** | Add: mountainside snow line, atmospheric snow level, melting level, upslope IVT, non-dimensional mountain height, AR family, sensitivity function `g(Q)`, recession time constant, dynamic storage, runoff regime, sediment regime, rating epoch, conveyance drift, tidal class, skew surge, control fraction, encroachment, snow drought, AEP, ladder vintage, UNVERIFIABLE. §3.14 |

---

## 2. How to read the replacement text

§3 gives the **full proposed replacement text** for every existing section that changes. §4 gives the
**full text of every proposed new section**, with its intended insertion point. Both are written in
`HYDROLOGY.md`'s existing voice and labelling convention (FACT / ASSUMPTION / INFERENCE / OPEN
QUESTION) and are conservative by construction: where the corpus disagrees with itself, the proposed
text says so rather than picking a side.

Sections **6 (agreement, in part), 11, 13 (in part) and 14 (in part)** change only by addition; their
unchanged paragraphs are shown elided as `[unchanged]` so the diff is visible. Sections **3, 5, 12**
change by both replacement and addition.

New sections carry letter suffixes (§8A, §9A, §10A, §12A, §12B, §12C) to avoid renumbering the whole
document in a proposal. If the delta is accepted, renumbering is a mechanical follow-up.

---

## 3. Full proposed replacement text, section by section

### 3.1 Replacement for §1 — The problem, stated as state estimation

> ## 1. The problem, stated as state estimation
>
> A watershed at time *t* holds water in a small number of stores. Weather adds water to the stores;
> the stores release it to the channel network at rates that depend on how full they are; the channel
> network routes it downstream — delayed, and usually but not always attenuated — through lakes and
> reservoirs whose operators may hold or release it, and, at the deltas, against a sea whose level is
> itself a boundary condition. Gauges, satellites, snow pillows, soil probes, radar and models
> observe this system imperfectly.
>
> ```
> state  S(t) = { soil water storage per elevation band,
>                 groundwater / baseflow state,
>                 snow storage per elevation band (SWE, cold content, liquid water, snow-covered area),
>                 channel storage per reach,
>                 channel conveyance state (bed elevation / rating epoch — a slow variable),
>                 lake / reservoir storage and the operator's allocated, available and
>                     discretionary buffers,
>                 coastal water level at tidally influenced outlets,
>                 frozen-ground / ice state (rarely material in western WA) }
>
> forcing F(t) = { precipitation rate, duration and phase per elevation band,
>                  short-duration intensity (I15, I60) where a geomorphic product needs it,
>                  air temperature, humidity, wind at snowpack elevations (energy for melt),
>                  freezing level, atmospheric snow level, mountainside snow line,
>                  terrain-projected (upslope) IVT, its direction, and its duration,
>                  low-level flow orientation relative to the basin's own barrier,
>                  the non-dimensional mountain height M = N h / U (is the flow blocked?),
>                  storm sequence structure (is this AR one of a family?) }
>
> observations y(t) = h(S(t), F(t)) + noise      (gauges, SNOTEL, SNODAS, MRMS, NBM, CO-OPS, …)
>
> question: P( Q_reach(t+h) > threshold | y(≤t), forecast distribution of F(t..t+h) ),  h ∈ {6,12,24,48,72,120} h
> ```
>
> **One component of the state vector is directly measured.** Under the storage-controlled assumption
> (Kirchner 2009), discharge is a monotone function of storage, so a flow percentile *is* a storage
> percentile and the basin's sensitivity to an additional millimetre of storage is recoverable from
> its own recession behaviour (§8A). This is the only part of `S(t)` the platform can observe without
> a model, and it is the reason the susceptibility surface is built on streamflow.
>
> The distinction the brief makes is the one we keep, with two corrections the evidence forces:
> **forcing determines how much water enters; state determines the *gain* that converts it to
> discharge, and most of what leaves was already in the basin.**
>
> - **The gain is large and measured.** Fitting Kirchner's sensitivity function on wet-season
>   recessions at four unregulated western Washington gauges gives `g(Q) ∝ Q^0.85–1.05`: a basin
>   sitting at 1.0 mm h⁻¹ converts an extra millimetre of storage into **7.6–11.1× more discharge**
>   than the same basin at 0.1 mm h⁻¹ (FACT — computed 2026-08-24 from five water years of USGS
>   instantaneous values; `docs/research/corpus/runoff-generation.md` §5.4). "Reacts" understates a
>   factor of ten.
> - **The gain's discriminating power in this region is nonetheless small during the flood season**,
>   because the basins are already at the top of their storage range. The wet-season dynamic store is
>   only **71–104 mm** and these basins filled it between **1 October and 5 November in every water
>   year of WY2020–2024** (FACT — same computation). Washington sits in the *low*-responsiveness
>   group of the West Coast antecedent-moisture synthesis: a **≈2-fold** amplification of event
>   maximum streamflow above the local threshold, against ≈4.5-fold on the California and Oregon
>   coast (FACT — Webb et al. 2025, controlling for storm-total precipitation). Low is not zero, and
>   the platform must say both sentences.
> - **Most of the forcing-side information is geometric and temporal, not volumetric.** Of the five
>   conditions that separate a flooding AR from a non-flooding one in this region — orientation,
>   strength, stationarity, melting level, antecedent soil wetness — only *strength* is a "how much"
>   quantity (FACT — Neiman et al. 2011). A clean forcing/state split hides this.
>
> Extreme Western Washington floods are forcing-driven (FACT — every peak daily flow above a 5-year
> return period in four unregulated western Washington basins over WY1980–2009 occurred with a
> landfalling atmospheric river, and 46 of 48 annual peak daily flows in WY1998–2009 did; Neiman et
> al. 2011). **The atmospheric river is a necessary cause and a poor sufficient one** — the same
> study is explicit that not all ARs in that period generated flooding, and the only published
> category-to-flood mapping anywhere (the Russian River) found major flooding in 33 % of AR 5 and
> 30 % of AR 4 events (FACT). Antecedent state modulates the response, sometimes strongly, and it
> never substitutes for the forcing: at the unregulated gauges, **24–25 % of cool-season annual
> maxima were preceded by a below-25th-percentile antecedent state seven days earlier** (FACT —
> computed 2026-08-24 from the full USGS daily record), including the second-largest Skykomish peak
> in 98 years.
>
> **Routing has two signs.** Between Concrete and Mount Vernon the peak change across twelve events
> 2003–2025 ranged from **−24.8 % to +27.8 %**, median −6.1 % (FACT — computed from USGS
> instantaneous values), and USACE documents the amplification mechanism directly: "floods with high
> peaks and large volumes will generally fill the channel storage, and combined with runoff from the
> 356 square mile local area … will cause the peak discharge to increase as it moves downstream."
> "Delayed and attenuated" is the common case, not the rule.

### 3.2 Replacement for §2 — The Western Washington regime

> ## 2. The Western Washington regime (what makes this region specific)
>
> - **Season.** Flood season is roughly October–March, with a November–January core, when atmospheric
>   rivers are most frequent and most moisture-laden (FACT — computed 2026-08-24 from the USGS annual
>   peak record: Oct–Mar carries **86–95 %** of annual peaks and Nov–Jan **63–70 %** at the Sauk,
>   Skykomish, Snoqualmie and Skagit at Mount Vernon). The dates recur across basins — 1990-11-24/25
>   and 2006-11-06/07 appear in the top three at three of the four gauges — so **regionally
>   simultaneous loading, not basin-by-basin independence, is the extreme signature** (INFERENCE from
>   the same computation).
>
> - **Atmospheric rivers.** ARs are long, narrow, *transient* corridors of concentrated water-vapour
>   transport ahead of the cold front of an extratropical cyclone; integrated vapour transport
>   (IVT, kg m⁻¹ s⁻¹) is the standard measure (FACT). Four properties of the AR scale (Ralph et al.
>   2019) must travel with any category the platform ever displays, because without them the number
>   invites a misreading the authors explicitly warn against (all FACT):
>   - it is **Eulerian at a point**, computed from a time series of IVT on a 0.5° grid, with **no
>     shape or geometry test** — it is not an AR detection algorithm;
>   - an **"AR event" is one continuous period** of IVT ≥ 250 kg m⁻¹ s⁻¹ at that point; a sequence of
>     ARs separated by sub-threshold gaps is **not one event** and cannot be scored as one;
>   - **duration promotes a category**, so an "AR 4" is not a statement that IVT reached
>     1000 kg m⁻¹ s⁻¹; at the one well-observed reference point a material share of high-category
>     events got there by lasting ≥48 h;
>   - the authors state the scale is **not linked to a location**, so its impact meaning varies with
>     topography, land surface and antecedent conditions. **A category may never be rendered as a
>     basin hazard level.**
>
>   Whether an AR is present at all is a **method output, not an observation**: applying 20+ published
>   detection algorithms to one dataset gives materially different frequencies, durations and
>   seasonalities (FACT — ARTMIP). Any AR flag the platform computes is DERIVED/EXPERIMENTAL and
>   carries its detector's parameters. Two products disagreeing about AR presence is information, not
>   a fault.
>
> - **The five conditions.** What separates a flooding AR from a non-flooding one here is a
>   conjunction, of which magnitude is one term (FACT — Neiman et al. 2011): **orientation** of the
>   low-level flow into the specific basin, **strength** of the onshore low-level vapour flux,
>   **stationarity** (whether the AR stalls), **melting level** (how much of the basin is
>   rain-exposed), and **antecedent soil wetness**. The two atmospheric quantities with published
>   skill against *runoff* rather than against precipitation are:
>   - **storm-total upslope IVT** — the moisture flux projected onto the terrain gradient — which
>     explained **74 % of the variance in storm-total rainfall and 61 % of storm-total runoff volume**
>     across 91 events at a coastal observatory, and gives **r² = 0.85** against hourly windward
>     rainfall in warm-sector Olympic events with a slope of 0.014 mm h⁻¹ per kg m⁻¹ s⁻¹ (FACT);
>   - **duration of AR conditions** — ARs with double the composite mean duration produced nearly
>     **6× greater peak streamflow and more than 7× the storm-total runoff volume** (FACT).
>
>   Neither exists in the platform today. Orientation is basin-specific and statistically separable:
>   the Green floods only on low-level flow from **245°–275°**, the Sauk essentially only on
>   south-westerly flow, and the separation between basin pairs is significant at >95 % confidence
>   (FACT). The Green's peak flows vary by an **order of magnitude** between years, which Neiman et
>   al. attribute to the narrowness of that window; its flood composites carry the *weakest* vapour
>   fluxes of the four basins studied — i.e. **flooding on the Green is more sensitive to flow
>   orientation than to the magnitude of the incoming flux** (FACT). Per-basin windows are published
>   only for the Green and the Sauk; the other six are an OPEN QUESTION and are derivable from the
>   platform's own record.
>
> - **AR families.** About half of all ARs belong to a family — two to six ARs within a regional
>   aggregation window, typically taken as 5 days (FACT). *Density*, not count, is what matters: over
>   the **Cascade Range the extra runoff from dense clusters is 150–300 % more than from sparse
>   clusters**, and dense clusters peak in November (FACT). The mechanism is the one fill-and-spill
>   predicts: the earlier ARs remove the basin's remaining storage so the later one cannot be
>   absorbed. Event Zero was a family, not an event (§12).
>
> - **Orographic enhancement.** Precipitation increases steeply on windward slopes and maximises on
>   **ridge crests upwind of the range crest, not at the highest elevations** (FACT — a ~800 m,
>   ~10 km-wide Olympic ridge carries 50 % more precipitation than the valleys 10 km either side;
>   annual-mean ridge-crest excess is 50–70 %, with 50–300 % local enhancement in model climatologies;
>   Washington's wettest recorded station sits at 600 ft). Elevation is a proxy that fails at exactly
>   the sub-basin scale where it is most tempting to use.
>
>   The relation holds only when the flow can ascend. The blocking criterion is the non-dimensional
>   mountain height `M = N h / U` (the inverse Froude number); blocking is favoured when `M > 1`, and
>   the linear upslope prediction degrades badly as `M` rises (FACT). Measured over the Olympics
>   across 18 frontal periods: warm sector mean **M = 0.7** (unblocked, high IVT, high enhancement),
>   warm frontal **1.1**, post-frontal **2.5** (blocked, weakly forced) — but the per-event spread
>   forbids using frontal sector as a proxy, and `M` must be computed (FACT). The **Puget Sound
>   Convergence Zone** is a separate mechanism entirely: post-frontal, diurnally modulated,
>   terrain-wake convergence that lands on the Snohomish/Skykomish/Snoqualmie headwaters at a time
>   when the upslope relation has already failed. No IVT-based reasoning will see it, and a low
>   forcing level derived from IVT or QPF must never be rendered as reassurance during post-frontal
>   north-westerly flow.
>
> - **Basin-aggregated precipitation carries a signed, regime-dependent uncertainty**, not a random
>   one, and it must be computed from the highest-resolution product available with the regime label
>   travelling beside it (FACT): coarse-model verification over this region found light and moderate
>   events **over**-predicted on upper windward slopes and heavy events **under**-predicted in the
>   lowlands and Cascade gaps; modern convection-permitting models show bias ratio rising
>   windward → leeward across barriers, and the authors decline to say whether that is model bias or
>   reference bias (OPEN QUESTION). The observing floor is real: radar QPE adequately covers only
>   **one-quarter to one-third** of the coastal western US land surface, reads **<50 % of gauge
>   values** in the heaviest precipitation of a real flood, and names the Snoqualmie among the basins
>   whose coverage is "extremely poor or nonexistent"; and cool-season gauge undercatch in this
>   region runs **5–15 % in the lowlands, 15–20 % in Cascade gaps and 25–40 % above 1,500 m**. Where
>   a gridded QPE product falls back to a climatological downscaling of distant gauges, the cell is
>   **MODELED, not OBSERVED**, and the platform must say so.
>
> - **The rain/snow transition is three distinct elevations, not one** (§7), and the transient snow
>   zone is **not a fixed band**. The concept "implies a static area, when in fact the area undergoing
>   melt is highly dynamic during storm events" (FACT), the observing network does not cover the band
>   that generates the floods (median western-WA SNOTEL elevation **3,900 ft**; only **1 of 31 sites
>   below 2,000 ft**), and the band's own position drifts (centre-of-timing has moved **2.3–4.6 days
>   per decade** earlier at the snow-influenced gauges over ~90-year records). The platform therefore
>   computes the **rain-exposed** and **rain-on-snow-exposed** basin fractions each cycle from
>   hypsometry and the forecast mountainside snow line, and does not carry a fixed elevation band as
>   a parameter.
>
> - **Two runoff-generation regimes, not one.** The platform's basin list spans (a) **Cascade-front
>   mountain basins** — deep permeable profiles over saprolite and volcanics, saturated conductivity
>   far exceeding any rain rate, storm flow by lateral subsurface flow at the soil–bedrock interface;
>   and (b) **Puget Lowland basins and lower reaches** — Vashon till and glaciomarine clay forming
>   shallow aquicludes, where perched water flows along the permeability contact and the response is
>   fastest and least buffered (FACT; the region's own regulatory hydrology already encodes till
>   versus outwash as separate runoff-generation classes). `runoff_regime` belongs beside
>   `regulation_class` as a basin/sub-basin attribute.
>
> - **Basin response times are dominated by regulation, not by basin size** (FACT — computed
>   2026-08-24). The recession time constant at a flood-generating flow of 1 mm h⁻¹ is **17.5–28.1 h**
>   in the unregulated basins (Sauk, Skykomish, NF Stillaguamish, Snoqualmie), **42 h** at Skagit at
>   Mount Vernon, **116 h** on the Cedar and **264 h** on the Green below Howard Hanson. Any
>   travel-time or time-to-threshold logic that uses one time scale for regulated and unregulated
>   reaches is wrong by an order of magnitude. Crest lag from Concrete to Mount Vernon is a measured
>   distribution — **median 16.9 h, sd 3.5 h, range 9.5–23.8 h** — not "roughly a day" (FACT, n = 12).
>
> - **Regulation.** The region mixes near-natural and heavily controlled rivers (FACT for the
>   operators; operational details vary):
>   - Skagit: Ross, Diablo and Gorge (Seattle City Light) control the upper Skagit; **Upper Baker**
>     (Puget Sound Energy) carries **74,000 acre-feet** of authorised flood storage on the Baker.
>     **Lower Baker has no authorised flood storage**; it is constrained only against drawing down
>     while Upper Baker is storing. The **Sauk** is unregulated, is **over 25 % of the area above
>     Concrete and just over half the uncontrolled area**, and contributed **45–64 %** of the Concrete
>     peak in the 1990, 1995, 2003 and 2006 floods.
>   - Green: Howard A. Hanson Dam (USACE) above Auburn; this is why NWS defines Auburn's flood
>     categories by **flow**.
>   - White: Mud Mountain Dam (USACE) above Auburn; flow-defined categories.
>   - Cedar: Chester Morse Lake / Masonry Dam (Seattle Public Utilities) — a water-supply reservoir
>     whose flood reduction is **incidental**; no public rule curve or flood release schedule has been
>     located (OPEN QUESTION). Renton's stage thresholds are official.
>   - Snoqualmie: essentially unregulated on the main stem; the South Fork Tolt reservoir (SPU) is a
>     small upstream control on the Tolt tributary.
>   - Nooksack: unregulated; the lower river is weakly tidally influenced at Ferndale (0.019 ft of
>     stage per ft of Cherry Point tide — see §10A, and note that the strongly tidal forecast point in
>     the platform is **Snohomish at Snohomish**, not Ferndale).
>
>   **What regulation cannot do is a published number and it belongs in the doctrine.** Control
>   fraction — the share of the drainage area above a gate — bounds everything downstream: Ross and
>   Upper Baker control **39 %** of the area at Mount Vernon (32 % of mean annual runoff); Howard
>   Hanson **55 %** above Auburn; Mud Mountain **42 %** at Puyallup (FACT, each stated in the
>   project's own manual or study). The consequence is stated by USACE without hedging: the Skagit
>   system holds the lower valley below damage only to about the **4–5 % exceedance (20–25-year)**
>   event, and above that "flood runoff from the Skagit's uncontrolled watersheds … is sufficient to
>   produce major flooding in the valley **regardless of the flood control regulation**" (FACT).
>   Separately, **low-elevation tributaries below the flood-control dams can contribute more than
>   half the total flow** — and those tributaries are the most rain-exposed part of the basin under a
>   high melting level, so a warm AR shifts flood generation into precisely the area the dams do not
>   control (FACT).
>
>   A basin's `regulation_class` (natural / partially regulated / regulated) is a domain attribute
>   that changes how every downstream quantity is interpreted — and it is now independently
>   measurable: the storage–discharge sensitivity exponent orders the basins exactly as
>   `regulation_class` does (unregulated 0.85–1.05 > Skagit at Mount Vernon 0.67–0.77 > Cedar
>   0.17–0.26 > Green −0.06), so the hydrograph itself can be used as a consistency check on the seed
>   data (FACT — computed 2026-08-24).
>
> - **Three basins have glaciated stratovolcano headwaters** — Nooksack (Mount Baker), Skagit
>   (Glacier Peak via the Sauk; Mount Baker via the impounded Baker), White (Mount Rainier) — and
>   this, not land use, is the best single predictor of which gauges' stage records drift (§9A).
>   `sediment_regime` belongs beside `regulation_class` as a display-only basin attribute.

### 3.3 Replacement for §3 — Surface I, Basin susceptibility

> ## 3. Surface I — BASIN SUSCEPTIBILITY
>
> *How primed is the watershed to respond strongly if significant precipitation arrives?*
>
> The physics is a **switch plus a gain**, not a reservoir filling linearly. Hillslopes connect to the
> channel network above a storage threshold and barely contribute below it: the published
> storm-precipitation thresholds are **18–60 mm** (30 mm at the closest analogue site in the western
> Cascades), and measured subsurface stormflow was **more than 75× larger** once connectivity was
> achieved (FACT). The honest form of an antecedent index is therefore **distance to a threshold and
> the gain above it**, not a linear rank — a percentile band implies a smooth dose–response the
> physics does not have (INFERENCE).
>
> Inputs (each a `DerivedFeature` with provenance and percentile context):
>
> | Feature | Meaning | Primary sources (see DATA_SOURCES) |
> |---|---|---|
> | river state percentile, and **its 24/48 h change** | current flow vs day-of-year climatology; the *level* is a state estimate and the *derivative* is the event signal | USGS (observed), NWPS |
> | **catchment sensitivity `g(Q)`** and its gain vs the seasonal median | how sharply discharge responds to one more millimetre of storage (§8A) | USGS discharge (derived) |
> | **recession time constant τ(Q) = 1/g(Q)** | the basin's own physical response time scale | derived |
> | **storage limb** (rising / falling / unknown) | storage–discharge is hysteretic; the same percentile means different things on the two limbs | derived |
> | soil water storage / saturation percentile | remaining storage before saturation-excess runoff dominates | NWM land output and NWM retrospective (modeled), API proxy |
> | antecedent precipitation index (API, 7/14/30 d), and a 90-day standardized index | recency-weighted prior rainfall | MRMS/Stage IV (observed), AORC, SNOTEL PREC |
> | baseflow / groundwater proxy | how high the slow store sits | gauge baseflow separation (derived), NWM |
> | snow storage & state | SWE **below the forecast mountainside snow line**, snow-covered fraction, pack buffer capacity | SNODAS (modeled/assimilated), SNOTEL (point), MODIS/VIIRS SCA |
> | **snow drought state** (none / dry / warm / warm-and-dry) | the one *signed* snow feature: warm snow drought raises susceptibility, dry snow drought lowers it, and low SWE alone says nothing | AWDB WTEQ + PREC percentiles (derived) |
> | reservoir buffers (required / available / discretionary) | how much of the operator's flood space remains, in three distinct senses (§10) | operator data (USACE CWMS, SCL, PSE, SPU) |
> | seasonal context | where in the climatological year we are | static |
>
> Output: a categorical state (LOW / MODERATE / HIGH / VERY HIGH / UNKNOWN) plus the contributing
> features, each with its value, percentile, direction of contribution, and freshness. Until
> calibrated against history it is labeled an **experimental susceptibility index**, never a
> probability.
>
> **Three honesty constraints the surface must carry, each measured** (all FACT, computed 2026-08-24
> on the platform's own configured gauges):
>
> 1. **A percentile is not a number until it carries a sampling interval.** A 30-year day-of-year
>    ladder estimates a mid-winter percentile with a sampling SD of **±5.5–6.2 percentile points**; a
>    10-year ladder, **±12**. The band edges are 25/75/90. A value within one standard deviation of an
>    edge is **not resolvable into a band**, and the surface must return UNKNOWN with a reason rather
>    than manufacture the distinction.
> 2. **The ladder saturates exactly where floods live.** Stored percentiles stop at p95 and clamp.
>    During the December 2025 event the Sauk read p95 / VERY HIGH at 24,900, 41,500, 62,600 **and**
>    21,100 cfs on four consecutive days — a 2.5× range in flow with zero percentile discrimination —
>    and it could not fall as the river receded. Observed flows reach **5.0× the p95 ladder value**.
>    Either the tail is extended where the sample supports it, or the surface publishes the **flow
>    multiple** (`value ÷ ladder p95`) beside the clamped percentile, or it declares itself saturated.
> 3. **The level is not the signal; the derivative often is.** Replaying December 2025 with a
>    climatology that excludes 2025, the surface would have read **LOW in four of six basins on 3–4
>    December** and **MODERATE in all six on 5 December** — the day NWS Seattle issued its first Flood
>    Watch, 6.5 days before the record Mount Vernon crest. It first read VERY HIGH on 8–10 December,
>    when the rivers were already in flood. Across the full record, **45–75 % of all VERY HIGH
>    readings occur on days when flow is already more than 25 % above its value three days earlier.**
>    The Sauk moved **64 percentile points in 48 hours** on 4–6 December. A VERY HIGH reading
>    concurrent with a rising hydrograph and a VERY HIGH reading on a stable one mean opposite things
>    and must be visually distinct.
>
> What it is not: it is not a flood forecast. A basin can be VERY HIGH susceptibility in a dry
> forecast and the hazard is LOW.
>
> **And LOW is not an all-clear.** Measured at the six configured gauges, a LOW band still carries a
> **0.0–0.8 %** probability of a top-1 % November–February flow within the following week against a
> **1.0 %** base rate, and **24–25 % of cool-season annual maxima at the unregulated gauges were
> preceded by a below-25th-percentile state seven days earlier** — including the second-largest
> Skykomish peak in 98 years (antecedent percentile 8 at −5 days). The surface reports the antecedent
> state's level *and* its rate of change, and never renders LOW as reassurance.

### 3.4 Replacement for §4 — Surface II, Meteorological forcing

> ## 4. Surface II — METEOROLOGICAL FORCING
>
> *How much hydrologically significant water is likely to arrive, where on the basin, in what form,
> and for how long?*
>
> | Feature | Meaning | Sources |
> |---|---|---|
> | basin-average QPF per window (6/12/24/48/72/120 h) | liquid-equivalent precipitation forecast, area-weighted over the basin polygon | NBM, HRRR, GFS/GEFS, WPC QPF |
> | **duration above a rate**, and basin fraction simultaneously above it | the western-Cascades extreme is long and moderate, not short and intense | same, hourly |
> | **short-duration intensity (I₁₅, I₆₀)** | the controlling variable for every regional debris-flow product; absent today | MRMS hourly QPE (observed) |
> | rain/snow partition per elevation band | fraction of QPF falling as rain, using the forecast **mountainside snow line** and hypsometry | NBM/HRRR wet-bulb snow level + terrain offset + DEM |
> | **rain-exposed basin fraction** | share of basin area below the forecast mountainside snow line | derived |
> | **rain-on-snow exposed fraction** | share of currently snow-covered area below the forecast mountainside snow line | derived (SNODAS/SCA ∩ snow line) |
> | **upslope IVT** — IVT projected onto the basin's own terrain gradient — instantaneous and **integrated over the event** | the strongest published atmospheric predictor of runoff (74 % of storm-total rainfall variance, 61 % of runoff-volume variance) | GFS/GEFS pressure-level fields (derived) |
> | **AR duration** — hours of continuous IVT ≥ 250 kg m⁻¹ s⁻¹ at the basin's reference point | co-equal with intensity: 2× duration ⇒ ~6× peak streamflow | derived |
> | **orientation favourability** — angular distance between forecast low-level flow and the basin's optimal window | the only western-WA-specific, statistically significant flood discriminator published | GFS/GEFS + CONFIGURED per-basin bearing |
> | **non-dimensional mountain height `M = N h / U`** | is the flow blocked? a driver that *qualifies the QPF's confidence*, never a multiplier | derived from model sounding + DEM |
> | **AR sequence / family** — membership, inter-event gap, cluster density | dense clusters produce 150–300 % more Cascade runoff than sparse ones | derived, with an explicit aggregation-period parameter |
> | **AR category** (Ralph et al. 2019) computed by the platform, badged DERIVED/EXPERIMENTAL | so a category can carry provenance instead of being read off an image | derived from IVT + duration |
> | temperature, **dewpoint and wind at band elevations** | melt energy proxies; the discriminating variables for an extreme rain-on-snow event | HRRR/NBM |
> | forecast spread, including **latitudinal spread of coastal IVT maximum** | ensemble disagreement, and the dominant error mode on this coast | GEFS, NBM percentiles |
> | **basin-average MAP / MAT / SWE ensembles** where an authority publishes them | a bias-corrected 45-member basin-average forcing ensemble on the RFC's own zones | NWS HEFS/MEFP (modeled) |
>
> **CW3E's AR-scale and IVT products are image-only, research-use-only, with no data endpoint**
> (re-confirmed 2026-08-24). They must not be listed as a source and must not be ingested: a category
> read off a picture has no `valid_time`, no `issued_at`, no model identity and no unit, and cannot
> satisfy §1 of `DATA_DOCTRINE.md`.
>
> Output: per horizon, a categorical forcing level plus the numbers behind it and their spread.
> Forecast values always carry `issued_at` and `valid_time`; a newer run supersedes, never overwrites,
> an older one.
>
> **A single basin-mean scalar, banded, cannot carry this surface** (INFERENCE, and it is the sharpest
> structural criticism the corpus makes of the current design). Two ARs with identical basin 72-hour
> QPF but different orientation, duration and melting level have documented flood responses differing
> by nearly an order of magnitude. Two further measured cautions on the band edges: the top-10 annual
> peak daily flows on the Sauk and the Green occurred with **2-day Cascade precipitation totals of
> 85–150 mm**, and the top 0.1 % of daily precipitation across the whole NWRFC region is
> **73.7 mm/24 h** — both suggest the upper edges sit high, and both are cheap hindcast checks
> (INFERENCE; the comparisons are not like-for-like and are flagged as such).

### 3.5 Replacement for §5 — Surface III, Flood hazard

> ## 5. Surface III — FLOOD HAZARD
>
> *Given susceptibility, forcing, routing, regulation and model uncertainty — what is the chance
> meaningful thresholds are crossed, per horizon?*
>
> Ordered by authority:
>
> 1. **Official forecast category** (NWPS/NWRFC deterministic forecast vs official categories): the
>    forecast crest and its category, when issued, by whom. This is always shown and always labeled
>    OFFICIAL.
>
>    Two properties of that forecast must travel with it. First, **it is an observation of an
>    authority's judgement, not a model output the platform could reproduce.** The NWRFC chain runs
>    SNOW-17 → SAC-SMA → unit hydrograph → Lag-K inside CHPS, and its data assimilation is the duty
>    forecaster's manual modification of model states — modifications that are not logged publicly and
>    are not present in any ensemble product (FACT). The official forecast is archived verbatim with
>    its issuance time and is never modelled. Second, **at a regulated point it is conditional on an
>    assumed operating plan**: NWRFC incorporates the planned regulation into its forecast of
>    reservoir elevation and downstream discharge (FACT), so the forecast at Mount Vernon, Auburn or
>    Puyallup embeds an operator decision that has not been published. That sentence belongs on the
>    display.
>
>    It is also the best antecedent-state-conditioned product available for these basins — its state
>    vector is snow water equivalent, snow cover, soil moisture and river/reservoir levels, adjusted
>    by a human to match observations before each run (FACT) — which is the substantive reason it
>    ranks first, not merely deference.
>
>    Its error scale here is known and should be stated rather than implied: the Mount Vernon forecast
>    crest for the December 2025 event evolved **36.9 → 41.5 → 42.3 → 39.1 → 38.26 ft** against an
>    observed **37.73 ft** — a **+4.57 ft** peak over-forecast and a textbook flip-flop (FACT, §12).
>
> 2. **Official or authoritative probabilities where they exist**, shown as *model probabilities* with
>    the model named. The NWS **HEFS** ensemble is live and machine-readable at all six configured
>    forecast points — **45 members** indexed by historical year 1981–2025, 6-hourly to 30 days, one
>    cycle per day — and is the only authoritative probability the platform can obtain today (FACT,
>    measured 2026-08-24). Three constraints:
>    - HEFS is **MODELED, not OFFICIAL_FORECAST.** Its endpoint is self-labelled experimental and it
>      omits the forecaster modifications that make the official forecast official. It is **not the
>      ensemble version of the official forecast**, and the platform must not imply the official crest
>      sits at any particular HEFS quantile.
>    - **A model exceedance fraction is computable only where the official threshold and the model
>      output share a unit.** HEFS serves flow only. At Mount Vernon, Carnation, Renton and Ferndale
>      the official categories are in **stage**, so the fraction is **absent with a reason** — the same
>      structural block that stops NWM category agreement — and the ensemble is displayed as a
>      hydrograph band. At Auburn and R Street, which are flow-defined, the fraction is computable.
>    - Any member fraction is reported with the **member count and the number of distinct member
>      values**. A fraction over identical members is arithmetic, not evidence — and the platform has
>      already met both failure modes: one distinct NWM crest across six members, and **zero HEFS
>      spread at lead 0**. A low measured spread is never rendered as confidence.
>
> 3. **Model agreement** (Surface IV below): a first-class signal.
>
> 4. **Cascade experimental hazard index**: only after hindcast evaluation demonstrates skill
>    (`TESTING.md` §7); until then the platform shows 1–3 and the susceptibility/forcing surfaces, and
>    does not print a Cascade-derived percentage. **Some strata will never become verifiable** and the
>    evaluation must be able to say so (§12C): minor flooding occurs on **0.16–0.77 % of days** at the
>    six points, and at Green near Auburn the *moderate* category has been exceeded **twice since
>    1990** on the instantaneous peak record while *major* has **never** occurred since the dam closed
>    in 1962.
>
> Thresholds are official NWS categories (action / minor / moderate / major), in stage or flow as NWS
> defines them per forecast point, with datum recorded. Reach-level thresholds without an official
> forecast point are a later, clearly-labeled derivation.
>
> **A stage threshold has a discharge vintage.** On an aggrading, levee-confined reach the discharge
> that produces the official stage category falls over time: at Mount Vernon the measured conveyance
> at flood stage has dropped roughly **9–11 % over the last three decades** (INFERENCE with strong
> physical corroboration — measured rating-independent pairs, the agency's own rating remark that
> older high-flow measurements were excluded "based on presumed control changes", a 1975→1999
> cross-section survey showing +1.5 ft of average bed, and a 66 % increase in the suspended-sediment
> rating slope at the same gauge). On the Nooksack at Ferndale, stage at a given peak discharge has
> risen **+0.139 ft per decade since 1968** (FACT, computed 2026-08-24), against non-glacial control
> gauges that are flat. The interface must never let a reader infer a fixed flow equivalent for a
> stage threshold, and a threshold carries its **hydraulic epoch** alongside its datum (§9A).

### 3.6 Replacement for §6 — Surface IV, Model agreement

> ## 6. Surface IV — MODEL AGREEMENT (meta-signal)
>
> Disagreement between NWPS (NWRFC), HEFS, NWM configurations, ensemble spread, and Cascade features
> is information, never averaged away. Agreement levels: HIGH / MODERATE / LOW / UNKNOWN, computed
> from crest magnitude, crest timing, and category differences, explained with the specific divergence
> ("NWM medium-range produces a stronger runoff response than the official forecast under similar
> basin QPF").
>
> **Four constraints the comparison must respect, each of which the corpus establishes:**
>
> - **The dominant upstream error is not a magnitude error.** Ensemble disagreement about atmospheric
>   rivers is structured, not isotropic: IVT spread is largest on the **poleward flank** of the AR
>   core, and operational models favour **northward** landfall-location errors on this coast (FACT).
>   An agreement metric computed only on crest magnitude and timing registers a latitudinal
>   displacement of the loading as ordinary spread. A `landfall_latitude_spread` driver is the honest
>   expression of it.
> - **Part of a forecast may be an observation.** NWM v3.1, operational 2026-08-18, assimilates USGS
>   streamflow observations into the beginning hours of the short-, medium- and long-range forecasts,
>   so "the initial forecast period overlapping with available observations will thus track observed
>   values" (FACT). Inside that assimilation tail, agreement between the NWM and a gauge is not
>   agreement between two forecasts and will read artificially high. The comparison window must begin
>   after the tail, and **the tail length must be measured, not assumed** (OPEN QUESTION).
> - **Ensembles of different sizes are different evidence.** HEFS (45 members, forcing uncertainty,
>   no initial-condition spread) and NWM medium-range (6 members, GFS-forced, observation-initialised)
>   are different objects. `3 of 6` and `22 of 45` must never be rendered as the same statement, and
>   every fraction carries a distinct-value count.
> - **Model version is part of provenance.** A stored series labelled with a module constant is wrong
>   the moment the producing model changes. The producing model version belongs on the row.
>
> Model skill is evaluated per basin and per regime (AR-driven rain, rain-on-snow, spring melt, summer
> low flow) as history accumulates — **with the qualification that at the regulated points the upper
> categories may never acquire a verifiable sample.** There the evaluation returns UNVERIFIABLE with
> the instantaneous event count (§12C), and the agreement surface is the only meta-signal available.
> Rain-on-snow will be the last regime to acquire a sample and carries the most model-structural
> uncertainty, because the operational snow model is a temperature index and the rain-on-snow energy
> balance is not (§7).

### 3.7 Replacement for §7 — Snow doctrine

> ## 7. Snow doctrine
>
> - **SWE is storage, not hazard — and the buffer is small.** More SWE can buffer a storm (cold, deep
>   pack absorbing rain) or amplify it (warm, ripe pack releasing meltwater); the sign depends on
>   temperature, pack state, and elevation distribution (FACT). The magnitude of the buffering side
>   must be stated with the claim, or "the pack can buffer the storm" reads as far stronger than the
>   physics supports: for a typical maritime pack the combined cold-content and liquid-water buffer is
>   **≈30–45 mm of water** (roughly 2.5 mm of cold content plus 27–37 mm of liquid retention; up to
>   ~60 mm at full saturation) against a **200–400 mm** atmospheric river. The pack absorbs roughly
>   **8–20 % of the storm and conducts the rest** (INFERENCE, arithmetic from measured liquid-water
>   contents). A cold, deep pack is genuinely different — 800 mm SWE at −5 °C forgoes ~25 mm of melt,
>   about sixteen hours at a strong rain-on-snow melt flux — so the sign flip is real, but the
>   buffering side is worth **hours to a day, not a storm**.
>
> - **Snowmelt is a minority of the water in a maritime rain-on-snow flood.** Across three
>   independent methods, snowmelt supplies on the order of **19–45 %** of the water reaching the
>   ground and rain supplies the rest; in the 26 largest storms at the closest long-record analogue
>   forest, **more than 60 % of storm precipitation fell as rain in every one** (FACT). No derived
>   feature may imply otherwise.
>
> - **Snowpack outflow has hard rate ceilings.** In maritime packs, net hourly outflow was below
>   **3 mm h⁻¹** for more than 97 % of the hours on the day before and the day of peak discharge,
>   total outflow below **10 mm h⁻¹**, and total **never exceeded 14 mm h⁻¹**; cumulative outflow over
>   a ten-day storm was under 300 mm (FACT). Any product implying tens of millimetres per hour of
>   snowmelt in a maritime event is wrong, and these are range-validation bounds on every derived melt
>   quantity.
>
> - **Precipitation phase involves three distinct elevations, routinely conflated.** The **freezing
>   level** is the height of the 0 °C isotherm in the free air. The **atmospheric snow level** is where
>   falling hydrometeors finish melting in a column — this is what the NBM `SNOWLVL` field is (a
>   wet-bulb crossing). The **mountainside snow line** is where the rain/snow boundary intersects the
>   terrain on a windward slope; it is the lowest of the three, and **it is the one that may be
>   intersected with hypsometry.** Working values, all to be stored as parameters with provenance,
>   never hard-coded:
>   - melting level ≈ free-air 0 °C altitude **− 200–400 m** (FACT — the observational basis a
>     peer-reviewed western Washington flood study uses, subtracting 300 m);
>   - a further **mesoscale/terrain depression of order 100–250 m** on a windward slope, which the
>     platform does not currently apply to `SNOWLVL` at all;
>   - total offset from the upwind free-air freezing level to the mountainside snow line therefore
>     roughly **250–450 m (800–1,500 ft)** in ordinary storms — which brackets the platform's existing
>     ~1,000 ft ASSUMPTION well.
>
>   **But the form is wrong, not just the value.** The offset **grows with precipitation intensity**
>   (the melting-distance term alone runs from ~60 m in weak precipitation to ~150 m at 3.5 mm h⁻¹ to
>   beyond 300 m in intense precipitation) and the storm-to-storm range spans a full kilometre (FACT).
>   A fixed offset is biased **exactly during the heaviest AR hours**, which is when the answer
>   matters most, and it biases the rain-exposed fraction **low**. The sensitivity is severe: a
>   modelled ~610 m in-storm snow-line rise **tripled runoff** in three mountain basins (FACT). This
>   is the single highest-leverage forecast quantity in a maritime flood.
>
>   Phase partitioning by air temperature alone is the wrong family of method: the 50 % rain–snow air
>   temperature threshold near the Pacific coast and Cascades is **0.6–1.5 °C, not 0 °C**, each 10 %
>   increase in relative humidity lowers it by **0.8 °C**, and humidity-aware or wet-bulb methods have
>   markedly lower variance in success rate than temperature-only methods (FACT).
>
> - **Rain-on-snow melt energy partitioning is contested, and the operational conclusion survives the
>   contest.** The honest statement is regime-dependent (all FACT): net radiation, dominated by
>   longwave from a warm saturated overcast, leads in the *event population* and in wind-sheltered
>   forest (**33–55 %** across three sites over eight years; **68 %** for the mountainous western US),
>   while turbulent sensible and latent fluxes dominate (**60–90 %**) in **wind-exposed extremes**.
>   Advected rain heat is a minor mass term (~7.5 % of the rain depth at ΔT = 6 K) and its energy
>   share ranges **<10 % to 44 %** — the high end being **persistent-melt events, which are the ones
>   that produce floods**. Condensation onto a melting pack releases about **7.5×** the energy needed
>   to melt the same mass, which is why humid, windy air is the dangerous combination.
>
>   **Therefore: temperature, humidity and wind at snowpack elevations are forcing inputs, not just
>   precipitation** — but the reason is that *turbulence is what makes an ordinary rain-on-snow event
>   an extreme one*, not that turbulence dominates in general. Neither wind nor dewpoint at pack
>   elevation is ingested today, which is why the forcing surface cannot represent rain-on-snow at all
>   (OPEN QUESTION, and a data gap rather than a science gap).
>
> - **Snow level rising does not remove snow.** It changes what falls on it. Melt requires an energy
>   balance; the visualization must never depict snow disappearing because the snow line moved
>   (`VISUAL_TRUTH_DOCTRINE.md`).
>
> - **A SNOTEL pillow that does not fall during a rain-on-snow event is not evidence that the pack did
>   not deliver water.** SWE can stay flat or rise across a rain-on-snow event through liquid
>   retention and intermittent snowfall, and water can reach the ground through preferential flow
>   paths occupying only **3–8 %** of the pack's cross-sectional area before the bulk cold content is
>   satisfied — highly stratified mid-winter packs have been observed to produce a *faster* outflow
>   response than isothermal ones (FACT). "Ripe or not" is not a binary gate on outflow.
>
> - **Basin hypsometry is the pivot** that turns a mountainside snow line into *rain-exposed basin
>   fraction* and, intersected with snow-covered area, into *rain-on-snow exposed fraction*. These two
>   fractions are the first derived snow features Cascadia Papsukkal computes (`ROADMAP.md` Phase 3),
>   and until 3DEP hypsometry exists — basin geometry is currently HUC8 unions — **every rain-exposed
>   and rain-on-snow-exposed statement is blocked.** This is the largest structural blocker in the
>   snow domain (OPEN QUESTION).
>
>   Note the sign of the error the platform is exposed to meanwhile. **Percent-of-median SWE is
>   misleading in the direction of calm**, which `DATA_DOCTRINE.md` §12 forbids: on 2025-12-11, the
>   day before the record Skagit crest, the twenty western-Washington Cascade SNOTEL sites **below
>   4,500 ft held 14 % of median SWE with ten of them reading exactly 0.0 in**, while the all-station
>   composite read **44 %** because three crest and leeward North Cascades sites sat at 128–174 % of
>   median (FACT, computed from NRCS AWDB 2026-08-24). A basin-mean percent-of-normal would have
>   concealed the entire hydrologic story of the event.
>
> - **Low SWE is unsigned; snow *drought state* is signed.** A **warm** snow drought (SWE at or below
>   the 30th percentile with accumulated precipitation *above* median) is a flood-relevant state
>   because the water arrived as rain; a **dry** snow drought (both below median) is not. WY2026 is
>   the textbook case: on 2026-04-01 the western-WA composite read 55 % of median SWE with accumulated
>   precipitation at **105–138 % of median at every station** (FACT). The platform currently has no
>   way to express "low SWE with above-normal precipitation is a positive susceptibility
>   contribution", so it emits nothing where the science supports something. Encoding it requires a
>   two-dimensional driver, not a scalar.
>
> - **Point observations (SNOTEL) are ground truth for their elevation and aspect; gridded products
>   (SNODAS) give spatial structure but assimilate those same points and have known biases in
>   maritime packs. Fuse; do not pick one.** The consequence of the point network's geometry is more
>   severe than a coverage note (FACT, computed 2026-08-24): of 31 active western-Washington sites the
>   median elevation is **3,900 ft**, only three sit below 3,000 ft and **one below 2,000 ft** — the
>   network is ground truth for a band **above** the one that makes the floods. Three basins are
>   effectively single-station; the Sauk's and the Stillaguamish's only sites have records beginning
>   in 2018 and 2020 and **AWDB returns no median for either**, so percent-of-median is *uncomputable*
>   in those two basins today. The Cascade crest is a hydroclimatic divide inside single basins: on
>   2025-12-11 maritime-side Skagit sites read 0–9 % of median while a crest site read 174 %.
>   Per-basin observing coverage — how much of the basin's hypsometry lies near a sensor — is a
>   first-class provenance fact, not a footnote.
>
> - **Recent fire in the flood-generating band is a measurable, mappable basin state.** In burned
>   forest, rain-on-snow events produced **14.3 mm d⁻¹ of meltwater against 6.2 mm d⁻¹ unburned**, and
>   a single event cost a high-elevation burned site **151 mm SWE against 39 mm unburned** (FACT,
>   western Oregon Cascades). The effect is larger than the classic clearcut effect and is trackable
>   from public fire perimeters. **Plot-scale clearcut amplification, by contrast, does not scale to
>   the basin** and must never be a basin-level term: it is worth 20–40 % on melt at a *point*, but
>   post-logging increases in >1-year peaks were only 10–20 % in small basins and "small basin peaks
>   do not account for the magnitudes of large basin rain-on-snow peak discharges" (FACT).
>
> - **Phase interference is the most promising unexploited signal in the domain, and is unmeasured
>   here.** In the largest maritime floods, precipitation pulses and snowpack-outflow pulses are
>   nearly in phase across multiple timescales for several days; in moderate floods they are half a
>   cycle out of phase and interfere destructively. Only 7 of 26 storms had continuous net snowpack
>   outflow and only 2 of those produced extreme floods (FACT). Whether the signal exists at the scale
>   of a 500–3,000 mi² Washington basin, or is a 64 km² phenomenon, is an OPEN QUESTION and no
>   operational product represents it.

### 3.8 Replacement for §8 — Soil doctrine

> ## 8. Soil doctrine
>
> - The useful quantity is **remaining storage**, not a binary "saturated" — and the response to
>   filling it is a **threshold, not a trend**. As storage fills, saturation-excess runoff generation
>   expands (variable source areas), interflow accelerates, and a given rainfall produces a larger,
>   faster hydrograph (FACT for forested PNW soils). The expansion is gated: published
>   storm-precipitation thresholds for significant subsurface stormflow run **18–60 mm**, with
>   **30 mm** measured at the closest western-Cascades analogue site and **55 mm** at the canonical
>   hillslope, above which subsurface stormflow was **more than 75× larger** (FACT). The threshold is
>   a property of the storage deficit, not of the storm: the same 60 mm is sub-threshold on a drained
>   hillslope and super-threshold on a primed one. **No basin-scale threshold has been published for
>   any Cascadia basin** (OPEN QUESTION; it is estimable from gridded QPE plus the stored hydrographs).
>
> - **Infiltration-excess (Hortonian) overland flow is negligible here, and this is what licenses
>   reasoning about duration rather than intensity** (ASSUMPTION, with a measured anchor): soil
>   infiltration capacity in western Cascades forest exceeds **200 mm h⁻¹** against a maximum
>   precipitation intensity of about **10 mm h⁻¹** — a factor of roughly twenty (FACT). The exceptions
>   are roads, compacted ground and impervious surfaces, which are the only Hortonian surfaces in the
>   landscape. Runoff generation is **saturation-excess and subsurface**, and at basin scale what
>   distinguishes an extreme is not how much rain fell but **how much of the basin crossed threshold
>   at the same time** — hourly intensity in the largest western-Cascades floods was only
>   **2.7 ± 0.9 mm h⁻¹** (FACT). Duration and simultaneity, not rain rate.
>
> - **The store is small and it fills early.** The wet-season dynamic store — the entire water volume
>   separating a normally wet basin from a flood-generating one — is **71–104 mm** in the unregulated
>   western Washington basins, one to two days of atmospheric-river precipitation, and those basins
>   completed their autumn wet-up **between 1 October and 5 November in every water year of
>   WY2020–2024** (FACT, computed 2026-08-24). In a forested western-Cascades catchment the
>   transpiration deficit refills in an average of **48 days** after the onset of winter rains (FACT).
>   The consequence is that "remaining storage" is near zero for most of the flood season, which makes
>   it a **poor discriminator within the season and a good one at its margins** — October events,
>   March–May events, and the aftermath of an anomalously dry autumn (INFERENCE).
>
> - **No single product observes basin soil water, and the products the doctrine has previously named
>   are not all available here.** Measured against the platform's own basin list (FACT, NRCS AWDB
>   queried 2026-08-24): SNOTEL soil moisture is registered at **zero** stations in the Stillaguamish,
>   Skykomish/Snohomish, Snoqualmie and Green basins and **none in the Sauk** — the gauge the Skagit
>   susceptibility surface actually reads; the single Nooksack station returned nothing at all before
>   2025-12-12, i.e. through the entire lead-up to the record flood, and 51 days of physically
>   impossible 0.0 % readings; the Cedar's registered station returned **no data at all** over a
>   123-day window. This is a permanent constraint on method selection, not a plumbing problem.
>   Satellite root-zone products are also poorly matched: the leading assimilation product's own
>   accuracy requirement **excludes snow, frozen ground, mountainous topography and high-water-content
>   vegetation**, which describes the Cascades in winter (FACT).
>
>   The platform therefore fuses what it can defend: **modeled soil moisture from the national land
>   model, against its own 44-year 1 km retrospective climatology**; an **antecedent precipitation
>   index** and a **90-day standardized index** from a gridded forcing archive; point probes where a
>   station genuinely reports; and the streamflow-derived storage proxy of §8A. Each contributes a
>   percentile; **disagreement between them is reported, not averaged** — that disagreement is the
>   platform's honest expression of the hysteresis below. The comparative literature ranks the
>   estimator families **soil-moisture-accounting bucket (R² 0.90) > API (0.82) > antecedent discharge
>   index (0.67) > fixed 5-day antecedent rainfall (0.19)** against a calibrated storage deficit
>   (FACT), so the flow percentile is *a* recognised proxy, not *the* standard one.
>
> - **Storage–discharge is hysteretic, and a percentile with no limb context is under-specified.**
>   Storage rises on one trajectory during wetting and falls on another during recession; the loop can
>   even reverse direction as antecedent wetness increases (FACT). On the rising limb a flow
>   percentile **understates** storage and on the recession limb it **overstates** it — so a basin can
>   be near its connectivity threshold while its river is still low, which is precisely the state in
>   which a susceptibility surface would earn its keep (INFERENCE). Every susceptibility read carries
>   a rising/falling flag.
>
> - **Percentiles require climatology, and a climatology is not a number until it carries its
>   vintage, its sampling interval and its homogeneity** (§12A). The platform builds its own from
>   stored history and, until enough history exists, labels percentiles as derived from the product's
>   own reanalysis with the period stated — and additionally records the **regulation epoch**, because
>   a percentile at a regulated gauge is a percentile of *managed* flow. Ninety-nine percent of the
>   Mount Vernon annual peak record carries the USGS "discharge affected by regulation or diversion"
>   qualification (FACT).
>
> - **Never display a pre-event-water fraction or any old/new-water claim.** Storm flow in humid
>   forested catchments is dominated by water that was already in the basin, and the mechanism —
>   pressure-wave propagation, not the transport of the falling rain — is why the hydrograph responds
>   in minutes to water that is months old. But the measured spread of event-water fraction across the
>   literature is nearly the whole 0–100 % interval and moves with wetness, intensity and land cover
>   (FACT). It is not measurable operationally here and must not be rendered.

### 3.9 Replacement for §9 — River / hydraulic doctrine

> ## 9. River / hydraulic doctrine
>
> - Stage and discharge are different observations related by a site-specific rating curve that USGS
>   shifts and revises (FACT). Store both; **never derive one from the other in the platform.** The
>   numbers that make this non-negotiable at the platform's own primary forecast point: the
>   stage–discharge scatter about a log-discharge fit at Skagit near Mount Vernon has a standard
>   deviation of **0.68 ft** and a residual range of **4.08 ft** across 85 paired annual peaks, and
>   the record contains a direct inversion — **138,000 cfs at 33.85 ft in 2006 against 127,000 cfs at
>   36.99 ft in 2021**, more flow at 3.14 ft lower stage, fifteen years apart. NWS category spacing
>   there is **2 ft**. The current rating is **extrapolated above about 125,000 cfs**, beyond any
>   current-meter measurement (all FACT, computed or read 2026-08-24).
>
> - **Vertical datums**: stage is relative to gauge datum; thresholds are defined on that gauge's
>   datum. Record the datum on every stage series and every threshold; comparisons across unrecorded
>   or mismatched datums are refused, not approximated (V1 lesson, `V1_AUDIT.md` §4.5). Three
>   extensions the corpus forces:
>   - **The refusal applies within a single station's history.** The USGS annual-peak stage series at
>     Snoqualmie near Carnation — a configured susceptibility gauge — contains a **41.26 ft
>     discontinuity** between the 1939 and 1940 water years (FACT). A stage series spanning two datum
>     epochs may not be aggregated into one climatology.
>   - **Tidal datums are a different family** (MLLW, MHHW, MHW, station datum) with a published epoch,
>     and are not geodetic datums. Four Puget Sound stations the platform would need have **no
>     published NAVD88 tie**; converting a tidal datum to a geodetic one there requires a transformation
>     tool, not arithmetic (FACT). See §10A.
>   - **Reservoir pool datum is CONFIGURED per project, sourced from the water control manual or the
>     licence, never from the feed.** Every USACE A2W series in scope returns `vertical_datum: NGVD29`,
>     which contradicts the projects' own documents — Upper Baker's constants are stated in NAVD88 and
>     Ross's in a project datum 1.79 ft above NGVD29 (FACT). The field appears to be a service-wide
>     default and must not be trusted.
>
> - **Hydraulic headroom** is expressed three ways, each labeled:
>   - **stage headroom**: `threshold_stage − current_stage` (datum-checked) — the more robust basis
>     during a fast rise, because it does not inherit the rating loop, but on an aggrading reach it
>     carries a **conveyance-drift uncertainty** (§9A) and on a tidal reach it is meaningless without
>     de-tiding (§10A);
>   - **flow headroom**: `threshold_flow − current_flow` (the only valid form on flow-defined points)
>     — which inherits unsteady-flow hysteresis, and on a **regulated reach is headroom under a
>     release decision that can change on the next forecast cycle**, so it is displayed beside the
>     reservoir's own `hours_to_top_of_flood` or suppressed (§10);
>   - **time-to-threshold**: headroom ÷ current rate of rise, with the rate's window and the caveat
>     that rise is nonlinear — an indicator, not a prediction. The physically motivated denominator
>     scale is the basin's own **recession time constant τ(Q)** (§8A), not a hand-chosen window.
>
>   **Unsteady flow puts a floor under discharge uncertainty** before any rating error. Under a flood
>   wave the rating is not single-valued: the rising limb carries more discharge at a given stage than
>   the falling limb, and the loop widens as bed slope flattens. Applying the standard correction to
>   the December 2025 Mount Vernon hydrograph with a physically consistent celerity gives a total loop
>   width of about **1.6–3.4 %** of discharge (INFERENCE). That is the floor; the measured falling-limb
>   deviation on that event was larger (−5.9 % against the published rating) on a single
>   *Fair*-rated measurement whose own stated uncertainty is 8 %, which is itself the finding.
>
> - Rate of rise and acceleration are computed over named windows (1 h, 3 h, 6 h) from stored history
>   with gap handling; **trend never comes from the two endpoints of a response window.** (This
>   sentence is correct and unchanged. It is also currently violated by the implementation, which
>   computes `(last − first) / span`; that is a code defect to be fixed, not a doctrine to be
>   softened.)
>
> - **Routing**: upstream/downstream relationships come from NWPS `upstreamLid`/`downstreamLid` and
>   NHDPlus/NWM topology; travel time is estimated from history (crest-to-crest lag) and from NWM, and
>   carried as a distribution. That distribution now exists for the reach that matters most —
>   Concrete → Mount Vernon, **median 16.9 h, sd 3.5 h, range 9.5–23.8 h** over twelve events
>   2003–2025 (FACT) — and it should be seeded rather than guessed. Two properties must travel with
>   it:
>   - **Crest-to-crest lag is not wave celerity.** The implied crest speed on that reach is
>     **2.2–5× below** the kinematic celerity implied by the reach's own documented in-channel
>     velocities, so the lag is a *storage-and-local-inflow statistic*, not a wave speed (INFERENCE).
>   - **The lag appears to lengthen with flood magnitude** (r = +0.65; 17.0 h for peaks ≥100,000 cfs
>     against 14.5 h below), which is the opposite of kinematic expectation and is the signature of
>     storage engagement. It is carried as **INFERENCE, not FACT**, because USACE's own documentation
>     states the reach's *hydraulic* travel time **shortens** with discharge, and because timing a
>     broad crest by its maximum is not a robust timestamp.
>
> - **A falling stage during a rising upstream hydrograph is an anomaly, not an improvement.** It is
>   the documented signature of a downstream breach or spill on this exact reach: the Fir Island levee
>   failure below Mount Vernon in November 1990 "increased the river slope and velocity below Mount
>   Vernon, causing an artificially low crest stage at the Mount Vernon gage" (FACT). The platform
>   detects and surfaces this as a `conveyance_anomaly` with `quality=suspect` and a reason; it is
>   never smoothed, never read as basin behaviour, and never used in a rate-of-rise.
>
> - **Conveyance thresholds on a reach are CONFIGURED display context, never inputs to a hazard
>   number.** For the lower Skagit, bankfull at Mount Vernon is about **130,000 cfs** and above
>   **146,000 cfs** flow escapes the right bank through Burlington toward the Samish (FACT). Storage
>   cells attenuate only until they are full: in one historical flood the peak was held for six hours
>   at Mount Vernon and "the duration of this peak was more significant than its magnitude because it
>   minimized the effectiveness of natural storage" and the dikes then failed from prolonged high
>   water (FACT). Duration beats magnitude on this reach.
>
> - **Regulated reaches**: headroom below a flood-control dam depends on the operator's release plan;
>   the platform shows the reservoir surface (§10) beside the reach and never presents natural-flow
>   reasoning on a regulated reach without the regulation flag.

### 3.10 Replacement for §10 — Reservoir, dam and flood-defense doctrine

> ## 10. Reservoir, dam and flood-defense doctrine
>
> - Reservoirs are first-class entities with: pool elevation and **its datum, configured per project
>   from the manual or licence**, storage, flood-control pool bounds (seasonal rule curve), inflow,
>   outflow, rate of change, operator, data source and freshness — plus the four attributes that bound
>   what the project can do: **control fraction** at its named control point, the **control point**
>   itself, the **objective flow** the operator regulates to, and the **travel time** from the dam to
>   that point.
>
> - **Flood buffer is three volumes, not one**, and the difference between them is the difference
>   between a reassuring number and a true one:
>
>   ```
>   required_buffer   = S(rule_curve_elevation_today) − S(pool_now)     # may be NEGATIVE: encroached
>   available_buffer  = S(top_of_flood_elevation)     − S(pool_now)     # what physically remains
>   pool_below_curve  = max(0, S(rule_curve_today)    − S(pool_now))    # discretionary, not obliged
>   ```
>
>   `required_buffer` is rendered **signed and never clipped**; when it is negative the operators' own
>   word is *encroachment*, and the display says "encroached into the flood pool by N ft", not
>   "N % full". `available_buffer` is the only one that answers "how much more can it hold".
>   `pool_below_curve` is buffer the operator is not obliged to have and may spend on power or water
>   supply at any moment; it is labelled **discretionary** and never added to `required_buffer`
>   without saying which part is which.
>
>   **December 2025 is why.** Measured from the primary series (FACT, computed 2026-08-24): Ross
>   entered the storm about **7.6 ft below its rule curve** and absorbed **110,900 acre-feet — 92 % of
>   a full design flood pool** — while occupying only **≈22 % of its *designated* flood pool**. A
>   gauge reporting "percent of flood pool used" against the rule curve alone would have shown a
>   quarter-full reservoir during the most consequential regulation event in the basin's modern
>   record. Upper Baker absorbed **53,194 acre-feet**, 72 % of its allocated pool, at ≈5.9 % of its
>   designated pool.
>
>   The companion rate quantity, directly analogous to time-to-threshold:
>   `hours_to_top_of_flood = available_buffer ÷ net inflow`, over a named window, UNKNOWN when net
>   inflow is not positive, and **always carrying "assumes present release continues" — because it
>   does not.** Howard Hanson bottomed at about **33 hours** on 2025-12-12 (INFERENCE, computed).
>
> - **Derive storage from elevation; keep the provider's storage series beside it, never inside the
>   same arithmetic.** Pool **elevation** is the primary observable; the project's elevation–storage
>   table is a versioned CONFIGURED artifact with its survey date; storage is DERIVED with lineage.
>   The reason is measured: at Howard Hanson's December 2025 peak the reported elevation **rose** while
>   the reported storage **fell**, which a single-valued capacity curve cannot do; and the live series
>   sits **3.3 %** (Howard Hanson) and **7.2 %** (Mud Mountain) below the manuals' tables at the same
>   elevation (FACT). USACE's own press release used the table where the live series says otherwise.
>   When the two disagree beyond a declared tolerance that is a **disagreement assessment about the
>   reservoir**, not an error to hide.
>
> - **The rule curve is a published, machine-readable seasonal function**, not something to be
>   reconstructed by polling — and the live curves **disagree with the published manuals** at two
>   projects: Upper Baker's live curve requires its full flood storage from early **October** rather
>   than from 15 November, and Howard Hanson's live winter curve reads a different elevation from its
>   2011 manual (FACT, fetched 2026-08-24). Seed the curve from the authoritative seasonal array, treat
>   the summary value as a rounded cross-check, and **snapshot it daily as a change-detection record on
>   a policy artifact** — because the array carries no version history, so a revision is otherwise
>   invisible at a past knowledge time.
>
> - **The platform never infers dam operations; it reports them** — and it distinguishes three states
>   of knowledge:
>   - **Inflow forecasts are published** for several projects as ordinary NWPS gauge objects and are
>     OFFICIAL_FORECAST. But two of the largest allocated flood pools in scope currently serve an
>     **empty `data` array behind a live-looking metadata block with a three-week-old issuance time**
>     (FACT, 2026-08-24). That is exactly the shape that silently renders as "no flood risk". The
>     ingest must distinguish **forecast absent** from **forecast of low flow**, and treat issuance age
>     as a first-class staleness signal.
>   - **The release dimension is UNKNOWN by construction.** Forecast pool trajectories are catalogued
>     server-side and return no values on any public path tested; until that changes, the reservoir's
>     future release is UNKNOWN with the reason stated.
>   - **The official downstream forecast at a regulated point already embeds an assumed operating
>     plan** made by the RFC in coordination with the Corps. The prohibition on *inferring* operations
>     stands; the disclosure that the official forecast is **conditional on an unpublished operating
>     intention** must accompany it.
>
> - **Section 7 status is a knowable, time-stamped state of a reservoir** — "Corps-directed" versus
>   "owner-directed" — with a named legal basis, and it changes the meaning of every release. On the
>   Skagit it flipped on 2025-12-08 and again on 2025-12-15. **There is no public feed for it**
>   (OPEN QUESTION); it defaults to UNKNOWN with a reason and is CONFIGURED when a dated agency
>   statement exists.
>
> - **At sufficiently extreme forcing a flood-control reservoir stops attenuating and approaches
>   pass-through.** The effectiveness curve is a hump, not a plateau: on the Skagit the modelled peak
>   reduction at Concrete runs **0 % at the 2-year event, a maximum of ~18 % near the 25-year event,
>   and back to ~11 % at the 500-year event**, and at Mount Vernon the 100-year reduction is only
>   ~12.6 % because 61 % of the contributing area enters below the dams (FACT and arithmetic on the
>   authoritative study's own table). Both Corps manuals in scope carry a discharge regulation schedule
>   that raises releases earlier precisely to prevent a premature fill, and the design-flood routings
>   pass most of the inflow. This is why **"the dam will hold" and "the dam will protect us" are
>   different claims, and the platform makes neither** (§13). Successive official studies have moved
>   the regulated 100-year flow at Concrete by **26,000 cfs (12 %) in nine years with no change to the
>   dams** (FACT) — a reminder that these are model outputs with vintages.
>
> - **Evacuating the pool is as rule-bound as filling it, and the binding constraint is the next
>   storm.** Water in flood-control space must be evacuated as rapidly as can be safely accomplished
>   without exceeding controlling downstream rates; on the Skagit, evacuation of one project must not
>   push the control point back above its peak or create a secondary peak. Therefore **a reservoir's
>   remaining buffer during an AR family is a function of the next storm's forecast, not only of the
>   current one** (INFERENCE). December 2025 was six AR pulses over nearly two weeks.
>
> - Levees, dikes, floodwalls and channel works are displayed with their authoritative attributes
>   (National Levee Database, local districts) and never as guarantees. A design height is a design
>   height. **And a levee failure changes the gauge reading itself** — the observability clause, not
>   just the disclaimer: a breach steepens the local water-surface slope so the gauge upstream of it
>   *falls* while the flood is still rising (§9). A stage record from a breach-affected event is not
>   comparable to one from an intact event, and the platform records which it is.

### 3.11 Addition to §11 — Explanation doctrine

*The existing §11 stands unchanged. One sentence is added at the end.*

> [unchanged: "Every change in a surface is attributable to named features … If an LLM is ever used to
> verbalize, it verbalizes the structure and is labeled."]
>
> **Identifiers are not interpretations.** Where an ensemble member carries a historical year as its
> index, that index is a rank-ordering label produced by the ensemble's own construction, not an
> analogue of that year's weather. The explanation layer may print the index — "12 of 45 members
> exceed …" — and must not describe a member as "the 1990 analogue" or attribute a historical year's
> meteorology to it.

### 3.12 Replacement for §12 — Historical intelligence and hindcasting

> ## 12. Historical intelligence and hindcasting
>
> The defining test of every intelligence output is: *what would Cascadia Papsukkal have shown at time
> T with only what was knowable at T?* The platform therefore stores, for every value, its **knowledge
> time** (`available_at` — when it was retrievable, not merely when it was valid), keeps superseded
> forecasts, and keeps revised observations as revisions. Replays use knowledge time exclusively.
>
> **Knowledge time is necessary and not sufficient.** Four look-ahead channels escape a timestamp
> filter, and all four are live for this platform:
>
> - **the reference distribution.** A day-of-year ladder rebuilt annually is *the same method version
>   with different inputs*, so a replay that reads today's ladder is ranking a 2025 value against a
>   baseline that did not exist in 2025. Given a measured 4–8 percentile-point sensitivity to a single
>   decade of ladder data, this is a real bias. `as_known_at(T)` must select the ladder whose own
>   `available_at ≤ T` (§12A).
> - **product version.** Reprocessing of a forcing or analysis archive arrives as new rows with honest
>   knowledge times and is still not what existed at T. The defence is **version pinning**.
> - **model version.** NWM v3.1 became operational on 2026-08-18; any archive spanning that boundary
>   silently mixes two models. Every forecast row carries its producing model version, and a hindcast
>   crossing a boundary either refuses or declares the split.
> - **archive survivorship.** The HEFS API retains roughly ten cycles and NWPS a handful of forecasts.
>   A purged cycle is **invisible**, not `quality=missing`, unless the platform archives it or records
>   the gap.
>
> ### Event Zero — December 2025
>
> Event Zero is the December 2025 flood. It was **an atmospheric river family, not a single event**:
> three ARs across 3–5, 7 and 8–11 December, with roughly 96 hours of AR conditions across the family
> span. Under the AR scale's own definition an AR event is **one continuous period** of AR conditions
> at a point, so a category may not be applied to the family, and the per-AR categories and the
> inter-event gaps are recorded separately (FACT). The categories reported for this event came from
> published imagery with no machine-readable source and are stored as CONFIGURED-from-narrative, not
> as a derived AR scale value.
>
> Snow levels were 6,000–9,000 ft and the maritime snowpack was effectively absent below the storm's
> snow line: on 2025-12-11 the twenty western-Washington Cascade SNOTEL sites **below 4,500 ft held
> 14 % of median SWE with ten reading exactly 0.0 in**, while the all-station composite read 44 %
> (FACT). The response was **rain on wet soils, not snowmelt** — the textbook antecedent-moisture
> flood, and the cleanest possible test of the susceptibility surface.
>
> **The Skagit at Mount Vernon crested at a preliminary record 37.73 ft / ~133,000 cfs on 2025-12-12
> 08:15Z**, above the 1990 record of 37.37 ft despite a lower flow (~152,000 cfs in 1990). Three
> qualifications must travel with that comparison or it teaches a stronger drift than the evidence
> supports (all FACT): the **1990 stage is breach-depressed** — the Fir Island levee failed twice in
> November 1990 and USACE attributes an "artificially low crest stage at the Mount Vernon gage" to it;
> the December 2025 peak is **preliminary and is not yet in the USGS annual peak series**, so "record"
> must name which series and which approval state; and the measured conveyance drift at flood stage is
> **9–11 % over roughly three decades** (population-level, −4.4 % in flow at 37 ft), **not the ~29 %**
> a two-point comparison against a 1906 indirect estimate suggests.
>
> Snohomish at Snohomish and Cedar at Renton also set records. **The Snohomish record is a compound
> quantity**: that gauge transmits 0.831 ft of stage per foot of Seattle tide at low flow (§10A). On
> the day it crested, the tide was **6.64 ft below MHHW**.
>
> **The coastal boundary was benign, and that fact must be stored with the event.** All three record
> crests occurred at **4.8–6.6 ft below MHHW**, the largest skew surge on any tidal cycle in the whole
> AR sequence was **+1.17 ft**, and the surge on the tidal cycle containing the Mount Vernon crest was
> **−0.03 ft** (FACT, computed 2026-08-24). Had the same crest arrived on that water year's highest
> predicted tide with a 99th-percentile winter skew surge, the downstream boundary would have been
> about **8 ft higher**. Without this recorded, any skill score computed on Event Zero silently
> assumes a benign coastal boundary and will mislead the first time an AR crest lands on a king tide.
>
> **Regulation dominated the Green, White/Puyallup and Skagit outcomes — within a bound that must be
> stated.** Ross withheld **99.2 % of inflow at the instantaneous peak** (50,099 cfs in, 389 cfs out),
> and **event-integrated passed roughly 20 % of the inflow volume**; the "~99 %" figure is an
> instantaneous one and must be labelled as such. Howard Hanson reached a record pool of 1,189.3 ft;
> its live storage series reads **75,171 acre-feet** where the agency's release used the capacity
> table's **77,700** — a 3.3 % disagreement reported, not reconciled. The bound is control fraction:
> the dams command **39 %** of the drainage area at Mount Vernon, **55 %** above Auburn and **42 %**
> at Puyallup, and the Skagit system holds the lower valley below damage only to about the 20–25-year
> event.
>
> **The forecast record is the platform's first consistency benchmark.** The first NWS Seattle Flood
> Watch was issued 2025-12-05 16:10 PST, about 2.5 days before the main AR and 6.5 days before the
> Mount Vernon crest. The Mount Vernon forecast crest then evolved **36.9 → 41.5 → 42.3 → 39.1 →
> 38.26 ft** before the 37.73 ft observation — a **+4.57 ft peak over-forecast** and a textbook
> flip-flop (up 4.6, up 0.8, down 3.2, down 0.8). Consistency is a **separate axis from accuracy** and
> is verified separately (§12C); a panel that shows the trace is showing data, and a panel that also
> quantifies the revision magnitude relative to spread is showing information.
>
> **And the surfaces themselves must be replayed, not just the inputs.** Replayed with a climatology
> excluding 2025, the susceptibility surface would have read **LOW in four of six basins on 3–4
> December** and **MODERATE in all six on 5 December** — the day of the official Flood Watch. It first
> read VERY HIGH on 8–10 December, when the rivers were already in flood. The signal was in the
> derivative: the Sauk moved **64 percentile points in 48 hours**.
>
> December 2025 was also a large **landslide** event — roughly 750 slides catalogued across Whatcom,
> Skagit and Snohomish counties, with field response concentrated near Concrete and Darrington — which
> belongs in the evidence set as context, not as a hydrologic signal.
>
> Every one of these facts is an evidence row for the hindcast dataset described in `EVENT_ZERO.md`;
> reconstruction tasks are in `ROADMAP.md` Phase 6.

### 3.13 Replacement for §13 — What Cascadia Papsukkal will not claim

> ## 13. What Cascadia Papsukkal will not claim
>
> - A probability without a calibrated, hindcast-evaluated method behind it. At base rates of
>   0.16–0.77 % of days, a probability that has not passed a reliability check with a stated sample
>   size is not merely unproven — it is very likely uncheckable with the data the platform will hold
>   for years.
> - **A recurrence interval, return period or annual exceedance probability for any reach.** Frequency
>   estimates are fitted statistics with a record period, a method version, a regulation status and a
>   confidence interval — not properties of a river (§12B).
> - Flood depth, inundation extent or water-surface elevation without an authoritative model.
> - That a levee or dam "will hold" — and, equally, that a reservoir is **"protecting"** a place. The
>   Corps' own manuals state that total control of all floods is impossible at control fractions of
>   42–55 %. The platform also never displays a **"damages prevented"** figure: these are
>   estimation-class numbers dominated by assumed inventory and price level, not comparable across
>   vintages, and advocacy-adjacent.
> - **An atmospheric-river category sourced from imagery.** A category read off a picture has no
>   `valid_time`, no `issued_at`, no model identity and no unit, and cannot satisfy `DATA_DOCTRINE.md`
>   §1. Where the platform shows a category it computes it, badges it DERIVED/EXPERIMENTAL, and
>   carries the detector's parameters — or it shows none.
> - **A modelled or forecast geomorphic hazard.** The platform will not model lahars, glacial outburst
>   floods, landslide-dam outbursts or post-fire debris flows. It displays the responsible agency's
>   product verbatim and links to it (§9A).
> - **A complete river stage forecast at a tidally influenced point when the source model does not
>   carry the coastal boundary condition** (§10A). Said carefully, and without implying the official
>   forecast is wrong.
> - **A climate projection, or an attribution of any individual event to climate change.** The
>   platform states the vintage, the period and the sampling interval of every reference distribution
>   it ranks a live value against, so that a reader can see the baseline move without the platform
>   claiming to have measured why (§12A). Century-scale projections cannot carry a knowledge time,
>   cannot be verified at a 6–120 h lead, and may not enter a threshold, a percentile, a band edge or
>   a hazard computation.
> - That a source is current when it is stale, or official when it is configured — including the case
>   where a provider serves an **empty payload behind a live-looking metadata block**, which is a
>   staleness event and not an absence of hazard.
> - Any evacuation, warning or life-safety instruction. Those come from NWS and emergency management;
>   Cascadia Papsukkal links to them and labels them OFFICIAL.

### 3.14 Additions to §14 — Glossary

*Existing entries stand unchanged. The following are added, and the `snow level` entry is replaced by
three distinct entries.*

> | Term | Definition |
> |---|---|
> | freezing level | elevation of the 0 °C isotherm in the free atmosphere |
> | melting level | elevation at which falling hydrometeors finish melting; observed 200–400 m below the free-air 0 °C isotherm |
> | atmospheric snow level | column-based rain/snow transition height as a model reports it (e.g. a wet-bulb crossing); **not** a terrain intersection |
> | mountainside snow line | elevation at which the rain/snow boundary intersects the terrain on a windward slope; the lowest of the three, and the only one that may be intersected with hypsometry |
> | upslope IVT (IVT⊥) | integrated vapour transport projected onto the terrain gradient in the direction of the flow |
> | non-dimensional mountain height (M) | `M = N h / U`, the inverse Froude number; blocking is favoured when M > 1 |
> | AR family | a cluster of atmospheric rivers landing within a regional aggregation window (commonly 5 days), typically 2–6 ARs |
> | sensitivity function `g(Q)` | `dQ/dS`, the change in discharge per unit change in basin storage, recoverable from recession behaviour |
> | recession time constant `τ(Q)` | `1/g(Q)`; the basin's physical response time scale at a given flow |
> | dynamic storage | the water volume between two chosen flows, obtained by integrating `1/g(Q)` |
> | storage limb | whether the basin is on the wetting or drying trajectory of its hysteretic storage–discharge relation |
> | runoff regime | mountain-subsurface / lowland-till / outwash / urban-impervious, per basin or sub-basin |
> | sediment regime | volcanic-glaciated / glaciated-non-volcanic / non-glacial, per basin; display only |
> | rating epoch / hydraulic epoch | the period over which a gauge's stage–discharge relation is treated as homogeneous |
> | conveyance drift | measured change in stage at a fixed discharge, in ft per decade |
> | tidal class | measured category of a forecast point's tidal transmission: TIDAL / TIDALLY_MODULATED / MARGINAL / FLUVIAL / UNKNOWN |
> | skew surge | maximum observed water level in a tidal cycle minus the maximum predicted water level in the same cycle, regardless of timing |
> | control fraction | share of the drainage area above a control point that lies above a regulating gate |
> | encroachment | pool elevation above the rule curve, i.e. a negative required buffer |
> | snow drought (warm / dry) | SWE at or below the 30th percentile with accumulated precipitation respectively above / below median |
> | AEP | annual exceedance probability; the reciprocal of a return period |
> | ladder vintage | the reference period and build date of the day-of-year climatology a percentile was computed against |
> | UNVERIFIABLE | an evaluation verdict for a stratum with too few observed events to support a skill number |

---

## 4. Full text of every proposed NEW section

### 4.1 NEW §8A — Catchment sensitivity, connectivity and response time

*Insertion point: immediately after §8 (Soil doctrine). This section exists because the corpus
identified a quantity the platform can compute today, from data it already ingests, with a published
peer-reviewed method and a per-basin fit statistic — and currently does not.*

> ## 8A. Catchment sensitivity, connectivity and response time
>
> The platform cannot observe basin storage. It can observe discharge. Under the assumption that
> discharge is a single-valued function of storage — the assumption that already licenses using a flow
> percentile as a wetness proxy (§8) — the basin's *sensitivity* to an additional millimetre of
> storage is recoverable from its own recession behaviour, with no new data source (FACT — Kirchner
> 2009, and the reference implementation in `docs/research/corpus/runoff-generation.md` §5.4):
>
> ```
> dS/dt = P − E − Q                      mass balance
> Q     = f(S)                           single-valued storage–discharge relation
> g(Q)  ≡ dQ/dS = f′(f⁻¹(Q))             the sensitivity function
> g(Q)  ≈ (−dQ/dt) / Q                   during recession, when P ≪ Q and E ≪ Q
> τ(Q)  = 1 / g(Q)                       recession time constant
> ΔS    = ∫ dQ / g(Q)                    dynamic storage between two flows
> ```
>
> **Measured for the platform's own basins** (FACT, computed 2026-08-24 from five water years of USGS
> instantaneous discharge, Nov–Mar recessions):
>
> | Gauge | Regulation | `b − 1` (≈ the exponent of `g`) | τ at 1 mm h⁻¹ | dynamic store | gain `g(1.0)/g(0.1)` |
> |---|---|---|---|---|---|
> | Sauk near Sauk | none | 1.05 | 17.5 h | 74.9 mm | 11.1× |
> | Skykomish near Gold Bar | none | 0.91 | 25.3 h | 95.9 mm | 8.2× |
> | NF Stillaguamish near Arlington | none | 0.98 | 17.7 h | 71.1 mm | 9.5× |
> | Snoqualmie near Carnation | negligible | 0.88 | 28.1 h | 103.9 mm | 7.6× |
> | Skagit near Mount Vernon | upper basin regulated | 0.67 | 42.2 h | 136.3 mm | 4.7× |
> | Cedar at Renton | partial | 0.17 | 115.7 h | 335.2 mm | 1.5× |
> | Green near Auburn | Howard Hanson | −0.06 | 263.6 h | 786.5 mm | 0.9× |
>
> Five statements the platform is licensed to make from this, and three it is not.
>
> **Licensed:**
>
> 1. **The maritime storage–discharge form is transferable and near-linear in sensitivity.** The
>   unregulated basins sit at `g(Q) ∝ Q^0.85–1.05`, statistically indistinguishable from the maritime
>   upland catchments where the method was developed.
> 2. **The gain is the quantitative content of "antecedent conditions matter" for these basins:**
>   **7.6–11.1×** across the wet-season flow range. It is a *gain*, not a probability, and it is
>   monotone in discharge, so a banding built on it stays reproducible while its edges acquire a
>   physical meaning ("sensitivity ≥ 5× the seasonal median") instead of meaning "the flow is unusual".
> 3. **The response time scale is basin-specific and measurable**, and it is the honest denominator for
>   rate-of-rise and time-to-threshold (§9) rather than a hand-chosen window.
> 4. **Regulation is measurable from the hydrograph.** On the Green below Howard Hanson `g(Q)` is flat
>   and the implied "storage" of ~790 mm is a dam operating rule, not basin water. **`g(Q)` must
>   therefore be refused by type on regulated reaches**, returning UNKNOWN with the regulation named —
>   the same refusal `susceptibility` already applies. That the exponent orders the basins exactly as
>   `regulation_class` does is an independent check on the seed data.
> 5. **This is the first derived quantity in the platform that can carry a numeric quality measure
>   without violating `DATA_DOCTRINE.md` §9**, because the method is peer-reviewed with a stated
>   failure mode and the fit statistic is an ordinary regression `r²`. The statistic published must be
>   the **unbinned** one (≈0.74–0.80), not the binned one (≥0.985), which would overstate certainty by
>   hiding about a quarter of the variance.
>
> **Not licensed:**
>
> - **Extrapolation to flood flows is untested.** The fits reach 1.5–3.0 mm h⁻¹; the December 2025
>   Skagit event exceeded that (OPEN QUESTION — testing `g(Q)`-predicted peaks against Event Zero is
>   the obvious hindcast).
> - **The method's own scale limit is not respected here.** Its author speculates it "must break down
>   for catchments that are too large" and offers ~1,000 km² as a guess; six of the seven gauges above
>   are at or beyond that. Channel-network routing lag is an unexcluded alternative explanation for the
>   flattened sensitivity at Mount Vernon, competing with the regulation explanation (OPEN QUESTION).
> - **The exponent is not fully reproducible as reported.** An independent reimplementation returned
>   1.69–1.92 rather than 1.85–2.05, and the exponent falls monotonically with the recession-filter
>   length. The *ordering* and the *order of magnitude* are robust; the third significant figure is not.
>
> **The connectivity threshold is the companion quantity and it is unmeasured here.** The hillslope
> literature gives 18–60 mm of storm precipitation; nobody has published a basin-scale value for the
> Sauk, Snoqualmie or Nooksack, and it is estimable from gridded QPE plus the stored hydrographs
> (OPEN QUESTION). Until it exists, the platform reports the gain and the distance to the seasonal
> median, and does not claim to know where the switch is.
>
> **One negative result belongs here because it disciplines everything above.** Regressing the 25
> largest independent November–March peaks on the pre-event flow at four unregulated gauges gives
> **r² = 0.001–0.057** (FACT, computed 2026-08-24). This is *not* evidence that antecedent state is
> irrelevant — the events are selected on the outcome, and by the time the flood season arrives the
> seasonal switch is already thrown. It is evidence that **a susceptibility surface built on an
> antecedent-flow percentile must never be read, or displayed, as a standalone predictor of peak
> magnitude.** The decisive experiment is the interaction — peak given basin QPE *and* antecedent
> state — and it requires a precipitation product the platform does not yet ingest. A null result for
> western Washington would be a genuine finding and belongs in this document, not in a drawer.

### 4.2 NEW §9A — Channel non-stationarity: rating epochs, conveyance drift and sediment regime

*Insertion point: immediately after §9 (River / hydraulic doctrine).*

> ## 9A. Channel non-stationarity
>
> The channel is a slow variable with a date. Two stage values from different channel states are not
> comparable even when their datums match, and an official stage threshold is a statement about the
> channel **as it was when the threshold was set**.
>
> - **Add a fourth time for slow variables: the hydraulic epoch.** `DATA_DOCTRINE.md` §3 has
>   `valid_time`, `issued_at` and `retrieved_at`. Stage observations and stage thresholds additionally
>   belong to a channel state with a date. Every stage series carries a `rating_epoch`; every stage
>   threshold carries a `hydraulic_epoch`; a *historical* stage comparison across epochs is refused.
>
> - **Conveyance drift is measurable per gauge, and it is confined to a predictable set of basins.**
>   Fitting stage against log-discharge on the upper half of the annual-peak distribution and taking
>   the trend of the residual (FACT, computed 2026-08-24 across fifteen western Washington gauges):
>   **Nooksack at Ferndale +0.139 ft per decade** (1968–2024, n = 31, p = 0.0001) — about 0.8 ft of the
>   official stage scale consumed in 56 years by the riverbed rather than by water; against **Skykomish
>   near Gold Bar +0.003 ft/decade (p = 0.74)** and **Sauk near Sauk 0.000 ft/decade (p = 0.88)**. The
>   drift is confined to basins with glaciated volcanic headwaters. At Skagit near Mount Vernon the
>   signal is different in kind: residual **variance** rose sharply after 2005 (residual sd
>   0.25 → 1.38 ft), which is scatter, not trend, and is the operationally dominant term there.
>
> - **`sediment_regime` belongs beside `regulation_class` as a CONFIGURED, display-only basin
>   attribute** — `volcanic_glaciated` / `glaciated_non_volcanic` / `non_glacial` — with the volcano
>   named. It never enters a hazard computation and it is the honest answer to "why does this gauge's
>   stage record drift and that one's does not." Three of the eight basins qualify: Nooksack (Mount
>   Baker), White (Mount Rainier), and Skagit — but the Skagit's *unregulated* volcanic source is
>   **Glacier Peak via the Sauk**, because Mount Baker's contribution to the Skagit arrives via the
>   impounded Baker. Mount Baker's unimpeded sediment goes to the Nooksack. That distinction predicts
>   correctly which gauges drift.
>
> - **A geomorphic anomaly is a data-quality event, not a hydrologic one.** A stage change
>   inconsistent with the discharge trend is a candidate log jam, avulsion, breach, debris flow or
>   rating break. It is surfaced with `quality=suspect` and a reason; never smoothed, never read as
>   basin behaviour, never used in a rate of rise. Two signatures are detectable from data the platform
>   already holds: a sustained stage rise upstream with a simultaneous discharge collapse at the next
>   gauge downstream (impoundment), and a step change in stage on a falling or steady discharge
>   (avulsion, jam, breach).
>
> - **Gauge control quality is provenance.** The hydraulic control at Skagit near Mount Vernon was
>   debris-affected in **29 %** of USGS gage-height field visits, against 3 % at Skykomish near Gold
>   Bar and 5 % at the Sauk (FACT, computed 2026-08-24). Rendered as a labelled category, not a
>   decimal.
>
> - **Staleness needs a slow-variable class.** `DATA_DOCTRINE.md` §5 derives staleness from an expected
>   cadence. A 2019 channel survey is not stale; it is the current best estimate of a decadal quantity.
>   The correct display is "as surveyed 2019", not an age-in-years staleness mark.
>
> - **Acute geomorphic hazards are real here and are not the platform's to model.** Lahars from three
>   stratovolcanoes, glacial outburst floods, landslide dams (the 2014 valley-blocking slide on the
>   North Fork Stillaguamish overtopped within 25 hours and its downstream flood-conveyance consequence
>   was modest and short-lived, while its *sediment* signal was large), and post-fire debris flows all
>   have an owning authority with a published product. The platform links and displays; it does not
>   model (§13).
>
>   **One structural gap follows from this and is worth naming.** In the Pacific Northwest the dominant
>   debris-flow initiation mechanism is **shallow landsliding driven by multi-day accumulation with
>   antecedent memory**, not runoff generation driven by short-duration intensity; the calibrated
>   regional threshold for the Seattle area is a cumulative 3-day-against-15-day form, and it captured
>   more than 90 % of historical multi-landslide days (FACT). Post-fire, the mechanism partially
>   shifts toward runoff initiation and the operative variable becomes **peak 15-minute intensity**
>   (the regional post-fire design storm is about 25 mm h⁻¹, and the agency assessment states its
>   models were **not developed for rain-on-snow**, which describes the Washington burn areas). The
>   forcing surface currently carries neither I₁₅/I₆₀ nor a cumulative antecedent-precipitation margin,
>   so it cannot reason about the one geomorphic hazard that *is* rainfall-triggered (§4).
>
> - **Land use is recorded and is not a hazard term.** Forest-harvest peak-flow effects in this region
>   are **undetectable beyond about a 6-year return period** and are **smaller than interannual
>   variability at basin scale** in the state-of-science synthesis; a frequency-paired reanalysis
>   disputes the statistical basis of that conclusion and finds the opposite trend with return period
>   (CONTESTED). Roads are a real Hortonian surface in a landscape that otherwise has none and extend
>   drainage density by 21–50 % in the studied basins. The honest position is to record
>   `forest_disturbance_pct`, `road_density` and `effective_impervious_pct` as CONFIGURED basin
>   attributes, cite both sides in the method note, and **use neither in a hazard computation.**

### 4.3 NEW §10A — Coastal boundary conditions and compound flooding

*Insertion point: immediately after §10 (Reservoir, dam and flood-defense doctrine). `HYDROLOGY.md`
currently has no tide, no surge, no sea level and no datum below the gauge, while two of its six
configured forecast points sit in deltas and one of them is substantially a tide gauge.*

> ## 10A. Coastal boundary conditions and compound flooding
>
> At a delta outlet, stage is not a river quantity. The governing decomposition is (FACT):
>
> ```
> TWL = T + S + R + TSI + SRI + TRI + datum
>
> T = astronomical tide      S = storm surge      R = river-induced water level
> TSI, SRI, TRI = the tide–surge, surge–river and tide–river interaction terms
> ```
>
> **The three interaction terms are first-order, not corrections**, and they have opposite signs: in a
> Puget Sound estuary the tide–surge term is about **+10 % of total water level downstream** and is
> what lifts a king tide from no flooding to major flooding, while the surge–river and tide–river terms
> are **negative upstream, together reducing water levels by up to 50 % relative to a linear sum**
> (FACT). **Therefore the platform never sums tide + surge + river.** If a combined water level is
> ever displayed it comes from a hydrodynamic model, badged MODELED, or it is labelled an upper bound
> that ignores nonlinear damping.
>
> - **Tidal influence is a measured per-point coefficient, not a basin flag.** Measured by regressing
>   tidal-band river stage on tidal-band sea level at low flow (FACT, computed 2026-08-24):
>
>   | Forecast point | Tidal transmission | Correlation | Class |
>   |---|---|---|---|
>   | Snohomish at Snohomish | **0.831 ft/ft** | r = 0.94 | **TIDAL** |
>   | Nooksack at Ferndale | 0.019 ft/ft | r = 0.33 | MARGINAL |
>   | Skagit at Mount Vernon | 0.010 ft/ft | r = 0.23 | MARGINAL |
>
>   Raw stage at Snohomish swung **4.89 → 17.16 ft** over that window — an ~11 ft diurnal oscillation
>   at a gauge whose flood stage is 25 ft. `tidal_class` (TIDAL / TIDALLY_MODULATED / MARGINAL /
>   FLUVIAL / UNKNOWN) is a forecast-point attribute derived from this measurement and re-derived on a
>   schedule.
>
> - **Trend and headroom are wrong at a TIDAL point unless the series is de-tided.** A rate of rise
>   computed over a 1, 3 or 6-hour window at Snohomish is dominated by the tide, not the flood. Either
>   de-tide before computing trend, or refuse trend there with an explicit reason. This is a live
>   defect, not a future concern.
>
> - **River discharge and coastal water level are dependent here, and the dependence is measurable.**
>   Over thirty winters, Spearman correlation between daily discharge and Seattle skew surge at a
>   one-day lead is **+0.31 (Skagit), +0.39 (Nooksack), +0.30 (Snohomish)**, robust to
>   de-seasonalising; conditional on discharge at or above its 95th percentile, a 90th-percentile skew
>   surge is **1.9–2.5× more likely than under independence** (FACT, computed 2026-08-24). One synoptic
>   object produces both. The optimum is **surge leading discharge by about a day**, so a zero-lag
>   dependence test understates the hazard. **Treat these as dependence measurements, never as a
>   calibrated joint model**; no joint probability may be displayed until a copula has been fitted and
>   hindcast-evaluated (OPEN QUESTION).
>
> - **Use skew surge, not the non-tidal residual, and compute it per tidal cycle.** Skew surge is the
>   maximum observed water level in a tidal cycle minus the maximum predicted level in that cycle,
>   regardless of whether the two maxima coincide; the non-tidal residual contains timing error. The
>   calendar-day shortcut is wrong by up to 2 ft in spring because diurnal inequality splits the
>   higher-high pair across the day boundary (FACT).
>
> - **Puget Sound is a small-surge, small-freeboard system, and the seasonal cycle stacks the deck.**
>   Over 21,166 matched tidal cycles at Seattle the skew surge mean is +0.12 ft, the 99th percentile
>   +1.38 ft, the maximum in thirty years **+2.58 ft**, and **no cycle exceeded 3.0 ft** — consistent
>   with the modelled maximum of 2.5–3.0 ft for most of the Sound. But **24 of the 50 highest observed
>   high waters fall in December and 18 in January**, monthly mean higher-high water is 0.60 ft higher
>   in winter than summer, and the December 2022 event reached **3.76 ft above MHHW — above the
>   published fitted 100-year still-water level** (FACT). Design intuitions imported from hurricane
>   coasts will be wrong in both directions: a 0.6 m surge is minor on a hurricane coast and is the
>   difference between no flooding and major flooding here.
>
> - **Relative sea level is a vertical-land-motion measurement and its sign reverses inside the
>   domain.** Measured tide-gauge trends (FACT, computed 2026-08-24): **Cherry Point −0.06 mm yr⁻¹
>   (95 % CI −0.64 to +0.52 — indistinguishable from zero)**, Friday Harbor +1.19, Port Townsend
>   +1.80, **Seattle +2.09**, and **Neah Bay −1.70** — relative sea level there is *falling*. The
>   spread across ~150 km of one inland sea is **2.15 mm yr⁻¹**. **A single regional or statewide
>   sea-level number applied to a specific delta is wrong**, and the only defensible input is the
>   nearest long-record gauge's own measured trend with its confidence interval — reported as "no
>   detectable trend" where the interval includes zero.
>
> - **The observing network is the constraint, not the science.** There is **no real-time NOAA water
>   level gauge in Skagit Bay, Padilla Bay, Port Susan or Possession Sound**; the two most relevant
>   delta locations are prediction-only subordinate stations without published geodetic ties. A
>   modelled operational-forecast-system water level is available at several of those locations and is
>   **MODELED, never OFFICIAL_FORECAST**.
>
> - **A tide prediction breaks the platform's knowledge-time rule and needs its own entry.** Harmonic
>   predictions for future decades are computable today, so `available_at` is effectively "whenever the
>   harmonic constants were published" (OPEN QUESTION for `DATA_DOCTRINE.md` §11).
>
> - **A gauge datum is not permanent.** A Cascadia megathrust rupture reverses the interseismic uplift
>   instantaneously; the state's own sea-level product ships a modelled land-level change for a
>   500-year-return-interval event alongside its other tables. This is recorded as sourced,
>   non-life-safety context and never as a hazard number. **NON-OPERATIONAL CONTEXT.**
>
> - **Coastal water level is a modifier of hazard at TIDAL points, not a fifth surface.** It is a
>   boundary condition, not a basin property, and only a minority of forecast points feel it. Where it
>   applies, the platform may show a **tidal headroom** indicator — how much coastal water level the
>   event did not get — badged EXPERIMENTAL, and must show the coastal state (water level, predicted
>   high water, skew surge, next high water, source kind, station, datum) or UNKNOWN with a reason. The
>   renderer must never draw a static sea beside a tidal delta: sea level in Puget Sound moves ~11 ft
>   twice a day, and a frozen shoreline is a fabricated certainty of the same family as a moving snow
>   line.

### 4.4 NEW §12A — Reference distributions and their vintage

*Insertion point: immediately after §12 (Historical intelligence and hindcasting). This is the
measured-non-stationarity section. It contains no projections.*

> ## 12A. Reference distributions and their vintage
>
> The platform ranks live values against reference distributions it builds itself. Those distributions
> are estimated, and their estimation error is larger than the climate signal they are sometimes
> imagined to track. Every claim in this section is a **measurement on the platform's own configured
> gauges**, made 2026-08-24.
>
> - **A day-of-year percentile has two error terms, and the larger one is sampling.** Rebuilding the
>   ladder from a random 20 years instead of the full record — which destroys any trend while
>   preserving the sample size — moves **12.8–17.4 % of daily observations into a different
>   susceptibility band** across ten gauges (300 draws each). The additional flip rate attributable to
>   *recency* is **0 to +7 percentage points** and is statistically distinguishable from the sampling
>   null at only **four of ten** gauges. The dominant corruption of the reference distribution is not
>   climate drift; it is estimation variance.
>
> - **A percentile is not a number until it carries a sampling interval.** For a value whose true rank
>   is the median, the standard deviation of the estimated percentile is **±12.1 points at a 10-year
>   ladder, ±7.7 at 20 years, ±5.5–6.2 at 30 years, ±4.0 at 50 years**. The band edges are 25/75/90.
>   Every percentile-bearing feature therefore carries `climatology_period_start`,
>   `climatology_period_end`, `n_years`, `n_effective` and `percentile_sampling_sd`, and is rendered
>   with its interval — *"p78 ± 6 (30-year ladder, 1996–2025)"*, never a bare p78. **The band must be
>   able to return UNKNOWN with reason `within_sampling_error_of_band_edge`** rather than manufacture a
>   distinction the data does not support.
>
> - **The reference period is the longest *homogeneous* record, not the most recent one.** Homogeneity,
>   not recency, is the binding constraint. A homogeneity break is a gauge datum epoch change, a
>   documented rating-revision epoch, a station relocation, or a change of upstream operating rule — it
>   is **not** the passage of time. This is the opposite of the intuition that a warming climate demands
>   a recent baseline, and it holds here because the drift is small relative to interannual variance.
>   It is supported by an out-of-sample rolling-origin test (full-record mean calibration error 3.42
>   percentile points against 3.98 for the most recent 30 years and 5.04 for the most recent 20) —
>   **and that support is on average across held-out decades, not uniformly**: a recent-30 ladder beat
>   the full record at all ten gauges on one decade and lost on another. The rule is adopted with that
>   caveat visible.
>
> - **A change of regulation regime corrupts the ladder more than any climate effect measured.**
>   Splitting the Green and Skagit records at their major-impoundment dates shifts the ranking by a
>   mean of **9.9–11.1 percentile points and flips 29–32 % of days.** The operating-rule epochs for the
>   region's projects are **CONFIGURED seed data the platform does not yet carry**, and the ladder
>   cannot be correctly bounded without them (OPEN QUESTION — the split dates used in the measurement
>   are working values, not facts).
>
> - **The observing network contains steps that dwarf any climate signal.** The USGS annual-peak stage
>   series at Snoqualmie near Carnation — a configured susceptibility gauge — contains a **41.26 ft
>   datum discontinuity** between the 1939 and 1940 water years. Across the eleven-state SNOTEL network
>   a sensor upgrade produced a step of **+1.7 °C in minimum temperature and −0.5 °C in maximum**,
>   which propagates into widely used gridded products. **The platform must never state a snowpack or
>   temperature trend from its own SNOTEL feed**, and a trend computed from that network's temperature
>   channel is invalid.
>
> - **The seasonal shape of the ladder is itself drifting, slowly and in the expected pattern.** Centre
>   of timing has moved earlier by **1.75–4.63 days per decade**, significant at five of ten gauges,
>   and the October–February share of annual flow has risen by 0.33–0.95 points per decade. The
>   significant gauges are the **snow-influenced** ones and the rain-dominated lowland gauges show
>   nothing — which is the physically expected pattern and is evidence the signal is not an artefact.
>   The resulting within-key heterogeneity at a mid-winter day-of-year key is of order **±10 % in
>   flow**, well inside the sampling term above.
>
> - **A ladder rebuild is a revision, and replay must reproduce the ladder of its knowledge time.**
>   See §12. This is a bug class, not a feature request.
>
> - **Publish vintage sensitivity as a disagreement signal; never as a correction.** Compute the same
>   value against a second, explicitly named ladder and expose the signed difference as a
>   `climatology_vintage_sensitivity` driver. A trend adjustment would be an uncalibrated method and
>   would be chasing a term smaller than the noise at six of ten gauges.
>
> - **What the platform does not do with any of this.** It does not use climate projections, and it
>   does not attribute individual events to climate change (§13). It states the vintage, the period and
>   the sampling interval of every reference distribution it ranks a live value against, so that a
>   reader can see the baseline move without the platform claiming to have measured why.
>
> - **A note on the moisture constraint, because it is routinely misapplied.** Clausius–Clapeyron gives
>   about **7 % K⁻¹** for saturation vapour pressure and, under near-constant relative humidity over
>   the ocean, for column water vapour. **It is a constraint on moisture and only on moisture.**
>   Precipitation is `w · q · ε` and only `q` is constrained; observations depart from the relation in
>   both directions. Over 1980–2023 the quantity the platform would badge — **AR IVT — rose by less
>   than 1 %** in reanalysis, with AR area up 6–9 % and low-level wind speed *decreasing*, and the
>   authors themselves caution that assimilation changes may affect those trends. Importing a
>   "7 % per degree" or "14 % per degree" factor into a western Washington design storm or threshold is
>   unsupported in both directions.

### 4.5 NEW §12B — Flood frequency and recurrence: what the platform refuses, and what it says instead

*Insertion point: immediately after §12A. `HYDROLOGY.md` and `DATA_DOCTRINE.md` currently contain no
occurrence of "return period", "recurrence", "AEP" or "100-year"; the prior pass asserted the platform
"already declines to compute return periods", which is not true in writing.*

> ## 12B. Flood frequency and recurrence
>
> **Every recurrence-interval number that could be attached to a western Washington river is either
> inapplicable, uncertain by a factor of two, or measuring a dam — and the authoritative source the
> platform already reads publishes no recurrence interval at all.** The engineering response is not to
> compute a better one; it is to refuse the object and say precisely why.
>
> Four independent reasons (all FACT):
>
> 1. **The federal standard excludes these rivers by its own scope.** Its procedures "do not cover
>   watersheds where flood flows are appreciably altered by reservoir regulation, watershed changes, or
>   hydrologic nonstationarities". At Skagit near Concrete **101 of 107** annual peaks and at Mount
>   Vernon **85 of 86** carry the USGS "discharge affected by regulation or diversion" code. The same
>   standard states plainly that regulated peak-flow data "do not fit any statistical distribution".
> 2. **The peaks are a mixed population, and the two USGS-affiliated authorities disagree about what to
>   do.** At Skagit near Concrete, 18 % of annual peaks are warm-season and **none of them is in the
>   top 20**. One body of work finds the western-US annual maximum series is a mixture whose tail is
>   AR-dominated; the authoritative Washington study inspected the frequency plots and concluded no
>   streamgage required mixed-population treatment. Both agree a mixture exists; they disagree about
>   the criterion. Unresolved, and squarely about these basins. The federal standard concedes it has
>   **no evaluated method** for the situation, and USGS peak codes cannot supply the "objective and
>   hydrologically meaningful criterion" it requires — the snowmelt code appears **3 times in ~900**
>   western Washington annual peaks.
> 3. **The uncertainty is a factor of two and it is published.** Across the western Washington gauges
>   with 50 or more years of record, the median 95 % confidence interval on the 1 % AEP flood spans a
>   factor of about **1.6–1.7**, and on the 0.2 % AEP about **1.9–2.0**.
> 4. **"The 100-year flood keeps happening" is arithmetic, not signal.** About **52 %** of those gauges
>   have already recorded a peak exceeding their own published 1 % AEP estimate; the binomial
>   expectation under stationarity for these record lengths is about **49 %**. (This is a consistency
>   check on the fitting procedure, not a powerful test of stationarity, because each estimate is
>   fitted to the very record whose maximum is then compared against it.)
>
> Two further facts bound what the platform could even inherit: **NWPS publishes no AEP, recurrence or
> return-period field at any of the platform's forecast points**; and **Washington has no modern
> precipitation-frequency atlas** — design precipitation frequency here still rests on a 1973
> publication for 1–24 h durations and a 1964 one above 24 h. Washington and Oregon are the only two
> CONUS states in that position. Every design storm in Washington predates the entire modern flood
> record. A trend-aware replacement is scheduled; its **projection volume is out of scope** (§0), and
> its present-day volume will be ingested, when published, with its vintage and its confidence
> interval or not at all.
>
> **Therefore the platform will not display a recurrence interval, return period or annual exceedance
> probability for any reach** (§13). Where an authority publishes one, it may be shown as a **cited
> external estimate with its interval, its record period, its regulation status and its vintage** —
> never as a category, a colour, a threshold, or a sentence containing the phrase "N-year flood".
>
> **What the platform says instead**, all computable now and none of them a frequency claim:
>
> - **Rank in record.** *"This crest is the Nth highest stage in M years of record at this gauge
>   (WY a–b), and the Kth highest discharge."* Rank is an observation and carries no distributional
>   assumption. Stage rank and discharge rank are stated **separately**, because at Mount Vernon they
>   differ, and a "record" must name which series it is a record in and whether the value is approved
>   or preliminary — the December 2025 crest is preliminary and is not yet in the annual peak series.
> - **Distance to the nearest observed analogue**, by peak discharge, with that event's crest stage.
> - **Day-of-year percentile against a stated climatology** — honest because it is an empirical rank
>   against a named record, not an extrapolated tail, and provided it carries the vintage, sampling
>   interval and regulation epoch §12A requires.
>
> **Cross-source disagreement on a crest is reported, not reconciled**: the same 2021 Mount Vernon
> crest is published as 37.32 ft / 122,596 cfs by one authority and 36.99 ft / 127,000 cfs by another.
>
> And at a tidally influenced point, the stage-frequency object and the discharge-frequency object are
> **different objects with different generating processes**; a stage-frequency statement there is a
> joint river-and-tide statement and cannot be inherited from a discharge fit (INFERENCE, OPEN
> QUESTION — nobody in the fetched literature computes one for these reaches).

### 4.6 NEW §12C — Verification doctrine: what would count as skill

*Insertion point: immediately after §12B. `TESTING.md` §7 owns the harness; this section states what
the doctrine will and will not accept as evidence that a surface works.*

> ## 12C. Verification doctrine
>
> The platform's central evaluation problem is not that its indices might be wrong. It is that **at its
> own forecast points the events it exists to anticipate are too rare to measure.**
>
> - **Measured base rates** (FACT, computed 2026-08-24): minor flooding occurs on **0.16–0.77 % of
>   days** across the six configured points. At Skagit at Mount Vernon: action 1.82 %, minor 0.358 %,
>   moderate 0.167 %, major 0.0796 % of days. At Green near Auburn, *moderate* has been exceeded
>   **twice since 1990** on the instantaneous peak record and *major* **never** since the dam closed in
>   1962. Any conventional skill score computed on that sample is dominated by the base rate and will
>   read "excellent" for a forecast that says *no flood, forever*.
>
> - **Base rates are computed from instantaneous values, not daily means.** NWS categories are defined
>   on instantaneous stage or flow; computing exceedance from daily means silently redefines the event,
>   which the platform's "official thresholds, in the unit NWS defines them" rule does not permit. The
>   December 2025 Mount Vernon crest was **37.73 ft instantaneous against a 35.06 ft daily mean** — a
>   2.67 ft shortfall on the one day that matters most.
>
> - **UNVERIFIABLE is a legitimate verdict.** `DATA_DOCTRINE.md` §12 makes UNKNOWN first-class for
>   *values*; the evaluation layer needs the analogue for *verdicts*. Where a stratum's event count is
>   zero or near-zero the report says `UNVERIFIABLE (n_events = 2 instantaneous peaks since 1990)`,
>   never "skill = 1.0" and never a blank.
>
> - **Every skill number carries its reference, its stratum and its event count.** Minimum record:
>   `{metric, value, reference, n_pairs, n_events, base_rate, stratum, lead_time, method_version,
>   evaluated_at}`. A skill score against climatology without a named reference is meaningless, and at
>   day 1 climatology inherits persistence skill and depresses the score of a real forecast — so
>   persistence is reported as a second reference at short lead.
>
> - **The metrics must not degenerate.** Threat score, equitable threat score and hit rate degenerate
>   to trivial limits as the base rate approaches zero. Report a non-degenerating rare-event measure
>   alongside them; report **CRPS**, which reduces to mean absolute error for a deterministic forecast
>   and is therefore the one score that puts the official single-valued forecast and the ensembles on a
>   single axis; report the Brier decomposition **bias-corrected**, with its sample size and bin count
>   stated, because the finite-sample inflation of the reliability term scales as bins over samples and
>   at these base rates is a material fraction of the whole uncertainty term. **A reliability diagram
>   drawn from a few winters of western Washington data is measuring its own sampling noise.** And a
>   rank histogram alone does not establish reliability — recent work argues spread-error and
>   rank-based diagnostics can pass a demonstrably miscalibrated ensemble (CONTESTED, and recent).
>
> - **Skill is not value.** Relative economic value peaks where the user's cost-of-acting to
>   cost-of-loss ratio equals the base rate. At 0.0016–0.008, **the only users for whom a Cascadia
>   Papsukkal flood signal has value are those whose cost of acting is under about 1 % of their loss**
>   — cheap precautionary actions, not expensive irreversible ones. The product should be built around
>   lead time on cheap actions and must never imply it supports expensive decisions. Publish the value
>   curve across a range of cost-loss ratios, not a point.
>
> - **Structural traps this domain names, all of which apply here.** Aggregating across forecast points
>   is ill-posed (different distributions, and stage cannot be converted to flow). Aggregate statistics
>   hide the tail — a point with a good overall error can under-forecast its largest events with
>   falling detection and rising false alarms as observed stage rises. **The no-forecast problem**: at
>   flood-only points, a flood that was not anticipated produces no forecast–observation pair and
>   silently vanishes from the sample; a flood with no forecast pair is a **miss**, not an absence.
>   Timing errors masquerade as magnitude errors on a steep rising limb, so timing is measured by
>   **threshold-crossing time**, not by peak-time difference. Rising and falling limbs are verified
>   separately.
>
> - **Consistency is a separate axis from accuracy and is verified separately.** Forecast jumpiness and
>   forecast error are only weakly correlated: a jumpy forecast is not necessarily wrong and a stable
>   one is not necessarily right. The revision magnitude, normalised by ensemble spread or by threshold
>   width, is its own metric. The December 2025 Mount Vernon sequence (§12) is the platform's first
>   consistency benchmark.
>
> - **Verification unit is the event, not the timestep.** Timestep-pooled scores at these base rates
>   measure the dry season. And "one year of verification data" is really **one flood season** —
>   perhaps three to eight independent AR sequences. Independence, not calendar length, is the sample
>   size. Bootstrap intervals on every score; at these base rates the interval will usually contain
>   zero, and **that is the finding**.
>
> - **Where "what would have happened naturally" is unobservable** — every regulated reach — the only
>   way to separate model error from operator decision is verification against a reference simulation.
>   That is badged as such and never conflated with verification against a gauge.
>
> - **A method is promoted on an evaluation report, not on an aggregate number.** The report contains
>   the reliability diagram *and* its sample size, the value curve, the stratum table with event
>   counts, and an explicit list of strata marked UNVERIFIABLE.
>
> - **One circularity hazard to name explicitly.** At White at R Street the only moderate-category day
>   in the digital record **is Event Zero itself** — the same event the platform uses as its replay
>   target. The verification sample and the calibration event are the same event, and the report must
>   say so.

---

## 5. Claims we must now retract or soften

Ordered by consequence. Each names the sentence, what is wrong with it, and the minimum honest
replacement. **R1–R4 are retractions** — the current wording asserts something the evidence does not
support. **R5–R14 are softenings** — the wording is defensible but claims more precision, more
generality or more reassurance than the corpus permits.

| # | Where | What must change | Why |
|---|---|---|---|
| **R1** | `HYDROLOGY.md` §7 — "Rain-on-snow runoff enhancement comes **mostly** from turbulent sensible and latent heat fluxes … the heat content of the rain itself is a minor term **(FACT)**" | **Retract the FACT label and the generality.** Replace with the regime-dependent statement in §3.7. | This is the only claim in the document the corpus **refutes as stated**. Net radiation leads in the event population and in wind-sheltered forest (33–55 %, and 68 % for the mountainous western US); the 60–90 % turbulent figure is a single wind-exposed extreme event; and advected rain heat is **29–44 % of the energy budget in persistent-melt events** — the very events that flood. The operational conclusion survives; the stated mechanism does not. |
| **R2** | `HYDROLOGY.md` §12 — Event Zero as "a CW3E AR-4 (coastal WA) / AR-3 (Cascade foothills) event with ~96 h of AR conditions" | **Retract as a category error.** Restate as an **AR family** with per-AR categories and inter-event gaps, and record the categories as CONFIGURED-from-narrative. | Under the AR scale's own definition an AR event is one *continuous* period of AR conditions at a point. Three ARs across nine days are a family; 96 h is the family span. The categories came from imagery with no machine-readable source, so they fail `DATA_DOCTRINE.md` §1 provenance as currently carried. |
| **R3** | `HYDROLOGY.md` §10 — "**Flood-buffer capacity** = available flood-control storage (rule-curve maximum − current storage)" | **Retract the single formula.** Replace with three signed volumes (§3.10). | The formula produces ≈22 % for Ross in the event where Ross removed **110,900 acre-feet** — 92 % of a full design flood pool — from the Skagit. A public "percent of flood pool used" built on it would have shown a quarter-full reservoir during the most consequential regulation event in the basin's modern record. |
| **R4** | `HYDROLOGY.md` §2 — "**Transient snow zone.** In the Cascades, terrain between roughly 1,000 and 4,000 ft …" | **Retract the band as a parameter.** Keep the derived dynamic fractions; move any elevation description to prose with a vintage. | Three independent reasons: the concept "implies a static area, when in fact the area undergoing melt is highly dynamic during storm events"; the observing network does not cover the band (median western-WA SNOTEL 3,900 ft, one site below 2,000 ft); and the band's own position is drifting (2.3–4.6 days/decade of timing shift at the snow-influenced gauges). |
| **R5** | `HYDROLOGY.md` §1 — "forcing determines how much water enters; state determines how the basin **reacts**" | Soften and split. State the measured gain (7.6–11.1×) *and* the regional qualification that Washington is the low-responsiveness group (≈2×, not 4.5×), *and* that three of the five flood conditions are forcing-side but geometric. | The single sentence is true in three different senses that point in different directions, and as written it is read as licensing a susceptibility surface to carry more discriminating weight than the region's own record supports. |
| **R6** | `HYDROLOGY.md` §2 — "the lower Skagit … **crests roughly a day** after the upper-basin peaks (INFERENCE)" | Soften to a measured distribution: **median 16.9 h, sd 3.5 h, range 9.5–23.8 h**, and add that response time is dominated by regulation rather than basin size. | The claim is ~30 % long, and the spread is operationally larger than the bias. Recession time constants run 17.5–28.1 h unregulated against 264 h on the Green. |
| **R7** | `HYDROLOGY.md` §1 — the channel network "routes it downstream, **delayed and attenuated**" | Soften: routing has two signs. Peak change Concrete → Mount Vernon measured **−24.8 % to +27.8 %**. | USACE documents the amplification mechanism explicitly; two of twelve recent events amplified by more than 20 %. |
| **R8** | `HYDROLOGY.md` §7 — "Working assumption: snow level ≈ freezing level − ~1,000 ft" | Soften the *form*, not the value. The offset is **precipitation-intensity dependent** and the storm-to-storm range spans a kilometre; and three distinct elevations must be named, because the platform's input is a wet-bulb column level with no terrain depression applied. | A fixed offset is biased **exactly during the heaviest AR hours**, and biases the rain-exposed fraction low when the answer matters most. |
| **R9** | `HYDROLOGY.md` §4 — forcing sources listed as "GFS/GEFS (derived), **CW3E products**" | **Strike "CW3E products".** | They are image-only, research-use-only, with no data endpoint (re-confirmed 2026-08-24). The doctrine currently names a source that cannot be ingested, and implicitly licenses reading a category off a picture. |
| **R10** | `HYDROLOGY.md` §2 — "Upper and **Lower Baker** (Puget Sound Energy) control the Baker" | Correct: **Lower Baker has no authorised flood storage.** | It is constrained only against drawing down while Upper Baker is storing. Grouping the two overstates the Skagit system's controlled fraction. |
| **R11** | `HYDROLOGY.md` §2 — "Nooksack … the lower river is tidally influenced at Ferndale" | Soften and re-prioritise. Ferndale's measured transmission is **0.019 ft/ft**; the platform's genuinely tidal forecast point is **Snohomish at Snohomish at 0.831 ft/ft**, and the doctrine does not mention it. | The doctrine flags a marginal case and is silent on the one that will produce a wrong trend and a wrong time-to-threshold today. |
| **R12** | `HYDROLOGY.md` §6 — model skill "is evaluated per basin and per regime … **as history accumulates**" | Soften: at the regulated points the upper categories may **never** acquire a verifiable sample. | Green near Auburn *moderate*: two instantaneous events since 1990. *Major*: none since 1962. History will not accumulate there. |
| **R13** | `HYDROLOGY.md` §8 — "Percentiles require climatology; the platform builds its own from stored history … with the period stated" | Soften: a period is necessary and **not sufficient**. A percentile needs its sampling interval, effective sample size, homogeneity epoch and regulation epoch. | 12.8–17.4 % of daily observations change band from ladder length alone; a regulation split moves the ranking by ~10 percentile points and flips 29–32 % of days. |
| **R14** | The prior pass, `flood-genesis-mechanisms-2026-08-24.md` — "**~29 % less water** for the same stage" at Mount Vernon, and "backwater and tide … strong leverage on stage at the gauge", and "the platform already declines to compute return periods" | Three corrections, none of which is in `HYDROLOGY.md` but all of which would migrate there if the delta were written from the prior pass alone. | (a) The drift is **9–11 % at flood stage** over ~three decades (population-level −4.4 %), not 29 %; the 1906 datum is a historic indirect estimate with an unknown peak day and the 1990 datum is breach-depressed. (b) The tide does **not** reach the Mount Vernon gauge — measured tidal amplitude there is of order 0.004–0.009 ft against a bay range of 8–11 ft, and the authoritative hydraulic model puts the tidal limit about seven river miles downstream. (c) **The platform does not decline return periods in writing** — the strings do not occur in either doctrine file. §12B fixes this. |

**Two things that should *not* be softened, despite pressure from adjacent findings:**

- **§9's refusal to convert stage ↔ flow.** Three separate corpus files independently strengthen it,
  and it now has numbers behind it (0.68 ft residual SD and a 3.14 ft inversion against 2 ft category
  spacing; a rating extrapolated above 125,000 cfs; ~9–11 % conveyance change in three decades). It is
  also the reason four of six forecast points cannot carry a model exceedance probability — an
  expensive consequence that is nonetheless correct.
- **§13's refusal to print an uncalibrated probability.** At base rates of 0.16–0.77 % of days, a
  probability that has not passed a reliability check is not merely unproven, it is very likely
  uncheckable with the data the platform will hold for years. The *index* / *indicator* vocabulary is
  the correct long-term answer, not a placeholder.

---

## 6. Claims the corpus newly licenses us to make

Each of these is something `HYDROLOGY.md` does **not** currently say, that the corpus supports, with
the label it should carry. They are ordered by how much they improve a 6–120 h flood prediction.

| # | New claim the platform may now make | Label | Basis |
|---|---|---|---|
| **L1** | **Basin flood response is orientation-selective, and the selectivity is statistically significant.** The Green floods only on low-level flow from 245°–275°; the Sauk essentially only on south-westerly flow; the separation between basin pairs holds at >95 % confidence; and the Green's flood composites carry the *weakest* vapour fluxes of the four basins studied, so its flooding is more sensitive to orientation than to flux magnitude. | **FACT** | Neiman et al. 2011, composited over the top-10 annual peak daily flows in four unregulated western Washington basins, WY1980–2009. |
| **L2** | **Storm-total upslope IVT and AR duration are the two atmospheric quantities with published skill against runoff.** Upslope IVT explains 74 % of storm-total rainfall variance and 61 % of storm-total runoff-volume variance; doubling the mean duration multiplied peak streamflow by ~6× and storm-total runoff volume by >7×. Over the Olympics the instantaneous relation gives r² = 0.85 in unblocked warm sectors, at 0.014 mm h⁻¹ per kg m⁻¹ s⁻¹. | **FACT** | Ralph et al. 2013; Tierney & Durran 2024. |
| **L3** | **The wet-season dynamic store of these basins is 71–104 mm, they fill it between 1 October and 5 November every year, and the marginal millimetre at high flow produces 7.6–11.1× the discharge it produces at seasonal-median flow.** | **FACT** (computed) | Kirchner sensitivity fits on five water years of USGS instantaneous discharge at seven Cascadia gauges. |
| **L4** | **Response time is a measured, basin-specific quantity dominated by regulation:** τ at 1 mm h⁻¹ runs 17.5–28.1 h unregulated, 42 h at Mount Vernon, 116 h on the Cedar, 264 h on the Green. And crest lag Concrete → Mount Vernon is a distribution with median 16.9 h and sd 3.5 h. | **FACT** (computed) | Same fits; USGS instantaneous values across twelve events 2003–2025. |
| **L5** | **The maritime snowpack is a small, leaky buffer worth ≈30–45 mm against a 200–400 mm AR** — roughly 8–20 % of the storm — **snowmelt supplies only ~19–45 % of the water** in a maritime rain-on-snow flood, and **snowpack outflow is bounded at <3 mm h⁻¹ net, <10 mm h⁻¹ total, never above 14 mm h⁻¹.** | **INFERENCE** for the buffer arithmetic; **FACT** for the outflow ceilings and the melt fraction | Measured liquid-water contents and lysimeter records from the closest long-record maritime analogue forest. |
| **L6** | **Percent-of-median SWE is misleading in the direction of calm, and by how much.** On 2025-12-11 the sub-4,500 ft western-WA sites read 14 % of median with ten at exactly zero, while the all-station composite read 44 %. | **FACT** (computed) | NRCS AWDB, fetched and computed 2026-08-24. |
| **L7** | **Snow drought state is signed and computable today from data already ingested.** Warm snow drought (low SWE with above-median accumulated precipitation) raises susceptibility; dry snow drought lowers it; low SWE alone says nothing. | **FACT** for the published definition; the derived state is **DERIVED/EXPERIMENTAL** | An operational percentile-based snow-drought definition using exactly the two AWDB elements the platform already reads. |
| **L8** | **A day-of-year percentile carries ±5.5–6.2 percentile points of sampling error at a 30-year ladder, and 12.8–17.4 % of daily observations change band from ladder length alone.** A regulation-regime split moves the ranking further than any climate effect measured. | **FACT** (computed) | Permutation nulls across ten gauges, 300 draws each. |
| **L9** | **The susceptibility surface saturates during floods.** The stored ladder clamps at p95; during December 2025 the Sauk read p95 across a 2.5× flow range and could not fall as the river receded; observed flows reach 5.0× the p95 value. | **FACT** (computed) | Replay of the platform's own banding against the full daily record. |
| **L10** | **The signal in Event Zero was in the derivative, not the level:** the surface would have read LOW in four of six basins two days before the official Flood Watch and MODERATE everywhere on the day of it; the Sauk moved 64 percentile points in 48 hours. | **FACT** (computed replay) | Reconstructed with a climatology excluding 2025. |
| **L11** | **A LOW susceptibility band is not an all-clear**, with the measured numbers: 0.0–0.8 % probability of a top-1 % weekly flow against a 1.0 % base rate, and 24–25 % of unregulated-gauge annual maxima preceded by a sub-25th-percentile state at −7 days. | **FACT** (computed) | Full-record conditional frequencies at the six configured gauges. |
| **L12** | **Regulation has a published ceiling, and the platform may state it:** control fractions of 39 % (Skagit at Mount Vernon), 55 % (Howard Hanson) and 42 % (Mud Mountain); reduction that peaks near the 25-year event and decays thereafter; and the Corps' own statement that above roughly the 25-year event the uncontrolled watersheds produce major flooding "regardless of the flood control regulation". | **FACT** | Project water control manuals and the authoritative basin study. |
| **L13** | **The rule curve is a published, machine-readable seasonal function, and the live curves disagree with the published manuals at two projects.** | **FACT** | CWMS seasonal-value arrays, fetched 2026-08-24. |
| **L14** | **The tide does not reach the Skagit gauge at Mount Vernon**, and the genuinely tidal forecast point in the platform is Snohomish at Snohomish (0.831 ft/ft, r = 0.94). Tidal class is a measured per-point coefficient. | **FACT** (computed) | High-pass regression of river stage on sea level at low flow; corroborated by the authoritative hydraulic model's stated tidal limit. |
| **L15** | **River discharge and coastal water level are dependent in these basins**, at ρ = +0.30 to +0.39 with surge leading by a day, raising the conditional likelihood of a high skew surge by 1.9–2.5× — **and December 2025 sampled the benign corner**, with all three record crests at 4.8–6.6 ft below MHHW. | **FACT** (computed) for the dependence; the joint model remains absent | Thirty winters of paired USGS discharge and CO-OPS skew surge. |
| **L16** | **Relative sea level in Puget Sound is a vertical-land-motion measurement whose sign reverses inside the domain** — Cherry Point indistinguishable from zero, Seattle +2.09 mm yr⁻¹, Neah Bay **falling** at −1.70. A single statewide number applied to a delta is wrong. | **FACT** (computed) | NOAA CO-OPS monthly mean sea level, OLS with autocorrelation-inflated standard errors. |
| **L17** | **Conveyance drift is measurable per gauge and is confined to the glaciated-volcanic basins:** Nooksack at Ferndale +0.139 ft/decade of stage at fixed peak discharge since 1968, against flat non-glacial controls. And a stage threshold therefore has a discharge vintage. | **FACT** (computed) for the drift; **INFERENCE with strong corroboration** for the ~9–11 % Mount Vernon conveyance change | Theil–Sen trends on stage residuals across fifteen gauges; rating-independent measured pairs; cross-section surveys; the agency's own rating remark. |
| **L18** | **A falling stage during a rising upstream hydrograph is the documented signature of a downstream breach or spill on this exact reach**, and must be surfaced as an anomaly rather than read as improvement. | **FACT** | USACE's account of the Fir Island failures in November 1990. |
| **L19** | **HEFS is live and machine-readable at all six configured forecast points** — 45 members, flow only, one cycle a day, ~10 cycles of archive — **and is MODELED, not OFFICIAL_FORECAST**; at the four stage-defined points an exceedance fraction is not computable without a conversion the platform forbids. | **FACT** (measured live) | The ensemble API, queried 2026-08-24. |
| **L20** | **The official forecast is an observation of a judgement, not a reproducible model output**, because the NWS's operational data assimilation is unlogged forecaster modification — **and at a regulated point it is conditional on an unpublished operating plan.** | **FACT** | The RFC's own documentation and the national ensemble system description; the project water control manual for the conditionality. |
| **L21** | **The official forecast's error scale here is known:** the Mount Vernon crest forecast over-predicted by **+4.57 ft** at its peak during Event Zero, in a flip-flop sequence. | **FACT** | The platform's own Event Zero record. |
| **L22** | **Some verification strata will never become verifiable**, with the counts: 0.16–0.77 % daily base rates; Green near Auburn *moderate* n = 2 since 1990, *major* n = 0 post-dam. **UNVERIFIABLE is a verdict.** | **FACT** (computed) | USGS instantaneous peaks and daily values against the official categories. |
| **L23** | **The platform's value is confined to low-cost precautionary actions**, because relative economic value peaks where the cost-to-loss ratio equals the base rate — under about 1 % here. | **INFERENCE** from the standard cost–loss result and the measured base rates | Cost–loss decision model; measured base rates. |
| **L24** | **Runoff generation here is saturation-excess and subsurface, with a factor-of-twenty margin**: infiltration capacity >200 mm h⁻¹ against maximum rain rates of ~10 mm h⁻¹, so the only Hortonian surfaces are roads, compacted ground and impervious cover — **which is what licenses reasoning about duration rather than intensity.** Hourly intensity in the largest western-Cascades floods was 2.7 ± 0.9 mm h⁻¹. | **FACT** for the measurements; **ASSUMPTION** for the platform-wide simplification | Western Cascades experimental-forest measurements; the region's own regulatory hydrology. |
| **L25** | **These basins span two runoff-generation regimes** — mountain-subsurface and lowland-till — and the same rainfall produces different physics in the upper and lower parts of several of them. `runoff_regime` belongs beside `regulation_class`. | **INFERENCE** from surficial geology and the region's design manual | The regional design manual already encodes till versus outwash as separate runoff-generation classes. |
| **L26** | **Blocking is computable and belongs on the display as a qualifier of QPF confidence, never as a multiplier:** `M = Nh/U`, with measured Olympic sector means of 0.7 / 1.1 / 2.5 and a per-event spread that forbids inferring it from storm type. | **FACT** for the measurements; the derived flag is **DERIVED/EXPERIMENTAL** | Eighteen instrumented frontal periods over the Olympics. |
| **L27** | **AR families amplify Cascade runoff by 150–300 % over sparse clusters**, and about half of all ARs belong to one. Event Zero was a family. | **FACT** | Cool-season reanalysis climatology of clustered AR landfalls. |
| **L28** | **The observing floor is quantified and signed:** radar QPE adequately covers only ¼–⅓ of the coastal western US and reads <50 % of gauge values in the heaviest precipitation; cool-season gauge undercatch is 5–15 / 15–20 / 25–40 % by elevation band; and gridded-QPE cells filled by a climatological downscaling are MODELED, not OBSERVED. | **FACT** | Regional radar assessment; regional undercatch study; the QPE product's own documentation. |
| **L29** | **Post-fire rain-on-snow is a mappable amplifier** — 14.3 against 6.2 mm d⁻¹ of meltwater, and 151 against 39 mm SWE in a single event — while **plot-scale clearcut amplification does not scale to the basin** and must never be a basin-level term. | **FACT** | Western Oregon Cascades burned/unburned comparison; the 1,000-peak western Cascades harvest study. |
| **L30** | **The refusal to compute a recurrence interval is now a defended position, not an implicit choice**, with four independent grounds and three honest substitutes (rank in record, nearest observed analogue, day-of-year percentile). | **FACT** for the grounds; the doctrine sentence is a **decision** | §12B. |

---

## 7. What this delta does not resolve

Carried forward as OPEN QUESTIONs, in the order they block work:

1. **Basin hypsometry does not exist.** Every rain-exposed and rain-on-snow-exposed statement in §7
   and §4 is blocked until it does. This is the single largest structural blocker in the delta.
2. **Homogeneity and regulation epochs are unenumerated.** §12A's reference-period rule cannot be
   implemented without them; the split dates used to size the effect are working values.
3. **Per-basin cross-barrier bearings are published for two of eight basins.** L1 and L2 are only
   partially actionable until the other six are fitted from the platform's own record.
4. **The NWM v3.1 assimilation-tail length is unmeasured**, so the agreement window's exposure is real
   but unquantified.
5. **The interaction hindcast has not been run.** Whether antecedent state adds skill in western
   Washington *conditional on the forcing* is unanswered, and a null result would be a genuine finding.
6. **No AR-category-to-flood verification exists for Washington.** The only published mapping anywhere
   is for a Californian basin.
7. **Section 7 reservoir status has no public feed**, and forecast pool trajectories are catalogued but
   not served.
8. **Whether the phase-interference signal scales** from a 64 km² experimental basin to a
   500–3,000 mi² Washington basin is unknown, and it is the most promising unexploited signal in the
   snow domain.
9. **The upper-tail behaviour of `g(Q)`** is untested against a real flood, and the method's own scale
   limit is not respected by six of the seven gauges it was fitted on.
10. **The copula family for the river–coastal joint distribution is unfitted**, so no joint probability
    may be displayed.
