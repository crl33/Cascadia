import { describe, expect, it } from 'vitest';
import type { CameraPose } from '../state/store';
import { parseCam, parseDeepLink, serializeCam, serializeDeepLink, type DeepLink } from './deep-link';

const EMPTY: DeepLink = { basinId: null, forecastPointId: null, motion: null, band: null, asOf: null, eventId: null, at: null, cam: null, pinnedCameraId: null };

describe('deep link', () => {
  it('round-trips selection, basin context, motion and band', () => {
    const link: DeepLink = { ...EMPTY, basinId: 'basin:skagit', forecastPointId: 'fp:nwps:MVEW1', motion: 'reduced', band: 'river' };
    const qs = serializeDeepLink(link);
    expect(qs).toContain('sel=fp%3Anwps%3AMVEW1');
    expect(qs).toContain('basin=basin%3Askagit');
    expect(parseDeepLink(qs)).toEqual(link);
  });

  it('round-trips as_of and an entity-anchored camera', () => {
    const link: DeepLink = {
      ...EMPTY,
      basinId: 'basin:skagit',
      forecastPointId: 'fp:nwps:MVEW1',
      asOf: '2025-12-12T08:15:00Z',
      cam: { anchor: { kind: 'entity', id: 'fp:nwps:MVEW1' }, rangeM: 18000, headingDeg: 205, pitchDeg: -32, mode: 'free' },
    };
    expect(parseDeepLink(serializeDeepLink(link))).toEqual(link);
  });

  it('serializes nothing for the empty state and omits the system motion default', () => {
    expect(serializeDeepLink(EMPTY)).toBe('');
    expect(serializeDeepLink({ ...EMPTY, motion: 'system' })).toBe('');
    expect(parseDeepLink('')).toEqual(EMPTY);
  });

  it('drops invalid values instead of guessing', () => {
    expect(parseDeepLink('?basin=Skagit&fp=mvew1&motion=fast&band=space&as_of=yesterday&cam=nonsense')).toEqual({
      ...EMPTY, forecastPointId: 'fp:nwps:MVEW1',
    });
    expect(parseDeepLink('?as_of=2026-13-99T99:99:00Z').asOf).toBeNull();
  });

  it('parses legacy basin/fp keys and full-id sel values', () => {
    expect(parseDeepLink('?basin=basin%3Askagit&fp=MVEW1')).toEqual({ ...EMPTY, basinId: 'basin:skagit', forecastPointId: 'fp:nwps:MVEW1' });
    expect(parseDeepLink('?fp=fp:nwps:MVEW1').forecastPointId).toBe('fp:nwps:MVEW1');
    expect(parseDeepLink('?sel=basin:skagit').basinId).toBe('basin:skagit');
    expect(parseDeepLink('?sel=fp:nwps:mvew1').forecastPointId).toBe('fp:nwps:MVEW1');
  });

  it('normalizes as_of to a UTC instant', () => {
    expect(parseDeepLink('?as_of=2025-12-12T08:15Z').asOf).toBe('2025-12-12T08:15:00Z');
    expect(parseDeepLink('?as_of=2025-12-12T08:15:30.500Z').asOf).toBe('2025-12-12T08:15:30.500Z');
  });
});

describe('event deep links (P2 Event Zero)', () => {
  it('round-trips event and at, composing with sel/basin', () => {
    const link: DeepLink = {
      ...EMPTY, basinId: 'basin:skagit', forecastPointId: 'fp:nwps:MVEW1',
      eventId: 'event-zero-2025-12', at: '2025-12-12T09:00:00Z',
    };
    const qs = serializeDeepLink(link);
    expect(qs).toContain('event=event-zero-2025-12');
    expect(qs).toContain('at=2025-12-12T09%3A00%3A00Z');
    expect(qs).not.toContain('as_of=');
    expect(parseDeepLink(qs)).toEqual(link);
  });

  it('event and as_of are mutually exclusive: event wins, as_of dropped (ADR-0010 honesty)', () => {
    const parsed = parseDeepLink('?event=event-zero-2025-12&as_of=2026-08-22T06:00:00Z&at=2025-12-10T00:00:00Z');
    expect(parsed.eventId).toBe('event-zero-2025-12');
    expect(parsed.asOf).toBeNull();
    expect(parsed.at).toBe('2025-12-10T00:00:00Z');
    const qs = serializeDeepLink({ ...EMPTY, eventId: 'event-zero-2025-12', at: '2025-12-10T00:00:00Z', asOf: '2026-08-22T06:00:00Z' });
    expect(qs).toContain('event=');
    expect(qs).not.toContain('as_of');
  });

  it('rejects unknown event ids and drops at without an event', () => {
    expect(parseDeepLink('?event=event-unknown').eventId).toBeNull();
    expect(parseDeepLink('?event=event-unknown&at=2025-12-10T00:00:00Z').at).toBeNull();
    expect(parseDeepLink('?at=2025-12-10T00:00:00Z')).toEqual(EMPTY);
    expect(parseDeepLink('?event=event-zero-2025-12&at=nonsense').at).toBeNull();
  });
});

describe('cam grammar v1 (docs/CAMERA_SYSTEM.md §7)', () => {
  it('parses the documented example', () => {
    expect(parseCam('1~e:fp:nwps:MVEW1~18000~205~-32')).toEqual({
      anchor: { kind: 'entity', id: 'fp:nwps:MVEW1' }, rangeM: 18000, headingDeg: 205, pitchDeg: -32, mode: 'free',
    });
    expect(parseCam('1~e:basin:skagit~95000~180~-40~orbit')?.mode).toBe('orbit');
  });

  it('round-trips within 1% of range and 1 degree', () => {
    const poses: CameraPose[] = [
      { anchor: { kind: 'entity', id: 'basin:skagit' }, rangeM: 95234, headingDeg: 212.6, pitchDeg: -41.4, mode: 'orbit' },
      { anchor: { kind: 'geo', lat: 48.4453, lon: -122.3342 }, rangeM: 1_512_345, headingDeg: 359.7, pitchDeg: -54.9, mode: 'free' },
      { anchor: { kind: 'geo', lat: -0.00004, lon: 0.00004 }, rangeM: 8_042, headingDeg: -0.2, pitchDeg: -89.6, mode: 'follow' },
    ];
    for (const pose of poses) {
      const round = parseCam(serializeCam(pose));
      expect(round).not.toBeNull();
      expect(Math.abs(round!.rangeM - pose.rangeM) / pose.rangeM).toBeLessThan(0.01);
      expect(Math.abs(round!.headingDeg - pose.headingDeg)).toBeLessThanOrEqual(1);
      expect(Math.abs(round!.pitchDeg - pose.pitchDeg)).toBeLessThanOrEqual(1);
      expect(round!.mode).toBe(pose.mode);
      if (pose.anchor.kind === 'geo' && round!.anchor.kind === 'geo') {
        expect(Math.abs(round!.anchor.lat - pose.anchor.lat)).toBeLessThanOrEqual(1e-4);
        expect(Math.abs(round!.anchor.lon - pose.anchor.lon)).toBeLessThanOrEqual(1e-4);
      } else {
        expect(round!.anchor).toEqual(pose.anchor);
      }
    }
  });

  it('keeps 3 significant figures on range and integer degrees', () => {
    expect(serializeCam({ anchor: { kind: 'entity', id: 'basin:skagit' }, rangeM: 95234, headingDeg: 212.6, pitchDeg: -41.4, mode: 'free' }))
      .toBe('1~e:basin:skagit~95200~213~-41');
  });

  it('falls back to sel on unknown versions and rejects malformed parts', () => {
    expect(parseCam('2~e:basin:skagit~1000~0~-45')).toBeNull();
    expect(parseCam('1~e:basin:skagit~1000~0')).toBeNull();                 // missing pitch
    expect(parseCam('1~x:whatever~1000~0~-45')).toBeNull();                 // bad anchor kind
    expect(parseCam('1~g:99,-200~1000~0~-45')).toBeNull();                  // out-of-range lon
    expect(parseCam('1~e:basin:skagit~-5~0~-45')).toBeNull();               // negative range
    expect(parseCam('1~e:basin:skagit~1000~0.5~-45')).toBeNull();           // non-integer degrees
    expect(parseCam('1~e:basin:skagit~1000~0~-45~fly')).toBeNull();         // fly is never encoded
    const link = parseDeepLink('?sel=basin%3Askagit&cam=2~e%3Abasin%3Askagit~1000~0~-45');
    expect(link.cam).toBeNull();
    expect(link.basinId).toBe('basin:skagit');                              // sel still frames
  });
});


describe('pin param', () => {
  it('round-trips a pinned flood-observation camera and rejects junk', () => {
    const link = parseDeepLink('?pin=cam:usgs:WA_Skagit_River_near_Mount_Vernon');
    expect(link.pinnedCameraId).toBe('cam:usgs:WA_Skagit_River_near_Mount_Vernon');
    expect(serializeDeepLink({ ...EMPTY, pinnedCameraId: link.pinnedCameraId })).toBe('?pin=cam%3Ausgs%3AWA_Skagit_River_near_Mount_Vernon');
    expect(parseDeepLink('?pin=javascript:alert(1)').pinnedCameraId).toBeNull();
    expect(parseDeepLink('?pin=cam:usgs:').pinnedCameraId).toBeNull();
  });
});
