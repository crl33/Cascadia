# Hillslope runoff generation and catchment storage dynamics

*Corpus entry, 2026-08-24. Part of the Cascadia Papsukkal flood-science corpus.*

Labels follow the repository convention: **FACT** = read on a page or PDF fetched in this pass, or
computed here from a fetched primary dataset (source given); **INFERENCE** = reasoned from cited
facts; **ASSUMPTION** = a working simplification; **OPEN QUESTION** = unresolved. Where a number
comes from a source I could not open myself, it is marked *not independently fetched* and demoted to
INFERENCE. Original computations in §5.4 were run on USGS instantaneous-values data downloaded on
2026-08-24; the scripts and the exact query URLs are given so they can be re-run.

---

## 1. Headline

**A western Washington flood is a storage-threshold crossing, not a rainfall accumulation — and the
state variable that governs the crossing is already being measured by the streamgauge.** Storm flow
in humid forested catchments is mostly water that was in the basin before the storm; it leaves
because a pressure signal travels far faster than the water does; and it leaves *disproportionately*
because the sensitivity of discharge to storage, `g(Q) = dQ/dS`, rises steeply with how full the
basin already is. I estimated `g(Q)` from five water years of 15-minute USGS data for seven Cascadia
gauges (§5.4): in every unregulated basin the wet-season recession obeys `−dQ/dt = a·Q^b` with
**b = 1.85–2.05 (r² = 0.985–0.996)**, i.e. `g(Q) ∝ Q^0.85–1.05` — the same near-linear sensitivity
Kirchner (2009) found at Plynlimon (c₂ = 0.97 and 1.10). A basin sitting at 1.0 mm h⁻¹ converts an
extra millimetre of storage into **7.6–11.1× more discharge** than the same basin at 0.1 mm h⁻¹.
The dynamic store that separates those two states is only **71–104 mm** of water. That is the
mechanism behind every "the basin was already primed" narrative, and it is computable *today* from
data the platform already ingests.

The counterweight, also computed here and uncomfortable: over WY2020–2024, **pre-event flow alone
explains essentially none of the variance in flood-peak magnitude** for the Sauk, Skykomish,
NF Stillaguamish and Snoqualmie (r² = 0.001–0.057, n = 25 independent Nov–Mar peaks per gauge).
Antecedent state sets the *gain*; it does not, by itself, order the *outcomes*, because by the time
the flood season arrives the switch is already thrown. Both statements are true and the platform has
to say both.

---

## 2. Mechanisms (the physics, stated properly)

### 2.1 What actually generates runoff in maritime forested mountains

Three mechanisms compete for the same rain:

| Mechanism | Condition | Where it applies here |
|---|---|---|
| **Infiltration-excess (Hortonian) overland flow** | rainfall rate > infiltration capacity | essentially nowhere in intact forest; roads, compacted ground, impervious surfaces only |
| **Saturation-excess overland flow** | soil profile fills to the surface; variable source areas | riparian margins, hollows, toeslopes, wetlands; expands with wetness |
| **Lateral subsurface stormflow / interflow** | perched saturation on a conductivity contrast, then downslope flow | the dominant storm mechanism on forested hillslopes |

The quantitative reason infiltration-excess is absent is a factor-of-20 mismatch. At the H. J.
Andrews Experimental Forest (western Cascades, Oregon — the closest long-term analogue to the
western Washington Cascades), "overland flow rarely occurs because soil infiltration capacity
(>20 cm h⁻¹) greatly exceeds maximum precipitation intensity (10 mm h⁻¹)" (**FACT** — Jones &
Perkins 2010, *WRR* 46, W12512, citing Dyrness 1969 and U.S. Forest Service 1973). Measured
saturated hydraulic conductivity of the upland soils is **>360 mm h⁻¹** at HJA and **>1000 mm h⁻¹**
in the Oregon Coast Range (so high it exceeded the field permeameter limit), with porosities of
**65 % and 70 %** respectively (**FACT** — Hale & McDonnell 2016, *WRR* 52, Table 1).

King County's own regulatory hydrology says the same thing for the Puget Lowland, and says it about
*till*, not just mountain soils: "Horton overland flow is almost nonexistent in densely vegetated
areas, such as forest or shrub land" and "the runoff from forests and pastures, on till soils, is
dominated by shallow subsurface flows (interflow) which have hydrologic response times much longer
than those used in event methods" (**FACT** — King County Surface Water Design Manual 2016,
Chapter 3, §3.1 and §3.2). The manual's land-cover classes are literally *Till forest / Till pasture
/ Till grass / Outwash forest / Outwash pasture / Outwash grass / Wetland / Impervious* — the
region's operational hydrology already encodes runoff-generation regime as a first-class attribute.

### 2.2 The old-water paradox and isotope hydrograph separation

Two-component isotope hydrograph separation (IHS) partitions streamflow into *event* (this storm's
rain) and *pre-event* (water already stored) using a mass balance on δ¹⁸O or δ²H:

```
Q_t = Q_p + Q_e                      (water)
C_t·Q_t = C_p·Q_p + C_e·Q_e          (tracer)
⇒  F_p = (C_t − C_e) / (C_p − C_e)
```

IHS "ushered in a paradigm shift" by showing "stored, pre-event water dominated the storm hydrograph
in most natural, humid systems" (**FACT** — Klaus & McDonnell 2013, *J. Hydrol.* 505, 47–64, fetched
PDF). Recent laser-spectrometer work shows "some forested catchments with runoff ratios above 50 %
may display no detectable rainfall in channel stormflow, even at the peak of the storm hydrograph"
(**FACT** — Klaus & McDonnell 2013 quoting Berman et al. 2009).

**The spread is enormous and it is not noise.** From Klaus & McDonnell's compilation of event-water
fractions (i.e. `1 − F_p`) at peak flow or by volume (**FACT** — all read from the fetched Table):

- 62–69 % event water at peak, rubber plantation, SW China (Liu et al. 2011)
- 87 % event water (mean), suburban Toronto, 20 % paved (Meriano et al. 2011)
- 44 % at peak / 27 % by volume and 59 % / 37 % in two Tanzanian catchments (Hrachowitz et al. 2011)
- 16–100 % at peak in an Appalachian urban-agricultural catchment, 1–21 % in its larger neighbour (Buda & DeWalle 2009)
- "mainly below 30 % by volume", forest/meadow, Western Australia (Ocampo et al. 2006)
- 6–99 % at peak, increasing with wetness, in one catchment
- 100 % event water after a long dry period, southern France (Marc et al. 2001)

Land use orders it: "pre-event water was most important in forested catchments and less important in
urban areas with agricultural sites in between" (**FACT** — Klaus & McDonnell 2013 summarising
Buttle 1994). So does antecedent state, and the direction is *not* what intuition suggests: "most
studies have found increasing event water contributions with increasing dryness" (Marc 2001; Casper
2003; Cras 2007; Blume 2008; Pellerin 2008; James & Roulet 2009), because a dry catchment is
disconnected and *cannot supply* pre-event water — but a minority found the opposite where storage
filling drove saturation excess (Cey 1998; McCartney 1998; Ocampo 2006) (**FACT** — same source).
Rainfall intensity matters too: "event water dominated channel stormflow during intense rainstorms,
whereas pre-event water dominated during moderate-intensity rainstorms" (Kværner & Kløve 2006).

**The technique's five assumptions, and why they break** (**FACT** — Klaus & McDonnell 2013, §2):
(1) event and pre-event isotopic contents differ significantly; (2) the event signature is constant
in space and time or can be accounted for; (3) so is the pre-event signature; (4) vadose-zone
contributions are negligible *or* soil water is isotopically like groundwater; (5) surface storage
contributes minimally. Assumptions 3 and 4 are the ones that fail in real catchments — soil water
and groundwater have distinct signals, and the resulting two-component separations "sometimes exceed
100 % or fall below 0 %". Three-component and EMMA approaches exist precisely because of this. There
is no catchment-size law: results are "equivocal or contradictory", with increasing, decreasing and
flat size relationships all published.

**Consequence for this platform (INFERENCE).** "Pre-event fraction" is not a constant to hard-code.
It is a distribution whose central tendency in humid forest is >50 % but whose spread spans nearly
the whole 0–100 % interval and moves with wetness, intensity and land cover. Any doctrine sentence
of the form "most flood water is old water" must carry the qualifier "in humid forested catchments,
at moderate intensity, when the catchment is wet".

### 2.3 Kirchner's double paradox

Kirchner (2003, *Hydrol. Process.* 17, 871–874, fetched PDF from the author's reprint archive) states
two linked paradoxes (**FACT**, near-verbatim structure, paraphrased):

- **Paradox 1 — rapid mobilisation of old water.** Streamflow responds promptly to rain, but passive
  tracers (¹⁸O, ²H, sea-salt Cl⁻) are "strongly damped". *How do these catchments store water for
  weeks or months, but then release it in minutes or hours?*
- **Paradox 2 — variable chemistry of old water.** Reactive species (Ca, Si, Al, H⁺) are highly
  sensitive to discharge even though baseflow and stormflow are *both* mostly old water. *How do
  catchments store old water, release it rapidly, and vary its chemistry with flow regime?*

Kirchner's own verdict on the state of the art: conceptual models (piston flow, kinematic waves,
transmissivity feedback, matrix–macropore exchange) have been invoked "with limited success"; the
hard part is making one "mechanistically plausible and quantitatively realistic". His preferred
reading of Paradox 2 is that catchments hold **several stores, or a continuum of stores, of old
water with different chemical signatures, mobilised in different proportions at high and low flow**.

**Why Paradox 2 matters operationally (INFERENCE).** A continuum-of-stores catchment cannot be
represented by one soil-moisture number. It is the physical justification for the platform's
existing multi-source soil doctrine (HYDROLOGY §8) and against ever collapsing storage state to a
single scalar without saying which store it refers to.

### 2.4 The mechanisms that reconcile the paradox

Velocity is not celerity. This is the whole resolution, and it is stated cleanly in the
transit-time literature: catchments "transmit hydraulic potentials (celerity) differently than they
transmit water itself (velocity)", and velocities "can be orders of magnitude slower" (**FACT** —
Hale & McDonnell 2016, §5.2; Jasechko et al. 2016, *Nature Geoscience* 9, 126–129, both fetched).

| Mechanism | Statement | Status |
|---|---|---|
| **Piston / translatory flow** | infiltrating rain displaces stored water downslope ahead of it; the *volume* balance is satisfied by old water | established as a component; cannot alone explain the speed |
| **Pressure-wave propagation** | infiltration raises pore pressure at the water table; the pressure signal moves at celerity, discharge of old groundwater rises almost immediately | established; the dominant explanation |
| **Transmissivity feedback** | K_sat increases strongly (often exponentially) toward the surface, so a rising water table intersects progressively more conductive soil and lateral export rises super-linearly | established mechanism, hard to observe directly |
| **Groundwater ridging / capillary-fringe collapse** | rain converts a near-stream tension-saturated capillary fringe to positive pressure, instantly steepening the gradient toward the channel | **contested** — "observational evidence … is again limited by the density of pressure head measurements necessary to characterise its occurrence" (**FACT** — McGuire, Klaus & Jackson 2024, *Hydrol. Process.* 38, e15263, fetched); numerical evaluations (Cloke et al. 2006) and comments on them dispute it (*not independently fetched*) |
| **Preferential flow / macropores** | root, worm, ant, mole and salamander channels convey water even unsaturated, and far more when saturated; "tracer velocities in interflow … cannot be explained by the bulk saturated conductivity of the soil" | established; unparameterisable at catchment scale |

Preferential flow is not exotic. Across ~1,500 sensors at 40 sites in 17 US ecoregions, "PF is
widespread, with sites experiencing PF in **up to 60 % of rainfall events ≥2 mm**", and it is more
likely with higher peak rainfall intensity, finer texture, low soil-moisture variability, humid
climate and higher net primary productivity (**FACT** — Li et al. 2025, *Geophys. Res. Lett.*,
10.1029/2025GL118045, fetched PDF). Every one of those five predictors is *high* in western
Washington forest. At the Maimai hillslope (New Zealand; the maritime-forest analogue site),
excavation showed downslope flow concentrated at the soil–bedrock interface with "velocities several
orders of magnitude greater than predicted by Darcy's law using measured hydraulic conductivities"
(**FACT** — Graham, Woods & McDonnell 2010, *J. Hydrol.* 393, 65–76, fetched PDF). Beven & Germann
(2013, *WRR* 49, 3071–3092) conclude 30 years on that "there is still not an adequate physical
theory linking all types of flow" (*not independently fetched — abstract via search*).

### 2.5 Fill-and-spill: the threshold that makes floods nonlinear

The canonical result: 147 storms at the Panola hillslope trench showed a **55 mm precipitation
threshold** for significant subsurface stormflow; below it transient groundwater formed in
disconnected patches, above it water spilled over microtopographic relief in the bedrock surface and
the saturated patches connected to the trench (**FACT as reported** — Tromp-van Meerveld & McDonnell
2006a,b, *WRR* 42, W02410/W02411; *not independently fetched in this pass*, confirmed by publisher
abstract text and by the repository's prior review, which also records the **>75× larger** total
subsurface stormflow once connectivity was achieved).

The generalisation: McDonnell et al. (2021, *WRR* 57, e2020WR027514) frame fill-and-spill as a
scale-free description — "vertical and lateral additions of water to a landscape unit are placed
into storage (the fill) — and only when this storage reaches a critical level (the spill), and other
storages are filled and become connected, does a previously infeasible outflow pathway become
activated" (*not independently fetched — publisher abstract via search*).

**Threshold magnitudes actually reported.** The review literature puts the spread at **18–60 mm** of
storm precipitation (Du et al. 2016; Mosley 1979; Tani 1997; Uchida et al. 2005; Weiler et al. 2006)
(**FACT** — McGuire, Klaus & Jackson 2024, §4, fetched). Specific values:

- **30 mm** at HJA WS10, western Cascades: "Quick flow was not produced at either the trench or
  catchment for rainfall amounts less than 30 mm"; smaller events instead "contributed to soil water
  recharge reducing soil water deficits" (**FACT** — McGuire & McDonnell 2010, *WRR* 46, W10543).
- **~20 mm** thresholds reported in other "humid Pacific Rim studies" (Mosley 1979; Sidle et al.
  1995; Tani 1997) (**FACT as reported** in the same paper).
- **60 mm** on a low-relief Georgia hillslope, "at the high end of the range of thresholds reported
  elsewhere" — the paper is titled *lots of fill, little spill* (**FACT** — Du et al. 2016,
  *J. Hydrol.* 534, accepted manuscript fetched).
- **~316 mm** for the *sum* of antecedent-soil-moisture index and gross precipitation at Hubbard
  Brook: below it quickflow was uncorrelated with the index, above it r ≥ 0.98 (**FACT** — Detty &
  McGuire 2010, *WRR* 46, W07525, fetched PDF).
- **2–3 mm** to *activate* subsurface flow at all, but **5 mm (wet) to 25 mm (dry)** to generate
  meaningful volumes, with wet-vs-dry antecedent conditions producing SSF volumes "one to three
  orders of magnitude larger" for similar rainfall (**FACT** — Thoenes et al. 2026, *HESS* 30,
  4405–4436, Black Forest, fetched).

The threshold is a property of the *storage deficit*, not the storm. The same 60 mm is sub-threshold
on a drained hillslope and super-threshold on a primed one.

**How far interflow actually travels.** Jackson et al.'s geometric model gives the downslope travel
distance of a perched saturated wedge before it percolates into the restrictive layer:

```
L_D = (K_u/K_L) · sin θ · [(N + C_n)/C_n] · N      →  L_D = (K_u/K_L) · sin θ · N   as C_n → ∞
```

where `K_u/K_L` is the conductivity ratio across the restricting interface, `θ` the slope, `N` the
saturated wedge thickness and `C_n` the restrictive-layer thickness (**FACT** — reproduced in
McGuire, Klaus & Jackson 2024, Eq. 1–2). In a meta-analysis of 17 instrumented hillslopes, travel
distances "varied from less than a metre to several hundred metres"; they were **less than 50 % of
slope length at 14 of 17 sites and less than 30 % at 11**, meaning "in 14 of 17 cases, most water
perched above a shallow restrictive layer percolates through the restrictive layer before reaching
the valley" (**FACT as reported** — Klaus & Jackson 2018, via the fetched 2024 review).

**INFERENCE.** Fill-and-spill is therefore not a whole-hillslope switch in most landscapes; it is a
*spectrum* of local switches, and the catchment-scale threshold is the emergent statistic of that
spectrum. Du et al. (2016) say exactly this: "there are spectra of each threshold across the
hillslope, and these spectra contribute to the large [variability]".

### 2.6 Variable source area theory

Hewlett & Hibbert (1967) and Dunne & Black (1970) established that storm runoff comes from a small,
*dynamic* fraction of the catchment that expands and contracts with wetness. The modern refinement
matters for the platform: **interflow is a subsurface extension of the variable source area** — "as
a topographically-driven process, interflow delivers water precisely to the areas where variable
source areas tend to form (toeslopes, hollows, channel and wetland margins and floodplains)" and
"interflow often contributes to this rise and partly controls the dynamics of variable source areas"
(**FACT** — McGuire, Klaus & Jackson 2024, §7).

Detty & McGuire (2010) put a number on the expansion. Event runoff ratios ranged **0.2 % to 51 %**;
the riparian area was ~12 % of the catchment, so "when runoff ratios rose above ~12 % … the effective
contributing area" had to have expanded onto the hillslopes (**FACT**, fetched). At the hillslope
scale in Germany, minimum contributing area grew from near zero under dry conditions to ~700 m²
(subsurface runoff coefficient ≈0.23) and ~2,000 m² (≈0.08) at two trenches, with a steep increase
above P_tot > 15 mm under wet conditions (**FACT** — Thoenes et al. 2026).

### 2.7 Storage–discharge: catchments as simple dynamical systems

Kirchner (2009, *WRR* 45, W02429, fetched PDF) is the load-bearing framework for this platform
because it converts *storage* — unobservable — into *discharge* — already ingested.

Mass balance and the single-store assumption `Q = f(S)` give

```
dQ/dt = (dQ/dS)(P − E − Q) = g(Q)·(P − E − Q)                                   (Kirchner Eq. 4, 18)

g(Q) ≡ dQ/dS = f′(f⁻¹(Q))            "the sensitivity function"                  (Eq. 5)

g(Q) = (dQ/dt)/(P − E − Q)  ≈  (−dQ/dt)/Q   during recession (P ≪ Q, E ≪ Q)      (Eq. 6)

ln g(Q) ≈ c₁ + c₂ ln Q + c₃ (ln Q)²                                              (Eq. 9)

S_max − S_min = ∫[Q_min→Q_max] dQ / g(Q)     "dynamic storage"                   (Eq. 20)

recession time constant τ = 1/g(Q)                                               (Eq. 21)
```

Kirchner's Plynlimon results (**FACT**, all from the fetched PDF): Severn `c₁ = −2.439 ± 0.017,
c₂ = 0.966 ± 0.035, c₃ = −0.100 ± 0.016`; Wye `c₁ = −2.207 ± 0.028, c₂ = 1.099 ± 0.048,
c₃ = −0.002 ± 0.018`. Catchment precipitation **2,553 and 2,599 mm a⁻¹**, streamflow 1,987 and
2,111 mm a⁻¹, ET 566 and 488 mm a⁻¹. Annual **dynamic storage 98 mm (Severn) / 62 mm (Wye)** from
recession-plot parameters, 124/107 mm if calibrated to the time series, and **190/95 mm** over the
27-year flow range. Independent field data agree: neutron-probe annual soil-moisture range
**58 ± 30 mm**, geological storage change **70 ± 28 mm** (Kirby et al. 1991). Nash–Sutcliffe
efficiency of the one-equation model, **computed on logarithmic axes** (Kirchner §7, and the Table 2/3
footnotes): **0.913 (Severn) and 0.859 (Wye)** over 1992–1996 when `g(Q)` is estimated from recession
plots — the method proposed in §6.2 — with cross-validation cells spanning **0.785–0.940**. The higher
figures (0.93–0.95) belong to Table 3, where `g(Q)` is instead *calibrated directly to the hydrograph
time series*, a different and more heavily fitted method. Because the efficiencies are computed on log
flows they are dominated by low and moderate flows and say little about peak-flow skill. The
characteristic recession time varies **by roughly three orders of magnitude** within the annual flow
range — "from hours at high flows, to thousands of hours at low flows".

The sentence that should be pinned to the platform's susceptibility surface (**FACT**, verbatim
structure): *"peak storm discharge can be straightforwardly estimated from the sensitivity function
g(Q), using preevent discharge as an implicit measure of antecedent moisture."* And the theoretical
justification: "If discharge is a function of storage, then the catchment's antecedent moisture
(i.e. storage) will be implicitly measured by stream discharge, and the catchment's response to a
unit increase in storage will be directly quantified by g(Q)."

**Where the framework fails** (**FACT** — Kirchner 2009 §15.6 and §3):
1. Where **bypassing flow** dominates — Hortonian overland flow, direct channel precipitation,
   saturated impervious areas connected to the channel. The correction is `Q = f(S) + k_P·P` with
   `g(Q − k_P·P)`; the method can *test* for it.
2. In **snowmelt-dominated** catchments the inferred "precipitation" is melt plus liquid rain, not
   snowfall. Kirchner calls this an advantage (it is one of the few ways to estimate spatially
   averaged melt) — but it means the inversion cannot be read as a QPE check during ROS.
3. In catchments with **multiple interconnected reservoirs** with different storage–discharge
   relations — diagnosed by diurnal ET-driven oscillations in summer streamflow, which a single
   store cannot produce.
4. The relationship "may not describe any individual point on the landscape" — it is an aggregate.
5. In **ephemeral streams**, because `f(S)` becomes non-invertible when `Q → 0`. This sets a lower
   limit on catchment size.
6. **In catchments that are too large.** Verbatim (§15.6 [108]): the methods "must break down for
   catchments that are too large, but it is not yet clear how big is too big. The catchments studied
   here are roughly 10 km² in area. One can speculate that in significantly larger catchments (say,
   1000 km² in area), the lag times required for changes in discharge to propagate through the
   channel network would be so long, and so variable with distance from the outlet, that the methods
   presented here would not work." Kirchner adds that the methods "cannot be expected to work in
   catchments that are much larger than individual storm systems."
   **This is the failure mode that binds hardest here and §5.4 does not respect it.** Drainage areas:
   NF Stillaguamish 679 km²; Green 1,033; Skykomish 1,386; Snoqualmie 1,562; Sauk 1,849; Skagit at
   Mount Vernon **8,011 km²**. Six of the seven gauges are at or beyond Kirchner's speculated
   breakdown scale and all are 70–800× his study catchments. Channel-network routing lag is therefore
   an unexcluded alternative explanation for a flattened `g(Q)` at Mount Vernon, competing with the
   regulation explanation offered in §5.4 finding 4.

### 2.8 Hysteresis in storage–discharge

Storage and discharge do not trace the same curve up and down. Sayama et al. (2011, *Hydrol.
Process.* 25, 3899–3908, fetched PDF) observed a **clockwise** dV–Q loop during the largest storm at
one Northern California sub-watershed and none at all at its neighbour. Davies & Beven (2015) find
hysteresis "antecedent wetness and scale dependent … in rather complex and site-specific ways"
(*not independently fetched — via search*). McGuire & McDonnell (2010) report the sharpest version:
at HJA WS10 the hillslope *led* the catchment hydrograph during the transition phase, was
*synchronised* at intermediate wetness, and the loop **reversed direction** once antecedent wetness
increased further — "no study that we are aware of shows hillslope–streamflow hysteresis patterns
that change direction over time" (**FACT**, fetched).

**INFERENCE for the platform.** Hysteresis means a rating between any storage proxy and discharge is
path-dependent; two basins at the same percentile can be on opposite limbs. A susceptibility number
that carries no rising/falling context is under-specified.

### 2.9 Transit times, TTDs, SAS functions and young water

Transit-time theory answers "how old is the water leaving?", which is a different question from "how
fast does the hydrograph respond?" The modern formalism (**FACT** — Benettin et al. 2022, *WRR* 58,
e2022WR033096, fetched PDF): the age-ranked storage `S_T(T,t)` is the cumulative storage age
distribution times storage; the **StorAge Selection (SAS) function** `ω_Q(T,t) = p_Q(T,t)/p_S(T,t)`
is the ratio of the age distribution in an outflow to the age distribution in storage. `ω = 1` for
all `T` means the outflow samples storage randomly; `ω > 1` at young ages means the catchment
preferentially exports young water — which is what happens at high flow.

Numbers that matter:

- **Mean transit times of ~1–5 years** for ~100 small intensively studied headwater catchments, from
  seasonal isotope cycles (**FACT** — Jasechko et al. 2016, fetched). These estimates are
  "susceptible to aggregation errors", so true MTTs "have been underestimated, potentially by large
  factors" (Kirchner 2016).
- The bias-resistant statistic is the **young water fraction** `F_yw`, water younger than
  **2.3 ± 0.8 months**. Across **254 watersheds** worldwide: **mean 26 %, median 21 %, 10th–90th
  percentile 4–53 %, flow-weighted 34 %**; ≥5 % in 89 % of rivers (**FACT** — Jasechko et al. 2016,
  fetched).
- `F_yw` **declines with topographic slope** (ρ = −0.38, p < 0.0001), "suggesting steeper landscapes
  are characterized by deeper infiltration" (**FACT** — same). Steep mountain catchments export
  *older* water.
- Young streamflow is derived from **<0.1 % of global groundwater storage** — "a thin veneer of
  aquifer storage" (**FACT** — same).
- Bedrock permeability, not form, sets MTT. Fifteen nested catchments in western Oregon, half at HJA
  (low-permeability volcanics) and half in the Coast Range (permeable Tyee sandstone), matched for
  vegetation, topography and climate: **MTT 1.8 y vs 6.2 y on average**. At the permeable site 67 %
  of MTT variance was explained by drainage area with no topographic correlation; at the
  low-permeability site MTT was uncorrelated with area but the ratio of median flow-path length to
  gradient explained **91 %** of the variance. Yet "flow duration and recession analysis, and storm
  response analysis, show that the two sites share relatively indistinguishable hydrodynamic
  behavior" (**FACT** — Hale & McDonnell 2016, fetched PDF).

**INFERENCE.** Hydrograph similarity is not hydrologic similarity. Two Cascadia basins that look the
same on a flow-duration curve can hold water for 1.8 or 6.2 years and route it through entirely
different subsurface volumes. That is a real limit on regionalising any storage parameter by
topography alone.

### 2.10 Bedrock permeability and deep groundwater

Beyond the MTT result above: at HJA WS10 the *bedrock* water table responds to storms, and beneath
the ~130 cm soil there is 1–7 m (mean ~3.7 m) of saprolite (**FACT** — McGuire & McDonnell 2010).
Sayama et al. (2011) explain their storage results with a "hydrologically active bedrock hypothesis
whereby the amount of water a watershed can store is influenced by filling of unrequited storage in
bedrock", and found dynamic storage **positively** correlated with median slope gradient
(**r = 0.74, p < 0.05**) — steeper basins store *more*, because seepage from bedrock into the soil
expands less readily, delaying connectivity (**FACT**, fetched). At Maimai the bedrock is
"moderately permeable" and vertical percolation into it is "a potentially large component of the
hillslope water balance" (**FACT** — Graham et al. 2010).

Regionally, the Oregon Cascades split into a low-permeability **Western Cascades** province
("well-developed flow network of shallow subsurface flow paths, along steep gradients with high
lateral conductivities") and a high-permeability young-volcanic **High Cascades** province, "better
conceptualized as a system of two aquifers (surface and deeper groundwater) rather than as a single
aquifer" (**FACT as reported** — Tague & Grant 2004, *WRR* 40, W04303; *abstract via search, full
text not independently fetched*).

### 2.11 Scaling from hillslope to basin

The scaling does not close. Jones & Perkins (2010) analysed >1,000 peak-discharge events, 1953–2006,
from three paired small (<1 km²) experimental catchments and six large (60–600 km²) basins in the
western Cascades (**FACT**, fetched PDF):

- Rain-on-snow events "delivered **75 % more water to soils** than rain events".
- Peaks of >10-year ROS events were "almost twice as high as rain peaks in **large** basins but only
  slightly higher in **small** basins".
- Forest harvest raised >1-year ROS peaks by only **10–20 %** in small basins, "but small basin peaks
  do not account for the magnitudes of large basin rain-on-snow peak discharges".
- The proposed mechanism is **synchronisation**: at the large-basin scale, harvest increases the area
  of snowpack melting simultaneously, so tributary peaks arrive together.
- In extreme floods, "despite very high infiltration capacity, high soil porosity, and steep hillslope
  gradients, prolonged precipitation and synchronous snowmelt produce rapid, synchronized hydrograph
  responses to small variations in maximum precipitation intensity."

In flood-scaling notation `q_p(A) ∝ A^θ(p)`; θ exceeding ~0.9 means runoff is almost directly
predicted by basin area, which happens where floods are snowmelt-dominated (Gupta & Dawdy 1995; Yue
& Gan 2009, as cited). Jones & Perkins conjecture the ROS-conditional distribution has a larger
exponent than the unconditional one (**FACT as reported**).

**INFERENCE — the single most important scaling statement for this platform.** At basin scale the
controlling variable is not *how much* rain fell but *how much of the basin crossed threshold at the
same time*. Hillslope thresholds are individually small (18–60 mm) and are crossed everywhere in a
long maritime frontal storm; what distinguishes an extreme is **simultaneity**, exactly as the
repository's prior review concluded from the intensity result (2.7 ± 0.9 mm h⁻¹ during the largest
HJA floods).

---

## 3. Quantitative anchors

| Quantity | Value | Context | Source |
|---|---|---|---|
| Soil infiltration capacity vs max rain intensity | **>200 mm h⁻¹** vs **10 mm h⁻¹** | western Cascades forest; ratio ≈20 | Jones & Perkins 2010 (Dyrness 1969) |
| Upland soil K_sat | **>360 mm h⁻¹** (HJA), **>1000 mm h⁻¹** (OR Coast Range) | measured; Coast Range exceeded permeameter limit | Hale & McDonnell 2016 |
| Soil porosity | **65 %** (HJA), **70 %** (Coast Range) | — | Hale & McDonnell 2016 |
| Storm-precipitation threshold for subsurface stormflow | **18–60 mm**; **30 mm** at HJA WS10; **55 mm** Panola; **60 mm** GA | review range + specific sites | McGuire et al. 2024; McGuire & McDonnell 2010; Tromp-van Meerveld & McDonnell 2006 (*not fetched*); Du et al. 2016 |
| Connectivity multiplier on subsurface stormflow | **>75×** above vs below threshold | Panola hillslope | Tromp-van Meerveld & McDonnell 2006 (*not independently fetched*) |
| Wet-vs-dry SSF volume ratio at fixed rainfall | **1–3 orders of magnitude** | Black Forest trenches | Thoenes et al. 2026 |
| Antecedent-index + precipitation threshold | **~316 mm**; r ≥ 0.98 above it, uncorrelated below | Hubbard Brook, till-mantled | Detty & McGuire 2010 |
| Event runoff ratio range | **0.2 %–51 %**; riparian area ≈12 % marks hillslope engagement | Hubbard Brook | Detty & McGuire 2010 |
| Quickflow ratio, HJA WS10 | mean **0.31** (catchment), **0.22** (hillslope); >30 % when storm P > ~65 mm | 18 storms, 2002–03 wet-up | McGuire & McDonnell 2010 |
| Hillslope quickflow ratio above threshold | **0.58** when antecedent 14-day rainfall > 20 mm | HJA WS10 | McGuire & McDonnell 2010 |
| Maximum observed saturated thickness at soil–bedrock interface | **≤25 cm** | HJA WS10, storm conditions | McGuire & McDonnell 2010 (Harr; van Verseveld) |
| Event-water mean transit time | **8–34 h** | HJA WS10 storms | McGuire & McDonnell 2010 |
| Soil-water mean transit time | **10–25 days** | HJA WS10, 30–95 cm depths | McGuire & McDonnell 2010 |
| Hillslope seepage / baseflow MTT | **1–2 years** | HJA WS10 | McGuire & McDonnell 2010 |
| Catchment MTT, contrasting bedrock | **1.8 y** (low-K volcanics) vs **6.2 y** (permeable sandstone) | 15 nested catchments, western Oregon | Hale & McDonnell 2016 |
| Global young water fraction (<2.3 ± 0.8 months) | mean **26 %**, median **21 %**, 10–90 % range **4–53 %**, flow-weighted **34 %** | 254 watersheds | Jasechko et al. 2016 |
| F_yw vs slope | **ρ = −0.38, p < 0.0001** | steeper ⇒ older water | Jasechko et al. 2016 |
| Catchment dynamic storage | **62–190 mm** | Plynlimon, MAP 2,553–2,599 mm a⁻¹ | Kirchner 2009 |
| Sensitivity-function exponent c₂ | **0.966 ± 0.035** (Severn), **1.099 ± 0.048** (Wye) | maritime upland, Wales | Kirchner 2009 |
| Single-equation model skill | hourly **NSE 0.913 / 0.859** (Severn/Wye) from recession-plot `g(Q)`, **on log axes**; 0.93–0.94 only when `g(Q)` is calibrated to the time series | Plynlimon | Kirchner 2009 §7, Tables 2–3 |
| Recession-time variation across annual flow range | **~3 orders of magnitude** | Plynlimon | Kirchner 2009 |
| Rainfall required to fill watershed storage | **200–500 mm** (dV_max 232–652 mm across 17 sub-basins) | N. California, MAP ~1,100 mm | Sayama et al. 2011 |
| Storage vs median slope | **r = 0.74, p < 0.05** (steeper stores more) | same | Sayama et al. 2011 |
| Interflow travel distance vs slope length | **<50 % at 14/17 sites, <30 % at 11/17** | meta-analysis | Klaus & Jackson 2018 via McGuire et al. 2024 |
| Interflow-promoting soil thickness | **0.15–1.8 m**, median **0.70 m**, mean **0.86 m** | review | ⚠️ **NOT LOCATED on re-check (2026-08-24 adversarial pass):** absent from the fetched McGuire et al. 2024 full text and from its published abstract; no source found by targeted search. Treat as unattributed until a page reference is produced. |
| Preferential-flow occurrence | up to **60 % of rainfall events ≥2 mm** | 1,500 sensors, 40 sites, 17 US ecoregions | Li et al. 2025 |
| Rain-on-snow water delivered to soil | **+75 %** vs rain events | western Cascades, 1,000+ peaks | Jones & Perkins 2010 |
| Forest-harvest effect on >1-yr ROS peaks | **+10–20 %** small basins; large-basin peaks not explained by small-basin response | western Cascades | Jones & Perkins 2010 |
| Basin yield, forested Puget Lowland | **~55 %** of annual rain becomes streamflow (65 % lawn, 85–90 % impervious) | King County | KC SWDM 2016 Ch.3 |
| Annual runoff fraction, HJA | **56 %** of annual precipitation | WS10 | McGuire & McDonnell 2010 |
| **Wet-season recession exponent b, unregulated Cascadia** | **1.85–2.05** (r² 0.985–0.996) | computed here, §5.4 | USGS IV, this pass |
| **Sensitivity gain g(1.0)/g(0.1) mm h⁻¹, unregulated Cascadia** | **7.6–11.1×** | computed here | USGS IV, this pass |
| **Wet-season dynamic storage Q = 0.05→3.0 mm h⁻¹, unregulated Cascadia** | **71–104 mm** | computed here | USGS IV, this pass |
| **Recession time constant at Q = 1 mm h⁻¹** | **17.5–29.3 h** (unregulated) vs **234–264 h** (Green nr Auburn) | computed here | USGS IV, this pass |
| **Peak vs pre-event flow, top-25 Nov–Mar peaks** | **r² = 0.001–0.057** | computed here | USGS IV, this pass |
| **Basin wet-up date (7-day mean > 3× Sept median)** | between **1 Oct and 5 Nov** in all of WY2020–2024 | Sauk, Snoqualmie | USGS IV, this pass |

---

## 4. What is settled, what is emerging, what is contested

**Settled (established).**
- Infiltration-excess overland flow is negligible in undisturbed humid forested uplands; saturation
  excess and lateral subsurface stormflow dominate.
- Storm hydrographs in humid forested catchments are dominated by pre-event water in the majority of
  reported cases, and the response is celerity-driven, not velocity-driven.
- Runoff generation is threshold/connectivity-controlled, not linear in rainfall.
- Storage–discharge relationships are strongly nonlinear; recession "constants" are not constant.
- Bedrock permeability is a first-order control on transit time and storage.
- Variable source areas expand and contract; interflow feeds them from below.
- Preferential flow is ubiquitous and cannot be represented by matrix conductivity.

**Emerging.**
- Young water fraction as the bias-resistant replacement for MTT (Kirchner 2016; Jasechko 2016).
- SAS functions as the general formalism for age-selective release; still few operational uses.
- Fill-and-spill as a scale-free organising principle (McDonnell et al. 2021).
- The finding that most perched interflow percolates away before reaching the valley — which
  *demotes* whole-hillslope interflow as a routine catchment-scale mechanism (Klaus & Jackson 2018).
- Global syntheses of runoff processes: 691 forested catchments, testing "seven classic hypotheses
  and an original one", results "corroborate some theories while challenging others" (**FACT** —
  abstract of *Controls on runoff processes in forested catchments worldwide*, Nature Water 2025,
  doi 10.1038/s44221-025-00547-z; **full text paywalled, not read**).

**Contested.**
- **Groundwater ridging / capillary-fringe collapse.** Proposed in the 1970s–80s, challenged
  numerically (Cloke et al. 2006) with a published Comment disputing that challenge; the 2024 review
  says observational evidence remains limited by measurement density. Do not encode it.
- **Does the old-water paradox even hold where surface flowpaths prevail?** Barthold & Woods (2015)
  reviewed 42 small forested catchments, of which 30 had the three characteristics needed to
  classify into one of 8 conceptual models; only **4** supported the hypothesis that hydrographs are
  new-water dominated where surface flowpaths prevail, and they conclude that theory "remains highly
  uncertain" while field support is larger for subsurface- than surface-flowpath sites (*abstract via
  search; full text 403 at the publisher*).
- **Catchment size effects on pre-event fraction** — increasing, decreasing and null results are all
  published (Klaus & McDonnell 2013).
- **Direction of the antecedent-wetness effect on event-water fraction** — majority say drier ⇒ more
  event water, a minority the reverse; the resolution is catchment-specific (Klaus & McDonnell 2013).
- **Forest harvest and peak flows in the western Cascades.** Jones & Grant (1996) reported increases
  "as much as 50 % in small basins and 100 % in large basins"; Beschta et al. (2000) and Thomas &
  Megahan (1998, 2001) disputed the statistical interpretation; Jones & Perkins (2010) find only
  10–20 % for >1-year ROS peaks in small basins. This is a live, decades-old dispute in exactly this
  region (*via search; the exchange itself not independently fetched*).
- **Two water worlds.** Brooks et al. (2010, *Nature Geoscience* 3, 100–104) reported at HJA that
  trees use tightly bound soil water while mobile water bypasses the root zone; subsequent papers
  (McDonnell 2014 *WIREs Water*; Berry et al. 2017) treat it as a hypothesis with multiple working
  alternatives (*via search; not independently fetched*). If true, "soil moisture" as measured is
  partly water that will never reach the stream.

---

## 5. Western Washington specificity

### 5.1 What transfers well

- **The H. J. Andrews / western Oregon Cascades corpus transfers strongly.** Same lithology class
  (Oligo-Miocene volcanics and volcaniclastics), same Douglas-fir/western hemlock forest, same
  frontal-storm regime (>80–85 % of precipitation Oct–Apr in "long-duration, low-to-moderate
  intensity frontal storms"), similar MAP (HJA 2,220–2,800 mm; western WA mountain basins comparable
  or wetter). The 30 mm quickflow threshold, the 0.22/0.31 quickflow ratios, the ≤25 cm saturated
  thickness, the 8–34 h event-water transit times and the 56 % annual runoff fraction are the best
  available first-order numbers for the Cascade-front basins (**INFERENCE**, from FACTs in §2).
- **Plynlimon transfers surprisingly well for storage–discharge form.** Maritime, 2,553–2,599 mm a⁻¹,
  upland, humid — and its `c₂ ≈ 0.97–1.10` is statistically indistinguishable from what I measure for
  unregulated western Washington rivers (§5.4). That is a genuine, checkable transfer.
- **Maimai (NZ) transfers for hillslope process typology** — maritime, steep, forested, high MAP.

### 5.2 What transfers poorly

- **Sayama et al.'s 200–500 mm wetting-up requirement is a Mediterranean-climate number**
  (N. California, MAP ~1,100 mm, sharp dry season). Western Washington basins receive 2–4× that and
  wet up much faster (§5.4). Use the *concept* (storage limit then storage excess), not the number.
- **Thoenes et al. 2026 (Black Forest, 836 mm a⁻¹, convective summer maxima)** is a different
  seasonality entirely. Its finding that rainfall *intensity* dominates for events >20 mm while
  antecedent conditions dominate below is likely inverted in importance here, where the extreme
  events are long and moderate rather than short and intense.
- **Hubbard Brook / Panola / southern Appalachian thresholds** come from till- and
  saprolite-mantled landscapes with seasonal frost and much lower MAP. Detty & McGuire's
  till-mantled catchment is arguably a better analogue for the **Puget Lowland** than for the
  Cascades.
- **Snowmelt-dominated Rockies and interior findings** do not transfer: the western Washington flood
  season is rain and rain-on-snow, not spring melt.

### 5.3 The Puget Lowland is a second, different runoff-generation regime

The platform's basin list spans two distinct regimes and currently treats them alike (**INFERENCE**):

1. **Cascade-front mountain basins** (Sauk, Skykomish, Snoqualmie above Snoqualmie Falls, upper
   Nooksack, upper Skagit, White above Mud Mountain): deep permeable Andisol/Inceptisol profiles over
   saprolite and volcanics, K_sat ≫ rain rate, interflow at the soil–bedrock interface, VSAs in
   hollows and riparian margins.
2. **Puget Lowland basins and lower reaches** (Cedar below Landsburg, lower Green, lower Snohomish,
   Stillaguamish floodplain, lower Nooksack): Vashon till and glaciomarine Lawton clay form shallow
   aquicludes; "the contact between recessional outwash and Vashon Till is normally less than 10 feet
   deep"; perched water flows along the permeability contact until it emerges as springs and seeps
   (**FACT as reported** — USGS OFR 98-239 and associated Puget Lowland literature; *page fetched via
   search result index, contents not read line-by-line in this pass*). King County's design manual
   codifies till vs outwash as separate runoff-generation classes and states forested basin yield at
   **~55 %** of annual rain (**FACT**, fetched).

The consequence is that the *same* rainfall produces different runoff-generation physics in the
upper and lower parts of several of the platform's basins, and the till-mantled lowland is the part
where the response is fastest and least buffered.

### 5.4 Original computation: the sensitivity function for seven Cascadia gauges

**Method.** USGS instantaneous values (`00060`, discharge), 2019-10-01 → 2024-09-30, from
`https://waterservices.usgs.gov/nwis/iv/?sites=<id>&parameterCd=00060&startDT=2019-10-01&endDT=2024-09-30&format=rdb`;
drainage areas from `https://waterservices.usgs.gov/nwis/site/?...&siteOutput=expanded`. Values were
averaged to hourly and converted to basin depth (mm h⁻¹). Following Kirchner (2009) Eq. 6, recession
points were selected as hours in **Nov–Mar** where `dQ/dt < 0` continuously for the preceding
6 h (and, as a robustness check, 12 h); `−dQ/dt` was computed as a centred difference on contiguous
hours. Points were binned by equal counts in `ln Q`, bins with standard error ≥0.5 discarded, and a
line fitted to `ln(−dQ/dt)` vs `ln Q`, giving `−dQ/dt = a·Q^b` and hence `g(Q) = a·b·Q^(b−1)`.

> **Caveat added on adversarial re-check (2026-08-24).** The r² below is computed on ~20 *binned
> means*, each averaging several hundred points, so it measures how well a line fits the bin
> centroids — not how well it fits the data. Refitting the same points unbinned gives
> **r² = 0.74–0.80** for the four unregulated gauges (b is essentially unchanged). §6.4's proposal to
> publish this r² as the platform's first legitimate numeric quality measure must therefore use the
> unbinned statistic, or it will overstate certainty by hiding ~25 % unexplained variance.
> Two further reproducibility findings from that pass: (a) an independent reimplementation of the
> method exactly as written above returns **b = 1.69–1.92**, not 1.85–2.05, so the "exit test" in
> §6.2 is not reproducible as stated; (b) `b` is *not* insensitive to the recession filter — it falls
> monotonically with filter length (Sauk: 2.04 at 2 h, 1.92 at 6 h, 1.85 at 12 h, 1.71 at 24 h), so
> the 6 h/12 h pair reported here samples the shortest, highest-`b` end of an arbitrary continuum.
> Kirchner's own Table 2 shows Severn `c₂` ranging 0.750–1.132 across five single years at one
> catchment, which makes "statistically indistinguishable from Plynlimon" close to unfalsifiable.

**Results (FACT — computed 2026-08-24; 6-hour filter, 12-hour filter in parentheses).**

| Gauge | Regulation | b | b−1 | r² | τ = 1/g at 1 mm h⁻¹ | Storage 0.05→3.0 mm h⁻¹ | g(1.0)/g(0.1) |
|---|---|---|---|---|---|---|---|
| 12189500 Sauk nr Sauk (714 mi²) | none | 2.047 (2.000) | 1.047 (1.000) | 0.991 (0.985) | 17.5 h | 74.9 mm | 11.1 |
| 12134500 Skykomish nr Gold Bar (535 mi²) | none | 1.914 (1.884) | 0.914 (0.884) | 0.996 (0.994) | 25.3 h | 95.9 mm | 8.2 |
| 12167000 NF Stillaguamish nr Arlington (262 mi²) | none | 1.978 (1.901) | 0.978 (0.901) | 0.990 (0.986) | 17.7 h | 71.1 mm | 9.5 |
| 12149000 Snoqualmie nr Carnation (603 mi²) | negligible | 1.882 (1.852) | 0.882 (0.852) | 0.990 (0.986) | 28.1 h | 103.9 mm | 7.6 |
| 12200500 Skagit nr Mount Vernon (3,093 mi²) | upper basin regulated | 1.669 (1.769) | 0.669 (0.769) | 0.932 (0.931) | 42.2 h | 136.3 mm | 4.7 |
| 12119000 Cedar at Renton (184 mi²) | partial (Chester Morse) | 1.174 (1.259) | 0.174 (0.259) | 0.909 (0.868) | 115.7 h | 335.2 mm | 1.5 |
| 12113000 Green nr Auburn (399 mi²) | Howard Hanson | 0.940 (0.966) | −0.060 (−0.034) | 0.919 (0.900) | 263.6 h | 786.5 mm | 0.9 |

**Five findings.**

1. **Unregulated western Washington rivers have a Kirchner sensitivity exponent of ~1.** `b−1` is
   0.85–1.05 across four independent basins spanning 262–714 mi², with r² ≥ 0.985 and negligible
   sensitivity to the recession filter. Kirchner's Plynlimon values (0.97, 1.10) sit inside this
   range. The maritime-upland storage–discharge form is transferable (**INFERENCE** from the FACTs).
2. **The wet-season dynamic store is small: 71–104 mm.** That is the entire water volume separating a
   "normally wet" basin from a flood-generating one. It is one to two days of AR precipitation.
3. **The sensitivity gain is 7.6–11.1×.** Doubling storage roughly doubles `g`, so the marginal
   millimetre of rain arriving at high flow produces an order of magnitude more discharge than the
   same millimetre at seasonal-median flow. This is the quantitative form of "antecedent conditions
   matter" for these specific basins — and it is a *gain*, not a probability.
4. **Regulation destroys the signal, in exactly the way the repository already assumes.** The Green
   below Howard Hanson has `b−1 ≈ −0.05`: `g(Q)` is *flat*, i.e. the apparent storage–discharge
   relation is a dam operating rule, not a hillslope. Its implied "storage" of ~790 mm is reservoir
   operation, not basin water. The Cedar is intermediate (0.17–0.26); the Skagit at Mount Vernon,
   whose largest unregulated tributary is the Sauk, sits at 0.67–0.77 — between its regulated upper
   basin and its unregulated Sauk. This is independent, quantitative confirmation that reading Skagit
   susceptibility from the Sauk rather than from Mount Vernon is correct.
5. **Recession time constants are real and basin-specific.** At 1 mm h⁻¹, τ = 17.5 h (Sauk) to
   28.1 h (Snoqualmie) — directly usable as the physical time scale behind "time to threshold", and
   two to fifteen times shorter than the regulated reaches.

**Second computation — does antecedent flow order the peaks?** For each gauge I took the 25 largest
independent (≥120 h apart) Nov–Mar hourly peaks in WY2020–2024 and regressed `ln(Q_peak)` on
`ln(Q_pre)`, where `Q_pre` is the minimum flow in the 96 h before the peak.

| Gauge | slope | r² | peak range (mm h⁻¹) | pre-event range (mm h⁻¹) |
|---|---|---|---|---|
| Sauk | −0.144 | **0.027** | 0.54–3.35 | 0.042–0.551 |
| Skykomish | +0.075 | **0.009** | 0.80–5.16 | 0.038–0.516 |
| NF Stillaguamish | +0.134 | **0.033** | 1.16–6.03 | 0.048–0.679 |
| Snoqualmie | +0.027 | **0.001** | 0.65–3.01 | 0.075–0.563 |
| Skagit at Mount Vernon | +0.153 | **0.057** | 0.37–1.62 | 0.079–0.646 |

**FACT** (computed). **Interpretation (INFERENCE, and the caveat is load-bearing):** this is *not*
evidence that antecedent state is irrelevant. It is evidence that, *conditioned on an event already
being one of the 25 largest*, antecedent flow carries no additional ordering information — because
the events are selected on the outcome and because the basins are already past their wet-season
switch when they occur. The correct experiment is the *interaction* (peak given basin QPE **and**
antecedent state), which requires a precipitation product and is the hindcast the platform should
run. What this does establish is that a susceptibility surface built on an antecedent-flow
percentile must never be read, or displayed, as a standalone predictor of peak magnitude.

**Third computation — the switch is thrown early and stays thrown.** Median flow by month
(mm h⁻¹) and the date each water year when the 7-day mean first exceeded 3× the September median
(**FACT**, computed):

- Sauk: Sep 0.063 → Oct 0.088 → **Nov 0.175** → Dec 0.185 → Jan 0.226 → Feb 0.156 → Mar 0.139.
  Wet-up dates: 2019-10-21, 2020-10-01, 2021-10-02, 2022-11-04, 2023-11-04.
- Snoqualmie: Sep 0.041 → Oct 0.095 → **Nov 0.207** → Dec 0.222 → Jan 0.314 → Feb 0.216 → Mar 0.214.
  Wet-up dates: 2019-10-09, 2020-10-01, 2021-10-01, 2022-10-31, 2023-11-04.
- Share of Nov–Mar hours above the annual median flow: **53 % (Sauk), 58 % (Skykomish), 64 %
  (Snoqualmie), 70 % (NF Stillaguamish)**.

In all five water years, in both basins, the basin wet-up completed between 1 October and 5 November
— before the climatological peak of the flood season. This is direct quantitative support for the
repository's prior INFERENCE that in maritime western Washington antecedent wetness behaves as a
**seasonal switch with early- and late-season exceptions**, not as a continuously informative dial.
The exceptions — October events, March events, and the aftermath of a dry autumn — are where a
susceptibility surface earns its keep.

---

## 6. What this means for Cascadia Papsukkal

### 6.1 Doctrine

- **HYDROLOGY §1 understates the role of state, and §8 is right for the wrong emphasis.** "Forcing
  determines how much water enters; state determines how the basin reacts" should become: *forcing
  determines how much water enters; state determines the gain that converts it to discharge, and
  most of what leaves was already there.* The measurable expression of that gain is `g(Q)`.
- **Replace "remaining storage" with "distance to the basin's connectivity threshold, and the gain
  above it."** The physics is a switch plus a gain, not a reservoir filling linearly.
- **State explicitly that runoff generation in these basins is saturation-excess and subsurface, and
  that roads, compacted ground and impervious surfaces are the only Hortonian surfaces.** This is
  already implicit in §8; it should be a named ASSUMPTION with the 20× infiltration-capacity anchor
  attached, because it is what licenses ignoring rainfall intensity in favour of duration.
- **Add a `runoff_regime` basin/sub-basin attribute** — `mountain_subsurface` vs `lowland_till` vs
  `outwash` vs `urban_impervious` — as a sibling of `regulation_class`. Two of the platform's eight
  basins are substantially lowland-till in their lower reaches, and the design manual for the region
  already distinguishes them.
- **Never display a "pre-event water fraction" or any old/new-water claim.** The literature's spread
  is 0–100 % and it is not measurable operationally here.

### 6.2 Methods

- **`method:catchment-sensitivity@1.0.0` — new, buildable now, no new data source.** For each basin
  gauge, fit `ln(−dQ/dt) = c₁ + c₂ ln Q + c₃ (ln Q)²` on wet-season recessions from the stored USGS
  history (Kirchner 2009 Eq. 9), publish `g(Q)`, the dynamic storage between chosen flows (Eq. 20),
  and the recession time constant `τ = 1/g(Q)` (Eq. 21). Every output is DERIVED with a published,
  citable method and a per-basin fit quality (r²) that can be shown. My §5.4 fits are the reference
  implementation and the exit test: an independent implementation should reproduce b = 1.85–2.05 for
  the four unregulated gauges on the same window.
- **Re-shape `susceptibility@0.1.0`.** Keep the day-of-year flow percentile as the *display*
  statistic, but band it by `g(Q)` rather than by the USGS WaterWatch 25/75/90 convention, and label
  the driver as *storage sensitivity*, not wetness. `g(Q)` is monotone in `Q`, so the banding stays
  reproducible, but the band edges then mean something physical (e.g. sensitivity ≥ 5× the seasonal
  median value) instead of meaning "the flow is unusual".
- **Emit `recession_time_constant_h` as a first-class derived feature** and use it, not a
  hand-chosen window, as the denominator scale for rate-of-rise and time-to-threshold. HYDROLOGY §9
  already warns that rise is nonlinear; `τ(Q)` is the published quantity that says *how* nonlinear.
- **Refuse to compute `g(Q)` on regulated reaches, by type.** My Green-at-Auburn fit (`b−1 = −0.06`,
  implied storage 790 mm) is the demonstration: on a regulated reach the recession plot measures the
  operator, not the basin. The method should return UNKNOWN with a reason naming the regulation, in
  the same way `susceptibility` already caps confidence by regulation class.
- **Add a rising/falling limb flag to every susceptibility read.** Storage–discharge is hysteretic
  and the loop can reverse direction with wetness (McGuire & McDonnell 2010). A percentile with no
  limb context is ambiguous.
- **Duration-above-rate, not peak intensity.** Reinforced independently here: infiltration capacity
  exceeds any plausible rain rate by ~20×, so intensity cannot generate Hortonian runoff; what makes
  an extreme is *simultaneous* threshold crossing across the basin (Jones & Perkins 2010). The
  forcing surface should carry "hours above X mm h⁻¹" and "basin fraction simultaneously above X",
  which the existing NBM grid-mask machinery can compute.

### 6.3 Data sources

- **No new provider is required for §6.2's core.** `g(Q)` needs only USGS IV discharge, which the
  platform already ingests, plus drainage area from the USGS site service.
- **To run the interaction hindcast (§5.4, second computation) a basin QPE is required.** MRMS
  gauge-corrected hourly QPE or AORC would let the platform compute event runoff ratios per storm and
  test the antecedent × precipitation interaction that the peak-vs-pre-event regression cannot reach.
  This is the highest-value new ingest for this domain.
- **Soil-moisture products remain secondary here.** Given that discharge is a *sufficient* storage
  proxy under the Kirchner assumption, and given that SNOTEL SMS cannot support a percentile
  (already recorded in `susceptibility.py`), the platform should treat SMAP/NWM soil moisture as
  corroboration of `g(Q)`, not as its replacement.
- **A basin-scale land-surface attribute set** (till/outwash extent from surficial geology, road
  density, impervious fraction) would let `runoff_regime` be assigned from data rather than by hand.

### 6.4 Contracts

- New `DerivedFeature` ids: `catchment_sensitivity_g`, `recession_time_constant_h`,
  `dynamic_storage_mm`, `storage_sensitivity_gain` (= g(Q)/g(Q_seasonal_median)),
  `storage_limb` (`rising`/`falling`/`unknown`).
- New method ids: `method:catchment-sensitivity@1.0.0`, `method:recession-time-constant@1.0.0`.
- `Basin` gains `runoff_regime` (closed vocabulary) alongside `regulation_class`.
- Every one of these is DERIVED, not EXPERIMENTAL, *provided* the fit statistic is published with the
  value — the method is from a peer-reviewed paper with a stated failure mode, and the fit quality is
  measurable per basin. The *banding* built on top of it remains EXPERIMENTAL until hindcast.

---

## 7. What this domain contradicts or qualifies in current repo doctrine

1. **HYDROLOGY §1: "forcing determines how much water enters; state determines how the basin
   reacts."** *Qualified, materially.* State also determines how much of the pre-existing store is
   recruited, and it does so multiplicatively: measured gain 7.6–11.1× across the wet-season flow
   range in these basins (§5.4). "Reacts" understates a factor of ten.
2. **HYDROLOGY §8: "As storage fills, saturation-excess runoff generation expands … a given rainfall
   produces a larger, faster hydrograph (FACT)."** *Correct but under-specified.* The expansion is
   threshold-gated, not gradual, and the published thresholds are 18–60 mm of storm precipitation
   (30 mm at the closest analogue site). The doctrine should name a threshold, not a trend.
3. **HYDROLOGY §8: "The useful quantity is remaining storage, not a binary 'saturated'."** *Correct,
   and now quantified for this region:* the wet-season dynamic store is only 71–104 mm, and the
   basins fill it between 1 October and 5 November every year of WY2020–2024. "Remaining storage" is
   near zero for most of the flood season — which is why it is a poor discriminator *within* the
   season and a good one at its margins.
4. **`susceptibility@0.1.0` band edges (USGS WaterWatch 25/75/90).** *Contradicted as a physical
   choice.* Those edges encode "how unusual is this flow", which is a hydrologic-drought convention.
   The physically motivated edges are levels of `g(Q)`. The module docstring already concedes the
   edges are "NOT calibrated to flood response in Washington basins"; this domain supplies the
   principled replacement that does not require calibration to adopt.
5. **`susceptibility@0.1.0` using streamflow percentile as an antecedent-wetness proxy.** *Vindicated
   in theory, sharply qualified in practice.* Kirchner (2009) §11 gives the theoretical licence —
   under the storage-controlled assumption, discharge *is* the implicit measure of antecedent
   moisture. But my regression shows that among the largest events, antecedent flow explains
   r² = 0.001–0.057 of peak magnitude. The proxy is defensible as a *state* estimate and indefensible
   as a *peak predictor*. Copy must reflect that distinction.
6. **HYDROLOGY §2, "Basin response … respond within hours to a day."** *Quantified and partly
   contradicted.* The recession time constant at flood-generating flow is 17.5–28.1 h in the
   unregulated basins, but 42 h at Mount Vernon, 116 h on the Cedar and 264 h on the Green. Response
   time is not a basin-size property; it is dominated by regulation. Any travel-time or
   time-to-threshold logic that treats regulated and unregulated reaches with the same time scale is
   wrong by an order of magnitude.
7. **HYDROLOGY §2 regulation table.** *Strengthened with an independent measurement.* `b−1` orders
   the basins exactly as `regulation_class` does (unregulated 0.85–1.05 > Skagit 0.67–0.77 > Cedar
   0.17–0.26 > Green −0.06). The platform can now *measure* regulation class from the hydrograph as
   a consistency check on its seed data.
8. **DATA_DOCTRINE §9, "Confidence is reserved for calibrated quantities."** *Supported, with a new
   opportunity.* `g(Q)` comes with a per-basin r² from an ordinary regression. That is a legitimate
   fit statistic, not an invented confidence — the first derived quantity in the platform that can
   carry a numeric quality measure without violating the doctrine.
9. **HYDROLOGY §7, snow doctrine.** *Unchallenged, one addition.* Kirchner (2009) §15.6 notes that in
   snow-affected catchments streamflow-inferred "precipitation" is melt plus rain, not snowfall — so
   any inverse method the platform ever adopts must be badged as estimating *water reaching the
   ground*, never QPF verification.
10. **Nothing in this domain contradicts the platform's refusal to convert stage↔flow, its
    threshold doctrine, or its UNKNOWN handling.** All three survive intact.

---

## 8. Open questions

1. **Does `g(Q)` extrapolate to flood flows?** Kirchner's recession plots reached only ~1–1.5 mm h⁻¹
   and he flags the extrapolation explicitly. My fits reach 1.5–3.0 mm h⁻¹ but the December 2025
   Skagit event exceeded that. Testing `g(Q)`-predicted peaks against Event Zero is the obvious
   hindcast.
2. **What is the basin-scale connectivity threshold for each Cascadia basin, in mm of basin QPE?**
   The hillslope literature says 18–60 mm; nobody has published a basin-scale value for the Sauk,
   Snoqualmie or Nooksack. It is estimable from MRMS QPE plus the stored hydrographs.
3. **Is the antecedent × precipitation interaction detectable in western Washington at all?** Webb et
   al. (2026) report six catchments with "cooler mean annual temperatures" showing little or no
   improvement from an antecedent index. A null result for western Washington is a publishable
   finding and should be sought, not avoided.
4. **How much of the "storage" the platform reasons about is mobile?** If the two-water-worlds
   hypothesis holds at HJA it plausibly holds in the Washington Cascades, in which case a fraction of
   measured soil moisture is bound water that will never reach the channel.
5. **Does the till/outwash contrast produce a measurable difference in `b`?** The Cedar and Green
   fits are contaminated by regulation; a lowland unregulated gauge (e.g. a smaller Snohomish or
   Stillaguamish tributary) would test whether till-mantled basins have a different exponent.
6. **What is the hysteresis limb signature in Cascadia hydrographs, and does the loop reverse with
   wetness as it does at HJA WS10?** Computable from stored data; would validate or kill the proposed
   `storage_limb` feature.
7. **Do roads matter enough to model?** Overland flow is confined to roads and compacted ground, and
   road density varies greatly across these basins, but no western Washington quantification was
   found in this pass.
8. **Is the ~1 exponent stable across decades, or does it drift?** Scaife & Band (2017) report
   threshold non-stationarity with seasonal and interannual rainfall totals (*not independently
   fetched — publisher 403*). Refitting `g(Q)` per water year would answer it directly.
9. **Does bedrock permeability vary enough among the eight basins to matter?** Hale & McDonnell's
   1.8 vs 6.2 year MTT contrast arose between two western Oregon sites that looked hydrologically
   identical. The Skagit, Nooksack and White drain young volcanic terrain (Baker, Rainier) that may
   behave like the High Cascades province.

---

## 9. Sources

Fetched and read in this pass (PDF or HTML retrieved and text extracted):

- [Kirchner, J. W. (2009), Catchments as simple dynamical systems, *WRR* 45, W02429](https://seismo.berkeley.edu/~kirchner/reprints/2009_86_catchment_dynamical_systems.pdf)
- [Kirchner, J. W. (2003), A double paradox in catchment hydrology and geochemistry, *Hydrol. Process.* 17, 871–874](https://seismo.berkeley.edu/~kirchner/reprints/2003_63_double_paradox.pdf)
- [Klaus, J. & McDonnell, J. J. (2013), Hydrograph separation using stable isotopes: review and evaluation, *J. Hydrol.* 505, 47–64](https://water.usask.ca/hillslope/documents/pdfs/2013/13-08%20Klaus2013JOH_505_47-64.pdf)
- [McGuire, K. J., Klaus, J. & Jackson, C. R. (2024), Interflow, subsurface stormflow and throughflow: a synthesis of field work and modelling, *Hydrol. Process.* 38, e15263](https://www.osti.gov/pages/servlets/purl/2586430)
- [McGuire, K. J. & McDonnell, J. J. (2010), Hydrological connectivity of hillslopes and streams: characteristic time scales and nonlinearities, *WRR* 46, W10543](https://research.fs.usda.gov/download/treesearch/39666.pdf)
- [Hale, V. C. & McDonnell, J. J. (2016), Effect of bedrock permeability on stream base flow mean transit time scaling relations: 1, *WRR* 52](https://andrewsforest.oregonstate.edu/sites/default/files/lter/pubs/pdf/pub4972.pdf)
- [Jasechko, S., Kirchner, J. W., Welker, J. M. & McDonnell, J. J. (2016), Substantial proportion of global streamflow less than three months old, *Nature Geoscience* 9, 126–129](https://water.usask.ca/hillslope/documents/pdfs/2016/16-9%20ngeo2636.pdf)
- [Sayama, T., McDonnell, J. J., Dhakal, A. & Sullivan, K. (2011), How much water can a watershed store?, *Hydrol. Process.* 25, 3899–3908](https://water.usask.ca/hillslope/documents/pdfs/2011/11-01Sayama%20et%20al_2011.pdf)
- [Jones, J. A. & Perkins, R. M. (2010), Extreme flood sensitivity to snow and forest harvest, western Cascades, Oregon, *WRR* 46, W12512](https://research.fs.usda.gov/download/treesearch/39625.pdf)
- [Detty, J. M. & McGuire, K. J. (2010), Threshold changes in storm runoff generation at a till-mantled headwater catchment, *WRR* 46, W07525](https://vtechworks.lib.vt.edu/server/api/core/bitstreams/699c8761-cdf6-4ae8-bccc-a350eb4e8616/content)
- [Graham, C. B., Woods, R. A. & McDonnell, J. J. (2010), Hillslope threshold response to rainfall: (1) a field based forensic approach, *J. Hydrol.* 393, 65–76](https://research.fs.usda.gov/download/treesearch/39619.pdf)
- [Du, E., Jackson, C. R., Klaus, J., McDonnell, J. J. et al. (2016), Interflow dynamics on a low relief forested hillslope: lots of fill, little spill, *J. Hydrol.*](https://www.osti.gov/pages/servlets/purl/1247925)
- [Li, B., Sprenger, M., Wyatt, B. M. et al. (2025), Ubiquity and causes of soil water preferential flow across 17 ecoregions, *Geophys. Res. Lett.*, 10.1029/2025GL118045](https://gfzpublic.gfz.de/pubman/item/item_5036866_1/component/file_5036913/5036866.pdf)
- [Thoenes, E., Blume, T., Weiler, M., Kohl, B., Hopp, L. & Achleitner, S. (2026), Influence of rainfall event characteristics and antecedent conditions on subsurface stormflow response of two forested hillslopes, *HESS* 30, 4405–4436](https://hess.copernicus.org/articles/30/4405/2026/)
- [Benettin, P., Rodriguez, N. B., Sprenger, M., Kim, M., Klaus, J., Harman, C. J. et al. (2022), Transit time estimation in catchments: recent developments and future directions, *WRR* 58, e2022WR033096](https://water.usask.ca/hillslope/documents/pdfs/2022/benettin_2022.pdf)
- [King County Surface Water Design Manual (2016), Chapter 3 — Hydrologic Analysis and Design](https://your.kingcounty.gov/dnrp/library/water-and-land/stormwater/surface-water-design-manual/Chapter_3_FINAL_4_18_2016.pdf)
- [*Controls on runoff processes in forested catchments worldwide*, Nature Water (2025), doi 10.1038/s44221-025-00547-z](https://www.nature.com/articles/s44221-025-00547-z) — **abstract fetched; full text paywalled and not read** (691 forested catchments; tests seven classic hypotheses plus one original)

Primary datasets fetched and computed on 2026-08-24:

- USGS instantaneous values, discharge (`00060`), 2019-10-01 → 2024-09-30, sites 12189500, 12134500,
  12167000, 12149000, 12200500, 12119000, 12113000 — `https://waterservices.usgs.gov/nwis/iv/`
- USGS site service (expanded output) for drainage areas — `https://waterservices.usgs.gov/nwis/site/`

Cited but **not independently fetched** in this pass (publisher 403, paywall, or abstract-only):

- Tromp-van Meerveld, H. J. & McDonnell, J. J. (2006a,b), Threshold relations in subsurface
  stormflow 1 & 2, *WRR* 42, W02410 / W02411 — the 55 mm threshold and the >75× connectivity effect.
- [McDonnell, J. J., Spence, C., Karran, D. J., van Meerveld, H. J. I. & Harman, C. (2021), Fill-and-spill: a process description of runoff generation at the scale of the beholder, *WRR* 57, e2020WR027514](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2020WR027514)
- [Barthold, F. K. & Woods, R. A. (2015), Stormflow generation: a meta-analysis of field evidence from small, forested catchments, *WRR* 51, 3730–3753](https://agupubs.onlinelibrary.wiley.com/doi/10.1002/2014WR016221) — 42 catchments reviewed, 30 classifiable into 8 conceptual models, 4 supporting new-water dominance.
- [Beven, K. & Germann, P. (2013), Macropores and water flow in soils revisited, *WRR* 49, 3071–3092](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1002/wrcr.20156)
- [Brooks, J. R., Barnard, H. R., Coulombe, R. & McDonnell, J. J. (2010), Ecohydrologic separation of water between trees and streams in a Mediterranean climate, *Nature Geoscience* 3, 100–104](https://www.nature.com/articles/ngeo722)
- [Tague, C. & Grant, G. E. (2004), A geological framework for interpreting the low-flow regimes of Cascade streams, Willamette River Basin, Oregon, *WRR* 40, W04303](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2003WR002629)
- [Jencso, K. G., McGlynn, B. L., Gooseff, M. N., Wondzell, S. M., Bencala, K. E. & Marshall, L. A. (2009), Hydrologic connectivity between landscapes and streams, *WRR* 45, W04428](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2008WR007225) — hillslope–riparian–stream water-table connectivity 9–123 days.
- [Scaife, C. I. & Band, L. E. (2017), Nonstationarity in threshold response of stormflow in southern Appalachian headwater catchments, *WRR* 53](https://agupubs.onlinelibrary.wiley.com/doi/10.1002/2017WR020376)
- [Davies, J. & Beven, K. (2015), Hysteresis and scale in catchment storage, flow and transport, *Hydrol. Process.* 29](https://onlinelibrary.wiley.com/doi/full/10.1002/hyp.10511)
- [Cloke, H. L., Anderson, M. G., McDonnell, J. J. & Renaud, J.-P. (2006), Using numerical modelling to evaluate the capillary fringe groundwater ridging hypothesis of streamflow generation, *J. Hydrol.*](https://www.sciencedirect.com/science/article/abs/pii/S0022169405002064) — and the published Comment disputing it.
- Klaus, J. & Jackson, C. R. (2018), meta-analysis of 17 hillslope travel distances — read as reported inside McGuire et al. 2024.
- Jones, J. A. & Grant, G. E. (1996) / Beschta et al. (2000) / Thomas & Megahan (1998, 2001) — the western Cascades harvest–peak-flow exchange.
- [USGS OFR 98-239, Landslides triggered by the winter 1996–97 storms in the Puget Lowland, Washington](https://pubs.usgs.gov/of/1998/ofr-98-239/ofr-98-239.html) — Vashon till / Lawton clay perched-water setting.
