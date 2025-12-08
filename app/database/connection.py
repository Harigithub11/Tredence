"""Database Connection Management

Provides async database session management with connection pooling.
Uses SQLAlchemy 2.0 async API with asyncpg driver.
"""

from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.pool import NullPool

from app.config import settings
from app.database.models import Base


# Global engine instance
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """
    Get or create the global async database engine.

    Returns:
        AsyncEngine instance

    Note:
        Engine is created once and reused throughout the application.
    """
    global _engine

    if _engine is None:
        # Configure engine based on database type
        engine_kwargs = {
            "echo": settings.DEBUG,  # Log SQL queries in debug mode
            "future": True,  # Use SQLAlchemy 2.0 API
        }

        # For SQLite (testing), use NullPool
        # For PostgreSQL (production), use default async pool
        if "sqlite" in settings.DATABASE_URL:
            engine_kwargs["poolclass"] = NullPool
        else:
            # For PostgreSQL with async, use AsyncAdaptedQueuePool (default)
            engine_kwargs["pool_pre_ping"] = True
            engine_kwargs["pool_size"] = 5
            engine_kwargs["max_overflow"] = 10

        _engine = create_async_engine(
            settings.DATABASE_URL,
            **engine_kwargs
        )

    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Get or create the session factory.

    Returns:
        async_sessionmaker for creating sessions

    Note:
        Session factory is created once and reused throughout the application.
    """
    global _session_factory

    if _session_factory is None:
        engine = get_engine()
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,  # Don't expire objects after commit
            autocommit=False,
            autoflush=False,
        )

    return _session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database sessions in FastAPI.

    Yields:
        AsyncSession instance

    Usage:
        @app.get("/items")
        async def get_items(session: AsyncSession = Depends(get_session)):
            # Use session here
            pass
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_session_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for getting database sessions.

    Yields:
        AsyncSession instance

    Usage:
        async with get_session_context() as session:
            # Use session here
            await session.commit()
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database by creating all tables.

    This creates all tables defined in models.
    Use Alembic migrations in production.

    Note:
        Only use this for testing or initial setup.
        In production, use Alembic migrations.
    """
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    """
    Drop all tables from the database.

    Warning:
        This is destructive and should only be used in testing.
    """
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def close_db() -> None:
    """
    Close database connections and dispose of the engine.

    Call this when shutting down the application.
    """
    global _engine, _session_factory

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None


# Utility function for health checks
async def check_database_connection() -> bool:
    """
    Check if database connection is healthy.

    Returns:
        True if connection is healthy, False otherwise
    """
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception:
        return False
