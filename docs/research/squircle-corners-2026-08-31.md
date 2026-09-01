# Squircles on the web — state of the art, August 2026

Research for the Cascadia glass/panel design system. Every claim below carries its source and date.
Numeric claims marked **[derived]** come from a reproducible fit script (appendix) — not from a publication.

---

## 1. Native `corner-shape` / `superellipse()` — what shipped

**Spec**: CSS Borders and Box Decorations Level 4 (`css-borders-4`, Editor's Draft), §3.7–3.9
"Corner Shaping" — longhands `corner-top-left-shape` (+ physical/logical side shorthands), shorthand
`corner-shape`. (drafts.csswg.org/css-borders-4)

**The math** (MDN `superellipse` value page; Amit Sheen, master.dev blog, 2025-06-23):
the curve is `|x|^n + |y|^n = 1` with exponent **n = 2^K** where K is the parameter you write.

| CSS | K | exponent n | shape |
|---|---|---|---|
| `bevel` | 0 | 1 | straight diagonal |
| `round` (initial) | 1 | 2 | today's border-radius arc |
| **`squircle`** | **2** | **4** | quartic superellipse — the "iOS-ish" corner |
| `square` | ∞ | ∞ | sharp corner |
| `scoop` | −1 | ½ | concave |
| `notch` | −∞ | — | square inward notch |
| `superellipse(K)` | any | 2^K | continuum; animatable between all of the above |

**Syntax** (MDN corner-shape page):
```css
border-radius: 24px;           /* size of the corner box — REQUIRED, 0 ⇒ corner-shape is a no-op */
corner-shape: squircle;        /* 1–4 values, TL TR BR BL, same slash-less pattern as radius */
corner-shape: superellipse(2.2) squircle;  /* mix keywords and functions */
```
`border-radius` keeps controlling corner *size*; `corner-shape` controls the *curve* inside that
corner box. All radius collision/overlap rules carry over. Animatable (smooth superellipse
interpolation). If the newer `border-shape` property is set, `border-radius`+`corner-shape` are ignored.

**Support matrix (checked 2026-08-31)**

| Engine | Status | Source |
|---|---|---|
| Chrome **139+** stable (desktop + Android), released **2025-08-05** | ✅ shipped, no flag | developer.chrome.com/release-notes/139; chromestatus feature 5357329815699456; blink-dev Intent to Ship |
| Edge 139+, Opera 123+ | ✅ (Chromium) | caniuse `mdn-css_properties_corner-shape` |
| Safari — through Safari 26.x / TP 27 | ❌ not shipped; WebKit standards position: **support** (positive) | caniuse; webkit standards-positions |
| Firefox — through 157 | ❌ not shipped; Mozilla position request **open, no response** (standards-positions#823); tracking bug bugzilla 1726232; WPT tests already vendored in mozilla-central | github.com/mozilla/standards-positions/issues/823 |
| Global reach | ≈ **68%** of users | caniuse, Aug 2026 |
| Interop 2026 | **not** a focus area (`shape()` is; see §2b) | webkit.org/blog/17818, web.dev/blog/interop-2026 |

Practical read: Chromium-only for all of 2026; Safari is favorable but has published no timeline.

**What follows the shaped corner** (MDN corner-shape, "properties that follow the shape";
Smashing Magazine 2026-03-12 verified box-shadow behavior in demos):
background (color+image), **border**, **outline** (focus rings!), **box-shadow incl. inset**,
**overflow clipping of children**, and **backdrop-filter**. This is the whole reason it beats every
fallback: it is the only technique where a glass panel needs *zero* extra elements.

---

## 2. Fallback techniques where `corner-shape` is unavailable

### (a) Plain `border-radius` approximation

Facts first:
- Apple's continuous corner is **not** a superellipse; it's a chain of cubic Béziers (with quirks),
  and **Figma corner smoothing ξ = 0.6 "just about nails the iOS shape"** (Figma, "Desperately
  seeking squircles"). The smoothed corner consumes **(1+ξ)·r** of edge per side (2r at ξ=1) —
  ξ=0.6 ⇒ ~1.6r.
- iOS smoothing *keeps the central arc at the nominal radius* and spends the smoothing on the
  tangent blend. So the silhouette of an iOS(r, 60%) corner ≈ a plain arc of the **same r**.
  **The best plain-radius multiplier for "iOS 60% smoothing" is ≈ 1.0×** — you can't fake the G2
  blend with an arc, and changing the radius only makes the silhouette worse. **[derived + Figma]**
- The CSS `squircle` is a different animal: drawn inside the full corner box R it hugs the corner
  much tighter (diagonal clearance 0.225R vs 0.414R for round). Its silhouette is almost exactly a
  plain arc of **ρ ≈ 0.57R** (max deviation ≈ 0.012R, i.e. sub-pixel for R ≤ 40px). **[derived]**

Two rules fall out of this, and they are the backbone of the recipe in §5:

1. **Fallback rule**: `corner-shape: squircle` at radius R degrades gracefully to
   `border-radius: R` (what non-supporting browsers render) but the *visually matched* fallback is
   `border-radius: ≈0.6R`. Since the property just gets ignored, you author it the other way around:
2. **Authoring rule**: to keep the corner "weight" you had at legacy radius r, write
   `border-radius: ≈1.75r; corner-shape: squircle;` inside `@supports`, keeping `border-radius: r`
   as the base. (Matches the folk advice "pair squircle with a generous radius" — squircle.js blog.)

### (b) `clip-path` with a superellipse path

- `clip-path: path("…")` — SVG px coordinates, **not responsive**. Dead end for fluid components.
- SVG `<clipPath clipPathUnits="objectBoundingBox">` — responsive but the corner scales with the
  box (and distorts on non-square aspect). Wrong for design systems where radius is a token.
- **`clip-path: shape()` — the modern answer.** Path-like commands (`from`, `curve … with cp1/cp2`,
  `hline/vline`, `close`) that accept **any CSS length-percentage incl. `calc()` mixing % and px**,
  so corners stay fixed-size while the shape is responsive. Shipped: **Chrome 135** (2025-04),
  **Safari 18.4** (2025-04), **Firefox 148** (2026-02) — **Baseline newly-available Feb 2026**, and
  an **Interop 2026 focus area**. (developer.chrome.com/blog/css-shape; MDN shape(); web.dev
  interop-2026.) MDN also lists `shape()` for `offset-path` and the future `border-shape`.
- A quartic-squircle corner is well-approximated by **one cubic per corner with control points at
  8% of R from the corner vertex** (k = 0.92 of the way from tangent point to vertex; Hausdorff
  error ≈ 0.02R — ~½px at R=24). **[derived]** Exact CSS in §5.
- Caveat: everything in §3 about clipping shadows/borders applies.

### (c) SVG mask / `mask-image`

Same geometry options as clip-path but via alpha masking (`mask-image:
url("data:image/svg+xml,…")` or `mask: paint(…)`). A stretched mask distorts corners; the 9-slice
`mask-border` / `-webkit-mask-box-image` keeps corners fixed but has no Firefox support. Masking
adds nothing over `shape()` today except softer AA edges; it shares every shadow/border caveat and
adds one: a *mask on an ancestor* makes that ancestor a backdrop root (see §3). Use only when you
need feathered/graded edges.

### (d) JS path generation (Figma-style)

| Package | What it is | Size / API | Notes |
|---|---|---|---|
| `figma-squircle` **1.1.0** (2024-09-19) | The Figma corner-smoothing math as `getSvgPath({ width, height, cornerRadius, cornerSmoothing 0–1, preserveSmoothing, per-corner radii })` → SVG path string | **26.6 KB unpacked**, zero deps (npm registry) | The canonical ξ implementation; pair with ResizeObserver yourself |
| `corner-smoothing` (Sana Labs) | `squircleObserver()` / React `<Squircle>`; applies **clip-path**, so hover/hit-testing follows the curve; **border mode**: outer squircle + inset `::before` inner squircle, gap = border (gradient borders possible) | zero deps | The most complete off-the-shelf; still subject to §3 clip caveats |
| `@squircle-js/react` | ResizeObserver + clip-path, Figma algorithm | — | squircle.js.org |
| `hyperellipse` (2026-06) | **Spec-accurate `corner-shape` polyfill**: write `--corner-shape: squircle` next to `border-radius`, call `registerHyperellipse()` once; claims backgrounds, gradients, borders, box-shadow, outline+offset; SSR-safe, idempotent | MIT, hyperellipse.vercel.app | Closest to "author native, polyfill the rest" (dev.to/mikhailmogilnikov) |

### (e) Houdini paint worklet

CSS Painting API: Chrome 65+/Edge 79+ only, ≈76% global; **Safari: behind a never-enabled flag in
all versions; Firefox: none through 157** (caniuse `css-paint-api`). Since the only engines that run
`paint()` already have real `corner-shape`, Houdini is a **dead end as a squircle fallback in 2026**.

---

## 3. The glass-panel interaction matrix (the part that bites)

A glass panel needs four things to agree on one silhouette: backdrop blur, a 1px hairline,
an inset top highlight, and an outer shadow.

Verified engine behavior for "does X get clipped/shaped correctly":

- **clip-path / mask do clip the backdrop-filter output** on the same element in all three engines
  today: Chromium fixed in Chrome 77 (bug noted in Chrome 76), WebKit bug 142662 RESOLVED FIXED
  2016-05-25 (and backdrop-filter unprefixed + interop fixes in Safari 18, webkit.org WWDC24 post),
  Gecko bug 1579957 RESOLVED FIXED (~2022). Keep `-webkit-backdrop-filter` alongside for Safari ≤17.
- **clip-path clips box-shadow and borders**: an outer shadow painted outside the clip region
  disappears; the 1px border keeps following the *border-radius* box, not the clip path
  (CSS-Tricks "Using box-shadows and clip-path together"; corner-smoothing README).
- **The wrapper-drop-shadow trick breaks glass**: the usual fix (`filter: drop-shadow()` on a
  parent of the clipped element) makes that parent a **backdrop root** — any ancestor `filter`,
  `opacity < 1`, or `mask` limits what a descendant `backdrop-filter` can see, so the panel stops
  blurring the page behind it (filter-effects-2 "Backdrop Root"; MDN backdrop-filter). Shadow must
  live on a *sibling/pseudo-element behind* the glass, never on a wrapping ancestor.
- **corner-shape shapes all four coherently** on one element: border, outline, box-shadow (outer
  *and* inset), overflow, backdrop-filter (MDN corner-shape; Smashing 2026-03-12).

| Technique | Squircle fidelity | backdrop-filter | 1px hairline border | inset highlight | outer shadow | responsive | JS |
|---|---|---|---|---|---|---|---|
| `corner-shape` (Chromium 139+) | exact | ✅ shaped | ✅ shaped | ✅ shaped | ✅ shaped | ✅ | none |
| plain `border-radius` | none (round) | ✅ | ✅ | ✅ | ✅ | ✅ | none |
| `clip-path: shape()` | ≈0.02R error | ✅ clipped OK | ⚠️ follows radius box → underlay `border-radius: .6R` (mismatch ≈0.012R ≈ sub-px) or inner-squircle `::before` | ⚠️ same | ❌ clipped → sibling/`::before` shadow (never wrapper `filter`) | ✅ (calc-pinned) | none |
| `clip-path: path()` / SVG oBB clipPath | good | ✅ | ⚠️ as above | ⚠️ | ❌ | ❌ / distorts | none |
| SVG `mask-image` | good | ✅ (modern) | ⚠️ | ⚠️ | ❌ | ⚠️ 9-slice prefixed, no FF | none |
| JS clip-path libs (figma-squircle et al.) | exact (Figma ξ) | ✅ | ⚠️ lib-managed double squircle | ⚠️ | ❌ same | ✅ (ResizeObserver) | yes |
| Houdini `paint()` | exact | n/a (bg only) | via worklet | via worklet | ❌ | ✅ | worklet |

**Consequence for the design system**: for *glass* surfaces, the only two techniques that keep the
material coherent without extra elements are `corner-shape` and plain `border-radius`. Clip/mask
fallbacks are fine for opaque decorative surfaces, but on glass they cost a sibling shadow layer
and accept a sub-pixel hairline mismatch — spend that complexity only where the silhouette is the
point (hero/marketing), not on working HUD panels.

---

## 4. Real products / public write-ups (searched 2026-08-31)

- **No public squircle-on-web write-ups found from Vercel, Linear, Family, or Arc.** Family and Arc
  are native apps (their squircles are platform-drawn); nothing surfaced on linear.app / vercel.com
  / family.co for "squircle" or corner smoothing.
- What does exist publicly: **Sana Labs** ships `corner-smoothing` (built for sana.ai's UI);
  **Adam Argyle** runs `shape()`-based squircle progressive enhancement on nerdy.dev (2025-09-26)
  and pushed corner-shape for Interop 2026; **Figma** documented the definitive iOS reverse-
  engineering ("Desperately seeking squircles") and ships ξ smoothing in the editor;
  **squircle.js / CornerKit / hyperellipse** are the active OSS ecosystem; Smashing Magazine
  (2026-03) and webdevsimplified (2026-05) cover component-library usage of corner-shape.
- Industry pattern in 2026: author `corner-shape` behind `@supports`, plain radius elsewhere; JS
  clip-path libraries only where pixel-parity with Figma/native is a hard requirement.

---

## 5. Recommended layered recipe — 5 shape classes, no JS

Strategy: **base layer = plain border-radius (every browser). Enhancement layer = corner-shape at
~1.75× the base radius (Chromium). Optional silhouette layer = `clip-path: shape()` for opaque
decorative surfaces only (Safari 18.4+/Firefox 148+), never for glass.** Capsules stay `round` on
purpose — a true pill *is* a circle-ended shape; squircling it reads as a worn rectangle.

```css
/* ---------- tokens ---------- */
:root {
  /* base radius = what Safari/Firefox render; squircle radius ≈ 1.75x keeps perceived weight */
  --shape-control-r: 10px;  --shape-control-R: 18px;
  --shape-card-r:    16px;  --shape-card-R:    28px;
  --shape-sheet-r:   20px;  --shape-sheet-R:   36px;
  --shape-panel-r:   28px;  --shape-panel-R:   48px;
}

/* ---------- shape classes ---------- */
.shape-capsule { border-radius: 999px; }             /* intentionally round everywhere */

.shape-control { border-radius: var(--shape-control-r); }
.shape-card    { border-radius: var(--shape-card-r); }
.shape-sheet   { border-radius: var(--shape-sheet-r); }
.shape-panel   { border-radius: var(--shape-panel-r); }

@supports (corner-shape: squircle) {
  .shape-control { border-radius: var(--shape-control-R); corner-shape: squircle; }
  .shape-card    { border-radius: var(--shape-card-R);    corner-shape: squircle; }
  .shape-sheet   { border-radius: var(--shape-sheet-R);   corner-shape: squircle; }
  /* large panels: slightly gentler curve reads better at size — K is a taste dial, 1.5–2 */
  .shape-panel   { border-radius: var(--shape-panel-R);   corner-shape: superellipse(1.8); }
}

/* ---------- glass material (works on every shape class above) ---------- */
.glass {
  background: rgb(18 24 32 / .55);
  -webkit-backdrop-filter: blur(20px) saturate(1.4);   /* Safari <= 17 */
  backdrop-filter: blur(20px) saturate(1.4);
  border: 1px solid rgb(255 255 255 / .14);            /* hairline — follows corner-shape */
  box-shadow:
    0 8px 32px rgb(0 0 0 / .35),                       /* outer — follows corner-shape */
    inset 0 1px 0 rgb(255 255 255 / .18);              /* top highlight — follows corner-shape */
}
/* In Chromium: silhouette, blur, hairline, highlight, shadow all superellipse. 
   In Safari/Firefox: identical material at the base radius. One element. No JS. */

/* ---------- OPTIONAL: true squircle silhouette for OPAQUE surfaces on Safari/Firefox ---------- */
/* one cubic per corner, control points 8% of R from each vertex (fit err ~2% of R) */
@supports (clip-path: shape(from 0 0, line to 100% 100%)) and (not (corner-shape: squircle)) {
  .shape-squircle-clip {
    --R: 28px;
    --c: calc(var(--R) * 0.08);
    border-radius: calc(var(--R) * 0.6);  /* keeps any border/inset shadow within ~0.3px of the clip */
    clip-path: shape(
      from 0 var(--R),
      curve to var(--R) 0                 with 0 var(--c) / var(--c) 0,
      hline to calc(100% - var(--R)),
      curve to 100% var(--R)              with calc(100% - var(--c)) 0 / 100% var(--c),
      vline to calc(100% - var(--R)),
      curve to calc(100% - var(--R)) 100% with 100% calc(100% - var(--c)) / calc(100% - var(--c)) 100%,
      hline to var(--R),
      curve to 0 calc(100% - var(--R))    with var(--c) 100% / 0 calc(100% - var(--c)),
      close
    );
  }
  /* outer shadow for a clipped surface: sibling/pseudo BEHIND it —
     never filter:drop-shadow on a wrapper (ancestor filter = backdrop root, kills glass blur) */
  .shape-squircle-clip-shadow { position: relative; }
  .shape-squircle-clip-shadow::before {
    content: ""; position: absolute; inset: 0; z-index: -1;
    border-radius: calc(var(--R) * 0.6);
    box-shadow: 0 8px 32px rgb(0 0 0 / .35);
  }
}
```

Rules of use:
1. Glass surfaces: shape class + `.glass` only. Do not add the clip layer to glass.
2. Opaque decorative surfaces that must read squircle cross-browser: add `.shape-squircle-clip`.
3. Focus rings: `outline` follows `corner-shape` in Chromium; elsewhere it follows the base radius — acceptable.
4. Re-audit when Safari/Firefox announce `corner-shape` (WebKit position is already positive); then delete the clip layer.

---

## Appendix — derivation script (reproducible)

Quartic superellipse corner (`corner-shape: squircle`, n = 2^2 = 4) sampled at 4001 points in a unit
corner box; (1) best-fit tangent circular arc against the full rounded-rect boundary → ρ = 0.571R,
max deviation 0.0115R; (2) diagonal clearance 0.225R vs 0.414R (round); (3) single-cubic fit with
symmetric control points k of the way from tangent point to vertex → k = 0.92 best
(two-sided error ≈ 0.021R; k=1.0 → 0.048R). Python one-file script run 2026-08-31 in this session.

## Sources

- MDN: `corner-shape`, `<corner-shape-value>`, `superellipse()`, `backdrop-filter`, `shape()` (Baseline Feb 2026) — developer.mozilla.org
- Chrome 139 release notes (2025-08-05) — developer.chrome.com/release-notes/139; chromestatus.com/feature/5357329815699456; blink-dev Intent to Ship thread
- caniuse: `mdn-css_properties_corner-shape` (~68% global), `css-paint-api` (~76%, Chromium-only)
- drafts.csswg.org/css-borders-4 (corner shaping); drafts.csswg.org/filter-effects-2 (Backdrop Root)
- WebKit: bug 142662 (fixed 2016); "News from WWDC24: Safari 18" (backdrop-filter unprefixed/fixes); webkit.org/blog/17818 Interop 2026
- Mozilla: standards-positions#823 (open, no position); bugzilla 1726232 (corner-shape), 1579957 (fixed)
- developer.chrome.com/blog/css-shape (shape(): Chrome 135, Safari 18.4, Firefox 148; calc-mixing)
- Figma, "Desperately seeking squircles" (iOS ≈ ξ 0.6; not a superellipse; (1+ξ)r consumption)
- Smashing Magazine 2026-03-12 (corner-shape shapes shadows/outlines); master.dev blog 2025-06-23 (n = 2^K); nerdy.dev/squircles 2025-09-26
- npm registry: figma-squircle 1.1.0 (2024-09-19, 26.6KB); github.com/sanalabs/corner-smoothing; squircle.js.org; hyperellipse.vercel.app (2026-06)
- CSS-Tricks: "Using box-shadows and clip-path together"; superellipse() almanac
