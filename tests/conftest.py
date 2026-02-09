from __future__ import annotations

import os
from typing import AsyncIterator, Iterator

from alembic.config import Config
from httpx import ASGITransport, AsyncClient
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncEngine, AsyncSession, create_async_engine

from alembic import command
from backend.database.session import get_session as app_get_session


DEFAULT_DATABASE_URL = "postgresql+asyncpg://learning_platform:learning_platform@127.0.0.1:5432/learning_platform"

os.environ.setdefault("DATABASE_URL", DEFAULT_DATABASE_URL)
os.environ.setdefault("SESSION_DAYS", "30")
os.environ.setdefault("BOOTSTRAP_ADMIN_USERNAME", "admin")
os.environ.setdefault("BOOTSTRAP_ADMIN_PASSWORD", "admin")


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Configure pytest-anyio to use asyncio."""
    return "asyncio"


@pytest.fixture(scope="session")
def database_url() -> str:
    """Return the Postgres database URL for tests."""
    return (os.getenv("DATABASE_URL") or DEFAULT_DATABASE_URL).strip()


@pytest.fixture(scope="session")
def configure_test_env(database_url: str) -> Iterator[None]:
    """Set required env vars for backend settings and reset cached sessionmakers."""
    os.environ["DATABASE_URL"] = database_url
    os.environ.setdefault("SESSION_DAYS", "30")
    os.environ.setdefault("BOOTSTRAP_ADMIN_USERNAME", "admin")
    os.environ.setdefault("BOOTSTRAP_ADMIN_PASSWORD", "admin")

    # The backend caches its SQLAlchemy engine/sessionmaker; tests may set env vars
    # after import, so we reset the cache here to ensure `DATABASE_URL` is honored.
    from backend.database import session as db_session

    db_session.reset_sessionmaker()

    yield


@pytest.fixture(scope="session")
def apply_migrations(configure_test_env: None, database_url: str) -> Iterator[None]:
    """Ensure the schema is up-to-date for the test database.

    This fixture pins `DATABASE_URL` before running Alembic so migrations are
    applied to the same database the SQLAlchemy engine will connect to.
    """
    os.environ["DATABASE_URL"] = database_url
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(cfg, "head")
    yield


@pytest.fixture()
async def engine(database_url: str) -> AsyncIterator[AsyncEngine]:
    """Create a per-test async engine.

    Async drivers (asyncpg) bind connections to an event loop. pytest-anyio runs
    each test in its own loop by default, so we keep the engine function-scoped
    to avoid cross-loop pooled connections.
    """
    engine = create_async_engine(database_url, pool_pre_ping=True)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture()
def sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create an AsyncSession factory for unit-level tests."""
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture()
async def db_reset(
    apply_migrations: None,
    configure_test_env: None,
    engine: AsyncEngine,
) -> AsyncIterator[None]:
    """Keep DB-backed tests isolated by truncating all tables between tests."""
    async with engine.begin() as conn:
        result = await conn.execute(
            text(
                "SELECT table_schema, table_name "
                "FROM information_schema.tables "
                "WHERE table_type = 'BASE TABLE' "
                "AND table_schema NOT IN ('pg_catalog', 'information_schema') "
                "AND table_name != 'alembic_version' "
                "ORDER BY table_schema, table_name"
            )
        )
        tables = [(str(row[0]), str(row[1])) for row in result.all()]
        if tables:
            def _qi(identifier: str) -> str:
                return '"' + identifier.replace('"', '""') + '"'

            qualified = ", ".join(f"{_qi(schema)}.{_qi(name)}" for schema, name in tables)
            await conn.execute(text(f"TRUNCATE TABLE {qualified} RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture()
async def db_session(
    db_reset: None,
    sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Provide an AsyncSession for unit-level tests."""
    async with sessionmaker() as session:
        yield session


@pytest.fixture(scope="session")
def app(configure_test_env: None):
    """Return the FastAPI app instance."""
    from backend.main import app as fastapi_app

    return fastapi_app


@pytest.fixture()
async def app_client(
    app,
    db_reset: None,
    sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncClient]:
    """Provide an httpx AsyncClient bound to the FastAPI app."""

    async def _override_get_session() -> AsyncIterator[AsyncSession]:
        async with sessionmaker() as session:
            yield session

    app.dependency_overrides[app_get_session] = _override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Convenience for tests that need to set `dependency_overrides`.
        client.app = app  # type: ignore[attr-defined]
        try:
            yield client
        finally:
            app.dependency_overrides.pop(app_get_session, None)
