# Session checkpoint — 2026-08-31: the UX reconstruction

Continuation point for the cinematic-client reconstruction mission (§34's 28 items, in
order). Backend state unchanged from `session-checkpoint-2026-08-28d.md`. Every claim
verified at writing time against the running app or production; screenshots in the session
record and `scratchpad/`.

## 1. HEAD

`9afb6ba` (`the opening scene earns its checklist`), pushed; six commits this mission:
`1ae6a37` audit+research, `e8630b7` world/envelope/boot, `743b450` glass/dismissal/language,
`b65721b` rivers/boot-spec/measures, `9afb6ba` orbital cities/framing (+ the checkpoint
commit carrying this file). CI/deploy state at writing: deploy green (production runs
`743b450`+), final CI watching.

## 2. UX findings before implementation

`docs/research/ux-audit-2026-08-31.md` — 17 findings (F1–F17) recorded from a real
first-time-user journey with screenshots, plus 5 systemic diagnoses (no dismissal
primitive, no surface primitive, truth classes as headline typography, readiness ≠ visual
coherence, camera freedom ≠ product scope). Every §-numbered owner complaint reproduced on
pixels before any code changed.

## 3. Design skills

Anthropic `frontend-design` skill loaded and applied (design-lead stance, restraint rules,
copy-as-design); `overseek944/frontend-ui-ux-skill` audit method summarized in the liquid-
glass decision doc (5 pillars + Definition-of-Done; its "gratuitous glassmorphism" flag
shaped the edge-only refraction). `ui-ux-pro-max` present but unused — two overlapping
skills sufficed (§0's own warning).

## 4. Glass research/decision

`docs/research/liquid-glass-decision-2026-08-31.md`. Verdict **C — reproduce with
primitives**: universal CSS specular rim (mask-composite ring) + Chromium-gated edge-band
backdrop refraction (per-surface canvas displacement maps, sRGB interpolation, neutral
center for text) at ULTRA/HIGH; chromatic multi-pass deliberately NOT shipped (compositor
freeze data); LOW = today's frosted, byte-for-byte. Implemented in
`design-system/refraction.ts` (~150 lines, zero deps) + `surface.css`.

## 5. PNW camera constraints

`camera/envelope.ts`: HARD_DOMAIN [-128, 44, -116.5, 51.5] (globe shader-discarded +
imagery never requested outside), SOFT_ENVELOPE [-124.8, 45.8, -119.8, 49.6] (moveEnd
spring-back, pure clamp, 5 tests), zoom 600 m–1,800 km, north-up constrainedAxis, look
disabled, per-band tilt caps (15°→50° from nadir). Wandering to Europe/planet is
impossible; the spring is cinematic (0.7 s minimum-jerk, always loses to the hand).

## 6. Top-down camera

CASCADIA_VIEW/BASIN_FRAMING at pitch −85° (map-like); FORECAST_POINT −50° (controlled
oblique at local only); home range tightened 1,500→1,150 km so the domain fills the frame.

## 7–8. Loading manifest + real percentage

`app/boot-progress.ts`: renderer 5 % / tile-queue drain 55 % (1 − pending/high-water) /
five discrete boot queries 25 % / live envelope 15 % (degradable). Monotonic clamp; 100 ⇔
SCENE_VISUAL_READY (sustained-empty tile queue — 600 ms — not a transient zero, the F2
blurry-reveal fix). 6 unit tests (weights, monotonicity, delayed-critical, degraded-
optional, 100-gate) + `tests/e2e/web/boot.spec.ts` (3 specs: monotonic+reveal-at-100,
route-delayed critical delays 100, route-failed optional degrades and reveals).

## 9. Cold-start metrics (headless Chromium, dev server, 1440×900)

| | before | after |
|---|---|---|
| cold reveal | 21–23 s (timeout-bound, blurry) | **12.7 s at a true 100 %** |
| ground composed | 23–27 s | **13.4 s** |
| warm reveal | ≈ cold | **10.8 s** |
| zoom-settle per step | 8.7–12.3 s | **5.8 → 1.2 s** |

Drivers: no out-of-domain tile requests (envelope), refinement batching, SSE freeze.

## 10. Imagery transition architecture

Globe: preloadAncestors+siblings, cache 600, `loadingDescendantLimit 64` (detail lands as
areas), `maximumScreenSpaceError` 3.5 during flights → 2 on settle (refine once, in
place). Research doc records the verified "not publicly possible" list (no per-tile fade in
Cesium 1.144 — upstream #8581) so nobody chases it.

## 11. White tiles

`DiscardMissingTileImagePolicy` keyed on verified all-white tile 13/2830/1291 (872 B,
byte-identical across zooms — hash-checked): white offshore tiles now render the PARENT's
real imagery. Measured: white-void fraction 0.0 at every descent step (was whole
coastlines on white).

## 12. River redesign

Two registers separated within doctrine §7.2: line colour = `COLOR.water` (physical
geography, constant); state speaks only through width/alpha lift and the glow — which now
requires intensity ≥ 0.66 or explicit selection (never proximity). At LOCAL the centerline
steps back (alpha 0.9→0.55) so photography carries the channel; no implied width from
centerlines. 14 style tests. NOT done: water polygons at ground scale (no authoritative
polygon source integrated; recorded as future work, §28-item 28).

## 13. Click-away dismissal

`design-system/dismiss.ts` — THE primitive: outside pointerdown (capture) + Escape;
inside-interaction safe; `ignoreCanvas` defers canvas clicks to the pick pipeline, where
`SceneController.onEmptyClick` closes the pinned camera (empty map = click-away) and
marker clicks toggle/replace. Wired: camera card, provenance inspector, settings menu.

## 14. GlassSurface everywhere

`design-system/surface.css` + `GlassSurface.tsx`: five densities × five silhouettes ×
specular rim × refraction contract. ALL 13 floating surfaces compose from it (top strip,
panels ×3, timeline, search results, camera card, provenance inspector, settings menu,
weather strip, disclaimer, replay/event banners, scene-degraded). The material class
carries no `position` (learned: it silently relocated the timeline once).

## 15. Corner geometry

`corner-shape: squircle` (controls/cards/sheets) and `superellipse(1.8)` (large panels)
behind `@supports`, radius ×1.75 to preserve corner weight; plain radius on
Safari/Firefox; capsules stay round by design. Glass never gets clip-path (research: only
corner-shape and border-radius keep blur+hairline+shadow on one silhouette).

## 16. Basin panel IA

1-second read: name → "Low flood susceptibility" (Cascadia-assessment chip). 5-second:
CURRENT "River steady · well below seasonal high flows" / NEXT 72 H "Little rain expected —
11.6 mm over 72 h" / OFFICIAL "No flood stages forecast" (+ category chip). Sentences from
`panels/summary-language.ts` (pure, 5 tests, derived-never-invented; UNKNOWN keeps its
reason). Forensics moved (never removed): hover titles + WHY/Forecasts/Context folds;
regulation/valid-time/outlet-id now in Context.

## 17. Truth-class language

Badges speak human everywhere: Observed / Official forecast / Model / Derived / **Cascadia
assessment** (was EXPERIMENTAL) / Configured / Unknown; categories and freshness sentence-
case. Formal classes stay in contracts and the inspector ("experimental methodology"
remains in provenance detail). Search subtitles still show ids — remaining item 28.

## 18. Cascadia assessment hierarchy

The §18 four-way split is now visible in the summary itself: Observed (current), Cascadia
assessment (headline + next), Official forecast (outlook) — maturation needs a label
change only, no redesign.

## 19–20. Controls removed from chrome

Top strip = wordmark, search, health dot (plain-language title), ⚙ Settings. Motion
(System/Reduced/Full) and Graphics (Ultra/High/Balanced/Low) live in Settings. Band,
flight-state, motion-resolution remain ONLY as visually-hidden diagnostic stamps for
tests/tooling. Motion cannot change label availability (labels re-place on camera settle,
not on motion state); the owner's "names changed with motion" is explained by
flight-vs-cut landing poses producing different collision outcomes — same camera pose now
yields identical labels by construction.

## 21. Timeline

One temporal model: LIVE chip · −72 h ↔ now · local readout once ("Aug 31, 5:53 PM");
scrubbed: AS OF chip + "Aug 30, 1:35 PM · 27 h ago", banner explains replay semantics in
local time; event mode keeps absolute UTC edges (archives are not relative). Full UTC on
hover/aria everywhere. Was seven timestamps; now one (plus the banner's).

## 22. Weather layer controls

WEATHER ☑ Rain (radar · local time) ☑ Snow (model · local time) + inspector chip — the
checkbox SHOWS/HIDES the wash (verified live against the renderer). The provenance
inspector opens viewport-aware (upward from bottom chrome — the F12 page-push is gone) and
dismisses like everything else.

## 23. Labels

Class semantics kept; tier-1 cities join orbital (mission's own standing: city beats
basin, so the frames yield along I-5 and return at state band); basin labels capped by the
zoom ceiling (no more names floating in space — the space is unreachable).

## 24. Cameras

24 verified cameras (A:11/B:13); glyphs legible; preview cards clamp to the viewport
(F14); card metadata speaks human ("Why this camera?"). Diagnostics unchanged
(statusReason + dev console).

## 25. Browser screenshots

Session record: audit set (F1–F17), veil with real percentage, envelope home (before/after
framing), production acceptance scene, new Skagit panel, phone stack, continuity descent
frames (`scratchpad/continuity-*.png`).

## 26. Performance

§9 above, plus: white-fraction probe 0.0 across descent; heap 202 MB dev headless (cache
600 + preloads; prod build measured 38 MB last pass — re-measure post-deploy); glass
compositor cost not isolated this session (rim is ~free CSS; refraction is
Chromium-tier-gated and OFF at balanced default) — remaining item 28.

## 27. Tests/gates

Unit 263 passed (+14 this mission: boot 6, envelope 5, summary-language 5, network 3, less
consolidations) | e2e 22/22 twice locally + boot.spec 3/3 | react-doctor 100 | tsc, ruff,
lint-imports clean. E2e specs re-pinned to the human labels and local-time banner (UTC
moved to title attributes).

## 28. Deployed / production-proven

Deploy of `743b450` verified live: production home scene captured (PNW-only, top-down,
glass chrome, one-time timeline, human weather strip — the §27 checklist). Final CI on
`9afb6ba` was in flight at writing; verify then amend if red.

## Remaining UX defects / future work (honest list)

- Search result subtitles still expose `basin:`/`fp:nwps:` ids (§17 residue).
- Basin-arrival choreography (F8: panel appears mid-flight) unaddressed.
- Water polygons at ground scale (§10's last mile) need an authoritative source (NHD
  area geometry) — a provider decision, not a style change.
- Glass refraction unverified on a real-GPU Chromium (headless SwiftShader only) and its
  frame cost unmeasured; chromatic pass deliberately unshipped.
- Imagery NAIP tone seams remain (source data; documented in BasemapProvider).
- Vignette-feathered domain edge (research 1d) not built — the hard edge reads acceptably
  as a map sheet at current framings.
- `?basin=` legacy deep links require the `basin:` prefix (unchanged grammar).
