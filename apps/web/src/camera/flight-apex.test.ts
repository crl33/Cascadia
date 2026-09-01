import { describe, expect, it } from 'vitest';
import { ZOOM_CEILING_M } from './envelope';
import { cappedArcApexM, defaultArcApexM } from './flight-math';

// Cesium's getAltitude (CameraFlightPath.js:22-34) for a perspective frustum, then × 0.2 (:99-102).
const PERSPECTIVE = { fovyRad: Math.PI / 3, aspectRatio: 1.6 };

describe('flight apex — maximumHeight is the apex Cesium flies, so the cap reproduces and clamps it', () => {
  it('reproduces Cesium: 20 % of the height at which the frustum spans the offset, in Cesium\'s argument order', () => {
    const tanTheta = Math.tan(0.5 * PERSPECTIVE.fovyRad);
    // getAltitude(frustum, verticalDistance, horizontalDistance): UP / (aspect · tan), RIGHT / tan
    const up = 200_000, right = 50_000;
    const expected = Math.max(up / (PERSPECTIVE.aspectRatio * tanTheta), right / tanTheta) * 0.2;
    expect(defaultArcApexM(up, right, PERSPECTIVE)).toBeCloseTo(expected, 6);
    // the skeptic's two cases (2026-09-01), against Cesium's own numbers at aspect 1.6 / fovy 60°:
    // right 30 km + up 200 km → 43,301 m; right 200 km + up 30 km → 69,282 m
    expect(defaultArcApexM(200_000, 30_000, PERSPECTIVE)).toBeCloseTo(43_301, 0);
    expect(defaultArcApexM(30_000, 200_000, PERSPECTIVE)).toBeCloseTo(69_282, 0);
  });

  it('non-perspective frustum: Cesium uses max(dx, dy); the 1e9 m ceiling holds', () => {
    expect(defaultArcApexM(3_000, 4_000, null)).toBeCloseTo(800);
    expect(defaultArcApexM(1e12, 0, null)).toBe(1_000_000_000);
  });

  it('a Nooksack→Puyallup-sized hop (~200 km) stays far below the envelope ceiling — never lifted to it', () => {
    const apex = cappedArcApexM(defaultArcApexM(200_000, 30_000, PERSPECTIVE), ZOOM_CEILING_M);
    expect(apex).toBeLessThan(ZOOM_CEILING_M);
    expect(apex).toBe(defaultArcApexM(200_000, 30_000, PERSPECTIVE)); // the default is untouched when it is below the cap
  });

  it('an apex above the composed home frame is clamped to ZOOM_CEILING_M', () => {
    expect(cappedArcApexM(5_000_000, ZOOM_CEILING_M)).toBe(ZOOM_CEILING_M);
    expect(cappedArcApexM(defaultArcApexM(20_000_000, 0, PERSPECTIVE), ZOOM_CEILING_M)).toBe(ZOOM_CEILING_M);
  });
});
