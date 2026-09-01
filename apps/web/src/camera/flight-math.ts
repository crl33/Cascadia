/**
 * Pure camera math: flight duration from distance and height change (MOTION.flight tokens),
 * and the range needed to frame a sphere of a given radius in a frustum. No renderer types.
 */
import { MOTION } from '../design-system/motion';

const clamp = (x: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, x));

/** Distance-based duration: base + perDoubling × log2(1 + weighted km / scale km), clamped to [min, max]. */
export function computeFlightDuration(distanceM: number, heightChangeM: number, tierScale = 1): number {
  const { baseMs, perDoublingMs, scaleKm, heightWeight, minMs, maxMs } = MOTION.flight;
  const weightedKm = Math.max(0, distanceM) / 1000 + (heightWeight * Math.abs(heightChangeM)) / 1000;
  const doublings = Math.log2(1 + weightedKm / scaleKm);
  return Math.round(clamp((baseMs + perDoublingMs * doublings) * tierScale, minMs, maxMs));
}

/** Range so a sphere of `radiusM` fits a frustum whose narrowest half-angle is `halfAngleRad`, with padding. */
export function framingRange(radiusM: number, halfAngleRad: number, paddingFactor = 1.15): number {
  const angle = clamp(halfAngleRad, 0.05, Math.PI / 2 - 0.05);
  return (radiusM / Math.sin(angle)) * paddingFactor;
}

/**
 * Cesium's own default arc apex, reproduced from CameraFlightPath.js (createHeightFunction →
 * getAltitude): the flight peaks at 20 % of the height from which the current frustum would
 * span the start→end offset. Cesium's argument order is the non-obvious part and is kept
 * VERBATIM here: `getAltitude(frustum, verticalDistance, horizontalDistance)` divides the
 * offset's component along the camera's UP axis by (aspectRatio · tan θ) and the component
 * along the RIGHT axis by tan θ — so `upM` is |dot(diff, camera.up)| and `rightM` is
 * |dot(diff, camera.right)|. Cesium falls back to a plain height lerp (no arc) whenever this
 * apex is below max(startHeight, endHeight), so the value only matters on long hops.
 * `perspective` is null for a non-perspective frustum (Cesium: max of the two).
 */
export function defaultArcApexM(upM: number, rightM: number, perspective: { fovyRad: number; aspectRatio: number } | null): number {
  const spanned = perspective
    ? Math.max(upM / (perspective.aspectRatio * Math.tan(0.5 * perspective.fovyRad)), rightM / Math.tan(0.5 * perspective.fovyRad))
    : Math.max(upM, rightM);
  return Math.min(spanned * 0.2, 1_000_000_000);
}

/**
 * The apex to hand `flyTo*` as `maximumHeight`. That option IS the apex Cesium flies through
 * (createHeightFunction takes it verbatim, CameraFlightPath.js:81-83), not an upper bound —
 * passing the ceiling alone would LIFT every short basin→basin hop to 1,250 km. So the cap
 * reproduces the default and clamps it: never higher than the ceiling, never higher than what
 * Cesium would have flown anyway.
 */
export function cappedArcApexM(defaultApexM: number, ceilingM: number): number {
  return Math.min(defaultApexM, ceilingM);
}

/** Approximate great-circle distance between two lon/lat points (metres), enough for durations. */
export function haversineM(lon1: number, lat1: number, lon2: number, lat2: number): number {
  const R = 6_371_000;
  const toRad = (d: number) => (d * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1), dLon = toRad(lon2 - lon1);
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}
