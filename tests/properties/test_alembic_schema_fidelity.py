"""Property 2: Schema Fidelity.

Feature: alembic-migrations
Property 2: Schema Fidelity

Validates: Requirements 2.3, 6.2, 6.3

For any SQLAlchemy model definition, the generated DDL SHALL produce table
structures with identical columns, types, constraints, and indexes as the
original SQL init scripts.

This test compares the SQLAlchemy model metadata against the expected schema
derived from the original SQL init scripts.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Set

import pytest

# Skip if models not yet available
try:
    from src.core.infrastructure.db.models import (
        Base,
        MultimodalAsset,
        MultimodalCapability,
        MultimodalExecution,
        MultimodalJobPlan,
        MultimodalOutcome,
        AssetProvenance,
        Prompt,
        SessionEmbedding,
        TaskArtifact,
        TaskRegistry,
        TenantToolFlag,
        ToolCatalog,
    )
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False


# Expected tables from SQL init scripts
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
}

# Expected columns per table (column_name: expected_type_pattern)
# Using regex patterns to match SQLAlchemy type representations
# SQLAlchemy uses generic types that map to PostgreSQL types at runtime
EXPECTED_COLUMNS: Dict[str, Dict[str, str]] = {
    "task_registry": {
        "name": r"TEXT|VARCHAR",
        "kind": r"TEXT|VARCHAR",
        "module_path": r"TEXT|VARCHAR",
        "callable": r"TEXT|VARCHAR",
        "queue": r"TEXT|VARCHAR",
        "rate_limit": r"TEXT|VARCHAR",
        "max_retries": r"INTEGER",
        "soft_time_limit": r"INTEGER",
        "time_limit": r"INTEGER",
        "enabled": r"BOOLEAN",
        "tenant_scope": r"ARRAY",
        "persona_scope": r"ARRAY",
        "arg_schema": r"JSONB|JSON",
        "artifact_hash": r"TEXT|VARCHAR",
        "soma_tags": r"ARRAY",
        "created_by": r"TEXT|VARCHAR",
        "created_at": r"TIMESTAMP|DATETIME",
        "updated_at": r"TIMESTAMP|DATETIME",
    },
    "task_artifacts": {
        "id": r"UUID",
        "name": r"TEXT|VARCHAR",
        "version": r"TEXT|VARCHAR",
        "storage_uri": r"TEXT|VARCHAR",
        "sha256": r"TEXT|VARCHAR",
        "signed_by": r"TEXT|VARCHAR",
        "created_at": r"TIMESTAMP|DATETIME",
    },
    "multimodal_assets": {
        "id": r"UUID",
        "tenant_id": r"TEXT|VARCHAR",
        "session_id": r"TEXT|VARCHAR",
        "asset_type": r"asset_type|ENUM|VARCHAR",
        "format": r"TEXT|VARCHAR",
        "storage_path": r"TEXT|VARCHAR",
        "content": r"BYTEA|LARGEBINARY|BLOB",
        "content_size_bytes": r"BIGINT",
        "checksum_sha256": r"TEXT|VARCHAR",
        "original_filename": r"TEXT|VARCHAR",
        "mime_type": r"TEXT|VARCHAR",
        "dimensions": r"JSONB|JSON",
        "metadata": r"JSONB|JSON",
        "created_at": r"TIMESTAMP|DATETIME",
        "expires_at": r"TIMESTAMP|DATETIME",
    },
    "multimodal_capabilities": {
        "tool_id": r"TEXT|VARCHAR",
        "provider": r"TEXT|VARCHAR",
        "tenant_id": r"TEXT|VARCHAR",
        "modalities": r"JSONB|JSON",
        "input_schema": r"JSONB|JSON",
        "output_schema": r"JSONB|JSON",
        "constraints": r"JSONB|JSON",
        "cost_tier": r"cost_tier|ENUM|VARCHAR",
        "latency_p95_ms": r"INTEGER",
        "health_status": r"capability_health|ENUM|VARCHAR",
        "last_health_check": r"TIMESTAMP|DATETIME",
        "failure_count": r"INTEGER",
        "enabled": r"BOOLEAN",
        "display_name": r"TEXT|VARCHAR",
        "description": r"TEXT|VARCHAR",
        "documentation_url": r"TEXT|VARCHAR",
        "created_at": r"TIMESTAMP|DATETIME",
        "updated_at": r"TIMESTAMP|DATETIME",
    },
    "multimodal_job_plans": {
        "id": r"UUID",
        "tenant_id": r"TEXT|VARCHAR",
        "session_id": r"TEXT|VARCHAR",
        "request_id": r"TEXT|VARCHAR",
        "plan_json": r"JSONB|JSON",
        "plan_version": r"TEXT|VARCHAR",
        "status": r"job_status|ENUM|VARCHAR",
        "total_steps": r"INTEGER",
        "completed_steps": r"INTEGER",
        "budget_limit_cents": r"INTEGER",
        "budget_used_cents": r"INTEGER",
        "started_at": r"TIMESTAMP|DATETIME",
        "completed_at": r"TIMESTAMP|DATETIME",
        "error_message": r"TEXT|VARCHAR",
        "error_details": r"JSONB|JSON",
        "created_at": r"TIMESTAMP|DATETIME",
        "updated_at": r"TIMESTAMP|DATETIME",
    },
    "multimodal_executions": {
        "id": r"UUID",
        "plan_id": r"UUID",
        "step_index": r"INTEGER",
        "tenant_id": r"TEXT|VARCHAR",
        "tool_id": r"TEXT|VARCHAR",
        "provider": r"TEXT|VARCHAR",
        "status": r"execution_status|ENUM|VARCHAR",
        "attempt_number": r"INTEGER",
        "asset_id": r"UUID",
        "latency_ms": r"INTEGER",
        "cost_estimate_cents": r"INTEGER",
        "quality_score": r"REAL|FLOAT",
        "quality_feedback": r"JSONB|JSON",
        "error_code": r"TEXT|VARCHAR",
        "error_message": r"TEXT|VARCHAR",
        "started_at": r"TIMESTAMP|DATETIME",
        "completed_at": r"TIMESTAMP|DATETIME",
        "created_at": r"TIMESTAMP|DATETIME",
    },
    "asset_provenance": {
        "asset_id": r"UUID",
        "request_id": r"TEXT|VARCHAR",
        "execution_id": r"UUID",
        "plan_id": r"UUID",
        "user_id": r"TEXT|VARCHAR",
        "tenant_id": r"TEXT|VARCHAR",
        "session_id": r"TEXT|VARCHAR",
        "prompt_summary": r"TEXT|VARCHAR",
        "generation_params": r"JSONB|JSON",
        "tool_id": r"TEXT|VARCHAR",
        "provider": r"TEXT|VARCHAR",
        "model_version": r"TEXT|VARCHAR",
        "trace_id": r"TEXT|VARCHAR",
        "span_id": r"TEXT|VARCHAR",
        "quality_gate_passed": r"BOOLEAN",
        "quality_score": r"REAL|FLOAT",
        "rework_count": r"INTEGER",
        "created_at": r"TIMESTAMP|DATETIME",
    },
    "multimodal_outcomes": {
        "id": r"UUID",
        "plan_id": r"UUID",
        "task_id": r"TEXT|VARCHAR",
        "step_type": r"TEXT|VARCHAR",
        "provider": r"TEXT|VARCHAR",
        "model": r"TEXT|VARCHAR",
        "success": r"BOOLEAN",
        "latency_ms": r"REAL|FLOAT",
        "cost_cents": r"REAL|FLOAT",
        "quality_score": r"REAL|FLOAT",
        "feedback": r"TEXT|VARCHAR",
        "timestamp": r"TIMESTAMP|DATETIME",
    },
    "prompts": {
        "id": r"UUID",
        "name": r"VARCHAR|TEXT",
        "version": r"INTEGER",
        "content": r"TEXT|VARCHAR",
        "created_at": r"TIMESTAMP|DATETIME",
        "updated_at": r"TIMESTAMP|DATETIME",
    },
    "tool_catalog": {
        "name": r"TEXT|VARCHAR",
        "description": r"TEXT|VARCHAR",
        "parameters_schema": r"JSONB|JSON",
        "enabled": r"BOOLEAN",
        "cost_impact": r"TEXT|VARCHAR",
        "profiles": r"ARRAY",
        "updated_at": r"TIMESTAMP|DATETIME",
    },
    "tenant_tool_flags": {
        "tenant_id": r"TEXT|VARCHAR",
        "tool_name": r"TEXT|VARCHAR",
        "enabled": r"BOOLEAN",
        "updated_at": r"TIMESTAMP|DATETIME",
    },
    "session_embeddings": {
        "id": r"BIGINT|BIGSERIAL",
        "session_id": r"UUID",
        "text": r"TEXT|VARCHAR",
        "vector": r"VECTOR|LARGEBINARY|BLOB",
        "metadata": r"JSONB|JSON",
        "created_at": r"TIMESTAMP|DATETIME",
    },
}


@pytest.mark.skipif(not MODELS_AVAILABLE, reason="Models not yet created")
class TestSchemaFidelity:
    """Property 2: Schema Fidelity tests.

    Feature: alembic-migrations, Property 2: Schema Fidelity
    Validates: Requirements 2.3, 6.2, 6.3
    """

    def test_all_expected_tables_defined(self):
        """Verify all expected tables are defined in SQLAlchemy models.

        Property 2: Schema Fidelity
        Validates: Requirements 2.3
        """
        actual_tables = set(Base.metadata.tables.keys())
        missing_tables = EXPECTED_TABLES - actual_tables

        assert not missing_tables, (
            f"Missing table definitions: {missing_tables}\n"
            f"Expected: {sorted(EXPECTED_TABLES)}\n"
            f"Actual: {sorted(actual_tables)}"
        )

    def test_no_unexpected_tables(self):
        """Verify no unexpected tables are defined.

        Property 2: Schema Fidelity
        Validates: Requirements 2.3
        """
        actual_tables = set(Base.metadata.tables.keys())
        unexpected_tables = actual_tables - EXPECTED_TABLES

        # Allow some flexibility for future additions
        assert not unexpected_tables, (
            f"Unexpected table definitions: {unexpected_tables}\n"
            f"If these are intentional, add them to EXPECTED_TABLES"
        )

    @pytest.mark.parametrize("table_name", sorted(EXPECTED_TABLES))
    def test_table_has_expected_columns(self, table_name: str):
        """Verify each table has all expected columns.

        Property 2: Schema Fidelity
        Validates: Requirements 2.3, 6.2
        """
        if table_name not in Base.metadata.tables:
            pytest.skip(f"Table {table_name} not yet defined")

        table = Base.metadata.tables[table_name]
        actual_columns = set(c.name for c in table.columns)
        expected_columns = set(EXPECTED_COLUMNS.get(table_name, {}).keys())

        missing_columns = expected_columns - actual_columns
        assert not missing_columns, (
            f"Table '{table_name}' missing columns: {missing_columns}"
        )

    @pytest.mark.parametrize("table_name", sorted(EXPECTED_TABLES))
    def test_column_types_match(self, table_name: str):
        """Verify column types match expected patterns.

        Property 2: Schema Fidelity
        Validates: Requirements 2.3, 6.2, 6.3
        """
        if table_name not in Base.metadata.tables:
            pytest.skip(f"Table {table_name} not yet defined")

        table = Base.metadata.tables[table_name]
        expected_cols = EXPECTED_COLUMNS.get(table_name, {})

        type_mismatches: List[str] = []

        for col_name, expected_pattern in expected_cols.items():
            if col_name not in [c.name for c in table.columns]:
                continue

            column = table.c[col_name]
            actual_type = str(column.type).upper()

            if not re.search(expected_pattern, actual_type, re.IGNORECASE):
                type_mismatches.append(
                    f"  {col_name}: expected pattern '{expected_pattern}', "
                    f"got '{actual_type}'"
                )

        assert not type_mismatches, (
            f"Table '{table_name}' has column type mismatches:\n"
            + "\n".join(type_mismatches)
        )

    def test_task_registry_has_primary_key(self):
        """Verify task_registry has correct primary key.

        Property 2: Schema Fidelity
        Validates: Requirements 6.3
        """
        if "task_registry" not in Base.metadata.tables:
            pytest.skip("task_registry not yet defined")

        table = Base.metadata.tables["task_registry"]
        pk_columns = [c.name for c in table.primary_key.columns]

        assert pk_columns == ["name"], (
            f"task_registry primary key should be ['name'], got {pk_columns}"
        )

    def test_multimodal_capabilities_has_composite_pk(self):
        """Verify multimodal_capabilities has composite primary key.

        Property 2: Schema Fidelity
        Validates: Requirements 6.3
        """
        if "multimodal_capabilities" not in Base.metadata.tables:
            pytest.skip("multimodal_capabilities not yet defined")

        table = Base.metadata.tables["multimodal_capabilities"]
        pk_columns = set(c.name for c in table.primary_key.columns)

        assert pk_columns == {"tool_id", "provider"}, (
            f"multimodal_capabilities primary key should be "
            f"{{'tool_id', 'provider'}}, got {pk_columns}"
        )

    def test_tenant_tool_flags_has_composite_pk(self):
        """Verify tenant_tool_flags has composite primary key.

        Property 2: Schema Fidelity
        Validates: Requirements 6.3
        """
        if "tenant_tool_flags" not in Base.metadata.tables:
            pytest.skip("tenant_tool_flags not yet defined")

        table = Base.metadata.tables["tenant_tool_flags"]
        pk_columns = set(c.name for c in table.primary_key.columns)

        assert pk_columns == {"tenant_id", "tool_name"}, (
            f"tenant_tool_flags primary key should be "
            f"{{'tenant_id', 'tool_name'}}, got {pk_columns}"
        )

    def test_foreign_key_relationships_exist(self):
        """Verify expected foreign key relationships are defined.

        Property 2: Schema Fidelity
        Validates: Requirements 6.2
        """
        expected_fks = [
            ("multimodal_executions", "plan_id", "multimodal_job_plans"),
            ("multimodal_executions", "asset_id", "multimodal_assets"),
            ("asset_provenance", "asset_id", "multimodal_assets"),
            ("asset_provenance", "execution_id", "multimodal_executions"),
            ("asset_provenance", "plan_id", "multimodal_job_plans"),
            ("tenant_tool_flags", "tool_name", "tool_catalog"),
        ]

        missing_fks: List[str] = []

        for table_name, column_name, ref_table in expected_fks:
            if table_name not in Base.metadata.tables:
                continue

            table = Base.metadata.tables[table_name]
            column = table.c.get(column_name)

            if column is None:
                continue

            fk_refs = [fk.column.table.name for fk in column.foreign_keys]

            if ref_table not in fk_refs:
                missing_fks.append(
                    f"{table_name}.{column_name} -> {ref_table}"
                )

        assert not missing_fks, (
            f"Missing foreign key relationships:\n"
            + "\n".join(f"  {fk}" for fk in missing_fks)
        )
