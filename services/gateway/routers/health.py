"""Health router extracted from the gateway monolith.

Provides a minimal /v1/health endpoint that can be mounted independently of
the legacy gateway file. Returns static OK until full integration wires real
health checks through the orchestrator.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/v1", tags=["health"])


@router.get("/health")
async def health() -> dict[str, object]:
    """Minimal health endpoint expected by the UI smoke test.

    The UI smoke script validates that the JSON response contains a ``status``
    field whose value is either ``"ok"`` or ``"degraded"``, and that a
    ``components`` key is present (it may be empty).  The original implementation
    returned ``{"healthy": True}``, which caused the test to fail.

    We now return the required structure while keeping the response lightweight.
    """
    return {"status": "ok", "components": {}}
