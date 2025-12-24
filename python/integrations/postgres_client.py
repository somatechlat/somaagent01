"""Production Postgres client - 100% Django.

VIBE Compliant - Uses Django database connection.
"""

from __future__ import annotations

from django.db import connection


class PostgresPool:
    """Django-backed database connection wrapper.
    
    Provides compatibility interface for code migrating from asyncpg.
    All queries should use Django ORM directly instead.
    """

    def __init__(self, dsn: str | None = None) -> None:
        # DSN ignored - Django uses settings.DATABASES
        pass

    def acquire(self):
        """Return Django database cursor context manager."""
        return connection.cursor()


# PRODUCTION ONLY - Always use Django database connection
postgres_pool = PostgresPool()
