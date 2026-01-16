"""Agents API - Combined router.

Pure Django Ninja implementation for agent management.
"""

from ninja import Router

from admin.agents.api.agents import router as agents_router
from admin.agents.api.core import (
    get_multimodal_config,
    MultimodalConfig,
    router as core_router,
    update_multimodal_config,
)

# Master router for agents domain
router = Router(tags=["agents"])

# Mount sub-routers
router.add_router("", agents_router)
router.add_router("", core_router)

__all__ = ["MultimodalConfig", "get_multimodal_config", "router", "update_multimodal_config"]
