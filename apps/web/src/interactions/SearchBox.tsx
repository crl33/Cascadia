/**
 * SearchBox: GET /search?q= → pick a result → store selection (the bridge turns that into a
 * camera flight). Semantic events only; no renderer imports.
 */
import { useDeferredValue, useId, useState } from 'react';
import { useSearch } from '../api/hooks';
import type { SearchResult } from '../contracts/schemas';
import { useSceneStore } from '../state/store';

export function SearchBox() {
  const [text, setText] = useState('');
  const deferred = useDeferredValue(text);
  const results = useSearch(deferred);
  const selectBasin = useSceneStore((s) => s.selectBasin);
  const selectForecastPoint = useSceneStore((s) => s.selectForecastPoint);
  const listId = useId();

  const choose = (result: SearchResult) => {
    if (result.kind === 'basin') selectBasin(result.id);
    else if (result.kind === 'forecast_point') selectForecastPoint(result.id, result.basin_id);
    else selectBasin(result.basin_id);
    setText('');
  };

  const items = results.data?.items ?? [];
  const open = text.trim().length >= 2;

  return (
    <search className="search">
      <input
        className="search-input"
        data-testid="search-input"
        type="search"
        placeholder="Search basins, forecast points, stations"
        aria-label="Search"
        aria-controls={listId}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => { if (e.key === 'Enter' && items[0]) choose(items[0]); if (e.key === 'Escape') setText(''); }}
      />
      {open ? (
        <ul className="search-results" id={listId} aria-label="Search results" data-testid="search-results">
          {results.isPending ? <li className="muted">searching…</li> : null}
          {results.isError ? <li className="error">search unavailable: {results.error.message}</li> : null}
          {results.data && items.length === 0 ? <li className="muted">no matches</li> : null}
          {items.map((r) => (
            <li key={`${r.kind}:${r.id}`}>
              <button type="button" className="search-result" data-testid="search-result" onClick={() => choose(r)}>
                <span className="search-kind">{r.kind.replace('_', ' ')}</span>
                <span>{r.name}</span>
                <span className="mono muted">{r.id}</span>
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </search>
  );
}
