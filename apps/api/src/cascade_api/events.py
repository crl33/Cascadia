"""`/system/events`: notify-then-fetch over SSE — names of what changed, never payloads.

The stream carries `{kind, available_at}` events, where `kind` is a product id from the
registry; a client invalidates the queries that product feeds and refetches through the normal
read path (CINEMATIC_ROADMAP C3a: "no payloads over the stream"). Payloads over a push channel
would be a second read path with its own staleness and no `as_of` — the one the doctrine
already forbids twice.

**Change detection is a poll of our own database, deliberately.** The honest signal for "new
knowledge exists" is the same one /system/health trusts: `product_freshness_anchors()`, which
sees every writer — the scheduler's jobs, a queue bootstrap, a manual backfill — without any of
them having to cooperate. A LISTEN/NOTIFY design would be pushier but only hears writers that
notify, and the API reads through the POOLED Neon URL where LISTEN does not survive
transaction pooling anyway.

**The poller runs only while someone is connected.** Zero subscribers cost zero queries — the
Neon compute-hours arithmetic (deployment memory) is the reason this is a rule and not a nice-
to-have. `POLL_SECONDS` bounds the notification lag; the fastest product cadence is the 5-min
alert poll, so 20 s is prompt without being busy.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy.ext.asyncio import async_sessionmaker

from cascade_core.knowledge import as_known_at
from cascade_core.timeutils import utcnow

log = logging.getLogger("cascade.api.events")

POLL_SECONDS = 20.0
#: SSE comment heartbeat, so proxies and the 100-s Cloudflare idle window keep the stream open.
HEARTBEAT_SECONDS = 15.0
#: A slow client whose queue backs up this far is dropped rather than backpressuring the poller.
MAX_QUEUED_EVENTS = 64


@dataclass
class IngestEventBroker:
    """One poller, many subscribers; alive only while subscribed to."""

    sessions: async_sessionmaker
    poll_seconds: float = POLL_SECONDS
    _subscribers: set[asyncio.Queue] = field(default_factory=set)
    _poller: asyncio.Task | None = None
    _last: dict[str, datetime] = field(default_factory=dict)
    _primed: bool = False

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=MAX_QUEUED_EVENTS)
        self._subscribers.add(q)
        if self._poller is None or self._poller.done():
            self._poller = asyncio.create_task(self._poll_loop())
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self._subscribers.discard(q)
        # The loop notices the empty set on its next tick and exits; nothing to cancel here.

    async def _poll_loop(self) -> None:
        log.info("ingest poller up (%d subscriber(s))", len(self._subscribers))
        try:
            while self._subscribers:
                try:
                    changed = await self._advance()
                except Exception:  # a transient DB error must not kill the stream
                    log.exception("ingest poll failed; stream stays up")
                    changed = []
                for kind, available_at in changed:
                    self._broadcast(kind, available_at)
                await asyncio.sleep(self.poll_seconds)
        finally:
            self._primed = False
            self._last.clear()
            log.info("ingest poller down")

    async def _advance(self) -> list[tuple[str, datetime]]:
        """Anchors now vs anchors last tick. The FIRST tick primes and emits nothing: a client
        that just connected refetches anyway, and replaying the whole catalogue as 'changes'
        would say something false — nothing changed while it was connected."""
        async with self.sessions() as session:
            anchors = await as_known_at(session, utcnow()).product_freshness_anchors()
        current: dict[str, datetime] = {}
        for pid, anchor in anchors.items():
            # The CONTENT instant, preferentially: for valid-until-superseded products both
            # valid_time and retrieved_at advance on EVERY successful poll (that is their
            # freshness job), and keying change detection there made quiet weather emit a
            # cache-defeating invalidation every five minutes. `content_time` is the pure
            # value-side instant the anchor carries for exactly this consumer; a product with
            # no value rows yet falls back to the poll clock — the only instant it has.
            instant = anchor.content_time or anchor.valid_time or anchor.retrieved_at
            if instant is not None:
                current[pid] = instant
        if not self._primed:
            self._last, self._primed = current, True
            return []
        changed = [(pid, t) for pid, t in current.items() if self._last.get(pid) != t]
        self._last = current
        return changed

    def _broadcast(self, kind: str, available_at: datetime) -> None:
        payload = json.dumps({"kind": kind, "available_at": available_at.isoformat()})
        for q in list(self._subscribers):
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                # A reader this far behind is not reading. Discarding the queue alone left a
                # ZOMBIE stream — heartbeats forever, events never (adversarial review
                # 2026-08-28) — so the stream is told to END: the None sentinel replaces the
                # oldest queued event, sse_stream terminates on it, and EventSource reconnects
                # with a fresh subscription.
                self._subscribers.discard(q)
                try:
                    q.get_nowait()
                    q.put_nowait(None)
                except (asyncio.QueueEmpty, asyncio.QueueFull):
                    pass
                log.warning("dropped a slow /system/events subscriber; its stream will close")


async def sse_stream(broker: IngestEventBroker) -> AsyncIterator[str]:
    """One client's stream: retry hint, then events interleaved with comment heartbeats."""
    q = broker.subscribe()
    try:
        yield "retry: 5000\n\n"
        while True:
            try:
                payload = await asyncio.wait_for(q.get(), timeout=HEARTBEAT_SECONDS)
                if payload is None:  # dropped by the broker: end, so the client reconnects
                    return
                yield f"event: ingest\ndata: {payload}\n\n"
            except TimeoutError:
                yield ": keep-alive\n\n"
    finally:
        broker.unsubscribe(q)
