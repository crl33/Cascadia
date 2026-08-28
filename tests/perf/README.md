# tests/perf — the `/viz/basins` amplification baseline

Measured **2026-08-26**, before any optimisation. This folder exists to make one claim provable
in both directions: `/viz/basins` is slow because of how MANY statements it issues, not because
any of them is expensive — and whatever is done about that, the body it returns must not change.

> **Outcome, 2026-08-26.** 120 statements → **13**, on both drivers, with the stored bodies
> byte-for-byte unchanged. Everything below is the measurement as it was taken; where each of
> the 120 went is in [What happened to the 120](#what-happened-to-the-120) at the end. The
> `baseline/` bodies were NOT regenerated — they are what proves the answer did not move.
>
> **Regenerated once, 2026-08-27**, when `nwis/stat` was retired for the OGC statistics API
> (`docs/research/nwis-stat-successor-2026-08-27.md`). The semantic diff was **four fields, all
> provenance**, on the cross-check ref of each gauge — `source_id`, `product_id`, `method_id` and
> `label`. No percentile, band, score, rank, seasonal multiple, velocity, driver value or
> confidence moved; the `climatology_p50_disagreement` driver kept its exact value because the
> two published sources agree to the cent at the fixture's day-of-year.
>
> **Regenerated again, 2026-08-28**, for the SNOTEL basin-attribution correction. The diff is three
> lines, all Skagit and all traceable to two pillows NRCS itself places outside every seeded basin:
> the SWE site count 7 → 5, the PREC label `6 point site(s) at 1680–6490 ft` → `4 ... at 1680–4310
> ft`, and the `snotel_precip_14d_percent_of_median` driver **61.4 → 48.3**. That driver ships
> `direction: context_not_scored`, so no band, score or susceptibility state moved — all six basins
> are byte-identical on those. The number changing is the point: it was wrong before.
>
> The same regeneration refreshed two things that had gone stale earlier and that no test guards:
> `total_queries` 13 → **14**, which is the growth-rank split (`595fc92`) reading the growth
> reference as its own prefetch, and the per-station observation timestamps in
> `*.queries.json`, which follow the instantaneous fixtures replaced in `e7ba235`. Neither came
> from the statistics migration. If the count moves again, it is a regression until explained.

Nothing here is imported by `cascade_api`, `cascade_core` or `cascade_hydrology`. The
instrumentation attaches from the outside at measurement time and detaches again, and
`tests/perf/test_query_budget.py::test_instrumentation_does_not_change_the_response` asserts that
the endpoint answers identically with it and without it.

## Run it

```bash
python -m tests.perf.capture_baseline            # scratch SQLite, (re)writes baseline/
python -m tests.perf.capture_baseline --check    # re-measure, diff against baseline/, write nothing
python -m tests.perf.capture_baseline --db "$URL" --check   # same, on a migrated scratch PostgreSQL
python -m pytest tests/perf -q                   # the budget + the semantic baseline, offline
```

The PostgreSQL half is a throwaway database, created and dropped for the measurement — the local
`cascadia` container database is left alone. The DSN below is the local `cascadia-pg` dev
container's, the same one `docs/research/pg-migration-verification-2026-08-24.md` and
`tests/unit/test_worker_queue.py` already use; production credentials live in Neon and Railway and
appear in no file in this repository.

```bash
docker exec cascadia-pg psql -U postgres -c "CREATE DATABASE cascadia_perf_baseline"
docker exec cascadia-pg psql -U postgres -d cascadia_perf_baseline -c "CREATE EXTENSION postgis"
CASCADE_ALEMBIC_URL="postgresql+psycopg://postgres:dev@127.0.0.1:5433/cascadia_perf_baseline" \
  alembic -c infra/migrations/alembic.ini upgrade head
python -m tests.perf.capture_baseline --check \
  --db "postgresql+psycopg://postgres:dev@127.0.0.1:5433/cascadia_perf_baseline"
docker exec cascadia-pg psql -U postgres -c "DROP DATABASE cascadia_perf_baseline"
```

## The measurement

Six basins, one outlet forecast point each, at a pinned knowledge time (`as_of=2026-08-24T23:00:00Z`).
The database is seeded and ingested from the checked-in provider payloads, so every number below
is a function of the code alone.

| | `/viz/basins` | `/basins/basin:skagit/state` |
|---|---:|---:|
| statements executed | **120** | **22** |
| distinct (SQL text **and** bound params) | 103 | 20 |
| exact repeats (same text, same params) | **17** | 2 |
| distinct SQL statement **texts** | **12** | 12 |
| response body | 76,902 B, 6 items, 60 provenance refs | 13,672 B, 1 item, 11 refs |
| local PostgreSQL 18 p50, n=10 | 409 ms | 71 ms |
| production, measured 2026-08-25 | **21.8 s** | — |

The counts are **identical on SQLite and on PostgreSQL**, and both drivers return a body that is
byte-for-byte identical once `generated_at` is normalised. The count is decided by `Knowledge`
and the assemblers; the driver only decides what each one costs.

**120 executions of 12 distinct statement texts.** That is the whole finding stated as compactly
as it can be. Per-statement cost is not the problem — 120 × ~176 ms of production round trip is
21 s, and 120 × ~3.4 ms locally is 0.4 s. The same work, the same rows, a 50× difference in what
a round trip costs.

### Where the 120 go

Two statements are issued once per request. The other 118 are **20 per basin** (18 at
`basin:snohomish-snoqualmie`, where agreement short-circuits before reading NWM):

```
  2  once per request      basins, products
  9  per basin             outlet lookup + susceptibility (4) + forcing (4)
 11  per forecast point    assess_point (8) + agreement (3)
```

## Inventory

`class` is the brief's classification: **(a)** exact duplicate, **(b)** per-basin N+1 that could
be one set-based query, **(c)** per-forecast-point N+1, **(d)** genuinely singular.

On `/viz/basins` a basin has exactly one outlet point, so (b) and (c) have the same multiplicity
here. They are still distinguished, because the loop each sits in is different: (b) is
`assemble.basin_envelope`'s own loop, (c) is inside `assess_point` / `agreement.assess`, which
`river_envelope` also drives once per forecast point — so a (c) fix pays twice.

| n | table | what it fetches | reader | call site | class |
|--:|---|---|---|---|---|
| 1 | `basin` | every basin, ordered by id | `basins` | `routes.py:134 viz_basins` | (d) |
| 1 | `source_product` | the whole product registry, for cadence/grace/labels | `products` | `assemble.py:357 basin_envelope` | (d) |
| 6 | `forecast_point` | the outlet point, by LID parsed out of `basin.outlet_fp_id` | `forecast_point_by_lid` | `assemble.py:361 basin_envelope` | (b) |
| 6 | `threshold` | every threshold row for the point with `effective_from <= T` | `thresholds` | `assemble.py:162 assess_point` | (c) |
| 6 | `observation` | 14 days of the threshold-basis variable, to take the last row | `observations` | `knowledge.py:105 latest_observation` | (c) |
| 6 | `station` | the observation's station, for its `external_id` | `station` | `assemble.py:187 assess_point` | (c) |
| 6 | `observation` | the *other* variable at the primary's exact `valid_time` | `observations` | `assemble.py:201 assess_point` | (c) |
| 6 | `observation` | the 6-hour window behind T, for rate of rise | `observations` | `assemble.py:219 assess_point` | (c) |
| 6 | `forecast_run` | latest OFFICIAL run at the point known at T | `latest_forecast_run` | `assemble.py:261 assess_point` | (c) |
| 6 | `forecast_value` | that run's full hydrograph | `forecast_values` | `assemble.py:266 assess_point` | (c) |
| 6 | `forecast_run` | latest OFFICIAL run at the point known at T — **already fetched above** | `latest_forecast_run` | `agreement.py:1050 assess` | **(a)** |
| 6 | `forecast_value` | that same run's hydrograph — **already fetched above** | `forecast_values` | `agreement.py:1055 assess` | **(a)** |
| 5 | `forecast_run` | latest NWM medium-range cycle at the point | `latest_forecast_run` | `agreement.py:948 latest_model_cycle` | (c) |
| 5 | `derived_feature` | that cycle's stored member series | `derived_features` | `agreement.py:951 latest_model_cycle` | (c) |
| 6 | `derived_feature` | day-of-year flow percentile at the basin's gauge | `derived_features` | `knowledge.py:220 latest_derived_feature` ← `susceptibility.py:280` | (b) |
| 6 | `station` | the susceptibility gauge station, for its `external_id` | `station` | `susceptibility.py:292 assess` | **(a)** ×5 |
| 6 | `derived_feature` | basin SNOTEL SWE context | `derived_features` | `knowledge.py:220 latest_derived_feature` ← `susceptibility.py:374` | (b) |
| 6 | `derived_feature` | basin SNOTEL 14-day precipitation context | `derived_features` | `knowledge.py:220 latest_derived_feature` ← `susceptibility.py:379` | (b) |
| 6 | `derived_feature` | 72-h basin-mean QPF p50 (selects the cycle) | `derived_features` | `forcing.py:471 assess` | (b) |
| 12 | `derived_feature` | the same cycle's pointwise p90 and p10, one query each | `derived_features` | `forcing.py:488 assess` | (b) |
| 6 | `derived_feature` | snow-level context rows | `derived_features` | `forcing.py:499 assess` | (b) |
| **120** | | | | | |

### (a) The exact duplicates — 17

Same SQL text, same bound parameters, same request. Seventeen of the 120 statements answer a
question that has already been answered.

| ×  | table | first issued at | issued again at | why |
|--:|---|---|---|---|
| 6 | `forecast_run` | `assemble.py:261 assess_point` | `agreement.py:1050 assess` | `assess_point` reads the official run, and `PointAssessment` carries the thresholds it derived out to the caller but not the run itself, so `agreement.assess` reads it again. |
| 6 | `forecast_value` | `assemble.py:266 assess_point` | `agreement.py:1055 assess` | consequence of the above: the same `run_id`, the same hydrograph, twice. |
| 5 | `station` | `assemble.py:187 assess_point` | `susceptibility.py:292 assess` | the same station id at five of six basins. Not a duplicate at `basin:skagit`, whose susceptibility gauge is the Sauk (12189500) while the outlet MVEW1 gauges at 12200500. |

The `station` pair has a second cause worth writing down, because it is not visible in the code:

> **SQLAlchemy's identity map holds weak references.** `Knowledge.station` is `session.get(Station,
> id)`, which is free on a second call *only while something still holds the loaded object*. In
> `assess_point` the `Station` is read for one attribute (`external_id`) and goes out of scope on
> the next line, so it is collected and the next `session.get` for that same id re-queries.
> Measured directly: two `k.station(same_id)` calls with the object dropped in between issue 2
> statements; with a strong reference alive, the second issues 0.

That makes `station` a request-scoped memo away from free — exactly the memoisation inside one
`Knowledge` instance the brief permits, since a `Knowledge` is constructed per request and its
reads are already knowledge-time filtered.

### (b) Per-basin N+1 — 54 statements, 9 per basin

Every one of these asks the same question of six different scope ids and could be one set-based
query per question:

- `forecast_point_by_lid` — six single-row lookups by `lid`. The six LIDs are known before the
  loop starts (`basin.outlet_fp_id` on rows already in hand from `k.basins()`).
- **susceptibility, 3 × 6** — `streamflow_doy_percentile` keyed by gauge station id, plus
  `basin_swe_percent_of_median` and `snotel_precip_14d_percent_of_median` keyed by basin id. All
  three go through `latest_derived_feature`, which is `derived_features` + "take the last row":
  the same `(feature, method_id)` with six different `scope_id`s.
- **forcing, 4 × 6** — the 72-h QPF p50, then p90 and p10 **as two separate queries in a
  `for percentile in (90, 10)` loop**, then snow level. Same `feature`/`method_id`/`window`
  family, six scope ids, and within a basin three of them differ only in the percentile
  encoded in the feature name.

`derived_feature` alone is **47 of the 120**. Nothing about it is expensive; there are 90 rows in
the whole table on this fixture. It is asked 47 times.

### (c) Per-forecast-point N+1 — 62 statements, 11 per point

`assess_point` issues eight and `agreement.assess` three. `/viz/basins` drives it once per basin,
but `river_envelope` drives the same function once per forecast point, so this is the group that
also decides what `/viz/rivers` costs.

Three of the eight are `observation` reads at the **same station**, differing only in variable and
time window:

| # | variable | window | used for |
|--:|---|---|---|
| 1 | threshold basis (`stage` or `flow`) | `T − 14 d … T` | the latest observation |
| 2 | the other variable | `primary.valid_time … primary.valid_time` | the secondary quantity |
| 3 | threshold basis | `T − 6 h … T` | rate of rise |

Query 3's window is a **subset** of query 1's — the same station, same variable, same knowledge
filter — so the 6-hour trend rows are already inside the rows query 1 returned.

### (d) Genuinely singular — 2

`k.basins()` and `k.products()`. Both are already once-per-request and both are reference data.
`products` is the whole `source_product` table (11 rows) and is threaded correctly through
`basin_envelope` → `assess_point` → `forcing`/`susceptibility` as a dict; it is the pattern the
rest of the endpoint does not follow.

## What is NOT the problem

Worth stating explicitly, so the optimisation does not go looking in the wrong place:

- **No query is slow.** 120 statements against a local PostgreSQL cost ~300 ms of SQL wall time in
  total, over a database of 540 observations, 648 forecast values and 90 derived features.
- **No query is missing an index.** Every one of the 12 shapes filters on an indexed leading
  column: `ix_observation_station_id`, `ix_forecast_run_fp_id`, `ix_forecast_value_run_id`,
  `ix_threshold_fp_id`, `ix_derived_feature_scope_time (scope_id, feature, valid_time)`,
  `forecast_point`'s unique index on `lid`, and primary keys for `station` / `basin`.
  `source_product` is an eleven-row full scan, once per request. (An index that would *help* is a
  different question from one that is *missing* — a composite `(station_id, variable, valid_time)`
  on `observation` would tighten the three per-point reads — but neither is where 21 s went.)
- **The hydrology is not expensive.** `/viz/basins` end to end is 409 ms locally with 120 queries
  in it; the arithmetic on top of the rows is not what the extra 21 s in production is made of.
- **There is no lazy-load surprise.** All 120 statements are attributable to an explicit
  `Knowledge` reader; none is emitted by relationship loading. (`tests/perf/instrument.py` reports
  an unattributable statement as `(outside Knowledge)`; there are none.)

## Attack order, against the owner's list

1. **Remove exact duplicates** — 17 statements (−14%), no semantics involved: carry the official
   run and its values out of `assess_point` on `PointAssessment` the way `thresholds` already is,
   and memoise `station` for the life of one `Knowledge`.
2. **Batch related reads** — the three `observation` reads per point are one read of the widest
   window, sliced in memory; the four `forcing` reads per basin are one read of that feature
   family; `latest_derived_feature`'s three susceptibility reads are one.
3. **Eliminate per-basin / per-forecast-point N+1** — every remaining group is "the same question,
   six scope ids". `WHERE scope_id IN (...)` plus a group-by in Python preserves the knowledge
   filter exactly, because the filter (`available_at <= as_of`) is on the row, not on the scope.
4. **Fetch common reference state once** — `products` already is; `basins`, the outlet points and
   the thresholds can join it.
5/6. **Cache or precompute** — not reached by this baseline, and on these numbers it should not
   need to be. Steps 1–3 are arithmetic, not architecture.

Knowledge-time semantics survive all of 1–4 untouched: batching changes the `IN` list, never the
`available_at <= as_of` predicate, never the `ORDER BY revision_seq` that picks the highest
revision known at T. Any change that touches those predicates is out of scope for this work.

## The discrepancy with the production measurement

Production, 2026-08-25: ~120 queries, **92 distinct, 28 exact repeats**. This harness: **120
queries, 103 distinct, 17 exact repeats**. The totals agree exactly; the split does not, and the
production database is not reachable from here, so the difference is recorded rather than
explained away. Two candidates, both testable by the orchestrator against production:

- **A different grouping key.** Distinct here means identical SQL text *and* identical bound
  parameters. Grouping by statement text alone gives **12**, not 92; grouping by
  text + params gives 103. If production grouped by a normalised statement plus a subset of the
  parameters, the eleven-query gap is definitional rather than real.
- **A seventh station.** If production's `basin:skagit` susceptibility gauge resolved to the
  outlet's own station rather than the Sauk, that `station` pair becomes a sixth exact duplicate
  — one of the eleven, not all of them.

Whichever it is, the number the budget test pins is the total, which matches.

## Files

| file | what it is |
|---|---|
| `instrument.py` | `QueryRecorder` (engine events) + `attributed()` (call-site attribution). Read-only. |
| `normalize.py` | canonicalises a response body for byte-for-byte diffing; documents what may be normalised and what may not. |
| `harness.py` | the ingested scratch database — the P3 integration ingest plus `usgs.fetch_iv`. |
| `capture_baseline.py` | writes / re-checks everything under `baseline/`. |
| `test_query_budget.py` | the regression gate: query budget + semantic baseline. |
| `test_normalize.py` | the comparator's own tests. An unverified comparator would report "identical" for a change that was not, and hand a silent regression a green tick. |
| `baseline/<endpoint>.json` | the captured response body, verbatim. This is the semantic contract. |
| `baseline/<endpoint>.read_time_fields.json` | what `generated_at` / `as_of` / `time.valid` were at capture, so normalising them does not make them invisible. |
| `baseline/<endpoint>.queries.json` | every statement, in execution order and grouped by identity — SQLite paramstyle, produced by the offline harness. |
| `baseline/<endpoint>.queries.postgres.json` | the same, from a migrated scratch PostgreSQL 18 + PostGIS: production paramstyle, identical counts. |
| `baseline/summary.json` | the four headline numbers per endpoint. |

The query logs store each SQL text **once** in `statement_texts` and reference it by index from
`distinct_statements[].statement_ref` and `in_order[].statement_ref` — there are twelve texts
behind 120 executions, and writing each out 103 times would bury the finding in repetition of it.
The canonical (normalised) form of a body is not stored: it is `normalize.canonical_json()` of
the body beside it, and a stored copy could only ever drift from its source.
`python -m tests.perf.capture_baseline --check` prints the diff.

`baseline/` is evidence, not cache. The point of the optimisation is that those bodies do not
change; regenerating them to make a test pass is falsifying the measurement.

## Appendix — all 120 statements in execution order

Full SQL text and bound parameters for each are in `baseline/viz_basins.queries.postgres.json`
(PostgreSQL paramstyle, as production issues them) and `baseline/viz_basins.queries.json`
(SQLite). The clock parameter (`2026-08-24 23:00:00`, on every knowledge-filtered read) and the
product-id lists are elided from the scope column below.

| # | table | reader | call site | scope key (bound params, clock + product ids elided) |
|---:|---|---|---|---|
| 1 | `basin` | `basins` | `routes.py:134 viz_basins` | `—` |
| 2 | `source_product` | `products` | `assemble.py:357 basin_envelope` | `—` |
| 3 | `forecast_point` | `forecast_point_by_lid` | `assemble.py:361 basin_envelope` | `RNTW1` |
| 4 | `threshold` | `thresholds` | `assemble.py:162 assess_point` | `fp:nwps:RNTW1` |
| 5 | `observation` | `observations` | `knowledge.py:105 latest_observation` | `station:usgs:12119000, stage` |
| 6 | `station` | `station` | `assemble.py:187 assess_point` | `station:usgs:12119000` |
| 7 | `observation` | `observations` | `assemble.py:201 assess_point` | `station:usgs:12119000, flow` |
| 8 | `observation` | `observations` | `assemble.py:219 assess_point` | `station:usgs:12119000, stage` |
| 9 | `forecast_run` | `latest_forecast_run` | `assemble.py:261 assess_point` | `fp:nwps:RNTW1` |
| 10 | `forecast_value` | `forecast_values` | `assemble.py:266 assess_point` | `5` |
| 11 | `forecast_run` | `latest_forecast_run` | `agreement.py:1050 assess` | `fp:nwps:RNTW1` |
| 12 | `forecast_value` | `forecast_values` | `agreement.py:1055 assess` | `5` |
| 13 | `forecast_run` | `latest_forecast_run` | `agreement.py:948 latest_model_cycle` | `fp:nwps:RNTW1` |
| 14 | `derived_feature` | `derived_features` | `agreement.py:951 latest_model_cycle` | `nwm_mr_member_flow_series, fp:nwps:RNTW1, method:nwm-member-series@2.0` |
| 15 | `derived_feature` | `derived_features` | `knowledge.py:220 latest_derived_feature` | `streamflow_doy_percentile, station:usgs:12119000, method:susceptibilit` |
| 16 | `station` | `station` | `susceptibility.py:292 assess` | `station:usgs:12119000` |
| 17 | `derived_feature` | `derived_features` | `knowledge.py:220 latest_derived_feature` | `basin_swe_percent_of_median, basin:cedar, method:snotel-basin-swe-cont` |
| 18 | `derived_feature` | `derived_features` | `knowledge.py:220 latest_derived_feature` | `snotel_precip_14d_percent_of_median, basin:cedar, method:snotel-precip` |
| 19 | `derived_feature` | `derived_features` | `forcing.py:471 assess` | `basin_qpf_72h_pointwise_p50, basin:cedar, method:basin-qpf@1.0.0, 72h` |
| 20 | `derived_feature` | `derived_features` | `forcing.py:488 assess` | `basin_qpf_72h_pointwise_p90, basin:cedar, method:basin-qpf@1.0.0, 72h` |
| 21 | `derived_feature` | `derived_features` | `forcing.py:488 assess` | `basin_qpf_72h_pointwise_p10, basin:cedar, method:basin-qpf@1.0.0, 72h` |
| 22 | `derived_feature` | `derived_features` | `forcing.py:499 assess` | `basin_snow_level_pointwise_p50, basin:cedar, method:basin-snow-level@1` |
| 23 | `forecast_point` | `forecast_point_by_lid` | `assemble.py:361 basin_envelope` | `AUBW1` |
| 24 | `threshold` | `thresholds` | `assemble.py:162 assess_point` | `fp:nwps:AUBW1` |
| 25 | `observation` | `observations` | `knowledge.py:105 latest_observation` | `station:usgs:12113000, flow` |
| 26 | `station` | `station` | `assemble.py:187 assess_point` | `station:usgs:12113000` |
| 27 | `observation` | `observations` | `assemble.py:201 assess_point` | `station:usgs:12113000, stage` |
| 28 | `observation` | `observations` | `assemble.py:219 assess_point` | `station:usgs:12113000, flow` |
| 29 | `forecast_run` | `latest_forecast_run` | `assemble.py:261 assess_point` | `fp:nwps:AUBW1` |
| 30 | `forecast_value` | `forecast_values` | `assemble.py:266 assess_point` | `—` |
| 31 | `forecast_run` | `latest_forecast_run` | `agreement.py:1050 assess` | `fp:nwps:AUBW1` |
| 32 | `forecast_value` | `forecast_values` | `agreement.py:1055 assess` | `—` |
| 33 | `forecast_run` | `latest_forecast_run` | `agreement.py:948 latest_model_cycle` | `fp:nwps:AUBW1` |
| 34 | `derived_feature` | `derived_features` | `agreement.py:951 latest_model_cycle` | `nwm_mr_member_flow_series, fp:nwps:AUBW1, method:nwm-member-series@2.0` |
| 35 | `derived_feature` | `derived_features` | `knowledge.py:220 latest_derived_feature` | `streamflow_doy_percentile, station:usgs:12113000, method:susceptibilit` |
| 36 | `station` | `station` | `susceptibility.py:292 assess` | `station:usgs:12113000` |
| 37 | `derived_feature` | `derived_features` | `knowledge.py:220 latest_derived_feature` | `basin_swe_percent_of_median, basin:green-duwamish, method:snotel-basin` |
| 38 | `derived_feature` | `derived_features` | `knowledge.py:220 latest_derived_feature` | `snotel_precip_14d_percent_of_median, basin:green-duwamish, method:snot` |
| 39 | `derived_feature` | `derived_features` | `forcing.py:471 assess` | `basin_qpf_72h_pointwise_p50, basin:green-duwamish, method:basin-qpf@1.` |
| 40 | `derived_feature` | `derived_features` | `forcing.py:488 assess` | `basin_qpf_72h_pointwise_p90, basin:green-duwamish, method:basin-qpf@1.` |
| 41 | `derived_feature` | `derived_features` | `forcing.py:488 assess` | `basin_qpf_72h_pointwise_p10, basin:green-duwamish, method:basin-qpf@1.` |
| 42 | `derived_feature` | `derived_features` | `forcing.py:499 assess` | `basin_snow_level_pointwise_p50, basin:green-duwamish, method:basin-sno` |
| 43 | `forecast_point` | `forecast_point_by_lid` | `assemble.py:361 basin_envelope` | `NKSW1` |
| 44 | `threshold` | `thresholds` | `assemble.py:162 assess_point` | `fp:nwps:NKSW1` |
| 45 | `observation` | `observations` | `knowledge.py:105 latest_observation` | `station:usgs:12213100, stage` |
| 46 | `station` | `station` | `assemble.py:187 assess_point` | `station:usgs:12213100` |
| 47 | `observation` | `observations` | `assemble.py:201 assess_point` | `station:usgs:12213100, flow` |
| 48 | `observation` | `observations` | `assemble.py:219 assess_point` | `station:usgs:12213100, stage` |
| 49 | `forecast_run` | `latest_forecast_run` | `assemble.py:261 assess_point` | `fp:nwps:NKSW1` |
| 50 | `forecast_value` | `forecast_values` | `assemble.py:266 assess_point` | `4` |
| 51 | `forecast_run` | `latest_forecast_run` | `agreement.py:1050 assess` | `fp:nwps:NKSW1` |
| 52 | `forecast_value` | `forecast_values` | `agreement.py:1055 assess` | `4` |
| 53 | `forecast_run` | `latest_forecast_run` | `agreement.py:948 latest_model_cycle` | `fp:nwps:NKSW1` |
| 54 | `derived_feature` | `derived_features` | `agreement.py:951 latest_model_cycle` | `nwm_mr_member_flow_series, fp:nwps:NKSW1, method:nwm-member-series@2.0` |
| 55 | `derived_feature` | `derived_features` | `knowledge.py:220 latest_derived_feature` | `streamflow_doy_percentile, station:usgs:12213100, method:susceptibilit` |
| 56 | `station` | `station` | `susceptibility.py:292 assess` | `station:usgs:12213100` |
| 57 | `derived_feature` | `derived_features` | `knowledge.py:220 latest_derived_feature` | `basin_swe_percent_of_median, basin:nooksack, method:snotel-basin-swe-c` |
| 58 | `derived_feature` | `derived_features` | `knowledge.py:220 latest_derived_feature` | `snotel_precip_14d_percent_of_median, basin:nooksack, method:snotel-pre` |
| 59 | `derived_feature` | `derived_features` | `forcing.py:471 assess` | `basin_qpf_72h_pointwise_p50, basin:nooksack, method:basin-qpf@1.0.0, 7` |
| 60 | `derived_feature` | `derived_features` | `forcing.py:488 assess` | `basin_qpf_72h_pointwise_p90, basin:nooksack, method:basin-qpf@1.0.0, 7` |
| 61 | `derived_feature` | `derived_features` | `forcing.py:488 assess` | `basin_qpf_72h_pointwise_p10, basin:nooksack, method:basin-qpf@1.0.0, 7` |
| 62 | `derived_feature` | `derived_features` | `forcing.py:499 assess` | `basin_snow_level_pointwise_p50, basin:nooksack, method:basin-snow-leve` |
| 63 | `forecast_point` | `forecast_point_by_lid` | `assemble.py:361 basin_envelope` | `WRAW1` |
| 64 | `threshold` | `thresholds` | `assemble.py:162 assess_point` | `fp:nwps:WRAW1` |
| 65 | `observation` | `observations` | `knowledge.py:105 latest_observation` | `station:usgs:12100490, flow` |
| 66 | `station` | `station` | `assemble.py:187 assess_point` | `station:usgs:12100490` |
| 67 | `observation` | `observations` | `assemble.py:201 assess_point` | `station:usgs:12100490, stage` |
| 68 | `observation` | `observations` | `assemble.py:219 assess_point` | `station:usgs:12100490, flow` |
| 69 | `forecast_run` | `latest_forecast_run` | `assemble.py:261 assess_point` | `fp:nwps:WRAW1` |
| 70 | `forecast_value` | `forecast_values` | `assemble.py:266 assess_point` | `6` |
| 71 | `forecast_run` | `latest_forecast_run` | `agreement.py:1050 assess` | `fp:nwps:WRAW1` |
| 72 | `forecast_value` | `forecast_values` | `agreement.py:1055 assess` | `6` |
| 73 | `forecast_run` | `latest_forecast_run` | `agreement.py:948 latest_model_cycle` | `fp:nwps:WRAW1` |
| 74 | `derived_feature` | `derived_features` | `agreement.py:951 latest_model_cycle` | `nwm_mr_member_flow_series, fp:nwps:WRAW1, method:nwm-member-series@2.0` |
| 75 | `derived_feature` | `derived_features` | `knowledge.py:220 latest_derived_feature` | `streamflow_doy_percentile, station:usgs:12100490, method:susceptibilit` |
| 76 | `station` | `station` | `susceptibility.py:292 assess` | `station:usgs:12100490` |
| 77 | `derived_feature` | `derived_features` | `knowledge.py:220 latest_derived_feature` | `basin_swe_percent_of_median, basin:puyallup-white, method:snotel-basin` |
| 78 | `derived_feature` | `derived_features` | `knowledge.py:220 latest_derived_feature` | `snotel_precip_14d_percent_of_median, basin:puyallup-white, method:snot` |
| 79 | `derived_feature` | `derived_features` | `forcing.py:471 assess` | `basin_qpf_72h_pointwise_p50, basin:puyallup-white, method:basin-qpf@1.` |
| 80 | `derived_feature` | `derived_features` | `forcing.py:488 assess` | `basin_qpf_72h_pointwise_p90, basin:puyallup-white, method:basin-qpf@1.` |
| 81 | `derived_feature` | `derived_features` | `forcing.py:488 assess` | `basin_qpf_72h_pointwise_p10, basin:puyallup-white, method:basin-qpf@1.` |
| 82 | `derived_feature` | `derived_features` | `forcing.py:499 assess` | `basin_snow_level_pointwise_p50, basin:puyallup-white, method:basin-sno` |
| 83 | `forecast_point` | `forecast_point_by_lid` | `assemble.py:361 basin_envelope` | `MVEW1` |
| 84 | `threshold` | `thresholds` | `assemble.py:162 assess_point` | `fp:nwps:MVEW1` |
| 85 | `observation` | `observations` | `knowledge.py:105 latest_observation` | `station:usgs:12200500, stage` |
| 86 | `station` | `station` | `assemble.py:187 assess_point` | `station:usgs:12200500` |
| 87 | `observation` | `observations` | `assemble.py:201 assess_point` | `station:usgs:12200500, flow` |
| 88 | `observation` | `observations` | `assemble.py:219 assess_point` | `station:usgs:12200500, stage` |
| 89 | `forecast_run` | `latest_forecast_run` | `assemble.py:261 assess_point` | `fp:nwps:MVEW1` |
| 90 | `forecast_value` | `forecast_values` | `assemble.py:266 assess_point` | `3` |
| 91 | `forecast_run` | `latest_forecast_run` | `agreement.py:1050 assess` | `fp:nwps:MVEW1` |
| 92 | `forecast_value` | `forecast_values` | `agreement.py:1055 assess` | `3` |
| 93 | `forecast_run` | `latest_forecast_run` | `agreement.py:948 latest_model_cycle` | `fp:nwps:MVEW1` |
| 94 | `derived_feature` | `derived_features` | `agreement.py:951 latest_model_cycle` | `nwm_mr_member_flow_series, fp:nwps:MVEW1, method:nwm-member-series@2.0` |
| 95 | `derived_feature` | `derived_features` | `knowledge.py:220 latest_derived_feature` | `streamflow_doy_percentile, station:usgs:12189500, method:susceptibilit` |
| 96 | `station` | `station` | `susceptibility.py:292 assess` | `station:usgs:12189500` |
| 97 | `derived_feature` | `derived_features` | `knowledge.py:220 latest_derived_feature` | `basin_swe_percent_of_median, basin:skagit, method:snotel-basin-swe-con` |
| 98 | `derived_feature` | `derived_features` | `knowledge.py:220 latest_derived_feature` | `snotel_precip_14d_percent_of_median, basin:skagit, method:snotel-preci` |
| 99 | `derived_feature` | `derived_features` | `forcing.py:471 assess` | `basin_qpf_72h_pointwise_p50, basin:skagit, method:basin-qpf@1.0.0, 72h` |
| 100 | `derived_feature` | `derived_features` | `forcing.py:488 assess` | `basin_qpf_72h_pointwise_p90, basin:skagit, method:basin-qpf@1.0.0, 72h` |
| 101 | `derived_feature` | `derived_features` | `forcing.py:488 assess` | `basin_qpf_72h_pointwise_p10, basin:skagit, method:basin-qpf@1.0.0, 72h` |
| 102 | `derived_feature` | `derived_features` | `forcing.py:499 assess` | `basin_snow_level_pointwise_p50, basin:skagit, method:basin-snow-level@` |
| 103 | `forecast_point` | `forecast_point_by_lid` | `assemble.py:361 basin_envelope` | `CRNW1` |
| 104 | `threshold` | `thresholds` | `assemble.py:162 assess_point` | `fp:nwps:CRNW1` |
| 105 | `observation` | `observations` | `knowledge.py:105 latest_observation` | `station:usgs:12149000, stage` |
| 106 | `station` | `station` | `assemble.py:187 assess_point` | `station:usgs:12149000` |
| 107 | `observation` | `observations` | `assemble.py:201 assess_point` | `station:usgs:12149000, flow` |
| 108 | `observation` | `observations` | `assemble.py:219 assess_point` | `station:usgs:12149000, stage` |
| 109 | `forecast_run` | `latest_forecast_run` | `assemble.py:261 assess_point` | `fp:nwps:CRNW1` |
| 110 | `forecast_value` | `forecast_values` | `assemble.py:266 assess_point` | `2` |
| 111 | `forecast_run` | `latest_forecast_run` | `agreement.py:1050 assess` | `fp:nwps:CRNW1` |
| 112 | `forecast_value` | `forecast_values` | `agreement.py:1055 assess` | `2` |
| 113 | `derived_feature` | `derived_features` | `knowledge.py:220 latest_derived_feature` | `streamflow_doy_percentile, station:usgs:12149000, method:susceptibilit` |
| 114 | `station` | `station` | `susceptibility.py:292 assess` | `station:usgs:12149000` |
| 115 | `derived_feature` | `derived_features` | `knowledge.py:220 latest_derived_feature` | `basin_swe_percent_of_median, basin:snohomish-snoqualmie, method:snotel` |
| 116 | `derived_feature` | `derived_features` | `knowledge.py:220 latest_derived_feature` | `snotel_precip_14d_percent_of_median, basin:snohomish-snoqualmie, metho` |
| 117 | `derived_feature` | `derived_features` | `forcing.py:471 assess` | `basin_qpf_72h_pointwise_p50, basin:snohomish-snoqualmie, method:basin-` |
| 118 | `derived_feature` | `derived_features` | `forcing.py:488 assess` | `basin_qpf_72h_pointwise_p90, basin:snohomish-snoqualmie, method:basin-` |
| 119 | `derived_feature` | `derived_features` | `forcing.py:488 assess` | `basin_qpf_72h_pointwise_p10, basin:snohomish-snoqualmie, method:basin-` |
| 120 | `derived_feature` | `derived_features` | `forcing.py:499 assess` | `basin_snow_level_pointwise_p50, basin:snohomish-snoqualmie, method:bas` |

---

## What happened to the 120

Removed **2026-08-26**, in the owner's order: exact duplicates, then batching, then the per-basin
and per-point N+1s, then the common reference reads. Steps 5 and 6 — cache or precompute — were
**not reached and deliberately not taken**: at 13 statements a cache would be a correctness risk
bought for nothing, and every cache has an invalidation bug waiting in it.

| step | what was done | `/viz/basins` |
|---|---|---:|
| — | baseline | **120** |
| 1 | `Knowledge` memoises its readers for the life of one request | **97** |
| 2–4 | set-based readers + one prefetch per surface | **13** |

Step 1 removed 23, not the 17 exact duplicates alone: memoising `observations` by its window let
the six-hour trend read be answered out of the fourteen-day read it already sits inside, which
was the sixth statement per point and never showed up as an exact repeat because the two ask for
different windows.

### Why memoising inside `Knowledge` is not a cache

A `Knowledge` is constructed per request and every read it performs is already filtered to one
knowledge time. Within one instance a reader is a **pure function of its arguments** — the same
question at the same T has one answer — so remembering it cannot change any answer, and `as_of`
is not in any memo key because it cannot vary. Nothing survives the request. The project rule
that forbids process-local caches of knowledge-filtered rows is about state that outlives the
question; this does not.

### The thirteen, and what each replaced

| # | statement | replaced | issued by |
|--:|---|---:|---|
| 1 | every basin | 1 | `routes.viz_basins` |
| 2 | the product registry | 1 | `assemble.basin_envelope` |
| 3 | the outlet points, by lid | 6 | `assemble._prefetch_basins` |
| 4 | every station named by the request | 11 | `assemble._prefetch_basins` |
| 5 | thresholds at every point | 6 | `assemble.prefetch_points` |
| 6 | the latest official run at every point | 12 | `assemble.prefetch_points` |
| 7 | those runs' hydrographs | 12 | `assemble.prefetch_points` |
| 8 | the latest observation per (station, variable) | 6 | `assemble.prefetch_points` |
| 9 | the trend windows and the secondary instants | 12 | `assemble.prefetch_points` |
| 10 | the latest NWM cycle at every point | 5 | `agreement.prefetch` |
| 11 | those cycles' member series | 5 | `agreement.prefetch` |
| 12 | QPF p50/p90/p10 and snow level, every basin | 24 | `forcing.prefetch` |
| 13 | flow percentile + SNOTEL SWE + SNOTEL precip | 18 | `susceptibility.prefetch` |

Statement 4 is the only one assembled outside the surface that reads it, and the README's
station finding is why: two surfaces read stations and they are frequently the same rows, so the
union is read once and both find their rows already in hand. `susceptibility.gauge_ids` exists so
that the assembler can ask which stations rather than re-deciding it.

**The count no longer depends on how many basins are asked for.** `/basins/{id}/state` — one
basin through the same assembler — issues the same thirteen, where it issued 22 before.

### What is data-dependent, and the ceiling

Three of the thirteen are conditional on what is in the database rather than on the code: the
member series is not read where no NWM cycle is known, the secondary-variable observation is not
read where there is no observation, and the climatology fallback IS read where a flow percentile
is missing. That last one is batched for exactly the gauges that will take it — worked out from
rows already read, so it costs no statement when no gauge needs it. **The ceiling the code can
reach is 14**; the budget is 16.

### Measured, before and after

Same ingested database, same knowledge time, `n=15`, this machine.

| | statements | p50 | SQL wall time |
|---|---:|---:|---:|
| `/viz/basins`, PostgreSQL 18 + PostGIS, before | 120 | 416 ms | 245 ms |
| `/viz/basins`, PostgreSQL 18 + PostGIS, after | **13** | **95 ms** | **47 ms** |
| `/basins/basin:skagit/state`, PostgreSQL, before | 22 | 85 ms | 63 ms |
| `/basins/basin:skagit/state`, PostgreSQL, after | **13** | **54 ms** | **35 ms** |
| `/viz/rivers?basin=skagit`, PostgreSQL, before | 11 | 44 ms | 26 ms |
| `/viz/rivers?basin=skagit`, PostgreSQL, after | **9** | **33 ms** | **25 ms** |

Local latency is not the number that matters and is recorded only to show the SQL half shrinking
with the count. Production is where the round trip is ~176 ms: 120 × 176 ms was the 21.8 s, and
13 statements is the claim to re-measure there.

### How the correctness was checked

- **The stored bodies.** `python -m tests.perf.capture_baseline --check`, on SQLite and on a
  migrated scratch PostgreSQL 18 + PostGIS: `body identical to the baseline` for both endpoints
  on both drivers, `generated_at` the only normalised field.
- **Replay at every knowledge edge.** Every distinct `available_at` / `effective_from` in the
  database, plus one second either side, × six read endpoints = 90 probes. Before and after are
  identical on both drivers, and the 90 probes carry 75 distinct answers — a probe set that
  never varied would prove nothing.
- **Batched vs singular.** `tests/unit/test_knowledge_batching.py` compares every set-based
  reader against the per-scope reader it replaces, on data built to make them disagree if they
  can: revisions inserted out of order, two forecast products at one point, two methods
  computing one feature, rows on the far side of the knowledge clock.
- **Prefetch purity.** `test_the_prefetches_are_pure_warm_up` deletes every prefetch and asserts
  the body does not move while the count does, at two knowledge times.
