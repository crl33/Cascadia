/**
 * Motion tokens (docs/CAMERA_SYSTEM.md §9): the only module where a duration or easing is
 * written. Literal values are FACT from v1/design_guidelines.md. Also owns the minimum-jerk
 * easing the camera flight path uses; CSS transitions take the bezier tokens from tokens.css.
 */
export const MOTION = {
  easing: {
    standard: [0.22, 1, 0.36, 1],
    snappy: [0.2, 0.9, 0.2, 1],
    calm: [0.16, 1, 0.3, 1],
  },
  duration: { micro: 140, ui: 220, panel: 320, state: 520, ambient: 2400 },
  profile: { flight: 'minimum-jerk' },
  flight: { minMs: 600, maxMs: 4200, baseMs: 600, perDoublingMs: 550, scaleKm: 5, heightWeight: 2, balancedTierScale: 0.8 },
} as const;

export type MotionPreference = 'full' | 'reduced';
export type MotionSetting = 'system' | MotionPreference;

/** `userSetting ?? (prefers-reduced-motion ? 'reduced' : 'full')` — an explicit choice wins. */
export const resolveMotion = (setting: MotionSetting, systemReduced: boolean): MotionPreference =>
  setting === 'system' ? (systemReduced ? 'reduced' : 'full') : setting;

/** Minimum-jerk profile 10t³ − 15t⁴ + 6t⁵: zero velocity and acceleration at both ends. */
export const minimumJerk = (t: number): number => {
  const x = Math.min(1, Math.max(0, t));
  return x * x * x * (10 + x * (-15 + 6 * x));
};
