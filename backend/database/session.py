from __future__ import annotations

import os
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncEngine, AsyncSession, create_async_engine


def _database_url() -> str:
    """Read `DATABASE_URL` from the environment.

    Returns:
        Database URL string.

    Raises:
        RuntimeError: If `DATABASE_URL` is missing.
    """
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL is required (e.g. postgresql+asyncpg://user:pass@host:5432/db)")
    return url


_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def create_engine() -> AsyncEngine:
    """Create the async SQLAlchemy engine."""
    pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
    max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "1800"))
    return create_async_engine(
        _database_url(),
        pool_pre_ping=True,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=pool_recycle,
    )


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Return a cached AsyncSession factory.

    This is intentionally lazy to avoid importing-time failures in tooling/tests
    that don't set `DATABASE_URL` until later.
    """
    global _engine, _sessionmaker
    if _sessionmaker is None:
        _engine = create_engine()
        _sessionmaker = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    return _sessionmaker


def reset_sessionmaker() -> None:
    """Reset cached engine/sessionmaker (primarily for tests)."""
    global _engine, _sessionmaker
    _engine = None
    _sessionmaker = None


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields a per-request AsyncSession."""
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        yield session
