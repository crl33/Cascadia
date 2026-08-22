/**
 * Forecast-point marker styling: pure mapping from (observed category, freshness, selection) to
 * marker size/tone and the label text (category word printed — never colour alone).
 */
import { COLOR, type Hsl } from '../../design-system/tokens';
import type { FloodCategory, FreshnessState } from '../../contracts/schemas';
import { CATEGORY_BADGE, FRESHNESS_BADGE } from '../../design-system/badges';

export interface MarkerSemantic {
  name: string;
  category: FloodCategory;
  freshness: FreshnessState;
  selected: boolean;
  hovered: boolean;
}

export interface MarkerStyle {
  pixelSize: number;
  color: Hsl;
  outline: Hsl;
  outlineWidthPx: number;
  labelText: string;
  labelVisible: boolean;
}

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

export function riverMarker(s: MarkerSemantic): MarkerStyle {
  const stale = s.freshness !== 'current';
  const freshnessNote = stale ? ` · ${FRESHNESS_BADGE[s.freshness].label}` : '';
  return {
    pixelSize: s.selected ? 14 : s.hovered ? 12 : 10,
    color: categoryColor(s.category),
    outline: s.selected ? COLOR.textPrimary : COLOR.canvas,
    outlineWidthPx: s.selected ? 3 : 2,
    labelText: `${s.name} · ${CATEGORY_BADGE[s.category].label}${freshnessNote}`,
    labelVisible: s.selected || s.hovered,
  };
}
