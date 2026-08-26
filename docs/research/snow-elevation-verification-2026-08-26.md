# Snow elevation verification — 2026-08-26

Independent re-measurement of the snow vertical-relevance claim in
`docs/research/doctrine-delta-2026-08-24.md` §7.5 / §12.3, from primary NRCS AWDB data fetched
this session. The review's arithmetic was recomputed site-by-site, and then pushed further:
per-basin rather than pooled, with the platform's **actual** estimator, and with a census of
whether each basin has the vertical sampling to stratify at all.

Status labels follow `docs/research/README.md`: **FACT** = computed this session from a fetched
payload (query given); **INFERENCE** = reasoned, not directly observed; **ASSUMPTION** = adopted
without proof; **OPEN QUESTION** = unresolved.

---

## 0. Verdict in one table

| Review claim (`doctrine-delta-2026-08-24.md` §7.5 / §12.3) | Verdict | Measured this session |
|---|---|---|
| On 2025-12-11, **twenty** western-WA Cascade SNOTEL sites below 4,500 ft | **Confirmed exactly** | n = **20** sites below 4,500 ft reporting a usable value/median pair |
| …held **14 %** of median SWE | **Confirmed** | **13.8 %** (ratio-of-sums), 13.7 % (mean-of-ratios) |
| …with **ten of them reading exactly 0.0 in** | **Confirmed exactly** | **10** of the 20 report SWE = 0.00 in |
| …while the all-station composite read **44 %** | **Confirmed within 1.6 pts** | **45.6 %** (ratio-of-sums) over 27 reporting sites |
| …because **three** crest/leeward North Cascades sites sat at **128–174 %** | **Confirmed** | Rainy Pass 128.0 %, Brown Top 133.9 %, Harts Pass **173.6 %** — the stated range, to the tenth. (A fourth, Swamp Creek 130.6 %, sits *below* 4,500 ft) |
| 2026-04-01 western-WA composite **55 %** of median SWE | **Confirmed** | **55.7 %** (ratio-of-sums, n = 25) |
| …with accumulated precipitation at **105–138 % of median at every station** | **Confirmed exactly** | per-station range **105–138 %**, pooled 118.1 %, **zero** stations below 100 % |
| Percent-of-median SWE is "misleading in the direction of calm" | **Partially confirmed — true for two basins, false for three** | The 44 %/14 % gap is a *pooled* artefact. Per basin the naive number is already ≈0 in three of six basins |
| Elevation stratification should be adopted | **Confirmed in principle, blocked in practice for half the basins** | Only 2 of 6 basins have the vertical sampling to support it. See §4 |

**Two findings the review does not contain:**

1. **Roughly half the 44 %/14 % gap is a basin-attribution error, not an elevation effect.**
   Three of the four sites inflating the composite have `associatedHucs` lying wholly or mostly
   in the **Columbia basin (HUC 1702\*)** — they are east-of-crest, leeward pillows filed under
   a Puget Sound HUC8. Removing them drops the pooled 2025-12-11 composite from **45.6 % to
   28.9 %** before any elevation banding is applied (§5).
2. **The platform does not compute the statistic the review criticises.** `swe_percent_of_median`
   in `packages/providers/awdb/.../normalize.py` returns a **mean of per-site ratios, per basin**
   — not a pooled ratio-of-sums across all of western Washington. On 2025-12-11 that estimator
   returns 0.4 % for the Cedar and 93.0 % for the Skagit. The 44 % figure is not a number the
   platform emits (§6).

---

## 1. Data fetched

The endpoint is the one the platform's own client already uses
(`packages/providers/awdb/src/cascade_providers_awdb/client.py`), with the two load-bearing
parameters that file documents (`periodRef=END`, `centralTendencyType=MEDIAN`).

**Station metadata** (fetched 2026-08-26):

```
GET https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/stations
      ?stationTriplets=*:WA:SNTL&activeOnly=true
```

→ **78** active WA SNOTEL stations. `activeOnly=false` returned the same 78, so there are no
retired WA SNOTEL sites in the AWDB response to recover extra vertical sampling from (FACT).

**Daily SWE with per-value median:**

```
GET https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/data
      ?stationTriplets=<29 mapped triplets>&elements=WTEQ&duration=DAILY
      &beginDate=2025-11-25&endDate=2025-12-20
      &periodRef=END&centralTendencyType=MEDIAN&returnFlags=true
```

and the same for `2026-03-25 → 2026-05-15`, and `elements=PREC` for `2026-03-30 → 2026-04-02`.

**Basin mapping** is the platform's own rule (`normalize.map_stations_to_basins`): a station is
assigned by the first eight digits of its **own** `huc` against the seeded basin HUC8 lists read
from `tests/fixtures/geo/basins_seed_basin_lod.geojson`:

| Basin | HUC8s |
|---|---|
| `basin:nooksack` | 17110004 |
| `basin:skagit` | 17110005, 17110006, 17110007 |
| `basin:snohomish-snoqualmie` | 17110009, 17110010, 17110011 |
| `basin:cedar` | 17110012 |
| `basin:green-duwamish` | 17110013 |
| `basin:puyallup-white` | 17110014 |

**FACT.** 29 of the 78 active WA SNOTEL sites map into a seeded basin. 49 lie elsewhere in
Washington.

---

## 2. The vertical sampling census — the decisive question

Every active SNOTEL pillow inside a seeded basin HUC8, by elevation (FACT, from the stations
payload above).

### basin:nooksack — n = 3, range 3,050–4,940 ft, spread 1,890 ft

| Triplet | Name | Elev (ft) | SHEF | HUC12 | Since |
|---|---|---|---|---|---|
| 910:WA:SNTL | Elbow Lake | 3,050 | ELSW1 | 171100040401 | 1995-08 |
| 909:WA:SNTL | Wells Creek | 4,040 | WCSW1 | 171100040103 | 1995-08 |
| 1011:WA:SNTL | MF Nooksack | 4,940 | MNOW1 | 171100040303 | 2002-10 |

### basin:skagit — n = 9, range 1,680–6,490 ft, spread 4,810 ft

| Triplet | Name | Elev (ft) | SHEF | HUC12 | Since |
|---|---|---|---|---|---|
| 991:WA:SNTL | Hozomeen Camp | 1,680 | HZOW1 | 171100050602 | 2000-10 |
| 999:WA:SNTL | Marten Ridge | 3,520 | MRTW1 | 171100051004 | 2006-07 |
| 990:WA:SNTL | Beaver Pass | 3,630 | BVPW1 | 171100050605 | 2000-10 |
| 975:WA:SNTL | Swamp Creek | 3,930 | SWSW1 | 171100050503 | 1999-10 |
| 817:WA:SNTL | Thunder Basin | 4,310 | THBW1 | 171100050702 | 1987-09 |
| 1319:WA:SNTL | Decline Creek | 4,480 | DCKW1 | 171100060403 | 2018-11 |
| 711:WA:SNTL | Rainy Pass | 4,880 | RAIW1 | 171100050503 | 1979-10 |
| 1080:WA:SNTL | Brown Top | 5,850 | BRTW1 | 171100050601 | 2009-09 |
| 515:WA:SNTL | Harts Pass | 6,490 | HRPW1 | 171100050501 | 1979-10 |

### basin:snohomish-snoqualmie — n = 4, range 3,320–4,010 ft, **spread 690 ft**

| Triplet | Name | Elev (ft) | SHEF | HUC12 | Since |
|---|---|---|---|---|---|
| 912:WA:SNTL | Skookum Creek | 3,320 | KUSW1 | 171100100503 | 1995-08 |
| 908:WA:SNTL | Alpine Meadows | 3,500 | APSW1 | 171100100501 | 1994-09 |
| 791:WA:SNTL | Stevens Pass | 3,940 | SVNW1 | 171100090102 | 1979-10 |
| 672:WA:SNTL | Olallie Meadows | 4,010 | OMWW1 | 171100100301 | 1979-10 |

### basin:cedar — n = 4, range 2,930–3,810 ft, **spread 880 ft**

| Triplet | Name | Elev (ft) | SHEF | HUC12 | Since |
|---|---|---|---|---|---|
| 898:WA:SNTL | Mount Gardner | 2,930 | MGSW1 | 171100120103 | 1993-10 |
| 899:WA:SNTL | Tinkham Creek | 3,000 | TKSW1 | 171100120101 | 1993-10 |
| 897:WA:SNTL | Meadows Pass | 3,230 | MPSW1 | 171100120101 | 1993-10 |
| 911:WA:SNTL | Rex River | 3,810 | RXSW1 | 171100120102 | 1995-08 |

### basin:green-duwamish — n = 4, range 3,210–4,640 ft, spread 1,430 ft

| Triplet | Name | Elev (ft) | SHEF | HUC12 | Since |
|---|---|---|---|---|---|
| 420:WA:SNTL | Cougar Mountain | 3,210 | CUMW1 | 171100130202 | 1979-10 |
| 788:WA:SNTL | Stampede Pass | 3,850 | SMPW1 | 171100130103 | 1979-10 |
| 1069:WA:SNTL | Lynn Lake | 3,900 | LAKW1 | 171100130203 | 2007-08 |
| 1068:WA:SNTL | Sawmill Ridge | 4,640 | SAWW1 | 171100130104 | 2006-07 |

### basin:puyallup-white — n = 5, range 2,250–5,810 ft, spread 3,560 ft

| Triplet | Name | Elev (ft) | SHEF | HUC12 | Since |
|---|---|---|---|---|---|
| 928:WA:SNTL | Huckleberry Creek | 2,250 | HKSW1 | 171100140307 | 1997-10 |
| 941:WA:SNTL | Mowich | 3,170 | MHSW1 | 171100140105 | 1998-09 |
| 942:WA:SNTL | Burnt Mountain | 4,160 | BUSW1 | 171100140103 | 1999-07 |
| 1085:WA:SNTL | Cayuse Pass | 5,260 | CAYW1 | 171100140301 | 2006-10 |
| 418:WA:SNTL | Corral Pass | 5,810 | COPW1 | 171100140307 | 1979-10 |

**Pooled across all six basins:** n = 29, 1,680–6,490 ft, median 3,900 ft.
Deciles (ft): 1,680 / 2,986 / 3,194 / 3,392 / 3,666 / 3,900 / 3,996 / 4,250 / 4,736 / 5,370 / 6,490.

---

## 3. Split counts at candidate band elevations

Number of sites **below / at-or-above** each candidate band (FACT):

| Basin | n | 3,000 ft | 3,500 ft | 4,000 ft | **4,500 ft** | 5,000 ft |
|---|---|---|---|---|---|---|
| nooksack | 3 | 0 / 3 | 1 / 2 | 1 / 2 | **2 / 1** | 3 / 0 |
| skagit | 9 | 1 / 8 | 1 / 8 | 4 / 5 | **6 / 3** | 7 / 2 |
| snohomish-snoqualmie | 4 | 0 / 4 | 1 / 3 | 3 / 1 | **4 / 0** | 4 / 0 |
| cedar | 4 | 1 / 3 | 3 / 1 | 4 / 0 | **4 / 0** | 4 / 0 |
| green-duwamish | 4 | 0 / 4 | 1 / 3 | 3 / 1 | **3 / 1** | 4 / 0 |
| puyallup-white | 5 | 1 / 4 | 2 / 3 | 2 / 3 | **3 / 2** | 3 / 2 |

---

## 4. Which basins can support an elevation-stratified snow statistic

**ASSUMPTION** used for the verdicts below: a band needs **at least two reporting sites** to be
a statistic rather than a single point observation. One pillow is a point measurement of one
aspect, one canopy and one drift; calling it a basin band statistic is the same fabrication the
doctrine forbids elsewhere.

| Basin | Can it stratify at 4,500 ft? | Verdict and reason |
|---|---|---|
| **skagit** | **Yes** | 6 below / 3 above (4 / 3 among reporting sites). The only basin with real vertical span — 4,810 ft. **But see §5:** 3 of the 9 sites are leeward Columbia-drainage pillows and 1 sits above Ross Dam |
| **puyallup-white** | **Yes** | 3 below / 2 above; 3,560 ft span; a genuine low site at 2,250 ft. The best-conditioned basin, though site count drops to 3 on some days (§7) |
| **nooksack** | **Marginal** | 2 below / 1 above. The upper band is a single pillow (MF Nooksack, 4,940 ft). Reportable as a two-band split only with the upper band flagged n = 1 |
| **green-duwamish** | **Marginal** | 3 below / 1 above. Upper band is a single pillow (Sawmill Ridge, 4,640 ft) |
| **snohomish-snoqualmie** | **No — UNKNOWN** | All four sites lie between 3,320 and 4,010 ft, a **690 ft** spread. The 4,500 ft upper band is **empty**; the "below" band is the whole network, so stratification returns the unstratified number and calls it something else. And its highest site, Stevens Pass, is itself leeward-associated (§5) |
| **cedar** | **No — UNKNOWN** | All four sites lie between 2,930 and 3,810 ft, an **880 ft** spread, entirely below 4,000 ft. No band above 3,810 ft can be observed at all |

**FACT.** Two of six basins can support an elevation-stratified SWE statistic at ~4,500 ft. Two
can support a two-band split only with a single-site upper band. **Two cannot, at any band
elevation, and the honest answer for them is UNKNOWN** — exactly as the task brief anticipated.

**INFERENCE.** For Cedar and Snohomish-Snoqualmie the problem is not the choice of band; it is
that the entire SNOTEL network sits inside one narrow elevation slice. No banding method, no
lapse-rate interpolation and no re-weighting recovers information that was never sampled. What
those basins can honestly report is "SWE at ~3,000–4,000 ft", with the band stated, and UNKNOWN
above it.

---

## 5. The finding the review missed: basin attribution, not elevation

**FACT.** The AWDB station record carries `associatedHucs` alongside the primary `huc`. For four
sites mapped into a seeded basin, the *majority* of `associatedHucs` lie in **HUC 1702\*** — the
Columbia basin, east of the Cascade crest:

| Triplet | Name | Elev (ft) | Primary HUC (used for mapping) | associatedHucs in Columbia |
|---|---|---|---|---|
| 515:WA:SNTL | Harts Pass | 6,490 | 171100050501 → **skagit** | **6 / 6** (Methow, Pasayten) |
| 711:WA:SNTL | Rainy Pass | 4,880 | 171100050503 → **skagit** | **5 / 5** (Methow, Stehekin/Chelan) |
| 975:WA:SNTL | Swamp Creek | 3,930 | 171100050503 → **skagit** | 4 / 6 |
| 791:WA:SNTL | Stevens Pass | 3,940 | 171100090102 → **snohomish-snoqualmie** | 4 / 6 |

Thunder Basin (4,310 ft, Skagit) is a fifth borderline case: 4 of 6 associated HUCs are 1702\*.

`normalize.map_stations_to_basins` already documents the Harts Pass case as a "known caveat kept
visible rather than patched". **FACT: it is not one site, it is at least four, and they are
disproportionately the high-percentage ones.** On 2025-12-11, three of the four sites reading
≥128 % of median were Harts Pass (173.6 %), Rainy Pass (128.0 %) and Swamp Creek (130.6 %) — all
leeward-associated. The review's characterisation "crest and leeward North Cascades sites" is
therefore **correct and confirmed from the station metadata**, but the review treats the
consequence as an elevation problem when a large part of it is a mapping problem.

**FACT — decomposing the 2025-12-11 gap** (ratio-of-sums, pooled across the six basins):

| Site set | Composite | n |
|---|---|---|
| All mapped sites | **45.6 %** | 27 |
| Windward only (leeward sites dropped) | **28.9 %** | 23 |
| Windward **and** below 4,500 ft | **9.9 %** | 18 |
| All mapped, below 4,500 ft (the review's cut) | 13.8 % | 20 |

Decomposed in that order, the fall from 45.6 % to 9.9 % is **−16.7 pts of basin attribution
followed by −19.0 pts of elevation** — the two effects are of comparable size, and roughly half
of the gap the review attributes to elevation disappears once the leeward pillows are excluded,
before any banding is applied. (The review's own cut, 13.8 %, keeps the leeward pillows and
takes only the elevation step.)

**FACT — the Skagit alone**, ratio-of-sums:

| Day | All 7 reporting | Windward only (4) | Windward and < 4,500 ft (3) |
|---|---|---|---|
| 2025-12-08 | 93.5 % | 67.2 % | 33.5 % |
| 2025-12-10 | 102.6 % | 68.1 % | 28.6 % |
| **2025-12-11** | **97.3 %** | **63.8 %** | **26.3 %** |
| 2025-12-12 | 89.8 % | 57.5 % | 23.7 % |
| 2025-12-15 | 86.0 % | 51.6 % | 18.6 % |

**INFERENCE, separate and also unremarked:** the Skagit's one low-elevation pillow, Hozomeen
Camp at 1,680 ft, sits on Ross Lake — i.e. **upstream of Ross Dam**, a flood-control reservoir.
Its SWE is not hydrologically available to the Mount Vernon forecast point without passing a
regulated release decision. It reported no value on 2025-12-11 in any case. The Skagit's usable
low-elevation sampling is therefore thinner than its nine-site count suggests.

---

## 6. What the platform actually computes

**FACT.** `swe_percent_of_median` in
`packages/providers/awdb/src/cascade_providers_awdb/normalize.py` ends:

```
mean = sum(c.percent_of_median for c in contributions) / len(contributions)
```

That is a **mean of per-site ratios**, computed **per basin**, over sites mapped by primary HUC8,
with exclusions for absent value, absent median, median ≤ 0, and suspect QC flag. It is not the
pooled ratio-of-sums the review's 44 % figure represents.

The two estimators are not interchangeable. Ratio-of-sums weights a site by its median SWE, so a
deep high pillow dominates; mean-of-ratios weights every site equally, so a shallow low pillow
with a tiny median can swing the answer. On **2025-12-08 in the Puyallup-White** the two differ
by more than a factor of two: **48.7 %** (ratio-of-sums) against **23.3 %** (mean-of-ratios).
This is an *independent* source of the same "misleading in the direction of calm" defect, and
the review does not mention it.

### 6.1 The platform's actual numbers, 2025-12-11 (the day before the record Skagit crest)

Mean-of-ratios, per basin, reproducing the shipped code path exactly (FACT):

| Basin | ALL sites | < 4,500 ft | ≥ 4,500 ft | ALL − (<4,500) |
|---|---|---|---|---|
| nooksack | 29.7 % (n=3) | 17.1 % (n=2) | 54.9 % (n=1) | +12.6 pts |
| **skagit** | **93.0 % (n=7)** | **53.9 % (n=4)** | **145.2 % (n=3)** | **+39.1 pts** |
| snohomish-snoqualmie | 3.9 % (n=4) | 3.9 % (n=4) | UNKNOWN (n=0) | +0.0 pts |
| cedar | 0.4 % (n=4) | 0.4 % (n=4) | UNKNOWN (n=0) | +0.0 pts |
| green-duwamish | 2.1 % (n=4) | 2.1 % (n=3) | 2.3 % (n=1) | +0.0 pts |
| puyallup-white | 16.2 % (n=5) | 0.0 % (n=3) | 40.5 % (n=2) | +16.2 pts |
| *(pooled — not emitted by the platform)* | *31.4 % (n=27)* | *13.7 % (n=20)* | — | *+17.7 pts* |

**This is the most important correction in this file.** Per basin, on the critical day:

- **Skagit: the defect is real and large.** 93.0 % against 53.9 % below 4,500 ft, and the ≥4,500
  band reads 145.2 %. A reader shown "93 % of median" on the day before a record crest would
  draw exactly the wrong picture. And per §5, that 93 % is itself inflated by leeward pillows.
- **Puyallup-White: real.** 16.2 % against **0.0 %** below 4,500 ft — the low band is bare.
- **Nooksack: modest.** 29.7 % against 17.1 %.
- **Snohomish-Snoqualmie, Cedar, Green-Duwamish: no defect at all.** The naive statistic already
  read 0.4–3.9 %. It was not concealing anything, because there was no snow anywhere in those
  basins to conceal. Stratifying them changes the number by 0.0 pts — and cannot, because their
  upper band is empty (§4).

**Refutation of the general framing.** The review's §7.5 asserts that "percent-of-median SWE is
misleading in the direction of calm". Measured per basin on the day the review itself selects,
that is true for **two** of the six basins, marginal for a third, and **false for three**. The
44 %/14 % contrast is a property of a pooled six-basin composite that the platform does not
compute and, on this evidence, should not start computing.

### 6.2 Per-basin evolution through Event Zero

Ratio-of-sums, ALL sites / below 4,500 ft, with reporting counts (FACT). The full 2025-11-25 →
2025-12-20 series was computed; a representative slice:

| Day | nooksack | skagit | snohomish | cedar | green-duw | puyallup |
|---|---|---|---|---|---|---|
| 2025-12-01 | 18.9 / 18.3 (3/2) | 66.5 / 29.8 (7/4) | 20.0 / 20.0 (4/4) | 23.7 / 23.7 (4/4) | 25.9 / 21.8 (4/3) | 36.0 / 30.0 (5/3) |
| 2025-12-05 | 35.5 / 35.4 | 70.8 / 34.4 | 19.1 / 19.1 | 11.6 / 11.6 | 20.0 / 16.0 | 37.5 / 4.0 |
| 2025-12-08 | 46.1 / 27.5 | 93.5 / 44.1 | 12.8 / 12.8 | 1.1 / 1.1 | 8.0 / 4.7 | 48.7 / 0.0 |
| 2025-12-10 | 35.5 / 19.2 | 102.6 / 39.5 | 4.6 / 4.6 | 0.5 / 0.5 | 3.1 / 2.7 | 40.9 / 0.0 |
| **2025-12-11** | **33.8 / 17.0** | **97.3 / 37.2** | **3.9 / 3.9** | **0.5 / 0.5** | **2.0 / 2.0** | **34.6 / 0.0** |
| 2025-12-12 | 30.6 / 15.4 | 89.8 / 34.6 | 1.9 / 1.9 | 0.0 / 0.0 | 1.5 / 1.3 | 28.0 / 0.0 |
| 2025-12-15 | 18.3 / 7.3 | 86.0 / 27.1 | 0.0 / 0.0 | 0.0 / 0.0 | 0.9 / 1.1 | 17.3 / 0.0 |
| 2025-12-20 | 45.0 / 35.7 | 109.4 / 55.6 | 40.8 / 40.8 | 35.5 / 35.5 | 27.0 / 32.4 | 42.1 / 20.8 |

**FACT.** Pooled across all six basins, the low-band collapse through the AR sequence is stark:
the < 4,500 ft composite fell from 25.9 % on 2025-12-04 to **8.5 % on 2025-12-15**, and the
< 3,500 ft composite from 21.7 % to **0.3 %**. Note that this collapse means there was *less*
low-elevation snow available as the storm arrived — which reduces rain-on-snow potential rather
than raising it (§8).

### 6.3 Site-by-site, 2025-12-11 (the review's day, reproduced in full)

| Elev (ft) | Site | SWE (in) | Median (in) | % of median |
|---|---|---|---|---|
| 1,680 | Hozomeen Camp | — | — | *no value* |
| 2,250 | Huckleberry Creek | 0.00 | 0.30 | **0.0** |
| 2,930 | Mount Gardner | 0.00 | 2.80 | **0.0** |
| 3,000 | Tinkham Creek | 0.10 | 5.70 | 1.8 |
| 3,050 | Elbow Lake | 0.10 | 7.70 | 1.3 |
| 3,170 | Mowich | 0.00 | 0.20 | **0.0** |
| 3,210 | Cougar Mountain | 0.00 | 4.00 | **0.0** |
| 3,230 | Meadows Pass | 0.00 | 5.40 | **0.0** |
| 3,320 | Skookum Creek | 0.00 | 6.10 | **0.0** |
| 3,500 | Alpine Meadows | 0.00 | 10.20 | **0.0** |
| 3,520 | Marten Ridge | 0.60 | 11.40 | 5.3 |
| 3,630 | Beaver Pass | 0.90 | 10.10 | 8.9 |
| 3,810 | Rex River | 0.00 | 5.90 | **0.0** |
| 3,850 | Stampede Pass | 0.20 | 8.60 | 2.3 |
| 3,900 | Lynn Lake | 0.10 | 2.60 | 3.8 |
| 3,930 | Swamp Creek *(leeward)* | 4.70 | 3.60 | **130.6** |
| 3,940 | Stevens Pass *(leeward)* | 1.50 | 9.60 | 15.6 |
| 4,010 | Olallie Meadows | 0.00 | 12.60 | **0.0** |
| 4,040 | Wells Creek | 2.50 | 7.60 | 32.9 |
| 4,160 | Burnt Mountain | 0.00 | 2.00 | **0.0** |
| 4,310 | Thunder Basin | 6.60 | 9.30 | 71.0 |
| 4,480 | Decline Creek | 2.80 | *absent* | *excluded* |
| 4,640 | Sawmill Ridge | 0.10 | 4.40 | 2.3 |
| 4,880 | Rainy Pass *(leeward)* | 13.70 | 10.70 | **128.0** |
| 4,940 | MF Nooksack | 6.70 | 12.20 | 54.9 |
| 5,260 | Cayuse Pass | 3.20 | 12.20 | 26.2 |
| 5,810 | Corral Pass | 5.10 | 9.30 | 54.8 |
| 5,850 | Brown Top | 22.10 | 16.50 | **133.9** |
| 6,490 | Harts Pass *(leeward)* | 25.70 | 14.80 | **173.6** |

Below 4,500 ft: 20 reporting, **10 at exactly 0.00 in**, ratio-of-sums 13.8 %.
All reporting: 27, ratio-of-sums 45.6 %, mean-of-ratios 31.4 %.

**Note the ordering is not monotonic in elevation.** Swamp Creek at 3,930 ft reads 130.6 %
while Olallie Meadows at 4,010 ft reads 0.0 % and Burnt Mountain at 4,160 ft reads 0.0 %. A pure
elevation band cannot separate those; only the windward/leeward distinction can. This is direct
evidence that **elevation alone is the wrong single axis**.

---

## 7. Spring 2026 — the review's second numeric claim

**FACT.** 2026-04-01, pooled across the six basins:

| Cut | Ratio-of-sums | n |
|---|---|---|
| All mapped sites | **55.7 %** | 25 |
| Below 4,500 ft | 45.6 % | 18 |
| At/above 4,500 ft | 73.2 % | 7 |

The review's "western-WA composite read 55 % of median SWE" is confirmed.

**FACT.** 2026-04-01 accumulated water-year precipitation (PREC, percent of median):
per-station range **105–138 %**, pooled 118.1 %, n = 25, **zero stations below 100 %**. The
review's "105–138 % of median at every station" is confirmed exactly. Its **warm snow drought**
characterisation of WY2026 stands on measured data.

Per basin (ratio-of-sums, all sites / below 4,500 ft), and the same on 2026-05-01:

| Basin | 2026-04-01 all | < 4,500 ft | 2026-05-01 all | < 4,500 ft |
|---|---|---|---|---|
| nooksack | 41.1 % (3) | 33.6 % (2) | 28.9 % | 16.6 % |
| skagit | 75.4 % (7) | 47.2 % (4) | 59.6 % | 22.5 % |
| snohomish-snoqualmie | 58.0 % (4) | 58.0 % (4) | 38.9 % | 38.9 % |
| cedar | 38.1 % (4) | 38.1 % (4) | 13.4 % | 13.4 % |
| green-duwamish | 32.6 % (4) | 35.7 % (3) | 8.4 % | 14.1 % |
| puyallup-white | 56.0 % (3) | 40.7 % (1) | 39.2 % | 0.0 % |

Under the platform's own mean-of-ratios estimator on 2026-04-01: skagit 75.5 % all / 53.1 %
below 4,500 (+22.4 pts); puyallup-white 55.6 % / 40.7 % (+14.9); nooksack 39.7 % / 34.6 % (+5.1);
green-duwamish 32.0 % / 33.7 % (**−1.7**, i.e. the low band is *higher*); cedar and
snohomish-snoqualmie +0.0 by construction.

**FACT — a data-quality caveat the review does not raise.** The reporting site count **changes
day to day**, so a composite is not comparable across days without stating n. On 2026-04-01 the
Puyallup-White fell to n = 3 of 5: Huckleberry Creek (2,250 ft) reports median **0.0** in and is
excluded by the platform's own `median_zero` rule, and Mowich (3,170 ft) reports no value at all.
**Both of the basin's low-elevation sites drop out in spring** — precisely when the low band is
what matters. Similarly Decline Creek (4,480 ft) reports a value with **no median** on both
2025-12-11 and 2026-04-01, and Hozomeen Camp (1,680 ft) reports nothing on either day. On
2025-12-11 the Skagit ran on 7 of 9 sites.

---

## 8. On "understating rain-on-snow vulnerability"

The task brief paraphrases the review as saying the naive statistic **understates**
rain-on-snow vulnerability. The review's own wording (line 735) is narrower and better:
percent-of-median SWE is *"misleading in the direction of calm"*.

**These are not the same claim, and the physics runs the other way.** Rain-on-snow requires snow
to *exist* at the elevations rain will fall on. A sub-4,500 ft band at 14 % of median with half
its pillows bare means there was **very little low-elevation snow to melt** — which *lowers*
rain-on-snow potential. The composite's 44 % was not hiding a rain-on-snow threat; it was
hiding the fact that Event Zero was, as `EVENT_ZERO.md` and the review's §12.3 both say, **rain
on saturated soils rather than rain on snow**.

**INFERENCE.** The defect is therefore one of **wrong-mechanism attribution**, not of understated
magnitude. A displayed "44 % of median snowpack" invites a reader to reason about a snow buffer
and about melt contribution — when the correct operational reading was "there is effectively no
snow below 4,500 ft; treat this as a rain-on-wet-soil event". Both errors are serious, and the
doctrinal fix (band the statistic, or refuse it) is the same. But the doctrine text should say
*which* error it is, because a claim that low-elevation snow deficits raise rain-on-snow risk is
physically backwards and would not survive review.

---

## 9. What could NOT be verified

1. **The exact site universe behind the review's 44 %.** I measure 45.6 % over 27 sites mapped
   by seeded-basin HUC8. The review says "western-Washington Cascade" and elsewhere cites "31
   active western-Washington sites", so its universe differs slightly. The 1.6-pt gap is
   immaterial to the conclusion but the sets are not identical. **OPEN QUESTION.**
2. **Why the review counts three sites at 128–174 % when four exceed 128 %.** Swamp Creek
   (3,930 ft, 130.6 %) is the fourth; it sits below 4,500 ft, so it may have been deliberately
   assigned to the low band. Not stated in the review. **OPEN QUESTION.**
3. **Whether 4,500 ft is defensible for any basin.** It is *not* recommended here, and no
   alternative universal band is proposed. See §10.
4. **Basin hypsometry.** None exists in the repository — basin geometry is HUC8 unions. Without
   it there is no way to know what *fraction of basin area* a SNOTEL band represents, so even a
   well-sampled basin cannot convert a band statistic into a basin quantity. The review's §7.5
   calls this "the largest structural blocker in the snow domain"; **confirmed, and nothing in
   this session changes it.**
5. **QC/QA flag effects.** `returnFlags=true` was requested and the flags were fetched, but the
   platform's `SUSPECT_QC_FLAGS` exclusion was **not** applied in my aggregations. The platform's
   live numbers may differ slightly from §6.1 wherever a suspect flag is present.
6. **Whether SNOTEL pillow elevations represent the surrounding band.** Pillows are sited for
   access and reliability, not for statistical representativeness of an elevation band; canopy,
   aspect and drift are unmeasured. Every "band" number here inherits that. **ASSUMPTION.**
7. **SNODAS or any gridded product.** Not fetched. The review's "fuse, do not pick one" position
   was not tested, and gridded data is the obvious route to rescuing Cedar and
   Snohomish-Snoqualmie. **OPEN QUESTION.**
8. **Forecast snow level.** Not fetched. A data-driven band requires it (§10) and it was out of
   scope here.
9. **Sites outside the seeded HUC8s.** 49 of 78 active WA SNOTEL sites are unmapped. Some may sit
   just outside a basin boundary yet be more representative of it than a leeward pillow inside it
   — the mirror image of the §5 problem. Not investigated. **OPEN QUESTION.**
10. **Longer records.** Only 2025-11-25 → 2025-12-20 and 2026-03-25 → 2026-05-15 were fetched.
    No multi-year climatology of the stratification gap was computed.

---

## 10. Operational implications

**Do not adopt 4,500 ft, or any single universal band.** The measured evidence against it is
direct: at 4,500 ft the upper band is **empty** in two of six basins, and a **single pillow** in
two more. A universal band would emit a confident number for the Skagit and Puyallup-White, a
one-site number dressed as a statistic for the Nooksack and Green-Duwamish, and a tautology for
the Cedar and Snohomish-Snoqualmie. That last failure mode is the dangerous one, because it
returns a number rather than UNKNOWN.

**The honest per-basin capability today** (§4): stratify Skagit and Puyallup-White; report a
flagged two-band split for Nooksack and Green-Duwamish; return **UNKNOWN above ~4,000 ft** for
Cedar and Snohomish-Snoqualmie and say why.

**Fix the mapping before, or alongside, the banding.** §5 shows roughly half the pooled
2025-12-11 gap is leeward pillows, not elevation. `associatedHucs` is already in the payload the
platform fetches and is already parsed into the station record; using it — a site whose
associated HUCs are majority-1702\* is not a Puget Sound basin site — is a smaller change than
elevation banding and removes a larger share of the error. The four sites are Harts Pass,
Rainy Pass, Swamp Creek and Stevens Pass; Thunder Basin is borderline at 4/6.

**Report n, and report the exclusions, with every composite.** §7 shows the reporting count
moving 5→3 in one basin between December and April, with **both low-elevation sites** dropping
out in spring. The `ContextResult.excluded` counters already carry this; whatever renders the
number must render n and the band alongside it, or the number is not comparable to yesterday's.

**Pick one estimator and name it.** Ratio-of-sums and mean-of-ratios differ by more than 2× in
a real case (§6). The shipped code uses mean-of-ratios. Whichever survives, the method id must
say so, because the two answer different questions: ratio-of-sums asks "what fraction of normal
basin storage is present", mean-of-ratios asks "how anomalous is the typical site".

**What a data-driven band would need**, in dependency order:
1. **Basin hypsometry** from 3DEP — area-elevation curves per basin, to weight a band by the
   area it stands for. Without it no band statistic is a basin statistic. Currently blocked.
2. **Forecast snow level** per basin per cycle — so the band is the *storm's* rain/snow
   boundary, not a constant. The band that matters is "below the snow level for the next 24 h",
   which moves by more than 3,000 ft between storms.
3. **A windward/leeward classification** of every pillow (§5), because the 2025-12-11 record
   shows elevation and exposure are independent axes: 130.6 % at 3,930 ft leeward against 0.0 %
   at 4,010 ft windward.
4. **A minimum-sites rule** that returns UNKNOWN rather than a one-pillow band.

Until (1) and (2) exist, the defensible interim statement is per basin and explicitly bounded:
*"SWE at the N sites between X and Y ft is Z % of median (method, day, n, exclusions); no
observation exists above Y ft."* That is narrower than the review's proposal and it is
supportable with the network as it stands today.
