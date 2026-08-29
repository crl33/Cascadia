/**
 * Dynamic flood-camera attention — driven by OFFICIAL evidence only (mission §14, VTD).
 *
 * A camera is emphasized when its basin carries (in priority order):
 *  1. an active OFFICIAL alert (CAP product naming the basin), or
 *  2. an OFFICIAL forecast 72 h hazard category at or above action.
 * Nothing else emphasizes a camera: Cascade-derived susceptibility never lights one (a
 * derived surface must not borrow the official register), and there is no numeric score.
 * The reason is carried verbatim so the card can say exactly WHY it is highlighted.
 * Pure and total; tested in attention.test.ts.
 */
import type { BasinEnvelope } from '../../contracts/schemas';

export interface CameraAttention {
  kind: 'official_alert' | 'official_forecast_concern';
  detail: string;
}

const CONCERN = new Set(['action', 'minor', 'moderate', 'major']);

export function cameraAttentionByBasin(envelope: BasinEnvelope | undefined): Record<string, CameraAttention> {
  const out: Record<string, CameraAttention> = {};
  if (!envelope) return out;
  for (const basin of envelope.items) {
    if (!('surfaces' in basin)) continue;
    const alerts = basin.official_alerts ?? [];
    if (alerts.length > 0) {
      const first = alerts[0];
      out[basin.id] = {
        kind: 'official_alert',
        detail: `official ${first.event ?? 'alert'} names this basin`,
      };
      continue;
    }
    const category = basin.surfaces.hazard.official_category;
    if (CONCERN.has(category)) {
      out[basin.id] = {
        kind: 'official_forecast_concern',
        detail: `official 72 h forecast reaches ${category.toUpperCase()}`,
      };
    }
  }
  return out;
}
