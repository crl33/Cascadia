"""Job registry with cadences, `run_once` (all jobs, in dependency order) and `run_forever`
(asyncio loop; each job runs when due; failures are recorded and the loop continues)."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass

from cascade_providers_nwps import jobs as nwps_jobs
from cascade_providers_usgs import jobs as usgs_jobs
from cascade_worker.runtime import JobFn, Runtime, run_job

log = logging.getLogger("cascade.worker")


@dataclass(frozen=True)
class Job:
    name: str
    cadence_seconds: int
    fn: JobFn


JOBS: tuple[Job, ...] = (
    Job(nwps_jobs.JOB_THRESHOLDS, nwps_jobs.CADENCE_THRESHOLDS_SECONDS, nwps_jobs.run_fetch_thresholds),
    Job(nwps_jobs.JOB_FORECAST, nwps_jobs.CADENCE_FORECAST_SECONDS, nwps_jobs.run_fetch_forecast),
    Job(usgs_jobs.JOB_NAME, usgs_jobs.CADENCE_SECONDS, usgs_jobs.run_fetch_iv),
)


async def run_once(rt: Runtime) -> list[tuple[str, bool, int, str | None]]:
    out = []
    for job in JOBS:
        jr = await run_job(rt, job.name, job.fn)
        log.info("job %s ok=%s rows=%s error=%s", job.name, jr.ok, jr.rows_written, jr.error)
        out.append((job.name, bool(jr.ok), jr.rows_written, jr.error))
    return out


async def run_forever(rt: Runtime, *, tick_seconds: float = 5.0) -> None:
    due = {job.name: 0.0 for job in JOBS}
    while True:
        now = time.monotonic()
        for job in JOBS:
            if now >= due[job.name]:
                jr = await run_job(rt, job.name, job.fn)
                log.info("job %s ok=%s rows=%s error=%s", job.name, jr.ok, jr.rows_written, jr.error)
                due[job.name] = time.monotonic() + job.cadence_seconds
        await asyncio.sleep(tick_seconds)
