/**
 * Deep-link grammar (docs/CAMERA_SYSTEM.md §7, spike subset — the scope lives in the query
 * until path routing lands): `?sel=<EntityId>&basin=<id>&as_of=<iso>&event=<id>&at=<iso>
 * &cam=<v1>&motion=…&band=…`. `sel` is the primary selection (full namespaced EntityId);
 * `basin` carries the basin context when the primary is a forecast point (and is the legacy
 * primary key); `cam` is the compact camera target
 * `1~<anchor>~<rangeM>~<headingDeg>~<pitchDeg>[~<mode>]`; `pin=<cam:provider:id>` pins a
 * flood-observation camera's preview open (a shareable ground-truth view). `event` (validated against
 * event/registry) enters event replay with EVENT-time cursor `at`; event and as_of are
 * mutually exclusive — event wins and as_of is dropped, because backfilled archive rows carry
 * available_at = retrieval time (ADR-0010) and a knowledge-time replay inside the event would
 * honestly render UNKNOWN. Pure parse/serialize; stable ids only (never labels); unknown keys
 * ignored; invalid values dropped rather than guessed; an unknown cam version falls back to
 * sel. Load is always a cut.
 */
import { isEventId } from '../event/registry';
import type { CameraPose } from '../state/store';
import type { MotionSetting } from '../design-system/motion';
import { BANDS, type Band } from '../scene/bands';

export interface DeepLink {
  basinId: string | null;
  forecastPointId: string | null;   // full id, e.g. fp:nwps:MVEW1
  motion: MotionSetting | null;
  band: Band | null;
  /** ISO 8601 UTC knowledge time for replay; null means live now (and always null with an event). */
  asOf: string | null;
  /** Event replay id (event/registry); null outside event mode. */
  eventId: string | null;
  /** EVENT-time cursor for event replay; only meaningful beside eventId. */
  at: string | null;
  cam: CameraPose | null;
  /** Pinned flood-observation camera (cam:* id); its preview card opens on load. */
  pinnedCameraId: string | null;
}

const BASIN_ID = /^basin:[a-z0-9-]+$/;
const FP_PREFIX = /^fp:nwps:/i;
const LID = /^[A-Z0-9]{3,8}$/;
const ENTITY_ID = /^[a-z][a-z0-9-]*:[A-Za-z0-9:._-]+$/;
const WEBCAM_ID = /^cam:[a-z-]+:[A-Za-z0-9_.-]{1,120}$/;
const AS_OF = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d{1,3})?)?Z$/;
const MOTIONS: readonly MotionSetting[] = ['system', 'reduced', 'full'];

export const lidOf = (forecastPointId: string): string => forecastPointId.replace(FP_PREFIX, '');
export const forecastPointIdOf = (lid: string): string => `fp:nwps:${lid.toUpperCase()}`;

const parseAsOf = (raw: string | null): string | null => {
  if (!raw || !AS_OF.test(raw)) return null;
  const ms = Date.parse(raw);
  if (Number.isNaN(ms)) return null;
  return new Date(ms).toISOString().replace('.000Z', 'Z');
};

/** `cam` grammar v1. Unknown versions and malformed parts return null (fall back to sel). */
export function parseCam(raw: string): CameraPose | null {
  const parts = raw.split('~');
  if (parts[0] !== '1' || parts.length < 5 || parts.length > 6) return null;
  const [, anchorRaw, rangeRaw, headingRaw, pitchRaw, modeRaw] = parts;

  let anchor: CameraPose['anchor'] | null = null;
  if (anchorRaw.startsWith('e:')) {
    const id = anchorRaw.slice(2);
    if (ENTITY_ID.test(id)) anchor = { kind: 'entity', id };
  } else if (anchorRaw.startsWith('g:')) {
    const match = anchorRaw.slice(2).match(/^(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)$/);
    if (match) {
      const lat = Number(match[1]);
      const lon = Number(match[2]);
      if (Math.abs(lat) <= 90 && Math.abs(lon) <= 180) anchor = { kind: 'geo', lat, lon };
    }
  }

  const rangeM = /^\d+(\.\d+)?$/.test(rangeRaw) ? Number(rangeRaw) : NaN;
  const headingDeg = /^-?\d+$/.test(headingRaw) ? Number(headingRaw) : NaN;
  const pitchDeg = /^-?\d+$/.test(pitchRaw) ? Number(pitchRaw) : NaN;
  const mode: CameraPose['mode'] | null =
    modeRaw === undefined ? 'free' : modeRaw === 'orbit' || modeRaw === 'follow' ? modeRaw : null;
  if (anchor === null || !Number.isFinite(rangeM) || rangeM <= 0 || !Number.isFinite(headingDeg) || !Number.isFinite(pitchDeg) || mode === null) return null;
  return { anchor, rangeM, headingDeg, pitchDeg, mode };
}

/** 3 significant figures without scientific notation (rangeM per the grammar). */
const sig3 = (n: number): string => String(Number(n.toPrecision(3)));

export function serializeCam(pose: CameraPose): string {
  const anchor = pose.anchor.kind === 'entity'
    ? `e:${pose.anchor.id}`
    : `g:${pose.anchor.lat.toFixed(4)},${pose.anchor.lon.toFixed(4)}`;
  const mode = pose.mode === 'free' ? '' : `~${pose.mode}`;
  return `1~${anchor}~${sig3(pose.rangeM)}~${Math.round(pose.headingDeg)}~${Math.round(pose.pitchDeg)}${mode}`;
}

export function parseDeepLink(search: string): DeepLink {
  const params = new URLSearchParams(search.startsWith('?') ? search.slice(1) : search);
  const sel = params.get('sel');
  const legacyBasin = params.get('basin');
  const legacyFp = params.get('fp');
  const motion = params.get('motion');
  const band = params.get('band');
  const camRaw = params.get('cam');
  const eventRaw = params.get('event');
  const eventId = eventRaw !== null && isEventId(eventRaw) ? eventRaw : null;

  let basinId: string | null = null;
  let forecastPointId: string | null = null;
  if (sel && BASIN_ID.test(sel)) {
    basinId = sel;
  } else if (sel && FP_PREFIX.test(sel)) {
    const lid = lidOf(sel).toUpperCase();
    if (LID.test(lid)) forecastPointId = forecastPointIdOf(lid);
  }
  // `basin=` is the basin context beside an fp selection — and the legacy primary key.
  if (basinId === null && legacyBasin && BASIN_ID.test(legacyBasin)) basinId = legacyBasin;
  if (forecastPointId === null && legacyFp) {
    const lid = lidOf(legacyFp).toUpperCase();
    if (LID.test(lid)) forecastPointId = forecastPointIdOf(lid);
  }

  return {
    basinId,
    forecastPointId,
    motion: motion && (MOTIONS as readonly string[]).includes(motion) ? (motion as MotionSetting) : null,
    band: band && (BANDS as readonly string[]).includes(band) ? (band as Band) : null,
    // event wins over as_of: a knowledge-time replay inside a backfilled event is honestly UNKNOWN.
    asOf: eventId !== null ? null : parseAsOf(params.get('as_of')),
    eventId,
    at: eventId !== null ? parseAsOf(params.get('at')) : null,
    cam: camRaw ? parseCam(camRaw) : null,
    pinnedCameraId: (() => {
      const pin = params.get('pin');
      return pin && WEBCAM_ID.test(pin) ? pin : null;
    })(),
  };
}

export function serializeDeepLink(link: DeepLink): string {
  const params = new URLSearchParams();
  const sel = link.forecastPointId ?? link.basinId;
  if (sel) params.set('sel', sel);
  if (link.forecastPointId && link.basinId) params.set('basin', link.basinId);
  if (link.eventId) {
    params.set('event', link.eventId);
    if (link.at) params.set('at', link.at);
  } else if (link.asOf) {
    params.set('as_of', link.asOf);
  }
  if (link.cam) params.set('cam', serializeCam(link.cam));
  if (link.pinnedCameraId) params.set('pin', link.pinnedCameraId);
  if (link.motion && link.motion !== 'system') params.set('motion', link.motion);
  if (link.band) params.set('band', link.band);
  const qs = params.toString();
  return qs ? `?${qs}` : '';
}
