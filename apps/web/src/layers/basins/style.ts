/**
 * Basin edge styling: pure, total mapping from semantic state to presentation (widths, tokens,
 * alpha). No renderer calls. Boundaries are embedded in the landscape (LAYER_SYSTEM §9.3): faint
 * hairline at orbital/state, a gentle stronger edge for the selected basin, amber/red only from
 * official categories.
 */
import { COLOR, type Hsl } from '../../design-system/tokens';
import type { FloodCategory } from '../../contracts/schemas';
import type { Band } from '../../scene/bands';

export interface BasinEdgeSemantic {
  lod: 'state' | 'basin';
  band: Band;
  selected: boolean;
  hovered: boolean;
  /** Official hazard category of the basin outlet, or 'unknown'. */
  category: FloodCategory;
  /** Whether a basin-LOD outline exists for this basin (then the state-LOD one yields to it). */
  hasBasinLod: boolean;
}

export interface EdgeStyle { show: boolean; widthPx: number; color: Hsl; alpha: number; fadeIn: boolean }

const categoryColor = (category: FloodCategory): Hsl => {
  switch (category) {
    case 'none': return COLOR.cyan;
    case 'action': return COLOR.amberWatch;
    case 'minor': return COLOR.amberElevated;
    case 'moderate':
    case 'major': return COLOR.floodRed;
    case 'unknown': return COLOR.neutralUnknown;
  }
};

export function basinEdge(s: BasinEdgeSemantic): EdgeStyle {
  const color = categoryColor(s.category);
  const overview = s.band === 'orbital' || s.band === 'state';
  if (s.lod === 'basin') {
    // Only the selected basin carries a basin-LOD outline; it is the stronger edge at every band.
    return { show: s.selected, widthPx: 2.2, color, alpha: 0.9, fadeIn: true };
  }
  if (s.selected && s.hasBasinLod) return { show: false, widthPx: 0, color, alpha: 0, fadeIn: false };
  if (s.selected) return { show: true, widthPx: 2, color, alpha: 0.85, fadeIn: true };
  if (!overview) return { show: false, widthPx: 0, color, alpha: 0, fadeIn: false };
  if (s.hovered) return { show: true, widthPx: 1.6, color, alpha: 0.6, fadeIn: false };
  return { show: true, widthPx: 1, color, alpha: 0.32, fadeIn: false };
}
