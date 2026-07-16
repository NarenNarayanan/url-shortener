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

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import Click, URL, User  # noqa: F401  (registers tables on Base.metadata)

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/urlshortener_test"
)

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(scope="session", autouse=True)
def create_schema():
    """create_all is idempotent (checks for existing tables), so this is safe to run every session."""
    Base.metadata.create_all(bind=engine)
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
