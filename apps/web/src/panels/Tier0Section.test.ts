/**
 * The Tier 0 section rendered, so the browser-side half of the growth-rank fix is pinned too.
 *
 * `renderToStaticMarkup` rather than a DOM testing library: react-dom is already a dependency,
 * the section is presentational, and what these assertions care about is the TEXT a reader ends
 * up with. Interaction lives in the Playwright specs.
 */
import { renderToStaticMarkup } from 'react-dom/server';
import { createElement } from 'react';
import { describe, expect, it } from 'vitest';
import { loadFixtures } from '../../dev/stub-load.mjs';
import { buildBasinState } from '../../dev/stub-data.mjs';
import { BasinEnvelopeSchema } from '../contracts/schemas';
import { Tier0Section } from './Tier0Section';

const EVENT_ZERO = '2025-12-11T12:00:00Z';
const fx = loadFixtures();

function render(basin: string): string {
  const env = BasinEnvelopeSchema.parse(buildBasinState(fx, basin, EVENT_ZERO) as unknown);
  const item = env.items[0]!;
  return renderToStaticMarkup(createElement(Tier0Section, {
    state: item.hydrologic_state,
    changes: item.state_change,
    refs: env.provenance_refs,
    surfaceReason: item.surfaces.susceptibility.reason,
  }));
}

describe('Tier 0 renders three distinct statements', () => {
  it('shows a BELOW-p90 growth rank — the browser proof of the split', () => {
    const html = render('basin:snohomish-snoqualmie');
    expect(html).toContain('2.10×');                       // the change itself
    expect(html).toContain('rising');
    expect(html).toContain('759th');                       // ...and its historical rank
    expect(html).toContain('34,957');
    expect(html).toContain('tier0-change-24h-rank');
    // the level rank is separately, correctly, NOT read below p90 — the two must not be confused
    expect(html).toContain('Exact rank not read');
  });

  it('states a clamped level as a bound and never as an estimate', () => {
    const html = render('basin:skagit');
    expect(html).toContain('At or above the stored p95 limit');
    expect(html).toContain('4.99×');                        // the seasonal multiple
    expect(html).toContain('12,550 cfs');                   // ...and what it is a multiple OF
    expect(html).toContain('1st');                          // the exact rank, censored at 1
    expect(html).toContain('491');
    expect(html).toContain('37,400 cfs');                   // naming the record it beat
    expect(html).toContain('2004-12-11');
    // the boundary is a CONDITION, never a confidence or a probability
    expect(html).toContain('Sampling error is not quantified here');
    expect(html).not.toMatch(/confidence interval|probability|% chance/i);
  });

  it('renders the band-separation condition as a statement about the record', () => {
    const html = render('basin:snohomish-snoqualmie');
    expect(html).toContain('The record cannot separate moderate from high');
    expect(html).not.toMatch(/low confidence|uncertain|likely/i);
  });

  it('keeps every refusal specific and never collapses it to "Unavailable"', () => {
    const cedar = render('basin:cedar');
    expect(cedar).toContain('no daily mean within 6 h');
    expect(cedar).not.toContain('Unavailable');

    const green = render('basin:green-duwamish');
    expect(green).toContain('1.34×');                       // the change is exact
    expect(green).toContain('Not ranked');                  // only the rank is refused
    expect(green).toContain('build_climatology');
    expect(green).toContain('read at every percentile');    // and it does not blame the percentile
  });

  it('states an actual span that differs from the nominal window', () => {
    const html = render('basin:skagit');
    expect(html).toContain('measured over 47.5 h, not the nominal 48 h');
  });

  it('gives every statement its own provenance trigger, not one badge over the section', () => {
    const env = BasinEnvelopeSchema.parse(buildBasinState(fx, 'basin:skagit', EVENT_ZERO) as unknown);
    const item = env.items[0]!;
    const html = render('basin:skagit');
    // one trigger per statement, each with its own testid
    for (const testId of ['tier0-level-badge', 'tier0-change-24h-badge', 'tier0-change-48h-badge']) {
      expect(html, `${testId} has no provenance trigger`).toContain(testId);
    }
    // ...and they do NOT share an identity: the level is the tail-state method, each change is
    // the state-change method, and the level is EXPERIMENTAL where the changes are DERIVED.
    const levelRef = env.provenance_refs[item.hydrologic_state!.prov]!;
    const changeRef = env.provenance_refs[item.state_change![0]!.prov]!;
    expect(levelRef.method_id).toBe('method:streamflow-tail-state@0.1.0');
    expect(changeRef.method_id).toBe('method:streamflow-state-change@0.1.0');
    expect(levelRef.method_id).not.toBe(changeRef.method_id);
    expect(levelRef.source_kind).toBe('EXPERIMENTAL');
    expect(changeRef.source_kind).toBe('DERIVED');
    // the two windows are separate statements with separate refs
    expect(item.state_change![0]!.prov).not.toBe(item.state_change![1]!.prov);
  });

  it('never uses alarm language or the red register for a derived statement', () => {
    for (const basin of ['basin:skagit', 'basin:snohomish-snoqualmie', 'basin:cedar']) {
      const html = render(basin);
      expect(html, basin).not.toMatch(/extreme|dangerous|severe|imminent|warning|alert/i);
      expect(html, basin).not.toMatch(/flood-red|state-very_high/);
    }
  });

  it('says why when there is nothing to say', () => {
    const env = BasinEnvelopeSchema.parse(buildBasinState(fx, 'basin:nooksack', EVENT_ZERO) as unknown);
    const item = env.items[0]!;
    const html = renderToStaticMarkup(createElement(Tier0Section, {
      state: item.hydrologic_state, changes: item.state_change,
      refs: env.provenance_refs, surfaceReason: item.surfaces.susceptibility.reason,
    }));
    expect(html).toContain('tier0-absent');
    expect(html).toContain('No level or change statement at this knowledge time');
  });
});
