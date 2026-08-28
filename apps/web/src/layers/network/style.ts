/**
 * River-network styling: pure, total mapping from (mainstem, band, basin selection) to line
 * presentation. CARTOGRAPHIC register — this is where the rivers ARE; what they are doing
 * (flow, trend, category) stays on the truth-classed markers and panels. So: one hue (water
 * cyan), no state encoded, and the only variations are structural (mainstem vs tributary)
 * and attentional (the selected basin's rivers read a little brighter).
 *
 * "Rivers as first-class visual objects" (design direction 2026-08-28): the hydrologic
 * network is the skeleton of Cascadia's world and draws from the overview down — mainstems
 * from orbit, the full network once a basin has the frame.
 */
import { COLOR, type Hsl } from '../../design-system/tokens';
import type { Band } from '../../scene/bands';

export interface RiverLineSemantic {
  mainstem: boolean;
  band: Band;
  /** The river's basin is the selected one. */
  inSelectedBasin: boolean;
}

export interface RiverLineStyle {
  show: boolean;
  widthPx: number;
  color: Hsl;
  alpha: number;
}

export function riverLine(s: RiverLineSemantic): RiverLineStyle {
  const overview = s.band === 'orbital';
  if (overview && !s.mainstem) {
    return { show: false, widthPx: 0, color: COLOR.cyan, alpha: 0 };
  }
  const width = s.mainstem ? (overview ? 1.4 : 1.8) : 1.0;
  const alpha = (s.mainstem ? 0.8 : 0.4) * (s.inSelectedBasin ? 1.15 : 1);
  return { show: true, widthPx: width, color: COLOR.cyan, alpha: Math.min(alpha, 0.95) };
}
