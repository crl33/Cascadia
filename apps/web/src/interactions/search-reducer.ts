/**
 * Pure search-navigation state: query text, popup visibility, and the keyboard-highlighted
 * option (docs/SEMANTIC_ZOOM.md §9 — shortcut opens, arrows move, Enter selects, Escape
 * closes). No DOM, no fetching, no renderer types: the component owns focus, the query layer
 * owns results; this reducer is the unit-testable law for what the keys do. Results are grouped
 * by entity kind in a fixed order; keyboard movement walks the flattened group order.
 */
import type { SearchResult } from '../contracts/schemas';

export const MIN_QUERY_CHARS = 2;

export type SearchKind = SearchResult['kind'];
export interface SearchOption {
  readonly key: string;
  readonly result: SearchResult;
}
export interface SearchGroup {
  readonly kind: SearchKind;
  readonly label: string;
  readonly options: readonly SearchOption[];
}

const GROUP_ORDER: readonly SearchKind[] = ['basin', 'forecast_point', 'station'];
const GROUP_LABEL: Record<SearchKind, string> = { basin: 'Basins', forecast_point: 'Forecast points', station: 'Stations' };

export const optionKey = (result: SearchResult): string => `${result.kind}:${result.id}`;
export const optionDomId = (listId: string, key: string): string => `${listId}-option-${key}`;

/** Group results by kind in the canonical order, dropping empty groups, keeping API order within a group. */
export function groupSearchResults(items: readonly SearchResult[]): SearchGroup[] {
  return GROUP_ORDER.flatMap((kind) => {
    const options = items.filter((result) => result.kind === kind).map((result) => ({ key: optionKey(result), result }));
    return options.length > 0 ? [{ kind, label: GROUP_LABEL[kind], options }] : [];
  });
}

export const flattenGroups = (groups: readonly SearchGroup[]): SearchOption[] => groups.flatMap((group) => [...group.options]);

export interface SearchNavState {
  readonly query: string;
  readonly open: boolean;
  readonly activeKey: string | null;
}

export const INITIAL_SEARCH_NAV: SearchNavState = { query: '', open: false, activeKey: null };

export type SearchNavAction =
  | { type: 'input-changed'; query: string }
  | { type: 'move'; delta: 1 | -1; optionKeys: readonly string[] }
  | { type: 'hover'; key: string }
  | { type: 'escape' }
  | { type: 'close' }
  | { type: 'selected' };

const qualifies = (query: string): boolean => query.trim().length >= MIN_QUERY_CHARS;

/**
 * The highlighted option for aria-activedescendant: the tracked key while it still exists in
 * the current list, otherwise the first option. Keeps the highlight lawful when results change
 * under the cursor without mirroring the result list into state.
 */
export function effectiveActiveKey(state: SearchNavState, optionKeys: readonly string[]): string | null {
  if (!state.open || optionKeys.length === 0) return null;
  return state.activeKey !== null && optionKeys.includes(state.activeKey) ? state.activeKey : optionKeys[0] ?? null;
}

export function searchNavReducer(state: SearchNavState, action: SearchNavAction): SearchNavState {
  switch (action.type) {
    case 'input-changed':
      return { query: action.query, open: qualifies(action.query), activeKey: null };
    case 'move': {
      if (!state.open) return qualifies(state.query) ? { ...state, open: true } : state;
      const current = effectiveActiveKey(state, action.optionKeys);
      if (current === null) return state;
      const index = action.optionKeys.indexOf(current);
      const next = action.optionKeys[(index + action.delta + action.optionKeys.length) % action.optionKeys.length];
      return next === undefined ? state : { ...state, activeKey: next };
    }
    case 'hover':
      return state.open ? { ...state, activeKey: action.key } : state;
    case 'escape':
      // First Escape closes the popup; Escape with the popup closed clears the query.
      return state.open ? { ...state, open: false, activeKey: null } : { ...state, query: '', activeKey: null };
    case 'close':
      return state.open ? { ...state, open: false, activeKey: null } : state;
    case 'selected':
      return INITIAL_SEARCH_NAV;
  }
}
