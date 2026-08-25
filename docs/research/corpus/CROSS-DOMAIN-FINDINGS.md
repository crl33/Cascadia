# Cross-domain findings

*Synthesis across the twelve corpus files, 2026-08-24. See [`README.md`](README.md) for the index and
the per-file verification status.*

Nothing here is new evidence. Everything here is a statement that no single corpus file could make,
because it depends on two or more of them agreeing, disagreeing, or handing off to each other. The
test of relevance is unchanged: **a 6–120 hour flood forecast for a named western Washington basin.**

Four sections: findings the domains **converge** on (the strongest thing in the corpus), findings
they **contradict** each other on (which need adjudication and are named), the **causal chain** from
forcing to stage assembled end to end, and the **factor ranking** with an honest account of where it
is uncertain.

---

## 1. Convergent findings

These are strong precisely because the domains reached them from unrelated measurement systems —
atmospheric reanalysis, hillslope trenches, snow lysimeters, recession analysis, tide gauges,
reservoir storage series, rating-shift histories — without citing each other.

### C1 · Duration and simultaneity beat intensity, and four domains say so independently

| Domain | Independent evidence |
|---|---|
| `atmospheric-rivers` | Duration is co-equal with intensity in the AR scale. 2× the mean duration produced **~6× peak streamflow and >7× storm-total runoff volume** (Ralph et al. 2013). Dense AR clusters yield **150–300 % more runoff over the Cascade Range** than sparse ones (Zhou et al. 2024) |
| `runoff-generation` | Soil infiltration capacity exceeds any plausible rain rate by **~20×**, so intensity cannot generate Hortonian runoff at all in intact forest. What makes an extreme is *simultaneity* of threshold crossing across the basin (Jones & Perkins 2010) |
| `snow-hydrology` | Peak-day hourly intensity in the largest H.J. Andrews floods was only **2.7 ± 0.9 mm h⁻¹**. Extreme floods are the ones where precipitation and snowpack outflow are in phase at multiple timescales for days (Jennings & Jones 2015) |
| `regulation-operations` | The binding reservoir constraint is **volume across a sequence**, not peak attenuation of one hydrograph. December 2025 was six AR pulses over two weeks; evacuation between pulses is governed by the *next* storm's forecast |

The convergence has a clean, mechanistically-explained exception that strengthens it: in
`cascading-hazards`, the *opposite* variable governs. Debris flows are controlled by 15-minute
intensity, and the Dixie Fire comparison is decisive — an atmospheric river delivering **258.6 mm**
at peak I₁₅ of 16.8 mm h⁻¹ produced streamflow and a ~2,000 m³ sand deposit, while a thunderstorm
delivering **33.4 mm** at peak I₁₅ of 39.2 mm h⁻¹ produced debris flows depositing **≥10,000 m³**.
Western Washington's flood storms are the first kind. That is why the region's flood season and its
debris-flow season are not the same season.

**Consequence.** A forcing surface banded on a 72-hour basin-mean QPF total is measuring the one
variable all four domains agree is not the discriminator. `duration_above_rate` and *basin fraction
simultaneously above rate* are the shapes the evidence supports.

### C2 · The observing network's own artefacts are larger than the geophysical signals being sought

Seven domains found this independently, and none of them was looking for it.

- `climate-change` measured a **41.26 ft datum discontinuity** between WY1939 and WY1940 in the USGS
  annual-peak stage series at Snoqualmie near Carnation — *one of the platform's own configured
  susceptibility gauges* — plus a **+1.7 °C Tmin sensor step** across the whole 11-state SNOTEL
  network that propagates into PRISM and DAYMET.
- `cascading-hazards` found the same Carnation step (~43 ft) with a completely different method, plus
  a ~7 ft step at Ferndale between 1964 and 1968, steps at Cedar at Renton in ~1951 and ~1976, and a
  −0.8 ft step on the Sauk at WY2018 that persists.
- `routing-hydraulics` found that USGS itself excluded pre-2008 high-flow measurements from the
  current Mount Vernon rating *because the agency believes the control changed* — and that both
  modern high-flow measurements are rated *Fair*, i.e. 8 % uncertainty, the same size as the effect
  being measured.
- `snow-hydrology` found the median western-Washington SNOTEL sits at the **top** of the 1,000–4,000 ft
  band where maritime ROS floods are generated, with one site below 2,000 ft; three basins are
  single-station and two of those records begin in 2018 and 2020.
- `antecedent-conditions` found four of eight basins have **zero** SNOTEL soil-moisture stations, the
  Sauk has none, and the single Nooksack station returned 51 of 123 days *all reading 0.0 %* and
  nothing at all before 12 December 2025 — i.e. nothing through the entire lead-up to the record flood.
- `compound-coastal` found **no real-time NOAA water-level gauge in Skagit Bay, Padilla Bay, Port
  Susan or Possession Sound**, and that NWPS decodes its two Puget Sound tide gauges with the SHEF
  code for *cloud ceiling height*, datum absent.
- `orographic-precipitation` found gauge undercatch of **25–40 % above 1,500 m** in this region, and
  that radar adequately covers only ¼–⅓ of the coastal western US and reads **<50 % of gauge values**
  where precipitation is heaviest.

**Consequence, and it is the corpus's single most important cross-domain statement.** In western
Washington the largest step changes in the record are instrumental, not hydrologic. Any trend,
percentile or threshold computed across an unexamined record is measuring the network. This is why
`climate-change` §6.4's rule — *the reference period is the longest **homogeneous** record, and
homogeneity is broken by datum epochs, rating revisions and operating-rule changes far more violently
than by warming* — is not a refinement; it is a precondition.

### C3 · The stage–discharge relation is non-stationary, and it drifts toward thresholds arriving earlier

Five domains, four measurement approaches.

- `routing-hydraulics`: **−9 to −11 % conveyance at flood stage** at Mount Vernon since the late
  1980s, from rating-independent measured pairs, corroborated by USGS's own rating remark, a
  1975→1999 cross-section survey (+1.5 ft mean bed over 20 sections) and a **66 % increase in the
  suspended-sediment rating slope** at that exact gauge.
- `cascading-hazards`: measured at fifteen gauges. The signal is confined to basins with glaciated
  volcanic headwaters (Nooksack) and the non-glacial controls are flat (Skykomish +0.003 ft/decade
  over 92 years, residual sd 0.18 ft; Sauk exactly 0.000 over 1932–2017). Independently corroborated
  by USGS SIR 2019-5008, which measured +0.3 to +0.5 ft/decade in the 90th percentile of *daily*
  stage at Ferndale **with no trend in discharge**.
- `climate-change`: the population-level Mount Vernon drift is only −4.4 % at 37 ft over 85 paired
  annual peaks — but the residual **scatter** is ±0.68 ft against NWS category spacing of **2 ft**,
  and there is a 3.14 ft inversion in the record (138,000 cfs at 33.85 ft in 2006; 127,000 cfs at
  36.99 ft in 2021).
- `regulation-operations`: the dams are still operated against a Mount Vernon rating (32.7 ft =
  100,300 cfs "major damage") that is roughly **10 % higher in flow-for-stage** than the 2025
  observation. Both the forecast target and the operating target are drifting.
- `flood-statistics`: therefore a *stage*-frequency statement at such a point is a different object
  from a *discharge*-frequency statement and cannot be inherited from one.

**Consequence.** `HYDROLOGY.md` §9's refusal to convert stage↔flow is vindicated by four independent
lines, and it needs one addition all five domains imply: **a stage threshold has a hydraulic
vintage**, and the platform has no concept of a rating epoch.

### C4 · Regulation replaces the signal with a decision — and it is measurable from the hydrograph

Six domains.

- `runoff-generation`: the Green below Howard Hanson has a Kirchner exponent `b − 1 ≈ −0.05`, i.e.
  `g(Q)` is **flat** — the apparent storage–discharge relation is a dam operating rule, not a
  hillslope, and its implied 790 mm "storage" is reservoir operation. The exponent orders the basins
  *exactly* as `regulation_class` does (unregulated 0.85–1.05 > Skagit 0.67–0.77 > Cedar 0.17–0.26 >
  Green −0.06).
- `flood-statistics`: Green at Auburn shows a statistically significant **downward** trend in annual
  peaks (τ = −0.187, p = 0.010) that is Howard Hanson, not climate — and it is a *step at
  impoundment*, not a trend (τ = −0.070, p = 0.46 restricted to WY1970–2025).
- `climate-change`: splitting the Green and Skagit records at their major-impoundment dates flips
  **29–32 % of days** into a different susceptibility band and shifts the ranking by 9.9–11.1
  percentile points — **more than any climate effect measured anywhere in the corpus**.
- `regulation-operations`: the regulated frequency curve carries visible discontinuities at the
  62,000 and 90,000 cfs regulation triggers and **does not merge back** into the unregulated curve.
- `antecedent-conditions`: regulated gauges have the *highest* statistical persistence (Cedar
  ρ = 0.705, lowest mid-event share 45 %) — regulation makes the percentile **more** autocorrelated,
  not noisier. The confidence caps are right for the wrong stated reason.
- `forecasting-verification`: at Green at Auburn the moderate category has **2 instantaneous events
  in 36 years** and major has **0 since the dam closed in 1962**. Regulation destroys the upper half
  of the verification sample.

**Consequence.** Four domains independently confirm the platform's existing decision to read the Sauk
rather than Mount Vernon for Skagit susceptibility, and they add something the seed does not have:
regulation class is now *measurable from the hydrograph* as a consistency check on the configuration.

### C5 · Antecedent state is a gain, not a predictor — and here the gain is already engaged

Four domains, four unrelated instruments, all pointing the same uncomfortable way.

- `runoff-generation` (recession analysis on 15-minute discharge): the gain is real and large —
  **7.6–11.1×** between seasonal-median and flood-generating flow. And it does not order outcomes:
  pre-event flow explains **r² = 0.001–0.057** of peak magnitude across the top-25 Nov–Mar peaks at
  four unregulated gauges. The basins wet up between **1 October and 5 November** in every water year
  of WY2020–2024 — the switch is thrown before the flood season peaks.
- `antecedent-conditions` (a point soil probe, and a regional regression): Cayuse Pass root-zone soil
  moisture has a **November–February interquartile range of 0.50 percentage points**, with 96.1 % of
  Nov–Feb days within 2 points of the 15-year record maximum. Webb et al. 2025 places Washington in
  the *low*-responsiveness group at **2×**, against 4.5× for coastal California/Oregon — half the West
  Coast effect, not none. Moore et al. 2011 measured a **48-day** autumn refill, putting a
  western-Cascade basin at its winter plateau by mid-to-late November.
- `atmospheric-rivers`: antecedent wetness is one of Neiman's five flood terms, but the Russian River
  "< 20 % precursor soil moisture ⇒ no significant streamflow" floor is reached by default here from
  roughly November to March, so its discriminating power is concentrated in October and March.
- `snow-hydrology`: the other "state" term is equally small — the pack's combined buffer is ~30–45 mm
  against a 200–400 mm AR, i.e. it absorbs roughly 8–20 % of the storm and conducts the rest.

**Consequence.** Both statements must be said together, and the platform currently says only the
first. State sets the *gain*; forcing sets the *outcome*; and in this maritime regime the informative
window for state is October, March–May, and the aftermath of a dry autumn — not the November–January
core. The Event Zero replay in `antecedent-conditions` §3.1(f) is the proof: the surface read LOW/
MODERATE on the day the official Flood Watch was issued, and the entire signal was in the derivative.

### C6 · Six domains independently re-derived the platform's own refusals

This is a doctrinal rather than a scientific convergence, and it is the strongest one in the corpus:
six domain leads, working from unrelated literatures, arrived at the refusals `DATA_DOCTRINE.md`
already encodes — from evidence, not from the doctrine.

| Refusal | Domain that re-derived it, and from what |
|---|---|
| Never convert stage↔flow | `routing-hydraulics` — the current Mount Vernon rating is *extrapolated* above 125,000 cfs and conveyance changed ~11 % in three decades |
| Never publish a return period | `flood-statistics` — 17C excludes regulated watersheds by scope, provides no evaluated mixed-population method, and the 1 % AEP is known to a factor of ~1.6 |
| Never sum tide + surge + river | `compound-coastal` — the nonlinear interaction terms are first-order, reaching −50 % of a linear sum upstream in the Duwamish |
| Never average disagreeing models | `climate-change` — publish the ladder vintage sensitivity as a *disagreement signal*, never as a correction, because the adjustment would chase a term smaller than the noise at six of ten gauges |
| Never print an uncalibrated probability | `forecasting-verification` — at base rates of 0.0016–0.008 a probability is not merely unproven, it is *uncheckable* with the data the platform will have for years |
| UNKNOWN is a legitimate state | `antecedent-conditions` — four of eight basins have no mountain soil observation at all; `SOIL_UNAVAILABLE_REASON` is not merely defensible, it is understated |

`forecasting-verification` supplies the name for why this matters: Murphy's **type-1 goodness**
(consistency — the forecast matches what the system actually believes) is the precondition for
quality and value to be attainable at all. The badge system is not decoration.

---

## 2. Contradictions requiring adjudication

Named, with what each side rests on. Model disagreement is information; **so is corpus
disagreement**, and none of these should be silently resolved by picking the more recent file.

### X1 · The magnitude of the Mount Vernon stage–discharge drift — **three incompatible numbers**

| Source | Claim | Basis |
|---|---|---|
| prior repo pass | **−29 %** less flow for the same 37.00 ft stage | two points, one of which is a 1906 indirect estimate whose peak *day* is unknown |
| `routing-hydraulics` §5.2 | **−9 to −11 %** at flood stage since the late 1980s | rating-independent measured pairs, n = 3–4 per side, ±5 % two-standard-error interval |
| `climate-change` §3 | **−4.4 %** at 37 ft | population-level, 85 paired annual peaks, pre-1980 vs 1980+ log-linear fits |
| `cascading-hazards` §5.4 | *"the rating did not drift, it destabilised"* — residual sd **0.25 ft (1948–2005) → 1.38 ft (2006–2024)** | 41 annual peaks, upper half of the discharge distribution |

These are not all the same quantity — different estimators, reference stages, windows, and one is a
*variance* claim rather than a trend claim — but they cannot all be quoted, and two of the three
files do not cite each other. **Adjudication needed** on: which estimator and window the platform
adopts; and whether post-2005 Mount Vernon behaviour is a trend, a ramp (the residual sequence is
close to monotone and Mann–Kendall flags it at p = 0.0006), or a variance explosion. Note the
practical convergence underneath: all three agree the *scatter* (±0.68 to ±1.4 ft) is comparable to
or larger than the *trend*, against 2 ft NWS category spacing.

### X2 · Does crest lag on the lower Skagit lengthen or shorten with flood magnitude?

`routing-hydraulics` §5.1 measures **r = +0.65** — bigger floods travel *slower* (median 16.9 h
Concrete → Mount Vernon, 17.0 h for ≥100 kcfs vs 14.5 h below) — and attributes it to channel and
Nookachamps storage engagement. The same file flags that **USACE states the opposite** in §2.4.6.4 of
the 2013 hydrology document: hydraulic travel time *decreases* from 15–20 h at low flow to 10–15 h at
higher discharges. The file also concedes that `argmax` on a broad crest is not a robust timestamp —
the single most influential event (2006, lag 23.75 h) moves to 18.25 h on a different tie-break, and
crest breadth grows with flood size, so the tie-breaking noise is itself magnitude-dependent.
**Unresolved, and it is the input to time-to-threshold.** A crest-*centroid* timing method has not
been tried.

### X3 · Is attenuation on Concrete → Mount Vernon a big-flood phenomenon?

Same file, same reach. Measured r = −0.57 over 2003–2025 (attenuation grows with magnitude, ≥100 kcfs
median −11.0 %). **USACE asserts the opposite generalisation in the same document**: high-peak,
high-volume floods fill channel storage and, with 356 mi² of local inflow, *increase* the peak
downstream. Adding the eight historical events in USACE Table 9 keeps the sign but roughly halves the
effect (≥100 kcfs median −5.2 %), and several of the largest floods on record **amplified** — Feb
1951 +3.6 %, Dec 1975 +6.6 %, Nov 1990 second flood +4.1 %. The file settles on "bimodal", which is
honest and is not a usable parameter.

### X4 · Rain-on-snow melt energy partitioning — the repo asserts one side as FACT

`snow-hydrology` §4 contested #1. Marks et al. 1998: **60–90 % turbulent** (Feb 1996, open,
wind-exposed). Mazurkiewicz et al. 2008: **net radiation largest, 33–55 %** across three sites over
eight years, and the authors explicitly *"question the general perception of turbulent energy
exchange dominance of ROS and seasonal melt in the PNW"*. Li et al. 2019: **68 % net radiation**,
CONUS. Advected rain heat is separately contested at **<10 % / 10–15 % / 29–44 %** — and the high
value belongs to precisely the persistent-melt events that produce floods. `HYDROLOGY.md` §7
currently states the turbulent-flux side as FACT. The file's reconciliation — *turbulence does not
always dominate, but turbulence is what makes an ordinary ROS event an extreme one, so wind and
dewpoint at pack elevation are the discriminating variables* — is the best available synthesis and is
an INFERENCE, not a resolution.

### X5 · Are western Washington flood storms short or long?

`atmospheric-rivers` §4 contested #1. Warner, Mass & Salathé 2012 find most regional flooding events
are associated with precipitation periods of **24 h or less**, and that 2-day totals capture nearly
all major events. Jennings & Jones 2015 find the largest western-Cascades floods are produced by
**sustained, moderate-intensity** rain. Probably reconcilable by basin scale and response time —
small coastal basins versus western Cascade basins — but **unresolved for the platform's own basins**,
and the two support opposite designs for the second forcing feature (a short-window peak metric
versus `duration_above_rate`). Note the tension with C1: the convergence there is about *simultaneity
of threshold crossing*, which is not the same claim as *long storm*, and this contradiction is
partly a question about which of the two C1 is really describing.

### X6 · Do western Washington peak flows need mixed-population flood-frequency treatment?

`flood-statistics` §4. Barth et al. 2017 (1,375 gauges): the western-US annual maximum series is a
mixture whose tail is AR-dominated, and AR-only quantile estimates are *higher* than pooled ones.
USGS SIR 2016–5118 — the authoritative Washington study, published the year before — inspected the
frequency plots and concluded **"no streamgages had substantially diverging distributions that
required a mixed-population analysis"**, while conceding on the same page that many gauges *do* have
a mixed population. **Both are USGS-affiliated and they disagree about this state.** The corpus
establishes the disagreement is about the *criterion* (visual divergence of a fitted curve versus
quantile difference under an event catalogue), not about whether a mixture exists — and that USGS
peak codes **cannot** supply the objective criterion 17C demands, since code 9 appears **3 times in
~900 western Washington annual peaks**.

### X7 · Does the forest-harvest peak-flow effect grow or vanish with return period?

`cascading-hazards` §4 contested #1. Grant et al. 2008 (the state-of-science report): no detectable
effect beyond ~**6-year** return periods, and the basin-scale effect is **smaller than interannual
variability**. Alila et al. 2009, and now Kaluarachchi & Alila 2026 (*Ambio*
10.1007/s13280-026-02346-6): chronological pairing **cannot detect a frequency change in principle**,
and frequency-paired reanalysis finds effects that *grow* with return period — a 30-year event
becoming a 14-year event. Comments from Lewis, Reid & Grant, from Bathurst and from Birkinshaw
dispute Alila's method in turn; Bathurst et al. 2020 attempt reconciliation and report the curves
converging at the largest floods. **Live and unresolved.** Both camps' *practical* recommendation for
the platform coincides — keep land use out of the hazard computation — for opposite reasons, so the
platform's position must be stated as *unresolved method*, not as agreement between the camps.

### X8 · Longest record or most recent 30 years for the day-of-year ladder?

`climate-change` §2.3 argued for the longest record; its own adversarial reviewer found the evidence
**circular by construction** (the error metric was distance from the full-record ladder, which makes
the full record optimal arithmetically). Re-tested out-of-sample with a rolling-origin calibration
criterion, the rule survives *on average* — full-record mean calibration error **3.42** points versus
**3.98** for the most recent 30 years and **5.04** for the most recent 20 — but a recent-30 ladder
beat the full record at **10 of 10 gauges** on the 2016–2025 holdout and lost at essentially all of
them on 2006–2015. **The answer is PDO-phase dependent.** The rule in §6.4 is supported; the evidence
originally offered for it is not, and the file says so in place.

### X9 · Is the Mount Vernon forecast point compound at all?

Two domains agree the tide is negligible **at the gauge**: `compound-coastal` measures tidal
transmission of **0.010 ft/ft** and `routing-hydraulics` independently fits **M2 ≈ 0.004–0.009 ft**
against a Skagit Bay range of 8–11 ft, with the USACE model putting the tidal limit ~7 river miles
downstream. But `compound-coastal`'s own re-run found its backwater null is **underpowered, not
absent**: the high-flow subset coefficient is **+0.17 ± 0.10 ft/ft (t = +1.7)** — correctly signed,
merely non-significant — and, decisively, *a Skagit crest has essentially never coincided with a high
tide plus a large surge in the record*, so the regression contains almost no observations of the
regime that matters. **Adjudication: the refutation is solid for the oscillatory tide and weak for
the backwater term in the untested corner.** The Skagit Climate Science Consortium's public statement
that the river is "heavily influenced by the tide" from "below Mt. Vernon to Puget Sound" is
compatible with both — *below* the gauge, not at it — and the prior repo pass over-generalised it.

### X10 · Is the AR signal at Washington's latitude rising?

`climate-change` §4 and `atmospheric-rivers` §4 contested #3, reached separately. Pan et al. 2025
report an **"AR increasing hole"** over the Pacific Northwest — *"a region of little to no increase,
or slight decrease"* — with PNW total winter precipitation showing a significant **decrease of
22.3 mm per decade**. Scholz et al. 2025 report a widespread 20th-century increase. ARTMIP Tier 2
finds **detector choice dominates model choice** as the uncertainty source, so an AR-frequency
percentage is partly an artefact of the detection algorithm. Measured, over 40 years of reanalysis,
AR-mean **IVT has risen by less than 1 %**. **Not reconciled — and both files reach the same
operational verdict: the platform must not assert a local AR trend in either direction.** That
agreement on the verdict, despite disagreement on the science, is itself worth recording.

### X11 · Kirchner's stated scale limit versus the corpus's use of his method

An internal contradiction that `runoff-generation` flags against itself. Kirchner (2009) §15.6 states
the method *"must break down for catchments that are too large"* and speculates that ~1,000 km² is
too big, because channel-network routing lag would swamp the storage signal. **Six of the seven
gauges the same file fits are at or beyond that scale**, and all are 70–800× his study catchments.
Channel routing lag is therefore an unexcluded alternative explanation for the flattened `g(Q)` at
Mount Vernon, competing directly with the regulation explanation the file offers as finding 4 — and
`routing-hydraulics`, which measures a 16.9 h median routing lag on exactly that reach, is the domain
that would adjudicate it. Neither file cites the other. **This is the clearest hand-off failure in
the corpus.**

---

## 3. The causal chain, forcing to stage

Assembled across domains. Each link names its owner and its weakest point. The chain is only as good
as its worst link, and the worst links are **not** where the science is weakest — they are where the
science is fine and the *observation* is absent.

| # | Link | Owner | State of the link |
|---|---|---|---|
| **L1** | Synoptic setup: moisture delivered to the coast | `atmospheric-rivers` | **Strongest in the chain.** Neiman et al. 2011 is a *western Washington* paper; the flood/AR association is essentially 1:1. Forecastable to ~7 days. But the discriminating variables are geometric and temporal, not volumetric |
| **L2** | Terrain conversion: IVT → basin precipitation | `orographic-precipitation` | Strong where unblocked (r² = 0.85 over the Olympics, warm sector). **Weak at the crest** — convection-permitting models show bias ratio rising windward→leeward and nobody knows if that is model or PRISM bias — **and blind to the Puget Sound Convergence Zone**, which lands on Snohomish/Snoqualmie headwaters through a mechanism no IVT feature will ever see |
| **L3** | Phase partition: how much falls as rain, and how far down the slope | `snow-hydrology` | **Structurally blocked.** Three distinct elevations (free-air freezing level / atmospheric snow level / **mountainside snow line**) differ by hundreds of metres, and the offset *grows with precipitation intensity* — largest exactly during the heaviest AR hours. The platform has no hypsometry (`NEXT_STEPS.md` gap 6), so rain-exposed fraction is uncomputable |
| **L4** | Snowpack modulation: absorb, pass, or add | `snow-hydrology` | **Weakest link in the chain.** Simultaneously *unobserved* (the network sits above the generating band; wind and dewpoint at pack elevation are not in the ingest at all), *unmodelled* (no ROS representation in the forcing surface), and *scientifically unsettled* (X4). Hard bounds exist and are small: outflow <3 mm h⁻¹ net, <10 mm h⁻¹ total, never above 14 |
| **L5** | Measuring what actually fell | `orographic-precipitation` | Radar covers ¼–⅓ of the coastal western US adequately and reads <50 % of gauge values in the heaviest rain; gauges undercatch 25–40 % above 1,500 m. **A badging failure, not just an accuracy one**: MRMS is tagged OBSERVED, but a large fraction of upper-basin cells are Mountain Mapper (PRISM climatology × a distant gauge ratio, i.e. MODELED) or HRRR fill (DERIVED) — and Mountain Mapper is *not applied at all* in the frozen-precipitation season |
| **L6** | Antecedent state: the gain | `antecedent-conditions` + `runoff-generation` | Physics settled, magnitude measured (7.6–11.1× gain; 71–104 mm store), **predictive value near zero within the flood season** (C5). Informative in October, March–May, and after a dry autumn |
| **L7** | Hillslope → channel | `runoff-generation` | Mechanism settled (saturation excess + subsurface stormflow; fill-and-spill at 18–60 mm with a >75× connectivity multiplier; celerity ≠ velocity). **Scale gap**: every published threshold is a hillslope number, and nobody has published a basin-scale connectivity threshold for the Sauk, Snoqualmie or Nooksack |
| **L8** | Regulation: which fraction becomes a decision | `regulation-operations` | **Constants are excellent** — control fraction, allocated storage, objective flow, travel time all published per project, and December 2025 reproduced from primary series. **Intent is invisible**: no public Section 7 feed, forecast pool trajectories catalogued but unreadable, and the official downstream forecast already embeds an unpublished operating plan |
| **L9** | Channel routing | `routing-hydraulics` | Distribution measured (median 16.9 h, sd 3.5 h, peak change −25 % to +28 %). **The sign of the magnitude dependence is contested against the reach's own authority** (X2, X3) |
| **L10** | Conveyance: discharge → stage | `routing-hydraulics` + `cascading-hazards` | Best-measured link in the corpus, and the most dangerous: **the only place where a decades-scale variable silently rewrites an operational threshold**. Drift −9 to −11 % at flood stage; scatter ±0.68 to ±1.4 ft against 2 ft category spacing |
| **L11** | Downstream boundary condition | `compound-coastal` | Material at **one** forecast point (Snohomish at Snohomish, 0.83 ft/ft — which the doctrine does not mention) and marginal at the two the doctrine *does* flag. **The compound tail is unrealised**: Event Zero's three record crests all landed 4.8–6.6 ft below MHHW |
| **L12** | The reference distribution the stage is judged against | `flood-statistics` + `climate-change` | **Weakest link at the decision end.** The ladder saturates at p95 across a **2.5× flow range** during the event it exists for, carries ±5.5–6.2 percentile points of sampling error at 30 years, and its band edges are 15 points apart |
| **L13** | Whether any of it can be scored | `forecasting-verification` | Base rates 0.16–0.77 % of days. At **four of six** seed points the official category is in stage and the only available ensemble is in flow, so the exceedance probability is not computable at all |

### Where the chain is weakest, in order

1. **L3–L4, phase partition and snowpack.** The only link that is unobserved, unmodelled *and*
   scientifically unsettled at once. It is also the highest-leverage link in the chain: White et al.
   2002 modelled that a **610 m in-storm snow-line rise would triple runoff** in three northern
   California basins, and the western-Washington flood composite melting level is ~1.9 km MSL against
   a ~0.95 km in-storm climatology — a full kilometre anomaly. Unblocking it needs one thing:
   **hypsometry**. That single missing artifact blocks `swe-below-snow-line`, `rain-exposed fraction`,
   `ROS-exposed fraction` and `pack-buffer-capacity` simultaneously.
2. **L10, conveyance.** Not because the science is weak but because the platform has no rating epoch,
   so a slow variable corrupts a fast decision invisibly.
3. **L13, verifiability.** The chain terminates in a decision that cannot be scored at the points
   that matter, and at two regulated points may never acquire a sample.

### Where the hand-offs fail

Three places where two domains own adjacent links and do not talk:

- **L7 → L9** (X11): `runoff-generation` fits Kirchner's method at scales its author excludes, and
  the alternative explanation is exactly what `routing-hydraulics` measures.
- **L2 → L5**: `orographic-precipitation` establishes that models now beat gauge-interpolated grids
  for mountain totals (Lundquist et al. 2019, by a factor of 2 at independent sites) while
  `forecasting-verification` establishes that the NWRFC calibration is tuned to a *bias-corrected
  historical forcing* (AORC with optimised mid-month adjustment factors) rather than to the real-time
  forcing it is driven with. Together those imply a hindcast driven with real-time-style inputs is
  not exercising the model the calibration produced — neither file draws it.
- **L10 → L12**: `cascading-hazards` proposes a `rating_epoch` and `climate-change` proposes
  `homogeneity_epochs`. **These are the same object under two names**, and both are P0 in their own
  file. They should be one contract addition.

---

## 4. Factors ranked by how much they move flood outcome in western Washington

Read the caveats in §4.5 before using this ranking. It is a synthesis of single-variable studies;
**no factor here has been jointly hindcast against the others for a western Washington basin.**

### Tier 1 — sets whether a flood happens at all

**1. AR presence with a favourable low-level wind orientation into the specific basin.**
Every peak daily flow above a 5-year return period in four unregulated western-Washington basins over
WY1980–2009 occurred with a landfalling AR, and 46 of 48 annual peak daily flows in WY1998–2009 did
(Neiman et al. 2011). Orientation separates the four basins at **>95 % significance**: the Green
floods only in a **245°–275°** window and its peak flows consequently vary by an **order of magnitude**
between years, while the Sauk is rain-shadowed by both the Olympics and Vancouver Island for every
onshore direction except southwesterly. *Evidence: strong, local, quantitative — the single most
transferable result in the corpus to platform design.* **Uncertainty: only two of the platform's eight
basins have a published window.** Nooksack, Skykomish, Snoqualmie, Stillaguamish, White and Cedar have
none, and deriving them is a bounded piece of work the platform has the data for.

**2. Event duration and AR family structure.**
Doubling the mean duration of AR conditions produced **~6× peak streamflow and >7× storm-total runoff
volume** (Ralph et al. 2013). Over the **Cascade Range specifically**, dense AR clusters produce
**150–300 % more runoff** than sparse ones, and dense clusters peak in November (Zhou et al. 2024) —
the strongest region-specific amplification number in the corpus. Event Zero was an AR *family*, not
an event. *Uncertainty: the 6×/7× scalings are Russian River results, unverified here; the clustering
aggregation window is regionally variable and untabulated per basin.*

**3. Storm-total upslope IVT — IVT projected onto the basin's own terrain gradient.**
**74 % of the variance in storm-total rainfall and 61 % in storm-total runoff volume** (Ralph et al.
2013, 91 events). Independently, over the Olympics: **r² = 0.85**, slope 0.014 mm h⁻¹ per
kg m⁻¹ s⁻¹ (Tierney & Durran 2024) — a *western Washington* measurement, which is unusual good
fortune. *Uncertainty: the OLYMPEX fit is warm-sector, unblocked — the best case. The Cascades sit
near the blocking transition (M ≈ 1) where the Olympics in warm sector sit at 0.7, and Neiman et al.
2002's season-long variance-explained figures (31–48 %) are far below their case-study range (58–88 %).*

### Tier 2 — sets how big

**4. Melting level / mountainside snow line — i.e. rain-exposed basin fraction.**
The western-Washington flood composite melting level is **~1.9 km MSL against a ~0.95 km in-storm
climatology**, with 925 hPa temperatures 4–6 °C above normal (Neiman et al. 2011). White et al. 2002
modelled that a **610 m in-storm snow-line rise triples runoff**. *This is arguably rank 1 on physics
and is ranked 4 only because it rests on one Californian modelling result and one composite anomaly —
and because* **the platform cannot compute it at all**: there is no hypsometry, and NBM `SNOWLVL` is a
column wet-bulb level needing a further terrain depression of O(100–250 m) that grows with
precipitation intensity, i.e. is largest exactly when it matters.

**5. Regulation state — control fraction × allocated storage × pre-storm pool position.**
Effectiveness is a hump: **0 % at the 2-year event, 17.8 % at the 25-year, 10.8 % at the 500-year** on
the Skagit; Howard Hanson delivered a **58 % peak reduction** in December 2025 and Ross absorbed
**110,900 acre-feet**. Above roughly the 25-year event, uncontrolled runoff alone produces major
flooding in the lower Skagit valley *regardless of regulation*. *Uncertainty: none about the constants
— they are published per project. Total about operator intent.*

**6. Antecedent storage state.**
A measured **7.6–11.1× gain**, and a precipitation-controlled **2× amplification** above the local
threshold for the Washington group (Webb et al. 2025). *Uncertainty: high, and it cuts downward.* The
effect is real as a gain and near-zero as an ordering variable within the flood season, because the
switch is thrown by 5 November every year. **This is the factor most likely to be over-weighted by
intuition**, and the platform's current surface over-weights it.

### Tier 3 — changes what the number *means*, not what the river does

**7. Channel conveyance state (the rating's vintage).** −9 to −11 % at flood stage at Mount Vernon
over three decades; +0.065 to +0.139 ft/decade at Ferndale; ±0.68 ft residual scatter against 2 ft
NWS category spacing. *Uncertainty: magnitude contested three ways (X1), and the scatter probably
matters more than the trend.*

**8. The reference distribution's vintage and sampling interval.** **12.8–17.4 %** of daily
observations change susceptibility band from ladder length alone; ±5.5–6.2 percentile points at 30
years against band edges 15 points apart; the p95 clamp is flat across a 2.5× flow range during the
record event. *Uncertainty: low — measured on the platform's own gauges against an explicit
permutation null.*

**9. Snowpack state.** Buffer ~30–45 mm against a 200–400 mm AR; snowmelt supplies **19–45 %** of the
water reaching the ground in a maritime ROS flood; outflow hard-capped. *Uncertainty: melt-energy
partition contested (X4); the network does not observe the generating band; and on the eve of the
record crest the statistic the platform prints (**44 %** of median SWE) understated the flood-relevant
sub-4,500 ft anomaly (**14 %**) by a factor of three — misleading in the direction of calm.*

### Tier 4 — real, documented, and not movers of the main-stem flood peak

**10. Coastal water level.** The dependence is genuine (ρ = +0.30 to +0.39 against Seattle skew surge
at −1 day; a p90 surge is 1.9–2.5× more likely given Q ≥ p95) but Puget Sound surge is small — **zero
tidal cycles above 3.0 ft in 30 years** — and transmission is 1–2 % at Mount Vernon and Ferndale.
Material at **Snohomish at Snohomish only** (0.83 ft/ft, ~11 ft diurnal swing at a gauge whose flood
stage is 25 ft), where `trend.py` and `headroom.py` will produce nonsense today. *The tail's absence
from the record is not evidence of its absence from the future.*

**11. Forest harvest, roads, impervious area.** Largest effects are on the *smallest* storms;
undetectable beyond ~6-year return periods; smaller than interannual variability at basin scale —
contested in method (X7) but with both camps' practical recommendation coinciding. Roads are the one
real mechanism (**+21–50 %** drainage density, >57 % of road length draining to streams) and it does
not scale to the basin.

**12. Acute geomorphic hazards.** Lahars, jökulhlaups, landslide dams, post-fire debris flows: real,
documented for these exact valleys, and **mostly not coincident with the flood season** (C1's
exception). Oso fully impounded the North Fork Stillaguamish and **overtopped within 25 hours**, with
downstream aggradation of ~1 m over 0.5 km that peaked within a month. An authority owns each product;
the platform links rather than models.

**13. Century-scale climate projection.** Not admissible operationally, by the platform's own rules.

### 4.5 Where the ranking is uncertain — stated plainly

- **It is conditional on the event already being extreme, and that changes the order.** Antecedent
  state ranks 6th for *ordering the top-25 peaks* and would rank far higher for *the base rate of a
  flood occurring at all* — Webb's "convert a modest storm into a flood" framing. Both are true; they
  are different questions, and `antecedent-conditions` §4 contested #9 names the two literatures that
  license opposite emphases.
- **Factors 1–3 are not independent.** Orientation, duration and upslope IVT are three projections of
  one synoptic object, and no study in the corpus decomposes their contributions jointly for a
  Washington basin.
- **Factor 4 may deserve rank 1 and cannot currently be tested**, because rain-exposed fraction is
  uncomputable without hypsometry. Its rank rests on one Californian modelling result and one
  composite anomaly.
- **The decisive missing experiment is named independently in three domains and has never been run**:
  the interaction of antecedent state with basin QPE, *conditioned on the forcing*, so the test is
  "does state add skill given the forcing" rather than "does high flow follow high flow"
  (`runoff-generation` OQ2–3, `antecedent-conditions` OQ1 and §6.3 item 7, `atmospheric-rivers` OQ2).
  A null result for western Washington would be a genuine finding and belongs in `HYDROLOGY.md`, not
  in a drawer.
- **Two of the corpus's own original computations did not survive re-execution**
  (`cascading-hazards` §5.4's headline, `runoff-generation` §5.4's exit test). Any rank resting on a
  single original computation should be treated as provisional until re-derived.
