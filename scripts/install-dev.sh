#!/usr/bin/env bash
# Install every Cascadia Papsukkal Python package editable into the repo virtualenv, in dependency order.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIP="$ROOT/.venv/bin/pip"
[ -x "$PIP" ] || { echo "missing $ROOT/.venv (python -m venv .venv first)"; exit 1; }
for pkg in packages/contracts packages/core packages/geo packages/hydrology packages/providers/usgs packages/providers/nwps packages/providers/awdb packages/providers/nbm packages/providers/mrms packages/providers/wpc packages/providers/snodas apps/api; do
  "$PIP" install -q -e "$ROOT/$pkg"
done
# The worker carries the GRIB2 extra (eccodes) the NBM forcing jobs need; the API never does.
"$PIP" install -q -e "$ROOT/apps/worker[grib]"
"$PIP" install -q -e "$ROOT[dev]"
echo "installed: contracts core geo hydrology providers/usgs providers/nwps providers/awdb providers/nbm providers/mrms providers/wpc providers/snodas api worker (+dev tools incl. import-linter, alembic — run \`.venv/bin/lint-imports\` for the architecture contracts)"
