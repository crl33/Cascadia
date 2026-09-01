/**
 * The Cascadia operating envelope (mission §2–3): this application is a Pacific-Northwest
 * hydrologic instrument, not a globe viewer. Geography is framed intentionally:
 *
 * - HARD DOMAIN — the rendered world. Outside it the globe is not drawn and no imagery is
 *   ever requested (Globe.cartographicLimitRectangle + ImageryLayer rectangle). Covers all
 *   of Washington plus the British Columbia / Oregon / offshore context that PNW weather
 *   needs, so eastern-WA basins are addressable later without touching the renderer.
 * - SOFT ENVELOPE — where the CAMERA TARGET may rest. Seed-basin union (verified from
 *   tests/fixtures/geo/basins_seed_state_lod.geojson: [-122.71, 46.78] → [-120.65, 49.31])
 *   plus coastal/Columbia margin. Drifting past it is allowed mid-gesture; on idle the
 *   camera springs back cinematically (CameraEnvelope), so the constraint is a frame, not
 *   a wall.
 * - Zoom band 600 m … 1,800 km: the local floor from the brief, and a ceiling just above
 *   the 1,500 km home view so the orbital band survives while the planet does not.
 * - Tilt caps per band: near-nadir analytical camera at orbital→river (the tilt gesture
 *   barely moves), controlled oblique only at local.
 *
 * Pure data + pure clamps here; Cesium wiring lives in SceneController/CameraEnvelope.
 */
import type { Band } from '../scene/bands';

export interface DegreesRectangle {
  west: number;
  south: number;
  east: number;
  north: number;
}

/** Rendered-world limit: WA + context. Matches the imagery-layer rectangle. */
export const HARD_DOMAIN: DegreesRectangle = { west: -128, south: 44, east: -116.5, north: 51.5 };

/** Where the camera target may rest: seed-basin union + ~2° coastal/Columbia margin. */
export const SOFT_ENVELOPE: DegreesRectangle = { west: -124.8, south: 45.8, east: -119.8, north: 49.6 };

export const ZOOM_FLOOR_M = 600;
/** Max-out IS the composed home framing (mission §23): the ceiling sits just above the
 * 1,150 km opening view, so the outermost scene is a product screenshot, never a floating
 * sheet in a void. */
export const ZOOM_CEILING_M = 1_250_000;

/** Max user-gesture tilt, DEGREES from nadir (0 = straight down). Cesium's
 * ScreenSpaceCameraController.maximumTiltAngle takes radians from nadir at the pivot. */
export const TILT_CAP_DEG_BY_BAND: Record<Band, number> = {
  orbital: 15,
  state: 15,
  basin: 20,
  river: 25,
  local: 50,
};

/** Heading further from north than this springs back on idle (degrees). */
export const HEADING_TOLERANCE_DEG = 2;

export interface CameraPoseSample {
  lonDeg: number;
  latDeg: number;
  heightM: number;
  headingDeg: number;
  /** Negative looking down; -90 = nadir. */
  pitchDeg: number;
  band: Band;
}

export interface EnvelopeCorrection {
  lonDeg: number;
  latDeg: number;
  heightM: number;
  headingDeg: number;
  pitchDeg: number;
}

const clamp = (v: number, lo: number, hi: number): number => Math.min(Math.max(v, lo), hi);

/** Normalize a heading into (-180, 180] so "353°" springs to 0 the short way. */
const signedHeading = (deg: number): number => {
  const wrapped = ((deg % 360) + 360) % 360;
  return wrapped > 180 ? wrapped - 360 : wrapped;
};

/**
 * The pure spring-back decision: null when the pose already rests inside the envelope,
 * else the corrected pose. Pitch is clamped against the band's tilt cap (measured from
 * nadir: cap 15° ⇒ pitch must be ≤ -75°).
 */
export function clampToEnvelope(pose: CameraPoseSample): EnvelopeCorrection | null {
  const lonDeg = clamp(pose.lonDeg, SOFT_ENVELOPE.west, SOFT_ENVELOPE.east);
  const latDeg = clamp(pose.latDeg, SOFT_ENVELOPE.south, SOFT_ENVELOPE.north);
  const heightM = clamp(pose.heightM, ZOOM_FLOOR_M, ZOOM_CEILING_M);
  const nadirCapDeg = TILT_CAP_DEG_BY_BAND[pose.band];
  const pitchFloorDeg = -90 + nadirCapDeg; // e.g. cap 15° ⇒ pitch in [-90, -75]
  const pitchDeg = clamp(pose.pitchDeg, -90, pitchFloorDeg);
  const heading = signedHeading(pose.headingDeg);
  const headingDeg = Math.abs(heading) > HEADING_TOLERANCE_DEG ? 0 : pose.headingDeg;

  const unchanged =
    lonDeg === pose.lonDeg &&
    latDeg === pose.latDeg &&
    heightM === pose.heightM &&
    pitchDeg === pose.pitchDeg &&
    headingDeg === pose.headingDeg;
  if (unchanged) return null;
  return { lonDeg, latDeg, heightM, headingDeg, pitchDeg };
}
