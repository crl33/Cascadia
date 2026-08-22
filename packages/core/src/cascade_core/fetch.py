"""The one outbound HTTP path every provider adapter uses (vibesec addendum §1).

Allowlisted hosts only (re-validated on every redirect hop), hard timeout, max response bytes,
User-Agent with contact, per-host minimum interval + concurrency cap, and archive-before-parse:
the raw bytes are written to the object store and a RawArtifact row is flushed BEFORE the bytes
are returned to any parser. The API process never constructs one of these.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlsplit

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.models import RawArtifact
from cascade_core.objectstore import ObjectStore, sha256_hex
from cascade_core.timeutils import utcnow


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
        return self._client or httpx.AsyncClient(
            timeout=self.timeout_s,
            follow_redirects=False,
            headers={"User-Agent": self.user_agent, "Accept": "application/json"},
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
    ) -> FetchResult:
        """GET with redirect host re-validation; archive; return bytes plus the artifact id."""
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
                        response = await client.get(target)
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
            key = self.store.put(content, suffix=suffix)
            artifact = RawArtifact(
                sha256=sha256_hex(content),
                object_key=key,
                product_id=product_id,
                fetched_at=fetched_at,
                request_url=str(target),
                bytes=len(content),
                http_status=response.status_code,
                content_type=response.headers.get("content-type"),
            )
            session.add(artifact)
            await session.flush()
            return FetchResult(
                url=str(target),
                http_status=response.status_code,
                content=content,
                content_type=artifact.content_type,
                fetched_at=fetched_at,
                sha256=artifact.sha256,
                object_key=key,
                artifact_id=artifact.id,
            )
        finally:
            if owns:
                await client.aclose()
