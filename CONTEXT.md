# Cascadia Papsukkal — the workspace in one screen

Form: **umbrella** over (a) a documentation factory (`docs/`), (b) a historical reference
(`v1/`), and (c) the V2 implementation (`apps/`, `packages/`, `tests/`, `infra/`), which will
become a **system map** once code exists (`map/` is created at that point, not before).

## The pipeline of information

```
external sources → ingestion workers → raw archive → normalize/quality → historical store
→ state engine → feature engine → forecast intelligence → explanation/provenance → API → UI
```

Data acquisition never depends on a UI request. The renderer presents; it does not define.

## The three risk surfaces (never collapsed)

| Surface | Question | Owner doc |
|---|---|---|
| Basin susceptibility | how primed is the watershed? | `docs/HYDROLOGY.md` §3 |
| Meteorological forcing | how much hydrologically significant water is coming? | `docs/HYDROLOGY.md` §4 |
| Flood hazard | probability of crossing meaningful thresholds, per horizon | `docs/HYDROLOGY.md` §5 |

## Status is what exists

| Artifact | Means |
|---|---|
| `docs/*.md` present | Phase 0 documentation delivered |
| `docs/adr/ADR-NNNN-*.md` with `Status: Accepted` | decision settled |
| `packages/contracts/` with schemas + tests | Phase 0 contracts started |
| `apps/worker/` ingesting into PostGIS with fixtures passing | Phase 1 started |
| `apps/web/` with the Skagit flight spike passing E2E | Phase C1/C2 spike proven |

Factory (stable): `docs/`. Product (per run): `apps/`, `packages/`, data in PostGIS/object store.
