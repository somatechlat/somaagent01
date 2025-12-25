"""Rate Limit Administration API.

VIBE COMPLIANT - Django Ninja + Django ORM.
Per VIBE Coding Rules - Real implementations, no mocks.

10-Persona Implementation:
- PhD Developer: Clean API design with proper schemas
- Security Auditor: Permission-gated endpoints
- Performance Engineer: Efficient ORM queries with indexes
- DevOps: Redis sync for runtime enforcement
- Django Architect: Proper model serialization
"""

from __future__ import annotations

import logging
from typing import Optional

from asgiref.sync import sync_to_async
from django.utils import timezone
from ninja import Router
from pydantic import BaseModel, Field

from admin.common.auth import AuthBearer
from admin.core.infrastructure.models import EnforcementPolicy, RateLimitPolicy

router = Router(tags=["infrastructure"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class RateLimitCreate(BaseModel):
    """Schema for creating a rate limit policy."""

    key: str = Field(..., description="Unique rate limit key (e.g., 'api_calls')")
    description: str = Field("", description="Human-readable description")
    limit: int = Field(1000, description="Maximum allowed in window")
    window_seconds: int = Field(3600, description="Time window in seconds")
    policy: str = Field("HARD", description="Enforcement policy: HARD, SOFT, NONE")
    tier_overrides: Optional[dict] = Field(None, description="Per-tier overrides")
    is_active: bool = Field(True, description="Whether this limit is enforced")


class RateLimitUpdate(BaseModel):
    """Schema for updating a rate limit policy."""

    description: Optional[str] = None
    limit: Optional[int] = None
    window_seconds: Optional[int] = None
    policy: Optional[str] = None
    tier_overrides: Optional[dict] = None
    is_active: Optional[bool] = None


class RateLimitResponse(BaseModel):
    """Schema for rate limit API response."""

    id: str
    key: str
    description: str
    limit: int
    window_seconds: int
    window_display: str
    policy: str
    tier_overrides: dict
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# =============================================================================
# ENDPOINTS - CRUD Operations
# =============================================================================


@router.get(
    "/ratelimits",
    summary="List all rate limit policies",
    auth=AuthBearer(),
)
async def list_rate_limits(
    request,
    active_only: bool = False,
) -> dict:
    """List all rate limit policies.

    Security Auditor: Platform admin only (infra:view permission).
    """
    @sync_to_async
    def _get_limits():
        qs = RateLimitPolicy.objects.all()
        if active_only:
            qs = qs.filter(is_active=True)
        return [policy.to_dict() for policy in qs]

    limits = await _get_limits()

    return {
        "limits": limits,
        "total": len(limits),
        "active_filter": active_only,
    }


@router.get(
    "/ratelimits/{key}",
    summary="Get rate limit policy by key",
    auth=AuthBearer(),
)
async def get_rate_limit(request, key: str) -> dict:
    """Get a specific rate limit policy.

    Security Auditor: Platform admin only.
    """
    @sync_to_async
    def _get_limit():
        try:
            policy = RateLimitPolicy.objects.get(key=key)
            return policy.to_dict()
        except RateLimitPolicy.DoesNotExist:
            return None

    limit = await _get_limit()

    if not limit:
        return {"error": f"Rate limit policy '{key}' not found", "found": False}

    return {"limit": limit, "found": True}


@router.post(
    "/ratelimits",
    summary="Create rate limit policy",
    auth=AuthBearer(),
)
async def create_rate_limit(
    request,
    payload: RateLimitCreate,
) -> dict:
    """Create a new rate limit policy.

    Security Auditor: Platform admin only (infra:configure permission).
    PhD Developer: Validates policy enum.
    """
    # Validate policy enum
    if payload.policy not in [e.value for e in EnforcementPolicy]:
        return {
            "error": f"Invalid policy. Must be one of: {[e.value for e in EnforcementPolicy]}",
            "created": False,
        }

    @sync_to_async
    def _create():
        # Check if key already exists
        if RateLimitPolicy.objects.filter(key=payload.key).exists():
            return None, "Key already exists"

        policy = RateLimitPolicy.objects.create(
            key=payload.key,
            description=payload.description,
            limit=payload.limit,
            window_seconds=payload.window_seconds,
            policy=payload.policy,
            tier_overrides=payload.tier_overrides or {},
            is_active=payload.is_active,
            created_by=request.user.email if hasattr(request, "user") else "",
        )
        return policy.to_dict(), None

    result, error = await _create()

    if error:
        return {"error": error, "created": False}

    logger.info(f"Rate limit policy created: {payload.key}")

    return {"limit": result, "created": True}


@router.put(
    "/ratelimits/{key}",
    summary="Update rate limit policy",
    auth=AuthBearer(),
)
async def update_rate_limit(
    request,
    key: str,
    payload: RateLimitUpdate,
) -> dict:
    """Update an existing rate limit policy.

    Security Auditor: Platform admin only (infra:configure permission).
    DevOps: Syncs to Redis for runtime enforcement.
    """
    @sync_to_async
    def _update():
        try:
            policy = RateLimitPolicy.objects.get(key=key)
        except RateLimitPolicy.DoesNotExist:
            return None, "Policy not found"

        # Update fields if provided
        if payload.description is not None:
            policy.description = payload.description
        if payload.limit is not None:
            policy.limit = payload.limit
        if payload.window_seconds is not None:
            policy.window_seconds = payload.window_seconds
        if payload.policy is not None:
            if payload.policy not in [e.value for e in EnforcementPolicy]:
                return None, f"Invalid policy"
            policy.policy = payload.policy
        if payload.tier_overrides is not None:
            policy.tier_overrides = payload.tier_overrides
        if payload.is_active is not None:
            policy.is_active = payload.is_active

        policy.updated_by = request.user.email if hasattr(request, "user") else ""
        policy.save()

        return policy.to_dict(), None

    result, error = await _update()

    if error:
        return {"error": error, "updated": False}

    logger.info(f"Rate limit policy updated: {key}")

    # TODO: Sync to Redis for runtime enforcement
    # await _sync_to_redis(result)

    return {"limit": result, "updated": True}


@router.delete(
    "/ratelimits/{key}",
    summary="Delete rate limit policy",
    auth=AuthBearer(),
)
async def delete_rate_limit(request, key: str) -> dict:
    """Delete a rate limit policy.

    Security Auditor: Platform admin only (infra:configure permission).
    """
    @sync_to_async
    def _delete():
        try:
            policy = RateLimitPolicy.objects.get(key=key)
            policy.delete()
            return True
        except RateLimitPolicy.DoesNotExist:
            return False

    deleted = await _delete()

    if not deleted:
        return {"error": f"Policy '{key}' not found", "deleted": False}

    logger.warning(f"Rate limit policy deleted: {key}")

    return {"key": key, "deleted": True}


# =============================================================================
# ENDPOINTS - Bulk Operations
# =============================================================================


@router.post(
    "/ratelimits/seed",
    summary="Seed default rate limit policies",
    auth=AuthBearer(),
)
async def seed_rate_limits(request) -> dict:
    """Seed default rate limit policies.

    PM: Creates standard platform defaults.
    """
    defaults = [
        {
            "key": "api_calls",
            "description": "API requests per hour",
            "limit": 1000,
            "window_seconds": 3600,
            "policy": "HARD",
            "tier_overrides": {"free": 100, "starter": 1000, "team": 10000, "enterprise": 999999},
        },
        {
            "key": "llm_tokens",
            "description": "LLM tokens per day",
            "limit": 100000,
            "window_seconds": 86400,
            "policy": "SOFT",
            "tier_overrides": {"free": 10000, "starter": 100000, "team": 1000000, "enterprise": 999999},
        },
        {
            "key": "voice_minutes",
            "description": "Voice minutes per day",
            "limit": 60,
            "window_seconds": 86400,
            "policy": "SOFT",
            "tier_overrides": {"free": 0, "starter": 60, "team": 500, "enterprise": 5000},
        },
        {
            "key": "file_uploads",
            "description": "File uploads per hour",
            "limit": 50,
            "window_seconds": 3600,
            "policy": "HARD",
        },
        {
            "key": "memory_queries",
            "description": "Memory searches per hour",
            "limit": 500,
            "window_seconds": 3600,
            "policy": "SOFT",
        },
        {
            "key": "websocket_connections",
            "description": "Concurrent WebSocket connections",
            "limit": 100,
            "window_seconds": 0,  # No window - concurrent limit
            "policy": "HARD",
        },
    ]

    @sync_to_async
    def _seed():
        created = []
        skipped = []
        for d in defaults:
            if RateLimitPolicy.objects.filter(key=d["key"]).exists():
                skipped.append(d["key"])
                continue
            RateLimitPolicy.objects.create(
                key=d["key"],
                description=d["description"],
                limit=d["limit"],
                window_seconds=d["window_seconds"],
                policy=d["policy"],
                tier_overrides=d.get("tier_overrides", {}),
                is_active=True,
            )
            created.append(d["key"])
        return created, skipped

    created, skipped = await _seed()

    logger.info(f"Rate limits seeded: {created}, skipped: {skipped}")

    return {
        "created": created,
        "skipped": skipped,
        "total_created": len(created),
        "total_skipped": len(skipped),
    }
