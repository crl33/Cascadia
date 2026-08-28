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

# Worker-only extras installed into this image. The image is one artifact run in two modes
# (api | worker), and on Railway a single supervised container runs both, so the worker's
# GRIB2 stack has to be here. Build with --build-arg WORKER_EXTRAS= to get an API-only image
# without eccodes/eccodeslib/eckitlib (~94 MB) — p3-surfaces-design §4 item 7, §8.
ARG WORKER_EXTRAS=grib

# --- layer 1: third-party dependencies (changes rarely) ----------------------
COPY packages/contracts/pyproject.toml packages/contracts/pyproject.toml
COPY packages/core/pyproject.toml packages/core/pyproject.toml
COPY packages/geo/pyproject.toml packages/geo/pyproject.toml
COPY packages/hydrology/pyproject.toml packages/hydrology/pyproject.toml
COPY packages/providers/usgs/pyproject.toml packages/providers/usgs/pyproject.toml
COPY packages/providers/nwps/pyproject.toml packages/providers/nwps/pyproject.toml
COPY packages/providers/nbm/pyproject.toml packages/providers/nbm/pyproject.toml
COPY packages/providers/mrms/pyproject.toml packages/providers/mrms/pyproject.toml
COPY packages/providers/awdb/pyproject.toml packages/providers/awdb/pyproject.toml
COPY apps/api/pyproject.toml apps/api/pyproject.toml
COPY apps/worker/pyproject.toml apps/worker/pyproject.toml

# Collect every third-party requirement the local packages declare; the
# cascade-* names are satisfied by the local installs in layer 2.
RUN python - <<'PY' > /tmp/requirements-thirdparty.txt
import os
import tomllib
from pathlib import Path

paths = [
    "packages/contracts/pyproject.toml",
    "packages/core/pyproject.toml",
    "packages/geo/pyproject.toml",
    "packages/hydrology/pyproject.toml",
    "packages/providers/usgs/pyproject.toml",
    "packages/providers/nwps/pyproject.toml",
    "packages/providers/nbm/pyproject.toml",
    "packages/providers/mrms/pyproject.toml",
    "packages/providers/awdb/pyproject.toml",
    "apps/api/pyproject.toml",
    "apps/worker/pyproject.toml",
]
deps = set()
for p in paths:
    project = tomllib.loads(Path(p).read_text())["project"]
    declared = list(project["dependencies"])
    # Worker extras (WORKER_EXTRAS build arg) join the cacheable dependency layer so a source
    # edit never re-downloads the GRIB2 stack. Only the worker declares optional groups.
    if p == "apps/worker/pyproject.toml":
        optional = project.get("optional-dependencies", {})
        for extra in filter(None, os.environ.get("WORKER_EXTRAS", "").split(",")):
            declared += optional[extra]
    for dep in declared:
        if not dep.lower().replace("_", "-").startswith("cascade-"):
            deps.add(dep)
print("\n".join(sorted(deps)))
PY

# Everything the runtime needs is declared by the pyprojects above — no
# Dockerfile-only pins (dedrift 2026-08-24): psycopg[binary,pool] and obstore
# live in cascade-core, procrastinate in cascade-worker, geoalchemy2 in
# cascade-core. alembic is intentionally absent: migrations run from a repo
# checkout (scripts/migrate.sh), never from this image.
RUN pip install -r /tmp/requirements-thirdparty.txt

# --- layer 2: local sources + hash-free simple installs ----------------------
COPY packages/ packages/
COPY apps/api/ apps/api/
COPY apps/worker/ apps/worker/
RUN pip install \
    ./packages/contracts \
    ./packages/core \
    ./packages/geo \
    ./packages/hydrology \
    ./packages/providers/usgs \
    ./packages/providers/nwps \
    ./packages/providers/nbm \
    ./packages/providers/mrms \
    ./packages/providers/awdb \
    ./apps/api \
    "./apps/worker${WORKER_EXTRAS:+[$WORKER_EXTRAS]}"

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

# api/all modes: probe /system/health on ${PORT:-8000}; worker and one-shot modes:
# the probe reads /tmp/cascade-run-mode and exits 0 (nothing to probe).
HEALTHCHECK --interval=30s --timeout=6s --start-period=15s --retries=3 \
    CMD ["python", "/usr/local/bin/container-healthcheck.py"]

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["api"]
