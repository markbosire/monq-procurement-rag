"""Database engine, session factory, and migration utilities.

Provides a lazy-initialised SQLAlchemy engine, a FastAPI-compatible session
dependency, a context manager for transactional blocks, and simple schema
migration helpers for adding columns to existing tables.
"""

from contextlib import contextmanager
from functools import lru_cache
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings


@lru_cache(maxsize=1)
def _get_engine():
    connect_args = {"check_same_thread": False}
    poolclass = None
    if "memory" in settings.database_url:
        poolclass = StaticPool
    engine = create_engine(
        settings.database_url,
        connect_args=connect_args,
        poolclass=poolclass,
    )
    return engine


def get_engine():
    """Return the cached SQLAlchemy engine instance."""
    return _get_engine()


def _clear_engine_cache():
    _get_engine.cache_clear()


def _migrate_column(conn, table: str, column: str, col_type: str = "TEXT"):
    result = conn.execute(
        text(f"SELECT COUNT(*) FROM pragma_table_info('{table}') WHERE name='{column}'")
    )
    if result.scalar() == 0:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))


def _run_migrations():
    engine = get_engine()
    with engine.connect() as conn:
        _migrate_column(conn, "chat_messages", "source_chunks")
        _migrate_column(conn, "documents", "title")
        _migrate_column(conn, "documents", "summary")
        _migrate_column(conn, "documents", "extractions")
        conn.commit()


def init_db():
    """Create all tables and run any pending column migrations."""
    from app.db.models import Base
    Base.metadata.create_all(bind=get_engine())
    _run_migrations()


def get_db():
    """FastAPI dependency that yields a database session and closes it on teardown."""
    SessionLocal = sessionmaker(bind=get_engine(), autocommit=False, autoflush=False)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def transaction(db: Session):
    """Context manager that commits the transaction or rolls back on exception.

    Args:
        db: The active SQLAlchemy session.

    Yields:
        None.

    Raises:
        Exception: Re-raises the original exception after rolling back.
    """
    try:
        yield
        db.commit()
    except Exception:
        db.rollback()
        raise