# PG migration verification — 2026-08-24

End-to-end verification of the Phase 0 work landed by four builder agents (Alembic
migration + PostGIS, procrastinate worker, obstore raw archive, deploy scaffold).
Verified on 2026-08-24 (macOS, Python 3.14, PostgreSQL 18.6 + PostGIS 3.6 in the local
`cascadia-pg` container, port 5433). Every proof below ran against a **freshly created**
database `cascadia_v` — nothing was inherited from the builders' own verification runs.
Live network was used only for `run-once` and the queue proof (public NWPS/USGS APIs);
everything else is offline or local-Postgres.

## 1. What was claimed vs what proved true

| Claim (builder) | Evidence (this pass) |
|---|---|
| Alembic env at `infra/migrations`, revision 0001 creates full schema + PostGIS on a fresh DB | `bash scripts/migrate.sh` on empty `cascadia_v`: `Running upgrade  -> 0001` clean; `postgis_version()` → `3.6 USE_GEOS=1 USE_PROJ=1 USE_STATS=1` |
| `observation` partitioned by RANGE(valid_time), monthly, composite PK, natural-key unique per partition | `pg_class.relkind = 'p'`; 16 partitions (`observation_y2025m11` … `observation_y2027m01` + `observation_default`); parent PK `(id, valid_time)`; `uq_observation_revision` present and materialized per partition (`observation_y2026m08_product_id_station_id_variable_valid_t_key`) |
| Rows route to the correct monthly partition | All 3 432 live-ingested rows landed in `observation_y2026m08` (valid_time 2026-08-21 10:15 → 2026-08-24 10:00); no other partition holds rows |
| Partition helper exists | `pg_proc` has `cascade_ensure_month_partitions` |
| `seed` loads both LOD geometries and point geoms | seed output `{"sources": 3, "products": 3, "basins": 6, "stations": 6, "forecast_points": 6, "basin_geometries": 12}`; `basin_geometry` = 12 rows (6 basins × lod state/basin); `station` 6/6 geoms non-null, `forecast_point` 6/6 geoms non-null (the reported flush bug fix holds — the last forecast_point has its geom) |
| Procrastinate schema applies, is idempotent | `migrate.sh` step: `{"schema": "applied"}`; explicit rerun: `{"schema": "already-applied"}`; 4 `procrastinate_*` tables present |
| One task per job, lock = queueing_lock = job name, retry engages via JobFailed | Code inspected (`apps/worker/src/cascade_worker/queue.py`); registration confirmed at CLI startup (crons `10 */6 * * *`, `*/30 * * * *`, `*/15 * * * *`) |
| Deferred task executes through `run_job` with unchanged job_run bookkeeping | Queue proof (§2.4): defer `nwps.fetch_thresholds` → `run_worker_async(wait=False)` drains → `procrastinate_jobs` id 1 `succeeded` attempts 1 → **new `job_run` row id 4** (`ok=t`, `rows_written=0` — idempotent re-fetch minutes after run-once) |
| `run-once` unchanged, works on Postgres | Live: thresholds 24 rows, forecast 219 rows, USGS IV 3 432 rows, all `ok=true`; `job_run` rows 1–3; raw artifacts archived on disk (47 files under `data/raw/`) |
| Worker runtime uses the settings-selected object store | `runtime.py:15,34` imports and calls `store_from_settings(settings)` — the obstore builder's "not wired" concern was already resolved by the worker builder |
| API serves the same read-only contract surface on Postgres | §2.5: all probes 200, `POST /basins` → 405, `/system/health` → `status: ok`, both providers healthy, all three products `current` |
| as_of replay never shows current data | `?as_of=2026-01-01T00:00:00Z` → `observed=null`, `observed_category=unknown` ("no official NWPS thresholds known for this point"), thresholds/forecast null, provenance `source_kind=UNKNOWN freshness=missing`, `time.mode=past` |
| Envelopes validate against `cascade_contracts` | `ContractEnvelope.model_validate_json` OK for basin state, forecast-point state, and the as_of replay (all contract version 1.1.0); `SceneSummary.model_validate_json` OK for `/scene/summary` (classes live in `cascade_contracts.visualization`) |
| pg-marked tests pass and are properly gated | Without `CASCADE_TEST_PG_URL`: 5 skipped in the offline run. With it: `5 passed, 69 deselected in 6.45s` (3 migration + 2 worker-queue) |
| Offline suite intact | `python -m pytest -q` → **69 passed, 5 skipped** before this pass and again after it (was 40 before Phase 0; the growth is the builders' 29 new offline tests) |
| No provider import inside apps/api | grep: zero imports of provider packages; the only "provider" hits in `routes.py` are the health-endpoint vocabulary (`_provider_state`, `providers` dict) |
| No secrets in the tree | grep over tracked + untracked (14 modified, 19 new files) for AKIA/api_key=/token=/password=/private-key patterns: none. The only password-shaped value is compose-dev's documented `${POSTGRES_PASSWORD:-dev}` fallback (loopback-only; see gaps) |
| UTCDateTime everywhere a timestamp column exists | All 13 timestamp columns in `models.py` are `UTCDateTime`. Migration 0001 declares them `sa.DateTime()`, which renders the identical naive-UTC `TIMESTAMP` DDL (`UTCDateTime.impl = DateTime`) — consistent, not a violation, but hand-migration authors must keep the UTC convention by hand |

## 2. Exact commands and outcomes

All from the repository root, venv active. Quote the path (it contains a space).

### 2.1 Offline suite

```
python -m pytest -q
# 69 passed, 5 skipped in 26.91s        (skips = the 5 pg-gated tests)
```

### 2.2 Fresh database migration + seed

```
docker exec cascadia-pg psql -U postgres -c "DROP DATABASE IF EXISTS cascadia_v; CREATE DATABASE cascadia_v;"
export CASCADE_DB_URL=postgresql+psycopg://postgres:dev@127.0.0.1:5433/cascadia_v
bash scripts/migrate.sh
# INFO  [alembic.runtime.migration] Running upgrade  -> 0001, Initial schema: models,
#       PostGIS geometry, monthly-partitioned observation.
# {"schema": "applied"}
python -m cascade_worker seed
# {"sources": 3, "products": 3, "basins": 6, "stations": 6, "forecast_points": 6, "basin_geometries": 12}
python -m cascade_worker apply-queue-schema
# {"schema": "already-applied"}
python -m cascade_worker run-once            # live network, ~10 s
# nwps.fetch_thresholds ok rows=24 | nwps.fetch_forecast ok rows=219 | usgs.fetch_iv ok rows=3432
python -m cascade_worker queue-status
# {"totals": {"jobs_count": 0, "todo": 0, ... }, "queues": []}
```

Note: `run-once`'s forecast `rows_written=219` counts `forecast_run` parents plus
`forecast_value` children (6 + 213 in this run); table counts below are the split.

### 2.3 psql assertions on `cascadia_v`

| Check | Result |
|---|---|
| `observation` relkind | `p` (partitioned) |
| partitions | 16: `y2025m11..y2027m01` + `observation_default` |
| row routing | `SELECT tableoid::regclass, count(*) ... GROUP BY 1` → only `observation_y2026m08`: 3 432 rows, valid_time 2026-08-21 10:15 → 2026-08-24 10:00 |
| `basin_geometry` | 12 rows, 6 basins, lods `state`=6 / `basin`=6 |
| point geoms | station 6/6 non-null, forecast_point 6/6 non-null |
| value tables | threshold 24, forecast_value 213, forecast_run 6 |
| queue schema | `procrastinate_events/jobs/periodic_defers/workers` present |
| helper | `cascade_ensure_month_partitions` in `pg_proc` |
| partition-local unique | `observation_y2026m08_product_id_station_id_variable_valid_t_key` |

### 2.4 Queue proof (real task through procrastinate)

```python
app = create_queue_app(Settings.from_env())          # CASCADE_DB_URL -> cascadia_v
async with app.open_async():
    job_id = await app.tasks["nwps.fetch_thresholds"].defer_async()   # -> 1
    await app.run_worker_async(wait=False)           # drains and returns
```

Before: 3 `job_run` rows. After: `procrastinate_jobs` id 1 `succeeded` (attempts 1) and
`job_run` id 4 `nwps.fetch_thresholds ok=t rows_written=0` — the queue path drives the
identical bookkeeping as `run-once`, and the re-fetch was correctly idempotent (0 new
threshold rows minutes after the first fetch).

### 2.5 API against Postgres

`uvicorn cascade_api.main:app --port 8901` (background, `CASCADE_DB_URL` → `cascadia_v`);
killed after the probes.

| probe | status | bytes |
|---|---|---|
| `/system/health` | 200 | 413 — `status: ok`, usgs+nwps `healthy`, all 3 products `current` |
| `/basins` | 200 | 2234 |
| `/basins/basin:skagit/state` | 200 | 2587 |
| `/viz/rivers?basin=basin:skagit` | 200 | 3729 |
| `/forecast-points/MVEW1/state` | 200 | 3729 |
| `/scene/summary?band=basin&basin=basin:skagit` | 200 | 6390 |
| `/forecast-points/MVEW1/state?as_of=2026-01-01T00:00:00Z` | 200 | 1139 — replay: `observed=null`, category `unknown` with reason, provenance `UNKNOWN/missing`, `time.mode=past`; **no current data leaked** |
| `POST /basins` | **405** | — |

Contract validation (piped saved bodies through `cascade_contracts.visualization`):
`ContractEnvelope` OK for `BasinVisualizationState` 1.1.0, `RiverVisualizationState` 1.1.0
(current and as_of-replay); `SceneSummary` OK for the scene probe.

### 2.6 pg-marked tests

```
CASCADE_TEST_PG_URL=postgresql+psycopg://postgres:dev@127.0.0.1:5433/cascadia_v \
  python -m pytest -q -m pg
# 5 passed, 69 deselected in 6.45s
```

(The 3 migration tests create and drop scratch databases `cascadia_migtest_<hex>` on the
server; the 2 worker tests leave one succeeded stub row in `cascadia_v.procrastinate_jobs`.)

## 3. Fixes made in this pass

| Fix | File |
|---|---|
| Stale "Known gap: `python -m cascade_worker worker` … crash-loops" note removed — the subcommand landed (a builder cross-timing artifact) and was proven live here; replaced with a resolved note pointing at this report | `infra/CONTEXT.md` |

No code fixes were required: every mechanical claim by the four builders that this pass
could test reproduced cleanly on a fresh database.

## 4. Open gaps (verified still open, carried forward)

1. **Partition horizon ends 2027-01.** Nothing schedules `cascade_ensure_month_partitions`;
   rows past the horizon land in `observation_default`. Wire pg_partman on Neon (ADR-0013)
   or a periodic helper call before ingestion approaches 2027-01.
2. **`apply-queue-schema` is existence-gated**, not versioned: it will not run
   procrastinate's incremental migrations across a future procrastinate upgrade.
3. **`observation.revision_of` has no FK on PostgreSQL** (cannot target non-unique `id` on
   a partitioned table); the revision link is application-maintained there. SQLite keeps
   the ORM FK.
4. **Identity on the partitioned parent requires PostgreSQL ≥ 17** (local 18.6, Neon
   PG17/18 fine; older managed PG is not).
5. **JSON columns are `json`, not `jsonb`** — deliberate ORM parity; changing is a
   coordinated model+migration change.
6. **`ObstoreStore.put` conflict handling proven only against LocalStore's
   `AlreadyExistsError`**; if live R2/S3 surfaces the create-mode conflict as a
   PreconditionError (HTTP 412) that path raises instead of no-op. Needs a canary once R2
   credentials exist.
7. **Deploy scaffold not re-proven end-to-end here**: `docker compose up` still blocked
   locally by the `cascadia-pg` 5433 port clash; amd64/cp314 wheel availability and the
   Railway path remain unproven until the first real deploy. `/system/health` 500s on an
   unseeded first deploy until the runbook's one-shot seed runs.
8. **Prod-only deps pinned in `infra/Dockerfile`**, not in package pyprojects — the two
   lists will drift unless moved when M2 closes.
9. **ADR-0003 operational periodic tasks missing** (stalled-job retry, procrastinate_jobs
   pruning); also the leftover succeeded queue rows (builders' stub + this pass's proof)
   stay until pruning lands.
10. **`${POSTGRES_PASSWORD:-dev}` fallback in `docker-compose.dev.yml`** — documented,
    loopback-only, dev-parity value identical to the local verification container; flagged
    against the env-var-names-only rule rather than silently accepted.
11. **Shared `cascadia` dev DB lost its spike-era rows** (dropped by the migration builder
    so Alembic could own the schema); the on-disk raw archive is intact. `NOLOGIN` roles
    `ingest_writer`/`api_reader` exist on the shared server from roles.sql testing.
12. **station/forecast_point `geom` are migration-owned and unmapped in the ORM** — SQL
    access only; hand-migration authors must respect `PG_ONLY_GEOMETRY_COLUMNS` (documented
    in `models.py`, `env.py`, `infra/migrations/CONTEXT.md`).
13. **Migration DDL timestamps are `sa.DateTime()`** — same rendered DDL as `UTCDateTime`,
    but the UTC-naive convention lives only in the ORM layer; future hand migrations must
    not introduce `timestamptz` columns without a coordinated model change.

## M2 robustness batch (orchestrator verification, 2026-08-24)

The batch's verify agent completed every leg but was cut off before reporting; the
orchestrator re-ran the decisive checks: offline suite 72 passed / 6 skipped; pg suite 6
passed (incl. the new partition-horizon maintenance test); ruff clean; lint-imports 3
contracts kept / 0 broken; contracts drift gate clean; web contracts:check + 29 vitest +
production build green; `.github/workflows/ci.yml` parses with jobs backend / backend-pg /
web / e2e-stub / gitleaks; docker image rebuilt (arm64) and dual-process supervision proven
live twice (builder: kill -9 → container down; orchestrator: killed worker pid 8 → container
exited 1 within 15 s). AFOS archiver verified by live dry-run (ESFSEW 5, FFASEW 30, FLWSEW 93
products, FLSSEW et al. counted in the upload manifest); upload to `cascadia-event-zero`
executed by the orchestrator with credentials. Railway start command switched to the
supervised `all` mode. Known follow-ups: e2e-stub CI job is CI-verified-only; action major
tags unverified against github.com; gitleaks-action needs a license only if the repo moves
to an org.

## P1 web-client integration gates — 2026-08-24 (integrator pass)

Integration and gating of the four P1 builder workstreams in `apps/web` (timeline/replay,
hydrograph + provenance popover, search-to-flight + attribution, contract-first E2E specs).
All gates ran on the assembled tree after integration fixes; commands from `apps/web` unless
noted. Nothing outside `apps/web`, `tests/e2e` and this file was touched (plus
`scripts/sync-pages-fixtures.sh` run for `functions/fixtures`).

### Integration changes

- Spec-contract testids wired: `timeline` (bar cluster, was `timeline-bar`), `snap-to-now`
  (was `timeline-now`), `as-of-banner` (was `replay-banner`; copy now leads with
  "AS OF <knowledge time UTC>"), `hydrograph-axis-unit`, `hydrograph-threshold-line`,
  `hydrograph-threshold-label` (labels now carry value + unit, + datum on stage basis),
  `hydrograph-series-observed`/`-forecast` (were `hydrograph-observed`/`-forecast`),
  `hydrograph-register-boundary`, `inspector-*` row testids on the provenance popover
  (`inspector-source|kind|truth|product|method|issued|valid|retrieved|freshness|quality|raw-artifact`)
  and `inspector-close`.
- Popover SOURCE row now reads `source_id · product_id — label` (spec contract); its unit
  test updated accordingly.
- `npm run e2e` now builds with `VITE_API_BASE=http://localhost:8000`: the production-build
  default became same-origin for Cloudflare Pages, which silently pointed the E2E preview at
  :4173 (every API call 404 → 11/12 specs failed). Root cause, not a flake.
- Two pre-P1 specs (`skagit-flight`, `search`) asserted the legacy `?basin=` URL grammar;
  updated 3 assertions to the canonical `?sel=` serialization (unit tests had already migrated).
- AGENTS.md updates: `api/` may-import now blesses `state` (asOf keying, established by the
  timeline workstream), `panels/` row reflects Hydrograph + popover (LayerInspector deleted),
  timeline AGENTS.md records the e2e testid contract. README "does not do" list updated.

### Gates (in order, all green)

| Gate | Command | Result |
|---|---|---|
| Types | `npx tsc --noEmit` | clean |
| Lint | `npm run lint` (boundary rule incl.) | clean |
| Unit | `npx vitest run` | 16 files passed, 1 skipped (live-gated); 97 tests passed, 8 skipped |
| Build | `npm run build` | clean; `index-*.js` 4,490 kB (gzip 1,217 kB), CSS 36 kB (gzip 8 kB) — single-chunk spike layout unchanged, under the 2.5 MB shell+scene brotli target (PERFORMANCE §2); shell-only 250 kB budget unmeasurable until the scene chunk is split (documented deferral in vite.config.ts) |
| Doctor | `npx react-doctor@latest --verbose` | 90/100 before AND after (2 pre-existing warnings: js-combine-iterations in search-reducer.ts, unused-export in BasemapProvider.ts) |
| E2E (stub) | `npm run e2e` | **12/12 passed** (skagit-flight 4, timeline-scrub 3, hydrograph 2, provenance 2, search 1), 1.5 m, SwiftShader renderer ready |

### Live smoke (real backend, https://cascadia.papsukkal.com)

- `curl` probes all HTTP 200: `/system/health` (status ok, both providers healthy),
  `/search?q=skag`, `/forecast-points/MVEW1/state?as_of=2026-08-22T06:00:00Z`,
  `/forecast-points/AUBW1/runs/latest`, `/stations/station:usgs:12113000/series?variable=flow`.
- `CASCADE_LIVE_API_BASE=https://cascadia.papsukkal.com npx vitest run src/contracts/live-api.test.ts --testTimeout=30000`
  → **8/8 passed** (53 s). At the default 5 s testTimeout 3 tests time out on remote latency
  (~1.5–3 s/request, /scene/summary iterates 4 bands) — a timeout note, not a contract failure.


## P1 client — live production verification (orchestrator, 2026-08-24)

Deployed as 40b0cb1 (+1f6e4b3 gitleaks allowlist) to cascadia.papsukkal.com (bundle
index-CL8_FG0r.js) and driven in a real browser against the live backend:
- Deep link ?sel=fp:nwps:MVEW1 boots into the MVEW1 panel: observed 10.63 ft NGVD29 /
  6,730 cfs, provisional, OBSERVED + CURRENT (age 28 min, cadence 15 min), category NONE
  with the official-threshold explanation, hydrograph with labeled threshold lines
  (23.5/28/30/32 ft NGVD29) and forecast register boundary.
- Provenance popover from the OBSERVED badge: all fields incl. METHOD none (untransformed),
  replayed freshness, RAW ARTIFACT id.
- Timeline scrub to 2026-08-23 12:12 UTC: AS OF banner + ?as_of= in URL; panel renders
  all-UNKNOWN — correct, production's first ingestion was 2026-08-24 10:24 UTC (honest
  knowledge time at the boundary). Scrub to 11:12 UTC: the observation known then, with
  age computed against the replay clock. Snap-to-now drops banner and URL param.
- Search "skag": grouped results (basin / forecast point / station); Enter flies to the
  basin (band BASIN settled), URL ?sel=basin:skagit; basin panel shows the honest surfaces.
- Credit line reads "CesiumJS (renderer) (c) OpenStreetMap contributors" - ion logo gone.
CI on 40b0cb1: backend, backend-pg, web, e2e-stub green; gitleaks flagged a unit-test
fixture string (false positive) - allowlisted via .gitleaks.toml in 1f6e4b3.


## P2 Event Zero seed-station slice — adversarial verification (2026-08-24)

End-to-end verification of the P2 slice (three builders: USGS OGC December backfill; AFOS
FLW/FLS crest parser + loader; Event Zero client experience). Everything below ran against a
**freshly created** database `cascadia_p2v` on the local `cascadia-pg` container (:5433) —
migrate → seed → both December backfills executed live in this pass (IEM AFOS + USGS OGC,
anonymous: no `CASCADE_USGS_API_KEY` in the environment, polite degrade confirmed). Nothing
was inherited from the builders' own runs.

### Suites and gates (all green)

| Gate | Command | Result |
|---|---|---|
| Offline | `python -m pytest -q` | **99 passed, 8 skipped**, 28.5 s (was 69 pre-P2) |
| pg-marked | `CASCADE_TEST_PG_URL=…5433/postgres python -m pytest -q -m pg` | **8 passed**, 99 deselected, 15.0 s (3 new Event Zero pg tests; each creates+drops its own scratch DB via the real Alembic chain) |
| Types | `npx tsc -p tsconfig.json --noEmit` | clean |
| Lint | `npm run lint` | clean |
| Unit (web) | `npx vitest run` | **120 passed, 8 skipped** (128) |
| E2E | `npm run e2e` (fresh servers, :8000/:4173 verified free first) | **15/15 passed**, 1.9 m — includes the 3 new `event-zero.spec.ts` tests (deep-link entry, zero-look-ahead scrub with superseded marking, NOW exit) |
| Import contracts | `lint-imports` | 3 kept, 0 broken |
| Secrets sweep | grep over all new P2 files | none (only the test literal `"not-a-real-key"`) |

### The December backfills, run for real

```
export CASCADE_DB_URL=postgresql+psycopg://postgres:dev@127.0.0.1:5433/cascadia_p2v
bash scripts/migrate.sh && python -m cascade_worker seed   # 4 sources, 4 products, 6 fps
python scripts/backfill_event_zero_usgs.py                 # live OGC, anonymous
python scripts/backfill_event_zero_fls.py                  # live IEM AFOS
python -m cascade_worker run-once                          # live current data on top
```

- USGS: **34,940 rows written**, `skipped_absent=[]`, `errors=[]`. Partition routing:
  `observation_y2025m12` = 34,930, `observation_y2026m01` = 10 (the 2026-01-01T00:00Z
  boundary rows from the end-INCLUSIVE OGC interval — correctly routed and flagged).
- FLS/FLW: 502 products fetched+archived, 772 LID segments, **123 runs written** (+123
  values), 573 segments skipped across 37 unseeded LIDs (CONW1 et al., re-runnable), 73
  segments honestly stored as nothing (no parseable Forecast crest), 3 refused
  (all-zero H-VTEC crest time). `job_run` rows recorded for both jobs, `ok=true`.
- Idempotency (adversarial re-run, MVEW1 Dec 12): `rows_written: 0, skipped_identical: 194`.
- CRNW1 ESTIMATED qualifiers: 25 rows, quality `["provisional","estimated","backfilled"]`
  at `revision_seq 0` — a fresh run writes the mapped vocabulary directly; the builder's
  two-shape state (verbatim + revision row) was an artifact of their incremental local DB
  and is not reproduced on a clean run.

### GOLDEN 1 — MVEW1 December observed peak (exact)

SQL over `cascadia_p2v` (per-site max in the December window) reproduces EVENT_ZERO §3
for all six seeded sites exactly:

```
12100490 WRAW1 117.07 ft / 12,000 cfs     12149000 CRNW1  60.76 ft / 89,700 cfs
12113000 AUBW1  68.67 ft / 12,100 cfs     12200500 MVEW1  37.73 ft / 133,000 cfs
12119000 RNTW1  18.25 ft / 12,400 cfs     12213100 NKSW1  22.42 ft / 44,300 cfs
```

MVEW1 crest row: `value 37.73, valid_time 2025-12-12T08:15:00Z, quality
["approved","backfilled"], qualifier_raw "Approved", available_at 2026-08-24T13:03:13Z,
revision_seq 0`. Flow peak 133,000 cfs at 08:00Z (plateau 08:00/09:00Z per the builder's
honest note). The series API over the valid-time window returns the same 37.73 @ 08:15Z
with quality flags intact and freshness honestly `stale`.

### GOLDEN 2 — MVEW1 forecast evolution: the byte record, not the draft table

The stored chain (SQL and `GET /forecast-points/MVEW1/runs?start=2025-12-09…end=2025-12-13`,
identical) is **13 runs**:

```
12-09T17:01Z 36.9 | 12-10T01:24Z 41.5 | 12-10T08:54Z 41.5 | 12-10T16:47Z 41.5
12-10T19:01Z 41.5 | 12-10T23:14Z 42.3 | 12-11T02:21Z 42.1 | 12-11T06:47Z 41.3
12-11T10:04Z 39.7 | 12-11T18:17Z 39.1 | 12-12T01:12Z 38.3 | 12-12T08:50Z 38.1
12-12T16:27Z 27.4 (post-crest fall statement)
```

This does NOT equal the 9-row table in the 2026-08-22 draft of EVENT_ZERO §8 — and the
**bytes win**. Verified independently this session against live IEM (listings + product
text, not the builders' fixtures): (1) the Dec 10 KSEW FLSSEW listing contains 08:54Z and
no 09:24Z product; (2) the Dec 11 listing contains 02:21Z and no 01:15Z product (01:15
is the observed-stage citation inside the 02:21Z product); (3) `202512111004` reads
"rise to a crest of 39.7 feet" in the MVEW1 segment — not 39.1; (4) the 16:47Z/19:01Z
(41.5 ft) and 06:47Z (41.3 ft) issuances exist and were omitted. Six of the draft's nine
rows are byte-confirmed (17:01/36.9, 01:24/41.5, 23:14/42.3, 18:17/39.1, 01:12/38.3,
08:50/38.1). One fixture (`202512100854`) was diffed byte-identical against a live IEM
re-fetch. **EVENT_ZERO.md §8 has been corrected in this pass** (dated, cited: the 12-row
byte table; T3 AC "6 runs" → 12 issuances; T8 "six rows" → twelve). The full December
chain is 31 runs; `supersedes_run_id` chains 30/31 (only the first run is unchained).
Crest-time bins come from H-VTEC (12:00Z/18:00Z bins) — bins, not fabricated precise times.

### Look-ahead audit (T = 2025-12-10T12:00Z; TESTING.md §7 spirit)

- Latest run with `issued_at <= T`: run 12, issued 2025-12-10T08:54Z, **crest 41.5 ft** —
  the correct answer at that clock; every 42.x/39.x run has `issued_at > T`. PASS.
- Retrieval-time honesty: **0** of 34,940 December observation rows and **0** of 123 FLS
  runs have `available_at < 2026-08-24`; min available_at 2026-08-24T13:03:03Z (obs),
  13:03:43Z (runs). **0** December rows missing the `backfilled` quality flag. PASS.
- Consequence, verified at the API: any December `as_of` sees UNKNOWN (below).

### as_of interaction (uvicorn on :8001 over cascadia_p2v, live run-once data on top)

| Probe | Result |
|---|---|
| `/system/health` | ok; both providers healthy; all products `current` after run-once (thresholds 24, forecast 222, IV 3,430 rows) |
| series, valid window Dec 12, no `as_of` | 49 points, max **37.73 @ 08:15Z**, quality `["approved","backfilled"]`, provenance freshness honestly `stale` |
| series, same window, `as_of=2026-08-20` | **0 points** — no December leak before the backfill existed |
| series, `as_of=2025-12-12T12:00Z` | **0 points** — the platform did not exist then |
| `/forecast-points/MVEW1/runs`, `as_of=2026-08-20` | **items: 0** — reconstructed runs invisible pre-retrieval |
| state, `as_of` = now−1h (12:06Z) | observed **null**, mode `past` — correct: this scratch DB's first ingestion was 13:05Z; honest knowledge boundary, same shape production showed on 2026-08-24 |
| state, `as_of=2026-08-24T13:06:30Z` (after first ingestion) | observed **10.63 ft valid 12:45Z**, category `none` — replay of current data intact |
| state, no `as_of` | identical live document |

### Verdict and deferrals

The P2 slice holds under adversarial replay: append-only, provenance-complete
(`raw_artifact_id` on every run/observation; one artifact per OGC page and per AFOS
product), knowledge-time honest (available_at = retrieval, never historical), and the
golden crest + evolution reproduce the byte record exactly. Deferred / open:

1. **Neon production run not performed** — no production `DATABASE_URL` was supplied to
   this verifier either. Both scripts are idempotent and take `--db-url`/env; run them
   against Neon to promote (local verification complete).
2. CONW1 and the other §3 sites remain unseeded; 573 FLS segments and the CONW1 IV series
   await seeding + re-run (scripts skip-and-report, zero rework).
3. The FLS `(product, fp, issued_at)` unique key would drop a same-minute FLW+FLS crest
   collision (zero in this corpus for seeded LIDs) — design note if PIL scope widens.
4. No canary for `src:nws-afos` (static archive backfill, not a live cadence) — conscious
   deviation, endorsed.
5. `run-once` wrote 3,430 IV rows (not 3,432): two sensors published 2 fewer points in the
   72 h window at fetch time — live-data variance, not a defect.
6. EVENT_ZERO §5 timeline rows citing the three corrected §8 issuance times (if any beyond
   #47/#63 references) were not audited row-by-row; §5 was out of P2 scope.

---

# P3 — LIVE INTELLIGENCE SURFACES: adversarial verification (2026-08-24, later same day)

Independent, adversarial verification of the P3 slice (`susceptibility`, `forcing`,
`agreement`) against the §5 exit tests of `docs/research/p3-surfaces-design-2026-08-24.md`.
Nothing below is taken from the builders' own test names: every exit test was re-run, and every
claim a surface makes was checked against the data it is actually built from — live, over HTTP,
on real provider payloads fetched during this pass.

Environment: macOS, Python 3.14.6, PostgreSQL 18 + PostGIS 3.6 in the local `cascadia-pg`
container (port 5433). **Two freshly created databases**, both dropped at the end:
`cascadia_p3_verify` (schema/pg-suite/doctrine regression) and `cascadia_p3_live` (live
ingestion). *Deviation, stated:* the live end-to-end ran on a fresh database on the same docker
server rather than in the shared `cascadia` DB, because (a) the shared DB is still at revision
`0001` and would have needed migrating and re-seeding, and (b) a fresh database makes the §8
cost measurement exact — every byte and row in §P3.7 was written by this pass and nothing else.

## P3.0 — Headline: four things the surfaces claimed that their inputs do not support

Two were fixed here; two are reported for the owner because fixing them is a design decision.

| # | What was claimed | What the data actually says | Status |
|---|---|---|---|
| 1 | `nbm.fetch_core_snowlvl` is a working job; the snow-level context driver exists | **It failed on the real cycle and would have failed on every cycle forever.** NBM `core` publishes SNOWLVL *percentile* levels through f048 only; f054–f072 carry the deterministic record alone. The job requested f072, raised, and `run_job` discarded the session — throwing away the f024 and f048 rows that HAD decoded | **FIXED** (§P3.2) |
| 2 | `HazardState.model_probability` = "k of 6 members exceed \<category\>" — "the only genuinely probabilistic number v0 can honestly print" (design §3.5) | **All six NWM members carried ONE distinct crest at all six seed reaches** on the live 12Z cycle. The fraction can only be 0/6 or 6/6: it is a binary indicator over one forecast counted six times, not an empirical frequency over six draws | **DISCLOSED** (§P3.2) |
| 3 | "116 years of record" at the Sauk (12189500) | The gauge has approved daily means in **1911–1912, then nothing until 1928**: **101 years with data inside a 116-calendar-year span**. `end − begin + 1` counted 15 empty years as evidence | **FIXED** (§P3.2) |
| 4 | `agreement = low` at 4 of 5 comparable points | The magnitudes agreed to **0.6 %** (Skagit), **1 %** (Green), **0 %** (White). The level is `low` because of a *timing* term computed as the argmax of two flat recession hydrographs, over **two different time windows** | **REPORTED, not changed** (§P3.6) |

## P3.1 — Gates

| Gate | Before this pass | After the fixes |
|---|---|---|
| `python -m pytest -q` (offline, zero network) | 224 passed, 8 skipped | **227 passed, 8 skipped** (3 regression tests added here) |
| pg-marked suite, **fresh** scratch DB | — | **8 passed, 227 deselected** |
| `ruff check` | All checks passed | **All checks passed** |
| `lint-imports` | 5 kept, 0 broken | **5 kept, 0 broken** |
| `cascade_contracts.export_schema` vs `packages/contracts/schema` | — | **identical** (contracts untouched by this pass) |
| `apps/web`: `typecheck` / `lint` | clean | **clean** |
| `apps/web`: `vitest run` | — | **135 passed, 9 skipped (20 files)** |
| `apps/web`: `contracts:gen` + `contracts:check` | — | **`contracts:check OK`** (generated.ts regenerated byte-identical) |
| `apps/web`: `build` | — | **built in 1.62 s**, 4,503.69 kB js / 36.84 kB css |
| Playwright, fresh servers on :8000 (stub) and :4173 (preview) | — | **15 passed (1.9 m)**, including the three Event Zero replay specs |
| Live-API contract check (`CASCADE_LIVE_API_BASE`) against the real API with real P3 data | — | **8 of 9 passed**; the 9th asks for the Dec-2025 archive window, which the scratch DB does not carry (environment, not a defect) |

Fresh-database schema proof, `cascadia_p3_verify`:

```
bash scripts/migrate.sh
  Running upgrade  -> 0001, Initial schema: models, PostGIS geometry, monthly-partitioned observation.
  Running upgrade 0001 -> 0002, Derived features, basin grid masks, artifact retention class, susceptibility gauge config.
  {"schema": "applied"}
python -m cascade_worker seed
  {"sources": 9, "products": 11, "basins": 6, "stations": 7, "forecast_points": 6, "basin_geometries": 12}
```

`derived_feature` carries `uq_derived_feature_identity (method_id, feature, scope_id, window,
valid_time, issued_at) NULLS NOT DISTINCT`, `ck_derived_feature_confidence`, FKs to
`source_product` and `raw_artifact`, and `ix_derived_feature_scope_time`. `grid_mask` is keyed
`(basin_id, grid_definition_hash)`. All five `forecast_point.reach_id` values and all six
`basin.susceptibility_gauge_id`/`_confidence_ceiling` values seeded exactly as
`seed/p3_surfaces.json` declares (Sauk `station:usgs:12189500` present, station count 7).

## P3.2 — Fixes applied here (all of them)

**1. `packages/providers/nbm/src/cascade_providers_nbm/client.py` — `CORE_HORIZONS_H (24, 48, 72) → (24, 48)`.**
Measured live from the 18Z `core` `.idx` sidecars:

| lead | `.idx` bytes | SNOWLVL records | of which percentile levels |
|---|---|---|---|
| f024 | 16,731 | 16 | **15** |
| f036 | 16,821 | 16 | **15** |
| f042 | 15,964 | 16 | **15** |
| f048 | 15,173 | 16 | **15** |
| f054 | 10,509 | 1 | **0** |
| f060 | 6,412 | 1 | **0** |
| f066 | 6,758 | 1 | **0** |
| f072 | 6,410 | 1 | **0** |

f054 and beyond carry `SNOWLVL:0 m above mean sea level` alone. Design §1.7 assumed three
identical `core` fetches per cycle; that assumption is false. Only the shortest lead is ever
displayed (`forcing._nearest_snow_row` picks it), so no rendered number is lost.

**2. `packages/providers/nbm/src/cascade_providers_nbm/jobs.py` — one empty lead no longer costs the cycle.**
`run_fetch_core_snowlvl` collected the leads with no percentile field and now raises only when
**every** requested lead is empty (a real provider break, still retryable). Before: the first
empty lead raised, `run_job` discarded the session, and the f024/f048 rows already computed were
rolled back. After the fix the same job returned `ok=true, rows_written=36` against the live 12Z
cycle. *Every existing test called this job with `horizons=(24,)`, so the default path — the only
one production uses — had never been exercised.*

**3. `packages/hydrology/src/cascade_hydrology/agreement.py` — the two limitations now travel with the number.**
Design §3.2 says the `no_divergence_floor` flag exists "so the limitation travels with the number
instead of being lost". It was computed onto `AgreementResult.quality` and then dropped at the
contract boundary — no consumer could see it. Added: `QUALITY_DEGENERATE_ENSEMBLE`
(`members_identical_in_window`), a `distinct_member_crests` key on `model_probability`, and
`_caveats()`, which renders both flags into `AgreementState.reason`. No state, level, fraction or
divergence value changed — only what the reader is told.

**4. `packages/hydrology/src/cascade_hydrology/susceptibility.py` — a calendar span is not a length of record.**
`years = end_year − begin_year + 1` became `span_years`, rendered as "spanning N calendar years"
instead of "N years of record". Counted from the archived OGC `daily` CSVs fetched this pass:

| gauge | approved distinct years | first–last | calendar span | empty years inside the span |
|---|---|---|---|---|
| **12189500 (Sauk)** | **101** | 1911–2026 | **116** | **15** (gap 1913–1927) |
| 12149000 | 96 | 1929–2024 | 96 | 0 |
| 12113000 | 91 | 1936–2026 | 91 | 0 |
| 12119000 | 81 | 1945–2025 | 81 | 0 |
| 12213100 | 61 | 1966–2026 | 61 | 0 |
| 12100490 | 18 | 2009–2026 | 18 | 0 |

Only the Skagit's gauge has a gap, and the Skagit is the flagship basin. The honest depth
statement — `n=495 values in the day-of-year window` — was already in the label and is unchanged.

**5. `apps/web/src/event/event-filter.ts` — the frontend twin of read-path defect §3.4(1).**
`runsIssuedAtOrBefore` returned every product from `GET /forecast-points/{lid}/runs`, which is
the forecast-*evolution* read and deliberately serves the NWM ensemble beside the NWRFC run.
Both of its consumers present the result as the official forecast: `Hydrograph` draws it in the
forecast colour, titles every point `· OFFICIAL FORECAST` and hardcodes
`truth="authoritative_model"`; `ForecastEvolution` tables it under "Official forecast crests as
issued". An NWM run issued later than the RFC's would have taken that place. Now filtered on
`provenance.source_kind === 'OFFICIAL_FORECAST'` — the kind the API resolved from the registry,
never a product-id list held in the client. *Not reachable with today's data* (the Dec-2025 event
window predates any NWM run), which is why no test caught it; it is a live trap for the next event
window or any backfill.

Regression tests added: `tests/unit/test_forcing.py` (2), `tests/unit/test_agreement.py` (1),
`tests/unit/test_susceptibility.py` (extended), `apps/web/src/event/event-filter.test.ts` (2).
Two existing exact-dict assertions in `tests/unit/test_agreement.py` were updated for the new
`distinct_member_crests` key.

## P3.3 — §5 exit tests, per surface

Run as named tests **and** re-verified independently over HTTP against the live database. Every
UNKNOWN branch below was reached by advancing the knowledge clock on the real API, not by a mock.

**Forcing** — `tests/unit/test_forcing.py` **33 passed**.

| Exit test | Evidence |
|---|---|
| 1. non-`unknown` at all six basins with a stored cycle; specific reason otherwise | Live `/viz/basins`: six basins `forcing=low`, `value 0 mm`, `confidence=moderate`. `?as_of=2026-08-26T13:00Z` → `unknown`, reason *"No NBM qmd cycle known at this knowledge time."* |
| 2. `qmd.f072` decodes to 161 messages; Skagit p50 golden to 0.01 mm | `test_the_captured_wa_subset_is_the_shape_the_design_measured`, `test_skagit_basin_mean_is_golden_to_a_hundredth_of_a_millimetre` |
| 3. masked area within 3 % of WBD; a changed grid refuses | **Measured on the LIVE grid** (`60cd988c3d52…`, nx×ny 99×142, dx 2539.703 m): skagit 8250.6 km² vs WBD 8275.4 (**−0.30 %**), nooksack 2631.1 vs 2639.2 (−0.31 %), snohomish 4701.1 vs 4714.3 (−0.28 %), cedar 1568.0 vs 1572.3 (−0.27 %), green 1254.5 vs 1257.9 (−0.27 %), puyallup 2527.3 vs 2534.0 (−0.26 %). Worst case **0.31 %**, an order of magnitude inside the 3 % bound |
| 4. QPF `MODELED`, assessment `EXPERIMENTAL` | Live: every `basin_qpf_*` driver → `nbm-forcing-<slug>` → `MODELED`; every `forcing.prov` → `cascade-forcing-<slug>` → `EXPERIMENTAL` |
| 5. replay before ingestion is `unknown` with the no-cycle reason | `?as_of=` 2026-08-24T23:00Z / 20:00Z and 2026-08-20T00:00Z — all six basins `unknown` with the same specific reason, **zero unresolved provenance refs at every knowledge time** |

**Susceptibility** — `tests/unit/test_susceptibility.py` **33 passed**.

| Exit test | Evidence |
|---|---|
| 1. non-`unknown` with a score when a daily mean ≤ 48 h old exists; `unknown` with the 48-hour reason when not | Live: cedar 20.8 / green 60.5 / nooksack 27.1 / puyallup 7.1 / skagit 5.0 / snohomish 10.2 pct, all with `score`. Advance to `?as_of=2026-08-26T11:00Z` (daily mean 52 h old) → all six `unknown` |
| 2. golden climatology; within 10 % of `nwis/stat` p50 on ≥ 350/366 days | `test_golden_climatology_reproduces_exactly`, `test_cascade_and_published_p50_agree_on_at_least_350_of_366_days`. **Live cross-check at the Sauk today: cascade p50 2010.0 vs published p50 2010.0, `disagreement_fraction: 0.0`** — stored separately, never fused |
| 3. `soil_saturation_percentile` present with `value: null` and an unavailability provenance | Live, **all six basins**: driver present, `value: null`, `direction: unavailable`, `prov: cascade-soil-unavailable` → `source_kind: UNKNOWN`, label naming the SNOTEL SMS rejection. Present on every UNKNOWN branch too |
| 4. regulated basins never above `low`; skagit reads 12189500 and says so | Live: green-duwamish `low`, puyallup-white `low`; skagit label *"…flow percentile at 12189500 … The upper Skagit is regulated (Ross, Baker), so basin wetness is read from the unregulated Sauk"* |
| 5. no scored SWE driver | Live: every `basin_swe_percent_of_median` and `snotel_precip_14d_percent_of_median` carries `context_not_scored`. The **only** scored direction anywhere in the six documents is `increases_susceptibility` on `streamflow_doy_percentile`. Full direction vocabulary observed: `context_not_scored`, `decreases_forcing`, `increases_forcing`, `increases_susceptibility`, `model_below_official`, `model_earlier`, `model_exceeds_official`, `model_later`, `reference`, `unavailable` |

**Agreement** — `tests/unit/test_agreement.py` **28 passed**.

| Exit test | Evidence |
|---|---|
| 1. non-`unknown` at MVEW1/NKSW1/RNTW1/AUBW1/WRAW1; `unknown` at CRNW1 with the flow-column reason | Live: nooksack `high`, cedar/green/puyallup/skagit `low`, snohomish-snoqualmie **`unknown`** — *"The NWRFC forecast for CRNW1 carries no flow column (every secondary value is the −9999 sentinel); NWM produces flow only, so the two cannot be compared without a rating conversion (not in v0)."* No number is invented there: `drivers == ()`, `magnitude_divergence is None` |
| 2. `model_probability` non-null **only** at AUBW1/WRAW1, denominator 6 | Live: exactly two basins carry it — green-duwamish and puyallup-white — `{"exceeds": "action", "fraction": 0.0, "members": 6.0, "exceeding": 0.0, "distinct_member_crests": 1.0}`. The other four are `null` with `hazard.reason` beginning *"No model exceedance fraction is shown: …"*. `cascade_index` is `null` everywhere |
| 3. a later-issued NWM run never becomes the official forecast | **Verified by storing both runs and reading the API** — see §P3.4 |
| 4. nothing averages an official with a model value | Grep-level check — see §P3.5 |

## P3.4 — Doctrine regression, proved through the API rather than a unit test

Scratch DB `cascadia_p3_verify`, MVEW1, both runs stored as rows:

```
 id |       product_id        |      issued_at      | primary_variable | unit
----+-------------------------+---------------------+------------------+------
  1 | product:nwps-forecast   | 2026-08-24 15:00:00 | stage            | ft
  2 | product:nwm-mr-via-nwps | 2026-08-24 20:00:00 | flow             | cfs     <- FIVE HOURS LATER
```

API on `127.0.0.1:8012`, `as_of=2026-08-24T21:00:00+00:00`:

| Endpoint | Result |
|---|---|
| `/viz/rivers?basin=basin:skagit` | `official_forecast.issued_at = 2026-08-24T15:00:00Z`, issuer `NWRFC`, ref `product:nwps-forecast` / `src:nwps-v1` / **`OFFICIAL_FORECAST`**, truth `authoritative_model` — the 20:00Z model run did **not** displace it |
| `/forecast-points/MVEW1/runs/latest` | `issued_at 15:00:00Z`, `primary stage ft`, provenance `product:nwps-forecast` / `OFFICIAL_FORECAST` |
| `/viz/basins` agreement refs | `nwps-forecast-mvew1` → `src:nwps-v1` / `OFFICIAL_FORECAST`; `nwm-mr-mvew1` → `src:nwm-v3.1` / **`MODELED`** — two kinds, two refs, one comparison |
| `/forecast-points/MVEW1/runs` (evolution) | Returns **both**, each self-badged: `product:nwps-forecast` 15:00Z `OFFICIAL_FORECAST` (issuer NWRFC) and `product:nwm-mr-via-nwps` 20:00Z `MODELED` (issuer NOAA OWP) |

Property test, executed as a document scan rather than a code inspection: **36 ProvenanceRefs
were walked across 7 endpoints** (`/viz/basins`, `/viz/rivers`, `/forecast-points/MVEW1/runs`,
`/runs/latest`, `/basins/basin:skagit/state`, `/forecast-points/MVEW1/state`, `/scene/summary`).
**4 carry `source_id = src:nwm-v3.1`; all 4 are `MODELED`. Violations: none.** The same scan over
the live `cascadia_p3_live` documents found 54 refs, all resolving, none violating.

## P3.5 — Grep-level check: nothing averages official and model values

Files scanned: `agreement.py`, `surfaces.py`, `assemble.py`, `category.py`,
`reaches_normalize.py`, `reaches_parser.py`, `reaches_jobs.py`, `knowledge.py`. Pattern set:
`mean|average|avg|blend|consensus|fuse|statistics\.|fmean|sum\(|/ 2|\* 0\.5` plus the midpoint
regex `\(\s*\w+\s*\+\s*\w+\s*\)\s*/\s*2`.

Every arithmetic hit, classified:

| Site | Operation | Verdict |
|---|---|---|
| `agreement.compare` | `delta = (model.value − official.value) / denominator` | a signed **difference** over a denominator that is one side or a threshold; never a midpoint |
| `agreement.compare` | `delta_t = \|t_model − t_official\|` | a **difference** in hours |
| `agreement.member_exceedance` | `exceeding = sum(1 for m in members if m.value >= level)` | a **count over model members only**; the official value is not in the expression |
| `agreement.ensemble_from_feature` / `reaches_normalize.crest_summary` | `ordered[(len(ordered) − 1) // 2]` | **index selection** of a real member — the lower median. No arithmetic mean, so no value is invented that no member forecast |
| `reaches_normalize` / `reaches_jobs` | `provider_mean_crest` | the **provider's own** mean, stored and labelled as NWPS's read-time average. Confirmed never read back: `ensemble_from_feature` consumes only `members`, `median_member`, `median_rule`, `window_h`, `unit`. It appears in no driver, no surface and no comparison |

Everything else matching the pattern is prose in a docstring. **No official value is combined
with a model value anywhere in the agreement path.** `tests/unit/test_agreement.py::test_nothing_in_the_agreement_path_averages_an_official_with_a_model_value` encodes the same check and passes.

## P3.6 — Live end-to-end, `cascadia_p3_live`

`python -m cascade_worker run-once` at 23:38:29Z, real network, all ten jobs:

| job | ok | rows | note |
|---|---|---|---|
| `nwps.fetch_thresholds` | ✔ | 24 | |
| `nwps.fetch_forecast` | ✔ | 213 | |
| `usgs.fetch_iv` | ✔ | 3,996 | |
| `nbm.build_grid_masks` | ✔ | 6 | one mask per basin on grid `60cd988c…` |
| `nbm.fetch_qmd` | ✔ | 108 | |
| `nbm.fetch_core_snowlvl` | **✘ → ✔** | 0 → **36** | `NbmParseError: field_missing: core f072 carries no SNOWLVL percentile field`; green after fix 1+2 |
| `nwm.fetch_reach_medium_range` | ✔ | 480 | 6 runs × (1 + 72 values) + 42 derived |
| `usgs.build_climatology` | ✔ | 12 | 6 Cascade ladders + 6 published ladders, stored separately |
| `usgs.fetch_daily_percentile` | ✔ | 6 | |
| `awdb.fetch_snotel_context` | ✔ | 12 | |

API on `127.0.0.1:8011`, `GET /viz/basins` — six items, 54 provenance refs, **every value resolves
to a ProvenanceRef (0 unresolved)**:

| basin | susceptibility | forcing | agreement | hazard |
|---|---|---|---|---|
| `basin:cedar` | `low` 20.8 pct, conf `moderate`, EXPERIMENTAL | `low` 0 mm, conf `moderate` | `low` (RNTW1) | `none` |
| `basin:green-duwamish` | `moderate` 60.5 pct, conf **`low`** | `low` 0 mm, conf `moderate` | `low` (AUBW1) | `none` |
| `basin:nooksack` | `moderate` 27.1 pct, conf `moderate` | `low` 0 mm, conf `moderate` | **`high`** (NKSW1) | `none` |
| `basin:puyallup-white` | `low` 7.1 pct, conf **`low`** | `low` 0 mm, conf `moderate` | `low` (WRAW1) | `none` |
| `basin:skagit` | `low` 5.0 pct, conf `moderate` (Sauk) | `low` 0 mm, conf `moderate` | `low` (MVEW1) | `none` |
| `basin:snohomish-snoqualmie` | `low` 10.2 pct, conf **`high`** | `low` 0 mm, conf `moderate` | **`unknown`** (CRNW1, flow-column reason) | `none` |

Every surface `truth = cascade_derived`, `experimental = true`. Provenance kinds resolved from
the registry throughout: `OBSERVED` (USGS daily, AWDB), `MODELED` (NBM, NWM), `OFFICIAL_FORECAST`
(NWPS forecast/thresholds), `EXPERIMENTAL` (the two Cascade assessments), `UNKNOWN` (soil).

### Open finding A — `agreement = low` is being produced by a timing term with nothing to measure

Not fixed: the bands and the timing term are the design's stated (uncalibrated) assumption and
changing them is an owner decision. But the live numbers show the level is not carrying the
meaning a reader will take from it.

| basin (point) | official crest | NWM median-member crest | \|Δ\| | Δt | level |
|---|---|---|---|---|---|
| skagit (MVEW1) | 6,780.0 cfs | 6,740.2 cfs | **0.6 %** | **75 h** | `low` |
| puyallup-white (WRAW1) | 632.2 | 623.0 | **1.5 %** | **76 h** | `low` |
| green-duwamish (AUBW1) | 294.2 | 379.3 | 29 % | **52 h** | `low` |
| cedar (RNTW1) | 120.0 | 196.0 | 63 % | 20 h | `low` |
| nooksack (NKSW1) | 1,290.0 | 1,290.0 | ~0 % | 3 h | `high` |

At MVEW1 the two forecasts agree on magnitude to 0.6 % and the surface reports **low agreement**,
because both hydrographs are recessions with no crest in them: the official series falls then
rises at the far edge of the window (max 6,780 at 2026-08-27T18:00Z) while the NWM series falls
monotonically from its first hour (max 6,740.16 at 2026-08-24T15:00Z). `Δt` is measuring which end
of a flat line is a hair higher. The builders' own test docstring already records the same
behaviour on the fixture ("63 h apart on the crest timing"). In a dry Cascade summer this will be
the normal reading, which makes `low` uninformative exactly when it is most often shown.

### Open finding B — the two crests are maxima over DIFFERENT windows

Design §3.2 requires both crests to be taken over "the same window `(as_of − 6 h, as_of + 72 h]`
… so hazard and agreement are talking about the same event". They are not, and cannot be as
built: the official crest is computed at **read** time over an `as_of`-anchored window, while the
member crests are computed at **ingest** time over a **cycle**-anchored window `(referenceTime,
referenceTime + 72 h]` and frozen into `derived_feature`. Measured at `as_of = 2026-08-24T23:43:34Z`:

```
official window : (2026-08-24T17:43:34Z, 2026-08-27T23:43:34Z]
model window    : (2026-08-24T12:00:00Z, 2026-08-27T12:00:00Z]
model crest time:  2026-08-24T15:00:00Z   <-- 2 h 43 m BEFORE the official window opens
```

The model's selected crest sits at an instant from which the official crest could not have been
selected, and the official window's last 11.7 hours are invisible to the model side. The offset
equals the cycle age (5–14 h in practice) and is disclosed nowhere. On a rising hydrograph it
biases Δ negative systematically. The design is internally inconsistent here — it asks for an
`as_of`-anchored window *and* a precomputed per-cycle crest summary — so this needs an owner
decision, not a patch: either re-derive member crests at read time from the archived JSON, or
carry the offset out with the number.

### Open finding C — `/system/health` reported `status: ok` while a job was failing on every cycle

`JOB_TO_PROVIDER` in `apps/api/src/cascade_api/routes.py` maps **3 of the 10 registered jobs**
(`usgs.fetch_iv`, `nwps.fetch_thresholds`, `nwps.fetch_forecast`) and `HEALTH_PRODUCTS` covers
the same three products. During the run in which `nbm.fetch_core_snowlvl` failed, `/system/health`
answered:

```json
{"status": "ok", "providers": {"usgs": {...healthy}, "nwps": {...healthy}},
 "freshness": {"product:usgs-iv": "current", "product:nwps-forecast": "current",
               "product:nwps-thresholds": "current"}}
```

**This is the mechanism by which finding 1 would have stayed invisible in production forever.**
Deliberately not fixed here: adding the seven P3 jobs to `JOB_TO_PROVIDER` is one line, but it
makes `status` `degraded` on every fresh deploy until each job has run — and `usgs.build_climatology`
fires on **1 January only**, so a fresh deployment would read `degraded` for up to a year. The
right fix is a per-job "expected first run" notion, or an explicit bootstrap step in the deploy
runbook, and that is an operational decision for the owner. This should be the highest-priority
P3 carried-forward item, above the four already recorded in `NEXT_STEPS.md`.

### Smaller observations, none fixed

1. **`horizon_h` is measured from the cycle, not from `as_of`.** At `?as_of=2026-08-26T11:00Z` the
   Skagit reads `forcing=low, horizon_h=72` from a cycle issued 47 h earlier whose `valid_time` is
   only 25 h in the future — i.e. two thirds of the "next 72 hours" has already happened. Freshness
   correctly reads `degraded` (169,200 s) and confidence drops to `low`, so the staleness is badged;
   but nothing says the window has largely elapsed. `MAX_CYCLE_AGE = 2 days` is the builder's
   addition; the design set no bound.
2. **Unrounded floats in the API payload.** `basin_snow_level_pointwise_p50 = 3186.777804321641 m`
   and `basin_qpf_72h_pointwise_p90 = 0.021569362835888197 mm`, while agreement and susceptibility
   drivers are rounded to 1 dp. The web renders 1 dp (`format.ts::formatNumber`), so no user sees
   it — but the Pages gateway and any future consumer do. Significant digits are a claim.
3. **`direction: model_exceeds_official` on two displayed-equal values.** At NKSW1 both crest
   drivers print `1290.0 cfs` while the direction asserts the model is higher; the difference is
   below the 1-dp rounding applied to the driver values.
4. **Seed-note conflict at the Sauk.** The provenance label now reads "…at 12189500 (1911–2026,
   spanning 116 calendar years, n=495…)" while the seed note inside the same sentence says
   "(12189500, 1929-2026)". Both are true of different sources (Cascade's OGC-built ladder vs the
   USGS published table) but they read as a contradiction. A seed-text edit, deliberately left to
   the owner of `seed/p3_surfaces.json`.
5. **New provider fact worth recording against design §2.1's OPEN QUESTION.** The
   `api.waterdata.usgs.gov/statistics/v0` BETA now returns **366 percentile days for
   `USGS-12189500`** while still returning **0 features for `USGS-12200500`** (susceptibility
   canary, live). Discharge normals are appearing, unevenly, per site.
6. **`nbm_canary.py` line 117** estimates daily bytes as `4 × (qmd + core_f024 × len(CORE_HORIZONS_H))`.
   With the horizon fix that is now `× 2` rather than `× 3` — closer, but still assumes f048 is the
   same size as f024 (it is 206,867 B vs 171,727 B). The canary's `bytes_per_day` reported
   8,639,976 against a measured 8,780,536 for the same two jobs (§P3.7 forcing, excluding the
   once-daily mask build the canary does not count).

Canaries, run live and non-blocking (they define no `test_*` functions, so `pytest` collects
nothing from `tests/canaries/`): `nbm_canary.py` → `"ok": true`, grid consistent,
`bytes_per_cycle_qmd 1,816,540` = the design figure exactly, SNOWLVL selected by
`discipline=0, category=19, number=236 (never shortName)` with 15 percentile levels;
`susceptibility_canaries.py` → USGS `nwis/stat` 366 rows and `p50_disagreement_today 0.0`, AWDB
reachable with 78 WA SNTL stations / 29 Puget / WTEQ 28 / PREC 26, and **soil still refused**
(`soil_median_present: false`, 90 `no profile` flags, 6 distinct depth sets).

## P3.7 — Measured ingest cost vs design §8

Every byte below is `raw_artifact.bytes` written by this pass into an empty database, cross-checked
against the object store on disk (40 objects, 11,552,699 B; the 159 KB difference from the row sum
is one content-addressed duplicate plus one orphaned object from the rolled-back failed job —
exactly the bounded behaviour `reaches_jobs.py` documents).

**Per cycle, measured:**

| Job | requests | bytes | design estimate |
|---|---|---|---|
| `nbm.fetch_qmd` (f024/f048/f072 APCP) | 3 | 214,318 + 556,896 + 1,045,326 = **1,816,540** | 1,816,540 — **exact** |
| `nbm.fetch_core_snowlvl` (f024/f048 SNOWLVL) | 2 | 171,727 + 206,867 = **378,594** | 515,181 (3 × f024) — **−26 %** |
| `nwm.fetch_reach_medium_range` (6 reaches) | 6 | **957,987** (157,346–161,060 each) | 944,076 — **+1.5 %** |

**Per day (4 cycles), measured:**

| Surface | measured | design §8 | delta |
|---|---|---|---|
| Forcing — qmd 4 × 1,816,540 = 7,266,160 B; core 4 × 378,594 = 1,514,376 B; one daily mask build 171,727 B | **8.95 MB** (8,952,263 B) | 9.4 MB | −4.8 % |
| Agreement — 4 × 957,987 B | **3.83 MB** (3,831,948 B) | 3.8 MB | +0.8 % |
| Susceptibility — `latest-daily` 5,844 B + AWDB data 96,921 B + AWDB stations 34,719 B | **0.137 MB** (137,484 B) | ~0.025 MB | **+450 %** |
| **P3 total** | **12.92 MB/day** (12,921,695 B) | 13.2 MB/day | **−2.1 %** |

The susceptibility overshoot is real but immaterial in absolute terms: the AWDB job fetches a
**30-day** window for ~30 sites plus the station list every day, not "the latest day" as §2.5
assumed. 131.6 KB/day against a 13 MB/day total.

**One-time:** climatology backfill 6 × OGC `daily` CSV = 4,509,545 B (171,216 – 1,018,310 B per
site) + 6 × `nwis/stat` = 260,806 B = **4.77 MB** against the design's 5.7 MB.

**R2 growth:** 12.92 MB/day × 30 = **~388 MB/month** against the design's ~400 MB — the design's
90-day lifecycle rule on the `nbm/` prefix still caps the steady state at ~1.2 GB (12 % of the
10 GB free tier). `retention_class = "gridded-90d"` is correctly stamped on every NBM artifact and
`NULL` on everything else.

**Neon:** measured heap only (`pg_column_size`), because a 216-row table's index pages are
minimum-sized and not projectable.

| method | rows measured | avg heap bytes/row | rows/month | heap/month |
|---|---|---|---|---|
| `method:basin-qpf@1.0.0` | 108 | 849 | 12,960 | **11.0 MB** |
| `method:basin-snow-level@1.0.0` | 36 | 896 | 4,320 | 3.9 MB |
| `method:nwm-member-crest@1.0.0` | 42 | 478 | 5,040 | 2.4 MB |
| `forecast_value` (NWM mean series) | 639 | 50 | 51,840 | 2.6 MB |
| susceptibility daily (percentile + SWE + precip) | 18 | ~1,226 | 540 | 0.7 MB |
| climatology ladders (annual) | 12 | 13,922 / 9,544 | 12/yr | 141 kB/yr |
| **P3 total** | | | **~74,700/month** | **~20.6 MB/month heap** |

Row **count** matches the design (~73 k/month). Row **bytes** do not: the design projected
~14 MB/month; measured heap is **~20.6 MB/month (+47 %)**, because `derived_feature` rows are
~850 B wide (JSONB `quality`/`inputs`/`values_json` plus six string columns), not the ~270 B the
design's 15 k rows ↔ 4 MB implied. Indexes are on top. Against Neon's 0.5 GB free tier, and with
the pre-existing USGS IV write of ~30 MB/month, the combined figure is ~50 MB/month — the free
tier is consumed in roughly **10 months**, not two years. Worth the owner's attention before the
lifecycle question becomes urgent.

**Request budgets:** NOMADS 21/day (3 qmd + 2 core per cycle × 4, plus 1 mask build) against
120/min per IP; NWPS `/reaches` 24/day; USGS 1/day steady (6 + 6 annually); AWDB 2/day. All far
inside every published limit.

## P3.8 — Cleanup

`cascadia_p3_verify` and `cascadia_p3_live` dropped; both uvicorn processes (:8011, :8012)
stopped; the shared `cascadia` database was **not touched** and remains at revision `0001`.
Raw artifacts and scratch scripts stayed in the session scratchpad, outside the repository.

### Verdict

The P3 slice does what the design says, with the four exceptions in §P3.0. Three of those are
now either fixed or disclosed in the contract; the fourth — `agreement = low` from a timing term
with no crest to time, over two mismatched windows — is the one place where a surface still says
more than its inputs support, and it needs an owner decision rather than a patch. The
`/system/health` blind spot (finding C) is what let the only hard production failure hide, and
should be closed before the next deploy.

---

## P3.9 — Re-verification of the findings A/B/C fixes, adversarial, live (2026-08-25)

Independent re-verification of the two fix passes (agreement findings A + B; `/system/health`
finding C) against live NWPS / NWM / NBM / USGS / AWDB data. Nothing below is taken from the
fixers' own test names. Environment: macOS, Python 3.14.6, PostgreSQL 18 + PostGIS 3.6 in the
local `cascadia-pg` container (port 5433). **Two freshly created databases, both dropped at the
end**: `cascadia_p3_adv` (migrate → seed → live ingest → API on :8012) and `cascadia_p3_adv_pg`
(the pg-marked suite). The shared `cascadia` database was never connected to and remains at
revision `0001`.

### P3.9.0 — Headline

**A and B are closed; C is closed as designed but was, on live data, immediately re-opened in the
mirror direction by a registry value.** Three further defects were found and fixed here. All are
of the same family as the originals: the arithmetic was right and the sentence was not.

| # | What a surface claimed | What the data says | Status |
|---|---|---|---|
| A | `agreement = low` from a timing term with nothing to time | No live point reads `low` for an agreeing pair any more; `Δt` is `null` at all five comparable points with `direction: neither_forecast_crests_in_window` / `only_one_forecast_crests_in_window` | **CLOSED, verified live** |
| B | official and model crests taken over different windows | One `ComparisonWindow` object, bounds **identical** for both sides at all six points, `lost_tail 0.00 h` | **CLOSED, verified by measurement** |
| C | `/system/health: ok` while a job failed every cycle | 11/11 registered jobs and 10/10 expected products reported; a deliberately failing job forces `degraded`; a never-run database reads `unknown` | **CLOSED, verified over HTTP** |
| D | `"peaks 1% above the NWRFC forecast"` at AUBW1 while the two crests were **28.7 %** apart | The 1 % was a fraction of the 6,000 cfs *action flow*, not of the forecast — wrong by a factor of 20, and the clause that would have explained it fired only when the floor was absent (i.e. only when the sentence was already true) | **FIXED here** |
| E | `/system/health: degraded` on a fresh database with **all ten jobs green** | `product:nbm-v5-core` was registered PT1H·PT1H because NOAA publishes `core` hourly, while the job that writes it runs 6-hourly on a 7.5 h-lagged cycle — so it was stale on every cycle, forever | **FIXED here** |
| F | `product:nbm-v5-core: {"state": "current", "anchor": "raw_artifact", "reason": null}` on a database where its job had **never once succeeded** | `nbm.build_grid_masks` fetches a `core` file of its own, so bytes exist for a product of which not one value was ever produced. `state: current` is a claim about data | **FIXED here** |
| G | Both crests presented as one like-for-like magnitude comparison | Official 6-hourly / 13 points vs model hourly / 78 points over the same window, at **all five** comparable points, and the `official_series_coarser_than_model` flag was recorded at **none** of them (it fired only on the timing axis) | **FIXED here** (recorded; see §P3.9.7 for what still does not reach a reader) |

### P3.9.1 — Gates (exact tails)

| Gate | Result |
|---|---|
| `python -m pytest -q` (offline, zero network) | **277 passed, 8 skipped in 132.77s** (was 227/8 at §P3.1; +42 from the two fix passes, +8 added here) |
| `ruff check` | `All checks passed!` |
| `lint-imports` | `Contracts: 5 kept, 0 broken.` (112 files, 505 dependencies) |
| contracts drift (`export_schema` vs `packages/contracts/schema`) | **identical**, both before and after this pass; `packages/contracts` untouched |
| pg-marked suite, fresh `cascadia_p3_adv_pg` | **8 passed, 276 deselected in 13.49s** |
| `apps/web`: `tsc -p tsconfig.json --noEmit` | exit 0, no output |
| `apps/web`: `npm run lint` (eslint src) | clean |
| `apps/web`: `npx vitest run` | **19 passed \| 1 skipped (20 files); 135 passed \| 9 skipped (144 tests)** |
| `apps/web`: `npm run contracts:check` | `contracts:check OK` |
| `apps/web`: `npm run build` | `✓ built in 1.78s`; `index-CLy0zdAO.css 36.84 kB`, `index-CBkJTMQA.js 4,503.63 kB` (gzip 1,221.41 kB) |
| `apps/web`: `npm run e2e` (Playwright, stale :4173/:8000 killed first) | **15 passed (1.8m)**, all specs including the three Event Zero replays and the basin-scene screenshot |

Fresh-database provenance, `cascadia_p3_adv`:

```
docker exec cascadia-pg psql -U postgres -c "CREATE DATABASE cascadia_p3_adv;"
bash scripts/migrate.sh          -> upgrade 0001, 0002; {"schema": "applied"}
python -m cascade_worker seed    -> {"sources": 9, "products": 11, "basins": 6, "stations": 7,
                                     "forecast_points": 6, "basin_geometries": 12}
python -m cascade_worker run-once  (live network, 2026-08-25T01:13:23Z -> 01:15:48Z)
```

All ten scheduler jobs `ok=true` on the first attempt: thresholds 24, forecast 216, usgs.fetch_iv
3 992, grid masks 6, qmd 108, **core_snowlvl 36** (the §P3.2 horizon fix holds on a new cycle),
`nwm.fetch_reach_medium_range` **444**, climatology 12, daily percentile 6, AWDB 12. The
eleventh, queue-only `maintenance.ensure_observation_partitions`, was run once through `run_job`
(`ok=True, rows=8`) to reach the `ok` baseline — see §P3.9.4.

### P3.9.2 — Finding B closed by measurement, not by intent

`comparison_window(as_of, issued_at, coverage_h)` builds one `ComparisonWindow`, and `clip()` and
`ensemble_from_feature()` are both handed **that object**. Measured at
`as_of = 2026-08-25T01:30:00Z`, printing both sides' bounds and every point's timestamp:

```
hazard window     : (2026-08-24T19:30:00Z, 2026-08-28T01:30:00Z]   78.00 h
COMPARISON window : (2026-08-24T19:30:00Z, 2026-08-28T01:30:00Z]   78.00 h     <- both sides
model cycle       :  2026-08-24T18:00:00Z   age 7.50 h   coverage 96 h   lost_tail 0.00 h
```

| LID | official points (n, first, last) | model members (n, first, last) | every point of BOTH sides inside the one window |
|---|---|---|---|
| RNTW1 | 13, 2026-08-25T00:00Z, 2026-08-28T00:00Z | 6 × 78, 2026-08-24T20:00Z, 2026-08-28T01:00Z | **True** |
| MVEW1 | 13, same | 6 × 78, same | **True** |
| NKSW1 | 13, same | 6 × 78, same | **True** |
| AUBW1 | 13, same | 6 × 78, same | **True** |
| WRAW1 | 13, same | 6 × 78, same | **True** |
| CRNW1 | — (no flow column) | 6 × 78, same | window built, comparison correctly refused |

Compare §P3.6's before-state, where the model's crest sat **2 h 43 m before the official window
opened**. The `COVERAGE_HORIZON_H = 96 h` choice is doing exactly the work it was sized for:
AUBW1's stored cycle was `12:00Z` (13.5 h old at this `as_of`) and `12:00Z + 96 h` still clears
`hazard_end`, so `lost_tail = 0.00 h` even on the oldest cycle in the sample.

The as_of sweep proves the degradation is honest rather than silent:

| `as_of` | behaviour |
|---|---|
| +11 h (`2026-08-26T12:00Z`) | still compared; reason gains *"the NWM cycle covers only the first 60 h of that window"* |
| +41 h (`2026-08-27T18:00Z`) | still compared; *"…only the first 30 h…"* |
| +53 h (`2026-08-28T06:00Z`) | **all five UNKNOWN**: *"The newest NWM cycle for MVEW1 is 84 h old, so it and the official forecast share only 18 h of the 72-hour hazard window — too little for either maximum to be the crest of the same event."* |

### P3.9.3 — Finding A closed: the live agreement table over HTTP

`GET /viz/basins` on `127.0.0.1:8012`, `as_of = 2026-08-25T01:44:30Z`, after the §P3.9.5 fix:

| basin (point) | official crest | NWM median-member crest | \|Δ\| cfs | \|Δ\| % of official crest | Δt | level | reason chars |
|---|---|---|---|---|---|---|---|
| cedar (RNTW1) | 120.0 | 195.6 | 75.6 | 63.00 % | **none** | `low` | 248 |
| green-duwamish (AUBW1) | 294.7 | 379.3 | 84.6 | 28.71 % | **none** | `high` | 209 |
| nooksack (NKSW1) | 1,250.0 | 1,269.9 | 19.9 | 1.59 % | **none** | `high` | 226 |
| puyallup-white (WRAW1) | 637.1 | 589.0 | 48.1 | 7.55 % | **none** | `moderate` | 219 |
| skagit (MVEW1) | 8,000.0 | 6,780.1 | 1,219.9 | 15.25 % | **none** | `moderate` | 243 |
| snohomish-snoqualmie (CRNW1) | — | — | — | — | none | `unknown` | 193 |

**No basin reports a disagreement it does not have.** The §P3.6 pathology — MVEW1 agreeing to
0.6 % and reading `low` because `Δt = 75 h` — cannot recur: `Δt` is `null` at every point in this
sample, carried out as `direction: neither_forecast_crests_in_window` (four points) and
`only_one_forecast_crests_in_window` (RNTW1) rather than as a number. The single `low` is RNTW1,
where the two crests really are 63 % apart on a 120 cfs summer flow, and the reason says so.
**CRNW1 is still `unknown` with the flow-column reason, verbatim as §3.6 of the design requires.**

Provenance, 48 refs on the envelope, **0 unresolved**: `nwm-mr-*` resolve `MODELED` /
`src:nwm-v3.1` / `product:nwm-mr-via-nwps`, `nwps-forecast-*` resolve `OFFICIAL_FORECAST` /
`src:nwps-v1`. No model run is badged official; CRNW1 cites no NWM run at all, because it used
none.

Reason strings, verbatim, 193–248 characters — one sentence with at most two clauses:

```
cedar (RNTW1) low, 248: "The NWM median member peaks 63% above the NWRFC forecast, and only NWM
  crests inside this window; official flood categories here are stage-only so none could be
  compared and the percentage is scaled by the official crest rather than an action flow."
green-duwamish (AUBW1) high, 209: "The NWM median member peaks 85 cfs above the NWRFC forecast
  (1% of this point's 6,000 cfs action flow), and neither crests inside this window (official
  flat, NWM rising); all 6 NWM members reach the same peak."
nooksack (NKSW1) high, 226: "The NWM median member peaks 2% above the NWRFC forecast, and neither
  crests inside this window (both receding); official flood categories here are stage-only so
  none could be compared and all 6 NWM members reach the same peak."
puyallup-white (WRAW1) moderate, 219: "The NWM median member peaks 48 cfs below the NWRFC
  forecast (under 1% of this point's 5,500 cfs action flow), and neither crests inside this
  window (official rising, NWM receding); all 6 NWM members reach the same peak."
skagit (MVEW1) moderate, 243: "The NWM median member peaks 15% below the NWRFC forecast, and
  neither crests inside this window (official rising, NWM receding); official flood categories
  here are stage-only so none could be compared and all 6 NWM members reach the same peak."
snohomish-snoqualmie (CRNW1) unknown, 193: "The NWRFC forecast for CRNW1 carries no flow column
  (every secondary value is the −9999 sentinel); NWM produces flow only, so the two cannot be
  compared without a rating conversion (not in v0)."
```

### P3.9.4 — Finding C closed, tested in both directions over HTTP

| Scenario, on `cascadia_p3_adv` | `/system/health` answered |
|---|---|
| **Fresh, migrated, seeded, never run** | `status: unknown`; 11 jobs all `pending`, 10 products all `missing`, **21 reasons**, every provider `unknown`. **NOT `degraded`** ✔ |
| All 10 scheduler jobs green + the queue-only maintenance job run once | `status: ok`, `reasons: []`, 11/11 jobs `ok`, 10/10 products `current`, 8/8 providers `healthy` ✔ |
| **One deliberately failing `job_run` row injected** (`nbm.fetch_core_snowlvl`, error text carrying "DELIBERATE FAILURE") | `status: degraded`; that job `state: failing`, `age_seconds: 613`, `last_success_at` retained, the error quoted in `reasons`; `providers.nbm: degraded`. **NOT `ok`** ✔ |
| **The §P3.6 scenario exactly**: eight consecutive failures, no success ever | `status: degraded`; job `state: down`, `last_success_at: null`, `providers.nbm: down` ✔ |

The endpoint sees **11** jobs (including the queue-only `maintenance.ensure_observation_partitions`
that `scheduler.JOBS` does not carry) and **10** products, against 3 and 3 before.

**Operational note, confirmed rather than theoretical.** A fresh deployment reads `unknown` until
`maintenance.ensure_observation_partitions` has run once; `python -m cascade_worker run-once`
covers the other ten. Reaching the `ok` above needed one explicit deferral of that task. That
belongs in RUNBOOK-deploy §7 (not edited here).

### P3.9.5 — Fixes applied in this pass

Five changes, listed in full.

**1. `packages/hydrology/src/cascade_hydrology/agreement.py` — the percentage named the wrong
denominator (finding D).** `Δ = (C_nwm − C_off) / max(C_off, floor)`, and at the two points with
an official action FLOW the floor wins that max by 20×. Live at AUBW1: crests 294.7 and 379.3 cfs,
**28.7 % of the official crest apart**, and the sentence read *"The NWM median member peaks 1%
above the NWRFC forecast"*, level `high`. The floor is the right denominator for the **band** (85
cfs on a river that acts at 6,000 cfs is hydrologically nothing) and the wrong thing to attribute
to the forecast. `_magnitude_phrase` now states the difference in cfs when the floor is the
denominator, a new `_basis_phrase` names the action flow the percentage is a fraction of, and
`method_record["magnitude"]` carries `difference_cfs`, `denominator_cfs` and `denominator_basis`.
Unchanged where the official crest *is* the denominator — including a flow point whose crest is
above its own action flow. WRAW1 moved the same way: `"within 1% of"` → `"48 cfs below … (under
1% of this point's 5,500 cfs action flow)"`. **No level changed.**

**2. `packages/core/src/cascade_core/registry.py` — `product:nbm-v5-core` PT1H·PT1H → PT6H·PT8H
(finding E).** Measured on the fresh database with every job green:
`{"status": "degraded", "reasons": ["product:nbm-v5-core: stale: 47760 s old against a 3600 s
cadence (+3600 s grace)"]}`. NOAA publishes NBM `core` hourly, but freshness is computed against
the anchor Cascade *stores*, and `nbm.fetch_core_snowlvl` runs 6-hourly and selects its cycle with
`client.latest_qmd_cycle` (7.5 h latency), so the stored anchor is **7.5–13.5 h old at all times**
and could never be inside a 2 h tolerance. `/system/health` would have read `degraded` on roughly
every cycle forever — finding C in the mirror: an endpoint that says `degraded` whatever happens
hides a real failure exactly as well as one that says `ok`. `docs/DATA_SOURCES.md` line 249 was
the source of the PT1H·PT1H figure and is corrected with the reason.

**3. `packages/core/src/cascade_core/knowledge.py` + `registry.py` — bytes are not values
(finding F).** `product_freshness_anchors` fell back to `raw_artifact` for **any** product with no
value rows. `nbm.build_grid_masks` fetches a `product:nbm-v5-core` file of its own, so on a
database where `nbm.fetch_core_snowlvl` has never once succeeded the endpoint answered
`{"state": "current", "anchor": "raw_artifact", "reason": null}` — reproduced live before the fix.
The fallback is now restricted to a new `registry.METADATA_ONLY_PRODUCTS`
(`{product:awdb-stations}` — station metadata, which legitimately stores no value rows and would
otherwise read `missing` while being fetched daily). Verified live afterwards:
`product:nbm-v5-core → {"state": "missing", "anchor": null, "reason": "expected but never
ingested at this knowledge time; written by nbm.fetch_core_snowlvl"}`, while `awdb-stations` keeps
its `raw_artifact` anchor. **`tests/unit/test_system_health.py::test_everything_green_still_reads_ok`
was itself relying on the loophole** — it made every product `current` with `RawArtifact` rows and
no values — and was rewritten to write value rows.

**4. `agreement.py` — the sampling asymmetry is recorded on the magnitude axis (finding G).**
`QUALITY_COARSE_OFFICIAL_STEP` was appended only inside `if timing_assessable:`. Measured live,
the official series is 6-hourly (13 points) and the members hourly (78 points) over the same 78 h
window at **all five** comparable points, and because none of them crests, the flag was recorded
at **none** of them — while the magnitude comparison, which is what the level rested on, was the
asymmetric one. It is now recorded whenever the official step is coarser, and its note says what
that costs: on a peaked hydrograph the coarser series can step over a crest the finer one
resolves, biasing the difference toward *"the model exceeds the official forecast"*.

**5. Tests (all offline, no network).** `tests/unit/test_agreement.py`:
`test_the_percentage_in_the_reason_names_the_denominator_it_was_divided_by` (three cases: floored,
unfloored, and a flow point whose crest exceeds its action flow) and
`test_the_sampling_asymmetry_is_recorded_even_when_neither_side_crests`.
`tests/unit/test_job_registry.py`:
`test_no_product_expects_to_refresh_faster_than_the_job_that_writes_it` — the class-level
invariant behind finding E, which bites on exactly one product today and would bite on the next
one. `tests/unit/test_system_health.py`: `test_bytes_alone_never_make_a_product_current`, plus the
rewrite above. `tests/unit/test_p3_foundation.py`: the pinned NBM core cadence updated with the
reason.

### P3.9.6 — Storage delta from the member-series change, against design §8

Measured with `pg_column_size` on `cascadia_p3_adv` after one live cycle (6 reaches), projected at
4 cycles/day × 30 days = 120 cycles/month.

| | per cycle | rows/month | heap/month |
|---|---|---|---|
| `method:nwm-member-series@2.0.0` (**new**) | **6 rows, 12,060 B** (1,492–2,628 B/row; `values_json` 1,156–2,286 B compressed from 10.6–12.2 kB of JSON text) | 720 | **1.45 MB** |
| `method:nwm-member-crest@1.0.0` (old, §P3.7) | 42 rows, 20,076 B | 5,040 | 2.41 MB |
| **delta** | **−36 rows, −8,016 B (−40 %)** | **−4,320 (−86 %)** | **−0.96 MB** |
| `forecast_value` (NWM `mean`, unchanged) | 432 rows, 20,736 B (48 B/row) | 51,840 | 2.49 MB |

**Agreement surface totals:** 53,280 rows/month and **3.94 MB heap/month**, against design §8's
~57 k rows and ~10 MB — **inside budget on both**, and 0.96 MB/month cheaper than the pre-fix
shape. **P3 total Neon heap: ~20.6 MB/month (§P3.7) → ~19.6 MB/month.** With the pre-existing
~30 MB/month USGS IV write the combined figure is ~50 MB/month against Neon's 0.5 GB free tier —
the ~10-month horizon §P3.7 flagged is unchanged; this fix bought about two weeks of it.

**R2 is untouched by the change** — the same 157 kB JSON is fetched and archived either way.
Measured this cycle: `product:nwm-mr-via-nwps` 6 artifacts, **958,074 B** (+1.5 % on design §3.5's
944,076), → 3.83 MB/day → **115.0 MB/month** against §3.5's ~114 MB. Whole-run raw bytes
reproduced §P3.7 to within 0.03 %: qmd 1,816,540 (exact), core **550,321** = 378,594 (2 horizons)
+ 171,727 (the mask build's own f024 fetch — the byte trail behind finding F), susceptibility
133,563/day, one-time climatology 4,509,545. **P3 total 12.92 MB/day**, design 13.2.

### P3.9.7 — What still claims more than its inputs support

Not fixed. Each is a decision, not a patch.

1. **`explanation_ref` is a 404, and the method record it points at is not served.** Every basin
   emits `"explanation_ref": "/explanations/basin:skagit/agreement"`; `GET` on it returns **404**.
   That route is where `AgreementResult.method_record` — the window bounds, both shapes and their
   prominences, the band parameters and their ASSUMPTION sentence, and the **full text of every
   quality flag** — is supposed to live. The reason sentence carries at most **2** clauses of up
   to **6** flags, so on live data the ensemble-degeneracy note, the timing-not-assessable note,
   the trend note and the new sampling-asymmetry note are computed, tested, and reach nobody.
   `AgreementState` has no field for the record, so this needs a contract change plus a route.
   **This is the single largest gap in the slice: a surface that offers a reader an explanation
   link that does not resolve.**
2. **The magnitude comparison is 6-hourly against hourly and the dry-summer sample cannot show
   what that costs.** The flag is now recorded (§P3.9.5 item 4), but the bias only bites on a
   peaked hydrograph, and not one of the five comparable points crests inside the window in this
   sample. Neither the timing bands (6 h / 18 h) nor the crest-prominence threshold has ever been
   exercised by live data — only by unit tests. Hindcast calibration (ADR-0008) has to cover the
   sampling asymmetry alongside the 0.25/0.60 and 6 h/18 h bands.
3. **`high` is reachable while the two forecasts disagree about direction.** At AUBW1 the official
   run is *flat* (range 3.35 cfs over 294.7, 1.1 %) and the model *rises* to 28.7 % above it across
   the window; `QUALITY_TREND_DISAGREEMENT` caps at MODERATE only for `{rising, receding}`, and
   "flat" is treated as having no trend to contradict even when the other side moves 29 % away
   from it. The reason does say *"(official flat, NWM rising)"*, so the sentence is honest and the
   level is generous. Whether that asymmetry is right is a calibration question, not a bug.
4. **`RiverVisualizationState.agreement` is still `null`** at every river item, though design §3.3
   says the per-point state gets it. Verified live on `/viz/rivers`.
5. **Carried forward from the fixers, re-confirmed here:** `docs/DATA_SOURCES.md` lines 182/187
   still describe the superseded `method:nwm-member-crest@1.0.0` / `method:model-agreement@0.1.0`
   shape (reality: one row per reach under `method:nwm-member-series@2.0.0`, and
   `method:model-agreement@0.2.0`); design §3.2 step 4 and §3.4 are superseded on the precomputed
   crest summary and on Δt as an unconditional term; the stored `mean` series is still 72 h while
   the member series is 96 h. The `MODERATE` cap for opposing trends
   (`QUALITY_TREND_DISAGREEMENT`) remains a judgement call beyond the design and is visible live
   at MVEW1 and WRAW1.
6. **Smaller.** `usgs.build_climatology` has an annual cadence and `JOB_LATE_MULTIPLIER = 4`, so
   the *job* half of health would not call it late for four years — but
   `product:usgs-daily-stats` (P1Y + P30D grace) catches the same silence at ~395 days, so the
   payload is covered. `/system/health` `reasons` is unbounded (21 entries on a fresh database);
   fine to read, worth a cap if a client ever renders it raw.

### P3.9.8 — Cleanup

`cascadia_p3_adv` and `cascadia_p3_adv_pg` dropped; uvicorn on :8012 stopped; stale :4173/:8000
listeners killed before and after the Playwright run. Raw artifacts were written to the session
scratchpad (`CASCADE_RAW_DIR`), outside the repository. **The shared `cascadia` database was never
connected to and remains at revision `0001`.** Nothing committed, nothing pushed, no secrets
written.

### Verdict

Findings A, B and C are closed and each is proved by measurement rather than by intent: one window
object with identical bounds on both sides, `Δt` absent where there is no crest to time, and a
health endpoint that answers `unknown` / `ok` / `degraded` for the three situations that are
actually different. Three further defects of the same family were found live and fixed — a
percentage attributed to the wrong denominator, a product cadence that made `degraded` permanent,
and a freshness fallback that called bytes data. What remains is one route that does not exist:
the explanation the reason sentence promises, carrying the caveats there is no room for in one
sentence. Everything else on the list is calibration, which needs an event this sample does not
contain.

### P3.10 — Production found the eighth overclaim within an hour of deploy (2026-08-25)

`nbm.fetch_qmd` failed on every attempt in production with
`NbmParseError: field_missing: qmd f048 carries no 0-48 h APCP field`, so forcing stayed UNKNOWN
at all six basins. `/system/health` reported it — which is finding C's fix earning its keep on
its first day.

**Measured live across six cycles × three leads (S3 `.idx` sidecars, 2026-08-25):**

| cycle | f024 | f048 | f072 |
|---|---|---|---|
| 00Z, 12Z | `0-1 day acc` | `0-2 day acc` | `0-3 day acc` |
| 06Z, 18Z | `0-1 day acc` | none | none |

The intermediate cycles publish the per-day increments (`1-2 day`, `2-3 day`) and no 0-anchored
window at all. The design measured its numbers on a 12Z cycle (its `1,045,326 B` for `qmd.f072`
is exactly what a 12Z subset returns) and generalised to all four cycles; `QMD_CYCLE_HOURS` was
`(0, 6, 12, 18)`, so half of all runs asked for a field that was never coming.

**Fix.** `QMD_CYCLE_HOURS = (0, 12)`; product cadence PT6H → PT12H with grace PT9H; the job cron
became explicit — `40 7,19 * * *` rather than the derived `10 */12 * * *`, because the arithmetic
slot fires at 00:10/12:10 UTC and would collect a twelve-hour-old cycle every single time, while
each cycle lands about 7 h 20 m after its hour. The per-day increments are NOT summed into a
72-hour total: quantiles do not add, and the p90 of a three-day total is not the sum of three
daily p90s.

**Verified live after the fix** (cycle 20260824T12Z): `0-24`, `0-48` and `0-72` cumulative windows
all present; bytes/cycle **1,816,540 — the design's estimate to the byte**. Ingest cost halves,
since two cycles a day are fetched instead of four.

Same family as the SNOWLVL-at-f072 failure: asking a provider for a field it does not publish at
that cycle. The lesson both times is that a "field_missing" parse error is usually a request
error, and the honest fix is to stop asking.

### P3.11 — A regression my own fix introduced, caught by health (2026-08-26)

Restricting `QMD_CYCLE_HOURS` to the main cycles (§P3.10) also throttled the SNOW-LEVEL fetch,
because all three NBM jobs shared `latest_qmd_cycle`. `core` publishes on all four synoptic
cycles and lands ~44 min after its hour, so it inherited two wrong things at once: half the
cycles, and qmd's 7.5 h latency assumption. Production read `product:nbm-v5-core` **stale at
16.3 h while its job ran fine every 6 h** — no offline test could see it, because they all pass
an explicit cycle.

`core` now has its own `CORE_CYCLE_HOURS = (0, 6, 12, 18)` and `latest_core_cycle(latency 1.5 h)`.
Verified live: the selector moved from `20260825T12Z` (16.5 h old) to `20260826T00Z` (4.5 h old)
and the fetch returned all 15 SNOWLVL percentile levels — a twelve-hour freshness recovery.

Two further expectation-vs-reality corrections in the same pass, both found the same way:

- **Crons now follow publication, not arithmetic.** `nbm.fetch_core_snowlvl` moved to `50 */6`
  (the derived `:10` fired 34 min *before* each cycle landed, so it always took the previous
  one) and `nwm.fetch_reach_medium_range` to `45 0,6,12,18` (NWM medium range publishes ~6 h 30 m
  after its cycle).
- **`product:nwm-mr-via-nwps` grace 8 h → 12 h.** The freshest obtainable cycle is already ~6.5 h
  old, so a 14 h staleness threshold was unreachable in normal operation and health reported
  `degraded` on a healthy system.

The pattern across §P3.10 and §P3.11 is one thing: a declared expectation that the provider never
agreed to. Health is what makes those visible, which is why a health signal that cries wolf is
worth fixing as urgently as one that stays silent.
