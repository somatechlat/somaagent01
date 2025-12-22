"""Property 3 & 4: Migration Idempotency and Round-Trip.

Feature: alembic-migrations
Property 3: Migration Idempotency
Property 4: Migration Round-Trip

Validates: Requirements 3.3, 3.4, 3.5, 6.4

Property 3: For any migration M, running M twice in sequence SHALL produce
identical database state as running M once.

Property 4: For any migration M with upgrade U and downgrade D,
running U followed by D followed by U SHALL produce identical
database state as running U once.

These tests require REAL PostgreSQL infrastructure - no mocks.
Uses testcontainers for isolated PostgreSQL instances.
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, Set

import pytest

# Check for testcontainers availability
try:
    from testcontainers.postgres import PostgresContainer
    TESTCONTAINERS_AVAILABLE = True
except ImportError:
    TESTCONTAINERS_AVAILABLE = False

# Check for alembic availability
try:
    from alembic import command
    from alembic.config import Config
    ALEMBIC_AVAILABLE = True
except ImportError:
    ALEMBIC_AVAILABLE = False

# Check for sqlalchemy availability
try:
    from sqlalchemy import create_engine, inspect, text
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False


SKIP_REASON = []
if not TESTCONTAINERS_AVAILABLE:
    SKIP_REASON.append("testcontainers not installed")
if not ALEMBIC_AVAILABLE:
    SKIP_REASON.append("alembic not installed")
if not SQLALCHEMY_AVAILABLE:
    SKIP_REASON.append("sqlalchemy not installed")

pytestmark = pytest.mark.skipif(
    bool(SKIP_REASON),
    reason=", ".join(SKIP_REASON) if SKIP_REASON else "OK"
)


# Expected tables from the migration
EXPECTED_TABLES: Set[str] = {
    "task_registry",
    "task_artifacts",
    "multimodal_assets",
    "multimodal_capabilities",
    "multimodal_job_plans",
    "multimodal_executions",
    "asset_provenance",
    "multimodal_outcomes",
    "prompts",
    "tool_catalog",
    "tenant_tool_flags",
    "session_embeddings",
    "alembic_version",  # Alembic's own table
}

# Expected ENUM types
EXPECTED_ENUMS: Set[str] = {
    "asset_type",
    "job_status",
    "execution_status",
    "capability_health",
    "cost_tier",
}


def get_alembic_config(db_url: str) -> Config:
    """Create Alembic config pointing to the test database.

    Ensures the URL uses psycopg (v3) driver format.
    """
    # Get the path to alembic.ini relative to this test file
    test_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(test_dir))
    alembic_ini = os.path.join(project_root, "alembic.ini")

    config = Config(alembic_ini)
    # Ensure we use psycopg (v3) driver - testcontainers returns psycopg2 format
    db_url = db_url.replace("postgresql+psycopg2://", "postgresql+psycopg://")
    config.set_main_option("sqlalchemy.url", db_url)
    return config


def get_database_state(engine: Any) -> Dict[str, Any]:
    """Capture current database state for comparison.

    Returns a dict with:
    - tables: set of table names
    - enums: set of enum type names
    - columns: dict of table_name -> list of column info
    - indexes: dict of table_name -> list of index names
    - constraints: dict of table_name -> list of constraint names
    """
    inspector = inspect(engine)

    state = {
        "tables": set(inspector.get_table_names()),
        "enums": set(),
        "columns": {},
        "indexes": {},
        "constraints": {},
    }

    # Get enum types
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT typname FROM pg_type 
            WHERE typtype = 'e' 
            ORDER BY typname
        """))
        state["enums"] = {row[0] for row in result}

    # Get columns, indexes, constraints per table
    for table_name in state["tables"]:
        # Columns
        columns = inspector.get_columns(table_name)
        state["columns"][table_name] = sorted(
            [{"name": c["name"], "type": str(c["type"])} for c in columns],
            key=lambda x: x["name"]
        )

        # Indexes
        indexes = inspector.get_indexes(table_name)
        state["indexes"][table_name] = sorted([idx["name"] for idx in indexes])

        # Unique constraints
        unique_constraints = inspector.get_unique_constraints(table_name)
        check_constraints = inspector.get_check_constraints(table_name)
        state["constraints"][table_name] = sorted(
            [c["name"] for c in unique_constraints if c.get("name")]
            + [c["name"] for c in check_constraints if c.get("name")]
        )

    return state


def get_seed_data_counts(engine: Any) -> Dict[str, int]:
    """Get row counts for seeded tables."""
    counts = {}
    with engine.connect() as conn:
        # tool_catalog seed data
        result = conn.execute(text("SELECT COUNT(*) FROM tool_catalog"))
        counts["tool_catalog"] = result.scalar()

        # prompts seed data
        result = conn.execute(text("SELECT COUNT(*) FROM prompts"))
        counts["prompts"] = result.scalar()

        # multimodal_capabilities seed data
        result = conn.execute(text("SELECT COUNT(*) FROM multimodal_capabilities"))
        counts["multimodal_capabilities"] = result.scalar()

    return counts


@pytest.fixture(scope="function")
def postgres_container():
    """Create a fresh PostgreSQL container for each test.

    Uses testcontainers for isolated, real PostgreSQL instances.
    """
    # Use PostgreSQL 16 with pgvector extension
    with PostgresContainer(
        image="pgvector/pgvector:pg16",
        username="test",
        password="test",
        dbname="testdb",
    ) as postgres:
        # Wait for container to be ready
        time.sleep(2)
        yield postgres


@pytest.fixture
def db_url(postgres_container) -> str:
    """Get the database URL for the test container.

    Converts the default psycopg2 URL to psycopg (v3) format.
    """
    url = postgres_container.get_connection_url()
    # testcontainers returns postgresql+psycopg2:// which requires psycopg2
    # We use psycopg (v3) so convert to postgresql+psycopg://
    return url.replace("postgresql+psycopg2://", "postgresql+psycopg://")


@pytest.fixture
def engine(db_url: str):
    """Create SQLAlchemy engine for the test database."""
    eng = create_engine(db_url)
    yield eng
    eng.dispose()


class TestMigrationIdempotency:
    """Property 3: Migration Idempotency tests.

    Feature: alembic-migrations, Property 3: Migration Idempotency
    Validates: Requirements 3.3, 3.4, 3.5

    For any migration M, running M twice in sequence SHALL produce
    identical database state as running M once.
    """

    def test_upgrade_is_idempotent(self, db_url: str, engine):
        """Running upgrade twice produces same state as running once.

        Property 3: Migration Idempotency
        Validates: Requirements 3.3, 3.4
        """
        config = get_alembic_config(db_url)

        # First upgrade
        command.upgrade(config, "head")
        state_after_first = get_database_state(engine)
        counts_after_first = get_seed_data_counts(engine)

        # Second upgrade (should be idempotent)
        command.upgrade(config, "head")
        state_after_second = get_database_state(engine)
        counts_after_second = get_seed_data_counts(engine)

        # States should be identical
        assert state_after_first["tables"] == state_after_second["tables"], (
            "Tables differ after second upgrade"
        )
        assert state_after_first["enums"] == state_after_second["enums"], (
            "Enums differ after second upgrade"
        )
        assert state_after_first["columns"] == state_after_second["columns"], (
            "Columns differ after second upgrade"
        )
        assert state_after_first["indexes"] == state_after_second["indexes"], (
            "Indexes differ after second upgrade"
        )

        # Seed data counts should be identical (ON CONFLICT DO NOTHING)
        assert counts_after_first == counts_after_second, (
            f"Seed data counts differ: {counts_after_first} vs {counts_after_second}"
        )

    def test_all_expected_tables_created(self, db_url: str, engine):
        """Verify all expected tables are created by the migration.

        Property 3: Migration Idempotency
        Validates: Requirements 3.3
        """
        config = get_alembic_config(db_url)
        command.upgrade(config, "head")

        state = get_database_state(engine)
        missing_tables = EXPECTED_TABLES - state["tables"]

        assert not missing_tables, (
            f"Missing tables after migration: {missing_tables}"
        )

    def test_all_expected_enums_created(self, db_url: str, engine):
        """Verify all expected ENUM types are created by the migration.

        Property 3: Migration Idempotency
        Validates: Requirements 3.3
        """
        config = get_alembic_config(db_url)
        command.upgrade(config, "head")

        state = get_database_state(engine)
        missing_enums = EXPECTED_ENUMS - state["enums"]

        assert not missing_enums, (
            f"Missing ENUM types after migration: {missing_enums}"
        )

    def test_seed_data_inserted(self, db_url: str, engine):
        """Verify seed data is inserted by the migration.

        Property 3: Migration Idempotency
        Validates: Requirements 3.5
        """
        config = get_alembic_config(db_url)
        command.upgrade(config, "head")

        counts = get_seed_data_counts(engine)

        # tool_catalog should have 2 seed rows (echo, document_ingest)
        assert counts["tool_catalog"] >= 2, (
            f"Expected at least 2 tool_catalog rows, got {counts['tool_catalog']}"
        )

        # prompts should have 1 seed row (multimodal_critic)
        assert counts["prompts"] >= 1, (
            f"Expected at least 1 prompts row, got {counts['prompts']}"
        )

        # multimodal_capabilities should have 5 seed rows
        assert counts["multimodal_capabilities"] >= 5, (
            f"Expected at least 5 multimodal_capabilities rows, "
            f"got {counts['multimodal_capabilities']}"
        )


class TestMigrationRoundTrip:
    """Property 4: Migration Round-Trip tests.

    Feature: alembic-migrations, Property 4: Migration Round-Trip
    Validates: Requirements 6.4

    For any migration M with upgrade U and downgrade D,
    running U followed by D followed by U SHALL produce identical
    database state as running U once.
    """

    def test_upgrade_downgrade_upgrade_produces_same_state(
        self, db_url: str, engine
    ):
        """U -> D -> U produces same state as U alone.

        Property 4: Migration Round-Trip
        Validates: Requirements 6.4
        """
        config = get_alembic_config(db_url)

        # First upgrade
        command.upgrade(config, "head")
        state_after_first_upgrade = get_database_state(engine)

        # Downgrade to base
        command.downgrade(config, "base")

        # Verify tables are dropped
        state_after_downgrade = get_database_state(engine)
        # Only alembic_version should remain (or be empty)
        remaining_tables = state_after_downgrade["tables"] - {"alembic_version"}
        assert not remaining_tables, (
            f"Tables not dropped after downgrade: {remaining_tables}"
        )

        # Second upgrade
        command.upgrade(config, "head")
        state_after_second_upgrade = get_database_state(engine)

        # States should be identical
        assert state_after_first_upgrade["tables"] == state_after_second_upgrade["tables"], (
            "Tables differ after round-trip"
        )
        assert state_after_first_upgrade["enums"] == state_after_second_upgrade["enums"], (
            "Enums differ after round-trip"
        )
        assert state_after_first_upgrade["columns"] == state_after_second_upgrade["columns"], (
            "Columns differ after round-trip"
        )

    def test_downgrade_removes_all_tables(self, db_url: str, engine):
        """Downgrade removes all tables created by upgrade.

        Property 4: Migration Round-Trip
        Validates: Requirements 6.4
        """
        config = get_alembic_config(db_url)

        # Upgrade
        command.upgrade(config, "head")

        # Verify tables exist
        state_before = get_database_state(engine)
        assert len(state_before["tables"]) > 1, "No tables created by upgrade"

        # Downgrade
        command.downgrade(config, "base")

        # Verify tables removed
        state_after = get_database_state(engine)
        remaining = state_after["tables"] - {"alembic_version"}
        assert not remaining, f"Tables not removed: {remaining}"

    def test_downgrade_removes_all_enums(self, db_url: str, engine):
        """Downgrade removes all ENUM types created by upgrade.

        Property 4: Migration Round-Trip
        Validates: Requirements 6.4
        """
        config = get_alembic_config(db_url)

        # Upgrade
        command.upgrade(config, "head")

        # Verify enums exist
        state_before = get_database_state(engine)
        assert state_before["enums"], "No enums created by upgrade"

        # Downgrade
        command.downgrade(config, "base")

        # Verify enums removed
        state_after = get_database_state(engine)
        remaining = state_after["enums"] & EXPECTED_ENUMS
        assert not remaining, f"Enums not removed: {remaining}"

    def test_seed_data_restored_after_round_trip(self, db_url: str, engine):
        """Seed data is restored after upgrade -> downgrade -> upgrade.

        Property 4: Migration Round-Trip
        Validates: Requirements 6.4
        """
        config = get_alembic_config(db_url)

        # First upgrade
        command.upgrade(config, "head")
        counts_first = get_seed_data_counts(engine)

        # Downgrade
        command.downgrade(config, "base")

        # Second upgrade
        command.upgrade(config, "head")
        counts_second = get_seed_data_counts(engine)

        # Seed data should be identical
        assert counts_first == counts_second, (
            f"Seed data differs after round-trip: {counts_first} vs {counts_second}"
        )
