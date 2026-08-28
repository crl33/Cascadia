"""NWPS HEFS: the ensemble that is gone in ten days if nobody archives it.

Every assertion here runs against bytes captured from the live API on 2026-08-27 and checked in
under `tests/fixtures/providers/nwps_hefs/`. The provider documents itself as experimental and
"may be modified without advance notice", so these tests are as much a shape alarm as a
correctness check: when the payload changes, a job must fail loudly rather than quietly store a
thinner ensemble.

The tests are grouped by what would go wrong:

1. shape and knowledge time — the two timestamps must not be conflated;
2. refusals — a changed shape must raise, not adapt;
3. the job — archives what is missing, is idempotent, and isolates a failing location;
4. truth class — these are MODELED members, never official probabilities.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest
import respx
from sqlalchemy import select

from cascade_core.db import create_schema, make_engine, make_session_factory
from cascade_core.fetch import ArchivingFetcher, HostRateLimiter
from cascade_core.models import DerivedFeature, RawArtifact
from cascade_core.objectstore import LocalFilesystemStore
from cascade_core.registry import (
    PRODUCT_HEFS_ENSEMBLE,
    PRODUCT_HEFS_QUANTILES,
    SOURCES,
    SRC_NWPS,
    SRC_NWPS_HEFS,
)
from cascade_core.seed import seed_all
from cascade_core.settings import SEED_FILE
from cascade_providers_nwps import hefs_jobs
from cascade_providers_nwps.hefs_client import BASE_URL, DISCHARGE_PARAMETER, OBJECT_PREFIX
from cascade_providers_nwps.hefs_parser import (
    parse_ensembles,
    parse_headers,
    parse_quantiles,
)
from cascade_providers_nwps.reaches_parser import ParseError
from tests.conftest import FIXTURES, GEO

HEFS = FIXTURES / "nwps_hefs"
NOW = datetime(2026, 8, 27, 17, 0, tzinfo=UTC)
CYCLE = datetime(2026, 8, 27, 12, 0, tzinfo=UTC)
CREATED = datetime(2026, 8, 27, 15, 53, 43, tzinfo=UTC)
LIDS = ("RNTW1", "CRNW1", "MVEW1", "NKSW1", "AUBW1", "WRAW1")

HEADERS = (HEFS / "headers_MVEW1.json").read_bytes()
ENSEMBLE = (HEFS / "ensembles_MVEW1_2026-08-27T12.json").read_bytes()
QUANTILES = (HEFS / "hydrograph_quantiles_MVEW1.json").read_bytes()
EMPTY_HEADERS = (HEFS / "headers_unknown_location.json").read_bytes()
#: Three of the 45 members. The job tests walk 10 cycles x 6 points; parsing the full
#: payload 60 times cost 147 s and proved nothing the parser tests above do not.
ENSEMBLE_TRIMMED = (HEFS / "ensembles_MVEW1_trimmed_3_members.json").read_bytes()


@pytest.fixture
async def sessions(tmp_path):
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path}/hefs.db")
    await create_schema(engine)
    factory = make_session_factory(engine)
    async with factory() as session:
        await seed_all(session, geo_dir=GEO, seed_file=SEED_FILE)
    yield factory
    await engine.dispose()


def _fetcher(tmp_path) -> ArchivingFetcher:
    """A fetcher with the politeness delay removed — offline, so there is nobody to be polite to.

    The job makes up to 10 cycles x 6 locations + headers + quantiles calls in one run. Against the
    production `HostRateLimiter` (0.5 s per host) that is ~35 s per test of pure sleeping, for
    requests respx answers from memory. The interval is production behaviour and stays the default
    everywhere it matters; only these offline tests opt out.
    """
    return ArchivingFetcher(
        store=LocalFilesystemStore(tmp_path),
        user_agent="test",
        clock=lambda: NOW,
        limiter=HostRateLimiter(min_interval_s=0.0),
    )


def _mock(headers: bytes = HEADERS, ensemble: bytes = ENSEMBLE_TRIMMED, quantiles: bytes = QUANTILES) -> None:
    """The same payloads for every lid — plumbing, not hydrology.

    The Skagit's real ensemble answers for all six points. What is being exercised is the job's
    walk of the retention window, not the flows; the hydrologic assertions are made against the
    parser, on the site whose bytes these actually are.
    """
    respx.get(f"{BASE_URL}headers/").mock(
        return_value=httpx.Response(200, content=headers, headers={"content-type": "application/json"})
    )
    def ensembles_for_requested_cycle(request: httpx.Request) -> httpx.Response:
        # The Skagit's real 45-member payload, re-stamped to whichever cycle was asked for. The
        # job REFUSES an ensemble whose forecast_datetime is not the one requested — that guard is
        # exercised directly below — so a mock that always returned 2026-08-27 would only ever
        # test the guard, never the walk across the retention window.
        want = request.url.params["forecast_datetime"]
        doc = json.loads(ensemble)
        for member in doc[0]:
            member["forecast_datetime"] = want
        return httpx.Response(200, content=json.dumps(doc).encode(),
                              headers={"content-type": "application/json"})

    respx.get(f"{BASE_URL}ensembles/").mock(side_effect=ensembles_for_requested_cycle)
    respx.get(f"{BASE_URL}hydrograph-quantiles/").mock(
        return_value=httpx.Response(200, content=quantiles, headers={"content-type": "application/json"})
    )


# --- 1. shape and knowledge time ---------------------------------------------------------


def test_the_headers_list_is_the_retention_window_this_provider_serves() -> None:
    """Ten cycles, one per day at 12Z. This number IS the reason the adapter exists."""
    headers = parse_headers(HEADERS)
    assert len(headers) == 10
    cycles = sorted(h.forecast_datetime for h in headers)
    assert cycles[0] == datetime(2026, 8, 18, 12, 0, tzinfo=UTC)
    assert cycles[-1] == CYCLE
    assert {h.forecast_datetime.hour for h in headers} == {12}
    assert {h.parameter_id for h in headers} == {DISCHARGE_PARAMETER}
    assert {h.ensemble_id for h in headers} == {"MEFP"}
    assert {h.units for h in headers} == {"CFS"}
    assert {h.step_seconds for h in headers} == {21600}


def test_the_cycle_and_its_publication_time_are_never_the_same_instant() -> None:
    """ADR-0010's whole point, in the one place this provider could get it wrong.

    `forecast_datetime` is the model cycle (issued_at); `creation_datetime` is when NWS published
    it (available_at). They sit 3-4 h apart. Deriving either from the other would put knowledge in
    the system before the provider had it — the look-ahead bias the replay audit exists to catch.
    """
    head = next(h for h in parse_headers(HEADERS) if h.forecast_datetime == CYCLE)
    assert head.creation_datetime == CREATED
    lag = head.creation_datetime - head.forecast_datetime
    assert 3 * 3600 <= lag.total_seconds() <= 5 * 3600, "the documented ~3-4 h publication latency"
    for h in parse_headers(HEADERS):
        assert h.creation_datetime > h.forecast_datetime


def test_an_ensemble_is_45_weather_year_traces_on_a_six_hour_grid() -> None:
    ensembles = parse_ensembles(ENSEMBLE)
    assert len(ensembles) == 1
    ens = ensembles[0]
    assert ens.header.forecast_datetime == CYCLE
    assert len(ens.members) == 45
    indices = sorted(m.index for m in ens.members)
    assert indices == list(range(1981, 2026)), "member indices are weather YEARS, not member numbers"
    lengths = {len(m.values) for m in ens.members}
    assert lengths == {121}, "a 30-day horizon at 6 h"
    first = ens.members[0].values
    assert first[0][0] == CYCLE
    step = first[1][0] - first[0][0]
    assert step.total_seconds() == 21600
    assert all(isinstance(v, float) for _, v in first), "no None in a healthy trace"


def test_the_published_quantiles_are_labelled_by_their_exceedance_levels() -> None:
    q = parse_quantiles(QUANTILES)
    assert q.location_id == "MVEW1"
    assert q.levels == (0.05, 0.1, 0.25, 0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.9, 0.95)
    assert q.rows
    for _when, values, _mx, _mn in q.rows:
        assert len(values) == len(q.levels), "every value must carry its own level"


def test_an_unknown_location_answers_with_an_empty_list_not_an_error() -> None:
    """HTTP 200 + `[]`, verified live. Raising here would make a quiet location look like an outage."""
    assert json.loads(EMPTY_HEADERS) == []
    assert parse_headers(EMPTY_HEADERS) == ()


# --- 2. refusals: a changed shape must raise, not adapt -----------------------------------


def test_a_mislabelled_quantile_row_is_refused_rather_than_zipped_short() -> None:
    doc = json.loads(QUANTILES)
    doc["value_set"][0]["quantile_values"] = doc["value_set"][0]["quantile_values"][:-1]
    with pytest.raises(ParseError, match="exceedance levels"):
        parse_quantiles(json.dumps(doc).encode())


def test_members_from_two_different_cycles_are_refused() -> None:
    """One group must be one forecast. Mixing them would file members under the wrong issued_at."""
    doc = json.loads(ENSEMBLE)
    doc[0][1]["forecast_datetime"] = "2026-08-26T12:00:00Z"
    with pytest.raises(ParseError, match="mixes cycles"):
        parse_ensembles(json.dumps(doc).encode())


def test_a_naive_timestamp_is_refused_rather_than_assumed_utc() -> None:
    doc = json.loads(HEADERS)
    doc[0]["forecast_datetime"] = "2026-08-27T12:00:00"
    with pytest.raises(ParseError, match="carries no offset"):
        parse_headers(json.dumps(doc).encode())


def test_an_unknown_time_step_unit_is_refused() -> None:
    doc = json.loads(HEADERS)
    doc[0]["time_step_unit"] = "hour"
    with pytest.raises(ParseError, match="time_step_unit"):
        parse_headers(json.dumps(doc).encode())


def test_a_non_numeric_event_value_is_refused_rather_than_dropped() -> None:
    doc = json.loads(ENSEMBLE)
    doc[0][0]["events"][3]["value"] = "n/a"
    with pytest.raises(ParseError, match="is not a number"):
        parse_ensembles(json.dumps(doc).encode())


def test_the_provider_miss_val_becomes_none_not_a_number() -> None:
    doc = json.loads(ENSEMBLE)
    doc[0][0]["miss_val"] = -999.0
    doc[0][0]["events"][2]["value"] = -999.0
    ens = parse_ensembles(json.dumps(doc).encode())[0]
    assert ens.members[0].values[2][1] is None


# --- 3. the job ---------------------------------------------------------------------------


@respx.mock
async def test_the_job_archives_every_retained_cycle_it_does_not_already_have(sessions, tmp_path) -> None:
    """A backfill that runs daily: the first pass recovers the whole retention window."""
    _mock()
    async with sessions() as s:
        written = await hefs_jobs.run_fetch_hefs(s, _fetcher(tmp_path))
        await s.commit()
        rows = list(
            (
                await s.execute(
                    select(DerivedFeature).where(DerivedFeature.feature == hefs_jobs.FEATURE_MEMBERS)
                )
            ).scalars()
        )
    assert written > 0
    # ten retained cycles x six seed forecast points
    assert len(rows) == 10 * len(LIDS)
    assert {r.product_id for r in rows} == {PRODUCT_HEFS_ENSEMBLE}
    assert {r.method_id for r in rows} == {hefs_jobs.METHOD_MEMBERS}
    for r in rows:
        assert r.value is None, "a 45-member ensemble is not one number"
        assert r.issued_at == r.valid_time, "the row is about a cycle, not an instant"
        assert r.available_at > r.issued_at, "published after the cycle it forecasts"
        assert r.raw_artifact_id is not None
        assert r.values_json["member_count"] == 3, "the trimmed job fixture; 45 is asserted on the full one"
        assert r.values_json["encoding"] == "grid"


@respx.mock
async def test_a_second_run_stores_nothing_new(sessions, tmp_path) -> None:
    """Idempotent by cycle identity, so the daily run is cheap and a re-run is safe."""
    _mock()
    async with sessions() as s:
        first = await hefs_jobs.run_fetch_hefs(s, _fetcher(tmp_path))
        await s.commit()
    async with sessions() as s:
        second = await hefs_jobs.run_fetch_hefs(s, _fetcher(tmp_path))
        await s.commit()
        rows = len(
            list(
                (
                    await s.execute(
                        select(DerivedFeature.id).where(DerivedFeature.feature == hefs_jobs.FEATURE_MEMBERS)
                    )
                ).scalars()
            )
        )
    assert first > 0 and second == 0
    assert rows == 10 * len(LIDS)


@respx.mock
async def test_one_location_failing_does_not_discard_the_others(sessions, tmp_path) -> None:
    """Same rule the NWM reach job learned the hard way: isolate the failure, keep the data."""
    _mock()
    calls = {"n": 0}

    def headers_side_effect(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if request.url.params.get("location_id") == "MVEW1":
            raise httpx.ReadTimeout("")
        return httpx.Response(200, content=HEADERS, headers={"content-type": "application/json"})

    respx.get(f"{BASE_URL}headers/").mock(side_effect=headers_side_effect)
    async with sessions() as s:
        written = await hefs_jobs.run_fetch_hefs(s, _fetcher(tmp_path))
        await s.commit()
        scopes = {
            r for (r,) in await s.execute(
                select(DerivedFeature.scope_id).where(DerivedFeature.feature == hefs_jobs.FEATURE_MEMBERS)
            )
        }
    assert written > 0
    assert "fp:nwps:MVEW1" not in scopes
    assert len(scopes) == len(LIDS) - 1


@respx.mock
async def test_a_run_where_no_location_answers_is_retryable(sessions, tmp_path) -> None:
    """A silent zero here means history is being lost, so it must fail rather than report success."""
    respx.get(f"{BASE_URL}headers/").mock(side_effect=httpx.ReadTimeout(""))
    async with sessions() as s:
        with pytest.raises(hefs_jobs.NoHefsCyclesError, match="did not answer"):
            await hefs_jobs.run_fetch_hefs(s, _fetcher(tmp_path))
        await s.rollback()


@respx.mock
async def test_the_raw_bytes_are_archived_under_their_own_prefix(sessions, tmp_path) -> None:
    """The archive is the irreplaceable half: a cycle that ages out cannot be re-fetched.

    `hefs/` exists so the bucket can be reasoned about — and, unlike `nbm/`, it must never acquire
    an expiry rule.
    """
    _mock()
    async with sessions() as s:
        await hefs_jobs.run_fetch_hefs(s, _fetcher(tmp_path))
        await s.commit()
        keys = [k for (k,) in await s.execute(select(RawArtifact.object_key))]
    assert keys, "anti-vacuity"
    assert all(k.startswith(OBJECT_PREFIX) for k in keys), keys[:3]


# --- 4. truth class -----------------------------------------------------------------------


def test_hefs_is_its_own_source_and_is_not_an_official_forecast() -> None:
    """DATA_SOURCES H4: folding HEFS into `src:nwps-v1` would let an experimental ensemble
    inherit the official forecast's source_kind. Phase 5 may promote the QUANTILES to official
    probabilities (DATA_DOCTRINE §9(a)); until it rules, the members are MODELED."""
    by_id = {s["id"]: s for s in SOURCES}
    assert SRC_NWPS_HEFS in by_id and SRC_NWPS_HEFS != SRC_NWPS
    assert by_id[SRC_NWPS_HEFS]["kind"] == "MODELED"
    assert by_id[SRC_NWPS]["kind"] == "OFFICIAL_FORECAST"
    assert "EXPERIMENTAL" in str(by_id[SRC_NWPS_HEFS]["authority"])


def test_the_stored_members_say_what_they_are_and_what_they_are_not() -> None:
    """The caveat travels in the row, not only in a docstring nobody reading the table will open."""
    note = hefs_jobs.MEMBERS_NOTE
    assert "EXPERIMENTAL" in note
    assert "weather year" in note.lower() and "1981" in note
    assert "official probability" in note.lower()
    assert "§9(a)" in note


def test_nothing_computes_a_quantile_from_the_members() -> None:
    """The quantiles are fetched, not derived — that is what keeps them official guidance.

    A Cascade-computed quantile over the same members would be a Cascade-derived number wearing an
    official badge, however closely it matched. Enforced by reading the source: no percentile,
    quantile, median, sort or mean over member values anywhere in the adapter.
    """
    for name in ("hefs_jobs", "hefs_parser", "hefs_client"):
        src = Path(
            __import__(f"cascade_providers_nwps.{name}", fromlist=["__file__"]).__file__
        ).read_text()
        code = [ln for ln in src.splitlines() if not ln.strip().startswith("#")]
        body = "\n".join(code)
        body = body.split('"""', 2)[-1]  # drop the module docstring, which discusses quantiles
        for banned in ("statistics.", "np.percentile", "quantile(", "median(", "mean("):
            assert banned not in body, f"{name} computes {banned} over member values"


@respx.mock
async def test_an_ensemble_for_a_different_cycle_than_requested_is_refused(sessions, tmp_path) -> None:
    """Storing it would file one cycle's members under another cycle's issued_at.

    Every replay after that point would read the wrong forecast as having been knowable at the
    wrong time, which is the one error this whole knowledge-time discipline exists to prevent. So
    the job refuses rather than trusting the query it sent.
    """
    respx.get(f"{BASE_URL}headers/").mock(
        return_value=httpx.Response(200, content=HEADERS, headers={"content-type": "application/json"})
    )
    respx.get(f"{BASE_URL}ensembles/").mock(  # always the 08-27 cycle, whatever was asked for
        return_value=httpx.Response(200, content=ENSEMBLE, headers={"content-type": "application/json"})
    )
    async with sessions() as s:
        with pytest.raises(ValueError, match="asked .* and got"):
            await hefs_jobs.run_fetch_hefs(s, _fetcher(tmp_path))
        await s.rollback()


@respx.mock
async def test_the_published_quantiles_are_stored_as_their_own_product(sessions, tmp_path) -> None:
    """Separate row, separate product, separate method — because they are a different KIND of thing.

    The members are 45 equally-plausible traces; the quantiles are NWS's own summary of them. Phase
    5 may show the quantiles as official probability (DATA_DOCTRINE §9(a)) and may never show a
    Cascade summary of the members that way, so the two must not share an identity.
    """
    _mock()
    async with sessions() as s:
        await hefs_jobs.run_fetch_hefs(s, _fetcher(tmp_path))
        await s.commit()
        rows = list(
            (
                await s.execute(
                    select(DerivedFeature).where(DerivedFeature.feature == hefs_jobs.FEATURE_QUANTILES)
                )
            ).scalars()
        )
    assert len(rows) == len(LIDS), "one per seed forecast point"
    assert {r.product_id for r in rows} == {PRODUCT_HEFS_QUANTILES}
    assert {r.method_id for r in rows} == {hefs_jobs.METHOD_QUANTILES}
    assert PRODUCT_HEFS_QUANTILES != PRODUCT_HEFS_ENSEMBLE
    for r in rows:
        assert r.value is None
        assert r.values_json["exceedance_levels"] == [0.05, 0.1, 0.25, 0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.9, 0.95]
        assert len(r.values_json["rows"]) == 121
        assert "never Cascade-derived" in r.values_json["note"] or "official guidance" in r.values_json["note"]


# --- 4. the endpoint: the provider's numbers, verbatim, on the knowledge clock -------------


def test_the_endpoint_names_are_pinned_to_what_the_job_writes() -> None:
    from cascade_api.routes import HEFS_QUANTILES_FEATURE, HEFS_QUANTILES_METHOD

    assert HEFS_QUANTILES_FEATURE == hefs_jobs.FEATURE_QUANTILES
    assert HEFS_QUANTILES_METHOD == hefs_jobs.METHOD_QUANTILES


@respx.mock
async def test_the_latest_quantiles_are_served_verbatim_with_provenance(sessions, tmp_path) -> None:
    from httpx import ASGITransport, AsyncClient

    from cascade_api.main import create_app
    from cascade_core.settings import Settings
    from tests.conftest import GEO

    _mock()
    async with sessions() as s:
        await hefs_jobs.run_fetch_hefs(s, _fetcher(tmp_path))
        await s.commit()
        stored = (await s.execute(
            select(DerivedFeature).where(DerivedFeature.feature == hefs_jobs.FEATURE_QUANTILES)
        )).scalars().first()
    app = create_app(Settings(db_url="sqlite+aiosqlite://", geo_dir=GEO), engine=sessions.kw["bind"])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/forecast-points/MVEW1/hefs/latest")
        assert r.status_code == 200
        doc = r.json()
        # the ladder is the stored provider document, byte-for-byte in substance
        assert doc["exceedance_levels"] == stored.values_json["exceedance_levels"]
        assert doc["rows"] == stored.values_json["rows"]
        assert doc["unit"] == stored.unit and doc["parameter_id"] == stored.values_json["parameter_id"]
        assert "verbatim" in doc["provenance"]["label"] and "EXPERIMENTAL" in doc["provenance"]["label"]
        assert doc["provenance"]["source_kind"] == "MODELED"
        # the knowledge clock governs: before the cycle was AVAILABLE, it does not exist here
        early = (await client.get(
            "/forecast-points/MVEW1/hefs/latest",
            params={"as_of": (stored.available_at.replace(tzinfo=UTC) - timedelta(hours=1)).isoformat()},
        ))
        assert early.status_code == 404
        # an unknown point is a 404, never an empty ladder
        assert (await client.get("/forecast-points/XXXX1/hefs/latest")).status_code == 404
