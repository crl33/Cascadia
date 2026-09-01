# Cinematic film language for a pure-nadir hydrologic instrument

Research date: 2026-09-01. Lens: FILM (design research, not engineering). Target: `apps/web`
on CesiumJS **1.144.0** (ion-free). Companion research this doc builds on and does not repeat:
[`cesium-continuity-camera-2026-08-31.md`](cesium-continuity-camera-2026-08-31.md) (tile
continuity, envelope, what Cesium cannot do) and
[`liquid-glass-decision-2026-08-31.md`](liquid-glass-decision-2026-08-31.md) (the glass
material and its Backdrop Root trap). Where a shot needs a render-surface mechanism (plate,
SSE freeze, discard policy) this doc points at those files instead of restating them. A
render-surface lens was commissioned the same day; if it publishes, its shots slot into §6.

Verification legend — every claim below carries one of:

- **[dts:N]** `apps/web/node_modules/cesium/Source/Cesium.d.ts` line N (public API)
- **[src:File:N]** `apps/web/node_modules/@cesium/engine/Source/<path>` line N (implementation)
- **[repo:path:N]** a file in this repository, read on the research date
- **[web]** a URL fetched or a search snippet; **[web-snippet]** means the page itself refused
  the fetch (403/404/503) and only the search engine's excerpt was seen — treat as INPUT TO
  RE-VERIFY before quoting anywhere user-facing
- **UNVERIFIED** — a reference we wanted and could not confirm; used as metaphor only

House doctrine this must obey: CINEMATIC_ARCHITECTURE.md §2 (client tweens presentation, never
science), CAMERA_SYSTEM.md §4.1 ("heavy instrument on a stable mount, not a drone"), §9 rules
1–5, §11 (lighting is `cinematic`, never data), VISUAL_TRUTH_DOCTRINE.md (class E, driver named),
and the owner's 2026-09-01 directive recorded in
[repo:apps/web/src/camera/CameraController.ts:14-18]: pure nadir, no angles, anywhere.

---

## 0. Thesis — what "cinematic" means at nadir

The owner's word is "deeply cinematic"; the owner's other words are "no angles" and "one
reveal at rest" (commit `039c24c`). Those are not in tension once the definition is fixed:

> Cinematic = nothing breaks the illusion. Not more motion.

At pure nadir the map is a **still photograph that occasionally moves**. Film feel then comes
from four illusions, each with a named breaker:

| Illusion | What sustains it | What breaks it (observed in this app) |
|---|---|---|
| **Continuity** | one generation of the world per frame; motion is a continuous function of time | tile-by-tile refinement, LOD seam columns (ux-audit F2/F15; checkpoint 2026-08-31b §2) |
| **Composition** | the subject sits where the eye expects; chrome frames rather than occludes | basin centered under the 40 vw panel; labels over open ocean (F5) |
| **Light & material** | one constant light; glass that visibly transmits the live world | flat card not glass (F10); backdrop killed by a transform (checkpoint §15) |
| **Time** | scrubbing reads as weather passing, "now" is a place | seven timestamps (F13); washes that pop on every push |

Everything below serves those four. The reference canon and what each actually licenses is
§1; the numbered doctrine is §2; composition geometry is §3; the shot list is §5; mechanisms
per shot are §6.

---

## 1. Reference frames — what was studied, what transfers, what does not

| Reference | What it says (verified) | What transfers to a nadir instrument | What does NOT transfer |
|---|---|---|---|
| **Google Earth Studio — Easing** [web: https://earth.google.com/studio/docs/making-animations/easing/] | Motion must start and end still and "accelerate or decelerate"; Ease In / Ease Out / Auto Ease; "the steeper the line, the faster the motion"; keep easing "synced across attributes" or the camera "will actually take a *different path*" | The synced-attributes rule is the strongest transferable law: latitude, longitude and height must share one progress function or the path bends. Cesium's `flyToBoundingSphere` already interpolates one path under one `easingFunction` [dts:29138-29150]; never layer a second CSS/JS ease on top of it | Its default eases are ease-in/out beziers on keyframes; Cascadia's camera profile is the minimum-jerk quintic (§2 rule 6) |
| **Google Earth Studio — Camera Target** [web: https://earth.google.com/studio/docs/advanced-features/camera-target/] | Warns against "animating the camera directly above a target" — it can cause "an unwanted 180° 'flip'" | Confirms the nadir decision must be paired with a **locked heading** (0) and no target-tracking rig: at nadir there is no look-at geometry to track, only position and range. The repo already does exactly this: `constrainedAxis = UNIT_Z` [repo:SceneController.ts:147], heading spring-back [repo:envelope.ts:53-54,94-95] | Orbit/spiral/fly-to-and-orbit project types — excluded by CAMERA_SYSTEM §4.1 |
| **Apple HIG — Motion** [web via reader proxy of https://developer.apple.com/design/human-interface-guidelines/motion] | "Add motion purposefully, supporting the experience without overshadowing it"; "Make motion optional"; "Aim for brevity and precision in feedback animations"; "generally avoid adding motion to UI interactions that occur frequently" | The frequency rule is the one this app most needs: hover, scrub and legend toggles are frequent → no world motion, ≤ `--dur-micro` feedback (§2 rules 10, 14). "Optional" is already law: reduced motion = cut [repo:CameraController.ts:130-140] | Nothing — it is fully compatible |
| **NYT / Archie Tse, Malofiej 2016** [web-snippet: Nieman Lab 2016-03 (page 403 on fetch); slides https://github.com/archietse/malofiej-2016] | Readers just want to scroll; a click must be rewarded with something spectacular; graphics were redesigned "2 or 3 times to make it work on both desktop and mobile" | The "click must be rewarded" law maps 1:1 onto selection: **a flight is the reward for a click**, so the arrival must be composed — the panel, the outline, the network, in order (§5 S3). The mobile rule is §5 S8: the phone film is a different film, not a squeezed one | Scrollytelling itself — Cascadia is an instrument, not an article |
| **Heer & Robertson 2007**, *Animated Transitions in Statistical Data Graphics* [web: https://idl.cs.washington.edu/files/2007-AnimatedTransitions-InfoVis.pdf] | Maintain valid graphics during transitions; group similar transforms; use staging for complex transitions; keep transitions as long as needed but no longer; ~1 s baseline (Heer & Robertson citing Robertson et al. [21]; 1.25 s used in their own study, p.4–5); slow-in/slow-out improves predictability and tracking (p.3, "Maximize predictability") | Staging = the basin-selection sequence keyed to progress (CAMERA_SYSTEM §4.5); "valid graphics during transitions" = the plate holds a *true* last frame, never a synthetic one [repo:TransitionPlate.ts:8-11]; 1 s is the dwell budget of §2 rule 9 | Their transitions are between chart encodings; ours are between views of one photograph |
| **van Wijk & Nuij 2003**, *Smooth and efficient zooming and panning* [web-snippet: TU/e PDF 503 on fetch; parameters restated in arXiv 1801.09358 p.3: the user-preferred zoom/pan trade-off ρ was 1.42] | Perceived-velocity metric with speed V and trade-off ρ; for long pans the optimal path zooms out, translates, zooms in; the follow-up paper notes such paths are not smooth "when interrupted" | The cut-vs-flight decision of §2 rule 4 and §4: a flight that must exceed the trackable perceived velocity should either climb (arc) or cut. Interruption behaviour: our `cancelFlight` stop-in-place [dts:29031] is acceptable *because the hand's own gesture replaces the motion* | The ρ value is for free 2D pan-zoom; at nadir inside a 1,250 km ceiling the climb is bounded by the band above (CAMERA_SYSTEM §4.3 arc rule), so ρ is not a tunable here |
| **Flash & Hogan 1985**, minimum-jerk [web: https://www.semanticscholar.org/paper/7d8ac1ed3dc3fc96538372206da015e7dd4b251e] | Point-to-point hand movements minimise integrated squared jerk; bell-shaped velocity | The camera profile `10t³−15t⁴+6t⁵` [repo:motion.ts:24-28] is this exact polynomial; it is why flights feel "weighted" rather than "snapped" | Via-point curvature — our flights are straight lines at nadir |
| **Miyazaki via Ebert 2002** ("ma") [web-snippet: rogerebert.com interview (403 on fetch); secondary: screencraft.org, nocturnalmind.net] | The intentional emptiness between beats; constant tension numbs | §2 rule 9: the settle beat is content. Reveals need silence after them (plate release → hold → panel) | Nothing — but do not quote the passage at length; it is copyrighted interview text |
| **Disney "slow in and slow out", "staging"** (Thomas & Johnston 1981; [web: studiobinder.com summary]) | Ease at both ends; direct attention to one thing at a time | Staging = one primary motion (CAMERA_SYSTEM §9 rule 3); slow-in/out = the quintic | Squash/stretch, anticipation, exaggeration — forbidden by §4.1 |
| **Nielsen response limits** [web: https://www.nngroup.com/articles/response-times-3-important-limits/] | 0.1 s feels instantaneous; 1 s keeps flow of thought; 10 s holds attention | Dwell budgets: feedback ≤ 100 ms; arrival-to-panel ≤ 1 s; the boot veil must show measured progress because it can exceed 10 s (it does: 30 s honesty valve [repo:LoadingVeil.tsx:21]) | — |
| **Windy / earth.nullschool** [web: https://github.com/cambecc/earth README; community thread https://community.windy.com/topic/16097/smoother-animations/3] | earth (MIT) interpolates the 1° GFS grid **spatially** with bilinear interpolation; in the Windy thread a user proposes inserting linearly interpolated frames between forecast hours and another objects that "weather evolution is never linear" — no Windy staff statement was found | The objection is Cascadia's own law: temporal interpolation of values is forbidden (CAMERA_SYSTEM §9 rule 4; CINEMATIC_ROADMAP.md:500). The *film* feel of Windy comes from spatial continuity and constant particle motion, not from fabricated hours. §2 rule 11 | Particle animation — class E, C4 scope, not this pass |
| **Planet Earth II / Studio Ghibli nadir composition** — UNVERIFIED | Searches returned production notes (drones, UHD) and Ghibli flight-scene lists, nothing citable about top-down framing | Used only as metaphor in §3: a nadir drone shot works because the subject *enters and settles* into a held frame; Ghibli establishing shots work because they hold longer than expected | Do not cite as authority |
| **"Chanel rule"** — attribution UNVERIFIED (apocryphal; widely attributed, no primary source found [web: goodreads/quote sites only]) | "look in the mirror and take one thing off" | House name for the subtraction pass (§2 rule 14). Cite as *the house's* rule, not Chanel's | — |

---

## 2. Doctrine — fifteen rules, each with the failure it prevents

Each rule: **statement** → *failure prevented* → mechanism (pointer). Numbers that are house
constants are cited to the file that owns them; numbers proposed here are marked PROPOSED.

**1. The frame is a photograph that moves, never a camera that flies.** Pitch −90, roll 0,
heading 0 at every band; the tilt gesture does not exist [repo:SceneController.ts:146;
envelope.ts:45-51]. All feel comes from composition, light and timing.
*Prevents:* the Google-Earth oblique (ux-audit F3), the 180° flip Earth Studio warns about when
a camera passes over its target, and any "drone" read forbidden by CAMERA_SYSTEM §4.1.

**2. One generation of the world per frame.** During a gesture the whole view renders one LOD
step softer, uniformly [repo:SceneController.ts:168-189, `MOTION_SSE = 3.2`]; at rest the plate
holds the last true frame and the sharp world arrives as one crossfade
[repo:TransitionPlate.ts:18-22, `FADE_MS = 320`]. No frame may show crisp beside blurry.
*Prevents:* the patchwork the owner photographed (checkpoint 2026-08-31b §2; the
`loadingDescendantLimit` lesson at SceneController.ts:121-123).

**3. One primary motion; everything else is subordinate and keyed to it.** While the camera
moves, no panel mounts, no label re-places, no wash swaps. Layer reveals key to flight
progress or to `settled`, never to wall-clock (CAMERA_SYSTEM §9 rule 3; §4.5 tracks).
*Prevents:* the panel appearing over Central America mid-flight (F8). **Still open**:
`App.tsx:41-42` mounts `BasinPanel` on selection alone; nothing reads `flightState`
[repo:state/store.ts:66] — the panel enters at `--dur-panel` before the camera settles.

**4. Cut when the eye cannot track; fly when it can.** A flight exists to preserve the sense of
place. When the destination footprint is inside the current frame, fly (the eye tracks the
target). When it is outside *and* the clamped duration (`maxMs 2400` [repo:motion.ts:14]) would
force perceived velocity past what the eye tracks, do not smear — either climb first (arc rule,
CAMERA_SYSTEM §4.3) or veil-cut (the reduced-motion path, which already exists
[repo:CameraController.ts:132-140]). Decision procedure in §4.
*Prevents:* a 2.4 s blur across the state that reads as a loading glitch, and a flight that
"lands" before its tiles do.

**5. The arrival is the shot; the flight is the cut between shots.** Compose the destination
frame first (§3): subject on the stage, not under the panel; headroom for labels; the network
resolving inside the outline. Then derive the flight from it.
*Prevents:* a basin framed for a full canvas and then covered by a 420 px panel — the current
`flyToBasin` frames against the full frustum [repo:CameraController.ts:92-98] with no stage
offset.

**6. Minimum-jerk for the world, ease-out for chrome, nothing overshoots.** Camera path:
`minimumJerk` [repo:motion.ts:24-28]. Chrome: `--ease-standard` / `--ease-calm`
[repo:tokens.css:19-20]. Cesium ships `ELASTIC_*`, `BACK_*`, `BOUNCE_*` [dts:5697-5834 is the
`EasingFunction` namespace; the forbidden trio sits at 5789-5821 — ~~5697-5769~~ was too short
a range to reach them]; they are forbidden in this app. Cesium's own default for a flight with no easing is `QUINTIC_IN_OUT`
(or `CUBIC_OUT` when descending from above 11.5 km) [src:Scene/CameraFlightPath.js:548-558] —
always pass ours explicitly, as the repo does.
*Prevents:* snap-zoom (ease-out on a 3D camera reads as a lunge — CAMERA_SYSTEM §4.2) and
cartoon overshoot.

**7. Reveal, do not assemble.** A thing appears once, whole, at the moment it is true: the
opening frame only at `SCENE_VISUAL_READY` (100 % ⇔ composed ground, sustained-empty queue
600 ms [repo:SceneController.ts:36; boot-progress.ts:65-76]); the sharp world only when the
queue stays empty 250 ms under the plate [repo:TransitionPlate.ts:20]; a basin outline only
when the flight settles.
*Prevents:* the blurry reveal (F2), tile assembly on screen, and "data before context".

**8. Light is a constant, not a clock.** Analytical mode is the default and the only mode in
analysis (CAMERA_SYSTEM §11): one fixed light, low relief, never solar unless the user asks in
Presentation Mode. Today lighting is off entirely [repo:SceneController.ts:109]; §6 lists the
verified path to a *constant* hillshade if the owner wants relief at river/local band.
*Prevents:* December scenes going black over the very floods we care about; shading mistaken
for data; a second sun fighting the one already baked into NAIP orthoimagery.

**9. Dwell is content.** Every reveal is followed by silence: plate release then hold; flight
settle then ≥ 1 beat before the panel; boot 100 % then `SETTLE_BEAT_MS 400` [repo:LoadingVeil.tsx:22].
Budget: feedback ≤ 100 ms, arrival→panel ≤ 1 s total (Nielsen), never two reveals inside one
`--dur-state` (520 ms) window.
*Prevents:* the numbness of constant tension (Miyazaki's ma) and the "busy" read the owner
called shifting.

**10. The world never moves for a UI event.** Only selection moves the camera. Hover, scrub,
legend toggles, panel open/close, provenance popovers, follow-select: zero camera motion
(follow-select is explicitly selection-only [repo:SceneController.ts:305-341]); timeline scrub
is always a cut (CAMERA_SYSTEM §8 table).
*Prevents:* loss of place and motion sickness on frequent interactions (Apple HIG frequency
rule).

**11. Time reads as weather; values never interpolate.** Between two valid slices only
*opacity* crosses (CAMERA_SYSTEM §9 rule 4); the inspector names the bracketing slices
(LAYER_SYSTEM.md:210). One local time on screen (ux-reconstruction memory). "Now" is a place
on the bar, marked once, not a moving object.
*Prevents:* fabricated in-between values (the Windy objection, VTD class E), seven timestamps
(F13).

**12. Glass must stay silent over the live world.** No `transform`, `opacity < 1`, `isolation`,
`contain: paint` or `will-change` on any ancestor of a glass surface while it animates
(Backdrop Root trap — liquid-glass doc §(c) cautions; checkpoint §15). Enter/leave is an
opacity change on the surface itself (`panel-in` is opacity-only [repo:app.css:60-62] — keep it
that way).
*Prevents:* the material dying mid-animation (the camera card defect).

**13. Interruption is instant and clean; the hand always wins.** Pointer/wheel/key cancels the
flight [repo:CameraController.ts:41-45], drops the plate [repo:TransitionPlate.ts:64-77],
cancels the envelope correction [repo:CameraEnvelope.ts:35-39]. No residual ease, no re-arm
until idle.
*Prevents:* the fighting-the-user feel; the "not smooth when interrupted" defect the hyperbolic
zoom paper attributes to pre-computed paths [web: arXiv 1801.09358 abstract].

**14. The subtraction pass (the house's "Chanel rule").** Before a shot ships, remove one
thing. Hard cap: **one** cinematic effect per shot beyond the world itself (a crossfade, *or*
a hillshade, *or* a vignette — never stacked). The maximum-zoom-out frame is the test frame:
it must read as a map sheet dimming at its margin, not an app icon [repo:edge-vignette.ts:12-16].
*Prevents:* gratuitous glassmorphism (the frontend-ui-ux skill's named anti-pattern, liquid-glass
doc §(d)) and effect stacking.

**15. Reduced motion is the same film with cuts.** Same compositions, same order, same dwell;
flights become veil-cuts (`--dur-micro` veil [repo:app.css:17; CameraController.ts:135-138]),
fades become instant, the plate still works (it is not motion).
*Prevents:* two products; label reshuffles that differ by motion setting (F17's mechanism:
a settle by flight vs by cut lands collision at different positions).

---

## 3. Composition at nadir — framing rules

At nadir the only compositional variables are **scale (range), centre, and what chrome covers**.

**3.1 The stage.** The stage is the canvas minus persistent chrome: top strip (top 64 px),
panels column (right `min(420px, 40vw)`, from 64 px to 96 px above the bottom), timeline
capsule (bottom ≈ 96 px) [repo:app.css:27,54,118]. On desktop the stage is therefore the
left ~60 % of the canvas. On phone (≤ 640 px) the panel is a bottom sheet capped at 46 vh
[repo:app.css:179-189], so the stage is the top ~54 %.

**3.2 Subject placement (PROPOSED).** The selected basin's bounding sphere is framed to the
*stage*, not the canvas: centre at the stage centre, padding `1.1` [repo:CameraController.ts:17]
against the stage's narrowest half-angle. Two verified ways to do it without tilting:
(a) shift the flight destination by the world width of the covered strip (the geometry is
pure: `range · tan(half-angle) · coveredFraction`), using `camera.flyTo({ destination,
orientation: {heading:0, pitch:-π/2, roll:0} })` [dts flyTo options, verified above the
`flyToBoundingSphere` block]; or (b) keep the basin's true centre and offset the **frustum**
with `PerspectiveFrustum.xOffset` / `yOffset` [dts:12758,12762; src:Core/PerspectiveFrustum.js:82-91].
**Units (verification 2026-09-01):** ~~by the covered fraction~~ — the offset is *added to the
near-plane `left`/`right` (`top`/`bottom`)* of the off-centre frustum
[src:Core/PerspectiveFrustum.js:219-222], so a shift of `k` half-widths is
`xOffset = k · near · tan(fovx/2)` (i.e. `k · f.right`), not a bare fraction. Nothing in a
non-VR `Scene` resets it per frame: `Scene.js:1553` zeroes it only when `useWebVR` is toggled
off, and `:3431/:3438` are the VR stereo pass. (b) is cleaner (the camera's lon/lat remain the basin's — follow-select
and deep links stay honest) but it changes what `pickEllipsoid` at canvas centre means
[repo:SceneController.ts:320-323]; if (b) is chosen, follow-select must sample the *stage*
centre. Either way the panel never covers the subject.

**3.3 Headroom.** At nadir "headroom" is label room: basin labels are the "quiet uppercase
frame" [repo:layers/labels/style.ts:41]; leave the top ~12 % of the stage for the basin name
and the river names above the outline. Practically: padding 1.1 on the sphere plus the stage
offset gives this for free on desktop; on phone the sheet eats it, so the phone frame is a
different shot (S8).

**3.4 Thirds.** For a selected forecast point (river shot) the point sits on the stage's
lower-left thirds intersection so the upstream reach reads across the stage and the panel sits
downstream of the eye. PROPOSED; requires the (a)/(b) offset above with a 2D offset rather
than a horizontal one.

**3.5 The frame's edge.** The domain vignette is square-edged and narrow (6 % feather, 0.82
alpha) [repo:edge-vignette.ts:15-16]; it is *the* edge treatment and the only one. At max-out
the ceiling (1,250 km [repo:envelope.ts:40]) equals the composed home framing, so the outermost
frame is a product still, never a sheet in a void.

**3.6 What must never be in frame.** Labels at orbital are `reduced`
[repo:layers/labels/LabelsLayer.ts:46-47] — keep the range cull so no name floats over the
Pacific (F5). Nothing outside `HARD_DOMAIN` is ever drawn [repo:SceneController.ts:130-135].

---

## 4. Pacing — dwell, easing, and the cut-vs-flight decision

**4.1 Dwell table (house constants and one proposal).**

| Beat | Value | Owner |
|---|---|---|
| feedback (hover, selection tick) | `--dur-micro` 140 ms | tokens.css:21 |
| chrome enter/leave | `--dur-panel` 320 ms | tokens.css:23 |
| layer fade / state change | `--dur-state` 520 ms | tokens.css:24; BasinsLayer.ts:160 |
| plate crossfade | 320 ms | TransitionPlate.ts:21 |
| plate settle sustain | 250 ms | TransitionPlate.ts:20 |
| gesture idle before hold | 220 ms (plate) / 260 ms (SSE restore) | TransitionPlate.ts:18; SceneController.ts:177 |
| boot settle beat / boot fade | 400 ms / 700 ms | LoadingVeil.tsx:22-23 |
| flight | 500–2,400 ms, `base 500 + 420·log2(1 + km_w/5)` where `km_w = distance km + 2·|Δheight| km` (`heightWeight 2`, so a pure zoom is not free) | motion.ts:14; flight-math.ts:10-15 |
| **arrival hold before panel** | **PROPOSED 400 ms** (= one settle beat; total settle→panel ≤ 1 s with `--dur-panel`) | new |

**4.2 Easing.** Camera: minimum-jerk (rule 6). Opacity crossfades: `--ease-calm`. Never
ease-in-only on anything visible (a slow start reads as lag under the 100 ms feedback limit).

**4.3 Cut vs flight — the decision procedure (PROPOSED, all inputs already exist).**

```
given from-pose, to-pose (both nadir):
  d      = computeFlightDuration(distance, |Δheight|)            // flight-math.ts
  inView = destination footprint ⊂ current frustum footprint    // Camera.computeViewRectangle
  if motion == 'reduced'                 → CUT (veil)             // existing path
  if inView                              → FLY, duration d
  if !inView and d < maxMs               → FLY with arc (climb ≤ next band up)   // CAMERA_SYSTEM §4.3
  if !inView and d == maxMs (clamped)    → CUT (veil) — the eye could not track it anyway
```

Rationale: the clamp is the honest signal that the geometry exceeds the trackable
perceived-velocity budget (van Wijk & Nuij's metric is exactly this trade-off — the *equation*
"clamped duration ⇒ untrackable" is this doc's inference from their metric, not a result stated
in either paper). Deep links are
already cuts [repo:bridge.ts:15-18]; this extends the same treatment to any hop the film
cannot afford.

---

## 5. Shot list — Cascadia's states as shots

Each shot: *purpose* → *composition* → *choreography (ordered beats)* → *pacing* → *what
breaks it*. Mechanisms are in §6, keyed by shot id.

### S1 — Boot reveal (cold start)

*Purpose:* the first frame is the product still. *Composition:* the home view, 1,150 km nadir
over −122.3/47.6 [repo:CameraController.ts:16]; veil card is system glass, sheet squircle
[repo:LoadingVeil.tsx:120-122]. *Choreography:* (1) veil with measured % (renderer 5 / ground
40 / regional 15 / data 25 / live 15 [repo:boot-progress.ts:42-46]); (2) beneath the veil the
domain warms z5–z9 [repo:domain-warmer.ts:45-50] and the ground composes; (3) at 100 % a 400 ms
settle; (4) one 700 ms fade [repo:LoadingVeil.tsx:22-23]; (5) **silence** — nothing else
animates for one `--dur-state`; (6) basin hairlines are already present (they are part of the
still, not a reveal). *Pacing:* the fade is the only motion; no label fly-in, no outline draw-on.
*Breaks it:* revealing on a transient queue-zero (guarded by the 600 ms sustain), any post-reveal
element that "pops" (labels re-placing on the first settle — LabelsLayer re-places on settle
[repo:LabelsLayer.ts:67]; ensure the boot settle happens *under* the veil).

### S2 — Home (max-out is the same frame)

*Purpose:* the establishing shot; the whole instrument in one frame. *Composition:* PNW fills
the frame, vignette dims the margin, cities and the basin cluster read; the ceiling
(1,250 km) is this frame [repo:envelope.ts:37-40]. *Choreography:* none — it is a still.
Hover: basin edge 1 → 1.6 px at 0.6 alpha [repo:layers/basins/style.ts:52], `--dur-micro`.
*Pacing:* static. *Breaks it:* the "app icon" read from a wide rounded feather (fixed:
edge-vignette.ts:12-14); any label over water; the spring-back arriving with a visible ease
after a pan past the soft envelope (0.7 s minimum-jerk [repo:CameraEnvelope.ts:18] — acceptable
because it is the world settling, not the UI).

### S3 — Select basin (the reward for the click)

*Purpose:* Tse's law — something composed must happen. *Composition (§3.2):* basin on the
stage, panel on the right, name above the outline. *Choreography, keyed to flight progress p
(CAMERA_SYSTEM §4.5 adapted to nadir — no heading phase, no terrain exaggeration):*
(1) p = 0: hover edge holds; (2) p ≈ 0.35: the selected outline begins its `--dur-state` fade
[repo:BasinsLayer.ts:138-166 — exists] so the eye has an anchor before arrival; (3) p = 1
(`settled`): the plate arms if tiles are pending [repo:SceneController.ts:163], sharp ground
crossfades in; (4) **hold 400 ms**; (5) panel `panel-in` 320 ms opacity-only; (6) labels
re-place (collision) *before* the panel is visible — at settle, not after. Under the panel's
enter the world is already still. *Pacing:* flight 500–2,400 ms + 320 plate + 400 hold + 320
panel ≈ ≤ 3.4 s worst case; typical basin hop ≈ 2.2 s. *Breaks it:* the panel mounting
mid-flight (rule 3, open); framing against the full canvas so the panel covers the basin
(rule 5, open); a second wash swap landing during the flight (rule 3 — gate `setData` for
weather layers on `flightState === 'settled'`).

### S4 — Select river (forecast point)

*Purpose:* from basin to a place. *Composition:* 12 km range nadir [repo:CameraController.ts:18];
the point on the lower-left third (§3.4), marker 14 px selected [repo:layers/rivers/style.ts];
river label italic water-hue. *Choreography:* short hop (in view → FLY, ≈ 0.9–1.5 s); marker
grows at `--dur-micro` on settle; the river panel swaps for the basin panel as an opacity
crossfade in place (CAMERA_SYSTEM §9 rule 2: never unmount/remount an element present on both
sides). *Pacing:* the hop is the shortest flight in the film; keep the hold at 400 ms anyway.
*Breaks it:* the hydrograph rendering before the camera settles; camera preview auto-appearing
at river band (it is local-band only [repo:app/camera-preview-math.ts:24-33] — keep).

### S5 — Scrub time (the weather film)

*Purpose:* time passes over a still world. *Composition:* camera does not move (rule 10); one
timeline capsule; one local time. *Choreography:* (1) scrub coalesces to one commit per frame
[repo:TimelineController.ts:36-40]; (2) the wash for the new slice is built off-thread of the
eye (canvas paint, [repo:WeatherFieldLayer.ts:126-177]); (3) the new wash is **added at alpha 0
above the old one and crossfaded over `--dur-ui`–`--dur-state`, then the old is removed**
(continuity doc §1b; `ImageryLayer.alpha` [dts:37105]) — today it is detach-then-attach, i.e. a
pop [repo:WeatherFieldLayer.ts:171-173]; (4) the readout updates instantly (time is data, no
animation [repo:timeline.css:1]); (5) "now" is the LIVE chip in cyan [repo:timeline.css:8],
still. If a "now pulse" is ever added it is a ≤ 2,400 ms `ambient` opacity breathe on the
*chip*, never on the map, and it freezes under reduced motion. *Pacing:* at 10 Hz scrub the
crossfade must be shorter than the commit interval or crossfades pile up — bound it at
`--dur-ui` (220 ms) while dragging and `--dur-state` on release. *Breaks it:* any value
interpolation (rule 11); a wash swap that arrives while the camera flies (rule 3); a scrub that
moves the camera; AS-OF appearing in more than one place (F13).

### S6 — Camera preview (WSDOT card)

*Purpose:* a real photograph inside the photograph. *Composition:* solver-placed, in-viewport,
connector to the world point [checkpoint 2026-08-31b §12-16]; glass, rim, squircle; frame
respects the camera's cadence. *Choreography:* the card fades in at `--dur-ui` **after** the
pin/settle, opacity only; the world point tracks via `postRender` DOM writes
[repo:SceneController.ts:451-476]; a new frame crossfades inside the card (`--dur-ui`) rather
than swapping. *Pacing:* frame cadence is the camera's, not ours; never animate the connector.
*Breaks it:* a `transform` anywhere in the card subtree (Backdrop Root — rule 12, fixed by
left/top placement); the card hanging off-screen on phone (fixed: sheet at ≤ 640 px
[repo:app.css:270-276]).

### S7 — Max-out (zoom-out ring)

*Purpose:* returning to the establishing shot. *Composition:* identical to S2 by construction.
*Choreography:* during the wheel-out the world is uniformly soft (SSE 3.2), the zoom rate
decays toward the ceiling (built-in `ScreenSpaceCameraController` behaviour, continuity doc
Problem 2), the plate captures at gesture end and one crossfade brings detail. *Pacing:*
gesture-driven; the only authored beat is the 320 ms crossfade. *Breaks it:* the LOD ring
(coarse periphery beside crisp centre) — solved by the uniform SSE; height overshooting the
ceiling (clamped at 1,250,000 m, probed — checkpoint §10).

### S8 — Phone

*Purpose:* the same film, re-cut for a vertical frame (Tse's "2 or 3 times"). *Composition:*
stage = top ~54 %; basin framed to that stage (§3.1) — a *taller* range than desktop, not a
crop; sheet at ≤ 46 vh; legend above the sheet; timeline capsule; disclaimer three lines
[repo:app.css:179-195, 306-314]. *Choreography:* S3 with the sheet sliding **only as opacity**
(no transform — rule 12); no camera preview auto at phone width unless pinned. *Pacing:*
same dwell table; flights are shorter in screen-space so the perceived velocity is lower — do
not shorten durations. *Breaks it:* z-order chaos (F14, fixed by the occlusion registry);
framing against the full canvas so the sheet covers the basin.

### S9 — Interruption (every shot's escape hatch)

*Purpose:* the hand wins without a stutter. *Choreography:* pointerdown/wheel/key → flight
cancelled, plate dropped, envelope correction cancelled, panel stays (it is state, not
choreography), labels hold until the next settle. *Breaks it:* any ease that continues after
the gesture starts; a panel that unmounts because the flight was interrupted (`interrupted`
sets `flightState: 'settled'` [repo:bridge.ts:31] — correct: the film treats interruption as a
settle).

---

## 6. Mechanisms per shot — verified Cesium / CSS surface

Shots reference these by id. Continuity-doc mechanisms are named, not restated.

| Id | Mechanism | Verified where | Used by |
|---|---|---|---|
| M1 | Measured boot % + `SCENE_VISUAL_READY`; sustained-zero tile queue (`tileLoadProgressEvent` semantics) | repo:boot-progress.ts; SceneController.ts:243-270; continuity doc §1a | S1 |
| M2 | Domain warm z5–z9 into HTTP cache before reveal | repo:domain-warmer.ts:45-91 | S1, S2, S7 |
| M3 | Uniform-generation SSE during gestures (`globe.maximumScreenSpaceError` 3.2 ↔ 2) | repo:SceneController.ts:176-189; [dts:34720] | S7, all gestures |
| M4 | TransitionPlate snapshot hold + one crossfade (needs `preserveDrawingBuffer`) | repo:TransitionPlate.ts; SceneController.ts:105 | S1, S3, S7 |
| M5 | Camera flight: `flyToBoundingSphere` with explicit `easingFunction` (minimum-jerk), `cancelFlight` on input | [dts:29138-29150, 29031]; repo:CameraController.ts:157-176 | S3, S4, S9 |
| M6 | Stage-composed destination: `camera.flyTo({destination, orientation})` with a shifted destination, **or** `PerspectiveFrustum.xOffset/yOffset` (near-plane units — `k · near · tan(fovx/2)`, see §3.2; persists in non-VR scenes) | [dts: flyTo at 29085-29107; 12758, 12762]; [src:Core/PerspectiveFrustum.js:82-91, 219-222; Scene/Scene.js:1553, 3431-3438] | S3, S4, S8 (PROPOSED) |
| M7 | Whole-layer crossfade for weather washes: second `ImageryLayer` at `alpha` 0 → 1 in `scene.preRender`, then remove old (no built-in tween — `scene.tweens` is not public) | [dts:37105 alpha; 44333 preRender]; continuity doc §1b | S5 |
| M8 | Layer show/hide and outline fades: per-frame alpha via `CallbackProperty` keyed to `MOTION.duration.state` | repo:BasinsLayer.ts:138-166 | S3 |
| M9 | Label re-placement on settle only (screen-space collision) | repo:LabelsLayer.ts:67 | S1, S3 |
| M10 | Envelope spring-back on `moveEnd`, 0.7 s minimum-jerk, cancelled by pointerdown | repo:CameraEnvelope.ts; continuity doc Problem 2 §3 | S2, S7 |
| M11 | Domain vignette (`SingleTileImageryProvider` frame) + `cartographicLimitRectangle` + dark `backgroundColor`, no skybox/atmosphere | repo:edge-vignette.ts; SceneController.ts:130-141; continuity doc §1d | S2, S7 |
| M12 | Glass enter/leave = opacity-only on the surface; no ancestor transform (`panel-in` keyframes) | repo:app.css:60-62; surface.css; liquid-glass doc §(c) cautions | S3, S4, S6, S8 |
| M13 | DOM overlay tracking via `postRender` + `SceneTransforms.worldToWindowCoordinates` (no React per frame) | repo:SceneController.ts:457-476 | S6 |
| M14 | Reduced-motion cut: `.scene-veil` 140 ms opacity, `camera.lookAt` + `lookAtTransform(IDENTITY)` | repo:app.css:17,21; CameraController.ts:130-140,179-183 | all, S9 |
| M15 | **Constant hillshade (if ever wanted, rule 8):** `globe.enableLighting = true` [dts:34761] + terrain loaded with `requestVertexNormals: true` [dts:3046-3053] (the R2 pyramid was built with `octvertexnormals` — ADR-0021:37,53; `upgradeTerrain` does not request them today [repo:SceneController.ts:391-401]) + `scene.light = new DirectionalLight({direction, color, intensity})` [dts:33813-33830] replacing the default `SunLight` [src:Scene/Scene.js:766]; intensity via `globe.lambertDiffuseMultiplier` (default 0.9) and `globe.vertexShadowDarkness` (default 0.3) [dts:34767, 34880; src:Scene/Globe.js:176,379]. The shader multiplies imagery colour by the Lambert term only under `ENABLE_VERTEX_LIGHTING` [src:Shaders/GlobeFS.glsl:437-440]; that define is pushed only when `enableLighting && terrainProvider.hasVertexNormals` [src:Scene/GlobeSurfaceShaderSet.js:321-328; GlobeSurfaceTileProvider.js:2394-2396] — without normals `enableLighting` silently falls to `ENABLE_DAYNIGHT_SHADING` (no relief, a day/night terminator instead). `scene.light` is public [dts:44208] and a non-`SunLight` light's `direction` feeds `czm_lightDirectionEC` directly [src:Renderer/UniformState.js:1461-1479]. With a fixed direction the shade is constant, time-independent and therefore `cinematic` with driver "fixed light" (VTD). Keep `dynamicAtmosphereLighting` irrelevant (atmosphere is off). **Caveat:** NAIP already carries baked sun; A/B at river band before adopting; ellipsoid fallback shows no relief (no normals) — the honest degraded state | S4 (river/local only), PROPOSED |
| M16 | **Fog at nadir — do not use as depth cue.** `scene.fog` [dts:44153] is distance/height driven (`density` 0.0006, `maxHeight` 800 km, `screenSpaceErrorFactor` 2 — it also *culls tiles* [src:Scene/Fog.js:49-89; dts:34392-34396]). At nadir all pixels are near-equal distance, so fog is a uniform tint plus a faint peripheral falloff — a second vignette, which rule 14 forbids stacking on M11. Verification note: the home/orbital view sits at 1,150 km, *above* `maxHeight` (800 km), so fog is disabled outright there; the `FOG` define requires `fog.enabled && fog.renderable && !cameraUnderground` [src:Scene/GlobeSurfaceTileProvider.js:2397-2398] and the blend is `czm_fog(v_distance, …)` [src:Shaders/GlobeFS.glsl:533]. Leave enabled only for its tile-culling economy if measured; otherwise off | none (negative finding) |
| M17 | **Time-of-day tinting — grade, not light.** If Presentation Mode wants a solar mood, ease `ImageryLayer.brightness/contrast/saturation/gamma` per frame in `preRender` (uniforms, continuity doc §1b) rather than enabling solar lighting; the HUD must state "lighting: solar, valid …" (CAMERA_SYSTEM §11). `globe.enableLighting` + `SunLight` is the alternative and turns the December floods black | S5 (presentation only), PROPOSED |
| M18 | Post-process: `scene.postProcessStages.bloom` exists (disabled by default) [dts:43107; src:Scene/PostProcessStageCollection.js:38,55]; custom `PostProcessStage` with `colorTexture` [dts:42912; src:Scene/PostProcessStage.js:30]. **Not licensed** by rule 14 for any shot in this list; recorded so no one re-researches it | none |

---

## 7. Open items surfaced by this lens (for the owner / engineering)

1. **Rule 3 is violated today**: the basin panel mounts on selection, not on settle
   (`App.tsx:41-42`; no `flightState` read in `panels/`). The fix is a gate in the panel host on
   `flightState === 'settled'` plus the 400 ms hold — no renderer change.
2. **Rule 5 is unimplemented**: `flyToBasin` frames against the full frustum; the stage offset
   (M6) is the single largest compositional win available at zero motion cost.
3. **S5 pops**: `WeatherFieldLayer.setData` detaches then attaches; the M7 crossfade makes
   scrubbing read as a weather film.
4. **Weather `setData` during flights**: gate on `settled` (rule 3) — two lines in
   `SceneDataBridge`.
5. **Hillshade (M15)** is a real, verified, low-cost option — but it is an owner taste decision
   and must be A/B'd against NAIP's baked sun at river band before it enters the film.
6. The **forecast half of the timeline** (`[T−72h, T+120h]`, CINEMATIC_ARCHITECTURE §7.1) is
   deferred past P1 [repo:window.ts:7,52-61]; S5's pacing notes hold for the 72 h window and
   should be re-checked when +120 h ships (issued-at labelling per §7.2).

---

### Source index

- Cesium 1.144 (local): `Cesium.d.ts` lines cited; `@cesium/engine/Source/Scene/{CameraFlightPath,Camera,Scene,Globe,Fog,PostProcessStageCollection,PostProcessStage,ImageryLayer}.js`, `Core/PerspectiveFrustum.js`, `Shaders/GlobeFS.glsl`
- Repo: `apps/web/src/{scene,camera,layers,app,timeline,design-system}` files cited; `docs/CAMERA_SYSTEM.md`, `docs/CINEMATIC_ARCHITECTURE.md`, `docs/VISUAL_TRUTH_DOCTRINE.md`, `docs/LAYER_SYSTEM.md`, `docs/adr/ADR-0021-ion-free-terrain.md`, `docs/research/ux-audit-2026-08-31.md`, `docs/research/session-checkpoint-2026-08-31b.md`
- https://earth.google.com/studio/docs/making-animations/easing/ · https://earth.google.com/studio/docs/advanced-features/camera-target/ (quick-start page 404 at fetch)
- https://developer.apple.com/design/human-interface-guidelines/motion (read through a text proxy; the page is script-rendered)
- https://www.niemanlab.org/2016/03/at-the-malofiej-infographics-world-summit-the-best-form-of-storytelling-is-often-static/ (403 at fetch; snippet only) · https://github.com/archietse/malofiej-2016
- https://idl.cs.washington.edu/files/2007-AnimatedTransitions-InfoVis.pdf
- https://vanwijk.win.tue.nl/zoompan.pdf (503 at fetch) · https://arxiv.org/pdf/1801.09358 (ρ = 1.42 restated, p.3)
- https://www.semanticscholar.org/paper/7d8ac1ed3dc3fc96538372206da015e7dd4b251e (Flash & Hogan 1985)
- https://www.rogerebert.com/interviews/hayao-miyazaki-interview (403 at fetch; snippet only)
- https://www.nngroup.com/articles/response-times-3-important-limits/
- https://github.com/cambecc/earth · https://community.windy.com/topic/16097/smoother-animations/3
- https://www.studiobinder.com/blog/what-are-the-12-principles-of-animation/ (Disney principles summary)

---

## Verification

Adversarial pass, 2026-09-01. Every Cesium claim was re-grepped against
`apps/web/node_modules/cesium/Source/Cesium.d.ts` and `@cesium/engine/Source` (1.144.0); every
external claim was re-fetched (the two PDFs were fetched and text-extracted locally with pypdf).
Legend: ✓ verified as stated · ✓* verified with a correction applied inline above · ✗ refuted.

### Cesium API claims

| # | Claim | Verdict | Note |
|---|---|---|---|
| C1 | Earth Studio: keep easing synced across attributes or the camera takes a different path; `flyToBoundingSphere` interpolates one path under one `easingFunction` | ✓ | Page quotes verbatim: "keep your easing synced across attributes" / "your camera will actually take a different path". `flyToBoundingSphere(…, {easingFunction?: EasingFunction.Callback})` at dts:29137-29150; `flyTo` has the same option at dts:29094-29107. |
| C2 | Default flight easing is `QUINTIC_IN_OUT`, `CUBIC_OUT` when descending from > 11.5 km; ELASTIC/BACK/BOUNCE ship; repo passes minimum-jerk | ✓* | `CameraFlightPath.js:548-558` exact (`startHeight > endHeight && startHeight > 11500.0` → `CUBIC_OUT`, else `QUINTIC_IN_OUT`). `minimumJerk` at motion.ts:24-28, passed at CameraController.ts:159. **Correction:** the cited dts range 5697-5769 stops before the forbidden trio; `ELASTIC_*`/`BACK_*`/`BOUNCE_*` are at dts:5789-5821 (namespace 5697-5834). Fixed in rule 6. |
| C3 | Two public ways to anchor the subject off-centre without tilt: `camera.flyTo({destination, orientation})` or `PerspectiveFrustum.xOffset/yOffset` | ✓* | `xOffset` dts:12758, `yOffset` dts:12762; ctor defaults PerspectiveFrustum.js:82-91; applied to the off-centre frustum at :219-222. **Correction:** the offset is in *near-plane distance units* (added to `left/right`), not "the covered fraction" — §3.2 and M6 now state `k · near · tan(fovx/2)`. Also checked that nothing clobbers it: `Scene.js:1553` zeroes it only in the `useWebVR` setter's false branch; `:3431/:3438` are the VR stereo pass. |
| C4 | Constant hillshade via `enableLighting` + `requestVertexNormals` + `scene.light = DirectionalLight`, tuned by `lambertDiffuseMultiplier` 0.9 / `vertexShadowDarkness` 0.3; shader multiplies only under `ENABLE_VERTEX_LIGHTING`; R2 pyramid has octvertexnormals; `upgradeTerrain` does not request them | ✓* | dts:34761 `enableLighting`, :34767 `lambertDiffuseMultiplier`, :34880 `vertexShadowDarkness`, :3046-3053 `requestVertexNormals` (default false), :33813-33830 `DirectionalLight`, :44208 `light: Light`; Scene.js:766 `this.light = new SunLight()`; Globe.js:176 (0.9), :379 (0.3); GlobeFS.glsl:437-440. ADR-0021:37 (`--extension octvertexnormals`), :53 (`quantized-mesh-1.0 + octvertexnormals`). SceneController.ts:109 `enableLighting = false`, :391-401 `fromUrl(root)` with no options. **Added:** the define is gated on `enableLighting && hasVertexNormals` (GlobeSurfaceShaderSet.js:321-328; GlobeSurfaceTileProvider.js:2394-2396) — without normals you get `ENABLE_DAYNIGHT_SHADING`, not relief; a non-`SunLight` direction feeds `czm_lightDirectionEC` at UniformState.js:1461-1479. |
| C5 | Fog is distance/height driven (density 0.0006, maxHeight 800 km), culls tiles via `screenSpaceErrorFactor`, and at nadir is a uniform tint plus a second vignette | ✓* | Fog.js:49 `density = 0.0006`, :62 `maxHeight = 800000`, :82 `screenSpaceErrorFactor = 2.0` (doc: "reduce the number of terrain tiles requested"), :89 `minimumBrightness`; dts:34392-34396 `screenSpaceErrorFactor`; edge-vignette.ts:15-16 `FEATHER 0.06`, `EDGE_ALPHA 0.82`. The nadir "uniform tint" reading follows from `czm_fog(v_distance, …)` at GlobeFS.glsl:533. **Added:** at the 1,150 km home view the camera is above `maxHeight`, so fog is off there regardless. |

### External / repo claims

| # | Claim | Verdict | Note |
|---|---|---|---|
| E1 | Pure nadir at every band, tilt disabled, heading spring-back | ✓ | CameraController.ts:14-18 (`pitchDeg: -90` ×3, `headingDeg: 0`); SceneController.ts:146 `enableTilt = false`, :147 `constrainedAxis = UNIT_Z`; envelope.ts:45-51 all `TILT_CAP_DEG_BY_BAND` = 0, :53-54 `HEADING_TOLERANCE_DEG = 2`, :94-95 spring to 0. |
| E2 | Earth Studio Camera Target warns of an unwanted 180° flip when animating directly above a target | ✓ | Verbatim on the page: "avoid animating the camera directly above a target—this can cause an unwanted 180° 'flip'". The "therefore lock heading, no target rig" step is this doc's inference; the page only states the warning. |
| E3 | Rule 3 violated: panel mounts on selection; nothing under `panels/` reads `flightState`; F8 open | ✓ | App.tsx:41-42 mounts `BasinPanel`/`RiverPanel` unconditionally inside `.panels`; BasinPanel.tsx:54,59 gates only on `selectedBasinId`; `grep -rn flightState apps/web/src/panels/` → no hits (only `state/store.ts` and `app/TopStrip.tsx` reference it); store.ts:66 field, :117 setter; ux-audit-2026-08-31.md:36 is F8 "The basin panel appears mid-flight". |
| E4 | Rule 5 unimplemented: `flyToBasin` frames against the full frustum's narrowest half-angle, no panel offset | ✓ | CameraController.ts:92-98 `framingRange(sphere.radius, this.narrowestHalfAngle(), 1.1)`; :185-189 `narrowestHalfAngle` = `min(fov, fovy)/2` of the whole frustum; app.css:54 `.panels { width: min(420px, 40vw) }`. |
| E5 | Weather scrub pops (detach-then-attach); fix is a second layer with `ImageryLayer.alpha` ramped in `scene.preRender`; `scene.tweens` not public | ✓ | WeatherFieldLayer.ts:171-173 `this.detach(); this.imagery = new ImageryLayer(provider, {}); this.attach(...)`; dts:37105 `alpha: number`; dts:44333 `readonly preRender: Event`; `grep -n tweens Cesium.d.ts` → zero hits; continuity doc §1b at lines 38-43 says the same. |
| E6 | House constants: micro 140 / ui 220 / panel 320 / state 520; plate 320 fade + 250 sustain; idle 220/260; boot 400 + 700; flights 500–2,400 via `500 + 420·log2(1+km/5)` | ✓* | tokens.css:21-24 (eases at :19-20); TransitionPlate.ts:18 `GESTURE_IDLE_MS 220`, :20 `SETTLE_SUSTAIN_MS 250`, :21 `FADE_MS 320`; SceneController.ts:176-177 `MOTION_SSE 3.2`, `MOTION_IDLE_MS 260`; LoadingVeil.tsx:21-23 `30_000 / 400 / 700`; motion.ts:12,14; flight-math.ts:10-15. **Correction:** the log argument is *weighted* km (`distance + 2·|Δheight|`, flight-math.ts:12), fixed in the §4.1 table. |
| E7 | Heer & Robertson 2007: valid graphics, staging, as-long-as-needed, ~1 s, 1.25 s in-study, slow-in/slow-out improves tracking | ✓* | PDF text extracted: "Maintain valid data graphics during transitions" (p.3), "Use staging for complex transitions", "Make transitions as long as needed, but no longer … recommend transition times around 1 second" (citing Robertson et al. [21]), "animated transitions were 1.25 seconds in duration" (p.5), "improve tracking. This suggests slow-in slow-out timing" (under "Maximize predictability"). **Clarified** in §1 that the 1 s figure is Robertson et al. via Heer. |
| E8 | ρ = 1.42 restated in arXiv 1801.09358 p.3; underpins the cut-vs-flight rule; follow-up notes paths are not smooth when interrupted | ✓* | Reach & North, "Smooth, Efficient, and Interruptible Zooming and Panning". Abstract (p.1): "Unlike the technique of van Wijk and Nuij, the animations produced by our technique are smooth at the endpoints and when interrupted by a change of target". p.3 (two page breaks in): "a user study found that the user-preferred value of ρ was 1.42, which is roughly √2". TU/e PDF not re-fetched. **Clarified** in §4.3 that "clamp ⇒ untrackable" is this doc's inference from the metric, not a stated result. Note that Cesium's `cancelFlight` stop-in-place is precisely the velocity discontinuity the paper describes; the doc's acceptance of it is a design judgement. |
| E9 | Apple HIG Motion: purposeful, optional, brief/precise feedback, avoid on frequent interactions | ✓ | Fetched via r.jina.ai; all four sentences present verbatim, including "In apps, generally avoid adding motion to UI interactions that occur frequently." |
| E10 | Miyazaki "ma" (rogerebert 403), "Chanel rule" apocryphal, Planet Earth II / Ghibli nadir unverified — all marked as such | ✓ | rogerebert.com returned HTTP 403 again on this pass. Goodreads page loads, attributes to Coco Chanel, cites no primary source, and carries the disclaimer "Quotes are added by the Goodreads community and are not verified by Goodreads." The Planet Earth II / Ghibli searches were not repeated; the doc already labels them UNVERIFIED and uses them as metaphor only, which is the correct state. |

Net: 15/15 claims stand; none refuted. Six carried imprecisions now corrected inline (rule 6 dts
range; §3.2/M6 `xOffset` units; §4.1 weighted km; §4.3 inference labelled; M15 shader gate and
light-direction path; M16 fog `maxHeight` at home view; §1 Heer/Robertson attribution).
