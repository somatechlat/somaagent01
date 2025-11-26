"""Simple health monitor for the orchestrator.

Provides a lightweight ``UnifiedHealthMonitor`` that aggregates the ``health``
coroutine of each registered ``BaseSomaService``.  The ``attach_to_app``
function mounts a ``/v1/health`` endpoint on a FastAPI app.
"""

from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter

router = APIRouter()


class UnifiedHealthMonitor:
    """Collect health information from a list of ``BaseSomaService`` objects.

    Each service implements an async ``health`` method returning a ``dict``
    with at least a ``healthy`` boolean.  This monitor aggregates those results
    and provides a combined view.
    """

    def __init__(self, services: List[object]) -> None:
        self._services = services

    async def _gather(self) -> Dict[str, Dict]:
        results: Dict[str, Dict] = {}
        for svc in self._services:
            try:
                results[svc.name] = await svc.health()
            except Exception as exc:  # pragma: no cover – defensive
                results[svc.name] = {"healthy": False, "error": str(exc)}
        return results

    async def health_endpoint(self) -> Dict:
        per = await self._gather()
        overall = all(v.get("healthy", False) for v in per.values())
        return {"healthy": overall, "services": per}


def attach_to_app(app, monitor: UnifiedHealthMonitor) -> None:
    """Mount the health router onto the provided FastAPI ``app``.

    The router defines a single ``GET /v1/health`` endpoint that delegates to
    ``monitor.health_endpoint``.
    """

    @router.get("/v1/health")
    async def health() -> Dict:
        return await monitor.health_endpoint()

    app.include_router(router)
