import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createDebouncer, SEARCH_DEBOUNCE_MS } from './search-debounce';

describe('createDebouncer', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it('fires once with the latest value after the delay', () => {
    const fired: string[] = [];
    const debouncer = createDebouncer<string>(SEARCH_DEBOUNCE_MS, (v) => fired.push(v));
    debouncer.push('s');
    debouncer.push('sk');
    debouncer.push('ska');
    expect(fired).toEqual([]);
    vi.advanceTimersByTime(SEARCH_DEBOUNCE_MS);
    expect(fired).toEqual(['ska']);
    expect(debouncer.pending).toBe(false);
  });

  it('restarts the delay on every push (trailing edge)', () => {
    const fired: string[] = [];
    const debouncer = createDebouncer<string>(200, (v) => fired.push(v));
    debouncer.push('sk');
    vi.advanceTimersByTime(150);
    debouncer.push('ska');
    vi.advanceTimersByTime(150);
    expect(fired).toEqual([]); // 300ms elapsed, but only 150ms since the last push
    vi.advanceTimersByTime(50);
    expect(fired).toEqual(['ska']);
  });

  it('flush fires the pending value immediately and is a no-op when idle', () => {
    const fired: string[] = [];
    const debouncer = createDebouncer<string>(200, (v) => fired.push(v));
    debouncer.flush();
    expect(fired).toEqual([]);
    debouncer.push('skagit');
    debouncer.flush();
    expect(fired).toEqual(['skagit']);
    vi.advanceTimersByTime(400);
    expect(fired).toEqual(['skagit']); // the cleared timer never double-fires
  });

  it('cancel drops the pending value', () => {
    const fired: string[] = [];
    const debouncer = createDebouncer<string>(200, (v) => fired.push(v));
    debouncer.push('skagit');
    expect(debouncer.pending).toBe(true);
    debouncer.cancel();
    expect(debouncer.pending).toBe(false);
    vi.advanceTimersByTime(400);
    expect(fired).toEqual([]);
  });
});
