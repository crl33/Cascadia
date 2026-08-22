# apps/ — deployable units

- `api/` FastAPI, read-mostly, no provider imports (enforced). Routers mirror
  `docs/ARCHITECTURE.md` §6.
- `worker/` scheduler + job runner importing `packages/providers/*/jobs.py` and
  `packages/hydrology` methods; the only process type that writes.
- `web/` Vite + React + TypeScript + CesiumJS; consumes generated contract types; see
  `docs/CINEMATIC_ARCHITECTURE.md`. Nested `AGENTS.md` files are added per subsystem
  (`scene/`, `camera/`, `layers/<domain>/`, `timeline/`) only when that subsystem exists and
  carries real complexity.

Status: empty until Phase 0 implementation / the cinematic spike.
