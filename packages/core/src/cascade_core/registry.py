"""Source/product registry ids and cadences (docs/DOMAIN_MODEL.md §2.2, docs/DATA_DOCTRINE.md §5).

Ids are the vocabulary shared by providers, hydrology, the API and /system/health. Cadence and
grace seconds are the seed values; the SourceProduct rows are what freshness is computed from.

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

SRC_USGS = "src:usgs-nwis-iv"
SRC_NWPS = "src:nwps-v1"
SRC_CASCADE = "src:cascade"
SRC_NWS_AFOS = "src:nws-afos"
# P3 additions (p3-surfaces-design-2026-08-24 §1.6, §2.1, §3.4).
SRC_NBM = "src:nbm-v5"
SRC_NWM = "src:nwm-v3.1"
SRC_USGS_OGC = "src:usgs-wdfn-ogc"
SRC_USGS_STATS = "src:usgs-wdfn-statistics"
SRC_AWDB = "src:nrcs-awdb"

PRODUCT_USGS_IV = "product:usgs-iv"
PRODUCT_NWPS_FORECAST = "product:nwps-forecast"
PRODUCT_NWPS_THRESHOLDS = "product:nwps-thresholds"
PRODUCT_NWS_FLS_CREST = "product:nws-fls-crest"
# P3 additions.
PRODUCT_NBM_QMD = "product:nbm-v5-qmd"
PRODUCT_NBM_CORE = "product:nbm-v5-core"
PRODUCT_NWM_MR = "product:nwm-mr-via-nwps"
PRODUCT_USGS_OGC_DAILY = "product:usgs-ogc-daily"
PRODUCT_USGS_DAILY_STATS = "product:usgs-daily-stats"
PRODUCT_AWDB_DAILY = "product:awdb-snotel-daily"
PRODUCT_AWDB_STATIONS = "product:awdb-stations"

SOURCES: tuple[dict[str, str], ...] = (
    {"id": SRC_USGS, "authority": "U.S. Geological Survey", "kind": "OBSERVED", "base_url": "https://waterservices.usgs.gov/nwis/iv/", "docs_url": "https://waterservices.usgs.gov/docs/instantaneous-values/"},
    {"id": SRC_NWPS, "authority": "NOAA National Weather Service (NWPS)", "kind": "OFFICIAL_FORECAST", "base_url": "https://api.water.noaa.gov/nwps/v1/", "docs_url": "https://api.water.noaa.gov/nwps/v1/docs/"},
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
    {"id": SRC_AWDB, "authority": "USDA NRCS National Water and Climate Center (AWDB: SNOTEL/SNOLITE/SCAN)", "kind": "OBSERVED", "base_url": "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/", "docs_url": "https://wcc.sc.egov.usda.gov/awdbRestApi/v3/api-docs"},
)

PRODUCTS: tuple[dict[str, object], ...] = (
    {"id": PRODUCT_USGS_IV, "source_id": SRC_USGS, "label": "USGS instantaneous values (stage 00065, discharge 00060)", "variables": ["stage", "flow"], "expected_cadence_seconds": 900, "grace_seconds": 4500},
    {"id": PRODUCT_NWPS_FORECAST, "source_id": SRC_NWPS, "label": "NWRFC official river forecast via NOAA NWPS", "variables": ["stage", "flow"], "expected_cadence_seconds": 86400, "grace_seconds": 64800},
    {"id": PRODUCT_NWPS_THRESHOLDS, "source_id": SRC_NWPS, "label": "Official NWS flood categories (NWPS)", "variables": ["threshold"], "expected_cadence_seconds": 21600, "grace_seconds": 21600},
    {"id": PRODUCT_NWS_FLS_CREST, "source_id": SRC_NWS_AFOS, "label": "NWRFC crest via WFO FLW/FLS text (reconstructed; 6-hourly hydrograph lost)", "variables": ["stage", "flow"], "expected_cadence_seconds": 21600, "grace_seconds": 43200},
    # PT6H / PT8H: qmd runs only for the 00/06/12/18Z cycles and lands ~7 h 20 m after the
    # cycle (design §1.1, measured). A displayed QPF percentile can legitimately be 7-13 h old
    # and the freshness badge must say so rather than the grace hiding it.
    {"id": PRODUCT_NBM_QMD, "source_id": SRC_NBM, "label": "NBM v5.0 QPF percentiles (qmd, WA subset via NOMADS filter_blend.pl)", "variables": ["precip_accum"], "expected_cadence_seconds": 21600, "grace_seconds": 28800},
    # PT1H / PT1H: core is hourly and landed at cycle + 42-44 m (design §1.1, measured).
    {"id": PRODUCT_NBM_CORE, "source_id": SRC_NBM, "label": "NBM v5.0 core, snow-level percentiles (WA subset via NOMADS filter_blend.pl)", "variables": ["snow_level"], "expected_cadence_seconds": 3600, "grace_seconds": 3600},
    # PT6H / PT8H: medium range runs 00/06/12/18Z. Member count is read from the payload,
    # never assumed (design §7 item 4).
    {"id": PRODUCT_NWM_MR, "source_id": SRC_NWM, "label": "NWM v3.1 medium-range ensemble by reach via NWPS /reaches (members, never blended with the official forecast)", "variables": ["flow"], "expected_cadence_seconds": 21600, "grace_seconds": 28800},
    # P1D / PT36H (DATA_SOURCES H2). A daily mean older than 48 h makes the susceptibility
    # surface UNKNOWN rather than falling back to the instantaneous value (design §2.2).
    {"id": PRODUCT_USGS_OGC_DAILY, "source_id": SRC_USGS_OGC, "label": "USGS daily mean discharge (OGC API daily/latest-daily, 00060 statistic 00003)", "variables": ["flow"], "expected_cadence_seconds": 86400, "grace_seconds": 129600},
    # Recomputed annually (design §2.2 step 1); grace P30D. Effectively static reference data.
    {"id": PRODUCT_USGS_DAILY_STATS, "source_id": SRC_USGS_STATS, "label": "USGS published day-of-year discharge statistics (nwis/stat, approved daily means)", "variables": ["flow"], "expected_cadence_seconds": 31536000, "grace_seconds": 2592000},
    # P1D / PT36H (DATA_SOURCES S1, doctrine defaults). SNOTEL SWE and precipitation are
    # CONTEXT drivers only: more SWE is not more risk (HYDROLOGY §7), so nothing here is scored.
    {"id": PRODUCT_AWDB_DAILY, "source_id": SRC_AWDB, "label": "SNOTEL daily values (WTEQ, PREC) with per-value median, point network", "variables": ["swe", "precip_accum"], "expected_cadence_seconds": 86400, "grace_seconds": 129600},
    {"id": PRODUCT_AWDB_STATIONS, "source_id": SRC_AWDB, "label": "AWDB station metadata (triplet, HUC, elevation, station elements)", "variables": ["metadata"], "expected_cadence_seconds": 604800, "grace_seconds": 604800},
)
