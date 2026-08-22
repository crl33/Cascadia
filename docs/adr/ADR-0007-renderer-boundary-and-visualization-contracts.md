# ADR-0007: The renderer consumes semantic visualization contracts only

- Status: Accepted
- Date: 2026-08-22

## Context
Cinematic ambition must not leak renderer concepts into the science, nor science into the renderer. Multiple clients (web, later Unreal) and historical replay require the same contracts.

## Decision
`packages/visualization` emits the contracts in `docs/VISUALIZATION_CONTRACTS.md`: stable ids, semantic states, time, provenance refs, confidence labels, optional display ranges. No colours, materials, shaders, CSS, or camera instructions. Presentation mapping lives in `apps/web/src/layers/*/style.ts`. The client computes no hydrologic quantity. Camera changes never trigger scientific recomputation. A rendering failure cannot corrupt scientific data (the client is read-only).

## Consequences
A second renderer can be built without touching hydrology; visual regression tests use fixture contracts; provenance is guaranteed by schema. Cost: two mapping layers (semantic → presentation) to maintain, which is the point.
