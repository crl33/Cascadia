"""NRCS AWDB / SNOTEL adapter (Phase 2A).

Fetches snow water equivalent (WTEQ) for one or more SNOTEL stations.
Batches all configured stations into a single AWDB request to be efficient.

Returns one PrecursorSignal per requested station, or None if data is
unavailable. Stale detection: SNOTEL publishes daily; data older than 3 days
is flagged as stale.

API: https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/data
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

import httpx

from .types import PrecursorSignal

log = logging.getLogger(__name__)

AWDB_DATA_URL = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/data"
USER_AGENT = "CascadeOracle/0.2 (research)"
HTTP_TIMEOUT = 15.0

# Public AWDB labels.
SOURCE_KEY = "nrcs_snotel"
SOURCE_LABEL = "NRCS AWDB / SNOTEL"

STALE_AFTER_DAYS = 3
LOOKBACK_DAYS = 14  # enough to compute 7-day trend even if a few values missing


def _trend_label(latest: float, prior: Optional[float]) -> str:
    if prior is None:
        return "insufficient history"
    delta = latest - prior
    if abs(delta) < 0.2:
        return "holding"
    if delta > 0:
        return f"rising +{delta:.1f} in / 7d"
    return f"melting {delta:.1f} in / 7d"


def _interpretation(
    name: str,
    elevation_ft: float,
    latest: Optional[float],
    prior: Optional[float],
    is_stale: bool,
) -> str:
    if latest is None:
        return f"No recent SWE observation from {name} ({int(elevation_ft)} ft)."
    pieces = [f"Upper-basin SWE at {latest:.1f} in (source: {name}, {int(elevation_ft)} ft)."]
    if prior is not None:
        delta = latest - prior
        if abs(delta) < 0.2:
            pieces.append("Snowpack holding steady over the past 7 days.")
        elif delta > 0:
            pieces.append(f"Snowpack rose roughly {delta:.1f} in over the past 7 days.")
        else:
            pieces.append(f"Snowpack melted roughly {abs(delta):.1f} in over the past 7 days.")
    if is_stale:
        pieces.append("Data flagged stale (>3 days since last observation).")
    pieces.append("Representative snowpack signal only — not a flood forecast.")
    return " ".join(pieces)


def _confidence_for_signal(mapping_confidence: str, is_stale: bool, has_value: bool) -> float:
    """Combine mapping confidence + freshness into a 0..1 numeric confidence."""
    base = {"high": 0.85, "medium": 0.65, "low": 0.45}.get(mapping_confidence, 0.5)
    if not has_value:
        return 0.0
    if is_stale:
        return max(0.30, base - 0.30)
    return base


async def fetch_swe_batch(
    client: httpx.AsyncClient,
    triplets: List[str],
    lookback_days: int = LOOKBACK_DAYS,
) -> Tuple[Dict[str, dict], Optional[str]]:
    """Fetch WTEQ for multiple stations in a single AWDB request.

    Returns (per-triplet results, error). Each per-triplet result is:
      { 'values': [(date_str, value_float), ...] }  ordered ascending.
    """
    if not triplets:
        return {}, None

    end = datetime.now(timezone.utc).date()
    begin = end - timedelta(days=lookback_days)
    params = {
        "stationTriplets": ",".join(triplets),
        "elements": "WTEQ",
        "duration": "DAILY",
        "beginDate": begin.strftime("%Y-%m-%d"),
        "endDate": end.strftime("%Y-%m-%d"),
        "periodRef": "END",
        "returnFlags": "false",
        "returnOriginalValues": "false",
        "returnSuspectData": "false",
    }
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}

    try:
        r = await client.get(AWDB_DATA_URL, params=params, headers=headers, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        payload = r.json()
    except Exception as e:
        log.warning("AWDB SWE request failed: %s", e)
        return {}, f"AWDB request failed: {e}"

    out: Dict[str, dict] = {t: {"values": []} for t in triplets}
    for entry in payload or []:
        trip = entry.get("stationTriplet")
        if not trip or trip not in out:
            continue
        elements = entry.get("data", []) or []
        for el in elements:
            if (el.get("stationElement", {}) or {}).get("elementCode") != "WTEQ":
                continue
            vals = []
            for v in el.get("values", []) or []:
                raw = v.get("value")
                d = v.get("date")
                if raw is None or d is None:
                    continue
                try:
                    vals.append((d, float(raw)))
                except (TypeError, ValueError):
                    continue
            vals.sort(key=lambda x: x[0])
            out[trip]["values"] = vals
            break  # first WTEQ block is enough
    return out, None


def build_swe_signal(
    triplet: str,
    name: str,
    elevation_ft: float,
    mapping_confidence: str,
    fetched: dict,
    error: Optional[str] = None,
) -> PrecursorSignal:
    """Construct a PrecursorSignal from the raw fetched data for one station."""
    values = (fetched or {}).get("values", []) or []
    latest = values[-1] if values else None
    prior = values[0] if values else None
    # Pick an entry approximately 7 days before latest if possible.
    if latest and len(values) >= 2:
        try:
            latest_dt = datetime.strptime(latest[0], "%Y-%m-%d").date()
            target = latest_dt - timedelta(days=7)
            best = None
            best_diff = 99
            for d, v in values[:-1]:
                dd = datetime.strptime(d, "%Y-%m-%d").date()
                diff = abs((dd - target).days)
                if diff < best_diff:
                    best_diff = diff
                    best = (d, v)
            if best:
                prior = best
        except Exception:
            prior = values[0]

    is_stale = True
    timestamp_iso = None
    if latest:
        timestamp_iso = latest[0] + "T00:00:00+00:00"
        try:
            dt = datetime.strptime(latest[0], "%Y-%m-%d").date()
            age = (datetime.now(timezone.utc).date() - dt).days
            is_stale = age > STALE_AFTER_DAYS
        except Exception:
            is_stale = True

    latest_v = latest[1] if latest else None
    prior_v = prior[1] if prior else None

    note_parts: List[str] = []
    if error:
        note_parts.append(f"Source error: {error}")
    note_parts.append(_interpretation(name, elevation_ft, latest_v, prior_v, is_stale))
    note_parts.append(_trend_label(latest_v if latest_v is not None else 0.0, prior_v))

    return PrecursorSignal(
        kind="snow_water_equivalent",
        source=SOURCE_KEY,
        source_label=SOURCE_LABEL,
        value=latest_v,
        unit="in",
        timestamp=timestamp_iso,
        confidence=_confidence_for_signal(mapping_confidence, is_stale, latest_v is not None),
        validated=True if latest_v is not None and not is_stale else False,
        notes=" | ".join(note_parts),
    )
