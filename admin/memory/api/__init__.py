"""Memory App - API Package."""

from ninja import Router

from admin.memory.api.memory import router as memory_router

router = Router(tags=["memory"])
router.add_router("/", memory_router)

__all__ = ["router"]
