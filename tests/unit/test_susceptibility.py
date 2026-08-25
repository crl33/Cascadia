"""SUSCEPTIBILITY v0 — the §5 exit tests of docs/research/p3-surfaces-design-2026-08-24.md.

Offline: SQLite + respx + checked-in REAL provider payloads. No network (docs/TESTING.md §3).

Four of these tests exist to stop a future change from being *quietly* wrong rather than to
check arithmetic, and they are the point of the file:

- ``test_soil_saturation_percentile_is_present_and_null_with_its_reason`` — soil must stay
  UNKNOWN *visibly*. A driver that disappears looks like a surface that has no opinion; a driver
  with ``value=None`` and an unavailability provenance is a surface saying so.
- ``test_snotel_soil_moisture_still_cannot_support_a_percentile`` — asserts against the REAL
  captured SMS bytes, so "let us just use SNOTEL soil moisture" has to argue with the data.
- ``test_no_snow_driver_is_ever_scored`` — HYDROLOGY §7: more SWE is not more risk.
- ``test_regulated_basins_are_capped_and_the_skagit_reads_the_sauk`` — on a regulated reach flow
  is an operator decision, not a basin state.
"""

from __future__ import annotations

import gzip
import json
from datetime import UTC, date, datetime, timedelta

import httpx
import pytest
import respx
from sqlalchemy import select

from cascade_contracts import ConfidenceLabel, SourceKind
from cascade_contracts.visualization import SurfaceLevel
from cascade_core.db import create_schema, make_engine, make_session_factory
from cascade_core.fetch import ArchivingFetcher
from cascade_core.knowledge import as_known_at
from cascade_core.models import Basin, DerivedFeature
from cascade_core.objectstore import LocalFilesystemStore
from cascade_core.registry import PRODUCT_AWDB_DAILY, PRODUCT_USGS_DAILY_STATS, PRODUCT_USGS_OGC_DAILY
from cascade_core.seed import seed_all
from cascade_core.settings import SEED_FILE
from cascade_hydrology import susceptibility
from cascade_providers_awdb import jobs as awdb_jobs
from cascade_providers_awdb import normalize as awdb_normalize
from cascade_providers_awdb.parser import ParseError as AwdbParseError
from cascade_providers_awdb.parser import parse_data, parse_stations
from cascade_providers_usgs import climatology as clim
from cascade_providers_usgs import stats_jobs
from cascade_providers_usgs.parser import ParseError
from cascade_providers_usgs.stats_parser import (
    parse_daily_csv,
    parse_latest_daily_json,
    parse_nwis_stat_rdb,
)
from tests.conftest import FIXTURES, GEO

# The fixtures were captured 2026-08-24 ~22:06Z; the latest daily mean everywhere is 2026-08-23,
# whose PDT day boundary is 2026-08-24T07:00Z. NOW is five hours later: fresh, not stale.
NOW = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)
STATS = FIXTURES / "usgs_stats"
AWDB = FIXTURES / "awdb"
SKAGIT_SITE = "12200500"
SAUK_SITE = "12189500"
GAUGE_SITES = ("12100490", "12113000", "12119000", "12149000", "12189500", "12213100")

DAILY_URL = "https://api.waterdata.usgs.gov/ogcapi/v0/collections/daily/items"
LATEST_URL = "https://api.waterdata.usgs.gov/ogcapi/v0/collections/latest-daily/items"
NWIS_STAT_URL = "https://waterservices.usgs.gov/nwis/stat/"
AWDB_STATIONS_URL = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/stations"
AWDB_DATA_URL = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/data"


# --- fixtures ----------------------------------------------------------------------------


@pytest.fixture
async def sessions(tmp_path):
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path}/susceptibility.db")
    await create_schema(engine)
    factory = make_session_factory(engine)
    async with factory() as session:
        await seed_all(session, geo_dir=GEO, seed_file=SEED_FILE)
    yield factory
    await engine.dispose()


def fetcher(tmp_path) -> ArchivingFetcher:
    return ArchivingFetcher(store=LocalFilesystemStore(tmp_path), user_agent="CascadiaPapsukkal/0.1 (test)", clock=lambda: NOW)


def _mock_usgs_stats() -> None:
    """The real captured payloads, served per site.

    The Skagit's own record answers for 12200500 and the Sauk's for every other gauge. That is
    PLUMBING, not hydrology: it exercises the job's write path end to end offline. The
    hydrological assertions in this file are made against the site whose record is really its
    own (the golden climatology test, and the cross-check test).
    """
    skagit = (STATS / "daily_12200500.csv").read_bytes()
    sauk = (STATS / "daily_12189500_2000.csv").read_bytes()
    stat_skagit = (STATS / "stat_12200500.rdb").read_bytes()
    stat_sauk = (STATS / "stat_12189500.rdb").read_bytes()

    def daily(request: httpx.Request) -> httpx.Response:
        site = request.url.params["monitoring_location_id"].removeprefix("USGS-")
        body = skagit if site == SKAGIT_SITE else sauk
        return httpx.Response(200, content=body, headers={"content-type": "text/csv; charset=utf-8"})

    def stat(request: httpx.Request) -> httpx.Response:
        site = request.url.params["sites"]
        # The Sauk's real table, relabelled to the requested site_no. The relabelling is what
        # makes the plumbing testable at all: `published_climatology` REFUSES rows whose site_no
        # does not match the site asked for, which the next test asserts directly.
        body = stat_skagit if site == SKAGIT_SITE else stat_sauk.replace(SAUK_SITE.encode(), site.encode())
        return httpx.Response(200, content=body, headers={"content-type": "text/plain"})

    respx.get(DAILY_URL).mock(side_effect=daily)
    respx.get(NWIS_STAT_URL).mock(side_effect=stat)
    respx.get(LATEST_URL).mock(
        return_value=httpx.Response(200, content=(STATS / "latest_daily_gauges.json").read_bytes(),
                                    headers={"content-type": "application/json"})
    )


def _mock_awdb() -> None:
    respx.get(AWDB_STATIONS_URL).mock(
        return_value=httpx.Response(200, content=(AWDB / "stations_wa_sntl.json").read_bytes(),
                                    headers={"content-type": "application/json"})
    )
    respx.get(AWDB_DATA_URL).mock(
        return_value=httpx.Response(200, content=(AWDB / "data_wteq_prec_puget.json").read_bytes(),
                                    headers={"content-type": "application/json"})
    )


async def _ingest(sessions, tmp_path, *, awdb: bool = True) -> None:
    async with sessions() as session:
        f = fetcher(tmp_path)
        await stats_jobs.run_build_climatology(session, f, now=NOW)
        await stats_jobs.run_fetch_daily_percentile(session, f, now=NOW)
        if awdb:
            await awdb_jobs.run_fetch_snotel_context(session, f, now=NOW)
        await session.commit()


# --- A. parsers on real bytes ---------------------------------------------------------------


def test_daily_csv_is_the_whole_record_and_is_not_time_ordered_on_the_wire() -> None:
    raw = (STATS / "daily_12200500.csv").read_bytes()
    assert b"\n,,2014-04-02," in raw[:200]  # the payload really does start mid-record
    rows = parse_daily_csv(raw, site=SKAGIT_SITE)
    assert len(rows) == 31373
    assert [r.day for r in rows] == sorted(r.day for r in rows)  # the parser sorts
    assert rows[0].day == date(1940, 10, 1) and rows[-1].day == date(2026, 8, 23)
    assert rows[-1].approval_status == "Provisional" and rows[0].approval_status == "Approved"
    assert {r.site for r in rows} == {SKAGIT_SITE}


def test_daily_csv_refuses_a_broken_row_and_a_missing_approval_column() -> None:
    with pytest.raises(ParseError, match="not an ISO date"):
        parse_daily_csv((STATS / "daily_malformed.csv").read_bytes(), site=SKAGIT_SITE)
    with pytest.raises(ParseError, match="approval_status"):
        parse_daily_csv((STATS / "daily_missing_column.csv").read_bytes(), site=SKAGIT_SITE)


def test_latest_daily_carries_every_gauge_with_its_approval_status() -> None:
    rows = parse_latest_daily_json((STATS / "latest_daily_gauges.json").read_bytes())
    assert {r.site for r in rows} == set(GAUGE_SITES)
    assert {r.day for r in rows} == {date(2026, 8, 23)}
    assert all(r.approval_status == "Provisional" for r in rows)


def test_published_statistics_table_parses_366_days() -> None:
    stats = parse_nwis_stat_rdb((STATS / "stat_12200500.rdb").read_bytes())
    assert len(stats) == 366
    jan1 = next(s for s in stats if (s.month, s.day) == (1, 1))
    assert jan1.percentiles[50] == 13700.0 and jan1.begin_year == 1941 and jan1.count == 86
    assert set(jan1.percentiles) == {5, 10, 25, 50, 75, 90, 95}


def test_the_modern_statistics_api_serves_no_discharge_normals_at_the_skagit_outlet() -> None:
    """Coverage is per-SITE, which is itself the argument for owning the climatology.

    Verified live 2026-08-24 by the canary: `USGS-12189500` (the Sauk) now returns a full
    366-day discharge percentile ladder from this API, while `USGS-12200500` still returns
    nothing at all. A published climatology that exists at one gauge and not its neighbour
    cannot be the dependency for a six-basin surface; it can only be a cross-check. See
    DATA_SOURCES H9.
    """
    doc = json.loads((STATS / "observation_normals_12200500_00060.json").read_bytes())
    assert doc["features"] == []


# --- B. the climatology -------------------------------------------------------------------


def test_golden_climatology_reproduces_exactly() -> None:
    """Design §5 susceptibility 2: the ladder is reproduced from the checked-in record."""
    rows = parse_daily_csv((STATS / "daily_12200500.csv").read_bytes(), site=SKAGIT_SITE)
    built = clim.build_doy_climatology(rows, site=SKAGIT_SITE, unit="cfs").to_values_json()
    golden = json.loads((STATS / "golden_climatology_12200500.json").read_bytes())
    for key in ("ladder", "begin_year", "end_year", "used_rows", "skipped", "percentiles"):
        assert built[key] == golden[key], f"{key} drifted from the golden ladder"
    assert len(built["ladder"]) == 366 and "02-29" in built["ladder"]
    assert built["skipped"]["not_approved"] == 117  # provisional tail, counted not used


def test_cascade_and_published_p50_agree_on_at_least_350_of_366_days() -> None:
    """Design §5 susceptibility 2, second half — and the two are never fused."""
    rows = parse_daily_csv((STATS / "daily_12200500.csv").read_bytes(), site=SKAGIT_SITE)
    cascade = clim.build_doy_climatology(rows, site=SKAGIT_SITE, unit="cfs")
    published = clim.published_climatology(
        parse_nwis_stat_rdb((STATS / "stat_12200500.rdb").read_bytes()), site=SKAGIT_SITE, unit="cfs"
    )
    within = [k for k in clim.DOY_KEYS
              if (d := clim.p50_disagreement(cascade, published, k)) is not None and abs(d) <= 0.10]
    assert len(within) >= 350
    assert cascade.method_id != published.method_id
    assert cascade.climatology_ref.startswith("usgs-ogc-daily:") and published.climatology_ref.startswith("usgs-nwis-stat:")


def test_percentile_ranking_interpolates_inside_and_refuses_to_invent_a_tail() -> None:
    ladder = clim.DoyLadder(key="08-24", values={5: 100.0, 10: 200.0, 25: 300.0, 50: 400.0, 75: 500.0, 90: 600.0, 95: 700.0}, sample_count=425)
    assert clim.percentile_of(400.0, ladder).percentile == 50.0
    mid = clim.percentile_of(450.0, ladder)
    assert mid.percentile == 62.5 and mid.quality == ()
    high = clim.percentile_of(9999.0, ladder)
    assert high.percentile == 95.0 and clim.OUTSIDE_RANGE in high.quality
    low = clim.percentile_of(1.0, ladder)
    assert low.percentile == 5.0 and clim.OUTSIDE_RANGE in low.quality


def test_a_thin_day_of_year_sample_is_refused_rather_than_published() -> None:
    rows = parse_daily_csv((STATS / "daily_12200500.csv").read_bytes(), site=SKAGIT_SITE)[:20]
    built = clim.build_doy_climatology(rows, site=SKAGIT_SITE)
    assert built.ladders == {} or all(entry.sample_count >= clim.MIN_SAMPLE for entry in built.ladders.values())


def test_daily_mean_valid_time_is_the_local_day_boundary_and_says_when_it_guessed() -> None:
    """A daily mean dated D is complete at local midnight ENDING D (DATA_DOCTRINE §3)."""
    summer, flags = clim.daily_mean_valid_time(date(2026, 8, 23), time_zone="PST8PDT")
    assert summer == datetime(2026, 8, 24, 7, 0, tzinfo=UTC) and flags == ()  # PDT
    winter, _ = clim.daily_mean_valid_time(date(2026, 1, 15), time_zone="PST8PDT")
    assert winter == datetime(2026, 1, 16, 8, 0, tzinfo=UTC)  # PST — DST is not assumed away
    guessed, flags = clim.daily_mean_valid_time(date(2026, 8, 23), time_zone=None)
    assert guessed == datetime(2026, 8, 24, tzinfo=UTC) and flags == ("day_boundary_assumed_utc",)


# --- C. SNOTEL context, and the soil negative result ----------------------------------------


def test_snotel_sites_map_to_basins_by_their_own_huc() -> None:
    stations = parse_stations((AWDB / "stations_wa_sntl.json").read_bytes())
    geo = json.loads(gzip.open(GEO / "basins_seed_full.geojson.gz").read())
    huc8 = {f["properties"]["id"]: f["properties"]["huc8"] for f in geo["features"]}
    mapping = awdb_normalize.map_stations_to_basins(stations, huc8)
    assert set(mapping) == set(huc8)
    assert all(sites for sites in mapping.values())  # every seed basin has at least one pillow
    assert sum(len(s) for s in mapping.values()) == 29
    skagit = {s.triplet for s in mapping["basin:skagit"]}
    assert "515:WA:SNTL" in skagit  # Harts Pass: filed under Upper Skagit, caveat kept visible


def test_swe_percent_of_median_is_unknown_when_every_median_is_zero() -> None:
    """Late August: the honest answer is 'no value, and here is why' — never 0 %, never 100 %."""
    stations = parse_stations((AWDB / "stations_wa_sntl.json").read_bytes())
    series = parse_data((AWDB / "data_wteq_prec_puget.json").read_bytes())
    geo = json.loads(gzip.open(GEO / "basins_seed_full.geojson.gz").read())
    huc8 = {f["properties"]["id"]: f["properties"]["huc8"] for f in geo["features"]}
    sites = awdb_normalize.map_stations_to_basins(stations, huc8)["basin:skagit"]
    mine = tuple(s for s in series if s.triplet in {x.triplet for x in sites})
    swe = awdb_normalize.swe_percent_of_median(mine, sites, day=awdb_normalize.latest_common_day(mine, element="WTEQ"))
    assert swe.value is None
    assert "median" in swe.reason and swe.excluded["median_zero"] > 0
    assert swe.direction == awdb_normalize.CONTEXT_DIRECTION

    precip = awdb_normalize.precip_14d_percent_of_median(mine, sites, day=awdb_normalize.latest_common_day(mine, element="PREC"))
    assert precip.value is not None and precip.value > 0  # PREC differences ARE usable in August
    assert precip.direction == awdb_normalize.CONTEXT_DIRECTION
    assert all(c.value >= 0 for c in precip.sites)  # a water-year rollover is dropped, never clamped


def test_snotel_soil_moisture_still_cannot_support_a_percentile() -> None:
    """The evidence behind ``soil_saturation_percentile = null`` (design §2.1, §7).

    Asserted against the REAL captured bytes so this decision has to be re-argued with data.
    """
    soil = parse_data((AWDB / "data_sms_puget.json").read_bytes())
    assert soil, "the SMS capture is not empty; it is unusable, which is a different thing"
    assert all(v.median is None for s in soil for v in s.values), "AWDB now serves an SMS median — revisit design §2.1"
    depth_sets = {s.triplet: tuple(sorted({x.height_depth for x in soil if x.triplet == s.triplet})) for s in soil}
    assert len(set(depth_sets.values())) > 1, "depths are inconsistent between sites"
    assert any(v.qc_flag == "N" for s in soil for v in s.values), "'no profile' flags are present"
    # Physically incoherent: at Rainy Pass the -4 in probe reads 0.0 % between two wet layers.
    rainy = {s.height_depth: s.values[-1].value for s in soil if s.triplet == "711:WA:SNTL"}
    assert rainy[-2] > 0 and rainy[-4] == 0.0 and rainy[-8] > rainy[-2]


def test_awdb_parser_refuses_a_missing_field() -> None:
    with pytest.raises(AwdbParseError, match="elementCode"):
        parse_data((AWDB / "data_missing_field.json").read_bytes())


# --- D. the ingest jobs, offline ------------------------------------------------------------


@respx.mock
async def test_build_climatology_stores_both_ladders_separately_and_never_fuses_them(sessions, tmp_path) -> None:
    _mock_usgs_stats()
    async with sessions() as session:
        written = await stats_jobs.run_build_climatology(session, fetcher(tmp_path), now=NOW)
        await session.commit()
        rows = list((await session.execute(select(DerivedFeature).where(DerivedFeature.feature == "streamflow_doy_climatology"))).scalars())
    assert written == 12  # six gauges x (cascade-built, usgs-published)
    by_method = {}
    for row in rows:
        by_method.setdefault(row.method_id, []).append(row)
    assert set(by_method) == {clim.METHOD_ID, clim.PUBLISHED_METHOD_ID}
    assert len(by_method[clim.METHOD_ID]) == 6 and len(by_method[clim.PUBLISHED_METHOD_ID]) == 6
    # the two products are distinct, so the registry can resolve two different source kinds
    assert {r.product_id for r in by_method[clim.METHOD_ID]} == {PRODUCT_USGS_OGC_DAILY}
    assert {r.product_id for r in by_method[clim.PUBLISHED_METHOD_ID]} == {PRODUCT_USGS_DAILY_STATS}
    assert all(r.value is None and r.values_json["ladder"] for r in rows)  # a ladder is not one number
    assert all(r.raw_artifact_id is not None for r in rows)


@respx.mock
async def test_climatology_job_is_append_only_and_a_rerun_writes_nothing(sessions, tmp_path) -> None:
    _mock_usgs_stats()
    async with sessions() as session:
        first = await stats_jobs.run_build_climatology(session, fetcher(tmp_path), now=NOW)
        await session.commit()
    async with sessions() as session:
        second = await stats_jobs.run_build_climatology(session, fetcher(tmp_path), now=NOW)
        await session.commit()
        n = len(list((await session.execute(select(DerivedFeature).where(DerivedFeature.feature == "streamflow_doy_climatology"))).scalars()))
    assert first == 12 and second == 0 and n == 12


@respx.mock
async def test_the_cross_check_may_fail_without_costing_the_surface_its_value(sessions, tmp_path) -> None:
    """WaterServices decommissions Q1 2027. This is the rehearsal."""
    _mock_usgs_stats()
    respx.get(NWIS_STAT_URL).mock(return_value=httpx.Response(503))
    async with sessions() as session:
        written = await stats_jobs.run_build_climatology(session, fetcher(tmp_path), now=NOW)
        await session.commit()
        methods = {r.method_id for r in (await session.execute(select(DerivedFeature))).scalars()}
    assert written == 6 and methods == {clim.METHOD_ID}


@respx.mock
async def test_daily_percentile_job_ranks_every_gauge_against_its_own_ladder(sessions, tmp_path) -> None:
    _mock_usgs_stats()
    async with sessions() as session:
        f = fetcher(tmp_path)
        await stats_jobs.run_build_climatology(session, f, now=NOW)
        written = await stats_jobs.run_fetch_daily_percentile(session, f, now=NOW)
        await session.commit()
        rows = list((await session.execute(select(DerivedFeature).where(DerivedFeature.feature == "streamflow_doy_percentile"))).scalars())
    assert written == 6 and len(rows) == 6
    for row in rows:
        assert 0.0 <= row.percentile <= 100.0
        assert row.unit == "cfs" and row.value is not None  # the observation travels with its rank
        assert row.valid_time.replace(tzinfo=UTC) == datetime(2026, 8, 24, 7, 0, tzinfo=UTC)  # PDT day boundary
        assert row.climatology_ref.startswith("usgs-ogc-daily:")
        assert row.values_json["cross_check"]["threshold"] == 0.10
        assert "provisional" in row.quality


@respx.mock
async def test_snotel_context_is_written_per_basin_and_soil_is_not_among_it(sessions, tmp_path) -> None:
    _mock_awdb()
    async with sessions() as session:
        written = await awdb_jobs.run_fetch_snotel_context(session, fetcher(tmp_path), now=NOW)
        await session.commit()
        rows = list((await session.execute(select(DerivedFeature))).scalars())
    assert written == 12  # six basins x (SWE, 14-day precipitation)
    assert {r.feature for r in rows} == {"basin_swe_percent_of_median", "snotel_precip_14d_percent_of_median"}
    assert all(r.product_id == PRODUCT_AWDB_DAILY and r.scope_kind == "basin" for r in rows)
    swe = [r for r in rows if r.feature == "basin_swe_percent_of_median"]
    assert all(r.value is None and "unavailable" in r.quality for r in swe)  # August: no median
    assert all(r.confidence_label == "low" for r in rows if r.value is not None)  # point network, never better


# --- E. the surface (design §5 susceptibility 1, 3, 4, 5) ------------------------------------


@respx.mock
async def test_every_basin_reports_a_state_and_a_score_when_a_recent_daily_mean_exists(sessions, tmp_path) -> None:
    _mock_usgs_stats()
    _mock_awdb()
    await _ingest(sessions, tmp_path)
    async with sessions() as session:
        k = as_known_at(session, NOW)
        products = await k.products()
        for basin in await k.basins():
            a = await susceptibility.assess(k, basin, products)
            assert a.surface.state is not SurfaceLevel.UNKNOWN, basin.id
            assert a.surface.reason is None
            assert a.surface.score is not None and 0.0 <= a.surface.score <= 1.0
            assert a.surface.value is not None and a.surface.value.unit == "pct"
            assert a.surface.horizon_h is None  # a present-state surface has no horizon
            assert a.surface.experimental is True
            assert a.surface.spread is None  # the ladder is in cfs; spread must share value's unit
            assert a.surface.prov in a.refs
            assert a.refs[a.surface.prov].source_kind is SourceKind.EXPERIMENTAL
            assert {d.prov for d in a.drivers} <= set(a.refs)


@respx.mock
async def test_a_daily_mean_older_than_48_hours_makes_the_surface_unknown_with_that_reason(sessions, tmp_path) -> None:
    """Design §5 susceptibility 1, second branch — and NO fallback to the 15-minute value."""
    _mock_usgs_stats()
    await _ingest(sessions, tmp_path, awdb=False)
    async with sessions() as session:
        # the daily mean is complete at 2026-08-24T07:00Z, so 48 h expires at 08-26T07:00Z
        for as_of, expected in ((NOW + timedelta(hours=40), False), (NOW + timedelta(hours=50), True)):
            k = as_known_at(session, as_of)
            products = await k.products()
            basin = await k.basin("basin:skagit")
            a = await susceptibility.assess(k, basin, products)
            assert (a.surface.state is SurfaceLevel.UNKNOWN) is expected
            if expected:
                assert a.surface.reason == susceptibility.STALE_REASON
                assert a.surface.score is None and a.surface.value is None


async def test_a_basin_with_no_climatology_says_so_rather_than_blaming_staleness(sessions) -> None:
    async with sessions() as session:
        k = as_known_at(session, NOW)
        products = await k.products()
        basin = await k.basin("basin:skagit")
        a = await susceptibility.assess(k, basin, products)
    assert a.surface.state is SurfaceLevel.UNKNOWN
    assert a.surface.reason == susceptibility.no_climatology_reason("station:usgs:12189500")


async def test_a_basin_with_no_configured_gauge_says_that_instead(sessions) -> None:
    async with sessions() as session:
        basin = await session.get(Basin, "basin:cedar")
        basin.susceptibility_gauge_id = None
        await session.flush()
        k = as_known_at(session, NOW)
        a = await susceptibility.assess(k, basin, await k.products())
    assert a.surface.reason == susceptibility.NO_GAUGE_REASON
    assert a.surface.confidence is ConfidenceLabel.UNKNOWN


@respx.mock
async def test_soil_saturation_percentile_is_present_and_null_with_its_reason(sessions, tmp_path) -> None:
    """Design §5 susceptibility 3. The absence of a soil claim must be RENDERED, not omitted."""
    _mock_usgs_stats()
    _mock_awdb()
    await _ingest(sessions, tmp_path)
    async with sessions() as session:
        k = as_known_at(session, NOW)
        products = await k.products()
        for basin in await k.basins():
            a = await susceptibility.assess(k, basin, products)
            soil = [d for d in a.drivers if d.feature == "soil_saturation_percentile"]
            assert len(soil) == 1, basin.id
            assert soil[0].value is None and soil[0].unit == "pct"
            assert soil[0].direction == susceptibility.UNAVAILABLE_DIRECTION
            ref = a.refs[soil[0].prov]
            assert ref.source_kind is SourceKind.UNKNOWN
            assert "SNOTEL SMS" in ref.label and "cannot support a percentile" in ref.label
            assert ref.freshness.state.value == "missing"


async def test_the_soil_driver_survives_every_unknown_branch(sessions) -> None:
    """A surface that cannot be computed still has to say it has no soil number."""
    async with sessions() as session:
        k = as_known_at(session, NOW)
        products = await k.products()
        a = await susceptibility.assess(k, await k.basin("basin:green-duwamish"), products)
    assert a.surface.state is SurfaceLevel.UNKNOWN
    assert [d.feature for d in a.drivers] == ["soil_saturation_percentile"]
    assert a.drivers[0].value is None and a.drivers[0].prov in a.refs


@respx.mock
async def test_no_snow_driver_is_ever_scored(sessions, tmp_path) -> None:
    """Design §5 susceptibility 5 / HYDROLOGY §7: more SWE is not more risk."""
    _mock_usgs_stats()
    _mock_awdb()
    await _ingest(sessions, tmp_path)
    scored = {susceptibility.SCORED_DIRECTION, "increases_forcing", "decreases_forcing", "model_exceeds_official"}
    async with sessions() as session:
        k = as_known_at(session, NOW)
        products = await k.products()
        for basin in await k.basins():
            a = await susceptibility.assess(k, basin, products)
            snow = [d for d in a.drivers if "swe" in d.feature or "snotel" in d.feature]
            assert len(snow) == 2, basin.id
            for driver in snow:
                assert driver.direction == susceptibility.CONTEXT_DIRECTION
                assert driver.direction not in scored
            # the index is the flow percentile and nothing else
            assert a.surface.score == round(next(d.value for d in a.drivers if d.feature == "streamflow_doy_percentile") / 100.0, 4)


@respx.mock
async def test_regulated_basins_are_capped_and_the_skagit_reads_the_sauk(sessions, tmp_path) -> None:
    """Design §5 susceptibility 4."""
    _mock_usgs_stats()
    await _ingest(sessions, tmp_path, awdb=False)
    async with sessions() as session:
        k = as_known_at(session, NOW)
        products = await k.products()
        by_basin = {b.id: await susceptibility.assess(k, b, products) for b in await k.basins()}

    for basin_id in ("basin:green-duwamish", "basin:puyallup-white"):
        assert by_basin[basin_id].surface.confidence is ConfidenceLabel.LOW, basin_id
    assert by_basin["basin:cedar"].surface.confidence is not ConfidenceLabel.HIGH
    # nothing may exceed HIGH, and no basin may exceed its seeded ceiling
    async with sessions() as session:
        ceilings = {b.id: b.susceptibility_confidence_ceiling for b in (await session.execute(select(Basin))).scalars()}
    order = [c.value for c in (ConfidenceLabel.UNKNOWN, ConfidenceLabel.LOW, ConfidenceLabel.MODERATE, ConfidenceLabel.HIGH)]
    for basin_id, a in by_basin.items():
        assert order.index(a.surface.confidence.value) <= order.index(ceilings[basin_id]), basin_id

    skagit = by_basin["basin:skagit"]
    label = skagit.refs[skagit.surface.prov].label
    assert "12189500" in label, "the Skagit must SAY it read the Sauk, not the Mount Vernon outlet"
    assert "unregulated Sauk" in label  # the seeded note travels with the number
    # A CALENDAR SPAN IS NOT A LENGTH OF RECORD. Measured 2026-08-24 from the archived OGC
    # `daily` CSV: 12189500 carries approved daily means in 1911-1912, then nothing until 1928 —
    # 101 years with data inside a 116-year span. `end - begin + 1` counts the empty years too,
    # so no label may turn it into "116 years of record"; the depth claim is the sample size.
    for a in by_basin.values():
        text = a.refs[a.surface.prov].label
        assert "years of record" not in text, text
        assert "calendar years" in text and "values in the day-of-year window" in text, text


@respx.mock
async def test_a_climatology_disagreement_lowers_confidence_and_becomes_a_driver(sessions, tmp_path) -> None:
    """DATA_DOCTRINE §10: disagreement is reported, never averaged."""
    _mock_usgs_stats()
    await _ingest(sessions, tmp_path, awdb=False)
    async with sessions() as session:
        row = (await session.execute(
            select(DerivedFeature).where(DerivedFeature.feature == "streamflow_doy_percentile",
                                         DerivedFeature.scope_id == "station:usgs:12149000")
        )).scalar_one()
        values = dict(row.values_json)
        values["cross_check"] = {**values["cross_check"], "disagreement_fraction": 0.42, "threshold": 0.10}
        row.values_json = values
        row.quality = [*row.quality, "climatology_disagreement"]
        await session.flush()
        k = as_known_at(session, NOW)
        a = await susceptibility.assess(k, await k.basin("basin:snohomish-snoqualmie"), await k.products())
    assert a.surface.confidence is not ConfidenceLabel.HIGH  # ceiling is high; the disagreement drops it
    disagreement = [d for d in a.drivers if d.feature == "climatology_p50_disagreement"]
    assert len(disagreement) == 1 and disagreement[0].value == 42.0
    assert disagreement[0].direction == "lowers_confidence"


# --- F. the vocabulary the surface and the jobs must agree on --------------------------------


def test_the_surface_and_the_jobs_agree_on_the_feature_and_method_vocabulary() -> None:
    """cascade_hydrology must not import a provider package, so the coupling is TESTED."""
    assert susceptibility.CLIMATOLOGY_METHOD_ID == clim.METHOD_ID
    assert susceptibility.PUBLISHED_CLIMATOLOGY_METHOD_ID == clim.PUBLISHED_METHOD_ID
    assert susceptibility.PERCENTILE_FEATURE == stats_jobs.PERCENTILE_FEATURE
    assert susceptibility.CLIMATOLOGY_FEATURE == stats_jobs.CLIMATOLOGY_FEATURE
    assert susceptibility.METHOD_ID == stats_jobs.PERCENTILE_METHOD_ID == "method:susceptibility-index@0.1.0"
    assert susceptibility.SWE_FEATURE == awdb_normalize.SWE_FEATURE
    assert susceptibility.PRECIP_FEATURE == awdb_normalize.PRECIP_FEATURE
    assert susceptibility.SWE_METHOD_ID == awdb_normalize.SWE_METHOD_ID
    assert susceptibility.PRECIP_METHOD_ID == awdb_normalize.PRECIP_METHOD_ID
    assert susceptibility.CONTEXT_DIRECTION == awdb_normalize.CONTEXT_DIRECTION == "context_not_scored"


def test_the_band_table_is_monotone_and_uncalibrated() -> None:
    """Design §2.2 step 4: the exit test checks reproducibility, never that the bands are right."""
    order = [SurfaceLevel.LOW, SurfaceLevel.MODERATE, SurfaceLevel.HIGH, SurfaceLevel.VERY_HIGH]
    seen = [susceptibility.band(p) for p in range(0, 101)]
    assert [order.index(s) for s in seen] == sorted(order.index(s) for s in seen)
    assert susceptibility.band(24.9) is SurfaceLevel.LOW and susceptibility.band(25.0) is SurfaceLevel.MODERATE
    assert susceptibility.band(74.9) is SurfaceLevel.MODERATE and susceptibility.band(75.0) is SurfaceLevel.HIGH
    assert susceptibility.band(89.9) is SurfaceLevel.HIGH and susceptibility.band(90.0) is SurfaceLevel.VERY_HIGH
    assert susceptibility.METHOD_PARAMETERS["calibrated"] is False


def test_a_published_table_for_the_wrong_site_is_refused_rather_than_merged() -> None:
    """A cross-check must be the SAME gauge or it is not a cross-check."""
    stats = parse_nwis_stat_rdb((STATS / "stat_12189500.rdb").read_bytes())
    assert clim.published_climatology(stats, site=SAUK_SITE).ladders
    wrong = clim.published_climatology(stats, site=SKAGIT_SITE)
    assert wrong.ladders == {} and wrong.skipped["other_site"] == 366


@respx.mock
async def test_confidence_never_collapses_a_weak_answer_into_no_answer(sessions, tmp_path) -> None:
    """LOW is the floor while a value exists; UNKNOWN confidence means UNKNOWN state."""
    _mock_usgs_stats()
    await _ingest(sessions, tmp_path, awdb=False)
    async with sessions() as session:
        k = as_known_at(session, NOW)
        products = await k.products()
        computed = [await susceptibility.assess(k, b, products) for b in await k.basins()]
        stale = await susceptibility.assess(as_known_at(session, NOW + timedelta(days=5)), await k.basin("basin:skagit"), products)
    assert all(a.surface.confidence is not ConfidenceLabel.UNKNOWN for a in computed)
    assert all(a.surface.state is not SurfaceLevel.UNKNOWN for a in computed)
    assert stale.surface.state is SurfaceLevel.UNKNOWN and stale.surface.confidence is ConfidenceLabel.UNKNOWN


@respx.mock
async def test_every_provenance_kind_is_resolved_from_the_registry(sessions, tmp_path) -> None:
    """DATA_DOCTRINE §2: a source kind is looked up, never spelled out beside the value.

    The two deliberate exceptions are asserted as exceptions: the Cascade index is EXPERIMENTAL
    (a stricter badge than the registry's DERIVED, because the method has not passed hindcast
    evaluation — ADR-0008), and the soil ref is UNKNOWN because there is no source at all.
    """
    _mock_usgs_stats()
    _mock_awdb()
    await _ingest(sessions, tmp_path)
    async with sessions() as session:
        k = as_known_at(session, NOW)
        products = await k.products()
        a = await susceptibility.assess(k, await k.basin("basin:skagit"), products)
    assert susceptibility.resolved_source_kind("src:usgs-wdfn-ogc") is SourceKind.OBSERVED
    assert susceptibility.resolved_source_kind("src:nrcs-awdb") is SourceKind.OBSERVED
    assert susceptibility.resolved_source_kind("src:not-registered") is SourceKind.UNKNOWN
    for key, ref in a.refs.items():
        if ref.source_id == "src:cascade" and ref.method_id == susceptibility.METHOD_ID:
            assert ref.source_kind is SourceKind.EXPERIMENTAL, key
        elif key == "cascade-soil-unavailable":
            assert ref.source_kind is SourceKind.UNKNOWN, key
        else:
            assert ref.source_kind is susceptibility.resolved_source_kind(ref.source_id), key
    # and nothing in this surface may ever claim the authority of an official forecast
    assert all(r.source_kind is not SourceKind.OFFICIAL_FORECAST for r in a.refs.values())
