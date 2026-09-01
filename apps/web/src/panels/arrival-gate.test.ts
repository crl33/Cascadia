import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ARRIVAL_HOLD_MS, createArrivalGate } from './arrival-gate';

describe('arrival gate — the panel is part of the arrival, never of the flight', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it('holds while flying and for ARRIVAL_HOLD_MS after settle, then shows', () => {
    const gate = createArrivalGate();
    const seen: string[] = [];
    gate.subscribe(() => seen.push(gate.gate()));
    expect(gate.gate()).toBe('show');
    gate.update('flying');
    expect(gate.gate()).toBe('hold');
    gate.update('settled');
    expect(gate.gate()).toBe('hold');
    vi.advanceTimersByTime(ARRIVAL_HOLD_MS - 1);
    expect(gate.gate()).toBe('hold');
    vi.advanceTimersByTime(1);
    expect(gate.gate()).toBe('show');
    expect(seen).toEqual(['hold', 'show']);
  });

  it('a settle the gate never saw as a flight (deep-link cut) adds no hold', () => {
    const gate = createArrivalGate();
    gate.update('settled');
    expect(gate.gate()).toBe('show');
    expect(vi.getTimerCount()).toBe(0);
  });

  it('reduced motion (hold 0) releases synchronously on settle — no timer, no extra frame', () => {
    const gate = createArrivalGate(0);
    gate.update('flying');
    expect(gate.gate()).toBe('hold');
    gate.update('settled');
    expect(gate.gate()).toBe('show');
    expect(vi.getTimerCount()).toBe(0);
  });

  it('a new flight during the hold cancels the pending release and keeps holding', () => {
    const gate = createArrivalGate();
    gate.update('flying');
    gate.update('settled');
    vi.advanceTimersByTime(ARRIVAL_HOLD_MS / 2);
    gate.update('flying');
    vi.advanceTimersByTime(ARRIVAL_HOLD_MS);
    expect(gate.gate()).toBe('hold');
    gate.update('settled');
    vi.advanceTimersByTime(ARRIVAL_HOLD_MS);
    expect(gate.gate()).toBe('show');
  });

  it('repeated settled updates during the hold neither restart nor duplicate the timer', () => {
    const gate = createArrivalGate();
    gate.update('flying');
    gate.update('settled');
    vi.advanceTimersByTime(300);
    gate.update('settled');
    expect(vi.getTimerCount()).toBe(1);
    vi.advanceTimersByTime(100);
    expect(gate.gate()).toBe('show');
  });

  it('idle opens the gate immediately; dispose cancels a pending release', () => {
    const gate = createArrivalGate();
    gate.update('flying');
    gate.update('idle');
    expect(gate.gate()).toBe('show');
    gate.update('flying');
    gate.update('settled');
    gate.dispose();
    vi.advanceTimersByTime(ARRIVAL_HOLD_MS * 2);
    expect(gate.gate()).toBe('hold');
    expect(vi.getTimerCount()).toBe(0);
  });
});
