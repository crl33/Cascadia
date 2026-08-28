# ADR-0021: Terrain comes from a self-built 3DEP quantized-mesh pyramid in R2

- Status: Proposed (decision drafted 2026-08-28; the build and its measurements are their own
  arc, and this ADR moves to Accepted only with the exit test below green)
- Serves: CINEMATIC_ROADMAP "proper terrain" (design direction 2026-08-28: "snow level is
  rising through these elevations" needs elevations); CINEMATIC_ARCHITECTURE's ion-free rule.

## Context

The renderer runs ion-free as doctrine: no Cesium ion account, no ion token in the bundle, no
ion terms binding the deployment. `EllipsoidTerrainProvider` is the current stand-in, which is
why the North Cascades render as a painted flatland — the one thing the muted-world direction
cannot mute its way out of. CesiumJS consumes terrain natively in exactly two open forms:
quantized-mesh tile pyramids (`CesiumTerrainProvider`) and heightmap pyramids (legacy).

What exists without ion:

- **Cesium World Terrain** — ion-gated. Out by doctrine, not by quality.
- **MapTiler / other hosted quantized-mesh** — API keys, usage terms, an external runtime
  dependency for the platform's ground truth. Rejected: the basemap already accepts that
  compromise for OSM tiles, but terrain requests scale with camera motion and a keyed
  third-party in the render loop is a new failure surface the project controls nothing of.
- **AWS Open Data Terrain Tiles (Terrarium PNGs)** — open and keyless, but raster-encoded
  heights need a custom decoding provider and give Cesium none of the mesh-level LOD/skirt
  machinery; the known third-party providers for it are unmaintained. Rejected.
- **Self-built quantized-mesh from USGS 3DEP** — the authoritative national DEM (1/3
  arc-second ≈ 10 m over Washington), public domain, converted once with the established
  `cesium-terrain-builder` (ctb-quantized-mesh) toolchain and hosted as static tiles. The
  deployment already has the shelf to put it on: the R2 bucket behind the Cloudflare edge,
  fronted by the same Pages project that serves the app (a `/terrain/*` route on the
  gateway's include list, `Cache-Control: immutable` — tiles of a DEM do not change).

## Decision

1. Build a quantized-mesh pyramid from 3DEP 1/3" DEM for the seeded window padded to whole
   degrees (W123–W120, N46–N50), zoom 0–12 (≈10 m source resolution stops paying above that),
   with `--extension octvertexnormals` so terrain shading works if lighting is ever enabled.
2. Host it in the existing R2 bucket under `terrain/v1/`; serve via the Pages gateway with
   long immutable caching; `layer.json` at the root names the tiling scheme.
3. The web's `BasemapProvider.createTerrain` returns `CesiumTerrainProvider.fromUrl(<gateway
   terrain URL>)` when configured, `EllipsoidTerrainProvider` otherwise — the fallback stays
   forever (previews, offline dev, and the e2e stub never fetch terrain).
4. Attribution: "USGS 3DEP" joins the credit line; public-domain data, credit as courtesy and
   provenance, not license.

## Exit test (gates Accepted)

- Measured pyramid size on disk and in R2 (estimate: single-digit GB at z12 for 3°x4°; if the
  measurement lands far above that, revisit the max zoom before shipping).
- The deployed scene renders the Cascade crest in relief with `depthTestAgainstTerrain`
  decided deliberately (clamped polylines and ground primitives must not z-fight or sink).
- Camera flights hold frame rate on the bands (the quality-tier machinery may gate terrain to
  `full` motion tiers only).
- The e2e suite stays green with the ellipsoid fallback — terrain is enhancement, never a
  dependency.

## Consequences

- One-time build cost (DEM download tens of GB, hours of ctb runtime) and a few GB standing
  in R2 — against the deployment memory's storage arithmetic, the first standing storage cost
  beyond the raw archive; recorded when measured.
- Terrain interacts with everything clamped: rivers, hatches and outlines all use
  ground-clamping already, which is the right primitive for a terrain future — but
  `depthTestAgainstTerrain` and camera minimum heights need re-verification on real relief.
- The snow/rain-exposure visualization (C3c's hypsometric bands) gains its spatial ground:
  a snow level drawn ON terrain instead of implied by numbers.
