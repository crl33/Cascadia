"""/system/events: notify-then-fetch — names of what changed, nothing else, live-cost-only.

The broker is the honest part: it reads the same anchors /system/health trusts, so it sees
every writer without cooperation; it emits only CHANGES (the first tick primes silently); and
it runs only while someone is listening, because an idle poller is exactly the Neon
compute-hour leak the deployment memory warns about.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta

import pytest

from cascade_api.events import IngestEventBroker, sse_stream
from cascade_core.db import create_schema, make_engine, make_session_factory
from cascade_core.models import OfficialAlertRecord, RawArtifact
from cascade_core.registry import PRODUCT_NWS_ALERTS, PRODUCT_USGS_IV
from cascade_core.timeutils import utcnow


@pytest.fixture
async def db(tmp_path):
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path}/events.db")
    await create_schema(engine)
    yield make_session_factory(engine)
    await engine.dispose()


def _artifact(product_id: str, at: datetime, n: int) -> RawArtifact:
    return RawArtifact(sha256=f"{n:064d}", object_key=f"e/{n}", product_id=product_id,
                       fetched_at=at, request_url="https://example.invalid/e", bytes=1,
                       http_status=200, content_type="application/json")


async def test_a_new_ingest_becomes_one_event_and_the_first_tick_primes_silently(db) -> None:
    broker = IngestEventBroker(sessions=db, poll_seconds=0.05)
    now = utcnow()
    async with db() as s:
        # A PRE-EXISTING anchored product (alerts is valid-until-superseded, so its bare poll
        # artifact anchors) — the catalogue the priming tick must NOT replay. The bare USGS
        # artifact anchors nothing (a value product with no value rows), which is itself worth
        # holding: bytes alone are not ingest.
        s.add(_artifact(PRODUCT_NWS_ALERTS, now - timedelta(minutes=10), 1))
        s.add(_artifact(PRODUCT_USGS_IV, now - timedelta(minutes=10), 2))
        await s.commit()
    q = broker.subscribe()
    try:
        # priming tick: the pre-existing catalogue is NOT replayed as change
        await asyncio.sleep(0.2)
        assert q.empty(), "connecting must not shower the client with the whole catalogue"
        # a genuinely new poll lands: the anchor advances, one event says so
        async with db() as s:
            s.add(_artifact(PRODUCT_NWS_ALERTS, now, 3))
            s.add(OfficialAlertRecord(id="urn:e.1", event="Flood Warning", status="Actual",
                                      message_type="Alert", sent=now, ugc=["WAC057"],
                                      basin_ids=["basin:skagit"], mapping_method_id="m",
                                      references=[], retrieved_at=now, available_at=now))
            await s.commit()
        payload = json.loads(await asyncio.wait_for(q.get(), timeout=2.0))
        assert payload["kind"] == PRODUCT_NWS_ALERTS
        assert payload["available_at"]  # an instant, for logging; clients refetch regardless
        # ...and only that one: the untouched catalogue stays silent
        await asyncio.sleep(0.15)
        assert q.empty()
    finally:
        broker.unsubscribe(q)


async def test_the_poller_lives_exactly_as_long_as_its_audience(db) -> None:
    broker = IngestEventBroker(sessions=db, poll_seconds=0.05)
    q = broker.subscribe()
    assert broker._poller is not None and not broker._poller.done()
    broker.unsubscribe(q)
    await asyncio.wait_for(broker._poller, timeout=2.0)
    assert broker._poller.done(), "zero subscribers -> zero queries (the compute-hours rule)"
    # a later subscriber revives it
    q2 = broker.subscribe()
    assert not broker._poller.done()
    broker.unsubscribe(q2)
    await asyncio.wait_for(broker._poller, timeout=2.0)


async def test_the_stream_speaks_sse_with_a_retry_hint_and_heartbeats(db, monkeypatch) -> None:
    import cascade_api.events as events_mod

    monkeypatch.setattr(events_mod, "HEARTBEAT_SECONDS", 0.05)
    broker = IngestEventBroker(sessions=db, poll_seconds=0.05)
    stream = sse_stream(broker)
    first = await asyncio.wait_for(anext(stream), timeout=2.0)
    assert first == "retry: 5000\n\n"
    beat = await asyncio.wait_for(anext(stream), timeout=2.0)
    assert beat.startswith(": keep-alive"), "comments keep proxies from closing a quiet stream"
    await stream.aclose()
    await asyncio.sleep(0.1)
    assert not broker._subscribers, "a departed client is forgotten"


async def test_a_replay_never_reaches_this_endpoint_by_design() -> None:
    """The route takes no as_of. Pinned as an API-shape assertion: adding a knowledge-time
    parameter to a live-push channel would claim the past can change."""
    import inspect

    from cascade_api.routes import system_events

    assert "as_of" not in inspect.signature(system_events).parameters
