"""Queue app: cron derivation, conninfo conversion, task registration (locks, retry, periodic),
defer dedupe via queueing_lock, the run_job wrap contract, and the partition-maintenance
task's registration/window math. Offline: InMemoryConnector only."""

from __future__ import annotations

from datetime import date

import pytest
from procrastinate import exceptions
from procrastinate.testing import InMemoryConnector

from cascade_core.settings import Settings
from cascade_worker import maintenance
from cascade_worker import queue as q
from cascade_worker.scheduler import JOBS

PG_SETTINGS = Settings(db_url="postgresql+psycopg://postgres:dev@127.0.0.1:5433/cascadia")


def test_cron_for_cadence_maps_the_known_cadences() -> None:
    assert q.cron_for_cadence(900) == "*/15 * * * *"
    assert q.cron_for_cadence(1800) == "*/30 * * * *"
    assert q.cron_for_cadence(6 * 3600) == "10 */6 * * *"  # fixed minute every 6 hours
    assert q.cron_for_cadence(3600) == "10 */1 * * *"
    with pytest.raises(ValueError, match="no cron mapping"):
        q.cron_for_cadence(700)  # does not divide the hour
    with pytest.raises(ValueError, match="no cron mapping"):
        q.cron_for_cadence(7 * 3600)  # does not divide the day


def test_conninfo_from_url_strips_the_sqlalchemy_driver() -> None:
    assert q.conninfo_from_url("postgresql+psycopg://postgres:dev@127.0.0.1:5433/cascadia") == "postgresql://postgres:dev@127.0.0.1:5433/cascadia"
    # query params (sslmode) and encoded passwords survive the conversion
    assert q.conninfo_from_url("postgresql+psycopg://u:p%40ss@host.example/db?sslmode=require") == "postgresql://u:p%40ss@host.example/db?sslmode=require"


def test_conninfo_rejects_sqlite_with_a_clear_error() -> None:
    with pytest.raises(ValueError, match="requires PostgreSQL"):
        q.conninfo_from_url("sqlite+aiosqlite:///./data/cascade.db")


def test_create_queue_app_rejects_sqlite_settings() -> None:
    with pytest.raises(ValueError, match="requires PostgreSQL"):
        q.create_queue_app(Settings())  # default Settings is sqlite


def test_tasks_registered_with_locks_retry_and_cron() -> None:
    app = q.create_queue_app(PG_SETTINGS, connector=InMemoryConnector())
    for job in JOBS:
        task = app.tasks[job.name]
        assert task.queueing_lock == job.name  # never two queued instances of one job
        assert task.lock == job.name  # never two running instances of one job
        assert task.queue == q.QUEUE_NAME
        assert task.retry_strategy is not None
        assert task.retry_strategy.max_attempts == 5
        assert task.retry_strategy.exponential_wait == 4
    crons = {name: pt.cron for (name, _), pt in app.periodic_registry.periodic_tasks.items()}
    assert crons == {
        "usgs.fetch_iv": "*/15 * * * *",
        "nwps.fetch_forecast": "*/30 * * * *",
        "nwps.fetch_thresholds": "10 */6 * * *",
        "maintenance.ensure_observation_partitions": "3 0 1 * *",
    }


def test_partition_maintenance_task_registered_with_monthly_cron() -> None:
    app = q.create_queue_app(PG_SETTINGS, connector=InMemoryConnector())
    task = app.tasks[maintenance.JOB_NAME]
    assert task.queueing_lock == maintenance.JOB_NAME  # never two queued instances
    assert task.lock == maintenance.JOB_NAME  # never two running instances
    assert task.queue == q.QUEUE_NAME
    assert task.retry_strategy is not None
    crons = {name: pt.cron for (name, _), pt in app.periodic_registry.periodic_tasks.items()}
    assert crons[maintenance.JOB_NAME] == "3 0 1 * *"  # 00:03 UTC, 1st of the month


def test_month_window_spans_current_month_through_13_ahead() -> None:
    assert maintenance.month_window(date(2026, 8, 24)) == (date(2026, 8, 1), date(2027, 9, 1))
    assert maintenance.month_window(date(2026, 12, 31)) == (date(2026, 12, 1), date(2028, 1, 1))  # year rollover
    assert maintenance.month_window(date(2027, 1, 1)) == (date(2027, 1, 1), date(2028, 2, 1))


async def test_defer_works_and_queueing_lock_dedupes() -> None:
    connector = InMemoryConnector()
    app = q.create_queue_app(PG_SETTINGS, connector=connector)
    async with app.open_async():
        await app.tasks["usgs.fetch_iv"].defer_async()
        with pytest.raises(exceptions.AlreadyEnqueued):
            await app.tasks["usgs.fetch_iv"].defer_async()
        await app.tasks["nwps.fetch_forecast"].defer_async()  # a different job is unaffected
    assert sorted(j["task_name"] for j in connector.jobs.values()) == ["nwps.fetch_forecast", "usgs.fetch_iv"]
    assert all(j["status"] == "todo" for j in connector.jobs.values())


class _FakeJobRun:
    def __init__(self, ok: bool, rows: int, error: str | None) -> None:
        self.ok, self.rows_written, self.error = ok, rows, error


async def test_task_wraps_run_job_and_raises_only_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[object, str, object]] = []
    fake_rt = object()
    built: list[object] = []

    async def fake_run_job(rt: object, name: str, fn: object) -> _FakeJobRun:
        calls.append((rt, name, fn))
        return _FakeJobRun(True, 7, None) if name == "usgs.fetch_iv" else _FakeJobRun(False, 0, "boom")

    def factory(settings: Settings) -> object:
        built.append(settings)
        return fake_rt

    monkeypatch.setattr(q, "run_job", fake_run_job)
    app = q.create_queue_app(PG_SETTINGS, connector=InMemoryConnector(), runtime_factory=factory)

    out = await app.tasks["usgs.fetch_iv"].func(timestamp=123)
    assert out == {"job": "usgs.fetch_iv", "ok": True, "rows_written": 7, "timestamp": 123}
    by_name = {j.name: j for j in JOBS}
    assert calls[0] == (fake_rt, "usgs.fetch_iv", by_name["usgs.fetch_iv"].fn)  # frozen fn passed through untouched

    # run_job recorded the failure in job_run; the task re-raises so procrastinate retries
    with pytest.raises(q.JobFailed, match="nwps.fetch_forecast: boom"):
        await app.tasks["nwps.fetch_forecast"].func()
    assert calls[1][1] == "nwps.fetch_forecast"
    assert built == [PG_SETTINGS]  # the Runtime is built lazily, once per process
