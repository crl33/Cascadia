# apps/worker — the only writer

One job: run the provider jobs on their cadences, record each run, never serve HTTP.

## Inputs
- Environment (`packages/core/settings.py`), the seed data (`cascade_core/seed/stations.json`,
  `tests/fixtures/geo/*.geojson`), and the providers' `jobs.py` (USGS IV every 15 min, NWPS
  thresholds every 6 h, NWPS forecast every 30 min).

## Outputs
- `python -m cascade_worker seed` — schema + reference rows (idempotent).
- `python -m cascade_worker run-once` — every job once, in order thresholds -> forecast -> USGS;
  prints one JSON line per job (ok, rows_written, error). Exit 1 if any job failed.
- `python -m cascade_worker run` — the asyncio scheduler loop (legacy; superseded by `worker`).
- `python -m cascade_worker worker` — the procrastinate worker (ADR-0003): executes queued
  jobs and runs the periodic deferrer (USGS `*/15`, forecast `*/30`, thresholds `10 */6`);
  `queueing_lock`/`lock` = job name (one queued + one running instance per job across
  replicas); exponential retry, 5 attempts. Requires PostgreSQL (`CASCADE_QUEUE_DB_URL` or
  `CASCADE_DB_URL`, DIRECT connection, never a PgBouncer pooler). Railway entrypoint;
  SIGTERM shuts down gracefully.
- `python -m cascade_worker apply-queue-schema` — procrastinate schema, idempotent.
- `python -m cascade_worker queue-status` — pending/doing/failed counts as JSON.
- Rows in `raw_artifact`, `observation`, `forecast_run`/`forecast_value`, `threshold`, `job_run`.

## Human check
Run `run-once` twice. The second run must report `rows_written: 0` for USGS and the forecast job
(idempotent), while `raw_artifact` gains one row per request (every fetch is archived).
