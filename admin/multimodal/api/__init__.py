"""Multimodal Admin App - API Package."""

from ninja import Router

from admin.multimodal.api.multimodal import router as multimodal_router

router = Router(tags=["multimodal"])
router.add_router("", multimodal_router)

__all__ = ["router"]
