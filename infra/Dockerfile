# Cascadia Papsukkal — single backend image, two run modes (api | worker),
# selected by the container command via infra/docker-entrypoint.sh.
# Build from the REPO ROOT:   docker build -f infra/Dockerfile .
# Layering is deliberately boring and cacheable: pyprojects first (third-party
# dependency layer survives source edits), sources after.

FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_ROOT_USER_ACTION=ignore

WORKDIR /app

# --- layer 1: third-party dependencies (changes rarely) ----------------------
COPY packages/contracts/pyproject.toml packages/contracts/pyproject.toml
COPY packages/core/pyproject.toml packages/core/pyproject.toml
COPY packages/hydrology/pyproject.toml packages/hydrology/pyproject.toml
COPY packages/providers/usgs/pyproject.toml packages/providers/usgs/pyproject.toml
COPY packages/providers/nwps/pyproject.toml packages/providers/nwps/pyproject.toml
COPY apps/api/pyproject.toml apps/api/pyproject.toml
COPY apps/worker/pyproject.toml apps/worker/pyproject.toml

# Collect every third-party requirement the local packages declare; the
# cascade-* names are satisfied by the local installs in layer 2.
RUN python - <<'PY' > /tmp/requirements-thirdparty.txt
import tomllib
from pathlib import Path

paths = [
    "packages/contracts/pyproject.toml",
    "packages/core/pyproject.toml",
    "packages/hydrology/pyproject.toml",
    "packages/providers/usgs/pyproject.toml",
    "packages/providers/nwps/pyproject.toml",
    "apps/api/pyproject.toml",
    "apps/worker/pyproject.toml",
]
deps = set()
for p in paths:
    for dep in tomllib.loads(Path(p).read_text())["project"]["dependencies"]:
        if not dep.lower().replace("_", "-").startswith("cascade-"):
            deps.add(dep)
print("\n".join(sorted(deps)))
PY

# Third-party deps + production-only runtime (PostgreSQL driver, job queue,
# object store, migrations). The second group is pinned here until the package
# pyprojects declare them (M2); keep the floors in sync with the repo venv.
RUN pip install -r /tmp/requirements-thirdparty.txt \
    "psycopg[binary,pool]>=3.2" \
    "procrastinate>=3.9" \
    "obstore>=0.11" \
    "geoalchemy2>=0.20" \
    "alembic>=1.19"

# --- layer 2: local sources + hash-free simple installs ----------------------
COPY packages/ packages/
COPY apps/api/ apps/api/
COPY apps/worker/ apps/worker/
RUN pip install \
    ./packages/contracts \
    ./packages/core \
    ./packages/providers/usgs \
    ./packages/providers/nwps \
    ./packages/hydrology \
    ./apps/api \
    ./apps/worker

# --- layer 3: runtime data, entrypoint, non-root -----------------------------
# Basin geography LOD fixtures: the API loads CASCADE_GEO_DIR at startup.
COPY tests/fixtures/geo/ tests/fixtures/geo/
COPY infra/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
COPY infra/container-healthcheck.py /usr/local/bin/container-healthcheck.py

RUN useradd --create-home --uid 10001 cascade \
    && chmod +x /usr/local/bin/docker-entrypoint.sh \
    && mkdir -p /app/data/raw \
    && chown -R cascade:cascade /app/data

USER cascade

ENV CASCADE_GEO_DIR=/app/tests/fixtures/geo \
    CASCADE_RAW_DIR=/app/data/raw

EXPOSE 8000

# api mode: probe /system/health on ${PORT:-8000}; worker and one-shot modes:
# the probe reads /tmp/cascade-run-mode and exits 0 (nothing to probe).
HEALTHCHECK --interval=30s --timeout=6s --start-period=15s --retries=3 \
    CMD ["python", "/usr/local/bin/container-healthcheck.py"]

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["api"]
