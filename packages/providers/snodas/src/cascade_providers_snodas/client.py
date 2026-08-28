"""SNODAS at NSIDC (noaadata.apps.nsidc.org): one daily tar, the UNMASKED grid on purpose.

Unmasked because the Nooksack and Skagit headwaters cross into British Columbia and the masked
CONUS grid cuts them off (DATA_SOURCES S2). ~5-7 MB/day in August; winter will be larger, and
the ``snodas/`` object prefix carries a 30-day lifecycle because NSIDC archives every day back
to 2003 — the raw tar is always re-fetchable, the derived rows are the permanent record.

NSIDC runs at a "Basic" service level and intermittently answers HTTP 500 (measured — once in
two probe fetches); the fetcher's error path plus the parser's tar magic check cover both the
refused and the HTML-as-200 shape of that failure.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.fetch import ArchivingFetcher, FetchResult
from cascade_core.registry import PRODUCT_SNODAS_SWE

BASE_URL = "https://noaadata.apps.nsidc.org/NOAA/G02158/unmasked/"
NSIDC_HOSTS = frozenset({"noaadata.apps.nsidc.org"})
OBJECT_PREFIX = "snodas/"

__all__ = ["BASE_URL", "NSIDC_HOSTS", "OBJECT_PREFIX", "day_tar_url", "fetch_day_tar"]


def day_tar_url(day: date) -> str:
    # month directories are named "08_Aug" — number AND abbreviation
    return f"{BASE_URL}{day.year}/{day:%m_%b}/SNODAS_unmasked_{day:%Y%m%d}.tar"


async def fetch_day_tar(
    fetcher: ArchivingFetcher, session: AsyncSession, day: date
) -> FetchResult:
    return await fetcher.fetch(
        session,
        url=day_tar_url(day),
        params=None,
        allowed_hosts=NSIDC_HOSTS,
        product_id=PRODUCT_SNODAS_SWE,
        prefix=OBJECT_PREFIX,
        suffix=".tar",
        accept="*/*",
    )
