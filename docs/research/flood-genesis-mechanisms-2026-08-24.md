# FLOOD GENESIS IN WESTERN WASHINGTON — mechanisms, quantitative weights, and the WY2027 antecedent position

*Research review, 2026-08-24. Labels follow `docs/DATA_SOURCES.md` conventions: **FACT** = read on a
fetched page or computed from a fetched primary dataset (source given); **INFERENCE** = reasoned from
cited facts, not itself read anywhere; **ASSUMPTION** = a working simplification; **OPEN QUESTION** =
unresolved. §8 verifies the claims `docs/HYDROLOGY.md` currently makes. Nothing in the repository was
modified except this file.*

---

## 0. The seven findings that should change how the platform is built

1. **Storm flow is mostly water that was already in the basin.** Isotope hydrograph separation in humid
   forested catchments shows the stream during a storm runs mostly on *pre-event* water. Rain is
   largely a trigger that mobilises stored water, not the water you see. This makes basin storage state
   the magazine and precipitation the primer — the inverse of the intuitive model. (§1)
2. **Runoff generation is a switch, not a dial.** Hillslopes connect to the channel network only above a
   storage threshold; below it they barely contribute. Measured subsurface stormflow was **75× larger**
   once connectivity was achieved. Flood response is therefore threshold-nonlinear by construction. (§1.3)
3. **The AR scale alone is a poor flood predictor.** Only **17%** of AR4–5 events in California produced
   a flood response. Adding a 90-day antecedent-moisture index lifted the fraction of flood-generating
   ARs correctly flagged as hazardous from **63% → 81%**, and the correlation with peak streamflow from
   **0.29 → 0.52**. Forcing and antecedent state are not separable surfaces — the skill lives in their
   *interaction*. This is the sharpest critique of the current three-surface design. (§2.5, §3)
4. **Extreme floods here are long and moderate, not short and intense.** In the largest western-Cascades
   floods on record, hourly precipitation intensity was only **2.7 ± 0.9 mm h⁻¹**. Duration and
   basin-wide simultaneity, not rain rate, make the extreme. (§2.4)
5. **Snowpack's sign is set by energy, not by mass — and "percent of normal SWE" is close to useless for
   flood risk.** What matters is SWE *below the storm's snow level* and whether the pack's cold-content
   deficit has been paid. WY2026 is the proof case: Oct–Feb precipitation **104% of normal**, snowpack
   **~50% of normal** — a textbook *warm* snow drought. The same water year contained both the December
   2025 record floods and an April 2026 statewide drought declaration. (§4)
6. **The Skagit at Mount Vernon needs materially less water than it used to for the same flood stage.**
   From the USGS peak record: 1906 required 180,000 cfs to reach 37.00 ft; 2021 reached 36.99 ft on
   **127,000 cfs** — ~29% less water for the same stage. December 2025 set a record stage of 37.73 ft on
   ~133,000 cfs, ~12% below the 1990 flow that produced a *lower* stage. Stage thresholds on this reach
   are not a stationary target. (§7.1)
7. **Where the water is now: dry basins, a historic El Niño, and a stubbornly negative PDO pointing the
   other way.** Western WA outlet gauges sit at or below their 10th percentile for the date; CPC gives
   **>90%** odds of a very strong El Niño and **69%** odds of a *historic* one; the PDO is **−2.03** and
   has been negative essentially continuously since 2020. The two dominant modes disagree. (§5)

**The through-line.** Items 1–3 say the same thing from three directions: *the basin, not the storm,
decides how much of the storm becomes a flood* — and it decides by crossing thresholds, not by scaling
smoothly. Item 6 adds that even a perfect discharge forecast maps to a *moving* stage.

---

## 1. Framing: a flood is a state transition, not an accumulation

The intuitive model — rain falls, runs downhill, fills the river — is wrong in almost every particular
for humid forested catchments like the western Cascades. Three results establish this.

### 1.1 The old water paradox

Isotope hydrograph separation (comparing the isotopic signature of streamwater against that of the
falling rain) was the technique that broke the intuitive model in the 1970s. It showed that Hortonian
overland flow and rapid delivery of "new" event water to the stream **was not widely applicable**, and
that most water in the stream during storms in humid, forested watersheds is **old, pre-event water**
(FACT — Carleton SERC teaching module; Barthold & Woods 2015 meta-analysis).

Kirchner (2003) named the resulting tension the **double paradox**: catchments store water for weeks or
months, yet release it within minutes of rainfall onset — and the water they release is chemically old
while the response is hydraulically fast (FACT — *Hydrological Processes*, "A double paradox in
catchment hydrology and geochemistry").

Two mechanisms reconcile this (FACT — as summarised in the retrieved literature):

- **Displacement / piston flow** — infiltrating rain pushes previously stored water out ahead of it.
- **Pressure-wave propagation** — infiltrating rain raises pore pressure at the water table; the
  *pressure* signal travels far faster than the *water* does, so discharge of old groundwater increases
  almost immediately. Related mechanisms include groundwater ridging and capillary-fringe collapse.

**Why this matters to the platform (INFERENCE).** If the flood is largely mobilised storage, then the
single most predictive basin quantity is *how much mobilisable water is stored and how well connected it
is* — precisely what `susceptibility` is trying to estimate. The doctrine in `HYDROLOGY.md` §8 ("the
useful quantity is remaining storage, not a binary saturated") is mechanistically correct. But the
framing in §1 — "forcing determines how much water enters; state determines how the basin reacts" —
understates the case: state also determines *how much of the pre-existing store is recruited*, which is
the larger term in the mass balance.

### 1.2 What actually generates runoff here

Infiltration-excess (Hortonian) overland flow requires rainfall intensity to exceed soil infiltration
capacity. Western Cascades forest soils are extraordinarily permeable; at the H.J. Andrews Experimental
Forest, "overland flow does not occur except on roads or surfaces compacted by logging," and "soils
rarely freeze" (FACT — Jennings & Jones 2015, quoting Harr 1977 and Jones & Perkins 2010).

Runoff is therefore generated by **saturation excess** on expanding variable source areas, and by
**lateral subsurface stormflow** through the soil profile and at the soil–bedrock interface. Note the
corollary, which is easy to miss: because overland flow is confined to roads and compacted ground, the
**road network is a first-order runoff-generating surface** in an otherwise non-Hortonian landscape.

### 1.3 Fill-and-spill: the threshold that makes floods nonlinear

Tromp-van Meerveld & McDonnell (2006, *Water Resources Research*) analysed 147 storms on the Panola
hillslope and found a sharp **55 mm precipitation threshold** for significant subsurface stormflow.
Below it, transient groundwater formed in patches but stayed disconnected; above it, water spilled over
microtopographic relief in the bedrock surface and connected the patches downslope (FACT).

The magnitude of the effect is the headline: **total subsurface stormflow was more than 75× larger when
connectivity was achieved than when it was not** (FACT).

The threshold is not a property of the storm — it is the storage deficit of the bedrock depressions,
which is set by antecedent conditions. The *same* 60 mm storm is sub-threshold on a drained hillslope
and super-threshold on a primed one. McDonnell (2021) generalised this as *fill-and-spill* across scales
(FACT — *WRR*, "Fill-and-Spill: A Process Description of Runoff Generation at the Scale of the
Beholder"), and the same mechanism has been documented over frozen ground.

**Consequence (INFERENCE).** A linear or smoothly-banded susceptibility index misrepresents the physics.
The honest structure is a *threshold with a distance-to-threshold*, which is also the structure the
literature in §3 independently recovers from streamflow data.

---

## 2. The forcing: atmospheric rivers, and why IVT is not precipitation

### 2.1 The empirical dominance is near-total

- Neiman et al. (2011, *J. Hydrometeorology*, "Flooding in Western Washington: The Connection to
  Atmospheric Rivers"): **46 of 48 annual peak daily flows** across four western-WA watersheds (two
  Olympic, two western Cascades) occurred with landfalling ARs (FACT).
- Barth et al. (2017, *WRR*): across 1,375 USGS gauges with ≥30 years of record, the Pacific Northwest
  and northern California coast show the **highest fraction of AR-generated annual peaks, ~80–100%**,
  and **the upper tail of the flood frequency distribution is dominated by AR-induced floods** (FACT).

This fully supports `HYDROLOGY.md` §1's "nearly always from atmospheric rivers." It also has a
statistical consequence the doctrine does not yet draw — see §7.5.

### 2.2 The orographic transfer function

IVT is a *moisture flux*, not precipitation. The conversion is the upslope model: precipitation rate
scales with the product of **the wind component parallel to the terrain elevation gradient** and the
**column-integrated moisture**, times the slope. Empirically this works well:

- Neiman et al. (2002): **58–88%** of the variance in surface rain rate over California's coastal
  mountains was explained by upslope flow speed measured near the coast (FACT).
- Ralph et al. (2013): **74%** of rainfall variance accounted for by a linear relationship with upslope
  integrated water vapour flux (FACT).

So the correct scalar is not IVT magnitude but **IVT projected onto the terrain gradient**. For the
west-facing Cascade slopes this makes storm *direction* a first-order term, not a refinement.

### 2.3 The failure mode: blocking and the Froude number

The linear upslope model holds only when the air actually ascends the terrain. The control is the
non-dimensional **Froude number, Fr = U/(Nh)** (U = cross-barrier wind, N = Brunt–Väisälä frequency
i.e. static stability, h = barrier height). When Fr is large the flow rises over the terrain; when Fr is
small the oncoming flow is **blocked or dammed** and diverted along the barrier instead (FACT).

Agreement between dynamical models and the linear upslope prediction is "nearly perfect for highest
Froude number, unblocked cases but degrades dramatically as the index decreases" (FACT).

**Why this is operationally important (INFERENCE).** Blocking moves precipitation *off* the windward
slope and onto the coastal plain and foothills — it redistributes where the water lands within and
between basins. Two ARs with identical IVT and identical orientation can load different basins depending
on stability. Any basin-QPF product that does not resolve this is inheriting the error from its parent
model, which is exactly why `HYDROLOGY.md` §2's insistence on highest-resolution QPF is right, and why
basin QPF must carry its own uncertainty rather than a single number.

### 2.4 Extreme floods are long and moderate, not short and intense

Jennings & Jones (2015, *WRR*) examined the 26 largest floods from 1992–2012 at the H.J. Andrews. All
were rain-on-snow events with initial SWE > 0 and more than 60% of precipitation falling as rain. And
critically: on the day before and the day of these peak discharges, **hourly precipitation intensity was
low — 2.7 ± 0.9 mm h⁻¹** (FACT).

This is a genuinely counterintuitive and load-bearing result. The regional extreme is produced by
*sustained, spatially coherent, moderate* rain over a large fraction of the basin — long enough to carry
the whole catchment past its connectivity threshold (§1.3) — not by a convective burst. Peak-intensity
metrics (mm h⁻¹, 1-hour QPF) are the wrong headline for this hazard; **duration above a moderate rate**
and **basin-fraction simultaneously above it** are the right ones.

### 2.5 The AR scale is a weak flood predictor on its own

The Ralph et al. (2019) AR scale ranks events 1–5 on IVT magnitude and duration. It is a good *storm*
scale and a poor *flood* scale:

> "most high-ranked ARs do not produce flooding, with only **17% of AR4–5 events in California**
> generating flood responses" (FACT — Webb et al. 2026, *Nature Communications*)

An AR4 tells you a lot of water vapour arrived. It tells you comparatively little about whether the
basin converted it to a flood — because that conversion is governed by §1.3 and §3.

### 2.6 AR families and temporal compounding

Fish, Wilson & Ralph (2019, *J. Hydrometeorology*, "Atmospheric River Families: Definition and Associated
Synoptic Conditions") formalised the observation that floods are often associated with **a series of ARs
striking in close succession** — a distinct class of long-duration extreme event (FACT). Subsequent work
established that ARs are "uniquely suited to a temporally compounding perspective because of the
association between successive cyclones and heavy precipitation, and the inherent lag between the end of
the AR event and the time for the hydrologic system to fully recover" (FACT).

Event Zero was exactly this: three ARs (Dec 3–5, Dec 7, Dec 8–11 2025). The first two were not the
disaster; they were what removed the basin's remaining storage so the third could not be absorbed. Under
fill-and-spill, an AR family is the mechanism that *manufactures* super-threshold conditions.

**OPEN QUESTION.** No AR-family or sequence identification exists in the current data model. The forcing
surface's 24/48/72 h cumulative windows partially capture it, but a 5-day gap between two ARs falls
outside every window while remaining hydrologically continuous.

---

## 3. Antecedent state: how much it actually matters, quantified

This is the direct answer to "how relative is snowpack / how much do prior conditions matter," and it is
now well quantified for exactly this coastline.

**Webb et al. (2025, *J. Hydrometeorology*) — "Wet Antecedent Soil Moisture Increases Atmospheric River
Streamflow Magnitudes Non-Linearly."** 43,000+ AR events across 122 U.S. West Coast watersheds,
1980–2023 (FACT):

- A robust **non-linear** relationship between streamflow and antecedent soil moisture in **89% of
  watersheds**.
- Each watershed has a **critical ASM threshold** above which event maximum streamflow is, on average,
  **2 to 4.5× larger**.
- Sensitivity is highest in California and southwestern Oregon — watersheds with shallow, clay-rich
  soils, lower winter precipitation and higher evaporation.

**Webb et al. (2026, *Nature Communications*) — "Antecedent moisture enhances early warning of
atmospheric river flood hazards."** Uses the **90-day Seasonal Standardized Precipitation Index (SSPI)**
as the antecedent proxy, "selected due to its consistent performance across hydroclimatic settings", and
modifies the AR scale by promoting an event one rank when SSPI ≥ 0.5 and demoting it one rank when
SSPI ≤ −0.5 (FACT). Results:

| Metric | AR scale alone | SSPI-modified |
|---|---|---|
| Flood-generating ARs flagged hazardous (California) | 63% | **81%** |
| Flood-generating ARs flagged hazardous (central Chile) | 47% | **64%** |
| Median correlation with peak streamflow (California) | 0.29 | **0.52** |
| Separation of median peak streamflow between adjacent ranks | — | **2.1× larger** |

**The caveat that matters most for Washington (FACT, then INFERENCE).** The paper reports that "only six
catchments, primarily located in settings with **cooler mean annual temperatures**, show little or no
improvement in correlation," indicating limitations in snow-dominated regions.

INFERENCE: western Washington is plausibly in that low-improvement group, for a specific and instructive
reason. A 90-day SSPI discriminates well where winter wetting is *variable*; in maritime western WA, the
basins wet up reliably within a few weeks of the first sustained autumn rain and stay wet until spring.
**The threshold is crossed by default for most of the flood season.** Antecedent moisture is therefore
better modelled here as a *seasonal switch with occasional early- and late-season exceptions* than as a
continuously informative dial — and the exceptions (October and March events, and the aftermath of an
unusually dry autumn) are precisely where a susceptibility surface earns its keep.

This is testable against the platform's own history and should be tested before the susceptibility index
is given any weight. It is the highest-value hindcast experiment available.

---

## 4. Snowpack: the most misunderstood variable in the region

### 4.1 Mass is not the state variable; energy is

A snowpack cannot melt until its **cold content** — the energy deficit required to bring the whole pack
to 0 °C — has been paid. Cold content is a linear function of snowpack mass and temperature, and
"positive energy fluxes into a snowpack must first satisfy the remaining energy deficit before snowmelt
runoff begins" (FACT). The pack then **ripens**: absorbed energy melts grain boundaries and the meltwater
is retained in pore space against gravity up to the pack's **liquid water holding capacity**. Only once
the pack is **isothermal at 0 °C and at holding capacity** does further input produce outflow (FACT).

So a deep, cold pack is a *sink* — it absorbs rain and refreezes it, releasing latent heat that pays down
its own cold content but yielding no outflow. A shallow, ripe, isothermal pack is a *conduit* — rain
passes through and adds its own meltwater. **Identical SWE, opposite hydrologic sign.** This is why
`HYDROLOGY.md` §7's "SWE is storage, not hazard" is exactly right, and why any product that scores SWE
as risk is wrong in both directions.

### 4.2 Rain-on-snow is a turbulent-flux phenomenon

Marks et al. (2001) report that **60–90% of the energy available to melt the snowpack** during
Pacific-Northwest rain-on-snow came from **sensible and latent heat exchange** driven by warm, moist,
windy conditions (FACT). Condensation onto the pack is the dominant single term, because the latent heat
of vapourisation (~2.5 MJ kg⁻¹) is roughly 7.5× the latent heat of fusion (~0.334 MJ kg⁻¹): every
kilogram of water vapour condensing on the snow surface releases enough heat to melt ~7.5 kg of ice.

The heat content of the rain itself is minor. **The wind and dewpoint at pack elevation are the melt
forcing** — this is why `HYDROLOGY.md` §7 correctly lists temperature, humidity and wind as forcing
inputs, and why a precipitation-only forcing surface cannot represent ROS.

### 4.3 The transient snow zone is dynamic, not a band

`HYDROLOGY.md` §2 carries a fixed 1,000–4,000 ft transient snow zone as an ASSUMPTION. Jennings & Jones
(2015) challenge the concept directly:

> "Current concepts and terminology are inadequate: 'rain-on-snow' conditions only rarely lead to extreme
> floods, and **the transient snow zone implies a static area, when in fact the area undergoing melt is
> highly dynamic during storm events**." (FACT)

The repo's *derived* quantities — rain-exposed fraction and rain-on-snow-exposed fraction, computed from
hypsometry ∩ forecast snow level ∩ snow-covered area — are the correct dynamic formulation and should be
treated as primary. The fixed elevation band should be demoted to documentation prose, never a parameter.

### 4.4 Phase interference: why most ROS events are not floods

Jennings & Jones' deeper finding is a timing mechanism. Precipitation arrives in pulses; snowpack outflow
also pulses. In ordinary ROS events the two are out of phase — pulses of incoming precipitation are
"counteracted by pulses of net snowpack outflow displaced by π radians, producing **destructive
interference** and a damped waveform of Q." In the extreme floods, they are nearly in phase, producing
**constructive interference** and "a higher amplitude waveform of Q" (FACT).

The snowpack is normally a *low-pass filter* that smooths the storm. In the rare extreme it stops
filtering and starts amplifying. This is a mechanism no operational product represents, and it explains
why "rain on snow" as a binary flag has such poor predictive value.

### 4.5 Percent-of-normal SWE is the wrong statistic

Three independent reasons (INFERENCE from the above, plus Harpold et al. 2017):

1. **Wrong elevation.** SNOTEL sites sit mostly above the elevations where ROS flooding is generated. A
   basin can be at 90% of normal SWE at 4,500 ft and have nothing at 2,000 ft, which is what a warm AR
   will actually rain on.
2. **Wrong quantity.** The flood-relevant quantity is SWE *below the forecast snow level*, intersected
   with snow-covered area — a different number that can move by a factor of several within one storm as
   the snow level rises.
3. **Unstable denominator.** A ratio to a small climatological median is numerically unstable and
   conveys nothing about absolute mobilisable mass.

### 4.6 Warm vs dry snow drought — and why WY2026 is the definitive case study

Harpold et al. (2017) split snow drought into two mechanisms (FACT):

- **Dry snow drought** — Oct–Mar precipitation *below* normal, SWE below normal. Less water arrived.
- **Warm snow drought** — Oct–Mar precipitation *at or above* normal, SWE below normal. The water
  arrived; it fell as rain instead of being stored.

These have opposite flood implications. Dry snow drought lowers the whole hydrograph. **Warm snow drought
is a flood-relevant state**: the same or more water is delivered, but it runs off immediately, low
elevations are fully rain-exposed, and the pack that would have buffered a mid-winter AR is absent.

Washington's water year 2026 is a textbook warm snow drought, from the state's own declaration
(FACT — WA Dept. of Ecology, 8 April 2026):

| Quantity | Value |
|---|---|
| Oct–Feb precipitation | **104% of normal** |
| Statewide snowpack (late March) | **~50% of normal**, 4th lowest in 40 years |
| Ecology's stated cause | "Too much of that precipitation fell as rain instead of snow, leaving the state with about half of its usual snowpack." |
| Drought declaration | Statewide, 4th consecutive year — a record under the 1989 framework |

**The synthesis that answers the question directly.** Water year 2026 contained *both* the December 2025
record floods (Skagit at Mount Vernon 37.73 ft, a record) *and* an April 2026 statewide drought
declaration. Not a contradiction — the same phenomenon. Normal precipitation delivered as rain rather
than snow produces a record flood in December and an empty reservoir in July.

**So: how relative is snowpack?** Snowpack is not a flood predictor in western Washington. It is a
*modifier whose sign depends on energy state and elevation distribution*, and a low seasonal snowpack is
weak evidence *for* rather than against a dangerous winter, because the most common cause of low
snowpack here is warmth — which is also what makes an AR rain on the whole basin at once.

---

## 5. Where the water is now: the long-term cycle, August 2026

### 5.1 The two dominant modes are pointing in opposite directions

**ENSO — a possibly historic El Niño.** CPC ENSO Diagnostic Discussion, issued **13 August 2026**
(FACT — fetched):

- ENSO Alert System Status: **El Niño Advisory**
- Niño-3.4 anomaly: **+1.4 °C** (July)
- **>90%** chance of a **very strong** event during fall and winter 2026–27
- **69%** chance during Oct–Dec 2026 of "a historic event that would exceed the strength of previous
  El Niño events dating back to 1950 (+2.5 °C or more)"

CPC's seasonal outlook favours **below-normal precipitation over the Northwest** and above-normal
temperatures across much of the West for DJF 2026–27.

**PDO — strongly negative, and persistently so.** From the NCEI ERSSTv5 PDO index (FACT — fetched
`ersst.v5.pdo.dat`), monthly values for 2026: Jan −1.24, Feb −1.00, Mar −1.42, Apr −1.62, May −1.67,
Jun −1.71, **Jul −2.03**. The index has been negative essentially continuously since 2020, reaching
−4.21 in July 2025.

The conventional teleconnections conflict. El Niño → warmer, drier PNW winter, lower snowpack. Negative
PDO → cooler, wetter PNW, higher streamflow. The retrieved literature notes the interaction is real and
not additive: reduced runoff is associated with El Niño **during positive PDO phases**, while increased
runoff coincides with La Niña **during negative PDO phases** (FACT). The current combination — strong
El Niño *within* a strongly negative PDO — is the off-diagonal case, which is exactly the configuration
with the thinnest analogue record.

**OPEN QUESTION.** How many historical winters combine a very strong El Niño with a PDO ≤ −1.5? A short
list of analogues, with their western-WA peak flows, is a bounded and high-value piece of work.

### 5.2 What ENSO does and does not do to flood risk

**What it does — it moves where the ARs land.** El Niño shifts AR landfall latitude **equatorward**;
La Niña shifts it **poleward**, with the average La Niña landfall latitude tending to fall along the
Washington coast (FACT). Over the past 30 years El Niño has brought *more frequent* West Coast
landfalling ARs overall, La Niña fewer — but the frequency increase is concentrated south of Washington.

**What it does not do — it does not control the tail.** ENSO shifts the *seasonal mean* distribution.
Western Washington's floods are single-event phenomena from the upper tail (§2.1), and a single
well-oriented AR of sufficient duration can produce a record flood in any ENSO phase. A seasonal
outlook favouring below-normal precipitation is a statement about the *mean*, not about the maximum, and
must never be rendered as reduced flood hazard.

**INFERENCE — the operationally honest reading for winter 2026–27.** Expect a below-normal snowpack with
high confidence (warm + drier signal, on top of a four-year deficit), which by §4.6 is a *warm snow
drought* signature and therefore *not* protective. Expect fewer AR days at Washington's latitude than
climatology. Expect no reduction whatever in the severity of the ARs that do arrive. The seasonal signal
should be presented as *context for water supply*, never as a flood-hazard modifier.

### 5.3 Current basin state (computed 2026-08-24)

Latest USGS instantaneous discharge against that site's published day-of-year percentiles for 24 August
(FACT — computed from USGS IV and the USGS daily-statistics service; this is the same day-of-year
percentile method `cascade_hydrology.susceptibility` implements):

| Gauge | Now (cfs) | p10 | p25 | p50 | Position |
|---|---|---|---|---|---|
| Skagit at Mount Vernon | 6,780 | 6,570 | 7,530 | 9,240 | just above p10 |
| Sauk at Sauk (unregulated) | 1,190 | 1,390 | 1,590 | 2,030 | **below p10** |
| Skykomish at Gold Bar | 365 | 544 | 643 | 867 | **far below p10** (67% of the p10 value) |
| Snoqualmie at Carnation | 502 | 518 | 621 | 795 | **below p10** |

Statewide context (FACT — UW Climate Impacts Group, 10 August 2026): 20 gauges statewide reporting
**record low** daily streamflow as of 6 August; mountain-basin streamflows below to extremely below
normal; drought expanding on the northern Olympic Peninsula.

**Reading (INFERENCE).** The Sauk is the important row: it is unregulated, so it is a true basin-state
signal rather than an operations artefact — which is why the repo correctly reads the Sauk as the
Skagit's susceptibility proxy. The west-side basins enter WY2027 with depleted groundwater and soil
storage after four consecutive drought years.

**This is not protection.** By §1.3 and §3, a dry autumn raises the storage deficit that must be filled
before hillslopes connect — which delays and damps the *first* events of the season. It does nothing to
the *third* event, and in a maritime climate the deficit is typically erased within a few weeks of
sustained autumn rain. The correct statement is *"the season's first threshold crossing is likely to
require more rain than usual, and its timing is the quantity to watch"* — not *"flood risk is lower."*

---

## 6. Mechanisms absent from the current model

These are the "factors you may not be aware of." Each is real, documented, and currently unrepresented.

### 6.1 The stage–discharge relation at Mount Vernon is not stationary

**This is the most consequential gap, because every official threshold on the reach is defined in stage.**

From the USGS annual peak-flow record for 12200500 (FACT — fetched
`nwis.waterdata.usgs.gov/nwis/peak`), plus the December 2025 values already in `EVENT_ZERO.md`:

| Date | Peak Q (cfs) | Peak stage (ft) | Note |
|---|---|---|---|
| 1906-11 | 180,000 | 37.00 | historic estimate (codes 7, Bd) |
| 1951-02-11 | 144,000 | 36.85 | |
| 1990-11-25 | 152,000 | 37.37 | prior stage record |
| 1995-11-30 | 141,000 | 37.34 | |
| 2003-10-21 | 135,000 | 36.19 | |
| 2006-11-07 | 138,000 | 33.85 | **outlier — 3 ft low for its flow** |
| 2021-11-16 | 127,000 | 36.99 | |
| 2025-12-12 | ~133,000 | **37.73** | **record stage** |

All modern peaks carry qualification code 6 (*discharge affected by regulation or diversion*); no datum
change or site relocation is flagged in the file header.

The drift is large and one-directional: **1906 needed 180,000 cfs for 37.00 ft; 2021 reached 36.99 ft on
127,000 cfs — about 29% less water for the same stage.** December 2025 set a record stage on ~12% less
flow than the 1990 event that produced a lower one.

Candidate mechanisms, all documented for this reach (FACT — Skagit River Hydrology Technical Document,
Skagit County, August 2013, fetched and text-extracted):

- **Aggradation.** "Predicted rates of bed accumulation for 100 years in the Skagit River system vary in
  depth from 4 feet at the mouth of the ... North and South Forks." Bed material from Mount Vernon
  downstream is "predominantly sand" — a mobile bed.
- **Levee confinement.** "The Skagit River downstream from Mount Vernon is fully confined by levees on
  both banks." Confinement raises stage for a given discharge by preventing floodplain conveyance.
- **Backwater and tide.** The gradient from Mount Vernon to Skagit Bay is only **~2 ft per mile**, and
  the tidally-affected reach extends up toward the gauge. On a slope that flat, a downstream water-level
  control has strong leverage on stage at the gauge.
- **Delta subsidence + sea-level rise.** "Olympic Peninsula shorelines are rising whereas the **Skagit
  delta shorelines are sinking**" (FACT — USGS/Skagit Climate Science Consortium).

Two important caveats, stated plainly:

1. **Q here is itself rating-derived.** Peak discharge at this site is computed from stage via a rating
   that USGS shifts as the channel changes. The apparent drift is precisely what a progressively shifting
   rating looks like — which is the *point* (the channel changed) — but separating "channel changed" from
   "rating method was revised" requires the USGS station analysis files, not the peak file.
2. **Unsteady-flow hysteresis is a competing partial explanation.** In a looped rating, the rising limb
   carries *greater* discharge for a given stage and the falling limb *smaller* (FACT). A record stage at
   comparatively low discharge is therefore *not* explained by rising-limb hysteresis; it is more
   consistent with a flattened water-surface slope — i.e. backwater — which points back at the tidal and
   delta mechanisms above.

**The 2006 outlier** (138,000 cfs at only 33.85 ft — over 3 ft below what 127,000 cfs produced in 2021)
is the mirror image and probably diagnostic: stage decoupling downward implies water leaving the channel
upstream of the gauge. The 2013 technical document notes its hydraulic tables come from "infinite levee"
model runs "which assume that no water can escape from the river channel due to spill, levee overtopping,
or levee failure," and separately discusses reanalysis of **Nookachamps Creek coincident flows** — the
off-channel storage area immediately upstream of Mount Vernon. **OPEN QUESTION:** confirm from the USGS
station analysis and county records whether 2006 involved upstream spill, breach, or Nookachamps storage
engagement.

**Implication for the platform.** `headroom` in stage on this reach is measured against a threshold whose
hydraulic meaning is drifting. The platform should (a) never convert stage↔flow itself — already correct
per ADR-0011 and §9 of the doctrine; (b) record the rating shift identifier and date alongside stage
observations; and (c) treat "stage record" and "flow record" as genuinely different claims, which
`EVENT_ZERO.md` already does correctly and deserves to be generalised.

### 6.2 Compound coastal flooding

The lower Skagit, Nooksack, and Snohomish are delta rivers. Flood water level there is a *joint*
function of river discharge, tide stage, and storm surge — and "the highest tides of the year coincide
with the seasons of strongest storms and the biggest river floods" (FACT — Skagit Climate Science
Consortium). Sea level and surge "back up" into the lower river.

The platform currently models discharge and stage but carries **no tide, no surge, and no joint
probability**. For any forecast point in a tidally-influenced reach — Mount Vernon, Ferndale, and the
lower Snohomish — a river-only stage forecast is structurally incomplete. NOAA tide predictions and
observed water levels are free and well-documented, making this a tractable addition.

### 6.3 Sediment supply, volcanic and glacial

The Sauk and the Nooksack drain Glacier Peak and Mount Baker. Mount Baker carries **~1.8 km³ of ice —
more than all other Cascade volcanoes except Rainier combined** (FACT — USGS / Natural Resources Canada).
Debris flows reach these rivers from lahars, **glacial outburst floods**, and moraine landslides, and
while initial deposition takes minutes to hours, "long-lasting down-valley transport of sediment occurs
over a period of **decades** and affects fish habitat, **flood risk**, gravel mining, and drinking water"
(FACT — USGS, Mount Baker lahars and debris flows).

This is the physical supply term behind §6.1's aggradation, and it is episodic: a single outburst can
change downstream conveyance for years. It is also a rare but real *direct* flood mechanism independent
of weather.

### 6.4 Conveyance failure and storage engagement

Levee overtopping, levee breach, log jams, and landslide dams all break the stage–discharge relation, in
both directions, at exactly the moment the platform's numbers matter most. The Skagit historical-peak
literature notes explicitly that "discharge numbers are highly disputed due to their regulatory
importance and complexity of measurement, with factors such as **levee failures and log jams**
complicating gage measurements and estimates" (FACT).

The platform correctly refuses to assert that a levee will hold. The gap is the *observability* one: a
sudden stage drop during a rising hydrograph is a candidate breach signature and should be surfaced as an
anomaly, not smoothed as noise or read as improvement.

### 6.5 Mixed populations: the flood statistics are not one distribution

If ~80–100% of annual peaks are AR-generated and the rest are not (§2.1), the annual maximum series is a
**mixed population** drawn from two different generating processes. Fitting a single distribution
(the LP3 convention) is then statistically improper, and Barth et al. (2017) show the upper tail is
AR-dominated. Bulletin 17C provides a framework for mixed populations (FACT).

**Consequence.** Any recurrence-interval statement ("100-year flood") on these rivers inherits this
issue, *plus* the nonstationary rating of §6.1, *plus* the disputed historic peaks of §6.8. The platform
already declines to compute return periods; this is the rigorous justification for that refusal, and it
should be written down as one.

### 6.6 Forest cover, roads, and land use

Overland flow in these basins occurs essentially only on roads and compacted ground (§1.2), making road
density a direct runoff-generation term. Separately, the effect of canopy openings on rain-on-snow peaks
— whether clearcuts augment ROS melt by exposing snow to wind and turbulent transfer — is a long-running
line of research in this exact region (Harr 1986; Berris & Harr 1987; Marks et al. 2001; Storck et al.
2002) (FACT — as cited in Jennings & Jones 2015). It is a live scientific question, not a settled one,
and it is a genuine per-basin covariate.

### 6.7 Nonstationary forcing and design standards

AR moisture transport is increasing at close to **Clausius–Clapeyron scaling, ~7% per °C** of surface
warming (FACT), and AR condition frequency is projected to increase substantially under high-end
scenarios. NOAA is replacing Atlas 14 with **NOAA Atlas 15**, which explicitly abandons the stationary
assumption and incorporates nonstationary statistical and dynamical modelling to produce present and
projected precipitation-frequency estimates (FACT).

Any threshold, design storm, or climatological percentile the platform stores has a *vintage*. This is
already the doctrine's instinct (thresholds are versioned rows, never updates); Atlas 15 makes it
concrete and imminent.

### 6.8 The historic peaks are contested, and it is regulatory

The 1921 Skagit peak of 240,000 cfs was determined in 1923 by USGS hydrologist James Stewart, and the
1897, 1909 and 1917 peaks were then derived by extending the stage–discharge rating through that single
1921 measurement. A later recalculation using channel roughness verified against the 1949 flood indicated
the 1921 peak "probably was 6.2 percent lower," but USGS did not officially change it because the change
did not exceed the 10% revision guideline and the estimate already carried ±15% error bands (FACT —
USGS SIR 2007-5159 and Skagit County documentation).

So the upper tail of the Skagit record rests on a chain of inference from one 1923 indirect measurement,
with acknowledged ±15% uncertainty, and it is disputed because it sets floodplain regulation. Displaying
these as historical crests without their uncertainty would be exactly the kind of false precision the
project's doctrine exists to prevent.

---

## 7. Verification of the claims `docs/HYDROLOGY.md` currently makes

| # | Repo claim | Label in repo | Verdict | Evidence |
|---|---|---|---|---|
| 1 | Extreme western WA floods are forcing-driven, nearly always from ARs | FACT | **Confirmed, strongly** | Neiman 2011: 46/48 annual peak daily flows; Barth 2017: ~80–100% of annual peaks are AR-generated in the PNW, upper tail AR-dominated |
| 2 | Flood season Oct–Feb, peaking Nov–Jan | FACT | **Confirmed** | Jennings & Jones: >80% of precipitation Nov–Apr; ROS events Nov–Mar; max daily streamflow Dec–Jan |
| 3 | AR scale (Ralph et al. 2019) rates events 1–5 by IVT magnitude and duration | FACT | **Confirmed as a description** — but see #4 | Webb 2026 |
| 4 | *(implicit)* AR intensity is the forcing signal | — | **Materially incomplete** | Only 17% of AR4–5 events in CA produce floods; skill requires antecedent moisture coupling (63%→81%, r 0.29→0.52) |
| 5 | Orientation, duration and temperature matter beyond IVT | FACT | **Confirmed, and quantified** | Upslope model: P ∝ terrain-parallel wind × column moisture; 58–88% (Neiman 2002) and 74% (Ralph 2013) of rain-rate variance. Adds a mechanism the repo lacks: **Froude-number blocking** |
| 6 | Transient snow zone ≈ 1,000–4,000 ft | ASSUMPTION | **Correctly labelled; concept criticised in the literature** | Jennings & Jones: "the transient snow zone implies a static area, when in fact the area undergoing melt is highly dynamic." Keep the derived dynamic fractions; demote the fixed band |
| 7 | Snow level ≈ freezing level − ~1,000 ft | ASSUMPTION | **Correctly labelled; not further verified here** | Repo's own `weather-forecast-models` research file is the standing source |
| 8 | ROS melt is dominated by turbulent sensible/latent flux; rain heat is minor | FACT | **Confirmed, quantified** | Marks et al. 2001: **60–90%** of available melt energy from sensible + latent exchange |
| 9 | SWE is storage, not hazard; sign depends on temperature, pack state, elevation | FACT | **Confirmed, and mechanistically deeper than stated** | Cold content must be paid before any outflow; ripening and liquid-water holding capacity gate the response |
| 10 | Saturation-excess dominates; infiltration-excess is rare in PNW forest soils | FACT | **Confirmed** | H.J. Andrews: "overland flow does not occur except on roads or surfaces compacted by logging" |
| 11 | Frozen ground rarely material in western WA | (parenthetical) | **Confirmed** | H.J. Andrews: "soils rarely freeze" |
| 12 | Remaining storage, not binary saturation, is the useful quantity | FACT | **Confirmed, and sharpened** | Fill-and-spill: connectivity threshold, **75×** stormflow difference; Webb 2025: threshold in 89% of watersheds, 2–4.5× |
| 13 | Streamflow DOY percentile as antecedent-wetness proxy (`susceptibility@0.1.0`) | EXPERIMENTAL | **Reasonable proxy; two caveats** | (a) literature uses soil moisture or 90-day SSPI, not flow percentile — relationship untested here; (b) the response is threshold-shaped, so a linear percentile band misrepresents it |
| 14 | Sauk is unregulated and often dominant; read it rather than the regulated outlet | FACT/design | **Confirmed and well-founded** | Skagit hydrology technical document; Ross/Baker control only the upper basin |
| 15 | Model disagreement is information, never averaged | doctrine | **Confirmed as good practice** | Consistent with mixed-population and threshold-nonlinearity findings |
| 16 | Stage and discharge are different observations; never derive one from the other | FACT | **Confirmed — and more important than the doctrine claims** | §6.1: the Mount Vernon relation has drifted ~29% in flow-for-stage across the record |

No claim in `HYDROLOGY.md` was found to be **wrong**. Two are **incomplete** in ways that matter (#4,
#6), one is **understated** (#16), and one **derived method** (#13) rests on an untested proxy
substitution.

---

## 8. What this implies for the platform, in priority order

1. **Couple forcing and antecedent state.** Keep the surfaces separately *displayed* — that is good
   doctrine — but add an explicit interaction assessment. Webb et al. (2026) provide a directly
   implementable, publication-backed recipe: compute 90-day SSPI, promote/demote the forcing level one
   band at SSPI ≥ 0.5 / ≤ −0.5, and label it as the published method it is. This is the single largest
   available skill gain and it needs no new data source.
2. **Re-shape susceptibility as a threshold, not a linear percentile.** Report *distance to the basin's
   critical antecedent state* rather than a bare percentile band. This matches fill-and-spill physics and
   the empirical 2–4.5× step.
3. **Test the flow-percentile proxy before trusting it.** Hindcast the DOY-flow-percentile susceptibility
   against soil-moisture and SSPI formulations on the platform's own history. Include the §3 hypothesis
   that western WA sits in the low-improvement regime — a null result there is a genuine finding and
   should be published in the doc rather than buried.
4. **Add duration-above-rate to the forcing surface.** Given §2.4, "hours above a moderate rate" and
   "basin fraction simultaneously above it" carry more signal than peak intensity or a 72 h total.
5. **Represent AR sequences.** Add an inter-event recovery term so an AR family is not invisible between
   fixed accumulation windows.
6. **Record the rating shift with every stage observation** on drifting reaches, and keep "record stage"
   and "record flow" as distinct claims everywhere.
7. **Add tide and surge for tidally-influenced forecast points.** NOAA CO-OPS is free and documented;
   without it, lower-river stage is structurally incomplete.
8. **Write the refusal to compute return periods into doctrine**, with §6.5's mixed-population argument
   as the justification. It is currently an implicit choice; it deserves to be an explicit, defended one.
9. **Never render a seasonal ENSO signal as a flood-hazard modifier.** §5.2. It is water-supply context.
   Given a possibly historic El Niño this winter, this is a live risk of misreading, not a hypothetical.

---

## 9. Sources

Primary data fetched and computed on 2026-08-24:

- USGS annual peak streamflow, Skagit River near Mount Vernon (12200500) — `nwis.waterdata.usgs.gov/nwis/peak`
- USGS instantaneous values and daily statistics — `waterservices.usgs.gov`
- NCEI ERSSTv5 PDO index — `ncei.noaa.gov/pub/data/cmb/ersst/v5/index/ersst.v5.pdo.dat`
- [CPC ENSO Diagnostic Discussion, 13 August 2026](https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso_disc_aug2026/ensodisc.shtml)
- [WA Dept. of Ecology — statewide drought declared, 8 April 2026](https://ecology.wa.gov/about-us/who-we-are/news/2026/april-8-statewide-drought-declared-due-to-dismal-snowpack)
- [UW Climate Impacts Group — August 2026 Drought and Streamflow Update](https://climate.uw.edu/2026/08/10/august-2026-drought-and-streamflow-update/)
- [Skagit River Hydrology Technical Document, Skagit County, August 2013](https://www.skagitcounty.net/PublicWorksSalmonRestoration/Documents/Skagit%20River%20Hydrology%20Technical%20Doc_Final_August2013.pdf)

Literature:

- [Neiman et al. 2011 — Flooding in Western Washington: The Connection to Atmospheric Rivers, *J. Hydrometeor.*](https://journals.ametsoc.org/view/journals/hydr/12/6/2011jhm1358_1.xml)
- [Barth et al. 2017 — Mixed populations and annual flood frequency estimates in the western US: the role of atmospheric rivers, *WRR*](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1002/2016WR019064)
- [Jennings & Jones 2015 — Precipitation-snowmelt timing and snowmelt augmentation of large peak flow events, western Cascades, Oregon, *WRR*](https://andrewsforest.oregonstate.edu/pubs/pdf/pub4911.pdf)
- [Tromp-van Meerveld & McDonnell 2006 — Threshold relations in subsurface stormflow: 2. The fill and spill hypothesis, *WRR*](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2004WR003800)
- [McDonnell et al. 2021 — Fill-and-Spill: A Process Description of Runoff Generation at the Scale of the Beholder, *WRR*](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2020WR027514)
- [Kirchner 2003 — A double paradox in catchment hydrology and geochemistry, *Hydrol. Process.*](https://onlinelibrary.wiley.com/doi/10.1002/hyp.5108)
- [Barthold & Woods 2015 — Stormflow generation: a meta-analysis of field evidence from small forested catchments, *WRR*](https://agupubs.onlinelibrary.wiley.com/doi/10.1002/2014WR016221)
- [Webb et al. 2025 — Wet antecedent soil moisture increases atmospheric river streamflow magnitudes non-linearly, *J. Hydrometeor.*](https://journals.ametsoc.org/view/journals/hydr/26/6/JHM-D-24-0078.1.xml)
- [Webb et al. 2026 — Antecedent moisture enhances early warning of atmospheric river flood hazards, *Nat. Commun.*](https://pmc.ncbi.nlm.nih.gov/articles/PMC13009374/)
- [Fish, Wilson & Ralph 2019 — Atmospheric River Families: Definition and Associated Synoptic Conditions, *J. Hydrometeor.*](https://journals.ametsoc.org/view/journals/hydr/20/10/jhm-d-18-0217_1.xml)
- [Harpold et al. 2017 — Defining snow drought and why it matters, *Eos*](https://eos.org/opinions/defining-snow-drought-and-why-it-matters)
- [Roberts-Pierel et al. 2024 — Tracking the evolution of snow drought in the U.S. Pacific Northwest at variable scales, *WRR*](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2023WR034588)
- [Houze 2012 — Orographic effects on precipitating clouds, *Rev. Geophys.*](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2011RG000365)
- [Smith & Barstad 2004 — A linear theory of orographic precipitation, *J. Atmos. Sci.*](https://journals.ametsoc.org/view/journals/atsc/61/12/1520-0469_2004_061_1377_altoop_2.0.co_2.xml)
- [Neiman et al. 2014 — orographic precipitation processes (CW3E)](https://cw3e.ucsd.edu/wp-content/uploads/2016/02/neiman_etal_jhyd2014.pdf)
- [Payne et al. 2020 — Responses and impacts of atmospheric rivers to climate change, *Nat. Rev. Earth Environ.*](https://www.nature.com/articles/s43017-020-0030-5)
- [USGS SIR 2007-5159 — Re-evaluation of the 1921 peak discharge at Skagit River near Concrete, Washington](https://pubs.usgs.gov/publication/sir20075159)
- [USGS — Mount Baker lahars and debris flows](https://www.usgs.gov/volcanoes/mount-baker/science/lahars-and-debris-flows-mount-baker)
- [Skagit Climate Science Consortium — coastal delta flood risks](http://www.skagitclimatescience.org/flood-risk-coastal-delta/)
- [Spicer et al. 2025 — Decomposing a compound flood event in an urban Pacific Northwest estuary, *Earth's Future*](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2025EF006001)
- [NOAA Atlas 15 informational page](https://water.noaa.gov/about/atlas15)
- [Ponce — Rating curves revisited (loop rating / unsteady flow hysteresis)](https://ponce.sdsu.edu/rating_curves_revisited.html)
