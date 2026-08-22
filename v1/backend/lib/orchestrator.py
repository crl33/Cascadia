"""Orchestrates USGS + NWPS + risk computation per station, with Phase 2A precursors."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import List

import httpx

from .nwps import fetch_nwps_thresholds
from .precursors import attach_precursors, refresh_snotel_layer
from .risk import compute_risk, is_stale
from .types import FloodThresholds, StationConfig, StationSnapshot
from .usgs import PARAM_DISCHARGE, PARAM_GAGE_HEIGHT, fetch_usgs_iv

log = logging.getLogger(__name__)


def _thresholds_from_fallback(cfg: StationConfig) -> FloodThresholds:
    fb = cfg.fallback_thresholds_ft
    has_values = isinstance(fb, dict) and any(
        fb.get(k) is not None for k in ("action", "minor", "moderate", "major")
    )
    if has_values:
        if cfg.fallback_validated:
            return FloodThresholds(
                action=fb.get("action"),
                minor=fb.get("minor"),
                moderate=fb.get("moderate"),
                major=fb.get("major"),
                unit="ft",
                source="configured_validated",
                source_label="Configured (validated)",
                validated=True,
                notes=cfg.fallback_notes,
            )
        return FloodThresholds(
            action=fb.get("action"),
            minor=fb.get("minor"),
            moderate=fb.get("moderate"),
            major=fb.get("major"),
            unit="ft",
            source="configured_pending",
            source_label="Pending validation",
            validated=False,
            notes=cfg.fallback_notes
            or "Threshold values configured locally; validation pending.",
        )
    return FloodThresholds(
        action=None,
        minor=None,
        moderate=None,
        major=None,
        unit="ft",
        source="thresholds_unavailable",
        source_label="Thresholds unavailable",
        validated=False,
        notes=cfg.fallback_notes,
    )


async def build_snapshot(client: httpx.AsyncClient, cfg: StationConfig) -> StationSnapshot:
    errors: List[str] = []

    usgs_task = fetch_usgs_iv(client, cfg.usgs_site)
    nwps_task = fetch_nwps_thresholds(client, cfg.nwps_lid)
    usgs, (nwps_thresholds, nwps_err) = await asyncio.gather(usgs_task, nwps_task)

    gh = usgs[PARAM_GAGE_HEIGHT]
    dq = usgs[PARAM_DISCHARGE]
    if not gh.available:
        errors.append(f"USGS gage height unavailable: {gh.note}")
    if not dq.available:
        errors.append(f"USGS discharge unavailable: {dq.note}")

    if nwps_thresholds is None:
        if nwps_err:
            errors.append(nwps_err)
        thresholds = _thresholds_from_fallback(cfg)
    else:
        thresholds = nwps_thresholds

    state, reason = compute_risk(gh.latest, thresholds)
    stale = is_stale(gh.latest_at)

    snap = StationSnapshot(
        id=cfg.id,
        name=cfg.name,
        river=cfg.river,
        basin=cfg.basin,
        basin_group=cfg.basin_group,
        usgs_site=cfg.usgs_site,
        nwps_lid=cfg.nwps_lid,
        lat=cfg.lat,
        lon=cfg.lon,
        active=cfg.active,
        notes=cfg.notes,
        gage_height=gh,
        discharge=dq,
        thresholds=thresholds,
        risk_state=state,  # type: ignore[arg-type]
        risk_reason=reason,
        is_stale=stale,
        fetched_at=datetime.now(timezone.utc).isoformat(),
        errors=errors,
    )
    # Phase 2A precursor attachment (live snowpack). Trust rules: this is a precursor
    # signal only and MUST NOT be used to compute river risk_state.
    try:
        snap.precursors = await attach_precursors(cfg.basin_group)
    except Exception as e:
        log.warning("attach_precursors failed for %s: %s", cfg.id, e)
        snap.precursors = None
    return snap


async def build_all_snapshots(configs: List[StationConfig]) -> List[StationSnapshot]:
    timeout = httpx.Timeout(15.0, connect=8.0)
    # Pre-warm SNOTEL layer once per global refresh so per-station calls hit cache.
    try:
        await refresh_snotel_layer()
    except Exception as e:
        log.warning("SNOTEL layer pre-warm failed (continuing): %s", e)

    async with httpx.AsyncClient(timeout=timeout) as client:
        tasks = [build_snapshot(client, c) for c in configs if c.active]
        return await asyncio.gather(*tasks)


async def build_one_snapshot(cfg: StationConfig) -> StationSnapshot:
    timeout = httpx.Timeout(15.0, connect=8.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        return await build_snapshot(client, cfg)
