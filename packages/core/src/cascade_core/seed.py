"""Seed reference rows: sources/products (registry), basins (geo fixtures), stations and forecast
points (seed/stations.json). Idempotent: rows are merged by id, never duplicated.

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
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.models import Basin, DataSource, ForecastPoint, SourceProduct, Station
from cascade_core.registry import PRODUCTS, SOURCES

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


async def seed_all(session: AsyncSession, *, geo_dir: Path, seed_file: Path) -> dict[str, int]:
    counts = {"sources": 0, "products": 0, "basins": 0, "stations": 0, "forecast_points": 0}
    for s in SOURCES:
        await session.merge(DataSource(**s))
        counts["sources"] += 1
    for p in PRODUCTS:
        await session.merge(SourceProduct(**p))  # type: ignore[arg-type]
        counts["products"] += 1
    seed = json.loads(Path(seed_file).read_text())
    basin_meta = seed.get("basins", {})
    for feature in load_basin_features(geo_dir, "state")["features"]:
        props = feature["properties"]
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
            )
        )
        counts["basins"] += 1
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
                time_zone="PST8PDT",
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
                reach_id=fp.get("reach_id"),
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
