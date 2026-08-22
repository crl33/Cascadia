"""MongoDB cache layer for snapshots, station config, and refresh metadata.

Collections (Phase 1.5):
  co_stations  — station configuration (one doc per station)
  co_snapshots — latest normalized snapshot per station (upserted)
  co_meta      — single doc tracking refresh attempts (key='refresh_state')
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from .stations import DEFAULT_STATIONS
from .types import RefreshAttempt, StationConfig, StationSnapshot

log = logging.getLogger(__name__)

STATIONS_COLLECTION = "co_stations"
SNAPSHOTS_COLLECTION = "co_snapshots"
META_COLLECTION = "co_meta"
META_REFRESH_KEY = "refresh_state"
SNAPSHOT_TTL_SECONDS = 300  # 5 minutes


async def seed_or_upgrade_stations(db: AsyncIOMotorDatabase) -> None:
    """Seed defaults if empty; otherwise upgrade existing docs to current schema."""
    coll = db[STATIONS_COLLECTION]
    count = await coll.count_documents({})
    if count == 0:
        log.info("Seeding %d default stations into Mongo.", len(DEFAULT_STATIONS))
        await coll.insert_many([{**s} for s in DEFAULT_STATIONS])
        return
    # Phase 1.5 schema upgrade: ensure new fields exist on each station doc.
    new_fields = ("basin_group", "active", "notes", "fallback_validated", "fallback_notes")
    docs = await coll.find({}, {"_id": 0}).to_list(1000)
    by_id = {d.get("id"): d for d in docs}
    for default in DEFAULT_STATIONS:
        existing = by_id.get(default["id"])
        if not existing:
            await coll.insert_one({**default})
            continue
        update = {}
        for k in new_fields:
            if k not in existing or existing.get(k) is None:
                if k in default:
                    update[k] = default[k]
        if update:
            log.info("Upgrading station %s with fields %s", default["id"], list(update))
            await coll.update_one({"id": default["id"]}, {"$set": update})


async def load_station_configs(db: AsyncIOMotorDatabase) -> List[StationConfig]:
    coll = db[STATIONS_COLLECTION]
    docs = await coll.find({}, {"_id": 0}).to_list(1000)
    if not docs:
        return [StationConfig(**s) for s in DEFAULT_STATIONS]
    out: List[StationConfig] = []
    for d in docs:
        try:
            out.append(StationConfig(**d))
        except Exception as e:
            log.warning("Skipping unparseable station config %s: %s", d.get("id"), e)
    return out


async def get_snapshot(db: AsyncIOMotorDatabase, station_id: str) -> Optional[StationSnapshot]:
    doc = await db[SNAPSHOTS_COLLECTION].find_one({"id": station_id}, {"_id": 0})
    if not doc:
        return None
    try:
        return StationSnapshot(**doc)
    except Exception as e:
        log.warning("Failed to parse cached snapshot for %s: %s", station_id, e)
        return None


async def get_all_snapshots(db: AsyncIOMotorDatabase) -> List[StationSnapshot]:
    cur = db[SNAPSHOTS_COLLECTION].find({}, {"_id": 0})
    docs = await cur.to_list(1000)
    out: List[StationSnapshot] = []
    for d in docs:
        try:
            out.append(StationSnapshot(**d))
        except Exception as e:
            log.warning("Skipping unparseable snapshot %s: %s", d.get("id"), e)
    return out


async def upsert_snapshot(db: AsyncIOMotorDatabase, snap: StationSnapshot) -> None:
    doc = snap.model_dump()
    await db[SNAPSHOTS_COLLECTION].update_one(
        {"id": snap.id},
        {"$set": doc},
        upsert=True,
    )


async def get_refresh_attempt(db: AsyncIOMotorDatabase) -> RefreshAttempt:
    doc = await db[META_COLLECTION].find_one({"key": META_REFRESH_KEY}, {"_id": 0, "key": 0})
    if not doc:
        return RefreshAttempt()
    try:
        return RefreshAttempt(**doc)
    except Exception:
        return RefreshAttempt()


async def record_refresh_attempt(
    db: AsyncIOMotorDatabase,
    *,
    ok: bool,
    errors: List[str],
    stations_attempted: int,
    stations_succeeded: int,
) -> RefreshAttempt:
    now_iso = datetime.now(timezone.utc).isoformat()
    existing = await get_refresh_attempt(db)
    payload = RefreshAttempt(
        attempted_at=now_iso,
        succeeded_at=now_iso if ok else existing.succeeded_at,
        ok=ok,
        errors=errors,
        stations_attempted=stations_attempted,
        stations_succeeded=stations_succeeded,
    )
    await db[META_COLLECTION].update_one(
        {"key": META_REFRESH_KEY},
        {"$set": {"key": META_REFRESH_KEY, **payload.model_dump()}},
        upsert=True,
    )
    return payload


def snapshot_age_seconds(snap: StationSnapshot) -> int:
    try:
        dt = datetime.fromisoformat(snap.fetched_at.replace("Z", "+00:00"))
    except Exception:
        return 10**9
    age = (datetime.now(timezone.utc) - dt).total_seconds()
    return int(age)


def is_snapshot_fresh(snap: StationSnapshot, ttl_seconds: int = SNAPSHOT_TTL_SECONDS) -> bool:
    return snapshot_age_seconds(snap) < ttl_seconds
