"""
Database Router for Agent-as-a-Service (AAAS) Mode.

Routes database queries to the appropriate database:
- Agent models → 'default' database
- Brain models → 'brain' database
- Memory models → 'memory' database

VIBE Compliance:
- Rule 10: Django ORM only
- Rule 100: Centralized configuration
"""

from __future__ import annotations


class UnifiedDatabaseRouter:
    """
    Database router for multi-database unified AAAS mode.

    Routes models to their respective databases while allowing
    cross-service reads in a single process.
    """

    # App to database mapping
    ROUTE_MAP = {
        # SomaBrain apps
        "somabrain": "brain",
        "somabrain.aaas": "brain",
        # SomaFractalMemory apps
        "somafractalmemory": "memory",
        "somafractalmemory.aaas": "memory",
        # All other apps (somaAgent01) go to default
    }

    def db_for_read(self, model, **hints):
        """Return the database for reading."""
        app_label = model._meta.app_label
        return self.ROUTE_MAP.get(app_label, "default")

    def db_for_write(self, model, **hints):
        """Return the database for writing."""
        app_label = model._meta.app_label
        return self.ROUTE_MAP.get(app_label, "default")

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations within the same database.

        In single-process mode, we allow cross-database reads
        but not cross-database foreign keys.
        """
        db1 = self.ROUTE_MAP.get(obj1._meta.app_label, "default")
        db2 = self.ROUTE_MAP.get(obj2._meta.app_label, "default")
        return db1 == db2

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Ensure migrations run on the correct database.
        """
        expected_db = self.ROUTE_MAP.get(app_label, "default")
        return db == expected_db
