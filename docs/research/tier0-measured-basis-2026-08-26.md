# Tier 0 measured basis — what the shipped susceptibility surface actually did in Event Zero

Computed 2026-08-26 from **production Neon**, not from a synthesis: the stored
`method:streamflow-doy-climatology@1.0.0` ladders and the backfilled December-2025 observations,
ranked exactly the way `susceptibility.py` ranks them. Every number here is reproducible with the
query in §6.

Labels per `docs/research/README.md`: **FACT** = computed this session; **INFERENCE** = reasoned
from those facts; **OPEN QUESTION** = unresolved.

---

## 1. Verdict

Three defects, all confirmed with numbers, and **one interaction between them that the science
review did not state and that changes the fix order**:

| # | Defect | Status |
|---|---|---|
| 1 | The level lags the deterioration by **1–3 days** | FACT, quantified per basin (§2) |
| 2 | The percentile **collapses at p95** across flow ratios up to **3.7×** | FACT, quantified per basin (§3) |
| 3 | **The collapse also silences the derivative** — once clamped, Δ24 h and Δ48 h are identically 0 | FACT (§3), and it means fixing the derivative alone would still go blind at the peak |
| 4 | Skagit had **no susceptibility data at all** for Event Zero | FACT (§4) — a backfill gap, now fixed |

The governing question for Tier 0 is whether a corrected surface surfaces deterioration
*earlier without more false alarms*. §2 says the derivative alone buys 1–3 days on this event.
§3 says that buying it is worthless during the peak unless the tail is fixed too.

---

## 2. The level lags; the derivative does not (FACT)

Daily-mean flow at each basin's configured susceptibility gauge, ranked in that gauge's own
stored day-of-year ladder. `d24` / `d48` are percentile-point changes.

| basin (gauge) | first day level ≥ p90 | first day Δ48 h ≥ +40 | **lead gained** |
|---|---|---|---|
| cedar (12119000) | 12-09 | 12-08 | **1 day** |
| green-duwamish (12113000) | 12-08 | 12-07 | **1 day** |
| nooksack (12213100) | 12-07 | 12-06 | **1 day** |
| puyallup-white (12100490) | 12-09 | 12-06 | **3 days** |
| snohomish-snoqualmie (12149000) | 12-09 | 12-06 | **3 days** |
| **skagit (12189500, the Sauk)** | 12-09 | **12-06** | **3 days** |

The shape of the miss, at **Skagit — the basin of the event** (gauge backfilled 2026-08-26, §4):

| date | flow (cfs) | percentile | Δ24 h | Δ48 h |
|---|---|---|---|---|
| 12-04 | 2,358 | **22** | −2 | −7 |
| 12-05 | 2,580 | 27 | +5 | +3 |
| 12-06 | 6,537 | 81 | **+54** | **+59** |
| 12-07 | 7,208 | 85 | +4 | +58 |
| 12-08 | 8,359 | 89 | +4 | +8 |
| 12-09 | 24,976 | 95 | +6 | +10 |
| 12-11 | 72,440 | **95** | **+0** | **+0** |

Two days before the largest 24-hour swing in the record examined here (**+54 points**, p27 → p81),
the Skagit reads **p22** — the calmest value of the month. Five days later the same surface reads
the identical `p95` at 72,440 cfs that it read at 24,976 cfs.

And at Snohomish–Snoqualmie:

| date | flow (cfs) | percentile | Δ24 h | Δ48 h |
|---|---|---|---|---|
| 12-03 | 2,253 | 17 | −2 | −6 |
| 12-04 | 2,069 | **14** | −3 | −5 |
| 12-05 | 2,557 | 23 | +9 | +6 |
| 12-06 | 4,735 | 58 | **+35** | **+44** |
| 12-07 | 6,704 | 77 | +19 | **+54** |
| 12-08 | 7,942 | 83 | +6 | +25 |
| 12-09 | 22,860 | 95 | +12 | +18 |

On 12-04 the basin reads **p14** — the calmest reading of the month — two days before a +44-point
48-hour swing and five days before a 76,555 cfs daily mean. The level is not wrong; it is
answering a different question from the one a forecaster is asking.

The largest single-day changes observed: **+54 points/24 h** (skagit, 12-06), **+45** (nooksack,
12-06) and **+39** (green-duwamish, 12-07). The largest 48-hour changes: **+62** (nooksack,
12-05→07), **+59** (skagit), **+55** (cedar), **+54** (snohomish-snoqualmie), **+53**
(green-duwamish). Every one of the six basins exceeded +40 points in 48 hours before its level
reached p90.

> The review's "+64 percentile points in 48 hours" is **CONFIRMED in kind and magnitude** by this
> platform's own stored data (measured maximum +62 at nooksack). The specific figure depends on
> gauge and ladder vintage and should be quoted as a class, not a scalar.

---

## 3. The p95 collapse, and why it also kills the derivative (FACT)

The stored ladders end at `p95`. `susceptibility.py` ranks a value above that as exactly `95.0`.
Everything above the p95 flow is therefore one indistinguishable state:

| basin | flow at first clamp | max flow while clamped | ratio, all reported `p95` |
|---|---|---|---|
| cedar | 2,748 | 10,106 | **3.7×** |
| snohomish-snoqualmie | 22,860 | 76,555 | **3.3×** |
| nooksack | 14,165 | 38,182 | **2.7×** |
| **skagit** | 24,976 | 72,440 | **2.9×** |
| green-duwamish | 8,214 | 11,467 | 1.4× |
| puyallup-white | 8,503 | 8,926 | 1.0× |

Snohomish–Snoqualmie reports the identical hydrologic state at 22,860 cfs and at 76,555 cfs.
That is the whole flood.

**The interaction (FACT, and the reason fix order matters).** Once two consecutive days are
clamped, Δ24 h and Δ48 h are computed between two 95.0 values and are **identically +0**. In the
tables above, every basin's derivative reads `+0` from its second clamped day onward — through the
crest. So the collapse does not merely flatten the level: **it silences the velocity signal at
exactly the hours the velocity signal exists to cover.**

INFERENCE: a Tier 0 that adds the derivative but leaves the tail clamped would gain the 1–3 days
of §2 and then go blind for the 3–4 days that contain the crest. §7 and §8 of the milestone brief
are therefore one change, not two, and must land together.

---

## 4. Skagit had no susceptibility data for Event Zero (FACT)

`scripts/backfill_event_zero_usgs.py` `DEFAULT_SITES` is
`12100490, 12113000, 12119000, 12149000, 12200500, 12213100` — it backfilled **12200500
(Skagit at Mount Vernon)**, but the basin's configured *susceptibility* gauge is
`station:usgs:12189500` (**the Sauk**, chosen precisely because it is unregulated;
`basin.susceptibility_gauge_id`). The Sauk has a stored climatology ladder but **no December-2025
observations**, so Skagit — the basin of the event — was silently absent from every susceptibility
reconstruction above.

This is a hindcast-blocking gap of exactly the kind the register exists to catch, and it was
invisible because the surface correctly returns UNKNOWN with a reason rather than a wrong number.
Backfill of 12189500 for 2025-11-25 → 2025-12-31 was run on 2026-08-26 to close it: **7,104 rows
written**, and the resulting trajectory (above) is the strongest single piece of evidence in this
document. `DEFAULT_SITES` now derives the December site list from the seeded
`basin.susceptibility_gauge_id` values so the two can no longer drift apart.

OPEN QUESTION: whether any other basin's susceptibility gauge differs from its Event Zero
backfill site. The default list should be derived from `basin.susceptibility_gauge_id` rather
than hardcoded, so this cannot recur.

---

## 5. What this does and does not license

**Licensed now** (measured, no calibration required):
- Replacing the endpoint slope with a robust estimator — `trend.py` computes
  `rate = (pts[-1] - pts[0]) / span_h`, which the doctrine already forbids in words.
- Publishing Δ24 h and Δ48 h percentile change as a **first-class, independently interpretable**
  driver — not folded into a score.
- Preserving discrimination above p95 by some method that does not fabricate precision.
- Deriving the Event Zero backfill site list from the seeded susceptibility gauges.

**NOT licensed by this document**: any band cutoff for "RAPIDLY RISING", any weighting of the
derivative against the level, any composite score. The +40 points/48 h used in §2 is a **reporting
convention chosen for this table**, not a validated threshold — it was picked to show the ordering,
and a different value moves the lead times. A cutoff needs the multi-event validation of brief §18.

---

## 6. Reproduction

```sql
-- the ladder for one gauge
SELECT values_json FROM derived_feature
 WHERE scope_id = 'station:usgs:12149000'
   AND method_id = 'method:streamflow-doy-climatology@1.0.0'
 ORDER BY id DESC LIMIT 1;

-- the daily means it is ranked against
SELECT date_trunc('day', valid_time) d, avg(value) v
  FROM observation
 WHERE station_id = 'station:usgs:12149000' AND variable = 'flow'
   AND valid_time >= '2025-12-01' AND valid_time < '2025-12-14'
 GROUP BY 1 ORDER BY 1;
```

Rank each daily mean by linear interpolation between the ladder's `p05…p95` breakpoints, clamping
at both ends — which is what `susceptibility.py` does and is the defect in §3.
