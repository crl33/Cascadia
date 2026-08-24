# src/event — event replay (P2 Event Zero)

Client half of the historical-event experience (docs/EVENT_ZERO.md; docs/CINEMATIC_ROADMAP.md
§11 at P2 scope). The scrub cursor here is EVENT time (valid/issued time), never knowledge
time: backfilled archive rows carry `available_at` = retrieval time (ADR-0010), so event-mode
queries omit `as_of` entirely, fetch each archived window ONCE (series by valid_time, runs by
issued_at) and filter client-side — presentation-side windowing of complete honest documents.

| File | Owns |
|---|---|
| `registry.ts` | event descriptors (ids, window bounds, default framing — doc citations, no science), `eventBootTimeline`, synthetic search entries |
| `event-filter.ts` | pure cursor filters: series ≤ at, runs issued ≤ at, current-run selection, observed crest (first max), backfilled detection |
| `EventBanner.tsx` | the event-replay honesty banner (testid `event-banner`) |
| `ForecastEvolution.tsx` | the §8 runs-vs-observed-crest table (testids `forecast-evolution`, `evolution-run` + `data-superseded`, `evolution-backfilled`, `evolution-observed-crest`) |

Rules: no Cesium imports (ESLint-enforced); no science — every number arrives in a contract
document; UNKNOWN renders as UNKNOWN with its reason; superseded runs are marked, never
removed; no narrative text, no dramatization (VISUAL_TRUTH_DOCTRINE). May import `api/`,
`state/`, `contracts/`, `panels/` (format, hydrograph-math, ProvenanceLine), `design-system/`,
`timeline/window`.
