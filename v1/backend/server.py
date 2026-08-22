"""Cascade Oracle — FastAPI entrypoint (Phase 1.5 + Phase 2A)."""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.middleware.cors import CORSMiddleware

from lib.cache import (
    SNAPSHOT_TTL_SECONDS,
    get_all_snapshots,
    get_refresh_attempt,
    get_snapshot,
    is_snapshot_fresh,
    load_station_configs,
    record_refresh_attempt,
    seed_or_upgrade_stations,
    snapshot_age_seconds,
    upsert_snapshot,
)
from lib.orchestrator import build_all_snapshots, build_one_snapshot
from lib.precursors import (
    get_layer_status,
    refresh_snotel_layer,
)
from lib.snotel_stations import BASIN_SNOTEL
from lib.stations import BASIN_GROUPS
from lib.types import (
    PrecursorLayerStatus,
    StationSnapshot,
    StationsResponse,
    SystemStatus,
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
log = logging.getLogger("cascade_oracle")

mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Cascade Oracle starting up — seeding/upgrading station config.")
    try:
        await seed_or_upgrade_stations(db)
    except Exception as e:
        log.exception("Station seed/upgrade failed: %s", e)
    yield
    client.close()


app = FastAPI(title="Cascade Oracle API", version="0.2.0", lifespan=lifespan)
api = APIRouter(prefix="/api")


async def _refresh_all_into_cache() -> List[StationSnapshot]:
    configs_all = await load_station_configs(db)
    configs = [c for c in configs_all if c.active]
    snaps: List[StationSnapshot] = []
    errors: List[str] = []
    succeeded = 0
    try:
        snaps = await build_all_snapshots(configs)
    except Exception as e:
        log.exception("Global refresh failed: %s", e)
        errors.append(f"Global refresh exception: {e}")
        await record_refresh_attempt(
            db,
            ok=False,
            errors=errors,
            stations_attempted=len(configs),
            stations_succeeded=0,
        )
        return []

    for s in snaps:
        if s.gage_height.available:
            succeeded += 1
        try:
            await upsert_snapshot(db, s)
        except Exception as e:
            log.warning("Failed to cache snapshot %s: %s", s.id, e)
            errors.append(f"cache write failed for {s.id}: {e}")

    ok = succeeded > 0
    await record_refresh_attempt(
        db,
        ok=ok,
        errors=errors,
        stations_attempted=len(configs),
        stations_succeeded=succeeded,
    )
    return snaps


async def _ensure_fresh_all() -> List[StationSnapshot]:
    cached = await get_all_snapshots(db)
    configs_all = await load_station_configs(db)
    active_configs = [c for c in configs_all if c.active]

    if cached and len(cached) >= len(active_configs) and all(
        is_snapshot_fresh(s) for s in cached if s.id in {c.id for c in active_configs}
    ):
        order = {c.id: i for i, c in enumerate(active_configs)}
        cached_active = [s for s in cached if s.id in order]
        cached_active.sort(key=lambda s: order.get(s.id, 999))
        return cached_active

    log.info("Cache miss or stale — refreshing %d active stations.", len(active_configs))
    return await _refresh_all_into_cache()


async def _system_status(snaps: List[StationSnapshot], total: int, active: int) -> SystemStatus:
    with_data = sum(1 for s in snaps if s.gage_height.available)
    last_refresh = max((s.fetched_at for s in snaps), default=None)
    age = min((snapshot_age_seconds(s) for s in snaps), default=10**9)
    remaining = max(0, SNAPSHOT_TTL_SECONDS - age)
    notes: List[str] = []
    if with_data < active:
        notes.append(f"{active - with_data} station(s) returned no current observations.")
    last_attempt = await get_refresh_attempt(db)
    if last_attempt.attempted_at and not last_attempt.ok:
        notes.append("Last refresh attempt did not fully succeed.")
    return SystemStatus(
        ok=with_data > 0,
        stations_total=total,
        stations_active=active,
        stations_with_data=with_data,
        last_global_refresh_at=last_refresh,
        cache_seconds_remaining=remaining,
        last_attempt=last_attempt,
        notes=notes,
        phase=2,
        phase_label="Phase 2A • Snowpack Precursor Active",
        precursors=get_layer_status(),
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@api.get("/")
async def root():
    return {
        "service": "Cascade Oracle",
        "version": "0.2.0",
        "phase": 2,
        "phase_label": "Phase 2A • Snowpack Precursor Active",
        "description": "Real-time flood foresight platform for Washington State rivers.",
    }


@api.get("/system/status", response_model=SystemStatus)
async def system_status():
    snaps = await get_all_snapshots(db)
    configs = await load_station_configs(db)
    active = sum(1 for c in configs if c.active)
    return await _system_status(snaps, len(configs), active)


@api.get("/system/basins")
async def system_basins():
    return {"basins": BASIN_GROUPS}


@api.get("/system/precursors", response_model=PrecursorLayerStatus)
async def system_precursors():
    """Returns the precursor layer's last known status (snowpack + future phases)."""
    return get_layer_status()


@api.post("/system/precursors/refresh", response_model=PrecursorLayerStatus)
async def system_precursors_refresh():
    return await refresh_snotel_layer()


@api.get("/system/snotel-stations")
async def system_snotel_stations():
    """Returns the per-basin SNOTEL configuration for transparency."""
    return {"snotel_stations": BASIN_SNOTEL}


@api.get("/stations", response_model=StationsResponse)
async def list_stations():
    snaps = await _ensure_fresh_all()
    configs = await load_station_configs(db)
    active = sum(1 for c in configs if c.active)
    return StationsResponse(
        fetched_at=datetime.now(timezone.utc).isoformat(),
        stations=snaps,
        system=await _system_status(snaps, len(configs), active),
    )


@api.get("/stations/{station_id}", response_model=StationSnapshot)
async def get_station(station_id: str):
    cached = await get_snapshot(db, station_id)
    if cached and is_snapshot_fresh(cached):
        return cached

    configs = await load_station_configs(db)
    cfg = next((c for c in configs if c.id == station_id), None)
    if not cfg:
        raise HTTPException(status_code=404, detail=f"Station '{station_id}' not found")
    if not cfg.active:
        raise HTTPException(status_code=410, detail=f"Station '{station_id}' is inactive")

    snap = await build_one_snapshot(cfg)
    try:
        await upsert_snapshot(db, snap)
    except Exception as e:
        log.warning("Failed to cache snapshot %s: %s", snap.id, e)
    return snap


@api.post("/stations/{station_id}/refresh", response_model=StationSnapshot)
async def refresh_station(station_id: str):
    configs = await load_station_configs(db)
    cfg = next((c for c in configs if c.id == station_id), None)
    if not cfg:
        raise HTTPException(status_code=404, detail=f"Station '{station_id}' not found")
    if not cfg.active:
        raise HTTPException(status_code=410, detail=f"Station '{station_id}' is inactive")
    snap = await build_one_snapshot(cfg)
    try:
        await upsert_snapshot(db, snap)
    except Exception as e:
        log.warning("Failed to cache snapshot %s: %s", snap.id, e)
    return snap


@api.post("/refresh", response_model=StationsResponse)
async def refresh_all():
    snaps = await _refresh_all_into_cache()
    configs = await load_station_configs(db)
    active = sum(1 for c in configs if c.active)
    return StationsResponse(
        fetched_at=datetime.now(timezone.utc).isoformat(),
        stations=snaps,
        system=await _system_status(snaps, len(configs), active),
    )


app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
