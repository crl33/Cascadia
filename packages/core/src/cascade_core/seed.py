"""Seed reference rows: sources/products (registry), basins (geo fixtures), stations and forecast
points (seed/stations.json). Idempotent: rows are merged by id, never duplicated.

Seed data arrives in one primary file plus named addenda (``ADDENDUM_FILES``, resolved as
siblings of the primary seed file). Each addendum carries its own ``_provenance`` block with the
date its values were verified, and adds fields to rows the primary file already defines rather
than restating them — so a later phase never has to edit a file another phase owns, and no fact
is stated twice in two places. Addendum keys are validated against the primary seed: an unknown
basin id, forecast point id or gauge station id raises instead of silently seeding nothing (a
mis-keyed gauge would otherwise surface as an UNKNOWN with a misleading reason).

On PostgreSQL the seed additionally materializes the PostGIS surface (all regenerable
reference geometry, never value rows — DATA_DOCTRINE append-only rules concern value tables):

- `basin_geometry` from tests/fixtures/geo ``basins_seed_{state,basin}_lod.geojson`` via
  ST_GeomFromGeoJSON. Fixture geometries are Polygons or GeometryCollections that mix the
  basin polygons with flowline LineStrings, so ST_CollectionExtract(…, 3) keeps only the
  polygonal parts and ST_Multi normalizes to the column's MULTIPOLYGON typmod.
- `station.geom` / `forecast_point.geom` from the lon/lat columns via ST_MakePoint.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.models import Basin, DataSource, ForecastPoint, SourceProduct, Station
from cascade_core.registry import PRODUCTS, SOURCES

# Seed addenda, merged in order after the primary seed file. Siblings of the primary file.
ADDENDUM_FILES: tuple[str, ...] = ("p3_surfaces.json",)

#: Pacific time, by its CANONICAL IANA name. Every Washington gauge the platform seeds is in it.
PACIFIC_TIME_ZONE = "America/Los_Angeles"

#: Time zones this seed may write to `station.time_zone`, and the reason the set is this narrow.
#:
#: `PST8PDT` names the same zone as `America/Los_Angeles`, but the two are NOT interchangeable at
#: runtime. `PST8PDT` is a legacy POSIX alias, and the deployment image (`python:3.14-slim`,
#: infra/Dockerfile) ships Debian's `tzdata` WITHOUT `tzdata-legacy`: 486 resolvable keys over
#: 436 distinct zone files, with the POSIX aliases and most `backward` links dropped. It
#: resolves `America/Los_Angeles`; it raises `ZoneInfoNotFoundError` for `PST8PDT`,
#: `US/Pacific`, `EST5EDT` and `MST7MDT` (verified 2026-08-27).
#:
#: A developer laptop resolves all of them, which is what made the resulting defect look
#: intermittent rather than constant. Seeded `PST8PDT` stamped daily means at the local day
#: boundary from a laptop and at UTC midnight in the container, where
#: `climatology.daily_mean_valid_time` degraded it and flagged `day_boundary_assumed_utc`. Every
#: container-written `streamflow_doy_percentile` row from 2026-08-24 to 2026-08-27 carries that
#: flag, and because the two stampings sit 7 h apart — more than `STATE_CHANGE_TOLERANCE_H` —
#: `susceptibility.state_change` refused to pair them, so the 24 h entry every basin published
#: carried `growth: null` with a `reason` instead of a rate.
#: ADR-0017; docs/research/nwis-stat-successor-2026-08-27.md.
#:
#: Widening this set is a deliberate act. Check the new key against the deployment image first:
#:   docker run --rm python:3.14-slim python -c "from zoneinfo import ZoneInfo; ZoneInfo('<key>')"
SEEDABLE_TIME_ZONES: frozenset[str] = frozenset({PACIFIC_TIME_ZONE})

#: NWPS forecast points are all Washington gauges, so their stations carry Pacific time. Stated
#: here rather than per row because the primary seed file does not carry the field at all.
FORECAST_POINT_TIME_ZONE = PACIFIC_TIME_ZONE

_BASIN_GEOMETRY_UPSERT = text(
    """
    INSERT INTO basin_geometry (basin_id, lod, geom)
    VALUES (
        :basin_id,
        :lod,
        ST_Multi(ST_CollectionExtract(ST_SetSRID(ST_GeomFromGeoJSON(:geometry), 4326), 3))
    )
    ON CONFLICT (basin_id, lod) DO UPDATE SET geom = EXCLUDED.geom
    """
)

_POINT_GEOM_UPDATES = (
    text("UPDATE station SET geom = ST_SetSRID(ST_MakePoint(lon, lat), 4326) WHERE lon IS NOT NULL AND lat IS NOT NULL"),
    text("UPDATE forecast_point SET geom = ST_SetSRID(ST_MakePoint(lon, lat), 4326) WHERE lon IS NOT NULL AND lat IS NOT NULL"),
)


def load_basin_features(geo_dir: Path, lod: str) -> dict:
    path = Path(geo_dir) / f"basins_seed_{lod}_lod.geojson"
    return json.loads(path.read_text())


def load_addenda(seed_file: Path) -> dict:
    """Merge the addendum files that sit beside ``seed_file``; missing files are not an error."""
    merged: dict[str, dict] = {"forecast_point_reach_ids": {}, "basin_susceptibility_gauges": {}, "stations": []}
    for name in ADDENDUM_FILES:
        path = Path(seed_file).parent / name
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        merged["forecast_point_reach_ids"].update(data.get("forecast_point_reach_ids", {}))
        merged["basin_susceptibility_gauges"].update(data.get("basin_susceptibility_gauges", {}))
        merged["stations"].extend(data.get("stations", []))
    return merged


def _validate_addenda(addenda: dict, seed: dict, basin_ids: set[str]) -> None:
    """Every addendum key must name something the primary seed defines. Typos raise here."""
    fp_ids = {fp["id"] for fp in seed["forecast_points"]}
    station_ids = {fp["station_id"] for fp in seed["forecast_points"]} | {
        st["id"] for st in addenda["stations"]
    }
    unknown_fps = sorted(set(addenda["forecast_point_reach_ids"]) - fp_ids)
    if unknown_fps:
        raise ValueError(f"seed addendum names unknown forecast points: {unknown_fps}")
    unknown_basins = sorted(set(addenda["basin_susceptibility_gauges"]) - basin_ids)
    if unknown_basins:
        raise ValueError(f"seed addendum names unknown basins: {unknown_basins}")
    for basin_id, cfg in sorted(addenda["basin_susceptibility_gauges"].items()):
        if cfg["gauge_station_id"] not in station_ids:
            raise ValueError(
                f"{basin_id}: susceptibility gauge {cfg['gauge_station_id']!r} is not a seeded station"
            )
    for st in addenda["stations"]:
        if st["basin_id"] not in basin_ids:
            raise ValueError(f"seed addendum station {st['id']!r} names unknown basin {st['basin_id']!r}")


def _validate_time_zones(time_zones: Iterable[str | None]) -> None:
    """Refuse, at seed time, a station time zone this runtime cannot resolve.

    `climatology.daily_mean_valid_time` degrades an unresolvable zone to the UTC day boundary and
    says so with `day_boundary_assumed_utc` — honest, but quiet: the rows keep coming and only the
    flag records that the boundary was guessed. The seed is the one place that can refuse instead,
    and it runs inside the SAME image the jobs do, so a key the container cannot resolve fails
    here, once and loudly, rather than in every derived row for days.

    Both halves are load-bearing. The membership check is runtime-independent, so a legacy alias
    is refused even on a laptop whose tz database happily resolves it; the resolution check is
    runtime-dependent, so an allowed key that this particular image lacks is refused too.

    `None` is not an error. An unknown zone is a legitimate state, and the flag is its whole point.
    """
    for zone in sorted({z for z in time_zones if z}):
        if zone not in SEEDABLE_TIME_ZONES:
            raise ValueError(
                f"seed time zone {zone!r} is not in SEEDABLE_TIME_ZONES "
                f"{sorted(SEEDABLE_TIME_ZONES)}: seed the canonical IANA name, since legacy POSIX "
                "aliases such as 'PST8PDT' are absent from the deployment image's tz database"
            )
        try:
            ZoneInfo(zone)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(
                f"seed time zone {zone!r} is allowed but this runtime's tz database cannot resolve "
                "it, so every daily mean stamped with it would silently assume the UTC day boundary"
            ) from exc


async def seed_all(session: AsyncSession, *, geo_dir: Path, seed_file: Path) -> dict[str, int]:
    counts = {"sources": 0, "products": 0, "basins": 0, "stations": 0, "forecast_points": 0}
    for s in SOURCES:
        await session.merge(DataSource(**s))
        counts["sources"] += 1
    for p in PRODUCTS:
        await session.merge(SourceProduct(**p))  # type: ignore[arg-type]
        counts["products"] += 1
    seed = json.loads(Path(seed_file).read_text())
    addenda = load_addenda(Path(seed_file))
    basin_meta = seed.get("basins", {})
    basin_features = load_basin_features(geo_dir, "state")["features"]
    _validate_addenda(addenda, seed, {f["properties"]["id"] for f in basin_features})
    _validate_time_zones([st.get("time_zone") for st in addenda["stations"]] + [FORECAST_POINT_TIME_ZONE])
    gauges = addenda["basin_susceptibility_gauges"]
    for feature in basin_features:
        props = feature["properties"]
        gauge = gauges.get(props["id"], {})
        await session.merge(
            Basin(
                id=props["id"],
                name=props["name"],
                regulation_class=props["regulation_class"],
                outlet_fp_id=props.get("outlet_forecast_point_id"),
                huc8=list(props.get("huc8", [])),
                centroid=props.get("centroid"),
                bbox=props.get("bbox"),
                geometry_ref=f"/basins/{props['id']}/geometry?lod=basin",
                regulated_by=list(basin_meta.get(props["id"], {}).get("regulated_by", [])),
                # CONFIGURED: which gauge stands in for basin wetness, how far it may be
                # trusted, and the caveat that must be rendered with it (design §2.3).
                susceptibility_gauge_id=gauge.get("gauge_station_id"),
                susceptibility_confidence_ceiling=gauge.get("confidence_ceiling"),
                susceptibility_note=gauge.get("note"),
            )
        )
        counts["basins"] += 1
    for st in addenda["stations"]:
        # Stations with no NWPS forecast point (the unregulated Sauk proxy for the Skagit).
        await session.merge(
            Station(
                id=st["id"],
                agency=st["agency"],
                external_id=st["external_id"],
                name=st["name"],
                basin_id=st["basin_id"],
                lon=st["lon"],
                lat=st["lat"],
                vertical_datum=st.get("vertical_datum"),
                time_zone=st.get("time_zone"),
                tidal_class=st.get("tidal_class"),
            )
        )
        counts["stations"] += 1
    reach_ids = addenda["forecast_point_reach_ids"]
    for fp in seed["forecast_points"]:
        await session.merge(
            Station(
                id=fp["station_id"],
                agency="usgs",
                external_id=fp["usgs_site"],
                name=fp["name"],
                basin_id=fp["basin_id"],
                lon=fp["lon"],
                lat=fp["lat"],
                vertical_datum=fp["datum"],
                time_zone=FORECAST_POINT_TIME_ZONE,
                tidal_class=fp.get("tidal_class"),
            )
        )
        counts["stations"] += 1
        await session.merge(
            ForecastPoint(
                id=fp["id"],
                lid=fp["lid"],
                name=fp["name"],
                station_id=fp["station_id"],
                basin_id=fp["basin_id"],
                upstream_lids=list(fp.get("upstream_lids", [])),
                downstream_lids=[],
                reach_id=reach_ids.get(fp["id"], fp.get("reach_id")),
                datums=[fp["datum"]],
                rfc="NWRFC",
                wfo="SEW",
                in_service=True,
                lon=fp["lon"],
                lat=fp["lat"],
            )
        )
        counts["forecast_points"] += 1
    bind = session.bind
    if bind is not None and bind.dialect.name == "postgresql":
        # Pending merges must be real rows before the SQL-level geometry writes below:
        # session.execute(text(...)) does not autoflush the unit of work.
        await session.flush()
        counts["basin_geometries"] = 0
        for lod in ("state", "basin"):
            for feature in load_basin_features(geo_dir, lod)["features"]:
                await session.execute(
                    _BASIN_GEOMETRY_UPSERT,
                    {
                        "basin_id": feature["properties"]["id"],
                        "lod": lod,
                        "geometry": json.dumps(feature["geometry"]),
                    },
                )
                counts["basin_geometries"] += 1
        for stmt in _POINT_GEOM_UPDATES:
            await session.execute(stmt)
    await session.commit()
    return counts
