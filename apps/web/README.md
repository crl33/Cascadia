# Cascade Oracle — web spike

The cinematic client for the Skagit flight spike: globe over Cascadia (keyless OpenStreetMap
imagery, ellipsoid terrain, no Cesium ion), search → basin flight → basin panel →
forecast-point marker → river panel, every value badged with its source kind and freshness.

## Run

```bash
cd apps/web
npm install
npm run stub      # terminal 1: fixture-backed stub API on http://localhost:8000
npm run dev       # terminal 2: Vite on http://localhost:5173
```

Open <http://localhost:5173>, type `Skagit`, pick the basin, then click the Mount Vernon
marker (or open <http://localhost:5173/?basin=basin:skagit&fp=MVEW1&motion=reduced>).

### Pointing at the real API

`VITE_API_BASE` selects the backend (default `http://localhost:8000` in dev, same-origin in
production builds). The FastAPI spike
implements the same SPIKE API SPEC, so `VITE_API_BASE=http://localhost:8000 npm run dev`
works against either the stub or `apps/api`. The API must allow the origin
(`CASCADE_CORS_ORIGINS`); the stub allows `http://localhost:5173` and `:4173` plus that env.

### Basemap

`VITE_BASEMAP` selects a registered `BasemapProvider` (`src/layers/basemap/BasemapProvider.ts`);
only `osm-keyless` ships. Keyed providers (ion, vendor imagery) must be registered at startup
and receive their key from a reviewed `/config/public` endpoint — never from the bundle.

### Deep links

`?basin=basin:skagit&fp=MVEW1&motion=reduced|full&band=…` — stable ids only. Load is a cut.

## Test

```bash
npm test                          # vitest (offline, fixtures only)
npm run e2e                       # builds, starts stub + preview, runs Playwright headless
npm run contracts:check           # generated types match packages/contracts/schema
npx react-doctor@latest --verbose
```

Playwright Chromium: `npx playwright install chromium` once. The E2E uses SwiftShader for
WebGL; if WebGL cannot start the app shows a static fallback and the panel assertions still run.
The basemap tiles come from the OSM tile host; without network the globe renders without
imagery and the suite still passes (no pixel comparisons).

## What it does not do (spike)

No hydrographs, timeline, snow/soil/weather layers, SSE, or quality-tier degradation beyond
the store field. Susceptibility, forcing and agreement are UNKNOWN with reasons from the
contract. This client is not an official alert authority; official forecasts and warnings
come from the National Weather Service.
