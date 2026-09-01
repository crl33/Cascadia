/**
 * Edge-band liquid-glass refraction (mission §14, decision doc
 * docs/research/… — verdict C: reproduce with primitives, ~150 lines, no deps).
 *
 * Technique: a per-surface displacement map (red X-ramp ⊕ blue Y-ramp, interior
 * neutralized by a blurred 50%-gray inset) fed through feImage → feDisplacementMap
 * inside `backdrop-filter: url(#…)`. The neutral center leaves text over undistorted
 * world; only an edge band (~width set by the map blur) bends the backdrop — Apple's
 * lensing, restrained. Specular rim + frosted blur live in surface.css and carry every
 * browser; THIS module is a Chromium-only enhancement at ULTRA/HIGH quality.
 *
 * Correctness details from the research (each one load-bearing):
 * - filters default to linearRGB, remapping neutral gray 128 and injecting phantom
 *   displacement → color-interpolation-filters="sRGB" on the filter;
 * - one map PER SURFACE at its real size (a stretched shared map's edge band becomes
 *   anisotropic — the fisheye trap);
 * - the CSS variable and data attribute are set only after the map blob exists (an
 *   empty feImage shears the whole backdrop);
 * - blob: URLs, revoked on replacement; regeneration debounced behind ResizeObserver.
 */
import type { QualityTier } from '../state/store';

const TIER: Record<string, { scale: number; band: number; mapBlur: number; blurPx: number } | null> = {
  ultra: { scale: -72, band: 0.06, mapBlur: 10, blurPx: 7 },
  high: { scale: -48, band: 0.045, mapBlur: 8, blurPx: 8 },
  balanced: null,
  low: null,
};

let seq = 0;
let defsHost: SVGSVGElement | null = null;
const attached = new Map<HTMLElement, { filterId: string; blobUrl: string | null; ro: ResizeObserver; timer: number | null }>();
let activeTier: QualityTier = 'balanced';
let supported: boolean | null = null;

function supportsBackdropSvgFilter(): boolean {
  if (supported !== null) return supported;
  const ua = navigator.userAgent;
  const isChromium = /Chrom(e|ium)|Edg\//.test(ua) && !/Firefox/.test(ua);
  const parses =
    typeof CSS !== 'undefined' && CSS.supports('backdrop-filter', 'url(#x)');
  const calm =
    !window.matchMedia('(prefers-reduced-transparency: reduce)').matches &&
    !window.matchMedia('(prefers-contrast: more)').matches;
  // Safari/Firefox parse-but-no-op url() backdrop filters (verified Aug 2026) — the
  // CSS.supports check alone would strand them with no blur at all.
  supported = isChromium && parses && calm;
  return supported;
}

function host(): SVGSVGElement {
  if (defsHost) return defsHost;
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('aria-hidden', 'true');
  // rendered (not display:none — Safari ignores unrendered filter hosts) but invisible
  svg.style.cssText = 'position:absolute;width:0;height:0;overflow:hidden';
  document.body.appendChild(svg);
  defsHost = svg;
  return svg;
}

function drawMap(width: number, height: number, band: number, mapBlur: number): string | null {
  const canvas = document.createElement('canvas');
  canvas.width = Math.max(2, Math.round(width));
  canvas.height = Math.max(2, Math.round(height));
  const ctx = canvas.getContext('2d');
  if (!ctx) return null;
  const gx = ctx.createLinearGradient(0, 0, canvas.width, 0);
  gx.addColorStop(0, 'rgb(0,0,0)');
  gx.addColorStop(1, 'rgb(255,0,0)');
  ctx.fillStyle = gx;
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  const gy = ctx.createLinearGradient(0, 0, 0, canvas.height);
  gy.addColorStop(0, 'rgb(0,0,0)');
  gy.addColorStop(1, 'rgb(0,0,255)');
  ctx.globalCompositeOperation = 'difference';
  ctx.fillStyle = gy;
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.globalCompositeOperation = 'source-over';
  const inset = Math.round(Math.min(canvas.width, canvas.height) * band);
  ctx.filter = `blur(${mapBlur}px)`;
  ctx.fillStyle = 'rgba(128,128,128,0.93)';
  ctx.beginPath();
  ctx.roundRect(inset, inset, canvas.width - inset * 2, canvas.height - inset * 2, inset * 1.4);
  ctx.fill();
  return canvas.toDataURL('image/png');
}

function buildFilter(filterId: string): { feImage: SVGElement } {
  const ns = 'http://www.w3.org/2000/svg';
  const filter = document.createElementNS(ns, 'filter');
  filter.setAttribute('id', filterId);
  filter.setAttribute('color-interpolation-filters', 'sRGB');
  filter.setAttribute('x', '0');
  filter.setAttribute('y', '0');
  filter.setAttribute('width', '100%');
  filter.setAttribute('height', '100%');
  const feImage = document.createElementNS(ns, 'feImage');
  feImage.setAttribute('result', 'map');
  feImage.setAttribute('x', '0');
  feImage.setAttribute('y', '0');
  feImage.setAttribute('width', '100%');
  feImage.setAttribute('height', '100%');
  const feDisp = document.createElementNS(ns, 'feDisplacementMap');
  feDisp.setAttribute('in', 'SourceGraphic');
  feDisp.setAttribute('in2', 'map');
  feDisp.setAttribute('xChannelSelector', 'R');
  feDisp.setAttribute('yChannelSelector', 'B');
  feDisp.setAttribute('scale', '0');
  filter.appendChild(feImage);
  filter.appendChild(feDisp);
  host().appendChild(filter);
  return { feImage };
}

function refresh(el: HTMLElement): void {
  const entry = attached.get(el);
  const tier = TIER[activeTier];
  if (!entry) return;
  if (!tier) {
    el.removeAttribute('data-glass-refract');
    el.style.removeProperty('--glass-refract');
    el.style.removeProperty('--glass-refract-blur');
    return;
  }
  const rect = el.getBoundingClientRect();
  if (rect.width < 40 || rect.height < 24) return;
  const url = drawMap(rect.width, rect.height, tier.band, tier.mapBlur);
  if (!url) return;
  const filter = document.getElementById(entry.filterId);
  const feImage = filter?.querySelector('feImage');
  const feDisp = filter?.querySelector('feDisplacementMap');
  if (!feImage || !feDisp) return;
  feImage.setAttribute('href', url);
  feDisp.setAttribute('scale', String(TIER[activeTier]?.scale ?? 0));
  // set variable and attribute in the same synchronous block, after the map exists
  el.style.setProperty('--glass-refract', `url(#${entry.filterId})`);
  el.style.setProperty('--glass-refract-blur', `${tier.blurPx}px`);
  el.setAttribute('data-glass-refract', activeTier);
}

/** Attach edge refraction to a glass surface. No-op outside Chromium or below HIGH.
 * Returns a disposer. */
export function attachRefraction(el: HTMLElement): () => void {
  if (!supportsBackdropSvgFilter()) return () => {};
  const filterId = `glass-refract-${++seq}`;
  buildFilter(filterId);
  const entry = { filterId, blobUrl: null, ro: new ResizeObserver(() => schedule()), timer: null as number | null };
  const schedule = () => {
    if (entry.timer !== null) window.clearTimeout(entry.timer);
    entry.timer = window.setTimeout(() => {
      entry.timer = null;
      refresh(el);
    }, 120);
  };
  attached.set(el, entry);
  entry.ro.observe(el);
  refresh(el);
  return () => {
    entry.ro.disconnect();
    if (entry.timer !== null) window.clearTimeout(entry.timer);
    document.getElementById(filterId)?.remove();
    el.removeAttribute('data-glass-refract');
    el.style.removeProperty('--glass-refract');
    attached.delete(el);
  };
}

/** Quality-tier fan-out (store → module). balanced/low strip the enhancement. */
export function setRefractionQuality(tier: QualityTier): void {
  if (tier === activeTier) return;
  activeTier = tier;
  attached.forEach((_entry, el) => refresh(el));
}
