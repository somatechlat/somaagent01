"""Capsule instance store for runtime tracking.

Tracks active capsule instances at runtime, including scope (agent, workflow),
start/end times, and effective configuration overrides.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

import asyncpg

from src.core.config import cfg

__all__ = ["CapsuleInstance", "CapsuleInstanceScope", "CapsuleInstanceStore"]


class CapsuleInstanceScope(str, Enum):
    """Scope where the capsule instance is active."""
    AGENT = "agent"
    WORKFLOW = "workflow"
    SESSION = "session"
    GLOBAL = "global"


@dataclass(slots=True)
class CapsuleInstance:
    """Runtime instance of an active capsule.
    
    Tracks when a capsule definition is instantiated and active.
    """
    instance_id: str
    tenant_id: str
    definition_id: str  # FK to capsule_definitions.capsule_id
    scope: CapsuleInstanceScope = CapsuleInstanceScope.AGENT
    scope_ref_id: str | None = None  # e.g., agent_id or workflow_id
    started_at: datetime | None = None
    ended_at: datetime | None = None
    effective_config: Dict[str, Any] = field(default_factory=dict)  # Merged config overrides
    status: str = "active"  # active, completed, failed, cancelled


class CapsuleInstanceStore:
    """PostgreSQL-backed store for capsule runtime instances."""

    def __init__(self, dsn: str | None = None) -> None:
        self._dsn = dsn or cfg.settings().database.dsn

    async def ensure_schema(self) -> None:
        """Create the capsule_instances table if it doesn't exist."""
        conn = await asyncpg.connect(self._dsn)
        try:
            # Create scope enum type if not exists
            await conn.execute("""
                DO $$ BEGIN
                    CREATE TYPE capsule_instance_scope AS ENUM ('agent', 'workflow', 'session', 'global');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS capsule_instances (
                    instance_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    definition_id TEXT NOT NULL REFERENCES capsule_definitions(capsule_id),
                    scope capsule_instance_scope NOT NULL DEFAULT 'agent',
                    scope_ref_id TEXT,
                    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    ended_at TIMESTAMPTZ,
                    effective_config JSONB DEFAULT '{}'::jsonb,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    
                    CONSTRAINT chk_status CHECK (status IN ('active', 'completed', 'failed', 'cancelled'))
                );
                
                -- Indexes for common queries
                CREATE INDEX IF NOT EXISTS idx_capsule_instance_tenant ON capsule_instances(tenant_id);
                CREATE INDEX IF NOT EXISTS idx_capsule_instance_definition ON capsule_instances(definition_id);
                CREATE INDEX IF NOT EXISTS idx_capsule_instance_scope ON capsule_instances(scope, scope_ref_id);
                CREATE INDEX IF NOT EXISTS idx_capsule_instance_status ON capsule_instances(status);
                CREATE INDEX IF NOT EXISTS idx_capsule_instance_active ON capsule_instances(tenant_id, status) 
                    WHERE status = 'active';
            """)
        finally:
            await conn.close()

    async def start(self, instance: CapsuleInstance) -> str:
        """Start a new capsule instance. Returns instance_id."""
        conn = await asyncpg.connect(self._dsn)
        try:
            await conn.execute(
                """INSERT INTO capsule_instances (
                    instance_id, tenant_id, definition_id, scope, scope_ref_id,
                    started_at, effective_config, status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                instance.instance_id,
                instance.tenant_id,
                instance.definition_id,
                instance.scope.value,
                instance.scope_ref_id,
                instance.started_at or datetime.utcnow(),
                json.dumps(instance.effective_config),
                instance.status,
            )
            return instance.instance_id
        finally:
            await conn.close()

    async def end(self, instance_id: str, status: str = "completed") -> bool:
        """End a capsule instance. Returns True if found and updated."""
        conn = await asyncpg.connect(self._dsn)
        try:
            result = await conn.execute(
                """UPDATE capsule_instances 
                   SET ended_at = NOW(), status = $2, updated_at = NOW() 
                   WHERE instance_id = $1 AND status = 'active'""",
                instance_id, status,
            )
            _, count_str = result.split(" ")
            return int(count_str) > 0
        finally:
            await conn.close()

    async def get(self, instance_id: str) -> Optional[CapsuleInstance]:
        """Get a capsule instance by ID."""
        conn = await asyncpg.connect(self._dsn)
        try:
            row = await conn.fetchrow(
                "SELECT * FROM capsule_instances WHERE instance_id = $1",
                instance_id,
            )
            if not row:
                return None
            return self._row_to_instance(row)
        finally:
            await conn.close()

    async def list_active(self, tenant_id: str) -> List[CapsuleInstance]:
        """List all active capsule instances for a tenant."""
        conn = await asyncpg.connect(self._dsn)
        try:
            rows = await conn.fetch(
                """SELECT * FROM capsule_instances 
                   WHERE tenant_id = $1 AND status = 'active'
                   ORDER BY started_at DESC""",
                tenant_id,
            )
            return [self._row_to_instance(r) for r in rows]
        finally:
            await conn.close()

    async def list_by_definition(self, definition_id: str) -> List[CapsuleInstance]:
        """List all instances of a specific capsule definition."""
        conn = await asyncpg.connect(self._dsn)
        try:
            rows = await conn.fetch(
                """SELECT * FROM capsule_instances 
                   WHERE definition_id = $1
                   ORDER BY started_at DESC""",
                definition_id,
            )
            return [self._row_to_instance(r) for r in rows]
        finally:
            await conn.close()

    async def list_by_scope(
        self, scope: CapsuleInstanceScope, scope_ref_id: str
    ) -> List[CapsuleInstance]:
        """List all instances for a specific scope (e.g., agent or workflow)."""
        conn = await asyncpg.connect(self._dsn)
        try:
            rows = await conn.fetch(
                """SELECT * FROM capsule_instances 
                   WHERE scope = $1 AND scope_ref_id = $2
                   ORDER BY started_at DESC""",
                scope.value, scope_ref_id,
            )
            return [self._row_to_instance(r) for r in rows]
        finally:
            await conn.close()

    def _row_to_instance(self, row: asyncpg.Record) -> CapsuleInstance:
        """Convert a database row to CapsuleInstance."""
        return CapsuleInstance(
            instance_id=row["instance_id"],
            tenant_id=row["tenant_id"],
            definition_id=row["definition_id"],
            scope=CapsuleInstanceScope(row["scope"]),
            scope_ref_id=row["scope_ref_id"],
            started_at=row["started_at"],
            ended_at=row["ended_at"],
            effective_config=json.loads(row["effective_config"]) if row["effective_config"] else {},
            status=row["status"],
        )
