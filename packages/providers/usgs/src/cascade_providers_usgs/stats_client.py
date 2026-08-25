"""USGS clients for the day-of-year climatology path: OGC ``daily``/``latest-daily`` + ``nwis/stat``.

Three endpoints, two products, one deliberate asymmetry:

- ``product:usgs-ogc-daily`` (``api.waterdata.usgs.gov``) is the **dependency**. One request
  returns a station's entire daily-mean record, so the platform owns its climatology and the
  Q1-2027 WaterServices decommission cannot take it away (p3-surfaces-design §2.1).
- ``product:usgs-daily-stats`` (``waterservices.usgs.gov/nwis/stat``) is the **cross-check**,
  never a dependency. If it disappears the surface keeps working and loses only a confidence
  input (design §2.2 step 2).

Base URLs are compile-time constants (vibesec addendum §1); every call goes through
ArchivingFetcher, so the bytes are archived before any parser sees them. ``accept`` is passed
per call because two of these three are not JSON: the daily record is CSV and the statistics
table is RDB text.
"""

from __future__ import annotations

import re
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.fetch import ArchivingFetcher, FetchResult
from cascade_core.registry import PRODUCT_USGS_DAILY_STATS, PRODUCT_USGS_OGC_DAILY
from cascade_providers_usgs.ogc_client import build_backfill_fetcher, close_fetcher

__all__ = [
    "DAILY_URL",
    "LATEST_DAILY_URL",
    "NWIS_STAT_URL",
    "OBSERVATION_NORMALS_URL",
    "build_stats_fetcher",
    "close_fetcher",
    "fetch_daily_record",
    "fetch_latest_daily",
    "fetch_published_doy_stats",
]

DAILY_URL = "https://api.waterdata.usgs.gov/ogcapi/v0/collections/daily/items"
LATEST_DAILY_URL = "https://api.waterdata.usgs.gov/ogcapi/v0/collections/latest-daily/items"
NWIS_STAT_URL = "https://waterservices.usgs.gov/nwis/stat/"
# Documented for the quarterly re-probe in the canary only: on 2026-08-24 this served no
# discharge normals at any seed gauge, which is why it is not a code path (design §2.1).
OBSERVATION_NORMALS_URL = "https://api.waterdata.usgs.gov/statistics/v0/observationNormals"

OGC_HOSTS = frozenset({"api.waterdata.usgs.gov"})
# nwis/stat 301-redirects some query shapes onto the nwis. host (DATA_SOURCES H1).
NWIS_HOSTS = frozenset({"waterservices.usgs.gov", "nwis.waterservices.usgs.gov"})

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


async def fetch_published_doy_stats(fetcher: ArchivingFetcher, session: AsyncSession, *, site: str) -> FetchResult:
    """The LEGACY published day-of-year statistics table (RDB) — cross-check only.

    Sunsets in Q1 2027. A failure here must be tolerated by the caller: it costs the surface a
    confidence input, never its value.
    """
    params = {
        "format": "rdb",
        "sites": _site(site),
        "statReportType": "daily",
        "statTypeCd": "all",
        "parameterCd": DISCHARGE_CODE,
    }
    return await fetcher.fetch(
        session, url=NWIS_STAT_URL, params=params, allowed_hosts=NWIS_HOSTS,
        product_id=PRODUCT_USGS_DAILY_STATS, suffix=".rdb", accept="text/plain",
    )
