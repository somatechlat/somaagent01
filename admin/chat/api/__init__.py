"""Chat Admin App - API Package."""

from ninja import Router

from admin.chat.api.chat import router as chat_router

router = Router(tags=["chat"])
router.add_router("", chat_router)

__all__ = ["router"]