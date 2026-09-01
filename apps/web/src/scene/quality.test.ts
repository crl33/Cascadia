import { describe, expect, it } from 'vitest';
import {
  DOWNGRADE_MISSES,
  TIER_BUDGET,
  classifyProbe,
  downgradeAfterWindow,
  experienceOf,
  parseExperienceChoice,
  percentile,
  resolutionScaleFor,
  resolveTier,
  stepDown,
} from './quality';

describe('two experiences over four tiers', () => {
  it('auto follows the detection and is BALANCED until something is measured', () => {
    expect(resolveTier('auto', null)).toBe('balanced');
    expect(resolveTier('auto', 'ultra')).toBe('ultra');
    expect(resolveTier('auto', 'low')).toBe('low');
  });

  it('an explicit choice decides the experience; the detection only decides inside it', () => {
    expect(resolveTier('cinematic', null)).toBe('high');
    expect(resolveTier('cinematic', 'low')).toBe('high'); // never silently Essential
    expect(resolveTier('cinematic', 'ultra')).toBe('ultra');
    expect(resolveTier('essential', null)).toBe('balanced');
    expect(resolveTier('essential', 'ultra')).toBe('balanced'); // never silently Cinematic
    expect(resolveTier('essential', 'low')).toBe('low');
  });

  it('every tier maps to exactly one experience and the budgets match the doctrine', () => {
    expect(experienceOf('ultra')).toBe('cinematic');
    expect(experienceOf('high')).toBe('cinematic');
    expect(experienceOf('balanced')).toBe('essential');
    expect(experienceOf('low')).toBe('essential');
    // Cinematic renders native pixels with MSAA; Essential renders CSS pixels without
    expect(TIER_BUDGET.high.nativeResolution).toBe(true);
    expect(TIER_BUDGET.high.msaaSamples).toBe(4);
    expect(TIER_BUDGET.balanced.nativeResolution).toBe(false);
    expect(TIER_BUDGET.balanced.msaaSamples).toBe(1);
    expect(TIER_BUDGET.low.targetFrameRate).toBe(30);
  });

  it('steps down the ladder and stops at low', () => {
    expect(stepDown('ultra')).toBe('high');
    expect(stepDown('high')).toBe('balanced');
    expect(stepDown('balanced')).toBe('low');
    expect(stepDown('low')).toBe('low');
  });
});

describe('resolution scale', () => {
  it('native tiers always render every device pixel', () => {
    expect(resolutionScaleFor('high', 3840, 2160)).toBe(1);
    expect(resolutionScaleFor('ultra', 1280, 800)).toBe(1);
  });

  it('CSS tiers scale down only past their megapixel cap, never below the floor', () => {
    expect(resolutionScaleFor('balanced', 1280, 800)).toBe(1); // 1.02 MP under the 2.1 cap
    expect(resolutionScaleFor('balanced', 3840, 2160)).toBeCloseTo(0.5, 2); // 8.3 MP → 2.1
    expect(resolutionScaleFor('low', 1280, 800)).toBe(1);
    expect(resolutionScaleFor('low', 3840, 2160)).toBeCloseTo(0.38, 2);
    expect(resolutionScaleFor('low', 8000, 8000)).toBe(0.35);
  });
});

describe('probe classification (perf research §6)', () => {
  const sample = (gpu: number | null, delta: number, frames = 45) => ({ gpuMsP50: gpu, cpuMsP50: 4, frameDeltaP95Ms: delta, frames });

  it('is inconclusive on too few frames', () => {
    expect(classifyProbe(sample(3, 10, 5))).toBeNull();
  });

  it('classifies by GPU time when the timer exists, capped by frame arrival', () => {
    expect(classifyProbe(sample(4, 16))).toBe('ultra');
    expect(classifyProbe(sample(4, 25))).toBe('balanced'); // fast GPU, late frames → not Cinematic
    expect(classifyProbe(sample(8, 16))).toBe('high');
    expect(classifyProbe(sample(12, 16))).toBe('balanced');
    expect(classifyProbe(sample(20, 16))).toBe('low');
    expect(classifyProbe(sample(8, 40))).toBe('low');
  });

  it('falls back to frame deltas without a timer and never claims ULTRA that way', () => {
    expect(classifyProbe(sample(null, 16))).toBe('high');
    expect(classifyProbe(sample(null, 30))).toBe('balanced');
    expect(classifyProbe(sample(null, 60))).toBe('low');
  });

  it('percentile is nearest-rank on a copy', () => {
    const values = [5, 1, 9, 3, 7];
    expect(percentile(values, 0.5)).toBe(5);
    expect(percentile(values, 0.95)).toBe(9);
    expect(percentile([], 0.5)).toBe(0);
    expect(values[0]).toBe(5); // untouched
  });
});

describe('gesture-window downgrade', () => {
  it('needs consecutive misses, resets on a good window, then steps one tier', () => {
    let streak = 0;
    let out = downgradeAfterWindow({ p95Ms: 40, frames: 30 }, streak, 'auto', 'high', 'high');
    expect(out.detected).toBeNull();
    streak = out.missStreak;
    out = downgradeAfterWindow({ p95Ms: 12, frames: 30 }, streak, 'auto', 'high', 'high');
    expect(out.missStreak).toBe(0); // a good window resets the streak
    streak = 0;
    for (let i = 0; i < DOWNGRADE_MISSES - 1; i += 1) {
      out = downgradeAfterWindow({ p95Ms: 40, frames: 30 }, streak, 'auto', 'high', 'high');
      expect(out.detected).toBeNull();
      streak = out.missStreak;
    }
    out = downgradeAfterWindow({ p95Ms: 40, frames: 30 }, streak, 'auto', 'high', 'high');
    expect(out.detected).toBe('balanced');
  });

  it('never crosses the user\'s explicit choice', () => {
    // cinematic on HIGH: stepping the detection to balanced would not change the effective tier
    const out = downgradeAfterWindow({ p95Ms: 40, frames: 30 }, DOWNGRADE_MISSES - 1, 'cinematic', 'high', 'high');
    expect(out.detected).toBeNull();
    expect(out.missStreak).toBe(0);
    // cinematic on ULTRA can still settle to HIGH inside Cinematic
    const inside = downgradeAfterWindow({ p95Ms: 40, frames: 30 }, DOWNGRADE_MISSES - 1, 'cinematic', 'ultra', 'ultra');
    expect(inside.detected).toBe('high');
  });

  it('low has no floor — nothing below it to step to', () => {
    const out = downgradeAfterWindow({ p95Ms: 400, frames: 30 }, DOWNGRADE_MISSES - 1, 'auto', 'low', 'low');
    expect(out.detected).toBeNull();
  });
});

describe('persisted choice parsing', () => {
  it('accepts only the two experiences; anything else is auto', () => {
    expect(parseExperienceChoice('essential')).toBe('essential');
    expect(parseExperienceChoice('cinematic')).toBe('cinematic');
    expect(parseExperienceChoice('ultra')).toBe('auto');
    expect(parseExperienceChoice(null)).toBe('auto');
  });
});
