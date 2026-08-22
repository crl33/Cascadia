"""Cascade Oracle — PRECURSOR layer (Phase 2A SNOTEL active).

This module attaches snowpack signals to each StationSnapshot via the
BasinPrecursors model. SNOTEL is fetched in batch (all configured stations
in a single AWDB call) and cached for one hour.

Phase 2B/2C/2D will add precipitation, soil moisture, and a basin tension
score. Their slots already exist on BasinPrecursors and are kept None until
active.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import httpx

from .snotel import (
    SOURCE_LABEL as SNOTEL_LABEL,
    build_swe_signal,
    fetch_swe_batch,
)
from .snotel_stations import BASIN_SNOTEL, SnotelStationConfig, get_snotel_configs
from .types import BasinPrecursors, PrecursorLayerStatus, PrecursorSignal

log = logging.getLogger(__name__)


# In-memory cache (per-process). Keyed by basin_group → (BasinPrecursors, fetched_dt).
_CACHE: Dict[str, Tuple[BasinPrecursors, datetime]] = {}
_LAST_LAYER_STATUS: PrecursorLayerStatus = PrecursorLayerStatus()
CACHE_TTL_SECONDS = 60 * 60  # 1 hour — SNOTEL publishes daily


def _cache_fresh(now: datetime, fetched: datetime) -> bool:
    return (now - fetched).total_seconds() < CACHE_TTL_SECONDS


async def refresh_snotel_layer() -> PrecursorLayerStatus:
    """Fetch SWE for ALL configured SNOTEL stations in a single batch and update cache.

    Returns a PrecursorLayerStatus describing the snowpack layer.
    """
    global _LAST_LAYER_STATUS
    configs: List[SnotelStationConfig] = get_snotel_configs()
    triplets = [c.triplet for c in configs if c.active]
    if not triplets:
        _LAST_LAYER_STATUS = PrecursorLayerStatus(
            snowpack_active=False,
            note="No SNOTEL stations configured.",
        )
        return _LAST_LAYER_STATUS

    timeout = httpx.Timeout(15.0, connect=8.0)
    errors: List[str] = []
    async with httpx.AsyncClient(timeout=timeout) as client:
        fetched_map, err = await fetch_swe_batch(client, triplets)
        if err:
            errors.append(err)

    now = datetime.now(timezone.utc)
    successes = 0
    for cfg in configs:
        signal = build_swe_signal(
            triplet=cfg.triplet,
            name=cfg.name,
            elevation_ft=cfg.elevation_ft,
            mapping_confidence=cfg.confidence,
            fetched=fetched_map.get(cfg.triplet) or {},
            error=err if (cfg.triplet not in fetched_map and err) else None,
        )
        # Decorate with metadata
        signal.station_name = cfg.name
        signal.station_id = cfg.triplet
        signal.station_elevation_ft = cfg.elevation_ft
        signal.mapping_confidence = cfg.confidence
        signal.mapping_note = cfg.mapping_note
        signal.is_stale = (
            (signal.value is None) or (not signal.validated and signal.value is not None)
        )

        bp = BasinPrecursors(
            basin_group=cfg.basin_group,
            snow_water_equivalent=signal,
            precipitation_24h=None,
            soil_moisture=None,
            basin_tension_score=None,
            computed_at=now.isoformat(),
            available=signal.value is not None,
            note=(
                "Snowpack precursor active. Precipitation, soil moisture, and basin-tension "
                "layers are pending in upcoming phases."
            ),
        )
        _CACHE[cfg.basin_group] = (bp, now)
        if signal.value is not None:
            successes += 1

    layer_status = PrecursorLayerStatus(
        snowpack_active=successes > 0,
        snowpack_basins_with_data=successes,
        snowpack_basins_total=len(configs),
        snowpack_last_attempt_at=now.isoformat(),
        snowpack_last_attempt_ok=successes > 0 and not errors,
        snowpack_errors=errors,
        precipitation_active=False,
        soil_moisture_active=False,
        basin_tension_active=False,
        note=(
            "Phase 2A: snowpack precursor active. "
            "Phase 2B (precipitation), 2C (soil), 2D (basin tension) pending."
        ),
    )
    _LAST_LAYER_STATUS = layer_status
    return layer_status


def get_layer_status() -> PrecursorLayerStatus:
    return _LAST_LAYER_STATUS


async def get_or_refresh_snotel_for_basin(basin_group: str) -> Optional[BasinPrecursors]:
    if not basin_group:
        return None
    now = datetime.now(timezone.utc)
    cached = _CACHE.get(basin_group)
    if cached and _cache_fresh(now, cached[1]):
        return cached[0]
    # Fall through to a refresh; this also seeds the cache.
    await refresh_snotel_layer()
    cached = _CACHE.get(basin_group)
    return cached[0] if cached else None


async def attach_precursors(basin_group: str) -> Optional[BasinPrecursors]:
    """Attach precursor data for a basin's StationSnapshot.

    Phase 2A: returns SNOTEL-backed BasinPrecursors if the basin has a mapping;
    otherwise returns a 'no mapping' BasinPrecursors so the UI can render an
    explicit unavailable state instead of hiding the section.
    """
    if not basin_group:
        return None

    has_mapping = any(b["basin_group"] == basin_group for b in BASIN_SNOTEL)
    if not has_mapping:
        return BasinPrecursors(
            basin_group=basin_group,
            snow_water_equivalent=PrecursorSignal(
                kind="snow_water_equivalent",
                source="none",
                source_label=SNOTEL_LABEL,
                value=None,
                unit="in",
                timestamp=None,
                confidence=0.0,
                validated=False,
                notes="No SNOTEL station mapped to this basin yet.",
                is_stale=True,
                mapping_confidence="none",
                mapping_note="No upstream SNOTEL mapping configured for this basin.",
            ),
            available=False,
            note="No SNOTEL mapping configured for this basin.",
        )

    return await get_or_refresh_snotel_for_basin(basin_group)
