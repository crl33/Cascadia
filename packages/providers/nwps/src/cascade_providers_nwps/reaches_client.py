"""Client for the NWPS `/reaches/{reachId}` endpoints (National Water Model output).

Same host and same allowlist as `client.py`, deliberately a separate module: these endpoints
serve a different source (`src:nwm-v3.1`, MODELED) under a different product
(`product:nwm-mr-via-nwps`) from the official-forecast endpoints, and the archive must record
that difference on every byte it stores.

Why JSON and not NetCDF: the NWM CONUS `channel_rt` file is ~12.5 MB per timestep and needs the
269 MB RouteLink crosswalk re-derived on every NWM version change, to reproduce what this
endpoint already returns in ~157 KB (design §3.1). The reach id itself comes from NWPS's own
gauge crosswalk and is stored on `ForecastPoint.reach_id`; it is never guessed here.
"""

from __future__ import annotations

import re

from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.fetch import ArchivingFetcher, FetchResult
from cascade_core.registry import PRODUCT_NWM_MR
from cascade_providers_nwps.client import ALLOWED_HOSTS, BASE_URL
from cascade_providers_nwps.reaches_parser import SERIES_NAME

REACH_ID_PREFIX = "reach:nwm:"
_REACH_ID = re.compile(r"^[0-9]{1,12}$")


def reach_number(reach_id: str) -> str:
    """``reach:nwm:24270288`` (or a bare id) -> ``24270288``; anything else raises.

    The stored id keeps its namespace so a reach can never be confused with a station or a
    forecast point; the API path wants the bare NHDPlusV2 COMID."""
    bare = reach_id[len(REACH_ID_PREFIX) :] if reach_id.startswith(REACH_ID_PREFIX) else reach_id
    if not _REACH_ID.match(bare):
        raise ValueError(f"invalid NWM reach id {reach_id!r}")
    return bare


async def fetch_medium_range(fetcher: ArchivingFetcher, session: AsyncSession, reach_id: str) -> FetchResult:
    """The medium-range ensemble (provider mean + members) for one reach, archived before parse."""
    return await fetcher.fetch(
        session,
        url=f"{BASE_URL}reaches/{reach_number(reach_id)}/streamflow",
        params={"series": SERIES_NAME},
        allowed_hosts=ALLOWED_HOSTS,
        product_id=PRODUCT_NWM_MR,
    )
