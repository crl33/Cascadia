# Tidal gauge verification — 2026-08-26

Independent re-measurement of the tidal-transmission claim in
`docs/research/doctrine-delta-2026-08-24.md` §2.9 / §12.5 / new §10A, from primary data
fetched this session. Nothing in this file was taken from the review; every number below was
recomputed from raw USGS and NOAA CO-OPS payloads over **three** hydrologic windows (two
independent low-flow periods and the Event Zero flood), with a **non-tidal control gauge**
carried through every calculation so that the measurement noise floor is visible.

Status labels follow `docs/research/README.md`: **FACT** = computed this session from a
fetched payload (query given); **INFERENCE** = reasoned, not directly observed;
**ASSUMPTION** = adopted without proof; **OPEN QUESTION** = unresolved.

---

## 0. Verdict in one table

| Review claim (`doctrine-delta-2026-08-24.md` §2.9) | Verdict | Measured this session |
|---|---|---|
| Snohomish at Snohomish (SNAW1) transmits **0.831 ft/ft** at low flow | **Partially confirmed — right class, wrong precision** | 0.739 / 0.757 (phase-blind OLS, two windows); 0.892 / 0.919 (lag-corrected); rms amplitude ratio 0.901 / 0.918. The review's 0.831 sits *inside* the range spanned by defensible estimators but is not reproducible as a single number, and the review does not say which estimator it used |
| …with **r = 0.94** | **Refuted as stated** | r = +0.823 / +0.828 phase-blind; r = +0.993 lag-corrected. No estimator I can construct yields 0.94 |
| Ferndale (NKSW1) transmits **0.019 ft/ft (r = 0.33)** | **Refuted numerically; conclusion survives** | −0.0001 / −0.0015 phase-blind, +0.0009 / +0.0048 lag-corrected, r ≤ 0.29. Ferndale is **statistically indistinguishable from a definitively non-tidal control gauge** 20 river miles inland |
| Mount Vernon (MVEW1) transmits **0.010 ft/ft** | **Confirmed** | 0.0021 / −0.0053 phase-blind, 0.0045 / 0.0070 lag-corrected. Same class |
| Doctrine "names the wrong gauge as the tidal problem" | **Confirmed** | `HYDROLOGY.md` §75 says the Nooksack "is tidally influenced at Ferndale". At the Ferndale **gauge** that is not measurable |
| SNAW1's Event Zero record "arrived at a benign coastal boundary… tide 6.64 ft below MHHW" | **Confirmed exactly** | Seattle observed 4.723 ft MLLW at 2025-12-12T01:36Z vs SNAW1 peak 34.45 ft at 01:35Z; MHHW = 11.36 ft MLLW → **6.64 ft below MHHW**, to the hundredth |
| Doctrine should treat SNAW1 as `TIDAL` | **Confirmed as physics — but see §6** | **SNAW1 is not a seeded forecast point.** Doctrine that changes only for SNAW1 changes nothing the platform serves today |

**The operationally decisive finding (FACT):** all six of the platform's currently seeded
forecast points — including NKSW1, the one doctrine names — have a semidiurnal (M2) amplitude
of **≤ 0.008 ft** at low flow, against a coastal M2 of 2.26–3.36 ft. **None of them is tidally
affected.** The tidal defect the doctrine change is meant to prevent does not exist in any
gauge the platform currently serves.

---

## 1. Which gauges the platform actually serves

From `packages/core/src/cascade_core/seed/stations.json` (read, not modified):

| LID | Name in the seed | USGS site | Basin | Seeded? |
|---|---|---|---|---|
| MVEW1 | Skagit River near Mount Vernon | 12200500 | skagit | yes |
| AUBW1 | Green River near Auburn | 12113000 | green-duwamish | yes |
| WRAW1 | White River at R St near Auburn | 12100490 | puyallup-white | yes |
| **NKSW1** | **Nooksack River at Ferndale** | **12213100** | nooksack | **yes** |
| RNTW1 | Cedar River at Renton | 12119000 | cedar | yes |
| CRNW1 | Snoqualmie River near Carnation | 12149000 | snohomish-snoqualmie | yes |
| SNAW1 | Snohomish River at Snohomish | 12155500 | — | **no** |
| MROW1 | Snohomish River near Monroe | 12150800 | — | no (used here as control) |

**FACT.** Ferndale *is* the seeded Nooksack forecast point — `NKSW1` and "Ferndale" are the
same gauge, not two. The task brief's premise that "SNAW1 and Ferndale may NOT be seeded" is
half right: Ferndale is seeded, SNAW1 is not.

**FACT.** Site identities confirmed against the USGS site service:

```
https://waterservices.usgs.gov/nwis/site/?format=rdb&siteOutput=expanded
  &sites=12155500,12213100,12200500,12149000,12119000,12113000,12100490,12150800
```

| site_no | station_nm | alt_va (ft) | alt_datum_cd | huc_cd |
|---|---|---|---|---|
| 12155500 | SNOHOMISH RIVER AT SNOHOMISH, WA | **−6.43** | NAVD88 | 171100110203 |
| 12213100 | NOOKSACK RIVER AT FERNDALE, WA | 8.50 | NAVD88 | 17110004 |
| 12200500 | SKAGIT RIVER NEAR MOUNT VERNON, WA | 3.80 | NAVD88 | 17110007 |
| 12150800 | SNOHOMISH RIVER NEAR MONROE, WA | 17.05 | NAVD88 | 17110011 |
| 12149000 | SNOQUALMIE RIVER NEAR CARNATION, WA | 2.12 | NAVD88 | 17110010 |
| 12119000 | CEDAR RIVER AT RENTON, WA | 18.77 | NAVD88 | 17110012 |
| 12113000 | GREEN RIVER NEAR AUBURN, WA | *(blank)* | — | 17110013 |
| 12100490 | WHITE RIVER AT R STREET NEAR AUBURN, WA | 3.66 | NAVD88 | 17110014 |

The SNAW1 gauge datum of **−6.43 ft NAVD88** — a gauge zero below the geodetic datum — is
itself the signature of a tidal-reach installation (INFERENCE). Monroe, 12 river miles
upstream, sits at +17.05 ft.

**FACT.** USGS publishes **no discharge record at 12155500**: parameter 00060 returned zero
features in all three windows fetched here. SNAW1 is a stage-only gauge. Consistent with
`EVENT_ZERO.md` §81 ("stage only").

**FACT.** NWPS thresholds re-fetched 2026-08-26 (`https://api.water.noaa.gov/nwps/v1/gauges/{LID}`):
SNAW1 action 20 / minor 25 / moderate 27 / major 29 ft, flow −9999 (stage-only categories);
NKSW1 action 15 / minor 18 / moderate 20.5 / major 23 ft, flow −9999.

---

## 2. Data fetched

### 2.1 River stage and discharge — USGS OGC API

Collection `continuous`, statistic 00011, 15-minute cadence. Base URL is the one the platform's
own `packages/providers/usgs/.../ogc_client.py` already uses.

```
GET https://api.waterdata.usgs.gov/ogcapi/v0/collections/continuous/items
      ?monitoring_location_id=USGS-<site>
      &parameter_code=<00065|00060>
      &datetime=<start>/<end>
      &limit=10000&f=json
```

Three windows, eight sites, both parameters (fetched 2026-08-26T22:47–22:53Z):

| Window key | Range (UTC) | Regime | Stage points per site |
|---|---|---|---|
| `lowflow_2026` | 2026-07-15 → 2026-08-25 | late-summer low flow | 3 900–3 937 |
| `lowflow_2025` | 2025-08-25 → 2025-10-05 | late-summer low flow, independent year | 3 924–3 937 (SNAW1 2 422, partial) |
| `eventzero_2025` | 2025-12-01 → 2025-12-20 | the Event Zero flood | 1 822–1 826 |

Values are `Provisional` for the 2026 window and mixed `Approved`/`Provisional` for 2025.

### 2.2 Coastal water level — NOAA CO-OPS

**FACT, and a correction worth recording:** the endpoint named in the task brief
(`api.tidesandcurrents.noaa.gov/api/datagetter`) returns **HTTP 403 Forbidden** as of
2026-08-26, with any User-Agent. The working path is `/api/prod/datagetter`.

```
GET https://api.tidesandcurrents.noaa.gov/api/prod/datagetter
      ?product=water_level&station=<id>&begin_date=<YYYYMMDD>&end_date=<YYYYMMDD>
      &datum=MLLW&time_zone=gmt&units=english&format=json
```

6-minute observed water level, plus `product=predictions` for the same windows. Requests are
capped at 31 days, so each window was fetched in chunks.

| Station | Name | Paired with |
|---|---|---|
| 9447130 | Seattle | SNAW1, MROW1, CRNW1, RNTW1, AUBW1, WRAW1 |
| 9449424 | Cherry Point | NKSW1 (Ferndale), MVEW1 (Mount Vernon) |
| 9444900 | Port Townsend | (fetched, used as a cross-check) |

### 2.3 Tidal datums

```
GET https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations/<id>/datums.json?units=english
```

Epoch 1983–2001, feet on station datum:

| Station | MHHW | MHW | MSL | MLLW | NAVD88 | GT |
|---|---|---|---|---|---|---|
| Seattle 9447130 | 19.30 | 18.43 | 14.58 | 7.94 | **10.28** | 11.36 |
| Cherry Point 9449424 | 15.49 | 14.66 | 11.62 | 6.34 | **absent** | 9.15 |
| Port Townsend 9444900 | 11.88 | 11.20 | 8.35 | 3.36 | **absent** | 8.52 |

**FACT.** Seattle MHHW = 19.30 − 7.94 = **11.36 ft MLLW**; MLLW = NAVD88 − 2.34 ft.
**FACT, and it independently confirms the review's §9.2(b):** Cherry Point and Port Townsend
publish **no NAVD88 tie**. A Ferndale water-surface elevation (NAVD88) and a Cherry Point tide
(MLLW) **cannot be placed on a common datum by arithmetic** from published values — that
conversion needs VDatum. This is an OPEN QUESTION carried into §7.

---

## 3. Method, and why the obvious method is wrong

Three estimators were computed. The differences between them are the whole reason the review's
"0.831" is not reproducible as a single number.

**(a) Raw OLS of stage on tide.** Regress un-filtered gauge stage on un-filtered coastal water
level. This is almost certainly what produces round numbers like 0.019: it is contaminated by
every slow river motion that happens to co-vary with the spring/neap cycle. Reported below for
comparison only.

**(b) Band-limited OLS (the estimator used for the headline numbers).** Zero-phase FFT
band-pass of **both** series to the **semidiurnal band, 10–16 h**, then OLS.

Why 10–16 h and nothing wider: the semidiurnal band holds M2 (12.4206 h), S2 (12.00 h) and
N2 (12.658 h) and **nothing hydrologic or solar**. The diurnal band (22–27 h) at an inland
river gauge is contaminated by the *solar* day — snowmelt and glacier melt, evapotranspiration,
instrument temperature — whose periods (S1 24.000 h, P1 24.066 h, K1 23.934 h) are
indistinguishable from the diurnal tide over a month-long record.

**This is not a theoretical worry; it is measured.** A whole-window harmonic fit over the Event
Zero flood assigns **MROW1 (Monroe) K1 = 0.786 ft and P1 = 0.835 ft** — at a gauge 12 miles
above the head of tide whose measured low-flow M2 is 0.0002 ft. Those amplitudes are pure
leakage from the flood hydrograph into the near-24-h band. Any tidal statistic that includes
the diurnal band during a flood is measuring the flood.

**(c) Lag-corrected OLS.** A tidal wave arrives at an upstream gauge phase-shifted, and OLS on
a phase-lagged sinusoid is biased low by cos(lag). The band-passed tide series was shifted over
±6 h in 15-minute steps and the slope reported at the shift maximising r.

**Amplitude ratio** (rms of the band-passed gauge ÷ rms of the band-passed tide) is also given.
It is phase-blind in the other direction — insensitive to lag, but it counts non-tidal noise in
the same band as signal, so it is an upper bound.

**M2 amplitude** is reported separately as the single clean discriminant, from a whole-window
harmonic least-squares fit on the 25-h high-passed series.

**Control.** MROW1 (Snohomish near Monroe, 12150800) is carried through everything. It is on
the same river as SNAW1, upstream of tidal influence, at a gauge datum of +17.05 ft NAVD88. Its
value in each column **is the noise floor** for that column. Nothing at or below the control is
a measurement.

Rate-of-rise is computed with the platform's own method, read from
`packages/hydrology/src/cascade_hydrology/trend.py`:
`rate = (last − first) / hours`, an **endpoint difference**, not a least-squares slope; and
`STAGE_STEADY_EPS_FT_PER_H = 0.05`. `assemble.py:220` calls it with `window_h=6`.

---

## 4. Results — tidal transmission

### 4.1 Coastal forcing in each window (band-passed, 10–16 h)

| Window | Seattle semi p2p | Cherry Point semi p2p | Port Townsend semi p2p |
|---|---|---|---|
| lowflow_2026 | 9.891 ft (rms 2.524) | 6.809 ft (rms 1.694) | 6.595 ft (rms 1.617) |
| lowflow_2025 | 9.630 ft (rms 2.476) | 6.589 ft (rms 1.657) | 6.255 ft (rms 1.576) |
| eventzero_2025 | 9.507 ft (rms 2.533) | 6.487 ft (rms 1.746) | 6.269 ft (rms 1.635) |

Whole-window harmonic M2 amplitude: Seattle 3.362 / 3.035 ft, Cherry Point 2.264 / 2.144 ft
(lowflow_2026 / eventzero_2025). Puget Sound is mixed semidiurnal — the form number
(K1+O1)/(M2+S2) is 1.13 at Seattle and 1.61–1.64 at Cherry Point and Port Townsend
(lowflow_2026) — which is exactly why the diurnal band cannot be used at a river gauge.

### 4.2 LOW FLOW — `lowflow_2026`, 2026-07-15 → 2026-08-25

Semidiurnal band-pass; n = 3 735 after edge trimming.

| Site | Seeded | semi p2p (ft) | semi rms (ft) | slope (ft/ft) | ± s.e. | r | amp ratio | best lag | lag-corr slope | lag-corr r |
|---|---|---|---|---|---|---|---|---|---|---|
| **SNAW1** 12155500 | no | **8.661** | **2.2743** | **0.7391** | 0.0081 | **+0.823** | **0.9011** | +1.25 h | **0.8917** | **+0.993** |
| NKSW1 12213100 | yes | 0.058 | 0.0107 | −0.0001 | 0.0001 | −0.019 | 0.0063 | +3.00 h | +0.0009 | +0.143 |
| MVEW1 12200500 | yes | 0.153 | 0.0151 | 0.0021 | 0.0001 | +0.234 | 0.0089 | +2.25 h | +0.0045 | +0.522 |
| CRNW1 12149000 | yes | 0.781 | 0.0475 | −0.0009 | 0.0003 | −0.050 | 0.0188 | — | — | — |
| RNTW1 12119000 | yes | 0.043 | 0.0051 | 0.0001 | 0.0000 | +0.048 | 0.0020 | — | — | — |
| AUBW1 12113000 | yes | 0.024 | 0.0025 | −0.0002 | 0.0000 | −0.189 | 0.0010 | — | — | — |
| WRAW1 12100490 | yes | 0.092 | 0.0156 | 0.0012 | 0.0001 | +0.198 | 0.0062 | — | — | — |
| *MROW1 12150800 (control)* | no | *0.006* | *0.0011* | *0.0000* | *0.0000* | *+0.059* | *0.0004* | *−0.75 h* | *+0.0000* | *+0.065* |

Whole-window harmonic **M2 amplitude**, same window:

| Site | M2 (ft) | as % of the coastal M2 |
|---|---|---|
| **SNAW1** | **2.9726** | **88.4 %** of Seattle |
| NKSW1 | 0.0006 | 0.03 % of Cherry Point |
| MVEW1 | 0.0077 | 0.34 % of Cherry Point |
| CRNW1 | 0.0057 | 0.17 % of Seattle |
| RNTW1 | 0.0012 | 0.04 % |
| AUBW1 | 0.0005 | 0.01 % |
| WRAW1 | 0.0036 | 0.11 % |
| *MROW1 (control)* | *0.0002* | *0.01 %* |

SNAW1's median discharge is unavailable (no 00060 record); the other gauges ran at 111–1 710 cfs
(RNTW1 median 134, AUBW1 267, CRNW1 641, WRAW1 658, NKSW1 1 290, MROW1 1 600, MVEW1 7 640) —
genuine low flow, the condition under which the review made its claim.

### 4.3 LOW FLOW — `lowflow_2025`, 2025-08-25 → 2025-10-05 (independent year)

| Site | semi p2p (ft) | semi rms (ft) | slope | r | amp ratio | lag-corr slope | lag-corr r |
|---|---|---|---|---|---|---|---|
| **SNAW1** | **9.425** | **2.2741** | **0.7566** | **+0.828** | **0.9183** | **0.9192** | **+0.993** |
| NKSW1 | 0.291 | 0.0280 | −0.0015 | −0.086 | 0.0169 | +0.0048 | +0.281 |
| MVEW1 | 0.231 | 0.0408 | −0.0053 | −0.217 | 0.0246 | +0.0070 | +0.280 |
| CRNW1 | 0.010 | 0.0014 | +0.0002 | +0.352 | 0.0006 | — | — |
| RNTW1 | 0.049 | 0.0056 | +0.0003 | +0.127 | 0.0023 | — | — |
| AUBW1 | 0.012 | 0.0017 | +0.0000 | +0.023 | 0.0007 | — | — |
| WRAW1 | 0.103 | 0.0227 | +0.0014 | +0.152 | 0.0092 | — | — |
| *MROW1 (control)* | *0.170* | *0.0106* | *+0.0005* | *+0.112* | *0.0043* | *+0.0005* | *+0.114* |

**FACT — the low-flow result is reproducible across two independent years.** SNAW1: slope
0.739 vs 0.757; r +0.823 vs +0.828; amplitude ratio 0.901 vs 0.918; lag +1.25 h in both. Every
seeded gauge stays within a factor of ~3 of the Monroe control in both years.

### 4.4 THE FLOOD — `eventzero_2025`, 2025-12-01 → 2025-12-20

| Site | semi p2p (ft) | semi rms (ft) | slope | r | amp ratio | M2 (ft) | peak Q (cfs) |
|---|---|---|---|---|---|---|---|
| **SNAW1** | **5.739** | **1.0862** | **0.2233** | **+0.525** | **0.4288** | **1.0849** | *(no record)* |
| NKSW1 | 0.854 | 0.1265 | −0.0102 | −0.142 | 0.0725 | 0.0628 | 44 300 |
| MVEW1 | 0.183 | 0.0295 | +0.0020 | +0.118 | 0.0169 | 0.0135 | 133 000 |
| CRNW1 | 0.860 | 0.0937 | −0.0095 | −0.259 | 0.0370 | 0.0515 | 89 700 |
| RNTW1 | 0.183 | 0.0297 | +0.0003 | +0.025 | 0.0117 | 0.0045 | 12 400 |
| AUBW1 | 0.440 | 0.0489 | −0.0010 | −0.050 | 0.0193 | 0.0128 | 12 100 |
| WRAW1 | 0.415 | 0.0505 | −0.0016 | −0.083 | 0.0199 | 0.0030 | 12 000 |
| *MROW1 (control)* | *0.436* | *0.0630* | *−0.0029* | *−0.119* | *0.0249* | *0.0141* | *115 000* |

**FACT — tidal transmission at SNAW1 collapses by roughly a factor of three during the flood.**
Slope 0.739–0.757 at low flow → **0.223** at flood (0.318 lag-corrected). M2 amplitude
2.97 ft → **1.08 ft**. Amplitude ratio 0.90 → 0.43. This is what open-channel hydraulics
predicts: a high river discharge steepens the water surface and damps the upstream propagation
of the tidal wave. **The review's 0.831 is a low-flow number quoted without a regime, and it
overstates transmission by ~3× in the regime the platform exists to serve.**

**FACT — during the flood, no seeded gauge is distinguishable from the non-tidal control.**
The Monroe control reads semi rms 0.0630 ft and M2 0.0141 ft during the flood — twenty to sixty
times its own low-flow value. That is the noise floor a fast hydrograph imposes on any tidal
estimator. NKSW1 (0.1265 ft rms, M2 0.0628) and CRNW1 (0.0937 ft rms, M2 0.0515) sit at 1.5–2×
that floor; CRNW1 at Carnation, 40 river miles inland at a stage of 45–61 ft, **cannot** be
tidal, which fixes the floor empirically. **INFERENCE: the apparent flood-time "tidal" signal at
Ferndale is hydrograph leakage, not tide.**

### 4.5 Reconciling 0.739, 0.831 and 0.919

The phase lag explains the whole spread. At SNAW1 the semidiurnal wave arrives **+1.25 h**
behind Seattle (identical in both low-flow years) — about 36° at M2. Phase-blind OLS is
therefore biased low by cos(36°) ≈ 0.81, and 0.739 / 0.81 ≈ 0.91, which is what the
lag-corrected and amplitude-ratio estimators return.

| Estimator | lowflow_2026 | lowflow_2025 |
|---|---|---|
| Phase-blind band-limited OLS | 0.739 (r +0.823) | 0.757 (r +0.828) |
| **Review's figure** | **0.831 (r 0.94)** | — |
| Amplitude ratio (rms) | 0.901 | 0.918 |
| Lag-corrected OLS (+1.25 h) | 0.892 (r +0.993) | 0.919 (r +0.993) |

**INFERENCE.** 0.831 is a plausible intermediate — most likely raw un-filtered OLS over some
window, or a partially lag-aware fit. It is not wrong by class. It is wrong to carry into
doctrine as a three-significant-figure constant, because the estimator, the window and the
discharge regime each move it by more than the third digit. The honest doctrinal statement is
**"SNAW1 transmits roughly 0.75–0.92 ft of stage per ft of Seattle tide at low flow, falling to
roughly 0.22–0.32 during a large flood, with a +1.25 h lag."**

---

## 5. What a tidal signal does to the platform's rate-of-rise

This is the defect the doctrine change exists to prevent, so it is quantified against the
platform's actual code path: endpoint difference over a trailing window, `STAGE_STEADY_EPS_FT_PER_H
= 0.05`, live window `window_h=6`.

Rates below are computed from the **semidiurnal band alone** — i.e. the false rate a pure tide
injects into a stage series with no river motion in it at all. Units ft/h, absolute value.

### 5.1 Closed form

For a sinusoid of amplitude A and period T, the endpoint difference over a window W has maximum
magnitude `2A·|sin(πW/T)| / W`. At M2 (T = 12.4206 h) this is **0.501 A** at W = 1 h,
**0.459 A** at W = 3 h and **0.333 A** at W = 6 h. A tide of amplitude A therefore injects a
false rate of roughly **A/3 to A/2 ft per hour**, nearly independent of window length — widening
the window does *not* average it away, because a half tidal cycle is only 6.2 h.

### 5.2 Measured, low flow (`lowflow_2026`)

| Site | 1 h max | 1 h p95 | 3 h max | 3 h p95 | **6 h max** | **6 h p95** | % of 6 h samples exceeding the 0.05 ft/h STEADY epsilon |
|---|---|---|---|---|---|---|---|
| **SNAW1** | **2.186** | 1.871 | **2.000** | 1.713 | **1.443** | 1.241 | **96.7 %** |
| NKSW1 | 0.015 | 0.010 | 0.013 | 0.009 | 0.010 | 0.007 | 0.0 % |
| MVEW1 | 0.039 | 0.015 | 0.035 | 0.014 | 0.025 | 0.010 | 0.0 % |
| CRNW1 | 0.201 | 0.030 | 0.183 | 0.027 | 0.130 | 0.019 | 2.5 % |
| RNTW1 | 0.011 | 0.005 | 0.010 | 0.004 | 0.007 | 0.003 | 0.0 % |
| AUBW1 | 0.006 | 0.002 | 0.006 | 0.002 | 0.004 | 0.002 | 0.0 % |
| WRAW1 | 0.024 | 0.016 | 0.022 | 0.014 | 0.015 | 0.010 | 0.0 % |
| *MROW1 (control)* | *0.002* | *0.001* | *0.001* | *0.001* | *0.001* | *0.001* | *0.0 %* |

`lowflow_2025` reproduces this: SNAW1 6 h max 1.568, p95 1.259, 96.7 % above epsilon; every
seeded gauge ≤ 0.048 ft/h at 6 h and 0.0 % above epsilon.

### 5.3 Measured, during the flood (`eventzero_2025`)

| Site | 1 h max | 3 h max | **6 h max** | % of 6 h samples > 0.05 ft/h |
|---|---|---|---|---|
| **SNAW1** | **1.437** | **1.315** | **0.954** | **60.0 %** |
| NKSW1 | 0.222 | 0.202 | 0.142 | 21.0 % |
| CRNW1 | 0.214 | 0.196 | 0.143 | 7.4 % |
| AUBW1 | 0.115 | 0.104 | 0.073 | 2.5 % |
| WRAW1 | 0.106 | 0.096 | 0.069 | 2.0 % |
| MVEW1 | 0.045 | 0.041 | 0.030 | 0.0 % |
| RNTW1 | 0.050 | 0.045 | 0.030 | 0.0 % |
| *MROW1 (control)* | *0.109* | *0.100* | *0.073* | *2.9 %* |

Read the control row before reading any other row: NKSW1's 0.142 ft/h and CRNW1's 0.143 ft/h
sit at about 2× a gauge that has no tide at all. AUBW1 and WRAW1 are *below* the control. The
only row that clears the control by an order of magnitude is SNAW1.

### 5.4 What this means

**FACT.** At SNAW1 the platform's live 6 h rate-of-rise would report a spurious rise or fall
exceeding its own STEADY threshold in **96.7 % of low-flow samples and 60 % of Event Zero
samples**, at magnitudes up to **1.44 ft/h at low flow and 0.95 ft/h during the flood**. For
scale, SNAW1's action-to-minor gap is 5 ft: a naive time-to-threshold at 0.95 ft/h would
announce roughly five hours to flood stage on a falling river, twice a day, forever. At a
`TIDAL` point, rate of rise and time-to-threshold are not merely noisy — they are meaningless
without de-tiding. The review's §9.3 addition is correct.

**FACT.** At every seeded gauge the tidally-injected false rate at the live 6 h window is
**≤ 0.025 ft/h at low flow** — half the STEADY epsilon, and below the 0.01 ft resolution of the
stage record over any window shorter than a day. During the flood the seeded gauges reach
0.03–0.14 ft/h, but so does the non-tidal control (0.073 ft/h), so that is hydrograph noise, not
tide. **No de-tiding is needed for anything the platform currently serves.**

---

## 6. The Event Zero crest and the coastal boundary

**FACT.** SNAW1 peak stage in the fetched record: **34.45 ft at 2025-12-12T01:35Z**. This
matches `EVENT_ZERO.md` §81 exactly (USGS value; the NWPS 34.15 conflict noted there is
untouched by this work).

**FACT.** Seattle observed water level at 2025-12-12T01:36Z: **4.723 ft MLLW**. Seattle MHHW is
11.36 ft MLLW. The crest therefore arrived **6.64 ft below MHHW** — reproducing the review's
figure to the hundredth of a foot.

**FACT.** Within ±6 h of the crest the Seattle tide ranged 4.68 → 11.98 ft MLLW; the highest
water in that window was 11.98 ft MLLW, only 0.62 ft below MHHW. The maximum over the whole
2025-12-01→20 window was 13.35 ft MLLW, **1.99 ft above MHHW**.

**FACT.** The measured semidiurnal band at SNAW1 during Event Zero had a peak-to-peak swing of
**5.739 ft**. The crest's position on that swing was therefore worth roughly **±2.9 ft** of
stage.

**INFERENCE.** Had the same river crest arrived on the opposite tidal phase of the same day,
SNAW1 would have peaked near **37 ft** rather than 34.45 ft. Applying the measured flood-regime
transmission (0.22–0.32 ft/ft) to a crest landing at MHHW instead of 6.64 ft below it adds
**1.5–2.1 ft**; at the whole-window maximum tide, 2.1–2.8 ft. Against thresholds of minor 25 /
moderate 27 / **major 29 ft**, the event was already major-category, so no category boundary
turns on this — but the *record itself* is a compound quantity, and the review is right that
recording it as a pure river record is a trap. **Confirmed.**

**Note the sign, though.** Even at 0.22–0.32 ft/ft, the coastal boundary is worth ~2 ft on a
34-ft crest — about 6 %. The review's §12.5 phrasing ("the gauge transmits 0.831 ft of stage
per ft of Seattle tide") invites the reader to multiply 0.831 × 6.64 = 5.5 ft, which is
**2.6–3.6× too large** for a flood-regime crest. Carry the regime with the coefficient.

---

## 7. What could NOT be verified

1. **The review's r = 0.94 for SNAW1.** Not reproduced by any of the four estimators computed
   here (+0.823, +0.828 phase-blind; +0.993, +0.993 lag-corrected). The review does not state
   its estimator, window, or tide station, so the gap cannot be closed. **OPEN QUESTION.**
2. **The review's 0.019 ft/ft (r = 0.33) for Ferndale.** Not reproduced (−0.0015 to +0.0048,
   r ≤ 0.29). Both numbers mean "not tidal", so the conclusion is unaffected, but the specific
   value should not be carried into doctrine. **OPEN QUESTION.**
3. **Whether the Nooksack *reach below the Ferndale gauge* is tidal.** Only the gauge was
   measured. `HYDROLOGY.md` §75 says "the lower river is tidally influenced at Ferndale" — the
   *reach* claim may well be true while the *gauge* claim is false. Distinguishing them needs
   either a downstream gauge (none exists in the seed) or a hydraulic model. **OPEN QUESTION.**
4. **Ferndale's water-surface elevation against the Cherry Point tidal frame.** Blocked by the
   missing NAVD88 tie at Cherry Point (§2.3). The physically natural explanation for a
   perched, non-tidal low-flow Ferndale gauge — that its water surface sits above MHHW — cannot
   be checked without VDatum. **OPEN QUESTION**, and itself evidence for the review's §9.2(b).
5. **Regime dependence at Ferndale.** Its low-flow M2 (0.0006 ft) and flood M2 (0.0628 ft) differ
   by 100×, but the flood figure is at the hydrograph noise floor, so no trend can be asserted.
   A quiescent *high-flow* window (steady high baseflow, no rising limb) would settle it; none
   was available in the fetched data. **OPEN QUESTION.**
6. **Any tidal candidate not tested.** Only the six seeded points plus SNAW1 and MROW1 were
   measured. Other lower-delta LIDs referenced in `DATA_SOURCES.md` (NSSW1, GLBW1, ARLW1,
   PUYW1, MRTW1) were **not** measured. If any is ever seeded, it needs this measurement first.
7. **Whether SNAW1's Event Zero transmission would hold at other flood magnitudes.** One flood
   was measured. The 3× collapse is a single observation, not a curve. **INFERENCE only.**
8. **`lowflow_2025` SNAW1 record completeness.** Only 2 422 of ~3 900 expected 15-minute stage
   points were returned for that window; the gap was not investigated. Results were stable
   against `lowflow_2026` regardless.
9. **Provisional data.** The 2026 window is entirely `Provisional`. Values may be revised.

---

## 8. Operational implications

**Not urgent.** Nothing about the platform's six seeded forecast points changes. Every one of
them measures a semidiurnal amplitude at or near the noise floor of a gauge that is definitively
not tidal. `rate_of_rise`, headroom and time-to-threshold are sound as implemented for all six.

**Correct, but reword.** `HYDROLOGY.md` §75's "the lower river is tidally influenced at Ferndale"
is not supported **at the gauge**. The measured value is −0.0015 to +0.0048 ft/ft, r ≤ 0.29,
M2 = 0.0006 ft — indistinguishable from a control gauge that has no tide. If a statement about
the reach below the gauge is wanted, it must be labelled as such and evidenced separately (§7.3).

**Prospective, and cheap to encode.** SNAW1 is genuinely tidal — 0.75–0.92 ft/ft at low flow,
0.22–0.32 during a flood, +1.25 h lag, 96.7 % of low-flow 6 h rate-of-rise samples spuriously
non-STEADY. `EVENT_ZERO.md` T8 already names SNAW1 in the forecast-evolution dataset, so it is
a plausible next seed. **The tidal-class machinery should exist before SNAW1 is seeded, not
after.** A `tidal_class` field that reads `FLUVIAL` for all six current points, with the measured
coefficients recorded, costs nothing today and prevents a wrong number the day SNAW1 lands.

**If a tidal class is added, it must be regime-aware and measured, not asserted.** A single
scalar is wrong: SNAW1's own coefficient moves by 3× between regimes, and the estimator choice
moves it by 25 % within a regime. Record the low-flow coefficient, the flood coefficient, the
lag, the estimator, the window, and the control gauge used to establish the noise floor.

**A method note worth keeping.** Any future tidal measurement in this repository should
(a) band-pass to 10–16 h and ignore the diurnal band entirely, (b) carry a known non-tidal
control gauge through the identical pipeline, and (c) report the phase lag alongside the slope.
Skipping (a) attributes glacier melt to the moon; skipping (b) makes hydrograph leakage look
like a discovery; skipping (c) understates transmission by ~20 % at a 1.25 h lag.

---

## 9. Reproducing this

All raw payloads and scripts were written to the session scratchpad, not the repository. To
regenerate from scratch, the four steps are:

1. `GET https://waterservices.usgs.gov/nwis/site/?format=rdb&siteOutput=expanded&sites=…` for
   site identity, gauge datum and HUC.
2. `GET https://api.waterdata.usgs.gov/ogcapi/v0/collections/continuous/items?monitoring_location_id=USGS-<site>&parameter_code=00065&datetime=<start>/<end>&limit=10000&f=json`,
   following `links[rel=next]`, for the three windows in §2.1.
3. `GET https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?product=water_level&station=<id>&begin_date=…&end_date=…&datum=MLLW&time_zone=gmt&units=english&format=json`
   in ≤31-day chunks (note: **`/api/prod/datagetter`**, not `/api/datagetter`, which 403s).
4. Regrid both to a common 15-minute grid, FFT band-pass to 10–16 h, OLS, then repeat the OLS
   over ±6 h of shift and keep the maximum-r shift. Carry USGS 12150800 through unchanged as
   the control.
