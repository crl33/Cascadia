# Cascadia Papsukkal

A hydrologic intelligence platform for Washington State watersheds — continuous ingestion of
authoritative observations and forecasts, basin-centric state estimation, explainable and
provenance-carrying intelligence, and a cinematic geospatial interface in which the world is
the interface.

Start at [`CLAUDE.md`](CLAUDE.md) (routing) and [`docs/CONTEXT.md`](docs/CONTEXT.md)
(reading order). The V1 prototype is preserved read-only under [`v1/`](v1/CONTEXT.md); its
audit is [`docs/V1_AUDIT.md`](docs/V1_AUDIT.md).

Cascadia Papsukkal is not an official emergency-alert authority. Official warnings and forecasts
come from the National Weather Service and local emergency management; this platform
synthesizes and explains, and labels every value with its source and freshness.

The web spike is at [cascadia.papsukkal.com](https://cascadia.papsukkal.com). Pushes to `main`
on this repo auto-deploy there via Cloudflare Pages (fixture-backed API; see `infra/CONTEXT.md`).
