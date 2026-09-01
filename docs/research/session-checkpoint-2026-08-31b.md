# Session checkpoint — 2026-08-31 (second): the visual-continuity correction pass

The §31 report, item by item, with evidence. Supersedes `session-checkpoint-2026-08-31.md`
for scene/camera-preview state. Frames referenced live in the session scratchpad
(`harness-before/`, `harness-after/`, `film/`, `edge-*.png`, `max-out-after.png`).

1. **HEAD**: this checkpoint's commit (post `da27ec2`); working tree at gate time carried
   the correction pass in one batch. All gates below.

2. **Checkerboarding root cause** — two distinct mechanisms, proven by frame inspection:
   (a) DURING GESTURES: Cesium refines tile-by-tile with no per-tile fade (verified absent
   in 1.144's whole surface pipeline; upstream #8581) — mixed generations under a moving
   camera; (b) ZOOM-OUT RING: freshly revealed periphery renders coarse ancestors beside
   the crisp former-view center (harness BEFORE frame A-007: a hard vertical LOD seam
   column at Bellingham). Fix shipped: refinement FREEZES during manual gestures
   (`maximumScreenSpaceError` 3.5 on wheel/pointer, debounced 350 ms restore) exactly as
   it already did for flights, and `loadingDescendantLimit` 64→128 so restored refinement
   lands as whole composed regions. AFTER frame A-007: the seam column is gone; the view
   is uniformly detailed. Motion now shows a UNIFORMLY coarse frame (film contact sheet,
   mid-zoom frame) — coherence over sharpness, one composed refine on idle.

3. **Tile seams root cause** — remaining hard-edged tone steps are IN THE SOURCE JPEGS
   (adjacent NAIP campaigns; verified 2026-08-29 against raw tiles, still visible at the
   AFTER A-007 bottom-left corner). Not a loading defect. The real fix is §25/§26: a
   Cascadia-owned regional mosaic with unified grading — recorded as the next imagery
   project (licensing basis: USGS/USDA public domain permits derivatives; verify the
   specific collection notes before building).

4. **White blocks root cause** — THREE cases, each handled: (a) whole-tile baked white →
   `WhiteTileDiscardPolicy` (decoded-tile inspection, any zoom) → parent imagery renders;
   (b) HALF-void coastal tiles (cannot discard without losing the real half — the owner's
   "especially around water") → `colorToAlpha = WHITE @ 0.008` in the globe shader,
   verified in GlobeFS.glsl to compare the RAW texture pre-grade → void pixels become the
   dark canvas; (c) out-of-domain → never requested (envelope). Harness: white fraction
   0.0 in every frame of every trajectory, before-and-after fix sets compared at the
   owner's exact framing.

5. **Blue-void max zoom root cause** — two contributors: the zoom ceiling (1.8 Mm) pulled
   far beyond the domain's angular size, and the domain ended in a shader-discard razor
   cut. Fixes: ceiling 1,250 km (max-out ≈ the composed home framing) + a feathered
   vignette imagery layer (`edge-vignette.ts`, one static 512² canvas draped over the
   domain's outer 16%) dissolving the world into the canvas.

6. **Scene-composition architecture chosen** — freeze-and-batch (uniform coarse during
   motion + whole-region substitution on idle) + readiness-gated boot veil + vignetted
   domain. A snapshot-plate/dual-scene layer was evaluated and NOT shipped this pass: a
   static plate would hide the flight itself, and a second Viewer doubles GPU cost for a
   defect the freeze already removes from perception (film reviewed at 1× and
   frame-by-frame). Re-open if the owner still perceives assembly.

7. **Double buffering tested?** — dual-Viewer and framebuffer approaches were researched
   (cesium-continuity doc: no public offscreen composition; `scene.tweens` private) and
   cost-estimated (~2× GPU memory + duplicated tile cache); rejected for this pass in
   favor of §6's approach. Not tested live — recorded honestly.

8. **Readiness definition** — boot: SCENE_VISUAL_READY (renderer + sustained-empty tile
   queue 600 ms + data tasks + live). In-session transitions: the tile queue's
   sustained-zero within the CURRENT view (the queue is exactly the frustum's need — the
   research-verified semantics of `tileLoadProgressEvent`).

9. **Fallback behavior** — white → parent imagery (discard) or canvas-dark (shader);
   failed fetch → Cesium ancestor upsample; provider absence → never white. A slowdown
   degrades DETAIL (ancestors), never coverage.

10. **Max-out treatment** — `max-out-after.png`: the PNW fills the frame, vignette
    dissolves every edge, cities + basin cluster read. Pinned as the §23 regression
    artifact. Height clamps at exactly 1,250,000 m (probed).

11. **Click-away root cause** — clicking LAND picks the BASIN POLYGON: a hit, not an
    empty click, so the empty-click-only rule kept the card open (my earlier e2e clicked
    open ocean — insufficient, as §12 suspected). Fix: any non-camera entity hit unpins
    first, then selects. New e2e clicks REAL canvas land and asserts card gone + basin
    panel open. 3/3 passing.

12. **Placement solver** — `card-layout.ts`: 8 scored candidates, hard in-viewport
    requirement, occlusion-area + connector-length + edge-direction scoring, stickiness
    against frame flip-flop, honest clamp fallback. Pure, deterministic.

13. **Occlusion regions** — `[data-occlusion]` on top strip, panels, timeline, weather
    legend, disclaimer; `overlay-layout.ts` collects live rects (600 ms cache in the
    card's track loop). No component hardcodes another's pixels.

14. **Viewport-overflow property tests** — 500 seeded-LCG anchors including off-edge:
    zero overflow (plus phone-viewport case). Edge probes on the live app: five anchor
    positions, all boxes within safe bounds, placements flip correctly (top→below,
    right→left) — `edge-*.png`.

15. **GlassSurface adoption** — the camera card was ALREADY on the glass classes; the
    material was dead because the wrapper's per-frame `transform` made it a Backdrop
    Root (research-documented trap). Positioning is now left/top from the solver — no
    transform anywhere in the card subtree.

16. **Camera material** — live computed style on the card body:
    `backdrop-filter: blur(16px) saturate(1.5)` (probed at all five edge positions);
    rim + squircle from the system; refraction tier applies as everywhere else.

17–18. **Frame-time / GPU-RAM** — headless proxies: zoom-settle 5.8→1.2 s per step
    (unchanged from the prior pass); heap 202 MB dev / 16 MB prod build (unchanged — the
    vignette is one static tile; the freeze REDUCES in-motion tile churn). Real-GPU
    frame-time profiling remains un-run (headless SwiftShader only) — open item.

19. **Transition recording** — `film/transition-film-2026-08-31.webm` (max-out → local →
    back, 1280×800), reviewed at 1× and via 4 s contact sheets: no checkerboard, no
    white, no void, no glass instability; one single-frame corner artifact during ascent
    (partially decoded tile at the frame edge) noted. An auto preview appears at local,
    solver-placed, glassed, live WSDOT frame with attribution.

20. **Pinned max-zoom screenshot** — `max-out-after.png` (§10 above).

21. **Camera edge screenshots** — `edge-center/top/bottom/left/right.png` with boxes and
    placements logged.

22. **Gates** — unit 274 passed (283 with skips; +7 solver, +2 preview-math retunes,
    style pins), e2e full suite at gate time (result in the session log; dismissal 3/3,
    boot 3/3 included), react-doctor clean, tsc clean.

23. **Deployed / production-proven** — pushed and CI-watched this session; production
    bundle + health verified after deploy (see session log for the post-deploy probe).

24. **Still between this and fully cinematic** — the NAIP tone seams (source data; owned
    regional mosaic is the answer — §26 investigation is the next imagery milestone);
    real-GPU frame profiling; the mid-motion frame is deliberately soft (coherent-coarse)
    — if the owner wants sharp-during-motion, that IS the dual-scene project, costed in
    item 7; camera view-wedge avoidance (§16) not implemented (orientation exists on some
    WSDOT cams; solver hook is ready).
