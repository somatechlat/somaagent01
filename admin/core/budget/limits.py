"""Budget Limits — Plan-Based Limit Resolution.

SRS Source: SRS-BUDGET-SYSTEM-2026-01-16 Section 6

Applied Personas:
- PhD Analyst: Complete plan matrix
- Security Auditor: Fail-closed defaults
- Performance Engineer: Cache-first lookup
- Django Architect: Django cache integration
- Django Infra: Redis-compatible

Vibe Coding Rules:
- NO hardcoded values in decorators
- ALL limits from this module or database
- Redis cache for performance
"""

from __future__ import annotations

import logging
from typing import Optional

from django.core.cache import cache

from admin.core.budget.registry import get_metric

logger = logging.getLogger(__name__)


# =============================================================================
# PLAN LIMIT MATRIX — Single Source of Truth
# =============================================================================

PLAN_LIMITS: dict[str, dict[str, int]] = {
    # Free tier — minimal limits
    "free": {
        "tokens": 100_000,
        "tool_calls": 100,
        "images": 10,
        "voice_minutes": 10,
        "api_calls": 10_000,
        "memory_tokens": 500_000,
        "vector_ops": 50_000,
        "learning": 100,
        "storage_gb": 10,
        "sessions": 5,
    },
    # Starter tier — $29/month
    "starter": {
        "tokens": 1_000_000,
        "tool_calls": 1_000,
        "images": 100,
        "voice_minutes": 60,
        "api_calls": 100_000,
        "memory_tokens": 2_000_000,
        "vector_ops": 200_000,
        "learning": 1_000,
        "storage_gb": 50,
        "sessions": 10,
    },
    # Team tier — $99/month
    "team": {
        "tokens": 10_000_000,
        "tool_calls": 10_000,
        "images": 1_000,
        "voice_minutes": 300,
        "api_calls": 1_000_000,
        "memory_tokens": 10_000_000,
        "vector_ops": 1_000_000,
        "learning": 10_000,
        "storage_gb": 200,
        "sessions": 50,
    },
    # Enterprise tier — custom pricing
    "enterprise": {
        "tokens": 100_000_000,
        "tool_calls": -1,  # -1 = Unlimited
        "images": 10_000,
        "voice_minutes": -1,  # Unlimited
        "api_calls": -1,  # Unlimited
        "memory_tokens": -1,  # Unlimited
        "vector_ops": -1,  # Unlimited
        "learning": -1,  # Unlimited
        "storage_gb": 1_000,
        "sessions": -1,  # Unlimited
    },
}

# Cache TTL settings
PLAN_CACHE_TTL = 3600  # 1 hour for plan code
USAGE_CACHE_TTL = 300  # 5 minutes for usage


def get_tenant_plan(tenant_id: str) -> str:
    """Get tenant's subscription plan code.

    Checks cache first, then falls back to database.

    Args:
        tenant_id: Tenant identifier

    Returns:
        Plan code (e.g., "free", "starter", "team", "enterprise")
    """
    cache_key = f"plan:{tenant_id}"
    cached_plan = cache.get(cache_key)

    if cached_plan:
        return cached_plan

    # Fall back to database
    try:
        from admin.aaas.models import Tenant

        tenant = Tenant.objects.select_related("subscription_tier").get(pk=tenant_id)
        plan_code = tenant.subscription_tier.code if tenant.subscription_tier else "free"
        cache.set(cache_key, plan_code, PLAN_CACHE_TTL)
        return plan_code
    except Exception as exc:
        logger.warning("Failed to get tenant plan, defaulting to free: %s", exc)
        return "free"


def get_metric_limit(tenant_id: str, metric: str) -> int:
    """Get the limit for a metric for a tenant.

    Resolution order:
    1. Cache: limit:{tenant_id}:{metric}
    2. Tenant override (future)
    3. Plan limits matrix
    4. Default limit from registry

    Args:
        tenant_id: Tenant identifier
        metric: Metric code

    Returns:
        Limit value (-1 for unlimited)
    """
    cache_key = f"limit:{tenant_id}:{metric}"
    cached_limit = cache.get(cache_key)

    if cached_limit is not None:
        return int(cached_limit)

    # Get tenant plan
    plan_code = get_tenant_plan(tenant_id)

    # Look up in plan matrix
    plan_limits = PLAN_LIMITS.get(plan_code, PLAN_LIMITS["free"])
    limit = plan_limits.get(metric)

    if limit is not None:
        cache.set(cache_key, limit, PLAN_CACHE_TTL)
        return limit

    # Fall back to metric default
    try:
        metric_def = get_metric(metric)
        return metric_def.default_limit
    except KeyError:
        logger.error("Unknown metric: %s", metric)
        return 0  # Fail-closed: unknown metric = 0 limit


def get_current_usage(tenant_id: str, metric: str) -> int:
    """Get current usage count for a metric.

    Checks Redis cache which is updated by record_usage().

    Args:
        tenant_id: Tenant identifier
        metric: Metric code

    Returns:
        Current usage count (0 if not found)
    """
    cache_key = f"usage:{tenant_id}:{metric}"
    usage = cache.get(cache_key)
    return int(usage) if usage else 0


def increment_usage(tenant_id: str, metric: str, amount: int = 1) -> int:
    """Increment usage counter in cache.

    This is called after successful action completion.

    Args:
        tenant_id: Tenant identifier
        metric: Metric code
        amount: Amount to increment (default 1)

    Returns:
        New usage count
    """
    cache_key = f"usage:{tenant_id}:{metric}"

    try:
        # Use Redis INCR for atomic increment
        new_value = cache.incr(cache_key, amount)
    except ValueError:
        # Key doesn't exist, set it
        cache.set(cache_key, amount, USAGE_CACHE_TTL)
        new_value = amount

    return new_value


def check_budget_available(tenant_id: str, metric: str, amount: int = 1) -> bool:
    """Check if budget is available for an action.

    SECURITY: This is a fail-closed check. On any error, returns False.

    Args:
        tenant_id: Tenant identifier
        metric: Metric code
        amount: Units required

    Returns:
        True if budget available, False otherwise
    """
    try:
        limit = get_metric_limit(tenant_id, metric)

        # -1 means unlimited
        if limit == -1:
            return True

        usage = get_current_usage(tenant_id, metric)
        return (usage + amount) <= limit

    except Exception as exc:
        logger.error("Budget check failed (fail-closed): %s", exc)
        return False  # SECURITY: Fail-closed


def get_budget_remaining(tenant_id: str, metric: str) -> Optional[int]:
    """Get remaining budget for a metric.

    Args:
        tenant_id: Tenant identifier
        metric: Metric code

    Returns:
        Remaining units, or None for unlimited
    """
    limit = get_metric_limit(tenant_id, metric)

    if limit == -1:
        return None  # Unlimited

    usage = get_current_usage(tenant_id, metric)
    return max(0, limit - usage)
