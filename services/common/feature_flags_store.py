"""Feature flags store with PostgreSQL persistence.

This module provides database-backed feature flag management with:
- Multi-tenant support
- Environment variable override capability
- Profile-based flag management (minimal/standard/enhanced/max)
- Audit trail via timestamps
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

import asyncpg

from src.core.config import cfg

LOGGER = logging.getLogger(__name__)

# Default feature flags (14 flags from features.py)
DEFAULT_FLAGS = {
    "sse_enabled": True,
    "embeddings_ingest": False,
    "semantic_recall": True,
    "content_masking": True,
    "audio_support": False,
    "browser_support": False,
    "code_exec_support": True,
    "vision_support": True,
    "mcp_client": True,
    "mcp_server": False,
    "learning_context": False,
    "tool_sandboxing": False,
    "streaming_responses": True,
    "delegation": False,
}

# Profile defaults
PROFILE_DEFAULTS = {
    "minimal": {
        "sse_enabled": False,
        "embeddings_ingest": False,
        "semantic_recall": False,
        "content_masking": False,
        "audio_support": False,
        "browser_support": False,
        "code_exec_support": True,
        "vision_support": False,
        "mcp_client": False,
        "mcp_server": False,
        "learning_context": False,
        "tool_sandboxing": False,
        "streaming_responses": True,
        "delegation": False,
    },
    "standard": {
        "sse_enabled": True,
        "embeddings_ingest": False,
        "semantic_recall": True,
        "content_masking": True,
        "audio_support": False,
        "browser_support": False,
        "code_exec_support": True,
        "vision_support": True,
        "mcp_client": True,
        "mcp_server": False,
        "learning_context": False,
        "tool_sandboxing": False,
        "streaming_responses": True,
        "delegation": False,
    },
    "enhanced": DEFAULT_FLAGS,  # Same as default
    "max": {key: True for key in DEFAULT_FLAGS.keys()},
}


class FeatureFlagsStore:
    """PostgreSQL-backed feature flags store with multi-tenant support."""

    def __init__(self, dsn: Optional[str] = None) -> None:
        """Initialize store with database connection.
        
        Args:
            dsn: PostgreSQL connection string. If None, uses cfg.settings().database.dsn
        """
        raw_dsn = dsn or cfg.settings().database.dsn
        self.dsn = os.path.expandvars(raw_dsn)
        self._pool: Optional[asyncpg.Pool] = None

    async def _ensure_pool(self) -> asyncpg.Pool:
        """Create or retrieve asyncpg connection pool.
        
        Returns:
            asyncpg.Pool: Database connection pool
        """
        if self._pool is None:
            min_size = int(cfg.env("PG_POOL_MIN_SIZE", "1") or "1")
            max_size = int(cfg.env("PG_POOL_MAX_SIZE", "2") or "2")
            self._pool = await asyncpg.create_pool(
                self.dsn,
                min_size=max(0, min_size),
                max_size=max(1, max_size),
            )
        return self._pool

    async def ensure_schema(self) -> None:
        """Create feature_flags table if it doesn't exist."""
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS feature_flags (
                    id SERIAL PRIMARY KEY,
                    key TEXT NOT NULL,
                    enabled BOOLEAN NOT NULL DEFAULT false,
                    profile_override TEXT CHECK (profile_override IN ('minimal', 'standard', 'enhanced', 'max')),
                    tenant TEXT NOT NULL DEFAULT 'default',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE(tenant, key)
                );
                
                CREATE INDEX IF NOT EXISTS idx_feature_flags_tenant 
                ON feature_flags(tenant, key);
                """
            )
            LOGGER.info("feature_flags table schema ensured")

    async def get_flags(self, tenant: str = "default") -> dict[str, bool]:
        """Get all feature flags for a tenant.
        
        Args:
            tenant: Tenant identifier
            
        Returns:
            Dictionary mapping flag keys to enabled status
        """
        await self.ensure_schema()
        pool = await self._ensure_pool()
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT key, enabled FROM feature_flags WHERE tenant = $1",
                tenant
            )
            
            if not rows:
                # No flags in database, return defaults
                return DEFAULT_FLAGS.copy()
            
            return {row["key"]: row["enabled"] for row in rows}

    async def set_flag(
        self, 
        tenant: str, 
        key: str, 
        enabled: bool
    ) -> bool:
        """Set a single feature flag.
        
        Args:
            tenant: Tenant identifier
            key: Flag key (e.g., 'sse_enabled')
            enabled: Whether flag is enabled
            
        Returns:
            True if flag was set successfully
        """
        await self.ensure_schema()
        pool = await self._ensure_pool()
        
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO feature_flags (tenant, key, enabled, updated_at)
                VALUES ($1, $2, $3, NOW())
                ON CONFLICT (tenant, key) 
                DO UPDATE SET enabled = $3, updated_at = NOW()
                """,
                tenant, key, enabled
            )
            LOGGER.info(f"Feature flag set: {tenant}/{key} = {enabled}")
            return True

    async def get_profile(self, tenant: str = "default") -> str:
        """Get the feature profile for a tenant.
        
        Args:
            tenant: Tenant identifier
            
        Returns:
            Profile name (minimal/standard/enhanced/max) or 'enhanced' as default
        """
        await self.ensure_schema()
        pool = await self._ensure_pool()
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT profile_override 
                FROM feature_flags 
                WHERE tenant = $1 AND profile_override IS NOT NULL
                LIMIT 1
                """,
                tenant
            )
            return row["profile_override"] if row else "enhanced"

    async def set_profile(self, tenant: str, profile: str) -> bool:
        """Set feature profile and apply all profile defaults.
        
        Args:
            tenant: Tenant identifier
            profile: Profile name (minimal/standard/enhanced/max)
            
        Returns:
            True if profile was set successfully
            
        Raises:
            ValueError: If profile is invalid
        """
        if profile not in PROFILE_DEFAULTS:
            raise ValueError(
                f"Invalid profile '{profile}'. "
                f"Must be one of: {list(PROFILE_DEFAULTS.keys())}"
            )
        
        await self.ensure_schema()
        pool = await self._ensure_pool()
        
        profile_flags = PROFILE_DEFAULTS[profile]
        
        async with pool.acquire() as conn:
            # Set all flags for this profile
            for key, enabled in profile_flags.items():
                await conn.execute(
                    """
                    INSERT INTO feature_flags (tenant, key, enabled, profile_override, updated_at)
                    VALUES ($1, $2, $3, $4, NOW())
                    ON CONFLICT (tenant, key) 
                    DO UPDATE SET enabled = $3, profile_override = $4, updated_at = NOW()
                    """,
                    tenant, key, enabled, profile
                )
            
            LOGGER.info(f"Feature profile set: {tenant} -> {profile}")
            return True

    async def list_all_flags(self) -> list[str]:
        """List all available feature flag keys.
        
        Returns:
            List of flag keys
        """
        return list(DEFAULT_FLAGS.keys())

    async def delete_tenant_flags(self, tenant: str) -> int:
        """Delete all flags for a tenant (for cleanup/testing).
        
        Args:
            tenant: Tenant identifier
            
        Returns:
            Number of flags deleted
        """
        await self.ensure_schema()
        pool = await self._ensure_pool()
        
        async with pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM feature_flags WHERE tenant = $1",
                tenant
            )
            # Extract count from result string like "DELETE 5"
            count = int(result.split()[-1]) if result else 0
            LOGGER.info(f"Deleted {count} feature flags for tenant: {tenant}")
            return count

    async def get_effective_flags(
        self, 
        tenant: str = "default"
    ) -> dict[str, Any]:
        """Get effective flags with environment variable overrides.
        
        Priority: Environment > Database > Defaults
        
        Args:
            tenant: Tenant identifier
            
        Returns:
            Dictionary with 'profile', 'flags', and metadata
        """
        db_flags = await self.get_flags(tenant)
        profile = await self.get_profile(tenant)
        
        effective_flags = {}
        for key in DEFAULT_FLAGS.keys():
            env_key = f"SA01_ENABLE_{key}".upper()
            env_value = cfg.env(env_key)
            
            if env_value is not None:
                # Environment override
                enabled = env_value.lower() in ("true", "1", "yes", "on")
                effective_flags[key] = {
                    "enabled": enabled,
                    "source": "environment",
                    "env_var": env_key
                }
            else:
                # Database value or default
                enabled = db_flags.get(key, DEFAULT_FLAGS[key])
                effective_flags[key] = {
                    "enabled": enabled,
                    "source": "database" if key in db_flags else "default"
                }
        
        return {
            "profile": profile,
            "flags": effective_flags,
            "tenant": tenant
        }
