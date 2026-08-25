# Measured non-stationarity that corrupts the platform's own reference distributions

*Corpus entry, 2026-08-24. Part of the Cascadia Papsukkal flood-science corpus.*
*Supersedes the 2026-08-24 draft titled "Climate change: forcing intensification and PNW hydrologic
response", which was framed around century-scale projections. That framing was wrong for this
platform and the file has been rebuilt around measurement. All projection material now sits behind
the fence in Appendix P.*

*Labels follow the repository convention: **FACT** = read on a page I fetched, or computed by me from
a primary dataset I fetched (URL and method given); **INFERENCE** = reasoned from cited facts;
**ASSUMPTION** = a working simplification; **OPEN QUESTION** = unresolved. Where a paywall or bot wall
blocked me, the claim is marked "not independently fetched" and demoted to INFERENCE. Consensus is
marked **established / emerging / contested** per claim.*

---

## 0. Scope, and why the projection literature is fenced off

The platform's test is a 6–120 h flood forecast for the Skagit, Snoqualmie, Skykomish/Snohomish,
Stillaguamish, Nooksack, Green, White and Cedar. A finding earns a place here only if it changes that
forecast or changes a number the forecast is compared against.

Century-scale hydrologic projections fail that test **by the repository's own existing rules**, not by
a new editorial preference:

1. `DATA_DOCTRINE.md` §11 requires every value to carry an `available_at` knowledge time and requires
   replay to select rows with `available_at ≤ T`. A projection of the 2080s has no knowledge time in
   any operational sense — it is not a value that became retrievable at an instant and then aged; it is
   a statement about a distribution 60 years out. It cannot participate in `as_known_at(T)`.
2. `DATA_DOCTRINE.md` §9 forbids printing a probability without a calibrated, hindcast-evaluated
   method. A projection cannot be verified at a 6–120 h lead time — there is no forecast-verification
   pair to build a reliability diagram from.
3. `DATA_DOCTRINE.md` §2 puts a GCM/RCM/hydrologic-model chain at **MODELED** at best, and a
   Cascade-derived statement built on one at **EXPERIMENTAL**. Neither may be badged OFFICIAL, and
   neither may enter a threshold, a percentile, or a hazard computation.

So the exclusion is the existing epistemics applied consistently. Appendix P retains the projection
material as *reference literature about the direction of drift*, fenced, with scenario, ensemble and
compounded uncertainty attached to every number, and explicitly barred from every surface.

What **is** in scope, and is what this file is about: things instruments have already measured, and
the ways those measurements corrupt the reference distributions the platform ranks live values against.

---

## 1. Headline

**The platform ranks today's flow against a day-of-year climatological ladder, and I measured that
ladder's instability directly on all ten of the gauges the platform actually reads. The dominant
corruption is not climate drift — it is estimation variance. Rebuilding the ladder from 20 years
instead of the full record moves 13–17 % of daily observations into a different susceptibility band
*with no trend involved at all* (year-label permutation null, 300 draws per gauge). Climate drift adds
a further 0 to +7 percentage points on top, and that excess is statistically distinguishable from the
sampling null at only 4 of 10 gauges. A change of regulation regime moves more than either: splitting
the Green and Skagit records at their major-impoundment dates shifts the ranking by a mean of 9.9–11.1
percentile points and flips 29–32 % of days.**

Three consequences follow, and they are the operational content of this file:

- **The reference period must be the longest *homogeneous* record, not the most recent one.** At every
  ladder length I tested, the variance penalty of shortening exceeds the bias penalty of including
  older climate. Homogeneity — not recency — is the binding constraint, and homogeneity is broken by
  gauge datum epochs, rating revisions and operating-rule changes far more violently than by warming.
- **A percentile is not a number until it carries a sampling interval and a period.** A 30-year ladder
  estimates a mid-winter day-of-year percentile with a sampling SD of **5.5–6.2 percentile points**; a
  10-year ladder, **~12 points**. The platform's band edges are 25/75/90. A value within one SD of an
  edge is not resolvable into a band, and the surface currently pretends it is.
- **The ladder is blind in the tail, which is where floods live.** The stored ladder stops at p95 and
  clamps. During the December 2025 record event the Sauk read exactly p95 / VERY_HIGH on 9, 10, 11 and
  12 December at 24,900 → 41,500 → 62,600 → 21,100 cfs — a 2.5× range in flow with **zero** percentile
  discrimination. The Skykomish read p95 at 36,100 and at 79,700 cfs. Flows up to **5.0×** the p95
  ladder value have been observed since 2016.

Separately, and pointing the same way: the observing network itself contains steps that dwarf any
climate signal. The USGS annual-peak stage record at Snoqualmie near Carnation — one of the platform's
own configured susceptibility gauges — contains a **41.26 ft** datum discontinuity between the 1939
and 1940 water years. At Skagit near Mount Vernon the same discharge has been recorded at stages
differing by **3.14 ft** (138,000 cfs at 33.85 ft on 2006-11-07; 127,000 cfs at 36.99 ft on 2021-11-16)
against an NWS category spacing of **2 ft**.

---

## 2. Mechanisms

### 2.1 What a day-of-year percentile actually estimates, and its two error terms

The platform's `method:streamflow-doy-climatology@1.0.0` builds, for each day-of-year key `k`, an
empirical ladder from all approved daily means falling in a ±2-day window over a reference period of
`L` years, then ranks today's value by linear interpolation between order statistics. Write the
estimated rank of a value `x` as `P̂_L(x, k)`. It has two errors relative to the quantity a reader
believes they are being told:

```
P̂_L(x,k) − P_true(x,k,today)  =  [ P̂_L − E(P̂_L) ]   +   [ E(P̂_L) − P_true ]
                                   sampling error        drift / heterogeneity bias
                                   ~ 1/sqrt(n_eff)       ~ period-mean offset
```

with `n_eff` the number of **effectively independent** values in the window — not `n = 5L` days,
because the ±2-day window is serially correlated (a five-day block on a river is close to one
observation) and because adjacent years are weakly correlated through decadal modes.

Everything below is a measurement of the two terms on this platform's own gauges.

**Method for every computed number in §2.2–§2.5.** USGS NWIS daily mean discharge
(`https://waterservices.usgs.gov/nwis/dv/?format=rdb&sites=<site>&parameterCd=00060&statCd=00003`),
fetched 2026-08-24. Ladders rebuilt with the platform's exact convention — approved values only,
±2-day window with year-boundary wrap, R type-7 interpolation between order statistics, `min_sample`
10 — and banded on the platform's exact edges `[25, 75, 90]`
(`packages/hydrology/src/cascade_hydrology/susceptibility.py`). Test observations are every approved
daily mean from 2016 onward. **FACT, computed.**

### 2.2 The sampling term, measured: a short ladder is wrong even in a stationary world

The control the previous draft of this file lacked. For each gauge I drew `L` **random, non-contiguous
years** from the whole period of record — which destroys any trend while preserving the sample size —
built a ladder, and counted how many 2016–2026 daily observations land in a different susceptibility
band than they do against the full-record ladder. 300 draws per gauge.

| Gauge | observed flip rate, 2006–2025 ladder | null median | null 95th | null 99th | permutation p |
|---|---|---|---|---|---|
| Sauk nr Sauk 12189500 (**unregulated**) | **19.7 %** | 13.7 % | 17.2 % | 19.5 % | **0.007** |
| Skykomish nr Gold Bar 12134500 | **20.2 %** | 13.8 % | 17.3 % | 19.7 % | **0.003** |
| Sauk ab Whitechuck 12186000 | **20.1 %** | 13.8 % | 17.7 % | 21.1 % | **0.020** |
| Cedar at Renton 12119000 | **24.5 %** | 17.4 % | 23.1 % | 27.0 % | **0.030** |
| NF Stillaguamish 12167000 | 17.1 % | 13.3 % | 17.1 % | 20.1 % | 0.050 |
| Green nr Auburn 12113000 | 20.2 % | 16.0 % | 21.1 % | 25.8 % | 0.080 |
| SF Snoqualmie North Bend 12144500 | 15.7 % | 13.4 % | 17.1 % | 19.3 % | 0.120 |
| Nooksack at Ferndale 12213100 | 14.2 % | 12.8 % | 15.6 % | 17.2 % | 0.187 |
| Skagit nr Mount Vernon 12200500 (regulated) | 16.8 % | 15.0 % | 19.4 % | 22.6 % | 0.223 |
| Snoqualmie nr Carnation 12149000 | 14.7 % | 14.7 % | 18.3 % | 22.0 % | 0.490 |

**FACT, computed 2026-08-24.** Read the null column first: **12.8 %–17.4 % of daily observations change
band purely because the ladder was estimated from 20 years instead of ~90, with the trend removed by
construction.** The recent-window excess over that null is real but secondary, and is distinguishable
from noise at four gauges (Sauk, Skykomish, upper Sauk, Cedar), marginal at one (NF Stillaguamish) and
absent at five.

The previous draft of this file reported the Sauk's 19.4 % figure as a climate-vintage effect. **That
attribution was wrong.** Roughly two-thirds of it is sampling. The correction does not weaken the
operational conclusion — it strengthens it, because sampling error is present at *every* gauge whereas
the trend is present at four.

### 2.3 The variance–bias curve, and the reference-period rule it implies

Same construction, sweeping ladder length `L`. "Null" = random `L` years; "recent" = the most recent
contiguous `L` years, which carries both sampling error and drift.

| Gauge | L | null median flip % | null median mean\|ΔP\| | recent-L flip % | recent-L mean\|ΔP\| |
|---|---|---|---|---|---|
| Sauk 12189500 | 10 | 20.2 | 6.7 | 32.7 | 12.0 |
| | 20 | 14.1 | 4.6 | 19.4 | 7.0 |
| | 30 | 10.6 | 3.5 | 17.2 | 6.2 |
| | 50 | 6.9 | 2.3 | 11.4 | 3.8 |
| Snoqualmie 12149000 | 10 | 22.0 | 7.3 | 28.8 | 10.6 |
| | 20 | 14.8 | 4.8 | 15.4 | 5.5 |
| | 30 | 11.4 | 3.7 | 11.6 | 4.1 |
| | 50 | 7.3 | 2.4 | 8.3 | 2.8 |
| Cedar 12119000 | 10 | 25.6 | 8.1 | 27.5 | 8.8 |
| | 30 | 13.2 | 4.0 | 21.3 | 6.3 |
| | 50 | 7.9 | 2.4 | 14.1 | 4.9 |
| Skykomish 12134500 | 10 | 21.2 | 6.9 | 32.3 | 11.9 |
| | 30 | 10.8 | 3.6 | 17.5 | 6.0 |
| | 50 | 6.7 | 2.3 | 12.7 | 4.1 |

**FACT, computed.** Both curves fall monotonically with `L`, and **at no tested length does shortening
the ladder reduce total error.** On the Cedar — the gauge with the largest drift signal — going from a
50-year to a 30-year ladder trades a null mean error of 2.4 → 4.0 percentile points to chase a bias
term worth at most a few points. That is a bad trade. **INFERENCE from the computed table; the rule
"prefer the longest homogeneous record" follows directly, and it is the opposite of the intuition that
a warming climate demands a recent baseline.**

**Adversarial-review caveat added 2026-08-24 (independent reproduction).** The error metric in this
table is *distance from the full-record ladder*, which makes `L = full record` optimal **by
construction** — the monotone fall of both curves with `L` is arithmetic, not evidence, and "at no
tested length does shortening reduce total error" is therefore not a finding. A reviewer re-tested the
same question with a non-circular, out-of-sample criterion (rolling-origin: build the ladder from years
before a held-out decade, then score how close the *empirical* exceedance frequency of that decade's
daily flows is to each ladder point's nominal frequency; 10 gauges × 3 held-out decades). Under that
criterion the conclusion survives — full-record mean calibration error **3.42** points vs **3.98** for
the most recent 30 years and **5.04** for the most recent 20 — but only on average across decades: a
recent-30 ladder beat the full record at **10 of 10** gauges on the 2016–2025 holdout and lost at
essentially all of them on 2006–2015, which is the PDO-phase effect §5 describes. **The rule in §6.4 is
supported; the evidence in this table does not by itself support it.**

The caveat that saves the intuition from being simply wrong: this holds because the western Washington
drift is *small relative to interannual variance*. It would not hold on a variable with a large
signal-to-noise ratio (a tide gauge, §2.7) or across a step discontinuity (§2.5, §2.6).

### 2.4 The percentile's own sampling interval — the number the UI is missing

For a fixed value (the full-record p50 for that day) I resampled `L` random years 400 times and took
the SD of the estimated percentile.

| Gauge | day | value (cfs) | L = 10 | L = 20 | L = 30 | L = 50 |
|---|---|---|---|---|---|---|
| Sauk 12189500 | 15 Nov | 3,610 | **±12.1** | ±7.7 | ±6.2 | ±4.0 |
| Sauk 12189500 | 15 Jan | 3,440 | ±12.3 | ±8.1 | ±5.8 | ±3.5 |
| Snoqualmie 12149000 | 15 Nov | 3,640 | ±11.9 | ±7.3 | ±5.6 | ±3.9 |
| Snoqualmie 12149000 | 15 Jan | 4,030 | ±12.0 | ±7.6 | ±5.5 | ±3.6 |

(SD of the estimated percentile, percentile points, **FACT, computed**.) The interquartile range on the
Sauk at 15 November with a 10-year ladder is **p41.0–p58.3** for a value whose true rank is p50.

Set this against `BAND_EDGES = [25, 75, 90]`. A 30-year ladder — the WMO standard normal length — puts
a ±5.5–6.2 point uncertainty on the number that decides whether the surface says MODERATE or HIGH.
**The banding is not resolvable near an edge, and the platform currently renders it as if it were.**

### 2.5 The ladder saturates during floods — the p95 clamp

`PERCENTILES = (5, 10, 25, 50, 75, 90, 95)` and `percentile_of` clamps at the ends with an
`outside_climatology_range` flag. That is the honest choice given the stored ladder (inventing p99.4
from a p95 anchor would be fabrication), but the consequence is severe and I measured it.

| Gauge | days ≥ p95, 2016–2026 | % of all days | % of Oct–Feb days | largest observed flow ÷ p95 |
|---|---|---|---|---|
| Sauk 12189500 | 195 | 5.2 % | 6.9 % | **4.7×** (2026-03-20, 37,200 vs p95 7,893) |
| Skykomish 12134500 | 178 | 4.7 % | 6.7 % | **5.0×** (2026-03-20, 42,600 vs p95 8,485) |
| Cedar 12119000 | 173 | 4.8 % | 5.3 % | 4.0× |
| Skagit Mount Vernon 12200500 | 163 | 4.3 % | 6.7 % | 2.8× |
| NF Stillaguamish 12167000 | 136 | 3.7 % | 5.5 % | 4.7× |
| Nooksack Ferndale 12213100 | 126 | 3.4 % | 5.3 % | 3.5× |
| Green nr Auburn 12113000 | 124 | 3.4 % | 5.3 % | 2.5× |
| Snoqualmie Carnation 12149000 | 131 | 4.0 % | 6.6 % | 4.4× |

**FACT, computed.** The December 2025 event, day by day, as the surface would have shown it:

| Gauge | date | flow (cfs) | ladder p75 | p90 | p95 | percentile shown | band |
|---|---|---|---|---|---|---|---|
| Sauk 12189500 | 2025-12-05 | 2,740 | 5,470 | 8,696 | 11,330 | 30.8 | MODERATE |
| | 2025-12-07 | 7,170 | 5,520 | 8,028 | 9,719 | 84.9 | HIGH |
| | 2025-12-09 | 24,900 | 5,575 | 8,630 | 10,900 | **95.0** | VERY_HIGH |
| | 2025-12-10 | 41,500 | 5,660 | 8,786 | 11,260 | **95.0** | VERY_HIGH |
| | 2025-12-11 | **62,600** | 5,815 | 9,282 | 13,630 | **95.0** | VERY_HIGH |
| | 2025-12-12 | 21,100 | 5,950 | 9,456 | 13,800 | **95.0** | VERY_HIGH |
| Skykomish 12134500 | 2025-12-09 | 36,100 | 5,548 | 9,012 | 12,255 | **95.0** | VERY_HIGH |
| | 2025-12-10 | **79,700** | 5,595 | 9,683 | 16,250 | **95.0** | VERY_HIGH |

**FACT, computed.** The surface has no dynamic range across the entire flood. It also cannot fall: it
reads VERY_HIGH on the day the Sauk recedes to 21,100 cfs exactly as it did at 62,600 cfs. A related
and reassuring null result: including the December 2025 water year in the ladder changes those
percentiles by **+0.0** points, because the clamp absorbs it — so the self-reference concern is real in
principle but inert here, and would bite in the p75–p90 range instead.

### 2.6 The seasonal shape of the ladder is itself drifting — measured

A day-of-year ladder assumes the seasonal *shape* is stationary. It is not. Center of timing (day of
water year at 50 % cumulative flow) and the Oct–Feb share of annual flow, Mann–Kendall with tie
correction and Sen slope, complete water years only:

| Gauge | n WY | period | CT τ | CT p | CT days/decade | Oct–Feb share τ | p | pts/decade | mean share |
|---|---|---|---|---|---|---|---|---|---|
| Skagit nr Mount Vernon 12200500 | 85 | 1941–2025 | −0.303 | **0.0002** | **−4.63** | +0.262 | **0.0004** | +0.95 | 42.5 % |
| Skykomish nr Gold Bar 12134500 | 97 | 1929–2025 | −0.215 | **0.002** | −3.55 | +0.189 | **0.006** | +0.95 | 42.9 % |
| Sauk nr Sauk 12189500 | 97 | 1929–2025 | −0.217 | **0.002** | −2.95 | +0.211 | **0.002** | +0.89 | 38.5 % |
| Sauk ab Whitechuck 12186000 | 101 | 1918–2025 | −0.181 | **0.007** | −2.45 | +0.167 | **0.013** | +0.74 | 38.6 % |
| NF Stillaguamish 12167000 | 97 | 1929–2025 | −0.201 | **0.004** | −2.33 | +0.187 | **0.007** | +0.86 | 55.5 % |
| Green nr Auburn 12113000 | 89 | 1937–2025 | −0.140 | 0.052 | −1.79 | +0.144 | **0.046** | +0.73 | 52.9 % |
| Cedar at Renton 12119000 | 80 | 1946–2025 | −0.147 | 0.054 | −2.09 | +0.125 | 0.103 | +0.76 | 53.5 % |
| Snoqualmie Carnation 12149000 | 95 | 1930–2024 | −0.131 | 0.061 | −1.75 | +0.105 | 0.134 | +0.45 | 49.9 % |
| Nooksack Ferndale 12213100 | 58 | 1967–2025 | −0.143 | 0.115 | −2.97 | +0.131 | 0.147 | +0.75 | 47.7 % |
| SF Snoqualmie North Bend 12144500 | 68 | 1903–2024 | −0.099 | 0.236 | −1.89 | +0.057 | 0.495 | +0.33 | 48.3 % |

**Adversarial-review caveat added 2026-08-24.** The largest shift in this table, Skagit nr Mount
Vernon (−4.63 d/decade), is at the platform's *most regulated* gauge, and its record (from WY1941)
straddles Ross Dam's staged completion (1949–1953) and Upper Baker (1959) — winter drawdown and
release move the centre of timing earlier for reasons that are not climate. Restricted to WY1961+
the Skagit MV trend weakens to −2.91 d/decade and loses significance (p = 0.063), while on the
*unregulated* Sauk the same restriction **strengthens** the trend (−4.11 d/decade, p = 0.023) as it
does at Skykomish and NF Stillaguamish. The regional signal is robust; the Skagit MV number should
not be read as a climate shift, and using it as the header row of this table overstates the case.

**FACT, computed 2026-08-24. Established** as a regional signal (it is the Pacific-Northwest expression
of the earlier-spring-pulse literature — Stewart et al. 2005, Cayan et al. 2001, **not independently
fetched**). Note the ordering: the **snow-influenced** gauges (Skagit, Skykomish, both Sauks,
Stillaguamish) carry it significantly; the **rain-dominated lowland** gauges (SF Snoqualmie,
Snoqualmie at Carnation, Nooksack) do not. That is the physically expected pattern — phase shift
requires snow to shift — and its presence is evidence the signal is not an artefact.

This is the mechanism by which drift enters the ladder: at ~3 days per decade over a 97-year record,
the earliest and latest years in the same day-of-year sample are separated by roughly **a month of
seasonal phase**, and on the Sauk the full-record median flow between 15 October (2,000 cfs) and 15 November
(3,610 cfs) differs by **+80 %**. The ±2-day window cannot see this; it is a within-sample heterogeneity,
not a window-width problem. **INFERENCE from the two computed results.**

**Adversarial-review correction 2026-08-24: this inference overstates its own magnitude by about an
order of magnitude.** A centre-of-timing shift is dominated by the *snowmelt* half of the water year
and is not a uniform phase shift of the whole hydrograph, so the +80 % 15 Oct → 15 Nov seasonal
gradient is not the size of the within-key drift. Measured directly on the Sauk (annual median of the
±2-day window, Mann–Kendall): **15 Nov τ = +0.129, p = 0.059, first-half → last-half +8 %**; **15 Jan
τ = +0.167, p = 0.015, +9 %**; **15 Oct τ = −0.019, p = 0.783, −18 % (opposite sign, not
significant)**. The mechanism is real and the sign is as expected in mid-winter, but the within-key
heterogeneity it produces at these day-of-year keys is of order **±10 %** in flow, not 80 % — well
inside the sampling term measured in §2.2–§2.4, which is the file's own headline finding.

### 2.7 Local relative sea level is a vertical-land-motion measurement, not a global one

For the Skagit, Nooksack and Snohomish deltas the operational input is the *local* tide-gauge trend.
I computed it from NOAA CO-OPS deseasonalised monthly mean sea level
(`https://tidesandcurrents.noaa.gov/sltrends/data/<id>_meantrend.txt`), OLS with a lag-1
autocorrelation inflation of the standard error.

| Station | id | period | trend (mm yr⁻¹) | AR(1)-adjusted 95 % CI | lag-1 ρ | ft/century |
|---|---|---|---|---|---|---|
| **Cherry Point** (nearest the Nooksack delta) | 9449424 | 1973–2025 | **−0.06** | **[−0.64, +0.52]** | 0.43 | −0.02 |
| Friday Harbor | 9449880 | 1934–2025 | +1.19 | [+0.96, +1.42] | 0.40 | +0.39 |
| Port Townsend | 9444900 | 1972–2025 | +1.80 | [+1.24, +2.36] | 0.43 | +0.59 |
| Seattle | 9447130 | 1899–2025 | +2.09 | [+1.96, +2.23] | 0.39 | +0.69 |

**FACT, computed 2026-08-24; my slopes reproduce NOAA's own published trend line in the same files to
within 0.02 mm yr⁻¹ at all four stations.** **Established.**

**Cherry Point's relative sea level trend is statistically indistinguishable from zero**, while Seattle
115 km away rises at 2.09 mm yr⁻¹ with a tight interval. The difference — **2.15 mm yr⁻¹, 0.71 ft per
century across ~150 km of one inland sea** — is vertical land motion, not ocean. Puget Sound sits on a
subduction margin: interseismic strain, glacial isostatic adjustment and delta sediment compaction all
act, and their sum reverses sign within the domain. Reported GPS/levelling assessments put
southern Puget Sound at ~0.5–1.0 mm yr⁻¹ subsidence and the Skagit delta at ~0–1 mm yr⁻¹ deep subsidence
([Skagit Climate Science Consortium](https://www.skagitclimatescience.org/skagit-impacts/sea-level-rise/);
Newton et al. 2021, *Water* 13(3), 281; Montillet et al. 2018, *JGR-Oceans* — **neither independently
fetched**, INFERENCE for the GPS numbers, FACT for the tide-gauge numbers I computed).

**Operational reading: a single regional or global sea-level number applied to Ferndale as a downstream
boundary condition would be wrong by ~2 mm yr⁻¹ in the direction of over-warning. The measured local
trend at the nearest gauge is the only defensible input, and at Cherry Point that input is "no
detectable trend, CI ±0.6 mm yr⁻¹".**

### 2.8 Clausius–Clapeyron is a constraint on moisture, and only on moisture

```
d(ln e_s)/dT = L_v / (R_v T²)     L_v ≈ 2.5 × 10⁶ J kg⁻¹,  R_v = 461.5 J kg⁻¹ K⁻¹
```

At `T ≈ 288 K` this gives **≈ 6.5–7 % K⁻¹** for saturation vapour pressure, and under near-constant
relative humidity over the ocean, column water vapour scales at the same rate (FACT, textbook
thermodynamics; restated as `dq/dT ≈ 0.07 q` in the
[Yakima County BAS compilation](https://www.yakimacounty.us/DocumentCenter/View/43010/Clausius_Clapeyron_Atmospheric_Rivers_BAS_Research_DRAFT-12172025-ksw),
fetched). **Established.**

**Precipitation is not vapour, and flood response is not precipitation.** Point precipitation intensity
scales as `P ≈ w · q · ε` — vertical mass flux × specific humidity × efficiency — and only `q` is
CC-constrained; `w` is dynamic. Observations depart from CC in **both** directions:

- **Above CC:** hourly extremes in convective regimes scale at ~2× CC (~14 % K⁻¹) against dew point.
  [Da Silva & Haerter 2025, *Nat. Geosci.* 18, 382–388](https://pmc.ncbi.nlm.nih.gov/articles/PMC12074990/)
  (fetched) show, from 514 German stations at 10-minute resolution 2005–2020 with EUCLID lightning
  pairing, that stratiform and convective extremes **each scale at approximately CC in isolation**
  while the convective fraction rises at **β ≈ 41 % °C⁻¹**; the mixing alone reproduces the apparent
  super-CC. This is a **rain-type composition artefact**, not thermodynamic invigoration, in that
  dataset. **Emerging → established for the mechanism; contested as a universal claim.**
- **Below CC, and in the platform's own basins:** the observed AR response is far below CC.
  [Henny & Kim 2025, *J. Climate* 38(6)](https://cawaterlibrary.net/wp-content/uploads/2025/04/clim-JCLI-D-24-0234.1-1.pdf)
  (abstract fetched), across ARTMIP Tier-2 detectors on ERA5/MERRA-2/JRA-55 over 1980–2019/2023:
  AR area **+6 % to +9 %**, AR **IWV +1.5 % to +2.5 %**, AR **IVT < +1 %**, with 850-hPa wind speed and
  vertically-integrated moisture-flux convergence both **decreasing**. Restricted to the most intense
  AR grid points: IVT **+3–4 %**, IWV **+4–6 %**, VIMFC **+6–10 %**. Verbatim caution from the same
  abstract: *"further research is required to determine the extent to which these trends are affected
  by reanalysis observational assimilation changes."* **FACT for the numbers; emerging for attribution.**

So over 40 years of reanalysis, the quantity the platform actually badges — **IVT — has risen by less
than 1 %.** The correct statement is: *CC bounds the moisture term from below in a warming atmosphere;
it says nothing about what the platform will observe on any given basin at any given lead time, and the
measured AR record does not follow it.* Importing a "7 % per degree" or "14 % per degree" factor into a
western Washington design storm or threshold is unsupported in **both** directions. **Established as a
framing; the specific transfer is unsupported.**

---

## 3. Quantitative anchors

| Quantity | Value | Context | Source |
|---|---|---|---|
| **Band-flip rate from ladder length alone, no trend** | **12.8–17.4 %** of daily observations | random 20-year ladder vs full-record ladder, 10 gauges, 300 draws each | computed 2026-08-24, USGS NWIS dv |
| **Excess flip rate attributable to recency** (trend, decadal phase and undocumented epoch changes, not separable) | **0 to +7.1 points**; distinguishable from null at **4 of 10** gauges | 2006–2025 ladder vs null; p = 0.003–0.05 at Sauk, Skykomish, upper Sauk, Cedar; p = 0.08–0.49 at the rest | same |
| **Flip rate from a regulation-regime split** | **29.2 %** (Green, split 1962), **32.2 %** (Skagit MV, split 1959); mean shift **9.9 / 11.1** points | larger than any climate-vintage effect measured; pre-split ladders are short (26 / 19 yr) so part is sampling — the **mean shift** and p90 structure are not | computed 2026-08-24 |
| **Sampling SD of an estimated day-of-year percentile** | **±12.1** (L=10), **±7.7** (L=20), **±6.2** (L=30), **±4.0** (L=50) percentile points | Sauk, 15 Nov, at the full-record p50; band edges are 25/75/90 | computed 2026-08-24 |
| **Interquartile range of that estimate at L = 10** | **p41.0 – p58.3** for a value whose true rank is p50 | | same |
| **p95 clamp saturation** | **3.4–5.2 %** of all days, **5.3–6.9 %** of Oct–Feb days; observed flows to **5.0×** the p95 value | the surface has no resolution in the flood range | computed 2026-08-24 |
| **December 2025, Sauk** | p95 / VERY_HIGH at 24,900 / 41,500 / **62,600** / 21,100 cfs on 9–12 Dec | 2.5× flow range, 0.0 percentile range | same |
| **Center-of-timing shift** | **−1.75 to −4.63 days per decade**; significant (p ≤ 0.007) at 5 of 10 gauges, all snow-influenced | day of water year at 50 % cumulative flow | computed 2026-08-24 |
| **Oct–Feb share of annual flow** | **+0.33 to +0.95 points per decade**; significant at 5 of 10 | | same |
| **Sauk annual-peak trend, period dependence** | WY1912–2025 (n=98) τ = +0.198, **p = 0.004**; WY1976–2025 (n=50) τ = +0.007, **p = 0.953** | the same record, two windows, opposite conclusions | computed 2026-08-24, USGS peak file |
| **Regulated contrast, same statistic** | Skagit nr Mount Vernon WY1907–2025 (n=86) τ = +0.024, **p = 0.748**; Sauk truncated to WY1941–2025 (n=85) still τ = +0.202, **p = 0.006** | the contrast is not an artefact of unequal record length. It is a **two-gauge correlation**, not a demonstrated mechanism — Mount Vernon also drains a larger mixed basin and has no pre-regulation baseline | same |
| **Cascade April 1 SWE, period dependence** | **−23 %** (1930–2007, ~significant); **−48 %** (1950–1997, robust) of which **80 % circulation-driven**; **+19 %** (1976–2007, not significant); residual after removing Pacific variability **−2.0 % per decade** (−16 %, significant) | independent replication of the same period-dependence, on snow | [Stoelinga, Albright & Mass 2010, *J. Climate* 23](https://atmos.uw.edu/~cliff/SWEpaper_rev1_rendered.pdf) (fetched, full text) |
| Cascade SWE sensitivity to temperature | **−11 % per °C** | water-balance + radiosonde onshore-flow index | same |
| **WA SNOTEL April 1 SWE trend, 1979–2026** | **3 of 28** western/crest sites significant at p < 0.05 (2 negative, 1 **positive**); 17 of 28 τ < 0; **field p = 0.156** | **no field-significant trend.** Correlation-aware null: median 0, 95th percentile **7** sites — so the naive "5 % by chance" bar is wrong by a factor of five | computed 2026-08-24, NRCS AWDB REST, year-label permutation, 2000 draws |
| — the two significant declines | Blewett Pass 4,240 ft **−20.1 %/decade** (p < 0.001); Stampede Pass 3,850 ft **−10.1 %/decade** (p = 0.003) | | same |
| — the significant increase | Potato Hill 4,480 ft **+11.8 %/decade** (p = 0.011) | a network with significant trends of both signs over the same window | same |
| Western US snow-course decline, longer record | **−15 % to −30 %** (25–50 km³); **> 90 %** of sites declining, **33 %** significantly | **699 snow courses, 1955–2016** — a different network and a 24-year-longer window than SNOTEL | [Mote et al. 2018, *npj Clim Atmos Sci* 1, 2](https://www.nature.com/articles/s41612-018-0012-1) — **not independently fetched**, search summary |
| **Gauge datum discontinuity, Snoqualmie nr Carnation 12149000** | **+41.26 ft** step between WY1939 (peak 1938-12-08, 11.20 ft) and WY1940 (peak 1939-12-16, 52.46 ft) in the USGS annual-peak stage series | **a platform susceptibility gauge.** Residual SD of stage about a log-Q fit is 11.55 ft, range 46.29 ft — entirely datum, not physics | computed 2026-08-24, USGS peak file |
| **Stage–discharge scatter, Skagit nr Mount Vernon 12200500** | SD **0.68 ft**, residual range **4.08 ft** about a log-Q fit, n = 85 paired annual peaks 1906–2024 | **NWS category spacing there is 2 ft** (minor 28, moderate 30, major 32 ft) | computed 2026-08-24; categories from `api.water.noaa.gov/nwps/v1/gauges/MVEW1` |
| — largest inversion | **138,000 cfs at 33.85 ft** (2006-11-07, WY2007) vs **127,000 cfs at 36.99 ft** (2021-11-16, WY2022): more flow, **3.14 ft lower stage** | 15 years apart | same |
| — population drift in the relation | only **−4.4 %** in flow at 37 ft between pre-1980 (n=40) and 1980+ (n=45) log-linear fits | **corrects the repo's prior "~29 % less flow at 37 ft" figure**, which was a two-point comparison against the 1906 estimate (peak date recorded as `1906-11-00` — day unknown) | same |
| **SNOTEL temperature sensor step** | **+1.7 °C** in Tmin, **−0.5 °C** in Tmax, **−2.2 °C** in diurnal range, at sensor upgrade | Colorado upgrades 2004–2006, Montana 1997–2000; **affects the entire 11-state network incl. Washington**; propagates into **PRISM and DAYMET** | [Rangwala et al. 2015, WWA briefing](https://wwa.colorado.edu/sites/default/files/2021-08/Rangwalaetal2015.pdf) (fetched, full text), building on Oyler et al. 2015 |
| — regional artefact magnitude | western-region SNOTEL Tmin rose **~1.5 °C between 1997 and 2007**, inconsistent with NWS COOP stations over the same period | *"much of the signal related to the amplification of warming at high elevations in these studies is an artifact"* | same, verbatim |
| **SNOTEL SWE vs accumulated-precipitation inconsistency** | **44 % of 748** SNOTEL stations report at least one year with max SWE **greater than** accumulated precipitation | physically impossible; attributed to gauge undercatch and drifting snow | Meyer et al. 2012, *J. Hydrometeorol.* 13(6) — **403 at fetch**, search summary, INFERENCE |
| **Precipitation gauge undercatch of snow** | ~**90 %** caught at 1.3 m s⁻¹ wind; **~70 %** at 2.4–4.3 m s⁻¹; **~46 %** at 5.6 m s⁻¹ | correction factors for solid precipitation reach 30–330 mm yr⁻¹ (10–65 % of gauge total) depending on method | Fassnacht 2004, *Hydrol. Process.* 18 — **not independently fetched**, search summary, INFERENCE |
| **Relative sea level, Cherry Point** (Nooksack) | **−0.06 mm yr⁻¹**, 95 % CI **[−0.64, +0.52]**, 1973–2025 | **indistinguishable from zero** | computed 2026-08-24, NOAA CO-OPS |
| **Relative sea level, Seattle** | **+2.09 mm yr⁻¹** [+1.96, +2.23], 1899–2025 | | same |
| **Local RSL spread within Puget Sound** | **2.15 mm yr⁻¹ = 0.71 ft/century** between Cherry Point and Seattle, ~150 km apart | vertical land motion dominates; the global term is not the local input | same |
| Clausius–Clapeyron | **~7 % K⁻¹** saturation vapour pressure at ~288 K | a bound on **moisture**; precipitation and flood response are not required to follow it | thermodynamics; restated in Yakima County BAS (fetched) |
| **Observed AR IVT change, 1980–2023** | **< +1 %** (AR mean); **+3–4 %** for the most intense subset | AR area +6–9 %, IWV +1.5–2.5 %; 850-hPa wind and VIMFC **decreased** | [Henny & Kim 2025](https://cawaterlibrary.net/wp-content/uploads/2025/04/clim-JCLI-D-24-0234.1-1.pdf) (fetched) |
| Apparent super-CC hourly scaling | ~**2 × CC (~14 % K⁻¹)**, **explained by stratiform→convective mixing**; convective fraction β ≈ 41 % °C⁻¹ | Germany, 10-min, 2005–2020 — a convective regime, not ours | [Da Silva & Haerter 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12074990/) (fetched) |
| NOAA **Atlas 15** timeline | CONUS preliminary **Sept 2026**; published **2027**. Vol. 1 = present-day, **trend-aware**, replaces Atlas 14 | the design-storm layer under WA floodplain practice becomes officially non-stationary | [water.noaa.gov/about/atlas15](https://water.noaa.gov/about/atlas15) (fetched) |
| WMO standard normal definition | most recent 30-year period ending in a year ending in 0 (1991–2020, …), changed from non-overlapping periods at **Cg-17, 2015**; update recommended each decade | the external convention the platform's vintage labels should align to | [WMO-No. 1203](https://www.ncei.noaa.gov/data/normals-old/WMO/Guidelines%20for%20the%20Calculation%20of%20Climate%20Normals.WMO%20No1203_en.pdf) (PDF fetched but not text-extractable); definition from [WMO Climatological Normals](https://wmo.int/wmo-climatological-normals) and NCEI, **search summary — INFERENCE** |

---

## 4. What is settled, what is emerging, what is contested

### Settled

- **Atmospheric moisture rises at approximately the Clausius–Clapeyron rate.** Thermodynamics; not in
  dispute.
- **A percentile estimated from a short record has large sampling error, and that error is larger than
  the climate drift in these basins.** Computed here across 10 gauges with an explicit null (§2.2–2.4).
- **Streamflow timing in snow-influenced western Washington basins has shifted earlier**, by 2.3–4.6
  days per decade over ~90-year records, significantly at 5 gauges (§2.6). Consistent with the
  earlier-spring-pulse literature.
- **Relative sea level in Puget Sound is dominated by vertical land motion and varies in sign across
  the domain** (§2.7). Cherry Point ≈ 0, Seattle +2.09 mm yr⁻¹, both tightly estimated.
- **Observing-network changes produce steps far larger than any climate signal.** The 41.26 ft datum
  discontinuity at 12149000 and the +1.7 °C SNOTEL Tmin step are documented, not hypothetical.
- **Stage and discharge are not interconvertible at these gauges.** ±0.68 ft SD and a 3.14 ft inversion
  at Mount Vernon against 2 ft categories (§3).

### Emerging

- **The extremes of the AR population may be intensifying faster than the AR mean** (Henny & Kim: per-AR
  maximum IVT rising at 3–6× the AR-mean rate). If it holds, a fixed-IVT AR-scale category has a
  drifting exceedance frequency. Unverified independently.
- **Non-stationary precipitation-frequency standards as a routine operational input** — NOAA Atlas 15
  Vol. 1, CONUS preliminary September 2026, published 2027.
- **Reanalysis-assimilation change as a confound in observed AR trends** — flagged verbatim by the
  authors of the trend study itself.

### Contested

- **Whether Cascade snowpack decline is detectable, and over what window.** Stoelinga, Albright & Mass
  2010 (fetched) find −48 % over 1950–1997 of which **80 % is north-Pacific circulation**, +19 % over
  1976–2007, and a circulation-removed residual of −2.0 % per decade. Mote et al. 2018 find −15 % to
  −30 % since mid-century with 33 % of 699 snow courses significant. **My own computation on 28
  western/crest Washington SNOTEL sites finds no field-significant April 1 SWE trend over 1979–2026
  (field p = 0.156).** These are reconcilable rather than contradictory — different networks, different
  start years, and a correlation-aware null that is five times looser than the naive 5 % bar — but the
  reconciliation is not published and the disagreement is live. **The platform must not assert a local
  snowpack trend from its own SNOTEL feed.**
- **Whether landfalling AR frequency over the Pacific Northwest is changing at all.**
  [Pan et al. 2025, *npj Clim Atmos Sci* 8, 307](https://pmc.ncbi.nlm.nih.gov/articles/PMC12360949/)
  (fetched) report an *"AR increasing hole"* over the PNW — *"a region of little to no increase, or
  slight decrease"* — attributed to *"an anomalous anticyclone over northern North America"*, with PNW
  total winter precipitation showing *"a significant decrease of 22.3 mm per decade"*. Against this,
  [Scholz et al. 2025, *AGU Advances*](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2025AV001888)
  report a widespread 20th-century increase (**not independently fetched**, 403). ARTMIP Tier 2 finds
  **detector choice dominates model choice** as the uncertainty source. **Not reconciled. The platform
  must not assert a local AR-frequency trend in either direction.**
- **Whether super-CC precipitation scaling is physically real anywhere.** Da Silva & Haerter argue it is
  a rain-type mixing artefact; others maintain convective invigoration. Either way it does not transfer
  to a stratiform orographic regime.
- **Whether a 30-year normal is the right reference length for hydrologic percentiles at all.** WMO
  practice (30 years, decadal update) is a meteorological compromise for *stations with a seasonal
  cycle and modest autocorrelation*. My measurements say that for a daily-flow day-of-year ladder in
  these basins, 30 years costs ±5.5–6.2 percentile points of sampling error — larger than the drift it
  is meant to exclude. I found no operational hydrology guidance that resolves this; the drought-index
  literature (non-stationary SSI and similar) argues the opposite way for a different variable.

---

## 5. Western Washington specificity

**What transfers.**
- The **variance–bias argument** (§2.3) is generic arithmetic and transfers anywhere, but its *outcome*
  is regional: it favours long records here because western Washington drift is small relative to
  interannual variance. In a basin with a strong trend and low variance the answer would flip.
- **Observing-network artefact classes** (datum epochs, rating revisions, sensor upgrades, undercatch)
  are universal. The *specific* artefacts are local and must be enumerated per gauge, not assumed.
- **Stoelinga's period-dependence result is Cascade-specific and directly transferable** — it is the
  same phenomenon I measured on the Sauk peaks (p = 0.004 from 1912, p = 0.953 from 1976), on a
  different variable, by different authors, 16 years earlier. Two independent demonstrations that a
  30–50 year window here returns a PDO phase, not a climate trend.

**What transfers with caution.**
- **Mote et al. 2018's 33 %-of-sites-significant result.** The naive null it is compared against (5 %)
  ignores cross-site correlation. My permutation null on 28 correlated Washington sites puts the 95th
  percentile of the "significant site count" at **7 of 28 (25 %)**, not 5 %. Their 60-year snow-course
  network is a different and better-suited dataset than SNOTEL, and I am not refuting them — but a
  reader should not import "33 % significant" as though 5 % were the correct bar. **INFERENCE.**
- **European and continental-US super-CC results** (§2.8): different precipitation type entirely.
- **Non-stationary standardized-index methods** from the drought literature: built for a variable with
  a different signal-to-noise ratio and a different decision cost.

**Does not transfer.**
- **A regional or global sea-level rate applied to a specific delta.** Measured refutation in §2.7: the
  sign flips within the domain.
- **Reference-period recommendations derived from air-temperature normals.** Temperature has a high
  trend-to-noise ratio; daily flow on a maritime river does not.

**Purely local structure the literature will not give you.**
1. **Regulation epochs bound the usable record, and they matter more than climate.** Splitting the Green
   at 1962 and the Skagit at 1959 moves the ranking by 9.9–11.1 percentile points on average and flips
   29–32 % of days (§3). The exact operating-rule epochs for Howard Hanson, Mud Mountain, Ross/Diablo/
   Gorge, Baker and Chester Morse are **CONFIGURED seed data the platform does not yet carry**, and the
   ladder cannot be correctly bounded without them. The dates I used are approximate and are an
   **OPEN QUESTION**, not a FACT.
2. **The White at R St (12100490) has one vintage and therefore no vintage sensitivity — and no depth.**
   Its whole approved record is 2010–2026, so its "full period of record" ladder and its "2006–2025"
   ladder are nearly the same object (0.6 % flips). That is not stability; it is a 17-year ladder with
   ±8-point sampling error and no ability to detect anything. The seed already caps this basin's
   confidence at `low`; this measurement is the reason.
3. **Nooksack at Ferndale is tidally influenced** and the seed flags the daily mean as unchecked for
   tide contamination. Given §2.7 — Cherry Point RSL is flat — the *trend* risk there is small, but the
   *within-day* contamination question is unresolved and independent of climate.
4. **The Skagit outlet integrates a regulated upper basin and an unregulated Sauk.** The platform
   already reads the Sauk for Skagit susceptibility. The measurements here support that choice on two
   independent grounds: the Sauk carries a detectable century-scale peak trend (τ = +0.198, p = 0.004) and Mount Vernon
   does not (τ = +0.024, p = 0.748), and Mount Vernon's ladder is the one most disturbed by the
   regulation split (32.2 %).

---

## 6. What this means for Cascadia Papsukkal

### 6.1 (P0) A percentile must carry its period **and** its sampling interval

Required fields on any percentile-bearing `DerivedFeature`: `climatology_period_start`,
`climatology_period_end`, `climatology_n_years`, `climatology_n_effective`, and
`percentile_sampling_sd`. The last is computable at ladder-build time by the same resampling used in
§2.4 and costs nothing at read time. Render it: *"p78 ± 6 (30-year ladder, 1996–2025)"*, never a bare
p78. Given the measured ±5.5–6.2 points at L = 30, a bare percentile is a number without an error bar
in a system whose entire premise is that numbers carry their provenance.

Affects: `packages/contracts` (`DerivedFeature`), `packages/providers/usgs/…/climatology.py`,
`packages/hydrology/…/susceptibility.py`, `VISUALIZATION_CONTRACTS.md`.

### 6.2 (P0) The band must refuse to resolve near an edge

`band()` is currently a total function from a float to a level. It must become a function from
(percentile, sampling SD) to a level **or** to `UNKNOWN` with reason `within_sampling_error_of_band_edge`
when `|percentile − edge| < k · sd` (k = 1 as a starting, stated parameter). `DATA_DOCTRINE.md` §12
already says UNKNOWN is a legitimate state that must carry a reason; this is that rule applied to a
place where the platform currently manufactures false precision. The exit test is that a value at
p74 ± 6 does not render as MODERATE with the same confidence as a value at p50 ± 6.

### 6.3 (P0) Extend the ladder into the tail, or say the surface is saturated

Measured: the surface reads p95/VERY_HIGH across a 2.5× range of flow during the December 2025 event
and across 5–7 % of all Oct–Feb days (§2.5). Two changes, both cheap:

- Extend `PERCENTILES` to `(5, 10, 25, 50, 75, 90, 95, 98, 99, 99.5)` where the sample supports it
  (a 90-year ±2-day window has ~450 values, so p99 is the 4th-largest — publishable with its rank
  stated, refused below `min_sample_for_tail`).
- Publish, beside every clamped percentile, the **flow multiple**: `value ÷ ladder p95`, a DERIVED
  quantity with obvious provenance and no distributional assumption. It is the difference between
  "VERY_HIGH" and "VERY_HIGH, 4.6× the 95th percentile for this date".

Without this the susceptibility surface is least informative exactly when the platform exists.

### 6.4 (P1) The reference period is "longest homogeneous", and homogeneity is enumerated per gauge

The rule, with its justification:

> **Use the full period of record, truncated at the most recent homogeneity break.** A homogeneity
> break is: a gauge datum epoch change, a documented rating-revision epoch, a station relocation, or
> a change of upstream operating rule. It is **not** the passage of time.

Justification: §2.3 shows the variance penalty of shortening exceeds the drift bias at every tested
length; §2.6 shows the drift is real but slow; §3 shows a regulation split and a datum step are
order-of-magnitude larger discontinuities than either.

This requires new CONFIGURED seed data — a `homogeneity_epochs` block per station listing
`(start, end, reason, source)` — which the platform does not have. It is a bounded piece of work: 10
gauges, USGS station manuscripts and operator records. Until it exists, the platform is building
ladders across breaks it has not looked for.

### 6.5 (P1) A ladder rebuild is a **revision**, and replay must reproduce the ladder of its knowledge time

`DATA_DOCTRINE.md` §8 already makes recomputation under a new method version a new row, and §11 forbids
look-ahead. But a ladder rebuilt annually with one more year of data is *the same method version with
different inputs* — and a 2025 replay that reads today's ladder is using a baseline that did not exist
at T. Given the measured 4–8 percentile-point sensitivity to a single decade of ladder data, this is a
real look-ahead bias, not a theoretical one. `as_known_at(T)` must select the ladder row whose
`available_at ≤ T`, and there must be a test that a replay of December 2025 uses a ladder built before
December 2025. **This is a bug class, not a feature request.**

Set the rebuild boundary on a **published decadal schedule** aligned to the WMO convention (periods
ending in a year ending in 0), so the vintage is a stable citable object rather than a moving target,
while data continues to accumulate inside the current period.

### 6.6 (P1) Publish the vintage sensitivity as a disagreement signal — never a correction

Do **not** apply a trend adjustment to the ladder. It would be an uncalibrated method
(`DATA_DOCTRINE.md` §9), and §2.2 shows the adjustment would be chasing a term smaller than the noise
at six of ten gauges. Instead compute the same value against a second, explicitly named ladder (the
most recent WMO-aligned 30 years) and expose the signed difference as a
`climatology_vintage_sensitivity` driver. `DATA_DOCTRINE.md` §10 already establishes disagreement as
first-class information; this is that principle applied to reference data rather than to forecasts.

### 6.7 (P1) Never build a percentile or a trend on **stage** without a datum-epoch check

The 41.26 ft step at 12149000 is in the platform's own gauge list. `HYDROLOGY.md` §9 already requires a
datum on every stage series and refuses unrecorded comparisons — this measurement is the concrete
justification, and it extends the rule: **the refusal must apply within a single station's history,
not only across stations.** Add a contract test that a stage series spanning two datum epochs cannot be
aggregated into one climatology.

Related, and already correct: `HYDROLOGY.md` §9's "never derive one from the other". The measured
±0.68 ft SD and 3.14 ft inversion at Mount Vernon against 2 ft categories make this non-negotiable.
Record those numbers in the doctrine as the reason.

### 6.8 (P1) Correct the repository's stage–discharge drift figure

The prior pass carries "~29 % less flow for the same 37.00 ft stage between 1906 and 2021". That is a
two-point comparison, one point of which is a 1906 estimate whose peak date is recorded as
`1906-11-00` — the day is unknown, marking it an indirect historical estimate. The population-level
figure over 85 paired annual peaks is **−4.4 % at 37 ft** between pre-1980 and 1980+ log-linear fits.
Both should be stated: the drift is real and modest; the scatter (±0.68 ft) is what actually matters
operationally, and it is not a trend at all.

### 6.9 (P2) Relative sea level: use the nearest tide gauge's measured trend, per basin

Not a regional number, not a projection. Cherry Point for the Nooksack (**−0.06 ± 0.58 mm yr⁻¹, i.e.
no detectable trend**), and the nearest long-record gauge for the Skagit and Snohomish deltas with its
own measured value and CI. Where the CI includes zero the platform should say so rather than apply a
small positive number for tidiness. The 2.15 mm yr⁻¹ spread across the domain (§2.7) is the measurement
that forbids a single regional constant.

### 6.10 (P2) SNOTEL is a state sensor, not a trend sensor — and its temperature channel is broken for trends

Two independent measurements: no field-significant April 1 SWE trend across 28 western/crest Washington
sites over 1979–2026 (field p = 0.156, and a correlation-aware null that permits up to 7 "significant"
sites by chance); and a documented **+1.7 °C Tmin / −0.5 °C Tmax sensor step** across the whole
11-state network that propagates into PRISM and DAYMET. Consequences:

- The platform must never state a snowpack trend from its own AWDB feed.
- `basin_swe_percent_of_median` must keep `direction="context_not_scored"` **and** carry its
  denominator's period, for the same reason every other percentile must (§6.1).
- Any future use of SNOTEL air temperature — for a snow-level estimate, a melt-energy proxy, or a
  gridded product that assimilates it — must carry the sensor-epoch caveat, and a trend computed from
  it is invalid.

### 6.11 New or newly-justified data sources

| Source | What it gives | Priority |
|---|---|---|
| **USGS station manuscripts / datum & rating history** per gauge | the `homogeneity_epochs` block §6.4 requires; the 12149000 datum break is already proven | **P0** — the ladder is wrong without it |
| **Operator rule-curve and operating-rule epochs** (USACE Howard Hanson & Mud Mountain, SCL Ross/Diablo/Gorge, PSE Baker, SPU Chester Morse) | the regulation break dates that bound a regulated-reach ladder (§3: 29–32 % flip) | **P0**, CONFIGURED seed |
| **NOAA CO-OPS `sltrends` monthly MSL** (plain text, `<id>_meantrend.txt`) | measured local RSL per delta with CI; already fetched and computed here | P1, trivially cheap |
| **NOAA Atlas 15 Vol. 1** (CONUS preliminary Sept 2026) | the trend-aware precipitation-frequency standard replacing Atlas 14; any stored Atlas 14 value has a known expiry | P1, plan ingest now, store with `standard_version` |
| **NCEI ERSSTv5 PDO index** + CPC ONI | decadal phase as displayed *context* on a ladder, never a correction | P2 |
| **USGS annual peak files** (already fetched, 11 gauges) | homogeneity screening, stage–discharge scatter, trend period-dependence; recompute annually | P1 |

All of these are OBSERVED or CONFIGURED. None is a projection.

---

## 7. What this domain contradicts or qualifies in the current repo doctrine

| # | Repo statement | Verdict | Why |
|---|---|---|---|
| 1 | `HYDROLOGY.md` §8: *"Percentiles require climatology; the platform builds its own from stored history"* | **Materially incomplete** | Silent on which history, on the sampling error, and on homogeneity. Measured: ±5.5–6.2 points at 30 years, 12.8–17.4 % band flips from ladder length alone, 29–32 % from a regulation split. A percentile without a period **and an interval** is not defensible under §1's own provenance rule. |
| 2 | `susceptibility.py` `BAND_EDGES = [25, 75, 90]`, `band()` total | **Contradicted** | The banding asserts a resolution the data does not support. At L = 30 the sampling SD is ~6 points; the 75→90 band is 15 points wide. Needs an UNKNOWN outcome near edges (§6.2). |
| 3 | `climatology.py` `PERCENTILES` stops at 95, `percentile_of` clamps | **Correct-but-insufficient** | Clamping instead of extrapolating is right (fabrication would be worse). But the measured consequence is that the surface is flat across a 2.5× flow range during the December 2025 record event and across 5–7 % of all Oct–Feb days. Extend the tail and publish the flow multiple (§6.3). |
| 4 | `HYDROLOGY.md` §12 / `DATA_DOCTRINE.md` §11: knowledge-time replay | **Extended — and there is a live bug** | Replay guarantees the *values* known at T. It does not guarantee the *ladder* known at T. An annually rebuilt ladder back-dates a better baseline into a 2025 replay. Given the measured per-decade sensitivity this is a real look-ahead bias. |
| 5 | `HYDROLOGY.md` §9: datum discipline, refuse unrecorded comparisons | **Confirmed and extended** | The 41.26 ft WY1939→WY1940 step at 12149000 shows the refusal must apply *within* one station's history, not only across stations. |
| 6 | `HYDROLOGY.md` §9: *"never derive one from the other"* (stage↔flow) | **Confirmed, with the number that justifies it** | Mount Vernon: SD 0.68 ft, range 4.08 ft about a log-Q fit; 138,000 cfs at 33.85 ft vs 127,000 cfs at 36.99 ft. NWS categories are 2 ft apart. |
| 7 | `flood-genesis-mechanisms-2026-08-24.md`: *"~29 % less flow for the same 37.00 ft stage between 1906 and 2021"* | **Qualified — the figure is an outlier comparison** | Population-level drift is −4.4 % at 37 ft (n = 85 paired peaks). The 1906 point has an unknown peak day. Report both, and lead with the scatter. |
| 8 | Prior version of **this** file: *"19.4 % of Sauk days land in a different band … the reference distribution is non-stationary"* | **Corrected** | Roughly two-thirds of that 19.4 % is sampling error, not drift (null median 13.7 %, permutation p = 0.007 for the excess). The conclusion survives; the attribution did not. |
| 9 | Prior version of this file: open question 9, *"are the Cascade SNOTEL non-trends a power problem or a real elevation effect?"* | **Answered** | Field test across 28 sites: 3 significant (2 negative, 1 positive), field p = 0.156, correlation-aware null 95th = 7 sites. **No field-significant trend over 1979–2026.** It is a record-length problem, and Mote's signal comes from a 1955-onward snow-course network. |
| 10 | `p3_surfaces.json`: Sauk chosen for Skagit *"not from the Mount Vernon outlet"* on regulation grounds | **Confirmed, twice over** | The Sauk carries a detectable century-scale peak trend (τ = +0.198, p = 0.004, and p = 0.006 even when truncated to Mount Vernon's own WY1941+ window) while Mount Vernon does not (τ = +0.024, p = 0.748); and Mount Vernon's ladder is the most disturbed by the regulation split (32.2 % of days). Both are **INFERENCE by correlation**, not attribution. |
| 11 | `p3_surfaces.json`: White at R St confidence ceiling `low`, *"thinly sampled"* | **Confirmed with a measurement** | Its 0.6 % vintage-flip rate is not stability — it has only one vintage. A 17-year ladder carries ~±8 points of sampling error. |
| 12 | `HYDROLOGY.md` §2: transient snow zone *"roughly 1,000 and 4,000 ft"* (ASSUMPTION) | **Qualified** | Timing shifts of 2.3–4.6 days/decade concentrate in the snow-influenced gauges, so the band is time-varying. Keep the derived `rain-exposed` / `rain-on-snow exposed` fractions, which recompute each cycle and are correct by construction; demote the fixed band to a display annotation with a vintage. |
| 13 | `HYDROLOGY.md` §7: *"SWE is storage, not hazard"*, SWE `context_not_scored` | **Confirmed and reinforced** | Independent grounds: the platform's own SNOTEL feed cannot detect a trend (field p = 0.156), and the temperature channel of the same network carries a +1.7 °C sensor artefact. Percent-of-normal SWE must carry its denominator's period. |
| 14 | `HYDROLOGY.md` §5: hazard *"ordered by authority"*, official categories first | **Unchanged and correct** | Nothing here justifies adjusting an official category. The opposite: it justifies displaying the category's datum and vintage, given the 2 ft category spacing against 0.68 ft of rating scatter. |
| 15 | `DATA_DOCTRINE.md` §7: thresholds *"re-fetched on a schedule and versioned"* | **Correct instinct, insufficient scope** | Versioning catches NWS changing a value. It does not capture that the *underlying standard* is being replaced (Atlas 14 → Atlas 15, preliminary Sept 2026), nor that a stage-defined threshold sits on a drifting rating. Add `standard_version` and a `datum_and_baseline_vintage` block. |

---

## 8. Open questions

1. **What are the actual homogeneity epochs for each of the ten gauges?** Datum changes, rating-revision
   epochs, station moves. I proved one (12149000, WY1939→WY1940) by inspection; the others are unenumerated and
   §6.4 cannot be implemented without them.
2. **What are the operating-rule epochs for Howard Hanson, Mud Mountain, Ross/Diablo/Gorge, Baker and
   Chester Morse?** I used approximate split dates (1962, 1948, 1959) to size the effect; the effect is
   large (29–32 %) and the dates must come from the operators before any regulated-reach ladder is
   bounded. **The dates in §3 are working values, not FACTs.**
3. **What is `n_effective` for a ±2-day day-of-year window on a maritime river?** I measured the
   sampling SD empirically by year resampling, which is the right answer, but a closed form (or a
   decision on window width) would let the platform reason about the trade between window width and
   seasonal-phase heterogeneity (§2.6).
4. **Should the window widen or narrow given the 2.3–4.6 day/decade phase drift?** A wider window buys
   sample but mixes more seasonal phase; a narrower one does the reverse. Nothing I found addresses
   this for a drifting seasonal cycle.
5. **Is the tail extension (p98/p99) statistically supportable at these sample sizes, and where is the
   `min_sample_for_tail` cut?** A 90-year ±2-day window has ~450 values; p99 is the 4th-largest. The
   rank should be published with the value, but the refusal threshold is unset.
6. **Is the Nooksack at Ferndale daily mean materially tide-contaminated?** Flagged unresolved in the
   seed. §2.7 removes the *trend* concern (Cherry Point RSL ≈ 0) but not the within-day one.
7. **How much of the Sauk's 1929-onward peak trend survives PDO conditioning and a bedload/rating
   control?** The record starts in a warm-PDO phase, the 1976-onward window shows nothing, the Sauk is
   an aggrading heavy-bedload channel, and Glacier Peak glacier loss is uncontrolled. Treat the trend as
   **detected, not attributed**.
8. **Does the AR-scale rating degrade as a hazard signal?** If per-AR maximum IVT rises at 3–6× the
   AR-mean rate, a fixed-IVT category boundary has a drifting exceedance frequency. No study tests this.
9. **Does Mote et al. 2018's field significance survive a correlation-aware null?** My 28-site
   permutation puts the chance-expectation at up to 7 of 28 (25 %), not 5 %. Their 33 % is still above
   that, but the margin is much smaller than the paper's framing implies. Whether they addressed this is
   unknown to me — **the paper was not independently fetched.**
10. **What reference period do the NWS/NWRFC official thresholds themselves rest on, and when were they
    last revised?** The platform displays them as authoritative (correctly) but does not carry their
    vintage, and §6.7's rating-scatter measurement means a stage threshold set decades ago is not the
    same flow it was.

---

## 9. Sources

**Independently fetched:**

- [Stoelinga, M.T., Albright, M.D. & Mass, C.F. (2010), *A New Look at Snowpack Trends in the Cascade Mountains*, J. Climate 23(10)](https://atmos.uw.edu/~cliff/SWEpaper_rev1_rendered.pdf) — full text extracted; period-dependence, circulation attribution, −11 % °C⁻¹ sensitivity.
- [Rangwala, I., Bardsley, T., Pescinski, M. & Miller, J. (2015), *SNOTEL sensor upgrade has caused temperature record inhomogeneities for the Intermountain West*, Western Water Assessment Climate Research Briefing](https://wwa.colorado.edu/sites/default/files/2021-08/Rangwalaetal2015.pdf) — full text extracted; +1.7 °C Tmin / −0.5 °C Tmax / −2.2 °C DTR step; builds on Oyler et al. 2015.
- [Da Silva, N.A. & Haerter, J.O. (2025), *Super-Clausius–Clapeyron scaling of extreme precipitation explained by shift from stratiform to convective rain type*, Nature Geoscience 18(5), 382–388](https://pmc.ncbi.nlm.nih.gov/articles/PMC12074990/)
- [Henny, L. & Kim, K.-M. (2025), *The Changing Nature of Atmospheric Rivers*, J. Climate 38(6)](https://cawaterlibrary.net/wp-content/uploads/2025/04/clim-JCLI-D-24-0234.1-1.pdf) — abstract page.
- [Pan, M., Hu, S., Zaitchik, B.F. & Pan, W.K. (2025), *Contrasting historical trends of atmospheric rivers in the Northern Hemisphere*, npj Clim Atmos Sci 8, 307](https://pmc.ncbi.nlm.nih.gov/articles/PMC12360949/) — the PNW "AR increasing hole".
- [Musselman, K.N. et al. (2018), *Projected increases and shifts in rain-on-snow flood risk over western North America*, Nature Climate Change 8, 808–812](https://bpb-us-w2.wpmucdn.com/sites.coecis.cornell.edu/dist/f/423/files/2021/09/musselman18natcc.pdf) — full text; **projection, see Appendix P**.
- [Chegwidden, O.S. et al. (2020), *Climate change alters flood magnitudes and mechanisms in climatically-diverse headwaters across the northwestern United States*, ERL 15, 094048](https://iopscience.iop.org/article/10.1088/1748-9326/ab986f) — **projection, Appendix P**.
- [O'Brien, T.A. et al. (2022), *Increases in Future AR Count and Size: ARTMIP Tier 2 CMIP5/6*, JGR-Atmos 127](https://pmc.ncbi.nlm.nih.gov/articles/PMC9285484/) — **projection, Appendix P**; detector-dominates-model result.
- [Washington State Dept. of Ecology (Aug 2025), *2025 Summary Report on the Science of Human Caused Climate Change and Impacts in Washington State*, Pub. 25-14-064](https://apps.ecology.wa.gov/publications/documents/2514064.pdf) — **projection tables, Appendix P**.
- [UW Climate Impacts Group for Snohomish County (Sept 2021), *Climate Change & Flooding in Snohomish County*](https://cig.uw.edu/wp-content/uploads/sites/2/2021/09/Snohomish-WRF-DHSVM-Final-Report-2021-08-31-FINAL.pdf) — **projection, Appendix P**.
- [Lee, S.-Y. & Hamlet, A.F. (2011), *Skagit River Basin Climate Science Report*](https://www.skagitcounty.net/EnvisionSkagit/Documents/ClimateChange/Complete.pdf) — AR4/A1B vintage; **projection, Appendix P**; ENSO/PDO conditional-normal result.
- [NOAA Atlas 15 informational page](https://water.noaa.gov/about/atlas15) — timeline and Vol. 1/2 scope.
- [Yakima County (17 Dec 2025), *Clausius-Clapeyron Relationship and Atmospheric Rivers*, BAS Update compilation](https://www.yakimacounty.us/DocumentCenter/View/43010/Clausius_Clapeyron_Atmospheric_Rivers_BAS_Research_DRAFT-12172025-ksw) — secondary compilation.
- [WA State Climate Office / UW (13 Jan 2026), *December 8–11, 2025 Heavy Rainfall and Flooding*](https://climate.uw.edu/2026/01/13/december-8-11-2025-heavy-rainfall-and-flooding-historical-context-and-a-note-on-snow-drought/)
- [Skagit Climate Science Consortium, *Sea Level Rise*](https://www.skagitclimatescience.org/skagit-impacts/sea-level-rise/) — delta subsidence framing.
- [Copernicus/C3S, *Global Climate Highlights 2025*](https://climate.copernicus.eu/sites/default/files/custom-uploads/GCH-2025/GCH2025-full-report.pdf) — 1.47 °C (2025), 1.52 °C (2023–2025 mean); anchors which GWL column is "today".

**Primary datasets fetched and computed by me, 2026-08-24** (all results labelled FACT above):

- USGS NWIS daily mean discharge, `https://waterservices.usgs.gov/nwis/dv/?format=rdb&sites=<site>&parameterCd=00060&statCd=00003`, full period of record for **12189500** (Sauk nr Sauk, 36,166 approved daily means, 1911-04-01 to 2026-04-06), **12186000** (Sauk ab Whitechuck), **12213100** (Nooksack Ferndale), **12149000** (Snoqualmie Carnation), **12144500** (SF Snoqualmie North Bend), **12119000** (Cedar Renton), **12113000** (Green Auburn), **12100490** (White at R St), **12200500** (Skagit Mount Vernon), **12134500** (Skykomish Gold Bar), **12167000** (NF Stillaguamish). Day-of-year ladders rebuilt with the platform's exact convention; null distributions by year-label permutation.
- USGS annual peak-flow files, `https://nwis.waterdata.usgs.gov/nwis/peak?site_no=<site>&format=rdb` — datum discontinuity detection, stage–discharge scatter, trend period-dependence.
- NOAA CO-OPS deseasonalised monthly mean sea level, `https://tidesandcurrents.noaa.gov/sltrends/data/<id>_meantrend.txt` for 9449424 Cherry Point, 9449880 Friday Harbor, 9447130 Seattle, 9444900 Port Townsend — OLS with AR(1)-inflated standard errors.
- NRCS AWDB REST, `https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/` — station inventory (78 WA SNOTEL) and daily WTEQ for the 28 western/crest sites with records beginning ≤ 1990; April 1 SWE Mann–Kendall, Sen slope, and a cross-site-correlation-preserving field-significance permutation.
- NWS/NWPS gauge metadata, `https://api.water.noaa.gov/nwps/v1/gauges/MVEW1` — official flood categories at Mount Vernon (action 23.5, minor 28, moderate 30, major 32 ft; flow undefined, `-9999`).

**Cited but NOT independently fetched — all claims from these are labelled INFERENCE above:**

- Mote, P.W. et al. (2018), *Dramatic declines in snowpack in the western US*, npj Clim Atmos Sci 1, 2 — search summary only.
- Meyer, J.D.D. et al. (2012), *Systematic Patterns of the Inconsistency between SWE and Accumulated Precipitation as Reported by the Snowpack Telemetry Network*, J. Hydrometeorol. 13(6) — HTTP 403.
- Oyler, J.W. et al. (2015), on SNOTEL temperature inhomogeneity — via Rangwala et al.
- Fassnacht, S.R. (2004), *Estimating Alter-shielded gauge snowfall undercatch…*, Hydrol. Process. 18, 3481–3492 — search summary.
- Stewart, I.T., Cayan, D.R. & Dettinger, M.D. (2005), *Changes toward earlier streamflow timing across western North America*, J. Climate 18.
- Cayan, D.R. et al. (2001), on earlier spring pulse onset.
- Miller, I.M. et al. (2021), *An Assessment of Vertical Land Movement to Support Coastal Hazards Planning in Washington State*, Water 13(3), 281.
- Montillet, J.-P. et al. (2018), *GPS Vertical Land Motion Corrections to Sea-Level Rise Estimates in the Pacific Northwest*, JGR-Oceans.
- Scholz, S. et al. (2025), *Widespread Increase in Atmospheric River Frequency and Impacts Over the 20th Century*, AGU Advances — HTTP 403.
- WMO-No. 1203 (2017), *Guidelines on the Calculation of Climate Normals* — PDF fetched but not text-extractable with available tools; the 30-year / decadal-update / Cg-17 facts come from WMO and NCEI summary pages.
- Payne, A.E. et al. (2020), *Responses and impacts of atmospheric rivers to climate change*, Nat Rev Earth Environ 1, 143–157 — abstract only.
- Sharma, A., Wasko, C. & Lettenmaier, D.P. (2018), *If Precipitation Extremes Are Increasing, Why Aren't Floods?*, WRR 54, 8545–8551.
- Hausfather, Z. & Peters, G.P. (2020), *Emissions — the 'business as usual' story is misleading*, Nature 577, 618–620 — search summary; see Appendix P.
- Schwalm, C.R. et al. (2020), *RCP8.5 tracks cumulative CO₂ emissions*, PNAS 117 — the counter-argument; search summary.

---

## Appendix P — Projections (NOT operational inputs)

> **Nothing in this appendix may enter an operational surface.** No number here may be badged anything
> but MODELED (a Cascade-derived statement built on one is EXPERIMENTAL), may inform a threshold, a
> percentile, a category, a band edge or a hazard computation, or may be rendered beside a live value.
> These are century-scale projections: they carry no knowledge time (`DATA_DOCTRINE.md` §11), cannot be
> verified at a 6–120 h lead (§9), and are MODELED at best (§2). They are retained only as literature
> about the *direction* of drift, to inform which measurements are worth making.
>
> **Scenario discipline.** Several studies below use RCP8.5 or SSP5-8.5 as their only or primary
> forcing. [Hausfather & Peters (2020, *Nature* 577, 618–620)](https://www.nature.com/articles/d41586-020-00177-3)
> argue that framing RCP8.5 as "business as usual" is misleading, since it was constructed as a
> high-risk exploratory scenario and current policy trajectories fall below it; [Schwalm et al. (2020,
> *PNAS* 117)](https://www.pnas.org/doi/10.1073/pnas.2007117117) dissent, arguing RCP8.5 has tracked
> cumulative emissions well over the historical period. (**Neither independently fetched**; search
> summaries.) Where a lower scenario is reported by the same study it is given below; where only RCP8.5
> exists, the number is flagged as **single-scenario** and must be read as an upper exploratory bound,
> never a central estimate.
>
> **Numbers deleted from this file** because scenario, ensemble or compounded uncertainty could not be
> attached: the previous headline's "basin peak flow +11 % at 1.5 °C and +24 % at 4 °C"; the "1 °C moves
> the Cascade snowline from ~600 m to ~750 m with ~12 % SWE loss" figure (primary source never fetched);
> the "~10× extreme-AR-frequency" claim attributed to Higgins et al. 2025 (unverified).

| Projection | Value | Scenario | Ensemble / model chain | Uncertainty as reported |
|---|---|---|---|---|
| WA state-average **annual max daily runoff** | +10 % / +14 % / +17 % / +24 % at the 1.5 / 2 / 3 / 4 °C **global warming levels**; western WA +11 / +15 / +17 / +24 % | GWL-indexed (partially decouples scenario), underlying RMJOC-II uses RCP4.5 **and** 8.5 | 10 GCMs × 2 downscaling methods × 4 hydrologic models = **80 projections** | 5th–95th percentile of the 80 shown in the source table; hydrologic-model structural spread is **inside** the 80 but not separately reported |
| WA **2-year storm** precipitation | +3 % / +5 % / +13 % / +20 % at 1.5/2/3/4 °C (historical 1.8 in) | GWL-indexed, WRF-UW dynamical downscaling | single RCM, multiple driving GCMs | model agreement on **sign only at 4 °C** for the 25-yr storm |
| WA **25-year storm** precipitation | +2 % / +7 % / +13 % / +22 % (historical 3.0 in) | same | same | same |
| WA **April 1 SWE** | −21 % / −33 % / −50 % / −67 % at 1.5/2/3/4 °C (historical 6.7 in) | same | same | not separately decomposed |
| Snohomish + Stillaguamish **peak flow**, 2080s | +10 % to +40 %; per-gauge 2/5/10/25/50/100-yr averages cluster **+21 % to +40 %**; Snoqualmie nr Snoqualmie +27 % (1 h) / +25 % (1 d), 25th–75th **+10 to +42 %** | **RCP8.5 only — single-scenario** | DHSVM driven by **12** WRF-downscaled projections, 2070–2099 vs 1981–2010 | 25th–75th of 12 members given; authors state *"we recommend against using"* the 1.01-yr and 500-yr projections and report **no clear relationship with return interval** |
| NW-US headwater **flood magnitude by mechanism** | precipitation-driven annual maxima **+29 to +36 %**; snowmelt-driven +12 % (transition/montane), +33 % (temperate); **ROS-driven −9 to +10 %**; flood elasticity **1–2 % per 1 % annual precipitation** | RCP4.5 **and** 8.5 | 21 basins × 10 GCMs × 4 hydrologic models (3 VIC variants + PRMS), 1951–2099 | ranges span the GCM × hydro-model matrix; **"transition" = seven basins on the LEEWARD (east) side of the Cascades**, not the western WA transient zone; **"temperate" = seven lowland rain-dominant basins**, the class that maps here |
| Cascade **rain-on-snow event runoff volume** | +20 % to > +100 %; western N. America: 55 % of 106 basins > +20 %, 20 basins > +100 %; maritime snowmelt share of ROS runoff historically **30–45 %** (lowest of any region) | **RCP8.5 pseudo-global-warming — single-scenario** | WRF at 4 km, 19-model mean deltas, 2000–2013 vs end-century | no ensemble spread reported (single PGW realisation with mean deltas); *"the results shown in Fig. 4 do not include rainfall on snow-free ground"*, so the low-elevation ROS decline is a **category change**, not a risk decline |
| Global **AR frequency / geometry** | AR conditions ~+50 %; IVT strength ~+25 %; ARs ~25 % longer and wider; ~10 % **fewer** discrete ARs | **RCP8.5 — single-scenario** | 21 CMIP5 models, 1979–2002 vs 2073–2096 | ARTMIP Tier 2 finds **detector (ARDT) choice dominates model choice** as the uncertainty source at all latitudes — so an AR-frequency percentage is partly an artefact of the detection algorithm |
| ARTMIP Tier 2 **AR-day trend** | +1 to +10 AR days yr⁻¹ per century on western coastlines; ~+20 (~+30 %) in midlatitude storm tracks | RCP8.5 + SSP5-8.5 | CMIP5 + CMIP6, multiple ARDTs | detector spread exceeds model spread; see the **contested** PNW "AR increasing hole" in §4 |
| Skagit at **Mount Vernon** 100-yr flood | natural ~+30 % by the 2040s (10-scenario mean); **regulated** +20 % by 2040s, +24 % by 2080s; proposed extra flood storage buys back only 3 % / 7 % | AR4 / A1B — **vintage 2011, superseded scenario framework** | VIC + Hybrid Delta, 10 scenarios (natural); **single scenario** for the regulated case | regulated case is one scenario under one operating rule; the operating rule is itself under revision — a second, faster non-stationarity |
| Skagit at **Ross Dam** 100-yr flood | ~unchanged in the 2020s; **+49 % by the 2080s** | AR4 / A1B — **single-scenario, superseded framework** | same | headwater basin flips snow-dominant → transient; no ensemble spread reported for this figure |
| WA **snowpack-drought likelihood** (< 75 % of 1995–2014 April 1 SWE) | 0.2 → 0.25 / 0.5 / 0.85 / 0.95 at 1.5/2/3/4 °C | GWL-indexed | RMJOC-II 80-member chain | *"Nearly every year expected to fit the definition of snowpack drought under the 4.0 °C GWL."* — which is itself the argument that percent-of-normal SWE is a doomed statistic (§6.10) |
| WY2026 western-US **snow drought attribution** | ≈ **4.4×** more likely (95 % CI 2.6–9.4); Upper Colorado ≈ 14×; ~40 km³ missing snow | attribution, not projection | not stated in the release | **no separate Pacific Northwest factor published**; primary PNAS paper bot-walled, numbers from the [Colorado School of Mines release](https://www.minesnewsroom.com/news/climate-change-made-years-snow-drought-western-us-four-times-more-likely-new-colorado-school) — **INFERENCE** |
| Nov 2021 BC AR event attribution | AR of that magnitude ≈ 1-in-10-yr, made **≥ 60 %** more likely; 2-day precipitation ≈ 1-in-50 to 1-in-100 yr, +50 % likelihood; extreme streamflow **2–4×** more likely | attribution | multi-model | closest analogue to Nooksack/Skagit flooding; **arrives months after the event and can never be a live surface** (§6, and `DATA_DOCTRINE.md` §9) |

**The one operational statement this appendix supports**, and it is a statement about method rather
than magnitude: *the direction of drift is toward more cool-season runoff, earlier timing and less
April 1 SWE, which is the same direction the instruments already measure (§2.6, §2.7). That agreement
is a reason to trust the measured trends, not a licence to import a projected magnitude.*

**Recommended doctrine sentence:** *Cascadia Papsukkal does not use climate projections, and does not
attribute individual events to climate change. It states the vintage, the period and the sampling
interval of every reference distribution it ranks a live value against, so that a reader can see the
baseline move without the platform claiming to have measured why.*
