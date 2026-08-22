"""NOAA NWPS adapter (async, httpx).

Fetches official flood stage thresholds by NWS LID.
"""
from __future__ import annotations

import logging
from typing import Optional, Tuple

import httpx

from .types import FloodThresholds

log = logging.getLogger(__name__)

NWPS_GAUGE_URL = "https://api.water.noaa.gov/nwps/v1/gauges/{lid}"
USER_AGENT = "CascadeOracle/0.1 (research)"
HTTP_TIMEOUT = 12.0
NO_DATA_SENTINEL = -9000


def _stage(cats: dict, key: str) -> Optional[float]:
    cat = cats.get(key)
    if not isinstance(cat, dict):
        return None
    for k in ("stage", "value", "ft"):
        v = cat.get(k)
        try:
            if v is None:
                continue
            fv = float(v)
            if fv <= NO_DATA_SENTINEL:
                return None
            return fv
        except (TypeError, ValueError):
            continue
    return None


async def fetch_nwps_thresholds(client: httpx.AsyncClient, lid: Optional[str]) -> Tuple[Optional[FloodThresholds], Optional[str]]:
    """Returns (thresholds, error_message). thresholds is None if NWPS could not provide categories."""
    if not lid:
        return None, "No NWPS LID configured"

    url = NWPS_GAUGE_URL.format(lid=lid)
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    try:
        r = await client.get(url, headers=headers, timeout=HTTP_TIMEOUT)
        if r.status_code == 404:
            return None, f"NWPS LID '{lid}' not found (404)"
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return None, f"NWPS request failed: {e}"

    flood = data.get("flood") or {}
    cats = flood.get("categories") or {}

    action = _stage(cats, "action")
    minor = _stage(cats, "minor")
    moderate = _stage(cats, "moderate")
    major = _stage(cats, "major")

    if not any(v is not None for v in (action, minor, moderate, major)):
        return None, "NWPS response missing flood categories"

    return (
        FloodThresholds(
            action=action, minor=minor, moderate=moderate, major=major,
            unit="ft",
            source="official_nwps",
            source_label="Official NWS / NWPS",
            validated=True,
            notes="Authoritative thresholds from NOAA NWPS.",
        ),
        None,
    )
