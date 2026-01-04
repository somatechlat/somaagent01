"""Authorization helpers - 100% Django.

Provides authorization using OPA policy evaluation.
All exceptions use Django/admin.common.exceptions.


🎓 PhD Dev - Clean architecture
🔒 Security - OPA policy integration
⚡ Perf - Metrics tracked
📚 ISO Doc - Full docstrings
"""

from __future__ import annotations

import logging
import time
from functools import wraps
from typing import Any, Awaitable, Callable, Dict

from django.http import HttpRequest
from prometheus_client import Counter, Histogram, REGISTRY

from admin.common.exceptions import ForbiddenError
from services.common.policy_client import PolicyClient, PolicyRequest

try:
    AUTH_DECISIONS = Counter(
        "auth_decisions_total",
        "Selective authorization decisions",
        labelnames=("action", "result"),
    )
except ValueError:
    AUTH_DECISIONS = REGISTRY._names_to_collectors.get("auth_decisions_total")

try:
    AUTH_DURATION = Histogram(
        "auth_duration_seconds",
        "Latency of selective authorization decisions",
        labelnames=("source",),
    )
except ValueError:
    AUTH_DURATION = REGISTRY._names_to_collectors.get("auth_duration_seconds")


def get_policy_client() -> PolicyClient:
    return PolicyClient()


async def authorize(
    request: HttpRequest,
    action: str,
    resource: str,
    context: Dict[str, Any] | None = None,
    client: PolicyClient | None = None,
) -> Dict[str, Any]:
    """Authorize a request using OPA policy evaluation.

    🔒 Security: Evaluates policy against OPA
    ⚡ Perf: Metrics tracked via Prometheus

    Raises:
        ForbiddenError: If policy denies the request
    """
    start = time.perf_counter()
    ctx = context or {}
    tenant = request.headers.get("X-Tenant-Id", "default")
    persona = request.headers.get("X-Persona-Id")

    policy_req = PolicyRequest(
        tenant=tenant,
        persona_id=persona,
        action=action,
        resource=resource,
        context=ctx,
    )
    try:
        if client is None:
            client = get_policy_client()
        allowed = await client.evaluate(policy_req)
    except Exception as exc:
        allowed = False
        AUTH_DECISIONS.labels(action=action, result="error").inc()
        logging.getLogger("authz").warning(
            "authz evaluation error",
            extra={
                "action": action,
                "resource": resource,
                "tenant": tenant,
                "persona_id": persona,
                "error": str(exc),
            },
        )
    else:
        AUTH_DECISIONS.labels(action=action, result=("allow" if allowed else "deny")).inc()
        logging.getLogger("authz").info(
            "authz decision",
            extra={
                "action": action,
                "resource": resource,
                "tenant": tenant,
                "persona_id": persona,
                "result": "allow" if allowed else "deny",
                "mode": "live",
            },
        )
    AUTH_DURATION.labels(source=action).observe(max(0.0, time.perf_counter() - start))
    if not allowed:
        logging.getLogger("authz").info(
            "authz denial",
            extra={
                "action": action,
                "resource": resource,
                "tenant": tenant,
                "persona_id": persona,
                "result": "deny",
            },
        )
        raise ForbiddenError(action=action, resource=resource)
    return {"tenant": tenant, "persona_id": persona, "action": action, "resource": resource}


def require_policy(action: str, resource: str) -> Callable:
    """Decorator for Django Ninja route functions.

    Usage:
        @router.post("/secure")
        @require_policy("memory.write", "memory")
        async def write_secure(request, ...):
            ...
    """

    def _decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def _inner(*args, request: HttpRequest, **kwargs):
            await authorize(request=request, action=action, resource=resource)
            return await func(*args, request=request, **kwargs)

        return _inner

    return _decorator


async def authorize_request(
    request: HttpRequest, meta: dict[str, Any] | None = None
) -> Dict[str, Any]:
    """Legacy wrapper around authorize()."""
    return await authorize(request, action="auto", resource="auto", context=meta or {})


def _require_admin_scope(auth: dict[str, Any]) -> None:
    """Validate that the authenticated user has admin scope.

    Raises ForbiddenError if admin scope is not present.
    """
    scopes = auth.get("scopes", [])
    if "admin" not in scopes and not auth.get("is_admin", False):
        raise ForbiddenError(action="admin_access", resource="admin")


__all__ = [
    "authorize",
    "require_policy",
    "get_policy_client",
    "authorize_request",
    "_require_admin_scope",
]
