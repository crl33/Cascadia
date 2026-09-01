/**
 * Colour tokens as HSL numbers for renderer layers (layers/<name>/style.ts). These mirror
 * tokens.css exactly; the CSS is for React, this file is for Cesium materials. No other module
 * may carry a colour literal.
 */
export interface Hsl { h: number; s: number; l: number }

export const COLOR = {
  canvas: { h: 222, s: 52, l: 6 },
  textPrimary: { h: 210, s: 40, l: 98 },
  textSecondary: { h: 215, s: 18, l: 78 },
  textMuted: { h: 215, s: 14, l: 62 },
  stroke: { h: 215, s: 22, l: 22 },
  cyan: { h: 191, s: 92, l: 55 },
  glacier: { h: 205, s: 88, l: 58 },
  /** The PHYSICAL water register (mission §10): river/lake geography as calm natural blue.
   * Cyan stays the STATE/selection voice; a river's geometry is geography, not a signal. */
  water: { h: 203, s: 62, l: 52 },
  amberWatch: { h: 38, s: 92, l: 58 },
  amberElevated: { h: 32, s: 96, l: 56 },
  floodRed: { h: 6, s: 86, l: 56 },
  neutralUnknown: { h: 215, s: 10, l: 58 },
} as const satisfies Record<string, Hsl>;

export type ColorToken = keyof typeof COLOR;
