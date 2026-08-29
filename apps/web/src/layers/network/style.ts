/**
 * River-network styling: pure, total mapping from (mainstem, band, basin selection, flow
 * intensity) to line presentation.
 *
 * Two registers meet here WITHOUT blurring. The skeleton — where the rivers are, which is the
 * mainstem, one water-cyan hue — is CARTOGRAPHIC. On top of it, `intensity` carries the
 * contract's `flow_visual_intensity` (the station's day-of-year percentile / 100) and
 * modulates ONLY width and alpha — presence, a non-colour carrier (§7.2). `intensity: null`
 * falls back to the cartographic base. The hint's provenance renders in the basin panel.
 *
 * BAND-AWARE WEIGHT (visual-continuity pass 2026-08-29): a river must gain visual presence
 * as the camera approaches — a constant-width centerline perceptually vanishes as the world
 * gains detail. Widths are SCREEN PIXELS per semantic band, a cartographic hierarchy, and
 * explicitly NOT a claim about physical channel width. Tributaries stay quiet at basin band
 * (the whole network at full voice was clutter over imagery — measured 2026-08-29 baseline)
 * and come up as the camera descends. Mainstems of the selected basin may carry a restrained
 * glow at river/local bands — presence, never neon.
 */
import { COLOR, type Hsl } from '../../design-system/tokens';
import type { Band } from '../../scene/bands';

export interface RiverLineSemantic {
  mainstem: boolean;
  band: Band;
  /** The river's basin is the selected one. */
  inSelectedBasin: boolean;
  /** `flow_visual_intensity` for this river (0–1), or null when nothing is known. */
  intensity: number | null;
}

export interface RiverLineStyle {
  show: boolean;
  widthPx: number;
  color: Hsl;
  alpha: number;
  /** Restrained glow material for selected mainstems near the ground — presence, not neon. */
  glow: boolean;
}

/** Cartographic base width in screen px per band: [mainstem, tributary]. */
const BAND_WIDTH: Record<Band, readonly [number, number]> = {
  orbital: [1.2, 0],
  state: [1.6, 0.8],
  basin: [2.2, 1.0],
  river: [3.2, 1.7],
  local: [4.6, 2.5],
};
/** Base alpha per band: [mainstem, tributary]. Tributaries whisper until the camera is low. */
const BAND_ALPHA: Record<Band, readonly [number, number]> = {
  orbital: [0.8, 0],
  state: [0.7, 0.2],
  basin: [0.8, 0.26],
  river: [0.85, 0.45],
  local: [0.9, 0.55],
};
/** Full-intensity presence multiplier on width (p100 river ~1.8x its cartographic base). */
const INTENSITY_WIDTH_GAIN = 0.8;
const INTENSITY_ALPHA_GAIN = 0.12;

export function riverLine(s: RiverLineSemantic): RiverLineStyle {
  const overview = s.band === 'orbital';
  if (overview && !s.mainstem) {
    return { show: false, widthPx: 0, color: COLOR.cyan, alpha: 0, glow: false };
  }
  const lift = s.intensity == null ? 0 : Math.min(Math.max(s.intensity, 0), 1);
  const [stemWidth, tribWidth] = BAND_WIDTH[s.band];
  const [stemAlpha, tribAlpha] = BAND_ALPHA[s.band];
  const baseWidth = s.mainstem ? stemWidth : tribWidth;
  const width = baseWidth * (1 + INTENSITY_WIDTH_GAIN * lift);
  const alpha = (s.mainstem ? stemAlpha : tribAlpha) + INTENSITY_ALPHA_GAIN * lift;
  const selectedBoost = s.inSelectedBasin ? 1.12 : 1;
  return {
    show: true,
    widthPx: width,
    color: COLOR.cyan,
    alpha: Math.min(alpha * selectedBoost, 0.95),
    glow: s.mainstem && s.inSelectedBasin && (s.band === 'river' || s.band === 'local'),
  };
}
