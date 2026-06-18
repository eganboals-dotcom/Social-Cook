"""Database engine, session, and declarative base.

DB-touching endpoints use sync SQLAlchemy via the `get_db` dependency (FastAPI
runs sync handlers in a threadpool). The async `/extract` endpoint does no DB
work, so the two styles don't collide.
"""
from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    """Base class for all ORM models."""


# Engine construction is lazy — no connection is opened until first use.
engine = create_engine(get_settings().database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a request-scoped session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
