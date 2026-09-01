/**
 * The field legend: one provenance-chipped entry per field the scene draws, and NOTHING for a
 * field the API refused — the legend never advertises what the map is not showing.
 * Static-markup idiom.
 */
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { keys } from '../api/keys';
import { FieldLegend } from './FieldLegend';

const PRECIP = {
  contract: 'FieldRasterState', version: '1.5.0', kind: 'observed', field: 'qpe_01h', window: '1h',
  valid_time: '2026-08-28T20:00:00Z', as_of: '2026-08-28T20:30:00Z', generated_at: '2026-08-28T20:30:00Z',
  truth: 'observation', unit: 'mm',
  spec: { lo1: -122.865, la1: 49.455, dlon: 0.01, dlat: 0.01, nx: 237, ny: 283 },
  scale: 0.1, sentinel: 65535, display_max: 6.4, cells_b64: '',
  prov: 'field-precip_observed',
  provenance_refs: {
    'field-precip_observed': {
      source_id: 'src:mrms', source_kind: 'OBSERVED', product_id: 'product:mrms-qpe-01h-pass2',
      freshness: { state: 'current', age_seconds: 1800 }, quality: [],
      label: 'MRMS multi-sensor QPE pass 2, 1 h accumulation ending 2026-08-28 20:00Z',
    },
  },
};

function render(withPrecip: boolean): string {
  const qc = new QueryClient();
  if (withPrecip) qc.setQueryData(keys.vizField('precip_observed', null), PRECIP);
  return renderToStaticMarkup(
    createElement(QueryClientProvider, { client: qc }, createElement(FieldLegend)),
  );
}

describe('FieldLegend', () => {
  it('a drawn field gets a TOGGLE, a human name, a quiet source line, and the inspector chip', () => {
    const html = render(true);
    expect(html).toContain('field-legend-precip_observed');
    expect(html).toContain('field-toggle-precip_observed'); // clicking Rain shows/hides rain (§22)
    expect(html).toContain('Rain');
    expect(html).toContain('radar ·'); // the source speaks human; the truth class lives in the inspector
    expect(html).toContain('2026-08-28T20:00:00Z'); // exact instant preserved on the title
    expect(html).toContain('MRMS'); // the provenance popover carries the label
    expect(html).not.toContain('Snow'); // the snow field was not drawn, so it is not advertised
  });
  it('renders nothing at all when no field is drawn', () => {
    expect(render(false)).toBe('');
  });
});
