"""Capsules API — List and retrieve agent capsules."""

from ninja import Router

from admin.common.auth import AuthBearer
from admin.core.models.core import Capsule
from services.common.authorization import authorize_sync

router = Router(tags=["Capsules"])


@router.get("/", auth=AuthBearer())
def list_capsules(request):
    """List all active capsules."""
    authorize_sync(request, action="agent:read", resource="capsules")
    capsules = Capsule.objects.filter(status=Capsule.STATUS_ACTIVE).values(
        "id", "name", "version", "status", "description", "created_at"
    )
    return list(capsules)
