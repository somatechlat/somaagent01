"""UI Admin App - API Package."""

from ninja import Router

from admin.ui.api.skins import router as skins_router

router = Router(tags=["ui"])
router.add_router("", skins_router)

__all__ = ["router"]
