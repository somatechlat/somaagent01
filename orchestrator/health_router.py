"""FastAPI router for on‑demand health checks of registered services.

The project distinguishes two concerns:

* **Health router** – a lightweight ``/v1/health`` endpoint that aggregates the
  ``health()`` coroutine of each ``BaseSomaService`` registered with the
  orchestrator. This is used by external clients (e.g., Kubernetes liveness
  probes).
* **Health monitor** – a background async task (implemented in
  ``health_monitor.py``) that periodically checks external service URLs and
  maintains a richer status model.

Separating them avoids circular imports and lets the orchestrator mount the
router without starting the monitor automatically.
"""

from __future__ import annotations

from fastapi import APIRouter
from typing import Dict, List

router = APIRouter()


class UnifiedHealthRouter:
    """Collect health from a list of ``BaseSomaService`` instances.

    The router expects a *live* list of services; the orchestrator passes the
    registry's ``services`` list so the router always sees the current set.
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


def attach_to_app(app, router_obj: UnifiedHealthRouter) -> None:
    """Mount the health router onto the provided FastAPI app.

    ``router_obj`` is an instance of :class:`UnifiedHealthRouter`. The function
    registers a ``/v1/health`` endpoint that delegates to ``router_obj``.
    """

    @router.get("/v1/health")
    async def health() -> Dict:  # pragma: no cover – exercised via API tests
        return await router_obj.health_endpoint()

    app.include_router(router)
