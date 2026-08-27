# USGS instantaneous: NWIS IV vs the OGC `continuous` collection — measured parity

Measured 2026-08-27 by `scripts/compare_usgs_iv_ogc.py`, which fetches BOTH endpoints for the
same seven seeded gauges over the same window, runs each through its OWN shipped parser and
normalizer, and compares the resulting **semantic rows** — station, variable, valid time, value,
unit, datum, quality — never raw JSON. The transports serve different encodings by definition;
the only question that matters is what lands in `observation`.

Labels per `docs/research/README.md`: **FACT** = computed this session; **INFERENCE** = reasoned
from those facts; **OPEN QUESTION** = unresolved.

---

## 1. Verdict

**The two transports produce the same observations.** Over 8 independent samples (3 h window,
7 gauges, ~35 minutes apart):

| | |
|---|---|
| semantic rows, NWIS IV | **1,100** |
| semantic rows, OGC `continuous` | **1,100** |
| matched on (station, variable, valid time) | **1,100** |
| present on only one side | **0** |
| differences in value, unit, datum or quality | **0** |
| differences in `qualifier_raw` | 1,100 — `"P"` vs `"Provisional"` |
| HTTP failures | **0** |

The migration is therefore a **transport** change and not a scientific one, which is what licenses
keeping one product id (ADR-0015).

---

## 2. Every difference found, classified (FACT)

| # | difference | class | disposition |
|---|---|---|---|
| 1 | `qualifier_raw` is `"P"` on IV, `"Provisional"` on OGC | **representational only** | KEPT, deliberately. It is verbatim source text, so a stored row says which vocabulary — and therefore which parser — produced it, with no join. It is not part of the idempotency comparison, so it writes no revisions. |
| 2 | the mapped `quality` flag is `provisional` on both, but IV derives it from a qualifier letter and OGC from an `approval_status` field | **representational only** | No action. Different source fields, identical meaning, identical output. |
| 3 | a no-data reading is a provider-declared sentinel on IV (`sentinel` flag) and a JSON `null` on OGC (`unparseable` flag) | **genuine semantic difference** | DISCLOSED, not normalized away. The two APIs express absence differently and the flags name what was actually seen. No such row occurred in any sample, so it is unexercised in production; the OGC branch is covered by `derived_edge_cases.json`. |
| 4 | one request serves every gauge on IV; OGC is one request per gauge | **genuine, operational** | §4 below. |
| 5 | OGC serves GeoJSON at ~752 B per observation; IV packs a series into one array | **genuine, operational** | §4 below — it forced the live window from 72 h to 3 h. |
| 6 | in one early sample OGC served four stage timestamps at 12149000, and later a full hour at 12200500, that IV had not yet published | **transient, not systematic** | Measured again across 112 gauge-variable observations in 8 samples: **112 of 112 equal**, 0 either way. Recorded because it was real when observed, and because a single sample would have reported a 60-minute OGC advantage that does not hold. |

Nothing was classified as a legacy defect, an OGC defect, or unresolved.

---

## 3. Parity by gauge and variable (FACT)

Every seeded gauge, both variables, all 8 samples. `only` columns are rows present on one side
only; both are zero everywhere.

| gauge | stage matched | flow matched | only IV | only OGC | value/unit/datum/quality diffs |
|---|---|---|---|---|---|
| 12100490 White at R St | ✓ | ✓ | 0 | 0 | 0 |
| 12113000 Green nr Auburn | ✓ | ✓ | 0 | 0 | 0 |
| 12119000 Cedar at Renton | ✓ | ✓ | 0 | 0 | 0 |
| 12149000 Snoqualmie nr Carnation | ✓ | ✓ | 0 | 0 | 0 |
| 12189500 Sauk nr Sauk | ✓ | ✓ | 0 | 0 | 0 |
| 12200500 Skagit nr Mount Vernon | ✓ | ✓ | 0 | 0 | 0 |
| 12213100 Nooksack at Ferndale | ✓ | ✓ | 0 | 0 | 0 |

Pinned offline in CI by `tests/unit/test_usgs_transport_parity.py`, which compares captures of the
same six gauges over the same window (`tests/fixtures/providers/usgs_ogc/parity/`) against
`usgs/valid.json` and carries an anti-vacuity assertion — an empty comparison cannot pass as
identical.

---

## 4. What the transport costs (FACT)

Mean over 8 samples, 3 h window, 7 gauges:

| | NWIS IV | OGC `continuous` |
|---|---|---|
| requests | **1** | **7** (one per gauge) |
| bytes | 31,430 | 106,002 (**3.4×**) |
| seconds | 0.28 | 3.11 |
| failures | 0 | 0 |

Projected raw-archive growth at the 15-minute cadence, from the measured 752 B per observation:

| live window | per poll | per day | **per year** |
|---|---|---|---|
| 72 h (what the legacy job asked for) | 3.03 MB | 291 MB | **106 GB** |
| 6 h | 0.25 MB | 24 MB | 8.9 GB |
| **3 h (chosen)** | **0.13 MB** | **12 MB** | **4.4 GB** |

**The 72 h window did not survive the transport change.** It exists for gap recovery, and at a
15-minute cadence it was 288× redundant — every poll re-fetching three days of observations that
had not changed. That was invisible while it was one cheap request; on a per-site GeoJSON
transport it would have consumed a 10 GB R2 free tier ten times over in a year. Three hours still
recovers twelve consecutive missed polls.

The archive is content-addressed but cannot dedupe this: the window slides every poll, so no two
payloads are byte-identical. OPEN QUESTION: whether these artifacts should carry a
`retention_class` (DATA_DOCTRINE §13) — the bytes are re-derivable from USGS and the
**observations** are what the platform keeps. Not needed at 4.4 GB/year; the lever exists.

Rate limit: 28 requests/hour against a keyed ceiling of 4,000/hour.

---

## 5. Reproduction

```bash
python scripts/compare_usgs_iv_ogc.py --hours 3 --out report.json
```

Anonymous by default and writes to no database; the archive store is a temporary directory. The
registered key lives only in the Railway environment (owner directive 2026-08-24) and is not
needed for seven gauges over a few hours. `--api-key-env NAME` exists for a keyed run somewhere
that legitimately holds it.
