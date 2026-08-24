"""PostgreSQL-gated queue roundtrip: apply-queue-schema (idempotent) -> defer a stub task ->
run the worker programmatically with wait=False until empty -> assert completion.

No provider logic and no network: the stub task is registered ad hoc; unique names per run
keep the test independent of whatever else lives in the shared dev database."""

from __future__ import annotations

import os
import uuid

import pytest
from procrastinate import App, PsycopgConnector

from cascade_core.settings import Settings
from cascade_worker.queue import apply_queue_schema, conninfo_from_url, queue_status

PG_URL = os.environ.get("CASCADE_TEST_PG_URL")

pytestmark = [
    pytest.mark.pg,
    pytest.mark.skipif(not PG_URL, reason="CASCADE_TEST_PG_URL not set (PostgreSQL-gated)"),
]


def _conninfo() -> str:
    assert PG_URL is not None
    return conninfo_from_url(Settings(db_url=PG_URL).effective_queue_db_url)


def _fresh_app() -> App:
    # one connector per open/close cycle: procrastinate connectors are not reopenable
    return App(connector=PsycopgConnector(conninfo=_conninfo()))


async def test_apply_queue_schema_is_idempotent() -> None:
    assert await apply_queue_schema(_fresh_app()) in ("applied", "already-applied")
    assert await apply_queue_schema(_fresh_app()) == "already-applied"  # safe to run twice


async def test_defer_then_worker_processes_until_empty() -> None:
    await apply_queue_schema(_fresh_app())
    marker = uuid.uuid4().hex  # unique task/queue names: re-runs never collide
    app = _fresh_app()
    ran: list[str] = []

    @app.task(name=f"tests.stub_{marker}", queue=f"tests-{marker}", queueing_lock=f"tests.stub_{marker}")
    async def stub(payload: str) -> str:
        ran.append(payload)
        return payload

    async with app.open_async():
        job_id = await stub.defer_async(payload=marker)
        await app.run_worker_async(
            queues=[f"tests-{marker}"],  # only our queue: never executes unrelated dev jobs
            wait=False,  # process until the queue is empty, then return
            install_signal_handlers=False,
            listen_notify=False,
        )
        assert ran == [marker]
        status = await app.job_manager.get_job_status_async(job_id)
        assert status.value == "succeeded"

    st = await queue_status(_fresh_app())
    assert st["totals"]["jobs_count"] >= 1
    queue_row = next(r for r in st["queues"] if r["name"] == f"tests-{marker}")
    assert queue_row["succeeded"] == 1 and queue_row["todo"] == 0 and queue_row["failed"] == 0
