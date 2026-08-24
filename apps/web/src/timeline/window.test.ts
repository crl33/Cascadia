import { describe, expect, it } from 'vitest';
import {
  WINDOW_MS, anchorForBoot, clampToWindow, fractionOf, isWithin, timeAtFraction,
  truncateToMinute, windowEndingAt, type TimelineWindow,
} from './window';

const NOW = '2026-08-24T12:00:00Z';
const WINDOW: TimelineWindow = ['2026-08-21T12:00:00Z', '2026-08-24T12:00:00Z'];

describe('timeline window math', () => {
  it('truncates to the minute and normalizes millis', () => {
    expect(truncateToMinute('2026-08-24T12:34:56.789Z')).toBe('2026-08-24T12:34:00Z');
    expect(truncateToMinute('2026-08-24T12:34:00Z')).toBe('2026-08-24T12:34:00Z');
    expect(() => truncateToMinute('yesterday')).toThrow();
  });

  it('builds the [T-72h, T] window, minute-aligned', () => {
    const window = windowEndingAt('2026-08-24T12:00:30Z');
    expect(window).toEqual(WINDOW);
    expect(Date.parse(window[1]) - Date.parse(window[0])).toBe(WINDOW_MS);
  });

  it('clamps to the window edges and keeps interior instants', () => {
    expect(clampToWindow('2026-08-20T00:00:00Z', WINDOW)).toBe(WINDOW[0]);
    expect(clampToWindow('2026-08-25T00:00:00Z', WINDOW)).toBe(WINDOW[1]);
    expect(clampToWindow('2026-08-23T06:30:00Z', WINDOW)).toBe('2026-08-23T06:30:00Z');
  });

  it('containment matches the clamp', () => {
    expect(isWithin(WINDOW[0], WINDOW)).toBe(true);
    expect(isWithin(WINDOW[1], WINDOW)).toBe(true);
    expect(isWithin('2026-08-20T11:59:00Z', WINDOW)).toBe(false);
    expect(isWithin('not a time', WINDOW)).toBe(false);
  });

  it('fraction and timeAtFraction are inverse at minute resolution', () => {
    expect(fractionOf(WINDOW[0], WINDOW)).toBe(0);
    expect(fractionOf(WINDOW[1], WINDOW)).toBe(1);
    expect(fractionOf('2026-08-23T00:00:00Z', WINDOW)).toBeCloseTo(0.5, 10);
    for (const iso of ['2026-08-21T12:00:00Z', '2026-08-22T03:07:00Z', '2026-08-24T11:59:00Z']) {
      expect(timeAtFraction(WINDOW, fractionOf(iso, WINDOW))).toBe(iso);
    }
    expect(timeAtFraction(WINDOW, -1)).toBe(WINDOW[0]);
    expect(timeAtFraction(WINDOW, 2)).toBe(WINDOW[1]);
  });

  it('anchors the boot window at now, unless as_of predates the live 72 h window', () => {
    expect(anchorForBoot(null, NOW)).toBe('2026-08-24T12:00:00Z');
    expect(anchorForBoot('2026-08-23T00:00:00Z', NOW)).toBe('2026-08-24T12:00:00Z');   // inside → live window
    expect(anchorForBoot('2025-12-12T08:15:00Z', NOW)).toBe('2025-12-12T08:15:00Z');   // Event Zero replay → anchored at T
  });
});
