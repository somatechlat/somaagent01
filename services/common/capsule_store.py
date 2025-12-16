"""Capsule store using PostgreSQL for persistence.

Replaces the in-memory store with a persistent implementation backed by the
`capsule_definitions` table. Schema extended per SRS §14.1 to include all
CapsuleDefinition fields from SomaAgentHub domain model.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

import asyncpg

from src.core.config import cfg

__all__ = ["CapsuleRecord", "CapsuleStatus", "CapsuleStore"]


class CapsuleStatus(str, Enum):
    """Capsule lifecycle status."""
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"


@dataclass(slots=True)
class CapsuleRecord:
    """Full CapsuleDefinition per SRS §14.1 (SomaAgentHub alignment).
    
    Contains all 25+ policy fields for capsule governance.
    """
    # Identity
    capsule_id: str
    tenant_id: str = "default"
    name: str = ""
    version: str = "1.0.0"
    status: CapsuleStatus = CapsuleStatus.DRAFT
    description: str = ""
    
    # Persona & Role
    default_persona_ref_id: str | None = None
    role_overrides: Dict[str, Any] = field(default_factory=dict)
    
    # Tool Policy
    allowed_tools: List[str] = field(default_factory=list)
    prohibited_tools: List[str] = field(default_factory=list)
    allowed_mcp_servers: List[str] = field(default_factory=list)
    tool_risk_profile: str = "standard"  # low/standard/high/critical
    
    # Resource Limits
    max_wall_clock_seconds: int = 3600
    max_concurrent_nodes: int = 5
    allowed_runtimes: List[str] = field(default_factory=lambda: ["python", "node"])
    resource_profile: str = "default"  # default/compute/memory/gpu
    
    # Network Policy
    allowed_domains: List[str] = field(default_factory=list)
    blocked_domains: List[str] = field(default_factory=list)
    egress_mode: str = "restricted"  # none/restricted/open
    
    # Policy & Guardrails
    opa_policy_packages: List[str] = field(default_factory=list)
    guardrail_profiles: List[str] = field(default_factory=list)
    
    # HITL (Human-in-the-Loop)
    default_hitl_mode: str = "optional"  # none/optional/required
    risk_thresholds: Dict[str, float] = field(default_factory=dict)
    max_pending_hitl: int = 10
    
    # RL & Export
    rl_export_allowed: bool = False
    rl_export_scope: str = "tenant"  # tenant/global
    rl_excluded_fields: List[str] = field(default_factory=list)
    example_store_policy: str = "retain"  # retain/anonymize/discard
    
    # Classification & Retention
    data_classification: str = "internal"  # public/internal/confidential/restricted
    retention_policy_days: int = 365
    
    # Legacy compatibility
    installed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class CapsuleStore:
    """PostgreSQL-backed store for capsule definitions."""

    def __init__(self, dsn: str | None = None) -> None:
        self._dsn = dsn or cfg.settings().database.dsn

    async def ensure_schema(self) -> None:
        """Create the capsule_definitions table if it doesn't exist.
        
        Schema includes all 25+ policy fields per SRS §14.1.
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            # Create status enum type if not exists
            await conn.execute("""
                DO $$ BEGIN
                    CREATE TYPE capsule_status AS ENUM ('draft', 'published', 'deprecated');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS capsule_definitions (
                    -- Identity
                    capsule_id TEXT NOT NULL,
                    tenant_id TEXT NOT NULL DEFAULT 'default',
                    name TEXT NOT NULL,
                    version TEXT NOT NULL DEFAULT '1.0.0',
                    status capsule_status NOT NULL DEFAULT 'draft',
                    description TEXT DEFAULT '',
                    
                    -- Persona & Role
                    default_persona_ref_id TEXT,
                    role_overrides JSONB DEFAULT '{}'::jsonb,
                    
                    -- Tool Policy
                    allowed_tools JSONB DEFAULT '[]'::jsonb,
                    prohibited_tools JSONB DEFAULT '[]'::jsonb,
                    allowed_mcp_servers JSONB DEFAULT '[]'::jsonb,
                    tool_risk_profile TEXT DEFAULT 'standard',
                    
                    -- Resource Limits
                    max_wall_clock_seconds INTEGER DEFAULT 3600,
                    max_concurrent_nodes INTEGER DEFAULT 5,
                    allowed_runtimes JSONB DEFAULT '["python", "node"]'::jsonb,
                    resource_profile TEXT DEFAULT 'default',
                    
                    -- Network Policy
                    allowed_domains JSONB DEFAULT '[]'::jsonb,
                    blocked_domains JSONB DEFAULT '[]'::jsonb,
                    egress_mode TEXT DEFAULT 'restricted',
                    
                    -- Policy & Guardrails
                    opa_policy_packages JSONB DEFAULT '[]'::jsonb,
                    guardrail_profiles JSONB DEFAULT '[]'::jsonb,
                    
                    -- HITL
                    default_hitl_mode TEXT DEFAULT 'optional',
                    risk_thresholds JSONB DEFAULT '{}'::jsonb,
                    max_pending_hitl INTEGER DEFAULT 10,
                    
                    -- RL & Export
                    rl_export_allowed BOOLEAN DEFAULT FALSE,
                    rl_export_scope TEXT DEFAULT 'tenant',
                    rl_excluded_fields JSONB DEFAULT '[]'::jsonb,
                    example_store_policy TEXT DEFAULT 'retain',
                    
                    -- Classification & Retention
                    data_classification TEXT DEFAULT 'internal',
                    retention_policy_days INTEGER DEFAULT 365,
                    
                    -- Legacy compatibility
                    installed BOOLEAN DEFAULT FALSE,
                    metadata JSONB DEFAULT '{}'::jsonb,
                    
                    -- Timestamps
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    
                    -- Constraints
                    PRIMARY KEY (capsule_id),
                    CONSTRAINT uq_capsule_tenant_name_version UNIQUE (tenant_id, name, version)
                );
                
                -- Indexes for common queries
                CREATE INDEX IF NOT EXISTS idx_capsule_tenant ON capsule_definitions(tenant_id);
                CREATE INDEX IF NOT EXISTS idx_capsule_status ON capsule_definitions(status);
                CREATE INDEX IF NOT EXISTS idx_capsule_name ON capsule_definitions(name);
            """)
            
            # Migration: if old 'capsules' table exists, inform (do not auto-migrate)
            old_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'capsules'
                )
            """)
            if old_exists:
                # Log warning but do not auto-migrate per VIBE rules
                import logging
                logging.getLogger(__name__).warning(
                    "Legacy 'capsules' table exists. Manual migration to 'capsule_definitions' required."
                )
        finally:
            await conn.close()


    async def list(self, tenant_id: str | None = None) -> List[CapsuleRecord]:
        """List all capsules, optionally filtered by tenant."""
        conn = await asyncpg.connect(self._dsn)
        try:
            if tenant_id:
                rows = await conn.fetch(
                    "SELECT * FROM capsule_definitions WHERE tenant_id = $1 ORDER BY name, version",
                    tenant_id,
                )
            else:
                rows = await conn.fetch(
                    "SELECT * FROM capsule_definitions ORDER BY tenant_id, name, version"
                )
            return [self._row_to_record(r) for r in rows]
        finally:
            await conn.close()

    async def get(self, capsule_id: str) -> Optional[CapsuleRecord]:
        """Get a single capsule by ID."""
        conn = await asyncpg.connect(self._dsn)
        try:
            row = await conn.fetchrow(
                "SELECT * FROM capsule_definitions WHERE capsule_id = $1",
                capsule_id,
            )
            if not row:
                return None
            return self._row_to_record(row)
        finally:
            await conn.close()

    async def get_by_name_version(
        self, tenant_id: str, name: str, version: str
    ) -> Optional[CapsuleRecord]:
        """Get a capsule by tenant/name/version (unique key)."""
        conn = await asyncpg.connect(self._dsn)
        try:
            row = await conn.fetchrow(
                """SELECT * FROM capsule_definitions 
                   WHERE tenant_id = $1 AND name = $2 AND version = $3""",
                tenant_id, name, version,
            )
            if not row:
                return None
            return self._row_to_record(row)
        finally:
            await conn.close()

    async def create(self, record: CapsuleRecord) -> str:
        """Create a new capsule definition. Returns capsule_id."""
        conn = await asyncpg.connect(self._dsn)
        try:
            await conn.execute(
                """INSERT INTO capsule_definitions (
                    capsule_id, tenant_id, name, version, status, description,
                    default_persona_ref_id, role_overrides,
                    allowed_tools, prohibited_tools, allowed_mcp_servers, tool_risk_profile,
                    max_wall_clock_seconds, max_concurrent_nodes, allowed_runtimes, resource_profile,
                    allowed_domains, blocked_domains, egress_mode,
                    opa_policy_packages, guardrail_profiles,
                    default_hitl_mode, risk_thresholds, max_pending_hitl,
                    rl_export_allowed, rl_export_scope, rl_excluded_fields, example_store_policy,
                    data_classification, retention_policy_days,
                    installed, metadata
                ) VALUES (
                    $1, $2, $3, $4, $5, $6,
                    $7, $8,
                    $9, $10, $11, $12,
                    $13, $14, $15, $16,
                    $17, $18, $19,
                    $20, $21,
                    $22, $23, $24,
                    $25, $26, $27, $28,
                    $29, $30,
                    $31, $32
                )""",
                record.capsule_id, record.tenant_id, record.name, record.version,
                record.status.value, record.description,
                record.default_persona_ref_id, json.dumps(record.role_overrides),
                json.dumps(record.allowed_tools), json.dumps(record.prohibited_tools),
                json.dumps(record.allowed_mcp_servers), record.tool_risk_profile,
                record.max_wall_clock_seconds, record.max_concurrent_nodes,
                json.dumps(record.allowed_runtimes), record.resource_profile,
                json.dumps(record.allowed_domains), json.dumps(record.blocked_domains),
                record.egress_mode,
                json.dumps(record.opa_policy_packages), json.dumps(record.guardrail_profiles),
                record.default_hitl_mode, json.dumps(record.risk_thresholds),
                record.max_pending_hitl,
                record.rl_export_allowed, record.rl_export_scope,
                json.dumps(record.rl_excluded_fields), record.example_store_policy,
                record.data_classification, record.retention_policy_days,
                record.installed, json.dumps(record.metadata),
            )
            return record.capsule_id
        finally:
            await conn.close()

    async def install(self, capsule_id: str) -> bool:
        """Mark the capsule as installed.

        Returns True if successful (capsule existed), False otherwise.
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            result = await conn.execute(
                "UPDATE capsule_definitions SET installed = TRUE, updated_at = NOW() WHERE capsule_id = $1",
                capsule_id,
            )
            _, count_str = result.split(" ")
            count = int(count_str)
            return count > 0
        finally:
            await conn.close()

    async def publish(self, capsule_id: str) -> bool:
        """Change capsule status to published."""
        conn = await asyncpg.connect(self._dsn)
        try:
            result = await conn.execute(
                "UPDATE capsule_definitions SET status = 'published', updated_at = NOW() WHERE capsule_id = $1",
                capsule_id,
            )
            _, count_str = result.split(" ")
            return int(count_str) > 0
        finally:
            await conn.close()

    async def deprecate(self, capsule_id: str) -> bool:
        """Change capsule status to deprecated."""
        conn = await asyncpg.connect(self._dsn)
        try:
            result = await conn.execute(
                "UPDATE capsule_definitions SET status = 'deprecated', updated_at = NOW() WHERE capsule_id = $1",
                capsule_id,
            )
            _, count_str = result.split(" ")
            return int(count_str) > 0
        finally:
            await conn.close()

    def _row_to_record(self, row: asyncpg.Record) -> CapsuleRecord:
        """Convert a database row to CapsuleRecord with proper type handling."""
        return CapsuleRecord(
            capsule_id=row["capsule_id"],
            tenant_id=row["tenant_id"],
            name=row["name"],
            version=row["version"],
            status=CapsuleStatus(row["status"]),
            description=row["description"] or "",
            default_persona_ref_id=row["default_persona_ref_id"],
            role_overrides=json.loads(row["role_overrides"]) if row["role_overrides"] else {},
            allowed_tools=json.loads(row["allowed_tools"]) if row["allowed_tools"] else [],
            prohibited_tools=json.loads(row["prohibited_tools"]) if row["prohibited_tools"] else [],
            allowed_mcp_servers=json.loads(row["allowed_mcp_servers"]) if row["allowed_mcp_servers"] else [],
            tool_risk_profile=row["tool_risk_profile"] or "standard",
            max_wall_clock_seconds=row["max_wall_clock_seconds"] or 3600,
            max_concurrent_nodes=row["max_concurrent_nodes"] or 5,
            allowed_runtimes=json.loads(row["allowed_runtimes"]) if row["allowed_runtimes"] else ["python", "node"],
            resource_profile=row["resource_profile"] or "default",
            allowed_domains=json.loads(row["allowed_domains"]) if row["allowed_domains"] else [],
            blocked_domains=json.loads(row["blocked_domains"]) if row["blocked_domains"] else [],
            egress_mode=row["egress_mode"] or "restricted",
            opa_policy_packages=json.loads(row["opa_policy_packages"]) if row["opa_policy_packages"] else [],
            guardrail_profiles=json.loads(row["guardrail_profiles"]) if row["guardrail_profiles"] else [],
            default_hitl_mode=row["default_hitl_mode"] or "optional",
            risk_thresholds=json.loads(row["risk_thresholds"]) if row["risk_thresholds"] else {},
            max_pending_hitl=row["max_pending_hitl"] or 10,
            rl_export_allowed=row["rl_export_allowed"] or False,
            rl_export_scope=row["rl_export_scope"] or "tenant",
            rl_excluded_fields=json.loads(row["rl_excluded_fields"]) if row["rl_excluded_fields"] else [],
            example_store_policy=row["example_store_policy"] or "retain",
            data_classification=row["data_classification"] or "internal",
            retention_policy_days=row["retention_policy_days"] or 365,
            installed=row["installed"] or False,
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )

