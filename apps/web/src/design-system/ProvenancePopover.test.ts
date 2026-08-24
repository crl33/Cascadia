import { describe, expect, it } from 'vitest';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { ProvenancePopover, ProvenanceRecord } from './ProvenancePopover';
import { toProvenanceFields } from './provenance-record';
import type { ProvenanceRef } from '../contracts/schemas';

/** A ref with every ProvenanceRef field populated (values from the live NWPS run shape). */
const FULL_REF: ProvenanceRef = {
  source_id: 'src:nwps-v1',
  source_kind: 'OFFICIAL_FORECAST',
  product_id: 'product:nwps-forecast',
  method_id: 'method:crest-extract@1.0.0',
  issued_at: '2026-08-23T15:57:00Z',
  valid_time: '2026-08-24T06:00:00Z',
  retrieved_at: '2026-08-24T10:25:17Z',
  freshness: { state: 'current', age_seconds: 69367, expected_cadence_seconds: 86400 },
  quality: ['provisional', 'estimated'],
  label: 'NWRFC official river forecast via NOAA NWPS',
  raw_artifact_id: 'raw:artifact:9',
};

describe('toProvenanceFields', () => {
  it('derives every doctrine field, in order', () => {
    const fields = toProvenanceFields(FULL_REF, 'authoritative_model');
    expect(fields.map((f) => f.key)).toEqual([
      'SOURCE', 'KIND', 'TRUTH', 'PRODUCT', 'METHOD', 'ISSUED', 'VALID', 'RETRIEVED', 'FRESHNESS', 'QUALITY', 'RAW ARTIFACT',
    ]);
    const byKey = Object.fromEntries(fields.map((f) => [f.key, f.value]));
    expect(byKey['SOURCE']).toBe('src:nwps-v1 · product:nwps-forecast — NWRFC official river forecast via NOAA NWPS');
    expect(byKey['KIND']).toBe('official forecast');
    expect(byKey['TRUTH']).toBe('B · authoritative model');
    expect(byKey['PRODUCT']).toBe('product:nwps-forecast');
    expect(byKey['METHOD']).toBe('method:crest-extract@1.0.0');
    expect(byKey['ISSUED']).toBe('2026-08-23 15:57 UTC');
    expect(byKey['VALID']).toBe('2026-08-24 06:00 UTC');
    expect(byKey['RETRIEVED']).toBe('2026-08-24 10:25 UTC');
    expect(byKey['FRESHNESS']).toBe('current · age 19.3 h · cadence 24.0 h');
    expect(byKey['QUALITY']).toBe('provisional, estimated');
    expect(byKey['RAW ARTIFACT']).toBe('raw:artifact:9');
  });
  it('marks issued n/a for observations and prints explicit absences', () => {
    const observation: ProvenanceRef = {
      source_id: 'src:usgs-nwis-iv', source_kind: 'OBSERVED', label: 'USGS instantaneous values',
      freshness: { state: 'stale', age_seconds: null },
    };
    const byKey = Object.fromEntries(toProvenanceFields(observation, 'observation').map((f) => [f.key, f.value]));
    expect(byKey['ISSUED']).toBe('n/a (observation)');
    expect(byKey['TRUTH']).toBe('A · observation');
    expect(byKey['PRODUCT']).toBe('—');
    expect(byKey['METHOD']).toBe('none (untransformed)');
    expect(byKey['VALID']).toBe('—');
    expect(byKey['QUALITY']).toBe('—');
    expect(byKey['RAW ARTIFACT']).toBe('—');
    expect(byKey['FRESHNESS']).toBe('stale · age unknown');
  });
});

describe('ProvenancePopover rendering', () => {
  it('open popover renders every ProvenanceRef field', () => {
    const html = renderToStaticMarkup(
      createElement(ProvenancePopover, {
        provKey: 'nwps-forecast-mvew1', prov: FULL_REF, truth: 'authoritative_model', testId: 'forecast-badge', defaultOpen: true,
      }),
    );
    expect(html).toContain('data-testid="layer-inspector"');
    expect(html).toContain('OFFICIAL FORECAST');
    for (const field of toProvenanceFields(FULL_REF, 'authoritative_model')) {
      expect(html).toContain(field.key);
      expect(html.replace(/&#x27;|&quot;/g, '')).toContain(field.value.replace(/'/g, ''));
    }
  });
  it('closed popover renders only the trigger badge', () => {
    const html = renderToStaticMarkup(
      createElement(ProvenancePopover, { provKey: 'k', prov: FULL_REF, truth: null }),
    );
    expect(html).toContain('OFFICIAL FORECAST');
    expect(html).not.toContain('layer-inspector');
  });
  it('a missing ref renders the UNKNOWN badge and an incomplete-document explanation', () => {
    const html = renderToStaticMarkup(
      createElement(ProvenancePopover, { provKey: 'ghost-ref', prov: undefined, truth: null, defaultOpen: true }),
    );
    expect(html).toContain('UNKNOWN');
    expect(html).toContain('ghost-ref');
    expect(html).toContain('the value is UNKNOWN');
  });
  it('ProvenanceRecord is a native dialog labeled for the value', () => {
    const html = renderToStaticMarkup(
      createElement(ProvenanceRecord, { provKey: 'usgs-iv-12200500', prov: FULL_REF, truth: null, onClose: () => {} }),
    );
    expect(html).toContain('<dialog');
    expect(html).toContain('aria-label="Provenance for usgs-iv-12200500"');
    expect(html).toContain('not stated');
  });
});
