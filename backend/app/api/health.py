"""Health and readiness endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/")
def root() -> dict[str, str]:
    return {"service": get_settings().app_name, "status": "ok"}


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness probe. Extend with a DB connectivity check in Phase 2."""
    return {"status": "ok"}
