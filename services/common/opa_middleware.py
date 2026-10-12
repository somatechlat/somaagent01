"""Agent OPA middleware — policy on EVERY HTTP request (fail-closed).

Topology law: one OPA plane (``somabrain/auth/allow``). This middleware is
the agent-side twin of Brain's ``OpaMiddleware``: any route that does not
explicitly opt out is gated. Missing engine, transport error, or undecided
policy ⇒ 403. Never allow-on-error.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from django.http import HttpRequest, JsonResponse
from django.conf import settings

LOGGER = logging.getLogger("somaAgent01.opa_middleware")

# Public liveness probes only. Everything else is gated.
_PUBLIC_PATHS = frozenset({"/healthz", "/readyz", "/ping", "/health/basic"})


class OpaMiddleware:
    """Django middleware: OPA authorize every non-public request (fail-closed)."""

    def __init__(self, get_response: Callable[[HttpRequest], Any]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        path = (request.path or "/").rstrip("/") or "/"
        if request.path in _PUBLIC_PATHS or path in _PUBLIC_PATHS:
            return self.get_response(request)

        try:
            allowed = self._evaluate(request)
        except Exception as exc:
            LOGGER.error("OPA evaluation error (fail-closed deny): %s", exc)
            return JsonResponse({"detail": "OPA policy unavailable"}, status=403)

        if not allowed:
            return JsonResponse({"detail": "OPA policy denied request"}, status=403)
        return self.get_response(request)

    def _evaluate(self, request: HttpRequest) -> bool:
        """Build the product input schema and query the single OPA plane."""
        import asyncio

        body_bytes = getattr(request, "body", b"") or b""
        json_body: Any = None
        if body_bytes:
            try:
                import json as _json

                json_body = _json.loads(body_bytes)
            except Exception:
                json_body = None

        user = getattr(request, "user", None)
        tenant = (
            getattr(request, "tenant_id", None)
            or request.headers.get("X-Soma-Tenant")
            or request.GET.get("tenant_id")
            or ""
        )
        input_payload = {
            "subject": {
                "tenant": str(tenant or ""),
                "tenant_id": str(tenant or ""),
                "role": ",".join(
                    [str(r) for r in (getattr(user, "roles", None) or [])]
                )
                if user and getattr(user, "is_authenticated", False)
                else "",
                "agent_id": str(getattr(request, "agent_id", "") or ""),
            },
            "action": f"{request.method.lower()}:{request.path}",
            "resource": {
                "type": "agent",
                "namespace": str(getattr(request, "namespace", "") or ""),
            },
            "context": {
                "method": request.method,
                "path": request.path,
                "json": json_body,
            },
        }

        # Synchronous middleware: run the async PolicyClient on a private loop.
        try:
            from services.common.policy_client import get_policy_client
        except Exception:
            # No policy client wired → deny (fail-closed).
            return False

        client = get_policy_client()
        if getattr(client, "_disabled", False) and getattr(client, "base_url", None) is None:
            # No engine attached. Product law: REQUIRE_OPA must gate. Deny.
            require = bool(getattr(settings, "REQUIRE_OPA", True))
            if require:
                LOGGER.warning("REQUIRE_OPA: no policy engine — denying request")
                return False
            return True

        async def _run() -> bool:
            from services.common.policy_client import PolicyRequest

            req = PolicyRequest(
                tenant=str(tenant or ""),
                persona_id=str(getattr(request, "persona_id", "") or "") or None,
                action=input_payload["action"],
                resource="agent",
                context=input_payload,
            )
            return await client.evaluate(req)

        try:
            loop = asyncio.new_event_loop()
            try:
                return bool(loop.run_until_complete(_run()))
            finally:
                loop.close()
        except Exception as exc:
            LOGGER.error("OPA evaluate failed (fail-closed deny): %s", exc)
            return False
