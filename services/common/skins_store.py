"""Skins store using PostgreSQL for persistence.

PostgreSQL-backed store for AgentSkin theme definitions.
Schema defined in migrations/versions/003_add_agent_skins.py.

Per AgentSkin UIX Task 8 (TR-AGS-004, TR-AGS-005).
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import asyncpg

from src.core.config import cfg

__all__ = ["SkinRecord", "SkinsStore", "validate_no_xss"]


# XSS patterns to reject in CSS values (SEC-AGS-002)
XSS_PATTERNS = [
    re.compile(r"url\s*\(", re.IGNORECASE),
    re.compile(r"<script", re.IGNORECASE),
    re.compile(r"javascript:", re.IGNORECASE),
    re.compile(r"expression\s*\(", re.IGNORECASE),
    re.compile(r"@import", re.IGNORECASE),
]


def validate_no_xss(variables: Dict[str, str]) -> None:
    """Validate that CSS variables contain no XSS patterns.
    
    Raises ValueError if any XSS pattern is detected.
    Per SEC-AGS-002.1 - SEC-AGS-002.3.
    """
    for key, value in variables.items():
        if not isinstance(value, str):
            continue
        for pattern in XSS_PATTERNS:
            if pattern.search(value):
                raise ValueError(f"XSS pattern detected in variable '{key}': {pattern.pattern}")


@dataclass(slots=True)
class SkinRecord:
    """AgentSkin theme record per TR-AGS-005."""
    
    skin_id: str
    tenant_id: str
    name: str
    version: str
    description: str = ""
    author: str = ""
    variables: Dict[str, str] = field(default_factory=dict)
    changelog: List[Dict[str, Any]] = field(default_factory=list)
    is_approved: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SkinsStore:
    """PostgreSQL-backed store for AgentSkin theme definitions."""

    def __init__(self, dsn: str | None = None) -> None:
        self._dsn = dsn or cfg.settings().database.dsn

    async def ensure_schema(self) -> None:
        """Verify agent_skins table exists.
        
        Schema is created by migration 003_add_agent_skins.py.
        This method verifies the table exists and logs a warning if not.
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'agent_skins'
                )
            """)
            if not exists:
                import logging
                logging.getLogger(__name__).error(
                    "agent_skins table does not exist. Run migration 003_add_agent_skins.py"
                )
                raise RuntimeError("agent_skins table not found - run migrations")
        finally:
            await conn.close()

    async def list(
        self,
        tenant_id: str,
        include_unapproved: bool = False,
    ) -> List[SkinRecord]:
        """List skins for a tenant.
        
        Args:
            tenant_id: Tenant UUID to filter by
            include_unapproved: If True, include unapproved skins (admin only)
        
        Returns:
            List of SkinRecord objects
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            if include_unapproved:
                # Admin view: all skins for tenant
                rows = await conn.fetch(
                    """SELECT * FROM agent_skins 
                       WHERE tenant_id = $1::uuid 
                          OR tenant_id = '00000000-0000-0000-0000-000000000000'::uuid
                       ORDER BY name, version""",
                    tenant_id,
                )
            else:
                # User view: only approved skins
                rows = await conn.fetch(
                    """SELECT * FROM agent_skins 
                       WHERE (tenant_id = $1::uuid 
                          OR tenant_id = '00000000-0000-0000-0000-000000000000'::uuid)
                         AND is_approved = TRUE
                       ORDER BY name, version""",
                    tenant_id,
                )
            return [self._row_to_record(r) for r in rows]
        finally:
            await conn.close()

    async def get(self, skin_id: str) -> Optional[SkinRecord]:
        """Get a single skin by ID."""
        conn = await asyncpg.connect(self._dsn)
        try:
            row = await conn.fetchrow(
                "SELECT * FROM agent_skins WHERE id = $1::uuid",
                skin_id,
            )
            if not row:
                return None
            return self._row_to_record(row)
        finally:
            await conn.close()

    async def get_by_name(self, tenant_id: str, name: str) -> Optional[SkinRecord]:
        """Get a skin by tenant and name (unique key)."""
        conn = await asyncpg.connect(self._dsn)
        try:
            row = await conn.fetchrow(
                """SELECT * FROM agent_skins 
                   WHERE tenant_id = $1::uuid AND name = $2""",
                tenant_id, name,
            )
            if not row:
                return None
            return self._row_to_record(row)
        finally:
            await conn.close()

    async def create(self, record: SkinRecord) -> str:
        """Create a new skin. Returns skin_id.
        
        Validates XSS patterns before insertion.
        """
        # Validate no XSS patterns
        validate_no_xss(record.variables)
        
        conn = await asyncpg.connect(self._dsn)
        try:
            skin_id = record.skin_id or str(uuid.uuid4())
            await conn.execute(
                """INSERT INTO agent_skins (
                    id, tenant_id, name, description, version, author,
                    variables, changelog, is_approved
                ) VALUES (
                    $1::uuid, $2::uuid, $3, $4, $5, $6,
                    $7::jsonb, $8::jsonb, $9
                )""",
                skin_id,
                record.tenant_id,
                record.name,
                record.description,
                record.version,
                record.author,
                json.dumps(record.variables),
                json.dumps(record.changelog),
                record.is_approved,
            )
            return skin_id
        finally:
            await conn.close()

    async def update(self, skin_id: str, updates: Dict[str, Any]) -> bool:
        """Update a skin's fields.
        
        Args:
            skin_id: Skin UUID
            updates: Dict of field names to new values
        
        Returns:
            True if skin was updated, False if not found
        """
        if "variables" in updates:
            validate_no_xss(updates["variables"])
        
        conn = await asyncpg.connect(self._dsn)
        try:
            # Build dynamic UPDATE query
            set_clauses = []
            params = [skin_id]
            param_idx = 2
            
            allowed_fields = {
                "name", "description", "version", "author",
                "variables", "changelog", "is_approved"
            }
            
            for field_name, value in updates.items():
                if field_name not in allowed_fields:
                    continue
                if field_name in ("variables", "changelog"):
                    set_clauses.append(f"{field_name} = ${param_idx}::jsonb")
                    params.append(json.dumps(value))
                else:
                    set_clauses.append(f"{field_name} = ${param_idx}")
                    params.append(value)
                param_idx += 1
            
            if not set_clauses:
                return False
            
            query = f"UPDATE agent_skins SET {', '.join(set_clauses)} WHERE id = $1::uuid"
            result = await conn.execute(query, *params)
            _, count_str = result.split(" ")
            return int(count_str) > 0
        finally:
            await conn.close()

    async def delete(self, skin_id: str) -> bool:
        """Delete a skin by ID.
        
        Returns True if deleted, False if not found.
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            result = await conn.execute(
                "DELETE FROM agent_skins WHERE id = $1::uuid",
                skin_id,
            )
            _, count_str = result.split(" ")
            return int(count_str) > 0
        finally:
            await conn.close()

    async def approve(self, skin_id: str) -> bool:
        """Approve a skin (set is_approved = TRUE).
        
        Returns True if updated, False if not found.
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            result = await conn.execute(
                "UPDATE agent_skins SET is_approved = TRUE WHERE id = $1::uuid",
                skin_id,
            )
            _, count_str = result.split(" ")
            return int(count_str) > 0
        finally:
            await conn.close()

    async def reject(self, skin_id: str) -> bool:
        """Reject a skin (set is_approved = FALSE).
        
        Returns True if updated, False if not found.
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            result = await conn.execute(
                "UPDATE agent_skins SET is_approved = FALSE WHERE id = $1::uuid",
                skin_id,
            )
            _, count_str = result.split(" ")
            return int(count_str) > 0
        finally:
            await conn.close()

    def _row_to_record(self, row: asyncpg.Record) -> SkinRecord:
        """Convert a database row to SkinRecord."""
        variables = row["variables"]
        if isinstance(variables, str):
            variables = json.loads(variables)
        
        changelog = row["changelog"]
        if isinstance(changelog, str):
            changelog = json.loads(changelog)
        elif changelog is None:
            changelog = []
        
        return SkinRecord(
            skin_id=str(row["id"]),
            tenant_id=str(row["tenant_id"]),
            name=row["name"],
            version=row["version"],
            description=row["description"] or "",
            author=row["author"] or "",
            variables=variables or {},
            changelog=changelog,
            is_approved=row["is_approved"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
