from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession


@asynccontextmanager
async def session_scope(session: AsyncSession) -> AsyncIterator[None]:
    """Open a transaction only when one is not already active."""
    if session.in_transaction():
        yield
        return
    async with session.begin():
        yield
