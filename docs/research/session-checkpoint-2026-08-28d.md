# Session checkpoint — 2026-08-28 (fourth of the date): the visual-continuity pass

Continuation point after the visual-continuity / semantic-geography / glass-UI implementation
mission. Supersedes `session-checkpoint-2026-08-28c.md` for web-surface state; backend state is
unchanged from that checkpoint. Every claim verified at writing time; landed / deployed /
proven distinctions explicit.

## HEAD and tree

- Five commits this pass: `7aaf96f` continuity, `8a98b80` semantics, `09eaa6e` glass,
  `2df4c5a` horizons, plus the checkpoint/CI-headroom commit carrying this file.
- Gates: backend 581 passed + 16 pg passed; web vitest 244 passed (4 new); e2e 22/22 locally
  three times; react-doctor 100, design pass clean except the deliberate em-dash copy
  warnings; ruff, lint-imports clean.
- **CI find**: the 2-core runner failed two e2e specs that pass locally — the scene-capture
  spec (two 30 s ground-settle cycles + two software-GL captures overflow the 90 s default
  since `preloadSiblings` widened the tile set) and snap-to-now's URL assertion (the
  renderer starves the effect that rewrites the URL). Fixed as test headroom, not product
  change: `test.slow()` on the capture spec, 15 s on the URL assertion.

## Landed, deployed, AND proven in production (cascadia.papsukkal.com)

1. **Continuity** — `preloadAncestors`/`preloadSiblings`, `tileCacheSize 600`, globe
   `baseColor` = canvas dark (unloaded ground no longer flashes white), one-shot
   ground-composed event. **LoadingVeil**: real stages (INITIALIZING EARTH → COMPOSING
   TERRAIN → LOADING HYDROGRAPHY → LOADING LIVE STATE), readiness = controller + ground
   composed + hydrography queries settled, 18 s honesty timeout, no percentages. Proven in
   headless captures at t3000 (veil with live stage text) and settled reveal.
2. **Label semantics** — class band-windows (basin: orbital/state/basin ONLY), collision
   standing (city > river > town > water > peak > basin), text-rect screen-space collision,
   chrome exclusion bands, camera.moveEnd re-placement. Basin labels render "SKAGIT BASIN"
   quiet-uppercase on curated editorial anchors (contains-verified in `build_labels.py`,
   recorded as cartographic data). Proven live: SNOHOMISH–SNOQUALMIE BASIN frames the upper
   basin; no basin label at river/local band.
3. **River weight** — per-band screen-pixel width/alpha tables (mainstem 1.2→4.6 px orbital→
   local; tributaries 0 at orbital, whisper at basin), intensity as multiplier only,
   PolylineGlow on selected mainstems at river/local. Proven in scene G (Mount Vernon
   meander carries weight + restrained glow; tributaries quiet at basin band).
4. **Cameras** — tier B visible from basin band, redrawn glyph (dark disc, white halo,
   silhouette; pinned inverts; attention rings), `statusReason` diagnostics
   (shown/hidden-by-band per tier). Coverage 6 → **24** (A:11 B:13) via WSDOT river-named
   titles on `images.wsdot.wa.gov` within basin bboxes (third-party hosts excluded by URL
   host — the layer has no CameraOwner field). Proven live: `/geo/cameras` serves 24; the
   Everett corridor shows Stillaguamish ×2, Snohomish ×2, Ebey Slough.
5. **Glass family** — tokens `glass.chrome/panel/sheet/popover/compact` sharing tint, blur
   (16 px), saturation (150 %), hairline, highlight, shadow; `@supports not
   (backdrop-filter)` and `prefers-contrast: more` fall back near-opaque. Applied: top strip,
   panels (sheet on phone), timeline capsule, search results, field legend, disclaimer
   (attribution NEVER hidden), replay banner, camera cards, provenance popover (dashed border
   kept — the inspection register). Phone: top strip wraps instead of clipping (sweep J find).
6. **Horizon strip datum** — production-only find: five cells repeating "ft (NAVD88)"
   overlapped (the stub fixture has no horizons, so no local surface could show it). Shared
   datum now hoists to the register line once; mixed/partial datums keep full labels
   (`sharedDatum` pure helper, 4 tests).

Production checks after deploy: `/geo/cameras` 24; `/geo/labels` carries curated anchors;
`/system/health` ok, 17/17 jobs; live scene renders the full pass (capture on record); the
horizon strip re-read live after the fix deploy: cells "44.4 ft", register
"OFFICIAL FORECAST · NWRFC · NAVD88" (an immediately-post-deploy read still served the old
edge copy — re-read after propagation before judging a deploy).

## Measured (headless Chromium, software GL, 1440×900 — a floor, not a target)

- Cold reveal 21–23 s (timeout-bound; ground composes 23–27 s); warm ≈ cold because compose
  is CPU-bound on this rig, not network-bound (USGS tiles are cacheable, max-age 86400).
- Zoom-to-settle 8.7–12.3 s per multi-band descent; ancestors stand in throughout (no
  checkerboard, no blank world).
- Production build: 4.56 MB js (1.24 MB gzip); heap 38 MB settled (prod build) vs 179 MB dev.

## Imagery data characteristics (verified against source tiles, not guessed)

- **Collection seams**: straight-edged brightness steps (e.g. the bright urban rectangle over
  Seattle at basin band) are baked into USGS ImageryOnly JPEGs — adjacent NAIP campaigns
  differ in tone. Not a loading bug; not recolourable per-tile within scope.
- **Offshore white voids**: where no ortho collection exists at a mid LOD the service bakes
  OPAQUE WHITE into the tile — verified by fetching `tile/11/705/324` (San Juans), which
  carries a literal white square. Documented in `BasemapProvider.ts`.

## Still open from the mission

- Scene B (state band) has no dedicated capture; orbital and basin bracket it.
- At orbital only 2–3 of 6 basin names survive collision (anchors genuinely cluster at that
  range) — cartographically honest, could be revisited with abbreviated orbital names.
- Camera-glyph vs city-label overlap (Everett) — layers do not share a collision space.
- Dual-layer imagery crossfade not built; preload + cache + dark base + veil covered the
  observed pops, and the remaining tone steps are source-data seams (above).
