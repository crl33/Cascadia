/**
 * Snow-water-equivalent field styling: pure, total mapping from one cell's SWE to a pixel.
 * MODELED register (SNODAS is an assimilation analysis, truth `authoritative_model` on the
 * document): snow renders as a cold white-blue veil — paler and bluer than the rain wash,
 * never the derived amber, never a warm hue.
 *
 * Honesty rules, test-pinned (same family as precip):
 * - a SNOW-FREE cell is transparent — bare ground is the truthful rendering of 0 mm SWE;
 * - a SENTINEL cell (off-grid / not analyzed) is also transparent; painting it would claim
 *   an analysis that does not exist;
 * - the ramp is monotone and saturates at deep-winter pack: 400 mm SWE reads fully snowy and
 *   2,000 mm does not pretend to out-render it.
 */
import type { FieldPixel } from '../fields/WeatherFieldLayer';

/** Below this the analysis is noise-level patchiness, not snowpack. */
const BARE_BELOW_MM = 1;
const SATURATE_MM = 400;
const MAX_ALPHA = 140; // a veil: terrain, rivers and hatches stay legible through full pack

export function snowPixel(mm: number | null): FieldPixel {
  if (mm == null || !Number.isFinite(mm) || mm < BARE_BELOW_MM) {
    return { r: 0, g: 0, b: 0, a: 0 };
  }
  const t = Math.min(Math.sqrt(mm / SATURATE_MM), 1);
  // thin cover is a cool haze; deep pack whitens toward a blue-tinged snowfield
  return {
    r: Math.round(180 + 60 * t),
    g: Math.round(200 + 45 * t),
    b: 255,
    a: Math.round(30 + (MAX_ALPHA - 30) * t),
  };
}
