"""Capsule store using PostgreSQL for persistence.

Replaces the in-memory store with a persistent implementation backed by the
`capsules` table.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any

import asyncpg

from src.core.config import cfg

__all__ = ["CapsuleRecord", "CapsuleStore"]


@dataclass(slots=True)
class CapsuleRecord:
    """Public representation of a capsule."""

    capsule_id: str
    name: str | None = None
    installed: bool = False
    metadata: Dict[str, Any] | None = None


class CapsuleStore:
    """PostgreSQL-backed store for capsules."""

    def __init__(self, dsn: str | None = None) -> None:
        self._dsn = dsn or cfg.settings().database.dsn

    async def ensure_schema(self) -> None:
        """Create the capsules table if it doesn't exist."""
        conn = await asyncpg.connect(self._dsn)
        try:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS capsules (
                    capsule_id TEXT PRIMARY KEY,
                    name TEXT,
                    installed BOOLEAN DEFAULT FALSE,
                    metadata JSONB DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """
            )
            # Table is created but we do NOT seed mock data in production.
            # Real capsules should be installed via the API or a migration script.
            pass
        finally:
            await conn.close()

    async def list(self) -> List[CapsuleRecord]:
        """List all capsules."""
        conn = await asyncpg.connect(self._dsn)
        try:
            rows = await conn.fetch("SELECT capsule_id, name, installed, metadata FROM capsules ORDER BY capsule_id")
            return [
                CapsuleRecord(
                    capsule_id=r["capsule_id"],
                    name=r["name"],
                    installed=r["installed"],
                    metadata=json.loads(r["metadata"]) if r["metadata"] else {},
                )
                for r in rows
            ]
        finally:
            await conn.close()

    async def get(self, capsule_id: str) -> Optional[CapsuleRecord]:
        """Get a single capsule by ID."""
        conn = await asyncpg.connect(self._dsn)
        try:
            row = await conn.fetchrow(
                "SELECT capsule_id, name, installed, metadata FROM capsules WHERE capsule_id = $1",
                capsule_id,
            )
            if not row:
                return None
            return CapsuleRecord(
                capsule_id=row["capsule_id"],
                name=row["name"],
                installed=row["installed"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            )
        finally:
            await conn.close()

    async def install(self, capsule_id: str) -> bool:
        """Mark the capsule as installed.

        Returns True if successful (capsule existed), False otherwise.
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            # Check if exists first? Or just update and check rowcount.
            # Only update if it exists.
            result = await conn.execute(
                "UPDATE capsules SET installed = TRUE, updated_at = NOW() WHERE capsule_id = $1",
                capsule_id,
            )
            # format is usually "UPDATE 1"
            _, count_str = result.split(" ")
            count = int(count_str)
            return count > 0
        finally:
            await conn.close()
