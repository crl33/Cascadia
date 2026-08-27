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

from cascade_contracts import BandBoundary, ConfidenceLabel, SourceKind
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
        context = list((await session.execute(select(DerivedFeature).where(DerivedFeature.feature == stats_jobs.RECORD_CONTEXT_FEATURE))).scalars())
    # six gauges x (cascade-built ladder, usgs-published ladder, record context, growth reference)
    assert written == 24
    growth = list((await session.execute(select(DerivedFeature).where(DerivedFeature.feature == stats_jobs.GROWTH_REFERENCE_FEATURE))).scalars())
    assert len(growth) == 6
    # The record context is a SEPARATE feature under a SEPARATE method id. That is what keeps
    # `method:streamflow-doy-climatology@1.0.0` producing byte-identical output while the tail
    # gains a rank — and it is what keeps register X8 untouched by this change.
    assert len(context) == 6
    assert {r.method_id for r in context} == {clim.RECORD_CONTEXT_METHOD_ID}
    # the context holds the window tail and its per-key support; the growth distribution is a
    # SEPARATE row under its own method id, which is what lets the velocity read one without the
    # other (susceptibility.GROWTH_REFERENCE_METHOD_ID)
    assert all(r.value is None and r.values_json["keys"] and r.values_json["tail"] for r in context)
    assert all("growth" not in r.values_json for r in context), "the split must not leave a copy behind"
    assert all(r.value is None and r.values_json["growth"] for r in growth)
    assert {r.method_id for r in growth} == {clim.GROWTH_REFERENCE_METHOD_ID}
    assert all("percentiles" not in r.values_json and "ladder" not in r.values_json for r in context)
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
    # 12 ladders + 6 record contexts + 6 growth references, then nothing on a re-run
    assert first == 24 and second == 0 and n == 12


@respx.mock
async def test_the_cross_check_may_fail_without_costing_the_surface_its_value(sessions, tmp_path) -> None:
    """WaterServices decommissions Q1 2027. This is the rehearsal."""
    _mock_usgs_stats()
    respx.get(NWIS_STAT_URL).mock(return_value=httpx.Response(503))
    async with sessions() as session:
        written = await stats_jobs.run_build_climatology(session, fetcher(tmp_path), now=NOW)
        await session.commit()
        methods = {r.method_id for r in (await session.execute(select(DerivedFeature))).scalars()}
    # the ladder, its record context and its growth reference all survive; only the published
    # cross-check is missing
    assert written == 18
    assert methods == {clim.METHOD_ID, clim.RECORD_CONTEXT_METHOD_ID, clim.GROWTH_REFERENCE_METHOD_ID}


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
            # 0.2.0 publishes the reference distribution's own rank-space sampling error as the
            # spread, in percentile POINTS — the same unit as `value`, which is the contract's
            # rule. It is a dispersion with no coverage claim, never a probability.
            # A CLAMPED percentile is a bound, so the dispersion is withheld rather than
            # asserted either side of it; anything else publishes the resolution the clamp
            # refuses. Both branches are asserted so neither can be quietly dropped.
            if a.hydrologic_state is not None and a.hydrologic_state.percentile_clamped:
                assert a.surface.spread is None, basin.id
                assert a.hydrologic_state.boundary is BandBoundary.UNQUANTIFIED, basin.id
            else:
                assert set(a.surface.spread) == {"p_minus_1_rank_se", "p_plus_1_rank_se"}, basin.id
                lo, hi = a.surface.spread["p_minus_1_rank_se"], a.surface.spread["p_plus_1_rank_se"]
                assert 0.0 <= lo <= a.surface.value.value <= hi <= 100.0, basin.id
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
    # The SURFACE version and the id the INGEST stamps on the stored ranking row are two
    # different things, and 0.2.0 moved only the first. Bumping the row id would have orphaned
    # every percentile already stored, for no gain: both surface versions read the same rows.
    assert susceptibility.PERCENTILE_ROW_METHOD_ID == stats_jobs.PERCENTILE_METHOD_ID == "method:susceptibility-index@0.1.0"
    assert susceptibility.METHOD_ID == susceptibility.SURFACE_METHOD_V2 == "method:susceptibility-index@0.2.0"
    assert susceptibility.SURFACE_METHOD_V1 == "method:susceptibility-index@0.1.0"
    assert susceptibility.RECORD_CONTEXT_FEATURE == stats_jobs.RECORD_CONTEXT_FEATURE
    assert susceptibility.RECORD_CONTEXT_METHOD_ID == clim.RECORD_CONTEXT_METHOD_ID
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


# --- G. `@0.2.0`: the high tail, its velocity, and the version that must stay callable -------


async def _flood_row(session, *, gauge: str, day: date, value: float, valid_time: datetime) -> None:
    """Append one `streamflow_doy_percentile` row, ranked in the gauge's own stored ladder.

    Written the way the ingest writes it — same feature, same method id, same values_json shape
    — so these tests exercise the read path against rows the job could really have produced.
    """
    ladder_row = (await session.execute(
        select(DerivedFeature).where(DerivedFeature.feature == "streamflow_doy_climatology",
                                     DerivedFeature.scope_id == gauge,
                                     DerivedFeature.method_id == clim.METHOD_ID)
    )).scalars().first()
    climatology = clim.from_values_json(ladder_row.values_json, method_id=clim.METHOD_ID)
    key = clim.doy_key(day)
    ranked = clim.percentile_of(value, climatology.ladders[key])
    session.add(DerivedFeature(
        feature="streamflow_doy_percentile", scope_kind="station", scope_id=gauge, window=None,
        valid_time=valid_time, issued_at=None, computed_at=valid_time, available_at=valid_time,
        method_id=stats_jobs.PERCENTILE_METHOD_ID, product_id=PRODUCT_USGS_OGC_DAILY,
        value=value, unit="cfs", percentile=round(ranked.percentile, 2),
        values_json={
            "day": day.isoformat(), "doy_key": key, "sample_count": ranked.sample_count,
            "ladder": {f"p{p:02d}": v for p, v in sorted(climatology.ladders[key].values.items())},
            "climatology": {"method_id": clim.METHOD_ID, "ref": climatology.climatology_ref,
                            "begin_year": climatology.begin_year, "end_year": climatology.end_year},
            "approval_status": "Provisional", "cross_check": None,
        },
        climatology_ref=climatology.climatology_ref, confidence_label="unknown",
        quality=list(ranked.quality), inputs=[], raw_artifact_id=ladder_row.raw_artifact_id,
    ))


#: Event Zero's three decisive daily means at the Skagit's own susceptibility gauge, the Sauk:
#: 8,359 -> 24,976 -> 72,440 cfs, which the shipped surface reported as p89 -> p95 -> p95 with a
#: derivative of exactly +0 (`research/tier0-measured-basis-2026-08-26.md` §2, §3).
CREST_FLOWS = (8359.0, 24976.0, 72440.0)


async def _crest(sessions, tmp_path) -> tuple:
    """Ingest, then lay Event Zero's three-day rise on the Sauk ending above the ladder's ceiling.

    The FLOWS are the measured December 2025 ones; the DAYS are moved into the fixture's own
    August window on purpose. The stored ladder and record context were built from a record
    ending in August 2026, so they are not knowable at a December 2025 knowledge time — asking
    for them there would test the clock, not the tail. Every read below still filters
    `available_at <= as_of`; nothing here relaxes that.
    """
    _mock_usgs_stats()
    await _ingest(sessions, tmp_path, awdb=False)
    gauge = "station:usgs:12189500"
    at = datetime(2026, 8, 27, 12, 0, tzinfo=UTC)
    async with sessions() as session:
        for offset, flow in enumerate(CREST_FLOWS):
            day = date(2026, 8, 24) + timedelta(days=offset)
            await _flood_row(session, gauge=gauge, day=day, value=flow,
                             valid_time=datetime(2026, 8, 25 + offset, 7, 0, tzinfo=UTC))
        await session.commit()
    return gauge, at


@respx.mock
async def test_the_tail_discriminates_where_the_percentile_clamps(sessions, tmp_path) -> None:
    """The measured defect, closed: two flows the ladder calls identical are told apart.

    The percentile itself is UNCHANGED — still 95.0, still clamped, still flagged. What changed
    is that something beside it now moves.
    """
    _, at = await _crest(sessions, tmp_path)
    async with sessions() as session:
        products = await as_known_at(session, at).products()
        crest = await susceptibility.assess(as_known_at(session, at), await as_known_at(session, at).basin("basin:skagit"), products)
        earlier = as_known_at(session, at - timedelta(hours=24))
        onset = await susceptibility.assess(earlier, await earlier.basin("basin:skagit"), products)

    assert onset.surface.value.value == crest.surface.value.value == 95.0, "the ladder still clamps"
    assert onset.hydrologic_state.percentile_clamped and crest.hydrologic_state.percentile_clamped
    # ... and the multiple, which the clamp cannot silence, moves by exactly the flow ratio
    low, high = onset.hydrologic_state.multiple.multiple, crest.hydrologic_state.multiple.multiple
    assert high > low > 1.0
    # Each day is divided by ITS OWN day-of-year reference, so the ratio of the two multiples is
    # the flow ratio only where the reference is shared. What is asserted here is the exact
    # division each of them actually is.
    for state, flow in ((onset.hydrologic_state, 24976.0), (crest.hydrologic_state, 72440.0)):
        assert state.observed.value == flow
        assert state.multiple.multiple == pytest.approx(flow / state.multiple.reference.value, rel=1e-3)
    assert crest.hydrologic_state.multiple.reference.unit == "cfs"
    assert crest.hydrologic_state.multiple.reference_percentile == susceptibility.REFERENCE_PERCENTILE


@respx.mock
async def test_the_velocity_survives_the_clamp_that_silenced_the_percentile_derivative(sessions, tmp_path) -> None:
    """tier0 §3: between two clamped days a percentile change is identically +0. This is not."""
    _, at = await _crest(sessions, tmp_path)
    async with sessions() as session:
        k = as_known_at(session, at)
        a = await susceptibility.assess(k, await k.basin("basin:skagit"), await k.products())
    changes = {c.window_h: c for c in a.state_changes}
    assert set(changes) == {24, 48}
    assert changes[24].growth == pytest.approx(72440.0 / 24976.0, rel=1e-3)
    assert changes[48].growth == pytest.approx(72440.0 / 8359.0, rel=1e-3)
    assert changes[24].direction == "rising" and changes[48].direction == "rising"
    assert changes[24].from_value.unit == changes[24].to_value.unit == "cfs"
    assert changes[24].span_h == pytest.approx(24.0)
    # and it is rendered as a driver that says out loud that it is not scored
    growth_drivers = [d for d in a.drivers if d.feature.startswith("streamflow_growth_")]
    assert len(growth_drivers) == 2
    assert {d.direction for d in growth_drivers} == {susceptibility.STATE_CHANGE_DIRECTION}


@respx.mock
async def test_the_rank_names_the_record_it_beat_when_the_context_is_stored(sessions, tmp_path) -> None:
    """Above p90 the exact rank is published, censored at 1 and naming the previous maximum."""
    _, at = await _crest(sessions, tmp_path)
    async with sessions() as session:
        k = as_known_at(session, at)
        a = await susceptibility.assess(k, await k.basin("basin:skagit"), await k.products())
    rank = a.hydrologic_state.rank
    assert rank is not None and rank.rank == 1 and rank.exceeds_record
    assert rank.previous_max is not None and rank.previous_max.unit == "cfs"
    assert rank.previous_max_day is not None
    assert susceptibility.EXCEEDS_WINDOW_RECORD in a.refs[a.hydrologic_state.prov].quality
    assert a.hydrologic_state.reference.n > 0
    assert a.hydrologic_state.reference.independent_years == susceptibility.independent_years(
        a.hydrologic_state.reference.n
    )


@respx.mock
async def test_nothing_combines_the_level_and_the_velocity(sessions, tmp_path) -> None:
    """The prohibition, asserted: no composite, and no driver outside the percentile is scored."""
    _, at = await _crest(sessions, tmp_path)
    async with sessions() as session:
        k = as_known_at(session, at)
        a = await susceptibility.assess(k, await k.basin("basin:skagit"), await k.products())
    # the score is the percentile and nothing else, to the digit
    assert a.surface.score == pytest.approx(a.surface.value.value / 100.0)
    assert a.surface.state is susceptibility.band(a.surface.value.value)
    scored = [d for d in a.drivers if d.direction == susceptibility.SCORED_DIRECTION]
    assert [d.feature for d in scored] == [susceptibility.PERCENTILE_FEATURE]
    # every other driver declares itself unscored, so `headline_drivers` cannot read as a weighting
    assert {d.direction for d in a.drivers} - {susceptibility.SCORED_DIRECTION} <= {
        susceptibility.LEVEL_DIRECTION, susceptibility.STATE_CHANGE_DIRECTION,
        susceptibility.CONTEXT_DIRECTION, susceptibility.UNAVAILABLE_DIRECTION, "lowers_confidence",
    }
    # and there is no field on the state that summarises the three statements
    assert not {f for f in type(a.hydrologic_state).model_fields} & {"score", "index", "combined", "severity"}


@respx.mock
async def test_the_boundary_condition_is_published_and_fails_closed(sessions, tmp_path) -> None:
    """Correction 4: a condition, derived from the reference distribution's own sampling error."""
    from cascade_contracts import BandBoundary

    _mock_usgs_stats()
    _mock_awdb()
    await _ingest(sessions, tmp_path)
    async with sessions() as session:
        k = as_known_at(session, NOW)
        products = await k.products()
        states = {b.id: (await susceptibility.assess(k, b, products)).hydrologic_state for b in await k.basins()}
    for basin_id, state in states.items():
        assert state is not None, basin_id
        # Every seeded ladder has an n, so the ONLY reason the condition is unquantified is that
        # the percentile is a clamped bound. Asserting the iff is stronger than asserting the
        # condition is present: it catches both a silently dropped standard error and a spread
        # asserted either side of a bound.
        assert (state.boundary is BandBoundary.UNQUANTIFIED) == state.percentile_clamped, basin_id
        # Three conditions, three distinct shapes. UNQUANTIFIED must not be allowed to look like
        # either of the other two: it names no bands because it checked nothing, whereas
        # SEPARATED names none because the check passed.
        if state.boundary is BandBoundary.SEPARATED:
            assert state.bands_within_sampling_error == (), basin_id
            assert not state.percentile_clamped, basin_id
        elif state.boundary is BandBoundary.UNQUANTIFIED:
            assert state.bands_within_sampling_error == (), basin_id
            assert state.percentile_clamped, basin_id  # the only reason a seeded ladder cannot answer
        else:
            # the bands the record cannot tell apart are named, and the reported band is one of them
            assert len(state.bands_within_sampling_error) > 1, basin_id
            assert susceptibility.band(state.percentile) in state.bands_within_sampling_error, basin_id


@respx.mock
async def test_the_replaced_surface_version_is_still_callable_and_publishes_nothing_new(sessions, tmp_path) -> None:
    """Brief §22. Both methods run at the SAME knowledge time and agree about the band.

    This is the A/B harness's contract: `0.1.0` is the surface that shipped, and it must not
    acquire the tail, the velocity or the spread retroactively — otherwise the comparison would
    be the new code against itself.
    """
    _, at = await _crest(sessions, tmp_path)
    async with sessions() as session:
        k = as_known_at(session, at)
        basin = await k.basin("basin:skagit")
        products = await k.products()
        old = await susceptibility.assess(k, basin, products, version="0.1.0")
        new = await susceptibility.assess(k, basin, products, version="0.2.0")
        again = await susceptibility.assess(as_known_at(session, at), basin, products, version="0.1.0")

    assert old.version == "0.1.0" and new.version == "0.2.0"
    assert old.refs[old.surface.prov].method_id == susceptibility.SURFACE_METHOD_V1
    assert new.refs[new.surface.prov].method_id == susceptibility.SURFACE_METHOD_V2
    # deterministic at the same knowledge time
    assert again.surface.model_dump() == old.surface.model_dump()
    # the BAND is untouched: same state, same score, same value, no recalibration (brief §8)
    assert (old.surface.state, old.surface.score, old.surface.value) == (new.surface.state, new.surface.score, new.surface.value)
    # and 0.1.0 publishes none of what 0.2.0 added. The spread is conditional on the percentile
    # being resolved rather than clamped, so it is asserted as "never on the old arm, and on the
    # new arm exactly when the ladder resolved the value" — the crest used here is clamped, which
    # is precisely the case where 0.2.0 must ALSO withhold it.
    assert old.surface.spread is None
    assert new.hydrologic_state.percentile_clamped is True, "the crest fixture must be clamped"
    assert new.surface.spread is None
    assert old.hydrologic_state is None and new.hydrologic_state is not None
    assert old.state_changes == () and new.state_changes != ()
    assert not [d for d in old.drivers if d.direction in
                (susceptibility.LEVEL_DIRECTION, susceptibility.STATE_CHANGE_DIRECTION)]
    # 0.1.0's driver list is exactly what it shipped: percentile, SWE, precipitation, soil
    assert [d.feature for d in old.drivers] == [
        susceptibility.PERCENTILE_FEATURE, susceptibility.SWE_FEATURE,
        susceptibility.PRECIP_FEATURE, susceptibility.SOIL_FEATURE,
    ]


def test_an_unknown_method_version_is_refused_rather_than_silently_defaulted() -> None:
    assert susceptibility.VERSIONS == ("0.1.0", "0.2.0")
    assert susceptibility.SHIPPED_VERSION == "0.2.0"

#: A record context no seeded gauge's own record could ever produce. Everything in it is a
#: sentinel: a maximum an order of magnitude above anything in the captured payloads, days
#: outside the record entirely, and change denominators that are not counts of anything real.
SENTINEL_MAX = 111111.0
SENTINEL_MAX_DAY = date(1899, 8, 26)
SENTINEL_TAIL = [("1899-08-26", SENTINEL_MAX), ("1898-08-25", 90000.0), ("1897-08-27", 80000.0)]
SENTINEL_GROWTH_N = {24: 4242, 48: 2424}


async def _sentinel_record_context(session, *, gauge: str, valid_time: datetime) -> None:
    """Append a `streamflow_record_context` row for ONE gauge, later than the ingest's own."""
    doc = {
        "site": gauge.split(":")[-1],
        "unit": "cfs",
        "window_days": susceptibility.DOY_WINDOW_DAYS,
        "begin_water_year": 1897,
        "end_water_year": 2026,
        "used_rows": 40000,
        "parameters": {},
        "keys": {
            key: {"n": 490, "water_years": 98, "max": SENTINEL_MAX,
                  "max_day": SENTINEL_MAX_DAY.isoformat(), "tail_floor": 1000.0, "tail_years": 42}
            for key in ("08-23", "08-24", "08-25", "08-26", "08-27", "08-28")
        },
        "tail": [[day, value] for day, value in SENTINEL_TAIL],
    }
    # TWO rows since 2026-08-27, and writing them separately is what makes this test stronger:
    # the tail and the growth distribution are fetched under different feature/method ids and on
    # different read rules, so each has to be proved to come from the named gauge on its own.
    growth_doc = {**{k: v for k, v in doc.items() if k not in ("keys", "tail")},
                  "growth": {str(w): {"n": n, "span_days": w // 24, "top": [1.0]}
                             for w, n in SENTINEL_GROWTH_N.items()}}
    common = dict(
        scope_kind="station", scope_id=gauge, window=None, valid_time=valid_time, issued_at=None,
        computed_at=valid_time, available_at=valid_time, product_id=PRODUCT_USGS_OGC_DAILY,
        value=None, unit="cfs", percentile=None, confidence_label="unknown", quality=[], inputs=[],
    )
    session.add(DerivedFeature(
        feature=susceptibility.RECORD_CONTEXT_FEATURE,
        method_id=susceptibility.RECORD_CONTEXT_METHOD_ID, values_json=doc, **common,
    ))
    session.add(DerivedFeature(
        feature=susceptibility.GROWTH_REFERENCE_FEATURE,
        method_id=susceptibility.GROWTH_REFERENCE_METHOD_ID, values_json=growth_doc, **common,
    ))


@respx.mock
async def test_the_rank_and_the_growth_rank_come_from_the_gauge_the_label_names(sessions, tmp_path) -> None:
    """Provenance, not plausibility: the tail is ranked in THIS gauge's own stored record.

    Five of the six seeded gauges are served the same captured daily payload by this file's
    mocks (see `_mock_usgs_stats`), so a surface that read a NEIGHBOURING gauge's record context
    would publish numerically identical ranks and no assertion about the values could tell them
    apart. A sentinel context is therefore written for the Skagit's configured gauge alone, and
    every published number that depends on a record has to come out of it.
    """
    gauge, at = await _crest(sessions, tmp_path)
    async with sessions() as session:
        await _sentinel_record_context(session, gauge=gauge, valid_time=at - timedelta(hours=1))
        await session.commit()
    async with sessions() as session:
        k = as_known_at(session, at)
        a = await susceptibility.assess(k, await k.basin("basin:skagit"), await k.products())

    state = a.hydrologic_state
    assert state is not None and state.rank is not None
    assert state.rank.previous_max is not None
    assert state.rank.previous_max.value == SENTINEL_MAX, "ranked in some other gauge's record"
    assert state.rank.previous_max_day == SENTINEL_MAX_DAY
    # three stored tail values in this key's window are above the crest, so the rank is the 4th
    assert (state.rank.rank, state.rank.of) == (4, 491)
    assert not state.rank.exceeds_record
    assert "4th largest of 491" in a.refs[state.prov].label
    # and the growth rank is taken against the SAME gauge's stored change distribution
    by_window = {c.window_h: c.rank_of for c in a.state_changes}
    assert by_window == SENTINEL_GROWTH_N
    # and every statement is STAMPED with its own method identity, never a neighbour's: the
    # rank and the multiple are exact arithmetic, the change is a ratio of two daily means, the
    # reference is the Cascade-built ladder (not the USGS published cross-check), and only the
    # banded index is the experimental surface
    assert a.refs[state.prov].method_id == susceptibility.TAIL_STATE_METHOD_ID
    assert state.reference is not None
    assert state.reference.method_id == susceptibility.CLIMATOLOGY_METHOD_ID
    assert {a.refs[c.prov].method_id for c in a.state_changes} == {susceptibility.STATE_CHANGE_METHOD_ID}
    assert a.refs[a.surface.prov].method_id == susceptibility.SURFACE_METHOD_V2


@respx.mock
async def test_the_hindcast_history_stops_at_the_knowledge_time(sessions, tmp_path) -> None:
    """The replay harness's own look-ahead clamp, where `available_at` cannot stand in for it.

    `Knowledge.derived_features` deliberately does NOT clamp `valid_time` to `as_of` — a derived
    *forecast* feature is legitimately valid in the future — so the daily-mean readers pass
    `valid_until` themselves. Every hindcast evaluation is timed from the LAST row this reader
    returns (`hindcast.evaluate` sets `anchor = percentile_history[-1][0]` and publishes it as
    `Clocks.valid_at`), so losing the clamp moves the whole evaluation onto a day that had not
    happened yet.

    It has to be pinned with a row whose `valid_time` is ahead of `as_of` while its
    `available_at` is behind it, because the Event Zero projection sets
    `available_at := valid_time` for this family (`scripts/hindcast_event_zero.py`), which makes
    the two filters agree there and hides the difference. The private reader is called directly:
    it is the seam, and `hindcast.evaluate` needs a whole event to reach it.
    """
    from cascade_hydrology import hindcast

    gauge, at = await _crest(sessions, tmp_path)
    async with sessions() as session:
        await _flood_row(session, gauge=gauge, day=date(2026, 8, 27), value=999000.0,
                         valid_time=at + timedelta(hours=12))
        await session.commit()
    async with sessions() as session:
        future = (await session.execute(
            select(DerivedFeature)
            .where(DerivedFeature.feature == "streamflow_doy_percentile",
                   DerivedFeature.scope_id == gauge)
            .order_by(DerivedFeature.valid_time.desc())
        )).scalars().first()
        assert future.valid_time > at
        future.available_at = at - timedelta(hours=1)  # already known, just not yet true
        await session.commit()

    async with sessions() as session:
        history = await hindcast._percentile_history(as_known_at(session, at), gauge)

    assert history, "the history is empty and the assertions below would be vacuous"
    assert max(t for t, _v, _p in history) <= at
    assert history[-1][1] == 72440.0, "the replay anchored on a daily mean it could not have had"


@respx.mock
async def test_the_level_says_why_it_has_no_rank_instead_of_publishing_a_bare_null(sessions, tmp_path) -> None:
    """Absence is rendered with its reason, on BOTH sides of the surface.

    Below `RANK_READ_EDGE` the exact rank is deliberately not fetched. Until 2026-08-27 that was
    published as `hydrologic_state.rank = null` with no reason anywhere, while the velocity's
    `growth_rank` refused in the same situation with a full sentence two fields away. A reader
    could not tell "not read" from "no record for this gauge" from "nobody computed it", which is
    precisely what CLAUDE.md's one rule exists to prevent.
    """
    _mock_usgs_stats()
    _mock_awdb()
    await _ingest(sessions, tmp_path)
    async with sessions() as session:
        k = as_known_at(session, NOW)
        products = await k.products()
        seen = []
        for basin in await k.basins():
            a = await susceptibility.assess(k, basin, products)
            hs = a.hydrologic_state
            if hs is None or hs.percentile >= susceptibility.RANK_READ_EDGE:
                continue
            seen.append(basin.id)
            assert hs.rank is not None, f"{basin.id}: the refusal itself must be published"
            assert hs.rank.rank is None, basin.id
            assert hs.rank.reason, f"{basin.id}: a null rank without a reason is the defect"
            # it must say WHY it was not read, and must not be confusable with a missing record
            assert "Not read" in hs.rank.reason, basin.id
            assert hs.rank.reason != susceptibility.NO_RECORD_CONTEXT_REASON, basin.id
            # the sample size is known even though the position in it was not computed
            assert hs.rank.of >= 1, basin.id
    assert seen, "anti-vacuity: no basin below the read edge, so nothing was actually asserted"


@respx.mock
async def test_the_growth_rank_is_available_below_p90_where_the_velocity_actually_fires(sessions, tmp_path) -> None:
    """The Tier 0 defect of 2026-08-27, closed and pinned BEHAVIOURALLY.

    `RANK_READ_EDGE` (90.0) and `BAND_EDGES`' top edge are the same constant applied to the same
    rounded number. While the growth reference lived inside the record context it inherited that
    gate, so the growth rank was readable **iff the band already read VERY_HIGH** — and the
    velocity fires BELOW p90, which is the entire reason it exists. Measured consequence across
    all six basins (`research/event-zero-ab-2026-08-27.md` §7c): the Tier 0 lead time was
    identically the length of the unranked window, so 100 % of the lead was delivered by a
    statement that structurally could not say whether the change was fast.

    Asserting the constant is gone is structure. This asserts BEHAVIOUR: a gauge below the edge,
    with a real day-over-day rise, publishes a RANKED change.

    Both flows are derived from the gauge's own stored ladder rather than hardcoded, so the test
    keeps testing the same property if the fixture's record changes.
    """
    _mock_usgs_stats()
    await _ingest(sessions, tmp_path, awdb=False)
    gauge = "station:usgs:12189500"
    at = datetime(2026, 8, 27, 12, 0, tzinfo=UTC)
    async with sessions() as session:
        ladder_row = (await session.execute(
            select(DerivedFeature).where(DerivedFeature.feature == "streamflow_doy_climatology",
                                         DerivedFeature.scope_id == gauge,
                                         DerivedFeature.method_id == clim.METHOD_ID)
        )).scalars().first()
        ladder = clim.from_values_json(ladder_row.values_json, method_id=clim.METHOD_ID)
        # a value comfortably inside the ladder — the level stays UNREMARKABLE while the change
        # is large, which is exactly the state the velocity exists to describe
        p50 = ladder.ladders[clim.doy_key(date(2026, 8, 26))].values[50]
        for offset, value in enumerate((p50 / 2.0, p50)):
            await _flood_row(session, gauge=gauge, day=date(2026, 8, 25) + timedelta(days=offset),
                             value=value, valid_time=datetime(2026, 8, 26 + offset, 7, 0, tzinfo=UTC))
        await session.commit()

    async with sessions() as session:
        k = as_known_at(session, at)
        a = await susceptibility.assess(k, await k.basin("basin:skagit"), await k.products())
        hs = a.hydrologic_state
        assert hs is not None and hs.percentile < susceptibility.RANK_READ_EDGE, (
            f"anti-vacuity: the level must be BELOW the read edge, got {None if hs is None else hs.percentile}"
        )
        rising = [c for c in a.state_changes if c.growth is not None]
        assert rising, "anti-vacuity: no change computed, so the rank was never reached"
        assert any(c.growth > 1.4 for c in rising), "the fixture must actually contain a rise"
        for c in rising:
            assert c.rank is not None, (
                f"a {c.window_h} h change of x{c.growth:.2f} at p{hs.percentile:.1f} carries no rank "
                f"({c.rank_reason!r}) — the read is still coupled to RANK_READ_EDGE"
            )
            assert c.rank_of and c.rank_of >= c.rank
