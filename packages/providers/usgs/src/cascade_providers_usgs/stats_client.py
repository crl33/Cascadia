"""USGS clients for the day-of-year climatology path, all three on the OGC host.

Three endpoints, two products, one deliberate asymmetry:

- ``product:usgs-ogc-daily`` (``api.waterdata.usgs.gov``) is the **dependency**. One request
  returns a station's entire daily-mean record, so the platform owns its climatology and the
  Q1-2027 WaterServices decommission cannot take it away (p3-surfaces-design §2.1).
- ``product:usgs-doy-normals`` (``api.waterdata.usgs.gov/statistics/v0``) is the **cross-check**,
  never a dependency. If it disappears the surface keeps working and loses only a confidence
  input (design §2.2 step 2).

Nothing here calls ``waterservices.usgs.gov`` any more. The ``nwis/stat`` cross-check was retired
on 2026-08-27 in favour of ``observationNormals``, which is not the same numbers — a different
period of record and no published begin/end year — which is why it carries its own product and a
method-id bump rather than being treated as a transport swap
(docs/research/nwis-stat-successor-2026-08-27.md).

Base URLs are compile-time constants (vibesec addendum §1); every call goes through
ArchivingFetcher, so the bytes are archived before any parser sees them. ``accept`` is passed
per call because the daily record is CSV while the other two are JSON.
"""

from __future__ import annotations

import re
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.fetch import ArchivingFetcher, FetchResult
from cascade_core.registry import PRODUCT_USGS_DOY_NORMALS, PRODUCT_USGS_OGC_DAILY
from cascade_providers_usgs.ogc_client import build_backfill_fetcher, close_fetcher

__all__ = [
    "DAILY_URL",
    "LATEST_DAILY_URL",
    "OBSERVATION_NORMALS_URL",
    "build_stats_fetcher",
    "close_fetcher",
    "fetch_daily_record",
    "fetch_latest_daily",
    "fetch_published_doy_normals",
]

DAILY_URL = "https://api.waterdata.usgs.gov/ogcapi/v0/collections/daily/items"
LATEST_DAILY_URL = "https://api.waterdata.usgs.gov/ogcapi/v0/collections/latest-daily/items"
OBSERVATION_NORMALS_URL = "https://api.waterdata.usgs.gov/statistics/v0/observationNormals"

OGC_HOSTS = frozenset({"api.waterdata.usgs.gov"})

DISCHARGE_CODE = "00060"
DAILY_MEAN_STATISTIC = "00003"
DAILY_PROPERTIES = "time,value,approval_status"
MAX_DAILY_ROWS = 50000  # the OGC `daily` collection's documented per-request ceiling
_SITE_RE = re.compile(r"^\d{8,15}$")

# The same keyed, generously-sized fetcher the OGC backfill builds: it already puts the api key
# in an X-Api-Key header (never a URL) and raises max_bytes above the 903 KB full-record CSV.
build_stats_fetcher = build_backfill_fetcher


def _site(site: str) -> str:
    if not _SITE_RE.match(site):
        raise ValueError(f"not a USGS site number: {site!r}")
    return site


async def fetch_daily_record(
    fetcher: ArchivingFetcher,
    session: AsyncSession,
    *,
    site: str,
    since: date | None = None,
    until: date | None = None,
) -> FetchResult:
    """The station's daily-mean discharge record as CSV — the climatology input.

    ``since``/``until`` bound the record when a caller wants a shorter window (the Sauk fixture
    is captured this way); with neither, the whole period of record comes back in one request.
    """
    params = {
        "monitoring_location_id": f"USGS-{_site(site)}",
        "parameter_code": DISCHARGE_CODE,
        "statistic_id": DAILY_MEAN_STATISTIC,
        "f": "csv",
        "skipGeometry": "true",
        "limit": str(MAX_DAILY_ROWS),
        "properties": DAILY_PROPERTIES,
    }
    if since is not None or until is not None:
        lo = since.isoformat() if since else ".."
        hi = until.isoformat() if until else ".."
        if since is not None and until is not None and since > until:
            raise ValueError("since must not be after until")
        params["datetime"] = f"{lo}/{hi}"
    return await fetcher.fetch(
        session, url=DAILY_URL, params=params, allowed_hosts=OGC_HOSTS,
        product_id=PRODUCT_USGS_OGC_DAILY, suffix=".csv", accept="text/csv",
    )


async def fetch_latest_daily(fetcher: ArchivingFetcher, session: AsyncSession, *, sites: list[str]) -> FetchResult:
    """The previous complete daily mean at every requested site, in one request."""
    if not sites:
        raise ValueError("no sites")
    params = {
        "monitoring_location_id": ",".join(f"USGS-{_site(s)}" for s in sites),
        "parameter_code": DISCHARGE_CODE,
        "f": "json",
        "skipGeometry": "true",
        "limit": str(max(50, len(sites) * 4)),
    }
    return await fetcher.fetch(
        session, url=LATEST_DAILY_URL, params=params, allowed_hosts=OGC_HOSTS,
        product_id=PRODUCT_USGS_OGC_DAILY, suffix=".json",
    )


async def fetch_published_doy_normals(fetcher: ArchivingFetcher, session: AsyncSession, *, site: str) -> FetchResult:
    """The USGS published day-of-year discharge normals — CROSS-CHECK, never a dependency.

    A failure here must be tolerated by the caller: it costs the surface a confidence input, never
    its value. There is no fallback to the retired ``nwis/stat``; an absent cross-check is a state
    the surface already knows how to say.

    ``parameter_code`` is what makes this affordable. Unfiltered, the response carries every
    parameter the station publishes — sediment, turbidity, temperature — at 2.4-3.6 MB; filtered
    to discharge it is ~415 KB (nwis-stat-successor-2026-08-27 §4, §13).
    """
    params = {
        "monitoring_location_id": f"USGS-{_site(site)}",
        "normal_type": "DOY",
        "parameter_code": DISCHARGE_CODE,
    }
    return await fetcher.fetch(
        session, url=OBSERVATION_NORMALS_URL, params=params, allowed_hosts=OGC_HOSTS,
        product_id=PRODUCT_USGS_DOY_NORMALS, suffix=".json",
    )
