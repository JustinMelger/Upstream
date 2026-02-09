from __future__ import annotations

import asyncio
from logging.config import fileConfig
import os
from pathlib import Path
import sys

from sqlalchemy import pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context


# Ensure the repository root is on sys.path so `import backend` works when Alembic runs.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.database.orm_models import Base


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

MIGRATION_LOCK_ID = 74180321


def _database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL is required to run Alembic migrations.")
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode (async engine)."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = _database_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # `AsyncConnection.execute()` implicitly opens a transaction (autobegin). If we leave that
        # transaction open, SQLAlchemy will roll it back when the connection closes, which would
        # also roll back all DDL from the migration. To avoid that, we explicitly commit after
        # acquiring/releasing the advisory lock so the migration runs in its own transaction.
        await connection.execute(text("SELECT pg_advisory_lock(:lock_id)"), {"lock_id": MIGRATION_LOCK_ID})
        if connection.in_transaction():
            await connection.commit()
        try:
            await connection.run_sync(do_run_migrations)
        finally:
            await connection.execute(text("SELECT pg_advisory_unlock(:lock_id)"), {"lock_id": MIGRATION_LOCK_ID})
            if connection.in_transaction():
                await connection.commit()

    await connectable.dispose()


cmd_opts = getattr(config, "cmd_opts", None)
sql_mode = bool(getattr(cmd_opts, "sql", False)) if cmd_opts is not None else False

if sql_mode:
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
