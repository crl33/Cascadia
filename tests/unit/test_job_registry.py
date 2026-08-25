"""The job catalogue cannot silently fall behind the scheduler, and /system/health cannot silently
fall behind the catalogue.

Why this file exists: `/system/health` used to be driven by a hand-written map of three job names
and three product ids while the scheduler registered ten jobs. `nbm.fetch_core_snowlvl` then failed
on **every** cycle and the endpoint answered `status: ok` — "the mechanism by which that failure
would have stayed invisible in production forever"
(docs/research/pg-migration-verification-2026-08-24.md §P3.6 finding C).

`cascade_api` may not import `cascade_worker` (the import contract in pyproject.toml forbids the
provider adapters reaching the API, and the scheduler imports all of them), so the catalogue lives
in `cascade_core.registry` and the worker binds callables to it. That is two lists — which is
exactly the shape of the original defect — so this test imports BOTH, in the test process only, and
fails on any drift between them. Adding a job to the scheduler and forgetting the registry is a red
test here, not a blind spot in production.

The authority for "registered" is the QUEUE app's task table, not `scheduler.JOBS`, because those
two already disagree: `maintenance.ensure_observation_partitions` is registered on the queue alone
(it needs PostgreSQL, so `run-once` on sqlite must not carry it) and it runs through `run_job` and
leaves job_run rows like any other job. Pinning against `scheduler.JOBS` would have re-created the
same blind spot one layer down.
"""

from __future__ import annotations

import pytest
from procrastinate.testing import InMemoryConnector

from cascade_api.routes import HEALTH_PRODUCTS, JOB_TO_PROVIDER
from cascade_core.registry import (
    JOBS,
    JOBS_BY_NAME,
    PRODUCT_WRITERS,
    PRODUCTS,
    SOURCES,
    UNSCHEDULED_PRODUCTS,
)
from cascade_core.settings import Settings
from cascade_worker.queue import create_queue_app
from cascade_worker.scheduler import JOBS as SCHEDULED_JOBS

#: Every CASCADIA task the worker registers: the scheduler's jobs plus the queue-only maintenance
#: job. Built with the in-memory connector — no PostgreSQL, no network. Procrastinate's own
#: housekeeping tasks (`procrastinate.builtin_tasks.*`, and the `builtin:` aliases of them) are
#: excluded: they are the queue library maintaining itself, they never go through `run_job`, and
#: they leave no job_run row for health to read.
REGISTERED_JOB_NAMES = frozenset(
    name
    for name in create_queue_app(Settings(db_url="postgresql+psycopg://postgres:x@127.0.0.1:5433/none"), connector=InMemoryConnector()).tasks
    if not name.startswith(("procrastinate.", "builtin:"))
)

REGISTERED_PRODUCT_IDS = {str(p["id"]) for p in PRODUCTS}
REGISTERED_SOURCE_IDS = {str(s["id"]) for s in SOURCES}


def missing_from_catalogue(registered_names) -> set[str]:
    """The check itself, so the test below can prove it bites on a job that is not in the catalogue."""
    return set(registered_names) - set(JOBS_BY_NAME)


def test_every_registered_job_is_in_the_registry_catalogue() -> None:
    assert missing_from_catalogue(REGISTERED_JOB_NAMES) == set()
    assert set(JOBS_BY_NAME) == set(REGISTERED_JOB_NAMES)
    assert len(JOBS) == len(REGISTERED_JOB_NAMES) == 11


def test_a_job_registered_only_in_the_worker_fails_the_check() -> None:
    """The guard bites. A new worker job that nobody added to the catalogue is caught here."""
    assert missing_from_catalogue({*REGISTERED_JOB_NAMES, "nbm.fetch_something_new"}) == {"nbm.fetch_something_new"}


def test_the_queue_only_maintenance_job_is_covered() -> None:
    """It is registered on the queue and not in `scheduler.JOBS`; it still writes job_run rows."""
    assert "maintenance.ensure_observation_partitions" not in {job.name for job in SCHEDULED_JOBS}
    assert "maintenance.ensure_observation_partitions" in REGISTERED_JOB_NAMES
    assert "maintenance.ensure_observation_partitions" in JOB_TO_PROVIDER


def test_cadences_agree_between_the_scheduler_and_the_catalogue() -> None:
    disagreements = {job.name: (job.cadence_seconds, JOBS_BY_NAME[job.name].cadence_seconds) for job in SCHEDULED_JOBS if JOBS_BY_NAME[job.name].cadence_seconds != job.cadence_seconds}
    assert disagreements == {}


def test_catalogue_ids_resolve_in_the_registry() -> None:
    """A job never invents a source or a product: both come from the registry vocabulary."""
    for spec in JOBS:
        assert spec.source_id in REGISTERED_SOURCE_IDS, spec.name
        assert set(spec.products) <= REGISTERED_PRODUCT_IDS, spec.name


def test_every_registered_product_is_written_by_a_job_or_declared_unscheduled() -> None:
    """The other direction: a product added to the registry cannot quietly vanish from health.

    Either some job writes it — and then /system/health expects it — or it is named in
    UNSCHEDULED_PRODUCTS with the reason, which makes "nothing writes this" a decision on the
    record rather than an omission nobody notices.
    """
    unaccounted = REGISTERED_PRODUCT_IDS - set(PRODUCT_WRITERS) - set(UNSCHEDULED_PRODUCTS)
    assert unaccounted == set()
    assert set(UNSCHEDULED_PRODUCTS) <= REGISTERED_PRODUCT_IDS
    assert all(reason for reason in UNSCHEDULED_PRODUCTS.values())


def test_no_product_expects_to_refresh_faster_than_the_job_that_writes_it() -> None:
    """A product cannot be fresher than its writer, and freshness is judged on what we STORE.

    `product:nbm-v5-core` carried `expected_cadence_seconds = 3600` because NOAA publishes NBM
    `core` hourly — but `nbm.fetch_core_snowlvl` runs 6-hourly and picks its cycle 7.5 h in
    arrears, so the stored anchor is between 7.5 h and 13.5 h old at all times and the product
    was STALE on every cycle. Measured live 2026-08-25 with all ten jobs green, `/system/health`
    answered `degraded` naming that product alone (§P3.9). That is finding C in the mirror: an
    endpoint that says `degraded` whatever happens hides a real failure just as well as one that
    said `ok` whatever happened.

    The invariant is cadence only — `grace_seconds` is what absorbs provider latency, and the
    products that satisfy this exactly (usgs-iv, nwps-thresholds, nbm-qmd, nwm-mr, awdb-daily)
    all rely on it doing so.
    """
    too_fast = {
        pid: (p_cadence, jobs, min(JOBS_BY_NAME[j].cadence_seconds for j in jobs))
        for pid, jobs in PRODUCT_WRITERS.items()
        for p_cadence in [next(int(p["expected_cadence_seconds"]) for p in PRODUCTS if p["id"] == pid)]
        if p_cadence < min(JOBS_BY_NAME[j].cadence_seconds for j in jobs)
    }
    assert too_fast == {}, "product cadence is faster than the job that writes it: " + repr(too_fast)


@pytest.mark.parametrize("job_name", sorted(REGISTERED_JOB_NAMES))
def test_health_covers_every_registered_job(job_name: str) -> None:
    """The endpoint's own maps. Parametrized per job so a gap names the job that is not covered."""
    assert job_name in JOB_TO_PROVIDER, f"{job_name} is registered but /system/health does not see it"


def test_health_expects_every_product_a_registered_job_writes() -> None:
    assert set(HEALTH_PRODUCTS) == set(PRODUCT_WRITERS)
    assert "product:nbm-v5-core" in HEALTH_PRODUCTS  # the product behind finding C
