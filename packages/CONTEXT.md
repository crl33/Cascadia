# packages/ — Python domain packages (one uv workspace)

One job per package; science in packages, IO at the edges. Import direction is enforced by
`import-linter` (to be configured in Phase 0):

```
contracts  ←  core  ←  geo  ←  hydrology  ←  history
                 ↑            ↑
              providers   visualization
```

- `contracts/` Pydantic models + JSON Schema export (API and visualization contracts). No IO.
- `core/` config, logging/tracing, DB session, object store client, time/units utilities.
- `geo/` basins, hypsometry, topology, zonal aggregation, LOD geometry generation.
- `providers/<name>/` one source each: `client.py` (HTTP, rate limit, archive), `parser.py`
  (strict, typed), `normalize.py` (units/time/quality), `fixtures/`, `canary.py`. See
  `providers/CONTEXT.md`.
- `hydrology/` features (`Method`s), surfaces/assessments, explanation deltas.
- `history/` events, timelines, `as_known_at`, hindcast harness.
- `visualization/` scene contracts assembly, tile/derivative generation. May prepare data for
  rendering; may not compute hydrologic truth.

Status: directories exist; code starts in Phase 0 per `docs/ROADMAP.md`.
