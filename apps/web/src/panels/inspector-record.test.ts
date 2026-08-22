import { describe, expect, it } from 'vitest';
import { toInspectorRecord } from './inspector-record';

describe('toInspectorRecord', () => {
  it('prints every inspector line for an observation', () => {
    const lines = toInspectorRecord({
      source_id: 'src:usgs-nwis-iv', source_kind: 'OBSERVED', product_id: 'product:usgs-iv-00065-00060',
      valid_time: '2026-08-22T08:15:00Z', retrieved_at: '2026-08-22T08:26:43Z',
      freshness: { state: 'current', age_seconds: 2700, expected_cadence_seconds: 900 }, quality: ['provisional'],
      label: 'USGS instantaneous values (provisional)',
    }, 'observation');
    const byKey = Object.fromEntries(lines.map((l) => [l.key, l.value]));
    expect(Object.keys(byKey)).toEqual(['SOURCE', 'TYPE', 'TRUTH', 'VALID', 'ISSUED', 'RETRIEVED', 'FRESHNESS', 'QUALITY', 'METHOD']);
    expect(byKey.ISSUED).toBe('n/a (observation)');
    expect(byKey.FRESHNESS).toBe('current — age 45 min · cadence 15 min');
    expect(byKey.QUALITY).toBe('provisional');
    expect(byKey.METHOD).toBe('none (untransformed)');
  });
});
