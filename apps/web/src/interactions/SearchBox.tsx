/**
 * SearchBox: keyboard-first search-to-flight (docs/CINEMATIC_ROADMAP.md §6 C1,
 * docs/SEMANTIC_ZOOM.md §9). "/" or Cmd/Ctrl+K focuses the input; keystrokes are debounced
 * before GET /search?q=; results are grouped by entity kind with name + id subtitle. Enter or
 * click runs the normal selection pipeline (store selection → scene bridge → camera flight;
 * the reduced-motion cut is owned by the CameraController). Escape closes, then clears.
 * Combobox pattern: DOM focus stays on the input, aria-activedescendant tracks the highlight.
 * Semantic events only; no renderer imports (interactions/ may import api and state only).
 */
import { useEffect, useId, useMemo, useReducer, useRef, useState } from 'react';
import { useSearch } from '../api/hooks';
import { eventBootTimeline, eventById, eventSearchResults } from '../event/registry';
import { useSceneStore } from '../state/store';
import { createDebouncer, SEARCH_DEBOUNCE_MS } from './search-debounce';
import {
  effectiveActiveKey,
  flattenGroups,
  groupSearchResults,
  INITIAL_SEARCH_NAV,
  MIN_QUERY_CHARS,
  optionDomId,
  searchNavReducer,
  type ClientSearchResult,
} from './search-reducer';

/** True when the shortcut target is a place where "/" means typing, not "focus search". */
const isTypingElsewhere = (target: EventTarget | null, searchInput: HTMLInputElement | null): boolean => {
  if (!(target instanceof HTMLElement) || target === searchInput) return false;
  return target.isContentEditable || target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT';
};

export function SearchBox() {
  const [nav, dispatch] = useReducer(searchNavReducer, INITIAL_SEARCH_NAV);
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [debouncer] = useState(() => createDebouncer<string>(SEARCH_DEBOUNCE_MS, setDebouncedQuery));
  const selectBasin = useSceneStore((s) => s.selectBasin);
  const selectForecastPoint = useSceneStore((s) => s.selectForecastPoint);
  const setTimeline = useSceneStore((s) => s.setTimeline);
  const results = useSearch(debouncedQuery);
  const listId = useId();
  const rootRef = useRef<HTMLElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => () => debouncer.cancel(), [debouncer]);

  // Keyboard-first entry: "/" (outside editable fields) or Cmd/Ctrl+K from anywhere.
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const commandK = (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k';
      const slash = event.key === '/' && !event.metaKey && !event.ctrlKey && !event.altKey && !isTypingElsewhere(event.target, inputRef.current);
      if (!commandK && !slash) return;
      event.preventDefault();
      inputRef.current?.focus();
      inputRef.current?.select();
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  // Event replays are client config (event/registry): offered locally, no API change.
  const eventEntries = useMemo(
    () => (debouncedQuery.trim().length >= MIN_QUERY_CHARS ? eventSearchResults(debouncedQuery) : []),
    [debouncedQuery],
  );
  const groups = useMemo(() => groupSearchResults([...eventEntries, ...(results.data?.items ?? [])]), [eventEntries, results.data]);
  const options = useMemo(() => flattenGroups(groups), [groups]);
  const optionKeys = useMemo(() => options.map((option) => option.key), [options]);
  const activeKey = effectiveActiveKey(nav, optionKeys);
  const activeDomId = activeKey === null ? undefined : optionDomId(listId, activeKey);

  // Keep the keyboard highlight visible inside the scrolling popup.
  useEffect(() => {
    if (activeDomId !== undefined) document.getElementById(activeDomId)?.scrollIntoView({ block: 'nearest' });
  }, [activeDomId]);

  const choose = (result: ClientSearchResult) => {
    if (result.kind === 'event') {
      // Entering the event frames its default forecast point and anchors the timeline to the
      // event window in EVENT time (queries carry no as_of — ADR-0010; see event/registry).
      const event = eventById(result.id);
      if (event) {
        selectForecastPoint(event.defaultSel, event.defaultBasin);
        setTimeline(eventBootTimeline(event, null));
      }
    } else if (result.kind === 'basin') selectBasin(result.id);
    else if (result.kind === 'forecast_point') selectForecastPoint(result.id, result.basin_id);
    else selectBasin(result.basin_id); // station: the contract carries no station framing yet, so fly to its basin
    debouncer.cancel();
    setDebouncedQuery('');
    dispatch({ type: 'selected' });
  };

  const onChange = (value: string) => {
    dispatch({ type: 'input-changed', query: value });
    debouncer.push(value);
  };

  const onKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        dispatch({ type: 'move', delta: 1, optionKeys });
        break;
      case 'ArrowUp':
        event.preventDefault();
        dispatch({ type: 'move', delta: -1, optionKeys });
        break;
      case 'Enter': {
        if (!nav.open) break;
        const active = options.find((option) => option.key === activeKey);
        if (active) {
          event.preventDefault();
          choose(active.result);
        }
        break;
      }
      case 'Escape':
        event.preventDefault();
        if (!nav.open) {
          debouncer.cancel();
          setDebouncedQuery('');
        }
        dispatch({ type: 'escape' });
        break;
      default:
        break;
    }
  };

  const onBlur = (event: React.FocusEvent<HTMLElement>) => {
    if (rootRef.current?.contains(event.relatedTarget as Node | null)) return;
    dispatch({ type: 'close' });
  };

  // Results shown for a superseded query stay visible, but the strip says a search is running.
  const stale = debouncedQuery.trim() !== nav.query.trim();
  let status: { text: string; tone: 'muted' | 'error' } | null = null;
  if (results.isError) status = { text: `search unavailable: ${results.error.message}`, tone: 'error' };
  else if (results.isLoading || stale) status = { text: 'searching…', tone: 'muted' };
  else if (results.data && options.length === 0) status = { text: 'no matches', tone: 'muted' };

  return (
    <search className="search" ref={rootRef} onBlur={onBlur}>
      <input
        ref={inputRef}
        className="search-input"
        data-testid="search-input"
        type="search"
        role="combobox"
        placeholder="Search basins, forecast points, stations"
        aria-label="Search"
        aria-keyshortcuts="/ Meta+K Control+K"
        aria-expanded={nav.open}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-activedescendant={activeDomId}
        autoComplete="off"
        spellCheck={false}
        value={nav.query}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={onKeyDown}
      />
      {nav.query === '' ? <kbd className="search-kbd" aria-hidden="true">/</kbd> : null}
      {nav.open ? (
        <div className="search-results" data-testid="search-results">
          {status ? <div className={`search-status ${status.tone}`} role="status">{status.text}</div> : null}
          <ul role="listbox" id={listId} aria-label="Search results">
            {groups.map((group) => (
              <li key={group.kind} role="presentation">
                <div className="search-group-label" id={`${listId}-group-${group.kind}`} role="presentation">
                  {group.label}
                </div>
                <ul role="group" aria-labelledby={`${listId}-group-${group.kind}`}>
                  {group.options.map(({ key, result }) => (
                    <li
                      key={key}
                      id={optionDomId(listId, key)}
                      role="option"
                      aria-selected={key === activeKey}
                      className="search-result"
                      data-testid="search-result"
                      onMouseDown={(event) => event.preventDefault()}
                      onClick={() => choose(result)}
                      onMouseEnter={() => dispatch({ type: 'hover', key })}
                    >
                      <span className="search-name">{result.name}</span>
                      <span className="search-subtitle mono muted">
                        {result.id}
                        {result.kind === 'basin' || result.kind === 'event' ? '' : ` · ${result.basin_id}`}
                      </span>
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </search>
  );
}
