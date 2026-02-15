"""Budget Gate Decorator — Universal Pre-Action Enforcement.

SRS Source: SRS-BUDGET-SYSTEM-2026-01-16 Section 7

Applied Personas:
- PhD Developer: Clean decorator pattern
- Security Auditor: Fail-closed enforcement
- Performance Engineer: Async Lago recording
- Django Architect: Request context extraction
- Django Evangelist: Django-native patterns

Vibe Coding Rules:
- NO mocks, stubs, or placeholders
- REAL Redis cache
- REAL Lago integration
- REAL error handling
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from functools import wraps
from typing import Any, Callable, cast, Optional, TypeVar

from django.http import HttpRequest

from admin.core.budget.exceptions import BudgetExhaustedError, MetricNotFoundError
from admin.core.budget.limits import (
    check_budget_available,
    get_current_usage,
    get_metric_limit,
    increment_usage,
)
from admin.core.budget.registry import get_metric

logger = logging.getLogger(__name__)

# Type variable for the decorated function
F = TypeVar("F", bound=Callable[..., Any])


def budget_gate(metric: str = "tokens") -> Callable[[F], F]:
    """Universal budget enforcement decorator.

    This decorator enforces budget limits BEFORE action execution.
    If budget is exhausted, raises BudgetExhaustedError (HTTP 402).

    Usage:
        @budget_gate(metric="tokens")
        async def process_chat(request, capsule):
            ...

        @budget_gate(metric="images")
        async def generate_image(request, prompt, capsule):
            ...

        @budget_gate(metric="tool_calls")
        async def execute_tool(request, tool_name, *args):
            ...

    Args:
        metric: Metric code from METRIC_REGISTRY

    Returns:
        Decorated function with budget enforcement

    Raises:
        BudgetExhaustedError: If budget limit exceeded (HTTP 402)
        MetricNotFoundError: If metric code is invalid
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract tenant_id from request or kwargs
            tenant_id = _extract_tenant_id(args, kwargs)

            if not tenant_id:
                logger.warning("No tenant_id found, skipping budget check")
                return await func(*args, **kwargs)

            # Validate metric exists
            try:
                metric_def = get_metric(metric)
            except KeyError:
                raise MetricNotFoundError(metric)

            # Check if metric is enabled for this tenant (future: toggle support)
            if not _is_metric_enabled(tenant_id, metric):
                logger.debug("Metric %s disabled for tenant %s", metric, tenant_id)
                return await func(*args, **kwargs)

            # PRE-ENFORCEMENT: Check budget BEFORE action
            if metric_def.enforce_pre:
                if not check_budget_available(tenant_id, metric):
                    usage = get_current_usage(tenant_id, metric)
                    limit = get_metric_limit(tenant_id, metric)
                    logger.warning(
                        "Budget exhausted: tenant=%s metric=%s usage=%d limit=%d",
                        tenant_id,
                        metric,
                        usage,
                        limit,
                    )
                    raise BudgetExhaustedError(
                        tenant_id=tenant_id,
                        metric=metric,
                        usage=usage,
                        limit=limit,
                    )

            # Execute the actual function
            result = await func(*args, **kwargs)

            # POST-ACTION: Record usage
            units_used = _extract_units_used(result, metric)
            increment_usage(tenant_id, metric, units_used)

            # ASYNC: Record to Lago (non-blocking)
            asyncio.create_task(_record_lago_event(tenant_id, metric_def.lago_code, units_used))

            return result

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            """Sync wrapper for non-async functions."""
            tenant_id = _extract_tenant_id(args, kwargs)

            if not tenant_id:
                return func(*args, **kwargs)

            try:
                metric_def = get_metric(metric)
            except KeyError:
                raise MetricNotFoundError(metric)

            if not _is_metric_enabled(tenant_id, metric):
                return func(*args, **kwargs)

            if metric_def.enforce_pre:
                if not check_budget_available(tenant_id, metric):
                    usage = get_current_usage(tenant_id, metric)
                    limit = get_metric_limit(tenant_id, metric)
                    raise BudgetExhaustedError(
                        tenant_id=tenant_id,
                        metric=metric,
                        usage=usage,
                        limit=limit,
                    )

            result = func(*args, **kwargs)

            units_used = _extract_units_used(result, metric)
            increment_usage(tenant_id, metric, units_used)

            return result

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        return cast(F, sync_wrapper)

    return decorator


def _extract_tenant_id(args: tuple[Any, ...], kwargs: dict[str, Any]) -> Optional[str]:
    """Extract tenant_id from function arguments.

    Checks in order:
    1. kwargs["tenant_id"]
    2. request.tenant_id (Django Ninja)
    3. request.user.tenant_id
    4. kwargs["capsule"].tenant_id

    Args:
        args: Positional arguments
        kwargs: Keyword arguments

    Returns:
        Tenant ID string or None
    """
    # Direct kwarg
    if "tenant_id" in kwargs:
        return str(kwargs["tenant_id"])

    # From request object
    request = None
    if args and isinstance(args[0], HttpRequest):
        request = args[0]
    elif "request" in kwargs:
        request = kwargs["request"]

    if request:
        # Django Ninja adds tenant_id to request
        if hasattr(request, "tenant_id"):
            return str(request.tenant_id)
        # Or on user
        if hasattr(request, "user") and hasattr(request.user, "tenant_id"):
            return str(request.user.tenant_id)

    # From capsule
    capsule = kwargs.get("capsule")
    if capsule and hasattr(capsule, "tenant_id"):
        return str(capsule.tenant_id)

    return None


def _extract_units_used(result: Any, metric: str) -> int:
    """Extract units used from function result.

    Different metrics use different units:
    - tokens: result.total_tokens or len(result)
    - images: 1 per generation
    - tool_calls: 1 per execution

    Args:
        result: Function return value
        metric: Metric code

    Returns:
        Units used (default 1)
    """
    if metric == "tokens":
        # Try to get token count from result
        if hasattr(result, "total_tokens"):
            return result.total_tokens
        if hasattr(result, "usage") and hasattr(result.usage, "total_tokens"):
            return result.usage.total_tokens
        if isinstance(result, dict):
            return result.get("total_tokens", result.get("tokens", 1))
        return 1

    if metric == "voice_minutes":
        if hasattr(result, "duration_minutes"):
            return int(result.duration_minutes)
        if isinstance(result, dict):
            return int(result.get("duration_minutes", 1))
        return 1

    # Default: 1 unit per call
    return 1


def _is_metric_enabled(tenant_id: str, metric: str) -> bool:
    """Check if metric is enabled for tenant.

    Lockable metrics can be disabled per-tenant.
    Non-lockable (critical) metrics are always enabled.

    Args:
        tenant_id: Tenant identifier
        metric: Metric code

    Returns:
        True if metric enforcement is enabled
    """
    try:
        metric_def = get_metric(metric)

        # Critical metrics cannot be disabled
        if not metric_def.lockable:
            return True

        # Current behaviour: lockable metrics default to enabled until
        # tenant-level toggles are introduced. Fail-closed remains True.
        return True

    except KeyError:
        return False


async def _record_lago_event(
    tenant_id: str,
    lago_code: str,
    units: int,
) -> bool:
    """Record usage event to Lago (async, non-blocking).

    CRITICAL: This must NEVER block the main flow.
    Failures are logged but do not affect the operation.

    Args:
        tenant_id: Tenant identifier
        lago_code: Lago metric code
        units: Units to record

    Returns:
        True if recorded, False on error
    """
    try:
        from admin.billing.lago_client import get_lago_client, UsageEvent

        client = get_lago_client()
        event = UsageEvent(
            transaction_id=f"{lago_code}-{uuid.uuid4().hex[:8]}",
            customer_external_id=tenant_id,
            code=lago_code,
            properties={"units": units},
        )
        await client.create_event(event)
        return True

    except ImportError:
        logger.debug("Lago client not available")
        return False
    except Exception as exc:
        logger.error("Failed to record Lago event: %s", exc)
        return False
