# Cascadia Papsukkal

A hydrologic intelligence platform for Washington State watersheds: continuous ingestion of
authoritative observations and forecasts → basin-centric state estimation → explainable,
provenance-carrying intelligence → a cinematic geospatial interface. What leaves this
workspace is *credible basin intelligence*, never a fabricated certainty.

Built on ICM: folders carry sequencing, hierarchy carries context, files carry state. If
something needs explaining, it goes in that folder's `CONTEXT.md`, not in anyone's head.

## Where things live

| Folder | What it holds |
|---|---|
| `docs/` | the factory: doctrine, architecture, domain model, data sources, testing, roadmaps (stable reference) |
| `docs/adr/` | Architecture Decision Records — settled decisions, one file each |
| `docs/research/` | provider/stack research evidence behind `DATA_SOURCES.md` (dated, cited) |
| `v1/` | the Emergent-generated prototype, read-only historical reference (`v1/CONTEXT.md`) |
| `apps/` | deployable units: `api/`, `worker/`, `web/` (created when a phase starts, not before) |
| `packages/` | Python domain packages (`contracts`, `hydrology`, `geo`, `providers/*`, `visualization`) |
| `tests/` | `fixtures/` (saved provider payloads), `unit/`, `integration/`, `e2e/`, `canaries/` |
| `infra/` | containers, compose, migrations tooling, deployment notes |
| `.claude/skills/` | `icm-architect`, `vibesec`, `react-quality` — load before structuring, securing, or writing React |

## Route by task

| If you are… | Go to | Then stop at |
|---|---|---|
| new to the project | `docs/V2_ASSESSMENT.md` | you can say what V1 was and what V2 is |
| orienting on the science | `docs/HYDROLOGY.md` → `docs/DATA_DOCTRINE.md` | you can state the three risk surfaces |
| changing data model / storage | `docs/DOMAIN_MODEL.md` → `docs/adr/` | an ADR exists or is proposed |
| adding a provider | `docs/DATA_SOURCES.md` → `packages/providers/CONTEXT.md` | fixture tests + canary exist |
| touching the renderer | `docs/CINEMATIC_ARCHITECTURE.md` → `docs/VISUALIZATION_CONTRACTS.md` | no Cesium type leaks upstream |
| writing tests | `docs/TESTING.md` | deterministic; no live weather dependence |
| asked "what is next" | `docs/NEXT_STEPS.md` then `docs/ROADMAP.md`, `docs/CINEMATIC_ROADMAP.md` | the next milestone and its exit test |
| asked about V1 | `docs/V1_AUDIT.md` → `v1/CONTEXT.md` | preserve knowledge, not debt |
| hindcasting / December 2025 | `docs/EVENT_ZERO.md` → `docs/HYDROLOGY.md` §12 | every input has a knowledge time |
| checking what the spike proved | `docs/research/spike-report-2026-08-22.md` | invariants list all checked |
| restructuring folders | `.claude/skills/icm-architect/SKILL.md` | walk test passes |
| security review | `.claude/skills/vibesec/SKILL.md` + its addendum | checklist complete |
| React / frontend work | `.claude/skills/react-quality/SKILL.md` | doctor score not lower |

## The one rule

Every displayed number answers: where did it come from, when, from which version, how stale,
what transformed it. UNKNOWN is a legitimate state; fabrication is not.
