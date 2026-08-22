import { describe, expect, it } from 'vitest';
import { deriveBand, effectiveHeight, SemanticZoomController } from './SemanticZoomController';
import { BAND_CONFIG } from './bands';

const [stateTop, basinTop, riverTop, localTop] = BAND_CONFIG.boundaries;
const h = BAND_CONFIG.hysteresis;

describe('deriveBand', () => {
  it('maps heights well inside each band regardless of the previous band', () => {
    for (const prev of ['orbital', 'state', 'basin', 'river', 'local'] as const) {
      expect(deriveBand(prev, 1_500_000)).toBe('orbital');
      expect(deriveBand(prev, (stateTop + basinTop) / 2)).toBe('state');
      expect(deriveBand(prev, (basinTop + riverTop) / 2)).toBe('basin');
      expect(deriveBand(prev, (riverTop + localTop) / 2)).toBe('river');
      expect(deriveBand(prev, 2_000)).toBe('local');
    }
  });
  it('applies hysteresis: entering needs 12 % past the boundary, leaving needs 12 % the other way', () => {
    expect(deriveBand('state', basinTop * 0.95)).toBe('state');            // not yet below 0.88 × top
    expect(deriveBand('state', basinTop * 0.87)).toBe('basin');
    expect(deriveBand('basin', basinTop * 1.05)).toBe('basin');            // not yet above 1.12 × top
    expect(deriveBand('basin', basinTop * 1.13)).toBe('state');
    expect(deriveBand('basin', basinTop * (1 - h) + 1)).toBe('basin');
    expect(deriveBand('basin', basinTop * (1 + h) - 1)).toBe('basin');
  });
  it('a camera resting on a boundary never flickers', () => {
    let band = deriveBand('orbital', stateTop);
    for (let i = 0; i < 50; i++) {
      const jitter = stateTop * (1 + (i % 2 === 0 ? 0.05 : -0.05));
      const next = deriveBand(band, jitter);
      expect(next).toBe(band);
      band = next;
    }
  });
});

describe('effectiveHeight', () => {
  it('is the height straight down and widens with shallow pitch, clamped at 0.34', () => {
    expect(effectiveHeight(1000, -90)).toBeCloseTo(1000);
    expect(effectiveHeight(1000, -30)).toBeCloseTo(2000);
    expect(effectiveHeight(1000, -10)).toBeCloseTo(1000 / 0.34);
  });
});

describe('SemanticZoomController', () => {
  it('emits only on change and labels multi-band moves as jumps', () => {
    const zoom = new SemanticZoomController();
    const events: string[] = [];
    zoom.on('bandChanged', (e) => events.push(`${e.prev}>${e.next}:${e.cause}`));
    zoom.onCameraSample({ heightAboveTerrainM: 1_400_000, approximate: true, pitchDeg: -55, settled: true });
    zoom.onCameraSample({ heightAboveTerrainM: 1_300_000, approximate: true, pitchDeg: -55, settled: true });
    expect(events).toEqual([]);
    zoom.onCameraSample({ heightAboveTerrainM: 200_000, approximate: true, pitchDeg: -60, settled: true });
    expect(events).toEqual(['orbital>basin:jump']);
    zoom.onCameraSample({ heightAboveTerrainM: 8_500, approximate: true, pitchDeg: -45, settled: true });
    expect(events).toEqual(['orbital>basin:jump', 'basin>river:descend']);
    expect(zoom.band).toBe('river');
  });
});
