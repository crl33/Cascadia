import { describe, expect, it } from 'vitest';
import type { CameraRecord } from '../contracts/schemas';
import { frameSrc, MAX_AUTO_PREVIEWS, previewCameraIds } from './camera-preview-math';

const cam = (over: Partial<CameraRecord> & { id: string }): CameraRecord => ({
  provider: 'usgs-nims', name: over.id, lon: -122.3, lat: 48.4, feed: 'still',
  image: { kind: 'usgs-s3', cam_id: 'X' }, refresh_seconds: 900,
  basin_id: 'basin:skagit', nwis_id: null, tier: 'A', reasons: [], orientation: null,
  attribution: 'USGS', ...over,
});

describe('previewCameraIds', () => {
  const cams = [
    cam({ id: 'cam:usgs:a', tier: 'A' }),
    cam({ id: 'cam:usgs:b', tier: 'A' }),
    cam({ id: 'cam:usgs:c', tier: 'A' }),
    cam({ id: 'cam:usgs:d', tier: 'B' }),
    cam({ id: 'cam:other', tier: 'A', basin_id: 'basin:cedar' }),
  ];
  it('opens nothing above the basin band, pinned or not', () => {
    expect(previewCameraIds(cams, 'state', 'basin:skagit', 'cam:usgs:a')).toEqual([]);
    expect(previewCameraIds(cams, 'orbital', 'basin:skagit', null)).toEqual([]);
  });
  it('auto-previews only at local band, tier A, selected basin, capped — never a wall of feeds', () => {
    const ids = previewCameraIds(cams, 'local', 'basin:skagit', null);
    expect(ids).toEqual(['cam:usgs:a', 'cam:usgs:b']);
    expect(ids.length).toBeLessThanOrEqual(MAX_AUTO_PREVIEWS);
    expect(previewCameraIds(cams, 'river', 'basin:skagit', null)).toEqual([]);
    expect(previewCameraIds(cams, 'local', null, null)).toEqual([]);
  });
  it('the pinned camera rides along at any camera-showing band and is never doubled', () => {
    expect(previewCameraIds(cams, 'basin', null, 'cam:usgs:c')).toEqual(['cam:usgs:c']);
    const ids = previewCameraIds(cams, 'local', 'basin:skagit', 'cam:usgs:a');
    expect(ids[0]).toBe('cam:usgs:a');
    expect(new Set(ids).size).toBe(ids.length);
  });
});

describe('frameSrc', () => {
  it('quantizes to the camera\'s own cadence so the upstream is never polled faster than it updates', () => {
    const wsdot = cam({ id: 'cam:wsdot:1', image: { kind: 'static-url', url: 'https://images.wsdot.wa.gov/nw/x.jpg' }, refresh_seconds: 300 });
    const t0 = 300_000 * 3_333_334; // aligned to a bucket boundary
    expect(frameSrc(wsdot, t0)).toBe(frameSrc(wsdot, t0 + 299_000)); // same bucket
    expect(frameSrc(wsdot, t0)).not.toBe(frameSrc(wsdot, t0 + 301_000));
  });
  it('USGS frames route through the same-origin gateway redirect', () => {
    const usgs = cam({ id: 'cam:usgs:mv', image: { kind: 'usgs-s3', cam_id: 'WA_Skagit_River_near_Mount_Vernon' } });
    expect(frameSrc(usgs, 0)).toBe('/cameras/usgs/WA_Skagit_River_near_Mount_Vernon/latest.jpg?t=0');
  });
});
