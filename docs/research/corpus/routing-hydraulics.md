# Flood routing, hydraulics, and channel non-stationarity

*Corpus entry, 2026-08-24. Part of the Cascadia Papsukkal flood-science corpus.*

Labels follow the repository convention: **FACT** = read on a page/dataset this agent fetched, or
computed by this agent from a primary dataset it fetched (URL and command given); **INFERENCE** =
reasoned from cited facts; **ASSUMPTION** = a working simplification; **OPEN QUESTION** =
unresolved. Every number computed here is reproducible from the fetch commands in §9.3.

---

## 1. Headline

**Between the upstream reservoirs and the levee-confined delta, the Skagit does three things the
platform currently does not represent: it delays the crest by a *distribution* (median 16.9 h
Concrete → Mount Vernon, 9.5–23.8 h observed, and the delay gets *longer* as the flood gets
bigger), it changes the peak by anywhere from −25 % to +28 % depending on whether channel storage
or local inflow wins, and it converts discharge into stage through a relation that has lost about
**9–11 % of its conveyance at flood stage since the 1990s** — a real, independently corroborated
drift, but roughly a third of the 29 % the repository currently asserts, and driven by bed
aggradation, not by the tide.**

The corollary matters more than the numbers: on this reach a stage threshold and a discharge
threshold are two different, slowly diverging statements about the same river, and the platform's
refusal to convert between them (`HYDROLOGY.md` §9, ADR-0011) is not conservatism — it is the only
defensible position.

---

## 2. Mechanisms (the physics, stated properly)

### 2.1 The wave hierarchy

Unsteady open-channel flow is governed by the Saint-Venant equations — continuity plus a momentum
balance whose terms are, in order, local acceleration, convective acceleration, pressure gradient
(water-surface slope), bed slope and friction slope:

```
∂A/∂t + ∂Q/∂x = q_lat                                    (continuity)
(1/g)∂v/∂t + (v/g)∂v/∂x + ∂h/∂x  −  S0 + Sf  =  0        (momentum)
   [local]     [convective]   [pressure]
```

Dropping terms defines the hierarchy (FACT — this is the standard classification set out by
Ponce & Simons 1977 and restated on Ponce's pages, fetched):

| Model | Terms kept | Behaviour | When it is right |
|---|---|---|---|
| **Kinematic wave** | S0 = Sf only | translation, **no attenuation**, no loop rating | steep channels, long flat waves |
| **Diffusion wave** | + pressure gradient ∂h/∂x | translation **with attenuation**; a measurable rating loop | most natural flood waves |
| **Dynamic wave** | all terms | translation, attenuation, dispersion, wave–wave interaction | flat slopes, tidal/backwater reaches, breaches, dam failures |

Ponce's applicability criteria, in dimensionless form (FACT for σ* = 0.17 / 30 % attenuation, read
on the fetched page; the τ* ≥ 171 and τ* ≥ 30 criteria are reported on the same author's pages via
search summary and are **not independently fetched from the primary 1977/1978 papers**):

- kinematic-wave solution within 95 % accuracy after one propagation period requires dimensionless
  wave period **τ\* ≥ 171**;
- diffusion-wave solution within 95 % requires **τ\* ≥ 30**;
- for dimensionless wavenumber **σ\* > 0.17 the wave attenuates by more than 30 %**, which is the
  conventional boundary between "diffusion wave" and "mixed kinematic–dynamic wave".

Roll-wave instability appears at Froude **F = 2** for Chezy friction in hydraulically wide channels,
equivalently Vedernikov **V = 1** (FACT — Ponce, fetched). Western Washington lowland rivers are far
from this; it matters only in steep tributaries and engineered chutes.

### 2.2 Kleitz–Seddon: why the flood wave outruns the water

Kinematic wave celerity is the slope of the rating divided by the top width (FACT — Ponce,
"Kinematic waves demystified", fetched; attributed there to Kleitz 1877 and Seddon 1900, derived
from Mississippi and Missouri observations):

```
c = dQ/dA = (1/B)·(dQ/dh)                                (Kleitz–Seddon law)
```

Because discharge grows faster than area (Q ∝ A^β with β > 1 for any friction law with a
depth-increasing velocity), **c = β·V > V**: the disturbance travels faster than the water. β = 3/2
for Chezy friction in a hydraulically wide channel (FACT — Ponce, fetched); β = 5/3 for Manning
friction in a wide channel (INFERENCE — standard textbook result, reported in a search summary of
the same author's pages, primary derivation not fetched). β falls toward 1 as the section becomes
more triangular and as floodplain storage engages, because widening the top width at high stage
flattens dQ/dA.

**Operational meaning.** A "travel time" derived from mean velocity is wrong by the factor β, and a
travel time derived from crest-to-crest lag on a real river is *also* not c — it is contaminated by
local inflow timing and storage. §5.1 shows both errors quantitatively on the Skagit.

### 2.3 Attenuation

A diffusion wave obeys a convection–diffusion equation with hydraulic diffusivity

```
∂Q/∂t + c·∂Q/∂x = ν·∂²Q/∂x²,      ν = Q / (2·S0·B)      (Hayami)
```

(INFERENCE — the ν = Q/(2 S0 B) form is the standard Hayami/Cunge result; the specific expression
was **not** confirmed on a fetched page in this pass.) Two consequences are load-bearing:

1. **Attenuation scales inversely with bed slope.** Flat reaches diffuse hard; steep reaches barely
   diffuse. The lower Skagit's average bed slope from Concrete to the mouth is **0.045 %**
   (2.4 ft mi⁻¹) and only **~2 ft per mile from Mount Vernon to Skagit Bay** (FACT — USACE/Skagit
   County *Hydraulics Technical Documentation*, fetched; and *Skagit River Hydrology Technical
   Document*, August 2013, fetched). This is a strongly diffusive reach.
2. **Attenuation scales with the inverse square of wave duration.** A long, flat flood wave
   attenuates far less than a short, sharp one over the same distance. This is why the western
   Cascades' characteristic multi-day AR hydrographs arrive at the delta nearly undiminished
   in *stage* even when the peak *discharge* falls (see §5.1 and the 1975 event note in §5.4).

Muskingum–Cunge makes the same physics into a routing scheme with parameters that are hydraulic,
not calibrated (FACT — Ponce, "Muskingum–Cunge method explained", fetched):

```
K = Δx / c            X = ½·(1 − q / (S0·c·Δx))
C0 = (Δt − 2KX)/(2K(1−X)+Δt)   C1 = (Δt + 2KX)/(2K(1−X)+Δt)   C2 = (2K(1−X)−Δt)/(2K(1−X)+Δt)
```

X → 0.5 means no attenuation (pure translation); X → 0 means maximum attenuation. Note that X
contains 1/S0: on the lower Skagit's 0.00045 slope, X is small and attenuation is large.

### 2.4 Looped (hysteretic) ratings

Under unsteady flow the stage–discharge relation is not single-valued. The **rising limb carries
more discharge at a given stage than the falling limb** (FACT — Ponce, "Rating curves revisited",
fetched: "the rising limb … corresponds to greater discharges for a given stage, while the receding
limb corresponds to smaller discharges"). Mechanistically, the water-surface slope is steeper than
the bed slope while the wave is rising and flatter while it is falling; equivalently, the stage
(pressure) wave and the discharge wave are out of phase.

The Jones (1916) monoclinal-wave approximation quantifies it:

```
Q_unsteady / Q_steady  =  sqrt( 1 + (1/(S0·c))·(dh/dt) )
```

(INFERENCE — the Jones form is standard and was confirmed in description by search summaries; the
1916 primary source was not fetched.) Two structural facts follow:

- the loop widens as **S0 decreases** — flat reaches loop most;
- **a pure kinematic wave produces no loop**; a diffusion wave produces a measurable one (FACT —
  Ponce, fetched).

§5.3 applies this to the December 2025 Mount Vernon crest and gets a loop half-width of 1–5 %.

### 2.5 Rating shifts: what USGS actually does

A USGS rating is a base curve plus a time-varying **shift** applied to gage height (FACT — USGS
California WSC training deck *"Ratings are not static"*, fetched, citing Rantz WSP 2175 pp. 348–352):

- shifts arise from "changes in the control such as scour or fill, growth/removal of vegetation, or
  debris accumulation";
- "shifts are used until evidence of a **permanent** change in the rating is documented" — at which
  point a new rating number is issued;
- shift = (rating gage height) − (measurement gage height) at the measured discharge; positive
  ("scouring") shifts mean more discharge for a given stage;
- USGS practice explicitly encodes **within-event asymmetry**: "often will prorate to positive shift
  as velocities increase on a rise to sometime soon after the peak … often will prorate to negative
  shift on a recession as sediment falls out";
- ADAPS measurement-quality uncertainties are **Excellent 2 %, Good 5 %, Fair 8 %, Poor > 8 %**.

That last row is the honesty constraint on everything in §5.2 and §5.3: a 6 % anomaly on a
*Fair*-rated measurement is inside the stated uncertainty.

The underlying geomorphic control is Lane's balance (FACT — same deck, "Modified from Lane, 1955"):
sediment load × grain size ∝ discharge × slope; a reach whose supply exceeds its transport capacity
aggrades, and aggradation is a **negative** (filling) shift — less discharge for a given stage.

### 2.6 Backwater, conveyance loss and storage

- **Backwater control.** Where the downstream water level is imposed (a tide, a confluence, a
  constriction), stage at a section decouples from local discharge. Leverage scales as 1/S0, so a
  reach at 2 ft mi⁻¹ is ~10× more sensitive to a downstream control than one at 20 ft mi⁻¹.
  Crucially, backwater *from an oscillating tide* leaves a detectable oscillation in the stage
  record; §5.5 uses that as a test.
- **Conveyance loss.** Conveyance K = (1.486/n)·A·R^(2/3) in US units. Vegetation raises n;
  sediment reduces A and R. The 2003 Skagit model used channel n = 0.030–0.043 above RM 17.5 and
  0.033–0.035 below, with overbank n = 0.06–0.12 above RM 17.5 and 0.036–0.040 below (FACT —
  Hydraulics Technical Documentation, fetched, Table 6). A shift of n from 0.033 to 0.037 (+12 %)
  costs ~11 % of conveyance at fixed geometry — the same order as the drift measured in §5.2.
- **Floodplain / off-channel storage.** Once flow leaves the channel, stage and discharge decouple:
  the channel's stage stops rising in proportion to the water arriving because the surplus goes into
  storage. Engagement is threshold-like and *duration-dependent* — a storage cell that fills stops
  attenuating. The Skagit's documented cell is the **Nookachamps Creek basin** on the left overbank
  between Mount Vernon and Sedro-Woolley (FACT — Hydraulics Technical Documentation, fetched).
- **Levee effects.** Levees raise stage for a given discharge by removing floodplain conveyance and
  storage. The inverse operation — levee setbacks — has been modelled systematically: a 0.43 km²
  setback produced **0–0.14 m** mean water-surface drop and a 112.5 km² setback **0.26–2.6 m**, a
  260× area increase for only an 18× stage effect, with a minimum effective threshold around
  **0.2–1 km² per km of river** (FACT — Lammers et al., *Modeling the effects of levee setbacks on
  flood hydraulics*, author preprint PDF fetched and text-extracted). Reach-scale field/model
  studies on the Middle Mississippi report 0.20 m (1 km setback) to 1.61 m (optimised) for the 1 %
  flood, and on the Lower Missouri 0.12–0.66 m stage reduction with **peak-discharge** attenuation
  of only 0.04–0.13 % (search-summary numbers; **not independently fetched**). The asymmetry is the
  point: **setbacks and levees move stage a lot and discharge almost not at all.**
- **Breach and overtopping.** A breach is a dynamic-wave event: it removes flow from the channel and
  steepens the local water-surface slope, so the gauge upstream of it **falls** while the flood is
  still rising. §5.4 documents exactly this on the Skagit in November 1990.

---

## 3. Quantitative anchors

| Quantity | Value | Context | Source |
|---|---|---|---|
| Crest lag Concrete → Mount Vernon | median **16.9 h**; range 9.5–23.8 h; sd 3.5 h (n = 12) | events 2003–2025, instantaneous discharge | computed here from USGS IV |
| Lag vs magnitude | r(Q_Concrete, lag) = **+0.65**; ≥100 kcfs median 17.0 h vs <100 kcfs 14.5 h | bigger floods travel *slower* | computed here |
| Peak change Concrete → Mount Vernon | median **−6.1 %**; range **−24.8 % to +27.8 %** | 356 mi² intervening area (11.5 % of basin) | computed here |
| Peak change vs magnitude | r = **−0.57**; ≥100 kcfs median −11.0 %, <100 kcfs median −1.1 % | attenuation is a big-flood phenomenon | computed here |
| Implied crest celerity | **2.3 mi h⁻¹ = 3.4 ft s⁻¹ = 1.02 m s⁻¹** over ~38 river miles | not the kinematic celerity — see §5.1 | computed here |
| In-channel velocity, Concrete → Mount Vernon | **5–10 ft s⁻¹** (§2.4.6.4) | implies kinematic c ≈ 7.5–16.7 ft s⁻¹ | Skagit Hydrology Tech Doc 2013 |
| In-channel velocity, below Mount Vernon, above the tidal reach | **3–9 ft s⁻¹** (§2.4.6.5) | *not* the Concrete→Mount Vernon reach | Skagit Hydrology Tech Doc 2013 |
| USACE hydraulic travel time, Concrete → Mount Vernon | **15–20 h at low flow, 10–15 h at higher discharges** — i.e. USACE documents travel time *shortening* with discharge | **directly opposed in sign to the crest-lag trend in §5.1**; see the caveat there | Skagit Hydrology Tech Doc 2013 §2.4.6.4 |
| Nov 1995 routing | 160,000 cfs Concrete → **141,000** Mount Vernon (−11.9 %) | no levee failure | Skagit Hydrology Tech Doc 2013 |
| Nov 1990 routing | 149,000 cfs Concrete → **152,000** Mount Vernon (**+2 %**) | local inflow + pondage reversed attenuation | Skagit Hydrology Tech Doc 2013 |
| Dec 2025 routing | Sauk 84,800 (12-11 04:30 PST) → Concrete 151,000 (07:15) → Mount Vernon 133,000 (12-12 00:00), stage 37.73 ft (00:15) | −11.9 %, 16.75 h | computed here from USGS IV |
| Bed slope Concrete → mouth | **0.045 %** (2.4 ft mi⁻¹) | strongly diffusive | Hydraulics Tech Doc |
| Gradient Mount Vernon → Skagit Bay | **~2 ft per mile** | high backwater leverage | Skagit Hydrology Tech Doc 2013 |
| Bed aggradation, mainstem RM 10.1–22.4 | **+2.2 ft thalweg, +1.5 ft average bed, 1975→1999** (24 yr; 25 sections listed, the averages taken over the **20** the table does not flag as "questionable"; over all 25 it is +1.6 / +1.2 ft) | ≈0.75 in yr⁻¹ average bed rise | WEST Consultants Table 1, fetched |
| Bed aggradation, North Fork | +2.6 ft thalweg, +1.6 ft bed (1975→1999) | | same |
| Bed aggradation, South Fork | −0.2 ft thalweg, +1.0 ft bed (1975→1999) | | same |
| Predicted 100-yr bed accumulation | **4 ft at the distributary mouths** | forward projection | Skagit Hydrology Tech Doc 2013 |
| Mean annual suspended-sediment load, Mount Vernon | **2.5 Tg yr⁻¹**; 74 % delivered Oct–Mar | 75 yr of daily record (1941–2015), 175 measurements | USGS SIR 2016-5106, fetched |
| Bedload fraction | **1–3 %** of total load, medium–coarse sand (0.25–1 mm) | winter storm flows | USGS SIR 2016-5106 |
| SSC–discharge relation slope change | **+66 %** between 1974–76 and 2006–09 | "implying changes in sediment supply, channel hydraulics, and (or) basin hydrology" | USGS SIR 2016-5106 |
| Conveyance drift at flood stage, 12200500 | **−11.1 %** (pre-2010 vs 2010+, measured pairs normalised to a fixed stage); **−9.2 %** excluding the falling-limb 2025 measurement | see §5.2 for method and caveats | computed here from USGS field measurements |
| Crest-record drift, ≥30 ft crests | **−0.138 % yr⁻¹**; ≥28 ft crests −0.064 % yr⁻¹ | ln(Q_crest/Q_rating24) regressed on year, n = 29 / 63 | computed here from NWPS crests |
| Rating 24.0 validity | in force since **2021-05-07**; range 7.28–40.50 ft = 2,000–157,000 cfs; measurements used span 6,620–125,000 cfs | above ~125 kcfs the rating is **extrapolated** | USGS rating file, fetched |
| USGS rating remark | *"Older high QMs were not used for the rating based on presumed control changes since the older QMs were made."* | the agency itself asserts the control changed | USGS rating file, fetched |
| Bankfull at Mount Vernon | **~130,000 cfs** (the Dec 1975 calibration flood, "close to a bankfull flow condition") | Dec 2025 peaked at 133,000 cfs | Hydraulics Tech Doc |
| Right-bank spill threshold | **>146,000 cfs at Mount Vernon** → overflow through Burlington to the Samish River and Samish Bay | a documented conveyance-loss threshold | Hydraulics Tech Doc |
| Debris obstruction, RR bridge RM 17.56 | **20 ft high across 90 % of the channel width**, observed 29 Nov 1995 | a lower loading (5.5 ft, 30 %) shifts flooding from Burlington to Mount Vernon | Hydraulics Tech Doc |
| Manning n, main channel | 0.030–0.043 above RM 17.5; **0.033–0.035 below** | overbank 0.06–0.12 above, 0.036–0.040 below | Hydraulics Tech Doc, Table 6 |
| Distributary split | ~60 % North Fork / 40 % South Fork in the flood model; USGS finds ~2:1 NF at low flow and **near-equal at high flow** | the split is itself dynamic | Hydraulics Tech Doc; USGS SIR 2016-5106 |
| Tidal limit under a 10-yr flood | **~7 mi up the North Fork, ~5 mi up the South Fork** | the forks are 7.3 and 8.1 mi long; Mount Vernon is ~6 mi above the split | Skagit Hydrology Tech Doc 2013 |
| Tidal boundary in the USACE model | MHHW **4.62 ft NGVD29**, MHW 3.72 ft NGVD29; "only strongly influences the stages in the immediate vicinity of the boundary (lower couple miles)" | | Hydraulics Tech Doc |
| M2 tidal amplitude at USGS 12200500 | **0.009 ft** at low flow (stage 10.6 ft, Aug 2026); control gauge Snohomish nr Monroe 0.0003 ft; Nooksack at Ferndale 0.005 ft | ≈0.1 % of the Skagit Bay tidal range | computed here (harmonic fit) |
| Delta subsidence | **0–1 mm yr⁻¹** deep subsidence; "sea levels in Skagit Bay are not currently being measured" | search-summary from Skagit Climate Science Consortium; **not independently fetched** | SCSC |
| Reservoir leverage on stage, Nov 1995 | Ross + Upper Baker storage reduced flood levels by **~5 ft at Concrete and ~2 ft at Mount Vernon** | the stage effect itself attenuates downstream | Skagit Hydrology Tech Doc 2013 |
| Feb 1951 crest duration | peak held for **6 h** at Mount Vernon; duration "more significant than its magnitude" because it exhausted Nookachamps storage and dikes failed from prolonged high water | **corrected 2026-08-24 by adversarial review: this passage is §2.4.9.3 *February 1951*, not December 1975** (1951: 139,000 cfs Concrete → 144,000 Mount Vernon) | Skagit Hydrology Tech Doc 2013 §2.4.9.3 |
| Nov 1990 breach signature | Fir Island levee failed ~3 mi below Mount Vernon and "increased the river slope and velocity below Mount Vernon, **causing an artificially low crest stage at the Mount Vernon gage**". The document's "~12–14 h before the peak" and "caused the Skagit River to **fall abruptly**" describe the **first** November 1990 flood (Nov 9–11); the levee "failed again during the second flood" (Nov 24–25) with **no timing given** — and it is the second flood that produced the 37.37 ft / 152,000 cfs annual peak | *timing attribution corrected 2026-08-24 by adversarial review* | Skagit Hydrology Tech Doc 2013 §2.4.9.4 |
| Jones loop width, Dec 2025 at Mount Vernon | rising +1.7 % to +4.5 %, falling −1.1 % to −3.0 %, total loop **2.9–7.6 %** (c = 9 → 3.4 ft s⁻¹) | S0 = 0.00045, dh/dt from 15-min stage | computed here |
| Observed falling-limb deviation, Dec 2025 | measured 111,000 cfs at 35.93 ft vs rating 118,000 cfs → **−5.9 %**, 9 h after the crest | measurement rated *Fair* (8 % uncertainty) — inside uncertainty | computed here from USGS field measurements |
| MVEW1 official categories | action **23.5**, minor **28**, moderate **30**, major **32 ft**; flow thresholds **undefined (−9999)**; vertical datum NGVD29 | stage-only reach | NWPS API, fetched |
| Flood-wave superposition | across 37 confluences (Elbe/Rhine/Danube/Weser, 3,803–139,549 km²), the largest downstream floods generally do **not** come from perfect temporal matching; observed lags 2–5 d | a Danube simulation showed a 20-h shift could change the downstream peak by up to 2× | Guse et al., HESS 24, 1633 (2020), fetched; the Danube 20-h result is Skublics et al. 2014 *as cited in* that paper, not a result of it |
| Tributary synchrony, lower Skagit | the regression between Skagit peaks and coincident East Fork Nookachamps peaks is **"poor"**; same for the Samish (106 mi²) | local tributaries do not reliably synchronise | Skagit Hydrology Tech Doc 2013 |

---

## 4. What is settled, what is emerging, what is contested

**Settled (established).**
- The kinematic/diffusion/dynamic hierarchy and their applicability criteria; Kleitz–Seddon celerity;
  c = βV with β > 1; Muskingum–Cunge as the hydraulically-parameterised routing scheme.
- Rating loops under unsteady flow, with the rising limb carrying more discharge; the loop vanishes
  for a kinematic wave and widens as bed slope flattens.
- USGS shift practice, its causes (scour, fill, vegetation, debris) and its uncertainty bands.
- Levees raise stage for a given discharge; setbacks lower it; both change *stage* far more than
  *peak discharge*.
- Lane's balance: a supply-rich, low-gradient, sand-bedded, levee-confined reach aggrades.
- That the lower Skagit *has* aggraded: 20 of 25 surveyed cross-sections, 1975 → 1999, +1.5 ft average bed.

**Emerging.**
- Systematic detection of unsteady-flow hysteresis at network scale (a French national-network
  framework exists; the paper was paywalled and **not fetched**), and the associated push toward
  "dynamic rating" methods that compute stage and discharge jointly from time series (USGS SIR
  2024-5129 — **not fetched, 403**).
- Backwater-estuarine wave propagation as a distinct regime: Dykstra & Dzwonkowski (2020, WRR)
  report over 238 km in coastal Alabama that celerity increased with water-surface slope and
  decreased with cross-sectional area, that waves transitioned from in-phase diffusive to
  out-of-phase dynamic, and — directly relevant here — that **small events moved downstream faster
  than large ones** (search-summary; the AGU page returned 403 and was **not fetched**).
- Non-stationary rating drift as a first-class operational problem rather than a station-file
  annoyance.

**Contested.**
- **How much of an apparent stage–discharge drift is channel change versus rating construction.**
  This is genuinely unresolved at 12200500 and §5.2 shows why: the reported discharges *are* rating
  outputs, and USGS deliberately excluded pre-2008 high measurements from the current rating. The
  agency's own remark asserts control change; the magnitude remains arguable.
- **Whether flood-wave superposition explains extreme floods.** Guse et al. (2020) find it is
  site-specific and that the largest observed floods usually are *not* perfectly synchronised, which
  cuts against the intuitive "everything peaked at once" narrative.
- **Whether crest-to-crest lag is a usable travel time.** The Skagit data (§5.1) show it behaves
  opposite to kinematic theory, so it is measuring storage and inflow timing, not celerity. Which of
  the two an operational platform *wants* is a design question, not a physics one.

---

## 5. Western Washington specificity — and the verification of the Mount Vernon drift

### 5.1 Routing on the Skagit, measured

Computed here from USGS instantaneous values for twelve events, 2003–2025, at
**12194000 Skagit R nr Concrete** (RM 54.1, DA 2,737 mi²) and **12200500 Skagit R nr Mount Vernon**
(DA 3,093 mi²; 48.4448 N, −122.3354; gauge altitude 3.8 ft NAVD88):

```
event        Q_Concrete  Q_MtVernon   lag_h    Δpeak     Q_Sauk   Sauk→Concrete
2003-10-21      166000      135000    17.75   -18.7%    106000        5.25 h
2006-11-07      145000      138000    23.75    -4.8%     86400        0.50 h
2007-12-04       77900       81000    17.75    +4.0%     45700        5.25 h
2009-01-08       62500       79900     9.50   +27.8%     38000        1.75 h
2011-01-17       74900       90600    13.25   +21.0%     30000        4.00 h
2014-11-29       91700       90700    16.50    -1.1%          -           -
2015-11-18       95800       78800    14.50   -17.7%     52800        4.00 h
2017-11-24      106000       94300    17.00   -11.0%     61900        4.00 h
2020-02-02       78900       73400    11.67    -7.0%     50000        4.08 h
2021-11-16      134000      127000    16.97    -5.2%     57700        9.50 h
2023-12-06       97400       73200    18.58   -24.8%     60900        5.42 h
2025-12-12      151000      133000    16.75   -11.9%     84800        2.75 h
```

Three findings, all FACT (computed from fetched primary data):

1. **The lag is a distribution, not a constant**: median 16.9 h, sd 3.5 h, range 9.5–23.8 h.
   `HYDROLOGY.md` §2's "crests roughly a day after the upper-basin peaks" is ~30 % long.
2. **The lag lengthens with magnitude** (r = +0.65; 17.0 h for ≥100 kcfs vs 14.5 h for <100 kcfs).
   Kinematic theory predicts the opposite, because c = βV rises with discharge. The observed sign is
   the signature of *storage engagement*: at high stage the Nookachamps cell and the overbank take
   volume out of the wave and delay the crest. It also matches the backwater-estuarine result that
   small events propagate faster than large ones (Dykstra & Dzwonkowski 2020, not fetched).

   **Caveat, added 2026-08-24 by adversarial review** (this is the caveat the §3 anchor table forward-
   references; it was missing). Two things weaken this finding and neither is resolved:
   (a) **USACE states the opposite trend.** §2.4.6.4 of the 2013 document says hydraulic travel time
   through this reach *decreases* "from 15-20 hours at low flow to between 10-15 hours at higher
   discharges." That is a *hydraulic* travel time, not a crest-to-crest lag, so the two are not
   strictly the same quantity — but the signs disagree and the platform must not present the
   crest-lag trend as though the reach's primary authority agreed with it.
   (b) **argmax on a broad crest is not a robust timestamp.** In the 2006 event — the single largest
   lag (23.75 h) and the most influential point in the correlation — the Concrete hydrograph sits
   between 139,000 and 145,000 cfs for more than ten hours and touches its 145,000 cfs maximum at
   five separate 15-minute steps spanning 20:00 on 11-06 to 01:30 on 11-07. Taking the last tie
   rather than the first changes that event's lag from 23.75 h to 18.25 h. Crest breadth grows with
   flood size, so this tie-breaking noise is itself magnitude-dependent and could manufacture part of
   the trend. r = +0.65 is robust to dropping any single event (0.56–0.72) and t = 2.7 on n = 12
   (p ≈ 0.02), but a crest-*centroid* timing method has not been tried and should be before this is
   seeded as doctrine. Treat the *lengthening* as **INFERENCE/emerging**, not established.
3. **Routing is not monotonically attenuating.** Median −6.1 %, but the 2009 and 2011 events
   *amplified* by +28 % and +21 %. The 2013 USACE hydrology document names the mechanism for the
   November 1990 case: "flood peaks between Concrete and Mount Vernon are normally reduced by
   attenuation and limited local inflow. This relation was reversed … due to significant local
   inflow, saturated soil conditions, and remaining pondage from the first flood" (FACT).

   **Correction to the magnitude dependence, 2026-08-24 (adversarial review).** An earlier draft read
   "attenuation is a big-flood phenomenon (r = −0.57)". The correlation is real and is not a
   normalisation artefact (r = −0.71 on the *absolute* cfs change, so it is not just a fixed local
   inflow divided by a growing denominator), but the claim was stated more strongly than the record
   supports, on two counts:
   (a) **USACE asserts the opposite generalisation** in the same document: "Skagit River flood peaks
   usually attenuate between Concrete and Mount Vernon. However, floods with high peaks and large
   volumes will generally fill the channel storage, and combined with runoff from the 356 square mile
   local area between Concrete and Mount Vernon, will cause the peak discharge to **increase** as it
   moves downstream" (FACT, fetched).
   (b) **The 2003–2025 window is unrepresentative.** Adding the eight historical events in Table 9 of
   the 2013 document (1949, 1951, 1955, 1975, 1980, both November 1990 floods, 1995) keeps the sign
   (r = −0.52, n = 20) but roughly halves the effect: the ≥100 kcfs median peak change becomes
   **−5.2 %**, not −11.0 %, and several of the largest floods on record *amplified* — Feb 1951
   139→144 kcfs (+3.6 %), Dec 1975 122→130 kcfs (+6.6 %), Nov 1990 second flood 146→152 kcfs (+4.1 %).
   The defensible statement is: **routing on this reach is bimodal, attenuation is more common and on
   average larger at high flow, and amplification at high flow is documented and not rare.**

The implied crest celerity, 38.4 river miles / 16.9 h = **3.4 ft s⁻¹**, is *below* the reported
in-channel velocity range for this reach, 5–10 ft s⁻¹ (§2.4.6.4 of the 2013 document; the
often-quoted 3–9 ft s⁻¹ is §2.4.6.5's figure for the reach *below* Mount Vernon), and therefore
2.2–5× below the kinematic celerity βV.
Crest-to-crest lag on this reach is a storage-and-inflow statistic, not a wave speed (INFERENCE).

### 5.2 The Mount Vernon stage–discharge drift: verified, and cut to about a third

**The repository's current claim** (`docs/research/flood-genesis-mechanisms-2026-08-24.md` §0 item 6
and §6.1): 1906 required 180,000 cfs to reach 37.00 ft; 2021 reached 36.99 ft on 127,000 cfs —
"~29 % less water for the same stage"; December 2025 set a record stage on ~12 % less flow than 1990.

**Step 1 — the peak-file arithmetic is correct but not evidence.** Both numbers are rating outputs.
Applying the *current* rating (ID 24.0, in force 2021-05-07, fetched) to every annual peak stage
gives Q_reported / Q_rating24 = 1.421 (1906), 1.148 (1951), 1.172 (1990), 1.089 (1995), 1.124
(2003), 1.352 (2006), 1.003 (2021), 1.000 (2025). Modern peaks sit on the modern rating by
construction. The comparison therefore measures *how the ratings changed*, which is not the same
claim as *how the channel changed*.

**Step 2 — the agency asserts the control changed.** Rating 24.0's own remark (FACT, fetched):
*"Rating based off QMs 559-610 (2015 to present) and all QMs>50kcfs since 2008 … Older high QMs were
not used for the rating based on presumed control changes since the older QMs were made."* USGS
excluded the older high-flow measurements *because it believes the control changed.* That is
independent corroboration of the direction, from the agency that owns the record.

**Step 3 — direct measured pairs, which are rating-independent.** From the USGS OGC
`field-measurements` collection (430 paired mean-gage-height/discharge measurements, 1959–2026,
fetched), all measurements above 90,000 cfs:

```
date          GH(ft)   Q_meas    quality   control          Q normalised to 33.00 ft
1989-12-05    32.28   103000     Good      —                     108,800
1990-11-25    36.91   141000     Good      debris light          107,300   ← Fir Island levee failed
1995-11-30    37.12   137000     Good      debris moderate       102,900
1995-12-01    32.54    98000     Good      debris light          101,500   ← added 2026-08-24 (was missing)
2003-10-22    33.92   113000     Fair      debris light          105,600
2006-11-07    32.68   125000     Poor      debris moderate       128,000   ← Poor; excluded
2017-11-24    32.99    95600     Good      clear                  95,700
2021-11-16    36.72   125000     Fair      clear                  96,300
2025-12-12    35.93   111000     Fair      clear                  90,200   ← falling limb
```

Normalisation uses the rating-24.0 curve *shape* to move each measurement to a common stage.
(**Corrected 2026-08-24 by adversarial review**: an earlier draft offered "the result is identical at a
33 ft and a 37 ft reference" as a robustness check. It is not one — normalisation multiplies every
measurement by the same factor R(ref), which cancels exactly in the ratio of the two group means, so
the answer is algebraically identical at *any* reference stage. The real sensitivity is to the
*curve shape* borrowed from the modern rating, which is not tested here.)

Excluding the *Poor* 2006 measurement and the breach-affected 1990 measurement:

- mean 1989–2003, **excluding** the 1995-12-01 measurement → **105,759 cfs at 33 ft**; mean 2017–2025
  → **94,062 cfs**; change **−11.1 %**; excluding the falling-limb 2025 measurement, modern mean
  96,011 cfs → **−9.2 %**;
- **including** the 1995-12-01 measurement (n = 4 pre / 3 modern) the pre-2010 mean is 104,686 cfs and
  the change is **−10.2 %**, or **−8.3 %** excluding the 2025 falling-limb point.

So the band is **−8 % to −11 %**, and it is sensitive to which of four pre-2010 measurements are kept.
The within-group scatter is 3.1 % (pre) and 3.6 % (modern), so with three or four points a side the
two-standard-error interval on the difference is roughly ±5 %. An independent check — regressing
ln(Q_measured / Q_rating24) on year over *all* non-*Poor* measurements above a discharge threshold —
gives −3.8 % over 35 years at a 40 kcfs threshold, −5.4 % at 60 kcfs, −10.4 % at 80 kcfs and −13.4 %
at 90 kcfs: the drift is threshold-dependent and concentrated at flood stage, which is consistent with
a control change at high flow but means the single number "9–11 %" is a flood-stage figure only.

**Step 4 — an independent trend on the full crest record.** Regressing ln(Q_crest / Q_rating24) on
year over the 63 NWPS historic crests at or above 28 ft gives **−0.064 % yr⁻¹**; restricted to the
29 crests at or above 30 ft, **−0.138 % yr⁻¹**. Over 1950–2025 that is −4.7 % to −10 %.

**Step 5 — the physical corroboration.**
- 25 surveyed cross-sections between RM 10.1 and RM 22.4, of which the 20 the table does not flag
  as "questionable" aggraded on average **+2.2 ft in thalweg and +1.5 ft in average bed elevation
  between 1975 and 1999** (FACT — WEST Consultants Table 1, fetched; over all 25 listed sections the
  averages are +1.6 ft thalweg / +1.2 ft bed). The Mount Vernon gauge sits inside that reach. The
  four nearest sections give +0.1 (RM 15.0), +2.3 (15.1), +2.6 (15.9) and +0.2 ft (16.2) of average
  bed — mean +1.3 ft, but with section-to-section scatter as large as the signal.
- The suspended-sediment rating slope at this exact gauge **increased 66 %** between 1974–76 and
  2006–09, which USGS reads as evidence of changed "sediment supply, channel hydraulics, and (or)
  basin hydrology" (FACT — SIR 2016-5106, fetched).
- The reach is levee-confined on both banks below Mount Vernon with a predominantly **sand** bed and
  a ~2 ft mi⁻¹ gradient (FACT — Skagit Hydrology Tech Doc 2013, fetched) — precisely Lane's
  aggrading configuration.

**Step 6 — two of the repository's data points are contaminated.**
- **1906** is a historic indirect estimate (peak codes 7, Bd — historic peak, day uncertain) and
  cannot carry a 29 % conclusion.
- **1990-11-25** is *breach-affected*: "A major levee failure at Fir Island during the November 1990
  flood increased the river slope and velocity below Mount Vernon, causing an **artificially low
  crest stage** at the Mount Vernon gage" (FACT — Skagit Hydrology Tech Doc 2013, fetched). The
  Fir Island levee failed in the first November 1990 flood and **failed again during the second**,
  which is the flood that produced the annual peak. Comparing 2025's levee-intact 37.73 ft to 1990's
  breach-depressed 37.37 ft *exaggerates* the drift.

**Verdict.** The drift is **real and independently corroborated**, but its magnitude is
**about 9–11 % at flood stage over roughly the last three decades (≈0.1–0.3 % yr⁻¹)**, not 29 %. Its
cause is **bed aggradation in a levee-confined sand-bed reach**, plus episodic debris and vegetation
effects — **not** the tide (§5.5). The direction of travel is one-way enough to matter: a stage
threshold on this reach silently becomes a *lower* discharge threshold every decade.

Caveats stated plainly: n = 2 modern high-flow measurements; the normalisation borrows the modern
rating's curve shape; measurement quality is *Fair* for both modern points (8 % ADAPS uncertainty),
which is the same size as the effect. The finding is **INFERENCE with strong physical corroboration**,
not FACT.

### 5.3 Hysteresis at Mount Vernon, quantified

The December 2025 crest was 37.73 ft at 2025-12-12 00:15 PST (133,000 cfs). USGS made a discharge
measurement at **09:08 PST the same day, 9 h into the recession**, at gage height 35.93 ft: measured
**111,000 cfs** against a rating value of **118,000 cfs** — the measurement is **5.9 % below** the
published rating, in the direction unsteady-flow theory requires for a falling limb (FACT, computed
from fetched data).

Applying the Jones formula with S0 = 0.00045 and celerity 3.4–9.0 ft s⁻¹ over the same event
(15-minute stage, 3-hour centred dh/dt) gives:

- maximum rising-limb enhancement **+1.7 % to +4.5 %** (at 12-11 13:00 PST, dh/dt = +0.51 ft h⁻¹);
- maximum falling-limb reduction **−1.1 % to −3.0 %** (at 12-12 11:30 PST, dh/dt = −0.33 ft h⁻¹);
- total loop width **2.9 % to 7.6 %** of discharge;
- at the measurement instant, theory predicts −1.1 % to −2.9 % against an observed −5.9 %.

**Honest reading.** Sign agrees, order of magnitude agrees, but the observed deviation exceeds the
theoretical one and the measurement is rated *Fair* (8 % uncertainty). This is **suggestive of a
loop, not a demonstration of one** (INFERENCE).

**Internal inconsistency, flagged 2026-08-24 (adversarial review).** The 2.9–7.6 % loop width uses
c = 3.4 ft s⁻¹ as its lower celerity bound — but §5.1 argues at length that 3.4 ft s⁻¹ is *not* a
celerity, it is a crest-to-crest storage statistic. The Jones formula needs the kinematic celerity.
Using the physically consistent value for this reach, βV with V = 5–10 ft s⁻¹ (§2.4.6.4) and
β = 1.5–5/3, i.e. **c = 7.5–16.7 ft s⁻¹**, the same 15-minute stage record gives rising +0.9 % to
+2.1 %, falling −0.6 % to −1.4 %, and a **total loop width of 1.6–3.4 %**, not 2.9–7.6 %. The observed
−5.9 % is then 2–4× the theoretical maximum rather than merely larger than it, which strengthens the
reading that the December 2025 deficit is measurement error or a rating shift rather than a loop.
**The uncertainty floor asserted in §6.1 item 5 should therefore be ±2–4 %, not ±3–8 %**, and it
should be labelled INFERENCE.

Note the asymmetry that matters operationally: a record **stage** at comparatively low **discharge**
is *not* explained by rising-limb hysteresis (which would push discharge up, not down). Hysteresis
and drift are separable, and the drift survives the separation.

### 5.4 Conveyance failure and storage engagement on this reach

- **Documented spill threshold**: above **146,000 cfs at Mount Vernon**, flow escapes the right bank
  through Burlington to the Samish River and Samish Bay (FACT — Hydraulics Tech Doc, fetched).
  December 2025 peaked at 133,000 cfs, below it. Bankfull is ~130,000 cfs.
- **Storage cell**: the Nookachamps Creek basin on the left overbank between Mount Vernon and
  Sedro-Woolley. Nookachamps enters at RM 18.8, DA 71.6 mi² (FACT).
- **Duration beats magnitude**: in **February 1951** (§2.4.9.3 — *corrected 2026-08-24 by adversarial
  review; an earlier draft attributed this passage to December 1975*) "the flood remained near its peak for 6 hours at
  Mount Vernon. The duration of this peak was more significant than its magnitude because it
  minimized the effectiveness of natural storage in the Nookachamps Creek area, and dikes failed
  because they lacked sufficient cross-sectional dimensions to withstand a long period of high
  water" (FACT). A storage cell only attenuates until it is full.
- **Breach signature**: November 1990, the Fir Island failure ~3 miles below the gauge "caused the
  Skagit River to fall abruptly" and produced an artificially low crest stage at the gauge (FACT).
  *Corrected 2026-08-24 by adversarial review*: the "~12–14 hours before the peak at Mount Vernon"
  and "fall abruptly" wording is §2.4.9.4's account of the **first** November 1990 flood (Nov 9–11).
  The levee "failed again during the second flood" (Nov 24–25) — the one that produced the annual
  peak — and the document gives **no timing** for that second failure. The stage-depression argument
  in §5.2 step 6 survives (USACE applies "artificially low crest stage" to the November 1990 flood
  generally) but the 12–14 h number must not be attached to the annual peak.
  This is the canonical anomaly the platform must be able to recognise:
  **falling stage during a rising upstream hydrograph.**
- **Debris as a time-varying control**: 20 ft of debris across 90 % of the channel at the railroad
  bridge at RM 17.56 was observed in November 1995, and the modelled *lower* debris case "mainly
  results in more flooding occurring in Mount Vernon versus Burlington" (FACT). A conveyance
  obstruction ~2 river miles above the gauge that changes between floods.
- **Regulation leverage on stage**: Ross + Upper Baker storage in November 1995 is estimated to have
  reduced flood levels by **~5 ft at Concrete and ~2 ft at Mount Vernon** (FACT). The stage benefit
  itself attenuates downstream by ~60 % over 38 miles.

### 5.5 The tide does not reach the Mount Vernon gauge — a refutation

The prior research pass listed "backwater and tide" as a candidate mechanism for the drift, noting
that "the tidally-affected reach extends up toward the gauge." Two independent lines refute it *at
the gauge*:

1. **Harmonic analysis of the gauge record** (computed here). Fitting a quadratic trend plus M2
   (12.42 h), S2, K1 and S1 constituents to 15-minute stage over 2026-08-10 → 2026-08-20 (low flow,
   stage ~10.6 ft, when tidal propagation upstream is at its *maximum*) gives an **M2 amplitude of
   0.009 ft** at 12200500. The same fit gives **0.0003 ft** at Snohomish River near Monroe (a
   demonstrably non-tidal control) and **0.005 ft** at Nooksack River at Ferndale. So a signal is
   detectable — ~30× the null-site value — but it is **0.009 ft against a Skagit Bay tidal range of
   order 8–11 ft**, i.e. ~0.1 %. Hydraulically negligible.

   **Reproduction note, 2026-08-24 (adversarial review).** An independent re-fit of the same three
   records over the same window, adding O1 and N2 to the constituent set, returns **M2 = 0.0042 ft**
   at Mount Vernon, 0.0045 ft at Ferndale and 0.0007 ft at Monroe (residual sd 0.0229 ft, matching).
   The M2 amplitude is therefore **not stable to the choice of constituents** — it moves by a factor
   of two — and in every variant it is an order of magnitude *below* the residual scatter of the fit,
   whose residuals are strongly autocorrelated. The **conclusion** (M2 of order 0.004–0.009 ft, ~0.1 %
   of the bay range, hydraulically negligible) is robust; the **specific value 0.0093 ft is not**, and
   the assertion that a signal is "detectable — ~30× the null-site value" is not supported and should
   be dropped. Note also that K1 and S1 are near-degenerate over a 10-day window and both come back
   large at all three sites (0.04 ft even at the non-tidal control) — they are fitting the diel
   evapotranspiration cycle, not a tide. Line 2 below, which is independent of this fit, carries the
   argument on its own.
2. **The USACE hydraulic model agrees.** Its downstream boundary is a tidal hydrograph (MHHW 4.62 ft
   NGVD29) and the report states it "only strongly influences the stages in the immediate vicinity
   of the boundary (lower couple miles)"; the 2013 hydrology document puts the tidal limit under a
   10-year flood at ~7 miles up the North Fork and ~5 up the South Fork — the forks are 7.3 and 8.1
   miles long and Mount Vernon is ~6 miles above the split, so the tidal limit falls roughly
   **7 river miles below the gauge** (FACT, both fetched).

**Consequence.** Delta subsidence (0–1 mm yr⁻¹) and sea-level rise are real for the *delta* and for
the distributary reaches, and they matter for compound coastal flooding there. They are **not** a
credible explanation for an ~11 % conveyance change at RM ~16, and a river-plus-tide joint model at
Mount Vernon would be solving the wrong problem. This qualifies the prior corpus entry's §6.2.

### 5.6 What transfers from elsewhere, and what does not

- **Transfers well.** Wave-hierarchy theory, Kleitz–Seddon, Jones, Muskingum–Cunge, USGS shift
  practice, Lane's balance. These are physics and agency practice, not regional empirics.
- **Transfers with care.** Levee-setback stage reductions from the Middle Mississippi and Lower
  Missouri (0.12–1.61 m for the 1 % flood) are from far larger, far lower-gradient systems with
  wide reconnectable floodplains; the Skagit's setback opportunities are smaller and its gradient is
  flatter still, which by Lammers et al. means *lower* per-area stage benefit. The direction
  transfers; the magnitude does not.
- **Transfers with strong care.** Backwater-estuarine celerity results from coastal Alabama
  (238 km, salinity-influenced, cypress-to-marsh friction transition) match the Skagit's
  "big floods travel slower" signature but the delta morphology is entirely different.
- **Does not transfer.** European confluence-superposition statistics (2–5 day lags, 3,803–139,549
  km² catchments) are an order of magnitude larger and slower than western Washington basins, where
  the whole Skagit responds in under a day and the Snoqualmie/Stillaguamish in hours. The
  *qualitative* conclusion — that perfect synchrony is not what makes the largest floods — is worth
  carrying; the numbers are not.
- **Region-specific and important.** Glacially-fed, volcano-sourced sediment supply (Glacier Peak
  via the Sauk, Mount Baker via the Baker and the Nooksack) is what keeps the lower Skagit
  aggrading at ~0.75 in yr⁻¹ average bed elevation. Rivers without a volcanic/glacial sediment
  source do not drift this way.

---

## 6. What this means for Cascadia Papsukkal

### 6.1 Doctrine additions

1. **A stage threshold has a discharge vintage.** On an aggrading, levee-confined, sand-bed reach,
   the discharge that produces the official stage category falls over time. `HYDROLOGY.md` §5 should
   say so, and the UI should never let a reader infer a fixed flow equivalent.
2. **Routing is a distribution with two signs.** "Delayed and attenuated" (`HYDROLOGY.md` §1) is
   incomplete: the Concrete → Mount Vernon peak change is measured between −25 % and +28 %.
3. **A falling stage during a rising upstream hydrograph is an anomaly, not an improvement.** It is
   the documented signature of a downstream breach or spill on this exact reach.
4. **Rating provenance is provenance.** A stage or discharge value from a rated site carries a
   rating id, a shift, and a rating validity date, exactly as it carries a source and a time.
5. **Unsteady flow puts a floor under discharge uncertainty.** On the lower Skagit, ±3–8 % during
   fast rises and recessions, before any rating error.

### 6.2 Method and contract changes

| Change | Where | Why |
|---|---|---|
| Add `rating_id`, `rating_shift`, `rating_valid_from` to rated observations | `packages/contracts` value model; `packages/core/models.py`; migration | the drift is invisible without it; USGS publishes it |
| Add `measurement_quality` and `control_condition` to any ingested field measurement | contracts + a new provider adapter | Good/Fair/Poor maps to 5 %/8 %/>8 % uncertainty; "debris moderate" is a conveyance state |
| Travel time as a stored empirical distribution per gauge pair, not a constant | `packages/hydrology` (new `routing.py`), seeded from history | median 16.9 h, sd 3.5 h, magnitude-dependent |
| Peak-change (attenuation/amplification) as a DERIVED feature per gauge pair | `packages/hydrology` | first-class routing signal; sign carries information |
| `conveyance_anomaly` detector: stage falling while upstream stage/flow rising | `cascade_hydrology.trend` / `assemble` | breach and spill signature; currently would read as "falling → good" |
| Reach conveyance thresholds as CONFIGURED domain attributes (bankfull 130 kcfs, right-bank spill 146 kcfs at Mount Vernon) | seed + `DOMAIN_MODEL.md` | display and explanation only; excluded from hazard computation by type |
| Cross-source crest reconciliation as an `Assessment` of kind `crest_disagreement` | `cascade_hydrology.agreement` | NWPS lists the 2021-11-16 Mount Vernon crest as 37.32 ft / 122,596 cfs; USGS lists 36.99 ft / 127,000 cfs for the same event |
| Do **not** add tide/surge to the Mount Vernon forecast point | qualifies prior corpus §6.2 | M2 = 0.009 ft at the gauge; tidal limit ~7 mi downstream |

### 6.3 New data sources to add to `DATA_SOURCES.md`

| Source | Endpoint | What it gives |
|---|---|---|
| USGS expanded rating tables | `https://nwis.waterdata.usgs.gov/nwisweb/get_ratings?site_no={site}&file_type=exsa` | rating ID, type, expansion, breakpoints, offsets, current and previous shift with begin/end times, **the analyst's remark**, and the full stage→discharge table. RDB. Verified working 2026-08-24. |
| USGS OGC `field-measurements` | `https://api.waterdata.usgs.gov/ogcapi/v0/collections/field-measurements/items?monitoring_location_id=USGS-{site}` | measured discharge, mean gage height, measurement rating (Good/Fair/Poor), control condition, per field visit; 430 paired measurements 1959–2026 at 12200500. Pair `Discharge` and `MeanGageHeight` on `field_visit_id`. |
| USGS OGC `peaks` | same collection family | annual peaks with qualification codes, replacing the legacy `nwis/peak` RDB |
| NWPS gauge crests | `https://api.water.noaa.gov/nwps/v1/gauges/{lid}` → `flood.crests.historic` | historic crest stage **and** flow with a preliminary/observed/revised flag — the record needed for §5.2 step 4 |

Legacy note for `docs/research/README.md`: `waterservices.usgs.gov/nwis/iv` now 301-redirects to
`nwis.waterservices.usgs.gov`, and `waterdata.usgs.gov/nwis/measurements` 301-redirects to the
monitoring-location HTML page — the RDB measurement export is gone; use the OGC collection.

---

## 7. What this contradicts or qualifies in current repo doctrine

1. **`docs/research/flood-genesis-mechanisms-2026-08-24.md` §0 item 6 and §6.1 — the 29 % drift.**
   Overstated. Independently measured pairs support **9–11 % since the late 1980s–2000s**. The 1906
   datum is a historic indirect estimate and the 1990 datum is depressed by the Fir Island levee
   failure. The *existence* of the drift is confirmed and strengthened (USGS's own rating remark,
   the 1975→1999 cross-section survey, the 66 % SSC-rating slope change).
2. **Same file §6.1 — "backwater and tide … strong leverage on stage at the gauge."** Refuted at the
   gauge: M2 amplitude 0.009 ft, and the USACE model and the 2013 hydrology document both put the
   tidal limit ~7 river miles downstream. Retain backwater as a *non-oscillatory* mechanism
   (downstream channel change) and move the tidal argument to the distributary reaches.
3. **Same file §6.2 — compound coastal flooding "for any forecast point in a tidally-influenced
   reach — Mount Vernon, Ferndale…".** Mount Vernon does not qualify on the evidence here; Ferndale
   showed an M2 amplitude of only 0.005 ft in the same test and should be re-checked before tide is
   wired to it.
4. **`docs/HYDROLOGY.md` §1 — "routes it downstream, delayed and attenuated."** Incomplete:
   amplification between Concrete and Mount Vernon was measured at +28 % (2009) and +21 % (2011),
   and is documented by USACE for November 1990.
5. **`docs/HYDROLOGY.md` §2 — the lower Skagit "crests roughly a day after the upper-basin peaks
   (INFERENCE)".** Measured median is **16.9 h** from Concrete, sd 3.5 h. The claim can be upgraded
   from INFERENCE to a measured distribution, and should be, because the spread is operationally
   larger than the bias.
6. **`docs/HYDROLOGY.md` §9 — "travel time is estimated from history … and carried as a
   distribution."** Correct in intent; the distribution now exists and should be seeded. But the
   doctrine should also record that crest-to-crest lag is *not* wave celerity on this reach (it is
   1.3–4× slower than βV) and that it **lengthens** with flood magnitude, which is the opposite of
   the naive expectation.
7. **`docs/HYDROLOGY.md` §9 — "time-to-threshold: headroom ÷ current rate of rise."** On this reach
   the rate of rise is also the variable that widens the rating loop; during the fastest observed
   rise (0.51 ft h⁻¹) the unsteady-flow discharge enhancement is +1.7 % to +4.5 %. Stage-basis
   headroom is the more robust of the two during fast rises; flow-basis headroom inherits the loop.
8. **`docs/HYDROLOGY.md` §9 — "Stage and discharge … never derive one from the other."** Strongly
   vindicated; this entry supplies the numeric justification (rating 24.0 is extrapolated above
   125,000 cfs; conveyance changed ~11 % in three decades).
9. **`docs/HYDROLOGY.md` §10 — levees "never as guarantees … a design height is a design height."**
   Correct but incomplete: a levee failure changes *the gauge reading itself*. The doctrine needs the
   observability clause, not just the disclaimer.
10. **`docs/DATA_DOCTRINE.md` §8 — revisions.** Framed around USGS provisional→approved discharge.
    Extend it: **stage is revised too** (NWPS 37.32 ft vs USGS 36.99 ft for 2021-11-16 at Mount
    Vernon), and rating revisions retroactively change what a historical stage *means* without
    changing any stored number.
11. **`docs/EVENT_ZERO.md` and `HYDROLOGY.md` §12 — "37.73 ft … above the 1990 record of 37.37 ft
    despite a lower flow (~152,000 cfs in 1990)".** True as recorded, but the 1990 stage is
    breach-depressed. The comparison must carry that qualification or it teaches the reader a
    stronger drift than the evidence supports.

---

## 8. Open questions

1. **The exact river mile of USGS 12200500.** All celerity numbers here use ~38 river miles from
   Concrete (RM 54.1, documented) to a Mount Vernon gauge assumed near RM 15.7–16.2. NHDPlus HR /
   3DHP flowline measure would settle it and would change the celerity by up to ±10 %.
2. **Is the 2021 NWPS/USGS crest discrepancy a stage revision or a different physical gauge?**
   0.33 ft and 3.5 % of flow, for the same event, from two authoritative sources.
3. **What happened at the 2006-11-07 peak?** 138,000 cfs at only 33.85 ft — 35 % more discharge per
   foot of stage than the modern rating. The one measurement is rated *Poor* with moderate debris,
   and county records show no breach. Rating epoch, debris at RM 17.56, or a real conveyance state?
   The USGS station analysis file would settle it and is not public.
4. **Has aggradation continued past 1999?** The only cross-section comparison found is 1975→1999.
   Post-1999 bathymetry (Skagit County, USACE, or lidar-derived bare-earth plus soundings) would
   convert §5.2's inference into a measurement.
5. **Where is the full shift history?** The `exsa` file gives only the current and previous shift.
   A shift time series would let the platform reconstruct what a historical stage meant *at the time*
   — which is exactly the knowledge-time problem `DATA_DOCTRINE.md` §11 exists for.
6. **Do NWM RouteLink Muskingum–Cunge parameters reproduce the observed 16.9 h Concrete → Mount
   Vernon lag and the −6 % median peak change?** A cheap, decisive test of whether NWM routing is
   usable on this reach.
7. **Datum reconciliation at Mount Vernon.** USGS site metadata gives altitude 3.8 ft NAVD88; NWPS
   reports the vertical datum as NGVD29; the 2003 USACE report says "the Mount Vernon gage datum is
   sea level … Sea level is 5.38 feet NGVD 29." Three statements, no single reconciled offset.
8. **What drives the +21 %/+28 % amplification events?** Nookachamps and Samish gauges (WSDOE
   03G100, USGS 12201500) exist; a coincident-flow analysis would confirm or refute the local-inflow
   explanation.
9. **Is the December 2025 falling-limb deficit (−5.9 %) a loop or measurement error?** One *Fair*
   measurement. A deliberate rising-and-falling measurement pair in a future event would settle it.
10. **Does vegetation contribute measurably to the drift?** USGS names vegetation growth as a shift
    cause; nothing found quantifies riparian encroachment in the leveed lower Skagit.

---

## 9. Sources

### 9.1 Fetched and read
- USGS annual peak-flow file, 12200500 — `https://nwis.waterdata.usgs.gov/nwis/peak?site_no=12200500&agency_cd=USGS&format=rdb` (retrieved 2026-08-24)
- USGS expanded rating table, 12200500, rating ID 24.0 — `https://nwis.waterdata.usgs.gov/nwisweb/get_ratings?site_no=12200500&file_type=exsa` (file retrieved date 2025-11-15; fetched 2026-08-24)
- USGS OGC API field measurements — `https://api.waterdata.usgs.gov/ogcapi/v0/collections/field-measurements/items?monitoring_location_id=USGS-12200500&limit=10000`
- USGS OGC API monitoring locations — `https://api.waterdata.usgs.gov/ogcapi/v0/collections/monitoring-locations/items?monitoring_location_number=12200500`
- USGS instantaneous values — `https://nwis.waterservices.usgs.gov/nwis/iv/` for 12200500, 12194000, 12189500, 12213100, 12150800 (event windows 2003–2026)
- NWPS gauge object MVEW1 — `https://api.water.noaa.gov/nwps/v1/gauges/MVEW1`
- USACE Seattle District / Skagit County, *Skagit River Flood Damage Reduction Feasibility Study — Hydraulics Technical Documentation*, October 2003 draft — [PDF](https://www.skagitcounty.net/PublicWorksSurfaceWaterManagement/Documents/HydraulicReport/03%20-%20Skagit%20Writeup1.pdf)
- WEST Consultants, *Table 1 — Skagit River Cross-Section Comparison (1975–1999)* — [PDF](https://www.skagitcounty.net/PublicWorksSurfaceWaterManagement/Documents/HydraulicReport/04%20-%20TABLE%201%20-Aggradation%20Analysis.pdf)
- USACE / Skagit County, *Skagit River Basin Flood Risk Management Study — Hydrology Technical Documentation*, August 2013 — [PDF](https://www.skagitcounty.net/PublicWorksSalmonRestoration/Documents/Skagit%20River%20Hydrology%20Technical%20Doc_Final_August2013.pdf)
- Curran, C.A., et al., *Sediment load and distribution in the lower Skagit River, Skagit County, Washington*, USGS SIR 2016-5106 — [PDF](https://pubs.usgs.gov/sir/2016/5106/sir20165106.pdf)
- USGS California Water Science Center, *Ratings are not static — you must learn how to apply "shifts" to them* (training deck citing Rantz WSP 2175 pp. 348–352 and Lane 1955) — [PDF](https://ca.water.usgs.gov/FERC/presentations/shifting-controls.pdf)
- Lammers, R.W., et al., *Modeling the effects of levee setbacks on flood hydraulics* (author preprint of the *J. Flood Risk Management* 2024 paper) — [PDF](https://iris.uga.edu/wp-content/uploads/2023/12/Scaling-Floodplain-Reconnection-Revised_clean89.pdf)
- Ponce, V.M., *Kinematic waves demystified* — [page](https://ponce.sdsu.edu/kinematic_waves_demystified.html)
- Ponce, V.M., *Kinematic and dynamic waves* — [page](https://ponce.sdsu.edu/kinematic_and_dynamic_waves.html)
- Ponce, V.M., *Rating curves revisited* — [page](https://ponce.sdsu.edu/rating_curves_revisited.html)
- Ponce, V.M., *Muskingum-Cunge method explained* — [page](https://ponce.sdsu.edu/muskingum_cunge_method_explained.html)
- Guse, B., Merz, B., Wietzke, L., Ullrich, S., Viglione, A. & Vorogushyn, S., *The role of flood wave superposition in the severity of large floods*, HESS 24, 1633–1648 (2020) — [article](https://hess.copernicus.org/articles/24/1633/2020/) (doi:10.5194/hess-24-1633-2020; **corrected 2026-08-24 — an earlier draft of this entry mis-cited the first author as “Thomas”**)

### 9.2 Cited but NOT independently fetched (paywall, 403, or search summary only)
- Dykstra, S.L. & Dzwonkowski, B., *The propagation of fluvial flood waves through a backwater-estuarine environment*, Water Resources Research 56(2), e2019WR025743 (2020) — AGU returned 403. A NOAA repository copy exists at `https://repository.library.noaa.gov/view/noaa/28544`. **Not fetched.**
- Mansanarez, V., et al. / Bonnifait et al., *A framework for detecting stage–discharge hysteresis due to flow unsteadiness: application to France's national hydrometry network*, J. Hydrology (2022) — Elsevier 403. **Not fetched.**
- USGS SIR 2024-5129, *Dynamic rating method for computing discharge and stage from time-series data* — pubs.usgs.gov 403. **Not fetched.**
- Rantz, S.E., et al., *Measurement and computation of streamflow*, USGS Water-Supply Paper 2175 (1982) — cited via the USGS training deck. **Not fetched directly.**
- Ponce, V.M. & Simons, D.B. (1977) and Ponce et al. (1978) — the τ* ≥ 171 and τ* ≥ 30 criteria come from search summaries of the author's own pages. The σ* > 0.17 / 30 % attenuation criterion **was** read on a fetched page.
- Jones, B.E. (1916), *A method of correcting river discharge for a changing stage* — standard reference for the loop formula. **Not fetched.**
- Hayami, S. (1951), diffusion-wave analogy and ν = Q/(2 S0 B). **Not fetched.**
- Skagit Climate Science Consortium, sea-level-rise and sediment pages (delta subsidence 0–1 mm yr⁻¹; "seawater backs up from the bay to about Mt. Vernon during high tides"; ~90 million m³ accumulated in Skagit Bay since the late 1880s) — search summaries only. **Not fetched.** Note the "backs up to about Mt. Vernon" statement is in tension with §5.5 and with the USACE model; treat it as a popular-summary statement until re-verified.
- Middle Mississippi (Remo et al.) and Lower Missouri (Jacobson et al.) levee-setback stage reductions — search summaries only. **Not fetched.**
- Lane, E.W. (1955), the qualitative sediment balance — cited via the USGS deck.

### 9.3 Reproduction

All computed numbers come from files retrieved into the session scratchpad on 2026-08-24. The
analysis steps were: (1) parse the `exsa` rating into a stage→discharge lookup; (2) evaluate every
annual peak stage and every NWPS historic crest stage against it; (3) pair `Discharge` with
`MeanGageHeight` on `field_visit_id` from the OGC field-measurements response and normalise measured
pairs to a common stage using the rating curve shape; (4) for each of twelve event windows, take the
instantaneous-discharge maximum at each site and difference times and magnitudes; (5) least-squares
fit of trend + M2/S2/K1/S1 harmonics to 15-minute stage for the tidal test. No proprietary data and
no manual adjustment were used.
