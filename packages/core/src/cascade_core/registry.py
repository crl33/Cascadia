"""Source/product registry ids and cadences (docs/DOMAIN_MODEL.md §2.2, docs/DATA_DOCTRINE.md §5).

Ids are the vocabulary shared by providers, hydrology, the API and /system/health. Cadence and
grace seconds are the seed values; the SourceProduct rows are what freshness is computed from.
"""

from __future__ import annotations

SRC_USGS = "src:usgs-nwis-iv"
SRC_NWPS = "src:nwps-v1"
SRC_CASCADE = "src:cascade"

PRODUCT_USGS_IV = "product:usgs-iv"
PRODUCT_NWPS_FORECAST = "product:nwps-forecast"
PRODUCT_NWPS_THRESHOLDS = "product:nwps-thresholds"

SOURCES: tuple[dict[str, str], ...] = (
    {"id": SRC_USGS, "authority": "U.S. Geological Survey", "kind": "OBSERVED", "base_url": "https://waterservices.usgs.gov/nwis/iv/", "docs_url": "https://waterservices.usgs.gov/docs/instantaneous-values/"},
    {"id": SRC_NWPS, "authority": "NOAA National Weather Service (NWPS)", "kind": "OFFICIAL_FORECAST", "base_url": "https://api.water.noaa.gov/nwps/v1/", "docs_url": "https://api.water.noaa.gov/nwps/v1/docs/"},
    {"id": SRC_CASCADE, "authority": "Cascadia Papsukkal", "kind": "DERIVED", "base_url": "", "docs_url": ""},
)

PRODUCTS: tuple[dict[str, object], ...] = (
    {"id": PRODUCT_USGS_IV, "source_id": SRC_USGS, "label": "USGS instantaneous values (stage 00065, discharge 00060)", "variables": ["stage", "flow"], "expected_cadence_seconds": 900, "grace_seconds": 4500},
    {"id": PRODUCT_NWPS_FORECAST, "source_id": SRC_NWPS, "label": "NWRFC official river forecast via NOAA NWPS", "variables": ["stage", "flow"], "expected_cadence_seconds": 86400, "grace_seconds": 64800},
    {"id": PRODUCT_NWPS_THRESHOLDS, "source_id": SRC_NWPS, "label": "Official NWS flood categories (NWPS)", "variables": ["threshold"], "expected_cadence_seconds": 21600, "grace_seconds": 21600},
)
