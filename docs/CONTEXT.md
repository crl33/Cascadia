# docs/ — the factory

One job: hold the stable doctrine, architecture, and decisions that every implementation
step reads. Nothing here is per-run output. If practice and a doc disagree, reconcile the
same day — update the doc or the code, never let them drift.

## Reading order by role

| Role | Read, in order |
|---|---|
| everyone, once | `V2_ASSESSMENT.md`, `HYDROLOGY.md`, `DATA_DOCTRINE.md` |
| backend / data | `DOMAIN_MODEL.md`, `ARCHITECTURE.md`, `DATA_SOURCES.md`, `adr/` |
| frontend / visualization | `VISUAL_TRUTH_DOCTRINE.md`, `CINEMATIC_ARCHITECTURE.md`, `VISUALIZATION_CONTRACTS.md`, `SEMANTIC_ZOOM.md`, `CAMERA_SYSTEM.md`, `LAYER_SYSTEM.md`, `PERFORMANCE.md` |
| QA / science evaluation | `TESTING.md`, `HYDROLOGY.md` §12 (hindcasting), `EVENT_ZERO.md` |
| planning | `ROADMAP.md`, `CINEMATIC_ROADMAP.md` |
| auditing the prototype | `V1_AUDIT.md` |
| checking provider facts | `DATA_SOURCES.md` → `research/README.md` |

## Inputs / outputs

- Inputs (every run): the prompt doctrine (sections 2–27 of the founding brief), V1 knowledge
  (`V1_AUDIT.md`), dated research evidence in `research/`.
- Outputs: the canonical `.md` files listed above; ADRs in `adr/` (copy `adr/ADR-0000-template.md`).

## Human check

A reader with no context can state, from these docs alone: the three risk surfaces, the
provenance rule, the persistence split (PostGIS vs object storage), the renderer boundary, and
the next phase's exit criteria. If not, the docs — not the reader — are wrong.

## Conventions

- Claims are labeled **FACT** (verified, cited), **ASSUMPTION**, **INFERENCE**, or
  **OPEN QUESTION** when the distinction matters.
- Dates are absolute (ISO 8601, UTC unless a local time is the point).
- External facts cite a URL and the date retrieved; `research/*.json` holds the evidence.
- Diagrams are ASCII or Mermaid; no images that cannot be diffed.
