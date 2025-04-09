from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from app.core.config import settings
from contextlib import contextmanager
from typing import Generator


# Create engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_pre_ping=True,  # Enable connection health checks
    echo=False  # Set to True for SQL query logging
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    Ensures proper session cleanup and connection return to pool.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_session() -> Session:
    """
    Dependency for FastAPI route handlers.
    Returns a database session that will be automatically closed.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 