"""Social Cook API — FastAPI application entrypoint.

Phase 0 ships a runnable skeleton: app wiring, configuration, CORS, and a health
check. Feature routers (extraction, auth, recipes, monetization) are mounted in
later phases — the call-sites below mark where they go.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.config import get_settings


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

    app.include_router(health_router)

    # Routers added in later phases:
    #   Phase 1: extraction router  (POST /extract)
    #   Phase 2: auth + recipes routers
    #   Phase 5: purchases/webhook router
    return app


app = create_app()
