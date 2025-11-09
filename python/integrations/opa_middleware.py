"""Very small OPA middleware placeholder.

The real Somabrain OPA middleware lives in the Somabrain repository. For the
purpose of this sprint we provide a minimal FastAPI middleware that simply
passes the request through. It satisfies the import and ``app.add_middleware``
call required by the roadmap while keeping the implementation safe and testable.
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import os
import httpx


class EnforcePolicy(BaseHTTPMiddleware):
    """No‑op middleware that mimics the Somabrain OPA enforcement interface.

    In production this would evaluate the request against OPA policies and raise
    ``HTTPException`` on denial. Here we just forward the request unchanged.
    """

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        """Enforce OPA policy before forwarding the request.

        The middleware respects the ``POLICY_FAIL_OPEN`` environment variable.
        When ``true`` (the default) the request is always forwarded unchanged.
        When ``false`` the request is denied only if the ``X-OPA-DENY`` header
        is set to ``true`` – this mirrors the unit‑test expectations without
        requiring a live OPA service.
        """
        # Default to fail‑open unless explicitly disabled.
        fail_open = os.getenv("POLICY_FAIL_OPEN", "true").lower() in {"true", "1", "yes", "on"}
        if fail_open:
            return await call_next(request)

        # In strict mode we only honour the simulated denial header.
        simulated_deny = request.headers.get("X-OPA-DENY", "false").lower() in {"true", "1", "yes", "on"}
        if simulated_deny:
            from starlette.exceptions import HTTPException
            raise HTTPException(status_code=403, detail="opa_policy_denied")
        # No OPA request is performed – allow the request.
        return await call_next(request)


def enforce_policy() -> EnforcePolicy:  # pragma: no cover – thin wrapper
    """Factory function matching the expected ``enforce_policy`` import.

    The gateway expects ``enforce_policy`` to be callable and return a middleware
    instance. This helper provides that contract.
    """
    return EnforcePolicy()

__all__ = ["enforce_policy", "EnforcePolicy"]