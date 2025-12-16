"""Capability Registry for multimodal tool/model discovery.

PostgreSQL-backed registry of available multimodal capabilities (tools/models)
with modality metadata, health tracking, and constraint matching for the
PolicyGraphRouter to select appropriate providers.

SRS Reference: Section 16.2 (Capability Registry)
Feature Flag: SA01_ENABLE_multimodal_capabilities
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import asyncpg

from src.core.config import cfg

__all__ = [
    "CapabilityRecord",
    "CapabilityHealth",
    "CostTier",
    "CapabilityRegistry",
]

logger = logging.getLogger(__name__)


class CapabilityHealth(str, Enum):
    """Health status for a capability (circuit breaker states)."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class CostTier(str, Enum):
    """Cost tier classification for budget filtering."""
    FREE = "free"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    PREMIUM = "premium"


@dataclass(slots=True)
class CapabilityRecord:
    """Multimodal capability registration record.
    
    Represents a tool/model with its modality support, constraints,
    cost information, and health status. Used by PolicyGraphRouter
    for capability discovery and selection.
    
    Attributes:
        tool_id: Unique identifier for the tool (e.g., 'dalle3_image_gen')  
        provider: Provider name (e.g., 'openai', 'stability', 'local')
        modalities: List of supported modalities (e.g., ['image', 'vision'])
        input_schema: JSON Schema for tool inputs
        output_schema: JSON Schema for tool outputs
        constraints: Tool-specific constraints (max_resolution, formats, etc.)
        cost_tier: Cost classification for budget filtering
        health_status: Current health status for circuit breaker integration
        latency_p95_ms: Expected P95 latency in milliseconds
        failure_count: Current failure count (for circuit breaker)
        enabled: Whether this capability is currently enabled
        tenant_id: Optional tenant-specific registration (None = global)
        display_name: Human-readable name for UI
        description: Description of the capability
        documentation_url: Link to documentation
        last_health_check: Timestamp of last health check
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    tool_id: str
    provider: str
    modalities: List[str] = field(default_factory=list)
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    cost_tier: CostTier = CostTier.MEDIUM
    health_status: CapabilityHealth = CapabilityHealth.HEALTHY
    latency_p95_ms: Optional[int] = None
    failure_count: int = 0
    enabled: bool = True
    tenant_id: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    documentation_url: Optional[str] = None
    last_health_check: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CapabilityRegistry:
    """PostgreSQL-backed registry for multimodal capabilities.
    
    Provides capability discovery, registration, and health tracking
    for the multimodal extension. Follows repository pattern consistent
    with CapsuleStore and other service layer components.
    
    Usage:
        registry = CapabilityRegistry()
        await registry.ensure_schema()
        
        # Find image generation capabilities
        candidates = await registry.find_candidates(
            modality="image",
            constraints={"max_cost_tier": "high"}
        )
        
        # Update health status (circuit breaker integration)
        await registry.update_health(
            tool_id="dalle3_image_gen",
            provider="openai",
            status=CapabilityHealth.DEGRADED
        )
    """

    def __init__(self, dsn: Optional[str] = None) -> None:
        """Initialize registry with database connection string.
        
        Args:
            dsn: PostgreSQL connection string. Defaults to config value.
        """
        self._dsn = dsn or cfg.settings().database.dsn

    async def ensure_schema(self) -> None:
        """Create the multimodal_capabilities table if not exists.
        
        This is a safety net - schema should be created by migration
        script 017_multimodal_schema.sql during deployment.
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            # Check if table exists
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'multimodal_capabilities'
                )
            """)
            if not exists:
                logger.warning(
                    "multimodal_capabilities table not found. "
                    "Run migration 017_multimodal_schema.sql to create schema."
                )
                raise RuntimeError(
                    "multimodal_capabilities table does not exist. "
                    "Database migration 017_multimodal_schema.sql must be applied."
                )
        finally:
            await conn.close()

    async def register(self, record: CapabilityRecord) -> None:
        """Register or update a capability.
        
        Uses UPSERT semantics - if capability already exists (by tool_id + provider),
        it will be updated with the new values.
        
        Args:
            record: CapabilityRecord with capability details
            
        Raises:
            asyncpg.PostgresError: On database errors
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            await conn.execute("""
                INSERT INTO multimodal_capabilities (
                    tool_id, provider, tenant_id, modalities,
                    input_schema, output_schema, constraints,
                    cost_tier, latency_p95_ms, health_status,
                    failure_count, enabled, display_name,
                    description, documentation_url
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15
                )
                ON CONFLICT (tool_id, provider) DO UPDATE SET
                    tenant_id = EXCLUDED.tenant_id,
                    modalities = EXCLUDED.modalities,
                    input_schema = EXCLUDED.input_schema,
                    output_schema = EXCLUDED.output_schema,
                    constraints = EXCLUDED.constraints,
                    cost_tier = EXCLUDED.cost_tier,
                    latency_p95_ms = EXCLUDED.latency_p95_ms,
                    health_status = EXCLUDED.health_status,
                    failure_count = EXCLUDED.failure_count,
                    enabled = EXCLUDED.enabled,
                    display_name = EXCLUDED.display_name,
                    description = EXCLUDED.description,
                    documentation_url = EXCLUDED.documentation_url,
                    updated_at = NOW()
            """,
                record.tool_id,
                record.provider,
                record.tenant_id,
                json.dumps(record.modalities),
                json.dumps(record.input_schema),
                json.dumps(record.output_schema),
                json.dumps(record.constraints),
                record.cost_tier.value,
                record.latency_p95_ms,
                record.health_status.value,
                record.failure_count,
                record.enabled,
                record.display_name,
                record.description,
                record.documentation_url,
            )
            logger.info(
                "Registered capability: %s/%s",
                record.tool_id, record.provider
            )
        finally:
            await conn.close()

    async def find_candidates(
        self,
        modality: str,
        constraints: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
        include_unhealthy: bool = False,
    ) -> List[CapabilityRecord]:
        """Find capabilities supporting a specific modality.
        
        Filters by modality presence in the modalities array and applies
        optional constraint matching. Results ordered by cost tier (cheapest first)
        and health status.
        
        Args:
            modality: Required modality (e.g., 'image', 'diagram', 'video')
            constraints: Optional constraint filters:
                - max_cost_tier: Maximum cost tier to include
                - min_latency_p95_ms: Minimum acceptable latency
                - required_formats: List of formats capability must support
            tenant_id: Filter by tenant (None = include global + tenant-specific)
            include_unhealthy: Include degraded/unavailable capabilities
            
        Returns:
            List of matching CapabilityRecord objects, ordered by cost tier
            
        Example:
            candidates = await registry.find_candidates(
                modality="image",
                constraints={"max_cost_tier": "medium"},
                tenant_id="acme-corp"
            )
        """
        constraints = constraints or {}
        conn = await asyncpg.connect(self._dsn)
        try:
            # Build query with filters
            query_parts = [
                "SELECT * FROM multimodal_capabilities",
                "WHERE enabled = TRUE",
                "AND modalities @> $1::jsonb",  # Contains modality
            ]
            params: List[Any] = [json.dumps([modality])]
            param_idx = 2

            # Health filter
            if not include_unhealthy:
                query_parts.append(f"AND health_status != ${ param_idx}")
                params.append("unavailable")
                param_idx += 1

            # Tenant filter (include global + tenant-specific)
            if tenant_id:
                query_parts.append(
                    f"AND (tenant_id IS NULL OR tenant_id = ${param_idx})"
                )
                params.append(tenant_id)
                param_idx += 1

            # Cost tier filter
            if "max_cost_tier" in constraints:
                max_tier = constraints["max_cost_tier"]
                tier_order = {t.value: i for i, t in enumerate(CostTier)}
                max_tier_idx = tier_order.get(max_tier, len(CostTier))
                allowed_tiers = [
                    t.value for t in CostTier 
                    if tier_order.get(t.value, 999) <= max_tier_idx
                ]
                param_slots = ", ".join(
                    f"${param_idx + i}" for i in range(len(allowed_tiers))
                )
                query_parts.append(f"AND cost_tier IN ({param_slots})")
                params.extend(allowed_tiers)
                param_idx += len(allowed_tiers)

            # Order by cost tier (cheapest first), then health (healthy first)
            query_parts.append("""
                ORDER BY 
                    CASE health_status 
                        WHEN 'healthy' THEN 0 
                        WHEN 'degraded' THEN 1 
                        ELSE 2 
                    END,
                    CASE cost_tier
                        WHEN 'free' THEN 0
                        WHEN 'low' THEN 1
                        WHEN 'medium' THEN 2
                        WHEN 'high' THEN 3
                        WHEN 'premium' THEN 4
                        ELSE 5
                    END
            """)

            query = " ".join(query_parts)
            rows = await conn.fetch(query, *params)
            
            results = [self._row_to_record(row) for row in rows]
            
            # Apply format constraints in-memory (JSONB nested filter is complex)
            if "required_formats" in constraints:
                required = set(constraints["required_formats"])
                results = [
                    r for r in results
                    if required <= set(r.constraints.get("formats", []))
                ]
            
            logger.debug(
                "Found %d candidates for modality=%s, constraints=%s",
                len(results), modality, constraints
            )
            return results
            
        finally:
            await conn.close()

    async def get(
        self, 
        tool_id: str, 
        provider: str
    ) -> Optional[CapabilityRecord]:
        """Get a single capability by tool_id and provider.
        
        Args:
            tool_id: Tool identifier
            provider: Provider name
            
        Returns:
            CapabilityRecord if found, None otherwise
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            row = await conn.fetchrow(
                "SELECT * FROM multimodal_capabilities WHERE tool_id = $1 AND provider = $2",
                tool_id, provider
            )
            if not row:
                return None
            return self._row_to_record(row)
        finally:
            await conn.close()

    async def list(
        self,
        modality: Optional[str] = None,
        tenant_id: Optional[str] = None,
        enabled_only: bool = True,
    ) -> List[CapabilityRecord]:
        """List all capabilities with optional filters.
        
        Args:
            modality: Filter by modality (optional)
            tenant_id: Filter by tenant (optional, includes global if set)
            enabled_only: Only return enabled capabilities
            
        Returns:
            List of CapabilityRecord objects
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            query_parts = ["SELECT * FROM multimodal_capabilities WHERE 1=1"]
            params: List[Any] = []
            param_idx = 1

            if enabled_only:
                query_parts.append("AND enabled = TRUE")

            if modality:
                query_parts.append(f"AND modalities @> ${param_idx}::jsonb")
                params.append(json.dumps([modality]))
                param_idx += 1

            if tenant_id:
                query_parts.append(
                    f"AND (tenant_id IS NULL OR tenant_id = ${param_idx})"
                )
                params.append(tenant_id)
                param_idx += 1

            query_parts.append("ORDER BY tool_id, provider")
            
            query = " ".join(query_parts)
            rows = await conn.fetch(query, *params)
            return [self._row_to_record(row) for row in rows]
        finally:
            await conn.close()

    async def update_health(
        self,
        tool_id: str,
        provider: str,
        status: CapabilityHealth,
        increment_failure: bool = False,
    ) -> bool:
        """Update health status of a capability.
        
        Called by circuit breaker integration to mark capabilities
        as degraded or unavailable when failures occur.
        
        Args:
            tool_id: Tool identifier
            provider: Provider name
            status: New health status
            increment_failure: Whether to increment failure count
            
        Returns:
            True if capability was found and updated, False otherwise
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            if increment_failure:
                result = await conn.execute(
                    """UPDATE multimodal_capabilities 
                       SET health_status = $3, 
                           failure_count = failure_count + 1,
                           last_health_check = NOW(),
                           updated_at = NOW()
                       WHERE tool_id = $1 AND provider = $2""",
                    tool_id, provider, status.value
                )
            else:
                result = await conn.execute(
                    """UPDATE multimodal_capabilities 
                       SET health_status = $3, 
                           failure_count = CASE WHEN $3 = 'healthy' THEN 0 ELSE failure_count END,
                           last_health_check = NOW(),
                           updated_at = NOW()
                       WHERE tool_id = $1 AND provider = $2""",
                    tool_id, provider, status.value
                )
            
            # Parse result like "UPDATE 1"
            _, count_str = result.split(" ")
            updated = int(count_str) > 0
            
            if updated:
                logger.info(
                    "Updated health for %s/%s to %s",
                    tool_id, provider, status.value
                )
            else:
                logger.warning(
                    "Capability %s/%s not found for health update",
                    tool_id, provider
                )
            
            return updated
        finally:
            await conn.close()

    async def reset_failure_count(
        self, 
        tool_id: str, 
        provider: str
    ) -> bool:
        """Reset failure count and mark as healthy.
        
        Called when circuit breaker recovery succeeds.
        
        Args:
            tool_id: Tool identifier
            provider: Provider name
            
        Returns:
            True if capability was found and reset, False otherwise
        """
        return await self.update_health(
            tool_id, 
            provider, 
            CapabilityHealth.HEALTHY,
            increment_failure=False
        )

    def _row_to_record(self, row: asyncpg.Record) -> CapabilityRecord:
        """Convert database row to CapabilityRecord.
        
        Handles JSON parsing and enum conversion with proper null handling.
        
        Args:
            row: asyncpg Record from query
            
        Returns:
            CapabilityRecord instance
        """
        return CapabilityRecord(
            tool_id=row["tool_id"],
            provider=row["provider"],
            modalities=json.loads(row["modalities"]) if row["modalities"] else [],
            input_schema=json.loads(row["input_schema"]) if row["input_schema"] else {},
            output_schema=json.loads(row["output_schema"]) if row["output_schema"] else {},
            constraints=json.loads(row["constraints"]) if row["constraints"] else {},
            cost_tier=CostTier(row["cost_tier"]) if row["cost_tier"] else CostTier.MEDIUM,
            health_status=CapabilityHealth(row["health_status"]) if row["health_status"] else CapabilityHealth.HEALTHY,
            latency_p95_ms=row["latency_p95_ms"],
            failure_count=row["failure_count"] or 0,
            enabled=row["enabled"] if row["enabled"] is not None else True,
            tenant_id=row["tenant_id"],
            display_name=row["display_name"],
            description=row["description"],
            documentation_url=row["documentation_url"],
            last_health_check=row["last_health_check"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
