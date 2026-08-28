import { gzipSync } from 'node:zlib';
import { describe, expect, it } from 'vitest';
import type { FieldRasterState } from '../../contracts/schemas';
import { decodeFieldCells } from './decode';

function stateWith(cells: number[], nx: number, ny: number): FieldRasterState {
  const raw = new Uint8Array(new Uint16Array(cells).buffer); // LE on every platform vitest runs on
  return {
    contract: 'FieldRasterState',
    version: '1.5.0',
    kind: 'observed',
    field: 'qpe_01h',
    window: '1h',
    valid_time: '2026-08-28T03:00:00Z',
    as_of: '2026-08-28T03:30:00Z',
    generated_at: '2026-08-28T03:30:00Z',
    truth: 'observation',
    unit: 'mm',
    spec: { lo1: -122.865, la1: 49.455, dlon: 0.01, dlat: 0.01, nx, ny },
    scale: 0.1,
    sentinel: 65535,
    display_max: 6.4,
    cells_b64: Buffer.from(gzipSync(raw)).toString('base64'),
    prov: 'field-precip_observed',
    provenance_refs: {
      'field-precip_observed': {
        source_id: 'src:mrms',
        source_kind: 'OBSERVED',
        freshness: { state: 'current' },
        label: 'test',
      } as FieldRasterState['provenance_refs'][string],
    },
  };
}

describe('decodeFieldCells', () => {
  it('round-trips raw*scale and turns the sentinel into NaN, never zero', async () => {
    const cells = await decodeFieldCells(stateWith([0, 12, 64, 65535], 2, 2));
    expect(cells[0]).toBe(0);
    expect(cells[1]).toBeCloseTo(1.2, 5);
    expect(cells[2]).toBeCloseTo(6.4, 5);
    expect(Number.isNaN(cells[3])).toBe(true);
  });
  it('refuses a payload whose byte count disagrees with the spec', async () => {
    await expect(decodeFieldCells(stateWith([1, 2, 3], 2, 2))).rejects.toThrow(/spec says 8/);
  });
});
