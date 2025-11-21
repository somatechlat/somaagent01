"""Health router extracted from the gateway monolith.

Provides a minimal /v1/health endpoint that can be mounted independently of
the legacy gateway file. Returns static OK until full integration wires real
health checks through the orchestrator.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/v1", tags=["health"])


@router.get("/health")
async def health() -> dict[str, bool]:
    return {"healthy": True}
