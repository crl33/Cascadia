"""USGS Water Data OGC API client — `continuous` collection (instantaneous values, statistic 00011).

Successor to the legacy NWIS IV service (client.py). Used ONLY by the Event Zero backfill for
now; the live 15-minute path stays on client.py until M3 retires it. Base URL is a compile-time
constant (vibesec addendum §1). Auth: header ``X-Api-Key`` from Settings.usgs_api_key
(env CASCADE_USGS_API_KEY) when present — 4000 req/h keyed; degrades politely to anonymous
through the shared HostRateLimiter otherwise.

Pagination is cursor-based: a page carries ``links[rel=next]`` exactly when
``numberReturned == limit`` (``numberMatched`` is null); the next href is fetched verbatim and
re-validated against the same allowlist. Every page is archived through ArchivingFetcher, so
each page gets its own RawArtifact. max_bytes is raised to 16 MB for the backfill fetcher only
(a 10k-feature page can exceed the core 8 MB default); no core change.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import datetime
from urllib.parse import parse_qsl, urlsplit, urlunsplit

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.fetch import ArchivingFetcher, FetchResult, HostRateLimiter
from cascade_core.objectstore import ObjectStore
from cascade_core.registry import PRODUCT_USGS_IV
from cascade_core.timeutils import iso_z, utcnow

OGC_BASE_URL = "https://api.waterdata.usgs.gov/ogcapi/v0/collections/continuous/items"
ALLOWED_HOSTS = frozenset({"api.waterdata.usgs.gov"})
PARAMETER_CODES = "00065,00060"
BACKFILL_MAX_BYTES = 16_000_000
_SITE_RE = re.compile(r"^\d{8,15}$")


def build_backfill_fetcher(
    store: ObjectStore,
    *,
    user_agent: str,
    api_key: str | None,
    clock: Callable[[], datetime] = utcnow,
) -> ArchivingFetcher:
    """An ArchivingFetcher tuned for the backfill: 16 MB pages, keyed header when available.

    The api key travels ONLY as the ``X-Api-Key`` header on this fetcher's own client (never in
    a URL, never logged). Close with :func:`close_fetcher` when done.
    """
    headers = {"User-Agent": user_agent, "Accept": "application/json"}
    if api_key:
        headers["X-Api-Key"] = api_key
    client = httpx.AsyncClient(timeout=120.0, follow_redirects=False, headers=headers)
    return ArchivingFetcher(
        store=store,
        user_agent=user_agent,
        timeout_s=120.0,
        max_bytes=BACKFILL_MAX_BYTES,
        limiter=HostRateLimiter(min_interval_s=0.5, max_concurrency=2),
        clock=clock,
        client=client,
    )


async def close_fetcher(fetcher: ArchivingFetcher) -> None:
    """Close the httpx client a build_backfill_fetcher() fetcher owns."""
    if fetcher._client is not None:  # noqa: SLF001 - our own fetcher, built above
        await fetcher._client.aclose()  # noqa: SLF001


async def fetch_continuous_first_page(
    fetcher: ArchivingFetcher,
    session: AsyncSession,
    *,
    site: str,
    start: datetime,
    end: datetime,
    limit: int = 10000,
) -> FetchResult:
    if not _SITE_RE.match(site):
        raise ValueError(f"not a USGS site number: {site!r}")
    if start >= end:
        raise ValueError("start must be before end")
    if not 1 <= limit <= 10000:
        raise ValueError("limit must be in 1..10000")
    params = {
        "f": "json",
        "monitoring_location_id": f"USGS-{site}",
        "parameter_code": PARAMETER_CODES,
        "datetime": f"{iso_z(start)}/{iso_z(end)}",
        "limit": str(limit),
    }
    return await fetcher.fetch(session, url=OGC_BASE_URL, params=params, allowed_hosts=ALLOWED_HOSTS, product_id=PRODUCT_USGS_IV)


async def fetch_continuous_next_page(fetcher: ArchivingFetcher, session: AsyncSession, *, next_url: str) -> FetchResult:
    """Fetch a links[rel=next] href; the fetcher re-validates the host allowlist.

    The core fetcher builds ``httpx.URL(url, params or {})``, and an empty params dict strips
    an existing query string — so the href is decomposed into its base and query parameters
    here and re-assembled by the fetcher, byte-equivalent to following the link verbatim.
    """
    parts = urlsplit(next_url)
    base = urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
    params = dict(parse_qsl(parts.query, keep_blank_values=True))
    if not params:
        raise ValueError(f"next link without query parameters: {next_url!r}")
    return await fetcher.fetch(session, url=base, params=params, allowed_hosts=ALLOWED_HOSTS, product_id=PRODUCT_USGS_IV)
