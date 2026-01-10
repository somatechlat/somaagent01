"""Agents API - Combined router.

Pure Django Ninja implementation for agent management.
"""

from ninja import Router

from admin.agents.api.agents import router as agents_router
from admin.agents.api.core import router as core_router
from admin.agents.api.core import get_multimodal_config, update_multimodal_config, MultimodalConfig

# Master router for agents domain
router = Router(tags=["agents"])

# Mount sub-routers
router.add_router("", agents_router)
router.add_router("", core_router)

__all__ = ["router", "get_multimodal_config", "update_multimodal_config", "MultimodalConfig"]