# Tail representation — what the p95 clamp destroys, and what can honestly replace it

Computed 2026-08-26 by `scripts/measure_tail_representation.py` against the **archived daily-values
CSVs the deployed ladders were built from** (content-addressed in R2, `retention_class` NULL), so
the analysis is bit-consistent with what production ranks against. No re-fetch, no USGS API calls.

Labels per `docs/research/README.md`: **FACT** = computed this session; **INFERENCE** = reasoned
from those facts; **OPEN QUESTION** = unresolved.

---

## 1. Verdict

Publish **three quantities** above the ladder's top breakpoint, because no single one of them is
both honest and non-collapsing:

| representation | what it is | collapses? |
|---|---|---|
| day-of-year percentile | interpolated rank in the ladder | **at p95** — dead through the whole event |
| empirical rank | a count of observations exceeded — a **fact**, not an interpolation | at rank 1, for up to 8 consecutive days |
| **ratio to p95** | dimensionless multiple of the top breakpoint | **never** |

INFERENCE: the ratio is the only continuously-varying quantity across the clamped region, so it
is what must carry the derivative; the rank is the most *informative* statement available and
fabricates nothing; the percentile stays because it is the only one comparable between gauges.
Publishing one and discarding the others loses something real in every case.

**Extending the ladder is a partial fix and cannot be the whole one.** §3 shows p98 is resolvable
at five of six gauges and p99 at three — but §4 shows four of six December peaks sit above
*every observation on record*, where no percentile of any resolution can reach them.

**Bands are not changed by any of this** and no cutoff is proposed. This restores discarded
information; it does not raise a warning level.

---

## 2. Two corrections to the earlier measurement (recorded against interest)

`tier0-measured-basis-2026-08-26.md` §3 reported clamp ratios of 2.9–3.7×. Both inputs to that
figure were wrong, in opposite directions, and the corrected figures are in §4:

1. **Wrong daily mean.** It averaged 15-minute observations over a **UTC** calendar day. A USGS
   daily mean is over the station's **local** calendar day — the definition the ladder is built
   from and the one `daily_mean_valid_time` already documents. For the Sauk on 12-11 the two
   differ by 15 % (72,440 UTC vs 62,808 local). Ranking one against a ladder of the other is a
   category error, not a rounding difference.
2. **Wrong ladder.** It ranked against a single first-clamp p95 rather than each day's own
   ladder key, and against a ladder **containing the event** (§5).

---

## 3. How far into the tail each gauge's own sample reaches (FACT)

Observations lying strictly above each candidate breakpoint, for the 12-09 ladder key. A
breakpoint needs at least **5** exceedances to be interpolated between real observations rather
than extrapolated past the end of the sample — a stated admissibility rule, not a tuned one.

| gauge | n | p96 | p97 | p98 | p99 | p99.5 |
|---|---|---|---|---|---|---|
| 12100490 (Puyallup) | 85 | 4 ✗ | 3 ✗ | 2 ✗ | 1 ✗ | 1 ✗ |
| 12113000 (Green) | 450 | 18 ✓ | 14 ✓ | 9 ✓ | 5 ✓ | 3 ✗ |
| 12119000 (Cedar) | 400 | 16 ✓ | 12 ✓ | 8 ✓ | 4 ✗ | 2 ✗ |
| 12149000 (Snoqualmie) | 475 | 19 ✓ | 15 ✓ | 10 ✓ | 5 ✓ | 3 ✗ |
| 12189500 (Sauk) | 495 | 20 ✓ | 15 ✓ | 10 ✓ | 5 ✓ | 3 ✗ |
| 12213100 (Nooksack) | 300 | 12 ✓ | 9 ✓ | 6 ✓ | 3 ✗ | 2 ✗ |

**Puyallup supports no extra breakpoint at all** — its approved record begins in 2009. Its
existing p95 already rests on only 4 exceedances. Any extension must therefore be decided
**per ladder from its own sample**, never as a global constant, and a gauge that supports
nothing must keep p95 and say so.

---

## 4. What the clamp costs, measured correctly (FACT)

Station-local daily means, each ranked in its own day-of-year ladder built from the record
**before** water year 2026 (§5). "Distinct states" counts how many different values each
representation reports across the clamped days.

| gauge | clamped days | flow across the clamp | percentile | rank | ratio |
|---|---|---|---|---|---|
| 12119000 (Cedar) | 13 | 2,626 → 10,065 = **3.83×** | 1 | 4 | **13** |
| 12149000 (Snoqualmie) | 8 | 16,200 → 80,565 = **4.97×** | 1 | 7 | **8** |
| 12189500 (Sauk) | 10 | 10,987 → 62,808 = **5.72×** | 1 | 7 | **10** |
| 12213100 (Nooksack) | 8 | 15,041 → 34,072 = 2.27× | 1 | 6 | **8** |

The Sauk reports the identical hydrologic state at 10,987 cfs and at 62,808 cfs.

Day-over-day change through the clamp, which is the signal §3 of the measured basis showed is
silenced:

- **percentile**: `[0, 0, 0, 0, 0, 0, 0, 0, 0]` — identically zero at every gauge, every day.
- **ratio** (Sauk): `[+1.30, +1.41, +1.23, −3.45, +0.25, +0.16, +0.92, −1.60, −0.06]` — never zero.
- **rank** (Cedar): `[−7, 0, 0, 0, 0, 0, 0, 0, 0, +1, +6, +1]` — **eight consecutive zeros**,
  because the gauge is pinned at rank 1 for eight days. The rank is exact but it saturates.

**FACT: at the crest, four of six gauges exceed every observation in their own day-of-year
window across the whole period of record.** The Sauk's 62,808 cfs is the highest 09–13 December
daily mean in 490 approved observations spanning 1911–2026; the previous highest was 37,400 cfs
on 2004-12-11. That is a **1.68× exceedance of the record**, and no percentile — p95, p99, or
p99.9 — can express it. The rank can, exactly, and it is the more useful sentence: *"higher than
every 9–13 December daily mean on record; the previous highest was 37,400 cfs in 2004."*

---

## 5. The deployed ladder contains the event it ranks (FACT — and this gates the hindcast)

The archived record includes **approved** December 2025 daily means at **five of the six**
gauges. The distribution each event value is ranked against therefore contains that value.

| gauge | p95 with WY2026 | p95 without | shift | ratio, with → without |
|---|---|---|---|---|
| 12100490 (Puyallup) | 7,532 | 5,991 | **+25.7 %** | 1.34× → 1.69× |
| 12189500 (Sauk) | 13,630 | 12,550 | +8.6 % | 4.59× → 4.99× |
| 12113000 (Green) | 7,245 | 6,822 | +6.2 % | 1.60× → 1.70× |
| 12213100 (Nooksack) | 14,020 | 13,260 | +5.7 % | 2.44× → 2.58× |
| 12149000 (Snoqualmie) | — | — | — | no approved WY2026 rows |

The bias **understates** severity — a self-included extreme raises its own p95 — so this is not
a result that flatters the platform. It is still look-ahead: the ranking uses values that did not
exist at the knowledge time being replayed. Puyallup is the worst case because its record is
short (n=85, from 2009), so five December-2025 days are 6 % of the entire sample.

**INFERENCE, and it is a blocking constraint**: any Event Zero hindcast must rank against a
ladder built from data available *before* the event. The vintage is not a presentational detail
to be exposed — brief §11 — it changes the number by up to a quarter at the gauge with the
shortest record. This is contradiction-register entry **X8**, now quantified rather than open.

OPEN QUESTION: whether the operational (non-hindcast) surface should also exclude the current
water year. Excluding it discards real information about a changing record; including it lets an
event damp its own signal. This document does not settle it and nothing yet depends on the answer.

---

## 6. Cost

Carrying the top 20 (value, year) pairs beside each ladder key so a rank can name what it beat:
**331 B per day key, 118 KB per gauge, 711 KB for all six**. Neon's free tier is 0.5 GB; this is
0.14 % of it. Thirty pairs would be needed to cover the whole above-p95 region at n=495.

---

## 7. Reproduction

```bash
CASCADE_DB_URL="$NEON_DIRECT_URL" CASCADE_OBJECT_STORE=s3 CASCADE_S3_BUCKET=cascadia-raw \
  CASCADE_S3_ENDPOINT="https://<account>.r2.cloudflarestorage.com" \
  python scripts/measure_tail_representation.py
```
