from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest
from sqlalchemy import text


pytestmark = pytest.mark.anyio


@pytest.mark.unit
async def test_transaction_rolls_back_on_error(db_session):
    """AsyncSession.begin rolls back changes when an exception is raised."""
    try:
        async with db_session.begin():
            await db_session.execute(
                text("INSERT INTO paths (name, description) VALUES (:name, :description)"),
                {"name": "TxTest", "description": "desc"},
            )
            raise RuntimeError("boom")
    except RuntimeError:
        pass

    result = await db_session.execute(text("SELECT 1 FROM paths WHERE name = :name"), {"name": "TxTest"})
    assert result.first() is None


@asynccontextmanager
async def _request_scoped_session(sessionmaker) -> AsyncIterator:
    """Mirror request-boundary commit/rollback behavior in a loop-safe way."""
    async with sessionmaker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest.mark.unit
async def test_request_session_dependency_commits_on_success(sessionmaker):
    """Request-scoped session pattern commits writes on successful exit."""
    async with _request_scoped_session(sessionmaker) as session:
        await session.execute(
            text("INSERT INTO paths (name, description) VALUES (:name, :description)"),
            {"name": "ReqTxCommit", "description": "desc"},
        )

    async with sessionmaker() as verify:
        result = await verify.execute(text("SELECT 1 FROM paths WHERE name = :name"), {"name": "ReqTxCommit"})
        assert result.first() is not None


@pytest.mark.unit
async def test_request_session_dependency_rolls_back_on_error(sessionmaker):
    """Request-scoped session pattern rolls back writes on raised errors."""
    with pytest.raises(RuntimeError):
        async with _request_scoped_session(sessionmaker) as session:
            await session.execute(
                text("INSERT INTO paths (name, description) VALUES (:name, :description)"),
                {"name": "ReqTxRollback", "description": "desc"},
            )
            raise RuntimeError("boom")

    async with sessionmaker() as verify:
        result = await verify.execute(text("SELECT 1 FROM paths WHERE name = :name"), {"name": "ReqTxRollback"})
        assert result.first() is None
