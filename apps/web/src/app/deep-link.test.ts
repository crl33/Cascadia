import { describe, expect, it } from 'vitest';
import { parseDeepLink, serializeDeepLink, type DeepLink } from './deep-link';

describe('deep link', () => {
  it('round-trips basin, forecast point, motion and band', () => {
    const link: DeepLink = { basinId: 'basin:skagit', forecastPointId: 'fp:nwps:MVEW1', motion: 'reduced', band: 'river' };
    const qs = serializeDeepLink(link);
    expect(qs).toBe('?basin=basin%3Askagit&fp=MVEW1&motion=reduced&band=river');
    expect(parseDeepLink(qs)).toEqual(link);
  });
  it('serializes nothing for the empty state and omits the system motion default', () => {
    const empty: DeepLink = { basinId: null, forecastPointId: null, motion: null, band: null };
    expect(serializeDeepLink(empty)).toBe('');
    expect(serializeDeepLink({ ...empty, motion: 'system' })).toBe('');
    expect(parseDeepLink('')).toEqual(empty);
  });
  it('drops invalid values instead of guessing', () => {
    expect(parseDeepLink('?basin=Skagit&fp=mvew1&motion=fast&band=space')).toEqual({
      basinId: null, forecastPointId: 'fp:nwps:MVEW1', motion: null, band: null,
    });
    expect(parseDeepLink('?fp=fp:nwps:MVEW1').forecastPointId).toBe('fp:nwps:MVEW1');
  });
});
