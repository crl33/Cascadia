/**
 * Deep-link grammar for the spike: `?basin=basin:skagit&fp=MVEW1&motion=reduced&band=basin`.
 * Pure parse/serialize; stable ids only (never labels); unknown keys ignored; invalid values
 * dropped rather than guessed. Load is always a cut (docs/CAMERA_SYSTEM.md §7).
 */
import type { MotionSetting } from '../design-system/motion';
import { BANDS, type Band } from '../scene/bands';

export interface DeepLink {
  basinId: string | null;
  forecastPointId: string | null;   // full id, e.g. fp:nwps:MVEW1 (URL carries the bare LID)
  motion: MotionSetting | null;
  band: Band | null;
}

const BASIN_ID = /^basin:[a-z0-9-]+$/;
const LID = /^[A-Z0-9]{3,8}$/;
const MOTIONS: readonly MotionSetting[] = ['system', 'reduced', 'full'];

export const lidOf = (forecastPointId: string): string => forecastPointId.replace(/^fp:nwps:/, '');
export const forecastPointIdOf = (lid: string): string => `fp:nwps:${lid.toUpperCase()}`;

export function parseDeepLink(search: string): DeepLink {
  const params = new URLSearchParams(search.startsWith('?') ? search.slice(1) : search);
  const basin = params.get('basin');
  const fp = params.get('fp');
  const motion = params.get('motion');
  const band = params.get('band');
  const lid = fp ? lidOf(fp).toUpperCase() : null;
  return {
    basinId: basin && BASIN_ID.test(basin) ? basin : null,
    forecastPointId: lid && LID.test(lid) ? forecastPointIdOf(lid) : null,
    motion: motion && (MOTIONS as readonly string[]).includes(motion) ? (motion as MotionSetting) : null,
    band: band && (BANDS as readonly string[]).includes(band) ? (band as Band) : null,
  };
}

export function serializeDeepLink(link: DeepLink): string {
  const params = new URLSearchParams();
  if (link.basinId) params.set('basin', link.basinId);
  if (link.forecastPointId) params.set('fp', lidOf(link.forecastPointId));
  if (link.motion && link.motion !== 'system') params.set('motion', link.motion);
  if (link.band) params.set('band', link.band);
  const qs = params.toString();
  return qs ? `?${qs}` : '';
}
