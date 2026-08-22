"""USGS NWIS IV client. Base URL is a compile-time constant (vibesec addendum §1).

NOTE: the legacy `waterservices.usgs.gov/nwis/iv/` service is scheduled for decommission in
Q1 2027 (successor: api.waterdata.usgs.gov OGC API). Some queries 301 to
`nwis.waterservices.usgs.gov`; both hosts are allowlisted and redirects are re-validated.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.fetch import ArchivingFetcher, FetchResult
from cascade_core.registry import PRODUCT_USGS_IV

BASE_URL = "https://waterservices.usgs.gov/nwis/iv/"
ALLOWED_HOSTS = frozenset({"waterservices.usgs.gov", "nwis.waterservices.usgs.gov"})
PARAMETER_CODES = "00065,00060"


async def fetch_iv(fetcher: ArchivingFetcher, session: AsyncSession, *, sites: list[str], hours: int) -> FetchResult:
    if not sites or hours <= 0 or hours > 24 * 120:
        raise ValueError("sites required and 0 < hours <= 2880")
    params = {
        "format": "json",
        "sites": ",".join(sites),
        "parameterCd": PARAMETER_CODES,
        "period": f"PT{int(hours)}H",
        "siteStatus": "all",
    }
    return await fetcher.fetch(session, url=BASE_URL, params=params, allowed_hosts=ALLOWED_HOSTS, product_id=PRODUCT_USGS_IV)
