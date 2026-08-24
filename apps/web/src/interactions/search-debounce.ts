/**
 * Trailing-edge debouncer for the search input: the query fires SEARCH_DEBOUNCE_MS after the
 * last keystroke, always with the latest value. Pure timer logic so it is unit-testable with
 * fake timers; the component wires onFire to React state.
 */
export const SEARCH_DEBOUNCE_MS = 200;

export interface Debouncer<T> {
  push(value: T): void;
  /** Fire the pending value now instead of waiting for the timer. */
  flush(): void;
  /** Drop the pending value and stop the timer. */
  cancel(): void;
  readonly pending: boolean;
}

export function createDebouncer<T>(delayMs: number, onFire: (value: T) => void): Debouncer<T> {
  let timer: ReturnType<typeof setTimeout> | null = null;
  let held: { value: T } | null = null;

  const clearTimer = () => {
    if (timer !== null) {
      clearTimeout(timer);
      timer = null;
    }
  };
  const fire = () => {
    const firing = held;
    held = null;
    timer = null;
    if (firing) onFire(firing.value);
  };

  return {
    push(value: T) {
      held = { value };
      clearTimer();
      timer = setTimeout(fire, delayMs);
    },
    flush() {
      if (held === null) return;
      clearTimer();
      fire();
    },
    cancel() {
      clearTimer();
      held = null;
    },
    get pending() {
      return held !== null;
    },
  };
}
