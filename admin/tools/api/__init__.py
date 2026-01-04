"""Tools Admin App - API Package."""

from ninja import Router

from admin.tools.api.tools import router as tools_router

router = Router(tags=["tools"])
router.add_router("", tools_router)

__all__ = ["router"]