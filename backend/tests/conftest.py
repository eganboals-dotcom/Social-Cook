"""Shared test fixtures.

DB-backed tests use an in-memory SQLite database (one shared connection via
StaticPool) with the schema created from the ORM metadata, and the `get_db`
dependency overridden to use it. Rate limiting is disabled so repeated auth
calls across tests don't trip 429s.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  -- register models on Base.metadata
from app.db import Base, get_db
from app.main import app
from app.rate_limit import limiter


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    TestingSession = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, future=True
    )
    Base.metadata.create_all(engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    limiter.enabled = False
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        limiter.enabled = True
        Base.metadata.drop_all(engine)
