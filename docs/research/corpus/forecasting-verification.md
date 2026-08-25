# Operational forecasting, ensembles, and verification science

*Corpus entry, 2026-08-24. Part of the Cascadia Papsukkal flood-science corpus.*

Domain lead scope: how NWRFC actually produces the river forecast the platform badges OFFICIAL;
how HEFS/ESP ensembles are constructed and what they do and do not represent; what the National
Water Model v3.1 is and where it fails; the metric theory the platform must use to judge its own
surfaces (CRPS, Brier, reliability, rank histogram, ROC, EDS/SEDI, relative economic value); the
base-rate problem for rare events; forecast evolution and crest convergence; multi-model
disagreement; and hindcast design under knowledge time.

Every claim below is labelled **FACT** (a page or dataset was fetched and read — URL given),
**INFERENCE** (reasoned from cited facts), **ASSUMPTION**, or **OPEN QUESTION**. Live data
fetched on 2026-08-24 is marked *(measured live 2026-08-24)*.

---

## 1. Headline

**The platform's central evaluation problem is not that its indices might be wrong — it is that
at its own six forecast points the events it exists to anticipate are too rare to measure, while
an authoritative ensemble it is not yet reading already exists.** Measured live from USGS daily
values, minor flooding occurs on 0.16 %–0.77 % of days at the six seed points, and at the two
regulated points — Green at Auburn (AUBW1) and White at R St (WRAW1) — the *moderate* and *major*
categories are all but absent from the digital record: 0 of 13,384 and 1 of 6,172 *daily means*
respectively. **Corrected on review:** daily means are the wrong instrument for an
instantaneously-defined threshold. On the USGS *annual instantaneous peak* record AUBW1 has
exceeded moderate (12,000 cfs) twice since 1990 — 12,400 cfs on 1996-02-08 and 12,200 cfs on
2006-11-07 — and three times since Howard Hanson closed in 1962. The right verdict at AUBW1
moderate is therefore `UNVERIFIABLE (n_events = 2)`, not `n_events = 0`; only AUBW1 *major* and
WRAW1 *major* are genuinely empty over the post-dam record. §3 and §5.1 carry the corrected counts.
Any conventional skill score computed on that sample is dominated by the base
rate and will read "excellent" for a forecast that says *no flood, forever*. Simultaneously, the
NWS **HEFS ensemble is live and machine-readable at all six seed LIDs** —
`https://api.water.noaa.gov/hefs/v1/` — 45 members indexed by historical year 1981–2025, 6-hourly
to 30 days, in CFS. The correct sequencing is therefore: **buy the official probability before
building one**, and design the evaluation harness around rarity (stratified, event-based,
non-degenerating scores, explicit "unverifiable" verdicts) rather than around aggregate skill.

---

## 2. Mechanisms (how the forecasts are actually made, and what that implies)

### 2.1 What NWRFC runs, and why the official forecast is not reproducible

**FACT.** The NWRFC forecast chain is a lumped conceptual model suite inside CHPS (the NWS
Community Hydrologic Prediction System, a Delft-FEWS derivative wrapping legacy NWSRFS Fortran):
**SNOW-17** (temperature-index snow accumulation/ablation, tracking heat deficit, liquid-water
ratio and areal snow cover) → **SAC-SMA** (Sacramento Soil Moisture Accounting: upper/lower zone
tension and free water buckets producing impervious runoff, surface runoff, interflow, supplemental
and primary baseflow) → **UNIT-HG** (a synthetic gamma unit hydrograph *per zone*, applied only
once excess water reaches the channel — unlike textbook UH formulations it does not carry the
soil-column travel path) → **Lag-K** hydrologic routing (lag = travel time, K = attenuation, both
allowed to vary with flow via lookup tables), plus **CHANLOSS** and **CONS_USE** where local
conditions require them. Source: Walters et al., *A comprehensive calibration framework for the
Northwest River Forecast Center* (EarthArXiv preprint, submitted to JAWRA), §2.

**FACT.** The 2018-onward NWRFC recalibration replaced manual calibration with an automated
framework whose specifics matter to anyone reasoning about the official forecast:
- Forcing is **AORC** (Analysis of Record for Calibration), 1979–present, hourly, on a 30-arcsecond
  (0.008333°) grid, zone-averaged.
- Zones are no longer elevation bands drawn by hand but **k-means clusters** over gridded basin
  characteristics (Nov–Mar mean precipitation-type fraction, annual precipitation, elevation,
  effective forest cover, saturated hydraulic conductivity, 30-day mean annual max SWE), resampled
  to 1 km. Clusters "often follow elevation contours but with additional nuances such as changes in
  forest cover, soil type, or basin aspect".
- The optimizer is **EDDS**, an evolving parallel Dynamically Dimensioned Search: check-in interval
  between parallel DDS chains tightens 1,000 → 500 → 100 → 10 iterations. A calibration runs in
  ~10 minutes on a laptop; a single basin can carry **up to ~90 parameters**.
- The operational objective function is **NSE(Q) + NSE(log Q)** evaluated on **daily means** while
  the model runs at a **6-hour** timestep — explicitly chosen to stop RMSE/NSE's squared term from
  over-weighting high flows at the cost of low flows.
- Achieved **KGE ranges 0.75–0.98** across calibrated zones; the paper reports KGE 0.75–0.96 as
  "representative of the entire suite of basins calibrated with this framework".

**FACT, and directly load-bearing for this platform.** One of the three published case-study basins
is **SAKW1 — Sauk River near Sauk, WA (USGS 12189500)** — the unregulated Skagit tributary named in
`docs/HYDROLOGY.md` §2 as "a major, often dominant, flood contributor at Concrete and Mount Vernon".
Its calibration KGE, POR run with forcing adjustment, is **0.856**, with four cross-validation folds
at 0.841–0.853; without forcing adjustment 0.837 (POR). By contrast the Oregon rain-dominated case
FSSO3 needed forcing adjustment badly (0.704 → 0.945) and the Montana snow basin WGCM8 was
insensitive (0.957 vs 0.956). **INFERENCE:** the Sauk sits in the middle — the calibration is good
but is the *worst* of the three published cases, and the AORC forcing there is close enough to
truth that climatological adjustment buys almost nothing, which is consistent with a
precipitation-rich maritime basin where the gridded analysis has real orographic skill.

**FACT.** The calibration framework applies **mid-month multiplicative adjustment factors** to
AORC precipitation, temperature, precipitation typing and PET, optimized as free parameters,
linearly interpolated between the 15th of adjacent months, and constrained to keep the resulting
monthly climatology inside limits set by external gridded datasets (CHIRPS, ERA5-Land, NCAR/Newman,
PRISM for precipitation; Daymet, ERA, NCAR, TopoWX for temperature; ERA, GLEAM, P-LSH, TerraClimate
for ET). The authors concede this "is not standard".
**INFERENCE:** the calibrated model is tuned to a *bias-corrected historical forcing*, not to the
real-time forcing it is driven with in operations. Any Cascade hindcast that drives a
reconstruction with real-time-style inputs is not exercising the model the calibration produced.

**FACT.** Two stated limitations of the NWRFC calibration framework: it **cannot represent tidally
influenced basins** (requires a nonlinear hydraulic model at the outlet), and it has **no reservoir
regulation** — "Regulation is a critical piece of operational hydrologic forecasting. In practice
this is done through specialized regulation models or real-time coordination with reservoir
operators." **INFERENCE:** for Skagit (Ross/Diablo/Gorge + Baker), Green (Howard Hanson), White
(Mud Mountain) and Cedar (Chester Morse), the published, *auto-calibrated* part of the NWRFC chain
stops above the dam.
**Corrected on review — do not read this as "no regulation model".** The same paper states that
NWRFC's model suite has a *third* supplemental model beyond CHANLOSS and CONS_USE: **SSARRESV**
(Streamflow Synthesis and Reservoir Regulation System), and that "NWRFC exclusively uses the
SSARRESV model" for reservoir regulation, citing National Weather Service (2004). The limitation is
therefore narrower and more precise than first written: *the auto-calibration framework* excludes
regulation, while the *operational* chain runs a named, documented regulation model whose parameters
and real-time operator coordination are the unpublished part. What leaves no public artifact is the
SSARRESV configuration and the operator coordination, not the existence of a regulation model.

**FACT.** Forecaster modifications ("MODs") are the NWS's data assimilation. NWRFC's own
documentation states that duty forecasters typically do **not** modify precipitation input but
instead change the rainfall-runoff input (`RRICHNG` MOD), SAC-SMA baseflow storage, or other bucket
storages; and that when this happens "the basic snow modeling is affected". NWRFC also states that
an objective seasonal volume tool would require QC "objective, standardized, and repeatable by
anyone who wishes to use the same model to reproduce the same volume forecast" — i.e. the current
process is not that. Source: NWRFC, *When NWSRFS, SEUS, and SNOW Intersect*.

**FACT.** Demargne et al. (2014, *BAMS*) state the same thing at the national level: "The data
assimilation (DA) process currently consists of manual modifications of model states and parameters
by the forecasters based on their expertise"; and "the RFCs have longstanding practices to apply in
a subjective way manual modifications of model states and parameters for single-valued forecasting
— modifications that are not currently included in HEFS."

> **The reproducibility consequence, stated plainly (INFERENCE, high confidence):** the official
> NWRFC river forecast is a *human-in-the-loop product*. It cannot be reproduced from published
> inputs, it cannot be hindcast by re-running the published models, and the difference between it
> and any model output — including HEFS, which shares its hydrologic core — contains an
> irreducible, unlogged human component. Cascadia Papsukkal must treat the official forecast as an
> **observation of an authority's judgement**, archived verbatim with issuance time, never as
> something derivable.

### 2.2 Ensemble generation: ESP → MEFP → HEFS

**FACT.** **ESP** (Ensemble Streamflow Prediction) takes the *current* model states from the
Operational Forecast System and drives them forward with **historical observed meteorological
sequences**, one member per historical year, treating the past as a sample of plausible futures.
NWRFC's ESP review documents a Dworshak example using 39 years (1950–1988) and states the error
sources as "climate variability, model/calibration error, and data errors", with the explicit
caveat for regulated points that "REGULATED FORECASTS ARE DERIVED FROM ANALYZING THE RECORD AND
COMPARING IT TO AVERAGES. THESE FORECASTS HAVE AN ADDITIONAL SOURCE OF ERROR BECAUSE THE RESERVOIR
AND TUNNEL OPERATORS MAY SUBSTANTIALLY DEVIATE FROM THE ESTIMATED REGULATION."

**FACT.** **HEFS** replaces the climatology-only front end with **MEFP** (Meteorological Ensemble
Forecast Processor), which conditions ensemble forcing on the single-valued forecast: a
meta-Gaussian model with a Normal Quantile Transform, explicit precipitation-intermittency
treatment via a mixed-type bivariate meta-Gaussian (Herr & Krzysztofowicz 2005), parameters
optimized under CRPS (Wu et al. 2011). Members are then reordered by the **Schaake shuffle**
(Clark et al. 2004) against the ranks of historical observations, which preserves rank correlation
across lead times, basins and variables. **The ensemble size is therefore fixed by the number of
observed historical years.** Downstream, **EnsPost** (Seo et al. 2006) adjusts the streamflow
ensemble for total hydrologic uncertainty in a lumped way.

**FACT (measured live 2026-08-24).** HEFS is running at every Cascadia Papsukkal seed forecast
point. Queried at `https://api.water.noaa.gov/hefs/v1/headers/?location_id={LID}`:

| property | measured value |
|---|---|
| LIDs served | MVEW1, CRNW1, RNTW1, NKSW1, AUBW1, WRAW1 (all six seed points), plus CONW1, SAKW1, SQUW1, SNAW1, GORW1 |
| `ensemble_id` | `MEFP` (single ensemble id; no separate EnsPost id exposed) |
| `parameter_id` | `QINE` only — **instantaneous flow, CFS**. No stage parameter is served. |
| members | **45**, `ensemble_member_index` = **1981 … 2025**, contiguous |
| timestep | 21,600 s = 6 h; 121 steps = **30 days** |
| cycles | **one per day at 12:00Z** (not 6-hourly) |
| issuance latency (`creation_datetime − forecast_datetime`), 8 cycles 2026-08-17…24 | 3 h 05 m – 5 h 19 m (median ≈ 3 h 30 m). **Re-measured on review over all 10 retained cycles (08-15…24): 3 h 07 m – 6 h 14 m** — the 08-16 cycle landed at 18:13Z. Do not size a staleness budget on the 8-cycle range. |
| archive depth in the API | **10 cycles ≈ 10 days**, then gone |
| quantile endpoint | `/hefs/v1/hydrograph-quantiles/` returns 11 exceedance quantiles (0.05, 0.1, 0.25, 0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.9, 0.95) plus min/max per step |
| service status | labelled **EXPERIMENTAL** in the OpenAPI title: "NWPS API - HEFS (EXPERIMENTAL)" |

The member index being a *historical year* is the historical-resampling construction visible in the
data — the platform can name *which year* a member is keyed to.
**Corrected on review — do not render this as "the meteorology of 1997".** That gloss is an
ASSUMPTION, not a fact, and it is probably wrong at short lead. MEFP conditions the forcing
ensemble on the *current single-valued forecast*; the historical year supplies the rank ordering
(Schaake shuffle) and the space–time covariance structure, not the weather itself. Member 1997 is
therefore "the trace that inherits 1997's rank position", which is not the same sentence as "what
1997's weather would do to today's basin". Until this is confirmed against NWRFC documentation, the
explanation layer may print the member index as an identifier — "12 of 45 members exceed …" — but
must **not** call the indices "analogues" or attribute a historical year's meteorology to a member.
This retires the "including the 1990, 1995 and 2006 analogues" phrasing proposed in §6.2 M2.

**FACT (measured live 2026-08-24, MVEW1, 12Z cycle).** Ensemble spread growth, expressed as the
ratio of member maximum to member minimum at a given lead:

| lead | 24 h | 48 h | 72 h | 120 h | 168 h | 240 h | 360 h | 714 h |
|---|---|---|---|---|---|---|---|---|
| max/min | 1.02 | 1.13 | 1.20 | 1.11 | 1.41 | 2.14 | 3.27 | 3.88 |

and at lead 0 **all 45 members are exactly equal** (6725.89 cfs at MVEW1; likewise at AUBW1 and
WRAW1). **INFERENCE:** as served, the HEFS ensemble carries **zero initial-condition uncertainty**.
Its spread at short lead is forcing spread only, and even that is near-nil in a dry August because
MEFP is conditioned on a single-valued QPF that forecasts nothing. Two consequences: (a) short-lead
HEFS will be **under-dispersed** wherever hydrologic uncertainty dominates; (b) *a low measured
spread in a dry month is not evidence of confidence* and must never be rendered as one. **CAVEAT:**
this is one cycle in one basin in one season; it is not a dispersion diagnosis.

**FACT.** Demargne et al. (2014) report, from the North Fork American River (NFDC1, 875 km², near
Sacramento) hindcasts at 6-h timestep 1979–2005 with **45 members**: the GFS-driven flow ensembles
show "a conditional bias consistent with the conditional bias of the precipitation ensembles:
overforecasting of small events and **underforecasting of large events**"; that "most of the flow
forecast skill comes from the MEFP component, with limited impact of EnsPost"; and that the sharp
CRPSS rise between forecast day 1 and day 2 is an artefact — at day 1 the *climatology reference*
is itself skilful through persistence, depressing the skill score of the real forecast.
**INFERENCE:** CRPSS against climatology systematically understates day-1 hydrologic skill. Any
Cascade skill report must state its reference and should report **persistence** as a second
reference at short lead.

**FACT.** CNRFC's public ensemble documentation states that its long-range ensemble traces are
"full-natural flow (no regulation effects are included in the forecasts)", that watersheds are
calibrated with 30–40 years so HEFS produces a similar member count (climatology 1980–2023 as of
October 2024), and that "beyond 14 days the streamflow traces are 100 % driven by climatological
meteorology". **Transferability caveat:** this is CNRFC, not NWRFC. **Measured live 2026-08-24 at
NWRFC points**, the HEFS `t=0` median matches the *regulated observed* flow closely — AUBW1
293 cfs vs 302 cfs observed; WRAW1 623 vs 577; MVEW1 6,726 vs 6,780 — so the WA short-range traces
are at least *initialised* on regulated reality. Whether regulation is propagated forward at
AUBW1/WRAW1 is an **OPEN QUESTION** that a winter drawdown would settle.

**FACT.** The NWS "short-term probabilistic guidance product" (`water.noaa.gov`) is HEFS-derived,
0–10 days, "updated typically every 6 hours", and exists as a PNG per LID at
`https://water.noaa.gov/resources/probabilistic/short_term/{LID}.shortrange.hefs.png`. Measured
2026-08-24: present (HTTP 200) for MVEW1, CRNW1, RNTW1, NKSW1, AUBW1, SAKW1, CONW1, SQUW1, SNAW1,
GORW1; **absent (404) for WRAW1** and for BAKW1. **INFERENCE:** the image product and the API do not
have identical coverage — the API served WRAW1 headers when the image did not exist — so coverage
must be probed per endpoint, not assumed.

### 2.3 The National Water Model: what v3.1 is, and what changed twelve days ago

**FACT.** NWM v3.0 configurations (water.noaa.gov/about/nwm, and SCN 26-64):
- **Analysis and Assimilation** — hourly, 3-hour look-back, MRMS + RAP/HRRR forcing; assimilates
  USGS and USACE streamflow observations (~7,000 gauges); provides initial states for every
  forecast configuration. A parallel **no-DA** ("open loop") run is published.
- **Short-Range** — hourly cycles, 18-hour horizon, HRRR/RAP forcing, deterministic.
- **Medium-Range** — four cycles/day (00/06/12/18Z), GFS forcing, **6 members**
  (`channel_rt_{1..6}`), member 1 to 10 days and members 2–6 to 8.5 days, 3-hourly output.
- **Long-Range** — four cycles/day, **4 members** (`channel_rt_{1..4}`), CFS forcing, 30 days.
- Over **3.2 million** river reaches; **over 5,000** reservoirs; CONUS forecasts ingest
  "RFC-supplied forecasts of reservoir outflow at several hundred locations".

**FACT, and this one is urgent.** NWS **Service Change Notice 26-64 (Updated), issued 2026-07-30**,
made **NWM v3.1 operational on or about 2026-08-18 beginning with the 1200 UTC run** — six days
before this corpus entry. Among the "All Domains" changes:

> "Assimilation of USGS streamflow observations available at the forecast execution time into the
> corresponding beginning hours of the NWM short-, medium-, and long-range forecasts. **The initial
> forecast period overlapping with available observations will thus track observed values.**"

Other v3.1 CONUS changes: dynamic NWP-based lapse rate for temperature downscaling; MRMS/NWP
precipitation-type specification in AnA, Short-Range and GFS Medium-Range; hydrofabric location
refinements for **311 USGS stream gauges**; a new `LQFRAC` forcing variable; Old River Control
Structure diversion via observed-flow persistence. The NDFD-forced Medium-Range configuration and
the NBM-forced time-lagged 6-member MR ensemble that were floated for comment in PNS 25-77
(2025-12-10) **did not appear in the final SCN** — the operational MR ensemble remains the
GFS-forced 6-member set.

> **INFERENCE, P0 for this repo:** `packages/hydrology/agreement.py` compares the official forecast
> and the NWM medium-range members over a shared window `(as_of − 6 h, as_of + 72 h]`. Under v3.1
> the earliest hours of the NWM member hydrographs **are the USGS observations**. Inside that
> region "agreement" is not agreement between two forecasts; it is agreement between a forecast and
> a gauge, and it will read artificially high. The comparison window must start after the
> assimilation tail, and the length of that tail must be measured, not assumed.

**FACT.** Independent evaluation of NWM v3.0 versus v2.1 during storm events reports a **38.1 %
RMSE improvement**, an **87.5 % KGE improvement** and a **172.7 % NSE improvement** for v3.0 over
v2.1, alongside a median **PBIAS of −13.03 %** (systematic underestimation) and cases of negative
NSE and KGE "highlighting difficulties in capturing extreme events". Source: *A comparative analysis
of national water model versions 2.1 and 3.0…*, Journal of Hydrology: Regional Studies (2025).
**Not independently fetched** (ScienceDirect returned HTTP 403); figures are from the indexed
abstract text. Percentage improvements in KGE/NSE are relative changes in an already-poor baseline
and should not be read as "87.5 % better forecasts".
**Transferability, added on review — this is a Texas study.** The sample is **610 USGS gauges across
Texas** and the events are Gulf tropical cyclones (Harvey, Hanna, Imelda). The −13.03 % median is a
whole-period Texas number, and the sign is event-dependent: for Hurricane Harvey v3.0 *over*-predicts
at PBIAS **+56.54 %** (worse than v2.1's +38.91 %). A Gulf-Coast tropical-cyclone result is a weak
analogue for maritime AR-driven western Washington and must not be quoted as a global NWM bias.
The closest published western analogue found on review is **"Improving National Water Model Flood
Forecast Skill over Coastal Western U.S. River Basins", J. Hydrometeorology 26(8), 2025** — WRF-Hydro
against RFC methods over seven Pacific Coast watersheds. That paper, not the Texas one, is the
transferable reference for this platform and has not yet been read.

**FACT.** USGS evaluation of NWM v3.0 retrospective streamflow by baseflow-index regime finds skill
"varied systematically across regimes: mixed flow systems were simulated most accurately, while
predominantly baseflow dominated and quickflow dominated regimes exhibited substantially poorer
performance", with the NWM "underestimat[ing] observed baseflow index magnitude and frequently
fail[ing] to reproduce seasonal baseflow patterns". Source: USGS Publications Warehouse
70279220. **Not independently fetched** (pubs.usgs.gov returned HTTP 403).

**FACT, with a version correction.** Evaluation of NWM short-range forecasts across 306 USGS gauges
in 16 study areas over 2021–2023 flood events reports **systematic underestimation of peak discharge
and flood volume across all basin types**, **forecast peaks occurring earlier than observed**, and
larger errors for "urban, regulated, arid, small basins and high-magnitude floods". Source: *How
well do U.S. National Water Model short-range forecasts predict flood event timing and magnitude?*,
Journal of Hydrology: Regional Studies (2026). **Not independently fetched** (403).
**Corrected on review: this study evaluates NWM v2.1, not v3.0** — two operational versions behind
what runs today. The indexed abstract also states that median peak bias stayed *close to zero*
across lead times even as error magnitude and gauge-to-gauge spread grew with lead. Cite it as a
v2.1 result and do not carry it forward as a property of v3.0/v3.1 without re-evaluation.

**INFERENCE.** Every documented NWM weakness stacks against western Washington simultaneously:
regulated (four of eight platform basins), snow-influenced, high-magnitude, and — at Mount
Vernon — tidally influenced. NWM is a legitimate *independent* opinion for the agreement surface.
It is not a second official forecast and must never be presented as one.

### 2.4 The metrics, stated properly

Let *p₁…pₙ* be forecast probabilities of a binary event with outcomes *x₁…xₙ ∈ {0,1}*.

**Brier score** (Brier 1950): `B = (1/n) Σ (pᵢ − xᵢ)²`, in [0,1], lower better. With *K* distinct
forecast values π₁…π_K, occasion sets I_k of size n_k, conditional frequencies `x̄_k`, and overall
frequency `x̄`, the **Murphy (1973) decomposition** is

```
B = REL − RES + UNC
REL = Σ_k (n_k/n)(π_k − x̄_k)²          reliability / calibration   (0 is best)
RES = Σ_k (n_k/n)(x̄_k − x̄)²            resolution                  (large is best)
UNC = x̄(1 − x̄)                          intrinsic uncertainty       (base-rate term)
```

**FACT.** Ferro & Fricker (2012, *QJRMS*, preprint fetched) prove the standard decomposition is
**biased at finite n**: reliability is systematically **over**estimated, uncertainty systematically
**under**estimated, resolution either way. With ν_{k,n} = P(n_k > 0),

```
E(REL) = REL∞ + (1/n) Σ_k ν_{k,n} μ_k(1−μ_k)
E(RES) = RES∞ + (1/n) Σ_k ν_{k,n} μ_k(1−μ_k) − μ(1−μ)/n
E(UNC) = UNC∞ − μ(1−μ)/n
```

An unbiased decomposition is shown to be **unattainable**; they propose a lower-bias alternative.
**INFERENCE, and this is the killer for this platform:** the bias term scales as **K/n**. UNC at
MVEW1's minor threshold is ≈ 0.00357 × 0.99643 ≈ 0.00356. With, say, K = 10 probability bins and
n = 500 verification pairs, the reliability inflation term is of order 10 × 0.00356 / 500 ≈ 7 × 10⁻⁵
— i.e. **2 % of the entire uncertainty term** just from finite-sample bias, before any real
miscalibration. At n = 100 it is 10 %. A reliability diagram drawn from a few winters of western
Washington data is measuring its own sampling noise.

**CRPS** (Hersbach 2000): for predictive CDF *F* and observation *y*,
`CRPS(F, y) = ∫ (F(x) − 𝟙{x ≥ y})² dx`. It is the Brier score integrated over all thresholds, is a
**proper** score, and **collapses to mean absolute error for a deterministic forecast** — which is
what makes it the one score that can compare an ensemble to the single-valued official forecast on
the same axis. Hersbach's decomposition splits CRPS into a reliability part (tied directly to the
rank histogram) and a resolution/uncertainty part (tied to mean ensemble spread and outlier
behaviour). **The Hersbach (2000) paper itself was not independently fetched** (AMS 403); the
definition and decomposition structure are from the indexed abstract and standard usage.

**CRPSS** `= 1 − CRPS_forecast / CRPS_reference`. **FACT** (Demargne et al. 2014, fetched): the
reference choice changes the answer qualitatively, and against climatology the day-1 score is
depressed because climatology inherits persistence skill.

**Rank histogram / PIT.** For an *m*-member ensemble, the rank of the observation among the sorted
members should be uniform over 1…m+1 if the ensemble is calibrated. U-shape → under-dispersion;
dome → over-dispersion; slope → bias.
**CONTESTED, and recent.** Dirkson & Buehner, *Are we misdiagnosing ensemble forecast reliability?
On the insufficiency of Spread-Error and rank-based reliability metrics* (arXiv:2512.02160,
2025-12-03, fetched) argue that spread-error and rank-histogram diagnostics **can pass while the
ensemble is demonstrably miscalibrated**: they test dispersion relative to error rather than whether
the ensemble samples the true predictive distribution, and can hide directional bias. They advocate
direct assessment of whether forecast probabilities match observed frequencies. **INFERENCE:** a
platform that will publish a reliability claim must not rest it on a rank histogram alone.

**ROC / discrimination.** Hit rate `H = a/(a+c)`, false-alarm rate `F = b/(b+d)` swept over
probability thresholds. ROC measures **discrimination** — can the system tell event days from
non-event days — and is **independent of calibration**, which is exactly why a system can have an
impressive ROC and useless probabilities.

**Rare-event degeneracy.** As base rate *p* → 0, threat score, equitable threat score and hit rate
**degenerate to trivial limits** — the classic statement of why "95 % accurate" is meaningless for
floods. Non-degenerating alternatives (definitions from standard verification references; **Ferro
& Stephenson (2011, WAF) not independently fetched — AMS 403**; the properties below are from the
indexed abstract, which states the new measures are "nondegenerating, base-rate independent,
asymptotically equitable, harder to hedge"):

```
EDS  = 2 ln((a+c)/n) / ln(a/n) − 1                                (Stephenson et al.; hedgeable, base-rate dependent)
SEDS = [ln((a+b)/n) + ln((a+c)/n)] / ln(a/n) − 1                  (Hogan et al. 2009)
EDI  = (ln F − ln H) / (ln F + ln H)
SEDI = [ln F − ln H − ln(1−F) + ln(1−H)] / [ln F + ln H + ln(1−F) + ln(1−H)]
```

Ferro & Stephenson (2011) recommend **SEDI** as the deterministic rare-event measure of choice.

**Relative economic value (REV).** The cost–loss decision model (Richardson 2000; Wilks 2001), as
documented by the WMO/CAWCR verification reference (fetched): a user pays cost *C* to protect and
loses *L* if the event occurs unprotected.

```
E_climate  = min(C, s̄·L)                     where s̄ = base rate
E_perfect  = s̄·C
E_forecast = (h + f)·C + m·L                  h, f, m = relative frequencies of hits, false alarms, misses
V = (E_climate − E_forecast) / (E_climate − E_perfect)
```

**FACT** (same source): the maximum of V occurs where the cost/loss ratio **α = C/L equals the
climatological probability s̄**, and at that point **V equals the Hanssen–Kuipers (Peirce) skill
score**. For probabilistic forecasts, sweeping the decision threshold traces a family of V(α)
curves whose **envelope is the potential value**; realised value is lower.
**INFERENCE, decisive for this platform:** because V peaks at α = s̄ and s̄ is 0.0016–0.008 at the
seed points, the only users for whom a Cascadia Papsukkal flood signal has value are those whose
**cost of acting is under ~1 % of their loss** — i.e. cheap precautionary actions (checking a pump,
moving equipment, staffing a gauge), not expensive irreversible ones. That is an argument for
building the product around *lead time on cheap actions*, and against ever implying it supports
expensive decisions.

### 2.5 Skill is not value: Murphy's three goodnesses

**FACT.** Murphy (1993, *Weather and Forecasting* **8**, 281–293) distinguishes three kinds of
forecast "goodness": **type 1, consistency** (the forecast matches the forecaster's actual
judgement); **type 2, quality** (the forecast matches the observations — this is *verification*);
**type 3, value** (the incremental benefit a decision-maker realises). He shows by example that
inconsistency degrades both quality and value.
**INFERENCE:** Cascadia Papsukkal's badge system is a **type-1** device. `EXPERIMENTAL`,
`UNKNOWN`-with-reason, and the refusal to print an uncalibrated percentage are all assertions that
the displayed number is what the system actually believes. That is not decoration; it is the
precondition Murphy identifies for the other two goodnesses to be attainable at all.

### 2.6 Forecast evolution: convergence, jumpiness, and why the platform must store it

**FACT.** Verification literature treats the convergence of successive forecasts toward the observed
hydrograph as the *expected* behaviour of a well-performing system, and treats departures from it as
a distinct failure mode with its own names: **inconsistency**, **jumpiness**, **flip-flop**,
**turning points**. Zsoter et al. (2009) defined an inconsistency index as the difference between
successive same-valid-time ensemble-mean fields divided by their average standard deviation, and
studied sign-alternating sequences (flip-flops); ensemble means are more consistent than control
runs. Later work formalises a **Flip-Flop Index** for fixed-event forecasts and a taxonomy of jump
patterns (flip, flip-flop, flip-flop-flip). Empirically, **forecast jumpiness and forecast error are
only weakly correlated** — i.e. a jumpy forecast is not necessarily a wrong one, and a stable one is
not necessarily right.
**INFERENCE:** consistency is a *separate axis* from accuracy and must be verified separately. A
Cascade "forecast evolution" panel that only shows the trace is showing data; a panel that also
quantifies the revision magnitude relative to spread is showing information.

**FACT** (from `docs/HYDROLOGY.md` §12 and the repo's Event Zero dataset). Mount Vernon, December
2025: the official forecast crest evolved **36.9 → 41.5 → 42.3 → 39.1 → 38.26 ft** before the
observed **37.73 ft** crest at 2025-12-12 08:15Z. The first NWS Seattle Flood Watch was issued
2025-12-05 16:10 PST, ~6.5 days before the crest.
**INFERENCE:** the peak forecast (42.3 ft) over-predicted the outcome by **4.57 ft**, and the
sequence is a textbook flip-flop: up 4.6, up 0.8, **down 3.2**, down 0.8. Anyone acting on the
42.3 ft trace would have prepared for major-plus flooding; the observed crest was 5.73 ft above
minor and 5.73 ft above the 32 ft major threshold — major, but not the near-record the mid-sequence
forecast implied. This single event is the platform's best available consistency benchmark and
should be the first thing the harness reproduces.

**FACT** (Welles, Cajina & Herr, NWS OHD, *Verification of National Weather Service River Stage
Forecasts*, fetched). Four structural problems in river forecast verification that the NWS itself
names:
1. **Aggregation across points is ill-posed** — samples from different forecast points come from
   different distributions; the Normal Quantile Transform was tried and is limited by insufficient
   climatological data; converting stage to flow via rating curves is defeated by rating revisions;
   and error measures do not transform back cleanly.
2. **Aggregate statistics hide the tail** — a point with aggregate RMSE 0.8 ft, ME −0.1 ft was shown,
   when split into 7 observed-magnitude bands (n from ~500 at low flow to ~30 at high flow), to
   **under-forecast the largest events**, with POD falling and FAR rising as observed stage rises,
   and average lead time of detection "very low at the highest category".
3. **The "no forecast" problem** — many points are *flood-only*: no forecast is issued unless
   flooding is anticipated, so a flood that was not anticipated produces **no forecast–observation
   pair at all** and silently vanishes from the verification sample.
4. **Timing errors masquerade as magnitude errors** — a correct peak shifted a few hours produces a
   large stage error on a steep rising limb; Morris (1988) proposes **threshold-crossing times** as
   the timing measure. They also note models "perform markedly differently in the rising and falling
   limbs" and that the two must be verified separately.

**FACT.** Independent analysis of NWS stage forecasts for 51 gauges in eastern/central Iowa,
1999–2014 (Regonda-lineage study, *Weather and Forecasting* 2017) evaluated lead times of 6, 12, 24,
48, 72, 96 and 120 h and found the RMSE difference between actual and persistence forecasts ranges
**0.04 to 1.24 ft**, increasing with lead time, with skill dependence on upstream area, water travel
time and number of upstream gauges. **Not independently fetched** (AMS 403; NOAA repository mirror
returned Access Denied); figures are from the indexed abstract. **Transferability: poor** — Iowa is
a different hydroclimate. The *method* transfers; the numbers do not.

### 2.7 Hindcast design: knowledge time, look-ahead, and the traps

**FACT.** A hindcast (reforecast) is a retrospective forecast generated with a **fixed** forecasting
system, required because probabilistic verification needs a large sample of events and real-time
archives are too short (Demargne et al. 2014).

**FACT.** Demargne et al. (2014) name the trap that `docs/DATA_DOCTRINE.md` §11 exists to prevent:
"the estimation of historical past forcings for model calibration and hindcasting may not be
consistent with real-time meteorological model inputs, owing to changes in tools (e.g. gauges versus
radar for precipitation estimation) and models, as well as estimation errors."
**INFERENCE:** this is a *forcing-generation* look-ahead, distinct from the timestamp look-ahead the
repo already guards. `as_known_at(T)` correctly excludes rows published after T. It does **not**
detect that a product's *definition* improved — AORC v1.1 replacing v1.0, MRMS re-gridding, a USGS
rating revision applied retroactively. Those arrive as new rows with honest `available_at` and are
still not what existed at T. The defence is **product version pinning**, not timestamp filtering.

**FACT.** Seasonal-forecast hindcast verification practice distinguishes verification against real
observations from verification against **pseudo-observations** (a reference simulation, also called
"synthetic truth" or "reanalysis"). Source: *Seasonal streamflow forecasts for Europe – Part I:
Hindcast verification with pseudo- and real observations*, HESS 22, 3453 (2018).
**INFERENCE:** for regulated western Washington reaches where "what would have happened naturally"
is unobservable, pseudo-observation verification is the only way to separate *model error* from
*operator decision*. It must be badged as such and never conflated with verification against gauges.

**Look-ahead sources this platform is specifically exposed to (INFERENCE):**

| trap | mechanism | detected by `as_known_at(T)`? |
|---|---|---|
| forecast supersession | using a newer run's values at T | **yes** |
| provisional→approved USGS revision | using the approved value at T | **yes**, via revision rows |
| product version improvement | AORC/MRMS/SNODAS reprocessing | **no** — needs version pinning |
| threshold revision | NWPS changes a flood category, hindcast uses today's | **no** — needs versioned threshold rows (repo already versions these) |
| rating-curve shift | stage↔flow relation revised after the event | **no** — and ADR-0011 already forbids the conversion |
| **NWM/HEFS model version change** | NWM v3.0→v3.1 on 2026-08-18 | **no** — a hindcast run through the boundary silently mixes two models |
| **survivorship in the archive** | HEFS API keeps only ~10 cycles; NWPS keeps ~5 forecasts | **no** — absent rows are invisible, not `quality=missing` |

---

## 3. Quantitative anchors

| quantity | value | context | source |
|---|---|---|---|
| NWRFC calibration KGE range | **0.75 – 0.98** per zone; 0.75–0.96 "representative" | new NWRFC auto-calibration framework, AORC forcing | Walters et al. (EarthArXiv preprint) |
| **Sauk R nr Sauk (SAKW1) calibration KGE** | **0.856** (POR, forcing-adjusted); CV folds 0.841–0.853; 0.837 unadjusted | the unregulated Skagit tributary that drives Concrete/Mount Vernon | ibid., Table 4 |
| NWRFC max parameters per basin | up to **~90** | multi-zone basins with routing, channel loss, consumptive use | ibid. |
| NWRFC calibration objective | **NSE(Q) + NSE(log Q)** on daily means, 6-h model timestep | deliberately balanced high/low flow | ibid. §7 |
| AORC resolution | 30 arcsec (0.008333°), hourly, 1979–present | the forcing the calibration is tuned to | ibid. §3.1 |
| HEFS members at WA seed points | **45**, indexed **1981–2025** | Schaake-shuffle member count = number of historical years | *measured live 2026-08-24*, `api.water.noaa.gov/hefs/v1/ensembles/` |
| HEFS cadence / horizon / step | **1 cycle/day at 12Z**, 30 days, 6 h, CFS, `QINE` only | no stage parameter served | *measured live 2026-08-24* |
| HEFS issuance latency | **3 h 07 m – 6 h 14 m** after nominal 12Z over all 10 retained cycles (the 8-cycle 08-17…24 subset gives the narrower 3 h 05 m – 5 h 19 m) | this is `available_at − issued_at` for the platform; budget against the wider range | *measured live 2026-08-24, re-measured on review* |
| HEFS API archive depth | **10 cycles ≈ 10 days** | the platform must archive or lose the evolution record | *measured live 2026-08-24* |
| HEFS spread, MVEW1, Aug cycle | max/min = 1.02 (24 h), 1.20 (72 h), 1.41 (7 d), 2.14 (10 d), 3.27 (15 d) | dry-season sample; **zero spread at lead 0** | *measured live 2026-08-24* |
| NWM MR ensemble size | **6 members** (1→240 h, 2–6→204 h); LR **4 members**, 30 d | v3.0 and v3.1 alike | SCN 26-64; water.noaa.gov/about/nwm |
| **NWM v3.1 operational date** | **2026-08-18, 12Z** | six days before this entry | SCN 26-64 (Updated), 2026-07-30 |
| NWM reaches / reservoirs | **3.2 M** reaches; **>5,000** reservoirs; RFC outflow forecasts at "several hundred" | v3.1 | SCN 26-64 |
| NWM v3.1 hydrofabric fix | **311** USGS gauge locations refined | changes which reach a gauge maps to | SCN 26-64 |
| NWM v3.0 median PBIAS | **−13.03 %** (underestimates) | storm-event comparison v2.1 vs v3.0 | J. Hydrol. Reg. Stud. (2025) — *not independently fetched* |
| NWM v3.0 vs v2.1 | RMSE −38.1 %, KGE +87.5 %, NSE +172.7 % | relative gains on a weak baseline | ibid. — *not independently fetched* |
| NWM short-range peak bias | systematic **underestimation** of peak Q and volume; peaks **early**; worse for regulated/urban/small/high-magnitude | 306 gauges, 16 areas, 2021–2023 | J. Hydrol. Reg. Stud. (2026) — *not independently fetched* |
| NWS stage forecast vs persistence | RMSE advantage **0.04 – 1.24 ft**, growing with lead 6→120 h | 51 Iowa gauges 1999–2014; **not transferable in magnitude** | *Weather and Forecasting* (2017) — *not independently fetched* |
| **MVEW1 base rate, action (23.5 ft)** | **1.82 %** of days (228/12,560) | USGS daily mean gage height 1990-01-01…2026-08-23 | *computed live 2026-08-24* from USGS DV 12200500 |
| **MVEW1 base rate, minor (28 ft)** | **0.358 %** of days (45/12,560) — 1 day in 279 | ibid. | ibid. |
| **MVEW1 base rate, moderate (30 ft)** | **0.167 %** (21/12,560) — 1 in 598 | ibid. | ibid. |
| **MVEW1 base rate, major (32 ft)** | **0.0796 %** (10/12,560) — 1 in 1,256 | ibid. | ibid. |
| CRNW1 (Snoqualmie, Carnation) | action 2.81 %, minor 0.773 %, moderate 0.365 %, major 0.126 % | daily stage 1990–2009 (series ends 2009) | *computed live* USGS DV 12149000 |
| **AUBW1 (Green, regulated)** | action 1.756 %, minor 0.486 %, **moderate 0.000 % (0/13,384)**, **major 0.000 %** | daily mean flow 1990-01-01…2026-08-23; **daily means only — see correction below** | *computed live* USGS DV 12113000 |
| **AUBW1 instantaneous peaks** | moderate exceeded **2 of 34 years** (1996-02-08 12,400 cfs; 2006-11-07 12,200 cfs); **major 0 of 62 years post-dam** | the count an evaluation report must print at AUBW1 | *computed on review 2026-08-24*, USGS peak file 12113000 |
| **WRAW1 (White, regulated)** | action 1.636 %, minor 0.178 %, **moderate 0.016 % (1/6,172)**, **major 0.000 %** | daily mean flow 2009-09-30…2026-08-23; the single moderate day is **2025-12-14, Event Zero itself** | *computed live* USGS DV 12100490 |
| RNTW1 (Cedar, Renton) | action 7.449 %, minor 0.292 %, moderate 0.122 %, major 0.016 % | daily stage 1991–2026 | *computed live* USGS DV 12119000 |
| NKSW1 (Nooksack, Ferndale) | action 0.711 %, minor 0.158 %, moderate 0.032 %, **major 0.008 % (1/12,659)** | daily stage 1991–2026 | *computed live* USGS DV 12213100 |
| MVEW1 annual-peak exceedance | action 86 % of years, minor 47 %, moderate 27 %, major 16.5 % (n = 85 peaks, 1906–2024) | annual peak series; **datum caveat** (early years old datum) | *computed live* USGS peak file 12200500 |
| Event Zero crest forecast evolution | 36.9 → 41.5 → **42.3** → 39.1 → 38.26 ft vs observed **37.73 ft** | Skagit at Mount Vernon, Dec 2025; peak over-forecast **+4.57 ft** | `docs/HYDROLOGY.md` §12 |
| Brier decomposition finite-n bias | REL inflated by ≈ (Σ_k ν_{k,n} μ_k(1−μ_k))/n; UNC deflated by μ(1−μ)/n | at MVEW1 minor, UNC ≈ 0.00356 → bias is ~2 % of UNC at n = 500, K = 10 | Ferro & Fricker (2012), fetched preprint |
| REV maximum | V_max attained at **α = C/L = s̄**, and equals the Peirce skill score | s̄ = 0.0016–0.0077 at seed points → only very-low-cost actions have value | CAWCR/WMO verification reference, fetched |

**Reading the base rates.** These are **daily means**, which under-count instantaneous exceedance
(a 6-hour crest above threshold may not lift the daily mean above it). They are therefore
**lower bounds**. They also mix gauge-datum eras at some sites. Both caveats push the same way:
the true event frequency is somewhat higher than tabulated but remains, at every site, under 1 % of
days for minor flooding.

**Corrected on review — "somewhat higher" understates the gap at the tail, and the method is wrong
in kind.** NWS flood categories are defined on **instantaneous** stage/flow; computing exceedance
from daily means silently redefines the event, which the platform's "official thresholds, in the
unit NWS defines them" rule does not permit. Measured: at MVEW1 the December 2025 crest was
**37.73 ft instantaneous vs a 35.06 ft daily mean** — a 2.67 ft shortfall on the one day that
matters most. At the regulated points the effect flips a category from "never" to "twice": AUBW1
moderate is **0 daily means but 2 instantaneous peaks since 1990**. Base rates must be recomputed
from USGS instantaneous values (or, before the IV record begins, the annual peak series) before any
of these numbers enters a verification report. The daily-mean figures above are retained because
they are what was measured, and are labelled as lower bounds — not as event counts.

---

## 4. What is settled, what is emerging, what is contested

**Settled (established).**
- Proper scores (Brier, CRPS) are the correct basis for probabilistic verification; improper scores
  can be hedged.
- The Murphy decomposition of the Brier score into reliability, resolution and uncertainty, and the
  Hersbach analogue for CRPS, are the standard diagnostic split.
- Traditional categorical scores (TS, ETS, POD) **degenerate** as the base rate → 0; this is a
  proved property, not a modelling opinion.
- Calibration (reliability) and discrimination (ROC) are **separate** attributes; neither implies
  the other.
- Skill and value are distinct (Murphy 1993); value depends on the user's cost–loss ratio and peaks
  at α = base rate.
- Forecaster modifications are the NWS's operational data assimilation and are **not** in HEFS
  (Demargne et al. 2014; NWRFC documentation).
- NWM systematically underestimates peaks and performs worst in regulated and extreme conditions.
- Hindcasting with a fixed system is required for probabilistic verification with acceptable
  sampling uncertainty.

**Emerging.**
- The NWRFC objective auto-calibration framework (Walters et al.) — a genuine step change in
  reproducibility of the *model*, published with code, but still explicitly ending in a "human in
  the loop" review step and still with no reservoir regulation.
- HEFS as a **public API** rather than an image product. The endpoint is live, labelled
  EXPERIMENTAL, retains ~10 days, and is not yet documented with per-endpoint coverage.
- NWM v3.1's assimilation of observations into the leading forecast hours. Operational for six days
  as of this writing; its effect on apparent short-lead skill has, as far as this sweep found, no
  published evaluation.
- Machine-learning benchmarks (LSTM, differentiable physics-informed models) beating NWM v3.0 on
  large gauge samples; the NWRFC paper explicitly offers its calibrations as the benchmark such
  models should be measured against.

**Contested.**
- **Whether rank histograms and spread–error diagnostics establish reliability at all.** Dirkson &
  Buehner (arXiv:2512.02160, Dec 2025) argue they are insufficient and can pass a miscalibrated
  ensemble. This is very recent and against decades of standard practice; treat as live dispute.
- **Whether KGE/NSE should be used for model accuracy assessment at all.** A 2025
  *Environmental Modelling & Software* paper titled "Friends don't let friends use Nash-Sutcliffe
  Efficiency (NSE) or KGE for hydrologic model accuracy evaluation: A rant with data and suggestions
  for better practice" argues the opposite of near-universal practice (*not independently fetched*).
  The NWRFC framework reports KGE; the USGS NWM evaluation reports KGE and NSE. **OPEN QUESTION** for
  the platform's own reporting.
- **Whether EDS-family scores are the right rare-event answer.** EDS is criticised as hedgeable and
  base-rate dependent; EDI/SEDI were introduced to fix it; the debate over the right rare-event
  measure is not closed.
- **Whether ensemble means should ever be shown.** Averaging members produces a hydrograph no member
  forecast; ensemble means are demonstrably *more consistent* than control runs (Zsoter et al.), so
  there is a real argument on both sides. The repo has already taken a side (lower-median member,
  never the mean) — that side is defensible but not uncontested.

---

## 5. Western Washington specificity

**What transfers.**
- The metric theory (Brier, CRPS, reliability, ROC, REV, rare-event degeneracy, decomposition bias)
  is mathematics and transfers without qualification.
- The structural verification problems named by NWS OHD — aggregation across points, the no-forecast
  problem, timing-vs-magnitude confusion, rising/falling limb asymmetry — are properties of *river*
  forecasting and transfer fully.
- HEFS/MEFP/EnsPost architecture and the "MODs are not in HEFS" fact are national.
- NWM configuration facts and the v3.1 assimilation change are national.

**What transfers with qualification.**
- **The North Fork American River (NFDC1) HEFS verification results.** NFDC1 is 875 km², Sierra
  Nevada, AR-driven, winter-dominated — genuinely the closest published analogue to a Cascade
  headwater. The *shape* of the conditional-bias finding (over-forecast small events,
  **under-forecast large events**) should be expected in western Washington; the *magnitudes*
  should not be assumed.
  **Corrected on review — the MEFP-vs-EnsPost split does not transfer at all.** Demargne et al.
  attribute EnsPost's small contribution at NFDC1 to that basin specifically: "the model simulation
  is of very high quality with a volume bias of only about 1 %" and "the additional improvement by
  EnsPost is marginal because of small hydrologic biases and uncertainties in this basin." They then
  state outright that, per Brown (2013), the relative contributions of MEFP and EnsPost "depend on
  the basin location". A regulated or poorly-simulated western Washington basin is exactly where
  EnsPost would be expected to matter more, not less. Carry the conditional bias forward; do not
  carry "most skill from MEFP" forward.
- **CNRFC's "no regulation in the long-range traces".** CNRFC and NWRFC are different offices with
  different practices. Measured live, the WA short-range HEFS traces are initialised on regulated
  observed flow. Whether NWRFC propagates regulation forward in HEFS is unresolved.
- **Iowa stage-forecast RMSE-vs-persistence numbers.** Method transfers; magnitudes do not — Iowa
  basins are flatter, slower, and not snow-influenced.

**What does not transfer, and what is specific here.**
1. **Regulation destroys the upper half of the verification sample.** At AUBW1, moderate flood flow
   (12,000 cfs) has occurred on **0 of 13,384** daily means since 1990 and major (14,000 cfs) on 0.
   At WRAW1, moderate on **1 of 6,172**. **Corrected on review — the instantaneous record is not
   empty.** NWS categories are defined on instantaneous flow, so daily means are the wrong
   instrument. On the USGS annual instantaneous peak series, AUBW1 exceeded **moderate** in
   **1996 (12,400 cfs)** and **2006 (12,200 cfs)** — two events since 1990, three since Howard
   Hanson closed in 1962 — and WRAW1's single moderate day (2025-12-14, daily mean 10,100 cfs) is
   **Event Zero itself**, which the platform also uses as its replay target: the verification
   sample and the calibration event are the same event, which is its own circularity hazard.
   Genuinely empty over the post-dam record are **AUBW1 major (0)** and **WRAW1 major (0)**.
   So the honest statement is not "there is no sample" but "the sample is 0–3 events" — which
   still cannot support a skill number, but changes what the report must print. Any evaluation
   report must return **UNVERIFIABLE with the instantaneous event count**, never a skill number,
   and must not derive that count from daily means.
2. **The official categories are stage at four of six seed points and flow at two** — MVEW1 32/30/
   28/23.5 ft, CRNW1 58/56/54/50.7 ft, RNTW1 16/14.5/13/10.4 ft, NKSW1 23/20.5/18/15 ft; AUBW1
   14,000/12,000/9,000/6,000 cfs and WRAW1 12,000/10,000/7,500/5,500 cfs (*measured live
   2026-08-24* from NWPS). **HEFS serves `QINE` — flow — only.** Therefore at the four stage-defined
   points, including Mount Vernon, an exceedance probability against the official category
   **cannot be computed** without a rating conversion that ADR-0011 forbids. The same structural
   block that stops NWM category agreement stops HEFS category probability. This is the single
   most consequential local fact in this entry.
3. **Two of the seed points are tidally influenced** (Mount Vernon, Ferndale). The NWRFC calibration
   framework explicitly cannot represent tidal basins; the NWM's coastal Total Water Level component
   is a separate model on a separate grid. Verifying a river forecast at a tidal outlet against a
   gauge whose stage is partly tidal conflates two errors.
4. **Regime stratification here is four-way, not two-way.** `docs/HYDROLOGY.md` §6 already names
   the regimes (AR-driven rain, rain-on-snow, spring melt, summer low flow). Rain-on-snow is the
   regime with the fewest events *and* the most model-structural uncertainty (SNOW-17 is a
   temperature index; the ROS energy balance is turbulent-flux dominated per §7). It will be the
   last regime to acquire a verifiable sample and should be flagged as such from the start.
5. **The seasonal concentration is extreme.** Flood season is roughly October–February. A "one
   year of verification data" claim is really "one flood season" — perhaps 3–8 independent AR
   sequences. Independence, not calendar length, is the sample size.

---

## 6. What this means for Cascadia Papsukkal

### 6.1 Doctrine additions

**D1 — "Unverifiable" is a legitimate evaluation verdict, alongside UNKNOWN.** `DATA_DOCTRINE.md`
§12 already makes UNKNOWN a first-class state for *values*. The evaluation layer needs the analogue
for *verdicts*: when the event count in a stratum is zero or near-zero, the report must say
`UNVERIFIABLE (n_events = 0 in 13,384 days)`, never "skill = 1.0" and never a blank. AUBW1 moderate
and major are the reference case.

**D2 — Every skill number carries its reference, its stratum and its event count.** A CRPSS without
a named reference is meaningless (climatology and persistence give different answers, and
climatology inherits persistence skill at day 1). A Brier score without n and K cannot be corrected
for decomposition bias. Proposed minimum record for any evaluation output:
`{metric, value, reference, n_pairs, n_events, base_rate, stratum, lead_time, method_version, evaluated_at}`.

**D3 — Consistency is verified separately from accuracy.** Forecast evolution is already stored
(supersession, never overwrite). Add a *revision magnitude* metric — successive-forecast change
normalised by ensemble spread or by threshold width — and report it as its own axis. Do not fold
it into accuracy; the literature says the two are only weakly correlated.

**D4 — Model version is part of knowledge time.** `as_known_at(T)` is necessary and not sufficient.
Every forecast row must carry the **producing model version** (`nwm-v3.0` vs `nwm-v3.1`,
`hefs-mefp`, NWRFC calibration vintage), and a hindcast that spans a version boundary must either
refuse or declare the split. NWM v3.1 went operational 2026-08-18; any archive the platform holds
already straddles that boundary.

**D5 — The official forecast is an observation of a judgement.** Because MODs are unlogged and not
in HEFS, the official forecast is not reproducible and must never be modelled, only recorded.
Corollary: HEFS is **not** the ensemble version of the official forecast, and the platform must not
imply that the official crest sits at any particular HEFS quantile.

### 6.2 Method and contract changes

**M1 — Fix the agreement window for NWM v3.1 assimilation (P0).** `agreement.py` uses
`LOOKBACK_H = 6.0` and `HAZARD_HORIZON_H = 72`. Under v3.1 the leading hours of the NWM member
hydrographs track observed values. Required: measure the assimilation tail length empirically
(compare `channel_rt` f001…f012 against USGS IV at the seed reaches for a week), then start the
comparison window after it, and record the measurement as a versioned method parameter with the
same "stated assumption" discipline `AgreementBands` already uses. Until measured, the honest
output at short lead is a caveat on the agreement level, not a higher level.

**M2 — Add HEFS as an ingest and as the model-probability source (P0).** All six seed LIDs are
served. The endpoints are `/hefs/v1/headers/`, `/hefs/v1/ensembles/`, `/hefs/v1/hydrograph-quantiles/`.
Provenance mapping:
- `source_kind` = **MODELED**, not OFFICIAL_FORECAST. The API self-labels EXPERIMENTAL and HEFS
  excludes the forecaster MODs that make the official forecast official. Badge it
  `nws-hefs-mefp (experimental)`.
- `issued_at` = `forecast_datetime`; `available_at` = `creation_datetime` (measured 3–5 h later);
  `retrieved_at` = fetch time. This is a rare case where the provider hands us all three cleanly —
  use it as the reference implementation of §3 three-valued time.
- Store **members**, not quantiles, and derive quantiles at read time (DATA_DOCTRINE §9). The member
  index is a historical year and belongs in the explanation layer verbatim: "12 of 45 members —
  including the 1990, 1995 and 2006 analogues — exceed …".
- **Archive aggressively.** The API keeps ~10 cycles. Without an ingest the forecast-evolution record
  for HEFS is lost after ten days.

**M3 — Model exceedance fractions: HEFS where flow thresholds exist, absent-with-reason elsewhere.**
`SurfaceReason.no_model_probability(why)` already exists for exactly this. At **AUBW1 and WRAW1**
(flow-defined) HEFS gives a defensible `k of 45 members exceed 9,000 cfs`. At **MVEW1, CRNW1, RNTW1,
NKSW1** the reason string should now name the specific blocker: *"official categories at this point
are defined in stage; HEFS produces flow (QINE) only; ADR-0011 forbids converting."* That is a
better sentence than today's generic one and it is true of both NWM and HEFS.

**M4 — Do not average the two ensembles, and do not treat 45 and 6 as comparable.** HEFS (45
members, forcing uncertainty via MEFP, no IC spread) and NWM MR (6 members, GFS-driven, USGS-DA
initialised) are different objects. A three-way agreement surface — official / HEFS / NWM — is more
informative than today's two-way one, but the member counts must be shown, because `3 of 6` and
`22 of 45` are not the same evidence. The existing `QUALITY_DEGENERATE_ENSEMBLE` flag generalises:
add a **distinct-value count** to every reported fraction.

**M5 — Design the harness around rarity from the start.** Concretely:
- Verification unit = **event**, not timestep. Timestep-pooled scores at a 0.36 % base rate measure
  the dry season.
- Report **SEDI** (non-degenerating) alongside POD/FAR, never POD/FAR alone.
- Report **CRPS** (which reduces to MAE for the deterministic official forecast) so the Cascade
  ensemble, HEFS and the official single-valued forecast land on one axis.
- Report the **bias-corrected** Brier decomposition (Ferro & Fricker) with n and K stated.
- Compute **relative economic value V(α)** across α ∈ [0.001, 0.1] and publish the curve, not a
  point. This is the honest way to say who the product is for.
- Bootstrap confidence intervals on every score; at these base rates the interval will usually
  contain zero, and that is the finding.
- Stratify by **regime × rising/falling limb × observed magnitude band**, per NWS OHD practice.
- Handle the **no-forecast problem**: a flood with no forecast pair is a miss, not an absence.
  The repo's `quality=missing` row discipline (DATA_DOCTRINE §4) is the right mechanism; it must be
  applied to *forecasts that were never issued*, not only to failed fetches.
- Measure **timing by threshold-crossing time** (Morris 1988), not by peak-time difference on a
  hydrograph that may have no crest — a lesson `agreement.py` already learned the hard way in its
  finding-A fix.

**M6 — Publish an evaluation report artefact, not a number.** `TESTING.md` §7's promotion rule
(EXPERIMENTAL → DERIVED only with a committed, reviewed evaluation report linked from the `Method`
row) is exactly right. Extend it: the report must contain the reliability diagram *and* its n, the
REV curve, the stratum table with event counts, and an explicit list of strata marked UNVERIFIABLE.
A method may not be promoted on aggregate skill alone.

### 6.3 New data sources this domain identifies

| source | endpoint | kind | why |
|---|---|---|---|
| **NWS HEFS API** | `https://api.water.noaa.gov/hefs/v1/{headers,ensembles,hydrograph-quantiles,locations}/` | MODELED (experimental) | 45-member ensemble at all six seed LIDs; the only authoritative probability the platform can currently obtain |
| HEFS forcing ensembles | same API, numeric `location_id`, `parameter_id` ∈ {`MAP`, `MAT`, `SWE`} | MODELED | **MEFP basin-average precipitation, temperature and SWE ensembles** — a direct, authoritative input to the *forcing* surface, currently built from NBM/HRRR alone |
| HEFS short-range image | `https://water.noaa.gov/resources/probabilistic/short_term/{LID}.shortrange.hefs.png` | MODELED | the operator-facing NWS rendering; useful as a cross-check, coverage differs from the API |
| NWM v3.1 post-processed RFC subsets | `https://nomads.ncep.noaa.gov/pub/data/nccf/com/nwm/prod/nwm.YYYYMMDD/post_processed/RFC/NW*/` | MODELED | NWRFC-domain subsets — much smaller than CONUS files for the same reaches |
| NWRFC model wrappers | `https://github.com/NOAA-NWRFC/nwsrfs-hydro-models` | reference | SNOW-17 / SAC-SMA / UNIT-HG / Lag-K in Python and R, verified functionally equivalent to CHPS's Java. Makes a *reproducible* reference hydrology possible for the unregulated Sauk |
| NWRFC calibration data/code | `https://zenodo.org/records/14057210`, `https://github.com/nwrfc/nwrfc-calibration-paper` | reference | the published SAKW1 calibration |
| USGS peak & daily values | `nwis.waterdata.usgs.gov/nwis/peak`, `waterservices.usgs.gov/nwis/dv` | OBSERVED | the base-rate denominators computed in §3 |

The **MAP/MAT/SWE MEFP ensembles** are the sleeper finding. The forcing surface currently derives
basin-average QPF itself from NBM/HRRR; NWRFC already publishes a bias-corrected, Schaake-shuffled,
45-member basin-average precipitation ensemble on the *same zones its hydrology model uses*. That is
a strictly better forcing input than anything the platform can derive, and it comes with the
provenance chain intact.

---

## 7. What this domain contradicts or qualifies in the current repo doctrine

1. **`HYDROLOGY.md` §5 item 2 is now under-specified, and §5 item 4 is now reachable sooner than it
   says.** §5 lists "Official or authoritative probabilities where they exist (HEFS/ESP ensembles,
   NWM medium-range ensemble exceedance fractions)" as tier 2. As of this entry HEFS **does** exist,
   at all six seed points, machine-readable. But §5 does not say what to do when the ensemble is in
   flow and the categories are in stage — which is the actual situation at four of six points. The
   doctrine needs a sentence: *a model exceedance fraction is computable only where the official
   threshold and the model output share a unit; elsewhere the ensemble is displayed as a hydrograph
   band and the fraction is absent with a reason.*

2. **`HYDROLOGY.md` §6 says model skill "is evaluated per basin and per regime as history
   accumulates". That is too optimistic at two of six points.** History will not accumulate at AUBW1
   moderate/major: 0 events in 36 years. §6 should be qualified: *at regulated points the upper
   categories may never acquire a verifiable sample; the evaluation reports UNVERIFIABLE and the
   agreement surface is the only meta-signal available there.*

3. **`DATA_DOCTRINE.md` §11 is necessary but not sufficient.** It defines look-ahead as a
   *timestamp* problem and enforces it with `as_known_at(T)`. Three look-ahead channels escape it:
   product-version improvement, model-version change (NWM v3.0→v3.1, 2026-08-18), and archive
   survivorship (HEFS keeps 10 cycles; what was purged is invisible, not `quality=missing`). §11
   should be extended to require a pinned `product_version` / `model_version` on every row and to
   treat a purged-before-archived cycle as a recorded gap.

4. **`DATA_DOCTRINE.md` §2 classes HEFS ambiguously.** HEFS is issued by NWS/NWRFC — which §2 says
   may be badged OFFICIAL — but it is served from an endpoint self-labelled EXPERIMENTAL and it
   omits the forecaster modifications that constitute the NWS's data assimilation. It is therefore
   **MODELED**, not OFFICIAL_FORECAST. §2's table should name HEFS explicitly on the MODELED row so
   nobody has to re-derive this.

5. **`DATA_DOCTRINE.md` §9(b) — "empirical fractions of a named ensemble" — needs a degeneracy
   clause.** The repo already discovered this for NWM (`QUALITY_DEGENERATE_ENSEMBLE`: 1 distinct
   crest across 6 members at all six reaches). The general rule belongs in doctrine: *a member
   fraction must be reported with the number of **distinct** member values; a fraction over
   identical members is arithmetic, not evidence.* Measured live, HEFS at MVEW1 has **zero spread at
   lead 0** — the same failure at a different point in the hydrograph.

6. **`agreement.py`'s comparison window is now scientifically wrong, not merely uncalibrated.** The
   module's docstring documents two hard-won fixes (shared window, crest-existence test). NWM v3.1
   introduces a third defect of meaning: inside the assimilation tail the NWM series **is** the
   observation. `LOOKBACK_H = 6.0` opens the window six hours *behind* `as_of`, well inside the
   region at risk. **Softened on review:** whether the window actually overlaps the tail depends on
   two unmeasured quantities — the tail length, which SCN 26-64 states only as "the beginning
   hours", and `ComparisonWindow.cycle_age`, since the tail is anchored on the NWM *cycle* time and
   not on `as_of`. A cycle several hours old may have its tail already behind the window's opening
   edge. The exposure is real and the measurement in M1 is required; "guaranteed contamination" is
   not established and should not be written as if it were.

7. **`agreement.py` calls its subject `nwm-v3.1-medium-range` (`MODEL_LABEL`).** As of 2026-08-18
   that is finally accurate — but any data ingested before that date is v3.0 under a v3.1 label. The
   label must become a stored per-row value, not a module constant.

8. **`TESTING.md` §7's metric list is right in spirit and incomplete in fact.** It names reliability
   diagram, Brier score, skill vs official and vs climatology. It should add: CRPS (the only score
   that puts the deterministic official forecast and the ensembles on one axis), SEDI (because POD/
   FAR/CSI degenerate at these base rates), bias-corrected Brier decomposition with n and K, relative
   economic value V(α), bootstrap intervals, and the rising/falling-limb and observed-magnitude
   stratifications the NWS itself uses. It should also name the **no-forecast problem** as a harness
   requirement.

9. **`HYDROLOGY.md` §12's Event Zero forecast evolution is described as a replay target; this domain
   says it is also the platform's first consistency benchmark.** The sequence 36.9 → 41.5 → 42.3 →
   39.1 → 38.26 vs 37.73 observed is a flip-flop with a **+4.57 ft** peak over-forecast. That number
   should be in the doctrine, because it sets the scale of what "the official forecast can be wrong
   by" in this region and is the honest counterweight to badging it OFFICIAL.

10. **Nothing in this domain contradicts the platform's refusal to print an uncalibrated
    probability.** It strengthens it: at base rates of 0.0016–0.008, a probability that has not
    passed a reliability check with a stated n is not merely unproven, it is very likely
    uncheckable with the data the platform will have for years. The `index` / `indicator` vocabulary
    is the correct long-term answer, not a placeholder.

---

## 8. Open questions

1. **What is the length of the NWM v3.1 assimilation tail?** How many forecast hours track observed
   values, does it vary by reach and by gauge latency, and does it differ between short-, medium-
   and long-range? Answerable directly by comparing `channel_rt` f001…f012 against USGS IV at the
   six seed reaches over one week.
2. **Does NWRFC's HEFS propagate reservoir regulation forward at AUBW1 and WRAW1?** CNRFC says its
   long-range traces are full-natural flow. WA short-range traces are initialised on regulated
   observed flow. A winter drawdown at Howard Hanson would settle it; so would asking NWRFC.
3. **Is EnsPost applied in the WA HEFS traces?** The API exposes only `ensemble_id = MEFP`. If
   EnsPost is not applied, the ensemble carries forcing uncertainty only and will be under-dispersed
   at short lead in exactly the way §2.2's zero-spread-at-lead-0 measurement suggests.
4. **What are the MEFP MAP/MAT/SWE basin `location_id`s for the Washington basins?** The `/locations/`
   endpoint enumerates numeric ids; mapping them to Skagit/Snoqualmie/Green/etc. zones would unlock
   an authoritative basin-average forcing ensemble.
5. **What is the actual verified skill of the NWRFC official forecast at the six seed points?**
   No public per-point verification for NWRFC was found in this sweep. NWS runs the Interactive
   Verification Program internally; whether NWRFC publishes point statistics is unknown.
6. **How long is the HEFS hindcast archive, and can the platform obtain it?** Demargne et al. describe
   multi-year HEFS hindcasting; the API serves ~10 days. If a hindcast archive exists for NWRFC
   points, it is the single highest-value dataset for calibrating anything the platform builds.
7. **Which NWRFC basins in western Washington are calibrated under the new framework, and with what
   KGE?** SAKW1 is published at 0.856. The Zenodo deposit (14057210) may contain more.
8. **Does the platform's own forecast archive straddle NWM v3.0→v3.1 (2026-08-18)?** If so, every
   stored NWM row before that date needs a version stamp retrofitted before any hindcast crosses it.
9. **What decision does the product actually support, and what is that decision's cost–loss ratio?**
   REV cannot be computed without α. Until the user's α is known, the platform can publish the V(α)
   curve but cannot claim value.
10. **Should the platform run its own reproducible hydrology on the unregulated Sauk?** The NWRFC
    model wrappers plus the published SAKW1 calibration make a *reproducible* SNOW-17/SAC-SMA/UNIT-HG
    reference simulation feasible — a pseudo-observation baseline against which the MOD-adjusted
    official forecast could be differenced, isolating the human contribution. High value, high cost,
    and it would be the platform's first genuinely original scientific product.
11. **Is KGE the right reporting metric at all,** given the 2025 critique? If the platform reports
    KGE it inherits a contested convention; if it does not, it loses comparability with NWRFC and
    USGS numbers.
12. **How many independent flood events per season do the eight basins collectively produce?** This
    is the real sample size for anything the platform wants to verify, and nothing in this sweep
    quantified it. It is computable from the USGS record and should be, before any evaluation plan is
    written.

---

## 9. Sources

Fetched and read:

- [Walters, G., C. Bracken, B. Gillies, L. Pope, H. Pai, S. Chokshi, V. Stegemiller, J. Bracken, S. King, T. Dixon, J. Intermill — *A comprehensive calibration framework for the Northwest River Forecast Center* (EarthArXiv preprint; submitted to JAWRA)](https://eartharxiv.org/repository/object/8993/download/16808/) — SNOW-17/SAC-SMA/UNIT-HG/Lag-K, AORC, k-means zones, EDDS, KGE results, **SAKW1 = Sauk = 0.856**, "lack of reservoir regulation" limitation. Journal version: [JAWRA 10.1111/1752-1688.70112](https://onlinelibrary.wiley.com/doi/10.1111/1752-1688.70112) (paywalled, 403).
- [Demargne, J., L. Wu, S. K. Regonda, J. D. Brown, H. Lee, M. He, D.-J. Seo, R. Hartman, H. D. Herr, M. Fresch, J. Schaake, Y. Zhu, 2014: *The Science of NOAA's Operational Hydrologic Ensemble Forecast Service*. BAMS 95(1), 79–98. DOI 10.1175/BAMS-D-12-00081.1](https://hdsc.nws.noaa.gov/pub/hdsc/data/papers/articles/HRL_Pubs_PDF_May12_2009/New_Scans_December_2013/HEFS_BAMS_Jan2014.pdf) — MEFP/EnsPost/Schaake shuffle, "MODs not currently included in HEFS", NFDC1 conditional bias, day-1 CRPSS artefact, hindcast forcing inconsistency.
- [Welles, E., N. Cajina, H. Herr (NWS OHD) — *Verification of National Weather Service River Stage Forecasts*](https://www.weather.gov/media/owp/oh/hrl/docs/NWSVerif.pdf) — IVP, three-category contingency table, POD/TFAR/HFAR/UFR/OFR, aggregation problem, no-forecast problem, timing errors, rising/falling limbs.
- [Ferro, C. A. T., and T. E. Fricker, 2012: *A bias-corrected decomposition of the Brier score*. QJRMS (preprint)](https://empslocal.ex.ac.uk/people/staff/ferro/Publications/ferro-fricker2012copyright.pdf) — Murphy decomposition, finite-n bias formulas, unattainability of an unbiased decomposition.
- [Dirkson, A., and M. Buehner, 2025: *Are we misdiagnosing ensemble forecast reliability? On the insufficiency of Spread-Error and rank-based reliability metrics*. arXiv:2512.02160](https://arxiv.org/pdf/2512.02160) — contested critique of rank histograms and spread–error diagnostics.
- [NWS Service Change Notice 26-64 (Updated), 2026-07-30: *Upgrade of National Water Model and related post processing system on NWS's WCOSS system, Effective August 18, 2026*](https://www.weather.gov/media/notification/pdf_2026/scn26-64_Updated_National_Water_Model_V3.1_aaa.pdf) — v3.1 contents, **assimilation into leading forecast hours**, member counts, 3.2 M reaches, 311 hydrofabric fixes.
- [NWS Public Information Statement 25-77, 2025-12-10: *Soliciting comments on the upgrade of the National Water Model to Version 3.1*](https://www.weather.gov/media/notification/pdf_2025/pns25-77_nwm_v3.1.pdf) — the proposed NDFD-MR and NBM-forced MR ensemble configurations that did **not** ship.
- [NOAA/NWS — *About the National Water Model*](https://water.noaa.gov/about/nwm) — configurations, forcings, cadences, ensemble sizes, reservoirs, DA.
- [NOAA/NWS — *Short-Term Probabilistic Guidance Product*](https://water.noaa.gov/about/short-term-probabilistic-guidance-product) — HEFS-derived 0–10 day guidance.
- [NOAA/NWS — *NWPS API info*](https://water.noaa.gov/about/api) — links to the experimental HEFS and NWM APIs.
- [NWPS HEFS API OpenAPI schema (EXPERIMENTAL)](https://api.water.noaa.gov/hefs/v1/schema/) and the live `headers`, `ensembles`, `hydrograph-quantiles`, `locations` endpoints — *all live measurements in §2.2 and §3 are from these*.
- [NWRFC — *Review of Extended Streamflow Prediction in NWSRFS*](https://www.nwrfc.noaa.gov/nwrfc/papers/esp_review/esp_review.html) — ESP construction, 39-year Dworshak example, the regulated-forecast error caveat.
- [NWRFC — *When NWSRFS, SEUS, and SNOW Intersect*](https://www.nwrfc.noaa.gov/nwrfc/papers/SEUS/seus.html) — forecaster MODs (`RRICHNG`, SAC storages) and the reproducibility statement.
- [NWRFC — *Water Supply Documentation*](https://www.nwrfc.noaa.gov/ws/ws_info.php) — ESP water-supply methodology.
- [CNRFC — *AHPS Ensemble Theory*](https://www.cnrfc.noaa.gov/ensemble_theory.php) — member count ≈ calibration years, 1980–2023 climatology, **"full-natural flow (no regulation effects are included in the forecasts)"**, 14-day climatology crossover.
- [CAWCR/WMO Forecast Verification — *Cost/loss ratio and relative value*](https://www.cawcr.gov.au/projects/verification/value/relativevalue_more.html) — cost–loss model, expense equations, V_max at α = s̄ equalling the Peirce score, envelope of value curves.
- [NOAA-NWRFC/nwsrfs-hydro-models (GitHub)](https://github.com/NOAA-NWRFC/nwsrfs-hydro-models) — Python/R wrappers for SAC-SMA, SNOW-17, UNIT-HG, Lag-K, CHANLOSS, CONS_USE, verified equivalent to the CHPS Java implementation.
- Live datasets queried directly on 2026-08-24 via `curl`:
  - `https://api.water.noaa.gov/nwps/v1/gauges/{MVEW1,CRNW1,RNTW1,NKSW1,AUBW1,WRAW1}` — official flood categories, units, crest history.
  - `https://waterservices.usgs.gov/nwis/dv/` for USGS 12200500, 12149000, 12113000, 12100490, 12119000, 12213100 — the base rates in §3.
  - `https://nwis.waterdata.usgs.gov/nwis/peak?site_no=12200500` — 86 annual peaks, 1906–2024.

Not independently fetched (paywall or HTTP 403), cited from indexed abstracts and clearly marked:

- *A comparative analysis of national water model versions 2.1 and 3.0 reveals advances and challenges in streamflow predictions during storm events*, Journal of Hydrology: Regional Studies (2025) — [ScienceDirect S2214581825000205](https://www.sciencedirect.com/science/article/pii/S2214581825000205) (403).
- *How well do U.S. National Water Model short-range forecasts predict flood event timing and magnitude?*, Journal of Hydrology: Regional Studies (2026) — [ScienceDirect S2214581826000066](https://www.sciencedirect.com/science/article/pii/S2214581826000066) (403).
- Ferro, C. A. T., and D. B. Stephenson, 2011: *Extremal Dependence Indices: Improved Verification Measures for Deterministic Forecasts of Rare Binary Events*. Weather and Forecasting 26(5) — [AMS](https://journals.ametsoc.org/view/journals/wefo/26/5/waf-d-10-05030_1.xml) (403). EDS/SEDS/EDI/SEDI formulas in §2.4 are from standard verification definitions, not from this paper's text.
- Hersbach, H., 2000: *Decomposition of the Continuous Ranked Probability Score for Ensemble Prediction Systems*. Weather and Forecasting 15(5), 559–570 — [AMS](https://journals.ametsoc.org/view/journals/wefo/15/5/1520-0434_2000_015_0559_dotcrp_2_0_co_2.xml) (403).
- Murphy, A. H., 1993: *What Is a Good Forecast? An Essay on the Nature of Goodness in Weather Forecasting*. Weather and Forecasting 8, 281–293 — [AMS](https://journals.ametsoc.org/view/journals/wefo/8/2/1520-0434_1993_008_0281_wiagfa_2_0_co_2.xml) (403). The three-goodness taxonomy is from the indexed abstract.
- *Analysis of National Weather Service Stage Forecast Errors*, Weather and Forecasting 32(4), 2017 — [AMS](https://journals.ametsoc.org/view/journals/wefo/32/4/waf-d-16-0219_1.xml) (403); NOAA repository mirror returned Access Denied.
- Brown, J. D., et al., 2014: *Verification of temperature, precipitation, and streamflow forecasts from the NOAA/NWS Hydrologic Ensemble Forecast Service (HEFS): 2. Streamflow verification*. Journal of Hydrology — [ScienceDirect S0022169414003941](https://www.sciencedirect.com/science/article/abs/pii/S0022169414003941) (403).
- USGS — *A roadmap for identifying and interpreting physical processes and national water model prediction bias associated with baseflow index regimes across the contiguous United States* — [USGS Pubs 70279220](https://pubs.usgs.gov/publication/70279220) (403).
- Troin, M., et al., 2021: *Generating Ensemble Streamflow Forecasts: A Review of Methods and Approaches Over the Past 40 Years*. WRR 57 — [AGU](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2020WR028392) (403).
- Zsoter, E., et al., 2009, on ensemble forecast "jumpiness"; Richardson, D. S., et al., 2020: *Evaluation of the Consistency of ECMWF Ensemble Forecasts*, GRL 47 — both blocked; the inconsistency/flip-flop concepts in §2.6 are from indexed abstracts.
- *Friends don't let friends use Nash-Sutcliffe Efficiency (NSE) or KGE for hydrologic model accuracy evaluation*, Environmental Modelling & Software (2025) — [ScienceDirect S1364815225003494](https://www.sciencedirect.com/science/article/abs/pii/S1364815225003494) (403).
- CW3E — [Forecast Informed Reservoir Operations at Howard A. Hanson Dam](https://cw3e.ucsd.edu/firo_howard_hanson/) and [Work Plan](https://cw3e.ucsd.edu/FIRO_docs/FIRO_HowardHanson_Workplan.pdf) — noted as the live western-Washington FIRO effort; not read in depth in this pass.
