# Liquid Glass for Cascadia — research & decision document

Date: 2026-08-31. Read-only research; no repo code was written. Sources fetched: README + actual source
of four liquid-glass implementations (three requested + shuding's reference), the frontend-ui-ux audit
skill, Apple's own material description, and browser-support primary sources (WebKit bugzilla, MDN BCD
issue tracker, caniuse, W3C svgwg).

**What "Liquid Glass" is, per Apple** ([Apple Newsroom, June 2025](https://www.apple.com/newsroom/2025/06/apple-introduces-a-delightful-and-elegant-new-software-design/)):
a "translucent material [that] reflects and refracts its surroundings", that "dynamically reacts to
movement with specular highlights", built "from multiple layers". The distinguishing optical facts vs
plain frosted blur: (1) the backdrop visibly **bends at the rim** (lensing), (2) a **specular rim**
lit on a fixed axis, (3) an optional **prismatic fringe** where refraction is strongest, (4) a
**transmissive, undistorted center** so content behind stays recognizable.

---

## (a) Per-implementation technique table

| | [sohumsuthar/liquid-glass](https://github.com/sohumsuthar/liquid-glass) | [xcyberpunkx0/liquid-glass](https://github.com/xcyberpunkx0/liquid-glass) | [PallavAg/liquid-glass-web-react](https://github.com/PallavAg/liquid-glass-web-react) | [shuding/liquid-glass](https://github.com/shuding/liquid-glass) (1.1k★) |
|---|---|---|---|---|
| License / lang | MIT, React+CSS+mjs | MIT, TS, zero-dep, headless | MIT, TS, zero-dep, ~5 kB | MIT, vanilla JS console paste |
| Map generation | Build-time PNG: ray-traced Snell refraction through a convex-**squircle** slab (BK7 n=1.5168), Fresnel-weighted (`lib/glass-optics.mjs`, `PHYSICS.md`) | Runtime canvas, ~30 lines: red X-ramp + blue Y-ramp via `difference` blend, blurred 50%-gray inset rect neutralizes interior (`src/core/map.ts`) | Runtime canvas, per-pixel math: SDF rounded-rect lens, erf falloff, dome curvature, specular baked into **blue** channel, lens shape in **alpha** (`src/core/displacementMap.ts`) | Runtime canvas, per-pixel fragment function over rounded-rect SDF + smoothstep (`liquid-glass.js`) |
| Application | `backdrop-filter: blur(...)` on effect layer **plus plain `filter: url(#lg-refract)` on the same element** — displacement applied to the *result* of the backdrop blur | `backdrop-filter: url(#lg-filter-N) blur(3px) saturate(1.5)` — displacement inside backdrop-filter, Chromium-gated | **`style.filter = url(#...)` on a wrapper around the page content** (not backdrop-filter) — refracts the element's own painted subtree; lens subregion attrs limit cost | `backdrop-filter: url(#id_filter) blur(0.25px) contrast(1.2) brightness(1.05) saturate(1.1)` |
| Edge refraction | Physically exact scale calibration: peak displacement = 0.524×bezel; `scale = 2.008 × 0.049 ≈ 0.10` in objectBoundingBox units. Documents the **anisotropy trap**: a stretched map's bezel is a % of each dimension independently ("that anisotropy is the fisheye") — fixed by per-element maps (`useLiquidLens`) | Neutral-gray interior confines displacement to an **edge band whose curvature is set by the map blur radius**; default `scale:-112, border:0.07, mapBlur:12` | Edge band via inner SDF + `erf` smooth falloff; `depth` = band width; per-element map at real pixel size (no anisotropy) | Whole-surface lens: `smoothStep(0.8, 0, sdf-0.15)` pulls UVs toward center — magnifier look, not edge-only |
| Specular rim | Pure CSS, **measured from macOS 26**: vertical-axis lighting (top/bottom bright hairline L+97, sides dark L−39), ring cut with `mask-composite` (excerpt below); Fresnel-shaped inset box-shadow shoulder | Not included (headless: leaves rim to your design system) | Baked in map blue channel; extracted with `feColorMatrix` and composited arithmetically (`k2=specular`); `specularAngle`, glow + edge-highlight terms | None (box-shadow only) |
| Chromatic fringe | 3× `feDisplacementMap` at per-channel Snell scales (n_F 1.5224 blue > n_C 1.5143 red), isolated with `feColorMatrix`, `feBlend mode="screen"` (channels disjoint ⇒ screen==add). **OFF by default — see perf** | Same 3-pass staggered-scale pattern; `scales = [s, s+chroma, s+2·chroma]`; lite tier = 1 pass, chroma 0 | 3 taps at `[s(1+0.2c), s(1+0.1c), s]` recombined with arithmetic feComposite | None |
| Fallback | Dangling `url()` ref degrades to no-op (blur still renders, verified Chrome 152); Firefox gets refraction via element-`filter` path; mobile flattens (`@media (max-width:639px)` kills heavy layers) | **Best in class**: engine no-ops entirely at tier `off`; contract = `--lg-filter-url` + `data-lg-active` + `data-lg-quality`; your existing CSS remains untouched; `[data-lg-quality="off"]` gets frosted 16px blur | UA-gated workarounds (iOS `userSpaceOnUse`, Safari fresh filter ID per update); no non-SVG fallback — the whole point is the filter | None — Chromium-only, breaks silently elsewhere |
| Performance notes | **Measured: 5 concurrent 3-pass CA elements froze Chrome's compositor capture; 1 was fine** — CA restricted to 1–3 surfaces. Static map = cached PNG, filter runs in the compositing pass. Documents the **Backdrop Root trap**: `isolation`, `contain: paint`, `content-visibility: auto`, ancestor transform/opacity silently turn backdrop-filter into a no-op (measured 69% → 1.2% stripe transmission) | Map regen is O(w·h) canvas fill, debounced 120 ms on resize, `blob:` URL (no 1.33× base64 copy); sub-pixel resizes skipped; single shared `<defs>` host | Map regen throttled to 1/frame; drag fast-path only moves filter subregion attrs. Safari caps filter source area (warns >2.5 MP); Safari re-caches filter output by ID (fresh ID per update) | Full map regen + `toDataURL` per mouse move when the fragment reads mouse — demo-grade |
| React-friendliness | React components (`LiquidGlass.jsx`, filter as JSX) but CSS is class-contract based | Framework-agnostic core + optional React peer; contract is CSS-native — **fits an existing token system by design** | Purpose-built React wrapper around imperative engine | None (IIFE) |

### Load-bearing code excerpts

**xcyberpunkx0 — the entire displacement map in ~25 lines** (`src/core/map.ts`; this is the piece worth owning):

```ts
// red left→right ramp = X displacement, blue top→bottom ramp = Y ("difference" keeps
// both since channels are disjoint); a blurred, inset 50%-gray rounded rect
// neutralizes the interior, confining refraction to an edge band whose curvature
// is set by the blur radius.
const gx = ctx.createLinearGradient(0, 0, w, 0);
gx.addColorStop(0, "rgb(0,0,0)"); gx.addColorStop(1, "rgb(255,0,0)");
ctx.fillStyle = gx; ctx.fillRect(0, 0, w, h);
const gy = ctx.createLinearGradient(0, 0, 0, h);
gy.addColorStop(0, "rgb(0,0,0)"); gy.addColorStop(1, "rgb(0,0,255)");
ctx.globalCompositeOperation = "difference";
ctx.fillStyle = gy; ctx.fillRect(0, 0, w, h);
ctx.globalCompositeOperation = "source-over";
ctx.filter = `blur(${mapBlur}px)`;
ctx.fillStyle = "rgba(128,128,128,0.93)";
ctx.beginPath();
ctx.roundRect(inset, inset, w - inset*2, h - inset*2, radius);
ctx.fill();
```

**xcyberpunkx0 — two non-obvious correctness details** (`src/core/svg.ts`, `src/core/apply.ts`):

```ts
// Load-bearing: filters default to linearRGB, which re-maps the map's neutral
// gray 128 to ~0.216 and injects a constant phantom displacement.
filter.setAttribute("color-interpolation-filters", "sRGB");
```
```ts
// Property and attribute are set in the same synchronous block: an attribute
// without the property would make var(--lg-filter-url) invalid-at-computed-value
// and momentarily disable the element's entire backdrop-filter.
el.style.setProperty("--lg-filter-url", `url(#${filterId})`);
el.setAttribute("data-lg-active", "");
```

**xcyberpunkx0 — chromatic 3-pass** (`src/core/svg.ts`): three `feDisplacementMap` at
`[scale, scale+chroma, scale+2·chroma]`, each isolated to one RGB channel with `feColorMatrix`
(`"1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0"` etc.), recombined with two `feBlend mode="screen"`.

**sohumsuthar — the specular rim ring, pure CSS, no filter** (`css/liquid-glass-core.css`; measured
pixel-by-pixel from macOS 26 Control Center: top/bottom bright hairline, left/right dark hairline —
"a conic gradient cannot express this"):

```css
.liquid-glass-shine::before {
  content: ''; position: absolute; inset: 0; border-radius: inherit; padding: 1px;
  background:
    linear-gradient(to right,
      rgba(0,0,0,var(--lg-rim-dark)) 0, rgba(0,0,0,0) var(--lg-rim-side),
      rgba(0,0,0,0) calc(100% - var(--lg-rim-side)), rgba(0,0,0,var(--lg-rim-dark)) 100%),
    linear-gradient(to bottom,
      rgba(255,255,255,var(--lg-rim-lit)) 0, rgba(255,255,255,var(--lg-rim-lit)) var(--lg-rim-hold),
      rgba(255,255,255,0) var(--lg-rim-fade), rgba(255,255,255,0) calc(100% - var(--lg-rim-fade)),
      rgba(255,255,255,var(--lg-rim-lit)) calc(100% - var(--lg-rim-hold)),
      rgba(255,255,255,var(--lg-rim-lit)) 100%);
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;
  mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  mask-composite: exclude;
}
```

**sohumsuthar — cross-browser refraction trick** (`css/liquid-glass-core.css`, effect layer):

```css
.liquid-glass-effect {
  backdrop-filter: blur(var(--lg-blur)) saturate(var(--lg-saturate))
                   brightness(var(--lg-brightness)) contrast(var(--lg-contrast));
  /* lensing rides on a plain element `filter`, applied to the RESULT of the
     backdrop-filter above ... Gecko can't apply an feImage/feDisplacementMap graph
     to a *backdrop*, but it applies SVG filters to elements fine — so Firefox now
     gets the refraction instead of the blur-only fallback. */
  filter: var(--lg-refract);   /* url(#lg-refract) — dangling ref degrades to no-op */
}
```
Also documented there: a **minifier trap** — lightningcss treats `-webkit-backdrop-filter`/`backdrop-filter`
as a prefix pair and drops one when their values differ; keep the pair's values identical (Vite's
default esbuild CSS minifier is not affected, but this matters if lightningcss is ever enabled).

**PallavAg — specular from the map's blue channel, lens shape from alpha** (`src/core/engine.ts`):

```ts
// map blue channel ─▶ specular highlight, composited over
fe("feColorMatrix", { in: ..., type: "matrix",
  values: `0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 1 0 ${-128 / 255}`, result: "specMask" });
fe("feComposite", { in: "specMask", in2: "lensResult", operator: "arithmetic",
  k1: 0, k2: this.options.specular, k3: 1, k4: 0 });
// The map's alpha channel is the exact lens shape. Clip the refracted result to it
// and punch the same shape out of the source (feComposite in / out / over).
```
Note: PallavAg refracts a **content wrapper** via `filter:`, not the backdrop. For Cascadia that
would mean wrapping the live Cesium canvas in the filtered subtree — an SVG filter graph re-run over
the WebGL canvas every frame. Architecturally wrong for us; its map math is still the best-documented.

**shuding** — the pattern-setter for `backdrop-filter: url(#f)` + canvas `feImage` map + drag-time
`toDataURL` regeneration; whole-surface magnifier rather than edge-band refraction; no fallback.
[Source](https://github.com/shuding/liquid-glass/blob/main/liquid-glass.js).

**Other implementations surveyed** (search pass): [LeonardSEO/liquid-glass-react](https://github.com/LeonardSEO/liquid-glass-react)
(single feDisplacementMap, ~5 kB, same Chromium constraint), [nikdelvin/liquid-glass](https://github.com/nikdelvin/liquid-glass)
(CSS+SVG-only recreation), [deepika-builds/liquid-glass](https://github.com/deepika-builds/liquid-glass)
(one-file SVG displacement), and the technique articles [kube.io "Liquid Glass in the Browser"](https://kube.io/blog/liquid-glass-css-svg/)
(ray-traced map, 127 samples/radius, "Only Chrome currently supports using SVG filters as backdrop-filter";
"dynamic shape/size changes are costly … full displacement map rebuild") and
[ekino-france on Medium](https://medium.com/ekino-france/liquid-glass-in-css-and-svg-839985fcb88d).
Nothing surveyed beats the xcyber map + sohum rim combination for a token-system integration.

---

## (b) Verified browser-support matrix (as of Aug 2026)

| Technique | Chrome/Edge (Blink) | Safari (WebKit) | Firefox (Gecko) | Sources |
|---|---|---|---|---|
| `backdrop-filter: blur()/saturate()` (function filters) | Yes | Yes (`-webkit-` alias legacy; Chrome 152+ dropped its own `-webkit-` alias per sohum's notes) | Yes (since FF 103) | [MDN backdrop-filter](https://developer.mozilla.org/docs/Web/CSS/Reference/Properties/backdrop-filter) |
| **`backdrop-filter: url(#svg-filter)`** (feImage + feDisplacementMap on the *backdrop*) | **Yes — only engine that renders it** | **No.** Bug open since 2022; in **July 2026** WebKit PRs [#68614](https://bugs.webkit.org/show_bug.cgi?id=245510) (software-rendered `url()` reference filters, tests passing) + #68613 were posted — active, not shipped as of Aug 2026 | **No** — parses, silently no-ops; BCD issue closed "not planned"; open Mozilla Connect request | [WebKit bug 245510](https://bugs.webkit.org/show_bug.cgi?id=245510) (status NEW, PRs July 2026), [mdn/browser-compat-data#24110](https://github.com/mdn/browser-compat-data/issues/24110), [Mozilla Connect idea](https://connect.mozilla.org/t5/ideas/support-svg-filters-in-backdrop-filter-for-advanced-glass/idi-p/98453), [kube.io](https://kube.io/blog/liquid-glass-css-svg/) |
| Interop standardization | — | — | — | Open spec discussion: [w3c/svgwg#1142](https://github.com/w3c/svgwg/issues/1142) "define interoperable backdrop displacement/refraction for liquid glass UI" — no interoperable path exists yet |
| `filter: url(#svg)` on elements (incl. feDisplacementMap, feColorMatrix, feBlend, feComposite, feSpecularLighting) | Yes | Yes, with quirks: iOS misplaces objectBoundingBox primitive subregions (use `userSpaceOnUse`), caches filter output by ID, caps source area (~2.5 MP warning threshold) — all handled in [PallavAg engine.ts](https://github.com/PallavAg/liquid-glass-web-react) | Yes | [mdn/browser-compat-data#24110](https://github.com/mdn/browser-compat-data/issues/24110) ("SVG filters work with the `filter` property in Firefox and Safari"), PallavAg source |
| sohum's combo: `backdrop-filter: blur()` + element `filter: url(#displace)` on the same element | Yes (verified by author in Chrome 152) | Untested by author (plausible — both halves supported); **needs a spike** | **Yes per author** ("Firefox now gets the refraction") — needs our own verification | [sohumsuthar css comments](https://github.com/sohumsuthar/liquid-glass) |
| `mask-composite: exclude` / `-webkit-mask-composite: xor` (rim ring cut) | Yes (unprefixed in Chromium now) | Yes (`-webkit-` form; unprefixed `mask` since 15.4) | Yes (originated `exclude`) | [caniuse mask-composite](https://caniuse.com/mdn-css_properties_mask-composite), [Fyrd/caniuse#6170](https://github.com/Fyrd/caniuse/issues/6170) |
| `corner-shape: squircle` | Chrome 139+ only (~65% global) | No, no timeline | No, no timeline | [MDN corner-shape](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/corner-shape), [squircle.js survey](https://squircle.js.org/blog/squircles-in-css) |
| `prefers-reduced-transparency` media query | Yes (Chrome 118+) | Partial/behind-flag history — treat as progressive | Behind flag historically — treat as progressive | [caniuse](https://caniuse.com/mdn-css_at-rules_media_prefers-reduced-transparency) |
| `feImage` with `data:`/`blob:` href inside filters | Yes (blob cheaper; needs `img-src blob:`/`data:` if a CSP is ever added — none in the repo today) | data-URL only from *rendered* (not `display:none`) SVG hosts (sohum note); quirks above | Yes | sohum `LiquidGlassFilter.jsx`, xcyber `map.ts` |

**Bottom line**: true backdrop refraction is a **Chromium-only progressive enhancement** in Aug 2026.
Safari is actively implementing (July 2026 PRs) — gate by capability + UA, not by a build flag, so
Safari picks it up when it ships. Feature detection must be UA-assisted: `CSS.supports("backdrop-filter","url(#x)")`
returns true in browsers that parse-but-no-op, which is why xcyber's `support.ts` excludes
Safari/Firefox by UA on top of the `CSS.supports` check.

---

## (c) Recommendation

### Verdict: **C — reproduce with existing primitives** (≈150 lines of owned code), stealing the
xcyber architecture (headless engine + CSS element contract + tier gates), the xcyber canvas map
(edge-band displacement), and the sohum rim (mask-composite specular ring). Do **not** adopt a
dependency (A), and don't vendored-fork a whole repo (B).

Why not A: every candidate is MIT but none matches our constraints out of the box — sohum ships a
5-file CSS system with its own class contract, light-mode scrims and macOS-calibrated white tint
(wrong for our dark `--glass-tint: 221 42% 9%` over satellite imagery); PallavAg filters content
wrappers (wrong architecture over a Cesium canvas); xcyber is the right shape but is a 0-star,
month-old package — the value is its ~100 lines of core, not the dependency. The app ships 4.5 MB;
cosmetics must not add a supply-chain edge. Why not B wholesale: our glass family already defines
the material's tint/blur/saturate/hairline; we only need the two missing optical layers.

### The two layers to add

**Layer 1 — specular rim (all browsers, BALANCED and up).** Pure CSS, zero runtime cost beyond a
pseudo-element per surface. Adapted from sohum's measured vertical-axis rim, recolored into the
existing hairline family (dark-world numbers, restrained):

```css
:root {
  --glass-rim-lit: hsl(206 80% 92% / 0.28);   /* top/bottom hairline core */
  --glass-rim-dark: hsl(224 60% 3% / 0.30);   /* side hairline */
  --glass-rim-fade: 12px;                      /* bright falloff */
  --glass-rim-side: 5px;                       /* dark falloff */
}
/* on each glass surface (::after, pointer-events:none, border-radius:inherit): */
.glass-rim::after {
  content: ''; position: absolute; inset: 0; border-radius: inherit; padding: 1px;
  pointer-events: none;
  background:
    linear-gradient(to right, var(--glass-rim-dark) 0, transparent var(--glass-rim-side),
      transparent calc(100% - var(--glass-rim-side)), var(--glass-rim-dark) 100%),
    linear-gradient(to bottom, var(--glass-rim-lit) 0, var(--glass-rim-lit) 1px,
      transparent var(--glass-rim-fade), transparent calc(100% - var(--glass-rim-fade)),
      var(--glass-rim-lit) calc(100% - 1px), var(--glass-rim-lit) 100%);
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;
  mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  mask-composite: exclude;
}
```
This replaces the current single flat `--glass-highlight` inset with Apple's actual rim geometry
(bright horizontal hairlines, dark flanks, crossover inside the corner arc) and works in every
browser. Keep `--glass-hairline` border as-is underneath it.

**Layer 2 — edge-only backdrop refraction (Chromium; ULTRA/HIGH only).** One small module, e.g.
`design-system/refraction.ts`, and one shared `<defs>` host:

1. Support gate (xcyber `support.ts` logic): UA excludes Safari/Firefox, then
   `CSS.supports("backdrop-filter","url(#x)")`, then canvas readback try/catch. Media-query hard
   gates: `prefers-reduced-transparency: reduce` and `prefers-contrast: more` → off (our tokens
   already push surfaces near-opaque there; refraction under near-opaque tint is wasted cost).
2. Per-surface map: xcyber's canvas recipe above, **sized to the element** (never stretch one map —
   sohum's anisotropy trap: a shared 512px map's bezel becomes 62 px on the long axis and 7 px on the
   short axis of a 660×72 card, i.e. fisheye). `ResizeObserver`, debounce ~120 ms, `blob:` URL,
   revoke the old one. Set `color-interpolation-filters="sRGB"` on the filter (phantom-displacement
   trap) and only set the data-attribute after the first map loads (empty feImage shears the backdrop).
3. Element contract, exactly xcyber's (frozen, minimal, plays with tokens):
   `--glass-refract: url(#...)` + `data-glass-refract="ultra|high"` set by the module; CSS owns the
   actual `backdrop-filter` so all existing token fallbacks keep working:

```css
/* additive rule — when the attribute is absent, today's frosted glass is untouched */
[data-glass-refract] {
  -webkit-backdrop-filter: var(--glass-refract) blur(var(--glass-refract-blur, 6px))
                           saturate(var(--glass-saturate));
  backdrop-filter: var(--glass-refract) blur(var(--glass-refract-blur, 6px))
                   saturate(var(--glass-saturate));
  /* identical prefixed/unprefixed values — the lightningcss prefix-pair trap */
}
```
   Interior blur drops 16px → ~6px when refracting (the lens supplies the "material" read; xcyber
   ships 3px, we stay higher for text legibility) — the *center* stays neutral-gray in the map, so
   text sits over undistorted, tinted, blurred world exactly as today.
4. Filter graph: single-pass `feImage` + `feDisplacementMap` (xChannelSelector R, yChannelSelector B)
   for panels/chrome/sheet/compact. The 3-pass chromatic graph **only** on the popover, **only** at
   ULTRA — sohum measured 5 concurrent 3-pass surfaces freezing Chrome's compositor while 1 was fine,
   and we have ~11 glass surfaces; one popover at a time is inside the safe envelope.

### Sizing per quality tier

| Tier | Refraction | Rim | Interior |
|---|---|---|---|
| ULTRA | All 5 surface classes, single-pass, `scale ≈ -72`, edge band `border 0.06` (≈10–14 px, sits under panel padding, never under text), `mapBlur 10`; popover additionally 3-pass chroma ≈ 4 (restrained fringe) | Full (`--glass-rim-lit` 0.28) | blur 6px, alphas unchanged |
| HIGH | Single-pass everywhere incl. popover, `scale ≈ -48`, band ≈8 px, `mapBlur 8`; no chromatic passes | Full | blur 8px |
| BALANCED | **None** (no SVG filters at all) | Rim only (pure CSS, ~free) | current 16px frosted, unchanged |
| LOW | None | None — `[data-quality="low"]` suppresses the ::after | **exactly today's frosted glass, byte-for-byte tokens** |

Wire-up: the store already holds `qualityTier` (`state/store.ts`; `'ultra'|'high'|'balanced'|'low'`,
CINEMATIC_ARCHITECTURE.md §11). Mirror it once onto `<html data-quality>` and let the refraction
module subscribe; Safari/Firefox resolve to "rim-only" at every tier automatically, which **is** the
graceful fallback (current design + better rim). Negative scale = convex/magnifying read (xcyber
default −112 is theatrical; −72/−48 is the restrained "world bends at the chrome edge" from the
visual-direction memory).

Costs: map generation is a 4-draw canvas fill per surface per resize (≪2 ms for panel sizes, off the
hot path); runtime is one extra displacement sample in the compositor pass Chromium already runs for
our 16px blur — and since the backdrop is a live Cesium render, that pass already re-runs per frame
today. Est. added code: ~150 lines TS + ~40 lines CSS + ~10 lines JSX defs host. Zero dependencies,
zero bundle-relevant assets (maps are runtime blobs).

Cautions to carry into implementation (all from primary sources above):
- **Backdrop Root trap** (sohum, measured): no `isolation`, `contain: paint`, `content-visibility: auto`,
  ancestor `transform`/`opacity<1`/`mask`/`will-change` around glass surfaces, or backdrop-filter
  silently samples nothing. Panel enter animations that transform an ancestor will kill the material
  while animating — audit `--dur-panel` motion.
- Re-test the support gate when Safari ships `backdrop-filter: url()` (WebKit PRs are live as of
  July 2026) — capability check, not build flag; also re-check the Safari filter-source-area cap then.
- If a CSP is ever added at the Pages gateway, `img-src blob:` is required for the feImage maps.
- Verify (spike, ~1 h) sohum's element-`filter`-over-backdrop-filter combo on Firefox against the
  Cesium canvas before considering it as a Firefox path; treat it as a later bonus, not a dependency
  of this work.

---

## (d) frontend-ui-ux-skill audit method — summary for manual application

Source: [overseek944/frontend-ui-ux-skill](https://github.com/overseek944/frontend-ui-ux-skill)
(`SKILL.md`, MIT, branch `master`; references/: hci-foundations, accessibility, performance,
anti-patterns, component-architecture). "Evidence-based doctrine" — every choice must trace to a
heuristic, an accessibility requirement, a perf budget, or an existing convention; "looks fine" is
never sufficient. Precedence: explicit instruction → project's existing system → doctrine defaults
("never introduce a second, competing pattern next to one that already exists").

**Five pillars checked:**
1. **Interaction & information design** — Nielsen's 10 (feedback <100 ms; plain-language errors with
   next action; visible way out of destructive flows), Fitts (44×44 pt targets, 24 px WCAG floor;
   destructive far from primary), Hick (≤~7 nav items, one primary action per screen), Miller (group
   fields 3–5), Jakob (match ecosystem conventions), Peak–End (craft error/empty/success states).
2. **Visual system** — one modular type scale; 45–75 ch lines; 4/8 px baseline; palette derived from
   something real; semantic vs brand color never collide; 4.5:1 / 3:1 contrast pre-ship; motion
   150–300 ms eased, gated on `prefers-reduced-motion`. Anti-pattern list explicitly flags
   **"gratuitous glassmorphism"** — glass must be a considered material choice, which is exactly why
   the recommendation above keeps refraction off text centers and off LOW tier.
3. **Architecture** — semantic HTML before div+ARIA; design tokens as single source of truth ("a
   hardcoded hex duplicating an existing token is a bug"); one CSS methodology; state completeness
   (loading/empty/error for everything); mobile-first, `clamp()`, container queries.
4. **Accessibility (hard floor: WCAG 2.2 AA)** — full keyboard pass with visible focus; real labels;
   color never the only signal; errors announced; verify by doing (keyboard-only pass, 200%/400%
   zoom, screen-reader spot check).
5. **Performance** — CWV at p75: LCP ≤2.5 s, INP ≤200 ms, CLS ≤0.1; reserve space pre-load; keep the
   main thread free; "question any new dependency that exists to do something a few lines of code
   could do directly" (which is the (c) verdict in one line).

**Definition-of-Done gate** (run before declaring the glass work finished): keyboard + visible focus;
contrast pairs pass; holds at 320 px and 400% zoom without body scroll; light/dark + reduced-motion
respected; loading/empty/error states exist; every element earns its place; LCP element fast and
shift-free; no token-duplicating hardcoded values; every visual choice defensible out loud; **actually
looked at it rendered, not just read the source**. For the glass pass specifically this means: verify
text contrast over the brightest satellite tile (glacier/snow) at every tier, and eyeball the ULTRA
tier in a real Chromium build over the live Cesium scene, per the production-verification memory.

---

### Source index
- https://github.com/sohumsuthar/liquid-glass (+ raw: `css/liquid-glass-core.css`, `components/LiquidGlassFilter.jsx`, `PHYSICS.md`, `lib/glass-optics.mjs`)
- https://github.com/xcyberpunkx0/liquid-glass (+ raw: `src/core/{map,svg,support,tiers,engine,apply}.ts`, `src/styles.css`)
- https://github.com/PallavAg/liquid-glass-web-react (+ raw: `src/core/{displacementMap,engine}.ts`)
- https://github.com/shuding/liquid-glass (+ raw: `liquid-glass.js`)
- https://github.com/overseek944/frontend-ui-ux-skill (+ raw: `SKILL.md`)
- https://www.apple.com/newsroom/2025/06/apple-introduces-a-delightful-and-elegant-new-software-design/
- https://bugs.webkit.org/show_bug.cgi?id=245510 · https://github.com/mdn/browser-compat-data/issues/24110 · https://github.com/w3c/svgwg/issues/1142 · https://connect.mozilla.org/t5/ideas/support-svg-filters-in-backdrop-filter-for-advanced-glass/idi-p/98453
- https://kube.io/blog/liquid-glass-css-svg/ · https://medium.com/ekino-france/liquid-glass-in-css-and-svg-839985fcb88d
- https://caniuse.com/mdn-css_properties_mask-composite · https://caniuse.com/mdn-css_at-rules_media_prefers-reduced-transparency · https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/corner-shape · https://squircle.js.org/blog/squircles-in-css
- Local grounding: `apps/web/src/design-system/tokens.css`, `apps/web/src/state/store.ts` (qualityTier), `docs/CINEMATIC_ARCHITECTURE.md` §11, `apps/web/src/app/app.css` (~11 backdrop-filter surfaces)
