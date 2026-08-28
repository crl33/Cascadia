"""Reservoir observations: the regulated basins' storage state, verbatim and undated-datum.

Assertions run against the real captured xml.cgi payloads (23 series, 2026-08-28). Pinned
provider truths: units arrive long-form and are stored verbatim; one instant can arrive under
SEVERAL SHEF type-source codes (LS under RG+RR, HP under RZ+RG — measured) and the pick is
declared, deterministic, and flags disagreement; forebay elevations carry no vertical datum
and none is invented.
"""

from __future__ import annotations

from datetime import UTC, datetime

import httpx
import pytest
import respx
from sqlalchemy import select

from cascade_core.db import create_schema, make_engine, make_session_factory
from cascade_core.fetch import ArchivingFetcher, FetchError, HostRateLimiter
from cascade_core.models import Observation
from cascade_core.objectstore import LocalFilesystemStore
from cascade_core.seed import seed_all
from cascade_core.settings import SEED_FILE
from cascade_providers_nwrfc import jobs as nwrfc_jobs
from cascade_providers_nwrfc.reservoirs import (
    BASE_URL,
    SERIES,
    ReservoirParseError,
    parse_series,
)
from tests.conftest import FIXTURES, GEO

NWRFC = FIXTURES / "nwrfc"
NOW = datetime(2026, 8, 28, 8, 50, tzinfo=UTC)


def _payload(lid: str, pe: str) -> bytes:
    return (NWRFC / f"{lid}_{pe}.xml").read_bytes()


# --- parser -------------------------------------------------------------------------------


#: What each series ACTUALLY served on capture day (2026-08-28). The research (R4) verified
#: these PE codes exist per site, but the provider serves several of them empty right now
#: (DIAW1 entirely silent; UBDW1 only QI; TLRW1/MORW1 only the pool elevation) — an empty
#: series is a legitimate answer, stored as nothing, never fabricated. SERIES stays the
#: research-verified capability set so the poll keeps asking; this map pins today's reality.
SERVED_ON_CAPTURE = {
    ("HHDW1", "HF"), ("HHDW1", "LS"), ("HHDW1", "QI"),
    ("MMRW1", "HF"), ("MMRW1", "LS"), ("MMRW1", "QI"), ("MMRW1", "QR"),
    ("RODW1", "HF"), ("RODW1", "QI"), ("RODW1", "QR"),
    ("UBDW1", "QI"),
    ("MORW1", "HP"),
    ("TLRW1", "HP"),
}


def test_every_captured_series_parses_and_the_silent_ones_are_honestly_empty() -> None:
    seen_units: set[str] = set()
    for lid, pes in SERIES.items():
        for pe in pes:
            values = parse_series(_payload(lid, pe), lid=lid, pe=pe)
            if (lid, pe) in SERVED_ON_CAPTURE:
                assert values, f"{lid}/{pe} parsed to nothing but served data at capture"
            else:
                assert values == (), f"{lid}/{pe} was silent at capture; parsing must say so"
            for v in values:
                assert v.valid_time.tzinfo is not None
                seen_units.add(v.unit)
    # long-form, exactly as served — never abbreviated at ingest
    assert "cubic feet per second" in seen_units
    assert "k-acre-feet" in seen_units
    assert "feet" in seen_units


def test_duplicate_shef_codes_collapse_deterministically_and_disagreement_is_flagged() -> None:
    # HHDW1 LS really serves RG and RR at the same instants (the captured fact)
    values = parse_series(_payload("HHDW1", "LS"), lid="HHDW1", pe="LS")
    times = [v.valid_time for v in values]
    assert len(times) == len(set(times)), "one row per instant"
    assert all(v.ts_code in ("RZ", "RG", "RR") for v in values)
    # synthetic disagreement: two codes, different values at one instant
    doc = b"""<?xml version="1.0" ?><HydroMetData xmlns="/xml/schemas/2004/03/hydromet_data">
    <SiteData id="HHDW1"><observedData>
    <observedValue petype="LS" durCode="0" tsCode="RR" extremumCode="Z">
      <dataDateTime>2026-08-28T00:00:00Z</dataDateTime>
      <lake_storage units="k-acre-feet">35.84</lake_storage></observedValue>
    <observedValue petype="LS" durCode="0" tsCode="RG" extremumCode="Z">
      <dataDateTime>2026-08-28T00:00:00Z</dataDateTime>
      <lake_storage units="k-acre-feet">36.90</lake_storage></observedValue>
    </observedData></SiteData></HydroMetData>"""
    (only,) = parse_series(doc, lid="HHDW1", pe="LS")
    assert only.ts_code == "RG", "declared preference, not first-seen (RG outranks RR)"
    assert only.value == 36.90
    assert only.disagrees, "the codes disagree and the row says so"


def test_wrong_site_naive_instants_and_broken_xml_are_refused() -> None:
    with pytest.raises(ReservoirParseError, match="wrong_site"):
        parse_series(_payload("MMRW1", "HF"), lid="HHDW1", pe="HF")
    with pytest.raises(ReservoirParseError, match="not_xml"):
        parse_series(b"<html>Server error</html><", lid="HHDW1", pe="HF")
    naive = _payload("HHDW1", "HF").replace(b":00:00Z<", b":00:00<")
    with pytest.raises(ReservoirParseError, match="naive_instant"):
        parse_series(naive, lid="HHDW1", pe="HF")


# --- the job ------------------------------------------------------------------------------


@pytest.fixture
async def sessions(tmp_path):
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path}/nwrfc.db")
    await create_schema(engine)
    factory = make_session_factory(engine)
    async with factory() as session:
        await seed_all(session, geo_dir=GEO, seed_file=SEED_FILE)
    yield factory
    await engine.dispose()


def _fetcher(tmp_path) -> ArchivingFetcher:
    return ArchivingFetcher(
        store=LocalFilesystemStore(tmp_path), user_agent="test", clock=lambda: NOW,
        limiter=HostRateLimiter(min_interval_s=0.0),
    )


def _mock_all() -> None:
    for lid, pes in SERIES.items():
        for pe in pes:
            respx.get(BASE_URL, params__contains={"id": lid, "pe": pe}).mock(
                return_value=httpx.Response(200, content=_payload(lid, pe)))


def test_the_seven_reservoir_stations_are_seeded_into_their_basins() -> None:
    import json
    from pathlib import Path

    doc = json.loads((Path(SEED_FILE).parent / "reservoirs.json").read_text())
    by_id = {s["id"]: s for s in doc["stations"]}
    assert len(by_id) == 7
    assert by_id["station:nwrfc:RODW1"]["basin_id"] == "basin:skagit"
    assert by_id["station:nwrfc:MORW1"]["basin_id"] == "basin:cedar"
    for s in by_id.values():
        assert s["lon"] < 0, "west longitudes carry their sign (the provider serves them unsigned)"
        assert s["vertical_datum"] is None


@respx.mock
async def test_one_poll_stores_every_series_with_honest_columns(sessions, tmp_path) -> None:
    _mock_all()
    async with sessions() as s:
        written = await nwrfc_jobs.run_fetch_reservoirs(s, _fetcher(tmp_path), now=NOW)
        await s.commit()
        rows = list((await s.execute(select(Observation).where(
            Observation.product_id == "product:nwrfc-reservoir-obs"))).scalars())
    assert written == len(rows) > 300  # the 13 series that served data, ~24-96 instants each
    stations = {r.station_id for r in rows}
    # DIAW1 answered but served every series empty on capture day (SERVED_ON_CAPTURE): it
    # stores nothing and appears in no rows — an empty answer is not an outage.
    assert stations == {nwrfc_jobs.station_id(lid) for lid, _ in SERVED_ON_CAPTURE}
    by_var = {}
    for r in rows:
        by_var.setdefault(r.variable, []).append(r)
    assert set(by_var) == {"forebay_elevation", "storage", "inflow", "outflow"}
    for r in by_var["forebay_elevation"]:
        assert r.datum is None and nwrfc_jobs.DATUM_UNSTATED in r.quality
        assert r.unit == "feet"
    assert {r.unit for r in by_var["storage"]} == {"k-acre-feet"}
    assert {r.unit for r in by_var["inflow"]} == {"cubic feet per second"}
    for r in rows:
        # the wild carries codes beyond the preference list (RX observed); any unlisted code
        # ranks below the listed ones and still rides verbatim in qualifier_raw
        assert r.qualifier_raw and r.qualifier_raw.startswith("R") and len(r.qualifier_raw) == 2


@respx.mock
async def test_a_second_poll_appends_nothing(sessions, tmp_path) -> None:
    _mock_all()
    async with sessions() as s:
        first = await nwrfc_jobs.run_fetch_reservoirs(s, _fetcher(tmp_path), now=NOW)
        await s.commit()
    async with sessions() as s:
        second = await nwrfc_jobs.run_fetch_reservoirs(s, _fetcher(tmp_path), now=NOW)
        await s.commit()
    assert first > 0 and second == 0


@respx.mock
async def test_one_dead_station_does_not_hold_the_others_hostage(sessions, tmp_path) -> None:
    _mock_all()
    for pe in SERIES["RODW1"]:
        respx.get(BASE_URL, params__contains={"id": "RODW1", "pe": pe}).mock(
            return_value=httpx.Response(500))
    async with sessions() as s:
        written = await nwrfc_jobs.run_fetch_reservoirs(s, _fetcher(tmp_path), now=NOW)
        await s.commit()
        stations = {r for (r,) in await s.execute(select(Observation.station_id).distinct())}
    assert written > 0
    assert nwrfc_jobs.station_id("RODW1") not in stations
    assert nwrfc_jobs.station_id("HHDW1") in stations


@respx.mock
async def test_a_total_outage_fails_loudly_instead_of_recording_success(sessions, tmp_path) -> None:
    respx.get(BASE_URL).mock(return_value=httpx.Response(500))
    async with sessions() as s:
        with pytest.raises(FetchError, match="provider_down"):
            await nwrfc_jobs.run_fetch_reservoirs(s, _fetcher(tmp_path), now=NOW)


# --- the endpoint -------------------------------------------------------------------------


def test_the_endpoint_product_name_is_pinned() -> None:
    from cascade_api.routes import RESERVOIR_PRODUCT, RESERVOIR_VARIABLES
    from cascade_core.registry import PRODUCT_NWRFC_RESERVOIR

    assert RESERVOIR_PRODUCT == PRODUCT_NWRFC_RESERVOIR
    assert set(RESERVOIR_VARIABLES) == set(nwrfc_jobs.VARIABLE_BY_PE.values())


@respx.mock
async def test_the_basin_endpoint_serves_verbatim_state_and_the_nooksack_truth(sessions, tmp_path) -> None:
    from httpx import ASGITransport, AsyncClient

    from cascade_api.main import create_app
    from cascade_core.settings import Settings
    from tests.conftest import GEO as GEO_DIR

    _mock_all()
    async with sessions() as s:
        await nwrfc_jobs.run_fetch_reservoirs(s, _fetcher(tmp_path), now=NOW)
        await s.commit()
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path}/nwrfc.db")  # same file, async engine
    app = create_app(Settings(db_url="sqlite+aiosqlite://", geo_dir=GEO_DIR), engine=engine)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/basins/basin:green-duwamish/reservoirs",
                             params={"as_of": NOW.isoformat().replace("+00:00", "Z")})
        assert r.status_code == 200
        doc = r.json()
        (hhd,) = doc["reservoirs"]
        assert hhd["lid"] == "HHDW1"
        v = hhd["variables"]
        assert set(v) == {"forebay_elevation", "storage", "inflow"}, "QR is not an HHDW1 series"
        assert v["storage"]["unit"] == "k-acre-feet"
        assert v["inflow"]["unit"] == "cubic feet per second"
        assert nwrfc_jobs.DATUM_UNSTATED in v["forebay_elevation"]["quality"]
        assert v["forebay_elevation"]["qualifier"].startswith("R")
        ref = doc["provenance_refs"][hhd["prov"]]
        assert ref["source_kind"] == "OBSERVED" and "no vertical datum" in ref["label"]
        # the Skagit carries its three dams; empty variables mean a dam that served nothing
        r = await client.get("/basins/basin:skagit/reservoirs",
                             params={"as_of": NOW.isoformat().replace("+00:00", "Z")})
        lids = [x["lid"] for x in r.json()["reservoirs"]]
        assert lids == ["DIAW1", "RODW1", "UBDW1"]
        # the Nooksack is unregulated: an empty list is the truth, not a gap
        r = await client.get("/basins/basin:nooksack/reservoirs",
                             params={"as_of": NOW.isoformat().replace("+00:00", "Z")})
        assert r.status_code == 200 and r.json()["reservoirs"] == []
        # replay honesty: before the poll, the dams' variables are absent
        early = await client.get("/basins/basin:green-duwamish/reservoirs",
                                 params={"as_of": "2026-08-27T00:00:00Z"})
        assert early.json()["reservoirs"][0]["variables"] == {}
