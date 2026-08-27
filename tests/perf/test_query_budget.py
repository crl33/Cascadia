"""The query budget for `/viz/basins`, and the semantic baseline it must not buy speed with.

Four assertions, and they only mean something together:

1. **Budget.** `/viz/basins` may issue at most :data:`VIZ_BASINS_QUERY_BUDGET` statements — 16,
   down from the 120 this file was written to record. Query *count* is the thing pinned, not
   latency: the production symptom was 120 statements at ~176 ms of round trip each, and a
   wall-clock assertion would measure this laptop's disk while the defect walked back in.

2. **Shape.** No statement comes from a reader that answers about ONE scope. A budget alone
   cannot tell thirteen batched reads from thirteen basins read one at a time — the second
   passes on a six-basin fixture and is the original defect at production scale.

3. **Body.** The response, normalised for read-time-only fields, is byte-for-byte the body stored
   under `baseline/`. Without this, the budget is trivially satisfiable by returning less.

4. **Purity.** With every prefetch removed the answer is unchanged and only the count moves,
   which is the claim the batching rests on: the surfaces still read for themselves, and a
   prefetch only decides whether those reads reach the database.

The baseline is regenerated with `python -m tests.perf.capture_baseline`. Regenerating it to make
this file pass is falsifying the evidence: a diff here means the endpoint's answer changed, which
is either a bug or a deliberate contract change that belongs in its own commit with its own
reason. `--check` prints the same diff without writing anything.

Offline (SQLite + checked-in payloads + fixed knowledge clock), so it runs in the default suite
and depends on neither the network nor the weather.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import inspect
from unittest import mock

import httpx
import pytest

from cascade_api.main import create_app
from cascade_contracts import ContractEnvelope
from cascade_core.db import make_engine
from cascade_core.settings import Settings
from cascade_hydrology import assemble

from tests.perf import normalize
from tests.perf.harness import AS_OF, BASELINE_DIR, BEFORE, SKAGIT, ingest, iso, settings_for
from tests.perf.instrument import QueryRecorder, attributed

# --------------------------------------------------------------------------------- the budget

#: Measured 2026-08-26 on the harness below, and confirmed statement-for-statement against a
#: scratch PostgreSQL 18 + PostGIS database. **120 before the amplification was removed, 13
#: after** — and the 120 were only 12 distinct SQL texts, which is what made them removable.
#: The inventory of all 120, and where each of them went, is in tests/perf/README.md.
#:
#: 16 rather than 13 because four reads are conditional on the data, not on the code: the NWM
#: member series is not read where no NWM cycle is known, the secondary-variable observation is
#: not read where no observation is, the climatology fallback IS read where a flow percentile is
#: missing, and the day-of-year record context IS read where a percentile reaches p90. The
#: ceiling the code can reach is 15; the budget leaves one.
#:
#: **Measured 2026-08-26 with the Tier 0 tail and velocity in place: still 13.** The velocity
#: (`streamflow_growth_24h` / `_48h`) costs ZERO statements — it reads the same
#: `streamflow_doy_percentile` rows the level does, over a narrower valid_time range than
#: `susceptibility.prefetch` already batched, so it is answered out of the request memo. Forcing
#: the record-context read at every gauge (`RANK_READ_EDGE = 0`) measures 14, for six basins and
#: for one alike.
#:
#: **The number is now independent of how many basins are asked for.** That is the property
#: worth defending, and the one this test defends: `/viz/basins` (six basins) and
#: `/basins/{id}/state` (one) issue the same thirteen statements, so a per-basin N+1 growing
#: back shows up here as a count that scales with the fixture again.
#:
#: LOWER THIS as amplification is removed. Never raise it without saying, in the commit, which
#: query was added and why it could not be batched into one already being issued.
VIZ_BASINS_QUERY_BUDGET = 16

#: The single-basin envelope, same assembler, one sixth of the basins — and now the same count,
#: because every read on this path is set-based over whatever set it was handed. 22 before.
BASIN_STATE_QUERY_BUDGET = 16

#: Zero, and it should stay zero: `Knowledge` memoises its readers for the life of one request,
#: so a repeat means a caller reached the database around it. 17 before.
VIZ_BASINS_EXACT_REPEATS = 0

#: `Knowledge` readers that answer about exactly ONE scope. None of them may reach the database
#: on this path: whatever they want has been read for every scope at once before the loop, and a
#: statement issued from one of them is a per-basin or per-point N+1 by definition.
#: `basin` / `products` are absent because they are genuinely once-per-request reference reads.
SINGULAR_READERS = frozenset(
    {
        "forecast_point_by_lid",
        "station",
        "observations",
        "latest_observation",
        "latest_forecast_run",
        "forecast_values",
        "derived_features",
        "latest_derived_feature",
        "thresholds",
    }
)


# --------------------------------------------------------------------------------- fixtures


@pytest.fixture(scope="module")
def ingested(tmp_path_factory) -> Settings:
    """One ingested scratch database for the module. The ingest is the expensive part (exact
    basin-mask clipping, an 86-year climatology build); the reads under test are not."""
    return ingest(settings_for(tmp_path_factory.mktemp("perf")))


async def _noop(*_args, **_kwargs) -> None:
    """Stands in for a prefetch, so the endpoint falls all the way back to its per-scope reads."""


async def _get(settings: Settings, path: str, *, as_of: datetime = AS_OF) -> tuple[dict, QueryRecorder]:
    """Call one endpoint at a pinned knowledge time, counting every statement it issues."""
    engine = make_engine(settings.db_url)
    recorder = QueryRecorder().attach(engine)
    try:
        app = create_app(settings, engine=engine)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://perf") as client:
            with attributed():
                recorder.clear()
                response = await client.get(path, params={"as_of": iso(as_of)})
        assert response.status_code == 200, response.text
        return response.json(), recorder
    finally:
        recorder.detach()
        await engine.dispose()


def _baseline(stem: str) -> dict:
    path: Path = BASELINE_DIR / f"{stem}.json"
    assert path.exists(), f"no semantic baseline at {path}; run `python -m tests.perf.capture_baseline`"
    return json.loads(path.read_text())


# --------------------------------------------------------------------------------- tests


async def test_viz_basins_stays_inside_its_query_budget(ingested: Settings) -> None:
    """The regression gate. 120 statements for six basins was ~20 per basin, and per-basin work
    executed one statement at a time is what made this endpoint 21.8 s in production against
    2.67 s locally: the count was identical, only the round-trip cost differed."""
    _, recorder = await _get(ingested, "/viz/basins")
    assert recorder.total <= VIZ_BASINS_QUERY_BUDGET, (
        f"/viz/basins issued {recorder.total} queries, budget is {VIZ_BASINS_QUERY_BUDGET}.\n"
        + "\n".join(f"  {count:3d}x  {site}" for site, count in recorder.by_call_site().most_common())
    )


async def test_no_statement_comes_from_a_per_scope_reader(ingested: Settings) -> None:
    """Every statement `/viz/basins` issues comes from a SET-BASED reader.

    The count alone cannot tell "thirteen batched reads" from "thirteen basins read one at a
    time", and the second would pass the budget on a small fixture and fail in production. This
    names the shape instead of the size: a singular reader reaching the database on this path
    means a scope the prefetch did not cover, which is an N+1 at whatever scale the data has.
    """
    _, recorder = await _get(ingested, "/viz/basins")
    singular = {
        site: count
        for site, count in recorder.by_call_site().items()
        if site.split(" <- ")[0] in SINGULAR_READERS
    }
    assert not singular, "per-scope readers reached the database:\n" + "\n".join(f"  {n:3d}x  {s}" for s, n in singular.items())


async def test_basin_state_stays_inside_its_query_budget(ingested: Settings) -> None:
    _, recorder = await _get(ingested, f"/basins/{SKAGIT}/state")
    assert recorder.total <= BASIN_STATE_QUERY_BUDGET, (
        f"/basins/{SKAGIT}/state issued {recorder.total} queries, budget is {BASIN_STATE_QUERY_BUDGET}.\n"
        + "\n".join(f"  {count:3d}x  {site}" for site, count in recorder.by_call_site().most_common())
    )


async def test_exact_duplicate_queries_do_not_increase(ingested: Settings) -> None:
    """A statement issued twice with identical parameters inside one request is answered twice
    for one question. Pinned separately from the total because it is the cheapest class to remove
    and the easiest to reintroduce."""
    _, recorder = await _get(ingested, "/viz/basins")
    assert recorder.exact_repeats <= VIZ_BASINS_EXACT_REPEATS, (
        f"{recorder.exact_repeats} exact duplicate queries, baseline is {VIZ_BASINS_EXACT_REPEATS}.\n"
        + "\n".join(
            f"  {count}x  {sites}\n       {rep.parameters[:200]}"
            for rep, count, sites in recorder.by_identity()
            if count > 1
        )
    )


@pytest.mark.parametrize(("stem", "path"), [("viz_basins", "/viz/basins"), ("basin_skagit_state", f"/basins/{SKAGIT}/state")])
async def test_the_body_is_identical_to_the_semantic_baseline(ingested: Settings, stem: str, path: str) -> None:
    """Correctness is the whole point: the budget above is only worth having if the answer is
    unchanged. Normalisation covers `generated_at` and nothing else — at a pinned `as_of` every
    freshness age on this path is computed against `k.as_of`, so ages are deterministic and are
    compared, not blanked (tests/perf/normalize.py explains why that matters)."""
    body, _ = await _get(ingested, path)
    baseline = _baseline(stem)
    differences = normalize.diff(baseline, body)
    assert not differences, "response body changed against tests/perf/baseline:\n" + "\n".join(f"  {d}" for d in differences[:40])
    assert normalize.canonical_json(body) == normalize.canonical_json(baseline)


@pytest.mark.parametrize("when", [AS_OF, BEFORE], ids=["at_the_pinned_time", "at_an_earlier_knowledge_time"])
async def test_the_prefetches_are_pure_warm_up(ingested: Settings, when) -> None:
    """With every prefetch removed, `/viz/basins` answers exactly the same thing — slowly.

    This is the claim the whole design rests on. Each surface still reads for itself through the
    same per-scope readers it always used; the prefetches only mean those readers find the rows
    already in the request-scoped memo. If that is true, deleting them can cost statements and
    nothing else — so the bodies are compared, and the counts are compared too, because a patch
    that silently failed to apply would make this test agree with itself and prove nothing.

    Run at two knowledge times, the second early enough that most surfaces are UNKNOWN: the
    branches a prefetch could most easily disturb are the ones where a read comes back empty.
    """
    warm, warm_queries = await _get(ingested, "/viz/basins", as_of=when)
    with mock.patch.object(assemble, "_prefetch_basins", _noop), mock.patch.object(assemble, "prefetch_points", _noop):
        cold, cold_queries = await _get(ingested, "/viz/basins", as_of=when)
    assert cold_queries.total > warm_queries.total, (
        f"the prefetch patch did not take effect: {cold_queries.total} queries with it removed, "
        f"{warm_queries.total} with it in place"
    )
    assert not normalize.diff(cold, warm), "removing the prefetches changed the answer:\n" + "\n".join(
        f"  {d}" for d in normalize.diff(cold, warm)[:40]
    )
    assert normalize.canonical_json(cold) == normalize.canonical_json(warm)


async def test_the_baseline_body_is_a_valid_envelope() -> None:
    """The stored baseline is the contract, not just bytes: if it stopped validating, a later
    diff against it would be comparing the endpoint to something the contract forbids."""
    for stem in ("viz_basins", "basin_skagit_state"):
        ContractEnvelope.model_validate(_baseline(stem))


async def test_instrumentation_does_not_change_the_response(ingested: Settings) -> None:
    """`attributed()` wraps `Knowledge`'s readers to attribute statements to call sites. That
    wrapping must be pure observation, or every measurement above is measuring a different
    endpoint than the one that ships."""
    engine = make_engine(ingested.db_url)
    try:
        app = create_app(ingested, engine=engine)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://perf") as client:
            plain = await client.get("/viz/basins", params={"as_of": iso(AS_OF)})
        assert plain.status_code == 200
    finally:
        await engine.dispose()
    instrumented, _ = await _get(ingested, "/viz/basins")
    assert normalize.canonical_json(plain.json()) == normalize.canonical_json(instrumented)


@pytest.mark.parametrize("when", [AS_OF, BEFORE], ids=["at_the_pinned_time", "at_an_earlier_knowledge_time"])
async def test_the_explanation_endpoint_does_not_prefetch(ingested: Settings, when) -> None:
    """`/explanations/{basin}/agreement` assembles ONE point, so it must not batch.

    A set-based read over a set of size one IS the per-point read: it saves no round trip and can
    cost an extra statement. The route carried two prefetch calls until 2026-08-26; measured, they
    were 11 statements against 11 at the pinned time and 8 against 6 at the earlier one — never
    cheaper, sometimes dearer. They were removed, and this test keeps them out.

    The batching exists for the many-basin envelope. Adding it here again would be a plausible
    "consistency" change that costs round trips, which is exactly the direction Phase B reversed.
    """
    from cascade_api import routes

    src = inspect.getsource(routes.agreement_explanation)
    assert "prefetch" not in src.replace("No prefetch here on purpose", ""), (
        "the explanation route calls a prefetch again; it assembles one point, so a batch there "
        "cannot save a round trip and has been measured to cost one"
    )
    body, queries = await _get(ingested, f"/explanations/{SKAGIT}/agreement", as_of=when)
    assert body["surface"] == "agreement"
    # Whatever it costs, it must not exceed the whole six-basin envelope: a single-point
    # explanation that out-queries the full envelope would mean the per-point path had regressed.
    assert queries.total <= VIZ_BASINS_QUERY_BUDGET
