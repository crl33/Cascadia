"""App factory: CORS allowlist (no wildcard, no credentials), security headers on every response,
OpenAPI JSON at /openapi.json (the CDN-backed Swagger UI is disabled: no third-party scripts)."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncEngine

from cascade_api.geo import Geography
from cascade_api.routes import router
from cascade_core.db import make_engine, make_session_factory
from cascade_core.settings import Settings
from cascade_geo.hypsometry import HypsometryError, load_hypsometry


def create_app(settings: Settings | None = None, engine: AsyncEngine | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    engine = engine or make_engine(settings.db_url)
    app = FastAPI(title="Cascadia Papsukkal API (spike)", version="0.1.0", docs_url=None, redoc_url=None, openapi_url="/openapi.json")
    app.state.settings = settings
    app.state.engine = engine
    app.state.sessions = make_session_factory(engine)
    app.state.geo = Geography.load(settings.geo_dir)
    # The elevation-area curves ship in the same geo directory. Missing is tolerated — the
    # surface simply emits no rain-exposed fraction — but never silently: the absence of a whole
    # analytical input is worth one loud line at startup, not a quiet degradation.
    try:
        app.state.hypsometry = load_hypsometry(settings.geo_dir / "basin_hypsometry.json")
    except HypsometryError as e:
        logging.getLogger("cascade.api").warning("no hypsometry loaded: %s", e)
        app.state.hypsometry = None
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_credentials=False, allow_methods=["GET", "OPTIONS"], allow_headers=["*"], max_age=600)

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store"
        return response

    app.include_router(router)
    return app


app = create_app()
