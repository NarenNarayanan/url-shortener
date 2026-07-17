"""
Database connectivity: engine, session factory, declarative base.

Design note: we use SQLAlchemy's classic Session (not the async engine) for now.
FastAPI is async-capable, but sync SQLAlchemy + a small connection pool is simpler
to reason about, easier to debug, and plenty fast at this project's scale. If this
were built for high-concurrency production traffic, migrating to `asyncpg` +
SQLAlchemy's async session would be the next optimization — not needed yet.
"""
from collections.abc import Generator

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # detects stale/dropped connections before using them
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# Explicit naming convention for constraints/indexes. Without this, Postgres
# auto-generates constraint names, and Alembic's autogenerate can't produce a
# reliable migration to ALTER/DROP a constraint later because it doesn't know
# its own name. This must be set up before the first migration is written.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base class every ORM model inherits from."""
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a DB session per request and guarantees
    it's closed afterward, even if the request raises.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session_factory() -> sessionmaker:
    """
    Returns the session factory itself, not a session — for code that needs
    to open its OWN session independent of the current request, such as a
    BackgroundTask that runs after get_db has already closed the request's
    session. Injectable (like get_db) so tests can point it at the test
    database/connection instead of the real one.
    """
    return SessionLocal
