"""Defer one named job into the procrastinate queue — the manual-defer path, as tooling.

`queue.py` documents `app.tasks[name].defer_async()` as the answer to "the cron slot has
passed and the data now exists" (first needed 2026-08-28: NSIDC served the day's SNODAS tar
late, the single 13:40Z attempt found nothing, and the fix's 17:40Z retry slot had also
passed — production faced 24 h of staleness for want of one enqueue). This script is that
answer with a name: it enqueues; whichever worker watches the queue executes with its own
fetcher, store and credentials.

The queue connection comes from ``CASCADE_QUEUE_DB_URL`` (falling back to ``CASCADE_DB_URL``)
— the same variables the worker itself reads. Point them at production only from the
credential env files outside the repo; nothing here embeds or prints a URL.

The job name must be one the worker registers (scheduler.JOBS / maintenance). A duplicate
defer while the same job is already queued is refused by procrastinate's queueing lock —
that refusal is reported, not treated as failure, because the job IS going to run.

Usage: .venv/bin/python scripts/defer_job.py snodas.fetch_swe
"""

from __future__ import annotations

import asyncio
import sys

from procrastinate.exceptions import AlreadyEnqueued

from cascade_worker.queue import create_queue_app
from cascade_worker.runtime import Settings


async def defer(name: str) -> int:
    app = create_queue_app(Settings.from_env())
    if name not in app.tasks:
        known = ", ".join(sorted(app.tasks))
        print(f"unknown job {name!r}; the worker registers: {known}", file=sys.stderr)
        return 2
    async with app.open_async():
        try:
            job_id = await app.tasks[name].defer_async()
        except AlreadyEnqueued:
            print(f"{name}: already queued (queueing lock); it will run")
            return 0
    print(f"{name}: deferred as job {job_id}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    sys.exit(asyncio.run(defer(sys.argv[1])))
