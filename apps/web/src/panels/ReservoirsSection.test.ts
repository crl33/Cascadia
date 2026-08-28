/**
 * Reservoir section rendered: verbatim long-form units, the no-datum caveat on forebay
 * elevations, and NOTHING at all for an unregulated basin. Static-markup idiom.
 */
import { renderToStaticMarkup } from 'react-dom/server';
import { createElement } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, expect, it } from 'vitest';
import { keys } from '../api/keys';
import { ReservoirsSection } from './BasinPanel';

function render(basinId: string, doc: unknown): string {
  const qc = new QueryClient();
  qc.setQueryData(keys.basinReservoirs(basinId, null), doc);
  return renderToStaticMarkup(
    createElement(QueryClientProvider, { client: qc }, createElement(ReservoirsSection, { basinId })),
  );
}

const GREEN = {
  basin_id: 'basin:green-duwamish',
  as_of: '2026-08-28T09:00:00Z',
  reservoirs: [{
    station_id: 'station:nwrfc:HHDW1', lid: 'HHDW1', name: 'Howard Hanson Dam (GREEN - HOWARD HANSON DAM)',
    variables: {
      forebay_elevation: { value: 1155.03, unit: 'feet', valid_time: '2026-08-28T08:00:00Z', quality: ['datum_unstated_by_provider'], qualifier: 'RZ' },
      storage: { value: 35.84, unit: 'k-acre-feet', valid_time: '2026-08-28T08:00:00Z', quality: [], qualifier: 'RG' },
      inflow: { value: 160, unit: 'cubic feet per second', valid_time: '2026-08-28T08:00:00Z', quality: [], qualifier: 'RZ' },
    },
    prov: 'nwrfc-reservoir-hhdw1',
  }],
  provenance_refs: {
    'nwrfc-reservoir-hhdw1': {
      source_id: 'src:nwrfc-web', source_kind: 'OBSERVED', product_id: 'product:nwrfc-reservoir-obs',
      freshness: { state: 'current', age_seconds: 3000 }, quality: [],
      label: 'Howard Hanson Dam — NWRFC observed reservoir series, verbatim units.',
    },
  },
};

describe('ReservoirsSection', () => {
  it('renders the dam with verbatim units and the no-datum caveat', () => {
    const html = render('basin:green-duwamish', GREEN);
    expect(html).toContain('Howard Hanson Dam');
    expect(html).toContain('k-acre-feet');
    expect(html).toContain('cubic feet per second');
    expect(html).toContain('(datum unstated)');
    expect(html).toContain('OBSERVED');
  });

  it('renders nothing at all for an unregulated basin — no section, no empty shell', () => {
    const html = render('basin:nooksack', {
      basin_id: 'basin:nooksack', as_of: '2026-08-28T09:00:00Z', reservoirs: [], provenance_refs: {},
    });
    expect(html).toBe('');
  });
});

describe('error state', () => {
  it('a failed endpoint says so instead of impersonating an unregulated basin', async () => {
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false, retryOnMount: false, staleTime: Infinity } } });
    const key = keys.basinReservoirs('basin:green-duwamish', null);
    // settle the query into its error state the way the runtime would
    await qc.prefetchQuery({ queryKey: key, queryFn: () => Promise.reject(new Error('HTTP 500')) });
    const html = renderToStaticMarkup(
      createElement(QueryClientProvider, { client: qc },
        createElement(ReservoirsSection, { basinId: 'basin:green-duwamish' })),
    );
    expect(html).toContain('Reservoir state unavailable');
    expect(html).toContain('HTTP 500');
  });
});
