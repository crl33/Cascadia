"""NWPS v1 client. Base URL is a compile-time constant; only api.water.noaa.gov is allowlisted."""

from __future__ import annotations

import re

from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.fetch import ArchivingFetcher, FetchResult
from cascade_core.registry import PRODUCT_NWPS_FORECAST, PRODUCT_NWPS_THRESHOLDS

BASE_URL = "https://api.water.noaa.gov/nwps/v1/"
ALLOWED_HOSTS = frozenset({"api.water.noaa.gov"})
_LID = re.compile(r"^[A-Z0-9]{3,8}$")


def _lid(lid: str) -> str:
    if not _LID.match(lid):
        raise ValueError(f"invalid NWS LID {lid!r}")
    return lid


async def fetch_gauge(fetcher: ArchivingFetcher, session: AsyncSession, lid: str) -> FetchResult:
    return await fetcher.fetch(session, url=f"{BASE_URL}gauges/{_lid(lid)}", params=None, allowed_hosts=ALLOWED_HOSTS, product_id=PRODUCT_NWPS_THRESHOLDS)


async def fetch_stageflow(fetcher: ArchivingFetcher, session: AsyncSession, lid: str) -> FetchResult:
    return await fetcher.fetch(session, url=f"{BASE_URL}gauges/{_lid(lid)}/stageflow", params=None, allowed_hosts=ALLOWED_HOSTS, product_id=PRODUCT_NWPS_FORECAST)
