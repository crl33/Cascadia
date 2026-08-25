"""P3 stage-2 wiring: the three live surfaces as they leave `GET /viz/basins` (design §5, §6).

This is the exit test for the integration seam, and it is the only test that walks the whole
distance: real checked-in provider payloads -> the real ingest jobs -> `derived_feature` /
`forecast_run` rows -> `assemble.basin_envelope` -> the HTTP response -> contract validation.
Each surface has its own unit tests one layer down; what nobody could assert before Stage 2 is
that the feature ids, method ids, window labels and provenance keys the *writers* use are the
ones the *readers* ask for, and that the envelope's provenance refs all resolve once three
surfaces merge their drivers into one basin item.

Offline: SQLite + respx + the fixtures the surface builders captured. No network
(docs/TESTING.md §3). The knowledge clock is fixed, so nothing here depends on the weather.

The assertions that matter most are the ones about what the platform REFUSES to say:

- CRNW1 has no flow column in its official run, so `basin:snohomish-snoqualmie` reports
  agreement UNKNOWN with that reason. A fabricated comparison there would be a doctrine
  failure, not a bug.
- `model_probability` appears only where official **flow** thresholds exist (AUBW1, WRAW1).
- `soil_saturation_percentile` is present with `value: null` at every basin.
- Replayed to a knowledge time before ingestion, every surface is UNKNOWN with a reason that
  names the missing input — and never the pre-P3 "not implemented in the spike" sentence.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import json

import httpx
import pytest
import respx

from cascade_api.main import create_app
from cascade_contracts import ContractEnvelope, SourceKind
from cascade_contracts.visualization import AgreementLevel, SurfaceLevel
from cascade_core.db import create_schema
from cascade_core.fetch import ArchivingFetcher
from cascade_core.objectstore import LocalFilesystemStore
from cascade_core.registry import SRC_NWM
from cascade_core.seed import seed_all
from cascade_core.settings import Settings
from cascade_core.timeutils import utcnow
from cascade_hydrology import agreement as agreement_method
from cascade_hydrology import forcing as forcing_method
from cascade_hydrology import susceptibility as susceptibility_method
from cascade_providers_awdb import jobs as awdb_jobs
from cascade_providers_nbm import client as nbm_client
from cascade_providers_nbm import jobs as nbm_jobs
from cascade_providers_nwps import jobs as nwps_jobs
from cascade_providers_nwps.reaches_jobs import run_fetch_medium_range
from cascade_providers_usgs import stats_jobs
from cascade_worker.runtime import Runtime
from tests.conftest import FIXTURES, GEO

LIDS = ("RNTW1", "CRNW1", "MVEW1", "NKSW1", "AUBW1", "WRAW1")
REACHES = {
    "RNTW1": "24537890", "CRNW1": "23970199", "MVEW1": "24270288",
    "NKSW1": "23955772", "AUBW1": "23977634", "WRAW1": "23981235",
}
BASIN_OF_LID = {
    "RNTW1": "basin:cedar", "CRNW1": "basin:snohomish-snoqualmie", "MVEW1": "basin:skagit",
    "NKSW1": "basin:nooksack", "AUBW1": "basin:green-duwamish", "WRAW1": "basin:puyallup-white",
}
BASINS = tuple(BASIN_OF_LID.values())
#: Official flow thresholds exist at exactly these two points (design §3.1), so they are the
#: only basins where a counted member fraction is a statement the data supports.
FLOW_THRESHOLD_BASINS = {"basin:green-duwamish", "basin:puyallup-white"}

NBM_DIR = FIXTURES / "nbm"
NWM_DIR = FIXTURES / "nwm-via-nwps"
NWPS_DIR = FIXTURES / "nwps"
STATS_DIR = FIXTURES / "usgs_stats"
AWDB_DIR = FIXTURES / "awdb"

CYCLE = nbm_client.Cycle(2026, 8, 24, 12)
#: Retrieval clocks, each set to when that payload was really captured, so `available_at` and
#: freshness are computed from the same instants production would see.
T_OFFICIAL = datetime(2026, 8, 21, 15, 30, tzinfo=UTC)
T_SUSCEPTIBILITY = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)
T_NBM = datetime(2026, 8, 24, 22, 10, tzinfo=UTC)
T_NWM = datetime(2026, 8, 24, 22, 5, tzinfo=UTC)
#: The knowledge time everything is read at: after every ingest above.
AS_OF = datetime(2026, 8, 24, 23, 0, tzinfo=UTC)
#: A knowledge time before ANY of it — the replay boundary (design §5 forcing exit test 5).
BEFORE = datetime(2026, 8, 21, 12, 0, tzinfo=UTC)

QMD_URL = "https://nomads.ncep.noaa.gov/cgi-bin/filter_blend.pl"
DAILY_URL = "https://api.waterdata.usgs.gov/ogcapi/v0/collections/daily/items"
LATEST_URL = "https://api.waterdata.usgs.gov/ogcapi/v0/collections/latest-daily/items"
NWIS_STAT_URL = "https://waterservices.usgs.gov/nwis/stat/"
AWDB_STATIONS_URL = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/stations"
AWDB_DATA_URL = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/data"

SKAGIT_SITE, SAUK_SITE = "12200500", "12189500"


# ----------------------------------------------------------------------------- mocks


def _mock_nwps_gauges() -> None:
    """Official thresholds and the NWRFC stageflow forecast, from the spike fixtures."""
    for lid in LIDS:
        respx.get(f"https://api.water.noaa.gov/nwps/v1/gauges/{lid}").mock(
            return_value=httpx.Response(200, content=(NWPS_DIR / f"gauge_{lid}.json").read_bytes())
        )
        respx.get(f"https://api.water.noaa.gov/nwps/v1/gauges/{lid}/stageflow").mock(
            return_value=httpx.Response(200, content=(NWPS_DIR / f"stageflow_{lid}.json").read_bytes())
        )


def _mock_reaches() -> None:
    for lid, reach in REACHES.items():
        respx.get(f"https://api.water.noaa.gov/nwps/v1/reaches/{reach}/streamflow").mock(
            return_value=httpx.Response(
                200, content=(NWM_DIR / f"medium_range_{lid}.json").read_bytes(),
                headers={"content-type": "application/json"},
            )
        )


def _mock_nomads() -> None:
    """The NOMADS CGI keys off the `file` query parameter, exactly as the real service does."""
    qmd72 = (NBM_DIR / "qmd_f072_wa.grib2").read_bytes()
    core24 = (NBM_DIR / "core_f024_snowlvl_wa.grib2").read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        name = request.url.params["file"]
        body = core24 if ".core." in name else (qmd72 if ".f072." in name else None)
        if body is None:
            return httpx.Response(404, content=b"not found")
        return httpx.Response(200, content=body, headers={"content-type": "application/octet-stream"})

    respx.get(QMD_URL).mock(side_effect=handler)


def _mock_usgs_stats() -> None:
    """The Skagit's real record answers for 12200500, the Sauk's for the rest (plumbing, not
    hydrology — the hydrological assertions live in tests/unit/test_susceptibility.py)."""
    skagit = (STATS_DIR / "daily_12200500.csv").read_bytes()
    sauk = (STATS_DIR / "daily_12189500_2000.csv").read_bytes()
    stat_skagit = (STATS_DIR / "stat_12200500.rdb").read_bytes()
    stat_sauk = (STATS_DIR / "stat_12189500.rdb").read_bytes()

    def daily(request: httpx.Request) -> httpx.Response:
        site = request.url.params["monitoring_location_id"].removeprefix("USGS-")
        return httpx.Response(200, content=skagit if site == SKAGIT_SITE else sauk, headers={"content-type": "text/csv"})

    def stat(request: httpx.Request) -> httpx.Response:
        site = request.url.params["sites"]
        body = stat_skagit if site == SKAGIT_SITE else stat_sauk.replace(SAUK_SITE.encode(), site.encode())
        return httpx.Response(200, content=body, headers={"content-type": "text/plain"})

    respx.get(DAILY_URL).mock(side_effect=daily)
    respx.get(NWIS_STAT_URL).mock(side_effect=stat)
    respx.get(LATEST_URL).mock(
        return_value=httpx.Response(200, content=(STATS_DIR / "latest_daily_gauges.json").read_bytes(),
                                    headers={"content-type": "application/json"})
    )


def _mock_awdb() -> None:
    respx.get(AWDB_STATIONS_URL).mock(
        return_value=httpx.Response(200, content=(AWDB_DIR / "stations_wa_sntl.json").read_bytes(),
                                    headers={"content-type": "application/json"})
    )
    respx.get(AWDB_DATA_URL).mock(
        return_value=httpx.Response(200, content=(AWDB_DIR / "data_wteq_prec_puget.json").read_bytes(),
                                    headers={"content-type": "application/json"})
    )


# ----------------------------------------------------------------------------- fixture


def _fetcher(raw_dir, clock: datetime) -> ArchivingFetcher:
    return ArchivingFetcher(store=LocalFilesystemStore(raw_dir), user_agent="CascadiaPapsukkal/0.1 (test)", clock=lambda: clock)


async def _ingest_everything(settings: Settings) -> None:
    """Seed, then run each real ingest job once against the checked-in payloads."""
    rt = Runtime.build(settings, fetcher=_fetcher(settings.raw_dir, AS_OF), clock=lambda: AS_OF)
    try:
        await create_schema(rt.engine)
        with respx.mock:
            _mock_nwps_gauges()
            _mock_reaches()
            _mock_nomads()
            _mock_usgs_stats()
            _mock_awdb()
            async with rt.sessions() as s:
                await seed_all(s, geo_dir=settings.geo_dir, seed_file=settings.seed_file)
                await s.commit()
            async with rt.sessions() as s:
                official = _fetcher(settings.raw_dir, T_OFFICIAL)
                await nwps_jobs.run_fetch_thresholds(s, official)
                await nwps_jobs.run_fetch_forecast(s, official)
                await s.commit()
            async with rt.sessions() as s:
                await run_fetch_medium_range(s, _fetcher(settings.raw_dir, T_NWM))
                await s.commit()
            async with rt.sessions() as s:
                nbm = _fetcher(settings.raw_dir, T_NBM)
                # Masks first: without one for the live grid the NBM jobs refuse (scheduler.JOBS
                # encodes this same order, and tests/unit/test_worker_queue.py pins it).
                await nbm_jobs.run_build_grid_masks(s, nbm, geo_dir=GEO, cycle=CYCLE)
                await nbm_jobs.run_fetch_qmd(s, nbm, cycle=CYCLE, horizons=(72,))
                await nbm_jobs.run_fetch_core_snowlvl(s, nbm, cycle=CYCLE, horizons=(24,))
                await s.commit()
            async with rt.sessions() as s:
                usgs = _fetcher(settings.raw_dir, T_SUSCEPTIBILITY)
                await stats_jobs.run_build_climatology(s, usgs, now=T_SUSCEPTIBILITY)
                await stats_jobs.run_fetch_daily_percentile(s, usgs, now=T_SUSCEPTIBILITY)
                await awdb_jobs.run_fetch_snotel_context(s, usgs, now=T_SUSCEPTIBILITY)
                await s.commit()
    finally:
        await rt.engine.dispose()


@pytest.fixture(scope="module")
def ingested_settings(tmp_path_factory) -> Settings:
    """Ingest once for the whole module: exact basin-mask clipping and an 86-year climatology
    build are the expensive steps, and they are reference data in production too. Sync + one
    `asyncio.run` because the suite's fixture loop scope is per function."""
    root = tmp_path_factory.mktemp("p3-surfaces")
    settings = Settings(db_url=f"sqlite+aiosqlite:///{root}/p3.db", raw_dir=root / "raw", geo_dir=GEO)
    asyncio.run(_ingest_everything(settings))
    return settings


@pytest.fixture
async def ingested(ingested_settings: Settings):
    """A read-only Runtime over the ingested database; no test in this file writes to it."""
    rt = Runtime.build(ingested_settings, fetcher=_fetcher(ingested_settings.raw_dir, AS_OF), clock=lambda: AS_OF)
    yield rt
    await rt.engine.dispose()


async def _viz_basins(rt: Runtime, as_of: datetime) -> ContractEnvelope:
    app = create_app(rt.settings, engine=rt.engine)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/viz/basins", params={"as_of": as_of.isoformat().replace("+00:00", "Z")})
    assert r.status_code == 200, r.text
    return ContractEnvelope.model_validate(r.json())


# ----------------------------------------------------------------------------- tests


async def test_every_surface_computes_over_http_and_every_ref_resolves(ingested) -> None:
    """Design §5: no surface is UNKNOWN for a reason that is now implemented, and each traces."""
    env = await _viz_basins(ingested, AS_OF)
    items = {i.id: i for i in env.items}
    assert set(items) == set(BASINS)

    for basin_id, item in items.items():
        forcing, susceptibility = item.surfaces.forcing, item.surfaces.susceptibility

        # FORCING: banded from the 72-h basin-mean QPF of a real 12Z cycle.
        assert forcing.state is not SurfaceLevel.UNKNOWN and forcing.reason is None, basin_id
        assert forcing.horizon_h == 72 and forcing.experimental is True
        assert forcing.value is not None and forcing.value.unit == "mm" and forcing.score is not None
        # The spread keys say `pointwise`, because a basin mean of a per-cell percentile is not
        # a basin-scale percentile (design §1.4) — the single easiest overclaim to make here.
        assert forcing.spread and all(k.startswith("pointwise_p") for k in forcing.spread), forcing.spread
        assert env.provenance_refs[forcing.prov].source_kind is SourceKind.EXPERIMENTAL

        # SUSCEPTIBILITY: the day-of-year flow percentile at the basin's configured gauge.
        assert susceptibility.state is not SurfaceLevel.UNKNOWN and susceptibility.reason is None, basin_id
        assert susceptibility.horizon_h is None  # a present-state surface has no horizon
        assert susceptibility.value is not None and susceptibility.value.unit == "pct"
        assert 0.0 <= susceptibility.score <= 1.0 and susceptibility.experimental is True
        assert env.provenance_refs[susceptibility.prov].source_kind is SourceKind.EXPERIMENTAL

    # Every prov key on every driver and surface resolves — the envelope validator enforces it,
    # so reaching this line at all is the assertion; naming it keeps the intent visible.
    assert env.provenance_refs, "an envelope with computed surfaces must carry their refs"


async def test_the_qpf_is_modeled_and_the_assessment_is_experimental(ingested) -> None:
    """Design §5 forcing exit test 4: the model's number and Cascadia's judgement are two refs.

    NBM guidance is MODELED and is provenance-referenced as itself; the banding on top of it is
    a Cascadia Papsukkal method that has not passed hindcast evaluation, so it is EXPERIMENTAL.
    Collapsing the two would either lend the band table NOAA's authority or strip the QPF of it.
    """
    env = await _viz_basins(ingested, AS_OF)
    skagit = next(i for i in env.items if i.id == "basin:skagit")
    qpf = next(d for d in skagit.headline_drivers if d.feature.startswith("basin_qpf_"))
    assert env.provenance_refs[qpf.prov].source_kind is SourceKind.MODELED
    assert env.provenance_refs[qpf.prov].method_id == forcing_method.METHOD_BASIN_QPF
    assessment = env.provenance_refs[skagit.surfaces.forcing.prov]
    assert assessment.source_kind is SourceKind.EXPERIMENTAL
    assert assessment.method_id == forcing_method.METHOD_FORCING_ASSESSMENT
    assert "ASSUMPTION" in assessment.label  # the uncalibrated band table travels with the value


async def test_crnw1_agreement_stays_unknown_and_says_why(ingested) -> None:
    """Design §5 agreement exit test 1. This UNKNOWN is the CORRECT answer and must not regress.

    The NWRFC run at CRNW1 carries no usable flow column (every secondary value is the -9999
    sentinel) and NWM produces flow only. Comparing them would need a rating conversion, which
    v0 does not have — so the surface says exactly that instead of manufacturing a number.
    """
    env = await _viz_basins(ingested, AS_OF)
    items = {i.id: i for i in env.items}
    snoqualmie = items["basin:snohomish-snoqualmie"].surfaces.agreement
    assert snoqualmie.state is AgreementLevel.UNKNOWN
    assert snoqualmie.reason is not None and "no flow column" in snoqualmie.reason
    assert "rating conversion" in snoqualmie.reason

    for basin_id, item in items.items():
        if basin_id == "basin:snohomish-snoqualmie":
            continue
        state = item.surfaces.agreement
        assert state.state is not AgreementLevel.UNKNOWN, (basin_id, state.reason)
        assert state.prov and all(key in env.provenance_refs for key in state.prov)


async def test_no_model_run_is_ever_badged_as_the_official_forecast(ingested) -> None:
    """Design §5 agreement exit test 3, as a property over the whole document.

    The NWM ensemble and the NWRFC forecast now live in the same table and are shown side by
    side in the same basin item. The only thing keeping them apart is that `source_kind` is
    resolved from the registry, so this asserts the outcome rather than the mechanism.
    """
    env = await _viz_basins(ingested, AS_OF)
    model_refs = [ref for ref in env.provenance_refs.values() if ref.source_id == SRC_NWM]
    assert model_refs, "the agreement surface must carry the model's own provenance"
    assert all(ref.source_kind is SourceKind.MODELED for ref in model_refs)
    official = [ref for ref in env.provenance_refs.values() if ref.source_kind is SourceKind.OFFICIAL_FORECAST]
    assert official and all(ref.source_id != SRC_NWM for ref in official)


async def test_model_probability_is_counted_members_and_only_where_flow_thresholds_exist(ingested) -> None:
    """Design §5 agreement exit test 2, and DATA_DOCTRINE §9(b): k of n members, never a model.

    Where the official categories are defined in stage, ADR-0011 forbids inventing the flow
    equivalent — so the fraction is absent and the hazard's reason says so.
    """
    env = await _viz_basins(ingested, AS_OF)
    for item in env.items:
        hazard = item.surfaces.hazard
        if item.id in FLOW_THRESHOLD_BASINS:
            assert hazard.model_probability is not None, item.id
            members = hazard.model_probability["members"]
            assert members > 0 and hazard.model_probability["exceeding"] <= members
            assert hazard.model_probability["fraction"] == hazard.model_probability["exceeding"] / members
            assert hazard.model_probability["model"] == agreement_method.MODEL_LABEL
        else:
            assert hazard.model_probability is None, item.id
            assert hazard.reason and "No model exceedance fraction" in hazard.reason
        assert hazard.cascade_index is None  # never, until hindcast evaluation (ADR-0008)


async def test_headline_drivers_merge_into_one_ranked_list_with_units_and_provenance(ingested) -> None:
    """Three surfaces contribute drivers to one basin item; the merged list must read as one."""
    env = await _viz_basins(ingested, AS_OF)
    for item in env.items:
        drivers = item.headline_drivers
        assert len(drivers) >= 6, item.id
        assert [d.rank for d in drivers] == list(range(1, len(drivers) + 1)), item.id
        assert len({d.feature for d in drivers}) == len(drivers), item.id
        for d in drivers:
            assert d.unit, (item.id, d.feature)  # a number without its unit is not a number
            assert d.prov in env.provenance_refs, (item.id, d.prov)
        features = {d.feature for d in drivers}
        assert susceptibility_method.PERCENTILE_FEATURE in features
        assert any(f.startswith("basin_qpf_") for f in features)


async def test_soil_stays_unknown_visibly_and_snow_is_never_scored(ingested) -> None:
    """Design §5 susceptibility exit tests 3 and 5; HYDROLOGY §7 (more SWE is not more risk)."""
    env = await _viz_basins(ingested, AS_OF)
    for item in env.items:
        soil = next(d for d in item.headline_drivers if d.feature == susceptibility_method.SOIL_FEATURE)
        assert soil.value is None and soil.unit == "pct" and soil.direction == "unavailable"
        assert "SNOTEL SMS" in env.provenance_refs[soil.prov].label
        assert env.provenance_refs[soil.prov].source_kind is SourceKind.UNKNOWN
        for d in item.headline_drivers:
            if "swe" in d.feature or "snow" in d.feature or "precip" in d.feature:
                assert d.direction == "context_not_scored", (item.id, d.feature)


async def test_regulated_basins_are_capped_and_the_skagit_reads_the_sauk(ingested) -> None:
    """Design §5 susceptibility exit test 4: on a regulated reach flow is an operator decision."""
    env = await _viz_basins(ingested, AS_OF)
    items = {i.id: i for i in env.items}
    for basin_id in ("basin:green-duwamish", "basin:puyallup-white"):
        assert items[basin_id].surfaces.susceptibility.confidence == "low", basin_id
    skagit = items["basin:skagit"].surfaces.susceptibility
    assert SAUK_SITE in env.provenance_refs[skagit.prov].label
    assert skagit.confidence in ("moderate", "low")


async def test_replay_before_ingestion_is_unknown_with_a_reason_that_names_the_input(ingested) -> None:
    """The knowledge-time boundary, and the whole point of replacing the reason constants.

    Every surface goes UNKNOWN — but each says which input is missing, and none of them says
    "not implemented in the spike", which was true in the spike and is now false.
    """
    env = await _viz_basins(ingested, BEFORE)
    assert len(env.items) == 6
    for item in env.items:
        surfaces_ = item.surfaces
        assert surfaces_.forcing.state is SurfaceLevel.UNKNOWN
        assert surfaces_.forcing.reason == forcing_method.ForcingReason.NO_CYCLE
        assert surfaces_.susceptibility.state is SurfaceLevel.UNKNOWN
        assert surfaces_.susceptibility.reason in (
            susceptibility_method.STALE_REASON,
            susceptibility_method.no_climatology_reason(_gauge_of(item.id)),
        ), (item.id, surfaces_.susceptibility.reason)
        assert surfaces_.agreement.state is AgreementLevel.UNKNOWN
        assert surfaces_.agreement.reason == agreement_method.REASON_NO_OFFICIAL_RUN
        # The pre-P3 constants are gone; nothing may reintroduce them.
        for reason in (surfaces_.forcing.reason, surfaces_.susceptibility.reason, surfaces_.agreement.reason):
            assert "not implemented in the spike" not in reason
            assert "not ingested in the spike" not in reason
        # An UNKNOWN surface still explains itself in its provenance label, not only in `reason`.
        assert env.provenance_refs[surfaces_.forcing.prov].freshness.state == "missing"


def _gauge_of(basin_id: str) -> str:
    return {
        "basin:cedar": "station:usgs:12119000",
        "basin:snohomish-snoqualmie": "station:usgs:12149000",
        "basin:skagit": "station:usgs:12189500",
        "basin:nooksack": "station:usgs:12213100",
        "basin:green-duwamish": "station:usgs:12113000",
        "basin:puyallup-white": "station:usgs:12100490",
    }[basin_id]


async def test_the_document_validates_and_is_generated_at_the_read_clock(ingested) -> None:
    """A sanity rail: the envelope is the 1.2.0 contract and its as_of is the requested one."""
    env = await _viz_basins(ingested, AS_OF)
    assert env.contract == "BasinVisualizationState"
    assert env.as_of == AS_OF and env.time.valid == AS_OF
    assert env.generated_at <= utcnow()


async def test_the_explanation_link_the_contract_emits_actually_resolves(ingested) -> None:
    """`AgreementState.explanation_ref` is a promise; a 404 behind it is a broken one.

    The panel reduces the method record to one sentence and offers this link for the rest. If it
    does not resolve, the surface claims an explainability it does not have, and the band
    parameters, the comparison window and the untruncated quality text live nowhere a reader can
    reach (VISUAL_TRUTH_DOCTRINE §6).
    """
    as_of = AS_OF.isoformat().replace("+00:00", "Z")
    env = await _viz_basins(ingested, AS_OF)
    refs = [i.surfaces.agreement.explanation_ref for i in env.items if i.surfaces.agreement.explanation_ref]
    assert refs, "no basin offered an explanation link to check"

    app = create_app(ingested.settings, engine=ingested.engine)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        for ref in dict.fromkeys(refs):
            r = await c.get(ref, params={"as_of": as_of})
            assert r.status_code == 200, f"{ref} -> {r.status_code}: the contract offers a link that does not resolve"
            body = r.json()
            assert body["surface"] == "agreement" and body["method"], ref
            # the record states its own uncalibrated basis rather than presenting the bands as fact
            assert "assumption" in json.dumps(body["method"]).lower(), ref
        # an unknown basin is a 404, not an empty explanation
        assert (await c.get("/explanations/basin:nonesuch/agreement", params={"as_of": as_of})).status_code == 404
