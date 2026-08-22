"""cascade_core — the shared spine under every other package.

Owns: settings (env), the async SQLAlchemy engine/session, the ORM models for
docs/DOMAIN_MODEL.md §2 at spike scope, the content-addressed object store, time utilities,
unit conversion, freshness computation, the archiving HTTP fetcher every provider uses, and
`as_known_at` — the only permitted knowledge-time read path (ADR-0010). No science here.
"""
