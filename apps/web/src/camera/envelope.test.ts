import { describe, expect, it } from 'vitest';
import { clampToEnvelope, SOFT_ENVELOPE, ZOOM_CEILING_M, ZOOM_FLOOR_M, type CameraPoseSample } from './envelope';

const resting = (over: Partial<CameraPoseSample>): CameraPoseSample => ({
  lonDeg: -122.3,
  latDeg: 47.6,
  heightM: 400_000,
  headingDeg: 0,
  pitchDeg: -90,
  band: 'basin',
  ...over,
});

describe('the Cascadia envelope — a frame, not a wall', () => {
  it('a pose at rest inside the envelope needs no correction', () => {
    expect(clampToEnvelope(resting({}))).toBeNull();
  });

  it('wandering to Europe springs the target back to the Pacific Northwest', () => {
    const c = clampToEnvelope(resting({ lonDeg: 2.35, latDeg: 48.85 })); // Paris
    expect(c).not.toBeNull();
    expect(c?.lonDeg).toBe(SOFT_ENVELOPE.east);
    expect(c?.latDeg).toBeLessThanOrEqual(SOFT_ENVELOPE.north);
  });

  it('the planet is out of reach: height clamps to the operating ceiling and floor', () => {
    expect(clampToEnvelope(resting({ heightM: 20_000_000 }))?.heightM).toBe(ZOOM_CEILING_M);
    expect(clampToEnvelope(resting({ heightM: 50 }))?.heightM).toBe(ZOOM_FLOOR_M);
  });

  it('no angles, anywhere (owner 2026-09-01): every band springs back to pure nadir', () => {
    expect(clampToEnvelope(resting({ pitchDeg: -55, band: 'basin' }))?.pitchDeg).toBe(-90);
    expect(clampToEnvelope(resting({ pitchDeg: -55, band: 'local' }))?.pitchDeg).toBe(-90);
    expect(clampToEnvelope(resting({ pitchDeg: -90, band: 'local' }))).toBeNull();
  });

  it('heading springs to north the short way, with a small tolerance', () => {
    expect(clampToEnvelope(resting({ headingDeg: 1.5 }))).toBeNull();
    expect(clampToEnvelope(resting({ headingDeg: 12 }))?.headingDeg).toBe(0);
    expect(clampToEnvelope(resting({ headingDeg: 353 }))?.headingDeg).toBe(0);
  });
});
