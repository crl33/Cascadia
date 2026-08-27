# Trend estimator selection — an independent measurement, and the tidal guard design

Computed 2026-08-27 against a **local scratch PostGIS** (`cascadia_trend_scratch`) ingested
through the platform's own USGS OGC adapter: 15-minute stage and discharge at all seven seeded
gauges for **2025-12-01 → 2025-12-15** (Event Zero, 18,814 rows) and **2026-08-12 → 2026-08-26**
(late-summer low flow, 18,788 rows). Every window uses **actual timestamps**; nothing assumes
regular spacing. The STEADY epsilons are the shipped ones (`trend.py`), unchanged — this change
does not recalibrate anything, so that the A/B is not fitted to Event Zero.

Labels per `docs/research/README.md`: **FACT** = computed this session from stored rows or a
checked-in fixture; **INFERENCE** = reasoned from those facts; **OPEN QUESTION** = unresolved.

> **Concurrency note, stated first because it changes how to read this file.** A sibling agent
> measured the same question against **production Neon** over a longer window (14,700 stage
> windows, 2025-12-01 → 2025-12-22) and wrote
> `docs/research/trend-estimator-selection-2026-08-26.md`. That work and this work were done
> independently and neither read the other's numbers before producing them. **They reach the
> same conclusion.** This file is not a replacement for it: it is a second, differently-sampled
> measurement whose value is precisely that it was independent, plus the §5 tidal-guard design
> and the §6 metadata specification that the brief asks for. Where the two differ in emphasis,
> §4.6 says so.
>
> The prototype both notes describe is one module, not two. It was written for this phase as
> `packages/hydrology/src/cascade_hydrology/trend_candidates.py` — the name the brief gave it —
> renamed to **`trend_estimators.py`** by the implementing phase — the name used
> throughout the sections below — and finally folded into **`trend.py`** beside the
> `method:rate-of-rise@1.0.0` it replaces, which is where the shipped code now lives. Read
> every `trend_estimators.X` below as `cascade_hydrology.trend.X`. That is also the name used
> throughout below. If you find it under the other name, it is the same file. `trend.py` itself
> is untouched, and nothing is wired into `assemble.py` *by this note*.

---

## 1. Verdict

**Replace the endpoint difference with Siegel's repeated median.** Theil–Sen is a close second
and either would be a large improvement; the endpoint difference and OLS are both disqualified.

| | endpoint (shipped) | OLS | Theil–Sen | **repeated median** |
|---|---|---|---|---|
| agrees with the others on a clean rising limb (§3 A) | yes, to 10 % | yes, to 3 % | reference | yes, to 6 % |
| survives a contaminated endpoint (§3 B) | **no** — 17.4 % direction changes | **no** — 9.2 % | yes — 1.7 % | **yes — 1.1 %** |
| survives an interior outlier (§3 C) | blind to it | **no** — 3.7 % | yes — 0.6 % | **yes — 1.0 %** |
| survives a held datalogger run (§3 B2) | worst | poor | good | **best, 7 of 8 cases** |
| one real observation can flip the reported direction (§3 B3) | 6.39 % | 3.58 % | 3.12 % | **2.52 %** |
| reads STEADY on a flat hydrograph (§3 E) | yes | yes | yes | **yes** |
| refuses on inadequate support (§3 D) | ladder, not estimator | same | same | same |
| removes a tide (§5) | **no** | **no** | **no** | **no** |
| cost per call, n = 25 (§4.5) | 0.3 µs | 6 µs | 46 µs | 76 µs |

The tide row is not a defect of any candidate and is the reason §5 designs a **refusal**, not a
filter. On a 2.0 ft M2 sinusoid with no river motion in it at all, the *more robust* the
estimator the *larger* the false rate it reports: endpoint 0.666, OLS 0.781, Theil–Sen 0.797,
repeated median 0.845 ft/h peak, against a 0.05 ft/h STEADY epsilon. **No estimator choice
substitutes for the guard, and the guard must not be justified by one.**

### The one case that decides it, on real data with nothing injected

`tests/fixtures/providers/usgs_ogc/trend_dec_spike_12100490.json` — WRAW1, the White River at
R Street near Auburn, a **seeded forecast point**, 2025-12-10T04:45–10:45Z, 25 regular 15-minute
samples, no gaps, Approved data, during Event Zero:

| estimator | flow slope | reads | stage slope | reads |
|---|---|---|---|---|
| **endpoint (shipped)** | **−61.7 cfs/h** | STEADY | **−0.025 ft/h** | STEADY |
| OLS | +39.8 cfs/h | STEADY | +0.015 ft/h | STEADY |
| Theil–Sen | +100.0 cfs/h | **RISING** | +0.040 ft/h | STEADY |
| **repeated median** | **+115.3 cfs/h** | **RISING** | **+0.044 ft/h** | STEADY |

The window rises from 7,850 to 8,390 cfs and then takes a short real dip in its last two
samples (10:30 = 7,090; 10:45 = 7,480). **Over the following six hours the river rose to
8,900 cfs, an average +237 cfs/h.** The robust estimators were directionally right; the shipped
one was not. No outlier was injected and no value was repaired — the endpoint estimator needs
no bad data to fail, only a last sample that is unrepresentative, which a short transient
guarantees.

---

## 2. What is being replaced, and what the doctrine already says

`packages/hydrology/src/cascade_hydrology/trend.py`:

```python
rate = (pts[-1][1] - pts[0][1]) / span_h
```

`HYDROLOGY.md` §9 already forbids this in words — *"trend never comes from the two endpoints of
a response window"* — and `research/tier0-measured-basis-2026-08-26.md` §5 licenses the
replacement without any calibration. `assemble.py:282` calls it with `window_h=6` for every
seeded forecast point on every request, and `headroom.py` gates `time_to_threshold_h` on its
`direction`, so a wrong direction does not merely mislabel a number — it decides whether a
time-to-threshold is published at all.

**Scope fence.** These estimators are for the **native-unit** observed series (ft, cfs). The
same slope applied to a day-of-year *percentile* series inherits that ladder's p95 clamp and
reads **+0 through the crest** (`tier0-measured-basis` §3): 24,976 cfs and 72,440 cfs both rank
95.0 at the Sauk, so their difference is zero by construction. Fixing the estimator does not
touch that, and shipping a percentile-space derivative before the high tail is fixed would
produce a velocity that is silent exactly when velocity matters. Brief §7 and §8 remain one
change; this is not it. `trend_estimators.PERCENTILE_SPACE_WARNING` carries the fence in code.

**Stage and discharge stay separate** throughout. Every table below reports the two bases
separately, in their own units, and nothing here converts one into the other (`HYDROLOGY.md` §9).

---

## 3. The six conditions

### Candidates

| id | definition | breakdown point | cost |
|---|---|---|---|
| `endpoint` | `(y[-1] − y[0]) / (x[-1] − x[0])` — the shipped code | **0** | O(1) |
| `ols` | least-squares slope of y on the actual hours | **0** | O(n) |
| `theil_sen` | median of all `n(n−1)/2` pairwise slopes | 1 − 1/√2 ≈ **29.3 %** | O(n²) |
| `repeated_median` | median over *i* of (median over *j≠i* of the (i,j) slope), Siegel 1982 | **50 %** | O(n² log n) |

**Why exactly this third candidate and not another.** The brief allows one more robust estimator
only with a justification. Theil–Sen's 29.3 % breakdown covers isolated spikes but not a *run*:
a frozen datalogger, an ice-affected stage, a sensor holding its last reading — the realistic
telemetry fault at a winter USGS gauge writes consecutive bad values, and eight of twenty-five is
already past 29 %. Siegel's repeated median is the standard 50 %-breakdown line fit, is four
lines of code, needs no tuning constant, and adds no dependency. That justification was written
before it was measured; §3 B2 tests it and it holds.

**Rejected without measurement, and why:** a Huber/bisquare M-estimator (needs a tuning constant
and an iteration count, both of which are calibrations this change is forbidden to make); LOESS
or any smoother (introduces a bandwidth, and a smoothed series is no longer the observed series);
a Kalman filter (a state model this platform has not earned); anything requiring `scipy` (not a
dependency of `cascade-hydrology`, and the whole prototype is stdlib).

---

### A. Clean monotonic rising limbs — the estimators must agree

Every 6 h window in December that is monotone non-decreasing with a mean rate ≥ 2 × the STEADY
epsilon, at the six seeded forecast points, hourly. **FACT.**

| gauge / basis | windows | median slope (endpoint / OLS / **T-S** / RM) | unit | median deviation from T-S |
|---|---|---|---|---|
| NKSW1 stage | 39 | 0.412 / 0.438 / **0.431** / 0.390 | ft/h | 7.6 % / 1.5 % / — / 3.6 % |
| NKSW1 flow | 41 | 1007 / 1024 / **1042** / 1040 | cfs/h | 7.3 % / 2.2 % / — / 4.5 % |
| MVEW1 stage | 74 | 0.3025 / 0.3077 / **0.3110** / 0.3175 | ft/h | 1.6 % / 0.7 % / — / 1.0 % |
| MVEW1 flow | 46 | 1508 / 1532 / **1566** / 1591 | cfs/h | 2.1 % / 0.8 % / — / 1.1 % |
| CRNW1 stage | 40 | 0.3375 / 0.3559 / **0.3294** / 0.3327 | ft/h | 5.9 % / 1.9 % / — / 3.5 % |
| AUBW1 stage | 49 | 0.1733 / 0.1682 / **0.1647** / 0.1600 | ft/h | 5.6 % / 1.2 % / — / 3.4 % |
| AUBW1 flow | 39 | 193.3 / 200.1 / **200.0** / 210.0 | cfs/h | 10.1 % / 2.8 % / — / 6.3 % |

**Direction is stable: every estimator reads `rising` in every one of these windows, on both
bases.** Units are `<basis unit>/h` throughout and are never mixed. The endpoint estimator's
*median* deviation is tolerable (1.6–10.1 %) but its *maximum* is not: 162.9 % at AUBW1 flow,
40.9 % at AUBW1 stage — on windows that are, by construction, monotone and clean.

Two gauges (RNTW1 stage, WRAW1 stage) produced no qualifying window: their December stage rise
never sustained 2 × 0.05 ft/h over six hours. That is a property of those hydrographs, not a
failure of the test, and it is why the other conditions do not rely on this population.

**Condition A verdict: all four agree to within ~10 % on clean rising limbs.** This condition
does not discriminate, and it is not supposed to — its job is to prove that the robust
estimators do not *cost* anything on the easy case. They do not.

---

### B. A single outlier at either endpoint

Every 6 h window in December at the six seeded points, both bases, 3-hourly (1,332 windows). One
sample is displaced by ±5× and ±20× the window's own median successive difference (floored at
5 % of the window range), at each of `first`, `second`, `penultimate`, `last`. Both signs.
**FACT.**

The injected magnitudes are realistic, not cartoonish: median ×5 spike = **0.075 ft / 125 cfs**,
median ×20 = **0.30 ft / 500 cfs**; p95 ×20 = 3.6 ft / 11,000 cfs.

**Stage**, 5,312 contaminated cases per estimator per magnitude:

| estimator | ×5: median displacement | p95 | dir. changed | sign reversed | ×20: median | p95 | dir. changed | sign reversed |
|---|---|---|---|---|---|---|---|---|
| endpoint | 12.50 % | 250 % | 5.57 % | 6.74 % | **50.00 %** | 1000 % | **17.39 %** | **14.78 %** |
| OLS | 7.56 % | 176 % | 2.86 % | 4.59 % | 30.23 % | 706 % | 9.19 % | 14.83 % |
| Theil–Sen | 3.61 % | 52.5 % | 1.39 % | **0.40 %** | 4.16 % | 78.3 % | 1.71 % | **0.47 %** |
| **repeated median** | **0.71 %** | **43.5 %** | **0.79 %** | 0.68 % | **1.35 %** | **54.2 %** | **1.05 %** | 0.70 % |

**Flow**, 5,240 cases: the same shape — endpoint 50.0 % median displacement, **26.60 %**
direction changes and 14.27 % sign reversals at ×20; repeated median 1.80 %, 2.54 %, 0.61 %.

This is the condition the brief names as *"precisely how the endpoint method fails"*, and it
does: **one displaced sample at an endpoint changes what the platform says about the direction
of the river in one window in six on stage and one in four on flow**, and reverses the sign of
the rate in one in seven. Both robust candidates cut that by an order of magnitude. OLS does
not: its breakdown point is zero and an endpoint has maximum leverage.

#### B2. A held datalogger run (the fault Theil–Sen is not built for)

The last (or first) 25 % / 40 % of the window is replaced by a repeat of the adjacent value.
Error is reported **in STEADY epsilons**, because an error under 1.0 epsilon cannot change what
the surface says. 3,972 windows per season. **FACT.**

| December, 40 % held at the tail | median error (eps) | p95 (eps) | direction changed |
|---|---|---|---|
| endpoint | 0.315 | 2.600 | 14.38 % |
| OLS | 0.277 | 2.364 | 12.99 % |
| Theil–Sen | 0.297 | 2.292 | 13.77 % |
| **repeated median** | **0.233** | **2.035** | **12.31 %** |

Repeated median is best on median error in **8 of 8** configurations tested (two seasons × two
run lengths × head/tail) and best on direction changes in **6 of 8**. Theil–Sen is *worse than
OLS* on the 40 % run — exactly the 29.3 %-breakdown prediction, measured. This is the axis on
which the third candidate earns its place, and it is the axis on which repeated median wins.

#### B3. What one *real* observation can do — no injection, no assumed ground truth

For every 6 h window at the six seeded points, both bases, both seasons (3,972 windows each),
each observation is removed in turn and the estimate recomputed. This asks a question with no
modelling assumptions in it: *how far can one real observation move this answer?* **FACT.**

| December (Event Zero) | median max influence | p90 | p99 | direction flippable | sign flippable |
|---|---|---|---|---|---|
| endpoint | 10.56 % | 100.0 % | 543.5 % | **6.39 %** | **4.10 %** |
| OLS | 6.78 % | 45.4 % | 321.9 % | 3.58 % | 3.30 % |
| Theil–Sen | 6.25 % | 28.9 % | 113.8 % | 3.12 % | **0.20 %** |
| **repeated median** | **4.76 %** | 29.4 % | **146.7 %** | **2.52 %** | 0.53 % |

| August (low flow) | median | p90 | p99 | direction flippable | sign flippable |
|---|---|---|---|---|---|
| endpoint | 16.52 % | 100.0 % | 256.5 % | 5.36 % | 1.51 % |
| OLS | 14.59 % | 83.9 % | 760.9 % | 2.37 % | 4.76 % |
| Theil–Sen | 10.00 % | 65.5 % | 133.3 % | **2.06 %** | **0.00 %** |
| **repeated median** | **7.94 %** | 100.0 % | **114.3 %** | 2.17 % | 0.05 % |

**Honesty about the sign-flip column, which is the one place Theil–Sen beats repeated median.**
Restricting to the windows the platform would actually *report* as moving (direction ≠ steady),
**no single real observation flips any estimator from `rising` to `falling` or back**, in either
season, for any of the four. The realized failure mode on this archive is `rising → steady`, and
there the ordering is the usual one: December, of 1,642 endpoint-reported moving windows,
**7.67 %** could be silenced by removing one observation; Theil–Sen 3.93 %, repeated median
**2.83 %**. In August the endpoint estimator's reported motion is one observation away from
STEADY in **32.51 %** of cases against repeated median's 15.38 %. So the sign-reversal advantage
of Theil–Sen lands entirely on windows already reported STEADY, where it changes nothing, and it
does not decide the choice.

---

### C. An interior outlier

Same injection, at `q1`, `mid`, `q3`. 3,984 stage cases per magnitude. **FACT.**

| estimator | ×20: median displacement | p95 | dir. changed | sign reversed |
|---|---|---|---|---|
| endpoint | **0.00 %** | 0.00 % | **0.00 %** | 0.00 % |
| OLS | 11.14 % | 260.9 % | 3.71 % | 5.62 % |
| Theil–Sen | 0.88 % | 24.9 % | **0.58 %** | **0.03 %** |
| repeated median | 1.40 % | 43.1 % | 0.95 % | 0.50 % |

**The endpoint estimator's perfect score here is the defect, not a defence.** It scores 0.00 %
because it never looks at the interior of the window at all — the same blindness that produces
its 17.39 % in condition B, and the same blindness that made it read STEADY at WRAW1 while the
river climbed 1,420 cfs. An evaluation that injected *only* interior outliers would have
crowned the shipped code. That is worth recording as a methodological trap, not just avoided.

OLS is the real news here: an interior outlier at the quartiles has real leverage and OLS moves
11.1 % and reverses sign in 5.62 % of cases — **worse than the estimator it would replace, on
this fault.** OLS is not a robust estimator and must not be adopted as one.

---

### D. Missing observations and irregular cadence

**FACT — the archived record is far more regular than one might assume, and the exceptions are
real and few.** Across 37,602 rows: zero duplicate timestamps, all `revision_seq = 0`, median
gap exactly 15 min. Within-season gaps over 20 min: **CRNW1** 120 min (2026-08-17) and 60 min
(2026-08-22) and a **105 min gap on 2025-12-12 during the Event Zero recession**; the **Sauk**
180 min (2026-08-12). Everything else is a clean 15-minute grid. Two of these are checked in as
fixtures.

**Never assume regular spacing — measured.** Over the 38 real windows in the two seasons whose
sample spacing is not constant, computing the OLS slope on a *nominal* 15-minute index instead
of the actual timestamps gives a median error of **35.9 %** and a maximum of **106.7 %**
(worst: the Sauk, 2026-08-12T22:00Z, 14 samples, 3.0 h maximum gap). Every estimator in
`trend_estimators.py` takes `xs` built from `(t − t₀).total_seconds()/3600`; none of them has
an index-based path.

**Refusal, not extrapolation.** The existing ladder — `< MIN_SAMPLES`, `max_gap > 2 h`,
`span < 0.5 × window` — does the work, and it is the ladder rather than the estimator that
protects the answer. Random decimation of December windows (20 draws each, 6,720 draws per
level), all six points, both bases:

| dropped | refused | which refusal | median rel. error of the answers that survive (endpt / OLS / T-S / RM) |
|---|---|---|---|
| 20 % | 0.0 % | — | 0.00 / 2.96 / 3.03 / 3.73 % |
| 50 % | 3.0 % | 197 gap, 6 span | 4.55 / 6.59 / 7.07 / 8.12 % |
| 70 % | 27.8 % | 1,548 gap, 271 span, 51 too-few | 11.04 / 10.89 / **10.28** / 12.20 % |
| 85 % | **73.5 %** | 2,342 gap, 907 span, 1,693 too-few | 18.10 / 15.93 / **14.29** / 15.61 % |

At the levels that matter operationally the estimators are indistinguishable (a few percent),
and at severe decimation the robust ones are slightly *better*. **The estimator is not what
makes sparse data safe; the refusal ladder is.**

**One change to the ladder is proposed on evidence: `MIN_SAMPLES` 2 → 3.** With exactly two
points all four estimators are algebraically identical to the endpoint difference, so a
two-point answer would silently reinstate the defect this change removes. At 85 % decimation
**1,045 of 6,720 draws** landed on exactly two points. Three is the smallest count at which the
choice of estimator means anything. This is not a calibration — it is the arity below which the
method is not the method.

**Two real fixtures pin the two sides of the ladder.** `trend_dec_gap_12149000.json`: CRNW1
flow, 14 samples where 25 are nominal, spacing 15–105 min, inside the 2 h tolerance — the method
must **answer**, from actual timestamps (endpoint −2683, OLS −2253, T-S −2400, RM −2445 cfs/h;
stage over the same window is complete at 25 and gives −0.172/−0.167/−0.165/−0.190 ft/h).
`trend_aug_irregular_12189500.json`: the Sauk, 14 samples, a real 3.0 h gap — the method must
**refuse**, `GAP_EXCEEDS_TOLERANCE`, on both bases. Both behaviours were confirmed end-to-end
through `estimate_trend`: CRNW1 flow answers −2445 cfs/h carrying `quality = SPARSE_SUPPORT`
(14 samples where the 6 h span implies 24) while CRNW1 stage over the identical window answers
−0.190 ft/h with `quality = OK`, and the Sauk returns `slope = None`, `direction = "unknown"`,
`refusal.reason = "GAP_EXCEEDS_TOLERANCE"` on stage and flow alike. **The same window is
answerable on one basis and sparse on the other, which is why the support condition is recorded
per estimate rather than per station.**

---

### E. Flat hydrographs

331 hourly 6 h windows per gauge per basis over the August low-flow fortnight. **FACT.**

**Stage: all four estimators read STEADY in 100 % of windows at all six seeded points.** The p95
of |slope| ranges 0.0033–0.0300 ft/h against the 0.05 ft/h epsilon; median 0.000–0.0133. There
is no noise-driven RISING or FALLING on stage, for any candidate.

**Flow reads non-STEADY at some gauges — and it is right to.** WRAW1 41.1 % (Theil–Sen),
NKSW1 19.6 %, RNTW1 7.6 %, CRNW1 3.9 %, AUBW1 3.0 %, MVEW1 0.0 %. The estimator choice barely
moves these (endpoint 45.0 % vs Theil–Sen 41.1 % at WRAW1) — so this condition does not
discriminate between estimators either. It discriminates something else, and the discriminator
is decisive: **the readings are phase-locked to the solar day.** At WRAW1 the Theil–Sen
direction over the fortnight is `rising` in 9–10 of 14 days at 11–13 Z and `falling` in 9–10 of
14 days at 17–20 Z, `steady` overnight; at NKSW1 `rising` in 9–11 of 14 days at 15–19 Z and
never `falling` at any hour. That is a diurnal melt/regulation cycle on a real hydrograph, not
estimator noise. Condition E is **passed by all four**: nothing here is reading noise as motion.

**What it does surface, honestly, is the flow epsilon.** `steady_epsilon` returns
`max(1.0, 0.01 × |value|)` per hour, so at WRAW1's ~566 cfs August median the threshold is
5.7 cfs/h and a genuine diurnal swing of 4–17 cfs/h crosses it. Whether a real 1 %/h diurnal
oscillation *should* be surfaced as RISING is a product question, not an estimator question.
**No change is proposed here and none is licensed.** The evidence that would justify one: the
measured amplitude and phase stability of the diurnal cycle at each seeded gauge across at least
two melt seasons, and a demonstration that suppressing it does not also suppress the first hours
of a real rise — measured on Event Zero, where the WRAW1 rise begins during the same hours of
day the melt cycle occupies. Until that exists, the epsilon stays where it is.

---

### F. The real Event Zero rising limbs at the six seeded gauges

**F1 — the steepest 6 h window at each gauge.** Theil–Sen's maximum over December, both bases,
all 25 samples unless noted. **FACT.**

| gauge | basis | window end (Z) | endpoint | OLS | **Theil–Sen** | RM | unit | endpoint vs T-S |
|---|---|---|---|---|---|---|---|---|
| NKSW1 | stage | 12-09 13:00 | 0.920 | 1.007 | **1.013** | 1.045 | ft/h | **−9.2 %** |
| NKSW1 | flow | 12-09 13:00 | 1625 | 1754 | **1800** | 1849 | cfs/h | **−9.7 %** |
| MVEW1 | stage | 12-11 23:00 | 0.4967 | 0.4925 | **0.4900** | 0.4890 | ft/h | +1.4 % |
| MVEW1 | flow | 12-12 00:00 | 3600 | 3676 | **3692** | 4000 | cfs/h | −2.5 % |
| CRNW1 | stage | 12-09 09:00 | 0.6417 | 0.7022 | **0.7030** | 0.7213 | ft/h | **−8.7 %** |
| CRNW1 | flow | 12-11 08:00 (n=20) | 5783 | 6099 | **6000** | 6092 | cfs/h | −3.6 % |
| RNTW1 | stage | 12-11 21:00 | 0.2517 | 0.2278 | **0.2400** | 0.2516 | ft/h | +4.9 % |
| RNTW1 | flow | 12-11 21:00 | 418.3 | 369.4 | **395.0** | 405.6 | cfs/h | +5.9 % |
| AUBW1 | stage | 12-08 06:00 | 0.3117 | 0.3434 | **0.3516** | 0.3618 | ft/h | **−11.3 %** |
| AUBW1 | flow | 12-08 06:00 | 301.7 | 333.4 | **340.0** | 352.7 | cfs/h | **−11.3 %** |
| WRAW1 | stage | 12-09 09:00 | 0.2050 | 0.2462 | **0.2463** | 0.2573 | ft/h | **−16.8 %** |
| WRAW1 | flow | 12-09 10:00 | 441.7 | 506.5 | **518.9** | 539.5 | cfs/h | **−14.9 %** |

**The endpoint estimator under-reads the rate of rise in 9 of these 12 cases, by up to 16.8 %.**
That is the operationally worse direction of error: `headroom.py` divides headroom by the rate,
so an under-read rate makes the platform report that a threshold is *further away in time than
it is*, at exactly the hour the limb is steepest.

**F2 — and time-to-threshold does not separate the estimators, which is worth saying plainly.**
For every hourly window below each point's official **minor** threshold and within 48 h of the
true first crossing (288 windows; datums verified equal between observation and threshold at all
four stage points, and the two flow points are flow-defined), `headroom ÷ rate` was compared to
the truth in the record:

| estimator | answered | refused (not rising) | median abs error | p90 |
|---|---|---|---|---|
| endpoint | 154 | 46.5 % | **7.76 h** | 33.7 h |
| OLS | 149 | 48.3 % | 8.96 h | 35.4 h |
| Theil–Sen | 144 | 50.0 % | 9.14 h | 37.1 h |
| repeated median | 137 | 52.4 % | 9.33 h | 40.3 h |

A 1.6 h spread across a 7.8–9.3 h median error. **Time-to-threshold error is dominated by the
nonlinearity of the rising limb, not by the estimator**, which is precisely what `HYDROLOGY.md`
§9 says when it calls it *"an indicator, not a prediction"* — now with a number attached. The
shipped estimator's nominal 1.4 h edge here is not evidence for it; it is evidence that this
metric cannot adjudicate estimators, and it is reported because leaving it out would have made
the case look cleaner than it is.

**The case for the change is therefore not accuracy on clean data.** All four agree there (§3 A,
§3 F1). It is the absence of catastrophic failure on data that is not clean — §3 B, §3 B2,
§3 B3, and the WRAW1 window in §1.

---

## 4. The choice

### 4.1 Rejected: the endpoint difference (shipped)

Breakdown point 0 at the two positions with maximum leverage. 17.4 % (stage) / 26.6 % (flow)
direction changes under a single ×20 endpoint spike; 6.39 % of real Event Zero windows have a
direction one observation could flip; under-reads the steepest rise in 9 of 12 real cases by up
to 16.8 %; and produced a directionally wrong answer on a real, uninjected, Approved window at a
seeded forecast point during the event the platform exists for. Forbidden by `HYDROLOGY.md` §9
in words already.

### 4.2 Rejected: ordinary least squares

Efficient under Gaussian noise, O(n), trivially auditable — and breakdown point **0**. Measured:
9.2 % direction changes on an endpoint spike, and **worse than the shipped estimator on an
interior outlier** (11.1 % median displacement, 5.62 % sign reversals, against 0.00 %). Its
worst real-data figure is the August p99 leave-one-out influence of **760.9 %**, the largest
number in that table. It replaces one zero-breakdown estimator with another and buys only the
first two decimal places on data that is already clean. It is in the module as the measured
counter-example, not as a candidate.

### 4.3 Runner-up: Theil–Sen

Wins the sign-reversal column outright (0.20 % / 0.00 % real-data flippability) and has the
tightest tail on maximum influence (p99 113.8 % December). Costs 40 % less than the repeated
median. It loses on the held-run fault by construction — 29.3 % breakdown against a fault that
writes 25–40 % of the window — and on that fault it was measured *worse than OLS*. If the cost
in §4.5 ever becomes real, this is the estimator to fall back to, and the fallback costs
approximately one percentage point of direction-flip robustness.

### 4.4 Chosen: Siegel's repeated median

Best or tied-best on median displacement under an endpoint spike (0.71 % / 1.35 %), on direction
changes under an endpoint spike (0.79 % / 1.05 %), on held runs (8 of 8 on median error), and on
real-data leave-one-out influence and direction-flippability (4.76 % median, 2.52 % flippable).
50 % breakdown means no realistic single-window telemetry fault defeats it. Four lines, no tuning
constant, no dependency, stdlib.

Its one loss — the sign-reversal column — was shown in §3 B3 to land entirely on windows already
reported STEADY, where the sign of a sub-epsilon rate is not published and changes nothing.

### 4.5 The cost, measured, since this runs per forecast point per request

Median of ≥ 500 repetitions, Python 3.14, this machine (`time.perf_counter`).

| n (window) | shipped `rate_of_rise` | full `estimate_trend` with endpoint | with OLS | with Theil–Sen | **with repeated median** |
|---|---|---|---|---|---|
| 25 (6 h @ 15 min — **the live case**) | 18.2 µs | 100.2 µs | 110.5 µs | 149.7 µs | **183.9 µs** |
| 49 (6 h @ 7.5 min) | 30.5 µs | 286.8 µs | 297.7 µs | 499.7 µs | 664.8 µs |
| 97 (24 h @ 15 min) | 80.3 µs | 1082.6 µs | 991.1 µs | 2202.5 µs | 2388.8 µs |

Bare estimator cost at n = 25: endpoint 0.28 µs, OLS 6.2 µs, Theil–Sen 46.1 µs, repeated median
76.2 µs; `pairwise_slope_spread` a further 54.4 µs. **Six seeded forecast points × 183.9 µs =
1.1 ms per request**, against a `/viz/basins` budget currently dominated by 13 SQL round trips
(`docs/PERFORMANCE.md`). It does not need to move to `derived_feature` at ingest.

Two implementation notes for the next phase, both measured: (a) the envelope, not the estimator,
dominates — the sort, dedup and gap ladder cost ~100 µs of the 184; (b) Theil–Sen and the pair
spread should share **one** pair array — computed together that is 48.5 µs at n = 25 instead of
46.1 + 54.4 = 100.5 µs. The repeated median cannot share it (its inner medians are per-i), so
`RM + spread` is 138.1 µs; publishing the spread beside a repeated-median slope means paying for
both, and it is still under 1 ms for all six points. (c) **The O(n²) is a real constraint at a
24 h window**: 2.4 ms per point, 14 ms for six. If a 24 h trend is ever wanted, measure it again
before shipping it at read time.

### 4.6 Where this measurement and the sibling measurement differ

Both choose the repeated median; neither reads the other's numbers into its own tables.

- **Sample.** Theirs: production Neon, 2025-12-01 → 2025-12-22, 14,700 stage / 14,684 flow
  windows, seven gauges. Mine: a local scratch ingest, 2025-12-01 → 2025-12-15 **plus**
  2026-08-12 → 2026-08-26, 3,972 windows per estimator per season per basis. Theirs is the
  larger December sample; mine is the only one that carries a low-flow season, which is what
  condition E needs.
- **Magnitude of the endpoint-spike result.** Theirs: 45.69 STEADY epsilons and **78 %** direction
  changes. Mine: 17.4 % (stage) / 26.6 % (flow) at ×20. The gap is the injection magnitude, not a
  disagreement — theirs injects a fixed large fault, mine scales the spike to each window's own
  successive-difference scale, which is smaller on a steep limb. Both conclusions are the same
  and neither figure should be quoted without its injection model.
- **What only this file has.** The uninjected real WRAW1 sign-disagreement (§1), the leave-one-out
  influence study (§3 B3), the diurnal-phase explanation of the flow non-STEADY readings (§3 E),
  the time-to-threshold null result (§3 F2), the six checked-in offline fixtures, the tidal-guard
  design (§5) and the metadata specification (§6).
- **What only theirs has.** The 14,700-window jitter table (change in the reported rate between
  consecutive 15-minute updates) and a two-spike fault I did not run.

**OPEN QUESTION.** Neither measurement covers more than one flood. The multi-event validation of
brief §18 is still owed, and neither file licenses a "RAPIDLY RISING" band or any cutoff.

---

## 5. The tidal guard — a refusal, not a de-tiding subsystem

### 5.1 What the evidence licenses, and what it forbids

`research/tidal-gauge-verification-2026-08-26.md` settled this by measurement: **no seeded
forecast point is tidally affected.** Whole-window harmonic M2 amplitude ≤ **0.008 ft** at all
six (MVEW1 0.0077, CRNW1 0.0057, WRAW1 0.0036, RNTW1 0.0012, NKSW1 0.0006, AUBW1 0.0005) against
a coastal M2 of 2.26–3.36 ft, and the tidally-injected false 6 h rate is ≤ **0.025 ft/h**, half
the STEADY epsilon. **Building a de-tiding subsystem would be building a fix for a defect that
does not exist in anything the platform serves.** It is forbidden here.

What *is* licensed is the machinery that stops a wrong number the day a tidal gauge is seeded —
SNAW1 (12155500) is the plausible next one (M2 2.97 ft at low flow, 96.7 % of low-flow 6 h
rate-of-rise samples spuriously non-STEADY, up to 1.44 ft/h) and `EVENT_ZERO.md` T8 already
names it.

### 5.2 No estimator removes a tide — measured, so the guard cannot be argued away

A pure M2 sinusoid (T = 12.4206 h), no river motion at all, 6 h window, 15-minute cadence,
swept over 50 phases covering a full tidal cycle. **FACT.**

| amplitude | endpoint | OLS | Theil–Sen | repeated median |
|---|---|---|---|---|
| **A = 2.0 ft** (a tidal gauge) — peak false rate | 0.666 | 0.781 | 0.797 | **0.845 ft/h** |
| — median false rate | 0.469 | 0.550 | 0.617 | 0.711 ft/h |
| — % of phases exceeding the 0.05 ft/h epsilon | 94 % | 96 % | 96 % | **98 %** |
| **A = 0.008 ft** (the measured seeded maximum) — peak | 0.0027 | 0.0031 | 0.0032 | 0.0034 ft/h |
| — % of phases exceeding the epsilon | 0 % | 0 % | 0 % | **0 %** |

**The chosen estimator is the worst of the four on a tide.** Robustness is resistance to a
*minority* of discrepant points; a tide is not a minority, it is the whole signal, and a
half-tidal-cycle is 6.2 h so widening the window does not average it away (closed form:
`2A·|sin(πW/T)|/W`, ≈ 0.333 A at W = 6 h). This table is the argument that the guard must be a
refusal keyed on station physics and must never be replaced by "use a robust estimator".

The same table is the argument the guard is not needed today: at the measured seeded maximum,
every estimator is two orders of magnitude below the epsilon.

### 5.3 The design

**A per-station marker, and a method-level refusal that fails closed.** Prototyped in
`trend_estimators.py` as `TidalClass` + `tidal_refusal`.

```
TidalClass = FLUVIAL | TIDAL | UNVERIFIED     (and the field may be absent)

tidal_refusal(FLUVIAL)              -> None                       (compute normally)
tidal_refusal(TIDAL)                -> TIDAL_CONTAMINATION        (UNKNOWN + reason)
tidal_refusal(UNVERIFIED) / absent  -> TIDAL_CLASS_UNVERIFIED     (UNKNOWN + reason)
```

Five properties, each of which the brief asks for or the evidence forces:

1. **It is keyed on an explicit marker, not on the data.** A guard that inspected the series
   could be talked out of firing by the series — a flood damps tidal transmission by 3× at
   SNAW1 (0.75–0.92 → 0.22–0.32 ft/ft), so a data-driven guard would be weakest during a flood.
   `tidal_refusal` runs **before** any observation is read.
2. **It fails closed.** There is no code path in which an unmarked station is treated as fluvial.
   A future tidally-affected station cannot silently bypass the guard, because seeding a station
   at all requires setting the marker, and the only value that permits a trend is one that
   asserts a measurement. This is the brief's central requirement and it costs one enum.
3. **`FLUVIAL` is a measurement, not a default.** It may be set only from an M2 amplitude
   measured against a coastal reference with a **known non-tidal control gauge** carried through
   the identical pipeline, band-passed to 10–16 h and excluding the diurnal band
   (`tidal-gauge-verification` §3 — skipping the control makes hydrograph leakage look like a
   discovery; skipping the band-pass attributes glacier melt to the moon). All six current
   points qualify on that evidence and therefore **the guard does not fire for anything the
   platform serves today.**
4. **The reason is machine-readable and the two reasons are distinct.** `TIDAL_CONTAMINATION`
   ("we know this gauge is tidal") and `TIDAL_CLASS_UNVERIFIED` ("we do not know") are different
   operational states and a consumer must be able to tell them apart; collapsing them would hide
   a seeding gap behind a physics claim.
5. **It is basis-independent and it propagates.** The tidal wave contaminates stage and discharge
   alike, and because `headroom.py` gates `time_to_threshold_h` on `direction == RISING`, a
   refused trend automatically refuses the time-to-threshold that would otherwise announce
   "five hours to flood stage on a falling river, twice a day, forever"
   (`tidal-gauge-verification` §5.4).

**Where the marker lives (for the implementing phase, not decided here).** It belongs on the
station, beside the datum, as station physics — `stations.json` seed → a `station.tidal_class`
column → read through `as_known_at`. It must carry its evidence with it, as a class and never a
scalar: the low-flow coefficient, the flood coefficient, the phase lag, the estimator, the
window, and the control gauge used to fix the noise floor (`HYDROLOGY.md`, corrected 2026-08-26:
SNAW1's own coefficient moves 3× between regimes and 25 % between estimators within a regime).

**Not built, and deliberately:** any de-tiding filter, any harmonic decomposition at read time,
any runtime tidal detector, any inference of tidal class from the data. If SNAW1 is seeded, the
platform reports UNKNOWN for its trend with `TIDAL_CONTAMINATION` — which is the honest answer
until someone does the work — and a de-tiding method would then be a new, separately-evidenced
method version, not a patch to this one.

### 5.4 The synthetic series that must prove the guard fires

Three tests, and the third is the one that matters most.

**T1 — the guard fires on a tide-dominated station.** Series: 6 h, 15-minute cadence, 25 samples,
`v(t) = 12.0 + 2.0·sin(2π(t + φ)/12.4206)` ft on a `stage` basis, no river trend, swept over
`φ ∈ {0, 0.25, …, 12.25} h` (50 phases, a full tidal cycle). Station marker `TidalClass.TIDAL`.

*Assert:* every phase returns `refusal.reason == "TIDAL_CONTAMINATION"`, `slope is None`,
`direction == "unknown"`, and `n == 0` — the guard refused before reading any observation.

**T2 — what the guard is preventing, on the identical series.** Same 50 phases, marker
`TidalClass.FLUVIAL` (a marker that lies).

*Assert:* `direction != "steady"` in **at least 45 of 50 phases** and `max |slope| > 0.5 ft/h`
for the chosen estimator — the measured figures are 98 % of phases and 0.845 ft/h peak (§5.2).
This test exists so that a future reader cannot conclude the guard is decorative, and it fails
loudly if someone ever "fixes" the estimator into hiding a tide.

**T3 — the guard does not fire for the current six, and neither does the tide.** Two parts:

- *Marker:* for each of the six seeded points with its measured `FLUVIAL` marker,
  `tidal_refusal` returns `None`. A regression that made `FLUVIAL` refuse would silently blank
  every trend the platform serves.
- *Physics:* the same synthetic series at **A = 0.008 ft** — the measured seeded maximum, at
  MVEW1 — superimposed on a real flat window from
  `tests/fixtures/providers/usgs_ogc/trend_aug_flat_12213100.json`. *Assert:* the direction is
  unchanged from the un-superimposed window at every phase, and `|slope_with_tide − slope| <
  0.005 ft/h` (measured peak injected rate 0.0034 ft/h, against the 0.05 ft/h epsilon). This is
  the test that would fail first if someone tightened the STEADY epsilon by an order of magnitude
  without re-measuring the tide, and it ties the guard's inapplicability to a number rather than
  to a memory.

All three are deterministic, offline, and need no provider. **T2 must be written to fail if the
estimator is changed to suppress a tide**, because suppressing it silently is the outcome the
guard exists to prevent.

**All three were run against the prototype before this note was written, and pass** (FACT,
`estimate_trend(..., estimator="repeated_median")`):

| test | asserted | measured |
|---|---|---|
| T1 | all 50 phases refuse `TIDAL_CONTAMINATION`, `slope is None`, `n == 0` | **50/50**, `slope=None`, `direction="unknown"`, `n=0` |
| T1b | absent marker and `UNVERIFIED` both refuse `TIDAL_CLASS_UNVERIFIED` | both, verbatim |
| T2 | >= 45/50 phases non-STEADY, peak abs(slope) > 0.5 ft/h | **49/50**, peak **0.8452 ft/h** (16.9x the epsilon) |
| T3a | `FLUVIAL` never refuses | no refusal, on the real fixture window and on the synthetic |
| T3b | A = 0.008 ft tide on a real flat window: abs(delta slope) < 0.005 ft/h, direction unchanged | **0.003399 ft/h**, direction unchanged at **50/50** phases |

The T3b base window is `trend_aug_flat_12213100.json` (NKSW1 stage, −0.0139 ft/h, STEADY); the
measured seeded maximum tide moves it by a quarter of one percent of the STEADY epsilon.

---

## 6. What a trend must carry

Prototyped as `trend_estimators.TrendEstimate`. Every field answers the one rule — *where did it
come from, when, from which version, how stale, what transformed it.*

| field | why it must be there |
|---|---|
| `method_id` | `method:rate-of-rise@2.0.0`. A **major** bump: the mathematics changed, not a parameter. Two stored trends computed by different estimators must be distinguishable without reading code. |
| `estimator` | `repeated_median` \| `theil_sen` \| `ols` \| `endpoint`. The method id pins the contract; this pins which candidate produced the number, so a future A/B does not need a new method id per arm. |
| `basis` + `slope_unit` | `stage`/`flow` and `ft/h`/`cfs/h`. Kept separate, never converted (`HYDROLOGY.md` §9). A slope with no basis is not interpretable and a slope with the wrong unit is worse than none. |
| `window_h` | the window **requested** (a named window: 1, 3 or 6 h). |
| `span_h` | the **actual** first-to-last span, which is ≤ `window_h`. These are different numbers and conflating them is how a 45-minute sample becomes a "6-hour trend". |
| `n` | sample count actually used, after sentinel and duplicate removal. |
| `max_gap_h` | the largest gap inside the window. Publishing it is what lets a reader see *why* a borderline answer is borderline without re-deriving it. |
| `first_valid_time`, `last_valid_time` | the **valid time** of the estimate is `last_valid_time`, not the request clock. Distinct from `window_end`, which is the caller's knowledge-time `as_of`. |
| `window_end` | the trailing edge asked for; with `available_at <= as_of` upstream this is what makes a replay reproducible. |
| `slope` | `None` whenever `refusal` is set. Never a number and a refusal together. |
| `direction` + `steady_eps` | the label **and** the epsilon it was decided against — otherwise `steady` is unfalsifiable. |
| `slope_q25`, `slope_q75` | interquartile range of the pairwise slopes: how much the sub-intervals of the window disagree. **A dispersion, not a confidence interval and not a probability.** |
| `quality` | `OK` \| `SPARSE_SUPPORT` \| `WIDE_SLOPE_SPREAD` — a *condition*, attached to an answered estimate. Never a score, never a weight, never combined with anything. |
| `refusal.reason` | machine-readable: `INSUFFICIENT_OBSERVATIONS`, `GAP_EXCEEDS_TOLERANCE`, `SPAN_BELOW_MINIMUM`, `TIDAL_CONTAMINATION`, `TIDAL_CLASS_UNVERIFIED`. Prose beside it, never instead of it. |
| `tidal_class` | the marker the guard consulted — so a reader can see the guard ran and what it saw. |
| `station_id`, `input_product_ids`, `input_revision_seqs`, `input_quality_flags`, `raw_artifact_ids` | input provenance: which station, which product, which revisions, which quality flags (`provisional`, `estimated`, `backfilled`, `approved`), and the archived bytes each value came from. |

**Two things deliberately absent.** There is no confidence *probability* and no numeric
confidence score: the honest uncertainty statement available at zero cost is the pair-slope IQR,
in the slope's own units, and dressing it as a probability would be a fabrication. And there is
no composite of the trend with anything else — the rate is published as an independently
interpretable driver or not at all.

**A rule that was measured, then rejected.** Requiring the whole pair-slope IQR to clear the
epsilon before publishing a direction sounds prudent. Measured: on 1,986 August flat windows
Theil–Sen never reads non-STEADY at all, so the rule suppresses **nothing** there; on 1,986
December windows it would suppress **21.5 %** of non-STEADY readings, during Event Zero. A rule
with no measured benefit and a measured cost is not adopted. The spread is **published** as a
label; it does not **gate**.

---

## 7. What the implementing phase must not do

- Do not wire this in without deleting the endpoint path. Two live estimators is two answers.
- Do not apply any of these estimators to a percentile series (§2).
- Do not add a "RAPIDLY RISING" band, a cutoff, or a weighting. `tier0-measured-basis` §5 is
  explicit that nothing licenses one, and neither does this file.
- Do not recalibrate `STAGE_STEADY_EPS_FT_PER_H` or `FLOW_STEADY_FRACTION_PER_H` in the same
  change. §3 E records what a re-measurement would have to show first.
- Do not resolve **X8** (ladder vintage) here. It is the one operationally blocking
  contradiction and it is not this change's to settle.
- Do not let `FLUVIAL` become a default (§5.3 property 2).

---

## 8. Reproducing this

**Offline, from the repository** — every number in §1, §3 D, §3 E's fixture rows and §3 F1's
NKSW1 and MVEW1 rows recomputes from six checked-in captures with no network:

```
tests/fixtures/providers/usgs_ogc/trend_dec_rising_12213100.json    # A, F  steepest NKSW1 rise
tests/fixtures/providers/usgs_ogc/trend_dec_rising_12200500.json    # A     the estimators agree
tests/fixtures/providers/usgs_ogc/trend_dec_spike_12100490.json     # B, C  the decisive case
tests/fixtures/providers/usgs_ogc/trend_dec_gap_12149000.json       # D     a real 105-min gap
tests/fixtures/providers/usgs_ogc/trend_aug_flat_12213100.json      # E     flat, low flow
tests/fixtures/providers/usgs_ogc/trend_aug_irregular_12189500.json # D     a real 3 h gap
```

Each carries its url, `captured_at`, byte count, sha256 and its role in
`tests/fixtures/providers/usgs_ogc/manifest.yaml`. Parse features with `statistic_id == "00011"`,
map `parameter_code` 00065 → stage/ft and 00060 → flow/cfs, build `xs` from the actual `time`
values, and call `cascade_hydrology.trend_estimators`.

**The full population** (§3 A, B, B2, B3, C, D, E, F) needs the two-season ingest:

```bash
docker exec cascadia-pg psql -U postgres -c "CREATE DATABASE cascadia_trend_scratch;"
export CASCADE_DB_URL="postgresql+psycopg://postgres:dev@127.0.0.1:5433/cascadia_trend_scratch"
export CASCADE_ALEMBIC_URL="$CASCADE_DB_URL"
bash scripts/migrate.sh && python -m cascade_worker seed
python scripts/backfill_event_zero_usgs.py --start 2025-12-01T00:00:00Z --end 2025-12-15T00:00:00Z
python scripts/backfill_event_zero_usgs.py --start 2026-08-12T00:00:00Z --end 2026-08-26T00:00:00Z
# 18,814 + 18,788 rows across the seven seeded gauges, stage and flow
docker exec cascadia-pg psql -U postgres -c "DROP DATABASE cascadia_trend_scratch;"
```

Official thresholds for §3 F2 come from `cascade_providers_nwps.jobs.run_fetch_thresholds`
(re-fetched 2026-08-27): NKSW1 minor 18.0 ft NAVD88, MVEW1 28.0 ft NGVD29, CRNW1 54.0 ft NAVD88,
RNTW1 13.0 ft NGVD29, AUBW1 9,000 cfs, WRAW1 7,500 cfs. The stage datums were checked equal
against the stored observation datums before any headroom was computed; none was approximated.

The analysis scripts were written to the session scratchpad, not the repository, because the
fixtures plus these commands reproduce every claim and a seventh one-off script would not.
