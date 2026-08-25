# docs/research — dated evidence behind the doctrine

One job: hold the *evidence* (not the conclusions) that `DATA_SOURCES.md`, `EVENT_ZERO.md`
and the ADRs cite. Every file is dated in its name or its `retrieved_at`/summary. Facts decay:
re-verify before relying on anything older than a quarter; providers change endpoints and
policies (USGS legacy decommission, NBM v5.0, HRRR→RRFS, MinIO archived, S-NPP cutoff).

| File | What it is | Independently verified? |
|---|---|---|
| `v1-live-verification-2026-08-22.json` | Live check of the six V1 gauges against USGS NWIS IV, USGS OGC API, NWPS (gauge + stageflow) and AWDB (stations, elements, Dec-2025 Harts Pass SWE) | yes — raw API responses |
| `nwps-usgs-awdb-samples-2026-08-22.json` | Raw samples: NWPS MVEW1 gauge object (crests, impacts, datums, topology), stageflow forecast, USGS OGC monitoring-location and latest-continuous features | yes — raw API responses |
| `hydrology-observations-and-official-forecasts.json` | USGS legacy IV + new OGC API, NWPS API v1, NWPS HEFS API, NWRFC products, NWM v3.1, NWM retrospectives, RouteLink crosswalk | pending (verifier failed on session limit) |
| `weather-forecast-models-and-atmospheric-rivers.json` + `.verify.json` | NWS API, NBM v5.0, HRRR, GFS, GEFS, CW3E/PSL, WPC, snow-level offset, GRIB tooling | yes — 14 confirmed / 0 refuted; corrections listed in the verify file |
| `precipitation-observations.json` | MRMS, MRMS archives, Stage IV, NWRFC QPE, NWS ASOS, Synoptic, RAWS/FEMS, SNOTEL precip, USGS 00045, King County HIC, SPU, Atlas 2/14/15, COOP-HPD | pending |
| `snow-and-soil-state.json` | AWDB/SNOTEL (WA station list by HUC), SNODAS, NOHRSC, SMAP L3/L4, NWM land, NLDAS-2/3, Crop-CASMA, MODIS/VIIRS snow cover, in-situ soil | pending |
| `reservoirs-dams-and-flood-control.json` | USACE CWMS Data API (office NWDP), A2W reporting API, Dataquery, NWRFC/NWPS reservoir stations, USGS reservoir gauges, NID, NLD, HHD/MMD manuals, SCL Skagit, PSE Baker, SPU Cedar/Tolt, LWSC, county systems | pending |
| `static-geospatial-foundations.json` | WBD, NHDPlus HR, 3DHP, NLDI, StreamStats, Lynker hydrofabric, 3DEP, WA DNR LiDAR, exactextract/rasterstats, FEMA NFHL, NLD, Ecology GIS, NWPS metadata, datum offsets, Census/OSM/buildings | pending |
| `rendering-stack-and-geodata-delivery.json` + `.verify.json` | CesiumJS 1.144, ion terms, Google 3D Tiles, OSM/Esri/MapTiler/Mapbox, AWS terrain tiles, quantized-mesh production, 3D Tiles 1.1, point-cloud tooling, WA lidar, COG/TiTiler, PMTiles, Martin, Zarr, GeoParquet, React integration | yes — 13 confirmed / 1 refuted (Node ≥22 landed in 1.141, not 1.142) |
| `backend-stack-and-scientific-tooling.json` + `.verify.json` | PostgreSQL 18 / PostGIS 3.6, TimescaleDB vs pg_partman, FastAPI/Pydantic/SQLAlchemy/Alembic/GeoAlchemy2, Procrastinate vs PgQueuer vs brokers, Prefect/Dagster, object storage (MinIO archived), obstore, xarray/cfgrib/Herbie, raster tooling, Zarr, pint, observability, testing | yes |
| `event-zero-december-2025-western-washington-floods.json` | USGS peaks, NWPS crests, NWS Seattle product timeline (IEM AFOS), CW3E outlooks/summary, USACE operations, declarations, county reporting, antecedent analyses | pending |
| `flood-genesis-mechanisms-2026-08-24.md` | Mechanistic review of flood generation in western WA (old-water paradox, fill-and-spill thresholds, AR orographic transfer + Froude blocking, ROS energy balance, warm vs dry snow drought), the ENSO/PDO position entering WY2027, the non-stationary Mount Vernon stage-discharge relation, and a claim-by-claim verification of `HYDROLOGY.md` | yes — primary data fetched/computed 2026-08-24; literature cited per claim |
| `spike-report-2026-08-22.md` | What the architecture spike proved, commands, invariants checked, known gaps | written by the verification agent |

Status labels inside the files: `FACT` = read on a fetched page (URL given); `INFERENCE` =
not read on a fetched page; `OPEN_QUESTION` = unresolved. "Pending" above means the research
agent's FACT labels stand on their own citations but a second agent has not re-fetched them.

Human check: before a provider adapter is merged, open its rows here and in
`DATA_SOURCES.md` and confirm the endpoint, units, sentinel and cadence facts against a fresh
fetch; record the date in the adapter's `manifest.yaml`.
