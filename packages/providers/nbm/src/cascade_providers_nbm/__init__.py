"""cascade_providers_nbm — NBM v5.0 adapter (National Blend of Models, NOAA/NWS MDL).

MODELED guidance, never an official forecast (docs/DATA_SOURCES.md W2). The adapter fetches
WA-box subsets from the NOMADS ``filter_blend.pl`` CGI, archives the raw GRIB2 before parsing
it, decodes with eccodes (worker-only extra, imported lazily), and aggregates onto stored
basin masks. It computes no assessment: the methods live in ``cascade_hydrology.forcing``.
"""

from cascade_providers_nbm.client import (
    WA_BASINS,
    Cycle,
    SubRegion,
    fetch_core_snowlvl,
    fetch_qmd_apcp,
    latest_qmd_cycle,
)
from cascade_providers_nbm.parser import (
    APCP,
    SNOWLVL,
    Field,
    FieldKey,
    NbmParseError,
    decode,
    scan,
)

__all__ = [
    "APCP",
    "SNOWLVL",
    "Cycle",
    "Field",
    "FieldKey",
    "NbmParseError",
    "SubRegion",
    "WA_BASINS",
    "decode",
    "fetch_core_snowlvl",
    "fetch_qmd_apcp",
    "latest_qmd_cycle",
    "scan",
]
