"""Read-only query instrumentation: what SQL a request issues, and who asked for it.

Nothing here is imported by `cascade_api`, `cascade_core` or `cascade_hydrology` — it attaches
from the outside, at test/measurement time only, and detaches again. No production module knows
it exists, so it cannot change what any endpoint returns.

Two independent halves, because the two facts live in different places:

- **What SQL ran** — a SQLAlchemy ``before_cursor_execute`` / ``after_cursor_execute`` pair on
  the engine. This is the ground truth for the query COUNT, the statement text as the dialect
  renders it, the bound parameters, and the per-statement wall time. It is all the query-budget
  test needs, and it needs no patching of anything.

- **Who issued it** — the engine event fires inside SQLAlchemy's greenlet, whose Python stack
  starts at ``greenlet_spawn`` and therefore cannot see ``assemble.assess_point``. The async
  caller's stack is only visible from the async frame itself, so :func:`attributed` wraps the
  `Knowledge` reader methods (the project's ONLY knowledge-time read path, ADR-0010) and records
  the caller there, publishing it through a ``ContextVar`` that SQLAlchemy's greenlet inherits.
  A statement issued with no `Knowledge` frame in flight is reported as such rather than guessed
  at — that is a finding, not a gap.

The wrapper is pure observation: it awaits the original bound method and returns its result
unchanged. A `Knowledge` call that hits the session identity map (``session.get``) issues no
statement, and that shows up correctly as a call site with zero queries attached.
"""

from __future__ import annotations

import contextlib
import functools
import inspect
import time
import traceback
from collections import Counter
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine

from cascade_core.knowledge import Knowledge

REPO_ROOT = Path(__file__).resolve().parents[2]

#: The `Knowledge` reader in flight, as (method name, caller "file.py:line in func"). Set by the
#: :func:`attributed` wrappers, read by the cursor-execute listener. A ContextVar rather than a
#: module global because SQLAlchemy's greenlet inherits the caller's context, which is the only
#: reason the async call site is reachable from inside the sync event at all.
_IN_FLIGHT: ContextVar[tuple[str, str, tuple[str, ...]] | None] = ContextVar("cascade_perf_in_flight", default=None)

#: Every public reader on `Knowledge`. Listed explicitly, not discovered, so that a reader added
#: later shows up as a KeyError in the wrap step instead of silently going unattributed.
#:
#: The set-based readers are wrapped too, and they are the ones worth watching: after the
#: amplification was removed almost every statement `/viz/basins` issues comes from one of them,
#: and a statement attributed to a *singular* reader on that path now means a scope the prefetch
#: did not cover — an N+1 growing back, visible by name rather than only in the total.
KNOWLEDGE_READERS: tuple[str, ...] = (
    "products",
    "basins",
    "basin",
    "forecast_points",
    "forecast_point_by_lid",
    "forecast_points_by_lid",
    "station",
    "stations",
    "stations_by_id",
    "observations",
    "observations_for",
    "latest_observation",
    "latest_observations",
    "latest_forecast_run",
    "latest_forecast_runs",
    "forecast_runs",
    "forecast_values",
    "forecast_values_for",
    "derived_features",
    "derived_features_for",
    "latest_derived_feature",
    "latest_derived_features",
    "thresholds",
    "thresholds_for",
    "latest_job_runs",
    "product_freshness_anchors",
)

#: Frames that are plumbing, not a call site: the wrapper itself, and the async machinery.
_UNINTERESTING = ("tests/perf/instrument.py", "/asyncio/", "/contextlib.py", "site-packages/")


def _caller_frames(limit: int = 12) -> tuple[str, ...]:
    """The project frames beneath the current one, innermost first, as ``path:line in func``."""
    out: list[str] = []
    for frame in reversed(traceback.extract_stack()[:-2]):
        name = frame.filename
        if any(part in name for part in _UNINTERESTING):
            continue
        try:
            rel = str(Path(name).resolve().relative_to(REPO_ROOT))
        except ValueError:
            continue
        out.append(f"{rel}:{frame.lineno} in {frame.name}")
        if len(out) >= limit:
            break
    return tuple(out)


@dataclass(frozen=True)
class RecordedQuery:
    """One statement as the driver actually saw it, with the reader that asked for it."""

    statement: str
    parameters: str
    #: The `Knowledge` method in flight, or ``"(outside Knowledge)"``.
    reader: str
    #: The innermost project frame that called that reader, e.g. ``assemble.py:162 in assess_point``.
    call_site: str
    #: The project frames beneath it, innermost first — the whole chain, for the inventory.
    stack: tuple[str, ...]
    duration_ms: float

    @property
    def identity(self) -> tuple[str, str]:
        """What makes two queries an EXACT repeat: same statement text, same bound values."""
        return (self.statement, self.parameters)


@dataclass
class QueryRecorder:
    """Attach to an engine, collect every statement it executes, detach again."""

    records: list[RecordedQuery] = field(default_factory=list)
    _engine: Any = None
    _sync_engine: Any = None
    _started: float = 0.0

    # -- lifecycle -------------------------------------------------------------------------
    def attach(self, engine: AsyncEngine) -> QueryRecorder:
        self._engine = engine
        self._sync_engine = engine.sync_engine if isinstance(engine, AsyncEngine) else engine
        event.listen(self._sync_engine, "before_cursor_execute", self._before)
        event.listen(self._sync_engine, "after_cursor_execute", self._after)
        return self

    def detach(self) -> None:
        if self._sync_engine is None:
            return
        event.remove(self._sync_engine, "before_cursor_execute", self._before)
        event.remove(self._sync_engine, "after_cursor_execute", self._after)
        self._sync_engine = None

    def clear(self) -> None:
        self.records.clear()

    # -- listeners -------------------------------------------------------------------------
    def _before(self, conn, cursor, statement, parameters, context, executemany) -> None:  # noqa: ANN001, PLR0913
        self._started = time.perf_counter()

    def _after(self, conn, cursor, statement, parameters, context, executemany) -> None:  # noqa: ANN001, PLR0913
        elapsed = (time.perf_counter() - self._started) * 1000.0
        flight = _IN_FLIGHT.get()
        reader, call_site, stack = flight if flight is not None else ("(outside Knowledge)", "(unattributed)", ())
        self.records.append(
            RecordedQuery(
                statement=" ".join(statement.split()),
                parameters=repr(parameters),
                reader=reader,
                call_site=call_site,
                stack=stack,
                duration_ms=elapsed,
            )
        )

    # -- reporting -------------------------------------------------------------------------
    @property
    def total(self) -> int:
        return len(self.records)

    @property
    def distinct(self) -> int:
        return len({r.identity for r in self.records})

    @property
    def exact_repeats(self) -> int:
        """Statements issued when an identical one (text AND params) already ran this request."""
        return self.total - self.distinct

    def by_identity(self) -> list[tuple[RecordedQuery, int, tuple[str, ...]]]:
        """One representative per distinct (statement, params), with its occurrence count and
        EVERY call site that issued it, ordered most-repeated first then by first appearance.

        All the call sites, not just the first: a duplicate issued twice from the same line is a
        loop, and a duplicate issued from two different lines is two modules asking the same
        question — different defects with different fixes, and the count alone cannot tell them
        apart.
        """
        counts: Counter[tuple[str, str]] = Counter(r.identity for r in self.records)
        first: dict[tuple[str, str], RecordedQuery] = {}
        order: dict[tuple[str, str], int] = {}
        sites: dict[tuple[str, str], list[str]] = {}
        for i, r in enumerate(self.records):
            first.setdefault(r.identity, r)
            order.setdefault(r.identity, i)
            sites.setdefault(r.identity, []).append(f"{r.reader} <- {r.call_site}")
        return sorted(
            ((first[k], counts[k], tuple(dict.fromkeys(sites[k]))) for k in first),
            key=lambda kv: (-kv[1], order[kv[0].identity]),
        )

    def by_call_site(self) -> Counter[str]:
        return Counter(f"{r.reader} <- {r.call_site}" for r in self.records)

    def by_table(self) -> Counter[str]:
        return Counter(table_of(r.statement) for r in self.records)

    def total_ms(self) -> float:
        return sum(r.duration_ms for r in self.records)


def table_of(statement: str) -> str:
    """The table a SELECT reads, taken from its FROM clause. Reporting only."""
    lowered = statement.lower()
    marker = " from "
    if marker not in lowered:
        return "(no FROM)"
    rest = statement[lowered.index(marker) + len(marker) :].strip()
    return rest.split()[0].strip('"') if rest else "(unknown)"


@contextlib.contextmanager
def attributed():
    """Wrap `Knowledge`'s readers so every statement can name the method and caller that issued it.

    Restores the originals on exit. Read-only: each wrapper awaits the real coroutine and returns
    its result untouched, so a body captured under this context manager is the same body captured
    without it (tests/perf/test_query_budget.py asserts exactly that).
    """
    originals: dict[str, Any] = {}
    for name in KNOWLEDGE_READERS:
        fn = getattr(Knowledge, name)
        if not inspect.iscoroutinefunction(fn):  # pragma: no cover - guards the explicit list
            raise TypeError(f"Knowledge.{name} is not an async reader")
        originals[name] = fn
        setattr(Knowledge, name, _wrap(name, fn))
    try:
        yield
    finally:
        for name, fn in originals.items():
            setattr(Knowledge, name, fn)


def _wrap(name: str, fn):  # noqa: ANN001, ANN202
    @functools.wraps(fn)
    async def wrapper(self, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003, ANN202
        # The OUTERMOST reader wins, not the innermost. Several singular readers delegate to
        # their own set-based form for one scope (`thresholds` -> `thresholds_for([fp_id])`), so
        # innermost-wins attributed a per-point N+1 to a *batched* reader and
        # `test_no_statement_comes_from_a_per_scope_reader` reported nothing. Measured
        # 2026-08-26 by removing the `thresholds_for` prefetch: the budget test failed, the
        # shape test passed. The statement belongs to the question the caller asked.
        if _IN_FLIGHT.get() is not None:
            return await fn(self, *args, **kwargs)
        frames = _caller_frames()
        token = _IN_FLIGHT.set((name, frames[0] if frames else "(no project frame)", frames))
        try:
            return await fn(self, *args, **kwargs)
        finally:
            _IN_FLIGHT.reset(token)

    return wrapper
