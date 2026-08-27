"""`as_known_at(session, T)` — the only knowledge-time read path (ADR-0010, DATA_DOCTRINE §11).

Every read returns only rows with `available_at <= T` (thresholds: `effective_from <= T`) and,
for observations, the highest revision that existed at T. API projections and hydrology assembly
go through this object; direct table access in a replay path is a review failure.

**Most readers come in two forms**, and the second is why `/viz/basins` stopped issuing 120
statements to ask twelve questions: `thresholds(fp_id)` beside `thresholds_for(fp_ids)`,
`station(id)` beside `stations_by_id(ids)`, `latest_derived_feature(...)` beside
`latest_derived_features(...)`. They answer identically — the plural form is the singular
form's predicates with `IN (…)` where it had `=` — and both write into the same request-scoped
memo, so a caller that reads one scope at a time after a set-based read reaches no database at
all. `tests/unit/test_knowledge_batching.py` holds each pair to that.

The knowledge filter is never what batching touches. It is on the ROW (`available_at <= as_of`),
never on the scope, so widening a scope list cannot change which rows are visible at T; and the
revision rule stays a per-valid_time rule, so it cannot change either.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from cascade_core.models import (
    Basin,
    DerivedFeature,
    ForecastPoint,
    ForecastRun,
    ForecastValue,
    JobRun,
    Observation,
    RawArtifact,
    SourceProduct,
    Station,
    Threshold,
)
from cascade_core.registry import (
    METADATA_ONLY_PRODUCTS,
    PRODUCTS,
    SOURCES,
    VALID_UNTIL_SUPERSEDED_PRODUCTS,
)
from cascade_core.timeutils import to_utc

# Which products are an OFFICIAL forecast, resolved from the registry rather than listed here
# (cascade_core.registry is the only place a source's SourceKind is declared). P3 puts a second
# forecast product — the NWM medium-range ensemble — into `forecast_run`, so "the latest run at
# this point" stopped being a synonym for "the official forecast at this point"
# (docs/research/p3-surfaces-design-2026-08-24.md §3.4 defect 1).
_SOURCE_KIND: dict[str, str] = {str(s["id"]): str(s["kind"]) for s in SOURCES}
OFFICIAL_FORECAST_PRODUCTS: frozenset[str] = frozenset(
    str(p["id"]) for p in PRODUCTS if _SOURCE_KIND.get(str(p["source_id"])) == "OFFICIAL_FORECAST"
)

#: How far back `latest_observation` looks before answering "nothing known". Named rather than
#: spelled inline so a batched prefetch and the singular read cannot drift onto two windows and
#: quietly stop being the same question.
DEFAULT_OBSERVATION_LOOKBACK = timedelta(days=14)

#: The default `latest_derived_feature` window, for the same reason.
DEFAULT_DERIVED_FEATURE_LOOKBACK = timedelta(days=30)


def _within(value: datetime, lo: datetime | None, hi: datetime | None) -> bool:
    return (lo is None or value >= lo) and (hi is None or value <= hi)


def _covers(wide: tuple[datetime | None, datetime | None], narrow: tuple[datetime | None, datetime | None]) -> bool:
    """Does the closed valid_time range ``wide`` contain ``narrow``? (``None`` = unbounded.)"""
    w_lo, w_hi = wide
    n_lo, n_hi = narrow
    if w_lo is not None and (n_lo is None or n_lo < w_lo):
        return False
    return not (w_hi is not None and (n_hi is None or n_hi > w_hi))


@dataclass(frozen=True)
class FreshnessAnchor:
    """The timestamps `/system/health` computes a product's freshness from, plus which table they
    came from. `kind` is part of the answer, not decoration: "current because values landed" and
    "current because bytes were fetched" are different claims about the same product."""

    kind: str
    valid_time: datetime | None
    retrieved_at: datetime | None


@dataclass(frozen=True)
class Knowledge:
    """One knowledge time, one request, one memo.

    ### Why memoising in here is not a cache

    A `Knowledge` is constructed per request (`as_known_at`) and every read it performs is
    already filtered to a single knowledge time `as_of`. Inside one instance a reader is
    therefore a **pure function of its arguments**: the same question at the same T has exactly
    one answer, and asking the database a second time can only get the same rows back. `_memo`
    stores those answers so the second ask costs nothing, and the `*_for` / plural readers seed
    it so the first ask costs ONE statement for every scope instead of one statement per scope.

    That is the whole reason this is legitimate. A cache that outlived the request would be
    process-local state holding knowledge-filtered rows with no invalidation, which the project
    rule forbids; nothing here outlives the `Knowledge` object, and the object does not outlive
    the request. `as_of` is not part of any memo key because it cannot vary within an instance.

    Three rules every reader below keeps:

    - the memo holds **what a statement returned**, never a caller's post-processing of it, so
      one memo entry can answer several differently-shaped questions about the same rows;
    - every reader hands back a **fresh list/dict**, so a caller mutating what it got cannot
      corrupt the answer the next caller gets (the ORM rows themselves are shared, as they
      already are through SQLAlchemy's identity map);
    - a batched reader issues **exactly the predicates its singular counterpart would**, only
      with `IN (…)` where the singular has `=`. Knowledge-time filtering (`available_at <=
      as_of`, `effective_from <= as_of`) and revision ordering are never touched by batching.
    """

    session: AsyncSession
    as_of: datetime
    #: Request-scoped answers, keyed by (reader name, *arguments). Excluded from equality and
    #: repr because it is an accelerator, never part of what a `Knowledge` IS — and `init=False`
    #: so that it cannot be handed in and `dataclasses.replace(k, as_of=…)` starts a NEW one.
    #: A memo that followed an object to a different knowledge time would answer the new clock's
    #: questions with the old clock's rows, which is the one way this could break replay.
    _memo: dict[Any, Any] = field(default_factory=dict, compare=False, repr=False, init=False)

    # ------------------------------------------------------------------ reference data

    async def products(self) -> dict[str, SourceProduct]:
        if ("products",) not in self._memo:
            rows = (await self.session.execute(select(SourceProduct))).scalars().all()
            self._memo[("products",)] = {p.id: p for p in rows}
        return dict(self._memo[("products",)])

    async def basins(self) -> list[Basin]:
        if ("basins",) not in self._memo:
            rows = list((await self.session.execute(select(Basin).order_by(Basin.id))).scalars().all())
            self._memo[("basins",)] = rows
            for row in rows:
                self._memo.setdefault(("basin", row.id), row)
        return list(self._memo[("basins",)])

    async def basin(self, basin_id: str) -> Basin | None:
        key = ("basin", basin_id)
        if key not in self._memo:
            self._memo[key] = await self.session.get(Basin, basin_id)
        return self._memo[key]

    async def forecast_points(self, basin_id: str | None = None) -> list[ForecastPoint]:
        key = ("forecast_points", basin_id)
        if key not in self._memo:
            q = select(ForecastPoint).order_by(ForecastPoint.id)
            if basin_id is not None:
                q = q.where(ForecastPoint.basin_id == basin_id)
            rows = list((await self.session.execute(q)).scalars().all())
            self._memo[key] = rows
            for row in rows:
                self._memo.setdefault(("forecast_point_by_lid", row.lid), row)
        return list(self._memo[key])

    async def forecast_point_by_lid(self, lid: str) -> ForecastPoint | None:
        key = ("forecast_point_by_lid", lid)
        if key not in self._memo:
            await self.forecast_points_by_lid([lid])
        # `.get`, not `[…]`: the set-based readers drop an empty scope id before building their
        # `IN (…)`, so a caller passing one leaves no memo entry behind. That has to answer the
        # way the single-scope statement answered — "nothing known" — not raise. Every reader
        # below that delegates does the same, and `test_an_empty_scope_id_answers_as_it_did`
        # holds all four of them to it.
        return self._memo.get(key)

    async def forecast_points_by_lid(self, lids: Iterable[str]) -> dict[str, ForecastPoint]:
        """Every point in ``lids``, in ONE statement. `lid` is unique, so this is the set-based
        form of `forecast_point_by_lid` and nothing else about it differs."""
        wanted = sorted({lid for lid in lids if lid})
        missing = [lid for lid in wanted if ("forecast_point_by_lid", lid) not in self._memo]
        if missing:
            rows = (await self.session.execute(select(ForecastPoint).where(ForecastPoint.lid.in_(missing)))).scalars().all()
            found = {row.lid: row for row in rows}
            for lid in missing:
                self._memo[("forecast_point_by_lid", lid)] = found.get(lid)
        return {lid: row for lid in wanted if (row := self._memo[("forecast_point_by_lid", lid)]) is not None}

    async def station(self, station_id: str) -> Station | None:
        key = ("station", station_id)
        if key not in self._memo:
            self._memo[key] = await self.session.get(Station, station_id)
        return self._memo[key]

    async def stations_by_id(self, station_ids: Iterable[str]) -> dict[str, Station]:
        """Every station in ``station_ids``, in ONE statement, memoised as `station` reads them.

        `station` is `session.get`, which is free on a second call *only while something still
        holds the loaded object* — SQLAlchemy's identity map holds weak references, and the two
        call sites on the `/viz/basins` path each read one attribute and drop the row, so the
        second lookup re-queried. Prefetching here and memoising there removes both problems.
        """
        wanted = sorted({s for s in station_ids if s})
        missing = [s for s in wanted if ("station", s) not in self._memo]
        if missing:
            rows = (await self.session.execute(select(Station).where(Station.id.in_(missing)))).scalars().all()
            found = {row.id: row for row in rows}
            for s in missing:
                self._memo[("station", s)] = found.get(s)
        return {s: row for s in wanted if (row := self._memo[("station", s)]) is not None}

    async def stations(self) -> list[Station]:
        return list((await self.session.execute(select(Station).order_by(Station.id))).scalars().all())

    # ------------------------------------------------------------------ observations

    @staticmethod
    def _best_per_valid_time(rows: Iterable[Observation]) -> list[Observation]:
        """One row per valid_time — the highest revision known at T — ascending by valid_time.

        The rows must arrive ordered by (valid_time, revision_seq, id): the later write for a
        valid_time wins, which is the revision rule, and `id` only breaks a tie between two rows
        claiming the same revision of the same instant (possible across products, never within
        one). Applied identically to a singular read and to a slice of a batched one, which is
        what makes those two provably the same answer.
        """
        best: dict[datetime, Observation] = {}
        for row in rows:
            best[row.valid_time] = row
        return [best[k] for k in sorted(best)]

    async def observations(self, station_id: str, variable: str, since: datetime, until: datetime | None = None) -> list[Observation]:
        """Known-at-T observations in [since, until], one row per valid_time (highest known revision)."""
        lo = to_utc(since)
        hi = self.as_of if until is None else min(to_utc(until), self.as_of)
        rows = await self._observation_rows(station_id, variable, lo, hi)
        return self._best_per_valid_time(rows)

    async def _observation_rows(self, station_id: str, variable: str, lo: datetime, hi: datetime) -> list[Observation]:
        """The raw ordered rows behind `observations`, memoised, and sliced out of any WIDER
        window already read for the same station and variable.

        Narrowing is exact, not an approximation: the statement's other predicates
        (`station_id`, `variable`, `available_at <= as_of`) do not mention valid_time, so the
        rows of [a, b] are precisely the rows of a containing [A, B] whose valid_time lies in
        [a, b], in the same order. That is what collapses `assess_point`'s six-hour trend read
        into the fourteen-day read it already sits inside.
        """
        key = ("observations", station_id, variable, lo, hi)
        if key in self._memo:
            return list(self._memo[key])
        for w_lo, w_hi in self._memo.get(("observation_windows", station_id, variable), ()):
            if _covers((w_lo, w_hi), (lo, hi)):
                wide = self._memo[("observations", station_id, variable, w_lo, w_hi)]
                return [r for r in wide if _within(r.valid_time, lo, hi)]
        q = (
            select(Observation)
            .where(Observation.station_id == station_id, Observation.variable == variable)
            .where(Observation.available_at <= self.as_of)
            .where(Observation.valid_time >= lo, Observation.valid_time <= hi)
            .order_by(Observation.valid_time, Observation.revision_seq, Observation.id)
        )
        rows = list((await self.session.execute(q)).scalars().all())
        self._remember_observations(station_id, variable, lo, hi, rows)
        return list(rows)

    def _remember_observations(self, station_id: str, variable: str, lo: datetime, hi: datetime, rows: list[Observation]) -> None:
        self._memo[("observations", station_id, variable, lo, hi)] = rows
        self._memo.setdefault(("observation_windows", station_id, variable), []).append((lo, hi))

    async def observations_for(self, specs: Sequence[tuple[str, str, datetime, datetime | None]]) -> dict[tuple[str, str, datetime, datetime], list[Observation]]:
        """Several (station, variable, since, until) reads in ONE statement.

        The windows do not have to agree — `assess_point` wants a six-hour trend window on one
        variable and a single instant on the other — so the statement is an OR of each spec's
        own predicate under the shared knowledge filter, and each spec is then satisfied from
        the union by its own predicate. A spec already answerable from the memo (identically or
        by narrowing) is dropped before the statement is built, so a request whose observations
        are recent enough to fall inside a window already read issues nothing at all here.
        """
        resolved = [(s, v, to_utc(lo), self.as_of if hi is None else min(to_utc(hi), self.as_of)) for s, v, lo, hi in specs if s and v]
        wanted = sorted({spec for spec in resolved})
        missing = [spec for spec in wanted if not self._observations_answerable(*spec)]
        if missing:
            q = (
                select(Observation)
                .where(Observation.available_at <= self.as_of)
                # Redundant by construction — it is implied by the OR below, so it cannot change
                # which rows come back — and stated anyway because on PostgreSQL `observation` is
                # RANGE-partitioned by valid_time monthly (ADR-0013). A bound the planner can see
                # at the top level prunes partitions; the same bound reachable only through an OR
                # of per-spec branches is a bound the planner may or may not push down, and this
                # is the one statement on the path where that is the difference between touching
                # two partitions and touching all of them.
                .where(
                    Observation.valid_time >= min(lo for _, _, lo, _ in missing),
                    Observation.valid_time <= max(hi for _, _, _, hi in missing),
                )
                .where(
                    or_(
                        *[
                            and_(
                                Observation.station_id == s,
                                Observation.variable == v,
                                Observation.valid_time >= lo,
                                Observation.valid_time <= hi,
                            )
                            for s, v, lo, hi in missing
                        ]
                    )
                )
                .order_by(Observation.valid_time, Observation.revision_seq, Observation.id)
            )
            union = list((await self.session.execute(q)).scalars().all())
            for s, v, lo, hi in missing:
                rows = [r for r in union if r.station_id == s and r.variable == v and _within(r.valid_time, lo, hi)]
                self._remember_observations(s, v, lo, hi, rows)
        return {spec: self._best_per_valid_time(await self._observation_rows(*spec)) for spec in wanted}

    def _observations_answerable(self, station_id: str, variable: str, lo: datetime, hi: datetime) -> bool:
        if ("observations", station_id, variable, lo, hi) in self._memo:
            return True
        return any(_covers(w, (lo, hi)) for w in self._memo.get(("observation_windows", station_id, variable), ()))

    async def latest_observation(self, station_id: str, variable: str, lookback: timedelta = DEFAULT_OBSERVATION_LOOKBACK) -> Observation | None:
        key = ("latest_observation", station_id, variable, lookback)
        if key not in self._memo:
            rows = await self.observations(station_id, variable, since=self.as_of - lookback)
            self._memo[key] = rows[-1] if rows else None
        return self._memo[key]

    async def latest_observations(
        self,
        station_ids: Iterable[str],
        variables: Iterable[str],
        *,
        lookback: timedelta = DEFAULT_OBSERVATION_LOOKBACK,
    ) -> dict[tuple[str, str], Observation]:
        """The latest known-at-T observation per (station, variable), in ONE statement.

        Same answer as `latest_observation`, reached without shipping the whole lookback window:
        that reader takes the last row of [T − lookback, T] ordered by (valid_time, revision_seq,
        id), and `row_number()` over the same partition and the same ordering reversed selects
        exactly that row. Fourteen days of instantaneous values for a handful of stations is
        tens of thousands of rows to move in order to read the tail of each one; this moves one
        row per (station, variable).
        """
        stations = sorted({s for s in station_ids if s})
        names = sorted({v for v in variables if v})
        missing = [(s, v) for s in stations for v in names if ("latest_observation", s, v, lookback) not in self._memo]
        if missing:
            ranked = (
                select(
                    Observation,
                    func.row_number()
                    .over(
                        partition_by=(Observation.station_id, Observation.variable),
                        order_by=(Observation.valid_time.desc(), Observation.revision_seq.desc(), Observation.id.desc()),
                    )
                    .label("rank"),
                )
                .where(Observation.station_id.in_(sorted({s for s, _ in missing})))
                .where(Observation.variable.in_(sorted({v for _, v in missing})))
                .where(Observation.available_at <= self.as_of)
                .where(Observation.valid_time >= self.as_of - lookback, Observation.valid_time <= self.as_of)
                .subquery()
            )
            latest = aliased(Observation, ranked)
            rows = (await self.session.execute(select(latest).where(ranked.c.rank == 1))).scalars().all()
            found = {(row.station_id, row.variable): row for row in rows}
            for pair in missing:
                self._memo[("latest_observation", *pair, lookback)] = found.get(pair)
        return {
            (s, v): row
            for s in stations
            for v in names
            if (row := self._memo[("latest_observation", s, v, lookback)]) is not None
        }

    async def latest_forecast_run(
        self, fp_id: str, *, product_ids: frozenset[str] | None = OFFICIAL_FORECAST_PRODUCTS
    ) -> ForecastRun | None:
        """The latest run known at T at this point, restricted to ``product_ids``.

        ``forecast_run`` holds more than one forecast product: from P3 the NWM medium-range
        ensemble lands in the same table as the NWRFC official forecast. Ordering by issued_at
        across every product would hand back whichever run happens to be newest, so on any cycle
        where the model beat the RFC the caller displaying "the official forecast" would be
        showing a model run (design §3.4 defect 1 — the fix is the filter, not a convention).

        The default is therefore the registry-resolved OFFICIAL set, not "everything": a caller
        that says nothing gets the official forecast, which is what every existing caller means.
        Pass an explicit set to read another product, or ``product_ids=None`` to deliberately
        ask for the latest run of ANY product (the caller then owns badging it correctly)."""
        key = ("latest_forecast_run", fp_id, product_ids)
        if key not in self._memo:
            await self.latest_forecast_runs([fp_id], product_ids=product_ids)
        return self._memo.get(key)

    async def latest_forecast_runs(
        self, fp_ids: Iterable[str], *, product_ids: frozenset[str] | None = OFFICIAL_FORECAST_PRODUCTS
    ) -> dict[str, ForecastRun]:
        """The latest run known at T at each of ``fp_ids``, restricted to ``product_ids``, in ONE
        statement.

        `row_number()` partitioned by `fp_id` over the same `(issued_at DESC, id DESC)` ordering
        the singular reader takes its `LIMIT 1` from, under the same `available_at <= as_of` and
        the same product restriction. `id` is a primary key, so the ordering is total and "the
        first row of each partition" and "the one row `LIMIT 1` returns" are the same row.
        """
        wanted = sorted({f for f in fp_ids if f})
        missing = [f for f in wanted if ("latest_forecast_run", f, product_ids) not in self._memo]
        if missing:
            ranked = select(
                ForecastRun,
                func.row_number()
                .over(partition_by=ForecastRun.fp_id, order_by=(ForecastRun.issued_at.desc(), ForecastRun.id.desc()))
                .label("rank"),
            ).where(ForecastRun.fp_id.in_(missing), ForecastRun.available_at <= self.as_of)
            if product_ids is not None:
                ranked = ranked.where(ForecastRun.product_id.in_(sorted(product_ids)))
            sub = ranked.subquery()
            latest = aliased(ForecastRun, sub)
            rows = (await self.session.execute(select(latest).where(sub.c.rank == 1))).scalars().all()
            found = {row.fp_id: row for row in rows}
            for f in missing:
                self._memo[("latest_forecast_run", f, product_ids)] = found.get(f)
        return {f: row for f in wanted if (row := self._memo[("latest_forecast_run", f, product_ids)]) is not None}

    async def forecast_runs(
        self,
        fp_id: str,
        issued_from: datetime,
        issued_until: datetime,
        *,
        product_ids: frozenset[str] | None = None,
    ) -> list[ForecastRun]:
        """Known-at-T forecast runs with issued_at inside [issued_from, issued_until], ascending.

        The Event Zero forecast-evolution read: select by ISSUED time, knowledge-filter by
        available_at — a backfilled run (available_at ≫ issued_at) stays invisible at any T
        before its retrieval (ADR-0010).

        ``product_ids`` defaults to None = every product, because this is the *evolution* read:
        it returns runs of every kind side by side and each item carries its own product id and
        ProvenanceRef, so a model run shows up as a model run instead of being hidden. Pass a
        set when a caller needs one product's history only."""
        q = (
            select(ForecastRun)
            .where(ForecastRun.fp_id == fp_id, ForecastRun.available_at <= self.as_of)
            .where(ForecastRun.issued_at >= to_utc(issued_from), ForecastRun.issued_at <= to_utc(issued_until))
        )
        if product_ids is not None:
            q = q.where(ForecastRun.product_id.in_(sorted(product_ids)))
        q = q.order_by(ForecastRun.issued_at, ForecastRun.id)
        return list((await self.session.execute(q)).scalars().all())

    async def forecast_values(self, run_id: int) -> list[ForecastValue]:
        key = ("forecast_values", run_id)
        if key not in self._memo:
            await self.forecast_values_for([run_id])
        return list(self._memo.get(key, ()))

    async def forecast_values_for(self, run_ids: Iterable[int]) -> dict[int, list[ForecastValue]]:
        """The full hydrograph of each of ``run_ids``, in ONE statement.

        `(run_id, valid_time)` is unique, so ordering the union by `(run_id, valid_time)` and
        partitioning it in Python gives each run exactly the rows, in exactly the order, that
        `forecast_values` returns on its own.
        """
        wanted = sorted({r for r in run_ids if r is not None})
        missing = [r for r in wanted if ("forecast_values", r) not in self._memo]
        if missing:
            q = select(ForecastValue).where(ForecastValue.run_id.in_(missing)).order_by(ForecastValue.run_id, ForecastValue.valid_time)
            grouped: dict[int, list[ForecastValue]] = {r: [] for r in missing}
            for row in (await self.session.execute(q)).scalars():
                grouped[row.run_id].append(row)
            for r in missing:
                self._memo[("forecast_values", r)] = grouped[r]
        return {r: list(self._memo[("forecast_values", r)]) for r in wanted}

    async def derived_features(
        self,
        feature: str,
        scope_id: str,
        *,
        method_id: str | None = None,
        window: str | None = None,
        valid_from: datetime | None = None,
        valid_until: datetime | None = None,
        latest_per_valid_time: bool = False,
    ) -> list[DerivedFeature]:
        """Known-at-T derived features, ascending by (valid_time, available_at, id).

        Knowledge filtering is on ``available_at`` only. ``valid_time`` is deliberately NOT
        clamped to ``as_of``: a derived forecast feature (72-hour basin QPF) is legitimately
        valid in the future, and clamping it would silently hide the forecast half of the
        surface. Pass ``valid_until`` when a caller genuinely wants present-or-past rows.

        ``method_id`` and ``window`` filter only when given (``None`` means "do not filter",
        not "match NULL"). Recomputation is append-only — a new run under the same method is a
        new row — so ``latest_per_valid_time=True`` keeps the last-known row per valid_time,
        the same rule ``observations`` uses for revisions.
        """
        lo = None if valid_from is None else to_utc(valid_from)
        hi = None if valid_until is None else to_utc(valid_until)
        rows = await self._derived_feature_rows(feature, scope_id, method_id, window, lo, hi)
        return self._latest_per_valid_time(rows) if latest_per_valid_time else rows

    @staticmethod
    def _latest_per_valid_time(rows: Iterable[DerivedFeature]) -> list[DerivedFeature]:
        best: dict[datetime, DerivedFeature] = {}
        for row in rows:  # ordering means the last write for a valid_time wins
            best[row.valid_time] = row
        return [best[k] for k in sorted(best)]

    async def _derived_feature_rows(
        self,
        feature: str,
        scope_id: str,
        method_id: str | None,
        window: str | None,
        lo: datetime | None,
        hi: datetime | None,
    ) -> list[DerivedFeature]:
        """The raw ordered rows behind `derived_features`, memoised, and sliced out of any WIDER
        valid_time range already read for the same feature / scope / method / window.

        `latest_per_valid_time` is deliberately NOT part of the memo key: it is a pure function
        of these rows applied on the way out, so one read answers both shapes of the question.
        """
        shape = (feature, scope_id, method_id, window)
        key = ("derived_features", *shape, lo, hi)
        if key in self._memo:
            return list(self._memo[key])
        for w_lo, w_hi in self._memo.get(("derived_feature_ranges", *shape), ()):
            if _covers((w_lo, w_hi), (lo, hi)):
                wide = self._memo[("derived_features", *shape, w_lo, w_hi)]
                return [r for r in wide if _within(r.valid_time, lo, hi)]
        q = (
            select(DerivedFeature)
            .where(DerivedFeature.feature == feature, DerivedFeature.scope_id == scope_id)
            .where(DerivedFeature.available_at <= self.as_of)
            .order_by(DerivedFeature.valid_time, DerivedFeature.available_at, DerivedFeature.id)
        )
        if method_id is not None:
            q = q.where(DerivedFeature.method_id == method_id)
        if window is not None:
            q = q.where(DerivedFeature.window == window)
        if lo is not None:
            q = q.where(DerivedFeature.valid_time >= lo)
        if hi is not None:
            q = q.where(DerivedFeature.valid_time <= hi)
        rows = list((await self.session.execute(q)).scalars().all())
        self._remember_derived_features(shape, lo, hi, rows)
        return list(rows)

    def _remember_derived_features(
        self, shape: tuple[str, str, str | None, str | None], lo: datetime | None, hi: datetime | None, rows: list[DerivedFeature]
    ) -> None:
        self._memo[("derived_features", *shape, lo, hi)] = rows
        self._memo.setdefault(("derived_feature_ranges", *shape), []).append((lo, hi))

    async def derived_features_for(
        self,
        specs: Sequence[tuple[str, str | None, str | None]],
        scope_ids: Iterable[str],
        *,
        valid_from: datetime | None = None,
        valid_until: datetime | None = None,
    ) -> dict[tuple[str, str], list[DerivedFeature]]:
        """Several `(feature, method_id, window)` questions asked of several scopes, in ONE statement.

        The `derived_feature` table answered 47 of the 120 statements `/viz/basins` issued, and
        every one of them was the same handful of questions repeated per basin. This is that
        cross product: one `scope_id IN (…)`, one OR over the specs, and the shared valid_time
        bounds the family is read over — the predicates the singular reader would have applied
        one at a time, and nothing more. Each cell is then memoised under exactly the key
        `derived_features` looks for, so the surfaces go on calling their own readers and simply
        stop reaching the database.

        `window` rides on the spec rather than being one setting for the whole call because it
        is part of a feature's identity (it is in `uq_derived_feature_identity`), and a surface
        legitimately reads a windowed feature and an unwindowed one as a single family — the
        72-hour basin QPF and the snow level that qualifies it are one question about one cycle.

        Features must be distinct across ``specs``: the result is grouped by `(feature,
        scope_id)`, so two methods computing the same feature could not be told apart.
        """
        shapes: dict[str, tuple[str | None, str | None]] = {}
        for feature, method_id, window in specs:
            if feature in shapes and shapes[feature] != (method_id, window):
                raise ValueError(f"derived_features_for got two shapes for feature {feature!r}")
            shapes[feature] = (method_id, window)
        lo = None if valid_from is None else to_utc(valid_from)
        hi = None if valid_until is None else to_utc(valid_until)
        scopes = sorted({s for s in scope_ids if s})
        cells = [(f, s) for f in sorted(shapes) for s in scopes]
        missing = [(f, s) for f, s in cells if not self._derived_features_answerable((f, s, *shapes[f]), lo, hi)]
        if missing:
            features = sorted({f for f, _ in missing})
            q = (
                select(DerivedFeature)
                .where(DerivedFeature.scope_id.in_(sorted({s for _, s in missing})))
                .where(DerivedFeature.available_at <= self.as_of)
                .where(or_(*[self._feature_clause(f, *shapes[f]) for f in features]))
                .order_by(DerivedFeature.valid_time, DerivedFeature.available_at, DerivedFeature.id)
            )
            if lo is not None:
                q = q.where(DerivedFeature.valid_time >= lo)
            if hi is not None:
                q = q.where(DerivedFeature.valid_time <= hi)
            union = list((await self.session.execute(q)).scalars().all())
            for f, s in missing:
                self._remember_derived_features(
                    (f, s, *shapes[f]), lo, hi, [r for r in union if r.feature == f and r.scope_id == s]
                )
        return {(f, s): await self._derived_feature_rows(f, s, *shapes[f], lo, hi) for f, s in cells}

    @staticmethod
    def _feature_clause(feature: str, method_id: str | None, window: str | None):  # noqa: ANN205
        """One spec's predicate, with `None` meaning "do not filter" exactly as it does on the
        singular reader — never "match NULL"."""
        clauses = [DerivedFeature.feature == feature]
        if method_id is not None:
            clauses.append(DerivedFeature.method_id == method_id)
        if window is not None:
            clauses.append(DerivedFeature.window == window)
        return and_(*clauses)

    def _derived_features_answerable(
        self, shape: tuple[str, str, str | None, str | None], lo: datetime | None, hi: datetime | None
    ) -> bool:
        if ("derived_features", *shape, lo, hi) in self._memo:
            return True
        return any(_covers(r, (lo, hi)) for r in self._memo.get(("derived_feature_ranges", *shape), ()))

    async def latest_derived_features(
        self,
        specs: Sequence[tuple[str, str | None, str | None]],
        scope_ids: Iterable[str],
        *,
        lookback: timedelta = DEFAULT_DERIVED_FEATURE_LOOKBACK,
    ) -> dict[tuple[str, str], DerivedFeature]:
        """`latest_derived_feature` for several features and scopes, in ONE statement.

        Same bounds (`[T − lookback, T]`), same ordering, same last-row rule — so a scope whose
        answer arrives here is the answer the singular reader would have queried for, and after
        this the singular reader does not query at all.

        A caller reading one family over several lookbacks may pass the WIDEST of them and let
        each surface ask for its own: `[T − 48 h, T]` lies inside `[T − 7 d, T]`, so the narrower
        read is answered by narrowing the batch, which is the same rows the narrower statement
        would have returned. The staleness rule stays where it belongs — with the surface that
        owns it — and is applied to exactly the rows it asked for.
        """
        rows = await self.derived_features_for(specs, scope_ids, valid_from=self.as_of - lookback, valid_until=self.as_of)
        out: dict[tuple[str, str], DerivedFeature] = {}
        for cell, found in rows.items():
            latest = self._latest_per_valid_time(found)
            if latest:
                out[cell] = latest[-1]
        return out

    async def latest_derived_feature(
        self,
        feature: str,
        scope_id: str,
        *,
        method_id: str | None = None,
        window: str | None = None,
        lookback: timedelta = DEFAULT_DERIVED_FEATURE_LOOKBACK,
    ) -> DerivedFeature | None:
        """The most recent known-at-T row for a feature/scope with valid_time <= T.

        Bounded by ``lookback`` so a surface reading a stale table gets None (and says why)
        instead of quietly presenting a value from an arbitrary distance in the past.
        """
        rows = await self.derived_features(
            feature,
            scope_id,
            method_id=method_id,
            window=window,
            valid_from=self.as_of - lookback,
            valid_until=self.as_of,
            latest_per_valid_time=True,
        )
        return rows[-1] if rows else None

    async def thresholds(self, fp_id: str) -> dict[str, Threshold]:
        """Latest known-at-T official threshold row per category."""
        key = ("thresholds", fp_id)
        if key not in self._memo:
            await self.thresholds_for([fp_id])
        return dict(self._memo.get(key, {}))

    async def thresholds_for(self, fp_ids: Iterable[str]) -> dict[str, dict[str, Threshold]]:
        """`thresholds` for several points, in ONE statement.

        Ordering the union by `(fp_id, effective_from, id)` and partitioning it by `fp_id`
        leaves each point's rows in the `(effective_from, id)` order the singular reader reads
        them in, so the same last-row-per-category wins.
        """
        wanted = sorted({f for f in fp_ids if f})
        missing = [f for f in wanted if ("thresholds", f) not in self._memo]
        if missing:
            q = (
                select(Threshold)
                .where(Threshold.fp_id.in_(missing), Threshold.effective_from <= self.as_of)
                .order_by(Threshold.fp_id, Threshold.effective_from, Threshold.id)
            )
            grouped: dict[str, dict[str, Threshold]] = {f: {} for f in missing}
            for row in (await self.session.execute(q)).scalars():
                grouped[row.fp_id][row.category] = row
            for f in missing:
                self._memo[("thresholds", f)] = grouped[f]
        return {f: dict(self._memo[("thresholds", f)]) for f in wanted}

    async def latest_job_runs(self) -> dict[str, tuple[JobRun | None, JobRun | None]]:
        """Per job name: (last run, last successful run), restricted to runs started at or before T."""
        q = select(JobRun).where(JobRun.started_at <= self.as_of).order_by(JobRun.started_at, JobRun.id)
        out: dict[str, tuple[JobRun | None, JobRun | None]] = {}
        for row in (await self.session.execute(q)).scalars():
            last, last_ok = out.get(row.job, (None, None))
            out[row.job] = (row, row if row.ok else last_ok)
        return out

    async def product_freshness_anchors(self) -> dict[str, FreshnessAnchor]:
        """Per product id: the freshness anchor known at T, for /system/health.

        Table-agnostic on purpose. A product's values land in whichever table suits them —
        `observation`, `forecast_run`, `threshold` or `derived_feature` — and the old
        product-id-by-product-id branch covered exactly three ids, so every product added after
        the spike silently anchored on the threshold table and read `missing` forever. One
        grouped query per table, unioned, means a newly registered product is anchored the
        moment its first row lands (pg-migration-verification-2026-08-24 §P3.6 finding C).

        The value anchor is the time the SOURCE says the information is about, which for anything
        issued in cycles is the issue time, not the valid time: a forecast valid 72 h from now is
        not fresh because its valid_time is in the future. Hence `issued_at` where there is one
        and `valid_time` otherwise.

        `raw_artifact` is a fallback for the registry's `METADATA_ONLY_PRODUCTS` and nothing else,
        and `kind` says which was used. Those products store no value rows at all (station
        metadata) and would otherwise read `missing` while being fetched every day. Every other
        product is judged on its rows, because bytes can keep arriving while the step that turns
        them into values fails — and `nbm.build_grid_masks` fetches a `product:nbm-v5-core` file
        of its own, so an unrestricted fallback answered `current` for a product whose own job had
        never once succeeded (measured 2026-08-25, §P3.9 of the pg-migration verification).
        """
        anchors: dict[str, FreshnessAnchor] = {}
        fix = lambda x: None if x is None else (x if x.tzinfo else x.replace(tzinfo=self.as_of.tzinfo))  # noqa: E731

        def newer(a: datetime | None, b: datetime | None) -> datetime | None:
            return b if a is None else (a if b is None else max(a, b))

        async def collect(kind: str, value_col, retrieved_col, table, knowledge_col) -> None:
            q = select(table.product_id, func.max(value_col), func.max(retrieved_col)).where(knowledge_col <= self.as_of).group_by(table.product_id)
            for pid, v, r in (await self.session.execute(q)).all():
                if pid is None:
                    continue
                have = anchors.get(pid)
                if kind == "raw_artifact" and pid in VALID_UNTIL_SUPERSEDED_PRODUCTS and have is not None:
                    # Valid-until-superseded: the newest value row can be months old on a healthy
                    # system, so merge in the last successful fetch — freshness here is "when did
                    # we last check", not "how old is the value" (registry).
                    anchors[pid] = FreshnessAnchor(
                        kind=f"{have.kind}+{kind}",
                        valid_time=newer(have.valid_time, fix(v)),
                        retrieved_at=newer(have.retrieved_at, fix(r)),
                    )
                    continue
                if kind == "raw_artifact" and (have is not None or pid not in METADATA_ONLY_PRODUCTS):
                    # Value rows win, and for a product that is SUPPOSED to yield values, having
                    # none is `missing` — not `current` on the strength of bytes that never
                    # parsed. Only the registry's metadata-only products anchor on bytes.
                    continue
                if have is None:
                    anchors[pid] = FreshnessAnchor(kind=kind, valid_time=fix(v), retrieved_at=fix(r))
                else:  # the same product writes into more than one table: latest of both
                    anchors[pid] = FreshnessAnchor(
                        kind=f"{have.kind}+{kind}",
                        valid_time=newer(have.valid_time, fix(v)),
                        retrieved_at=newer(have.retrieved_at, fix(r)),
                    )

        await collect("observation", Observation.valid_time, Observation.retrieved_at, Observation, Observation.available_at)
        await collect("forecast_run", ForecastRun.issued_at, ForecastRun.retrieved_at, ForecastRun, ForecastRun.available_at)
        await collect("threshold", Threshold.retrieved_at, Threshold.retrieved_at, Threshold, Threshold.effective_from)
        await collect("derived_feature", func.coalesce(DerivedFeature.issued_at, DerivedFeature.valid_time), DerivedFeature.computed_at, DerivedFeature, DerivedFeature.available_at)
        await collect("raw_artifact", RawArtifact.fetched_at, RawArtifact.fetched_at, RawArtifact, RawArtifact.fetched_at)
        return anchors


def as_known_at(session: AsyncSession, as_of: datetime) -> Knowledge:
    return Knowledge(session=session, as_of=to_utc(as_of))
