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
from typing import Dict, List, Callable, Optional


class UnifiedHealthRouter:
    """Collect health from a list of ``BaseSomaService`` instances.

    The router expects a *live* list of services; the orchestrator passes the
    registry's ``services`` list so the router always sees the current set.
    """

    def __init__(self, services: List[object] | None = None, registry=None, services_provider: Optional[Callable[[], List[object]]] = None) -> None:
        self._services = services or []
        self._registry = registry
        self._services_provider = services_provider

    async def _gather(self) -> Dict[str, Dict]:
        results: Dict[str, Dict] = {}
        if self._services_provider is not None:
            services = self._services_provider()
        elif self._registry is not None:
            services = self._registry.services
        else:
            services = self._services
        for svc in services:
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

    router = APIRouter()

    @router.get("/v1/health")
    async def health() -> Dict:  # pragma: no cover – exercised via API tests
        return await router_obj.health_endpoint()

    app.include_router(router)
