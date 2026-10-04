"""Core Admin API - All routers combined.

Pure Django Ninja implementation for admin domain.
"""

from ninja import Router

from admin.core.api.agentiq import router as agentiq_router
from admin.core.api.degradation import router as degradation_router
from admin.core.api.general import router as general_router
from admin.core.api.health import router as health_router
from admin.core.api.kafka import router as kafka_router
from admin.core.api.llm import router as llm_router
from admin.core.api.migrate import router as migrate_router
from admin.core.api.sessions import router as sessions_router
from admin.core.api.settings_v2 import router as settings_router
from admin.core.infrastructure.api import router as infrastructure_router

# Master router for core admin domain
router = Router(tags=["admin"])

# Mount sub-routers
router.add_router("", general_router)
router.add_router("", health_router)  # /health endpoints
router.add_router("", llm_router)  # /llm endpoints
router.add_router("", sessions_router)  # /sessions endpoints
router.add_router("/kafka", kafka_router)
router.add_router("/migrate", migrate_router)
router.add_router("/infrastructure", infrastructure_router)  # Rate limits + infra
router.add_router("/infrastructure/degradation", degradation_router)  # Degradation monitor
router.add_router("/settings", settings_router)  # Service configuration
router.add_router("/agentiq", agentiq_router)  # Capsule knobs + server-derived settings

__all__ = ["router"]
