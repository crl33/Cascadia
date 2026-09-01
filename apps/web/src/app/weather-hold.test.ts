import { describe, expect, it } from 'vitest';
import { createWeatherHold, type WeatherLayerId } from './weather-hold';

describe('weather hold — no weather setData between started and settled', () => {
  it('applies straight through when no flight is active', () => {
    const applied: [WeatherLayerId, string][] = [];
    const hold = createWeatherHold<string>((layer, doc) => applied.push([layer, doc]));
    hold.offer('precip_observed', 'p1');
    expect(applied).toEqual([['precip_observed', 'p1']]);
    expect(hold.holding).toBe(false);
  });

  it('holds documents offered mid-flight and flushes the LATEST per layer on settle', () => {
    const applied: [WeatherLayerId, string | null][] = [];
    const holding: boolean[] = [];
    const hold = createWeatherHold<string | null>((layer, doc) => applied.push([layer, doc]), (h) => holding.push(h));
    hold.setFlying(true);
    hold.offer('precip_observed', 'p1');
    hold.offer('snow_cover', null);
    hold.offer('precip_observed', 'p2');
    expect(applied).toEqual([]);
    expect(hold.holding).toBe(true);
    hold.setFlying(false);
    expect(applied).toEqual([['precip_observed', 'p2'], ['snow_cover', null]]);
    expect(hold.holding).toBe(false);
    expect(holding).toEqual([true, false]);
  });

  it('a settle with nothing held applies nothing and reports no change', () => {
    let applies = 0;
    const holding: boolean[] = [];
    const hold = createWeatherHold<string>(() => { applies += 1; }, (h) => holding.push(h));
    hold.setFlying(true);
    hold.setFlying(false);
    expect(applies).toBe(0);
    expect(holding).toEqual([]);
  });

  it('a flight that supersedes another keeps holding; the flush waits for the final settle', () => {
    const applied: string[] = [];
    const hold = createWeatherHold<string>((_layer, doc) => applied.push(doc));
    hold.setFlying(true);
    hold.offer('snow_cover', 's1');
    hold.setFlying(true); // superseding flight: started again before any settle
    expect(applied).toEqual([]);
    hold.setFlying(false);
    expect(applied).toEqual(['s1']);
  });
});
