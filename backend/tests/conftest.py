"""
Test fixtures.

We test against a real Postgres database (see backend/db/init/ for how the
`urlshortener_test` database gets created), not SQLite — a couple of our
columns (INET on Click) are Postgres-specific, and in general it's better to
catch Postgres behavior differences in tests than in Docker.

Each test gets its own transaction that's rolled back afterward, using the
SAVEPOINT pattern below. This matters because our service layer calls
db.commit() as part of normal operation (e.g. register_user) — a plain
connection-level rollback wouldn't undo a commit that already happened.
Re-opening a SAVEPOINT after every commit means the outer transaction is
never actually finalized, so the final rollback undoes everything regardless
of how many times the code under test committed.
"""
import os

# Must happen before any `app.*` module is imported: app.config reads
# REDIS_URL into `settings` once, at import time, and app.rate_limit /
# app.cache build their Redis clients off that same `settings` object.
# Redis DB 1 (vs. the app's normal DB 0) keeps test rate-limit counters and
# cache entries fully separate from whatever's running under `docker
# compose up` — same idea as TEST_DATABASE_URL below, just for Redis.
os.environ["REDIS_URL"] = os.getenv("TEST_REDIS_URL", "redis://redis:6379/1")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.cache import redis_client
from app.database import Base, get_db
from app.main import app
from app.models import Click, URL, User  # noqa: F401  (registers tables on Base.metadata)
from app.rate_limit import limiter

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/urlshortener_test"
)

# Rate limiting is disabled by default for the suite: our tests call
# /register and /login far more times per run than a real user ever would
# (e.g. `_register_and_login` helpers in test_urls.py), and production-
# strength limits would make most of the existing tests flaky. One test
# (test_rate_limit.py) re-enables it to actually prove the limiting works.
limiter.enabled = False

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(scope="session", autouse=True)
def create_schema():
    """create_all is idempotent (checks for existing tables), so this is safe to run every session."""
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(scope="session", autouse=True)
def flush_test_redis():
    """
    Redis DB 1 is dedicated to tests (see REDIS_URL override above), so
    wiping it at the start of every session is safe and keeps rate-limit
    counters and cache entries from a previous run bleeding into this one —
    the same "run the suite as many times as you want" guarantee the
    Postgres per-test rollback gives us, just via a full flush instead.
    """
    redis_client.flushdb()
    yield


@pytest.fixture()
def db_session():
    connection = engine.connect()
    outer_transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    session.close()
    outer_transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
