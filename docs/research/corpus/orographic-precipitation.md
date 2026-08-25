# Orographic precipitation physics and QPF over terrain

*Corpus entry, 2026-08-24. Part of the Cascadia Papsukkal flood-science corpus.*

*Labels follow `docs/DATA_SOURCES.md` conventions. **FACT** = read on a page or PDF this agent
fetched and extracted (URL given); **INFERENCE** = reasoned from cited facts; **ASSUMPTION** = a
working simplification; **OPEN QUESTION** = unresolved. Where a paper could only be reached
through a search-result summary and not fetched, the claim says "not independently fetched" and is
labelled INFERENCE. Nothing in the repository was modified except this file.*

---

## 1. Headline

**Orographic precipitation is a transfer function, not an amplifier.** The water that falls on a
western-Washington basin during a flood-producing storm is set by (a) the *cross-barrier component*
of the impinging moisture flux, (b) whether the low-level flow is dynamically able to ascend the
terrain, and (c) how long condensate takes to convert and fall while being advected downwind. When
the flow is unblocked, the relation between upslope integrated vapour transport and windward
rainfall rate over the Olympics is tight enough to be a design constraint — **r² = 0.85–0.87, slope
0.014 mm h⁻¹ per (kg m⁻¹ s⁻¹) of IVT⊥**, so +200 kg m⁻¹ s⁻¹ buys +2.8 mm h⁻¹ (FACT, Tierney &
Durran 2024). When it is blocked, or when the storm is warm-frontal rather than warm-sector, the
same IVT lands somewhere else. The operative scalar is therefore **IVT projected onto each basin's
own terrain gradient**, and the single most discriminating fact in the region is that *the four
western-Washington basins Neiman et al. (2011) studied flood on different low-level wind directions
— the Sauk on southwesterly, the Green only in a 245°–275° window — at >95 % statistical
significance* (FACT).

Two consequences bind the platform. First, **AR magnitude without basin-specific orientation is
close to uninformative** for deciding *which* basin floods. Second, **every product that could tell
us the basin QPF is wrong in a known direction**: convection-permitting models spill precipitation
across the crest (bias ratio rises windward→leeward), coarse models under-resolve the ~10 km
ridge-valley pattern that carries a persistent **50–300 %** signal, radar covers only **one-quarter
to one-third** of the coastal-western-US land surface well enough for QPE and reads **<50 %** of
gauge values where the rain is heaviest, and the gauges themselves undercatch **5–15 % in the
lowlands, 15–20 % in Cascade gaps, and 25–40 % above 1,500 m** in exactly this region. UNKNOWN and
a signed, regime-dependent error bar are the honest outputs; a bare basin-mean millimetre value is
not.

---

## 2. Mechanisms (the physics, stated properly)

### 2.1 The upslope model — the zeroth-order transfer function

For saturated flow that parallels the terrain at all heights, the vertically integrated
condensation rate is (FACT, Minder & Roe, *Encyclopedia of Snow, Ice and Glaciers*, Eq. 1):

```
S(x,y) = ρ q_v  U · ∇h(x,y)
```

— the product of the **moisture flux** (ρ q_v U, i.e. IVT) and the **terrain slope in the direction
of the airflow**. Under the further assumption that conversion and fallout are instantaneous, S is
also the surface precipitation rate. Two controlling parameters fall straight out: how much vapour
is arriving, and the *component of the wind along the elevation gradient*. Orientation is therefore
a first-order term of the governing equation, not a refinement of IVT magnitude.

The model's central caveat is stated by its own users: moist ascent over topography alone is
typically **insufficient** to generate precipitation — orographic effects mainly *modify*
precipitation during pre-existing storms (FACT, Minder & Roe; Browning et al. 1974; Smith 2006).
The quantitative version of this appears in §2.5.

### 2.2 IVT⊥ — the operational form of the same quantity

```
IVT⊥ = (1/g) ∫₀^{z_t} ρ q u⊥ dz            (Tierney & Durran 2024, Eq. 1)
```

where `u⊥` is the wind component perpendicular to the barrier. Empirically, over the Olympics
during OLYMPEX warm sectors (FACT, Tierney & Durran 2024, fetched):

- r² = **0.87** (Quillayute sounding), **0.82** (Taholah), **0.85** for the pooled best-fit line,
  against hourly rainfall averaged over seven Quinault-basin gauges spanning 188–1,484 m.
- Best-fit slope **0.014 mm h⁻¹ (kg m⁻¹ s⁻¹)⁻¹**.
- The optimal projection bearing had to be *fitted per sounding site*: **251°** at Taholah, **224°**
  at Quillayute. The authors attribute the Taholah value to terrain-induced deflection of flow that
  was more nearly southwesterly further upstream.
- The advective lag from coastal sounding to gauge network was **1–2 h** at ~15 m s⁻¹ low-level
  upslope wind.

Earlier work in California's coastal mountains gives the same physics with weaker numbers because
it uses a scalar upslope wind rather than a full IVT: Neiman et al. (2002) found maximum correlation
between hourly upslope flow near **1 km MSL** (i.e. just above mountaintop, at low-level-jet
altitude) and mountain rain rate, with **case-study r = 0.761–0.939 → 58–88 % of rain-rate variance
explained** (FACT, fetched). The number the repo's prior pass cites is this one — but the same paper
reports that over a *whole winter season* only **31 %, 48 % and 41 %** of rain-rate variance was
explained at the three couplets, rising to **56 %** when restricted to low-level-jet conditions
(FACT). Unblocked cases gave r = 0.874–0.939; blocked cases only r = 0.761–0.832 (FACT).

### 2.3 Smith & Barstad (2004) linear theory — where the timescales live

S&B04 extends the upslope model with linearised mountain-wave dynamics, a conversion timescale
τ_c, a fallout timescale τ_f, and lee-side evaporation. The whole model is one transfer function in
Fourier space (FACT, fetched, their Eq. 49):

```
P̂(k,l) =            C_w i σ ĥ(k,l)
            ────────────────────────────────────────
            (1 − i m H_w)(1 + i σ τ_c)(1 + i σ τ_f)
```

with σ = Uk + Vl the intrinsic frequency, H_w the moist-layer depth, C_w the thermodynamic uplift
sensitivity, and m(k,l) = [(N_m² − σ²)/σ²]^½ (k²+l²)^½ sgn(σ) the vertical wavenumber. Setting
m = τ_c = τ_f = 0 recovers the raw upslope model (FACT).

Structural facts that matter operationally (all FACT, S&B04 as fetched):

- The **dynamics factor has a negative sign** — it shifts precipitation *upwind*. The **cloud
  factors have positive signs** — they shift precipitation *downwind*. Real patterns are the
  residue of two opposing displacements.
- Precipitation from a point source is smeared downwind over a distance **Uτ**; for equal
  timescales the Green's function peaks exactly **Uτ downstream** of the source.
- Canonical parameter set S&B04 used for **the Olympic Range**: southwest wind at **U = 15 m s⁻¹**,
  moist stability **N_m = 0.005 s⁻¹**, surface **T₀ = 280 K**, **q = 6.2 g kg⁻¹**, moist-layer depth
  **H_w = 2.5 km**, **τ_c = τ_f = 1000 s**, 1 km grid with terrain smoothed to 800 m. Result:
  6-h accumulation with a maximum of about **26 mm just upwind of Mount Olympus (2,428 m)**, four
  precipitation tongues on the four southwest-directed ridges, light precipitation well upstream
  over the sea, some spillover, and *no precipitation collected on the high northeast peaks*.
- Precipitation efficiency is strongly τ-sensitive. For a Gaussian ridge (U = 15 m s⁻¹,
  N = 0.005 s⁻¹, a = 15 km, H_w = 3 km): PE_dyn is fixed at **82 %**, but PE_cloud falls
  **96 % → 84 % → 67 % → 47 %** as τ_c = τ_f goes 250 → 500 → 1000 → 2000 s, and total PE falls
  **79 % → 70 % → 55 % → 39 %** (FACT, their Table 5).
- **Spillover has a closed form.** For a triangular ridge of half-width d, precipitation reaches a
  lee cutoff at `x_c = Uτ ln(2 − e^{−d/Uτ}) < d` (FACT, their Eq. 46).
- **Drying ratio** DR = P/F, the fraction of the incoming vapour flux precipitated, with
  `DR = (Γ_m/g)(A/H_w) · PE` (their Eq. 52). S&B04 state the linearity assumption "may be useful"
  when **DR < ~0.3** and is "less appropriate" when **DR > 0.5** (FACT).

**The scale warning that should be printed on any DEM-based downscaling.** S&B04 state that the raw
upslope approach "can seriously overestimate the precipitation" over complex terrain because the
same water is lifted repeatedly, and that reasonable totals require **smoothing the terrain to
30 km or more**; for terrain rising and falling at **scales of 20 km or less the model can
overestimate total precipitation by a factor of 5 or greater**, and Smith et al. (2003) found in the
Italian Alps that upslope estimates *exceeded the incoming moisture flux* — an outright violation of
water conservation (FACT, fetched).

### 2.4 Froude number, non-dimensional mountain height, and blocking

Stability is measured by the Brunt–Väisälä frequency N² = (g/T)(Γ − γ). The blocking criterion is
the **non-dimensional mountain height** (FACT, Minder & Roe Eq. 3):

```
M = N h / U           (= 1/Fr).      Blocking is favoured when M > 1.
```

When M is small the flow rises over the barrier and the linear/upslope relation holds; when M is
large the low-level flow is blocked, deflected around the barrier, stagnant or reversed, and the
precipitation maximum shifts upstream while precipitation over the upper windward slope is reduced
(FACT, Minder & Roe; Houze 2012 as cited therein). Agreement between dynamical models and the
linear prediction is near-perfect at high Froude number and "degrades dramatically" as it falls
(FACT, as recorded in `docs/research/flood-genesis-mechanisms-2026-08-24.md` §2.3).

**Measured M for the Olympics, by frontal sector** — this is the quantitative bridge from a
textbook criterion to an operational flag (FACT, Purnell & Kirshbaum 2018, MWR 146, Table 4,
fetched):

| Sector | mean \|u_m\| (m s⁻¹) | mean IVT (kg m⁻¹ s⁻¹) | mean **M** | CAPE (J kg⁻¹) |
|---|---|---|---|---|
| Warm-frontal (6 events) | 22 | 525 | **1.1** | ~1 |
| Warm-sector (6 events) | 23 | 640 | **0.7** | ~3 |
| Post-frontal (6 events) | 7–13 | 92–178 | **2.4–3.2** | 61–116 |

Warm sectors are the unblocked, high-IVT, high-enhancement regime; post-frontal flow is blocked
(M ≫ 1) and weakly forced. Latent heating during ascent reduces effective stratification, so flows
that would be blocked in dry air often surmount the barrier when condensation occurs (FACT, Minder
& Roe, citing Jiang 2003) — the "effective M" is lower than an upstream dry calculation implies.

### 2.5 Seeder–feeder, and the fact that orography alone produces almost nothing

Small-scale ridge-top precipitation maxima in the Olympics are produced by the **seeder–feeder**
mechanism (Bergeron 1969): synoptically generated precipitation falls from aloft through low-level
orographic cloud and grows by collecting cloud droplets (FACT, Minder & Roe; Minder et al. 2008).

The magnitude of the synoptic dependence is measurable. In Purnell & Kirshbaum's (2018) Olympics
simulations, removing the large-scale forcing while keeping identical upstream wind, moisture and
stability collapses the drying ratio (FACT, their Table 6, fetched):

| Simulation | DR | DR* (orographic only) | DR_w (windward) |
|---|---|---|---|
| WF.control | 0.21 | 0.06 | 0.15 |
| **WF.noforce** | **0.01** | 0.01 | 0.01 |
| WS.control | 0.20 | 0.11 | 0.14 |
| **WS.noforce** | **0.06** | 0.06 | 0.04 |

A twentyfold (warm-frontal) or threefold (warm-sector) reduction. Separately, adding a uniform
mid/upper-tropospheric ascent of only **0.2 m s⁻¹** to trigger seeder–feeder growth produced "more
than a factor-of-three increase in the windward-slope precipitation" (FACT, as reported in Tierney
& Durran 2024). Orographic enhancement is a *multiplier on a storm*, and the multiplier is the
part models get least wrong; the storm is the part they get wrong.

### 2.6 Microphysical timescales, fall speeds, and where the water lands

- Cloud particles must grow ~**10⁹-fold in volume** before they precipitate (FACT, Minder & Roe).
- Fall speeds: snow **0.5–2 m s⁻¹**, rain **7–10 m s⁻¹**, graupel intermediate (FACT, ibid.).
  At 20 m s⁻¹ cross-barrier wind, a snowflake falling 3 km at 1 m s⁻¹ drifts **60 km**; a raindrop
  falling the same distance at 8 m s⁻¹ drifts 7.5 km. Precipitation phase therefore relocates the
  precipitation, not merely its form.
- Hobbs et al. (1975) simulated a winter orographic storm at varying cloud-ice concentration: at low
  concentration snow grew fast and fell on the windward slopes; at high concentration growth was slow
  and snow was blown **nearly 100 km into the lee** (FACT, Minder & Roe).
- Consequence: the *same* model with a different microphysics scheme produces a different basin QPF.
  In the IMPROVE-2 Oregon Cascades case, of seven microphysics parameterisations tested, two clearly
  outperformed the rest, which **overpredicted snowfall by ~30–60 %** against SNOTEL (INFERENCE —
  search-result summary of Garvert/Colle/Mass IMPROVE-2 work; not independently fetched).

### 2.7 The melting level and the mountainside snow line

- The observed melting level sits **~200–400 m below the free-air 0 °C isotherm** (FACT, Neiman et
  al. 2011 JHM, fetched, citing Stewart et al. 1984 and White et al. 2002 — this is the number they
  subtract from NARR 0 °C heights).
- On a mountainside the snow line is depressed a further **"hundreds of metres" below its free-air
  upwind elevation**, from three mechanisms: latent cooling by melting precipitation, adiabatic
  cooling in orographic ascent, and the finite melting distance of frozen hydrometeors. The
  depression **increases with increasing temperature**, which would buffer mountain hydroclimates
  against warming, and it depends substantially on the microphysics scheme used (FACT, Minder,
  Durran & Roe 2011, JAS 68, fetched abstract).
- Melting-level depression over windward slopes "can amount to **0.5 km or more**" (FACT, Minder &
  Roe, citing Marwitz 1981).
- **An NWS Seattle document gives the offset directly.** In a WFO Seattle case study, the Quillayute
  sounding indicated a **freezing level of 3,500 ft** and "an ambient snow level of around
  **2,500 ft**", with the note that evaporational cooling inside heavier convergence-zone
  precipitation "likely forced it lower" (FACT, McDonnal & Colman, WFO Seattle,
  weather.gov/media/wrh/online_publications/talite/talite0344.pdf, fetched). That is a 1,000 ft
  offset in an NWS-Seattle-authored source.

### 2.8 Spillover, the rain shadow, and the drying ratio for these ranges

- The Cascade rain shadow is "among the strongest in the world", with **annual precipitation of more
  than 4 m on many western ridges and less than 25 cm in much of the Columbia River basin to the
  east** (FACT, Siler, Roe & Durran 2013, JHM 14, fetched).
- Interannual variability: a **rain-shadow index explains up to 31 %** of wintertime precipitation
  variance west and east of the crest, weak shadows correlate with El Niño and strong ones with
  La Niña, and **~70 % of the interannual variability in shadow strength is explained by large-scale
  circulation** (FACT, Siler et al. 2013; the 70 % figure as restated in Siler & Durran 2016,
  fetched).
- **Storm-type control.** In the Washington Cascades the *strongest* rain shadows occur in
  warm-sector storms and the *weakest* during warm-frontal passages; the mechanism is that a cold,
  zonally stagnant layer in the lee ahead of the warm front suppresses mountain-wave amplitude and
  therefore lee-side evaporation, and it persists long after frontal passage (FACT, Siler & Durran
  2016, JAS 73, fetched).
- **The Olympics behave oppositely.** There, precipitation shadows are *strongest* in warm-frontal
  events, because the quasi-axisymmetric massif lets impinging air detour laterally rather than
  build a lee cold pool (FACT, Purnell & Kirshbaum 2018, fetched). **Two ranges 100 km apart have
  opposite storm-type dependence of their rain shadows.** Any single regional "spillover" parameter
  is therefore wrong for one of them.
- **Drying ratios.** Sounding-constrained estimates give **DR = 48 % ± 2 % for the Sierras and
  Cascades**; deuterium changes of δD = 50–80 ‰ across four midlatitude ranges (Cascades, Sierras,
  Southern Andes, Southern Alps) suggest **DR = 30–50 %** (FACT, R. B. Smith, AMS 19th Mountain
  Meteorology abstract, fetched). Note this is a *whole-barrier, climatological* DR. The
  *event-scale, single-massif* drying ratios measured over the Olympics during OLYMPEX are much
  smaller: DR = **0.25 (WF) / 0.22 (WS) / 0.18 (PF)** including background precipitation, and the
  purely orographic component DR\* = **0.03 (WF) / 0.12 (WS) / 0.01 (PF)** (FACT, Purnell &
  Kirshbaum 2018, Table 4). By S&B04's own criterion (DR < 0.3) linear theory is inside its validity
  window for single western-WA massifs at event scale.

### 2.9 The Puget Sound Convergence Zone — a different mechanism entirely

The PSCZ forms when low-level westerly/north-westerly Pacific flow splits around the Olympic
Mountains and re-converges over Puget Sound, producing a narrow east–south-east band of convection
and precipitation that extends from the east entrance of the Strait of Juan de Fuca across
Snohomish County and **into the Cascades** (FACT, NWS Seattle WES case study, fetched; Wikipedia
summary citing Mass 2008, fetched). Key operational properties from the fetched NWS case study
(14–17 May 2003) (FACT):

- It forms *after* frontal passage, as surface pressure builds and low-level flow veers westerly,
  and dies as the upper-trough axis passes. In that case the trough lagged the surface front by
  ~72 h, giving an unusually long-lived PSCZ.
- Strong **diurnal cycle**: strengthening each day, peaking late afternoon/evening, weakening
  overnight.
- KATX radar showed **maximum echoes ~60 dBZ**, thunderstorms, quarter-inch hail accumulating to
  half an inch, and overnight snow accumulation at **Stevens and Snoqualmie Passes** in mid-May.

Frequency is most often quoted as "dozens of times per year", most frequent in late spring and early
summer when coastal flow is most often westerly (INFERENCE — Mass 1981 MWR is a scanned PDF whose
text could not be extracted; the count of 25 analysed events and the seasonality come from
search-result summaries and secondary explainers, not independently fetched). The PSCZ is
mechanistically important to Cascadia Papsukkal for one reason: **it deposits precipitation on the
Snohomish/Skykomish/Snoqualmie headwaters through a mechanism that is neither upslope nor
IVT-driven**, in the post-frontal sector where blocking (M ≫ 1) has already broken the upslope
relation.

### 2.10 Terrain-height dependence and the elevation of maximum precipitation

The naïve "precipitation increases with elevation" is wrong in detail here, in two separate ways.

1. **The maximum is on ridge *crests* at modest elevation, not at the highest peaks.** A dense rain
   and snow gauge network across Matheny Ridge in the south-west Olympics — an **~800 m high, ~10 km
   wide** ridge — measured **50 % higher precipitation on the ridge top than in the valleys 10 km
   away on either side** (FACT, Anders et al. 2007, JHM 8, fetched). Minder et al. (2008) put the
   annual-mean ridge-crest excess at **50–70 %**, with MM5 climatologies showing **50–300 %** local
   enhancement, and cite Anders et al. (2007) at 60–100 % and Colle (2008) at **200–300 % local
   ridge-top enhancement with a net 10–35 % enhancement over the windward slopes as a whole** (FACT,
   Minder et al. 2008, QJRMS 134, fetched). The mechanism is seeder–feeder over stable ascent on
   ridge flanks (§2.5), not elevation per se.
2. **Range-scale maxima sit well below the crest and well upwind of it.** S&B04's Olympics
   calculation puts the maximum *upwind* of Mount Olympus and predicts the high north-east peaks
   collect none (FACT). Washington's climatological wettest recorded station is **Wynoochee Oxbow,
   184 inches (4,670 mm) per year, at an elevation of only 600 ft (183 m)** (FACT, WRCC Washington
   climate narrative, fetched) — a station well below the Olympic crest that beats everything above
   it. On the west Cascade slope, WRCC gives **90 inches at 800–1,000 ft**, **60–100 inches or more**
   generally, and **140 inches** in the wetter areas in a 1-in-10 year (FACT, ibid.). The
   north-east-Olympic rain shadow reaches **~18 inches** at Sequim/Port Townsend/Coupeville (FACT,
   ibid.) — a ratio of **>10:1** across ~80 km.

---

## 3. Quantitative anchors

| Quantity | Value | Context | Source |
|---|---|---|---|
| IVT⊥ → windward rain rate, slope | **0.014 mm h⁻¹ per kg m⁻¹ s⁻¹** | Olympics, 6 OLYMPEX warm-sector events, 7 gauges 188–1,484 m | Tierney & Durran 2024 (FACT) |
| IVT⊥ → rain rate, variance explained | **r² = 0.87 / 0.82 / 0.85** (Quillayute / Taholah / pooled) | same | Tierney & Durran 2024 (FACT) |
| Optimal projection bearing | **224°** (Quillayute), **251°** (Taholah) | fitted, not assumed; differs by site because of flow deflection | Tierney & Durran 2024 (FACT) |
| Coast-sounding → gauge lag | **1–2 h** at ~15 m s⁻¹ | Olympics | Tierney & Durran 2024 (FACT) |
| Upslope flow → rain rate, case studies | **58–88 % of variance** (r = 0.761–0.939) | coastal California, CALJET, per-event | Neiman et al. 2002 (FACT) |
| Upslope flow → rain rate, whole season | **31 %, 41 %, 48 %**; **56 %** for LLJ periods | same sites, season-long | Neiman et al. 2002 (FACT) |
| Unblocked vs blocked correlation | r = **0.874–0.939** vs **0.761–0.832** | CALJET case studies | Neiman et al. 2002 (FACT) |
| Blocking criterion | **M = Nh/U > 1** | standard | Minder & Roe (FACT) |
| Measured M, Olympics, by sector | WF **1.1**, WS **0.7**, PF **2.4–3.2** | 18 OLYMPEX frontal periods | Purnell & Kirshbaum 2018 (FACT) |
| Mean IVT by sector, Olympics | WF **525**, WS **640**, PF **92–178** kg m⁻¹ s⁻¹ | same | Purnell & Kirshbaum 2018 (FACT) |
| Event drying ratio, Olympics | DR **0.25/0.22/0.18** (WF/WS/PF); DR\* **0.03/0.12/0.01** | orographic-only DR\* excludes background rain | Purnell & Kirshbaum 2018 (FACT) |
| Barrier-scale drying ratio | **48 % ± 2 %** (Sierras + Cascades); 30–50 % from δD | soundings / isotopes, climatological | R. B. Smith, AMS 19MountMet (FACT) |
| Orographic enhancement without synoptic forcing | DR falls **0.21 → 0.01** (WF), **0.20 → 0.06** (WS) | identical upstream wind/moisture/stability | Purnell & Kirshbaum 2018 (FACT) |
| Seeder–feeder trigger sensitivity | 0.2 m s⁻¹ uniform ascent → **>3×** windward precipitation | idealised Olympics WRF | Purnell & Kirshbaum 2018 via Tierney & Durran 2024 (FACT) |
| S&B04 canonical Olympics parameters | U 15 m s⁻¹ SW, N_m 0.005 s⁻¹, H_w 2.5 km, τ_c = τ_f = **1000 s** | linear-theory demo run, 1 km grid, terrain smoothed to 800 m | Smith & Barstad 2004 (FACT) |
| S&B04 precipitation efficiency vs τ | PE **79 → 70 → 55 → 39 %** for τ = 250 → 2000 s | Gaussian ridge a = 15 km | Smith & Barstad 2004, Table 5 (FACT) |
| Raw upslope model error at fine scale | **overestimates by ≥5×** at terrain scales ≤20 km; needs **≥30 km** smoothing | why DEM-based upslope downscaling fails | Smith & Barstad 2004 (FACT) |
| Ridge–valley precipitation contrast, Olympics | **+50 %** measured (gauges); **50–70 %** annual mean; **50–300 %** in MM5; 200–300 % local, 10–35 % net (Colle 2008) | ~10 km wide, ~800 m high ridges | Anders et al. 2007; Minder et al. 2008 (FACT) |
| Rain-shadow ratio, Cascades | **>4 m** west ridges vs **<25 cm** Columbia basin | annual | Siler et al. 2013 (FACT) |
| Rain-shadow ratio, Olympics | **184 in** (Wynoochee Oxbow, 600 ft) vs **~18 in** (Sequim) | annual, ~80 km apart | WRCC (FACT) |
| Rain-shadow interannual variance explained | index explains up to **31 %**; **~70 %** of shadow variability from large-scale circulation | SNOTEL-based | Siler et al. 2013; Siler & Durran 2016 (FACT) |
| Storm concentration, Olympics | **50 % of annual precipitation in 7–12 storms** per year (2003–06) | | Minder et al. 2011 via Tierney & Durran 2024 (FACT) |
| Melting level below free-air 0 °C | **200–400 m** | used operationally in NARR compositing | Neiman et al. 2011 (FACT) |
| Snow level below freezing level, NWS Seattle case | **1,000 ft** (3,500 ft FL → 2,500 ft SL) | Quillayute sounding, 16 May 2003 | McDonnal & Colman, WFO Seattle (FACT) |
| Melting-level depression over windward slopes | **≥0.5 km** | | Marwitz 1981 via Minder & Roe (FACT) |
| Composite melting level, top-10 flood days | **~1.9 km MSL** (range 1.5–2.3), ~1 km above the **0.95 km** in-storm climatology | Green, Sauk, Satsop, Queets; 28 yr Quillayute climatology | Neiman et al. 2011 (FACT) |
| 2-day precipitation, top-10 peak flows | **85–150 mm** (Green, Sauk — Cascades); **100–175 mm** (Satsop, Queets — Olympics) | NARR composites | Neiman et al. 2011 (FACT) |
| AR fraction of annual peak daily flows | **46 of 48**; other two were snowmelt | 4 western-WA basins | Neiman et al. 2011 (FACT) |
| Basin-specific flood wind direction | Green: **245°–275° only**; Sauk: rain-shadowed except southwesterly; Queets/Green flood on near-westerly, Sauk/Satsop on southwesterly, separation significant at **>95 %** | the sharpest single result for this platform | Neiman et al. 2011 (FACT) |
| Interannual peak-flow range | Queets varies by **3.5×**, Green by **an order of magnitude** | consequence of the narrow direction window | Neiman et al. 2011 (FACT) |
| Radar coverage, coastal western US | only **¼ to ⅓** of land surface adequately covered for QPE; **<¼** excluding partially blocked; coverage absent over **⅔** even counting partial | terrain blockage + shallow precipitation + low freezing levels | Westrick, Mass & Colle 1999 (FACT) |
| Radar QPE error in heavy precipitation | **<50 % of rain-gauge values** | Portland radar, February 1996 flood | Westrick et al. 1999 (FACT) |
| Radar coverage vs precipitation climatology | "little radar coverage over the regions of heaviest climatological precipitation"; **Snoqualmie and Chehalis** basins named as poor-or-nonexistent | 1999, pre-KLGX | Westrick et al. 1999 (FACT) |
| Radar generally in complex terrain | "frequently report less than 50 % of observed precipitation" | review | Lundquist et al. 2019 (FACT) |
| MRMS RQI definition | RQI = RQI_blk × RQI_hgt; **RQI_blk = 0 above 50 % blockage, 1 at ≤10 %**, linear between | the gate the platform should use | NOAA WDTD (FACT) |
| Mountain Mapper method | ratio of hourly gauge to PRISM-disaggregated hourly climatology, **IDW with b = 2, D = 200 km**, × PRISM hourly | all accumulations derive from the 1 h estimate | NOAA WDTD (FACT) |
| Gauge undercatch, western Washington cool season | **25–40 %** above 1,500 m; **15–20 %** in Cascade gaps (~1,000 m); **5–15 %** lowlands | derived from collocated wind/temp/precip | Colle, Mass & Westrick 2000 (FACT) |
| Gauge undercatch, unshielded weighing gauges | mean **34 %** (0.50 mm h⁻¹) across 8 WMO-SPICE sites; adjusted bias within **2 %** | transfer function CE = a·e^(−bU) + (1−a), capped at U_thresh = **7.2 m s⁻¹** | Kochendorfer et al. 2018 (FACT) |
| Solid-precipitation measurement error, general | **20–50 %** in windy conditions | | Rasmussen et al. 2012 (INFERENCE — search summary, not independently fetched) |
| MM5 PNW bias structure | light/moderate events: **overprediction on upper windward slopes**; heavy events: **underprediction in lowlands and Cascade gaps** | 250+ sites, 1997–99 cool seasons | Colle, Mass & Westrick 2000 (FACT) |
| Resolution effect on basin water mass | **+15 %** 36→12 km, **+10 %** 12→4 km; over some windward slopes precipitation **more than doubled** | western Washington | Colle et al. 2000 (FACT) |
| Resolution ≠ skill | 4 km still had larger RMS error than 12 km at many thresholds even after screening for synoptic error; 36 km *with* screening ≈ 12 km without | the error is dominated by the incoming flow | Colle et al. 2000 (FACT) |
| Modern model bias, Pacific ranges | NCAR-ENS control **~112 %** of observed cool-season total; HRRR close to observed; SREF-NMMB **~78 %**; NAM-3km mean bias ratio **1.319** | SNOTEL-based, western US, 2016/17 | Gowan, Steenburgh & Schwartz 2018 (FACT) |
| Convection-permitting cross-barrier bias | bias ratio **<1 on windward slopes, ~1 at crest, >1 in the lee** for NCAR-ENS, HRRR, NAM-3km — "typically increase as one moves climatologically downstream across mountain barriers" | may be model bias or PRISM bias — the authors do not resolve it | Gowan et al. 2018 (FACT) |
| Observational floor for verification | bias ratios of **0.85–1.2 treated as near-neutral** because of undercatch | i.e. ±15–20 % is unresolvable with gauges | Gowan et al. 2018 (FACT) |
| Models vs gauge-interpolated grids | at independent sites models beat gridded estimates for annual totals **by a factor of 2** | | Lundquist et al. 2019 (FACT) |
| Spread among gridded precipitation datasets | typically **±20 %** in annual means, western US; **200 mm yr⁻¹ or 5–60 %** in complex terrain, greatest in maritime ranges | | Lundquist et al. 2019 citing Henn et al. 2018 (FACT); Henn 2018 numbers via search summary (INFERENCE) |
| Gridded-product failure mode | underpredicted by **up to 50 %** for events with a large postfrontal fraction | California snow pillows | Lundquist et al. 2015 via Lundquist et al. 2019 (FACT) |
| PRISM/WRF frozen precipitation, Olympics | near-peak SWE unbiased on average but **30–60 % absolute error at some sites**; WRF+wet-bulb partitioning biased low **21 %** | OLYMPEX WY2016, SUMMA | Currier, Thorson & Lundquist 2017 (FACT) |
| NWRFC extreme daily precipitation thresholds | top 1 % = **33.0 mm/24 h**; top 0.1 % = **73.7 mm/24 h** | 32-km Stage IV grid, 2001–11, whole NWRFC region incl. dry interior | Sukovich et al. 2014, Table 2 (FACT) |
| Extreme QPF skill by region | WPC extreme QPF verifies **best in the west (NWRFC/CNRFC/CBRFC) and northeast**, best in the cool season; western/eastern MAE_cond about **half** that of central/southern RFCs | AR-driven synoptic events are the predictable kind | Sukovich et al. 2014 (FACT) |
| NBM post-processing weak link | NBM does not resolve terrain-trapped cold pools and inherits URMA's analysis error; warm bias **>15 °C** in extreme cases | temperature, Canaan Valley WV — transferability to precipitation not established | Schaefer et al. 2026, *J. Operational Meteor.* (FACT) |

---

## 4. What is settled, what is emerging, what is contested

**Settled (established).**

- Precipitation over a barrier scales with the cross-barrier moisture flux, and the relevant wind is
  near mountaintop / low-level-jet altitude (~1 km MSL), not at the surface and not at 700 hPa.
- The non-dimensional mountain height M = Nh/U governs whether that relationship holds; blocked flow
  moves precipitation upstream and flattens its spatial structure.
- Seeder–feeder growth over windward ridges produces persistent, repeatable, **~10 km-scale**
  precipitation maxima on ridge crests, and the pattern is robust to changes in temperature, winds
  and background rain rate.
- Orographic ascent alone produces very little precipitation; the enhancement is a multiplier on
  synoptically forced precipitation.
- Radar QPE is structurally inadequate over the Cascade and Olympic headwaters, and gauges undercatch
  in a wind- and temperature-dependent way that is largest exactly where the precipitation is largest.
- Raw upslope models applied to unsmoothed terrain violate water conservation.

**Emerging.**

- **Models are now better than observation-based grids for mountain precipitation totals.** The
  claim (Lundquist et al. 2019) is well argued and increasingly accepted, but it inverts several
  decades of hydrological practice and rests on a small number of independent-site comparisons.
- **Idealised unidirectional-flow simulations systematically underpredict the IVT⊥–rainfall
  relationship** by a large factor (Picard & Mass 2017 required >3× the IVT to reach the observed
  rate; Purnell & Kirshbaum 2018's warm-sector run gave 0.88 mm h⁻¹ at IVT = 607 kg m⁻¹ s⁻¹).
  Tierney & Durran (2024) argue this is a *simulation-design* artefact, not a model-physics defect.
  If it is a model defect, operational convection-permitting models under-produce orographic
  precipitation in exactly the AR regime that floods this region. Unresolved.
- **Nonstationarity of the transfer function.** Kirshbaum & Smith (2008) find that orographic
  precipitation becomes *less efficient* at extracting moisture as the atmosphere warms, buffering
  the Clausius–Clapeyron increase; Minder et al. (2011) find snow-line depression *increases* with
  temperature, buffering snowpack loss. Both are model results.

**Contested.**

- **The direction of the cross-barrier bias in convection-permitting models.** Gowan et al. (2018)
  find bias ratio rising windward→leeward across barriers in NCAR-ENS, HRRR and NAM-3km and
  explicitly decline to say whether this is a model bias or a PRISM bias. Colle et al. (2000) found
  MM5 *overpredicting* windward slopes at light-moderate thresholds and *underpredicting* lowlands
  and gaps at heavy thresholds. These are not the same picture, they use different verification
  references, and the disagreement matters directly to basin-mean QPF.
- **Whether higher resolution improves basin QPF.** Colle et al. (2000) found 4 km worse than 12 km
  at many thresholds even after screening for synoptic error; Gowan et al. (2018) found higher
  resolution "more deterministically skillful", especially over narrow interior ranges. Both are
  defensible; the reconciliation is probably that resolution helps *where* precipitation is placed
  and does not help *how much* arrives.
- **The storm-type dependence of the rain shadow reverses between the Olympics and the Cascades**
  (§2.7). Siler & Durran (2016) and Purnell & Kirshbaum (2018) both note this explicitly. There is no
  single regional spillover rule.
- **Whether the mountain snow line's temperature sensitivity is real in nature.** Minder et al.
  (2011) state the buffering result conditionally ("if present in nature") and show it depends on the
  microphysics scheme.

---

## 5. Western Washington specificity — what transfers and what does not

**Transfers well.** The upslope/IVT⊥ formalism, the Froude/blocking criterion, seeder–feeder, the
S&B04 timescale structure, and the gauge-undercatch transfer functions are physics and instrument
behaviour; they are not regional. The OLYMPEX-derived IVT⊥ regression (§2.2) is *itself* western
Washington, which is unusual good fortune — most of the AR literature the platform cites is
Californian.

**Transfers with care.**

- **California upslope results.** Neiman et al. (2002, 2009) and Kingsmill et al. (2016) concern
  coastal ranges of **~600–750 m** peak elevation, an order of magnitude lower than the Cascade
  crest and with far less blocking. The Cascades at M ≈ 1 sit near the blocking transition where the
  Californian coastal ranges rarely do. Californian variance-explained numbers are an *upper* bound
  for the Cascades and probably a *lower* bound for the Olympics' lower windward slopes.
- **Alpine and Rocky Mountain results.** Continental, drier, colder, more convective, with different
  microphysical regimes. Use for mechanism, not for magnitude.
- **Colorado / interior-range model verification.** The interior ranges are the regime where
  convection-permitting models show their largest *relative* advantage (Gowan et al. 2018); the
  Pacific ranges are where all the models are already close to unbiased on the seasonal total and
  wrong in the spatial distribution. Do not import an interior-range bias correction.

**Does not transfer.**

- **The Puget Sound Convergence Zone has no analogue in the AR literature.** It is a post-frontal,
  diurnally modulated, terrain-wake convergence band that lands on the Snohomish/Skykomish/Snoqualmie
  headwaters at a time when the upslope relation has already failed (M ≫ 1). No IVT-based reasoning
  will see it.
- **Basin aspect is decisive here in a way it is not on a straight coast.** The Olympics + Vancouver
  Island Mountains put the *entire* Cascade front in someone's rain shadow for most onshore
  directions. The Green's 245°–275° window (FACT, Neiman et al. 2011) has no Californian equivalent.
- **The maritime, near-freezing snow regime.** Melting-level depression, riming, wet-bulb-based phase
  partitioning and the transient snow zone all behave differently from a continental snowpack.

---

## 6. What this means for Cascadia Papsukkal

**P0 — the orientation feature.** `cascade_hydrology.forcing` currently derives basin-mean QPF from
NBM and a basin-mean snow level, and `DATA_SOURCES.md` W2 lists IVT/AR scale as "not ingested in v0,
deliberately". The literature says the highest-value forcing feature available is not IVT magnitude
but **IVT⊥ per basin**: IVT projected onto a per-basin cross-barrier bearing, stored as a
`CONFIGURED` basin attribute with its provenance. Neiman et al. (2011) supply defensible starting
bearings for two of the platform's own basins (**Green 245°–275°**, **Sauk south-westerly**) and the
method for deriving the rest (fit the bearing that maximises correlation with basin response over
history — the same fitting Tierney & Durran did per sounding site). This is the single largest
available skill gain in the forcing surface and it needs one new field from GFS/GEFS.

**P0 — a blocking flag, not a blocking correction.** Compute **M = N h / U** from the model sounding
upstream of each basin (h = basin barrier height from the DEM, U = cross-barrier wind, N from the
model temperature profile) and emit it as a *driver that qualifies the QPF's confidence*, not as a
multiplier. Purnell & Kirshbaum's measured values give the bands: **M ≲ 0.8 unblocked / high
enhancement; M ≈ 1 transitional; M ≳ 2 blocked, enhancement collapses and precipitation shifts
upstream**. Under `DATA_DOCTRINE` §9 this is a *labelled category*, never a decimal confidence.

**P0 — MRMS must be gated on RQI, not merely accompanied by it.** `DATA_SOURCES.md` P1 already says
"ingest RQI and GaugeInflIndex with every QPE". Make it binding: a basin-mean MRMS APE/API value
computed over cells whose RQI is below a stated threshold is `quality=out_of_range` with a reason,
not a number. The published RQI construction (RQI_blk = 0 above 50 % blockage) means an
RQI-weighted basin mean is computable and auditable.

**P1 — record which MRMS engine produced each cell.** Where MRMS falls back to **Mountain Mapper**,
the value is *PRISM climatology re-scaled by an inverse-distance-weighted (b = 2, D = 200 km) ratio
to low-elevation gauges*. Its stated failure mode is "large errors when real-time precipitation
gradients diverge significantly from PRISM climatology" — which is precisely the blocked, warm-frontal
and convergence-zone cases. This is a `source_kind` and lineage question, not a footnote: a
Mountain-Mapper cell is a *climatological downscaling of a distant gauge*, and the platform's one
rule ("what transformed it") requires saying so.

**P1 — precipitation observations need a catch-efficiency field.** Colle et al. (2000) give
region-specific cool-season undercatch for exactly this domain: **5–15 % lowlands, 15–20 % Cascade
gaps, 25–40 % above 1,500 m**. Kochendorfer et al. (2018) give the functional form
`CE = a·exp(−b·U) + (1−a)`, capped at U_thresh = 7.2 m s⁻¹ for unshielded gauges. Either apply the
correction as a **DERIVED** value with lineage to the raw reading, or carry an
`undercatch_class` on every precipitation observation. Silently comparing an uncorrected SNOTEL
`PREC` at 1,400 m against an NBM basin mean is a 25–40 % error with a known sign. `DATA_SOURCES.md`
S2 already prefers `PRCPSA` in the snow season — generalise that instinct into a field.

**P1 — close the W8 snow-level offset open question.** `DATA_SOURCES.md` W8 records "an
authoritative weather.gov/sew citation is an OPEN QUESTION" and currently rests on KIRO 7 and
OpenSnow. Two better citations now exist: (a) **NWS WFO Seattle** (McDonnal & Colman, WES technical
attachment) documents a Quillayute freezing level of 3,500 ft with an ambient snow level of
~2,500 ft — a 1,000 ft offset in an NWS-Seattle-authored source; (b) **Neiman et al. (2011, JHM)**
subtract **300 m** from NARR 0 °C heights on the basis that the melting level is **200–400 m** below
the isotherm (Stewart et al. 1984; White et al. 2002). The repo's 1,000 ft default with a
500–1,500 ft sensitivity range survives both, and can now be sourced peer-reviewed.

**P1 — the forcing bands need a sanity check against observed flood forcing.**
`forcing.FORCING_BANDS` uses 25 / 75 / 150 mm per 72 h (LOW/MODERATE/HIGH/VERY_HIGH), documented as
an ASSUMPTION. Two independent anchors suggest the upper edges sit high. Neiman et al. (2011) report
that the **top-10 annual peak daily flows on the Sauk and Green occurred with 2-day Cascade
precipitation totals of 85–150 mm** — i.e. events that produced these basins' largest recorded flows
of the past 30 years would land in the platform's **HIGH** band and only just touch VERY_HIGH.
Sukovich et al. (2014) put the NWRFC region's top-0.1 % daily precipitation at **73.7 mm/24 h** on a
32-km grid. Both comparisons carry caveats (NARR composites and 32-km Stage IV are both smoothed;
the NWRFC region includes the dry interior; a 72-h NBM pointwise-p50 basin mean is not a 2-day
observed total) — but the direction is consistent and this is a cheap, high-value hindcast check
(INFERENCE).

**P2 — never downscale QPF with a static orographic ratio.** Any scheme of the form "basin QPF ×
elevation ratio" or "NBM cell × PRISM ratio" is the Mountain Mapper failure mode reimplemented, and
S&B04's factor-of-5 warning applies to the DEM-based version. If sub-basin distribution is ever
needed, the defensible options are (a) use the model's own field at its native resolution and say so,
or (b) implement S&B04 properly as a named, versioned `EXPERIMENTAL` method with its five parameters
recorded, never a ratio.

**P2 — basin-mean is the right aggregation; per-cell display is not.** The ridge-crest signal is
**50–300 %** at ~10 km scale (§2.10), which is at or below the NBM 2.5 km grid's *effective*
resolution and far below what a 2.5 km grid can be trusted to place correctly. Rendering an NBM cell
value on a map as "precipitation here" asserts placement skill the product does not have. The
basin-mean, with its cell count and weight sum already recorded by `method:basin-qpf@1.0.0`, is the
honest unit.

**P2 — add a PSCZ awareness path.** The convergence zone is post-frontal, terrain-wake driven,
diurnally peaking, and lands on Snohomish/Snoqualmie headwaters. It will not appear in any IVT
feature and it is poorly handled by coarse QPF. At minimum: do not let a low forcing level derived
from IVT/QPF be rendered as reassurance during post-frontal north-westerly flow, and consider a
`mechanism` context driver (AR-upslope / post-frontal-convective / convergence-zone) that is
displayed and never scored.

**P2 — new data sources worth their cost.** GFS/GEFS wind and moisture profiles for IVT⊥ and N (W5,
already planned); MRMS RQI and GaugeInflIndex alongside every QPE (P1, already planned — make it
mandatory); NBM `SNOWLVL` percentiles (already ingested as a context driver — keep it unscored until
the offset parameter is versioned); a per-basin cross-barrier bearing and barrier height derived from
the DEM (`packages/geo`), stored `CONFIGURED` with provenance.

---

## 7. What this domain contradicts or qualifies in current repo doctrine

1. **`HYDROLOGY.md` §2, "Precipitation increases steeply with elevation on windward slopes"** —
   *qualified, and materially.* The controlling geometry is the **terrain gradient along the flow and
   ridge-crest position**, not elevation. Washington's wettest recorded station is at **600 ft**; the
   Olympics' ridge-crest maxima are on **800 m** ridges; S&B04's Olympics run predicts the highest
   north-east peaks collect nothing. Elevation is a proxy that fails at exactly the sub-basin scale
   where it is most tempting to use. The sentence should say "precipitation increases steeply on
   windward slopes and maximises on ridge crests upwind of the crest, not at the highest elevations."

2. **`HYDROLOGY.md` §4, IVT features** — *qualified.* The table lists "IVT magnitude, direction,
   duration; AR scale". Direction is not a co-equal attribute of IVT; **the projection of IVT onto the
   basin's own terrain gradient is the quantity with predictive skill**, and the projection bearing is
   basin-specific and must be fitted, not assumed. The AR scale, computed from unprojected IVT
   magnitude (per `DATA_SOURCES.md` W8), is by construction blind to the strongest discriminator in
   this region.

3. **`docs/research/flood-genesis-mechanisms-2026-08-24.md` §2.2 and §7 row 5** — *corrected.* The
   document reports "58–88 % (Neiman 2002) and 74 % (Ralph 2013) of rain-rate variance" as the
   orographic transfer function's skill. Reading the fetched Neiman et al. (2002): 58–88 % is the
   **per-case** range across seven selected case studies; the **season-long** figures at the same
   three couplets are **31 %, 48 % and 41 %**, rising to 56 % in low-level-jet conditions. And the
   74 % (Ralph et al. 2013) is **storm-total** rainfall variance, in **coastal California**, not
   hourly rain rate in Washington. The honest headline number for western Washington is Tierney &
   Durran's **r² = 0.85 for warm-sector, unblocked Olympics events**, with the explicit caveat that
   warm-sector unblocked periods are the *best case*.

4. **`HYDROLOGY.md` §2, "basin-average QPF from a coarse model can be badly wrong in the mountains"**
   — *confirmed and now quantifiable.* The bias is not random: light/moderate events are
   over-predicted on upper windward slopes and heavy events under-predicted in lowlands and Cascade
   gaps (Colle et al. 2000); modern convection-permitting models show bias ratio rising
   windward→leeward (Gowan et al. 2018). "Carries its own uncertainty" should become "carries its own
   *signed, regime-dependent* uncertainty", and the regime label (M, frontal sector) should travel
   with it.

5. **`DATA_SOURCES.md` P1 MRMS limitations** — *confirmed, and stronger than stated.* The repo says
   "Skagit/Nooksack/Snoqualmie headwaters remain beam-blocked or overshot". Westrick, Mass & Colle
   (1999) name the **Snoqualmie** as one of six flood-prone basins whose coverage is "either extremely
   poor or nonexistent", quantify regional adequacy at **¼–⅓ of the land surface**, and show radar
   reading **<50 % of gauge values** in the heaviest precipitation of a real flood. The pre-KLGX
   caveat applies to the coastal gap; it does not apply to the Cascade headwaters.

6. **`DATA_SOURCES.md` W8 snow-level offset** — *the open question can be closed* (see §6 above).

7. **`forcing.py` band edges** — *challenged with evidence, not overturned.* See §6, P1. The module
   already labels them an ASSUMPTION and caps confidence; this corpus supplies the first external
   numbers to test them against.

8. **`DATA_DOCTRINE.md` §2 source-kind taxonomy applied to QPE** — *one gap.* MRMS is tagged
   `OBSERVED` with `method=radar_qpe`. In western Washington a large fraction of MRMS cells over the
   basins of interest are **not radar-derived at all** — they are Mountain Mapper (PRISM climatology ×
   gauge ratio) or HRRR 1-h QPF fill. Those are `MODELED` and `DERIVED` respectively, and blanket
   `OBSERVED` tagging would be exactly the "never silently substitute one kind for another" violation
   the doctrine forbids.

9. **Nothing in `HYDROLOGY.md` was found to be wrong** in this domain. Items 1, 2 and 4 are
   incomplete; item 3 is an error in a research file, not in doctrine; items 5, 6, 8 are
   implementation-level.

---

## 8. Open questions

1. **What is the correct cross-barrier bearing for each of the eight platform basins?** Neiman et al.
   (2011) give Green (245°–275°) and Sauk (southwesterly). Snoqualmie, Skykomish, Stillaguamish,
   Nooksack, White and Cedar are unknown. The method is published and the platform has the data
   (basin polygons + DEM + GFS profiles + USGS peak flows). This is a bounded, high-value derivation.
2. **Does the OLYMPEX IVT⊥ regression (0.014 mm h⁻¹ per kg m⁻¹ s⁻¹) transfer to the Cascade front?**
   The Cascades are twice as high and blocked more often (M ≈ 1 vs the Olympics' warm-sector 0.7). An
   independent fit for a Cascade basin is testable against MRMS/Stage IV and NBM history.
3. **Is the windward→leeward bias-ratio gradient in HRRR/NBM a model bias or a PRISM bias?** Gowan et
   al. (2018) explicitly decline to answer. It determines whether a basin-mean QPF over a
   windward-facing Cascade basin should be corrected upward and by how much.
4. **What fraction of MRMS cells over each platform basin are Mountain Mapper or model-fill rather
   than radar, by month?** Computable from the MRMS product suite; determines whether MRMS-based API
   is an observation at all in the upper basins.
5. **Does the NBM v5 quantile-mapping post-processing preserve or destroy terrain structure over the
   Cascades?** Hamill et al. (2023) report that short training data plus supplemental locations
   "reduced the amount of terrain-related precipitation detail in the western United States"; whether
   v5's training regime fixed this for the Cascades is unverified (INFERENCE — search summary only).
6. **How will the HRRR → RRFS/REFS transition (2026-10-06) change orographic QPF bias in western
   Washington?** No verification of RRFS precipitation over the Cascades was found. `DATA_SOURCES.md`
   already schedules shadow ingest of `rrfs/para`; a bias comparison over the first flood season is
   the natural exit test.
7. **What is a defensible PSCZ climatology for the flood season?** Mass (1981) is a scanned PDF; no
   modern objective climatology was reached. Frequency, seasonal distribution, and precipitation
   contribution to the Snohomish/Snoqualmie basins are all unquantified here.
8. **Does the idealised-simulation underprediction of the IVT⊥–rainfall relation appear in operational
   models?** If it does, HRRR/RRFS/NBM under-produce orographic precipitation in exactly the AR
   warm-sector regime that floods western Washington. Tierney & Durran (2024) Part II addresses the
   cause but not the operational implication.
9. **What is the effective undercatch of the specific gauges the platform reads** (SNOTEL storage
   gauges, HADS tipping buckets, King County HYDSTRA network), by site, in winter? The transfer
   functions exist; the site metadata (shield type, gauge height, wind exposure) does not.

---

## 9. Sources

Fetched and text-extracted for this entry (FACT-bearing):

- [Smith & Barstad 2004 — A Linear Theory of Orographic Precipitation, *J. Atmos. Sci.* 61, 1377–1391](https://journals.ametsoc.org/downloadpdf/view/journals/atsc/61/12/1520-0469_2004_061_1377_altoop_2.0.co_2.pdf)
- [Minder & Roe — *Orographic Precipitation*, Encyclopedia of Snow, Ice and Glaciers (Springer)](https://earthweb.ess.washington.edu/roe/GerardWeb/Publications_files/MinderRoe_OrogPrecEncyc.pdf)
- [Tierney & Durran 2024 — Underestimates of Orographic Precipitation in Idealized Simulations, Part I, *J. Atmos. Sci.* 81](https://atmos.uw.edu/~durrand/pdfs/AMS/2024A_Tierney_Durran_JAS.pdf)
- [Neiman et al. 2002 — The Statistical Relationship between Upslope Flow and Rainfall in California's Coastal Mountains, *Mon. Wea. Rev.* 130, 1468](https://journals.ametsoc.org/downloadpdf/view/journals/mwre/130/6/1520-0493_2002_130_1468_tsrbuf_2.0.co_2.pdf)
- [Neiman et al. 2011 — Flooding in Western Washington: The Connection to Atmospheric Rivers, *J. Hydrometeor.* 12, 1337](https://journals.ametsoc.org/downloadpdf/view/journals/hydr/12/6/2011jhm1358_1.pdf)
- [Purnell & Kirshbaum 2018 — Synoptic Control over Orographic Precipitation Distributions during OLYMPEX, *Mon. Wea. Rev.* 146, 1023](http://olympex.atmos.washington.edu/publications/2018/MWR18_Purnell-etal_SynopticControl.pdf)
- [Siler, Roe & Durran 2013 — On the Dynamical Causes of Variability in the Rain-Shadow Effect, *J. Hydrometeor.* 14, 122](https://www.atmos.washington.edu/~durrand/pdfs/AMS/2013_SilerRoeDurran_Hydro.pdf)
- [Siler & Durran 2016 — What Causes Weak Orographic Rain Shadows?, *J. Atmos. Sci.* 73, 4077](https://www.atmos.washington.edu/~durrand/pdfs/AMS/2016_Siler_Durran_JAS.pdf)
- [Anders, Roe, Durran & Minder 2007 — Small-Scale Spatial Gradients in Climatological Precipitation on the Olympic Peninsula, *J. Hydrometeor.* 8, 1068](https://www.atmos.washington.edu/~durrand/pdfs/AMS/2007Anders_etal.pdf)
- [Minder, Durran, Roe & Anders 2008 — The climatology of small-scale orographic precipitation over the Olympic Mountains, *Q. J. R. Meteorol. Soc.* 134, 817](https://www.atmos.albany.edu/facstaff/jminder/research/minder_et_al_cases_published.pdf)
- [Minder, Durran & Roe 2011 — Mesoscale Controls on the Mountainside Snow Line, *J. Atmos. Sci.* 68, 2107](https://www.atmos.washington.edu/~durrand/pdfs/AMS/2011_Minder_etal_JAS.pdf) (abstract extracted; body figures not)
- [Westrick, Mass & Colle 1999 — The Limitations of the WSR-88D Radar Network for Quantitative Precipitation Measurement over the Coastal Western United States, *BAMS* 80, 2289](https://journals.ametsoc.org/downloadpdf/view/journals/bams/80/11/1520-0477_1999_080_2289_tlotwr_2_0_co_2.pdf)
- [Colle, Mass & Westrick 2000 — MM5 Precipitation Verification over the Pacific Northwest during the 1997–99 Cool Seasons, *Wea. Forecasting* 15, 730](https://journals.ametsoc.org/downloadpdf/view/journals/wefo/15/6/1520-0434_2000_015_0730_mpvotp_2_0_co_2.pdf)
- [Gowan, Steenburgh & Schwartz 2018 — Validation of Mountain Precipitation Forecasts from the Convection-Permitting NCAR Ensemble and Operational Forecast Systems over the Western United States, *Wea. Forecasting* 33, 739](https://journals.ametsoc.org/downloadpdf/view/journals/wefo/33/3/waf-d-17-0144_1.pdf)
- [Lundquist, Hughes, Gutmann & Kapnick 2019 — Our Skill in Modeling Mountain Rain and Snow is Bypassing the Skill of Our Observational Networks, *BAMS* 100, 2473](https://journals.ametsoc.org/downloadpdf/view/journals/bams/100/12/bams-d-19-0001.1.pdf)
- [Currier, Thorson & Lundquist 2017 — Independent Evaluation of Frozen Precipitation from WRF and PRISM in the Olympic Mountains, *J. Hydrometeor.* 18, 2681](http://olympex.atmos.washington.edu/publications/2017/JHM17_Currier_et_al_IndepEval.pdf)
- [Kochendorfer et al. 2018 — Testing and development of transfer functions for weighing precipitation gauges in WMO-SPICE, *HESS* 22, 1437](https://hess.copernicus.org/articles/22/1437/2018/hess-22-1437-2018.pdf)
- [Sukovich, Ralph, Barthold, Reynolds & Novak 2014 — Extreme Quantitative Precipitation Forecast Performance at the Weather Prediction Center from 2001 to 2011, *Wea. Forecasting* 29, 894](https://cw3e.ucsd.edu/wp-content/uploads/2016/02/sukovich_etal_wf2014.pdf)
- [Schaefer et al. 2026 — Analysis of Persistent Bias and Suggested Improvements in Forecasting Temperature Patterns over Canaan Valley, West Virginia with the National Blend of Models, *J. Operational Meteor.* 14 (8), 110–128](https://nwafiles.nwas.org/file/nwafiles/jom/articles/2026/2026-JOM8/2026-JOM8.pdf)
- [McDonnal & Colman (NWS WFO Seattle) — An Investigation of the Puget Sound Convergence Zone Using WES, Western Region Technical Attachment](https://www.weather.gov/media/wrh/online_publications/talite/talite0344.pdf)
- [NOAA WDTD — Radar Quality Index (RQI)](https://vlab.noaa.gov/web/wdtd/-/radar-quality-index-rqi-)
- [NOAA WDTD — Mountain Mapper QPE](https://vlab.noaa.gov/web/wdtd/-/qpe-mountain-mapper)
- [R. B. Smith — Orographic Precipitation, Drying Ratio and Isotope Fractionation, AMS 19th Conf. on Mountain Meteorology (abstract)](https://ams.confex.com/ams/19Mountain/webprogram/Paper376241.html)
- [WRCC — Climate of Washington (narrative)](https://wrcc.dri.edu/Climate/narrative_wa.php)
- [Wikipedia — Puget Sound Convergence Zone](https://en.wikipedia.org/wiki/Puget_Sound_Convergence_Zone) (secondary; cites Mass 2008)

Cited but **not independently fetched** (claims drawn from them are labelled INFERENCE):

- Mass 1981 — Topographically Forced Convergence in Western Washington State, *Mon. Wea. Rev.* 109. PDF retrieved but is a scanned image; text not extractable.
- Ferber & Mass 1990; Whitney, Bond & Mass 1997 — PSCZ literature named by the NWS WFO Seattle attachment.
- Rasmussen et al. 2012 — How Well Are We Measuring Snow?, *BAMS* 93. AMS page 403 on direct fetch.
- Henn et al. 2018 — An assessment of differences in gridded precipitation datasets in complex terrain, *J. Hydrol.* (ScienceDirect paywall). Numbers quoted are those restated in Lundquist et al. 2019 plus a search-result summary.
- Garvert, Colle & Mass 2005 — IMPROVE-2 Oregon Cascades microphysics sensitivity (AMS 403).
- Picard & Mass 2017; Kirshbaum & Smith 2008; Colle 2008; Hobbs et al. 1975; Marwitz 1981; Bergeron 1969; Stewart et al. 1984; White et al. 2002; Kingsmill et al. 2016; Zagrodnik et al. 2018/2019/2021; McMurdie et al. 2018 — reached only as citations inside the fetched papers.
- Hamill et al. 2023 — Improving NBM Probabilistic Precipitation Forecasts, Parts I & II, *Mon. Wea. Rev.* 151 (AMS 403 on the Part I XML; Part II PDF not extracted).
- Ralph et al. 2013 — the 74 % storm-total figure, taken from `docs/research/flood-genesis-mechanisms-2026-08-24.md` and a search summary.
- Houze 2012 — Orographic effects on precipitating clouds, *Rev. Geophys.* 50 (already cited in the prior repo research file).
