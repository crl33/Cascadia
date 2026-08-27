# High-tail selection — what the surface says above p95, and what the velocity is computed on

Decision phase for milestone brief §5 (high-tail representation) and §6 (state-change velocity).
Nothing ships in this change: `susceptibility.py` and
`method:streamflow-doy-climatology@1.0.0` are untouched, the uncalibrated band edges keep their
uncalibrated status, and **register X8 — which record vintage a ladder should be built from — is
deliberately left open.**

Every number below was computed from the **full USGS approved daily-mean record** for the six
seeded susceptibility gauges (§11 has the request and the reproduction). The candidates are
implemented in `packages/hydrology/src/cascade_hydrology/tail_candidates.py` and the headline
numbers are pinned in `tests/unit/test_tail_candidates.py`, so this document cannot drift away
from the code.

Labels per `docs/research/README.md`: **FACT** = computed for this document; **INFERENCE** =
reasoned from those facts; **OPEN QUESTION** = unresolved.

> **There is a second, independent measurement of the same question.**
> `docs/research/tail-representation-2026-08-26.md` (committed in `d2f182d`) answers it from the
> **R2-archived daily-values CSVs the deployed ladders were built from**; this document answers it
> from a **fresh fetch of the full USGS OGC `daily` record**. The two agree on the verdict and on
> the numbers where they overlap — including the WY2026 ladder contamination, to the digit at two
> gauges. **§13 reconciles them and names the one place they disagree**, which is the tail-support
> rule. Read that section before acting on either document. What this one adds beyond it: the
> peaks-over-threshold evaluation and refusal (§6), the state-change velocity specification (§8),
> ladder-point stability by bootstrap and jackknife (§4), and the false-positive character of the
> velocity (§8).

---

## 1. Verdict

| | |
|---|---|
| **Is the p95 ceiling the implementation or the record?** | **The implementation.** `PERCENTILES = (5, 10, 25, 50, 75, 90, 95)`, and `percentile_of` clamps. The record holds 15–25 approved daily means strictly above p95 in the same day-of-year window, from 7–13 distinct water years, reaching 2.0–4.6× the p95 flow (§2). Puyallup-white is the exception at every turn: 5 values from a single water year. |
| **Does continuing the empirical rank therefore fix it?** | **It fixes the level. It does not fix the velocity.** Event Zero's crest exceeded the **entire window sample** at all four demonstration basins, so every rank-shaped answer — an extended ladder point, a plotting position, an exact rank — saturates at the top of the record on exactly the days the velocity matters (§3, §5). |
| **What is chosen** | The percentile **unchanged**, plus two new fields: an **exact rank in the day-of-year window** (candidate A′) and a **seasonal high-flow multiple** `Q ÷ p95(DOY)` (candidate B). The multiple is the only candidate that is unbounded, and therefore the only one with a live derivative at a crest (§7). |
| **What the velocity is computed on** | Daily-mean **flow**, as a multiplicative growth factor `G24 = Q(t)/Q(t−24 h)`, which is algebraically the change in the multiple against a single named reference. It does not depend on the ladder at all, so **X8 cannot move it** — and X8 is not thereby resolved, because the level still depends on the ladder entirely (§8). |
| **What is refused** | Peaks-over-threshold / GPD (candidate C): not for lack of data, but because the fitted shape moves with an arbitrary threshold, its uncertainty exceeds the signal, its natural output is the return period register X6 forbids, and **it does not restore the velocity either** — a probability is bounded above by 1 the same way a percentile is bounded by 100 (§6). |

---

## 2. The ceiling is an implementation choice — established against the stored ladder and the record

`method:streamflow-doy-climatology@1.0.0` builds one ladder per day-of-year key from approved daily
means in a ±2-day window, `MIN_SAMPLE = 10`, R-type-7 interpolation between order statistics. It
stores seven breakpoints, `p05 … p95`, and `percentile_of` clamps anything beyond the outermost
breakpoint with an `outside_climatology_range` flag. **The sample it was built from is discarded.**

Rebuilding those ladders from a fresh fetch of the record reproduces the tier0 reconstruction to
the rounding — which is how the reconstruction here was validated as *being* the deployed ladder,
and it independently confirms that the R2-archived CSVs and the live record agree:

| Sauk (12189500), December 2025 | 12-04 | 12-05 | 12-06 | 12-07 | 12-08 | 12-09 | 12-11 |
|---|---|---|---|---|---|---|---|
| daily mean (cfs) | 2,358 | 2,580 | 6,537 | 7,208 | 8,359 | 24,976 | 72,440 |
| production (tier0 §2) | p22 | p27 | p81 | p85 | p89 | p95 | p95 |
| **rebuilt here** | p21.8 | p26.8 | p80.7 | p85.1 | p89.1 | p95.0 | p95.0 |

**A caveat that travels with those flows, and it does not change any conclusion.** Those daily
means are tier0's, averaged over a **UTC** day; a USGS daily mean is over the station's **local**
day, and tier0 has since been corrected in place for it. The published local-day value for the Sauk
on 2025-12-11 is **62,600 cfs**, against tier0's 72,440 and the sibling document's recomputed
62,808. The four demonstration pairs in §3 and §7 are the ones the brief names, so they are shown
as given; **every trajectory table in §5 and §7 uses the published local-day daily means instead**,
and the verdict is identical under either convention — because each candidate is a function of
(value, sample) and the crest exceeds the whole sample either way.

FACT — record depth and what the window actually holds, at the `12-11` key:

| gauge (site) | approved rows | window n | water years | > p95 (values / water years) | window max | max ÷ p95 |
|---|---|---|---|---|---|---|
| skagit — the Sauk (12189500) | 36,166 | 495 | 99 | 25 / 13 | 62,600 | 4.6× |
| snohomish-snoqualmie (12149000) | 34,958 | 475 | 95 | 24 / 10 | 48,100 | 2.9× |
| cedar (12119000) | 29,315 | 400 | 80 | 20 / 7 | 4,670 | 2.0× |
| nooksack (12213100) | 21,644 | 300 | 60 | 15 / 10 | 34,200 | 2.4× |
| green-duwamish (12113000) | 32,667 | 450 | 90 | 23 / 9 | 16,400 | 2.2× |
| puyallup-white (12100490) | 5,976 | 85 | 17 | 5 / 1 | 9,220 | 1.3× |

> The Sauk's ladder is built from **495 values across 99 water years** at each December key. The
> shipped ladder throws 24 of them away by refusing to name any level above the 25th-largest. That
> is a choice about what to publish, not a limit of the evidence.

**The honest denominator, and it changes what may be published.** The 495 are days, not events: 99
water years × 5 consecutive calendar days, and one December flood contributes up to five of them.
Distinct water years above each candidate breakpoint (ladder built from the approved record
**before WY2026**, so Event Zero cannot rank itself):

| gauge | > p90 | > p95 | > p98 | > p99 | > p99.5 |
|---|---|---|---|---|---|
| skagit | 23 | 13 | **8** | 4 | 3 |
| snohomish-snoqualmie | 22 | 10 | **8** | **5** | 3 |
| cedar | 14 | 7 | 3 | **1** | 1 |
| nooksack | 17 | 11 | **6** | 3 | 2 |
| green-duwamish | 15 | 9 | **6** | 3 | 2 |
| puyallup-white | 3 | **1** | 1 | 1 | 1 |

Cedar's p99 is one flood — December 2015 — wearing the clothes of a climatological quantile.
Puyallup-white's whole record (WY2009–) cannot support **p95**: one water year lies above it.

**The support rule this justifies.** Publish a tail breakpoint only where its exceedance set spans
**at least five distinct water years**, and print that count beside it. Five is the smallest count
at which the point survives losing any one year; it is a refusal-to-publish rule of the same kind as
the existing `MIN_SAMPLE = 10`, not a hydrologic threshold. What would justify a different number:
a leave-one-water-year-out sweep showing the point moves less than the width of whatever band is
drawn on it — the jackknife in §4 is that measurement's first half, and the band edges it would be
compared against are exactly what X8 blocks.

---

## 3. Candidate A — extend the empirical rank with more ladder breakpoints

**What it is.** `PERCENTILES = (…, 95, 98, 99)`, published per gauge under the support rule of §2,
each an ordinary order statistic of the same window sample. No extrapolation, no distribution, no
new dependency. This is method-spec **M0.1 step 2**.

**What it buys.** The shelf between p95 and the record maximum stops being one state. On the Sauk,
24,976 cfs moves from `p95` to `p98`, which is a real distinction the shipped surface cannot make.

**What it does not buy — measured at the four demonstration pairs** (ladder from the approved record
before WY2026; each day ranked against its own day-of-year key):

| | skagit | snoh-snoq | cedar | nooksack |
|---|---|---|---|---|
| 12-09 → 12-11 (cfs) | 24,976 → 72,440 | 22,860 → 76,555 | 2,748 → 10,106 | 14,165 → 38,182 |
| shipped ladder p05–p95 | p95.0 → p95.0 | p95.0 → p95.0 | p95.0 → p95.0 | p95.0 → p95.0 |
| **Δ48 h, shipped** | **+0.0 pts** | **+0.0 pts** | **+0.0 pts** | **+0.0 pts** |
| extended, support rule applied | p98.0 → p98.0 | p98.0 → p99.0 | p95.0 → p95.0 | p98.0 → p98.0 |
| breakpoints the record allows | p98 | p98, p99 | *none above p95* | p98 |
| **Δ48 h, extended** | **+0.0 pts** | **+1.0 pts** | **+0.0 pts** | **+0.0 pts** |

FACT: extending the ladder moves the ceiling and leaves the derivative where it was. Both endpoints
still land above the highest breakpoint the record can carry at three of the four basins, and at
cedar the record can carry none at all.

**A plotting position does not rescue it.** Gringorten `(i − 0.44)/(n + 0.12)` on the Sauk's 490-value
12-09 window renders 24,976 cfs as **p99.48** — and 72,440 cfs as *nothing*, because it is above the
sample maximum. Δ48 h is **undefined**. The same is true at all four basins. And the two decimals are
false precision: 490 days are 98 independent water years, so the tail resolves to roughly one part in
a hundred, not one in five hundred.

**Verdict.** Keep as an available improvement to the LEVEL; it is *not* the answer to the coupling
this phase exists to solve, and shipping it costs a `@2.0.0` ladder rebuild, a per-gauge refusal
rule, and a vintage decision that X8 blocks. **Deferred, with its evidence recorded here.**

---

## 4. How stable is a ladder point, really? (the fairness check for candidate A)

Two independent stability measurements at the `12-11` key, so "the tail is too uncertain" cannot be
asserted about p98/p99 without noticing that it is equally true of the p95 already on screen.

**Year-block bootstrap** (resample water years with replacement, 2,000 reps), SD as a percent of the
point:

| gauge | p90 | p95 | p98 | p99 | p99.5 |
|---|---|---|---|---|---|
| skagit | ±11 % | ±17 % | ±16 % | ±25 % | ±23 % |
| snohomish-snoqualmie | ±16 % | ±15 % | ±13 % | ±19 % | ±15 % |
| cedar | ±13 % | ±17 % | ±16 % | ±16 % | ±16 % |
| nooksack | ±12 % | ±11 % | ±24 % | ±29 % | ±18 % |
| green-duwamish | ±22 % | ±21 % | ±14 % | ±11 % | ±12 % |
| puyallup-white | ±27 % | ±18 % | ±16 % | ±15 % | ±15 % |

**Leave-one-water-year-out jackknife**, worst move over all years:

| gauge | p90 | p95 | p98 | p99 |
|---|---|---|---|---|
| skagit | 2.3 % | 12.5 % | 8.6 % | 9.9 % |
| snohomish-snoqualmie | 8.1 % | 6.8 % | 4.4 % | 15.9 % |
| cedar | 4.2 % | 4.6 % | 8.2 % | 13.1 % |
| nooksack | 3.2 % | 3.7 % | 3.3 % | 0.9 % |
| green-duwamish | 7.9 % | 9.9 % | 6.8 % | 19.2 % |
| puyallup-white | **45.8 %** | **24.9 %** | 23.7 % | 19.0 % |

INFERENCE: p98 is not materially less stable than the p95 the platform already publishes, so the
extension is not refused on uncertainty grounds. What the table does refuse is **puyallup-white's
whole ladder**: a single dropped water year moves its p90 by 46 %. A per-gauge confidence statement
is owed there regardless of anything in this document.

**Should the reference be smoothed with a wider window? Measured, and the answer is no.** The
±2-day reference jitters from one December day to the next by a median of 2.1–5.2 %, which a
±15-day window would cut to 0.1–0.8 % while also lifting p99's support from 3–5 exceedances to
19–31. Tempting — and unnecessary, because §8 defines the velocity against a **single** named
reference, so the jitter divides out of the derivative exactly and only touches the level, where it
is already smaller than the vintage sensitivity below. Widening is not free either: it drags the
`12-11` p95 down by 2–22 % (puyallup-white −22 %, green-duwamish −16 %, snohomish-snoqualmie −12 %,
cedar −8 %, skagit −4 %, nooksack +1 %) because mid-December is near but not at the seasonal peak.
**Keep the shipped ±2-day window.** It is the tested one, and nothing in the chosen design needs
the smoothing.

**Vintage sensitivity, for completeness and NOT as an X8 answer.** Adding WY2026 to the record moves
the `12-11` p95 by −7.9 % (skagit), −5.4 % (nooksack), −10.0 % (green-duwamish), −14.5 %
(puyallup-white) and 0.0 % at snohomish-snoqualmie and cedar, whose approved records do not yet
reach it. Every level statement in this document — percentile, rank and multiple alike — inherits
that sensitivity and must render its ladder's period and `available_at`. **X8 stays open.**

---

## 5. Candidate A′ — continue the empirical rank as an exact count

**What it is.** *"The kth largest of n daily means in this ±2-day day-of-year window over WY a–b."*
An integer. No estimator, no plotting position, no interpolation, no distributional assumption.
It is `method:rank-in-record@1.0.0`'s device (register X6, method-spec M0.5) applied to the
day-of-year window instead of to annual crests, and it is the honest form of "continue the empirical
rank" that §3's plotting position was reaching for.

At the four pairs, and through the whole event (USGS approved/provisional local-day means, ladder
before WY2026):

| Sauk | 12-05 | 12-06 | 12-08 | 12-09 | 12-10 | 12-11 | 12-12 | 12-13 |
|---|---|---|---|---|---|---|---|---|
| flow (cfs) | 2,740 | 8,220 | 11,100 | 24,900 | 41,500 | 62,600 | 21,100 | 12,800 |
| shipped percentile | 30.8 | 90.1 | 95.0 | 95.0 | 95.0 | 95.0 | 95.0 | 94.1 |
| Δ24 h percentile | +7.9 | **+59.4** | +9.7 | **+0.0** | **+0.0** | **+0.0** | **+0.0** | −0.9 |
| **rank in window** | 343 of 491 | 49 | 17 | **3** | **LARGEST** | **LARGEST** | 8 | 31 |

FACT: the rank discriminates 24,900 from 11,100 where the percentile cannot — and then **saturates at
1**, because a value above the record maximum is "the largest", and so is a value twice that. Cedar
read `LARGEST` for **nine consecutive days**, 12-10 through 12-18, while its flow ran 5,220 →
10,100 → 9,130 → 7,070 → 5,910 → 5,390 → 5,300 → 5,850 → 5,160 cfs — a factor of two, reported as
one state.

**This is the finding that decides the phase.** A percentile is bounded above by 100 and censored at
the record maximum; a rank is bounded below by 1. Neither can carry a derivative once the record runs
out — and at all four demonstration basins the record ran out *before the crest*, not after it.
The saturation is at least honest: it names the record it beat (*"larger than all 490 daily means in
this window since WY1912; previous maximum 37,400 cfs on 2004-12-11"*) rather than reporting a
number the ladder does not have.

**Verdict. Adopted for the LEVEL, alongside the unchanged percentile.**

---

## 6. Candidate C — peaks over threshold / generalized Pareto

Evaluated seriously and then refused, on four measured grounds. Cool-season window (15 Nov – 15 Jan),
7-day declustering so one flood is one event, Hosking PWM fit, record before WY2026.

**1. There is enough data, at the deep gauges.** Independent exceedances above the cool-season p95:
121 (skagit), 111 (snoh-snoq), 83 (green-duwamish), 74 (nooksack), 57 (cedar) — and **13** at
puyallup-white, where nothing can be fitted at all (its PWM shape is −1.15, a degenerate answer). So
sample size is *not* the disqualifier at five of six gauges, and saying otherwise would be lazy.

**2. The threshold choice moves the answer.** Fitted shape ξ by threshold:

| gauge | u = p95 | u = p98 | u = p99 |
|---|---|---|---|
| skagit | +0.125 | +0.167 | +0.107 |
| snohomish-snoqualmie | −0.051 | −0.085 | +0.115 |
| **cedar** | **+0.488** | **+0.194** | **−0.062** |
| nooksack | +0.023 | +0.226 | +0.094 |
| green-duwamish | −0.141 | −0.042 | −0.003 |

Cedar's fitted tail changes from **heavy to bounded** on a choice nobody can justify from the physics.

**3. Parameter uncertainty exceeds the signal.** At the Sauk — the deepest record available — the
95 % bootstrap interval on ξ alone is 0.33 wide at u = p90 and **0.59 wide at u = p99**, widening as
the threshold moves toward the region of interest. A shape parameter known to ±0.3 does not pin a
quantile at 5× the reference flow.

**4. It does not restore the velocity, and its output is a forbidden object.** Fitted non-exceedance
at the four pairs, u = cool-season p95:

| | skagit | snoh-snoq | cedar | nooksack |
|---|---|---|---|---|
| F(12-09) → F(12-11) | 0.732 → 0.992 | 0.554 → 0.999 | 0.581 → 0.985 | 0.131 → 0.959 |
| as a percentile of all days | p98.66 → p99.96 | p97.77 → p99.99 | p97.91 → p99.93 | p95.65 → p99.79 |
| **Δ48 h** | **+1.30 pts** | **+2.22 pts** | **+2.02 pts** | **+4.14 pts** |

Better than +0.0, and still compressed into a few points across a 2.7–3.4× change in flow — because
a probability is bounded above by 1 in exactly the way a percentile is bounded by 100. To make it
carry velocity you would render it on a return-period axis, and **register X6 settles that the
platform computes no recurrence interval, return period or annual exceedance probability for any
reach, ever**.

**Verdict. Refused.** `candidate_c_pot_gpd` exists in the prototype only to return these diagnostics
with the refusal attached, so a future proposal has to argue with the numbers rather than restate the
idea.

---

## 7. Candidate B — the seasonal high-flow multiple. **Chosen.**

**What it is.** `R = Q ÷ p95(day-of-year)` — the observed flow as a multiple of the top breakpoint the
ladder already stores. One division. No distributional assumption, no new provider, no fitting.

**Why p95 and not p90 or p50.** It is the *top stored breakpoint*, so `R ≥ 1.0` is exactly the
condition under which the shipped percentile clamps: the multiple begins precisely where the
percentile stops discriminating, and the two can never disagree about where that is. Measured
confirmation across each gauge's whole record, the p95 of R is **1.00** at all six.

**At the four pairs** (each day against its own day-of-year reference, pre-WY2026 ladder):

| | skagit | snoh-snoq | cedar | nooksack |
|---|---|---|---|---|
| reference p95, 12-09 / 12-11 (cfs) | 10,555 / 12,550 | 13,800 / 16,450 | 1,980 / 2,312 | 11,160 / 13,260 |
| **R: 12-09 → 12-11** | **2.37× → 5.77×** | **1.66× → 4.65×** | **1.39× → 4.37×** | **1.27× → 2.88×** |
| growth over the 48 h | ×2.90 | ×3.35 | ×3.68 | ×2.70 |

Through the whole event at the Sauk, beside the two representations that die:

| Sauk | 12-06 | 12-08 | 12-09 | 12-10 | 12-11 | 12-12 | 12-13 |
|---|---|---|---|---|---|---|---|
| percentile | 90.1 | 95.0 | 95.0 | 95.0 | 95.0 | 95.0 | 94.1 |
| rank in window | 49 | 17 | 3 | LARGEST | LARGEST | 8 | 31 |
| **R** | **0.81×** | **1.08×** | **2.36×** | **3.81×** | **4.99×** | **1.55×** | **0.94×** |

Monotone in flow by construction, exactly reproducible, and — decisively — **unbounded**. It is the
only one of the three that still moves between 12-09 and 12-11.

**The limitation that must travel with it, and it is not small.** R is a multiple of a *seasonal*
reference, never a flood magnitude. The largest multiples in these six records are late-summer flash
events on a tiny denominator: green-duwamish reached **8.91× on 1959-09-27** at 8,840 cfs — a flow
that against the 11 December reference reads **1.3×**. Consequences, and they are rules:

- the absolute flow is rendered beside the multiple **always**;
- the multiple is **never banded on a year-round cutoff**, and no band is proposed here;
- the multiple is never compared across gauges without its reference, and never across seasons at all.

Observed range of R over each full record: p50 ≈ 0.37–0.45, p95 = 1.00 by construction, p99 =
1.24–1.65, maximum 3.98–8.91. Event Zero reached 4.99× (skagit), 4.89× (snoh-snoq), 4.37× (cedar,
**a new record multiple for that gauge**, previous maximum 4.23× on 1975-12-03) and 2.58× (nooksack).

---

## 8. The state-change velocity (brief §6), stated exactly

### What Δ24 h and Δ48 h are computed ON

**On the daily-mean discharge, as a multiplicative growth factor:**

```
G24 = Q(t) ÷ Q(t − 24 h)          G48 = Q(t) ÷ Q(t − 48 h)
```

which is identically the change in the chosen representation against a single named reference,
because the reference divides out:

```
R(t) ÷ R(t−Δ) = (Q(t)/ref) ÷ (Q(t−Δ)/ref) = Q(t) ÷ Q(t−Δ)
```

**Not** on the percentile — that is the defect. **Not** on the rank — it is censored at 1. **Not** as
an additive change in R: additive ΔR ranks the crest above the onset (Sauk, Δ24 h: **+0.57** on 12-06
against **+1.18** on 12-11) while the multiplicative form ranks the onset above the crest (**×3.00**
against **×1.51**) — which is what a *rate* is supposed to do. Additive ΔR is a magnitude wearing a
derivative's name. The multiplicative form is scale-free, which is what
makes the same number meaningful at 500 cfs and at 60,000 cfs.

### What they are called

| | |
|---|---|
| feature id | `streamflow_growth_24h`, `streamflow_growth_48h` |
| method id (PROPOSED) | `method:streamflow-state-change@0.1.0` |
| unit | dimensionless multiple; rendered as `×2.24 in 24 h` or `+124 % in 24 h` |
| direction on the `Driver` | `state_change_not_scored` — a fourth direction beside `increases_susceptibility`, `context_not_scored` and `unavailable`. It contributes **nothing** to the susceptibility index; `SurfaceState.score` stays `percentile / 100` exactly as today |
| steady band | `trend.py`'s existing ±1 %/h, compounded over the actual span (×1.27 over 24 h, ×1.61 over 48 h), so two surfaces cannot call the same river steady and rising in the same breath |
| UNKNOWN | no observation within 6 h of `t − window`; a zero or negative endpoint; a window that spans no time. Refused with a reason, never interpolated — `trend.py`'s discipline |

### How it is labelled in the extrapolated region

**There is no extrapolated region.** The growth is arithmetic on two observations and touches no
ladder. That is the property the whole selection turns on, and it has three consequences:

1. **It is exact when the level is censored.** On 12-11 the Sauk's level said *"larger than every
   daily mean in this window since WY1912"* — a censored statement — while the change said **×1.51 in
   24 h, rising**, which the shipped percentile derivative reported as `+0.0`.
2. **It is computable when the level is not.** A gauge with no ladder, or one refused by
   `MIN_SAMPLE`, has no percentile, no rank and no multiple — and still has a state change. It must
   be published there.
3. **It does not depend on the ladder's vintage.** Register X8 disputes which record a ladder is
   built from; that dispute cannot move this number. **X8 is not resolved by this** — the level
   (percentile, rank, multiple) depends on the ladder entirely, and every level statement still
   renders its period, its `n`, its water-year count and its `available_at`.

The flag that *is* carried, on the LEVEL and never on the change, is `exceeds_window_record`, with
the previous maximum and the day it fell on.

### Is it fast? — answered by rank, not by a cutoff

`growth_rank` places the observed growth among that gauge's own past changes over the same window.
Measured at the Sauk (35,976 day-pairs before WY2026): ×3.00 on 12-06 ranks **200th**; ×2.24 on 12-09
ranks 502nd; **×1.51 on 12-11 — a day the shipped derivative read +0.0 — still ranks 1,514th, inside
the top 5 %**; and ×0.34 on 12-12 ranks 35,973rd of 35,976, so the recession is detected as sharply
as the rise. No band is drawn on any of this. What would justify one: a probability-of-detection /
false-alarm-ratio curve over a multi-event catalogue at all six basins (brief §18).

### Nothing is given up in the body to gain the tail (FACT)

The obvious objection is that a scale-free growth might lose the 1–3 days of lead that tier0 §2
measured from the *percentile* velocity. Tested at a **matched historical base rate** — the tier0
convention `Δ48 h percentile ≥ +40` has a measured frequency `f` in each gauge's own record, and the
G48 cut with the same `f` is the fair comparison:

| gauge | f(Δ48 pct ≥ +40) | matched G48 cut | first Dec-2025 day, percentile rule | first Dec-2025 day, growth rule |
|---|---|---|---|---|
| skagit | 3.08 % | ×2.23 | 12-06 (+67 pts) | 12-06 (×3.40) |
| snohomish-snoqualmie | 3.61 % | ×2.42 | 12-06 (+57 pts) | 12-06 (×2.88) |
| cedar | 1.66 % | ×2.02 | 12-08 (+62 pts) | **12-07 (×2.13)** |
| nooksack | 3.95 % | ×2.22 | 12-06 (+68 pts) | 12-06 (×3.56) |
| green-duwamish | 1.80 % | ×2.51 | 12-07 (+55 pts) | 12-07 (×2.66) |
| puyallup-white | 2.79 % | ×2.00 | 12-06 (+52 pts) | 12-06 (×2.46) |

Same day at five of six, one day earlier at cedar. Both cuts are **reporting conventions chosen to
order the days**, exactly as tier0 §5 says of `+40`; neither is a validated threshold and neither
is proposed as one.

**A caution that belongs in the open.** A large growth is not by itself a flood: across the full
record, days with `G24 ≥ 2.0` sit at or above their own p95 only **25–45 %** of the time and below
half of it **15–25 %** of the time. That is the measured reason the change must be rendered *beside*
the level and never fused into it.

---

## 9. What the surface says — HYDROLOGIC STATE and STATE CHANGE, without a composite

Two statements, separately provenanced, never combined, with no arithmetic between them and no
ordering imposed on the pair.

**HYDROLOGIC STATE — where the river is.** The percentile and its band, unchanged and still
EXPERIMENTAL; the rank in the window; the multiple; the absolute flow. Rendered:

> **Sauk at 62,600 cfs** — 4.99× the p95 flow for 11 Dec (12,550 cfs; ±2-day window, WY1912–WY2025,
> n = 490 over 98 water years). Larger than all 490 daily means in that window; previous maximum
> 37,400 cfs on 2004-12-11. Day-of-year percentile: at or above p95 *(the ladder does not resolve
> further; `outside_climatology_range`)*.

**STATE CHANGE — which way it is moving and how fast.** Its own row, its own provenance ref, its own
method id:

> **Rising: ×1.51 in 24 h (+51 %), ×2.51 in 48 h.** 1,514th largest 24-hour change in 35,976 daily
> pairs at this gauge, WY1912–WY2025.

**The rules that keep it out of composite territory:**

- no arithmetic combines the two — no sum, no product, no weighted index, no "adjusted percentile";
- the band (`LOW … VERY_HIGH`) is computed from the percentile **alone**, exactly as today, and
  `SurfaceState.score` stays `percentile / 100`;
- the state change is a `Driver` with `direction = state_change_not_scored`; it renders and explains,
  it does not score;
- the UI may not colour, size or order one by the other, and there is no cell in which a HIGH state
  and a fast change resolve into a single symbol;
- they meet only in a sentence that names both, and the sentence keeps them in separate clauses.

INFERENCE: this is the same doctrinal move `HYDROLOGY.md` §7 already makes for snow — *shown, never
scored* — applied for a different reason. Snow is context because more SWE is not more risk. The
state change is unscored because **no evidence exists for a weight**, and inventing one would be the
composite the brief prohibits.

---

## 10. What this document does and does not license

**Licensed now** (measured, no calibration required):

- publishing the exact rank in the day-of-year window, with `n`, water-year count and period;
- publishing `Q ÷ p95(DOY)` with its reference flow, key, window, period, `n` and water-year count;
- an explicit `exceeds_window_record` state naming the previous maximum and its day;
- computing Δ24 h / Δ48 h as a multiplicative flow growth, with `trend.py`'s steady band and refusal
  discipline, and ranking it in the gauge's own history;
- refusing peaks-over-threshold, with §6's diagnostics as the reason;
- a per-gauge tail-support rule requiring ≥ 5 distinct water years above any published breakpoint.

**NOT licensed by this document:** any band edge on the multiple or on the growth; any weighting of
the change against the level; any composite; any probability, return period or AEP; any change to
`method:streamflow-doy-climatology@1.0.0` or to `BAND_EDGES`; any answer to X8. The `+40 points` and
`top 1 %` conventions used above are ordering devices for these tables, not cutoffs.

**Open questions this leaves standing:**

1. **X8 — the ladder vintage.** Every level statement here inherits it. The velocity does not, which
   narrows X8's blast radius but does not close it.
2. **Puyallup-white's ladder.** A single dropped water year moves its p90 by 46 %, and its p95
   exceedance set is one water year. The honest answer above p90 there may be UNKNOWN. Out of scope
   here; it needs its own decision.
3. **Whether the extended breakpoints (§3) are worth a `@2.0.0` rebuild** once X8 is settled. They
   improve the level and are measurably irrelevant to the velocity.
4. **A cutoff on the growth.** Needs brief §18's multi-event POD/FAR curve. Until then: rank only.

---

## 11. Reproduction

The record — one request per gauge, public, no credentials, ~0.2–1.0 MB each. The
`limit` maximum is 50,000; none of the six records reaches it, so no pagination is involved:

```
https://api.waterdata.usgs.gov/ogcapi/v0/collections/daily/items
  ?monitoring_location_id=USGS-12189500      # and 12149000 12119000 12213100 12113000 12100490
  &parameter_code=00060&statistic_id=00003
  &f=csv&skipGeometry=true&limit=50000
  &properties=time,value,approval_status
```

The computation — approved rows only, `±2`-day day-of-year window, R-type-7 percentiles, water year
= Oct–Sep, which is `build_doy_climatology` verbatim:

```python
from cascade_hydrology.tail_candidates import (
    WindowSample, tail_state, state_change, supported_breakpoints, candidate_c_pot_gpd,
)
sample = WindowSample.from_pairs(window_pairs, key="12-11", window_days=2)
state  = tail_state(72440.0, sample, stored_ladder)          # percentile + rank + multiple
change = state_change(points, end=t, window_h=48)            # the velocity
```

`WindowSample.quantile` is asserted identical to `cascade_providers_usgs.climatology.percentile` at
p05/p50/p90/p95/p98/p99 for all six gauges. Ladders labelled *pre-WY2026* exclude every day from
2025-10-01 onward, so Event Zero cannot rank itself; the *full* ladders reproduce tier0 §2's
production percentiles to the rounding, which is how the reconstruction was validated.

`tests/unit/test_tail_candidates.py` pins the headline numbers offline against the Sauk's real
top-30 order statistics at the `12-11` key.

---

## 12. Register and doctrine consequences

Nothing here closes a register row. Two rows gain a note when this is promoted:

- **X8** — unchanged and still BLOCKING. Record that the proposed state-change velocity is
  vintage-independent, so the derivative may ship ahead of X8's resolution while the level may not
  gain new confidence from it.
- **X6** — unchanged. §6 is a second, independent arrival at its adjudication: this document refused
  a GPD fit on its own measurements before reaching X6's rule, and the two agree.
- **X8 claim D** (added 2026-08-26 from the sibling measurement: the deployed ladders contain the
  event they rank) is **independently confirmed here** from a different source — see §13.

`HYDROLOGY.md` §3 would gain the two new level fields and the state-change row when a method is
promoted; §13's X6 addition (*no recurrence interval, return period or AEP*) is a prerequisite for
§6's refusal to be doctrine rather than preference, and is still outstanding.

---

## 13. Reconciliation with `tail-representation-2026-08-26.md`

Two agents measured this question in parallel from **different sources** — that document from the
R2-archived daily-values CSVs the deployed ladders were built from, this one from a fresh fetch of
the full USGS OGC `daily` record. That is a stronger position than either alone, and it is worth
recording what survived the comparison.

**Agreed, and independently arrived at:**

- the p95 ceiling is an implementation choice, not a limit of the record;
- three quantities are published above it — the percentile unchanged, an exact rank, and the ratio
  to p95 — because no single one is both honest and non-collapsing;
- **the ratio is what must carry the derivative**, because it is the only one that never collapses;
- extending the ladder is a partial fix and cannot be the whole one;
- the extension must be decided per gauge from its own sample, never as a global constant;
- puyallup-white (record from WY2009) supports no breakpoint above p95 and must say so;
- four of six gauges crested **above every observation in their own day-of-year window** across the
  whole period of record — which is why no percentile of any resolution reaches the crest;
- cedar's rank saturation is long: that document reports eight consecutive days at rank 1, this one
  measures **nine** (12-10 → 12-18) from the published local-day series against a pre-WY2026 ladder.
  Same phenomenon, slightly different day set and daily-mean convention; neither corrects the other.

**Agreed to the digit, from independent sources.** Both documents measure the WY2026 contamination
of the deployed ladders (register X8 claim D). At the two gauges whose day-of-year keys coincide,
the numbers are identical: the Sauk's `12-11` p95 is **13,630 cfs with WY2026 and 12,550 without
(+8.6 %)**, and the Nooksack's is **14,020 / 13,260 (+5.7 %)**. Green-duwamish and puyallup-white
are quoted there at a different key and read **+11.1 %** and **+17.0 %** here at `12-11`
(+11.2 % / +13.2 % at `12-09`) — larger, not smaller, so the direction and the severity ordering
both hold. Cross-source agreement to four significant figures also establishes something neither
document set out to test: **the R2-archived CSVs and the live USGS record are the same data.**

**One refinement to claim D.** Five of six gauges carry approved WY2026 daily means — every one
except Snoqualmie 12149000 — which is what that document says. But cedar's approved WY2026 record
**stops at 2025-12-04**, before the crest, so cedar's `12-09` and `12-11` ladder keys are
uncontaminated (0.0 % shift) even though the gauge is in the contaminated five. The precise
statement is: *five of six gauges carry approved WY2026 data; **four** of six have it inside the
day-of-year window that ranks the crest.* The blocking conclusion is unchanged.

**One genuine disagreement — the tail-support rule, and this document argues its side.**

| | that document | this document |
|---|---|---|
| criterion | ≥ 5 **exceedances** above the breakpoint | ≥ 5 distinct **water years** above it |
| p98 admissible at | 5 of 6 gauges | **4 of 6** (cedar and puyallup-white refused) |
| p99 admissible at | 3 of 6 gauges | **1 of 6** (snohomish-snoqualmie only) |

The exceedance counts themselves are not in dispute — both documents measure 5 / 5 / 4 / 3 / 5 / 1
values above p99 at Sauk / Snoqualmie / Cedar / Nooksack / Green / Puyallup, which agree exactly.
The dispute is whether five *days* are five pieces of evidence. §2 measures that they are not: the
±2-day window makes one flood contribute up to five consecutive values, so cedar's five
p99-exceeding days are **one water year (December 2015)** and the Sauk's are **four**. §4 measures
the consequence — leave one water year out and p99 moves by up to 19.2 %. A breakpoint whose entire
exceedance set is one flood is a description of that flood, not a climatological quantile, and the
count of *days* cannot distinguish the two cases.

INFERENCE: adopt the water-year rule. It is strictly more conservative, it costs only breakpoints
whose derivative contribution §3 measures at `+0.0` anyway, and it is the one criterion that
notices cedar. **OPEN QUESTION** for whoever promotes a method: whether the count should be 5 or 3
— §4's jackknife is that measurement's first half, and its second half needs the band width that
X8 blocks.

**What this document adds that the other does not carry:** the peaks-over-threshold evaluation and
its measured refusal (§6); the state-change velocity specification, its vintage-freedom and its
base-rate-matched lead comparison (§8); ladder-point stability by year-block bootstrap and
leave-one-water-year-out jackknife (§4); the reference-window widening test (which argues *against*
widening, §4 note); and the seasonal-multiple caveat that the largest multiples on record are
September flash events on a tiny denominator (§7).

**What the other document carries that this one does not:** bit-consistency with the deployed
ladder artefacts, the storage cost of carrying the top-20 pairs beside each ladder key (711 KB for
all six gauges), and the corrected local-day daily means that supersede tier0 §3's UTC-day figures.
