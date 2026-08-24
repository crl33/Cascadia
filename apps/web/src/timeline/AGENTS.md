# src/timeline — knowledge time (C5 core, P1 scope)

The replay engine's client half. The server is a pure function of `as_of`; this folder only
decides *which* knowledge time is asked for, at a bounded rate, and keeps the UI honest about it.

| File | Owns |
|---|---|
| `window.ts` | pure [T−72h, T] window math (minute-aligned ISO strings; no Date in the store) |
| `TimelineController.ts` | rAF-coalesced scrub → at most one store `asOf` commit per frame; aborts in-flight queries keyed to a superseded `asOf` (TanStack `cancelQueries` fires their AbortSignal); `snapToNow` re-anchors the window |
| `TimelineBar.tsx` | bottom scrub bar: mode chip (NOW live / AS OF … past), 72 h slider, UTC + local readout, NOW button. E2E testids: `timeline` (cluster), `timeline-scrubber`, `snap-to-now`; the replay banner (`app/ReplayBanner`, testid `as-of-banner`) reads AS OF <knowledge time UTC> |
| `timeline.css` | bar styling, tokens only |

Rules: no Cesium imports (ESLint-enforced); no science, no interpolation — a scrub position is
truncated to the minute and sent to the server as `as_of`; freshness shown anywhere in replay is
the server-reported replayed freshness, never client-now math. May import `api/`, `state/`,
`panels/format`, `design-system`. The full C5 (playback engine, forecast horizon `[T, T+120h]`,
run picker) builds on this; see docs/CINEMATIC_ROADMAP.md §10.

## Event mode (P2 Event Zero)

`TimelineState.mode` gained `'event'`: the window becomes the archived event window
(`event/registry`), the cursor is `at` in EVENT time (valid/issued time), and `asOf` stays
null — event-mode queries carry NO `as_of` (ADR-0010: backfilled rows' knowledge time is the
2026 retrieval; a knowledge-time replay inside the event would honestly render UNKNOWN).
`TimelineController.scrubEvent` reuses the rAF coalescing and clamps to the event window; it
aborts nothing, because event queries are keyed by the whole window, not the cursor. The bar
shows an EVENT REPLAY chip; NOW exits to live. TimelineBar may additionally import
`event/registry` (descriptors only).
