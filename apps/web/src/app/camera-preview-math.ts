/**
 * Pure decisions for the camera preview host: WHICH cameras show a window, and WHERE a frame
 * comes from. No Cesium, no React, no clock reads — callers pass the time bucket.
 */
import type { CameraRecord } from '../contracts/schemas';
import type { Band } from '../scene/bands';

/** Never auto-open a wall of feeds: pinned + at most this many automatic previews. */
export const MAX_AUTO_PREVIEWS = 2;

/**
 * The preview set: the pinned camera always (when the band shows cameras at all), plus — at
 * LOCAL band only — up to MAX_AUTO_PREVIEWS Tier-A cameras in the selected basin. Band
 * thresholds for the finer ~100–200 m auto-expansion experiment are future ground-band work;
 * this v1 is deliberately band-driven and deterministic.
 */
export function previewCameraIds(
  cameras: readonly CameraRecord[],
  band: Band,
  selectedBasinId: string | null,
  pinnedCameraId: string | null,
): string[] {
  const out: string[] = [];
  const bandShowsCameras = band === 'basin' || band === 'river' || band === 'local';
  if (pinnedCameraId && bandShowsCameras && cameras.some((c) => c.id === pinnedCameraId)) {
    out.push(pinnedCameraId);
  }
  if (band === 'local' && selectedBasinId) {
    const auto = cameras
      .filter((c) => c.tier === 'A' && c.basin_id === selectedBasinId && c.id !== pinnedCameraId)
      .sort((a, b) => a.name.localeCompare(b.name))
      .slice(0, MAX_AUTO_PREVIEWS);
    out.push(...auto.map((c) => c.id));
  }
  return out;
}

/**
 * The frame URL for a camera at a refresh bucket. The bucket quantizes time to the camera's
 * own refresh cadence so the SOURCE is never polled faster than it updates (WSDOT low-volume
 * terms; USGS capture interval) — a re-render never mints a new URL inside a bucket.
 */
export function frameSrc(cam: CameraRecord, nowMs: number, gatewayBase = ''): string {
  const bucket = Math.floor(nowMs / (cam.refresh_seconds * 1000));
  if (cam.image.kind === 'static-url') {
    return `${cam.image.url}?t=${bucket}`;
  }
  return `${gatewayBase}/cameras/usgs/${encodeURIComponent(cam.image.cam_id)}/latest.jpg?t=${bucket}`;
}
