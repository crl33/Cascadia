---
name: react-quality
description: React engineering quality gate for Cascadia Papsukkal's web app (React + TypeScript + Vite + CesiumJS). Combines React Doctor (static health score and fix recipes), React Scan (runtime re-render detection), and Context7 (current library docs instead of stale training data). Use when writing, reviewing, profiling, or cleaning up any React/TypeScript code under apps/web, before committing frontend changes, when a UI feels slow, when adding a library API call, or when the user says "doctor", "scan renders", "react audit", "use context7", or "check the docs".
---

# React quality for Cascadia Papsukkal

Three tools, one rule each. Run them in this order when touching `apps/web`.

| Tool | Question it answers | Command |
|---|---|---|
| **Context7** | "What is the *current* API of this library?" | `npx ctx7@latest library <name> "<query>"` → `npx ctx7@latest docs <id> "<query>"` |
| **React Doctor** | "Is this code structurally sound?" (0–100 score) | `npx react-doctor@latest --verbose --scope changed` |
| **React Scan** | "Does it re-render when it shouldn't?" (runtime) | dev-only script/plugin, see [references/tooling.md](references/tooling.md) |

Upstream sources (vendored knowledge, not code): [react-doctor](https://github.com/millionco/react-doctor),
[react-scan](https://github.com/aidenybai/react-scan), [context7](https://github.com/upstash/context7).

## 1. Before writing library code: retrieve, don't recall

Your training data for CesiumJS, React 19, Vite, TanStack Query, Zustand, Zod and Vitest is
likely stale. For any API signature, config option, or "how do I" question:

1. `npx ctx7@latest library "CesiumJS" "<what you need>"` — pick the ID (`/org/project`), prefer
   official sources, version-specific IDs when a version is pinned in `package.json`.
2. `npx ctx7@latest docs /<org>/<project> "<one concept per query>"`.
3. At most 3 commands per question; if quota is exhausted say so and flag the answer as
   from memory. Never put secrets in queries.

Library IDs used in this repo are cached in [references/tooling.md](references/tooling.md).

## 2. After writing React code: run the doctor, keep the score

```bash
npx react-doctor@latest --verbose --scope changed
```

- The score must not regress versus `main`. Fix errors first, then warnings.
- When a finding maps to a rule, fetch the canonical recipe rather than improvising:
  `https://www.react.doctor/prompts/rules/<plugin>/<rule>.md`
  (or `npx react-doctor@latest rules explain <rule>`).
- A deliberate `// eslint-disable-next-line react-doctor/...` with a reason is a settled
  decision — respect it, do not re-litigate.
- For a whole-codebase improvement roadmap (read-only, plans only), follow the audit →
  vet → plan workflow in [references/audit-workflow.md](references/audit-workflow.md).
- `npx react-doctor@latest design --verbose` runs the focused UI/a11y/motion rules; use it
  before shipping panel or label changes (contrast on dark glass, reduced-motion, focus).

## 3. When something feels slow: measure renders, don't guess

- Dev only: React Scan highlights components that re-render. Enable it via the Vite plugin
  or the `<script>` tag described in [references/tooling.md](references/tooling.md). It
  must never ship to production (`dangerouslyForceRunInProduction` stays false).
- For a measured before/after, record a trace:
  `npx react-doctor@latest scan http://localhost:5173 --format json`
  and report in the structure: flow tested → verdict → evidence table → findings → limits.
- A high render count is evidence, not a verdict. Pair it with duration and user impact.
  Severity follows the hot path: anything touched per camera frame, per timeline tick, or
  per list row outranks a settings panel.

## 4. Cascadia Papsukkal–specific rules (the scanner cannot see these)

The renderer boundary is architecture, not style. Details and examples in
[references/cesium-react-boundary.md](references/cesium-react-boundary.md).

- **React orchestrates; Cesium renders.** No React state update may occur per animation
  frame or per camera move event. Camera, entities, primitives, shaders and the scene clock
  are owned by non-React controller modules (`scene/`, `camera/`, `layers/`) that expose
  imperative APIs and coarse-grained subscriptions.
- **No Cesium types in application state.** Zustand/TanStack stores hold semantic state
  (`selectedEntityId`, `time`, `activeLayers`, `qualityTier`), never `Cesium.Entity`,
  `Cartesian3`, or materials. A `useEffect` bridges state → controller, not the reverse.
- **No science in components.** Trend, anomaly, headroom, susceptibility, disagreement and
  "why" text come from backend contracts (`packages/contracts`). A component that computes a
  hydrologic quantity from raw series is a defect (V1 computed a 24 h stage trend in
  `RiverGaugeCard`).
- **Provenance is mandatory UI.** Every rendered scientific value shows its `source_kind`
  badge (OBSERVED / OFFICIAL FORECAST / MODELED / DERIVED / EXPERIMENTAL / UNKNOWN) and
  freshness. A value without provenance in props is a type error, not a prop default.
- **Centralized data orchestration.** Queries are keyed by (entity, time, layer set, camera
  extent band) in one query layer; components never fetch directly (V1's `FilterBar` fetched
  with raw axios on mount).
- **Reduced motion is a first-class path.** Every flight/transition has a non-animated
  equivalent gated on `prefers-reduced-motion` and the user setting.
- **Contracts are generated, not hand-typed.** Frontend types derive from the backend
  OpenAPI/JSON Schema; a drift check runs in CI.

## 5. Code conventions (adopted from react-doctor / react-scan maintainers, adapted)

- TypeScript `interface` over `type` for object shapes; no `as` casts unless unavoidable
  (and then commented with why); `Boolean(x)` over `!!x`.
- Files kebab-case; components PascalCase exports; one utility per file under `utils/`.
- Magic numbers live in `constants.ts` with unit suffixes (`_MS`, `_PX`, `_M`, `_KM`).
- Descriptive names (`didCameraSettle`, not `moved`); no 1–2 character identifiers.
- Comments only for the non-obvious "why"; hacks prefixed `// HACK: <reason>`.
- Effects: derived state is `useMemo`, user intent is an event handler, external-system
  bridges are single-purpose effects with cleanup. Never mirror one state into another.
- `data-testid` in kebab-case on interactive and key informational elements (kept from V1).

## 6. Pre-commit checklist

- [ ] Context7 consulted for any new library API used.
- [ ] `npx react-doctor@latest --scope changed` — no new errors, score not lower.
- [ ] Typecheck, lint, unit tests pass; contract types regenerated if backend changed.
- [ ] No Cesium type leaked into stores/props; no per-frame React state.
- [ ] Provenance badge + freshness present on every new scientific value.
- [ ] Reduced-motion path exists for any new animation.
