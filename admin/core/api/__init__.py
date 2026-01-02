"""Core Admin API - All routers combined.

Pure Django Ninja implementation for admin domain.
"""

from ninja import Router

from admin.core.api.general import router as general_router
from admin.core.api.health import router as health_router
from admin.core.api.kafka import router as kafka_router
from admin.core.api.llm import router as llm_router
from admin.core.api.memory import router as memory_router
from admin.core.api.migrate import router as migrate_router
from admin.core.api.sessions import router as sessions_router
from admin.core.infrastructure.api import router as infrastructure_router
from admin.core.infrastructure.degradation_api import router as degradation_router
from admin.core.infrastructure.settings_api import router as settings_router
from admin.core.infrastructure.observability_api import router as observability_router
from admin.core.infrastructure.feature_flags_api import router as feature_flags_router
from admin.core.infrastructure.api_keys_api import router as api_keys_router

# Master router for core admin domain
router = Router(tags=["admin"])

# Mount sub-routers
router.add_router("", general_router)
router.add_router("", health_router)  # /health endpoints
router.add_router("", llm_router)  # /llm endpoints
router.add_router("", sessions_router)  # /sessions endpoints
router.add_router("/kafka", kafka_router)
router.add_router("", memory_router)  # /memory endpoints
router.add_router("/migrate", migrate_router)
router.add_router("/infrastructure", infrastructure_router)  # Rate limits + infra
router.add_router("/infrastructure/degradation", degradation_router)  # Degradation monitor
router.add_router("/settings", settings_router)  # Service configuration
router.add_router("/observability", observability_router)  # Platform metrics
router.add_router("/flags", feature_flags_router)  # Feature flags
router.add_router("/apikeys", api_keys_router)  # API keys management

__all__ = ["router"]
