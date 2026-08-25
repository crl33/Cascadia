# Compound and coastal flooding in Puget Sound deltas

*Corpus entry, 2026-08-24. Part of the Cascadia Papsukkal flood-science corpus.*

*Label convention (as `docs/DATA_SOURCES.md`): **FACT** = read on a page I fetched, or computed by me
from a primary dataset I fetched (source and query given); **INFERENCE** = reasoned from cited facts,
not itself read anywhere; **ASSUMPTION** = a working simplification; **OPEN QUESTION** = unresolved.
Every original computation in this file was run on 2026-08-24 against live NOAA CO-OPS and USGS
endpoints; the queries are reproduced so they can be re-run. Nothing in the repository was modified
except this file. Web search quota was exhausted partway through; later sourcing is by direct fetch
and by primary-data computation, and where a paper could not be reached that is stated.*

---

## 1. Headline

**Compound river–coastal flooding is a real, statistically demonstrable hazard in the Puget Sound
deltas — and it is not what happened in December 2025. All three of Event Zero's record crests were
set at or near *low* water with a modest surge, so the platform's defining event contains almost none
of the compound signal. The compound tail is therefore unrealised, unmodelled, and invisible in the
repo's calibration set. Meanwhile the platform's own forecast points differ by a factor of ~50 in how
tidal they are — Snohomish at Snohomish is ~83 % a tide gauge, Skagit at Mount Vernon is ~1 % — and
the doctrine currently treats their stage records as the same kind of number.**

> **Adversarial review, 2026-08-24.** §3.1–§3.5 were independently re-run against the same endpoints
> and reproduce closely (matched-cycle count 21,165 vs 21,166; every §3.2 percentile to 3 dp; SNAW1 raw
> range 4.89–17.16 ft exactly; §3.1 sample sizes 3607/3597/3607 exactly; §3.4 backwater n = 3,316 and
> n = 171 exactly). Every literature citation in §9 was checked against Crossref/DataCite and **all
> exist exactly as described, with author lists, venues, volumes and years correct — no fabrication.**
> Six numeric errors were found and are corrected in place, each marked: the Event Zero maximum skew
> surge and crest-cycle skew surge (§1, §3.5), the Miller et al. 2018 0.1 %-exceedance SLR figure
> (§3.6), the Montillet NW-Olympic uplift rate (§2.8, §4), the BMTW1 "29 days stale" finding (§3.8,
> §6.3 — refuted; it was an array-ordering mistake) and the Bremerton NOS-vs-NWS threshold example
> (§3.7, §8). Two magnitude caveats were added, at §2.2 (spring–neap confound in the SNAW1 tidal-range
> collapse) and §3.4 (the high-flow backwater test is underpowered, not null). Note also that the §3.1
> p-values assume independent daily samples: winter ln(Q) has lag-1 autocorrelation 0.91 and daily skew
> surge 0.70, giving an effective n of ~800 rather than 3,607. The Skagit ρ = +0.31 then carries
> t ≈ 9 (p ≈ 10⁻¹⁹), not p = 3×10⁻⁸¹. The dependence is real; **do not quote the printed p-values.**

Three findings carry that headline:

1. **The dependence is real and measurable here.** Over 30 winters (NDJF 1996–2025) I find Spearman
   ρ = **+0.31 (Skagit at Mount Vernon)**, **+0.39 (Nooksack at Ferndale)** and **+0.30 (Snohomish
   near Monroe)** between daily discharge and Seattle skew surge at a one-day lead, all p < 10⁻⁷⁰,
   and robust to de-seasonalising. Conditional on Q ≥ p95, a p90 skew surge is **1.9–2.5×** more
   likely than under independence. (§3, computed)
2. **December 2025 sampled the benign corner of the joint distribution.** The record Skagit crest
   (37.73 ft, 2025-12-12 08:15Z) coincided with a Seattle water level of **6.56 ft MLLW — 4.80 ft
   *below* MHHW**. The record Snohomish crest (34.45 ft, 2025-12-12 01:35Z) coincided with **4.72 ft
   MLLW, 6.64 ft below MHHW**. The largest skew surge on any tidal cycle in the whole AR sequence was
   **+1.17 ft** (+0.83 ft if only higher-high cycles are counted), and −**0.03 ft** on the tidal cycle
   containing the Mount Vernon crest. (§3, computed; corrected 2026-08-24 in adversarial review — the
   original §3.5 figures matched only higher-high waters, inconsistent with §3.2's per-cycle method.)
3. **The gauges are not interchangeable.** Tidal-band transmission at low flow: Snohomish at
   Snohomish **0.83 ft per ft of Seattle tide (r = 0.94)**; Nooksack at Ferndale **0.019 ft/ft**;
   Skagit at Mount Vernon **0.010 ft/ft**. `HYDROLOGY.md` §2 flags Ferndale as tidally influenced and
   says nothing about Snohomish, which is the one that actually is. (§3, §7)

---

## 2. Mechanisms (the physics, stated properly)

### 2.1 What "compound" means, formally

Zscheischler et al. (2020, *Nature Reviews Earth & Environment*) define compound weather and climate
events as "combinations of multiple climate drivers and/or hazards that contribute to societal or
environmental risk", and give a four-way typology: **preconditioned**, **multivariate**, **temporally
compounding**, and **spatially compounding** (FACT — abstract read via search summary; the paper
itself was not fetched, paywall). River-plus-coastal flooding in a delta is the **multivariate** case:
two drivers, one impact. Rain-on-saturated-soil (the repo's Event Zero) is the **preconditioned**
case. An AR family is the **temporally compounding** case.

The NHESS decadal review (Bevacqua-adjacent community, 2025, open access) counts **366 papers
2012–2022**, growing ~**60 %/yr**, of which **72 % are multivariate**, 12 % temporally compounding,
4 % spatially compounding, 3 % preconditioned (FACT — fetched). So the sub-literature this domain sits
in is the largest and best-developed one, and the *preconditioned* case the repo already models is the
least studied — a note in the repo's favour.

The operational consequence that matters here: **a compound event is defined by its impact, not by its
drivers.** Two drivers that never co-occur are not compound; two drivers that co-occur but whose
combination is no worse than the larger alone are not compound either. The test is whether the joint
occurrence produces an impact neither would.

### 2.2 Total water level decomposition

Spicer et al. (2025, *Earth's Future*, PNNL) write the decomposition that this platform should adopt
verbatim (FACT — fetched full text via OSTI):

```
TWL = T + S + R + TSI + SRI + TRI + datum                                     (Spicer et al. eq. 1)

T   = astronomical tide
S   = storm surge (subtidal meteorological residual: wind setup + inverse barometer + remote forcing)
R   = river-induced water level
TSI = tide–surge interaction        (nonlinear)
SRI = surge–river interaction       (nonlinear)
TRI = tide–river interaction        (nonlinear)
```

The three nonlinear terms are not corrections. In the Duwamish they are **first-order**: TSI is
+10 % of TWL downstream and is what lifts a king tide from *no flooding* to *major flooding*; SRI and
TRI are **negative**, reaching **−17 % and −10 % at RK15 and −40 % (SRI) by RK20**, together reducing
upstream water levels by **up to 50 %** relative to a linear sum (FACT — Spicer et al. 2025). Anyone
who adds tide + surge + river arithmetically will over-predict upstream and under-predict downstream.

I observed TRI directly at Snohomish during Event Zero: the daily stage range at SNAW1 collapsed from
**10.51 ft on 2025-12-09** to **1.51 ft on 2025-12-12** as the flood wave arrived — the river's own
friction and slope drowning the tidal oscillation (FACT — computed from USGS OGC `continuous`,
12200500/12155500 series; §3). **Caveat added 2026-08-24 in adversarial review: part of that collapse
is astronomical, not fluvial.** Seattle's own observed daily range fell over the same days from
14.19 ft (12-09) to 8.99 ft (12-12) — a spring-to-neap reduction of 37 % (FACT — computed, CO-OPS
`water_level` 9447130). Scaling SNAW1's 12-09 range by that factor predicts ~6.7 ft on 12-12 against
1.51 ft observed, so the *river-attributable* damping is a factor of ~4.4, not ~7. The conclusion is
unchanged in kind and still large; the magnitude must not be quoted without this correction. Note also
that tidal damping in rivers at high flow is a classical result (Godin; Jay), not a finding original to
Spicer et al. — what Spicer et al. add is that the term is *first-order in the water-level budget*.

### 2.3 Skew surge versus non-tidal residual

- **Non-tidal residual (NTR)** = observed − predicted, at every timestep. It contains tide–surge
  interaction and, worse, *timing* error: a tide that arrives 20 minutes early produces a large
  spurious NTR on the rising limb.
- **Skew surge** = (maximum observed water level in a tidal cycle) − (maximum predicted water level in
  that cycle), *regardless of whether the two maxima are simultaneous*. One value per tidal cycle
  (FACT — NTSLF definition; Williams et al. 2016 *GRL*).

Williams et al. (2016) showed across UK, US, Netherlands and Ireland gauges that **the magnitude of
high water exerts no influence on the size of the most extreme skew surges** — i.e. tide and skew
surge are statistically independent, which is what licenses the multiply-the-marginals form of the
Joint Probability Method (FACT — search summary; paper not fetched, paywall). Santamaria-Aguilar &
Vafeidis (2018, *JGR Oceans*) contest this for **mixed semidiurnal** regimes — which is exactly Puget
Sound's regime (FACT — title and framing read; full text not fetched).

**I tested it for Seattle.** Over 21,166 matched tidal cycles 1996–2025, Spearman ρ(predicted high
water, skew surge) = **−0.094** overall and **−0.077** in NDJF (FACT — computed). Near-independence,
with a small *negative* tendency — consistent with tide–surge interaction damping surges on the
biggest tides, and consistent with the direction Santamaria-Aguilar & Vafeidis warn about, but too
weak to break the independence assumption. **Use skew surge, not NTR.** A methodological trap I hit
and you will too: computing skew surge per *calendar day* rather than per *tidal cycle* produced
spurious +3.5 to +4.6 ft "surges", all in May–June, because Seattle's diurnal inequality puts the
higher-high near local midnight in late spring and the day boundary splits the pair. Per-cycle
matching (±3 h around each predicted high water) gives a max of **+2.58 ft** over 30 years.

### 2.4 Why discharge and surge are dependent here — the meteorology

The dependence is not coincidence and it is not a statistical artifact of the seasonal cycle (I
de-seasonalised; §3). One synoptic object produces both:

- A landfalling **atmospheric river** embedded in an extratropical cyclone brings a deep surface low
  (inverse barometer), strong **onshore/southwesterly** wind (wind setup along the Strait of Juan de
  Fuca and up the Sound), and the moisture flux that orographic ascent converts to basin rainfall.
- Ward et al. (2018, *ERL*) found this signature explicitly in their composite atmospheric analysis:
  at dependent stations, "elevated precipitable water content" accompanies joint discharge/surge
  events, "attributable to steep topography and orographic rainfall effects", and they name **Neah
  Bay, Washington** as one of the analysed sites (FACT — fetched).
- The **lag structure** follows from the routing: the surge peaks with the front, the river peaks
  hours to a day later. My optimum is **lag −1 day** (surge leads discharge) for all three basins,
  with the correlation still positive at −3 days and decaying by +2 days (FACT — computed, §3). This
  is why a zero-lag dependence test understates the hazard, exactly as Ward et al. found globally
  (22 % → 56 % of stations significant when lags −5…+5 d are allowed).

### 2.5 What produces the surge in Puget Sound specifically

Four contributions, in rough order of size for this basin:

1. **Inverse barometer.** The standard static response is ≈ **1.0 cm per hPa** of pressure drop. The
   Skagit Climate Science Consortium states "**1.9 cm for every 1 mb**" (FACT — that page says this),
   which is roughly **twice** the classical value. **CONTESTED / probably wrong as a pure IB
   coefficient** — it may be an empirical regression that has absorbed the wind setup correlated with
   low pressure. Do not encode 1.9 cm/mb as physics; if a pressure→sea-level term is ever needed, use
   1.0 cm/hPa and label the rest as wind setup (INFERENCE).
2. **Local wind setup.** Fetch-limited within the Sound; Miller et al. (2019) model most of Puget
   Sound at an event **maximum surge of 2.5–3.0 ft**, with a few embayments (southern Hood Canal,
   Bellingham and Samish Bays) marginally exceeding 3.0 ft and Sinclair/Dyes Inlets, Liberty Bay and
   Hammersley Inlet **up to 1 ft higher** than the tide gauges suggest (FACT — fetched PDF, Box 3).
3. **Remote forcing.** Grossman et al. (2023, *Water* 15, 4167) argue that **remote sea level
   anomalies must be included** in Salish Sea hydrodynamic simulations to reproduce extreme water
   levels — coastally trapped waves and offshore steric signals propagate in through the Strait of
   Juan de Fuca (FACT — title and framing; MDPI returned HTTP 403 to both WebFetch and a
   browser-UA curl, so the numbers were **not independently fetched**).
4. **Steric / ENSO–PDO background.** Strong El Niño raised PNW coastal sea level by "almost one foot"
   in 1982-83 and 1997-98, and ~6 inches in 2015-16, per Ian Miller (Washington Sea Grant) (FACT —
   KUOW 2026-07-29, fetched). CIG's Figure A.4 notes the **highest observed water level at many
   Washington gauges dates to the 1982–83 winter**, the strongest El Niño on record for the state
   (FACT — fetched).

### 2.6 The seasonal cycle stacks the deck

Everything lines up in December. I computed the Seattle monthly climatology directly (CO-OPS
`monthly_mean`, 1999–2008, station 9447130):

| | Jan | May | Sep | Dec | winter−summer |
|---|---|---|---|---|---|
| monthly MSL (ft MLLW) | 6.972 | 6.445 | 6.475 | 6.938 | **+0.38 ft** (Nov–Jan vs Jun–Aug) |
| monthly MHHW (ft MLLW) | 11.955 | 11.311 | 10.906 | 12.047 | **+0.60 ft** |

Annual range of monthly-mean MSL = **0.527 ft (16.1 cm)** (FACT — computed). Of the **50 highest
observed high waters at Seattle 1996–2025, 24 fall in December and 18 in January** — 84 % in DJ
(FACT — computed). This is the quantitative content of the Skagit Climate Science Consortium's
sentence that "the highest tides of the year coincide with the seasons of strongest storms and the
biggest river floods" (FACT — fetched).

The **18.6-year lunar nodal cycle** modulates tidal range, raising Seattle high tides by up to ~0.6 ft
at the peak of the cycle, without changing mean sea level (FACT — Miller et al. 2019, Figure A.5).
Pickering et al. (2017) modelled 2.0 m of SLR and found tidal-range changes for Washington of "less
than a few inches", so **tides can be treated as stationary under SLR here** (FACT — Miller et al.
2019 summarising).

### 2.7 The dynamic tidal limit and backwater

The tidal limit of a river is not a fixed river mile. It moves upstream at low flow and downstream at
high flow, and there are two distinct limits:

- the **oscillatory** limit, where the semidiurnal/diurnal signal dies out (friction);
- the **backwater** limit, where the *mean* water level at the mouth still sets the downstream
  boundary condition for the water-surface profile.

The second extends much further upstream than the first, and it is the one that matters for flood
stage. Spicer et al. put the Duwamish tidal limit at **RK 20** and show tides comprising **~75 % of
TWL out to RK 14**, then falling as river terms climb from ~0 % to ~70 % between RK 10 and RK 20, with
tides crossing below river influence at **RK 18** (FACT — fetched).

### 2.8 Vertical land motion: the Skagit sinks while the Olympics rise

Relative sea level = absolute sea level − vertical land motion. In Cascadia the VLM field is
dominated by **interseismic locking on the megathrust**, which uplifts the outer coast and lets the
inland Sound subside, plus glacial-isostatic adjustment and local compaction/dewatering on deltas.
Montillet et al. (2018, *JGR Oceans*) report **+4.9 to −1.2 mm/yr** across 47 coastal GPS stations,
with Puget Sound "uniform subsidence at relatively slow rates of −0.1 to −0.3 mm/yr" and the northwest
Olympic Peninsula uplifting at **4.5 mm/yr** (FACT — abstract verbatim: "Uplift rates of 4.5 mm/yr persist
along the western Olympic Peninsula"; the full paper was **not fetched**). *Corrected 2026-08-24 in
adversarial review from ~3.5 mm/yr.* Note also that Montillet's central-Sound subsidence of
**−0.1 to −0.3 mm/yr** is ~5× smaller than the −1.5 mm/yr implied by Miller et al. (2018)'s Tacoma
−0.5 ft/century; Seattle's +2.08 mm/yr relative trend against ~1.7–1.9 mm/yr twentieth-century global
mean favours Montillet. **The magnitude of central Puget Sound subsidence is contested between this
file's own two sources** — do not encode either as settled.

The Miller et al. (2018) Washington assessment resolves VLM on a **0.1° grid (171 coastal locations)**
in **feet per century**, with Tacoma at **−0.5 ± 0.2 ft/century** (subsiding ≈ −1.5 mm/yr), Neah Bay
at **+1.1 ± 0.3 ft/century** (uplift ≈ +3.4 mm/yr), Taholah **+0.3 ± 0.5** (FACT — extracted from the
report PDF; the units are given as feet/century in Figure 3 and confirmed by arithmetic: relative
2100 central estimates 2.5 ft Tacoma, 1.0 ft Neah Bay, 1.7 ft Taholah against a 2.0 ft absolute
central estimate).

**The tide gauge records prove it independently.** CO-OPS published relative sea level trends
(fetched 2026-08-24, `dpapi/.../sealvltrends.json`):

| Station | Trend (in/decade) | mm/yr | Record |
|---|---|---|---|
| Seattle 9447130 | **+0.82 ± 0.03** | +2.08 | 1899-01 → 2025-12 |
| Port Townsend 9444900 | +0.72 ± 0.11 | +1.83 | 1972 → 2025 |
| Friday Harbor 9449880 | +0.47 ± 0.05 | +1.19 | 1934 → 2025 |
| Port Angeles 9444090 | +0.18 ± 0.13 | +0.46 | 1975 → 2025 |
| Toke Point 9440910 | +0.18 ± 0.13 | +0.46 | 1973 → 2025 |
| Cherry Point 9449424 | **−0.02 ± 0.11** | −0.05 | 1973 → 2025 |
| **Neah Bay 9443090** | **−0.67 ± 0.05** | **−1.70** | 1934 → 2025 |

(FACT — computed/fetched.) Neah Bay's relative sea level is **falling**. Cherry Point — 20 km from the
Nooksack delta — has been **flat for 52 years**. Seattle has risen 2.1 mm/yr. A single statewide SLR
number applied to all basins is wrong by ~4 mm/yr end to end.

The Skagit Climate Science Consortium states the delta is "sinking between 0 to 1 mm per year", which
"could shift projections upwards by up to 8 inches or more by 2100" (FACT — fetched).

### 2.9 The discrete term nobody models: co-seismic subsidence

A Cascadia megathrust rupture reverses the interseismic uplift instantaneously. Miller et al. (2018)
include **modelled land-level change for a 500-year-return-interval CSZ earthquake** in their
per-location relative-SLR tables — the only operational SLR product I found anywhere that does (FACT —
fetched). Dura/Nelson-lineage work published in *PNAS* (2025, "Increased flood exposure in the Pacific
Northwest following earthquake-driven subsidence and sea-level rise") quantifies **up to 2 m of sudden
coastal subsidence**, expanding the 1 % floodplain across 24 Cascadia estuaries by **90 km² (low,
~0.5 m), 160 km² (medium, ~1 m) or 300 km² (high, ~2 m)**, roughly **doubling** exposed residents,
structures and roads today and **more than tripling** it by 2100 when combined with SLR (FACT —
search summary of the abstract and USGS release; the PNAS text was **not independently fetched**).

For this platform the point is narrow and concrete: **a gauge datum is not permanent.** Every stage
threshold on a delta forecast point is defined on a benchmark that a subduction earthquake can move by
1–2 m in seconds.

---

## 3. Quantitative anchors

Everything marked **[computed]** was produced by me on 2026-08-24 from primary endpoints; the query is
given so it can be re-run. Everything else carries its source.

### 3.1 Original computations — dependence between river discharge and coastal water level

Winter (NDJF) daily USGS discharge vs Seattle (9447130) daily-maximum **skew surge**, 1996-01-01 to
2025-12-31. Skew surge computed per tidal cycle by matching each predicted high water to the maximum
observed water level within ±3 h. Sources: CO-OPS `high_low` (30 annual requests) and `predictions`
`interval=hilo`; USGS `waterservices/nwis/dv` `parameterCd=00060 statCd=00003`.

| Basin / gauge | n days | ρ at lag −1 d | p | de-seasonalised ρ | P(skew≥p90 \| Q≥p95) | ratio vs independence |
|---|---|---|---|---|---|---|
| Skagit at Mount Vernon (12200500) | 3607 | **+0.308** | 3.1×10⁻⁸¹ | +0.296 | 46/184 = 0.250 | **2.50×** |
| Nooksack at Ferndale (12213100) | 3597 | **+0.385** | 1.1×10⁻¹³⁰ | +0.376 | 40/182 = 0.220 | **2.20×** |
| Snohomish near Monroe (12150800) | 3607 | **+0.295** | 1.7×10⁻⁷⁴ | +0.288 | 34/183 = 0.186 | **1.86×** |

Lag structure, Skagit (ρ vs skew surge): L−3 **+0.284**, L−2 +0.298, **L−1 +0.308**, L0 +0.247,
L+1 +0.176, L+2 +0.121, L+3 +0.077. Negative lag = surge leads discharge. **[computed]**

Conditional on the rarer discharge threshold: P(skew ≥ p95 | Q ≥ p99) = 6/38 (Skagit, **3.16×**),
3/37 (Nooksack, 1.62×), 4/38 (Snohomish, 2.11×). Small samples; treat the ratios as order-of-magnitude.
**[computed]**

### 3.2 Original computations — Seattle skew surge climatology

21,166 matched tidal cycles, 1996–2025. **[computed]**

| Statistic | Value |
|---|---|
| mean | **+0.116 ft** (3.5 cm) |
| sd | 0.451 ft |
| p50 / p90 / p99 / p99.9 | +0.099 / **+0.668** / **+1.375** / +1.921 ft |
| maximum in 30 yr | **+2.576 ft** (2002-12-16 and 2006-12-15) |
| minimum | −1.605 ft |
| winter NDJF p90 / p99 / max | +0.885 / **+1.609** / +2.576 ft |
| summer JJA p90 / p99 / max | +0.482 / +0.803 / +1.209 ft |
| fraction of cycles ≥ 1.0 ft | 3.47 % |
| fraction ≥ 2.0 ft | 0.071 % |
| fraction ≥ 3.0 ft | **0 %** |
| ρ(predicted HW, skew surge) | −0.094 (all), −0.077 (NDJF) |

The 0 % above 3.0 ft is an independent confirmation of Miller et al. (2019): "storm surge is unlikely
to exceed … 3 ft in Puget Sound".

### 3.3 Original computations — Seattle extreme water levels and high-tide flooding

Top observed high waters 1996–2025, ft MLLW (MHHW = 11.36 ft MLLW): **[computed]**

| Rank | Time (LST) | Obs (ft MLLW) | vs MHHW | Predicted | Skew surge |
|---|---|---|---|---|---|
| 1 | 2022-12-27 08:42 | **15.12** | **+3.76** | 12.90 | **+2.22** |
| 2 | 2022-01-07 09:00 | 14.52 | +3.16 | 12.75 | +1.77 |
| 3 | 2012-12-17 08:06 | 14.48 | +3.12 | 12.93 | +1.55 |
| 4 | 2016-03-10 05:30 | 14.26 | +2.90 | 12.34 | +1.92 |
| 5 | 2003-01-03 06:12 | 14.21 | +2.85 | 12.78 | +1.43 |
| 6 | 2024-12-18 07:48 | 14.20 | +2.84 | 12.74 | +1.46 |

**Cross-validation of the whole chain:** Spicer et al. (2025) report the December 2022 Seattle event
as "a surge of 0.7 m coincid[ing] with a king tide, allowing a **3.9 m NAVD88** storm tide which broke
the previous high-water record". Converting with the CO-OPS datums (Seattle NAVD88 = 10.28 ft STND,
MLLW = 7.94 ft STND ⇒ NAVD88 = MLLW + 2.34 ft): 3.90 m = 12.80 ft NAVD88 = **15.14 ft MLLW** against
my computed **15.12 ft**; and their 0.7 m surge against my computed skew surge of **+2.22 ft =
0.677 m**. Independent agreement to 0.02 ft and 0.02 m. **[computed + FACT]**

Days per year with observed daily high water ≥ the NWS minor coastal-flood threshold (13.46 ft MLLW =
MHHW + 2.10 ft): **96 days in 30 years = 3.20 d/yr**; 1996–2010 mean 2.93 d/yr, 2011–2025 mean
**3.47 d/yr**. Worst years: 1998 (10), 2022 (10), 2010 (9), 2006 (8), 2016 (7). **[computed]**

### 3.4 Original computations — tidal transmission at the platform's delta forecast points

Method: 25-hour high-pass (centred moving-mean removal) applied to hourly river stage and to the
nearest CO-OPS observed water level, 2025-08-15 → 2025-09-30 (low flow; Skagit mean Q = 7,743 cfs);
lag swept −6 h … +18 h; slope = OLS regression of tidal-band stage on tidal-band sea level at the
best-correlating lag. Sources: USGS OGC API `collections/continuous` `parameter_code=00065`; CO-OPS
`hourly_height`. **[computed]**

| River gauge (NWS LID) | Tide station | stage tidal-band sd | sea tidal-band sd | best r | **slope (ft/ft)** | interpretation |
|---|---|---|---|---|---|---|
| Snohomish at Snohomish 12155500 (**SNAW1**) | Seattle 9447130 | **3.027 ft** | 3.411 ft | **0.936** | **0.831** | **fully tidal** |
| Nooksack at Ferndale 12213100 (**NKSW1**) | Cherry Point 9449424 | 0.162 ft | 2.771 ft | 0.329 | **0.019** | marginal |
| Skagit at Mount Vernon 12200500 (**MVEW1**) | Seattle 9447130 | 0.148 ft | 3.386 ft | 0.234 | **0.010** | marginal |

Raw stage at SNAW1 over that window swung **4.89 → 17.16 ft**, an ~11 ft diurnal oscillation at a
gauge whose NWS flood stage is 25 ft. Repeating the Mount Vernon analysis *during* the December 2025
flood gives slope 0.024 ft/ft, r = 0.165 — still ~2 %.

**Backwater test (null result).** Regressing Mount Vernon daily-mean stage on ln(daily-mean Q) plus
Seattle daily-mean sea level over 3,316 winter days 1996–2025: adding sea level moves R² from 0.8928
to 0.8929 and its coefficient is **−0.061 ± 0.034 ft/ft (t = −1.8, wrong sign)**. On the Q ≥ 40,000 cfs
subset (n = 171) the coefficient is +0.097 ± 0.093 (t = 1.0, not significant). **At daily resolution
there is no detectable Puget Sound backwater signal in 30 winters of Mount Vernon stage.**
**[computed]** — see §8 for the caveats that keep this from closing the question.

**Independent re-run, 2026-08-24 (adversarial review).** Same endpoints, same 3,316 winter days,
same n = 171 high-flow subset; R² 0.8928 → 0.8928. Full-sample sea-level coefficient
**−0.035 ± 0.036 (t = −1.0)**; **Q ≥ 40,000 cfs subset +0.174 ± 0.102 (t = +1.7, p ≈ 0.09)**. The
full-sample null replicates. The high-flow subset does **not** replicate as a clean null: the point
estimate is positive — the physically expected sign — and roughly 1.7 standard errors from zero.
**Read this as underpowered, not as evidence of absence.** Three reasons the test has little leverage
on the case that matters: (i) daily means smear a 12.4-hour signal; (ii) the ΔR² statistic is
uninformative for a marginal predictor in a model already at R² = 0.89 and should not be quoted as
evidence; (iii) per §3.5, a Skagit crest has essentially never coincided with a high tide plus a large
surge in this record, so the regression contains almost no observations of the regime the platform
cares about. §7.5 and §7.6 below must be read against this caveat.

### 3.5 Original computations — Event Zero's tidal context

| Quantity | Value | Source |
|---|---|---|
| Skagit MVEW1 crest | 37.73 ft, 2025-12-12 08:15Z | USGS OGC `continuous` **[computed]** |
| Seattle water level at that instant | **6.56 ft MLLW = MHHW − 4.80 ft** | CO-OPS `water_level` **[computed]** |
| Snohomish SNAW1 crest | 34.45 ft, 2025-12-12 01:35Z | USGS OGC **[computed]** |
| Seattle water level at that instant | **4.72 ft MLLW = MHHW − 6.64 ft** | **[computed]** |
| Largest skew surge, any cycle 2025-12-08…14 | **+1.17 ft** (predicted HW 2025-12-09 02:15Z) | **[computed — corrected 2026-08-24]** |
|  same, restricted to *higher*-high cycles only | +0.83 ft (2025-12-10 17:49Z) | **[computed]** |
| Skew surge on the Mount Vernon crest cycle (06:18Z HW) | **−0.03 ft** | **[computed — corrected 2026-08-24]** |
|  skew surge on the following HHW cycle (19:00Z) | +0.51 ft | **[computed]** |
| Largest 6-min NTR in the sequence | +1.47 ft (2025-12-09 04:06Z) | **[computed]** |
| Highest predicted HW during the sequence | 12.89 ft MLLW (2025-12-06) | **[computed]** |
| WY2026 highest predicted HW at Seattle | ≈ 13.0 ft MLLW (typical WY max, range 12.84–13.24 over WY1997–2025) | **[computed]** |

**INFERENCE — the unrealised compound tail.** Had the same crest arrived on that water year's highest
predicted tide with a p99 winter skew surge (13.0 + 1.61 = 14.6 ft MLLW), the downstream boundary
would have been **~8.0 ft higher** than it actually was at the Mount Vernon crest, and ~2.2 ft higher
than the highest water level that actually occurred anywhere in that AR sequence. Across water years
1997–2025 the Skagit's annual peak-day observed high water fell on average **0.93 ft below** that water
year's maximum *predicted* tide (median 1.03 ft), and came within 0.5 ft of it in only **8 of 29**
years. **[computed]**

### 3.6 Anchors from the literature and from agency data

| Quantity | Value | Context | Source |
|---|---|---|---|
| Puget Sound extreme still water level, 100-yr | **3.2 ft above MHHW** (2-yr 2.2, 5-yr 2.6, 20-yr 2.9, 50-yr 3.1) | regional GEV, 6 gauges pooled | Miller et al. 2019 Table 1/B.2 (FACT, fetched) |
| Seattle-specific 100-yr SWL | **3.3 ft above MHHW** | 119-yr record | ibid. Table B.2 |
| Pacific (outer) coast 100-yr SWL | **4.0 ft above MHHW** | 5 gauges | ibid. |
| Puget Sound GEV parameters | shape −0.27, scale 0.13, location 0.62 | weighted mean of 6 gauges | ibid. Table B.1 |
| Modelled max storm surge, most of Puget Sound | **2.5–3.0 ft** | 34 extreme events 1980–2016 | ibid. Box 3 (Yang et al. 2019c) |
| Embayments exceeding that | Sinclair/Dyes Inlets, Liberty Bay, Hammersley Inlet, **+1 ft** | model vs gauges | ibid. |
| Typical Puget Sound surge | 1–2 ft, "unlikely to exceed 3 ft" | | ibid. App. A |
| Waves in Skagit Bay | **3–5 ft on top of the tide** | | Skagit Climate Science Consortium (FACT, fetched) |
| Skagit delta subsidence | **0 to 1 mm/yr**; up to +8 in by 2100 | | ibid. |
| Days/yr Puget Sound sees higher-than-predicted tides | "nearly 50" | | ibid. |
| WA absolute SLR 2100, RCP8.5 | central **2.0 ft**, likely 1.4–2.8, 1 % exceedance **4.8 ft**, 0.1 % **8.3 ft** | rel. to 1991–2009 | Miller et al. 2018 (FACT, fetched — Table 1; the report's prose states "an upper limit of 8.3 feet ... by 2100". *Corrected 2026-08-24 in adversarial review: this cell previously read 10.0 ft, which is the 2150 1 %-exceedance value in the same table.*) |
| WA absolute SLR 2050, RCP8.5 | central 0.7 ft, likely 0.5–0.9, 1 % 1.3 ft | | ibid. |
| Relative SLR 2100 RCP8.5, Tacoma / Neah Bay | **2.5 ft / 1.0 ft** | VLM −0.5 / +1.1 ft-century | ibid. Table 2 |
| Skagit 100-yr flood, 2080s | **+74 % inundation area, +25 cm mean depth** | SLR + changed river flows | Hamman et al. 2016 (FACT via SCSC abstract page) |
| Skagit, 2040s | **+35 %** area from SLR alone; **+57 %** SLR + flow change | vs FEMA historic 100-yr | ibid. |
| Skagit, 2050s | historic (1970–99) **100-yr peak high water exceeded essentially every year** | peak annual tidal anomaly + SLR | ibid. |
| Duwamish Dec-2022 driver split | tide **~75 %**, surge **~15–17 %**, TSI **~10 %** of TWL to RK14 | AR event | Spicer et al. 2025 (FACT, fetched) |
| Duwamish upstream river share | 0 % → **~70 %** of TWL, RK8 → RK20 | | ibid. |
| Duwamish nonlinear damping | SRI −17 % → −40 %, TRI −10 %; net up to **−50 %** vs linear sum | | ibid. |
| Duwamish flooded area, Dec 2022 | 0.62 km² (all forcings); 0.61 km² without river; **0 km² without surge** | South Park | ibid. |
| Same event + 0.61 m SLR (AR6 SSP5-8.5, 2100) | **1.32 km²** — more than double | | ibid. |
| Warming scenario river increase | +50 m³/s Green River → **+3 cm** upstream TWL, **0** downstream | | ibid. |
| Ward et al. dependence, global | 22 % of 187 stations at lag 0; **56 % at optimal lag −5…+5 d** | skew surge \| Q | Ward et al. 2018 (FACT, fetched) |
| Joint-probability error from assuming independence | **68–74 %** of dependent cases differ by a factor > 2 | | ibid. |
| Couasnon global | 14 % (S\|Q), 20 % (Q\|S) of 3,434 river mouths significant; 6 % both | Δ = 3 d window, Gaussian copula | Couasnon et al. 2020 (FACT, fetched) |
| Cascadia GPS VLM range | +4.9 to −1.2 mm/yr; Puget Sound −0.1 to −0.3; NW Olympic ~+3.5 | 47 stations | Montillet et al. 2018 (abstract only, **not fetched**) |
| CSZ co-seismic subsidence | up to **2 m**; 1 % floodplain +90 / +160 / +300 km² | 24 estuaries | PNAS 2025 (abstract only, **not fetched**) |
| El Niño PNW sea level boost | ~12 in (1982-83, 1997-98), ~6 in (2015-16) | Ian Miller, WSG | KUOW 2026-07-29 (FACT, fetched) |
| HTF days added by 2023-24 El Niño | +6 to 8 outer coast, **+2 to 4 Puget Sound** | | ibid. (USDA NW Climate Hub) |
| NOAA national HTF thresholds | minor ≈ **0.54 m** above MHHW (spread 0.50–0.64), moderate ≈ 0.8 m, major ≈ 1.2 m | | Sweet et al. 2018 (search summary, **not fetched**) |

### 3.7 NOAA CO-OPS station inventory and datums for the target deltas — fetched 2026-08-24

Only **16 Washington stations** publish observed water levels, and **none of them is in Skagit Bay,
Padilla Bay, Port Susan or Possession Sound** (FACT — `mdapi/.../stations.json?type=waterlevels`).
162 WA stations publish tide *predictions*; the delta-adjacent ones are prediction-only.

| Station | ID | Type | MHHW | MLLW | GT | NAVD88 | Real-time WL? | NWS minor/mod/major (ft above MHHW) |
|---|---|---|---|---|---|---|---|---|
| Seattle | 9447130 | reference | 19.30 | 7.94 | 11.36 | **10.28** | yes | **2.10 / 3.00 / 3.40** |
| Tacoma | 9446484 | reference | 12.40 | 0.62 | 11.77 | **3.01** | yes | 2.29 / 2.99 / 3.39 (action 2.11) |
| Everett | 9447659 | reference (pred) | 10.83 | −0.26 | 11.09 | **1.77** | **no** | none published (404) |
| Port Townsend | 9444900 | reference | 11.88 | 3.36 | 8.52 | — | yes | 2.85 / 3.30 / — |
| Cherry Point | 9449424 | reference | 15.49 | 6.34 | 9.15 | — | yes | 1.85 / 2.85 / 3.85 |
| Friday Harbor | 9449880 | reference | 11.61 | 3.85 | 7.76 | — | yes | 1.75 / 2.25 / 2.75 |
| Neah Bay | 9443090 | reference | 9.96 | 2.00 | 7.96 | **2.84** | yes | 2.62 / — / — |
| Bremerton | 9445958 | reference | 23.10 | 11.38 | 11.72 | — | yes | 2.40 / 3.04 / 3.44 (action **6.43**) |
| **La Conner, Swinomish Ch.** | **9448558** | subordinate → Seattle | 14.85 | 4.50 | 10.35 | **—** | **no** | none |
| **Bellingham** | **9449211** | subordinate → Port Townsend | — | — | — | — | **no** | none |
| Sneeoosh Point (Skagit N. Fork mouth) | 9448576 | harmonic | — | — | — | — | no | none |
| Swinomish Ch. ent., Padilla Bay | 9448682 | harmonic | — | — | — | — | no | none |
| Tulare Beach, Port Susan (Stillaguamish) | 9448043 | harmonic | — | — | — | — | no | none |
| Duwamish Waterway, 8th Ave S | 9447029 | subordinate → Seattle | — | — | — | — | no | none |

All values feet above **station datum (STND)**, 1983–2001 epoch. **The critical gap: NAVD88 is
published at Seattle, Tacoma, Everett and Neah Bay but NOT at Port Townsend, Cherry Point, Friday
Harbor, Bremerton or La Conner.** Converting a tidal datum to NAVD88 at a station without a published
tie requires VDatum, not arithmetic. **[FACT — computed from `mdapi/.../datums.json` per station]**

Derived ties where NAVD88 exists: NAVD88 = MLLW + **2.34** ft (Seattle), **+2.39** (Tacoma),
**+2.03** (Everett), **+0.84** (Neah Bay). MHHW sits **+9.02 / +9.39 / +9.06 / +7.12 ft** above NAVD88
at those four. **[computed]**

**Bremerton's `action` level (29.53 ft STND) is above its `major` level (26.54 ft)** — a self-evidently
broken record in the CO-OPS floodlevels feed. **[FACT — fetched]**

### 3.8 NWPS carries two Puget Sound tide gauges — mislabelled, undated and stale

The `nwps_all_gauges_report.csv` contains **two WA locations with SHEF PE `HC`**, both tide gauges:

| LID | Name | PEDTS | minor | moderate | major | datum recorded |
|---|---|---|---|---|---|---|
| **EBSW1** | Pacific Ocean at Seattle Tide Gage | HCIRP | 2.10 ft | 3.00 | 3.40 | **none** |
| **BMTW1** | Pacific Ocean at Bremerton Tide Gage | HCIRG | 2.36 ft | 3.00 | 3.70 | **none** |

**Proof that these are feet above MHHW** (nothing in the API says so):
`EBSW1` 2.10/3.00/3.40 equals the CO-OPS NWS thresholds for Seattle (21.40/22.30/22.70 ft STND) minus
Seattle MHHW (19.30 ft STND) **exactly**. Independently, `BMTW1`'s last observation was **−0.47 ft at
2026-07-26T00:18Z**; CO-OPS 9445958 observed **11.243 ft MLLW** at that same instant, and Bremerton
MHHW − MLLW = 11.72 ft, giving **−0.477 ft relative to MHHW**. **[computed — exact match]**

Three defects follow, all checkable:

1. **Variable mislabelled.** The NWPS `/stageflow` response calls `BMTW1`'s primary series
   **"Ceiling Height"** in ft, with secondary "Flow" in kcfs. The NWS SHEF Code Manual (5 July 2012,
   p. 2965 of the extracted text) defines `HC` = "**Height, ceiling (FT, M)**" — a cloud-base
   variable — while `HM` = "Height of tide, MLLW". CO-OPS' own SHEF products use `HM` for MLLW-
   referenced water level (FACT — NOAA Tech. Rep. NOS CO-OPS 026, fetched). NWPS is decoding a
   MHHW-referenced water level with the generic PE table. **[FACT — both PDFs fetched and grepped]**
2. **Datum absent.** `datums.vertical.value` is `[]` for both. A consumer cannot know the numbers are
   MHHW-relative.
3. **Dead or stale.** `EBSW1/stageflow` returns **completely empty** observed and forecast arrays,
   while the CSV says "Forecasts are issued routinely year-round". `BMTW1`'s newest observation on
   2026-08-24 was **2026-07-26**. **CORRECTED 2026-08-24 in adversarial review: this was an
   array-ordering mistake.** `BMTW1/stageflow` serves a rolling ~30-day window in ascending time order;
   2026-07-26T01:00Z is its **oldest** entry, not its newest. Re-fetched 2026-08-24: 7,159 observations
   spanning 2026-07-26T01:00Z → 2026-08-25T00:24Z, i.e. **current to the minute**. BMTW1 is live;
   only EBSW1 is empty. **[FACT — re-fetched]**

### 3.9 NOAA SSCOFS gives modelled water level at the delta mouths — including where no gauge exists

CO-OPS' `ofs_water_level` product returns Salish Sea operational-forecast-system output at station
locations. Tested 2026-08-24:

| Station | ID | SSCOFS water level? | Relevance |
|---|---|---|---|
| **Sneeoosh Point** | 9448576 | **yes** | Skagit North Fork mouth |
| **Swinomish Ch. ent., Padilla Bay** | 9448682 | **yes** | Skagit / Swinomish |
| Turner Bay, Similk Bay | 9448657 | yes | Skagit / Padilla |
| **Everett** | 9447659 | **yes** | Snohomish delta (no real gauge) |
| Priest Point | 9447717 | yes | Snohomish / Possession |
| **Tulare Beach, Port Susan** | 9448043 | **yes** | Stillaguamish delta |
| **Bellingham** | 9449211 | **yes** | Nooksack delta (no real gauge) |
| Cherry Point / Seattle / Tacoma / Port Townsend | — | yes | reference gauges |
| La Conner 9448558, Anacortes 9448794, Duwamish 9447029 | — | **no** | not served |

Cadence and horizon at Bellingham and Sneeoosh Point: **931 values at exactly 6-minute spacing spanning
2026-08-24 00:00Z → 2026-08-27 21:00Z (≈ 94 h)** — nowcast plus ~3-day forecast, refreshed on the OFS
cycle. **[FACT — computed]** This is `MODELED`, never `OFFICIAL_FORECAST`.

### 3.10 A CO-OPS unit-label bug worth encoding as a parser guard

`dpapi/prod/webapi/product/sealvltrends.json` reports `"seasonalUnits": "inches"` with Seattle
January = **0.31**; the same request with `units=metric` reports `"seasonalUnits": "meters"` with
January = **0.093**. 0.093 m = 3.66 in, not 0.31 in — but it *is* 0.305 **feet**. The English seasonal
values are in **feet**, mislabelled inches; the metric label is correct. Independent check: the API's
metric seasonal range is 0.149 m = 0.489 ft, against my own Seattle monthly-MSL range of **0.527 ft**.
`trend` is fine (0.82 in/decade = 2.09 mm/yr, both agree). **[FACT — computed]**

Also observed: CO-OPS `datagetter` returned **HTTP 504 Gateway Time-out** on 10-year `predictions`
`interval=hilo` requests for 2016–2025 while succeeding on the same request shape for 1996–2005 and
2006–2015; year-by-year requests all succeeded. Chunk long historical pulls to ≤ 1 year and retry.
**[FACT — observed]**

---

## 4. What is settled, what is emerging, what is contested

### Settled (established)

- **Compound river–coastal flooding is a distinct hazard class with a formal typology.** Zscheischler
  et al. 2020; 366 papers 2012–2022, 72 % multivariate.
- **Assuming independence of river discharge and sea level understates joint hazard where dependence
  exists**, by more than a factor of 2 in ~70 % of dependent cases (Ward et al. 2018). Wahl et al.
  (2015) established the same for surge + rainfall in US cities, and specifically that **Pacific-coast
  compound risk is lower than Atlantic/Gulf** — a caveat that transfers to us as "lower, not zero".
- **Skew surge is the right statistic**, and it is near-independent of tidal amplitude in the North
  Atlantic (Williams et al. 2016). My Seattle test (ρ = −0.09) says near-independent here too.
- **Storm surge in Puget Sound is small.** 1–2 ft typical, 2.5–3.0 ft modelled maximum, and **zero
  cycles above 3.0 ft in 30 years of Seattle observations**. Three independent lines agree.
- **Relative sea level in Washington is spatially heterogeneous** because interseismic VLM ranges from
  ~+4.5 mm/yr (NW Olympic, Montillet) to somewhere between −0.3 (Montillet) and −1.5 mm/yr (Miller,
  Tacoma) in the central Sound — the *sign* is settled, the central-Sound *magnitude* is not. The
  tide-gauge trends confirm the heterogeneity:
  −1.70 mm/yr at Neah Bay, −0.05 at Cherry Point, +2.08 at Seattle.
- **The seasonal cycle concentrates coastal extremes in December–January** (84 % of Seattle's 50
  highest high waters), coincident with the AR flood season.
- **Nonlinear tide–river interaction damps the tide as river flow rises.** Spicer et al. modelled it;
  I observed it at SNAW1 (daily range 10.5 ft → 1.5 ft as the Dec-2025 flood arrived).

### Emerging

- **Nonlinear interaction terms are first-order in engineered PNW estuaries**, not corrections
  (Spicer et al. 2025, the only decomposition of a real PNW compound event I could find, published
  August 2025).
- **Remote sea level anomalies must be in the boundary conditions** for Salish Sea extreme water level
  modelling (Grossman et al. 2023 — **not independently fetched**).
- **PS-CoSMoS** is being built to give Puget Sound the CoSMoS treatment: 0–2 m SLR (plus a 5 m case),
  daily-to-100-year storms, **40 SLR × storm combinations**, 2 m DEM, and it *does* include river
  discharge. The Whatcom County release (Grossman, VanArendonk, Crosby, Tehranirad, Nederhoff,
  Barnard, Erikson, Danielson 2024, **DOI 10.5066/P9I08NS5**) is public. **Skagit and Snohomish
  releases were not found.** Project pages date the framework to 2016–2021 with no completion date.
- **Co-seismic subsidence as a flood-hazard term.** Miller et al. (2018) already ship a 500-year CSZ
  land-level change alongside their SLR tables; the 2025 PNAS paper quantifies the floodplain
  expansion. This is moving from geology into planning.
- **El Niño as a seasonal sea-level modifier with operational lead time.** With CPC giving >90 % odds
  of a very strong El Niño for WY2027 (per the prior repo pass) and historical analogues adding
  6–12 inches of PNW coastal sea level plus 2–4 Puget Sound HTF days, this is a *forecastable*
  seasonal shift in the coastal marginal — not just climatology.

### Contested

- **Tide–skew-surge independence in mixed semidiurnal regimes.** Williams et al. (2016) say
  independent (North Atlantic); Santamaria-Aguilar & Vafeidis (2018) explicitly question it for mixed
  semidiurnal tides — Puget Sound's regime. My ρ = −0.09 is small but non-zero and negative in exactly
  the direction they predict. **Treat as near-independent, log the residual dependence.**
- **Whether the Puget Sound extreme-SWL GEV is well specified.** Miller et al. (2019) give
  Seattle's 100-year still water level as **3.3 ft above MHHW** with a bounded shape parameter
  (−0.21 to −0.27). **The 2022-12-27 event reached 3.76 ft above MHHW — 0.46 ft above the fitted
  100-year level, three years after publication** (**[computed]**), and 2022-01-07 and 2012-12-17
  reached 3.16 and 3.12 ft, i.e. three events at or above the fitted ~50-year level in 30 years.
  Either the negative shape parameter truncates the tail too tightly, or the pooled regional fit
  underestimates Seattle. **INFERENCE — flag, do not silently use the 3.2/3.3 ft number as an upper
  bound.**
- **Trends in storminess and wave height in the NE Pacific.** Bromirski et al. (2003) found increasing
  San Francisco surges; Miller (2013) did not replicate at Neah Bay; Gemmrich et al. (2011) attribute
  much of the wave-height trend to instrumental bias. Projections are "ambiguous" (Miller et al. 2019,
  quoting Collins et al. 2013). **No trend in Puget Sound surge should be encoded.**
- **The inverse-barometer coefficient in circulation.** SCSC's "1.9 cm per mb" is ~2× the classical
  1.0 cm/hPa and is repeated in regional outreach material.
- **Whether the Mount Vernon *forecast point* is compound at all.** SCSC says the river is "heavily
  influenced by the tide" from "below Mt. Vernon to Puget Sound". My tidal-transmission (1 %) and
  backwater (null) tests both say the influence at the gauge is marginal. These are compatible —
  "below Mount Vernon" is the delta, not the gauge — but the repo's prior pass reads the SCSC line as
  applying to the gauge, and it does not.

---

## 5. Western Washington specificity — what transfers and what does not

**Transfers.**
- The Zscheischler typology, the TWL decomposition, and the skew-surge definition are general.
- Ward et al.'s finding that **US West Coast river mouths show widespread significant dependence**
  transfers directly, and Neah Bay is one of their sites. My three basins confirm it locally with
  larger and more significant ρ than the global median.
- The lag-window lesson (zero-lag testing halves the apparent dependence) transfers exactly; my
  optimum is −1 day, well inside Ward's −5…+5 d and Couasnon's ±3 d windows.
- Spicer et al.'s **nonlinear damping upstream / nonlinear amplification downstream** result is from a
  Puget Sound estuary under an AR — it is the most transferable single paper for this platform.

**Does not transfer.**
- **Gulf and Atlantic magnitudes.** Spicer et al. put it plainly: East Coast communities routinely
  absorb multi-metre surges, and a 0.6 m surge there is "negligible or minor"; here the same surge is
  the difference between no flooding and major flooding because there is no floodplain buffer between
  the high-water mark and the infrastructure. **Puget Sound is a small-surge, small-freeboard system.**
  Design intuitions imported from hurricane coasts will be wrong in both directions.
- **Tropical-cyclone compound literature** (P-Surge, storm-tide return periods, Delaware/Chesapeake
  skew-surge studies) is mechanically irrelevant: our surges are extratropical, slow, and broad.
- **California CoSMoS results** do not transfer: Puget Sound is fetch-limited, wave run-up is minor
  except in the Strait, and the wave climate is locally generated.
- **European copula case studies** (Bevacqua's Ravenna, the Rhine delta) are useful for method, not
  magnitude; the western Netherlands shows *no* significant dependence, which is the opposite of here.
- **A single statewide SLR rate.** Neah Bay's relative sea level is falling. Cherry Point's is flat.
  Any product that applies one Washington number to the Nooksack and the Duwamish is wrong.

**Uniquely local and load-bearing.**
- **The gauge network is the constraint, not the science.** There is no real-time NOAA water level
  gauge in Skagit Bay, Padilla Bay, Port Susan or Possession Sound. La Conner and Bellingham — the
  two most relevant delta locations — are prediction-only subordinate stations without published
  NAVD88 ties. SSCOFS partially fills this with modelled water level at Sneeoosh Point, Swinomish
  Channel, Everett, Tulare Beach and Bellingham; it does not fill it at La Conner or the Duwamish.
- **The three deltas are not one problem.** Snohomish at Snohomish is a tidal gauge; Nooksack at
  Ferndale and Skagit at Mount Vernon are not. Whatever the platform does about tide must be
  per-forecast-point, driven by a measured transmission coefficient, not by a basin-level flag.
- **Skagit non-stationarity compounds coastally.** The prior pass established that Mount Vernon now
  reaches the same stage on ~29 % less flow than in 1906, with aggradation, levee confinement and
  delta subsidence as candidate mechanisms. Two of those three are coastal. A stage threshold on that
  reach is drifting *toward* the sea, and SLR pushes the same direction.

---

## 6. What this means for Cascadia Papsukkal

### 6.1 Doctrine

- **`HYDROLOGY.md` needs a coastal section.** It currently has no tide, no surge, no sea level, no
  datum-below-the-gauge. Minimum content: the TWL decomposition of §2.2 as the governing equation for
  tidally influenced forecast points; the statement that stage at such a point is a **compound**
  quantity; and the per-point tidal transmission coefficients of §3.4.
- **Add `tidal_class` to the forecast-point domain model**, alongside `regulation_class`. Proposed
  values from measurement, not judgement: `TIDAL` (transmission ≥ 0.5 ft/ft), `TIDALLY_MODULATED`
  (0.05–0.5), `MARGINAL` (0.01–0.05), `FLUVIAL` (< 0.01), `UNKNOWN`. From §3.4: SNAW1 = `TIDAL`,
  NKSW1 = `MARGINAL`, MVEW1 = `MARGINAL`. The coefficient itself is a `DerivedFeature` with a
  method version and the measurement window recorded, re-derived annually.
- **Never sum tide + surge + river.** If a combined water level is ever displayed, it must come from a
  hydrodynamic model (SSCOFS, PS-CoSMoS) or be labelled as an upper bound that ignores nonlinear
  damping. Spicer et al. quantify the error at up to 50 % upstream.
- **"Compound risk" must remain an index, never a probability**, until a copula or conditional-
  exceedance model has been hindcast-evaluated per §3.1's method. The numbers in §3.1 are dependence
  *measurements*, not a calibrated joint model.
- **`DATA_DOCTRINE.md` §6 (units) needs a vertical-datum sibling.** A tidal datum (MLLW, MHHW, STND)
  is not a geodetic datum (NAVD88, NGVD29). The existing rule "refuse cross-datum comparisons" already
  covers it, but the *taxonomy* must name tidal datums explicitly, carry the **epoch** (1983–2001),
  and mark the four Puget Sound stations that have no published NAVD88 tie as requiring VDatum.
- **Add an `ARCHIVED`-adjacent presentation rule for MHHW-relative values.** A "2.1 ft" flood threshold
  that is silently MHHW-relative in one feed and STND-relative in another is exactly the V1-class
  failure this repo exists to prevent.

### 6.2 Methods

- **Compute skew surge, not NTR, and compute it per tidal cycle.** Reference implementation: match
  each predicted high water to the maximum observed water level within ±3 h. Store the matched pair
  (predicted HW time, predicted HW value, observed max time, observed max value, skew surge) so the
  match is auditable. The calendar-day shortcut is wrong by up to 2 ft in spring (§2.3).
- **Store the dependence measurements of §3.1 as a `DerivedFeature`** per (basin, tide station, lag),
  with `method_version`, so they can be recomputed as history accumulates and compared over time.
- **Add a coastal-context block to the Event Zero replay.** Every historical crest in the hindcast set
  should carry the concurrent observed water level, predicted high water, and skew surge at its
  reference tide station. Without it the replay cannot answer "was the tide helping or hurting?" —
  and for December 2025 the answer (helping, by ~5–7 ft) is the single most important unstated fact
  about the event.
- **Add a "tidal headroom" indicator for `TIDAL` points only.** Alongside the existing stage/flow/
  time-to-threshold headroom: the difference between the concurrent water level and that water year's
  maximum predicted high water plus the p99 winter skew surge — i.e. **how much coastal water level
  the event did not get**. For December 2025 at Seattle that is ~8 ft. Label it `EXPERIMENTAL`.
- **Do not attempt a stage↔TWL conversion.** ADR-0011's "never converts stage↔flow itself" extends
  here verbatim.

### 6.3 Data sources to add to `DATA_SOURCES.md`

**C1 · NOAA CO-OPS Data Retrieval API — `src:noaa-coops-datagetter` — OBSERVED / MODELED**
- Base `https://api.tidesandcurrents.noaa.gov/api/prod/datagetter`. No auth; `application=` string
  requested. Products used: `water_level` (6-min observed, **1 month max per request**),
  `hourly_height` (**1 yr**), `high_low` (**1 yr**), `predictions` (`interval=6|h|hilo`, **1 yr**
  for 6-min/hourly, **10 yr** for `hilo`), `monthly_mean` (**200 yr**), `ofs_water_level`,
  `air_pressure`, `wind`. `daily_mean` is **Great-Lakes only** — returns an error for coastal
  stations. Params: `station`, `product`, `datum` (**required** for water level; MLLW MHHW MHW MTL
  MSL MLW NAVD STND CRD IGLD LWD), `begin_date`/`end_date`/`range`/`date=latest|recent|today`,
  `units=english|metric`, `time_zone=gmt|lst|lst_ldt`, `format=json|xml|csv`. Errors come back as
  `{"error":{"message":...}}` with HTTP 200 — **parse the body, do not trust the status code**.
  Observed 504s on long `hilo` pulls (§3.10). Public domain. `expected_cadence` 6 min, `grace` 30 min.
- **C1a · Metadata API** `https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/`:
  `stations.json?type=waterlevels|tidepredictions&units=english`, `stations/{id}/datums.json`,
  `stations/{id}/floodlevels.json` (404 where none exist — e.g. Everett), `stations/{id}/harcon.json`.
  Datums carry `epoch` (1983-2001). Flood levels are **ft above station datum**, split into
  `nos_*` and `nws_*` families that can **disagree** — verified at Port Townsend (`nos_minor` 13.86 =
  1.98 ft above MHHW vs `nws_minor` 14.73 = 2.85 ft). *Corrected 2026-08-24: Bremerton is **not** an
  example — its `nos_*` fields are all `null`; the 3.44-vs-3.70 gap is CO-OPS `nws_major` against
  **NWPS** BMTW1, i.e. a CO-OPS/NWPS disagreement, not a NOS/NWS one.*
- **C1b · Sea level trends** `dpapi/prod/webapi/product/sealvltrends.json?station=&affil=US` — trend,
  error, start/end date, monthly seasonal cycle. **`seasonalUnits: "inches"` is wrong; the values are
  feet** (§3.10). Encode a unit override with this note as its provenance.

**C2 · NOAA SSCOFS via CO-OPS `ofs_water_level` — `src:noaa-sscofs` — MODELED**
- Same datagetter endpoint, `product=ofs_water_level`. 6-minute nowcast + ~3-day forecast (~94 h,
  931 values). Available at Sneeoosh Point (Skagit N. Fork), Swinomish/Padilla, Turner Bay, Everett,
  Priest Point, Tulare Beach (Port Susan), Bellingham, Cherry Point, Seattle, Tacoma, Port Townsend.
  **Not** at La Conner, Anacortes, Duwamish Waterway. `source_kind = MODELED`, never OFFICIAL.
  `expected_cadence` = OFS cycle (verify: likely 6-hourly), `grace` = one cycle.

**C3 · NWPS tide points EBSW1 / BMTW1 — `src:nwps-v1` — do NOT ingest naively**
- Add a parser guard: for PEDTS beginning `HC`, override the NWPS `primaryName` ("Ceiling Height")
  with `water_level_mhhw`, set `datum = MHHW` with the derivation in §3.8 as lineage, and reject the
  `secondaryUnits: kcfs` field. Alternatively, exclude both LIDs and use C1/C2 — recommended, since
  EBSW1 returns no data at all. (BMTW1 is *not* stale — see the correction in §3.8 — but it is still
  mislabelled and datum-less, which is reason enough to prefer C1/C2.)

**C4 · Washington Coastal Resilience Project SLR projections — `src:wcrp-slr-2018` — MODELED/CONFIGURED**
- Miller et al. (2018), **171 locations on a 0.1° grid**, Excel per location, one worksheet per RCP,
  first sheet carrying VLM estimate and **co-seismic subsidence** for a 500-yr CSZ event. Distributed
  from `wacoastalnetwork.com/wcrp-documents.html` (no API; the CIG interactive tool offers raw
  download). Static reference data — ingest once, version it, treat as `CONFIGURED` context, never as
  an input to a hazard computation.

**C5 · Miller et al. (2019) extreme still water level curves — `src:wcrp-eswl-2019` — CONFIGURED**
- Two regional GEV curves (Puget Sound, outer coast) in **ft above local MHHW** at 2/5/20/50/100-yr,
  plus a SLR-offset table. Encode with the §4 caveat that 2022-12-27 exceeded the Seattle 100-yr level.

**C6 · PS-CoSMoS / USGS CMGDS data releases — `src:usgs-pscosmos` — MODELED**
- Whatcom County flood depth and extent projections, **DOI 10.5066/P9I08NS5** (2024). 2 m DEM,
  0–2 m SLR × daily-to-100-yr storms (40 combinations), includes river discharge. USGS CMGDS metadata
  pages returned **HTTP 403** to WebFetch — retrieve via the DOI landing page or ScienceBase.
  **Skagit and Snohomish equivalents not found — track.**

### 6.4 Contracts

- `Station`: add `station_kind ∈ {river_gauge, tide_gauge, tide_prediction_only, ofs_virtual}`;
  make `tidal_datum_epoch` required when any tidal datum is present; allow `navd88_tie: null` with a
  reason ("not published by CO-OPS for this station") rather than a computed guess.
- `Threshold`: add `datum_family ∈ {gauge_datum, tidal_datum, geodetic_datum}` and
  `reference_datum` (e.g. `MHHW`). Reject construction of a threshold whose family is unknown. This
  is what makes EBSW1's "2.1 ft" safe to store.
- `ForecastPoint`: add `tidal_class` and `tidal_transmission_ft_per_ft` (nullable, `DerivedFeature`
  reference).
- `BasinVisualizationState` / `SceneSummary`: a delta basin needs a coastal sub-state —
  `coastal: { water_level, predicted_high_water, skew_surge, next_high_water_time, source_kind,
  station_id, datum }` or `UNKNOWN` with a reason. Rendering a delta scene with a flat blue sea and
  no tide state is a visual-truth violation of the same family as moving the snow line.
- The three-surface model (`susceptibility`, `forcing`, `hazard`, `agreement`) needs either a fourth
  surface **COASTAL STATE** or an explicit doctrinal statement that coastal water level is a
  *modifier* of hazard at `TIDAL` points and is out of scope elsewhere. My recommendation: a modifier,
  not a surface — it is not a basin property, it is a boundary condition, and only a minority of
  forecast points feel it.

---

## 7. What this domain contradicts or qualifies in the current repo doctrine

1. **`HYDROLOGY.md` §2, "Nooksack: … the lower river is tidally influenced at Ferndale."** True but
   quantitatively negligible: **0.019 ft of stage per ft of Cherry Point tide (r = 0.33)**, tidal-band
   sd 0.16 ft. The far larger omission is that **Snohomish at Snohomish (SNAW1) is ~83 % tidal**
   (slope 0.831 ft/ft, r = 0.94, tidal-band sd 3.03 ft) and the doctrine does not mention it at all —
   even though `HYDROLOGY.md` §12 cites SNAW1 as one of Event Zero's record gauges. **Its record stage
   is a compound quantity.**

2. **`HYDROLOGY.md` §9, hydraulic headroom and time-to-threshold.** On a `TIDAL` point the stage
   oscillates ~11 ft on a 12-hour cycle at low flow. `rate of rise` computed over a 1 h / 3 h / 6 h
   window at SNAW1 is dominated by the tide, not the flood. **`trend.py` and `headroom.py` will
   produce nonsense at SNAW1 today.** Either de-tide the series before computing trend, or refuse
   trend at `TIDAL` points with an explicit reason. This is a live bug, not a future concern.

3. **`HYDROLOGY.md` §9, "Vertical datums: … Record the datum on every stage series and every
   threshold."** Correct and insufficient. Tidal datums are a **different family** with an epoch, and
   four of the Puget Sound stations the platform would need (Port Townsend, Cherry Point, Friday
   Harbor, La Conner) have **no published NAVD88 tie**. The doctrine's "refuse cross-datum comparison"
   rule must extend to refusing tidal↔geodetic conversion without VDatum.

4. **`HYDROLOGY.md` §13, "What Cascadia Papsukkal will not claim."** Add: it will not claim a river
   stage forecast is complete at a tidally influenced point when the source model does not carry the
   coastal boundary condition. NWPS/NWRFC's MVEW1 and NKSW1 hydronotes say only that forecasts "take
   into account past and future precipitation" — no mention of tide (FACT — fetched). For SNAW1 that
   silence is material.

5. **`docs/research/flood-genesis-mechanisms-2026-08-24.md` §6.2** states "For any forecast point in a
   tidally-influenced reach — Mount Vernon, Ferndale, and the lower Snohomish — a river-only stage
   forecast is structurally incomplete." **Half right.** It is structurally incomplete at the lower
   Snohomish and materially so. At Mount Vernon and Ferndale the measured tidal transmission is 1–2 %
   and a 30-winter regression finds **no** daily-scale backwater signal at Mount Vernon
   (coefficient −0.06 ± 0.03 ft/ft). The prior pass over-generalised the Skagit Climate Science
   Consortium's "below Mt. Vernon to Puget Sound" — *below* the gauge, not at it.

6. **`flood-genesis-mechanisms` §6.1, backwater as an explanation for the Mount Vernon stage–discharge
   drift.** My null result is evidence *against* tidal/sea-level backwater as the mechanism at daily
   resolution, and therefore weak evidence *for* the aggradation and levee-confinement explanations.
   *Qualified 2026-08-24 in adversarial review:* the independent re-run gives the high-flow subset a
   coefficient of **+0.17 ± 0.10 (t = +1.7)** — positive, correctly signed, merely non-significant. A
   daily-resolution non-result is too weak to *adjudicate between* mechanisms; it justifies removing
   backwater from the list of *established* explanations, not promoting the other two.

7. **`EVENT_ZERO.md` (by implication).** The December 2025 hindcast dataset has no coastal dimension.
   The three record crests all occurred at 4.8–6.6 ft *below* MHHW, with no skew surge anywhere in the
   AR sequence exceeding +1.17 ft.
   Without that fact recorded, any skill score computed on Event Zero silently assumes a benign
   coastal boundary and will mislead the first time an AR crest lands on a king tide.

8. **`DATA_SOURCES.md` G12** correctly records the CO-OPS datum endpoint and the Seattle/Tacoma
   NAVD88↔MLLW offsets. It does not record that **NAVD88 is missing at Port Townsend, Cherry Point,
   Friday Harbor and La Conner**, nor the `floodlevels.json` endpoint, nor the NOS-vs-NWS threshold
   disagreement, nor the `sealvltrends` unit-label bug. All four belong there.

9. **`VISUAL_TRUTH_DOCTRINE.md`.** Its snow-line rule has an exact coastal analogue: the renderer must
   never draw a static sea surface beside a tidal delta, and must never animate water rising in a
   delta scene without a tidal source. Sea level in Puget Sound moves 11 ft twice a day. A frozen
   shoreline is a fabricated certainty.

---

## 8. Open questions

1. **Is the Mount Vernon backwater null result an artifact of daily averaging?** Daily means smear a
   12.4-hour signal. The decisive test is peak-timing: for the ~30 largest instantaneous crests, is
   there residual stage (after conditioning on instantaneous Q) correlated with concurrent Seattle
   water level? This needs the USGS 15-min record and a rating-shift-aware Q, and I did not run it.
2. **Where exactly is the Skagit's tidal limit?** I measured 1 % transmission at Mount Vernon
   (RM ≈ 15.7). The limit is between there and the North/South Fork split. USGS 12200500 is the only
   continuous gauge on the reach; the answer probably requires the Skagit County / USACE HEC-RAS model
   or a temporary deployment. Same question for the Nooksack below Ferndale.
3. **Does SSCOFS have published skill statistics for Puget Sound water level, and what is its
   cycle cadence and issuance time?** I confirmed the product exists and its horizon; I did not find
   its validation report, its update frequency, or whether the nowcast/forecast boundary is exposed
   in the API response.
4. **Do PS-CoSMoS Skagit and Snohomish data releases exist?** Only the Whatcom County release
   (10.5066/P9I08NS5) surfaced. USGS CMGDS metadata pages return 403 to automated fetch.
5. **What is the correct copula family for these basins?** I measured rank dependence and conditional
   exceedance but fitted no copula. Ward et al. tried Gumbel/Frank/Clayton; Couasnon used Gaussian
   with a BB7 sensitivity. Upper-tail dependence is the quantity that matters and is the one rank
   correlation does not reveal. Until this is done and hindcast-evaluated, no joint probability may be
   displayed.
6. **Is the Miller et al. (2019) Puget Sound GEV upper tail too tight?** 2022-12-27 exceeded the
   fitted 100-year level. Refitting with data through 2025 (which I now have for Seattle) would
   settle it.
7. **Is the SCSC "1.9 cm per mb" figure an error, or an empirical wind-plus-pressure regression?**
   Worth resolving before any pressure term enters a derived feature.
8. **Does NWRFC's Snohomish-at-Snohomish forecast carry a tidal boundary condition?** The published
   hydronote says only "past and future precipitation". If it does not, the official forecast at a
   fully tidal point is structurally incomplete and the platform should say so — carefully, and
   without implying the official forecast is wrong.
9. **How should `available_at` be assigned to a tide *prediction*?** Harmonic predictions for 2030 are
   computable today. Knowledge time is essentially "whenever the harmonic constants were published",
   which breaks the platform's `max(issued_at, retrieved_at)` rule. Needs an explicit doctrine entry.
10. **What is the CSZ co-seismic land-level change at each of the eight basins' outlets**, and should
    the platform surface it at all? Miller et al. (2018) ship it per location; it is a legitimate,
    sourced, non-life-safety piece of context, but it is also the single most alarming number in this
    corpus entry.
11. **Are the NOS and NWS coastal flood thresholds reconcilable?** They disagree at Bremerton
    at Port Townsend (minor 1.98 vs 2.85). (Bremerton's 3.44 vs 3.70 is CO-OPS vs NWPS, not NOS vs NWS
    — Bremerton has no `nos_*` values at all.) Only the NWS family
    may be badged OFFICIAL under `DATA_DOCTRINE.md` §2 — but that should be confirmed with NWS Seattle
    rather than assumed.

---

## 9. Sources

**Fetched and read directly**

- [Miller, Yang, VanArendonk, Grossman, Mauger, Morgan (2019), *Extreme Coastal Water Level in Washington State*, Washington Coastal Resilience Project / UW CIG](https://cig.uw.edu/wp-content/uploads/sites/2/2019/10/ExtremeWL_Final_15Oct19_midres.pdf) — 49 pp PDF, text-extracted. Tables 1, 2, B.1, B.2; Boxes 1–3; Appendix A.
- [Miller et al. (2018), *Projected Sea Level Rise for Washington State — A 2018 Assessment* (updated 07/2019)](https://cig.uw.edu/wp-content/uploads/sites/2/2019/07/SLR-Report-Miller-et-al-2018-updated-07_2019.pdf) — 24 pp PDF, text-extracted. Tables 1–2, Figures 3–4, Appendix C framing.
- [Spicer, Sun, Yang, Wang, Reesman, Taraphdar, Leung (2025), "Decomposing a Compound Flood Event in an Urban Pacific Northwest Estuary", *Earth's Future* 13(8), 10.1029/2025EF006001](https://www.osti.gov/servlets/purl/2584719) — full text via OSTI (Wiley returned 403). Equation 1, Figures 5–8, Table 1.
- [Ward, Couasnon, Eilander, Haigh, Hendry, Muis, Veldkamp, Winsemius, Wahl (2018), "Dependence between high sea-level and high river discharge increases flood hazard in global deltas and estuaries", *Environ. Res. Lett.* 13 084012](https://iopscience.iop.org/article/10.1088/1748-9326/aad400)
- [Couasnon, Eilander, Muis, Veldkamp, Haigh, Wahl, Winsemius, Ward (2020), "Measuring compound flood potential from river discharge and storm surge extremes at the global scale", *NHESS* 20, 489–504](https://nhess.copernicus.org/articles/20/489/2020/)
- [*Review article: The growth in compound weather and climate event research in the decade since SREX*, NHESS 25, 2591–2611 (2025)](https://nhess.copernicus.org/articles/25/2591/2025/)
- [Skagit Climate Science Consortium — Coastal Delta Flood Risks](http://www.skagitclimatescience.org/flood-risk-coastal-delta/)
- [Skagit Climate Science Consortium — abstract, Hamman, Hamlet, Lee, Fuller, Grossman (2016), "Combined Effects of Projected Sea Level Rise, Storm Surge, and Peak River Flows on Water Levels in the Skagit Floodplain", *Northwest Science* 90(1)](https://www.skagitclimatescience.org/research/completed-research/abstract-combined-effects-of-projected-sea-level-rise-storm-surge-and-peak-river-flows-on-water-levels-skagit-floodplain/) — abstract page; the BioOne full text was not reachable.
- [USGS PCMSC — PS-CoSMoS project page](https://www.usgs.gov/centers/pcmsc/science/ps-cosmos-puget-sound-coastal-storm-modeling-system) and [PS-CoSMoS FAQs](https://www.usgs.gov/centers/pcmsc/science/ps-cosmos-faqs)
- [NWS SHEF Code Manual, 5 July 2012](https://www.weather.gov/media/mdl/SHEF_CodeManual_5July2012.pdf) — PE table: `HC` = Height, ceiling; `HM` = Height of tide, MLLW; `HG` = Height, river stage.
- [NOAA Technical Report NOS CO-OPS 026, *A Guide to CO-OPS SHEF and CREX Products*](https://tidesandcurrents.noaa.gov/publications/NOAA_Technical_Report_NOS_COOPS_026.pdf)
- [NOAA CO-OPS Data Retrieval API documentation](https://api.tidesandcurrents.noaa.gov/api/prod/) — products, parameters, datums, per-product length limits.
- [KUOW, "Washington cities try to gird for coastal flooding as 'super El Niño' nears", 2026-07-29](https://www.kuow.org/climate/2026-07-29/washington-cities-try-to-gird-for-coastal-flooding-as-super-el-nino-nears) — quotes Ian Miller (Washington Sea Grant).
- [Washington Coastal Hazards Resilience Network — SLR projections tools](https://wacoastalnetwork.com/research-and-tools/slr-projections/)

**Primary datasets queried directly on 2026-08-24 (all computations in §3)**

- NOAA CO-OPS `api/prod/datagetter` — `water_level`, `hourly_height`, `high_low`, `predictions`
  (`interval=6|h|hilo`), `monthly_mean`, `ofs_water_level`; stations 9447130 (Seattle), 9445958
  (Bremerton), 9449424 (Cherry Point), 9448576, 9448682, 9448657, 9447659, 9447717, 9448043, 9449211,
  9446484, 9444900, 9443090, 9449880, 9444090.
- NOAA CO-OPS `mdapi/prod/webapi/` — `stations.json` (`type=waterlevels`, `type=tidepredictions`),
  `stations/{id}/datums.json`, `stations/{id}/floodlevels.json`.
- NOAA CO-OPS `dpapi/prod/webapi/product/sealvltrends.json` — 7 Washington stations, English and
  metric.
- NOAA NWPS `api.water.noaa.gov/nwps/v1/gauges/{lid}` and `/stageflow` — MVEW1, NKSW1, SNAW1, MROW1,
  EBSW1, BMTW1; plus `nwps_all_gauges_report.csv` (12,886 rows; 285 WA).
- USGS `waterservices.usgs.gov/nwis/dv` — 12200500, 12213100, 12150800 (`00060`/`00003`), 12200500
  (`00065`/`00003`), 1996–2025.
- USGS OGC API `api.waterdata.usgs.gov/ogcapi/v0/collections/continuous/items` — 12200500, 12213100,
  12155500 (`parameter_code=00065`), Aug–Sep 2025 and Dec 2025. **The legacy
  `waterservices.usgs.gov/nwis/iv` endpoint returned an empty body for 12200500 and had to be replaced
  by the OGC API** — consistent with the decommission noted in `DATA_SOURCES.md`.

**Cited but not independently fetched (paywall, 403, or search-summary only) — treat as INFERENCE**

- Zscheischler, Martius, Westra, Bevacqua, Raymond, Horton et al. (2020), "A typology of compound weather and climate events", *Nature Reviews Earth & Environment* 1, 333–347 — https://www.nature.com/articles/s43017-020-0060-z
- Wahl, Jain, Bender, Meyers, Luther (2015), "Increasing risk of compound flooding from storm surge and rainfall for major US cities", *Nature Climate Change* 5, 1093–1097 — https://www.nature.com/articles/nclimate2736
- Williams, Horsburgh, Williams, Proctor (2016), "Tide and skew surge independence: New insights for flood risk", *GRL* 43 — https://agupubs.onlinelibrary.wiley.com/doi/full/10.1002/2016GL069522
- Santamaria-Aguilar & Vafeidis (2018), "Are Extreme Skew Surges Independent of High Water Levels in a Mixed Semidiurnal Tidal Regime?", *JGR Oceans* — https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2018JC014282
- Moftakhari, Salvadori, AghaKouchak, Sanders, Matthew (2017), "Compounding effects of sea level rise and fluvial flooding", *PNAS* 114(37), 9785–9790 — https://pubmed.ncbi.nlm.nih.gov/28847932/
- Bevacqua, Maraun, Vousdoukas, Voukouvalas, Vrac, Mentaschi, Widmann (2019), "Higher probability of compound flooding from precipitation and storm surge in Europe under anthropogenic climate change", *Science Advances* 5 — https://www.science.org/doi/10.1126/sciadv.aaw5531
- Grossman, Tehranirad, Nederhoff, Crosby, Stevens, VanArendonk, Nowacki, Erikson, Barnard (2023), "Modeling Extreme Water Levels in the Salish Sea: The Importance of Including Remote Sea Level Anomalies", *Water* 15, 4167 — https://www.mdpi.com/2073-4441/15/23/4167 (**HTTP 403 to both WebFetch and browser-UA curl**)
- "Dynamic Modeling of Coastal Compound Flooding Hazards Due to Tides, Extratropical Storms, Waves, and Sea-Level Rise: A Case Study in the Salish Sea, Washington (USA)", *Water* 16, 346 (2024) — https://www.mdpi.com/2073-4441/16/2/346 (**HTTP 403**)
- Grossman, VanArendonk, Crosby, Tehranirad, Nederhoff, Barnard, Erikson, Danielson (2024), Whatcom County coastal flood hazard projections, USGS data release **DOI 10.5066/P9I08NS5** (CMGDS metadata pages returned **HTTP 403**)
- Montillet, Melbourne, Szeliga (2018), "GPS Vertical Land Motion Corrections to Sea-Level Rise Estimates in the Pacific Northwest", *JGR Oceans* — https://agupubs.onlinelibrary.wiley.com/doi/full/10.1002/2017JC013257
- "Increased flood exposure in the Pacific Northwest following earthquake-driven subsidence and sea-level rise", *PNAS* (2025) — https://www.pnas.org/doi/10.1073/pnas.2424659122
- Sweet, Dusek, Obeysekera, Marra (2018), *Patterns and Projections of High Tide Flooding Along the U.S. Coastline Using a Common Impact Threshold*, NOAA Tech. Rep. NOS CO-OPS 086 — https://tidesandcurrents.noaa.gov/publications/techrpt86_PaP_of_HTFlooding.pdf
- Grossman et al. (2020), "Sediment export and impacts associated with river delta channelization compound estuary vulnerability to sea-level rise, Skagit River Delta", *Marine Geology* 430, 106336
- Crosby et al. (2023), efficient modelling of wave generation and propagation in an estuary, *Ocean Modelling* 184, 102231 — PDF hosted by skagitclimatescience.org
- Qwuloolt Estuary Restoration Project, "Rivers and Tides" — tides influence the Snohomish "as far as 20 miles upstream" (https://www.qwuloolt.org/QwulooltEstuary/RiversAndTides)
- Salish Sea Wiki, *Puget Sound Tidal Restriction and Tidally Influenced Extent Mapping* — https://salishsearestoration.org/wiki/Puget_Sound_Tidal_Restriction_and_Tidally_Influenced_Extent_Mapping (**HTTP 403**)
