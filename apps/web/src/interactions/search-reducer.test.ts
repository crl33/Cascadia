import { describe, expect, it } from 'vitest';
import type { SearchResult } from '../contracts/schemas';
import {
  effectiveActiveKey,
  flattenGroups,
  groupSearchResults,
  INITIAL_SEARCH_NAV,
  MIN_QUERY_CHARS,
  optionDomId,
  optionKey,
  searchNavReducer,
  type SearchNavState,
} from './search-reducer';

const result = (kind: SearchResult['kind'], id: string, name: string, basinId = 'basin:skagit'): SearchResult => ({
  id, kind, name, basin_id: basinId, location: [-122.3, 48.4],
});

const skagit = result('basin', 'basin:skagit', 'Skagit');
const green = result('basin', 'basin:green', 'Green', 'basin:green');
const mvew1 = result('forecast_point', 'fp:nwps:MVEW1', 'Skagit River near Mount Vernon');
const station = result('station', 'station:usgs:12200500', 'USGS 12200500 (Skagit River near Mount Vernon)');

describe('groupSearchResults', () => {
  it('groups by kind in the canonical order (basins, forecast points, stations), omitting empty groups', () => {
    const groups = groupSearchResults([station, skagit, mvew1, green]);
    expect(groups.map((g) => g.kind)).toEqual(['basin', 'forecast_point', 'station']);
    expect(groups.map((g) => g.label)).toEqual(['Basins', 'Forecast points', 'Stations']);
    expect(groupSearchResults([mvew1]).map((g) => g.kind)).toEqual(['forecast_point']);
    expect(groupSearchResults([])).toEqual([]);
  });
  it('preserves API order within a group and flattens across groups in display order', () => {
    const groups = groupSearchResults([station, green, skagit, mvew1]);
    expect(flattenGroups(groups).map((o) => o.key)).toEqual([
      optionKey(green), optionKey(skagit), optionKey(mvew1), optionKey(station),
    ]);
  });
});

describe('optionDomId', () => {
  it('is deterministic and scoped by the list id', () => {
    expect(optionDomId(':r1:', 'basin:basin:skagit')).toBe(':r1:-option-basin:basin:skagit');
  });
});

describe('searchNavReducer', () => {
  const keys = flattenGroups(groupSearchResults([skagit, green, mvew1, station])).map((o) => o.key);
  const type = (query: string): SearchNavState => searchNavReducer(INITIAL_SEARCH_NAV, { type: 'input-changed', query });

  it(`opens once the query reaches ${MIN_QUERY_CHARS} characters and closes below it`, () => {
    expect(type('s').open).toBe(false);
    expect(type('sk').open).toBe(true);
    expect(type('  s  ').open).toBe(false); // whitespace does not count
    const reopened = searchNavReducer(type('ska'), { type: 'input-changed', query: 's' });
    expect(reopened.open).toBe(false);
  });

  it('resets the highlight whenever the query changes', () => {
    const highlighted = searchNavReducer(type('sk'), { type: 'move', delta: 1, optionKeys: keys });
    const retyped = searchNavReducer(highlighted, { type: 'input-changed', query: 'ska' });
    expect(retyped.activeKey).toBeNull();
  });

  it('ArrowDown walks the flattened group order and wraps; ArrowUp from the top wraps to the end', () => {
    let state = type('sk');
    expect(effectiveActiveKey(state, keys)).toBe(keys[0]); // default highlight is the first option
    state = searchNavReducer(state, { type: 'move', delta: 1, optionKeys: keys });
    expect(state.activeKey).toBe(keys[1]);
    state = searchNavReducer(state, { type: 'move', delta: 1, optionKeys: keys });
    state = searchNavReducer(state, { type: 'move', delta: 1, optionKeys: keys });
    expect(state.activeKey).toBe(keys[3]);
    state = searchNavReducer(state, { type: 'move', delta: 1, optionKeys: keys });
    expect(state.activeKey).toBe(keys[0]); // wrap forward
    state = searchNavReducer(state, { type: 'move', delta: -1, optionKeys: keys });
    expect(state.activeKey).toBe(keys[3]); // wrap backward
  });

  it('ArrowDown with the popup closed reopens it for a qualifying query instead of moving', () => {
    const closed = searchNavReducer(type('ska'), { type: 'escape' });
    const reopened = searchNavReducer(closed, { type: 'move', delta: 1, optionKeys: keys });
    expect(reopened.open).toBe(true);
    const empty = searchNavReducer(INITIAL_SEARCH_NAV, { type: 'move', delta: 1, optionKeys: keys });
    expect(empty.open).toBe(false); // nothing to search for
  });

  it('moving over an empty result list is a no-op', () => {
    const state = type('zz');
    expect(searchNavReducer(state, { type: 'move', delta: 1, optionKeys: [] })).toEqual(state);
    expect(effectiveActiveKey(state, [])).toBeNull();
  });

  it('a stale highlight (result set changed underneath) falls back to the first option', () => {
    const state = searchNavReducer(type('sk'), { type: 'hover', key: 'station:station:usgs:12200500' });
    const fewerKeys = keys.slice(0, 2);
    expect(effectiveActiveKey(state, fewerKeys)).toBe(fewerKeys[0]);
  });

  it('Escape closes the open popup keeping the query; a second Escape clears the query', () => {
    const open = type('skagit');
    const closed = searchNavReducer(open, { type: 'escape' });
    expect(closed).toMatchObject({ open: false, query: 'skagit', activeKey: null });
    const cleared = searchNavReducer(closed, { type: 'escape' });
    expect(cleared.query).toBe('');
  });

  it('hover highlights only while open; close and selected reset', () => {
    expect(searchNavReducer(INITIAL_SEARCH_NAV, { type: 'hover', key: keys[0]! }).activeKey).toBeNull();
    const hovered = searchNavReducer(type('sk'), { type: 'hover', key: keys[2]! });
    expect(hovered.activeKey).toBe(keys[2]);
    expect(searchNavReducer(hovered, { type: 'close' })).toMatchObject({ open: false, activeKey: null, query: 'sk' });
    expect(searchNavReducer(hovered, { type: 'selected' })).toEqual(INITIAL_SEARCH_NAV);
  });
});
