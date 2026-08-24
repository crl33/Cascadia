#!/usr/bin/env bash
# Install every Cascadia Papsukkal Python package editable into the repo virtualenv, in dependency order.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIP="$ROOT/.venv/bin/pip"
[ -x "$PIP" ] || { echo "missing $ROOT/.venv (python -m venv .venv first)"; exit 1; }
for pkg in packages/contracts packages/core packages/providers/usgs packages/providers/nwps packages/hydrology apps/api apps/worker; do
  "$PIP" install -q -e "$ROOT/$pkg"
done
"$PIP" install -q -e "$ROOT[dev]"
echo "installed: contracts core providers/usgs providers/nwps hydrology api worker (+dev tools incl. import-linter, alembic — run \`.venv/bin/lint-imports\` for the architecture contracts)"
