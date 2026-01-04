"""Capsules App - API Package."""

from ninja import Router

from admin.capsules.api.capsules import router as capsules_router

router = Router(tags=["capsules"])
router.add_router("/", capsules_router)

__all__ = ["router"]