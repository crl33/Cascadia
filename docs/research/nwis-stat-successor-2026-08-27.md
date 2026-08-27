# Eliminating the last WaterServices dependency: what replaces `nwis/stat`?

Date: 2026-08-27. Author: this workspace. Status: decision recorded, implementation pending.

Companion to `usgs-ogc-instantaneous-parity-2026-08-27.md` (ADR-0015). That migration moved the
live instantaneous path off WaterServices. `nwis/stat` is the only caller left.

The brief for this phase forbids assuming a one-for-one replacement exists. It does not. This
document records what was measured, not what was expected.

## 1. What Cascadia actually consumes today (§2)

Traced through `stats_client.fetch_published_doy_stats` → `stats_parser.parse_nwis_stat_rdb` →
`climatology.published_climatology` → `stats_jobs.run_fetch_daily_percentile` →
`hydrology.susceptibility.assess`.

| Question | Answer |
|---|---|
| Fields read | `PublishedDoyStat.percentiles` (9 levels), `count`, `begin_yr`, `end_yr` |
| Fields **consumed** | **`p50` only.** `climatology.p50_disagreement` reads `values[50]`; nothing reads p20/p80 |
| Meaning | USGS-published day-of-year percentiles of daily-**mean** discharge (00060), over USGS's own period of record |
| Where it lands | `values_json["cross_check"]` on the `streamflow_doy_percentile` row |
| Effect on output | Driver `climatology_p50_disagreement` (`lowers_confidence`) when \|fraction\| > 0.10; quality `climatology_disagreement` → `_one_level_down(confidence)` |
| Value or confidence? | **Confidence only.** No percentile, band, rank, multiple or score reads it |
| If unavailable today | `except FetchError: continue` → `cross_check: None`, quality `no_published_cross_check`. Already degrades gracefully |
| Fetch cadence | Annual (`BUILD_CADENCE_SECONDS = 31_536_000`) |
| Data cost | ~42–45 KB × 6 sites × 1/yr ≈ **260 KB/yr** |
| Provenance identity | `product:usgs-daily-stats`, `src:usgs-nwis-stat`, `method:usgs-published-doy-stats@1.0.0`, quality `["cross_check_only"]`, ref `usgs-nwis-stat:<site>:<begin>-<end>` |

The module docstring already states the architecture correctly: `product:usgs-ogc-daily` is the
dependency; `product:usgs-daily-stats` is the cross-check and **never** a dependency.

## 2. What the cross-check is scientifically for, and what it is not (§3)

Cascade builds its own day-of-year ladder from the OGC `daily` collection. USGS publishes its own
ladder. The comparison can only detect a difference between **two computations over USGS daily
values**. Three axes of independence, kept separate because they are routinely conflated:

| Axis | `nwis/stat` | `observationNormals` |
|---|---|---|
| Independent **observations** | No — both sides are USGS daily values | No |
| Independent **implementation** | Yes — USGS's own code | Yes — USGS's own code |
| Independent **record membership** | Yes — a different, shorter, differently curated record | Largely no — tracks the modern record Cascade reads |

**The check is not evidence about the river.** It is evidence about Cascade's percentile
construction. Any surface wording implying USGS "confirms" a river state would be false.

## 3. Re-probing the successor (§4)

The 2026-08-24 note in `stats_client.py` says `observationNormals` served no discharge normals at
any seed gauge. **That is no longer true.** Re-probed 2026-08-27:

```
GET https://api.waterdata.usgs.gov/statistics/v0/observationNormals
    ?monitoring_location_id=USGS-12189500&normal_type=DOY&parameter_code=00060
```

- Serves `00060` (ft^3/s), parent statistic `00003/Mean`, `time_of_year_type: day_of_year`.
- Per day it returns `arithmetic_mean`, `maximum`, `median`, `minimum`, and a `percentile`
  record carrying `percentiles: [5,10,25,50,75,90,95]` with a parallel `values` array and
  `sample_count`.
- `parameter_code` filtering is supported and cuts the payload from ~2.4 MB to ~415 KB.

### Coverage matches at every gauge that matters, and regresses at one that does not

| Gauge | OGC percentile days | sample_count range |
|---|---|---|
| 12119000 | 366 | 20–81 |
| 12149000 | 366 | 24–96 |
| 12213100 | 366 | 15–60 |
| 12113000 | 366 | 22–90 |
| 12100490 | 366 | 4–17 |
| 12189500 | 366 | 25–100 |
| **12200500** | **none** | — |

The first six are the basin susceptibility gauges (`stats_canary.GAUGES`), and the successor
covers all six exactly as `nwis/stat` did.

**12200500 is a real coverage regression, and it is not identical.** `nwis/stat` publishes a full
366-day discharge ladder for the Skagit at Mount Vernon (1941–2026, n=86, verified in
`tests/fixtures/providers/usgs_stats/stat_12200500.rdb`); `observationNormals` serves nothing
there. An earlier draft of this document called the coverage identical — that was wrong, read off
`stats_canary.GAUGES` (which excludes 12200500) rather than checked against the legacy fixture.

It has no production consequence: `run_build_climatology` iterates `_susceptibility_gauges`, and
the Skagit basin's susceptibility gauge is the unregulated Sauk (12189500), not the Mount Vernon
outlet. No basin reads a climatology for 12200500, so no cross-check is lost. If a future phase
ever gives Mount Vernon its own climatology, it will have no published cross-check and must say
so rather than borrow one.

### The levels served are exactly Cascade's ladder

`climatology.PERCENTILES = (5, 10, 25, 50, 75, 90, 95)`. `observationNormals` serves precisely
these. `nwis/stat` additionally serves p20/p80, which the RDB parser never even reads
(`RDB_PERCENTILE_COLUMNS` lists exactly the seven).

## 4. It is not value-identical (§7, §8)

Compared all 366 day-of-year records at each of the 6 gauges, per time series (2196 day pairs).

- p50 equal on **1213/2196** days.
- 9806 level-value differences across the 7 shared levels.
- 762 `sample_count` mismatches.

Two distinct causes, which must not be reported as one:

**(a) Published precision.** `nwis/stat` rounds to 3 significant figures; `observationNormals`
carries more (`372.0` vs `372.2`, `8430.0` vs `8432.0`). Same statistic, different rounding.

**(b) Different period of record.** Magnitudes of \|Δp50\|:

| Gauge | median | p95 | max | days > 10% | sample_count Δ (ogc − nwis) |
|---|---|---|---|---|---|
| 12119000 | 0.000% | 0.472% | 3.247% | 0 | 0…+1 |
| 12149000 | 0.000% | 0.246% | 0.490% | 0 | 0 |
| 12213100 | 0.000% | 0.146% | 0.385% | 0 | 0 |
| **12113000** | **4.305%** | **14.286%** | **25.225%** | **53** | **+6…+26** |
| 12100490 | 0.000% | 0.382% | 0.485% | 0 | 0 |
| 12189500 | 0.360% | 2.228% | 5.597% | 0 | +1…+2 |

At 12113000 the two USGS products disagree with **each other**, on the same river, past the 10%
threshold Cascadia uses to lower confidence — purely because `observationNormals` computes over
6–26 more years. Cascade's own climatology there spans 1936–2026 (n=450 = ±2 days × 90 years);
`observationNormals` reports 90 samples for the day; `nwis/stat` reports 65 (1962–2026).

**Period-of-record identity cannot be preserved.** `observationNormals` publishes **no
`begin_year`/`end_year` at all** — only `sample_count`. The existing provenance ref
`usgs-nwis-stat:12113000:1962-2026` has no successor-side equivalent.

### `observationNormals` emits literal `nan`

735 non-numeric percentile entries at 12100490 (the 17-year record) and 2 at 12213100 (Feb 29),
serialised as the string `"nan"`. A parser that calls `float()` without guarding will silently
produce NaN percentiles. `nwis/stat` omits the column instead.

## 5. Effect on the live confidence signal

Production `cross_check` values on 2026-08-26, and what each would have been under the successor:

| Gauge | cascade p50 | nwis p50 | ogc p50 | disagreement now | under successor |
|---|---|---|---|---|---|
| 12100490 | 703.5 | 704.0 | 703.5 | −0.0007 | 0.0000 |
| **12113000** | 273.5 | 295.0 | 273.5 | **−0.0729** | **0.0000** |
| 12119000 | 155.5 | 155.0 | 155.0 | +0.0032 | +0.0032 |
| 12149000 | 792.0 | 793.0 | 793.5 | −0.0013 | −0.0019 |
| 12189500 | 1950.0 | 1950.0 | 1940.0 | 0.0000 | +0.0052 |
| 12213100 | 1480.0 | 1500.0 | 1500.0 | −0.0133 | −0.0133 |

**No gauge crosses the 0.10 threshold under either source**, so no confidence outcome changes
today. The migration is downstream-invariant at the present state.

But the largest live signal in the system (−7.29%) goes to exactly zero. That single number is
the whole decision, so it is worth being precise about what it means. Across the **full** ladder
on 2026-08-25 the two candidates are comparable — Cascade vs successor median \|Δ\| **1.264%**,
Cascade vs `nwis/stat` median \|Δ\| **1.607%**. The successor is not uniformly "closer". It is
closer *at 12113000*, and only there, and specifically because it shares that gauge's longer
record. This is a record-membership effect, not agreement manufactured by re-reading one's own
rows: at 12189500 the successor disagrees with Cascade (+0.0052) where `nwis/stat` agreed exactly.

## 6. Decision table (§5, §6)

| Strategy | Independence provided | Coverage | Provenance honesty | Verdict |
|---|---|---|---|---|
| **A. Migrate to `observationNormals`** | USGS's own implementation, over a record close to Cascade's | All 6 susceptibility gauges; loses 12200500, which nothing reads | Requires new ids and a ref without years | **Chosen** |
| B. Recompute a second ladder from OGC daily inside Cascadia | **None** — same rows, same codebase | 7/7 | Would look like verification and be none | Rejected |
| C. Redesign around what the successor supports | — | — | — | Folded into A |
| D. Retire the cross-check entirely | n/a | n/a | Honest, but discards a working regression detector | Rejected, with a caveat below |

**Why not B.** This is the trap the brief names: a second calculation over the exact same rows
creates the appearance of independent verification with none of the substance. It would agree by
construction and fail silently in exactly the cases the check exists to catch.

**Why not D.** The check has a real job: catching a regression in Cascade's percentile
construction — interpolation, ±window, approval filtering, leap-day, units, datum. That job is
worth ~260 KB/yr. Retiring it because its *current* readings are quiet would discard a detector
because it has not yet fired.

**Why A.** `observationNormals` is the supported successor on the same host Cascadia already
depends on (`api.waterdata.usgs.gov`), it needs no new credential or recurring service, it serves
exactly Cascade's seven percentile levels at all six susceptibility gauges, and by holding the
record roughly fixed it isolates the axis the check actually claims to test — implementation —
rather than confounding it with record membership.

## 7. What must change with it, and what must not

Required by the successor's actual shape:

1. **New provenance identity.** `product:usgs-ogc-normals`, `src:usgs-ogc-statistics`, and
   `method:usgs-published-doy-stats@2.0.0`. The `@1.0.0` rows stay as they are; they were true.
2. **The ref loses its years.** `usgs-nwis-stat:<site>:<begin>-<end>` has no equivalent. The
   successor ref must carry what is actually published — `sample_count` — and must not invent
   years. This is a visible provenance change and is the honest one.
3. **`nan` must be rejected at parse time**, never coerced.
4. **No silent fallback to WaterServices.** A successor failure yields `no_published_cross_check`,
   the same state that already exists.

Frozen, per §11 — none of this touches: day-of-year windowing, the percentile ladder,
record-context construction, the growth reference, station-local day handling, the p5/p95 clamp,
susceptibility bands, state-change windows, the trend estimator, or score semantics.

## 8. One finding deliberately not acted on in this phase

The check lowers confidence when Cascade's p50 differs from the published p50 by >10%. At
12113000 that fires — under `nwis/stat` it reads −7.29%, within threshold but the largest in the
system — because **Cascade has 26 more years of record than the published table**. Lowering
confidence because Cascadia holds *more* data than the comparator is backwards.

This is a calibration question about what the threshold means, not a transport question. Changing
it would modify score semantics, which §11 freezes. Recorded here for the calibration phase.
