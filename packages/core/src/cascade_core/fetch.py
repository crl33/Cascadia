"""The one outbound HTTP path every provider adapter uses (vibesec addendum §1).

Allowlisted hosts only (re-validated on every redirect hop), hard timeout, max response bytes,
User-Agent with contact, per-host minimum interval + concurrency cap, and archive-before-parse:
the raw bytes are written to the object store and a RawArtifact row is flushed BEFORE the bytes
are returned to any parser. The API process never constructs one of these.

Two allowlists, deliberately:

- ``PROVIDER_HOSTS`` below is the *ceiling* — every host any Cascadia Papsukkal adapter is
  permitted to contact, in one reviewable place. Adding a provider means adding its host here
  on purpose, with a comment naming the DATA_SOURCES row it comes from.
- each adapter still passes the narrow ``allowed_hosts`` for the call it is making, so a bug in
  one adapter cannot reach another provider's host.

Bytes are not always JSON. ``fetch(..., accept=...)`` sets the Accept header per call, because
the same fetcher archives GRIB2 (``application/octet-stream``), RDB text and JSON.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit

import httpx
from httpx._client import USE_CLIENT_DEFAULT
from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.models import RawArtifact
from cascade_core.objectstore import ObjectStore, sha256_hex
from cascade_core.timeutils import utcnow

# Every host a Cascadia Papsukkal provider adapter may contact, with the docs/DATA_SOURCES.md
# row it belongs to. This is the ceiling, not the per-call allowlist: `fetch` refuses an
# `allowed_hosts` set that reaches outside it, so a new host is an explicit, reviewable edit.
PROVIDER_HOSTS: frozenset[str] = frozenset(
    {
        # H1 legacy WaterServices. NO production module requests these any more: instantaneous
        # moved to the OGC `continuous` collection 2026-08-27 (ADR-0015) and the `nwis/stat`
        # cross-check to the OGC statistics API the same day. They stay in the CEILING only so
        # the kept parity comparator (`usgs/client.py`) and its tests can still run; a
        # production caller is a regression, pinned by
        # test_usgs_transport_parity::test_no_production_module_calls_the_decommissioning_legacy_service.
        "waterservices.usgs.gov",            # H1 comparator only
        "nwis.waterservices.usgs.gov",       # H1 redirect target, comparator only
        "api.waterdata.usgs.gov",            # H2 USGS OGC API-Features; statistics v0 (BETA)
        "api.water.noaa.gov",                # H3 NWPS gauges/stageflow; H6 NWM reaches via NWPS
        "mesonet.agron.iastate.edu",         # AFOS text archive (IEM) for FLW/FLS reconstruction
        "nomads.ncep.noaa.gov",              # W2 NBM live subsets via filter_blend.pl (primary)
        "noaa-nbm-grib2-pds.s3.amazonaws.com",  # W2 NBM S3 archive: .idx + ranged GET (backfill/fallback)
        "wcc.sc.egov.usda.gov",              # S1 NRCS AWDB (SNOTEL WTEQ/PREC)
        "noaa-mrms-pds.s3.amazonaws.com",    # P1 MRMS QPE + gauge-influence (NODD mirror)
        "api.weather.gov",                   # W1 NWS API: CAP alerts (Phase 1), grids later
        "ftp-wpc.ncep.noaa.gov",             # W6 WPC 5-km QPF files (official human QPF)
        "noaadata.apps.nsidc.org",           # S2 SNODAS daily tars (NOAA@NSIDC G02158)
        "www.nwrfc.noaa.gov",                # R4 xml.cgi reservoir series
    }
)


class FetchError(Exception):
    def __init__(self, kind: str, detail: str) -> None:
        super().__init__(f"{kind}: {detail}")
        self.kind = kind
        self.detail = detail


@dataclass(frozen=True)
class FetchResult:
    url: str
    http_status: int
    content: bytes
    content_type: str | None
    fetched_at: datetime
    sha256: str
    object_key: str
    artifact_id: int
    #: The origin's own Last-Modified, when it sent one — the honest publication instant for
    #: plain-HTTP file servers (the S3-listing LastModified idea, without a listing). None when
    #: the origin stays silent; callers then fall back to ``fetched_at``, which can only ever be
    #: LATER than the truth — the conservative direction for replay.
    last_modified: datetime | None = None


class HostRateLimiter:
    """Minimum interval between requests per host plus a small global concurrency cap."""

    def __init__(self, min_interval_s: float = 0.5, max_concurrency: int = 2) -> None:
        self.min_interval_s = min_interval_s
        self._sem = asyncio.Semaphore(max_concurrency)
        self._last: dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def __aenter__(self) -> None:
        await self._sem.acquire()

    async def __aexit__(self, *exc: object) -> None:
        self._sem.release()

    async def wait_turn(self, host: str) -> None:
        async with self._lock:
            now = time.monotonic()
            delay = self._last.get(host, 0.0) + self.min_interval_s - now
            if delay > 0:
                await asyncio.sleep(delay)
            self._last[host] = time.monotonic()


class ArchivingFetcher:
    def __init__(
        self,
        *,
        store: ObjectStore,
        user_agent: str,
        timeout_s: float = 30.0,
        max_bytes: int = 8_000_000,
        max_redirects: int = 3,
        limiter: HostRateLimiter | None = None,
        clock: Callable[[], datetime] = utcnow,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.store = store
        self.user_agent = user_agent
        self.timeout_s = timeout_s
        self.max_bytes = max_bytes
        self.max_redirects = max_redirects
        self.limiter = limiter or HostRateLimiter()
        self.clock = clock
        self._client = client

    def _client_or_new(self) -> httpx.AsyncClient:
        # No Accept here: it is per call (JSON, GRIB2 and RDB all come through this fetcher).
        return self._client or httpx.AsyncClient(
            timeout=self.timeout_s,
            follow_redirects=False,
            headers={"User-Agent": self.user_agent},
        )

    async def fetch(
        self,
        session: AsyncSession,
        *,
        url: str,
        params: dict[str, str] | None,
        allowed_hosts: frozenset[str],
        product_id: str,
        suffix: str = ".json",
        accept: str = "application/json",
        prefix: str = "",
        retention_class: str | None = None,
        timeout_s: float | None = None,
    ) -> FetchResult:
        """GET with redirect host re-validation; archive; return bytes plus the artifact id.

        ``timeout_s`` overrides the fetcher's timeout for this call only: a server-side
        subsetting CGI (NOMADS ``filter_blend.pl``) legitimately takes 15-20 s to answer,
        which would otherwise sit inside the default 30 s and fail intermittently.

        ``prefix`` places the archived object under an object-store key prefix so a
        bucket lifecycle rule can bound one product family (``nbm/`` -> the R2 rule
        ``expire-nbm-90d``); it defaults to none, so every existing key is unchanged.

        ``accept`` is the Accept header for this call — GRIB2 wants
        ``application/octet-stream`` and USGS RDB wants ``text/plain``; only JSON is the
        default. ``retention_class`` is recorded on the RawArtifact so an object-store
        lifecycle rule (e.g. 90 days on gridded products, DATA_DOCTRINE §13) can expire the
        bytes while the row survives and provenance can say the grid expired.
        """
        outside = allowed_hosts - PROVIDER_HOSTS
        if outside:
            raise FetchError(
                "unregistered_host",
                f"{sorted(outside)} not in cascade_core.fetch.PROVIDER_HOSTS; "
                "register the host there (with its docs/DATA_SOURCES.md row) before fetching it",
            )
        client = self._client_or_new()
        owns = client is not self._client
        try:
            target = httpx.URL(url, params=params or {})
            response: httpx.Response | None = None
            for _hop in range(self.max_redirects + 1):
                host = urlsplit(str(target)).hostname or ""
                if host not in allowed_hosts:
                    raise FetchError("disallowed_host", f"{host!r} not in allowlist {sorted(allowed_hosts)}")
                async with self.limiter:
                    await self.limiter.wait_turn(host)
                    try:
                        response = await client.get(
                            target,
                            headers={"Accept": accept},
                            timeout=timeout_s if timeout_s is not None else USE_CLIENT_DEFAULT,
                        )
                    except httpx.TimeoutException as e:
                        raise FetchError("timeout", f"{target}: {e!r}") from e
                    except httpx.HTTPError as e:
                        raise FetchError("transport", f"{target}: {e!r}") from e
                if response.is_redirect and response.next_request is not None:
                    target = response.next_request.url
                    continue
                break
            assert response is not None
            if response.is_redirect:
                raise FetchError("too_many_redirects", str(target))
            if response.status_code >= 400:
                raise FetchError("http_status", f"{target} -> {response.status_code}")
            content = response.content
            if len(content) > self.max_bytes:
                raise FetchError("too_large", f"{len(content)} bytes > {self.max_bytes}")
            fetched_at = self.clock()
            key = self.store.put(content, suffix=suffix, prefix=prefix)
            artifact = RawArtifact(
                sha256=sha256_hex(content),
                object_key=key,
                product_id=product_id,
                fetched_at=fetched_at,
                request_url=str(target),
                bytes=len(content),
                http_status=response.status_code,
                content_type=response.headers.get("content-type"),
                retention_class=retention_class,
            )
            session.add(artifact)
            await session.flush()
            lm = response.headers.get("last-modified")
            try:
                last_modified = parsedate_to_datetime(lm) if lm else None
            except (TypeError, ValueError):
                last_modified = None
            return FetchResult(
                url=str(target),
                http_status=response.status_code,
                content=content,
                content_type=artifact.content_type,
                fetched_at=fetched_at,
                sha256=artifact.sha256,
                object_key=key,
                artifact_id=artifact.id,
                last_modified=last_modified,
            )
        finally:
            if owns:
                await client.aclose()
