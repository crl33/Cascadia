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
  /** The Cascade-derived rate of rise already in the envelope; null when the method refused. */
  trend: { direction: 'rising' | 'falling' | 'steady' | 'unknown'; rate: { value: number; unit: string } | null } | null;
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

/**
 * The trend fragment of the label. A glyph plus the word plus the rate — never colour, and never
 * the glyph alone (VISUAL_TRUTH_DOCTRINE §7.2: at least one non-colour carrier; a bare arrow at
 * label size is a squint test). `unknown` prints nothing: rate-of-rise REFUSES on tidal or
 * unmeasured gauges rather than guessing, and an absent statement must stay absent — an
 * "unknown trend" note on every quiet marker would train readers to ignore the slot.
 */
const trendNote = (trend: MarkerSemantic['trend']): string => {
  if (!trend || trend.direction === 'unknown') return '';
  const glyph = trend.direction === 'rising' ? '↗' : trend.direction === 'falling' ? '↘' : '→';
  const rate = trend.rate ? ` ${Math.abs(trend.rate.value).toFixed(2)} ${trend.rate.unit}` : '';
  return ` · ${glyph} ${trend.direction}${rate}`;
};

export function riverMarker(s: MarkerSemantic): MarkerStyle {
  const stale = s.freshness !== 'current';
  const freshnessNote = stale ? ` · ${FRESHNESS_BADGE[s.freshness].label}` : '';
  return {
    pixelSize: s.selected ? 14 : s.hovered ? 12 : 10,
    color: categoryColor(s.category),
    outline: s.selected ? COLOR.textPrimary : COLOR.canvas,
    outlineWidthPx: s.selected ? 3 : 2,
    labelText: `${s.name} · ${CATEGORY_BADGE[s.category].label}${trendNote(s.trend)}${freshnessNote}`,
    labelVisible: s.selected || s.hovered,
  };
}
