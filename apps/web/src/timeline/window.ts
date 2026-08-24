/**
 * Pure timeline window math (docs/CINEMATIC_ROADMAP.md §10 C5, P1 scope): the scrubbable
 * knowledge-time window is the 72 h ending at an anchor instant. ISO 8601 UTC strings in and
 * out — time is data, never a Date object in the store. Scrub positions are truncated to the
 * minute: URLs stay stable and no sub-minute precision is fabricated.
 */
export const WINDOW_HOURS = 72;
export const WINDOW_MS = WINDOW_HOURS * 3_600_000;
export const SCRUB_STEP_MS = 60_000;

export type TimelineWindow = readonly [start: string, end: string];

const toIso = (ms: number): string => new Date(ms).toISOString().replace('.000Z', 'Z');

export const truncateToMinute = (iso: string): string => {
  const ms = Date.parse(iso);
  if (Number.isNaN(ms)) throw new Error(`not an instant: ${iso}`);
  return toIso(Math.floor(ms / SCRUB_STEP_MS) * SCRUB_STEP_MS);
};

/** The [end−72h, end] window, minute-aligned. */
export const windowEndingAt = (endIso: string): TimelineWindow => {
  const end = truncateToMinute(endIso);
  return [toIso(Date.parse(end) - WINDOW_MS), end];
};

export const isWithin = (iso: string, window: TimelineWindow): boolean => {
  const ms = Date.parse(iso);
  return !Number.isNaN(ms) && ms >= Date.parse(window[0]) && ms <= Date.parse(window[1]);
};

export const clampToWindow = (iso: string, window: TimelineWindow): string => {
  const ms = Date.parse(iso);
  return toIso(Math.min(Date.parse(window[1]), Math.max(Date.parse(window[0]), ms)));
};

/** 0 at the window start, 1 at its end (clamped). */
export const fractionOf = (iso: string, window: TimelineWindow): number => {
  const start = Date.parse(window[0]);
  const end = Date.parse(window[1]);
  if (end <= start) return 1;
  return (Date.parse(clampToWindow(iso, window)) - start) / (end - start);
};

export const timeAtFraction = (window: TimelineWindow, fraction: number): string => {
  const f = Math.min(1, Math.max(0, fraction));
  const start = Date.parse(window[0]);
  const end = Date.parse(window[1]);
  return truncateToMinute(toIso(start + f * (end - start)));
};

/**
 * Where the boot window is anchored: at `now`, unless a deep-linked `as_of` predates the live
 * 72 h window — then the window is anchored at that knowledge time ([T−72h, T]; the forecast
 * half of the C5 window is deferred past P1).
 */
export const anchorForBoot = (asOf: string | null, nowIso: string): string => {
  const now = truncateToMinute(nowIso);
  if (asOf === null) return now;
  return isWithin(asOf, windowEndingAt(now)) ? now : truncateToMinute(asOf);
};
