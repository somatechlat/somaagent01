"""Agents API - Combined router.

Pure Django Ninja implementation for agent management.
"""

from ninja import Router

from admin.agents.api.agents import router as agents_router

# Master router for agents domain
router = Router(tags=["agents"])

# Mount sub-routers
router.add_router("", agents_router)

__all__ = ["router"]
