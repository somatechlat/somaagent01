"""Alembic migration environment for SomaAgent01.

This module configures Alembic to work with async PostgreSQL via asyncpg.
It supports both online (connected) and offline (SQL generation) migrations.

The database URL is read from the SA01_DB_DSN environment variable.
"""

from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Import the Base metadata from our models
# This import will be available once models are created
try:
    from src.core.infrastructure.db.models import Base

    target_metadata = Base.metadata
except ImportError:
    # Models not yet created - use None for initial setup
    target_metadata = None

# Alembic Config object for access to .ini file values
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def get_url() -> str:
    """Get database URL from environment variable.

    Converts the standard PostgreSQL URL to use asyncpg driver.
    Falls back to a default local development URL if not set.

    Returns:
        Database URL string with asyncpg driver.
    """
    default_dsn = "postgresql://soma:soma@localhost:5432/somaagent01"
    dsn = os.environ.get("SA01_DB_DSN", default_dsn)

    # Expand any environment variables in the DSN
    dsn = os.path.expandvars(dsn)

    # Convert postgresql:// to postgresql+asyncpg:// for async support
    if dsn.startswith("postgresql://"):
        dsn = dsn.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif dsn.startswith("postgres://"):
        dsn = dsn.replace("postgres://", "postgresql+asyncpg://", 1)

    return dsn


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the Engine
    creation we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with the given connection.

    Args:
        connection: SQLAlchemy connection object.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine.

    In this scenario we need to create an Engine and associate a
    connection with the context.
    """
    configuration = config.get_section(config.config_ini_section) or {}

    # Use URL from config if set (e.g., by tests), otherwise get from env
    url = config.get_main_option("sqlalchemy.url")
    if not url or url == "driver://user:pass@localhost/dbname":
        url = get_url()
    else:
        # Ensure async driver for URLs set externally
        if "postgresql+psycopg://" in url:
            url = url.replace("postgresql+psycopg://", "postgresql+asyncpg://")
        elif "postgresql://" in url and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://")

    configuration["sqlalchemy.url"] = url

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Wraps the async migration runner for synchronous Alembic CLI.
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
