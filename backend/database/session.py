from __future__ import annotations

import os
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncEngine, AsyncSession, create_async_engine


def _database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL is required (e.g. postgresql+asyncpg://user:pass@host:5432/db)")
    return url


def create_engine() -> AsyncEngine:
    """Create the async SQLAlchemy engine."""
    return create_async_engine(_database_url(), pool_pre_ping=True)


engine = create_engine()
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields a per-request AsyncSession."""
    async with SessionLocal() as session:
        yield session
