"""Selective authorization helpers.

Provides a FastAPI dependency/decorator that evaluates a policy decision
only for sensitive endpoints instead of globally applying middleware.
"""

from __future__ import annotations

import time
from functools import wraps
from typing import Any, Awaitable, Callable, Dict

from fastapi import HTTPException, Request
from prometheus_client import Counter, Histogram, REGISTRY
import logging

from services.common.policy_client import PolicyClient, PolicyRequest

try:
    AUTH_DECISIONS = Counter(
        "auth_decisions_total",
        "Selective authorization decisions",
        labelnames=("action", "result"),  # result: allow|deny|error
    )
except ValueError:  # reuse existing collector if re-imported under tests
    AUTH_DECISIONS = REGISTRY._names_to_collectors.get("auth_decisions_total")  # type: ignore[attr-defined]

try:
    AUTH_DURATION = Histogram(
        "auth_duration_seconds",
        "Latency of selective authorization decisions",
        labelnames=("action",),
    )
except ValueError:
    AUTH_DURATION = REGISTRY._names_to_collectors.get("auth_duration_seconds")  # type: ignore[attr-defined]


def get_policy_client() -> PolicyClient:
    # In a more advanced setup, this could be cached on app.state.
    return PolicyClient()


async def authorize(
    request: Request,
    action: str,
    resource: str,
    context: Dict[str, Any] | None = None,
    client: PolicyClient | None = None,
) -> Dict[str, Any]:
    start = time.perf_counter()
    ctx = context or {}
    tenant = request.headers.get("X-Tenant-Id", "default")
    persona = request.headers.get("X-Persona-Id")
    # Test-mode bypass: allow all decisions when TESTING env is set (except explicit override)
    import os
    if os.getenv("TESTING") in {"1", "true", "True"} and os.getenv("DISABLE_TEST_POLICY_BYPASS") not in {"1", "true", "True"}:
        # Allow all in test mode and log a structured decision
        AUTH_DECISIONS.labels(action=action, result="allow").inc()
        AUTH_DURATION.labels(action=action).observe(0.0)
        logging.getLogger("authz").info(
            "authz decision",
            extra={
                "action": action,
                "resource": resource,
                "tenant": tenant,
                "persona_id": persona,
                "result": "allow",
                "mode": "test-bypass",
            },
        )
        return {"tenant": tenant, "persona_id": persona, "action": action, "resource": resource}
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
    AUTH_DURATION.labels(action=action).observe(max(0.0, time.perf_counter() - start))
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
        raise HTTPException(status_code=403, detail="policy_denied")
    return {"tenant": tenant, "persona_id": persona, "action": action, "resource": resource}


def require_policy(action: str, resource: str) -> Callable:
    """Decorator for FastAPI route functions.

    Usage:
        @app.post("/v1/memory/secure")
        @require_policy("memory.write", "memory")
        async def write_secure(...):
            ...
    """

    def _decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def _inner(*args, request: Request, **kwargs):  # type: ignore[override]
            await authorize(request=request, action=action, resource=resource)
            return await func(*args, request=request, **kwargs)

        return _inner

    return _decorator

__all__ = [
    "authorize",
    "require_policy",
    "get_policy_client",
]
