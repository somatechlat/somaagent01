"""Files App - API Package."""

from ninja import Router

from admin.files.api.attachments import router as attachments_router

router = Router(tags=["files"])
router.add_router("/", attachments_router)

__all__ = ["router"]