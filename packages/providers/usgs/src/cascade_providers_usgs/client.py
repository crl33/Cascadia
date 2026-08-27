"""USGS NWIS IV client — RETIRED FROM PRODUCTION 2026-08-27; comparator and capture use only.

The live instantaneous path is the Water Data OGC API (`ogc_client.py`, `jobs.py`). Nothing in
`packages/`, `apps/` or the scheduler calls this module any more: `fetch_iv` appears outside
`tests/` and `scripts/` only in comments.

It is KEPT rather than deleted for one concrete reason the migration brief allows — it is half of
the parity evidence. `tests/unit/test_usgs_transport_parity.py` runs both transports over the same
captured window and asserts they normalize identically, and `scripts/compare_usgs_iv_ogc.py` does
the same against the live endpoints. A comparator that cannot be run is not a comparator.

It must NEVER become a fallback. `jobs.py` does not import it, and
`test_usgs_ogc_live_job.py::test_an_ogc_failure_fails_and_never_reaches_for_the_legacy_service`
fails if that changes: a transport that switches itself under failure makes both provenance and
outage interpretation ambiguous, and health would read green on data from somewhere else.

The service is scheduled for decommission in Q1 2027. Some queries 301 to
`nwis.waterservices.usgs.gov`; both hosts stay in the fetch ceiling for THIS comparator alone —
the `nwis/stat` cross-check that was the other reason was retired on 2026-08-27
(docs/research/nwis-stat-successor-2026-08-27.md).

Base URL is a compile-time constant (vibesec addendum §1).
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
