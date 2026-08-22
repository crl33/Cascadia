# ADR-0012: Repository strategy — V1 preserved under `v1/`, V2 at the root, one repository

- Status: Accepted
- Date: 2026-08-22

## Context
`crl33/Cascadia` was an empty repository; the prototype lived in the private `crl33/cascade-oracle`. The brief requires preserving V1 for comparison while starting V2 cleanly.

## Decision
`Cascadia` hosts V2 at the root (ICM-structured) and the V1 prototype verbatim under `v1/` (excluding its `.git` and Emergent `.gitconfig`), marked read-only by `v1/CONTEXT.md`. No code is ported by copy; ideas are ported via `docs/V1_AUDIT.md`. The private `cascade-oracle` repository remains the immutable original.

## Alternatives considered
- A `v2` branch in the prototype repo — hides V2 behind a branch and keeps Emergent scaffolding at the root.
- Separate repositories — loses side-by-side comparison and shared docs.

## Consequences
`v1/` adds ~110 files of reference material; CI excludes it from lint/test. When V2 reaches Phase 2, `v1/` may be moved to a tag and removed from the working tree by a later ADR.
