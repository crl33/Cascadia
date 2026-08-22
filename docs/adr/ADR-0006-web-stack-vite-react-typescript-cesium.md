# ADR-0006: Web client — Vite + React + TypeScript + CesiumJS (no CRA/CRACO)

- Status: Accepted
- Date: 2026-08-22

## Context
V1 is CRA 5 + CRACO + JavaScript with Emergent tooling and ~35 unused packages (FACT, `docs/V1_AUDIT.md` §3D). The V2 experience is a planetary-scale 3D observatory: terrain, imagery, 3D Tiles, time-dynamic layers.

## Decision
`apps/web` is Vite + React 19 + TypeScript (strict) with CesiumJS 1.144+ as the renderer (Apache-2.0; WebGL2 default; ~1.7 MB gzip core bundle plus static Workers/Assets/Widgets served at `CESIUM_BASE_URL` via `vite-plugin-static-copy` as in Cesium's own Vite example — `vite-plugin-cesium` has not been published since 2024-08 and is avoided; Resium is optional and not used for scene/camera/layers, which stay imperative controllers per ADR-0007), TanStack Query for server state, Zustand for client state, Zod for runtime validation of generated contract types, Vitest + Playwright for tests. Tailwind is kept for panel styling with a token file derived from V1's design system. No UI kit dump; primitives are added one at a time as needed (Radix primitives allowed individually).

## Alternatives considered
- Next.js — SSR adds nothing to a WebGL app and complicates Cesium asset handling.
- MapLibre GL / deck.gl — excellent 2.5D; weaker for globe, terrain-following camera, 3D Tiles and the orbital→local descent that defines the product. Kept as a candidate for the `low` quality tier.
- Three.js custom globe — re-implements what Cesium provides (tiling, terrain, 3D Tiles, time).
- Unreal (Cesium for Unreal) — deferred; the contracts are designed so it can be a second client.

## Evidence (retrieved 2026-08-22)
docs/research/rendering-stack-and-geodata-delivery.json: CesiumJS 1.144.0 (2026-08-04) adds terrain-draped clamped vector polylines/polygons; 1.142 added `MVTDataProvider` (experimental native MVT) and `GeoJsonPrimitive`; an ion-free Viewer needs `baseLayer`, `geocoder:false`, `baseLayerPicker:false` and a non-ion terrain provider; OSM tiles are dev/demo-only by policy (no SLA; heavy use blocked); production basemaps: self-hosted Planetiler→PMTiles (via Martin) or Esri Static Basemap Tiles (2M tiles/month free, token, "Powered by Esri"); ion-free quantized-mesh terrain: MapTiler `terrain-quantized-mesh-v2` (Flex plan) or self-tiled WA DNR/3DEP DEMs with Cesium Terrain Builder; Cesium ion Community plan is non-commercial/<$50K only with a mandatory ion logo and 15 GB/month streaming.

## Consequences
Bundle discipline matters (Cesium is large: code-split and lazy-load the scene). Cesium ion is optional: a `BasemapProvider` abstraction with a keyless default (OSM tiles, ellipsoid terrain) keeps the app runnable without accounts; higher tiers plug in ion/Google/MapTiler keys via public config.
