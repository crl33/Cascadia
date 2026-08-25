"""Job registry with cadences, `run_once` (all jobs, in dependency order) and `run_forever`
(asyncio loop; each job runs when due; failures are recorded and the loop continues).

`JOBS` is ORDERED, and the order is a dependency order, not a preference: `run_once` walks it
top to bottom, so a job that produces what another job reads is listed first. Two of those
dependencies are load-bearing for P3 and each fails *safely* rather than loudly when it is
violated, which is exactly why they are written down here:

- ``nbm.build_grid_masks`` before ``nbm.fetch_qmd`` / ``nbm.fetch_core_snowlvl``. Without a mask
  for the live grid definition the NBM jobs record refusals and every basin's forcing surface
  reads UNKNOWN with the "grid definition changed" reason. That is the designed behaviour — a
  basin mean is never approximated over a grid the mask was not built for — but it looks like a
  broken surface, so the mask job runs first and, on the queue, on its own earlier cron slot.
- ``usgs.build_climatology`` before ``usgs.fetch_daily_percentile``. The percentile job ranks
  today's daily mean inside a stored day-of-year ladder; with no ladder there is no percentile
  and susceptibility is UNKNOWN with the "no climatology" reason.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.fetch import ArchivingFetcher
from cascade_core.settings import Settings
from cascade_providers_awdb import jobs as awdb_jobs
from cascade_providers_nbm import jobs as nbm_jobs
from cascade_providers_nwps import jobs as nwps_jobs
from cascade_providers_nwps import reaches_jobs as nwm_jobs
from cascade_providers_usgs import jobs as usgs_jobs
from cascade_providers_usgs import stats_jobs as usgs_stats_jobs
from cascade_worker.runtime import JobFn, Runtime, run_job

log = logging.getLogger("cascade.worker")


@dataclass(frozen=True)
class Job:
    name: str
    cadence_seconds: int
    fn: JobFn
    #: An explicit cron for the queue, when the cadence alone does not say enough. Only used
    #: where the *slot* matters relative to another job — `cron_for_cadence` would put the mask
    #: build in the same minute as the NBM fetch that depends on it. `None` means "derive it
    #: from the cadence", which is the normal case.
    cron: str | None = None


async def _run_build_grid_masks(session: AsyncSession, fetcher: ArchivingFetcher) -> int:
    """`nbm.build_grid_masks` adapted to the `JobFn` contract (it returns per-basin reports).

    ``rows_written`` counts the masks actually written, so a re-run against an unchanged grid
    reports 0 rather than claiming six writes it did not make. The geometry directory comes from
    the environment (``CASCADE_GEO_DIR``) rather than the provider default, which is relative to
    the process working directory — the container sets an absolute path and the job should honour
    it instead of depending on where it was launched from.
    """
    reports = await nbm_jobs.run_build_grid_masks(session, fetcher, geo_dir=Settings.from_env().geo_dir)
    return sum(1 for report in reports if report.built)


JOBS: tuple[Job, ...] = (
    # --- observational truth and the official forecast (spike scope) ---------------------
    Job(nwps_jobs.JOB_THRESHOLDS, nwps_jobs.CADENCE_THRESHOLDS_SECONDS, nwps_jobs.run_fetch_thresholds),
    Job(nwps_jobs.JOB_FORECAST, nwps_jobs.CADENCE_FORECAST_SECONDS, nwps_jobs.run_fetch_forecast),
    Job(usgs_jobs.JOB_NAME, usgs_jobs.CADENCE_SECONDS, usgs_jobs.run_fetch_iv),
    # --- P3 forcing: masks first, then the two NBM subsets ------------------------------
    # 05:50 UTC: twenty minutes ahead of the 06:10 qmd slot, so a grid change is picked up
    # before the cycle that would otherwise be refused. A no-op day costs one ~172 KB subset.
    Job(nbm_jobs.JOB_BUILD_MASKS, 86400, _run_build_grid_masks, cron="50 5 * * *"),
    Job(nbm_jobs.JOB_FETCH_QMD, nbm_jobs.CADENCE_QMD_SECONDS, nbm_jobs.run_fetch_qmd),
    Job(nbm_jobs.JOB_FETCH_CORE_SNOWLVL, nbm_jobs.CADENCE_CORE_SNOWLVL_SECONDS, nbm_jobs.run_fetch_core_snowlvl),
    # --- P3 agreement: the independent model's ensemble at each seeded reach -------------
    Job(nwm_jobs.JOB_NAME, nwm_jobs.CADENCE_SECONDS, nwm_jobs.run_fetch_medium_range),
    # --- P3 susceptibility: the ladder, then today's rank inside it, then SNOTEL context --
    Job(usgs_stats_jobs.BUILD_JOB_NAME, usgs_stats_jobs.BUILD_CADENCE_SECONDS, usgs_stats_jobs.run_build_climatology),
    Job(usgs_stats_jobs.DAILY_JOB_NAME, usgs_stats_jobs.DAILY_CADENCE_SECONDS, usgs_stats_jobs.run_fetch_daily_percentile),
    Job(awdb_jobs.JOB_NAME, awdb_jobs.CADENCE_SECONDS, awdb_jobs.run_fetch_snotel_context),
)


async def run_once(rt: Runtime, jobs: Sequence[Job] | None = None) -> list[tuple[str, bool, int, str | None]]:
    """Run each job once, in `JOBS` order. `jobs` runs a subset (tests, targeted backfills)."""
    out = []
    for job in jobs if jobs is not None else JOBS:
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
