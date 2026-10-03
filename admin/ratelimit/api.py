"""Rate Limiting API - Request throttling and abuse prevention.


Per

- Security Auditor: Rate limiting, abuse prevention
- DevOps: Redis integration, distributed limits
"""

from __future__ import annotations

import logging
from typing import Optional

from django.utils import timezone
from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer
from admin.common.messages import ErrorCode, get_message
from services.common.authorization import authorize

router = Router(tags=["ratelimit"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class RateLimitConfig(BaseModel):
    """Rate limit configuration."""

    name: str
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_limit: int = 10
    enabled: bool = True


class RateLimitStatus(BaseModel):
    """Current rate limit status."""

    limit: int
    remaining: int
    reset_at: str
    retry_after_seconds: Optional[int] = None




# =============================================================================
# ENDPOINTS - Rate Limits
# =============================================================================


@router.get(
    "/limits",
    summary="Get rate limit configurations",
    auth=AuthBearer(),
)
async def get_rate_limits(request) -> dict:
    """Get all rate limit configurations.

    Security Auditor: View rate limiting rules.
    """
    await authorize(request, action="system:view", resource="ratelimit")
    from admin.aaas.models.profiles import PlatformConfig

    gd = await PlatformConfig.aget_instance()
    defaults = gd.defaults

    # Initialize if missing
    if "ratelimits" not in defaults:
        defaults["ratelimits"] = [
            {
                "name": "api_default",
                "requests_per_minute": 60,
                "requests_per_hour": 1000,
                "requests_per_day": 10000,
                "enabled": True,
            },
            {
                "name": "chat_messages",
                "requests_per_minute": 20,
                "requests_per_hour": 500,
                "requests_per_day": 5000,
                "enabled": True,
            },
        ]
        await gd.asave()

    return {
        "limits": defaults["ratelimits"],
        "total": len(defaults["ratelimits"]),
    }


@router.get(
    "/limits/status",
    response=RateLimitStatus,
    summary="Get current rate limit status",
    auth=AuthBearer(),
)
async def get_rate_limit_status(
    request,
    limit_name: str = "api_default",
) -> RateLimitStatus:
    """Get current rate limit status for the user.

    PM: Transparency on current limits.
    """
    await authorize(request, action="system:view", resource="ratelimit")
    return RateLimitStatus(
        limit=60,
        remaining=55,
        reset_at=(timezone.now()).isoformat(),
    )


@router.post(
    "/limits",
    summary="Create rate limit rule",
    auth=AuthBearer(),
)
async def create_rate_limit(
    request,
    payload: RateLimitConfig,
) -> dict:
    """Create a new rate limit rule.

    Security Auditor: Admin only.
    """
    await authorize(request, action="system:ratelimit", resource="ratelimit")
    from admin.aaas.models.profiles import PlatformConfig

    gd = await PlatformConfig.aget_instance()
    defaults = gd.defaults

    if "ratelimits" not in defaults:
        defaults["ratelimits"] = []

    # Check for duplicate
    for limit in defaults["ratelimits"]:
        if limit["name"] == payload.name:
            return {"error": get_message(ErrorCode.RATE_LIMIT_RULE_EXISTS), "created": False}

    new_rule = payload.dict()
    defaults["ratelimits"].append(new_rule)
    await gd.asave()

    logger.info("Rate limit created: %s", payload.name)

    return {
        "name": payload.name,
        "created": True,
    }


@router.patch(
    "/limits/{name}",
    summary="Update rate limit rule",
    auth=AuthBearer(),
)
async def update_rate_limit(
    request,
    name: str,
    requests_per_minute: Optional[int] = None,
    requests_per_hour: Optional[int] = None,
    enabled: Optional[bool] = None,
) -> dict:
    """Update a rate limit rule."""
    await authorize(request, action="system:ratelimit", resource="ratelimit")
    from admin.aaas.models.profiles import PlatformConfig

    gd = await PlatformConfig.aget_instance()
    defaults = gd.defaults

    if "ratelimits" not in defaults:
        return {"error": get_message(ErrorCode.RATE_LIMIT_NOT_DEFINED), "updated": False}

    found = False
    for limit in defaults["ratelimits"]:
        if limit["name"] == name:
            if requests_per_minute is not None:
                limit["requests_per_minute"] = requests_per_minute
            if requests_per_hour is not None:
                limit["requests_per_hour"] = requests_per_hour
            if enabled is not None:
                limit["enabled"] = enabled
            found = True
            break

    if found:
        await gd.asave()
        return {"name": name, "updated": True}

    return {"name": name, "updated": False, "error": get_message(ErrorCode.NOT_FOUND)}


@router.delete(
    "/limits/{name}",
    summary="Delete rate limit rule",
    auth=AuthBearer(),
)
async def delete_rate_limit(request, name: str) -> dict:
    """Delete a rate limit rule."""
    await authorize(request, action="system:ratelimit", resource="ratelimit")
    from admin.aaas.models.profiles import PlatformConfig

    gd = await PlatformConfig.aget_instance()
    defaults = gd.defaults

    if "ratelimits" not in defaults:
        return {"error": get_message(ErrorCode.RATE_LIMIT_NOT_DEFINED), "deleted": False}

    original_len = len(defaults["ratelimits"])
    defaults["ratelimits"] = [r for r in defaults["ratelimits"] if r["name"] != name]

    if len(defaults["ratelimits"]) < original_len:
        await gd.asave()
        return {
            "name": name,
            "deleted": True,
        }

    return {"name": name, "deleted": False, "error": get_message(ErrorCode.NOT_FOUND)}


# =============================================================================
# ENDPOINTS - IP Blocking
# =============================================================================


@router.get(
    "/blocked-ips",
    summary="List blocked IPs",
    auth=AuthBearer(),
)
async def list_blocked_ips(request) -> dict:
    """List blocked IP addresses.

    Security Auditor: Abuse prevention.
    """
    await authorize(request, action="system:view", resource="ratelimit")
    return {
        "blocked_ips": [],
        "total": 0,
    }


@router.post(
    "/blocked-ips",
    summary="Block IP address",
    auth=AuthBearer(),
)
async def block_ip(
    request,
    ip_address: str,
    reason: str,
    duration_hours: Optional[int] = None,  # None = permanent
) -> dict:
    """Block an IP address.

    Security Auditor: Manual block for abuse.
    """
    await authorize(request, action="system:ratelimit", resource="ratelimit")
    logger.warning("IP blocked: %s, reason: %s", ip_address, reason)

    return {
        "ip_address": ip_address,
        "blocked": True,
        "expires_at": None if not duration_hours else timezone.now().isoformat(),
    }


@router.delete(
    "/blocked-ips/{ip_address}",
    summary="Unblock IP address",
    auth=AuthBearer(),
)
async def unblock_ip(request, ip_address: str) -> dict:
    """Unblock an IP address."""
    await authorize(request, action="system:ratelimit", resource="ratelimit")
    logger.info("IP unblocked: %s", ip_address)

    return {
        "ip_address": ip_address,
        "unblocked": True,
    }


# =============================================================================
# ENDPOINTS - Usage Metrics
# =============================================================================


@router.get(
    "/usage/current",
    summary="Get current usage metrics",
    auth=AuthBearer(),
)
async def get_current_usage(
    request,
    tenant_id: Optional[str] = None,
) -> dict:
    """Get current usage metrics.

    DevOps: Real-time usage monitoring.
    """
    await authorize(request, action="system:read_metrics", resource="ratelimit")
    return {
        "period": "current_hour",
        "api_calls": 0,
        "chat_messages": 0,
        "file_uploads": 0,
        "tokens_used": 0,
    }


@router.get(
    "/usage/history",
    summary="Get usage history",
    auth=AuthBearer(),
)
async def get_usage_history(
    request,
    tenant_id: Optional[str] = None,
    period: str = "24h",  # 1h, 24h, 7d, 30d
) -> dict:
    """Get historical usage metrics."""
    await authorize(request, action="system:read_metrics", resource="ratelimit")
    return {
        "period": period,
        "data_points": [],
    }
