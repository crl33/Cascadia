/**
 * The parser gap, closed and pinned. Tier 0 shipped in the contract on 2026-08-27 and was
 * invisible in the browser: `generated.ts` had the types, `schemas.ts` did not, and `z.object`'s
 * minor-version tolerance stripped every field before the UI could see it. Nothing failed —
 * that is what makes it worth a dedicated test file.
 *
 * These assertions are on the RUNTIME schema. The compile-time half lives in `schemas.ts`
 * (`_noMissing*Keys`), which fails typecheck naming the missing key.
 */
import { describe, expect, it } from 'vitest';
import { loadFixtures } from '../../dev/stub-load.mjs';
import { buildBasinState, buildVizBasins } from '../../dev/stub-data.mjs';
import { BasinEnvelopeSchema } from './schemas';

const EVENT_ZERO = '2025-12-11T12:00:00Z';
const BEFORE_ANY_REFERENCE = '1999-01-01T00:00:00Z';
const fx = loadFixtures();
const parse = (asOf: string, basin: string) =>
  BasinEnvelopeSchema.parse(buildBasinState(fx, basin, asOf) as unknown);

describe('Tier 0 survives runtime parsing', () => {
  it('keeps hydrologic_state, with its reference, clamp and exact rank', () => {
    const item = parse(EVENT_ZERO, 'basin:skagit').items[0]!;
    const state = item.hydrologic_state;
    expect(state, 'hydrologic_state was stripped by the runtime schema').toBeTruthy();
    expect(state!.observed.value).toBe(62600);
    expect(state!.observed.unit).toBe('cfs');
    expect(state!.percentile).toBe(95);
    expect(state!.percentile_clamped).toBe(true);
    expect(state!.reference?.n).toBe(490);
    expect(state!.reference?.independent_years).toBe(98);
    expect(state!.reference?.method_id).toBe('method:streamflow-doy-climatology@1.0.0');
    // the exact rank, censored at 1, naming what it beat
    expect(state!.rank?.rank).toBe(1);
    expect(state!.rank?.of).toBe(491);
    expect(state!.rank?.exceeds_record).toBe(true);
    expect(state!.rank?.previous_max?.value).toBe(37400);
    expect(state!.rank?.previous_max_day).toBe('2004-12-11');
    // the seasonal multiple, with the reference it is a multiple OF
    expect(state!.multiple?.multiple).toBeCloseTo(4.988, 3);
    expect(state!.multiple?.reference_percentile).toBe(95);
    expect(state!.multiple?.reference.value).toBe(12550);
    // the boundary CONDITION — a bound cannot carry a sampling error
    expect(state!.boundary).toBe('unquantified');
    expect(state!.bands_within_sampling_error).toEqual([]);
  });

  it('keeps state_change entries with growth, span and direction', () => {
    const item = parse(EVENT_ZERO, 'basin:skagit').items[0]!;
    const changes = item.state_change ?? [];
    expect(changes.length, 'state_change was stripped by the runtime schema').toBe(2);
    const h24 = changes.find((c) => c.window_h === 24)!;
    expect(h24.growth).toBeCloseTo(1.5084, 4);
    expect(h24.direction).toBe('rising');
    expect(h24.from_value?.value).toBe(41500);
    expect(h24.to_value?.value).toBe(62600);
    // a span that differs from the nominal window must survive, because the UI states it
    const h48 = changes.find((c) => c.window_h === 48)!;
    expect(h48.span_h).toBe(47.5);
  });

  /* THE regression this whole change exists to prevent, asserted in the browser's own parser. */
  it('keeps a BELOW-p90 growth rank — the growth-rank split is not lost in the client', () => {
    const item = parse(EVENT_ZERO, 'basin:snohomish-snoqualmie').items[0]!;
    const state = item.hydrologic_state!;
    expect(state.percentile).toBeLessThan(90);
    expect(state.percentile_clamped).toBe(false);
    // the LEVEL rank is deliberately not read below p90 — that policy is unchanged
    expect(state.rank?.rank).toBeNull();
    expect(state.rank?.reason).toContain('Not read');
    // ...but the GROWTH rank must be present anyway. Before 595fc92 it inherited the level's
    // p90 gate and was absent here, which is the defect.
    const h24 = (item.state_change ?? []).find((c) => c.window_h === 24)!;
    expect(h24.growth).toBeCloseTo(2.0997, 4);
    expect(h24.rank, 'a below-p90 growth rank was lost in the client').toBe(759);
    expect(h24.rank_of).toBe(34957);
    expect(h24.rank_reason).toBeNull();
  });

  it('keeps a refusal with its own reason rather than a generic absence', () => {
    const cedar = parse(EVENT_ZERO, 'basin:cedar').items[0]!;
    const h24 = (cedar.state_change ?? []).find((c) => c.window_h === 24)!;
    expect(h24.growth).toBeNull();
    expect(h24.reason).toContain('no daily mean within 6 h');

    const green = parse(EVENT_ZERO, 'basin:green-duwamish').items[0]!;
    const g24 = (green.state_change ?? []).find((c) => c.window_h === 24)!;
    expect(g24.growth).toBeCloseTo(1.3438, 4);      // the change is exact
    expect(g24.rank).toBeNull();                     // only its rank is refused
    expect(g24.rank_reason).toContain('build_climatology');
    expect(g24.rank_reason, 'the refusal must not blame the percentile').toContain('read at every percentile');
  });

  it('rejects an envelope whose Tier 0 provenance key does not resolve', () => {
    const env = buildBasinState(fx, 'basin:skagit', EVENT_ZERO) as {
      provenance_refs: Record<string, unknown>;
    };
    expect(BasinEnvelopeSchema.safeParse(env).success).toBe(true);
    delete env.provenance_refs['cascade-change-skagit-24h'];
    const result = BasinEnvelopeSchema.safeParse(env);
    expect(result.success, 'a state-change prov key may not dangle').toBe(false);
    if (!result.success) expect(JSON.stringify(result.error.issues)).toContain('cascade-change-skagit-24h');
  });

  it('still tolerates a genuinely unknown future field', () => {
    const env = buildBasinState(fx, 'basin:skagit', EVENT_ZERO) as { items: Record<string, unknown>[] };
    env.items[0]!.some_field_from_contract_1_4_0 = { anything: true };
    const parsed = BasinEnvelopeSchema.parse(env);
    expect(parsed.items[0]).not.toHaveProperty('some_field_from_contract_1_4_0');
    expect(parsed.items[0]!.hydrologic_state, 'tolerance must not cost us Tier 0').toBeTruthy();
  });

  it('clears Tier 0 at a knowledge time before any reference existed', () => {
    const env = BasinEnvelopeSchema.parse(buildVizBasins(fx, BEFORE_ANY_REFERENCE) as unknown);
    for (const item of env.items) {
      expect(item.hydrologic_state, `${item.id} kept a level from a later knowledge time`).toBeNull();
      expect(item.state_change ?? [], `${item.id} kept a change from a later knowledge time`).toEqual([]);
    }
  });
});
