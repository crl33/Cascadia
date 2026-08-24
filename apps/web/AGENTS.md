# apps/web — agent entry (Cascadia Papsukkal web spike)

React 19 + TypeScript strict + Vite 8 + CesiumJS 1.144, npm. The renderer presents; it does
not define. Nothing in this app computes a hydrologic quantity — it renders contracts from
`packages/contracts` (generated into `src/contracts/generated.ts`, parsed with zod in
`src/contracts/schemas.ts`).

## Module boundaries (context boundaries — open only what the task needs)

| Folder | Owns | May import |
|---|---|---|
| `src/app/` | shell, deep-link parse/serialize, SceneView (ref-held container), SceneDataBridge (query → controller), error boundaries around panels only | everything except `cesium` |
| `src/state/` | Zustand store: selection, band, motion setting, active layers, time (`now`), quality tier, flight state. **No Cesium types, no server data.** | nothing renderer-side |
| `src/api/` | TanStack Query client, keys by entity id + `{asOf}` segment, typed fetchers with zod + AbortSignal forwarding `as_of`. `VITE_API_BASE` (dev default `http://localhost:8000`; production build is same-origin; `npm run e2e` builds against the stub origin). | contracts, state (asOf keying only) |
| `src/scene/` | `SceneController` (viewer lifecycle, layer registry, selection → framing, picking), `SemanticZoomController` + `bands.ts` (band math, hysteresis), `bridge.ts` (the ONLY store ↔ controller subscription) | cesium, camera, layers |
| `src/camera/` | `CameraController` (initial Cascadia view, basin/forecast-point framing, durations, interrupt, reduced-motion cut + veil), pure `flight-math.ts` | cesium, design-system/motion |
| `src/layers/` | `contract.ts` (SceneLayer), `basemap/` (keyless OSM + ellipsoid; registry hook for other providers), `basins/`, `rivers/` — each `style.ts` is the only place semantic state becomes presentation | cesium, contracts, design-system/tokens |
| `src/panels/` | BasinPanel, RiverPanel, Hydrograph (hand-rolled SVG + pure `hydrograph-math.ts`), ProvenanceLine, formatting. Every scientific value shows its source-kind badge + freshness; the badge opens the per-value provenance popover (`design-system/ProvenancePopover`, testid `layer-inspector`). | api, state, design-system, contracts |
| `src/interactions/` | SearchBox (semantic events only) | api, state |
| `src/timeline/` | TimelineController (rAF-coalesced knowledge-time commits, replay aborts), TimelineBar scrub UI, pure 72 h window math | api, state, panels/format, design-system |
| `src/design-system/` | `tokens.css`/`tokens.ts`, `motion.ts` (the only durations/easings), `badges.ts` (source_kind → word + glyph + tone), `ProvenancePopover` + `provenance-record.ts` (per-value inspector v1; rows carry `inspector-*` testids) | contracts types |
| `src/event/` | Event Zero replay (P2): event registry (window/default-framing config citing docs/EVENT_ZERO.md), EVENT-time cursor filters, EventBanner, ForecastEvolution table. Event mode fetches archived windows ONCE (no `as_of` — ADR-0010) and filters client-side | api, state, contracts, panels (format/math/ProvenanceLine), design-system, timeline/window |
| `dev/` | fixture-backed stub API (`stub-api.mjs` server, `stub-router.mjs` shared router, `stub-data.mjs` pure builders, `stub-load.mjs` Node fs loader) | Node only for load/server; router is edge-safe |

ESLint enforces: `panels/`, `state/`, `api/`, `interactions/`, `app/`, `timeline/` never import `cesium`.

## Rules (react-quality skill, enforced by review)

- React orchestrates; Cesium renders. No React state per animation frame or camera move; the
  controllers quantize to semantic events (`bandChanged`, `started/settled/interrupted`, `picked`).
- No Cesium types in the store or props. `SceneHandle` is an opaque brand.
- No science in components: trend, headroom, categories, freshness come from the contract.
- Provenance is mandatory UI: a value without a `prov` badge is a defect. UNKNOWN renders as
  UNKNOWN with its reason — never calm, green or zero.
- Reduced motion is a first-class path: every flight has a cut (veil → setView → veil out).
  Deep-link load is always a cut.
- Contracts are generated, never hand-typed: `npm run contracts:gen` / `contracts:check`.
- Colour is never the only carrier (badge word + glyph; category words printed).
- Motion tokens live only in `design-system/motion.ts`; colours only in `design-system/tokens.*`.

## Commands

```
npm run dev            # Vite on :5173 (expects an API on VITE_API_BASE, default :8000)
npm run stub           # fixture-backed stub API on :8000 (PORT to override)
npm run build          # tsc --noEmit + vite build (copies Cesium static assets, CESIUM_BASE_URL)
npm run preview        # serves dist on :4173
npm test               # vitest: band math/hysteresis, style mapping, badges, deep link, camera math, contract fixtures, stub envelopes vs JSON Schema (ajv)
npm run e2e            # build + Playwright (headless Chromium, SwiftShader) against stub + preview; screenshots → tests/e2e/__screenshots__/
npm run contracts:gen  # regenerate src/contracts/generated.ts from packages/contracts/schema/*.json
npm run contracts:check
npm run lint           # eslint (boundary rule included)
npm run doctor         # npx react-doctor@latest --verbose
```

Bands (spike tuning, `src/scene/bands.ts`): orbital > 900 km, state 900–450 km, basin
450–90 km, river 90–8 km, local < 8 km effective height (pitch-corrected), ±12 % hysteresis.
