/**
 * The /system/events SSE client: notify-then-fetch. An `ingest` event names a product id;
 * this module invalidates the LIVE query keys that product feeds, and react-query refetches
 * through the normal read path — no payloads ride the stream, so there is no second source of
 * truth to drift.
 *
 * Two rules:
 *
 * 1. **Live only.** Only keys whose asOf segment is 'now' are invalidated. A replay (`as_of`)
 *    shows what was known THEN, and the past does not change because new bytes arrived now.
 *    Event mode likewise: an archived December is finished.
 * 2. **Named products only.** A `kind` this map does not know invalidates nothing — silently
 *    refetching everything on every unknown event would hide the map going stale. The map is
 *    asserted against events in dev via a console.warn, which is the honest middle ground for
 *    a push channel that must keep working when the backend learns a new product first.
 */
import type { QueryClient } from '@tanstack/react-query';
import { API_BASE } from './client';
import { asOfOfKey } from './keys';

/** product id -> the root query-key prefixes it feeds. Envelope keys cover the basin panel,
 * viz layers and scene summary; river/series keys cover the point-scale surfaces. */
const KIND_PREFIXES: Record<string, string[][]> = {
  // ids verbatim from cascade_core.registry PRODUCTS (asserted against the registry-derived
  // fixture in events.test.ts, so a renamed product fails a test instead of going silent here)
  'product:usgs-iv': [['viz'], ['basin-state'], ['river-state'], ['series']],
  'product:nwps-forecast': [['viz'], ['basin-state'], ['river-state'], ['run'], ['runs']],
  'product:nwps-thresholds': [['viz'], ['basin-state'], ['river-state']],
  'product:nbm-v5-qmd': [['viz'], ['basin-state']],
  'product:nbm-v5-core': [['viz'], ['basin-state']],
  'product:nwm-mr-via-nwps': [['viz'], ['basin-state']],
  'product:mrms-qpe-01h-pass2': [['viz'], ['basin-state']],
  'product:mrms-gaugeinfl-01h-pass2': [['viz'], ['basin-state']],
  'product:wpc-qpf-5km-grib': [['viz'], ['basin-state']],
  'product:nws-api-alerts-active': [['viz'], ['basin-state']],
  'product:nwps-hefs-ensemble': [['viz'], ['basin-state']],
  'product:nwps-hefs-quantiles': [['viz'], ['basin-state']],
  'product:usgs-ogc-daily': [['viz'], ['basin-state'], ['river-state']],
  'product:usgs-daily-stats': [['viz'], ['basin-state'], ['river-state']],
  'product:usgs-doy-normals': [['viz'], ['basin-state'], ['river-state']],
  'product:awdb-snotel-daily': [['viz'], ['basin-state']],
  'product:snodas-swe-daily': [['viz'], ['basin-state']],
  'product:nwrfc-reservoir-obs': [['viz'], ['basin-state'], ['river-state'], ['series']],
  'product:nws-fls-crest': [['river-state'], ['runs']],
  // metadata-only: nothing a live view renders changes when station metadata refreshes
  'product:awdb-stations': [],
};

interface IngestEvent {
  kind: string;
  available_at: string;
}

export function invalidateForKind(queryClient: QueryClient, kind: string): number {
  const prefixes = KIND_PREFIXES[kind];
  if (!prefixes) {
    // A product the map does not know: say so once, invalidate nothing (rule 2).
    console.warn(`[events] unmapped ingest kind ${kind}; nothing invalidated`);
    return 0;
  }
  for (const prefix of prefixes) {
    void queryClient.invalidateQueries({
      predicate: (query) => {
        const key = query.queryKey;
        if (prefix.some((part, i) => key[i] !== part)) return false;
        return asOfOfKey(key) === 'now'; // live only (rule 1)
      },
    });
  }
  return prefixes.length;
}

/**
 * Connect the stream and keep it connected (EventSource reconnects on its own; the server
 * sends `retry: 5000`). Returns a disposer. One connection per app, made in main.tsx.
 */
export function connectIngestEvents(queryClient: QueryClient): () => void {
  if (typeof EventSource === 'undefined') return () => {}; // jsdom/node: no stream, no error
  const source = new EventSource(`${API_BASE}/system/events`);
  const onIngest = (event: MessageEvent) => {
    try {
      const parsed = JSON.parse(event.data) as IngestEvent;
      if (typeof parsed.kind === 'string') invalidateForKind(queryClient, parsed.kind);
    } catch {
      // a malformed frame invalidates nothing; the next poll still tells the truth
    }
  };
  source.addEventListener('ingest', onIngest);
  return () => {
    source.removeEventListener('ingest', onIngest);
    source.close();
  };
}
