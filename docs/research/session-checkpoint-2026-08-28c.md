# Session checkpoint 2026-08-28c — the cinematic satellite-first world

**HEAD at this checkpoint:** see `git log` (amended below after the final push of this doc).
**Mission:** turn the Cesium hydrology interface into a cinematic, satellite-first,
spatiotemporal flood-intelligence world — research → implement → verify → deploy.
**Contract:** 1.6.0. **Alembic:** 0007 (unchanged this session). **Truth doctrine:** intact —
every new layer carries its register; no cinema implies science anywhere.

## Session commits

- `64c1dfc` — satellite-first imagery (USGS orthoimagery default, per-provider grades, OSM
  demoted to explicit fallback) + app-owned GNIS labels (band budgets/priority/spacing).
- `12f1193` — static flood geography (FEMA NFHL + NLD levees, /geo/flood pre-compressed,
  Skagit outlet gap explicit) + flood-observation camera network v1 (9 curated, tiers WITH
  reasons, DOM preview cards, gateway S3-latest redirect, pin deep-links) + forecast horizons
  (contract 1.6.0, NOW/+12/+24/+48/+72 from the stored official series).
- (this doc's commit) — visual proofs + checkpoint.

## Landed vs deployed vs production-proven

| Piece | Landed | Deployed | Production-proven |
|---|---|---|---|
| USGS satellite basemap + dynamic attribution | ✓ | ✓ (Pages) | scenes verified vs stub; Pages serves the new client |
| GNIS labels (/geo/labels + LabelsLayer) | ✓ | pushed | pending Railway swap (BUILDING ~40 min at checkpoint) |
| Flood geography (/geo/flood + floodplain/levees layers + panel note) | ✓ | pushed | pending Railway swap |
| Cameras (/geo/cameras + markers + preview host) | ✓ | pushed | **gateway frame redirect LIVE**: 302 → USGS S3 `_newest.jpg`, real 465 KB Skagit frame 7 min old fetched through cascadia.papsukkal.com |
| Horizons (1.6.0) | ✓ | pushed | pending Railway swap (`horizons: []` from old container) |
| Health | — | — | `ok`, 17/17 throughout |

## Decisions with terms evidence (docs/research/*-2026-08-28.md)

- **Imagery:** USGS `USGSImageryOnly` — public domain, keyless, CORS `*`, hard z16 cap over
  WA, $0. Esri keyless is legally unclean (E300); NAIP has no public tiles (WMS only); EOX is
  CC BY-NC-SA. Multi-tier collapses to one PD provider + optional future NAIP focus layer.
- **Terrain:** unchanged (ADR-0021 pyramid already deployed).
- **Cameras:** USGS HIVIS/NIMS (PD, CORS-open S3, at-gauge) + WSDOT keyless ArcGIS layer
  ("low volume" + hold-harmless; stills hotlink, ~5 min refresh). Kent Green River cameras
  DEAD (frozen 2025-12-11 / 404) — the HTTP-200-is-not-freshness lesson. Snohomish Contrail
  login-walled; King County APIM-keyed; Seattle ArcGIS layer works (658 cams) but is urban.
  WSDOT Traveler AccessCode = free email form (owner action, optional — adds CameraOwner/IsActive).
- **Flood geo:** FEMA NFHL layer 28 GeoJSON recipes verified live (incl. NULL-subtype SFHA
  lesson); layer 0 availability probed at basin OUTLETS — the Skagit delta has NO digital
  FEMA data (effective or preliminary), recorded as `partial_edges_only` and stated in the
  panel. NLD2 API keyless; terms: shareable by anyone.
- **Labels:** GNIS Domestic Names (PD, keyless S3); editorial tiers are recorded judgment;
  (name, class, county) resolution because GNIS collides (Seattle's Mount Baker neighborhood).
- **Sensors:** matrix in the audit file. Highest-value ingestable gap: Pierce County KiWIS
  (keyless, 338 stations, Puyallup coverage; REDISTRIBUTION TERMS UNVERIFIED — verify before
  ingesting). King County/Snohomish need owner keys. Ecology flow network is archive-grade.

## Camera counts (mission §29)

Discovered machine-readable: WSDOT 1,701; Seattle 658; USGS WA 14. Classified flood-relevant
by verified evidence: 9 curated (5 WSDOT image-verified river cameras + 4 USGS at-gauge/
overflow); Tier A 2 (both AT gauge 12200500/MVEW1, 170 m), Tier B 7. Reasons stored per
camera; orientation only where provider-stated (WSDOT CompassDirection). Frame costs: only
visible cameras fetch, bucketed to each camera's own cadence (USGS 15 min, WSDOT 5 min);
gateway list+redirect ≤ ~1/min/camera under cache.

## Visual scenes verified (docs/research/img/*-2026-08-28.*)

orbital (real PNW from space + basin orientation), basin (Bellingham/Everett/rivers/peaks
labels over imagery), flood zones + levees (Snoqualmie valley slate wash + bronze dashes;
Skagit meander levee baselines), camera card (spatially anchored, honest offline fallback,
tier reasons), live Skagit frame (through the production gateway), Event Mode in the new
world, phone viewport. E2E 22 green ×3 runs; baselines re-pinned on imagery.

## Gates at checkpoint

Backend 581 + 16 pg; web 233 + e2e 22; contracts:check OK (generator now compiles standalone
roots); ruff/mypy(hydrology 0)/lint-imports clean; doctor 100; query budgets 17; perf
baselines regenerated twice (1.5.0→1.6.0, version-string-only diffs).

## Open items / blockers

- Railway deploy of `12f1193` BUILDING ~40 min at checkpoint (prior builds ~6 min) — if
  wedged, the next push supersedes; verify /geo/*, horizons, flood wire size after swap.
- WSDOT AccessCode, King County APIM key, Snohomish Contrail login, Earthdata (VIIRS): owner.
- E2E river-scene baseline caught tiles mid-load (timing) — watch for flakes; consider a
  tile-settle wait.
- Panel in Event Mode shows live-now envelope against the stub (stub limitation, pre-existing).

## Dependency-ordered continuation

1. Verify the Railway swap (geo routes, horizons, flood wire bytes, SSE still streams).
2. Live-world scene pass on production (labels+zones+cameras over real terrain) + commit those proofs.
3. Camera dynamic attention keyed to OFFICIAL evidence (mission §14) — needs an alert/warning
   fixture to verify honestly.
4. Hydrographic water polygons + restrained animated material at local band (mission §6);
   quality-tier gating.
5. Oblique crest-showcase camera (gates ADR-0021 Accepted; churns baselines deliberately).
6. C4: WPC QPF as forecast fields (same field_raster machinery; timeline-future design).
7. Pierce KiWIS terms verification → ingestion; CO-OPS tide gauges for tidal reaches.
8. Perf lab pass: entity counts under all layers at river band; imagery request counts/tier.

## Final amendment (2026-08-29 ~01:2x UTC)

Additional commits after the checkpoint body above:

- `ffb49a7` — e2e visual scenes gate on `data-tiles-pending` (SceneController stamps it from
  `tileLoadProgressEvent`); the mid-load-baseline flake class is closed and the pinned river
  scene now shows Mount Vernon's ring levees crisply.
- `f0bfaa3` — official-evidence camera attention (ring glyph + one-band tier promotion, CAP
  alert or official 72 h category ≥ action, straight off the envelope; derived surfaces can
  never light a camera; card states the reason verbatim) + the phone bottom-sheet pass
  (≤640 px: panel capped 46vh, the world stays the interface; verified 390×844).

**Deployment blocker (external):** Railway's builder was wedged from ~23:56Z — one build
stuck BUILDING 75+ min, its superseding deploy REMOVED by an async-completing cancel
mutation that had "timed out" (lesson: Railway cancels are async; a timeout is not a no-op),
then two consecutive deployments stuck QUEUED without ever building (00:37, 00:53). The old
container (`c9739e5`, contract 1.5.0) served healthily throughout — health `ok` 17/17 at
every probe — and the already-deployed NEW Pages client degrades gracefully (satellite
imagery + terrain live now; labels/cameras/flood/horizons 404 → honest absence until the
swap). No action needed on recovery: the newest commit auto-deploys. FIRST verification
after the swap: /system/version = f0bfaa3+, /geo/{labels,cameras,flood} 200 (flood wire
~1.3 MB gzip), horizons non-empty on MVEW1, SSE content-type intact, then the live-world
scene pass + committed proofs.

**Session totals:** 6 commits (`64c1dfc`…`f0bfaa3`); contract 1.6.0; gates at close: backend
581 + 16 pg, web 238, e2e 22×4 runs, doctor 100, ruff/mypy/lint-imports clean, budgets 17.
