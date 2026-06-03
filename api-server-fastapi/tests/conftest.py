"""Shared test fixtures.

Tests run against an in-memory SQLite DB (no Docker/Postgres needed). We set
required env vars before importing the app, then override get_session to use a
single shared in-memory connection via StaticPool.
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel

import app.models  # noqa: F401 -- register all tables on SQLModel.metadata
from app.core.database import get_session
from app.core.security import create_access_token
from app.api.v1.deps import ACCESS_COOKIE
from app.main import app


@pytest.fixture(name="engine")
def engine_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session):
    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    yield TestClient(app)
    app.dependency_overrides.clear()


def make_user(session, *, email="student@post.bgu.ac.il", full_name="Test Student",
              org="BGU", provider="google", sub=None, onboarded=True):
    """Insert a user directly and return it."""
    from app.models.user import User
    import uuid
    user = User(
        email=email,
        full_name=full_name,
        org=org,
        auth_provider=provider,
        provider_sub=sub or str(uuid.uuid4()),
        onboarded=onboarded,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def auth_cookies(user):
    """Cookie dict that authenticates as the given user."""
    return {ACCESS_COOKIE: create_access_token(str(user.id))}
