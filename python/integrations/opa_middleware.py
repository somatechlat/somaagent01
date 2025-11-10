"""Somabrain policy enforcement middleware.

Production-grade services should delegate authorization decisions to a
centralized policy engine. This middleware forwards request context to the
Somabrain policy evaluator over HTTP and enforces the returned decision.

Environment variables:
- ``POLICY_EVALUATE_URL``: Full URL to the policy evaluate endpoint.
    Defaults to ``${SOMA_BASE_URL}/v1/policy/evaluate``.
- ``POLICY_FAIL_OPEN``: If true, allow requests when the policy service is
    unavailable (default: true). If false, deny on errors (fail-closed).
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.exceptions import HTTPException
import os
import json
import httpx
from typing import Any, Dict

from observability.metrics import metrics_collector


class EnforcePolicy(BaseHTTPMiddleware):
    """HTTP adapter enforcing Somabrain policy decisions."""

    def __init__(self, app, evaluate_url: str | None = None) -> None:  # type: ignore[override]
        super().__init__(app)
        base = os.getenv("SOMA_BASE_URL", "http://host.docker.internal:9696").rstrip("/")
        self.evaluate_url = (
            evaluate_url
            or os.getenv("POLICY_EVALUATE_URL")
            or f"{base}/v1/policy/evaluate"
        )
        self.fail_open = os.getenv("POLICY_FAIL_OPEN", "true").lower() in {"true", "1", "yes", "on"}

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        # Fast-path allow for health and metrics to avoid boot loops
        path = str(getattr(request, "url", ""))
        if request.url.path in {"/live", "/ready", "/healthz", "/metrics"} or request.url.path.startswith("/health"):
            return await call_next(request)

        # Build minimal evaluation payload
        payload: Dict[str, Any] = {
            "method": request.method,
            "path": request.url.path,
            "query": dict(request.query_params),
            "tenant_id": request.headers.get("X-Tenant-Id", "default"),
            "user_id": request.headers.get("X-User-Id", "anonymous"),
            "trace_id": request.headers.get("traceparent"),
        }
        # Attempt to include a small, bounded body for POST/PUT (best-effort)
        try:
            if request.method in {"POST", "PUT", "PATCH"}:
                body_bytes = await request.body()
                if body_bytes:
                    # Avoid huge payloads; cap at 8KB
                    body_str = body_bytes[:8192].decode("utf-8", errors="ignore")
                    payload["body_preview"] = body_str
        except Exception:
            pass

        try:
            async with httpx.AsyncClient(timeout=2.5) as client:
                resp = await client.post(self.evaluate_url, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            # Policy service error: respect fail-open/closed
            if self.fail_open:
                metrics_collector.track_auth_result("skipped", "somabrain")
                return await call_next(request)
            raise HTTPException(status_code=503, detail="policy_unavailable") from exc

        allowed = bool(data.get("allow", False))
        reason = data.get("reason") or data.get("message")
        if not allowed:
            metrics_collector.track_auth_result("denied", "somabrain")
            raise HTTPException(status_code=403, detail=reason or "policy_denied")

        metrics_collector.track_auth_result("allowed", "somabrain")
        return await call_next(request)


def enforce_policy() -> EnforcePolicy:  # pragma: no cover – thin wrapper
    """Factory for compatibility with existing imports."""
    # FastAPI will pass the app when adding middleware; returning the class is fine
    return EnforcePolicy  # type: ignore[return-value]

def opa_client() -> EnforcePolicy:  # compatibility alias expected by some tests
    return EnforcePolicy  # type: ignore[return-value]

__all__ = ["enforce_policy", "EnforcePolicy", "opa_client"]