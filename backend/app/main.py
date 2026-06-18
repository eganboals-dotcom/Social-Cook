"""Social Cook API — FastAPI application entrypoint.

Phase 0 ships a runnable skeleton: app wiring, configuration, CORS, and a health
check. Feature routers (extraction, auth, recipes, monetization) are mounted in
later phases — the call-sites below mark where they go.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.auth import router as auth_router
from app.api.extract import router as extract_router
from app.api.health import router as health_router
from app.api.purchases import router as purchases_router
from app.api.recipes import router as recipes_router
from app.config import get_settings
from app.rate_limit import limiter


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        summary="Turn social cooking videos into clean, structured recipes.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiting for auth endpoints (slowapi).
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.include_router(health_router)
    app.include_router(extract_router)
    app.include_router(auth_router)
    app.include_router(recipes_router)
    app.include_router(purchases_router)

    return app


app = create_app()
