/**
 * Antecedent precipitation rendered: the honesty rules survive to the text a reader gets.
 * Same idiom as Tier0Section.test.ts — static markup, presentational assertions.
 */
import { renderToStaticMarkup } from 'react-dom/server';
import { createElement } from 'react';
import { describe, expect, it } from 'vitest';
import { AntecedentSection } from './BasinPanel';
import type { BasinVisualizationState, ProvenanceRef } from '../contracts/schemas';

type Entry = NonNullable<BasinVisualizationState['antecedent_precip']>[number];

const REFS: Record<string, ProvenanceRef | undefined> = {
  'qpe-antecedent-skagit': {
    source_id: 'src:mrms', source_kind: 'OBSERVED', product_id: 'product:mrms-qpe-01h-pass2',
    freshness: { state: 'current', age_seconds: 3400 },
    quality: [], label: 'MRMS multi-sensor QPE, hourly basin mean',
  } as unknown as ProvenanceRef,
};

function entry(overrides: Partial<Entry>): Entry {
  return {
    window_h: 6, window_end: '2026-08-28T04:00:00Z',
    total: { value: 9.0, unit: 'mm' }, hours_present: 6, hours_expected: 6,
    truth: 'observation', prov: 'qpe-antecedent-skagit', reason: null,
    ...overrides,
  } as Entry;
}

function render(entries: Entry[]): string {
  return renderToStaticMarkup(createElement(AntecedentSection, { entries, refs: REFS }));
}

describe('AntecedentSection', () => {
  it('prints total, coverage arithmetic and the observed window end', () => {
    const html = render([entry({})]);
    expect(html).toContain('9 mm');
    expect(html).toContain('(6/6 hours)');
    // the anchor is printed, so "6 h" cannot be misread as the last 6 wall-clock hours
    expect(html).toContain('antecedent-window-end');
    expect(html).toContain('2026-08-28');
  });

  it('keeps the underestimate caveat beside a partial sum', () => {
    const html = render([entry({
      window_h: 72, total: { value: 48.0, unit: 'mm' }, hours_present: 48, hours_expected: 72,
      reason: '24 of 72 hours missing at this knowledge time — the total covers only the hours that exist',
    })]);
    expect(html).toContain('48 mm');
    expect(html).toContain('(48/72 hours)');
    expect(html).toContain('24 of 72 hours missing');
  });

  it('an absent total prints UNKNOWN with its reason, never 0 mm', () => {
    const html = render([entry({ total: null, hours_present: 0, window_end: null,
      reason: 'no observed QPE hour is known at this knowledge time' })]);
    expect(html).toContain('UNKNOWN');
    expect(html).not.toContain('0 mm');
    expect(html).toContain('no observed QPE hour is known');
  });

  it('renders nothing at all for an empty list (a 1.3.0 document)', () => {
    expect(render([])).toBe('');
  });
});
