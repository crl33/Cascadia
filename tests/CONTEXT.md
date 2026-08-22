# tests/ — what counts as tested

Layout mirrors `docs/TESTING.md`: `fixtures/` (captured provider payloads + manifests),
`unit/`, `integration/` (testcontainers PostGIS/MinIO), `e2e/` (Playwright, fixed clock),
`canaries/` (scheduled live checks; never block CI). A feature without tests at the levels
`docs/TESTING.md` §10 requires is untested, whatever a report says.
