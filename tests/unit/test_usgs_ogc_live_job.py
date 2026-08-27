"""The live OGC instantaneous job, and the twelve failure modes the migration must not have.

Each test here names the mutation it exists to catch (§8 of the migration brief). They run
against real captured pages, offline, with respx standing in for the network.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
import respx
from sqlalchemy import select

from cascade_core.db import create_schema, make_engine, make_session_factory
from cascade_core.fetch import ArchivingFetcher
from cascade_core.models import Observation, RawArtifact
from cascade_core.objectstore import LocalFilesystemStore
from cascade_core.seed import seed_all
from cascade_core.settings import SEED_FILE
from cascade_providers_usgs import jobs
from cascade_providers_usgs.ogc_client import OGC_BASE_URL, build_live_fetcher
from tests.conftest import GEO

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures/providers"
SITES = ("12100490", "12113000", "12119000", "12149000", "12189500", "12200500", "12213100")
NOW = datetime(2026, 8, 22, 13, 30, tzinfo=UTC)


def _page_for(site: str) -> bytes:
    return (FIXTURES / f"usgs_ogc/pipeline/{site}.json").read_bytes()


def _mock(transform=None) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        site = request.url.params.get("monitoring_location_id", "").removeprefix("USGS-")
        body = _page_for(site)
        if transform is not None:
            body = transform(site, json.loads(body))
            body = json.dumps(body).encode()
        return httpx.Response(200, content=body, headers={"content-type": "application/json"})

    respx.get(OGC_BASE_URL).mock(side_effect=handler)


@pytest.fixture
async def sessions(tmp_path):
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path}/ogc.db")
    await create_schema(engine)
    factory = make_session_factory(engine)
    async with factory() as session:
        await seed_all(session, geo_dir=GEO, seed_file=SEED_FILE)
    yield factory
    await engine.dispose()


def _fetcher(tmp_path) -> ArchivingFetcher:
    return ArchivingFetcher(store=LocalFilesystemStore(tmp_path / "raw"), user_agent="t", clock=lambda: NOW)


async def _run(sessions, tmp_path, *, hours: int = 3) -> int:
    async with sessions() as s:
        n = await jobs.run_fetch_instantaneous(s, _fetcher(tmp_path), hours=hours)
        await s.commit()
    return n


async def _rows(sessions):
    async with sessions() as s:
        return list((await s.execute(select(Observation).order_by(Observation.station_id, Observation.variable, Observation.valid_time))).scalars())


# --- 1, 2, 5, 6: what each observation MEANS -------------------------------------------------


@respx.mock
async def test_stage_and_flow_keep_their_own_identity_units_and_datum(sessions, tmp_path) -> None:
    """Catches: stage/flow swapped (1); unit mislabeled (2)."""
    _mock()
    await _run(sessions, tmp_path)
    rows = await _rows(sessions)
    assert rows, "anti-vacuity: no observations were written"
    by_var = {}
    for r in rows:
        by_var.setdefault(r.variable, []).append(r)
    assert set(by_var) == {"stage", "flow"}
    # ADR-0009: a stage carries its STATION's datum, never a constant and never another gauge's.
    # The seeded gauges are a mix of NGVD29 and NAVD88, and the Sauk (12189500) carries None
    # deliberately — it is a discharge-only proxy whose seed states it has no gauge-zero datum.
    # That is pre-existing on the legacy path too (production holds 4,079 such rows) and the
    # migration must not change it: transport parity means transport parity.
    expected = {
        "station:usgs:12100490": "NGVD29", "station:usgs:12113000": "NGVD29",
        "station:usgs:12119000": "NGVD29", "station:usgs:12200500": "NGVD29",
        "station:usgs:12149000": "NAVD88", "station:usgs:12213100": "NAVD88",
        "station:usgs:12189500": None,
    }
    for r in by_var["stage"]:
        assert r.unit == "ft", r.station_id
        assert r.datum == expected[r.station_id], (r.station_id, r.datum)
    assert len({r.datum for r in by_var["stage"]}) > 1, "anti-vacuity: a single-datum fixture would not test this"
    for r in by_var["flow"]:
        assert r.unit == "cfs", r.station_id
        assert r.datum is None, "flow never carries a datum"
    # stage and flow are different magnitudes at these gauges; a swap would collide them
    assert max(r.value for r in by_var["flow"] if r.value) > max(r.value for r in by_var["stage"] if r.value)


@respx.mock
async def test_the_approval_status_survives_into_quality(sessions, tmp_path) -> None:
    """Catches: provisional/approved flag dropped (5)."""
    _mock()
    await _run(sessions, tmp_path)
    rows = await _rows(sessions)
    assert all(("provisional" in r.quality) or ("approved" in r.quality) for r in rows)
    assert any("provisional" in r.quality for r in rows), "anti-vacuity: no provisional row in the capture"
    # and the source's own wording is preserved verbatim beside the mapped flag
    assert all(r.qualifier_raw for r in rows)


@respx.mock
async def test_a_missing_value_stays_missing_and_never_becomes_zero(sessions, tmp_path) -> None:
    """Catches: missing value turned into zero (6)."""
    def blank_one(site, body):
        if site == "12200500":
            body["features"][0]["properties"]["value"] = None
        return body

    _mock(blank_one)
    await _run(sessions, tmp_path)
    rows = await _rows(sessions)
    nulls = [r for r in rows if r.value is None]
    assert len(nulls) == 1, "anti-vacuity: the null was not exercised"
    assert "unparseable" in nulls[0].quality
    assert not any(r.value == 0.0 for r in rows), "a missing reading became a real zero"


# --- 3, 4: WHERE and WHEN --------------------------------------------------------------------


@respx.mock
async def test_timestamps_keep_the_apis_declared_offset(sessions, tmp_path) -> None:
    """Catches: timestamp read in local time instead of the API's declared basis (3)."""
    _mock()
    await _run(sessions, tmp_path)
    rows = await _rows(sessions)
    times = {r.valid_time for r in rows}
    assert times, "anti-vacuity"
    # the capture window is 10:30-13:30Z; a 7-hour local-time misread would land outside it
    for t in times:
        as_utc = t if t.tzinfo else t.replace(tzinfo=UTC)
        assert datetime(2026, 8, 22, 10, 0, tzinfo=UTC) <= as_utc <= datetime(2026, 8, 22, 14, 0, tzinfo=UTC), as_utc
    assert all(t.minute in (0, 15, 30, 45) for t in times), "15-minute cadence was not preserved"


@respx.mock
async def test_a_page_belonging_to_another_gauge_is_refused(sessions, tmp_path) -> None:
    """Catches: site id assigned to the wrong gauge (4).

    The per-site request makes it tempting to trust what we ASKED for. Filing the Skagit's
    discharge under the Cedar's name is the worst thing this job could do quietly.
    """
    def wrong_site(site, body):
        if site == "12119000":
            for f in body["features"]:
                f["properties"]["monitoring_location_id"] = "USGS-12200500"
        return body

    _mock(wrong_site)
    with pytest.raises(ValueError, match="refusing to attribute"):
        await _run(sessions, tmp_path)


# --- 7, 9, 10, 11, 12: transport, provenance and idempotency ---------------------------------


@respx.mock
async def test_a_paged_live_window_is_reported_not_silently_truncated(sessions, tmp_path, caplog) -> None:
    """Catches: pagination truncated (7).

    The live window is sized to fit one page. If it ever does not, that is a wrong assumption
    about the cadence, and the job must say so rather than quietly keeping the first page.
    """
    def add_next(site, body):
        body["links"] = [*body.get("links", []), {"rel": "next", "href": f"{OGC_BASE_URL}?cursor=abc"}]
        return body

    _mock(add_next)
    import logging

    with caplog.at_level(logging.WARNING):
        await _run(sessions, tmp_path)
    assert any("paged response" in rec.message for rec in caplog.records)


async def test_the_collection_and_parameters_are_the_instantaneous_ones() -> None:
    """Catches: wrong OGC collection used (9)."""
    from cascade_providers_usgs.ogc_client import ALLOWED_HOSTS, OGC_BASE_URL, PARAMETER_CODES

    assert OGC_BASE_URL == "https://api.waterdata.usgs.gov/ogcapi/v0/collections/continuous/items"
    assert PARAMETER_CODES == "00065,00060"  # gauge height, discharge
    assert ALLOWED_HOSTS == frozenset({"api.waterdata.usgs.gov"})
    # `continuous` is the instantaneous collection; `daily` is a different product entirely
    assert "/collections/continuous/" in OGC_BASE_URL
    assert "/collections/daily/" not in OGC_BASE_URL


@respx.mock
async def test_every_observation_links_the_raw_artifact_it_came_from(sessions, tmp_path) -> None:
    """Catches: raw artifact not linked (10)."""
    _mock()
    await _run(sessions, tmp_path)
    async with sessions() as s:
        arts = {a.id: a for a in (await s.execute(select(RawArtifact))).scalars()}
    rows = await _rows(sessions)
    assert rows and arts
    assert len(arts) == len(SITES), "one archived page per gauge"
    for r in rows:
        assert r.raw_artifact_id in arts, f"{r.station_id} {r.variable} has no archived source"
        assert arts[r.raw_artifact_id].request_url.startswith("https://api.waterdata.usgs.gov/"), (
            "the artifact must record the transport that actually served the row"
        )


@respx.mock
async def test_a_second_identical_poll_writes_nothing(sessions, tmp_path) -> None:
    """Catches: duplicate poll inserts duplicate logical observations (11)."""
    _mock()
    first = await _run(sessions, tmp_path)
    assert first > 0, "anti-vacuity"
    second = await _run(sessions, tmp_path)
    assert second == 0, "a re-poll of unchanged data must write no rows"
    rows = await _rows(sessions)
    keys = [(r.station_id, r.variable, r.valid_time) for r in rows]
    assert len(keys) == len(set(keys)), "the same logical observation was stored twice"


@respx.mock
async def test_an_ogc_failure_fails_and_never_reaches_for_the_legacy_service(sessions, tmp_path) -> None:
    """Catches: OGC failure silently falls back to IV (12).

    A transport that changes itself under failure makes provenance and outage interpretation
    ambiguous: health would read green while the data came from somewhere else entirely.
    """
    respx.get(OGC_BASE_URL).mock(return_value=httpx.Response(503))
    legacy = respx.get("https://waterservices.usgs.gov/nwis/iv/").mock(
        return_value=httpx.Response(200, content=(FIXTURES / "usgs/valid.json").read_bytes())
    )
    with pytest.raises(Exception):  # noqa: B017 - any failure is acceptable; silence is not
        await _run(sessions, tmp_path)
    assert not legacy.called, "the job reached for the decommissioning legacy service"
    assert await _rows(sessions) == [], "a failed poll must not leave observations behind"
    # and the module must not even import the legacy client
    source = Path(jobs.__file__).read_text()
    assert "cascade_providers_usgs.client" not in source
    assert "nwis/iv" not in source or "decommission" in source


@respx.mock
async def test_the_api_key_travels_as_a_header_and_never_in_the_url(tmp_path) -> None:
    """Catches: API key omitted from the keyed request (8) — and the worse failure, a key in a
    URL, which would be archived into `raw_artifact.request_url` and logged."""
    keyed = build_live_fetcher(LocalFilesystemStore(tmp_path / "a"), user_agent="t", api_key="SECRET-KEY")
    anon = build_live_fetcher(LocalFilesystemStore(tmp_path / "b"), user_agent="t", api_key=None)
    try:
        assert keyed._client.headers["X-Api-Key"] == "SECRET-KEY"  # noqa: SLF001
        assert "X-Api-Key" not in anon._client.headers  # noqa: SLF001
        assert "SECRET-KEY" not in str(keyed._client.params or "")  # noqa: SLF001
    finally:
        await keyed._client.aclose()  # noqa: SLF001
        await anon._client.aclose()  # noqa: SLF001
