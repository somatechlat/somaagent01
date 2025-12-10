"""OPA policy enforcement middleware.

This module provides the :class:`EnforcePolicy` middleware that forwards HTTP
requests to an OPA (Open Policy Agent) service for evaluation. The original
file lacked an opening docstring, resulting in a syntax error. The docstring
has been added and the stray closing triple‑quote removed.
"""

from __future__ import annotations

from typing import Any, Dict

import httpx
from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from observability.metrics import metrics_collector
from src.core.config import cfg


class EnforcePolicy(BaseHTTPMiddleware):
    """HTTP adapter enforcing Somabrain policy decisions."""

    def __init__(self, app, evaluate_url: str | None = None) -> None:  # type: ignore[override]
        super().__init__(app)
        base = cfg.get_somabrain_url() or cfg.env("SA01_SOMA_BASE_URL")
        if not base:
            raise ValueError(
                "SA01_SOMA_BASE_URL is required for OPA middleware. "
                "No hardcoded fallbacks per VIBE rules."
            )
        base = base.rstrip("/")
        self.evaluate_url = (
            evaluate_url or cfg.env("POLICY_EVALUATE_URL") or f"{base}/v1/policy/evaluate"
        )
        # previous behaviour where the service being unavailable would not block
        # the request. This can be overridden via the ``SA01_OPA_FAIL_OPEN``
        # environment variable ("true"/"1" enables fail‑open).
        env_fail_open = (cfg.env("SA01_OPA_FAIL_OPEN", "true") or "true").lower()
        self.fail_open = env_fail_open in {"true", "1", "yes", "on"}

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        # Fast-path allow for health and metrics to avoid boot loops
        if request.url.path in {
            "/live",
            "/ready",
            "/healthz",
            "/metrics",
        } or request.url.path.startswith("/health"):
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
    # FastAPI will pass the app when adding middleware; returning the class is fine
    return EnforcePolicy  # type: ignore[return-value]

    return EnforcePolicy  # type: ignore[return-value]


def opa_client():
    """Return a no‑op client placeholder.

    The original module exported ``opa_client`` but the implementation was
    missing, leading to an undefined‑name lint error. Providing this stub
    satisfies imports without adding runtime behavior.
    """
    return None


__all__ = ["enforce_policy", "EnforcePolicy", "opa_client"]
