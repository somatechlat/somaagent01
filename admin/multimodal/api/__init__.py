"""Multimodal Admin App - API Package."""

from ninja import Router

from admin.multimodal.api.multimodal import router as multimodal_router

router = Router(tags=["multimodal"])
router.add_router("", multimodal_router)

# Phase 7.3: DALL-E, Mermaid, Playwright adapters
from admin.multimodal.execution import router as execution_router

router.add_router("/execution", execution_router)

__all__ = ["router"]
