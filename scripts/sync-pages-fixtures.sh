#!/usr/bin/env bash
# Copy committed stub fixtures into functions/fixtures so the Pages Function can
# import JSON without node:fs. Source of truth remains tests/fixtures and packages/contracts.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
dest="$root/functions/fixtures"
mkdir -p "$dest"
cp "$root/tests/fixtures/geo/basins_seed_basin_lod.geojson" "$dest/basins_seed_basin_lod.json"
cp "$root/tests/fixtures/geo/basins_seed_state_lod.geojson" "$dest/basins_seed_state_lod.json"
cp "$root/packages/contracts/fixtures/viz_basins_envelope.json" "$dest/viz_basins_envelope.json"
cp "$root/packages/contracts/fixtures/river_mvew1_envelope.json" "$dest/river_mvew1_envelope.json"
cp "$root/apps/web/dev/fixtures/mvew1-samples.json" "$dest/mvew1-samples.json"
gunzip -c "$root/tests/fixtures/geo/river_network.json.gz" > "$dest/river_network.json"
cp "$root/packages/contracts/fixtures/field_precip_observed.json" "$dest/field_precip_observed.json"
echo "synced Pages Function fixtures → functions/fixtures"
