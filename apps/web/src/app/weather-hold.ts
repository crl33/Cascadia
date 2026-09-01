/**
 * Weather hold (film rule 3, cesium-cinematic-plan-2026-09-01 row 1 / step 1.6): a weather
 * field that arrives mid-flight is not applied mid-flight. One primary motion at a time — a
 * precipitation wash re-painting under a moving camera is a second motion — so the latest
 * document per layer is held and applied on settle. Pure: no React, no DOM, no renderer.
 * SceneDataBridge owns the `apply` callback (controller.setData) and the DOM stamps.
 */
export type WeatherLayerId = 'precip_observed' | 'snow_cover';

export interface WeatherHold<Doc> {
  /** Latest document for a layer: applied now when not flying, else held (last one wins). */
  offer(layer: WeatherLayerId, doc: Doc): void;
  /** Flip on flight start / settle; settling flushes every held document, in layer order. */
  setFlying(flying: boolean): void;
  /** True while at least one document waits for the settle. */
  readonly holding: boolean;
}

export function createWeatherHold<Doc>(apply: (layer: WeatherLayerId, doc: Doc) => void, onHoldingChange?: (holding: boolean) => void): WeatherHold<Doc> {
  let flying = false;
  const pending = new Map<WeatherLayerId, Doc>();
  let lastHolding = false;
  const publish = () => {
    const holding = pending.size > 0;
    if (holding === lastHolding) return;
    lastHolding = holding;
    onHoldingChange?.(holding);
  };
  return {
    offer(layer, doc) {
      if (flying) {
        pending.set(layer, doc);
        publish();
        return;
      }
      apply(layer, doc);
    },
    setFlying(next) {
      flying = next;
      if (flying) return;
      const flush = [...pending.entries()];
      pending.clear();
      publish();
      flush.forEach(([layer, doc]) => apply(layer, doc));
    },
    get holding() { return pending.size > 0; },
  };
}
