"""Gateway App - API Package."""

from ninja import Router

from admin.gateway.api.gateway import router as gateway_router

router = Router(tags=["gateway"])
router.add_router("/", gateway_router)

__all__ = ["router"]