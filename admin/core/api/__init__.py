"""Core Admin API - All routers combined.

Pure Django Ninja implementation for admin domain.
"""

from ninja import Router

from admin.core.api.general import router as general_router
from admin.core.api.kafka import router as kafka_router
from admin.core.api.memory import router as memory_router
from admin.core.api.migrate import router as migrate_router

# Master router for core admin domain
router = Router(tags=["admin"])

# Mount sub-routers
router.add_router("", general_router)
router.add_router("/kafka", kafka_router)
router.add_router("", memory_router)  # /memory endpoints
router.add_router("/migrate", migrate_router)

__all__ = ["router"]
