# CONTRADICTION REGISTER — disputed numbers, and what they are allowed to become

*Opened 2026-08-26. One row per contradiction. The register is the gate between the corpus and
`HYDROLOGY.md`: a disputed number does not enter normative doctrine until its row says it may.*

The science corpus (`docs/research/corpus/CROSS-DOMAIN-FINDINGS.md` §2) named eleven contradictions
requiring adjudication, **X1–X11**. Two measurement-based verifications completed 2026-08-26
(`research/tidal-gauge-verification-2026-08-26.md`, `research/snow-elevation-verification-2026-08-26.md`)
closed some of them and opened six more, **X12–X17**. Nothing here is new evidence; everything here
is a statement about *what the platform is permitted to assert* while the evidence stands as it does.

**Labels** follow `docs/research/README.md`: **FACT** = read on a fetched page or computed from a
fetched payload (query given at the source); **INFERENCE** = reasoned, not directly observed;
**ASSUMPTION** = adopted without proof; **OPEN QUESTION** = unresolved.

**The blocking test**, applied literally in every row: *does a 6–120 hour flood prediction for a named
Puget Sound basin currently depend on picking a side?* If not, the row says NO and says why. Six of
the seventeen rows conclude that **nothing in the platform depends on the answer at all**. That is the
most useful thing this register does — it separates interesting from operational.

**Seeded scope**, for every "affected method" judgement below: six basins (`nooksack`, `skagit`,
`snohomish-snoqualmie`, `cedar`, `green-duwamish`, `puyallup-white`) and six forecast points
(MVEW1 12200500, AUBW1 12113000, WRAW1 12100490, NKSW1 12213100, RNTW1 12119000, CRNW1 12149000).
The Skagit basin's *susceptibility* gauge is the Sauk 12189500, not MVEW1
(`DATA_SOURCES.md` H9 note, 2026-08-24). SNAW1 (Snohomish at Snohomish, 12155500) is **not seeded**.

---

## 1. Index — everything that blocks, in one screen

| id | In one line | Operationally blocking? | Current disposition | Doctrine asserts a side? |
|---|---|---|---|---|
| **X8** | Day-of-year ladder: longest record or recent 30 years? **PDO-phase dependent.** | **YES** | **OPEN — BLOCKING** | no — needs addition |
| X1 | Mount Vernon stage–discharge drift: −29 % / −9 to −11 % / −4.4 % / "variance, not trend" | no | OPEN — NOT BLOCKING | §12 prose needs hedging |
| X2 | Does lower-Skagit crest lag lengthen or shorten with magnitude? | no | OPEN — NOT BLOCKING | §2 needs updating |
| X3 | Is Concrete→Mount Vernon attenuation a big-flood phenomenon? | no | OPEN — NOT BLOCKING | silent — safe |
| X4 | Rain-on-snow melt energy: turbulent flux or net radiation? | no | OPEN — NOT BLOCKING | **§7 asserts FACT — needs correction** |
| X5 | Are western Washington flood storms short or long? | no | OPEN — NOT BLOCKING | silent — safe |
| X6 | Do WA peak flows need mixed-population flood-frequency treatment? | no | OPEN — NOT BLOCKING | §13 needs an addition |
| X7 | Does the forest-harvest peak-flow effect grow or vanish with return period? | no | OPEN — NOT BLOCKING | silent — safe |
| X9 | Is the Mount Vernon forecast point compound at all? | no | **RESOLVED BY MEASUREMENT** (tide) / OPEN — NOT BLOCKING (backwater) | silent — safe |
| X10 | Is the AR signal at Washington's latitude rising? | no | RESOLVED BY ADJUDICATION (action-invariant) | silent — safe |
| X11 | Kirchner's ~1,000 km² scale limit vs the corpus's use of his method | no | OPEN — NOT BLOCKING | silent — safe |
| X12 | Doctrine names Ferndale as the tidal problem; measurement says it is not tidal | no | **RESOLVED BY MEASUREMENT** | **§2 line 75 — needs correction** |
| X13 | Four SNOTEL sites mapped into seeded basins are majority-Columbia | no | **RESOLVED BY MEASUREMENT** (fact) / OPEN — NOT BLOCKING (fix) | `DATA_SOURCES.md` §390–391 needs correction |
| X14 | Is elevation-stratified snow computable for Cedar and Snohomish-Snoqualmie? | no | **RESOLVED BY MEASUREMENT — no, for 2 of 6 basins** | §3 input table needs hedging |
| X15 | SNAW1 transmits 0.831 ft/ft (r = 0.94) — a single scalar | no (SNAW1 unseeded) | **RESOLVED BY MEASUREMENT — refuted as a scalar** | silent — safe |
| X16 | Which percent-of-median SWE estimator: ratio-of-sums or mean-of-ratios? | no | OPEN — NOT BLOCKING (a declaration, not an experiment) | silent — safe |
| X17 | Does a low-elevation SWE deficit *raise* rain-on-snow risk? | no | RESOLVED BY ADJUDICATION (mass balance) | silent — safe |

**One contradiction currently blocks an operational decision: X8.** Everything else is either resolved,
or open on a question no shipped surface consults.

---

## 2. The register

### X1 · Magnitude of the Mount Vernon stage–discharge drift

- **claim A** — The lower Skagit has lost **9–11 % of conveyance at flood stage** since the late 1980s:
  rating-independent measured pairs at 12200500 normalised to 33.00 ft give 105,759 → 94,062 cfs
  (−11.1 %), band −8 % to −11 % depending on which of four pre-2010 measurements are kept, two-standard-error
  interval ≈ ±5 %. *Source: `corpus/routing-hydraulics.md` §5.2 (USGS OGC `field-measurements`, 430 pairs
  1959–2026, fetched 2026-08-24). Labelled INFERENCE with strong physical corroboration, not FACT.*
- **claim B** — Three incompatible alternatives for the same reach:
  **(i) −29 %** (prior repo pass, `research/flood-genesis-mechanisms-2026-08-24.md` §0 item 6) from two
  points, one a 1906 indirect estimate whose peak *day* is unknown (peak codes 7, Bd);
  **(ii) −4.4 %** at 37 ft, population-level over 85 paired annual peaks, pre-1980 vs 1980+ log-linear fits
  (`corpus/climate-change.md` §3);
  **(iii) not a trend at all** — *"the rating did not drift, it destabilised"*: residual sd
  **0.25 ft (1948–2005) → 1.38 ft (2006–2024)**, Mann–Kendall p = 0.0006 on the residual sequence
  (`corpus/cascading-hazards.md` §5.4, reproduced in that file's adversarial re-run).
- **affected method** — **Nothing shipped consults it.** `HYDROLOGY.md` §9 forbids stage↔flow conversion,
  MVEW1's official categories are stage-defined, and `headroom.py` works in stage. The drift would bind
  on `method:nwps-rating-conversion@1.0.0` (unbuilt, `NEXT_STEPS.md` §140) and on the proposed
  `method:rating-epoch@1.0.0` + `method:conveyance-drift@1.0.0` (method-spec M1.3), which are the
  homogeneity boundary for `method:streamflow-doy-climatology@2.0.0`. Note the Skagit susceptibility
  ladder is built on the **Sauk** 12189500, not on the drifting MVEW1 rating.
- **operationally blocking?** — **NO.** No 6–120 h statement for any seeded basin converts a Mount Vernon
  stage to a flow or a flow to a stage today.
- **current disposition** — **OPEN — NOT BLOCKING.** The −29 % figure is **SUPERSEDED**: routing §5.2
  Step 6 shows both of its data points are contaminated (1906 indirect, day unknown; the 1990-11-25
  crest is *breach-depressed* by the Fir Island levee failure, per the 2013 Skagit Hydrology Tech Doc).
  The remaining three are not the same quantity — different estimators, reference stages, windows, and
  one is a variance claim — and the platform has adopted none. All three agree on the operationally
  important part: the **scatter** (±0.68 to ±1.4 ft) is comparable to or larger than the **trend**,
  against **2 ft** NWS category spacing at that gauge.
- **evidence needed to resolve** — One estimator, declared. Refit from USGS OGC `field-measurements` at
  12200500: all pairs ≥ 80,000 cfs, quality ≠ *Poor*, **excluding 1990-11-25** (breach), normalised to a
  declared reference stage of 33.00 ft, reporting the change with a two-standard-error interval **and**
  the sensitivity to the rating-24.0 curve shape the normalisation borrows (untested in §5.2). Separately,
  settle trend-vs-ramp-vs-variance on the 41 annual peaks: Theil–Sen on the residual, a breakpoint test at
  WY2006, and Levene's test on residual variance pre/post-2006. Window WY1948–2025.
- **doctrine status** — `HYDROLOGY.md` does not state a drift figure, so nothing to correct there.
  **§12 needs hedging**: "above the 1990 record of 37.37 ft despite a lower flow (~152,000 cfs in 1990)"
  compares a levee-intact 2025 crest against a breach-depressed 1990 crest. That pairing is not a
  homogeneous hydraulic comparison and it *exaggerates* the drift. Add the Fir Island caveat or drop
  the comparison.

---

### X2 · Does crest lag on the lower Skagit lengthen or shorten with flood magnitude?

- **claim A** — Bigger floods travel **slower**. Twelve events 2003–2025, Concrete 12194000 → Mount
  Vernon 12200500: median lag **16.9 h**, sd 3.5 h, range 9.5–23.8 h; r = **+0.65** against peak
  discharge (17.0 h for ≥100 kcfs vs 14.5 h below), attributed to Nookachamps and overbank storage
  engagement. *Source: `corpus/routing-hydraulics.md` §5.1, FACT for the distribution, INFERENCE/emerging
  for the trend.*
- **claim B** — USACE states the opposite: hydraulic travel time through this reach **decreases** from
  15–20 h at low flow to 10–15 h at higher discharges. *Source: USACE Skagit hydrology document 2013
  §2.4.6.4, fetched, quoted in `routing-hydraulics.md` §5.1.* The same file concedes the estimator is
  fragile: `argmax` on a broad crest is not a robust timestamp, the most influential event (2006,
  23.75 h) moves to 18.25 h on a different tie-break, and crest breadth grows with flood size, so the
  tie-breaking noise is itself magnitude-dependent.
- **affected method** — **Nothing shipped consults it.** The platform's time-to-threshold
  (`headroom.py`, `HYDROLOGY.md` §9) is `headroom ÷ rate of rise` at a *single* gauge; it does not use
  an upstream→downstream lag. `NEXT_STEPS.md` gap 6 records that there is no reach topology in the
  store. This binds the moment an upstream-lead-time feature ships.
- **operationally blocking?** — **NO.** No seeded-basin lead time is currently derived from a
  Concrete→Mount Vernon lag.
- **current disposition** — **OPEN — NOT BLOCKING.** Prior adjudication stands
  (`research/method-spec-2026-08-24.md` §1.1): store the empirical lag *distribution*, label it a
  storage-and-inflow statistic rather than a wave celerity (implied crest celerity 3.4 ft s⁻¹ is
  2.2–5× below the kinematic βV), and **do not assert the magnitude trend**.
- **evidence needed to resolve** — Recompute all twelve events with a crest-**centroid** timing method
  (flow-weighted time centroid over the hydrograph above 80 % of peak) in place of `argmax`, add the
  eight historical events in USACE 2013 Table 9 (1949, 1951, 1955, 1975, 1980, both Nov 1990, 1995),
  and report Pearson r of lag against peak Q on n = 20 with a leave-one-out range. If the sign survives
  the estimator change, the trend is real; if it does not, only the distribution is publishable.
- **doctrine status** — `HYDROLOGY.md` §2 says the lower Skagit "crests roughly a day after the
  upper-basin peaks (INFERENCE from routing distance; calibrate from history)". The label is honest but
  the number is **~30 % long** against a measured 16.9 h median. **Needs updating** to the measured
  distribution, and it should keep the INFERENCE label on the magnitude dependence.

---

### X3 · Is attenuation on Concrete → Mount Vernon a big-flood phenomenon?

- **claim A** — Attenuation grows with magnitude: r = −0.57 over 2003–2025 (−0.71 on the absolute cfs
  change, so not a normalisation artefact), ≥100 kcfs median **−11.0 %**.
  *Source: `corpus/routing-hydraulics.md` §5.1.*
- **claim B** — USACE asserts the opposite generalisation in the same document: high-peak, high-volume
  floods fill channel storage and, with **356 mi²** of local inflow between the two gauges, *increase*
  the peak downstream. Adding the eight Table 9 historical events keeps the sign (r = −0.52, n = 20) but
  roughly halves the effect (≥100 kcfs median **−5.2 %**), and several of the largest floods on record
  **amplified**: Feb 1951 +3.6 %, Dec 1975 +6.6 %, Nov 1990 second flood +4.1 %.
  *Source: USACE 2013, fetched; recomputation in `routing-hydraulics.md` §5.1.*
- **affected method** — **Nothing in the platform depends on this.** No shipped or proposed method routes
  a peak from Concrete to Mount Vernon; Concrete (CONW1) appears only as MVEW1's `upstreamLid` in
  `DOMAIN_MODEL.md` §149.
- **operationally blocking?** — **NO.** Nothing routes.
- **current disposition** — **OPEN — NOT BLOCKING.** The file's own verdict is "bimodal", which is honest
  and is not a usable parameter.
- **evidence needed to resolve** — On the same n = 20 event set, test whether local inflow explains the
  amplifying cases: regress Δpeak (%) on peak Q **and** on incremental-area runoff over the 356 mi²
  between the gauges (basin-mean QPE from MRMS/Stage IV or AORC over the incremental polygon, 48 h
  preceding the Concrete crest). Statistic: sign and significance of the local-inflow coefficient with
  peak Q controlled. Bimodality is a usable parameter only once the discriminator is named.
- **doctrine status** — `HYDROLOGY.md` is silent on attenuation. **Safe to keep.**

---

### X4 · Rain-on-snow melt energy partitioning — the doctrine asserts one side as FACT

- **claim A** — Melt energy in rain-on-snow is dominated by **turbulent sensible + latent flux**:
  **60–90 %** of melt energy, February 1996 Pacific Northwest flood, Oregon Cascades, **open,
  wind-exposed** sites. *Source: Marks et al. 1998, via `corpus/snow-hydrology.md` §2.4.*
- **claim B** — **Net radiation is the largest term.** Mazurkiewicz, Callery & McDonnell 2008 (H.J.
  Andrews, three sites 1,018–1,294 m, **eight years**, SNOBAL): net radiation **55 % / 35 % / 33 %**,
  turbulent max 42 %, and the authors explicitly *"question the general perception of turbulent energy
  exchange dominance of ROS and seasonal melt in the PNW"*. Li et al. 2019 (CONUS, process model):
  **net radiation 68 %**, longwave-dominated. *Source: `corpus/snow-hydrology.md` §2.4, §4 contested #1.*
- **claim B′ (the sub-dispute that matters most)** — **Advected rain heat** is contested at
  **< 10 %** (Trubilowicz & Moore 2017, BC, 286 ROS events over 10 yr) vs **10–15 %** (Mazurkiewicz 2008)
  vs **29–44 % of the energy budget in persistent-melt events** (Jennings & Jones 2015). The high value
  belongs to precisely the persistent-melt events that produce floods.
- **affected method** — **No shipped surface computes a ROS term.** `CROSS-DOMAIN-FINDINGS.md` §3 L4
  records the link as simultaneously unobserved, unmodelled and unsettled: wind and dewpoint at pack
  elevation are **not in the ingest at all**, and the NBM snow-level driver ships as
  `direction: context_not_scored` (`research/p3-surfaces-design-2026-08-24.md` §275). What the answer
  binds is the *input list* for the proposed `method:ros-exposed-fraction@1.0.0` and
  `method:pack-buffer-capacity@1.0.0` (method-spec M2.4, M1.2) — i.e. whether wind and dewpoint at pack
  elevation must be ingested at all.
- **operationally blocking?** — **NO.** No 6–120 h prediction for any seeded basin contains a melt term.
  It is nevertheless the highest-leverage *doctrinal* error in the register, because doctrine states one
  side as FACT and doctrine is what the software is allowed to encode.
- **current disposition** — **OPEN — NOT BLOCKING.** The corpus's own reconciliation — *turbulence does
  not always dominate, but turbulence is what makes an ordinary ROS event an extreme one, so wind and
  dewpoint at pack elevation are the discriminating variables* — is explicitly labelled **INFERENCE and
  is not a resolution** (`snow-hydrology.md` §2.4). Prior adjudication (`method-spec-2026-08-24.md` §1.1):
  **encode neither partition**; encode the operational consequence both sides support, and until wind and
  dewpoint at pack elevation exist, the ROS surface is UNKNOWN with that reason.
- **evidence needed to resolve** — The partition itself is a field-energy-balance question the platform
  cannot settle. The *operational consequence* is testable and is what matters: build a ROS event
  catalogue from hourly SNOTEL SWE decrements at the three sites that bracket the generating band
  (Stampede Pass 3,850 ft, Stevens Pass 3,940 ft, Olallie Meadows 4,010 ft), WY2017–WY2026, Nov–Mar,
  restricted to hours with precipitation and SWE decreasing; then test whether the decrement rate is
  better explained by a turbulent proxy (HRRR 10 m wind × 2 m dewpoint depression, lapsed to pillow
  elevation) or a radiative proxy (HRRR downward longwave). Statistic: adjusted R² difference with a
  block bootstrap by event. A null result is publishable and would justify leaving the ROS term UNKNOWN.
- **doctrine status** — **`HYDROLOGY.md` §7 asserts one side of a live contradiction as FACT and needs
  correction, not hedging.** Two sentences:
  1. *"Rain-on-snow runoff enhancement comes mostly from turbulent sensible and latent heat fluxes …
     (FACT — e.g. Marks et al. 1998)"* → **CONTRADICTED as a general FACT** (`snow-hydrology.md` §7 row 1).
     Marks 1998 is a single-event, wind-exposed result. Downgrade to a regime-dependent statement, and
     keep the operational consequence (wind and dewpoint at pack elevation are the discriminating
     variables) labelled **INFERENCE**.
  2. *"the heat content of the rain itself is a minor term (FACT)"* → **QUALIFIED**. Minor in most events,
     but **29–44 %** of the energy budget in the persistent-melt events that produce floods
     (`snow-hydrology.md` §7 row 2). "Minor" is wrong for exactly the cases the platform exists to detect.

---

### X5 · Are western Washington flood storms short or long?

- **claim A** — **Short.** Most regional flooding events are associated with precipitation periods of
  **24 h or less**, and 2-day totals capture nearly all major events.
  *Source: Warner, Mass & Salathé 2012, via `corpus/atmospheric-rivers.md` §4 contested #1.*
- **claim B** — **Long.** The largest western-Cascades floods are produced by **sustained,
  moderate-intensity** rain — peak-day hourly intensity **2.7 ± 0.9 mm h⁻¹**.
  *Source: Jennings & Jones 2015, via `corpus/snow-hydrology.md` and `atmospheric-rivers.md` §4.*
- **affected method** — `method:basin-qpf@1.0.0` (shipped: basin-mean QPF for cumulative 0–24 / 0–48 /
  0–72 h windows at pointwise p10/25/50/75/90, `DATA_SOURCES.md` NBM entry). Both sides are consistent
  with the *currently shipped* window set. What the answer binds is the **second** forcing feature —
  a short-window peak metric versus `duration_above_rate` and *basin fraction simultaneously above rate*
  (`CROSS-DOMAIN-FINDINGS.md` C1) — i.e. `method:qpe-intensity@1.0.0` and `method:ar-duration@1.0.0`,
  both proposed (method-spec M4.3, M3.3), neither built.
- **operationally blocking?** — **NO.** The shipped forcing surface bands on cumulative window totals,
  which neither side refutes; the contradiction gates which *new* feature to build, not which existing
  number to print.
- **current disposition** — **OPEN — NOT BLOCKING.** Probably reconcilable by basin scale and response
  time (small coastal basins versus western Cascade basins), but **unresolved for the platform's own
  basins**, and the two support opposite designs. Note the tension with C1: "simultaneity of threshold
  crossing" is not the same claim as "long storm", and part of this contradiction is a question about
  which of the two C1 is describing.
- **evidence needed to resolve** — Per seeded basin, take the top 25 Nov–Mar peaks WY1997–WY2025 at that
  basin's susceptibility gauge and compute from AORC (or MRMS/Stage IV where the record allows)
  basin-mean hourly precipitation for the 5 days preceding each peak. Regress peak Q separately on
  (a) maximum 24 h total and (b) `duration_above_rate` = hours above 2 mm h⁻¹. Statistic: paired
  adjusted-R² difference per basin with a bootstrap interval. The winner is the second forcing feature;
  a split verdict across basins is itself the answer and must be encoded per basin.
- **doctrine status** — `HYDROLOGY.md` §2 names duration, orientation and temperature as what matters
  beyond IVT, and §4 lists both "precipitation intensity and duration" as features. It asserts neither
  side. **Safe to keep.**

---

### X6 · Do western Washington peak flows need mixed-population flood-frequency treatment?

- **claim A** — Yes. The western-US annual maximum series is a mixture whose tail is AR-dominated, and
  AR-only quantile estimates are *higher* than pooled ones. *Source: Barth et al. 2017 (1,375 gauges),
  via `corpus/flood-statistics.md` §4.*
- **claim B** — No. *"no streamgages had substantially diverging distributions that required a
  mixed-population analysis"* — while conceding on the same page that many gauges **do** have a mixed
  population, and rejecting only *separate treatment*. *Source: USGS SIR 2016-5118 p. 23, quoted in
  `flood-statistics.md` §4.* **Both are USGS-affiliated and they disagree about this state.**
- **affected method** — **Nothing in the platform depends on this.** The platform computes no frequency
  curve, no return period and no AEP. The dispute is about a fitting choice inside a method
  (Bulletin 17C) that already excludes regulated watersheds by scope — and the Skagit, Green, White and
  Cedar are regulated. The corpus further establishes that no objective separator exists: USGS peak
  code 9 appears **3 times in ~900** western Washington annual peaks.
- **operationally blocking?** — **NO.** Nothing computes a frequency estimate at any horizon.
- **current disposition** — **OPEN — NOT BLOCKING**, and moot for this platform. Prior adjudication
  (`method-spec-2026-08-24.md` §1.1): do not compute a frequency curve at all; publish
  `method:rank-in-record@1.0.0` instead (proposed, M0.5).
- **evidence needed to resolve** — Only needed if the platform ever ingests a frequency estimate. The test
  would be: join a published AR chronology (Rutz/SIO or an ARTMIP catalogue) to the annual-maximum series
  at each seeded gauge, WY1950–WY2025, fit LP3 by EMA to the AR-only and pooled series, and test whether
  the 1 % AEP quantiles differ by more than their confidence intervals. Note the 1 % AEP is known to a
  factor of ~1.6 in the first place (`flood-statistics.md`), so a null is likely and would be informative.
- **doctrine status** — `HYDROLOGY.md` §13 lists what the platform will not claim and does **not**
  mention recurrence intervals, return periods, AEP or the "100-year flood" — grepped and confirmed zero
  matches in `HYDROLOGY.md` and `DATA_DOCTRINE.md` (`flood-statistics.md` §6.1). The prior pass asserts
  the platform "already declines to compute return periods"; **it does not decline in writing.**
  **Needs an addition to §13**, not a correction.

---

### X7 · Does the forest-harvest peak-flow effect grow or vanish with return period?

- **claim A** — It vanishes. No detectable effect beyond ~**6-year** return periods, and the basin-scale
  effect is **smaller than interannual variability**. *Source: Grant et al. 2008 (state-of-science
  report), via `corpus/cascading-hazards.md` §2.10, §4 contested #1.*
- **claim B** — It grows. Chronological pairing **cannot detect a frequency change in principle**, and
  frequency-paired reanalysis finds effects that *grow* with return period — a 30-year event becoming a
  14-year event. *Source: Alila et al. 2009; Kaluarachchi & Alila 2026, Ambio 10.1007/s13280-026-02346-6.*
  Comments from Lewis, Reid & Grant, from Bathurst and from Birkinshaw dispute Alila's method in turn;
  Bathurst et al. 2020 attempt reconciliation and report the curves converging at the largest floods.
- **affected method** — **Nothing in the platform depends on this.** Land use appears in no shipped or
  proposed hazard computation. `forest_disturbance_pct`, `road_density_km_km2` and
  `effective_impervious_pct` are CONFIGURED basin attributes carrying both citations
  (`method-spec-2026-08-24.md` §1.1) — descriptive metadata, never a scored driver.
- **operationally blocking?** — **NO.**
- **current disposition** — **OPEN — NOT BLOCKING.** Live and unresolved in the literature. Both camps'
  *practical* recommendation for the platform coincides — keep land use out of the hazard computation —
  **for opposite reasons**, so the platform's position must be recorded as *unresolved method*, never as
  agreement between the camps. Roads are the one real mechanism (+21–50 % drainage density, >57 % of road
  length draining to streams) and it does not scale to the basin.
- **evidence needed to resolve** — None proposed, and none needed. The platform's action is invariant to
  the answer. Resolving it would require a frequency-paired reanalysis of a western Washington paired-basin
  record, which does not exist and is not the platform's work.
- **doctrine status** — `HYDROLOGY.md` is silent on land use. **Safe to keep**, provided the *reason* is
  recorded honestly wherever the exclusion is stated.

---

### X8 · Day-of-year ladder: longest record, or the most recent 30 years? — **THE BLOCKING ROW**

- **claim A** — **Longest record.** Prefer the longest homogeneous record; shortening the ladder never
  reduces total error. Original evidence: `corpus/climate-change.md` §2.3's variance–bias sweep.
- **claim B** — **The original evidence is circular.** Its own adversarial reviewer found the error
  metric was *distance from the full-record ladder*, "which makes `L = full record` optimal **by
  construction** — the monotone fall of both curves with `L` is arithmetic, not evidence"
  (`climate-change.md` §2.3, caveat added 2026-08-24).
- **claim C (the re-test, and the actual state of play)** — Re-tested out-of-sample with a
  **rolling-origin calibration criterion** (build the ladder from years before a held-out decade, score
  how close that decade's empirical exceedance frequency is to each ladder point's nominal frequency;
  10 gauges × 3 held-out decades), the full-record rule **survives on average**: mean calibration error
  **3.42** points, versus **3.98** for the most recent 30 years and **5.04** for the most recent 20.
  **But a recent-30 ladder beat the full record at 10 of 10 gauges on the 2016–2025 holdout and lost at
  essentially all of them on 2006–2015.** *The answer is PDO-phase dependent.*
  *Source: `climate-change.md` §2.3 adversarial-review caveat; restated in `CROSS-DOMAIN-FINDINGS.md` §2 X8.*
- **affected method** — `method:streamflow-doy-climatology@1.0.0` (**shipped**) → the `river state
  percentile` driver → `method:susceptibility-index@0.1.0` (**shipped, on screen for all six seeded
  basins**), with `BAND_EDGES = [25, 75, 90]`. The cross-check ladder
  `method:usgs-published-doy-stats@1.0.0` is a second vintage, never averaged (`DATA_SOURCES.md` H9).
  The proposed successor `method:streamflow-doy-climatology@2.0.0` (method-spec M0.1) depends on
  `method:rating-epoch@1.0.0` and a `homogeneity_epochs` seed block **that does not exist**.
- **operationally blocking?** — **YES.** This is the reference distribution every susceptibility number
  for every seeded Puget Sound basin is judged against, and the answer moves it: **12.8–17.4 %** of daily
  observations change susceptibility band from ladder length alone; the estimate carries **±5.5–6.2
  percentile points** of sampling error at 30 years against band edges **15 points apart**; and a
  regulation-regime split flips **29–32 %** of days and shifts the ranking **9.9–11.1 points** — larger
  than any climate effect measured anywhere in the corpus. *Honesty caveat, stated in the doctrine's own
  words:* the susceptibility surface "is not a flood forecast" (`HYDROLOGY.md` §3). It is nevertheless the
  live operational state statement the platform renders at 6–120 h for named basins, and its value depends
  on picking a side today.
- **current disposition** — **OPEN — BLOCKING.** The shipped `@1.0.0` ladder is built across homogeneity
  breaks nobody has looked for — including a **41.26 ft** datum step between WY1939 and WY1940 at
  Snoqualmie near Carnation 12149000, *a seeded gauge*. Prior adjudication
  (`method-spec-2026-08-24.md` §1.1) is: use the longest **homogeneous** record as the primary ladder —
  homogeneity, not recency, is the binding constraint — and publish the WMO-aligned recent-30 ladder as a
  `climatology_vintage_sensitivity` **disagreement driver, never as a correction**
  (`climate-change.md` §6.6). That adjudication is **proposed, not shipped**, and it does not by itself
  settle the PDO-phase result.
- **evidence needed to resolve** — Extend the rolling-origin test that already exists: 10 gauges ×
  every 10-year holdout from 1976–1985 through 2016–2025, across four ladder vintages — full record,
  full record truncated at the most recent homogeneity break, recent-30, recent-20 — with criterion
  = mean |empirical exceedance frequency − nominal| across ladder points. Then regress the
  (full-record − recent-30) calibration advantage on the **mean PDO index of the holdout decade**
  (NOAA/NCEI PDO). If the advantage flips sign with PDO phase, the answer is *publish both, never pick*,
  and the vintage-sensitivity driver becomes mandatory rather than optional. Inputs: USGS OGC `daily`
  (already ingested, 31,373 daily means per gauge in one request), the NCEI PDO index, and the
  per-gauge `homogeneity_epochs` block — **the one genuinely missing artifact**, a bounded piece of work
  (10 gauges, USGS station manuscripts and operator records).
- **doctrine status** — `HYDROLOGY.md` §8 says only that "Percentiles require climatology; the platform
  builds its own from stored history … with the period stated". It **asserts no side** — but it is also
  silent on the rule that matters. **Needs an addition**, in the form `climate-change.md` §6.4 states it:
  *use the full period of record, truncated at the most recent homogeneity break; a homogeneity break is a
  gauge datum epoch change, a documented rating-revision epoch, a station relocation, or a change of
  upstream operating rule — it is never the passage of time*, **plus** the standing disagreement driver.
  A ladder rebuild is a **revision**, and replay must reproduce the ladder of its knowledge time
  (`climate-change.md` §6.5) — that is a bug class, not a feature request.

---

### X9 · Is the Mount Vernon forecast point compound at all?

- **claim A** — The tide is negligible **at the gauge**. `compound-coastal.md` §3.4 measures tidal
  transmission **0.010 ft/ft**; `routing-hydraulics.md` §5.5 independently fits **M2 ≈ 0.004–0.009 ft**
  against a Skagit Bay range of 8–11 ft (~0.1 %), with the USACE hydraulic model putting the tidal limit
  ~**7 river miles below** the gauge. Two domains, two methods, no cross-citation.
- **claim B** — The Skagit Climate Science Consortium states publicly that the river is "heavily
  influenced by the tide" from "below Mt. Vernon to Puget Sound". *Source: SCSC, via
  `compound-coastal.md` §4 contested.*
- **claim C (the surviving corner)** — `compound-coastal.md`'s own re-run found its **backwater null is
  underpowered, not absent**: on the Q ≥ 40,000 cfs subset (n = 171) the sea-level coefficient is
  **+0.17 ± 0.10 ft/ft (t = +1.7, p ≈ 0.09)** — correctly signed, merely non-significant — and,
  decisively, *a Skagit crest has essentially never coincided with a high tide plus a large surge in
  the record*, so the regression contains almost no observations of the regime that matters
  (`compound-coastal.md` §3.4 re-run, §7 item 6).
- **affected method** — `trend.py` rate-of-rise (endpoint difference over a trailing window,
  `STAGE_STEADY_EPS_FT_PER_H = 0.05`, live window `window_h = 6` per `assemble.py:220`),
  `headroom.py` time-to-threshold, and the proposed `method:tidal-transmission@1.0.0` (M1.5) and
  `method:skew-surge@1.0.0` (M5.2). All quantities cited from
  `research/tidal-gauge-verification-2026-08-26.md` §3, which read the code without modifying it.
- **operationally blocking?** — **NO.** The oscillatory tide is measured out at every seeded point, and the
  backwater corner has never occurred in 29 water years of record.
- **current disposition** — **RESOLVED BY MEASUREMENT** for the oscillatory tide; **OPEN — NOT BLOCKING**
  for the backwater term.
  **The measurement** (`tidal-gauge-verification-2026-08-26.md`, primary USGS OGC + NOAA CO-OPS payloads,
  three windows, semidiurnal 10–16 h band-pass, non-tidal control gauge MROW1 12150800 carried through
  every calculation): it does not merely confirm Mount Vernon — it **extends the finding to all six
  seeded gauges**. Whole-window harmonic **M2 amplitude ≤ 0.008 ft** at every seeded point
  (MVEW1 0.0077, CRNW1 0.0057, WRAW1 0.0036, RNTW1 0.0012, NKSW1 0.0006, AUBW1 0.0005) against a coastal
  M2 of **2.26–3.36 ft**. And, computed against the platform's own code path, the **tidally-injected
  false rate-of-rise at the live 6 h window is ≤ 0.025 ft/h at low flow** — half the 0.05 ft/h STEADY
  epsilon, with **0.0 %** of samples exceeding it at five of six gauges (CRNW1 2.5 %). During Event Zero
  the seeded gauges reach 0.03–0.14 ft/h, **but so does the non-tidal Monroe control (0.073 ft/h)**, so
  that is hydrograph leakage, not tide. **No de-tiding is needed for anything the platform serves.**
  The SCSC statement is compatible with all of this — *below* the gauge, not at it — and the prior repo
  pass over-generalised it.
- **evidence needed to resolve** — For the backwater corner: daily means smear a 12.4 h signal, so the
  regression must be redone at **hourly** resolution, against **Cherry Point** rather than Seattle, on the
  subset Q ≥ 100,000 cfs **and** coastal water level ≥ MHHW, 1996–2025. The verification's own finding is
  that this subset is close to empty, so the honest route is hydraulic, not statistical: run the USACE
  Skagit model (or an SSCOFS-forced HEC-RAS) with the December 2025 hydrograph on WY2026's maximum
  predicted tide plus a p99 winter skew surge, and read Δstage at RM ~16. Statistic: feet of stage at the
  gauge. `compound-coastal.md` §3.5 puts the unrealised boundary ~8.0 ft above what actually occurred.
- **doctrine status** — `HYDROLOGY.md` does not claim Mount Vernon is compound. **Safe to keep**, and now
  positively supportable: the statement *"no seeded forecast point is tidally affected at the gauge"* is
  cleared for doctrine (see §3). What must **not** be inherited is the "no backwater" conclusion — record
  it as underpowered, and record that *the tail's absence from the record is not evidence of its absence
  from the future*.

---

### X10 · Is the AR signal at Washington's latitude rising?

- **claim A** — There is an **"AR increasing hole"** over the Pacific Northwest — *"a region of little to
  no increase, or slight decrease"* — with PNW total winter precipitation showing *"a significant decrease
  of 22.3 mm per decade"*. *Source: Pan et al. 2025, npj Clim Atmos Sci 8, 307 (fetched), via
  `corpus/climate-change.md` §4.*
- **claim B** — A widespread 20th-century increase. *Source: Scholz et al. 2025, AGU Advances (403 at
  fetch, not independently read), via `climate-change.md` §4 and `corpus/atmospheric-rivers.md` §4
  contested #3.*
- **claim C (the measurement that outranks both)** — ARTMIP Tier 2 finds **detector choice dominates
  model choice** as the uncertainty source, so an AR-frequency percentage is partly an artefact of the
  detection algorithm. Measured over 40 years of reanalysis, AR-mean **IVT has risen by less than 1 %**
  (+3–4 % for the most intense subset; 850-hPa wind and VIMFC *decreased*) — Henny & Kim 2025, fetched.
- **affected method** — **Nothing in the platform depends on this.** No shipped or proposed method
  contains an AR-trend term. `method:basin-ivt@1.0.0` and `method:ar-scale@0.1.0` (proposed, Tier 3) are
  *state* estimators for the current storm, not trend estimators.
- **operationally blocking?** — **NO.** A 6–120 h forecast consults the current IVT field, never its
  40-year trend.
- **current disposition** — **RESOLVED BY ADJUDICATION — the platform's action is invariant to the
  answer.** Both corpus files reached the same operational verdict independently: *the platform must not
  assert a local AR trend in either direction.* Recording that agreement-on-the-verdict-despite-
  disagreement-on-the-science is itself the resolution. The **science remains open** and this row stays
  in the register for that reason.
- **evidence needed to resolve** — Only if the platform ever needs the trend: recompute landfalling-AR
  frequency at 47–49 °N with **≥ 3 ARTMIP Tier-2 detectors** over ERA5 1980–2025 and publish the
  inter-detector spread **beside** the trend. Since ARTMIP already establishes the detector dominates,
  a single-detector trend is uninterpretable and must be refused, not caveated.
- **doctrine status** — `HYDROLOGY.md` §2 describes AR seasonality and mechanism without asserting a
  trend. **Safe to keep.** The same refusal covers the parallel snowpack-trend dispute
  (`climate-change.md` §4): the platform must not assert a local snowpack trend from its own SNOTEL feed
  — 28 western/crest WA sites, 1979–2026, **field p = 0.156**, no field-significant April 1 SWE trend.

---

### X11 · Kirchner's stated scale limit versus the corpus's use of his method

- **claim A** — The storage–discharge sensitivity method *"must break down for catchments that are too
  large"*, speculatively around **~1,000 km²**, because channel-network routing lag would swamp the
  storage signal. *Source: Kirchner 2009 §15.6, quoted verbatim in `corpus/runoff-generation.md` §2.7.*
- **claim B** — The corpus fits it anyway. **Six of the seven gauges** `runoff-generation.md` §5.4 fits are
  at or beyond that scale, all **70–800×** Kirchner's study catchments, and reads the flattened `g(Q)`
  at Mount Vernon (`b − 1 ≈ 0.057`) as the signature of **regulation**. Channel routing lag is an
  unexcluded alternative explanation — and `routing-hydraulics.md` §5.1, which measures a **16.9 h**
  median routing lag on exactly that reach, is the domain that would adjudicate it. **Neither file cites
  the other.** `CROSS-DOMAIN-FINDINGS.md` §2 calls this "the clearest hand-off failure in the corpus".
- **affected method** — **Nothing shipped depends on this.** `method:catchment-sensitivity@1.0.0`
  (proposed, method-spec M1.1) is the one that would, and its stated purpose is to supply *physically
  motivated band edges* replacing the WaterWatch 25/75/90 convention in
  `method:susceptibility-index@0.1.0`. If the flattening at large scale is routing rather than
  regulation, the method cannot supply band edges at the scale the platform operates at — which would
  leave X8's uncalibrated edges standing.
- **operationally blocking?** — **NO** today. It becomes blocking the moment M1.1 is proposed for
  promotion, because M1.1 is the proposed fix for the band edges X8 makes urgent.
- **current disposition** — **OPEN — NOT BLOCKING.** Note the fit itself carries two independent
  reproducibility failures recorded in place (`runoff-generation.md` §5.4 adversarial caveat): an
  independent reimplementation returns **b = 1.69–1.92**, not the reported 1.85–2.05, so the §6.2 exit
  test is not reproducible as stated; and `b` falls monotonically with recession-filter length
  (Sauk: 2.04 at 2 h → 1.71 at 24 h), so the reported 6 h/12 h pair samples the highest-`b` end of an
  arbitrary continuum. Any rank resting on this computation is provisional.
- **evidence needed to resolve** — Refit `g(Q)` at the four unregulated gauges plus Mount Vernon after
  deconvolving the measured Concrete → Mount Vernon crest-lag distribution (median 16.9 h, sd 3.5 h,
  `routing-hydraulics.md` §5.1) from the Mount Vernon series, and add at least one genuinely sub-1,000 km²
  nested control from the same region — Sauk above White Chuck 12186000 is the obvious candidate and is
  already in the Event Zero record, though its drainage area is **not recorded anywhere in this
  repository** and must be read from the USGS site service before it is assumed to be under 1,000 km².
  Statistic: does `b − 1` at Mount Vernon rise toward the unregulated 0.85–1.05 once routing
  lag is removed, and does `b − 1` correlate more strongly with drainage area than with `regulation_class`
  across the seven gauges? Report the **unbinned** r² (0.74–0.80 for the unregulated gauges), never the
  binned one, per the same file's caveat. Inputs: USGS IV 00060, already in the ingest.
- **doctrine status** — `HYDROLOGY.md` is silent on storage–discharge sensitivity. **Safe to keep.** The
  related §2 claim that basins "respond within hours to a day" is separately contradicted by the same
  file — the recession time constant is 17.5–28.1 h unregulated but **42 h at Mount Vernon, 116 h on the
  Cedar and 264 h on the Green** — so response time is dominated by regulation, not basin size.

---

### X12 · Doctrine names Ferndale as the tidal problem; measurement says Ferndale is not tidal at the gauge

*Opened 2026-08-26 by `research/tidal-gauge-verification-2026-08-26.md`.*

- **claim A** — *"Nooksack: unregulated; the lower river is tidally influenced at Ferndale."*
  *Source: `docs/HYDROLOGY.md` §2, Nooksack bullet (line 75).* Reinforced downstream by
  `compound-coastal.md` §3.4's 0.019 ft/ft (r = 0.33) "marginal" classification and by
  `method-spec-2026-08-24.md` §1.1's recommendation to badge NKSW1 `MARGINAL`.
- **claim B** — At the **NKSW1 gauge** the tide is not measurable. Whole-window harmonic
  **M2 = 0.0006 ft**, i.e. **0.03 %** of Cherry Point's 2.264 ft M2; band-limited slope **−0.0015 to
  +0.0048 ft/ft**, r ≤ 0.29; **statistically indistinguishable from the non-tidal control gauge**
  (Snohomish near Monroe 12150800, 12 river miles above the head of tide, M2 = 0.0002 ft). Reproducible
  across two independent low-flow years. Meanwhile the gauge that *is* tidal — SNAW1, M2 = **2.9726 ft**,
  **88.4 %** of Seattle's, gauge datum **−6.43 ft NAVD88** — **is not seeded**.
  *Source: `research/tidal-gauge-verification-2026-08-26.md` §§1, 4.2–4.3, 5.2.*
  The review's own 0.019 ft/ft (r = 0.33) is **not reproduced by any estimator** and is an OPEN QUESTION
  (§7 item 2) — both numbers mean "not tidal", so the conclusion is unaffected, but the value must not
  enter doctrine.
- **affected method** — `trend.py` rate-of-rise and `headroom.py` time-to-threshold at NKSW1 (the defect
  the doctrine sentence would motivate guarding against), and the proposed
  `method:tidal-transmission@1.0.0` (M1.5), which would otherwise seed NKSW1 with a refuted coefficient.
- **operationally blocking?** — **NO.** Measured against the platform's own code path, the tidally-injected
  false rate at NKSW1's live 6 h window is **0.010 ft/h at low flow** — one-fifth of the
  `STAGE_STEADY_EPS_FT_PER_H = 0.05` threshold — with **0.0 %** of samples exceeding it. Nooksack
  rate-of-rise, headroom and time-to-threshold are sound as implemented.
- **current disposition** — **RESOLVED BY MEASUREMENT.** The gauge claim is refuted; the *reach* claim is
  untested and separable.
- **evidence needed to resolve** — For the reach below the gauge (the claim that may well be true):
  either a water-level record between the NKSW1 gauge and Bellingham Bay — none exists in the seed — or
  a VDatum-tied comparison of the Ferndale water surface (NAVD88; gauge datum +8.50 ft NAVD88) against
  Cherry Point MHHW. That second route is currently **blocked by a missing datum tie**: Cherry Point and
  Port Townsend publish **no NAVD88** value, so a Ferndale elevation and a Cherry Point tide cannot be
  placed on a common datum by arithmetic (§2.3, §7 item 4). Obtainable from VDatum, not from CO-OPS.
  Also open: a **quiescent high-flow window** at NKSW1 (steady high baseflow, no rising limb) to test
  regime dependence — its low-flow M2 (0.0006 ft) and flood M2 (0.0628 ft) differ by 100×, but the flood
  figure sits at the hydrograph noise floor, so no trend can be asserted (§7 item 5).
- **doctrine status** — **`HYDROLOGY.md` §2 line 75 needs correction.** As written it is not supported at
  the gauge. If a statement about the reach *below* the gauge is wanted, it must say so explicitly and be
  evidenced separately. Two additions belong with it: (a) SNAW1 is genuinely tidal and its Event Zero
  record stage is a **compound quantity** — `HYDROLOGY.md` §12 cites SNAW1 as a record gauge without
  saying so; (b) the tidal-class machinery should exist **before** SNAW1 is seeded, not after — a
  `tidal_class` field reading `FLUVIAL` for all six current points costs nothing today.

---

### X13 · SNOTEL basin misattribution — four sites mapped into seeded basins are majority-Columbia

*Opened 2026-08-26 by `research/snow-elevation-verification-2026-08-26.md`.*

- **claim A** — A SNOTEL site belongs to the basin containing the first eight digits of its **own primary
  `huc`**. On that rule 29 of 78 active WA sites map into a seeded basin. `DATA_SOURCES.md` §391 flags
  **Harts Pass alone** as an east-crest proxy and states that "Marten Ridge, Thunder Basin, Beaver Pass,
  Brown Top, Rainy Pass, Swamp Creek and Decline Creek carry the maritime Skagit/Sauk signal (INFERENCE)".
- **claim B** — For **four** sites the *majority* of `associatedHucs` lie in **HUC 1702\*** — the Columbia
  basin, east of the crest — and a fifth is borderline:
  Harts Pass 6,490 ft **6/6** (Methow, Pasayten) → skagit; Rainy Pass 4,880 ft **5/5** (Methow,
  Stehekin/Chelan) → skagit; Swamp Creek 3,930 ft **4/6** → skagit; Stevens Pass 3,940 ft **4/6** →
  snohomish-snoqualmie; Thunder Basin 4,310 ft **4/6** (borderline) → skagit.
  They are disproportionately the high-percentage sites: on 2025-12-11 three of the four sites reading
  ≥ 128 % of median were Harts Pass (173.6 %), Rainy Pass (128.0 %) and Swamp Creek (130.6 %).
  Dropping them moves the pooled six-basin composite from **45.6 % to 28.9 %** (ratio-of-sums, before any
  elevation banding), and the Skagit alone from **97.3 % to 63.8 %**. Decomposed, the fall from 45.6 % to
  9.9 % is **−16.7 points of basin attribution followed by −19.0 points of elevation** — the two effects
  are of comparable size. *Source: `snow-elevation-verification-2026-08-26.md` §5, from the AWDB stations
  payload the platform already fetches.*
- **affected method** — `swe_percent_of_median` in the AWDB normaliser →
  the `basin_swe_percent_of_median` driver in `method:susceptibility-index@0.1.0`, and
  `method:basin-mean-swe@1.0.0` (`VISUAL_TRUTH_DOCTRINE.md` §371). Also the proposed
  `method:snow-drought-state@1.0.0` and `method:snotel-elevation-coverage@1.0.0` (M1.2).
- **operationally blocking?** — **NO.** The SWE driver ships as `direction: context_not_scored`
  (`p3-surfaces-design-2026-08-24.md` §524), so a wrong composite moves **no band and no 6–120 h
  statement**. It moves a number rendered beside one — which on 2025-12-11 read **93.0 %** for the Skagit
  under the platform's own estimator, the day before a record crest.
- **current disposition** — **RESOLVED BY MEASUREMENT** as to the fact (it is at least four sites, not
  one, and the metadata proving it is already in the fetched payload); **OPEN — NOT BLOCKING** as to the
  fix, which is a policy decision, not a further measurement.
- **evidence needed to resolve** — Recompute per-basin `swe_percent_of_median` for Dec 1 – Mar 31 of
  WY2017–WY2026 under three mappings: **(a)** primary HUC8 (current); **(b)** (a) minus sites whose
  `associatedHucs` are majority 1702\*; **(c)** (b) plus any of the 49 currently-unmapped WA sites whose
  `associatedHucs` are majority a seeded HUC8 — the mirror-image problem the verification flags and did
  not investigate (§9 item 9). Statistic: per-basin per-day spread across the three mappings, and the
  fraction of days on which they disagree by more than 10 percentage points. **No new provider is
  needed** — every input is in the AWDB payload already fetched. This is a smaller change than elevation
  banding and removes a larger share of the error.
- **doctrine status** — `HYDROLOGY.md` §7 asserts that "Point observations (SNOTEL) are ground truth for
  their elevation and aspect" — correct, and the consequence is more severe than stated
  (`snow-hydrology.md` §7 row 9). **`DATA_SOURCES.md` §391 needs correction**: its INFERENCE that Rainy
  Pass, Swamp Creek and Thunder Basin "carry the maritime Skagit/Sauk signal" is contradicted by the
  station metadata. One further finding to record: the Skagit's only low-elevation pillow, **Hozomeen Camp
  (1,680 ft), sits on Ross Lake — upstream of Ross Dam**, so its SWE is not hydrologically available to
  the Mount Vernon forecast point without passing a regulated release decision (INFERENCE, §5).

---

### X14 · Is elevation-stratified snow computable at all for Cedar and Snohomish-Snoqualmie?

*Opened 2026-08-26 by `research/snow-elevation-verification-2026-08-26.md`.*

- **claim A** — Adopt elevation-stratified SWE (a sub-4,500 ft band), because a pooled composite is
  "misleading in the direction of calm": on 2025-12-11 the western-WA composite read 44 % while the
  sub-4,500 ft band read 14 %. *Source: `research/doctrine-delta-2026-08-24.md` §7.5 / §12.3;
  `corpus/snow-hydrology.md` §7 row 6; `CROSS-DOMAIN-FINDINGS.md` §4 factor 9.* The arithmetic is
  **confirmed exactly** — 20 sites below 4,500 ft, **13.8 %** of median, **10 of 20 at exactly 0.00 in**.
- **claim B** — Only **two of six** basins have the vertical sampling to stratify at all:
  **skagit** (n = 9, 1,680–6,490 ft, spread 4,810 ft) and **puyallup-white** (n = 5, 2,250–5,810 ft,
  spread 3,560 ft) can; **nooksack** (2 below / 1 above) and **green-duwamish** (3 below / 1 above) can
  only with a single-pillow upper band; and **cedar** (n = 4, 2,930–3,810 ft, spread **880 ft**, entirely
  below 4,000 ft) and **snohomish-snoqualmie** (n = 4, 3,320–4,010 ft, spread **690 ft**) **cannot, at any
  band elevation** — at 4,500 ft their upper band is *empty*, so stratification returns the unstratified
  number under a different name. *Source: `snow-elevation-verification-2026-08-26.md` §§2–4, ASSUMPTION
  stated in place: a band needs ≥ 2 reporting sites to be a statistic rather than a point observation.*
  Confirmed against the platform's own estimator on 2025-12-11: `ALL − (<4,500 ft)` = **+0.0 points** for
  cedar, snohomish-snoqualmie and green-duwamish, against **+39.1** for skagit and **+16.2** for
  puyallup-white. And the ordering is **not monotonic in elevation** — Swamp Creek at 3,930 ft read
  130.6 % while Olallie Meadows at 4,010 ft and Burnt Mountain at 4,160 ft read 0.0 % — direct evidence
  that **elevation alone is the wrong single axis** (windward/leeward is the second, see X13).
- **affected method** — `method:basin-mean-swe@1.0.0` and `swe_percent_of_median` (shipped);
  the proposed `method:swe-below-snow-line@1.0.0`, `method:snow-drought-state@1.0.0`,
  `method:snotel-elevation-coverage@1.0.0` (M1.2) and `method:ros-exposed-fraction@1.0.0` (M2.4).
- **operationally blocking?** — **NO** for flood prediction: SWE is unscored context and no ROS term
  exists. **YES for the snow method family** — it determines whether M1.2's output is a number or
  UNKNOWN for a third of the seeded basins.
- **current disposition** — **RESOLVED BY MEASUREMENT.** The answer is **no** for cedar and
  snohomish-snoqualmie at any band elevation, **yes** for skagit and puyallup-white, **marginal (n = 1
  upper band)** for nooksack and green-duwamish. Do **not** adopt 4,500 ft or any single universal band:
  it would emit a confident number for two basins, a one-site number dressed as a statistic for two, and
  a **tautology** for two — and that last failure mode is the dangerous one, because it returns a number
  rather than UNKNOWN. The defensible interim statement is per basin and explicitly bounded:
  *"SWE at the N sites between X and Y ft is Z % of median (method, day, n, exclusions); no observation
  exists above Y ft."*
- **evidence needed to resolve** — Two obtainable steps, in dependency order.
  **(1)** Whether a gridded product rescues the two blocked basins: fetch SNODAS/NOHRSC daily SWE for
  WY2017–WY2026, mask to `basin:cedar` and `basin:snohomish-snoqualmie`, and validate modelled SWE
  against the in-band pillows (2,930–3,810 ft; 3,320–4,010 ft) at the pillow cells. Statistic: bias and
  RMSE against pillow SWE, Dec–Mar, and the fraction of days the model would change the reported band.
  Untested to date — `snow-elevation-verification` §9 item 7 records that no gridded product was fetched
  and that this is the obvious route.
  **(2)** `method:basin-hypsometry@1.0.0` from 3DEP (method-spec M2.1), to convert a band statistic into
  a basin statistic at all. Without it, no band number is a basin number for *any* basin — including the
  two that can stratify. Basin geometry is currently HUC8 unions (`NEXT_STEPS.md` gap 6).
  A third, cheap: enforce a **minimum-sites rule** that returns UNKNOWN rather than a one-pillow band, and
  render **n and the exclusions** with every composite — the reporting count moves 5 → 3 in the
  Puyallup-White between December and April, with **both low-elevation sites** dropping out in spring,
  precisely when the low band is what matters.
- **doctrine status** — `HYDROLOGY.md` §3's susceptibility input table lists "snow storage & state — **SWE
  by elevation band**, snow-covered fraction, ripeness" as an input, and §7 makes hypsometry the pivot for
  rain-exposed and ROS-exposed fraction. **Needs hedging**: the elevation-band form is not computable for
  two of six seeded basins with the network as it stands, and UNKNOWN is the correct output there.
  §2's "transient snow zone … roughly 1,000 and 4,000 ft (ASSUMPTION)" should also go — the concept is
  criticised in the literature (Jennings & Jones: the transient zone "implies a static area, when in fact
  the area undergoing melt is highly dynamic during storm events") and unobserved in the network.

---

### X15 · SNAW1 transmits "0.831 ft/ft, r = 0.94" — a single scalar that no estimator reproduces

*Opened 2026-08-26 by `research/tidal-gauge-verification-2026-08-26.md`.*

- **claim A** — Snohomish at Snohomish (SNAW1) transmits **0.831 ft/ft** at **r = 0.94**; badge it `TIDAL`
  with that coefficient. *Source: `corpus/compound-coastal.md` §3.4 and §7 item 1;
  `research/doctrine-delta-2026-08-24.md` §2.9 / §12.5; carried into `method-spec-2026-08-24.md` §1.1 and
  M1.5 as the seed value.*
- **claim B** — The **class is right and the number is not reproducible as a single value.** Measured over
  two independent low-flow years with a 10–16 h semidiurnal band-pass: phase-blind OLS **0.739 / 0.757**
  (r **+0.823 / +0.828**); lag-corrected **0.892 / 0.919** (r **+0.993**); rms amplitude ratio
  **0.901 / 0.918**; phase lag **+1.25 h**, identical in both years. **No estimator yields r = 0.94.**
  And the coefficient is **regime-dependent**: during Event Zero it collapses to **0.223** (0.318
  lag-corrected), M2 from 2.97 ft to 1.08 ft — a ~3× fall, which is what open-channel hydraulics predicts
  when a high discharge steepens the water surface and damps upstream tidal propagation.
  *Source: `tidal-gauge-verification-2026-08-26.md` §§4.2–4.5, §0.*
- **affected method** — `method:tidal-transmission@1.0.0` (proposed, M1.5) and its dependent
  `method:skew-surge@1.0.0` (M5.2). **No shipped surface**, because SNAW1 is not seeded.
- **operationally blocking?** — **NO.** SNAW1 is not a seeded forecast point; doctrine that changes only
  for SNAW1 changes nothing the platform serves today.
- **current disposition** — **RESOLVED BY MEASUREMENT — refuted as a scalar, confirmed as a class.** The
  honest doctrinal statement is *"SNAW1 transmits roughly **0.75–0.92 ft** of stage per ft of Seattle tide
  at low flow, falling to roughly **0.22–0.32** during a large flood, with a **+1.25 h** lag."* The
  three-significant-figure form is a trap: the review's §12.5 phrasing invites the reader to compute
  0.831 × 6.64 ft = 5.5 ft for Event Zero, which is **2.6–3.6× too large** for a flood-regime crest. The
  correct figure is ~2 ft on a 34.45 ft crest (~6 %), and it does not cross a category boundary — SNAW1
  was already major (major = 29 ft). The related operational fact is confirmed and is large: at SNAW1 the
  platform's live 6 h rate-of-rise would report a spurious rise or fall exceeding its own STEADY threshold
  in **96.7 % of low-flow samples and 60 % of Event Zero samples**, at up to **1.44 ft/h** — a naive
  time-to-threshold would announce ~5 hours to flood stage on a falling river, twice a day, forever.
- **evidence needed to resolve** — Two specific gaps. **(1)** A **quiescent high-flow window** at SNAW1 —
  steady high baseflow, no rising limb, ≥ 20 days — band-passed 10–16 h against Seattle 9447130, to turn
  two regime points into a transmission *curve*; the 3× collapse is currently a single observation
  (§7 item 7). **(2)** The estimator behind r = 0.94, which the review does not state and which cannot be
  reconstructed (§7 item 1) — until it is, that number is an OPEN QUESTION, not a disagreement.
  Method note to inherit for any future tidal measurement in this repository: band-pass to 10–16 h and
  **ignore the diurnal band entirely** (a whole-window fit during Event Zero assigns the non-tidal Monroe
  control K1 = 0.786 ft and P1 = 0.835 ft — pure hydrograph leakage); carry a known non-tidal control
  gauge through the identical pipeline; and report the phase lag alongside the slope.
- **doctrine status** — `HYDROLOGY.md` is silent on SNAW1 transmission. **Safe to keep.** The number must
  not enter doctrine as a scalar; the class, the two regime coefficients, the lag, the estimator, the
  window and the control gauge must all travel together if it enters at all.

---

### X16 · Which percent-of-median SWE estimator: ratio-of-sums, or mean-of-ratios?

*Opened 2026-08-26 by `research/snow-elevation-verification-2026-08-26.md`.*

- **claim A** — The criticised statistic is a **pooled ratio-of-sums** across western Washington: "the
  composite read 44 %". *Source: `doctrine-delta-2026-08-24.md` §7.5; echoed in `snow-hydrology.md` §7
  row 6 and `CROSS-DOMAIN-FINDINGS.md` §4 factor 9.*
- **claim B** — **The platform does not compute that statistic.** `swe_percent_of_median` ends
  `mean = sum(c.percent_of_median for c in contributions) / len(contributions)` — a **mean of per-site
  ratios, per basin**, with exclusions for absent value, absent median, median ≤ 0 and suspect QC flag.
  On 2025-12-11 it returns **0.4 %** for the Cedar and **93.0 %** for the Skagit. The 44 % figure is not a
  number the platform emits. And the two estimators are **not interchangeable**: on 2025-12-08 in the
  Puyallup-White they differ by more than a factor of two — **48.7 %** (ratio-of-sums) against **23.3 %**
  (mean-of-ratios). *Source: `snow-elevation-verification-2026-08-26.md` §6, reproducing the shipped code
  path.*
- **affected method** — `swe_percent_of_median` → `basin_swe_percent_of_median` driver in
  `method:susceptibility-index@0.1.0`; `method:basin-mean-swe@1.0.0`.
- **operationally blocking?** — **NO.** Unscored context driver; no band moves.
- **current disposition** — **OPEN — NOT BLOCKING**, and it is a **declaration, not an experiment**. The
  two estimators answer different questions: ratio-of-sums asks *"what fraction of normal basin storage is
  present"*; mean-of-ratios asks *"how anomalous is the typical site"*. Both are legitimate; quoting one
  while criticising the other is the error. This is an *independent* source of the same
  "misleading in the direction of calm" defect the review names, and the review does not mention it.
- **evidence needed to resolve** — **No experiment will settle this.** The resolution is: pick one, say so
  **in the method id**, and render `n` and the exclusions beside every value (the `ContextResult.excluded`
  counters already carry them). One measurement is worth having alongside: the per-basin per-day gap
  between the two estimators over Dec–Mar WY2017–WY2026, so the magnitude of the choice is documented
  rather than assumed — the Puyallup-White case shows it can exceed 2×.
- **doctrine status** — `HYDROLOGY.md` is silent on the estimator. **Safe to keep**, but the register
  records a standing rule: **a composite without its estimator, its `n` and its band is not comparable to
  yesterday's composite** and must not be rendered as if it were.

---

### X17 · Does a low-elevation SWE deficit *raise* rain-on-snow risk?

*Opened 2026-08-26 by `research/snow-elevation-verification-2026-08-26.md`.*

- **claim A** — The naive percent-of-median statistic **understates rain-on-snow vulnerability** — a
  paraphrase that has circulated around `doctrine-delta-2026-08-24.md` §7.5 and the corpus's factor-9
  entry, which lists the 44 %/14 % gap under "snowpack state" as "misleading in the direction of calm".
- **claim B** — **The physics runs the other way.** Rain-on-snow requires snow to *exist* at the
  elevations rain will fall on. A sub-4,500 ft band at 13.8 % of median with **10 of 20 pillows bare**
  means there was very little low-elevation snow to melt, which **lowers** ROS potential. The composite's
  44 % was not hiding a rain-on-snow threat; it was hiding the fact that Event Zero was **rain on
  saturated soils, not rain on snow**. Pooled, the sub-4,500 ft composite fell from 25.9 % on 2025-12-04
  to **8.5 %** on 2025-12-15, and the sub-3,500 ft composite from 21.7 % to **0.3 %**, through the AR
  sequence. *Source: `snow-elevation-verification-2026-08-26.md` §8, §6.2.*
- **affected method** — The *wording* of any future ROS doctrine sentence, and the sign convention of
  `method:ros-exposed-fraction@1.0.0` (proposed, M2.4). **No shipped method depends on it**, because no
  ROS term ships.
- **operationally blocking?** — **NO.**
- **current disposition** — **RESOLVED BY ADJUDICATION**, on mass balance: ROS melt cannot exceed the
  snow available at the rain elevation, so a low-band SWE deficit cannot raise ROS runoff. The defect is
  **wrong-mechanism attribution**, not understated magnitude: a displayed "44 % of median snowpack"
  invites a reader to reason about a snow buffer and a melt contribution when the correct operational
  reading was *"there is effectively no snow below 4,500 ft; treat this as a rain-on-wet-soil event"*.
  Both errors are serious and the fix (band the statistic, or refuse it) is the same — but the doctrine
  text must say **which** error it is, because the reverse claim is physically backwards and would not
  survive review. The corpus's own narrower wording — *"misleading in the direction of calm"* — survives
  intact and is the phrasing to keep.
- **evidence needed to resolve** — Nothing further for the sign. If a magnitude is ever wanted, it is the
  same catalogue X4 needs: `ros-exposed-fraction` = SCA ∩ (area below forecast snow level), which requires
  `method:basin-hypsometry@1.0.0` and MODIS/VIIRS or SNODAS snow-covered area. On 2025-12-11 that fraction
  would have been near zero in the seeded basins regardless of how X4 resolves.
- **doctrine status** — `HYDROLOGY.md` §7 already says the sign of the SWE effect "depends on temperature,
  pack state, and elevation distribution (FACT)" and §12 already records Event Zero as "rain on saturated
  soils, not snowmelt (FACT)". **Both are safe to keep, and §12's claim is strengthened**: below 4,500 ft
  in the maritime Cascades on 2025-12-11, SWE was **13.8 % of median with 10 of 20 sites at exactly zero**,
  which upgrades "near record-low statewide" to a basin-band measurement. The correction owed here is to
  the doctrine-delta text and to any paraphrase of it, not to `HYDROLOGY.md`.

---

## 3. Promotion gate

*What a disputed number is allowed to become. "Cleared" means it may enter `HYDROLOGY.md` (or
`DATA_SOURCES.md`) with the stated label and the stated qualifiers attached. "Blocked" means it may be
cited inside `docs/research/` and nowhere else until the named evidence arrives.*

### BLOCKED from normative doctrine

| Disputed number | Row | Unblocks when |
|---|---|---|
| **Any single rain-on-snow melt-energy partition** (60–90 % turbulent; 33–55 % or 68 % net radiation; <10 % / 10–15 % / 29–44 % advected rain) | X4 | Never as a partition. The **operational consequence** (wind + dewpoint at pack elevation discriminate ordinary from extreme ROS) unblocks as INFERENCE when the X4 event-catalogue test returns; until then the ROS surface is UNKNOWN with that reason |
| **Any single Mount Vernon drift figure** without estimator, window and reference stage — and **−29 % is SUPERSEDED outright** | X1 | The X1 refit lands: one estimator, ≥ 80 kcfs pairs, quality ≠ Poor, 1990 excluded, 33.00 ft reference, two-s.e. interval, curve-shape sensitivity reported |
| **+0.139 ft/decade at Ferndale** (not reproduced; the stated Theil–Sen estimator gives **+0.065, p = 0.028**) | X1 | Use +0.065 as the anchor now; the higher figure never unblocks without a corrected derivation |
| **The crest-lag magnitude trend (r = +0.65)** — the *distribution* (median 16.9 h, sd 3.5 h) is cleared, the *trend* is not | X2 | A crest-centroid timing method reproduces the sign on n = 20 |
| **"Attenuation is a big-flood phenomenon" (−11.0 %)** | X3 | Never as stated. −5.2 % on n = 20 with the bimodal caveat is the most that is publishable, and only with the local-inflow discriminator named |
| **A settled ladder vintage** — neither "longest record" nor "recent 30" may be asserted as *the* rule | **X8** | The PDO-phase regression returns **and** the `homogeneity_epochs` seed block exists. Interim: longest-homogeneous as primary **plus** a mandatory `climatology_vintage_sensitivity` disagreement driver |
| **Any recurrence interval, return period or AEP for any reach** | X6 | Never. Add the refusal to `HYDROLOGY.md` §13 in writing |
| **Any local AR-frequency trend, and any local snowpack trend from the platform's own SNOTEL feed** | X10 | Never in either direction; a single-detector AR trend is uninterpretable by ARTMIP's own finding |
| **4,500 ft, or any single universal snow band** | X14 | Never universally. Per-basin capability only, with UNKNOWN above the top pillow for cedar and snohomish-snoqualmie |
| **Any pooled multi-basin SWE composite (44 % / 45.6 % / 31.4 %)** | X13, X16 | Never. The platform emits per-basin numbers; a pooled figure is not one of them and should not start being one |
| **0.831 ft/ft and r = 0.94 for SNAW1; 0.019 ft/ft and r = 0.33 for NKSW1; 0.010 ft/ft for MVEW1** | X12, X15 | Never as scalars. The *classes* are cleared (below); a coefficient enters only with its regime, lag, estimator, window and control gauge |
| **`g(Q)` band edges from `method:catchment-sensitivity@1.0.0`** at basin scale | X11 | The routing-deconvolution refit shows the flattening is regulation and not routing lag |
| **A short-window-peak vs `duration_above_rate` choice for the second forcing feature** | X5 | The per-basin ΔR² test returns; a split verdict is encoded per basin, not averaged |

### CLEARED for normative doctrine

| Statement | Label | Row | Qualifiers that must travel with it |
|---|---|---|---|
| **No seeded forecast point is tidally affected at the gauge.** M2 ≤ 0.008 ft at all six against a coastal M2 of 2.26–3.36 ft; tidally-injected false rate-of-rise ≤ 0.025 ft/h at the live 6 h window, against `STAGE_STEADY_EPS_FT_PER_H = 0.05` | FACT | X9, X12 | "at the gauge"; measured 2026-08-26 against a non-tidal control (MROW1 12150800); two independent low-flow years plus Event Zero |
| **`rate_of_rise`, headroom and time-to-threshold are sound as implemented at all six seeded points** | FACT | X9, X12 | Same measurement; no de-tiding is needed for anything the platform currently serves |
| **SNAW1 is genuinely tidal — a class, not a scalar:** ~0.75–0.92 ft/ft at low flow, ~0.22–0.32 during a large flood, +1.25 h lag | FACT (class) / INFERENCE (regime curve) | X15 | Not seeded; the regime collapse is one observation; the coefficient must never be quoted without its regime |
| **Event Zero's record crests arrived at a benign coastal boundary:** SNAW1 34.45 ft at 2025-12-12T01:35Z with Seattle at 4.723 ft MLLW = **6.64 ft below MHHW** | FACT | X9 | Reproduced to the hundredth of a foot; the record itself is therefore a compound quantity and must not be recorded as a pure river record |
| **The Mount Vernon backwater term is underpowered, not absent:** +0.17 ± 0.10 ft/ft (t = +1.7) on the high-flow subset, and the record contains almost no crest-on-high-tide-plus-surge observations | INFERENCE + OPEN QUESTION | X9 | Must be stated as *underpowered*; "no backwater" must not be inherited. The tail's absence from the record is not evidence of its absence from the future |
| **Below 4,500 ft on 2025-12-11, SWE was 13.8 % of median across 20 reporting sites, 10 of them at exactly 0.00 in** | FACT | X14, X17 | Estimator (ratio-of-sums), day, n, and exclusions stated; **not** to be generalised into a pooled composite |
| **Cedar and Snohomish-Snoqualmie cannot support an elevation-stratified SWE statistic at any band elevation; the honest answer above ~3,810 / ~4,010 ft is UNKNOWN** | FACT | X14 | Site counts and spreads stated (n = 4, 880 ft and 690 ft); Skagit and Puyallup-White can; Nooksack and Green-Duwamish only with an n = 1 upper band flagged |
| **Four SNOTEL sites mapped into seeded basins have majority-Columbia `associatedHucs`** (Harts Pass 6/6, Rainy Pass 5/5, Swamp Creek 4/6, Stevens Pass 4/6; Thunder Basin borderline 4/6) | FACT | X13 | From the station payload the platform already fetches; the *fix* is a pending policy decision, not a further measurement |
| **WY2026 is a warm snow drought:** 2026-04-01 composite 55.7 % of median SWE with accumulated precipitation at 105–138 % of median at every station, pooled 118.1 %, **zero** stations below 100 % | FACT | X14 | n = 25, ratio-of-sums, per-station range given |
| **The Mount Vernon rating drifted ~9–11 % at flood stage over roughly three decades**, cause bed aggradation in a levee-confined sand-bed reach, **not** the tide | INFERENCE with strong physical corroboration | X1, X9 | Never FACT; n = 2–3 modern high-flow measurements, both quality *Fair* (8 % uncertainty, the same size as the effect); the scatter matters more than the trend |
| **A stage threshold has a hydraulic vintage**, and the platform has no concept of a rating epoch | INFERENCE | X1, X8 | `CROSS-DOMAIN-FINDINGS.md` C3; the `rating_epoch` of `cascading-hazards` and the `homogeneity_epochs` of `climate-change` are **the same object under two names** and should be one contract addition |
| **A low-elevation SWE deficit lowers rain-on-snow potential; the defect in a pooled composite is wrong-mechanism attribution, not understated magnitude** | INFERENCE (mass balance) | X17 | Keep the corpus's narrower wording, "misleading in the direction of calm" |

---

## 4. Keeping this file true

- A row closes only by moving to **RESOLVED BY MEASUREMENT** (citing the measurement) or **RESOLVED BY
  ADJUDICATION** (citing the reasoning) or **SUPERSEDED** (citing what replaced it). Rows are not deleted;
  a closed row is the record of why a number is allowed to be where it is.
- A new contradiction gets the next free id from **X18**. Opening one is cheap and is the point.
- Any change to `HYDROLOGY.md` that touches a "needs correction" or "needs hedging" row above must update
  that row's **doctrine status** in the same change.
- The three doctrine defects this register currently carries against `HYDROLOGY.md` are, in order of
  severity: **§7's rain-on-snow FACT (X4, correction)**, **§2 line 75's Ferndale tidal claim (X12,
  correction)**, and **§12's 1990-vs-2025 crest comparison across a levee breach (X1, hedging)**. §13
  needs one addition (X6) and §8 needs one (X8).
