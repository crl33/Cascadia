/**
 * Observed-precipitation field styling: pure, total mapping from one cell's accumulation to a
 * pixel. OBSERVED register (truth `observation` on the document): this is what the radar and
 * gauges measured, so it renders in the rain's own blue-teal — a hue no derived or
 * experimental surface uses (susceptibility speaks amber hatch, hazard speaks the official
 * category colours) — and stays a translucent wash under all of them.
 *
 * Three honesty rules, test-pinned:
 * - a DRY cell is transparent — no texture is the truthful rendering of "0.0 mm measured";
 * - a SENTINEL cell (radar could not say) is also transparent, because painting it any colour
 *   would claim a measurement that does not exist; the two are indistinguishable on the map
 *   by design — the panel and provenance carry coverage, the map never fabricates it;
 * - the ramp is monotone and saturates: intensity discriminates drizzle from downpour in the
 *   range that matters (0–8 mm/h) and stops claiming precision above it.
 */

import type { FieldPixel } from '../fields/WeatherFieldLayer';

/** Below half a quantization step there is nothing to show — 0.0 mm measured is DRY. */
const DRY_BELOW_MM = 0.05;
/** The accumulation at which the wash reaches full presence; heavier rain reads the same. */
const SATURATE_MM = 8;
const MAX_ALPHA = 150; // ~0.59: a wash the terrain and rivers stay legible through

export function precipPixel(mm: number | null): FieldPixel {
  if (mm == null || !Number.isFinite(mm) || mm < DRY_BELOW_MM) {
    return { r: 0, g: 0, b: 0, a: 0 };
  }
  const t = Math.min(Math.sqrt(mm / SATURATE_MM), 1); // sqrt: drizzle is visible, downpour saturates
  // light rain speaks pale teal, heavy rain deepens toward blue — one hue family, no red ever
  return {
    r: Math.round(96 - 60 * t),
    g: Math.round(190 - 60 * t),
    b: Math.round(235 - 20 * t),
    a: Math.round(40 + (MAX_ALPHA - 40) * t),
  };
}
