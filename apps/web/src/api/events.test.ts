/**
 * The SSE kind map: complete against the registry (via the generated fixture), live-only in
 * what it invalidates, and silent-but-loud on an unknown kind.
 */
import { QueryClient } from '@tanstack/react-query';
import { afterEach, describe, expect, it, vi } from 'vitest';
import productIds from '../../dev/product-ids.json';
import { invalidateForKind } from './events';
import { keys } from './keys';

afterEach(() => vi.restoreAllMocks());

describe('the kind map', () => {
  it('names every registry product — a new provider must decide its invalidations', () => {
    const qc = new QueryClient();
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    for (const id of (productIds as { ids: string[] }).ids) {
      invalidateForKind(qc, id);
    }
    expect(warn).not.toHaveBeenCalled();
  });

  it('an unknown kind invalidates nothing and says so', () => {
    const qc = new QueryClient();
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    expect(invalidateForKind(qc, 'product:never-heard-of-it')).toBe(0);
    expect(warn).toHaveBeenCalledOnce();
  });
});

describe('live-only invalidation', () => {
  it('marks the live envelope stale and leaves the replay of the same query alone', async () => {
    const qc = new QueryClient();
    const live = keys.vizBasins(null);
    const replay = keys.vizBasins('2025-12-12T08:00:00Z');
    qc.setQueryData(live, { items: [] });
    qc.setQueryData(replay, { items: [] });
    invalidateForKind(qc, 'product:mrms-qpe-01h-pass2');
    await Promise.resolve();
    expect(qc.getQueryState(live)?.isInvalidated).toBe(true);
    expect(qc.getQueryState(replay)?.isInvalidated).toBe(false); // the past does not change
  });

  it('an alert ingest touches envelopes, not station series', async () => {
    const qc = new QueryClient();
    const series = keys.stationSeries('usgs:12200500', 'flow', null);
    const envelope = keys.basinState('basin:skagit', null);
    qc.setQueryData(series, []);
    qc.setQueryData(envelope, { items: [] });
    invalidateForKind(qc, 'product:nws-api-alerts-active');
    await Promise.resolve();
    expect(qc.getQueryState(series)?.isInvalidated).toBe(false);
    expect(qc.getQueryState(envelope)?.isInvalidated).toBe(true);
  });
});
