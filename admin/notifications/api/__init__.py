"""Notifications App - API Package."""

from ninja import Router

from admin.notifications.api.notifications import router as notifications_router

router = Router(tags=["notifications"])
router.add_router("/", notifications_router)

__all__ = ["router"]