"""Source/product registry ids and cadences (docs/DOMAIN_MODEL.md §2.2, docs/DATA_DOCTRINE.md §5).

Ids are the vocabulary shared by providers, hydrology, the API and /system/health. Cadence and
grace seconds are the seed values; the SourceProduct rows are what freshness is computed from.

`JOBS` is the job catalogue in the same vocabulary: name, provider, source, the products each
job writes, cadence. `/system/health` is derived from it rather than from a hand-kept list, so a
newly registered job is covered the moment it exists (see `JobSpec`).

`kind` here is the ONLY place a source's SourceKind is declared. Nothing downstream may hardcode
one: an adapter, an assembler or a ProvenanceRef resolves it by looking the product's source up
here (or in the seeded `data_source` row), so a model product can never be badged as an official
forecast by accident (docs/DATA_DOCTRINE.md §2, p3-surfaces-design §3.4 defect 2).

Cadence/grace for the P3 additions come from docs/DATA_SOURCES.md rows W2 (NBM), H6/H3 (NWM via
NWPS), H2 (USGS OGC) and S1 (AWDB), and were re-measured live in
docs/research/p3-surfaces-design-2026-08-24.md §1.1 (NBM qmd observed at cycle + 7 h 16 m,
core at cycle + 42–44 m).
"""

from __future__ import annotations

from dataclasses import dataclass

SRC_USGS = "src:usgs-nwis-iv"
SRC_NWPS = "src:nwps-v1"
SRC_NWPS_HEFS = "src:nwps-hefs-v1"
SRC_CASCADE = "src:cascade"
SRC_NWS_AFOS = "src:nws-afos"
# P3 additions (p3-surfaces-design-2026-08-24 §1.6, §2.1, §3.4).
SRC_NBM = "src:nbm-v5"
SRC_NWM = "src:nwm-v3.1"
SRC_USGS_OGC = "src:usgs-wdfn-ogc"
SRC_USGS_STATS = "src:usgs-wdfn-statistics"  # RETIRED 2026-08-27; historical rows only
SRC_USGS_NORMALS = "src:usgs-wdfn-normals"
SRC_AWDB = "src:nrcs-awdb"
SRC_MRMS = "src:mrms"
SRC_NWS_API = "src:nws-api"

PRODUCT_USGS_IV = "product:usgs-iv"
PRODUCT_NWPS_FORECAST = "product:nwps-forecast"
PRODUCT_HEFS_ENSEMBLE = "product:nwps-hefs-ensemble"
PRODUCT_HEFS_QUANTILES = "product:nwps-hefs-quantiles"
PRODUCT_NWPS_THRESHOLDS = "product:nwps-thresholds"
PRODUCT_NWS_FLS_CREST = "product:nws-fls-crest"
# P3 additions.
PRODUCT_NBM_QMD = "product:nbm-v5-qmd"
PRODUCT_NBM_CORE = "product:nbm-v5-core"
PRODUCT_NWM_MR = "product:nwm-mr-via-nwps"
PRODUCT_USGS_OGC_DAILY = "product:usgs-ogc-daily"
PRODUCT_USGS_DAILY_STATS = "product:usgs-daily-stats"  # RETIRED 2026-08-27; historical rows only
PRODUCT_USGS_DOY_NORMALS = "product:usgs-doy-normals"
PRODUCT_AWDB_DAILY = "product:awdb-snotel-daily"
PRODUCT_AWDB_STATIONS = "product:awdb-stations"
PRODUCT_MRMS_QPE = "product:mrms-qpe-01h-pass2"
PRODUCT_MRMS_GAUGEINFL = "product:mrms-gaugeinfl-01h-pass2"
PRODUCT_NWS_ALERTS = "product:nws-api-alerts-active"

SOURCES: tuple[dict[str, str], ...] = (
    {"id": SRC_USGS, "authority": "U.S. Geological Survey", "kind": "OBSERVED", "base_url": "https://api.waterdata.usgs.gov/ogcapi/v0/collections/continuous/items", "docs_url": "https://api.waterdata.usgs.gov/ogcapi/v0/openapi?f=html"},
    {"id": SRC_NWPS, "authority": "NOAA National Weather Service (NWPS)", "kind": "OFFICIAL_FORECAST", "base_url": "https://api.water.noaa.gov/nwps/v1/", "docs_url": "https://api.water.noaa.gov/nwps/v1/docs/"},
    # A SEPARATE source on the same host, deliberately. HEFS is an NWRFC ensemble service with
    # its own API, its own ~10-day retention and its own experimental status; folding it into
    # `src:nwps-v1` would let an experimental ensemble inherit the official forecast's
    # source_kind, which is the exact confusion DATA_SOURCES H4 warns about. Its members stay
    # MODELED until ROADMAP Phase 5 rules on official probabilities (DATA_DOCTRINE §9(a)).
    {"id": SRC_NWPS_HEFS, "authority": "NOAA NWS Office of Water Prediction / NWRFC (HEFS, EXPERIMENTAL — not supported 24/7 and may be modified without advance notice)", "kind": "MODELED", "base_url": "https://api.water.noaa.gov/hefs/v1/", "docs_url": "https://api.water.noaa.gov/hefs/v1/docs/"},
    {"id": SRC_CASCADE, "authority": "Cascadia Papsukkal", "kind": "DERIVED", "base_url": "", "docs_url": ""},
    {"id": SRC_NWS_AFOS, "authority": "NOAA NWS (AFOS text via IEM archive)", "kind": "OFFICIAL_FORECAST", "base_url": "https://mesonet.agron.iastate.edu/api/1/", "docs_url": "https://mesonet.agron.iastate.edu/api/1/docs"},
    # NBM is calibrated blended guidance, never the official forecast (DATA_SOURCES W2).
    {"id": SRC_NBM, "authority": "NOAA/NWS Meteorological Development Laboratory (National Blend of Models v5.0, via NODD/NOMADS)", "kind": "MODELED", "base_url": "https://nomads.ncep.noaa.gov/cgi-bin/filter_blend.pl", "docs_url": "https://vlab.noaa.gov/web/mdl/nbm-versions"},
    # NWM is an independent model, not the NWRFC forecast; v0 reads it through the NWPS
    # /reaches JSON API rather than the CONUS NetCDF (design §3.1).
    {"id": SRC_NWM, "authority": "NOAA/NWS Office of Water Prediction (National Water Model v3.1), served via NOAA NWPS", "kind": "MODELED", "base_url": "https://api.water.noaa.gov/nwps/v1/", "docs_url": "https://api.water.noaa.gov/nwps/v1/docs/"},
    {"id": SRC_USGS_OGC, "authority": "U.S. Geological Survey Water Data for the Nation (OGC API-Features)", "kind": "OBSERVED", "base_url": "https://api.waterdata.usgs.gov/ogcapi/v0/", "docs_url": "https://api.waterdata.usgs.gov/docs/ogcapi/migration/"},
    # Published day-of-year statistics: computed by the measuring authority from its own
    # approved measurements, so OBSERVED by the same rule DATA_DOCTRINE §2 applies to radar
    # QPE ("observed-derived ... tagged OBSERVED with a method"). It is NOT DERIVED: DERIVED
    # means computed by Cascadia Papsukkal. The Cascade-built climatology is the DERIVED one,
    # is stored separately, and the two are never averaged (design §2.2 step 2).
    {"id": SRC_USGS_STATS, "authority": "U.S. Geological Survey (published daily statistics; USGS states these may not match official USGS publications)", "kind": "OBSERVED", "base_url": "https://waterservices.usgs.gov/nwis/stat/", "docs_url": "https://waterservices.usgs.gov/docs/statistics/"},
    # The successor, on the host Cascadia already depends on. NOT the same numbers as the
    # retired nwis/stat source and deliberately not the same id: it computes over a different
    # period of record (up to 26 more years) and publishes no begin/end year at all, so p50
    # disagrees with nwis/stat past the 10% cross-check threshold at 12113000. ADR-0015 kept
    # ONE product across the instantaneous transports because parity was measured exact; the
    # opposite finding here is why this gets its own identity
    # (docs/research/nwis-stat-successor-2026-08-27.md §4, §6).
    {"id": SRC_USGS_NORMALS, "authority": "U.S. Geological Survey Water Data for the Nation (published day-of-year normals; USGS states these may not match official USGS publications)", "kind": "OBSERVED", "base_url": "https://api.waterdata.usgs.gov/statistics/v0/", "docs_url": "https://api.waterdata.usgs.gov/docs/statistics/"},
    {"id": SRC_AWDB, "authority": "USDA NRCS National Water and Climate Center (AWDB: SNOTEL/SNOLITE/SCAN)", "kind": "OBSERVED", "base_url": "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/", "docs_url": "https://wcc.sc.egov.usda.gov/awdbRestApi/v3/api-docs"},
    # OBSERVED with method radar_qpe (DATA_DOCTRINE §2): computed by the measuring authority
    # from radar+gauge+model blending, the same rule that classes the published day-of-year
    # statistics. The gauge-influence covariate rides the same source: it is NSSL's own
    # statement about its own estimate, not a Cascadia judgement.
    {"id": SRC_MRMS, "authority": "NOAA NSSL/NCEP Multi-Radar Multi-Sensor (MRMS) via NODD", "kind": "OBSERVED", "base_url": "https://noaa-mrms-pds.s3.amazonaws.com/", "docs_url": "https://www.nssl.noaa.gov/projects/mrms/"},
    {"id": SRC_NWS_API, "authority": "NOAA National Weather Service API (CAP alerts, WFO products)", "kind": "OFFICIAL_FORECAST", "base_url": "https://api.weather.gov/", "docs_url": "https://www.weather.gov/documentation/services-web-api"},
)

PRODUCTS: tuple[dict[str, object], ...] = (
    # ONE product across both transports, decided on measured parity (ADR-0015): the observation
    # is the same authoritative USGS instantaneous measurement whether it arrived over NWIS IV or
    # the OGC API, and a second product id would fragment the series, the freshness anchor and
    # every downstream read for a difference that is not scientific. WHICH transport supplied a
    # given row is answered per row by `observation.raw_artifact_id -> raw_artifact.request_url`.
    # The id string still says "iv" because renaming it would orphan every stored row's FK; it is
    # historical, and the label below names the transport actually in use.
    {"id": PRODUCT_USGS_IV, "source_id": SRC_USGS, "label": "USGS instantaneous values (stage 00065, discharge 00060) via the Water Data OGC API `continuous` collection; NWIS IV until 2026-08-27", "variables": ["stage", "flow"], "expected_cadence_seconds": 900, "grace_seconds": 4500},
    {"id": PRODUCT_NWPS_FORECAST, "source_id": SRC_NWPS, "label": "NWRFC official river forecast via NOAA NWPS", "variables": ["stage", "flow"], "expected_cadence_seconds": 86400, "grace_seconds": 64800},
    # Daily at 12Z, published ~15:06-15:49Z, and the provider keeps only ~10 days (FACT,
    # DATA_SOURCES H4). The grace is PT18H as documented; the retention is the reason the job
    # exists at all, so a stale reading here means history is being lost, not merely delayed.
    {"id": PRODUCT_HEFS_ENSEMBLE, "source_id": SRC_NWPS_HEFS, "label": "NWRFC HEFS ensemble streamflow members (MEFP, 45 traces, QINE in CFS) via the NWPS HEFS API", "variables": ["flow"], "expected_cadence_seconds": 86400, "grace_seconds": 64800},
    {"id": PRODUCT_HEFS_QUANTILES, "source_id": SRC_NWPS_HEFS, "label": "NWRFC HEFS published exceedance quantiles (the provider's own, never Cascade-derived)", "variables": ["flow"], "expected_cadence_seconds": 86400, "grace_seconds": 64800},
    {"id": PRODUCT_NWPS_THRESHOLDS, "source_id": SRC_NWPS, "label": "Official NWS flood categories (NWPS)", "variables": ["threshold"], "expected_cadence_seconds": 21600, "grace_seconds": 21600},
    {"id": PRODUCT_NWS_FLS_CREST, "source_id": SRC_NWS_AFOS, "label": "NWRFC crest via WFO FLW/FLS text (reconstructed; 6-hourly hydrograph lost)", "variables": ["stage", "flow"], "expected_cadence_seconds": 21600, "grace_seconds": 43200},
    # PT6H / PT8H: qmd runs only for the 00/06/12/18Z cycles and lands ~7 h 20 m after the
    # cycle (design §1.1, measured). A displayed QPF percentile can legitimately be 7-13 h old
    # and the freshness badge must say so rather than the grace hiding it.
    {"id": PRODUCT_NBM_QMD, "source_id": SRC_NBM, "label": "NBM v5.0 QPF percentiles (qmd, WA subset via NOMADS filter_blend.pl)", "variables": ["precip_accum"], "expected_cadence_seconds": 43200, "grace_seconds": 32400},  # 12-hourly: only 00Z/12Z carry the 0-N day cumulative windows (client.QMD_CYCLE_HOURS)
    # PT6H / PT8H, matching qmd — NOT the PT1H at which NOAA publishes `core`. Freshness is
    # computed against the anchor Cascade STORES, and `nbm.fetch_core_snowlvl` runs 6-hourly and
    # selects its cycle with `latest_qmd_cycle` (7.5 h latency), so the stored anchor is never
    # younger than 7.5 h and never older than ~13.5 h. Against a PT1H cadence that is stale on
    # every cycle: measured 2026-08-25 on a fresh database with all ten jobs green,
    # `/system/health` answered `degraded` naming this product alone, 47,760 s old against a
    # 3,600 s cadence (pg-migration-verification-2026-08-24 §P3.9). A health endpoint that is
    # degraded whatever happens hides a real failure exactly as well as one that is always ok.
    {"id": PRODUCT_NBM_CORE, "source_id": SRC_NBM, "label": "NBM v5.0 core, snow-level percentiles (WA subset via NOMADS filter_blend.pl)", "variables": ["snow_level"], "expected_cadence_seconds": 21600, "grace_seconds": 28800},
    # PT6H / PT8H: medium range runs 00/06/12/18Z. Member count is read from the payload,
    # never assumed (design §7 item 4).
    # Grace covers the publication latency: the freshest cycle obtainable is already that old,
    # so too tight a grace makes "stale" unreachable and /system/health reads degraded on a
    # healthy system. MEASURED 2026-08-27 against NWPS /reaches (the channel this product is
    # fetched from, NOT the S3 NetCDF channel DATA_SOURCES H6 times at ~6.5 h): the 00Z cycle
    # was absent at +8.23 h and present at +8.48 h. With the cron at +8.75 h the held cycle
    # reaches 14.75 h before the next run, so 6 h cadence + 12 h grace = 18 h covers it.
    {"id": PRODUCT_NWM_MR, "source_id": SRC_NWM, "label": "NWM v3.1 medium-range ensemble by reach via NWPS /reaches (members, never blended with the official forecast)", "variables": ["flow"], "expected_cadence_seconds": 21600, "grace_seconds": 43200},
    # P1D / PT36H (DATA_SOURCES H2). A daily mean older than 48 h makes the susceptibility
    # surface UNKNOWN rather than falling back to the instantaneous value (design §2.2).
    {"id": PRODUCT_USGS_OGC_DAILY, "source_id": SRC_USGS_OGC, "label": "USGS daily mean discharge (OGC API daily/latest-daily, 00060 statistic 00003)", "variables": ["flow"], "expected_cadence_seconds": 86400, "grace_seconds": 129600},
    # Recomputed annually (design §2.2 step 1); grace P30D. Effectively static reference data.
    # RETIRED 2026-08-27. Kept registered so historical rows keep a valid product_id and their
    # provenance still resolves; no job writes it, so PRODUCT_WRITERS drops it and
    # /system/health stops expecting it to arrive.
    {"id": PRODUCT_USGS_DAILY_STATS, "source_id": SRC_USGS_STATS, "label": "USGS published day-of-year discharge statistics (nwis/stat, approved daily means) — RETIRED 2026-08-27, superseded by product:usgs-doy-normals", "variables": ["flow"], "expected_cadence_seconds": 31536000, "grace_seconds": 2592000},
    {"id": PRODUCT_USGS_DOY_NORMALS, "source_id": SRC_USGS_NORMALS, "label": "USGS published day-of-year discharge normals (OGC statistics observationNormals, 00060 statistic 00003)", "variables": ["flow"], "expected_cadence_seconds": 31536000, "grace_seconds": 2592000},
    # P1D / PT36H (DATA_SOURCES S1, doctrine defaults). SNOTEL SWE and precipitation are
    # CONTEXT drivers only: more SWE is not more risk (HYDROLOGY §7), so nothing here is scored.
    {"id": PRODUCT_AWDB_DAILY, "source_id": SRC_AWDB, "label": "SNOTEL daily values (WTEQ, PREC) with per-value median, point network", "variables": ["swe", "precip_accum"], "expected_cadence_seconds": 86400, "grace_seconds": 129600},
    {"id": PRODUCT_AWDB_STATIONS, "source_id": SRC_AWDB, "label": "AWDB station metadata (triplet, HUC, elevation, station elements)", "variables": ["metadata"], "expected_cadence_seconds": 604800, "grace_seconds": 604800},
    # Hourly, ~57 min publication latency measured 2026-08-28. Grace PT2H per DATA_SOURCES P1.
    {"id": PRODUCT_MRMS_QPE, "source_id": SRC_MRMS, "label": "MRMS MultiSensor QPE 1 h Pass2 (radar+gauge+model blend), basin-aggregated", "variables": ["precip"], "expected_cadence_seconds": 3600, "grace_seconds": 7200},
    {"id": PRODUCT_MRMS_GAUGEINFL, "source_id": SRC_MRMS, "label": "MRMS gauge-influence index 1 h Pass2 — how much of the QPE came from gauges rather than radar", "variables": ["precip"], "expected_cadence_seconds": 3600, "grace_seconds": 7200},
    # Active CAP alerts, polled every 5 min (the provider allows once or twice a minute; the
    # payload is one ~5-50 KB request). Grace 10 min: two missed polls is a real gap.
    {"id": PRODUCT_NWS_ALERTS, "source_id": SRC_NWS_API, "label": "NWS active CAP alerts for Washington (api.weather.gov), routed to basins by the derived UGC mapping", "variables": ["alert"], "expected_cadence_seconds": 300, "grace_seconds": 600},
)


@dataclass(frozen=True)
class JobSpec:
    """One registered ingest job, described in the vocabulary everything else already shares.

    This is the *catalogue*: what the job is called, whose bytes it reads, which products it
    writes and how often it is expected to run. The worker binds each name to a callable
    (`apps/worker/src/cascade_worker/scheduler.py`); `/system/health` reads the catalogue to know
    what it must account for. The API cannot import the scheduler — that would drag the provider
    adapters into `cascade_api` and break the import contract — so the two live apart and are
    pinned together by `tests/unit/test_job_registry.py`, which imports both in the test process
    and fails when a job is registered in one and missing from the other, or when the cadences
    disagree. A job added to the scheduler and forgotten here is a red test, not a blind spot:
    that blindness is exactly what let `nbm.fetch_core_snowlvl` fail on every cycle while
    `/system/health` answered `ok` (pg-migration-verification-2026-08-24 §P3.6 finding C).

    `products` is what the job WRITES, and it is what the freshness half of `/system/health`
    expects to see arrive. It is empty for a job that produces no product rows at all
    (`nbm.build_grid_masks` writes basin masks, not values).
    """

    name: str
    #: Health grouping key — one upstream service, several jobs. Kept short and stable because
    #: it is the key clients see in `/system/health`'s `providers` map.
    provider: str
    #: The registry source this job reads from, so `source_kind` is never guessed here either.
    source_id: str
    products: tuple[str, ...]
    #: Seconds between scheduled runs; must equal the scheduler's cadence for the same job.
    cadence_seconds: int


JOBS: tuple[JobSpec, ...] = (
    JobSpec("nwps.fetch_thresholds", "nwps", SRC_NWPS, (PRODUCT_NWPS_THRESHOLDS,), 6 * 3600),
    JobSpec("nwps.fetch_forecast", "nwps", SRC_NWPS, (PRODUCT_NWPS_FORECAST,), 30 * 60),
    # Daily at 16:30Z — after the observed ~15:06-15:49Z publication of the 12Z cycle. This job is
    # a backfill that runs on a schedule: it walks the ~10 retained cycles and collects whatever is
    # not stored, so one missed run costs nothing and a fresh database recovers ten days at once.
    JobSpec("nwps.fetch_hefs", "nwps-hefs", SRC_NWPS_HEFS, (PRODUCT_HEFS_ENSEMBLE, PRODUCT_HEFS_QUANTILES), 86400),
    # Renamed from "usgs.fetch_iv" on 2026-08-27 when the transport moved to the OGC API. The
    # name is transport-NEUTRAL on purpose: the previous one named a service that is being
    # decommissioned, and this job's identity is "fetch the instantaneous observations", not
    # "call NWIS". Run history under the old name is not migrated; the health endpoint reports
    # `pending` (which reads `unknown`, not `degraded`) until the first run.
    JobSpec("usgs.fetch_instantaneous", "usgs", SRC_USGS, (PRODUCT_USGS_IV,), 900),
    # Writes grid masks, not values: no product of its own, and therefore nothing in the
    # freshness map. Its health is still reported — a silently failing mask build is what makes
    # every NBM basin mean read UNKNOWN (see the scheduler's JOBS docstring).
    JobSpec("nbm.build_grid_masks", "nbm", SRC_NBM, (), 86400),
    JobSpec("nbm.fetch_qmd", "nbm", SRC_NBM, (PRODUCT_NBM_QMD,), 12 * 3600),
    JobSpec("nbm.fetch_core_snowlvl", "nbm", SRC_NBM, (PRODUCT_NBM_CORE,), 6 * 3600),
    JobSpec("nwm.fetch_reach_medium_range", "nwm", SRC_NWM, (PRODUCT_NWM_MR,), 6 * 3600),
    # Builds both ladders in one pass: Cascade's own from the OGC daily record, and the USGS
    # published day-of-year table as the cross-check. They are stored separately and never averaged.
    JobSpec("usgs.build_climatology", "usgs-stats", SRC_USGS_NORMALS, (PRODUCT_USGS_OGC_DAILY, PRODUCT_USGS_DOY_NORMALS), 31_536_000),
    JobSpec("usgs.fetch_daily_percentile", "usgs-ogc", SRC_USGS_OGC, (PRODUCT_USGS_OGC_DAILY,), 86400),
    JobSpec("awdb.fetch_snotel_context", "awdb", SRC_AWDB, (PRODUCT_AWDB_DAILY, PRODUCT_AWDB_STATIONS), 86400),
    # Hourly at :20 — Pass2 for hour H publishes ~H+57 min (measured 2026-08-28). A backfill
    # on a schedule: each run lists the day prefix and ingests every accumulation not stored.
    JobSpec("mrms.fetch_qpe", "mrms", SRC_MRMS, (PRODUCT_MRMS_QPE, PRODUCT_MRMS_GAUGEINFL), 3600),
    JobSpec("nws.fetch_alerts", "nws-api", SRC_NWS_API, (PRODUCT_NWS_ALERTS,), 300),
    # Registered on the QUEUE only, never in `scheduler.JOBS` (it needs PostgreSQL, and `run-once`
    # must keep working on sqlite) — but it runs through `run_job` like everything else, leaves
    # job_run rows, and keeps the observation partition horizon ahead of ingestion. It belongs
    # here for exactly the reason this catalogue exists: a job whose only registration is in a
    # place health does not read is a job health cannot see. Monthly cron `3 0 1 * *`.
    JobSpec("maintenance.ensure_observation_partitions", "cascade", SRC_CASCADE, (), 30 * 86400),
)

JOBS_BY_NAME: dict[str, JobSpec] = {job.name: job for job in JOBS}

#: Registered products that NO scheduled job writes, with the reason. Listing them explicitly is
#: what stops a new product from being quietly dropped from `/system/health`'s freshness map:
#: `tests/unit/test_job_registry.py` asserts every id in `PRODUCTS` is either written by a job or
#: named here, so "nothing writes this" has to be a decision someone made, not an omission.
UNSCHEDULED_PRODUCTS: dict[str, str] = {
    # Event Zero reconstruction only: written by the December-2025 backfill, never on a cron.
    PRODUCT_NWS_FLS_CREST: "backfill-only (Event Zero); no scheduled job writes it",
    # RETIRED 2026-08-27 with the last call to waterservices.usgs.gov. Kept registered so the
    # historical rows that reference it still resolve to the service that actually produced them;
    # `usgs.build_climatology` now writes product:usgs-doy-normals instead.
    PRODUCT_USGS_DAILY_STATS: "retired 2026-08-27 (nwis/stat); superseded by product:usgs-doy-normals",
}

#: product id -> the jobs that write it, in `JOBS` order. Derived, never hand-listed.
PRODUCT_WRITERS: dict[str, tuple[str, ...]] = {
    pid: tuple(job.name for job in JOBS if pid in job.products)
    for pid in dict.fromkeys(pid for job in JOBS for pid in job.products)
}

#: The products `/system/health` expects to see arrive, in registry order. A product here with no
#: rows is reported as `missing` with a reason — it never falls out of the report.
EXPECTED_PRODUCTS: tuple[str, ...] = tuple(str(p["id"]) for p in PRODUCTS if str(p["id"]) in PRODUCT_WRITERS)

#: Products that legitimately produce NO value rows — metadata, not measurements — and can
#: therefore only ever be anchored on the bytes that were fetched. Freshness falls back to
#: `raw_artifact` for THESE and nothing else (`Knowledge.product_freshness_anchors`).
#:
#: The list has to be explicit because bytes are not values. `nbm.build_grid_masks` fetches a
#: `product:nbm-v5-core` file of its own, so on a database where `nbm.fetch_core_snowlvl` has
#: never once succeeded there are still `raw_artifact` rows for that product — and an unrestricted
#: fallback answered `state: current, reason: null` for a product of which not one value has ever
#: been produced (measured 2026-08-25, pg-migration-verification-2026-08-24 §P3.9). A product that
#: is supposed to yield values and has none reads `missing`, which is the truth.
METADATA_ONLY_PRODUCTS: frozenset[str] = frozenset({PRODUCT_AWDB_STATIONS})

#: Products whose values are **valid until superseded** rather than sampled on a cadence: an
#: official flood threshold is true until NWS changes it, which happens perhaps once a year.
#: Their rows are written only on change (append-only, never a duplicate), so the newest row is
#: months old on a healthy system and value-age says nothing about whether the information is
#: current — it says how long the value has been stable, which is not the same question.
#:
#: For these, freshness is "when did we last CHECK", so the anchor merges the newest value row
#: with the newest successful fetch of the product. The failure mode the `METADATA_ONLY_PRODUCTS`
#: comment warns about — bytes arriving while the parse step fails, reading `current` on the
#: strength of unparsed bytes — is covered here by the other half of `/system/health`: a parse
#: failure fails the JOB, and every registered job is now accounted for. Without this, thresholds
#: read `stale` forever and `/system/health` answers `degraded` on a perfectly healthy system,
#: which is the same disease as answering `ok` on a broken one: a signal nobody can act on.
VALID_UNTIL_SUPERSEDED_PRODUCTS: frozenset[str] = frozenset({PRODUCT_NWPS_THRESHOLDS})
