# Trend estimator selection — measured against real Event Zero hydrographs

Computed 2026-08-26 by `scripts/measure_trend_estimators.py` against **production Neon**: the
15-minute observations at all seven seeded gauges for 2025-12-01 .. 2025-12-22, both stage and
discharge. 14,700 admissible 6-hour windows on stage, 14,684 on flow. Nothing here is fitted;
no threshold is tuned; the STEADY epsilons are the shipped ones, unchanged.

Labels per `docs/research/README.md`: **FACT** = computed this session; **INFERENCE** = reasoned
from those facts; **OPEN QUESTION** = unresolved.

> **Provenance note.** `packages/hydrology/src/cascade_hydrology/trend_candidates.py` was written
> in an earlier phase of this session and cited a file dated `2026-08-27` that did not exist —
> the phase that was to produce it did not finish. The module's estimators were sound but its
> central claim ("measured against real hydrographs") was **unsupported at the time it was
> committed**. This document is that measurement, run afterwards. Its conclusion happens to
> agree with the module's reasoning; that agreement is now evidence rather than assertion.

---

## 1. Verdict

**Replace the endpoint difference with Siegel's repeated median.** It is the best estimator in
five of the six fault modes measured, ties every other candidate on lead time to within one
15-minute update, and costs 0.9 ms per request across all six basins.

| | endpoint (shipped) | OLS | Theil–Sen | **repeated median** |
|---|---|---|---|---|
| survives a bad endpoint reading | **no** (§3) | no | yes | **yes** |
| survives two bad readings | yes | **no** | yes | **yes** |
| survives a frozen datalogger | poor | poor | fair | **best** |
| spurious direction flips (§2) | 13 / 22 | 0 | 0 | **0** |
| lead time cost vs the best (§4) | — | — | — | **≤ 0.5 h** |
| removes a tide (§5) | no | no | no | **no** |

The tide row is not a defect of any candidate. **No estimator removes a tide**, which is why the
guard is a refusal and not a filter (§5).

---

## 2. Jitter: what the rate does between two consecutive updates (FACT)

Median and p95 change in the reported rate from one 15-minute update to the next, normalised by
the window's own last value so gauges are comparable. "Hard flips" counts transitions straight
from `rising` to `falling` or back, with no `steady` in between — a reversal the hydrograph
did not perform.

| estimator | stage: median step | p95 step | hard flips | flow: median step | p95 step | hard flips |
|---|---|---|---|---|---|---|
| endpoint | 1.18e-04 | 2.19e-03 | **13** | 1.10e-03 | 1.04e-02 | **22** |
| OLS | 6.04e-05 | 1.03e-03 | 0 | 4.27e-04 | 3.76e-03 | 0 |
| Theil–Sen | 5.16e-05 | 1.01e-03 | 0 | 3.93e-04 | 3.85e-03 | 0 |
| **repeated median** | **3.28e-05** | **9.86e-04** | 0 | **2.48e-04** | 4.13e-03 | 0 |

The shipped estimator moves **2.3× further per update on stage and 4.5× further on flow** than
the repeated median, and it is the only candidate that ever reverses direction outright. Every
robust candidate flips zero times in 14,700 windows.

---

## 3. Robustness: what one bad reading does (FACT — and this is the decisive result)

Four telemetry faults injected into each real window, then the estimate compared against the
same window uncorrupted. Error is reported **in STEADY epsilons**, because an error below 1.0
epsilon cannot change what the surface says; the count in parentheses is the number of windows
whose reported direction actually changed, out of 14,700 (stage).

| estimator | held run (25 %) | held run (40 %) | spike, mid-window | **spike at an endpoint** | two spikes |
|---|---|---|---|---|---|
| endpoint | 0.17 (1,170) | 0.27 (1,863) | 0.00 (0) | **45.69 (11,456)** | 0.00 (0) |
| OLS | 0.11 (703) | 0.25 (1,561) | 0.00 (17) | 10.16 (11,138) | 5.27 (10,552) |
| Theil–Sen | 0.08 (597) | 0.24 (1,470) | 0.00 (28) | 0.02 (276) | 0.02 (168) |
| **repeated median** | **0.04 (467)** | **0.14 (1,224)** | 0.01 (114) | **0.00 (167)** | **0.03 (294)** |

Flow behaves the same way: endpoint 8.42 epsilons and 11,235 direction changes on a bad first
reading, repeated median 0.00 and 292.

**A single bad reading at either end of the window moves the shipped estimator by a median of
45.7 steady epsilons and changes the reported direction in 11,456 of 14,700 windows — 78 %.**
The repeated median moves 0.00 epsilons and changes direction in 167 windows, 1.1 %.

Two entries deserve stating plainly rather than being read past:

- **The mid-window spike column flatters the endpoint estimator, and that is the point.** It
  scores a perfect 0.00 because it *does not look at* the value that was corrupted. Immunity by
  blindness is the defect, not a defence: the same blindness is what produces the endpoint
  column beside it. An earlier draft of this measurement injected spikes only mid-window and
  would have reported the shipped estimator as the most robust candidate on the table.
- **OLS fails the two-spike case worse than the estimator it would replace** (5.27 epsilons,
  10,552 direction changes). One spike up and one spike down is a lever on a least-squares fit.
  OLS is not a robust estimator and should not be adopted as one.

The 40 % held run is the only fault where every candidate degrades: it exceeds Theil–Sen's
29.3 % breakdown point, and the repeated median's advantage there (0.14 vs 0.24 epsilons) is
the 50 %-breakdown property doing exactly what it exists to do.

---

## 4. Lead time: does robustness cost anticipation? (FACT — no)

Hours before each gauge's **observed** December maximum at which the estimator first reports a
rise sustained for 2 hours. The peak is a fact about the record, not a label anyone assigned.

| gauge | peak (stage) | endpoint | OLS | Theil–Sen | repeated median |
|---|---|---|---|---|---|
| 12100490 | 12-15 17:15 | 247.25 | 247.75 | 247.75 | 247.75 |
| 12113000 | 12-13 15:15 | 157.00 | 156.75 | 156.00 | 155.50 |
| 12119000 | 12-11 23:00 | 105.25 | 105.00 | 105.00 | 104.50 |
| 12149000 | 12-11 12:00 | 127.50 | 127.75 | 127.75 | 127.75 |
| 12189500 | 12-11 12:30 | 127.50 | 127.25 | 127.00 | 127.00 |
| 12200500 | 12-12 08:15 | 145.75 | 145.00 | 144.75 | 144.50 |
| 12213100 | 12-12 06:15 | 142.00 | 142.00 | 141.75 | 141.50 |

Every difference is **at most 0.75 h — three updates** — and the sign varies by gauge. On the
6-to-120-hour question this milestone exists to answer, the four estimators are indistinguishable
on lead time. Robustness is therefore free here: it is not bought with lag.

One flow-basis row is not a tie and is reported because it is the largest single difference
measured: at **12119000 (Cedar), on discharge**, the endpoint estimator first sustains a rise
115.75 h before the peak while all three robust estimators sustain one at **233 h** — 117 hours
earlier. INFERENCE: the early rise was present in the record and the endpoint estimator's jitter
(§2) kept breaking the run before it reached two hours. A noisy estimator does not only add false
signal; it can destroy a true one by preventing it from persisting.

### The honest cost

Sustained rise onsets after 12-14, once every gauge has crested:

| | endpoint | OLS | Theil–Sen | repeated median |
|---|---|---|---|---|
| stage | **11** | 15 | 16 | 15 |
| flow | **17** | 20 | 19 | 22 |

The robust estimators report **more** sustained-rise onsets in the post-crest period — up to 5
more on flow. **This is reported as a cost, not explained away.** This script cannot distinguish
a genuine secondary rise (December 2025 had several) from a spurious one, so it does not label
them false positives, and neither does this document. OPEN QUESTION: whether that increase is
real signal or added alarm is exactly what the multi-event false-positive evaluation must
settle, and it must not be assumed favourable in the meantime.

---

## 5. Tide: no estimator removes it (FACT)

A pure 1.0 ft M2 signal (12.42 h) injected onto the real stage record at 12200500, the seeded
point nearest tidewater. STEADY epsilon is 0.05 ft/h.

| estimator | clean median rate | with tide | inflation | as a multiple of epsilon |
|---|---|---|---|---|
| endpoint | 0.0683 | 0.2279 | +0.1595 | 4.6× |
| OLS | 0.0685 | 0.2648 | +0.1963 | 5.3× |
| Theil–Sen | 0.0680 | 0.2912 | +0.2232 | 5.8× |
| repeated median | 0.0677 | **0.3265** | +0.2588 | **6.5×** |

The chosen estimator is the **worst** on this test. That is not a reason to reject it: a tide is
not an outlier, it is a coherent signal occupying most of the window, and robustness against
outliers is the wrong tool. Every candidate reports a rate 4.6–6.5× the STEADY epsilon on a
river that is not rising.

INFERENCE, and it is the design consequence: a tidal gauge cannot be fixed by choosing a better
estimator, so `tidal_refusal` must remain a **refusal that fails closed** on any station without
a measured tidal class. The measurement supports the guard that already exists rather than
licensing its removal.

---

## 6. Cost (FACT)

Per call at the 15-minute cadence, measured on this machine:

| window | endpoint | Theil–Sen | repeated median |
|---|---|---|---|
| 6 h (n=24) | 0.3 µs | 46.8 µs | 74.6 µs |
| 12 h (n=49) | 0.2 µs | 221.1 µs | 342.3 µs |

Six basins × two bases at the 6 h window: **0.9 ms**. `/viz/basins` measures ~2,600 ms in
production, of which ~195 ms per query is cross-region round trip. The estimator is 0.03 % of
the request. O(n²) is not a concern at these window sizes and would become one only above roughly
n=500, which no named window reaches.

---

## 7. What this licenses, and what it does not

**Licensed**: replacing `trend.py`'s endpoint difference with the repeated median under a new
method id, publishing the pair-slope IQR beside the rate as a dispersion, and keeping the tidal
refusal fail-closed.

**NOT licensed**: any change to the STEADY epsilons (untouched here and deliberately so — an
epsilon fitted to this event would prove nothing); any claim that the change reduces false
positives (§4 measures the opposite sign and leaves it open); any application of these
estimators to a **percentile** series, which inherits the p95 clamp and reads +0 through a crest
(`tier0-measured-basis-2026-08-26.md` §3).

---

## 8. Reproduction

```bash
CASCADE_DB_URL="$NEON_DIRECT_URL" python scripts/measure_trend_estimators.py --out report.json
```

The script caches the pulled observations, so re-runs are offline and deterministic. Sample
depth behind the ladders referenced above, for the 12-09 key: n=85 (12100490, 2009-2026) to
n=495 (12189500, 1911-2026).
