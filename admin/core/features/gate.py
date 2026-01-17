"""Feature Gating Decorator — Access Control Enforcement.

SRS Source: SRS-FEATURE-FLAGS-2026-01-16

Applied Personas:
- Security Auditor: Fail-closed enforcement
- Django Architect: Ninja-compatible asynchronous decorators

Vibe Coding Rules:
- No bypassing checks
- Standardized error responses
"""

from __future__ import annotations

import functools
import inspect
import logging
from typing import Any, Callable, TypeVar, cast

from django.http import HttpRequest

from admin.core.features.check import is_feature_enabled
from admin.core.features.exceptions import FeatureDisabledError

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def require_feature(feature_code: str) -> Callable[[F], F]:
    """Decorator to require a specific feature enabled.

    Usage:
        @router.get("/generate")
        @require_feature("image_generation")
        def generate_image(request, ...):
            ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def sync_wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
            _check_feature(request, feature_code, *args, **kwargs)
            return func(request, *args, **kwargs)

        @functools.wraps(func)
        async def async_wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
            _check_feature(request, feature_code, *args, **kwargs)
            return await func(request, *args, **kwargs)

        if inspect.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        return cast(F, sync_wrapper)

    return decorator


def _check_feature(request: HttpRequest, feature_code: str, *args: Any, **kwargs: Any) -> None:
    """Internal check logic."""
    tenant_id = _extract_tenant_id(request, *args, **kwargs)

    if not tenant_id:
        logger.error("Feature check failed: No tenant_id found in context")
        # Fail closed
        raise FeatureDisabledError(feature_code, "unknown", "no_tenant_context")

    if not is_feature_enabled(tenant_id, feature_code):
        logger.info(f"Feature access denied: {feature_code} for {tenant_id}")
        raise FeatureDisabledError(feature_code, tenant_id)


def _extract_tenant_id(request: HttpRequest, *args: Any, **kwargs: Any) -> str | None:
    """Extract tenant_id from request or args.

    Priority:
    1. request.state.tenant_id (Ninja/Middleware)
    2. request.user.active_tenant_id
    3. kwargs['tenant_id']
    4. args (if identifiable)
    """
    # 1. Middleware/State (Best practice)
    if hasattr(request, "state") and hasattr(request.state, "tenant_id"):
        return str(request.state.tenant_id)

    # 2. Authenticated User
    if hasattr(request, "user") and request.user.is_authenticated:
        # Assuming our custom user model has active_tenant_id
        # or it's attached by auth middleware
        if hasattr(request.user, "active_tenant_id") and request.user.active_tenant_id:
            return str(request.user.active_tenant_id)

    # 3. Kwargs
    if "tenant_id" in kwargs:
        return str(kwargs["tenant_id"])

    # 4. Auth attribute (Ninja often puts auth result in attribute)
    if hasattr(request, "auth") and hasattr(request.auth, "tenant_id"):
        return str(request.auth.tenant_id)

    return None
