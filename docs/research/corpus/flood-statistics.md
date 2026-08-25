# Flood frequency, mixed populations, and non-stationarity

*Corpus entry, 2026-08-24. Part of the Cascadia Papsukkal flood-science corpus.*

*Labels follow the project convention: **FACT** = read on a page or dataset I fetched (URL given), or
computed by me from a primary dataset I fetched (computation shown); **INFERENCE** = reasoned from
cited facts; **ASSUMPTION** = a working simplification; **OPEN QUESTION** = unresolved. Where a source
was paywalled or blocked I say "not independently fetched" and downgrade the claim. Original
computations in this file were run on 2026-08-24 against USGS NWIS peak files, USGS SIR 2016–5118
table 8, and the NWPS v1 API; the scripts are reproducible from the commands quoted inline.*

---

## 1. Headline

**Every recurrence-interval number that could be attached to a western Washington river is either
inapplicable, uncertain by a factor of two, or measuring a dam — and the authoritative source the
platform already reads (NWPS) publishes no recurrence interval at all. The correct engineering
response is not to compute a better one; it is to refuse the object, and to say precisely why.**

Four independent lines converge on that:

1. **Bulletin 17C excludes our rivers by its own terms.** "The procedures do not cover watersheds
   where flood flows are appreciably altered by reservoir regulation, watershed changes, or
   hydrologic nonstationarities" (FACT — [Bulletin 17C, p. 2](https://doi.org/10.3133/tm4B5)).
   101 of 107 annual peaks at Skagit near Concrete and 85 of 86 at Mount Vernon carry USGS
   qualification code **6, "discharge affected by regulation or diversion"** (FACT — computed from
   the NWIS peak files, §3).
2. **The peaks are a mixed population and the mixture is invisible in the fitted curve.** At Skagit
   near Concrete 18 % of annual peaks are warm-season (snowmelt) — and **not one of them is in the
   top 20** (FACT — computed, §3). USGS's own Washington report inspected for mixed populations and
   decided none were needed (FACT — SIR 2016–5118 p. 23); Barth et al. (2017) reached the opposite
   conclusion for the same region. That disagreement is unresolved and it is squarely about our
   basins.
3. **The uncertainty is a factor of two and it is published.** Across the 69 western Washington
   gauges with ≥50 years of record in USGS SIR 2016–5118, the median 95 % confidence interval on the
   1 % AEP flood spans a factor of **1.66**; at 0.2 % AEP it spans **1.98** (FACT — computed from
   the report's own table 8, §3).
4. **"The 100-year flood keeps happening" is not evidence of anything.** In those same 69 gauges,
   **52 %** have already recorded a peak exceeding their own published 1 % AEP estimate. Under
   perfect stationarity and a perfect estimate, the expected fraction for these record lengths is
   **49 %** (FACT — computed, §3). The observation is the arithmetic, not the climate.
   Caveat on how strong that test is: each published 1 % AEP estimate is *fitted to the very record
   whose maximum is then compared against it*, so the record max is one of the observations that set
   the quantile. The comparison is a consistency check on the fitting procedure, not a powerful test
   of stationarity — a real trend would already be partly absorbed into the fitted quantile. It
   refutes "the 100-year flood keeps happening, therefore the climate has shifted"; it does not, on
   its own, establish stationarity (INFERENCE).

The one thing a provenance-strict platform *can* do with frequency information is the thing nobody
does: carry it as a **dated, versioned, method-stamped estimate with its confidence interval and its
applicability flags**, and let the interface refuse to render it as a category, a colour, or a
sentence containing the word "year".

---

## 2. Mechanisms — the statistics, stated properly

### 2.1 What a frequency curve is, and what it is not

Flood frequency analysis (FFA) is not a forecast and not a physical model. It is a *fit of a
parametric distribution to a sample of annual maxima*, extrapolated past the sample. Every property
of the answer is a property of that fit.

Let `Q₁, …, Qₙ` be annual maximum instantaneous peak discharges. The **annual exceedance
probability** (AEP) `p` of a magnitude `q` is `p = P(Q > q)` in any one year. The **return period**
is defined as its reciprocal:

```
T = 1 / p                                             (return period, years)
```

`T` is a unit-carrying restatement of `p`, nothing more. Bulletin 17C states the consequence that
the phrase hides — risk accumulates over a design life (FACT — [Bulletin 17C, "Risk Accumulates",
p. 4–5](https://doi.org/10.3133/tm4B5)):

```
pₙ = 1 − (1 − p)ⁿ            probability of ≥1 exceedance in n years
```

For `p = 0.01`: **22 % over 25 years, 40 % over 50 years, 63 % over 100 years, and 26 % over the
life of a 30-year mortgage** (FACT — those four numbers are quoted verbatim in Bulletin 17C).

The USGS says the term itself is the problem: the "100-year flood" is "a misinterpretation of
terminology that leads to a misconception", and AEP language "reminds the observer that a rare flood
does not reduce the chances of another rare flood within a short time period" (FACT —
[USGS Water Science School, "The 100-Year Flood"](https://www.usgs.gov/special-topics/water-science-school/science/100-year-flood)).

A related structural subtlety: `T` from the annual-maximum series and the average recurrence interval
`ARI` from a peaks-over-threshold series are *not* the same quantity. Langbein's (1949) relation
`T = 1/(1 − e^(−1/ARI))` connects them under a homogeneous Poisson assumption on exceedance counts.
Dell'Aira, Cancelliere & Meier (2025) show the functional form survives non-stationarity and mixed
populations with adapted definitions, but **requires generalisation when exceedance counts are over-
or under-dispersed relative to Poisson** — the classical formula being the limiting case (FACT —
[arXiv:2509.23546](https://arxiv.org/abs/2509.23546)). Clustered AR sequences (Event Zero: three ARs
in nine days) are precisely an over-dispersed exceedance process, so this is not an abstract caveat
here (INFERENCE).

### 2.2 The federal method: LP3 fitted by EMA

Bulletin 17C (England et al. 2018, ver. 1.1 May 2019, USGS TM 4-B5) is the binding federal standard.
Its base method is the **log-Pearson Type III** distribution fitted by the **method of moments**
(FACT — [Bulletin 17C](https://doi.org/10.3133/tm4B5)):

```
X = log₁₀ Q  ~  Pearson Type III (mean m, sd s, skew γ)
Q_p = 10^( m + K(γ, p) · s )
```

with `K` the Pearson III frequency factor; the Wilson–Hilferty approximation used in practice is

```
K(γ, p) = (2/γ) · [ (1 + γz/6 − γ²/36)³ − 1 ],   z = Φ⁻¹(1 − p)
```

Bulletin 17C's four named improvements over 17B (FACT, quoted list, pp. 3–4):

1. **Interval representation of peak-flow data** — every observation is a `[lower, upper]` interval,
   not a point;
2. **the Expected Moments Algorithm (EMA)** (Cohn et al. 1997), a generalisation of the method of
   moments that consumes interval, censored and binomial-censored data *simultaneously* rather than
   as a chain of post-hoc adjustments;
3. **confidence intervals that account for historical/paleoflood information and regional skew**
   (Cohn et al. 2001) — "Large differences in confidence intervals may be observed between intervals
   computed with Bulletin 17B and [17C] because the Bulletin 17B confidence intervals ignored the
   uncertainty in the estimated skewness coefficient" (FACT, quoted);
4. **the Multiple Grubbs-Beck Test (MGBT)** (Cohn et al. 2013) for potentially influential low floods
   (PILFs), replacing the single-outlier test.

**Perception thresholds** are the concept that makes EMA work. Each year of the record is described
by a threshold `Th` above which a flood *would have been recorded had it occurred*. Systematic years
have `Th = 0`; historical/paleoflood years have `Th` = the level a flood had to reach to leave
evidence. A year with no recorded flood then contributes the censored information `Q < Th`, which is
real information, not a gap (FACT — Bulletin 17C, "Data Representation Using Flow Intervals and
Perception Thresholds", p. 15). **Treating historic peaks as if they were systematic annual maxima —
the naive thing — is the specific error EMA exists to prevent**; §3 quantifies what it costs on the
Skagit.

**Regional skew.** Skew is the parameter the tail is most sensitive to and the one a short record
estimates worst, so 17C weights the station skew `Ĝ` against a regional skew `G`:

```
G_W = ( MSE_G · Ĝ  +  MSE_Ĝ · G ) / ( MSE_G + MSE_Ĝ )
```

17C recommends the Bayesian WLS / Bayesian GLS regionalisation of Veilleux et al. (2011) and
explicitly retires Bulletin 17B plate 1: "The regional skew estimates published in IACWD (1982,
plate 1) are not recommended for use in flood frequency studies" (FACT, quoted).

### 2.3 Mixed populations — why one distribution is improper

If annual maxima arise from two independent generating processes with annual-maximum CDFs `F_A`
(atmospheric river) and `F_B` (snowmelt or other), the annual maximum of the *union* has

```
F_mix(q) = F_A(q) · F_B(q)          ⇒   AEP_mix(q) = 1 − F_A(q)·F_B(q)
```

which is in general **not** a Pearson III in log space for any parameter set. Fitting a single LP3
to the pooled sample estimates a shape that belongs to neither process. The characteristic symptom
17C names is "flood frequency curves with abnormally large skew coefficients reflected by abnormal
slope changes when plotted on logarithmic normal probability paper" (FACT, quoted, p. 21).

17C's guidance is conditional and deliberately weak (FACT, all quoted from pp. 21–22):

- "When it can be shown that there are two or more distinct and generally independent causes of
  floods, it may be more reliable to segregate the flood data by cause, analyzing and computing
  separate curves for each type of event and then combining the curves."
- "**Separation by calendar periods in lieu of separation by events is not considered hydrologically
  reasonable**, unless the events in the separate periods are clearly caused by different
  hydrometeorological conditions."
- "**regional skew coefficients cannot be used unless developed for the specific types of events
  being examined**."
- "**If the flood events that are believed to comprise two or more populations cannot be identified
  and separated by an objective and hydrologically meaningful criterion, the record shall be treated
  as coming from one population.**"
- "The Work Group did not conduct an evaluation of these procedures. Additional efforts are needed
  to provide guidance on the identification and treatment of mixed distributions."

That last sentence is the true state of the art: the federal standard concedes it has no evaluated
method for the situation that obtains in every basin Cascadia Papsukkal covers.

### 2.4 Regulation — the excluded case

Bulletin 17C's scope statement is a hard exclusion, not a caution (FACT, quoted, p. 2):

> "The procedures do not cover watersheds where flood flows are appreciably altered by reservoir
> regulation, watershed changes, or hydrologic nonstationarities, or where the possibility of unusual
> events, such as dam failures, must be considered."

Its "Regulated Flow Frequency" section (p. 35–36) says national guidance "is one area of future work
needed" and lists the ad-hoc options practitioners use: reconstructing unregulated flows (USACE
1993), graphical frequency analysis, total-probability methods (Kubik 1990; Sanders et al. 1990),
regionalising cumulative flood storage per unit area (Asquith 2001) (FACT). None is a standard.
17C's own "Applicability" section lists "the best methods of addressing regulated flows and mixed
distributions" first among the concerns that remain unsolved (FACT, quoted, p. 36).

Under 17C a regulated record is not merely uncertain — it is **out of scope**, and any frequency
curve fitted to it is a deviation that "must be supported by appropriate study and accompanied by a
comparison of results using the recommended procedures".

### 2.5 Non-stationarity: detection, and the separate question of modelling it

17C assumed time invariance and declined to evaluate methods: "Time invariance was assumed in the
development of these Guidelines… The Work Group did not evaluate methods to account for climate
variability in flood frequency" (FACT, quoted, p. 23). It permits time-varying parameters where
"there is sufficient scientific evidence", requiring that "all such methods employed need to be
thoroughly documented and justified".

The standard non-stationary construction replaces constant parameters with covariate-dependent ones,
e.g. for a GEV location:

```
μ(t) = μ₀ + μ₁·t        (or μ₀ + μ₁·x(t) for a physical covariate x)
Q_p(t) = μ(t) + (σ/ξ)·[ (−ln(1−p))^(−ξ) − 1 ]
```

Two distinct debates get conflated and must be kept apart:

- **Detection** — is there a trend in this record? Mann–Kendall `τ` is the workhorse. Its p-values
  are inflated by long-term persistence (Cohn & Lins 2005), a point the USGS Washington report itself
  makes (FACT — SIR 2016–5118 p. 8, citing Cohn and Lins 2005).
- **Modelling** — should the design estimate be non-stationary? Here the literature is genuinely
  contested (§4).

Slater et al. (2021), the standard review, is explicit about record length: multi-decadal shifts
"may simply be temporary excursions in longer (e.g. 100 year) records"; 50-year records are
insufficient where multi-decadal periodicity exists; "centuries of data" may be needed for low
signal-to-noise variables like precipitation and discharge extremes; "inappropriately applying
nonstationary models to short time series may have the undesired effect of increasing uncertainty";
and "stationary models may be the preferred option for design and management of extremes" when
structure or drivers are uncertain (FACT —
[HESS 25, 3897–3935, 2021](https://hess.copernicus.org/articles/25/3897/2021/)).

### 2.6 Precipitation frequency: the Atlas 14 → Atlas 15 transition

NOAA Atlas 15 will consist of two volumes (FACT —
[NOAA Atlas 15 informational page](https://water.noaa.gov/about/atlas15), fetched 2026-08-24):

- **Volume 1** — "a snapshot of current estimates that account for temporal changes in historical
  observations". It "will supersede the current NOAA Atlas 14 precipitation frequency estimates".
- **Volume 2** — future projections, built by "applying adjustment factors to Volume 1 estimates
  (i.e. future relative changes obtained from downscaled climate model data)".

Coverage: 50 % to 0.1 % average annual exceedance, durations 5 minutes to 60 days, spatially
continuous, accounting for trends "through the year 2100". The Montana pilot was released
2024-09-26 with a reduced envelope (1 h – 10 d, 50 % – 1 %) and "did not go through the peer review
process" (FACT, same page).

Schedule as published today (FACT, same page): Montana pilot 2024; **CONUS preliminary estimates
September 2026, published 2027**; oCONUS preliminary 2027, published 2028. Note a live
inconsistency: the same page also says publication "in 2026 (contiguous United States) and 2027
(outside the contiguous United States)", and an ASFPM policy note describes an approximately
one-month contract pause in 2025 against an earlier 2025-preliminary/2026-published schedule (FACT —
[ASFPM](https://www.floods.org/news-views/policy-matters/after-brief-delay-noaas-atlas-15-project-moves-ahead/)).
The schedule has slipped at least once and the page itself is not self-consistent. **OPEN QUESTION.**

---

## 3. Quantitative anchors

Rows marked ***(computed here)*** are my own calculations, run 2026-08-24, from the primary source
named. They are INFERENCE-grade derivations of FACT-grade inputs, not published values.

| Quantity | Value | Context | Source |
|---|---|---|---|
| Bulletin 17C version | ver. 1.1, May 2019; 148 p. | USGS TM 4-B5; the binding federal standard | [doi:10.3133/tm4B5](https://doi.org/10.3133/tm4B5) |
| 17C minimum record | **10 annual peaks** ("with an informative regional skew and/or record extension"); "not reliable with records composed of less than 10" | scope statement, p. 2 and p. 36 | Bulletin 17C |
| 17C AEP validity range | quantiles **0.10 to ~0.002**; below 0.005 "generally require augmentation"; below 0.002 needs >1,000-year historical/paleoflood records | p. 4, p. 36 | Bulletin 17C |
| 17C applicability | applies "only to portions of the flood frequency curve for AEPs less than 0.10" | p. 36 | Bulletin 17C |
| Risk over a design life at p=0.01 | 22 % / 25 yr · 40 % / 50 yr · 63 % / 100 yr · 26 % / 30 yr | quoted verbatim in 17C | Bulletin 17C p. 4–5 |
| PNW regional skew (B-WLS/B-GLS, the method 17C later recommended) | **G = −0.07**, MSE = **0.180**, GSE = 0.4243 | constant model, best for the whole PNW; 290 gauges ≥35 yr in ID/OR/WA/western MT | [SIR 2016–5118](https://pubs.usgs.gov/sir/2016/5118/sir20165118.pdf) p. 23, p. 46 |
| Superseded national skew map | MSE = **0.3025** | Bulletin 17B plate 1; 17C explicitly does not recommend it | SIR 2016–5118; Bulletin 17C |
| WA regional-regression standard error | **43.2–58.0 %** (western WA, Regions 3–4); 69.1–119.6 % (eastern WA) | ungauged-site estimates | SIR 2016–5118 abstract |
| WA regional-regression pseudo-R² | **92.35–95.44** (Regions 3–4) | western WA is the well-behaved half of the state | SIR 2016–5118 abstract |
| AR fraction of annual peaks, PNW | **>80 %, ~100 % at several locations** | 1,375 USGS gauges ≥30 yr | [Barth et al. 2017, WRR 53:257–269](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1002/2016WR019064) |
| AR fraction, central Columbia basin | 35 % to ~90 % | genuinely mixed region | Barth et al. 2017 |
| AR share of largest peaks | "nearly all of the top-5 and top-10 peaks on record" even where ARs are only 30–70 % of the record | the upper tail is AR-dominated | Barth et al. 2017 |
| AR-only vs mixed LP3 quantiles | RPDs commonly negative → AR-only quantile estimates are **higher** than mixed-population estimates | i.e. pooling *dilutes* the tail | Barth et al. 2017 |
| **Western WA cool-season share of annual peaks** ***(computed here)*** | Skagit@Concrete **80 %**, Skagit@Mount Vernon **86 %**, Snoqualmie@Carnation **95 %**, Skykomish@Gold Bar **95 %** | Oct–Mar vs Apr–Sep, full NWIS peak record | NWIS peak files, §3 method below |
| **Warm-season peaks in the top 20** ***(computed here)*** | **0 of 20 at Concrete, Carnation and Gold Bar; 1 of 20 at Mount Vernon** (1959-04-30, 92,300 cfs, rank 16). Also 1 of 20 at Green@Auburn and at NF Nooksack@Glacier | the mixture is *overwhelmingly*, not *entirely*, in the body: warm-season peaks are near-absent from the tail but not categorically absent | NWIS peak files |
| **Cool/warm mean peak ratio** ***(computed here)*** | Concrete 1.53 · Mount Vernon 1.45 · Carnation 1.67 · Gold Bar 1.88 | two populations, cleanly separated in the mean | NWIS peak files |
| **Median 95 % CI width on the 1 % AEP, western WA** ***(computed here)*** | **factor 1.66** (IQR 1.53–1.86), 69 gauges with ≥50 yr | e.g. Snoqualmie@Carnation 1 % AEP = 86,700 cfs, CI **69,700–108,000** | SIR 2016–5118 table 8 |
| **Median 95 % CI width on the 0.2 % AEP, western WA** ***(computed here)*** | **factor 1.98** | the "500-year flood" is known to a factor of two | SIR 2016–5118 table 8 |
| **Gauges whose record max already exceeds their own 1 % AEP** ***(computed here)*** | **36 of 69 (52 %)**; binomial expectation under stationarity for these record lengths = **49.4 %** | the "100-year flood keeps happening" is arithmetic, not signal | SIR 2016–5118 table 8 |
| **…exceeding their own 0.2 % AEP** ***(computed here)*** | 6 of 69 (**8.7 %**); expectation **12.8 %** | slightly *fewer* than expected — consistent with the fitted tail being pulled up by the record max | SIR 2016–5118 table 8 |
| Skykomish @ Gold Bar | published 1 % AEP = **121,000 cfs** (CI 96,300–153,000); observed max **129,000 cfs** (2006-11-06) | the record maximum exceeds the published 100-year flood | SIR 2016–5118 table 8; NWIS |
| Sauk near Sauk (unregulated) | 1 % AEP = **104,000 cfs** (CI 80,200–136,000); observed max 106,000 | the least-contaminated long record in the Skagit system | SIR 2016–5118 table 8 |
| **Kendall τ, WA long records through WY2025** ***(computed here)*** | NF Stillaguamish @ Arlington **+0.345 (p<0.0001)**; Sauk nr Sauk **+0.199 (p=0.0038)**; NF Nooksack bl Cascade Ck nr Glacier (12205000) **+0.310 (p<0.0001)**; Skykomish @ Gold Bar +0.168 (p=0.015) | full record, historic peaks excluded | NWIS peak files |
| **…same gauges restricted to WY1970–2025** ***(computed here)*** | Arlington **+0.092 (p=0.32)**; Sauk **+0.066 (p=0.48)**; Gold Bar +0.100 (p=0.28); **Nooksack@Glacier +0.362 (p=0.0001)** | three of four significant trends vanish — they are steps, not trends. Nooksack is the exception | NWIS peak files |
| **Regulated gauges** ***(computed here)*** | Green @ Auburn **τ = −0.187 (p=0.010)**; Skagit @ Concrete −0.028 (p=0.68); Skagit @ Mount Vernon +0.048 (p=0.51) | a significant *negative* trend at Auburn measures Howard Hanson, not climate | NWIS peak files |
| **Green @ Auburn is a step, not a trend** ***(computed here)*** | WY1970–2025: τ = **−0.070 (p=0.46)**, not significant. Median annual peak pre-WY1962 **12,900 cfs** (n=25) vs WY1962+ **9,005 cfs** (n=62) | Howard Hanson closed 1961–62; the negative trend is a level shift at impoundment, tested the same way as the four unregulated gauges above | NWIS peak file 12113000 |
| USGS WA trend result (published) | 21 of 83 long-term sites significant at p≤0.05 (16 positive, 5 negative); max \|τ\| = 0.41; "all sites with increasing trends were on the western side of the Cascade Mountains" | data through WY2014 | SIR 2016–5118 p. 8 |
| Peaks-above-base frequency trend, WA | τ = 0.125, **p = 0.0897 — not significant**; PDO+SOI regression adj. R² = **0.03**, no variable significant at 0.1 | 65 gauges, WY1930–2014 | SIR 2016–5118 p. 10–11 |
| WA active trends | 38 sites positive, 21 negative; half the positive ones began after 1965 | trends including WY2014 | SIR 2016–5118 p. 13 |
| Step trends in WA | positive steps around **1940–1950** and the **late 1960s**, persisting to 2014 | "Flood frequencies computed before and after a step trend will have different magnitudes" | SIR 2016–5118 p. 13 |
| **Regulation flag density** ***(computed here)*** | Skagit@Concrete **101/107** peaks coded 6; Skagit@Mount Vernon **85/86**; Green@Auburn **62/87**; Snoqualmie@Carnation **22/95** coded 5 | USGS itself flags the record as regulated | NWIS peak files, `peak_cd` |
| **Snowmelt flag density** ***(computed here)*** | code 9 ("snowmelt, hurricane, ice-jam or debris dam breakup") appears **3 times in the 900 annual peaks** across the ten records checked — 2 at Sauk nr Sauk, 1 at NF Nooksack bl Cascade Ck nr Glacier (12205000), zero elsewhere | **USGS peak codes cannot serve as the "objective criterion" 17C demands for mixed-population separation in western WA** | NWIS peak files |
| Skagit historic peaks, published (revised 2007) | 1815: **510,000** · 1856: **340,000** · 1897: **265,000** · 1909: **245,000** · 1917: **210,000** · 1921: **228,000** cfs | table 1; revisions of −5.8 % to +2.0 % from the previously published values | [SIR 2007–5159](https://pubs.usgs.gov/sir/2007/5159/pdf/sir20075159.pdf) |
| Skagit historic peaks, prior published | 1815: 500,000 · 1856: 350,000 · 1897: 275,000 · 1909: 260,000 · 1917: 220,000 · 1921: 240,000 cfs | the values in force 1923–2007 | SIR 2007–5159 table 1 |
| 1921 recalculations | 228,000 cfs (from 1949 n-verification) = **−5.0 %**; 219,000 cfs (from 2003/2006 data) = **−8.8 %**; 225,000 cfs (Flynn & Benson 1952) = −6.2 % | three independent recalculations, all lower than Stewart's 240,000 | SIR 2007–5159 |
| 1921 stated accuracy | slope-area recalculation is "a fair measurement **within 15 percent** of the actual value" | Benson and Dalrymple (1967) accuracy class | SIR 2007–5159 |
| USGS position, 2006 (one year earlier) | "the error of the 1921 peak discharge calculation is **+/-10 to 15 percent** and the most accurate value we can compute is **240,000 cfs plus or minus 24,000 to 36,000 cfs** … it would be **improper to use a lesser value** even though it may lie within the error range" | letter from the USGS Chief Scientist for Hydrology, 2006-10-26 | [USGS reply to the Kunzler whitepaper](https://www.skagitriverhistory.com/USGS%20Docs/2006-10-26%20USGS%20Reply%20to%20Whitepaper.pdf) |
| Stated accuracy of the *other* historic peaks | Stewart assigned 5 % to 1921 and 10–20 % to the others; USGS 2006: "10 to 15 percent would probably be more reasonable for the 1921 peak flow calculation and **15–25 percent for the other historical floods**" | the three peaks derived *from* 1921 by rating extension | USGS reply letter, 2006 |
| USGS revision guideline | peaks "should be revised if the difference … is more than about 10 percent" (Novak 1985) | why the 1952 and 1954 recalculations were never published | SIR 2007–5159 p. 11 |
| Rating extrapolation at Concrete | highest current-meter measurement = **138,000 cfs** (2003-10-21, meas. #475); the 1815 estimate of 510,000 cfs comes from a **straight-line rating extension to gage height 69.3 ft** | a ~3.7× extrapolation in discharge beyond any measurement | SIR 2007–5159 p. 10 |
| NWIS qualification on 1815/1856 | codes **2 (estimate), 7 (historic), Bm (month of occurrence unknown or not exact)** | the two largest numbers in the Skagit record are undated to the month | NWIS peak file 12194000 |
| **Naive vs conservative FFA at Concrete** ***(computed here)*** | 1 % AEP = **186,000 cfs** (systematic peaks only, weighted skew) vs **309,000 cfs** (historic peaks pooled in as if systematic) — a **factor of 1.66** | not a Bulletin 17C analysis; an illustration of the leverage EMA exists to control | NWIS peak file; method §3 |
| Precipitation frequency standard for **Washington** | **NOAA Atlas 2 Vol 9 (1973)** for 1–24 h; Arkell & Richards (1986) for <1 h; **Technical Paper 49 (1964)** for >24 h | Washington and Oregon are the **only two CONUS states not covered by NOAA Atlas 14** | [NWS OWP, current PF documents](https://www.weather.gov/owp/hdsc_currentpf), fetched 2026-08-24 |
| Idaho / Montana / Wyoming | NOAA Atlas 14 Vol 12 (2024) | our neighbours were updated; we were not | same |
| NOAA Atlas 15 CONUS schedule | preliminary **September 2026**, published **2027** | Volume 1 supersedes Atlas 14 (and, for WA, Atlas 2) on publication | [water.noaa.gov/about/atlas15](https://water.noaa.gov/about/atlas15) |
| **NWPS recurrence content** ***(computed here)*** | the NWPS v1 `/gauges/{lid}` payload for MVEW1, CONW1, CRNW1, AUBW1 contains **no AEP, recurrence-interval or return-period field of any kind** | keys: flood.categories, flood.crests, datums, status, impactsLowWaters, … | `api.water.noaa.gov/nwps/v1/gauges/MVEW1`, fetched 2026-08-24 |

**Method for the computed rows.** Peak files: `curl "https://nwis.waterdata.usgs.gov/nwis/peak?site_no=NNNNNNNN&agency_cd=USGS&format=rdb"`.
Seasonality: month of `peak_dt`, Oct–Mar vs Apr–Sep; the 1815/1856 rows have month `00` and are
excluded from both. Trend: Kendall τ on (water year, peak), historic peaks (`peak_cd` containing 7)
excluded, water year = calendar year + 1 for Oct–Dec. CI ratios and exceedance counts: USGS SIR
2016–5118 table 8 xlsx (`sir20165118_table8.xlsx`), line 3 (weighted flood discharge), line 4 (95 %
CI), column "Maximum peak used in analysis".
**Reproducibility note (adversarial re-derivation, 2026-08-24).** An independent re-parse of the same
workbook under the stated filter (flood region 3 or 4, column E ≥ 50 systematic peaks) returned **76**
gauges, not 69 — median record 68 yr (matches), median 95 % CI ratio **1.63** at 1 % AEP and **1.94**
at 0.2 % AEP, **40 of 76 (52.6 %)** exceeding their own 1 % AEP against a binomial expectation of
49.5 %, and 7 of 76 (9.2 %) at 0.2 % AEP against 12.9 %. No variant of the filter (section A only,
other record-length thresholds from 48 to 59) reproduces a denominator of 69, and the median CI ratio
is stable at 1.61–1.63 across all of them — never 1.66. **The gauge count and the second decimal place
of the CI ratios should be treated as unconfirmed; the substantive result is unchanged** — a factor of
~1.6–1.7 at 1 % AEP, ~1.9–2.0 at 0.2 % AEP, and observed exceedance ≈ binomial expectation.

Illustrative LP3: method-of-moments on log₁₀ Q with
Wilson–Hilferty `K`, station skew weighted to the PNW regional skew −0.07 (MSE 0.180) using the
Bulletin 17B `MSE_Ĝ` approximation. **This is deliberately not an EMA/MGBT analysis** — its purpose
is to show the size of the sensitivity, not to produce a number anyone should use.

---

## 4. What is settled, what is emerging, what is contested

### Settled (established)

- **LP3 + EMA + MGBT + Bayesian regional skew is the federal standard for unregulated, stationary,
  single-population records.** Not disputed within US practice.
- **Return period is a reciprocal of AEP and accumulates over a design life.** Not disputed; only
  miscommunicated.
- **The upper tail of western US flood frequency is AR-dominated.** Barth et al. (2017) over 1,375
  gauges; consistent with Neiman et al. (2011) for western Washington specifically.
- **Regulated records are outside Bulletin 17C's scope.** Stated in the document.
- **Historical and paleoflood information materially improves rare-quantile estimates *when
  represented as intervals with perception thresholds*.** This is the central innovation of 17C.
- **Estimation uncertainty on rare quantiles is large — a factor of ~2 at 1 % AEP in western
  Washington.** Published in the CIs of SIR 2016–5118 and reproduced above.
- **NOAA Atlas 15 will replace Atlas 14 (and Atlas 2 in Washington) with a non-stationary
  methodology.** Agency-announced with dates.

### Emerging

- **Mixed-population FFA conditioned on a physical event catalogue** (AR detection rather than
  calendar season). Barth et al. (2017) is the demonstration; there is still no evaluated federal
  procedure — 17C says so in its own text.
- **Generalisation of the AM↔POT correspondence to non-stationary, mixed and over-dispersed
  processes** (Dell'Aira et al. 2025, arXiv, September 2025 — recent, not yet a standard).
- **Covariate-based rather than time-based non-stationary models** — conditioning the distribution on
  a physical driver (IVT climatology, reservoir state, GMST) rather than on the year. Slater et al.
  (2021) recommend applying non-stationary approaches only "when there are good reasons to suspect
  physically plausible and predictable drivers of change".
- **Atlas 15 Volume 2's adjustment-factor approach** — applying downscaled-model relative changes to
  an observation-based Volume 1. Announced; the pilot "did not go through the peer review process".

### Contested

- **Should design estimates be non-stationary at all?** Milly et al. (2008) "Stationarity is dead"
  set the agenda; Montanari & Koutsoyiannis (2014) replied that "stationarity is immortal";
  Serinaldi & Kilsby (2015) argued "stationarity is undead: uncertainty dominates the distribution
  of extremes", finding that model-complexity uncertainty can swamp any gain; Luke et al. (2017)
  split-sampled 1,250 US annual-maximum records and found the **stationary approach superior in
  out-of-sample prediction while the non-stationary approach won only within-sample**.
  **Luke et al. was subsequently fetched in full** (eScholarship copy of WRR 53(7):5469–5494) and that
  characterisation is confirmed verbatim: "Our analysis shows that the ST predictions are preferred,
  overall. NS model parameter extrapolation is rarely preferred" (FACT). **But it carries a carve-out
  that applies directly to this platform's basins and was omitted above:** "if fitting period
  discharges are influenced by physical changes in the watershed, for example from anthropogenic
  activity, the uST model is strongly preferred relative to ST and NS predictions. The uST model is
  therefore recommended for evaluation of current flood risk in watersheds that have undergone
  physical changes" (FACT, quoted) — uST being an *updated stationary* model fitted with the
  non-stationary parameter values at the end of the record. Skagit, Green, White and Cedar are
  watersheds that have undergone exactly such physical change, so Luke et al. does **not** license
  "fit the whole record as stationary" for them; it licenses refitting stationary parameters to the
  post-change period. *(Serinaldi & Kilsby, Milly, and Montanari & Koutsoyiannis full texts were
  **not independently fetched** — ScienceDirect and Wiley returned 403 — though each was confirmed to
  exist with the stated authors, journal, volume and pages. Their characterisations are from
  search-result summaries and from Slater et al. 2021, which I did fetch.)*
- **Are western Washington peak flows actually a mixed population requiring separate treatment?**
  Barth et al. (2017) say the AR/non-AR split matters for quantile estimation in the western US.
  USGS SIR 2016–5118 — the authoritative Washington study, published the year before — inspected the
  frequency plots and concluded: "no streamgages had substantially diverging distributions that
  required a mixed-population analysis" (FACT, quoted, p. 23). Read the whole passage, though: the
  same page first concedes "many of the streamgages in the flood frequency analyses **do** have a
  mixed population of peak flows", and rejects only *separate treatment*, on the grounds that "the
  single log-Pearson Type III distribution seemed to capture both populations reasonably well"
  (FACT, quoted, p. 23). The disagreement with Barth et al. is therefore about the *criterion*
  (visual divergence of a fitted curve vs. quantile difference under an event catalogue), not about
  whether a mixture exists — both agree it does. **Both are USGS-affiliated and they disagree about our state.** One further qualification on the
  worked example: Stehekin River (12451000) sits in the report's **flood region 2**, not regions 3–4 —
  an east-slope, Lake Chelan, snowmelt-dominated basin, a different hydroclimate from the maritime
  western-Washington basins this platform covers (FACT — table 8, region column). The report's
  *conclusion* is stated for every streamgage in the study and so does cover western Washington, but
  its *demonstration* is not a western Washington river. Note both *predate* Bulletin 17C
  (England and others, 2018): SIR 2016–5118 states it "follows the methodology set by Bulletin 17B …
  except for the use of the Expected Moments Algorithm (EMA) and the Multiple Grubbs-Beck (MGB)
  low-outlier test", and Barth and others frame their analysis against "the Bulletin 17B framework".
  Neither has been revisited.
- **The Skagit historic peaks.** USGS wrote in October 2006 that 240,000 cfs was the best value and
  that "it would be improper to use a lesser value"; in 2007 USGS published 228,000 cfs and revised
  all five other historic peaks. The dispute is regulatory (it sets the USACE design flood and the
  FEMA flood insurance study) and is documented in a public exchange with a private citizen routed
  through a member of Congress. This is not settled science being reported; it is an adjudication.
- **Whether observed western Washington peak-flow trends are trends at all.** SIR 2016–5118 finds
  significant positive trends concentrated in western Washington, but also identifies **step changes
  around 1940–1950 and the late 1960s** and notes that Cohn & Lins (2005) long-term persistence
  inflates significance. My own computation through WY2025 (§3) shows that three of four significant
  full-record trends **become insignificant when restricted to 1970–2025**. NF Nooksack below Cascade Creek near Glacier (12205000) is
  the exception (τ = +0.362, p = 0.0001 post-1970) — and it drains Mount Baker, where sediment supply
  and channel aggradation are a competing explanation for rising *stage* and possibly for rating-derived
  *discharge* (INFERENCE; see the sediment discussion in `flood-genesis-mechanisms-2026-08-24.md` §6.3).

---

## 5. Western Washington specificity — what transfers and what does not

**Transfers well.**

- Bulletin 17C's *machinery* (EMA, interval data, perception thresholds, MGBT, weighted skew) is
  distribution-agnostic bookkeeping and applies anywhere.
- The **PNW regional skew of −0.07 (MSE 0.180)** — developed by B-WLS/B-GLS, the regionalisation 17C
  later recommended, though published two years before 17C — was developed specifically for
  ID/OR/WA/western MT from 290 gauges — this is a regionally correct parameter, not an import.
- Barth et al.'s AR-dominance finding is *strongest* in our region (>80 %, ~100 % at some sites), so
  the mixed-population critique transfers with extra force, not less.

**Transfers with reservations.**

- **Californian mixed-population results.** Barth et al. report up to 50 % of annual peaks flagged as
  PILFs in central/southern California. Western Washington has no comparable dry-year problem: our
  annual maxima are all genuine flood peaks. So the *low* end of the CA analysis does not transfer;
  the *tail* finding does.
- **Sierra Nevada rain/snow separation** (17C's worked example, from Crippen 1978): the Sierra splits
  cleanly into Nov–Mar rain floods and Apr–Jul snowmelt floods by elevation. Our version is weaker
  and differently shaped — at Skagit near Concrete the warm-season population is 18 % of peaks but
  **contributes nothing to the top 20**, so the two populations barely overlap in magnitude. A
  Sierra-style calendar split would satisfy 17C's "objective criterion" test only where the seasons
  really are different mechanisms — which 17C explicitly warns against assuming.
- **European and eastern-US non-stationarity results** (tropical-cyclone mixtures, ice jams,
  urbanisation-dominated records) are mechanistically different. Only the *methodological* lessons
  transfer.

**Does not transfer / is locally specific.**

- **Washington has no NOAA Atlas 14.** Design precipitation frequency for Washington rests on
  **NOAA Atlas 2 Volume 9 (1973)** for 1–24 h durations, **Technical Paper 49 (1964)** above 24 h, and
  **Arkell & Richards (1986)** below 1 h (FACT — NWS OWP, fetched today). Washington and Oregon are
  the only two CONUS states in that position; Idaho, Montana and Wyoming were updated in 2024 with
  Atlas 14 Vol 12. **Every design storm in Washington predates the entire modern flood record.**
  Atlas 15 Volume 1 will be the first update in 53 years, preliminary September 2026.
- **The regulated/unregulated split runs straight through our basin list.** Skagit (Ross/Diablo/Gorge
  + Baker), Green (Howard Hanson), White (Mud Mountain) and Cedar (Chester Morse) are regulated;
  Sauk, Snoqualmie main stem, Stillaguamish and Nooksack are not. Bulletin 17C applies to the second
  group and explicitly does not to the first. **The Sauk is the scientifically clean long record in
  the Skagit system** and is exactly where the platform should look for climate signal (INFERENCE).
- **Green River at Auburn's τ = −0.187 (p = 0.010)** is the clearest possible demonstration: a
  statistically significant *downward* trend in annual peaks that is a reservoir operating rule, not
  a climate. Any trend display that does not carry regulation class will publish this as a finding
  about the weather.
- **Compound tidal backwater at Mount Vernon and Ferndale** means the stage frequency curve and the
  discharge frequency curve at those points are different objects with different generating
  processes. See `flood-genesis-mechanisms-2026-08-24.md` §6.1–6.2 for the non-stationary rating; the
  statistical consequence is that a *stage*-frequency statement there is a joint river-tide statement
  and cannot be inherited from a discharge-frequency fit (INFERENCE).
- **The Skagit's upper tail is six numbers from before 1922, four of which were derived by extending
  a rating through a single 1923 indirect measurement**, and the 1815 value is a straight-line
  extrapolation to a stage 27 ft above the highest ever measured. Nowhere else in the platform's
  coverage does the 1 %-AEP estimate depend so heavily on so little.

---

## 6. What this means for Cascadia Papsukkal

### 6.1 The doctrine sentence that should exist and does not

`docs/HYDROLOGY.md` §13 lists what the platform will not claim. It does **not** mention recurrence
intervals, return periods, AEP or the 100-year flood — I grepped `HYDROLOGY.md` and
`DATA_DOCTRINE.md` for all of those terms and found **zero matches**. The prior research pass
(`flood-genesis-mechanisms-2026-08-24.md` §6.5) asserts "the platform already declines to compute
return periods". **It does not decline in writing.** Proposed §13 addition:

> - A recurrence interval, return period or annual exceedance probability for any reach. Frequency
>   estimates are fitted statistics with a record period, a method version, a regulation status and a
>   confidence interval, not properties of a river. Where an authority publishes one, the platform may
>   display it as a **cited external estimate with its interval and its vintage**, never as a category,
>   a colour, a threshold, or a sentence containing the phrase "N-year flood".

### 6.2 `source_kind` has no slot for a frequency estimate

`DATA_DOCTRINE.md` §2's closed taxonomy is OBSERVED / OFFICIAL_FORECAST / MODELED / DERIVED /
EXPERIMENTAL / CONFIGURED / UNKNOWN. A published 1 % AEP quantile is none of these. It is not
OBSERVED (nothing measured it), not OFFICIAL_FORECAST (it forecasts nothing — it has no
`valid_time`), not MODELED in the sense the doctrine means (no dynamical model), not DERIVED (we
didn't compute it), and calling it CONFIGURED would be a lie about its provenance.

Two options, in preference order:

1. **Do not ingest frequency estimates at all** in P3–P5. Simplest, and defensible.
2. If they are ever needed (§6.5), add a **`FREQUENCY_ESTIMATE`** kind with mandatory fields the
   other kinds do not have: `record_begin_year`, `record_end_year`, `n_systematic_peaks`,
   `n_historic_peaks`, `method` (e.g. `EMA-MGBT/LP3`), `method_version`, `regional_skew` + its MSE,
   `regulation_status`, `ci_lower`, `ci_upper`, `ci_level`, `publication`, `superseded_by`. A
   frequency estimate without a confidence interval must be refused at parse time.

### 6.3 What the platform can honestly say instead of a return period

All three of these are computable now from data the platform already holds, and none of them is a
frequency claim:

- **Rank in record.** *"This crest is the Nth highest stage in M years of record at this gauge
  (WY a–b), and the Kth highest discharge."* Rank is an observation, carries no distributional
  assumption, and is exactly what NWPS `flood.crests.historic` already provides — MVEW1 returns **93**
  historic crests (fetched 2026-08-24). Requires: the record period stated, and separate rank statements for stage and
  discharge (they differ at Mount Vernon — record stage 37.73 ft on ~133,000 cfs vs 152,000 cfs in
  1990 at a lower stage).
- **Distance to the nearest observed analogue.** "The closest observed event by peak discharge is
  2003-10-21 (135,000 cfs); its crest stage was 36.19 ft."
- **Day-of-year percentile against a stated climatology** — which `susceptibility.py` already
  computes (`streamflow_doy_percentile`, `method:streamflow-doy-climatology@1.0.0`, carrying
  `begin_year`/`end_year`). This is honest **because it is an empirical rank against a named record**,
  not an extrapolated tail.

### 6.4 Corrections the frequency literature forces on existing modules

- **`susceptibility.py` — percentile provenance must carry regulation class.** A day-of-year flow
  percentile at Green near Auburn or Skagit at Mount Vernon is a percentile of *managed* flow.
  Ninety-nine percent of the Mount Vernon peak record carries USGS code 6. The percentile is still
  useful, but the driver text and the `ProvenanceRef` should say "against the recorded, regulated
  flow climatology at this gauge (WY a–b)". Cheap, and it prevents a reader inferring a natural-basin
  statement. **P1.**
- **Ingest USGS `peak_cd` and `gage_ht_cd` verbatim.** The peak file already tells you the record is
  regulated (6), estimated (2), historic (7), affected to unknown degree (5), snowmelt-generated (9),
  urbanised (C), revised (R), and that the date is uncertain to the day (Bd) or month (Bm). These map
  directly onto the existing `quality` flag vocabulary in `DATA_DOCTRINE.md` §1 and are pure
  provenance gold. Note the negative result: code 9 appears **3 times across ~900 western WA peaks**,
  so it is a quality flag, not a mixed-population separator (3 occurrences in the 900 peaks across the ten western Washington records checked). **P1.**
- **Sentinel handling must cover NWPS crest and threshold payloads.** The MVEW1 `flood.categories`
  payload returns `flow: -9999` for all four categories (stage-defined point) and AUBW1 returns
  `stage: -9999` (flow-defined point); CRNW1's oldest historic crest carries `stage: -0.999`. These
  are exactly the provider sentinels `DATA_DOCTRINE.md` §4 requires be parsed to `quality=sentinel`.
  Verify the NWPS adapter treats `-9999` and `-0.999` as sentinels and not as values. **P0 — a
  `-0.999 ft` crest rendered as a stage is a visible falsehood.**
- **Annual peaks lag the event by up to two years, and this is a knowledge-time fact.** As of
  2026-08-24 the USGS peak file for Skagit near Mount Vernon ends at WY2025 (peak 2024-12-18). The
  **December 2025 record crest is not in the annual peak series and will not be until WY2026 closes
  and USGS approves the value.** NWPS already carries it as a preliminary crest (37.73 ft / 132,717
  cfs, `preliminary: "P"`). Any "record" claim must name which series it is a record in. **P1.**
- **Cross-source disagreement on crest values is already visible and should be reported, not
  reconciled.** NWPS gives the 2021-11-16 Mount Vernon crest as 37.32 ft / 122,596 cfs; the USGS
  peak file gives 36.99 ft / 127,000 cfs for the same event. `DATA_DOCTRINE.md` §10 says disagreement
  is information — this is a concrete instance for the historic-crest panel. **P1.**

### 6.5 New data sources this domain justifies (and one it does not)

| Source | Why | Buildable now |
|---|---|---|
| **USGS NWIS peak file** (`nwis.waterdata.usgs.gov/nwis/peak?...&format=rdb`) per gauge | rank-in-record, historic crest provenance, qualification codes, the honest alternative to a return period | yes — plain RDB, no auth, one request per site |
| **USGS SIR 2016–5118 table 8** (`sir20165118_table8.xlsx`) | the only published AEP estimates with 95 % CIs for Washington computed with EMA + MGBT + a B-GLS regional skew (17C's machinery, though the report itself is written against Bulletin 17B and predates 17C); note it **excludes regulated streamgages by design** — 12194000 and 12200500 are absent from table 8; useful as a labelled external reference and as the source of the CI-width honesty statement | yes — static xlsx, but ingest only if §6.2 option 2 is adopted |
| **NOAA Atlas 15 Volume 1 (CONUS preliminary, Sept 2026)** | will supersede Atlas 2 (1973) as Washington's precipitation-frequency basis; the platform's first chance to hold a non-stationary frequency product with a stated vintage | **not yet — watch item, ~1 month out.** Do not design against the pilot format |
| **NOAA Atlas 2 Vol 9 (1973) / TP-49 (1964)** | the *current* standard, for context only | no — do not ingest; a 1973 design storm has no operational use here |
| **A Cascade-computed FFA** | — | **no. Do not build.** 17C excludes regulated basins, provides no evaluated mixed-population method, and the platform has no calibrated basis to deviate. This would be a fabricated certainty of exactly the kind the doctrine exists to prevent |

### 6.6 Contract implications

- `BasinVisualizationState` / `SceneSummary`: **no field should ever carry a recurrence interval.**
  If a `historic_crest` block is added, it carries `rank`, `record_begin_year`, `record_end_year`,
  `basis` (stage|flow), `datum`, `preliminary` and `source_id` — and never a derived probability.
- The existing rule in `docs/DATA_DOCTRINE.md` §9(a) — probabilities may be displayed when "issued by
  an authority" — is **too permissive as written for frequency estimates**. A USGS 1 % AEP is
  authority-issued, but it is a fitted statistic about the *past*, not a probability statement about
  a *forecast*. §9 should distinguish *forecast probabilities* (authority-issued, time-stamped,
  verifiable) from *frequency estimates* (authority-issued, vintage-stamped, not verifiable on any
  operational horizon), and permit the second only with its CI and record period rendered beside it.
- **Copy rules** (`DATA_DOCTRINE.md` §12) should add: the strings "100-year", "N-year flood",
  "return period" and "recurrence interval" are prohibited in generated copy. If an official product
  the platform quotes verbatim uses them, they are inside a quotation with the issuer named.

---

## 7. What this domain contradicts or qualifies in the current repo doctrine

| # | Repo claim / state | Verdict | Basis |
|---|---|---|---|
| 1 | `flood-genesis-mechanisms-2026-08-24.md` §6.5: "The platform already declines to compute return periods" | **False as stated.** No such rule exists in `HYDROLOGY.md` or `DATA_DOCTRINE.md`; grep for "return period", "recurrence", "AEP", "100-year", "Bulletin", "Atlas 1" returns nothing in either file | grep of the two doctrine files, 2026-08-24 |
| 2 | `DATA_DOCTRINE.md` §2, closed `source_kind` taxonomy | **Incomplete for this domain.** A published frequency quantile fits no existing kind; see §6.2 | Bulletin 17C; SIR 2016–5118 table 8 structure |
| 3 | `DATA_DOCTRINE.md` §9(c): probabilities allowed if "(a) issued by an authority" | **Too permissive.** Admits a 1 %-AEP quantile with a factor-1.66 CI as if it were an issued forecast probability | §3 CI computation; §6.6 |
| 4 | `HYDROLOGY.md` §5: "Thresholds are official NWS categories… Reach-level thresholds without an official forecast point are a later, clearly-labeled derivation" | **Confirmed and strengthened.** NWPS carries *no* recurrence field at any of MVEW1/CONW1/CRNW1/AUBW1, so there is no official recurrence object to inherit even if the platform wanted one. Also confirms the flow/stage split (AUBW1 flow-defined, others stage-defined) with `-9999` sentinels on the unused basis | NWPS v1 API, fetched 2026-08-24 |
| 5 | `HYDROLOGY.md` §2: "regulation_class (natural / partially regulated / regulated) is a domain attribute that changes how every downstream quantity is interpreted" | **Confirmed, and now load-bearing for statistics too.** Bulletin 17C's scope exclusion makes regulation_class a *scope* gate on FFA, not only an interpretive one. (Not a *legal* one: 17C says federal agencies are "requested to use these Guidelines" and provides an explicit deviation clause — "deviations must be supported by appropriate study and accompanied by a comparison of results using the recommended procedures", p. 4. And USGS code 6 is a binary "affected by regulation or diversion" flag carrying no magnitude threshold, so code-6 density evidences regulation but does not by itself establish 17C's predicate of flows "appreciably altered".) Green at Auburn's significant negative τ is the demonstration | Bulletin 17C p. 2; τ computed §3 |
| 6 | `HYDROLOGY.md` §12: Event Zero record crest at Mount Vernon | **Qualified.** Correct as a *stage* record and correctly separated from flow in the existing text — but the December 2025 peak is **not yet in the USGS annual peak series** (which ends WY2025) and is `preliminary: "P"` in NWPS. "Record" must name its series and its approval state | NWIS peak file 12200500; NWPS MVEW1 |
| 7 | `HYDROLOGY.md` §8: percentiles "labeled as derived from the product's own reanalysis with the period stated" | **Confirmed, and one field short.** The period is necessary but not sufficient at a regulated gauge; regulation status belongs in the same label | `susceptibility.py`; peak_cd census §3 |
| 8 | `flood-genesis-mechanisms-2026-08-24.md` §6.7: "NOAA is replacing Atlas 14 with NOAA Atlas 15" | **Qualified — the premise is wrong for Washington.** Washington was never in Atlas 14. It is on **NOAA Atlas 2 Vol 9 (1973)**. Atlas 15 will be the first update in 53 years, not an incremental replacement | NWS OWP current-PF-documents page, fetched 2026-08-24 |
| 9 | `flood-genesis-mechanisms-2026-08-24.md` §6.8: the 1921 peak "probably was 6.2 percent lower" but "USGS did not officially change it" | **Superseded.** USGS *did* change it, in SIR 2007-5159 (2007), to **228,000 cfs (−5.0 %)**, and revised 1815, 1856, 1897, 1909 and 1917 at the same time. The current NWIS peak file for 12194000 carries the revised values (510,000 / 340,000 / 265,000 / 245,000 / 210,000 / 228,000). The repo's account describes the pre-2007 state | SIR 2007-5159 table 1; NWIS peak file 12194000 |
| 10 | `HYDROLOGY.md` §9: "trend never comes from the two endpoints of a response window" | **Contradicted by the implementation** (noticed in passing, adjacent to this domain): `trend.rate_of_rise` computes `(pts[-1] - pts[0]) / span_h` — exactly the two endpoints. Either the doctrine sentence or the method needs to change | `packages/hydrology/src/cascade_hydrology/trend.py` |

---

## 8. Open questions

1. **Barth et al. (2017) vs USGS SIR 2016–5118 on mixed populations in Washington.** One says the
   western-US annual maximum series is a mixture whose tail is AR-dominated; the other inspected
   Washington's frequency plots and found no site needing mixed-population treatment. Which is right
   for the Skagit, Snoqualmie and Nooksack? Resolvable by re-running EMA on the unregulated gauges
   with an AR catalogue as the separation criterion — but that is a research project, not a platform
   feature.
2. **Can an AR catalogue supply the "objective and hydrologically meaningful criterion" 17C
   requires?** USGS peak codes cannot (code 9 appears 3 times in ~900 peaks). A published AR detection
   catalogue could, but its own uncertainty then enters the frequency estimate, and 17C forbids using
   the regional skew unless it too was developed for the separated populations. (Census: code 9 occurs
   3 times in the 900 annual peaks across the ten Washington records checked.)
3. **Is NF Nooksack below Cascade Creek near Glacier's (12205000) persistent post-1970 trend (τ = +0.362, p = 0.0001) hydrologic or
   hydraulic?** Rising rating-derived discharge on a river aggrading from Mount Baker sediment is
   ambiguous. Needs the USGS station analysis and rating-shift history, which is not in the peak file.
4. **What is the stage-frequency object at a tidally influenced point?** Mount Vernon and Ferndale
   thresholds are in stage; the generating process for stage there is joint river+tide+surge. Nobody
   in the fetched literature computes a joint stage-frequency curve for these reaches.
5. **Does NOAA Atlas 15 Volume 1 for CONUS actually land in September 2026, and in what format?**
   The NOAA page is internally inconsistent about 2026 vs 2027 publication and the project has already
   slipped once. Watch item with a concrete date.
6. **What confidence interval, if any, will Atlas 15 publish?** Atlas 14 published 90 % CIs on
   precipitation frequency estimates. If Atlas 15 Volume 1 does not, the platform must not ingest a
   non-stationary point estimate without one.
7. **Do the 1815 and 1856 Skagit peaks have independent physical evidence** (tree scars, deposits,
   accounts) that would give them defensible *perception thresholds* under 17C, or do they exist only
   as points on an extrapolated rating? SIR 2007-5159 documents only the rating extension.
8. **Not fetched, and worth fetching later:** Serinaldi & Kilsby (2015), Milly et al. (2008),
   Montanari & Koutsoyiannis (2014), Cohn & Lins (2005). All were paywalled or 403 today; each was
   confirmed to exist with the stated authors, journal, volume and pages, but the claims sourced from
   them here are labelled INFERENCE. (Luke et al. 2017 *was* retrieved on the adversarial re-check and
   is now FACT-grade — see §4.)

---

## 9. Sources

**Fetched and read (FACT-grade).**

- [USGS Techniques and Methods 4-B5 — Guidelines for Determining Flood Flow Frequency, Bulletin 17C, ver. 1.1 (May 2019)](https://doi.org/10.3133/tm4B5) — PDF at `pubs.usgs.gov/tm/04/b05/tm4b5.pdf`, 168 p., text-extracted.
- [USGS SIR 2016–5118 — Magnitude, Frequency, and Trends of Floods at Gaged and Ungaged Sites in Washington, Based on Data through Water Year 2014, ver. 1.2 (Nov 2017)](https://pubs.usgs.gov/sir/2016/5118/sir20165118.pdf) — Mastin, Konrad, Veilleux & Tecca; and its [table 8 workbook](https://pubs.usgs.gov/sir/2016/5118/sir20165118_table8.xlsx).
- [USGS SIR 2007–5159 — Re-evaluation of the 1921 Peak Discharge at Skagit River near Concrete, Washington](https://pubs.usgs.gov/sir/2007/5159/pdf/sir20075159.pdf).
- [USGS letter, 2006-10-26, reply to the Kunzler whitepaper on the Skagit historic peaks](https://www.skagitriverhistory.com/USGS%20Docs/2006-10-26%20USGS%20Reply%20to%20Whitepaper.pdf) — third-party host of a USGS document; content is a signed USGS letter with enclosure.
- [USGS SIR 2005–5029 — Verification of 1921 Peak Discharge at Skagit River near Concrete, Washington, Using 2003 Peak-Discharge Data](https://pubs.usgs.gov/sir/2005/5029/pdf/sir20055029.pdf) — Mastin & Kresch; PDF retrieved, text extraction partial.
- [NWS Office of Water Prediction — Current NWS Precipitation Frequency Documents](https://www.weather.gov/owp/hdsc_currentpf) — the state-by-duration table showing Washington on NOAA Atlas 2 Vol 9 (1973), TP-49 (1964) and Arkell & Richards (1986).
- [NOAA Atlas 15 Informational Page](https://water.noaa.gov/about/atlas15) — Volume 1/2 definitions, methodology summary, schedule.
- [NOAA news release, 2024-09-26 — Update to U.S. precipitation frequency standards now accounts for climate trends](https://www.noaa.gov/news-release/update-to-us-precipitation-frequency-standards-now-accounts-for-climate-trends).
- [Slater et al. 2021 — Nonstationary weather and water extremes: a review of methods for their detection, attribution, and management, HESS 25, 3897–3935](https://hess.copernicus.org/articles/25/3897/2021/).
- [Barth, Villarini, Nayak & White 2017 — Mixed populations and annual flood frequency estimates in the western United States: The role of atmospheric rivers, WRR 53:257–269](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1002/2016WR019064) — fetched once; a second fetch returned 403, so the AR-fraction and RPD numbers above come from the first retrieval.
- [Dell'Aira, Cancelliere & Meier 2025 — Generalizations of Langbein's Formula under Non-Stationarity, Mixed Populations, and Over- or Under-Dispersion in the Number of Exceedances, arXiv:2509.23546](https://arxiv.org/abs/2509.23546).
- [USGS Water Science School — The 100-Year Flood](https://www.usgs.gov/special-topics/water-science-school/science/100-year-flood).
- [Luke, A., Vrugt, J.A., AghaKouchak, A., Matthew, R. & Sanders, B.F. 2017 — Predicting nonstationary flood frequencies: Evidence supports an updated stationarity thesis in the United States, WRR 53(7):5469–5494](https://escholarship.org/content/qt1cg4j6p6/qt1cg4j6p6.pdf) — Wiley returned 403; the eScholarship PDF was retrieved and text-extracted on the adversarial re-check, 2026-08-24.
- [UW Climate Impacts Group — Study Review: Trends in Flooding for Washington State (2024-10-15)](https://climate.uw.edu/2024/10/15/study-review-trends-in-flooding-for-washington-state/).
- [ASFPM — After Brief Delay, NOAA's Atlas 15 Project Moves Ahead](https://www.floods.org/news-views/policy-matters/after-brief-delay-noaas-atlas-15-project-moves-ahead/).

**Primary datasets fetched and computed on.**

- USGS NWIS annual peak files, RDB format, retrieved 2026-08-24:
  `https://nwis.waterdata.usgs.gov/nwis/peak?site_no={12194000,12200500,12149000,12134500,12167000,12189500,12144500,12205000,12113000,12108500}&agency_cd=USGS&format=rdb`
- NOAA NWPS v1 gauge API, retrieved 2026-08-24:
  `https://api.water.noaa.gov/nwps/v1/gauges/{MVEW1,CONW1,CRNW1,AUBW1}`

**Not independently fetched — claims sourced from them are labelled INFERENCE.**

- Serinaldi, F. & Kilsby, C.G. (2015), *Stationarity is undead: Uncertainty dominates the distribution of extremes*, Advances in Water Resources 77:17–36 — [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0309170815000020) returned 403.
- Milly, P.C.D. et al. (2008), *Stationarity is dead: whither water management?*, Science 319:573–574.
- Montanari, A. & Koutsoyiannis, D. (2014), *Modeling and mitigating natural hazards: Stationarity is immortal!*, WRR 50:9748–9756.
- Cohn, T.A. & Lins, H.F. (2005), *Nature's style: naturally trendy*, GRL 32:L23402 — cited within SIR 2016–5118, which I did fetch.
- Cohn et al. (1997, 2001, 2013), Veilleux et al. (2011), Griffis & Stedinger (2007), Crippen (1978), Murphy (2001), Asquith (2001), Kubik (1990), Novak (1985) — all cited within Bulletin 17C or SIR 2007-5159, which I did fetch; the primary papers were not retrieved.
