"""USGS Water Data OGC API client — `continuous` collection (instantaneous values, statistic 00011).

Successor to the legacy NWIS IV service. Used by the Event Zero backfill AND, since 2026-08-27,
by the live 15-minute instantaneous job — legacy `waterservices.usgs.gov/nwis/iv/` is scheduled
for decommission in Q1 2027 with degradation possible from August 2026.

The two callers differ in shape, not in semantics: the backfill asks for multi-day windows and
follows cursor pages; the live job asks each gauge for a short trailing window that fits in one
page. Semantic parity against the legacy path was measured before cutover and is recorded in
`docs/research/usgs-ogc-instantaneous-parity-2026-08-27.md`. Base URL is a compile-time
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
from datetime import datetime, timedelta
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


def _build_fetcher(
    store: ObjectStore,
    *,
    user_agent: str,
    api_key: str | None,
    timeout_s: float,
    max_bytes: int | None,
    clock: Callable[[], datetime],
) -> ArchivingFetcher:
    """The one place an OGC fetcher is constructed.

    The api key travels ONLY as the ``X-Api-Key`` header on this fetcher's own client — never a
    URL parameter, which would be archived verbatim into ``raw_artifact.request_url`` and logged.
    Close with :func:`close_fetcher` when done.
    """
    headers = {"User-Agent": user_agent, "Accept": "application/json"}
    if api_key:
        headers["X-Api-Key"] = api_key
    client = httpx.AsyncClient(timeout=timeout_s, follow_redirects=False, headers=headers)
    kwargs = {} if max_bytes is None else {"max_bytes": max_bytes}
    return ArchivingFetcher(
        store=store,
        user_agent=user_agent,
        timeout_s=timeout_s,
        limiter=HostRateLimiter(min_interval_s=0.5, max_concurrency=2),
        clock=clock,
        client=client,
        **kwargs,
    )


def build_backfill_fetcher(
    store: ObjectStore,
    *,
    user_agent: str,
    api_key: str | None,
    clock: Callable[[], datetime] = utcnow,
) -> ArchivingFetcher:
    """Tuned for the backfill: a longer timeout and 16 MB pages, because a 10k-feature page can
    exceed the core 8 MB default."""
    return _build_fetcher(store, user_agent=user_agent, api_key=api_key,
                          timeout_s=120.0, max_bytes=BACKFILL_MAX_BYTES, clock=clock)


async def close_fetcher(fetcher: ArchivingFetcher) -> None:
    """Close the httpx client a build_backfill_fetcher() fetcher owns."""
    if fetcher._client is not None:  # noqa: SLF001 - our own fetcher, built above
        await fetcher._client.aclose()  # noqa: SLF001


#: The live job's trailing window, and it is NOT the legacy job's 72 h. MEASURED 2026-08-27:
#: the OGC API serves GeoJSON at ~752 bytes per observation (one feature each), where NWIS IV
#: packed a whole series into one array — so the same 72 h window that cost 60 KB per poll on IV
#: costs 3.0 MB per poll here, 291 MB/day, **106 GB/year against a 10 GB R2 free tier**.
#:
#: The window exists for gap recovery, and at a 15-minute cadence 72 h was 288x redundant — every
#: poll re-fetching three days of observations that had not changed. That was invisible while it
#: was one cheap request. Three hours still recovers from twelve consecutive missed polls and
#: costs 4.4 GB/year; six hours would be 8.9 GB and too close to the tier to be prudent.
#:
#: The raw archive is content-addressed but this cannot dedupe: the window slides every poll, so
#: no two payloads are byte-identical. The next lever, if it is ever needed, is a
#: `retention_class` on these artifacts (DATA_DOCTRINE §13) — the bytes are re-derivable from
#: USGS and the OBSERVATIONS are what the platform actually keeps.
LIVE_WINDOW_HOURS = 3


def build_live_fetcher(
    store: ObjectStore,
    *,
    user_agent: str,
    api_key: str | None,
    clock: Callable[[], datetime] = utcnow,
) -> ArchivingFetcher:
    """An ArchivingFetcher for the 15-minute live poll.

    Separate from :func:`build_backfill_fetcher` only in its limits: a 3 h window for one gauge
    is ~20 KB and has no business being allowed anywhere near the backfill's 16 MB ceiling.
    """
    return _build_fetcher(store, user_agent=user_agent, api_key=api_key,
                          timeout_s=60.0, max_bytes=None, clock=clock)


async def fetch_continuous_window(
    fetcher: ArchivingFetcher,
    session: AsyncSession,
    *,
    site: str,
    hours: int = LIVE_WINDOW_HOURS,
    now: datetime | None = None,
) -> FetchResult:
    """One gauge's trailing `hours` window — the live poll's request shape.

    A thin wrapper over :func:`fetch_continuous_first_page` so the live job never open-codes a
    time window, and so the captures in `tests/fixtures/providers/usgs_ogc/pipeline/` document
    exactly the request this issues — one gauge, both parameters, one page.
    """
    end = now or utcnow()
    return await fetch_continuous_first_page(
        fetcher, session, site=site, start=end - timedelta(hours=hours), end=end,
    )


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
