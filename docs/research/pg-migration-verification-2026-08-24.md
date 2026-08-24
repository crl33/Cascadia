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
