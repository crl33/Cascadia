"""cascade_api — read-only FastAPI for the spike API spec.

Owns: the app factory (CORS allowlist, security headers, OpenAPI), the routes, and the static
geography loader. Every value read goes through `as_known_at(session, as_of)`; envelopes are
built by cascade_hydrology.assemble with cascade_contracts models. There is no code path that
calls a provider and no mutating endpoint.
"""
