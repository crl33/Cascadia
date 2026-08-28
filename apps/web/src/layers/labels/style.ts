/**
 * Label typography: pure, total mapping from a label's kind to its presentation — classic
 * cartographic register over satellite imagery. Every style carries a dark halo (outline)
 * because the ground below is now photography that can be any brightness; the halo is what
 * keeps a white name readable over a snowfield and a glacier-fed river alike.
 *
 * Register rules: water speaks italic in the water hue (rivers, lakes — the cartographic
 * convention this app's cyan already matches); administrative names speak upright white;
 * BASIN names are the quiet uppercase frame of the world; peaks are small and marked ▲.
 * Nothing here encodes any hydrologic state — labels are CARTOGRAPHIC, and a name never
 * changes colour because a river is rising.
 */
import type { LabelKind } from './select';

export interface LabelStyle {
  /** CSS font shorthand for Cesium's Label.font. */
  font: string;
  /** rgba 0-1 components (converted to Cesium.Color by the layer). */
  fill: { r: number; g: number; b: number; a: number };
  outline: { r: number; g: number; b: number; a: number };
  outlineWidth: number;
  /** Text transformation applied to the name before display. */
  transform: 'none' | 'uppercase-spaced';
  /** Prefix glyph (e.g. the summit mark), empty when none. */
  prefix: string;
}

const WHITE = { r: 1, g: 1, b: 1, a: 0.96 };
const QUIET_WHITE = { r: 1, g: 1, b: 1, a: 0.62 };
/** The water hue family the network layer already draws in (design-system cyan, lightened). */
const WATER = { r: 0.75, g: 0.91, b: 1, a: 0.95 };
const HALO = { r: 0.04, g: 0.09, b: 0.13, a: 0.85 };

const SANS = 'Inter, "Helvetica Neue", system-ui, sans-serif';

export const LABEL_STYLE: Record<LabelKind, LabelStyle> = {
  city: { font: `600 15px ${SANS}`, fill: WHITE, outline: HALO, outlineWidth: 4, transform: 'none', prefix: '' },
  town: { font: `400 12px ${SANS}`, fill: WHITE, outline: HALO, outlineWidth: 3, transform: 'none', prefix: '' },
  river: { font: `italic 500 12.5px ${SANS}`, fill: WATER, outline: HALO, outlineWidth: 3, transform: 'none', prefix: '' },
  water: { font: `italic 400 11px ${SANS}`, fill: WATER, outline: HALO, outlineWidth: 3, transform: 'none', prefix: '' },
  basin: { font: `600 12.5px ${SANS}`, fill: QUIET_WHITE, outline: HALO, outlineWidth: 3, transform: 'uppercase-spaced', prefix: '' },
  peak: { font: `400 11px ${SANS}`, fill: WHITE, outline: HALO, outlineWidth: 3, transform: 'none', prefix: '▲ ' },
};

/** THIN SPACE letterspacing for the basin frame (canvas fonts have no letter-spacing). */
export function displayText(name: string, kind: LabelKind): string {
  const style = LABEL_STYLE[kind];
  const text = style.transform === 'uppercase-spaced' ? name.toUpperCase().split('').join(' ') : name;
  return style.prefix + text;
}
