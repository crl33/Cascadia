"""Procrastinate queue app (ADR-0003): one task per scheduler Job, wrapping `run_job` unchanged.

Composition contract:
- The provider job functions (packages/providers/*/jobs.py) are FROZEN; this module never
  calls them directly. Each procrastinate task calls ``run_job(rt, name, fn)`` so job_run
  bookkeeping (started/finished/ok/rows/error, docs/ARCHITECTURE.md §3 "Health") is identical
  to the run-once path.
- ``run_job`` never re-raises (the failure IS the record). To hand the *retry* decision to
  procrastinate, the task re-raises ``JobFailed`` after the job_run row is recorded, so each
  attempt is one job_run row and the queue backs off exponentially (5 attempts max).
- ``queueing_lock = lock = job name``: at most one queued and one running instance per job,
  even with N worker replicas; the periodic deferrer's duplicate defers are skipped
  (AlreadyEnqueued) instead of piling up.
- The queue requires PostgreSQL (LISTEN/NOTIFY + row locks). sqlite keeps working for
  ``seed`` / ``run-once``; ``conninfo_from_url`` fails loudly for anything non-PostgreSQL.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from procrastinate import App, PsycopgConnector, RetryStrategy
from procrastinate.connector import BaseConnector
from sqlalchemy.engine.url import make_url

from cascade_core.settings import Settings
from cascade_worker.runtime import Runtime, run_job
from cascade_worker.scheduler import JOBS, Job

log = logging.getLogger("cascade.worker.queue")

QUEUE_NAME = "ingest"

#: Exponential backoff: waits of 4^1..4^4 s (4 s, 16 s, 64 s, ~4 min) between the 5 attempts.
RETRY = RetryStrategy(max_attempts=5, exponential_wait=4)


class JobFailed(Exception):
    """Raised to make procrastinate retry; the job_run row (ok=False, error) already exists."""


def conninfo_from_url(url: str) -> str:
    """SQLAlchemy URL (``postgresql+psycopg://...``) -> plain libpq conninfo URI.

    Raises ``ValueError`` for any non-PostgreSQL URL: the queue requires PostgreSQL;
    ``seed`` and ``run-once`` still work everywhere (direct asyncio path).
    """
    u = make_url(url)
    if u.get_backend_name() != "postgresql":
        raise ValueError(
            f"the job queue requires PostgreSQL, got {u.get_backend_name()!r}. "
            "`python -m cascade_worker seed|run-once` work on sqlite; for `worker`, "
            "`apply-queue-schema` and `queue-status` set CASCADE_QUEUE_DB_URL (or "
            "CASCADE_DB_URL) to a PostgreSQL DSN (a DIRECT one, not a PgBouncer pooler)."
        )
    return u.set(drivername="postgresql").render_as_string(hide_password=False)


def cron_for_cadence(seconds: int) -> str:
    """Map a job cadence to a cron string: 900 s -> ``*/15 * * * *``, 1800 s -> ``*/30``,
    whole-hour cadences -> a fixed minute (:10, avoiding the top-of-hour stampede)."""
    if seconds % 60 == 0 and seconds < 3600 and 3600 % seconds == 0:
        return f"*/{seconds // 60} * * * *"
    if seconds % 3600 == 0 and (24 * 3600) % seconds == 0:
        return f"10 */{seconds // 3600} * * *"
    raise ValueError(f"no cron mapping for cadence {seconds}s; add one deliberately")


def create_queue_app(
    settings: Settings,
    *,
    connector: BaseConnector | None = None,
    runtime_factory: Callable[[Settings], Runtime] | None = None,
) -> App:
    """Build the procrastinate App from Settings.

    ``connector=None`` derives a PsycopgConnector from ``queue_db_url`` (falling back to
    ``db_url``); tests pass ``procrastinate.testing.InMemoryConnector()``. The Runtime
    (engine, rate-limited archiving fetcher) is built lazily, once per worker process.
    """
    if connector is None:
        connector = PsycopgConnector(conninfo=conninfo_from_url(settings.effective_queue_db_url))
    app = App(connector=connector)
    factory = runtime_factory or Runtime.build
    holder: dict[str, Runtime] = {}

    def runtime() -> Runtime:
        if "rt" not in holder:
            holder["rt"] = factory(settings)
        return holder["rt"]

    for job in JOBS:
        _register_job(app, job, runtime)
    return app


def _register_job(app: App, job: Job, runtime: Callable[[], Runtime]) -> None:
    async def _run(timestamp: int | None = None) -> dict[str, Any]:
        # `timestamp` is injected by the periodic deferrer (cron slot, epoch seconds);
        # manual defers omit it.
        jr = await run_job(runtime(), job.name, job.fn)
        log.info("queue job %s ok=%s rows=%s error=%s", job.name, jr.ok, jr.rows_written, jr.error)
        if not jr.ok:
            raise JobFailed(f"{job.name}: {jr.error}")
        return {"job": job.name, "ok": True, "rows_written": jr.rows_written, "timestamp": timestamp}

    _run.__name__ = job.name.replace(".", "_")
    _run.__qualname__ = _run.__name__
    task = app.task(
        name=job.name,
        queue=QUEUE_NAME,
        queueing_lock=job.name,
        lock=job.name,
        retry=RETRY,
    )(_run)
    app.periodic(cron=cron_for_cadence(job.cadence_seconds), periodic_id="cadence")(task)


async def apply_queue_schema(app: App) -> str:
    """Apply the procrastinate schema; a no-op when already present (safe to run twice)."""
    async with app.open_async():
        if await app.job_manager.check_connection_async():
            return "already-applied"
        await app.schema_manager.apply_schema_async()
        return "applied"


async def queue_status(app: App) -> dict[str, Any]:
    """Job counts by status (pending=todo / doing / failed / ...), total and per queue."""
    async with app.open_async():
        rows = [dict(r) for r in await app.job_manager.list_queues_async()]
    keys = ("jobs_count", "todo", "doing", "succeeded", "failed", "cancelled", "aborted")
    return {"totals": {k: sum(r.get(k, 0) for r in rows) for k in keys}, "queues": rows}


async def run_worker(app: App, **options: Any) -> None:
    """Run the worker (job execution + periodic deferrer). With the default
    ``install_signal_handlers=True`` SIGTERM/SIGINT trigger a graceful shutdown:
    running jobs finish (up to ``shutdown_graceful_timeout``) before the process exits."""
    async with app.open_async():
        await app.run_worker_async(**options)
