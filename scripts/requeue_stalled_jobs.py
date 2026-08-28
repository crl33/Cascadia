"""Requeue queue jobs stuck in 'doing' after their worker died — procrastinate's own recovery.

A worker that dies mid-job (a deploy replacing the container, an OOM) leaves its job row in
'doing'. Because every task here runs under ``lock=name``, that orphan WEDGES the task: later
defers queue behind it forever and the product goes stale while /system/health counts the
silence. First real case, 2026-08-28: `usgs.fetch_instantaneous` job 935 hung mid-fetch at
20:00Z, the 21:02Z deploy killed its worker, and instantaneous ingest stopped until this
requeue.

Uses the queue's supported API — ``get_stalled_jobs`` (doing beyond a threshold, or belonging
to pruned workers) and ``retry_job`` — never raw UPDATEs. The connection comes from
``CASCADE_QUEUE_DB_URL`` / ``CASCADE_DB_URL``, the same variables the worker reads; point
them at production only from the credential env files outside the repo.

Also closes the matching orphaned ``job_run`` rows (ok NULL, started before the stall
threshold) as ok=false with the reason, so the health payload tells the truth about what
happened instead of showing a run forever in flight.

Usage: .venv/bin/python scripts/requeue_stalled_jobs.py [--nb-seconds 1200]
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from procrastinate import exceptions as pq_exceptions
from procrastinate import jobs as pq_jobs
from sqlalchemy import text

from cascade_core.db import make_engine, make_session_factory
from cascade_worker.queue import create_queue_app
from cascade_worker.runtime import Settings


async def requeue(nb_seconds: int) -> int:
    settings = Settings.from_env()
    app = create_queue_app(settings)
    async with app.open_async():
        stalled = await app.job_manager.get_stalled_jobs(nb_seconds=nb_seconds)
        if not stalled:
            print(f"no jobs stalled in 'doing' beyond {nb_seconds} s; nothing to requeue")
        for job in stalled:
            try:
                await app.job_manager.retry_job(job)
                print(f"requeued: job {job.id} {job.task_name!r} (was doing since its worker died)")
            except pq_exceptions.UniqueViolation:
                # A duplicate 'todo' already holds the queueing lock — the periodic deferrer
                # queued the next run while the orphan sat there. The queued one carries the
                # work; the orphan is finished honestly as failed, which frees the RUN lock.
                await app.job_manager.finish_job_by_id_async(job.id, pq_jobs.Status.FAILED, False)
                print(f"failed-out: job {job.id} {job.task_name!r} (a queued duplicate already holds the lock)")

    engine = make_engine(settings.db_url)
    async with make_session_factory(engine)() as session:
        result = await session.execute(text(
            "UPDATE job_run SET finished_at = now(), ok = false, "
            "error = 'orphaned: worker died mid-run; queue job requeued by requeue_stalled_jobs' "
            "WHERE ok IS NULL AND finished_at IS NULL "
            "AND started_at < now() - make_interval(secs => :secs)"
        ), {"secs": nb_seconds})
        await session.commit()
        if result.rowcount:
            print(f"closed {result.rowcount} orphaned job_run row(s) as ok=false with the reason")
    await engine.dispose()
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nb-seconds", type=int, default=1200,
                        help="a 'doing' older than this is stalled (default 20 min; the longest healthy job is ~2 min)")
    args = parser.parse_args()
    sys.exit(asyncio.run(requeue(args.nb_seconds)))
