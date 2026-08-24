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
