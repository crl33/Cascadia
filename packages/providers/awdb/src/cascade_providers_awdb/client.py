"""NRCS AWDB REST client (stations + daily values). Base URL is a compile-time constant.

Politeness (DATA_SOURCES S1: no documented rate limit, single Apache host, occasionally slow):
one station-metadata call a week and one values call a day, both through the shared
HostRateLimiter, both archived before parse.

Two request parameters are load-bearing and are always passed explicitly:

- ``periodRef=END`` — the DAILY value dated D is the 00:00 PST reading of D+1. With the default
  the platform would be silently off by a day (DATA_SOURCES S1, "the periodRef pitfall").
- ``centralTendencyType=MEDIAN`` — asks for the per-value ``median`` used for percent-of-median.
  It is a REQUEST, not a guarantee: WTEQ came back with ``median`` absent at one site and 0.0 at
  every other on 2026-08-24, which the normalizer refuses rather than divides by.
"""

from __future__ import annotations

import re
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.fetch import ArchivingFetcher, FetchResult
from cascade_core.registry import PRODUCT_AWDB_DAILY, PRODUCT_AWDB_STATIONS

BASE_URL = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1"
STATIONS_URL = f"{BASE_URL}/stations"
DATA_URL = f"{BASE_URL}/data"
ALLOWED_HOSTS = frozenset({"wcc.sc.egov.usda.gov"})

WA_SNOTEL_WILDCARD = "*:WA:SNTL"
CONTEXT_ELEMENTS = ("WTEQ", "PREC")  # snow water equivalent; water-year ACCUMULATED precipitation
SOIL_ELEMENT = "SMS:*"  # canary only — see __init__ and design §2.1
_TRIPLET_RE = re.compile(r"^[A-Za-z0-9_]+:[A-Z]{2}:[A-Z]+$")


def _triplets(triplets: list[str]) -> str:
    for t in triplets:
        if t != WA_SNOTEL_WILDCARD and not _TRIPLET_RE.match(t):
            raise ValueError(f"not an AWDB station triplet: {t!r}")
    return ",".join(triplets)


async def fetch_stations(
    fetcher: ArchivingFetcher,
    session: AsyncSession,
    *,
    triplets: list[str] | None = None,
    active_only: bool = True,
) -> FetchResult:
    """Station metadata: triplet, name, HUC12, elevation, coordinates, station time zone.

    The basin mapping is derived from each station's own HUC against the seeded basin HUC8
    lists, so there is no hardcoded site list to drift (normalize.map_stations_to_basins).
    """
    params = {"stationTriplets": _triplets(triplets or [WA_SNOTEL_WILDCARD]), "activeOnly": "true" if active_only else "false"}
    return await fetcher.fetch(
        session, url=STATIONS_URL, params=params, allowed_hosts=ALLOWED_HOSTS,
        product_id=PRODUCT_AWDB_STATIONS, suffix=".json",
    )


async def fetch_daily_values(
    fetcher: ArchivingFetcher,
    session: AsyncSession,
    *,
    triplets: list[str],
    elements: tuple[str, ...] = CONTEXT_ELEMENTS,
    begin: date,
    end: date,
) -> FetchResult:
    """Daily values with per-value median and QC/QA flags for the given stations."""
    if not triplets:
        raise ValueError("no station triplets")
    if begin > end:
        raise ValueError("begin must not be after end")
    params = {
        "stationTriplets": _triplets(triplets),
        "elements": ",".join(elements),
        "duration": "DAILY",
        "beginDate": begin.isoformat(),
        "endDate": end.isoformat(),
        "periodRef": "END",
        "centralTendencyType": "MEDIAN",
        "returnFlags": "true",
    }
    return await fetcher.fetch(
        session, url=DATA_URL, params=params, allowed_hosts=ALLOWED_HOSTS,
        product_id=PRODUCT_AWDB_DAILY, suffix=".json",
    )
