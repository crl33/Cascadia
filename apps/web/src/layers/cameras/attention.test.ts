import { describe, expect, it } from 'vitest';
import type { BasinEnvelope } from '../../contracts/schemas';
import { cameraAttentionByBasin } from './attention';

const basin = (id: string, category: string, alerts: unknown[] = []) => ({
  id, name: id, surfaces: { hazard: { official_category: category } }, official_alerts: alerts,
});

describe('cameraAttentionByBasin', () => {
  it('an official alert names the basin and wins over the forecast category', () => {
    const env = { items: [basin('basin:skagit', 'minor', [{ event: 'Flood Warning' }])] } as unknown as BasinEnvelope;
    expect(cameraAttentionByBasin(env)['basin:skagit']).toEqual({
      kind: 'official_alert', detail: 'official Flood Warning names this basin',
    });
  });
  it('an official 72 h category at action or above is forecast concern', () => {
    const env = { items: [basin('basin:cedar', 'action')] } as unknown as BasinEnvelope;
    expect(cameraAttentionByBasin(env)['basin:cedar']?.kind).toBe('official_forecast_concern');
  });
  it('quiet, unknown and derived-only states light nothing', () => {
    const env = { items: [basin('basin:cedar', 'none'), basin('basin:skagit', 'unknown')] } as unknown as BasinEnvelope;
    expect(cameraAttentionByBasin(env)).toEqual({});
    expect(cameraAttentionByBasin(undefined)).toEqual({});
  });
});
