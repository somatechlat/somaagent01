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
    AUTH_DECISIONS = REGISTRY._names_to_collectors.get("auth_decisions_total")  # type: ignore[reportAttributeAccessIssue]

try:
    AUTH_DURATION = Histogram(
        "auth_duration_seconds",
        "Latency of selective authorization decisions",
        labelnames=("source",),
    )
except ValueError:
    AUTH_DURATION = REGISTRY._names_to_collectors.get("auth_duration_seconds")  # type: ignore[reportAttributeAccessIssue]


def get_policy_client() -> PolicyClient:
    """Retrieve policy client."""

    return PolicyClient()


def _principal_from_request(
    request: HttpRequest,
) -> tuple[list[str], list[str] | None]:
    """Extract the subject's roles and, if it is a key, its scopes.

    FAIL-CLOSED: an unauthenticated request yields neither, which is no
    authority. A delegated key is reported as ``scopes`` and its roles are
    dropped — see ``authz.permissions_for_principal`` for why the two are
    never unioned.
    """
    auth = getattr(request, "auth", None)
    if auth is None:
        return [], None

    def _get(name, default=None):
        if isinstance(auth, dict):
            return auth.get(name, default)
        return getattr(auth, name, default)

    delegated = _get("delegated_scopes", None)
    if delegated is not None:
        return [], [str(s) for s in delegated]

    return [str(r) for r in (_get("roles") or [])], None


async def authorize(
    request: HttpRequest,
    action: str,
    resource: str,
    context: Dict[str, Any] | None = None,
    client: PolicyClient | None = None,
) -> Dict[str, Any]:
    """Authorize a request.

    Two layers, in this order, and the order is the security property:

    1. **Role-based access control.** The action maps to a catalog permission
       (``admin.core.authz``) and the subject's roles must grant it. This is
       the authority whenever no policy engine is attached, which is the
       normal Standalone case. It is also a floor the engine can only narrow.

    2. **Policy engine.** When OPA is attached its decision may only *deny
       further*. A policy engine that is absent, unreachable or erroring never
       grants anything.

    🔒 Security: FAIL-CLOSED at every step.
    ⚡ Perf: Metrics tracked via Prometheus

    Raises:
        ForbiddenError: If the subject is not authorized for the action.
    """
    from admin.core.authz import permissions_for_principal, resolve_action

    start = time.perf_counter()
    ctx = context or {}
    tenant = request.headers.get("X-Tenant-Id", "default")
    persona = request.headers.get("X-Persona-Id")

    # ---- 1. Role baseline -------------------------------------------------
    try:
        permission = resolve_action(action)
    except KeyError:
        AUTH_DECISIONS.labels(action=action, result="deny").inc()
        logging.getLogger("authz").warning(
            "authz denial: action has no catalog permission",
            extra={"action": action, "resource": resource, "tenant": tenant},
        )
        raise ForbiddenError(action=action, resource=resource)

    roles, scopes = _principal_from_request(request)
    granted = permissions_for_principal(roles=roles, scopes=scopes)
    if permission not in granted:
        AUTH_DECISIONS.labels(action=action, result="deny").inc()
        AUTH_DURATION.labels(source=action).observe(max(0.0, time.perf_counter() - start))
        logging.getLogger("authz").info(
            "authz denial",
            extra={
                "action": action,
                "permission": permission,
                "resource": resource,
                "tenant": tenant,
                "persona_id": persona,
                "roles": roles,
                "result": "deny",
                "layer": "rbac",
            },
        )
        raise ForbiddenError(action=action, resource=resource)

    # ---- 2. Policy engine, may only narrow --------------------------------
    if client is None:
        client = get_policy_client()

    if client.is_configured:
        # Ask the engine about the catalog permission, not the caller's
        # spelling of it. RBAC already resolved the action; if the engine were
        # asked the raw string it would see "settings:read" and "system:view"
        # as two different questions, and a policy written against the catalog
        # would silently miss every alias. One vocabulary, one question.
        policy_req = PolicyRequest(
            tenant=tenant,
            persona_id=persona,
            action=permission,
            resource=resource,
            context=ctx,
        )
        try:
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
        if not allowed:
            AUTH_DECISIONS.labels(action=action, result="deny").inc()
            AUTH_DURATION.labels(source=action).observe(max(0.0, time.perf_counter() - start))
            logging.getLogger("authz").info(
                "authz denial",
                extra={
                    "action": action,
                    "permission": permission,
                    "resource": resource,
                    "tenant": tenant,
                    "persona_id": persona,
                    "result": "deny",
                    "layer": "policy",
                },
            )
            raise ForbiddenError(action=action, resource=resource)

    AUTH_DECISIONS.labels(action=action, result="allow").inc()
    AUTH_DURATION.labels(source=action).observe(max(0.0, time.perf_counter() - start))
    logging.getLogger("authz").info(
        "authz decision",
        extra={
            "action": action,
            "permission": permission,
            "resource": resource,
            "tenant": tenant,
            "persona_id": persona,
            "roles": roles,
            "result": "allow",
            "policy_engine": client.is_configured,
        },
    )
    return {
        "tenant": tenant,
        "persona_id": persona,
        "action": action,
        "permission": permission,
        "resource": resource,
    }


def require_policy(action: str, resource: str) -> Callable:
    """Decorator for Django Ninja route functions.

    Usage:
        @router.post("/secure")
        @require_policy("memory.write", "memory")
        async def write_secure(request, ...):
            ...
    """

    def _decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        """Inner decorator for require_policy."""

        @wraps(func)
        async def _inner(*args, request: HttpRequest, **kwargs):
            """Wrapper with policy authorization."""
            await authorize(request=request, action=action, resource=resource)
            return await func(*args, request=request, **kwargs)

        return _inner

    return _decorator


def authorize_sync(
    request: HttpRequest,
    action: str,
    resource: str,
    context: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """``authorize()`` for sync handlers.

    The gate is identical — same catalog lookup, same RBAC floor, same
    fail-closed policy layer. Only the calling convention differs: some
    routes are ``def`` because they carry ``@transaction.atomic``, which
    Django cannot express on an async handler.

    This is not a second authorization path and it must never grow its own
    rules. Any change to the decision logic belongs in ``authorize()``.

    Raises:
        ForbiddenError: If the subject is not authorized for the action.
    """
    from asgiref.sync import async_to_sync

    return async_to_sync(authorize)(request, action=action, resource=resource, context=context)


__all__ = [
    "authorize",
    "authorize_sync",
    "require_policy",
    "get_policy_client",
]
