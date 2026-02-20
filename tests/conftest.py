from __future__ import annotations

import asyncio
import os
from typing import AsyncIterator, Iterator

from alembic.config import Config
from httpx import ASGITransport, AsyncClient
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncEngine, AsyncSession, create_async_engine

from alembic import command
from backend.database.session import get_session as app_get_session


DEFAULT_DATABASE_URL = "postgresql+asyncpg://learning_platform:learning_platform@127.0.0.1:5432/learning_platform"
DB_RESET_MAX_RETRIES = 5


def _is_deadlock_error(exc: DBAPIError) -> bool:
    """Detect PostgreSQL deadlock errors emitted via asyncpg/sqlalchemy."""
    orig = getattr(exc, "orig", None)
    sqlstate = getattr(orig, "sqlstate", None)
    if sqlstate == "40P01":
        return True
    return "deadlock detected" in str(exc).lower()


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Ensure every test is classified for marker-based runs.

    Rules:
    - Keep explicit `unit`/`integration` markers as-is.
    - Mark architecture guard tests as `architecture`.
    - Default other unclassified tests to `unit`.
    """
    for item in items:
        marker_names = {marker.name for marker in item.iter_markers()}
        if "unit" in marker_names or "integration" in marker_names:
            continue
        nodeid = item.nodeid.lower()
        is_architecture = "architecture" in nodeid or "test_page_package_" in nodeid
        if is_architecture:
            item.add_marker(pytest.mark.architecture)
        else:
            item.add_marker(pytest.mark.unit)


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

    async def _verify_schema() -> None:
        engine = create_async_engine(database_url, pool_pre_ping=True)
        try:
            async with engine.begin() as conn:
                tables_result = await conn.execute(
                    text(
                        "SELECT table_schema, table_name "
                        "FROM information_schema.tables "
                        "WHERE table_type = 'BASE TABLE' "
                        "AND table_schema NOT IN ('pg_catalog', 'information_schema') "
                        "ORDER BY table_schema, table_name"
                    )
                )
                tables = {(str(r[0]), str(r[1])) for r in tables_result.all()}
                if ("public", "courses") not in tables:
                    # Print helpful diagnostics for CI runs before failing.
                    db_result = await conn.execute(
                        text("SELECT current_database(), current_schema(), current_setting('search_path')")
                    )
                    db_row = db_result.first()
                    print(f"alembic verification failed: tables={sorted(tables)}", flush=True)
                    print(f"db info: {db_row}", flush=True)
                    raise RuntimeError("Alembic migrations did not create expected tables in public schema.")
        finally:
            await engine.dispose()

    asyncio.run(_verify_schema())
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
    for attempt in range(DB_RESET_MAX_RETRIES):
        try:
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
            break
        except DBAPIError as exc:
            is_last_attempt = attempt + 1 >= DB_RESET_MAX_RETRIES
            if not _is_deadlock_error(exc) or is_last_attempt:
                raise
            await asyncio.sleep(0.05 * (2**attempt))
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
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[app_get_session] = _override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Convenience for tests that need to set `dependency_overrides`.
        client.app = app  # type: ignore[attr-defined]
        try:
            yield client
        finally:
            app.dependency_overrides.pop(app_get_session, None)
