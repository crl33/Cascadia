# v1/ — the Emergent-generated prototype (read-only reference)

> Naming: the prototype called itself **Cascade Oracle**; the platform was renamed **Cascadia Papsukkal** on 2026-08-22. Files under `v1/` keep the historical name verbatim; nothing else in the repository uses it.

Origin: private repo `crl33/cascade-oracle`, single commit `06a1c69 "Auto-generated changes"`,
Emergent job `cf6569d5…` created 2026-05-02. Imported verbatim on 2026-08-22 (excluding
`.git/` and the Emergent `.gitconfig`). **Do not develop here.** Port ideas, not files; the
audit is `docs/V1_AUDIT.md`.

## Universes

| Universe | What | Where |
|---|---|---|
| **live knowledge** | station/LID/SNOTEL mappings, threshold-source taxonomy, "unknown is legitimate", precursor ≠ risk separation, design tokens & motion language | `backend/lib/stations.py`, `backend/lib/snotel_stations.py`, `backend/lib/types.py`, `backend/lib/risk.py`, `design_guidelines.md` |
| **leftover** | FastAPI+Motor app, CRA/CRACO frontend, request-driven refresh, process-local caches, Mongo latest-only cache | `backend/server.py`, `backend/lib/cache.py`, `backend/lib/precursors.py`, `frontend/` |
| **ghost** | "frozen" contract slots never implemented (`precipitation_24h`, `soil_moisture`, `basin_tension_score`), phases 3–5 of `plan.md` (TimesFM, theater mode), `lib/fallback_data.py` and `history` collection named in `plan.md` but never written, `tests/` (empty) | `backend/lib/types.py`, `plan.md`, `tests/__init__.py` |
| **hostile / remove** | third-party scripts and analytics key in `frontend/public/index.html`, non-registry tarball dependency, 20+ unused Python deps, unauthenticated refresh endpoints, `CORS * + credentials` | `frontend/public/index.html`, `frontend/package.json`, `backend/requirements.txt`, `backend/server.py` |

## Name collisions

- V1 **"risk_state"** (calm/watch/elevated/flood/unknown) is a *threshold-exceedance
  category of the current observation* — it is **not** V2's Flood Hazard, Susceptibility, or
  Forcing. V2 calls the V1 concept `observed_flood_category`.
- V1 **"precursor"** ≈ a single V2 *DerivedFeature* feeding Basin Susceptibility; V1's
  `confidence` (0.85/0.65/0.45) is a hand-picked number, not a calibrated confidence.
- V1 **"validated"** thresholds means "came from NWPS"; V2 separates `source_kind` from
  `quality`.
- V1 **"basin_group"** is a UI filter key, not a hydrologic basin polygon.
- V1 **"thresholds_unavailable"** for Green/White was a parser bug (NWPS defines those
  categories by *flow*, not stage) — see `docs/V1_AUDIT.md` §4.

## How to walk this folder

- Backend domain logic: `backend/lib/*.py` (≈1,300 lines). Start at `orchestrator.py`.
- Frontend domain components: `frontend/src/components/cascade/*.js`; everything under
  `frontend/src/components/ui/` is generated shadcn boilerplate (44 files, ~6 used).
- Design IP: `design_guidelines.md` (JSON): tokens, risk-state mapping table, motion timings.
- Claims vs evidence: `test_reports/*.json` + `.emergent/summary.txt` are agent self-reports;
  `backend_test.py` is a live-endpoint script against a now-dead preview URL.
