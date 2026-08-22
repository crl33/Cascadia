import { describe, expect, it } from 'vitest';
import { computeFlightDuration, framingRange, haversineM } from './flight-math';
import { MOTION } from '../design-system/motion';

describe('computeFlightDuration', () => {
  it('is the minimum for no movement and capped at the maximum for planetary moves', () => {
    expect(computeFlightDuration(0, 0)).toBe(MOTION.flight.minMs);
    expect(computeFlightDuration(20_000_000, 5_000_000)).toBe(MOTION.flight.maxMs);
  });
  it('grows monotonically with distance and with height change', () => {
    const d1 = computeFlightDuration(10_000, 0), d2 = computeFlightDuration(100_000, 0), d3 = computeFlightDuration(1_000_000, 0);
    expect(d1).toBeLessThanOrEqual(d2);
    expect(d2).toBeLessThanOrEqual(d3);
    expect(computeFlightDuration(10_000, 50_000)).toBeGreaterThan(d1);
  });
  it('keeps the Skagit flight from the initial view under the ~4 s cap', () => {
    const distance = haversineM(-122.3, 47.6, -121.35, 48.6);
    const duration = computeFlightDuration(distance, 1_500_000 - 270_000);
    expect(duration).toBeLessThanOrEqual(4200);
    expect(duration).toBeGreaterThan(MOTION.flight.minMs);
  });
  it('scales with the balanced-tier factor but never below the minimum', () => {
    expect(computeFlightDuration(0, 0, MOTION.flight.balancedTierScale)).toBe(MOTION.flight.minMs);
  });
});

describe('framingRange', () => {
  it('fits a sphere: range × sin(half angle) ≥ radius', () => {
    const range = framingRange(100_000, 0.35, 1);
    expect(range * Math.sin(0.35)).toBeCloseTo(100_000, 3);
    expect(framingRange(100_000, 0.35)).toBeGreaterThan(range);
  });
});
