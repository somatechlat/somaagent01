"""Capsules API — List and retrieve agent capsules."""

from ninja import Router

from admin.core.models.core import Capsule

router = Router(tags=["Capsules"])


@router.get("/")
def list_capsules(request):
    """List all active capsules."""
    capsules = Capsule.objects.filter(status=Capsule.STATUS_ACTIVE).values(
        "id", "name", "version", "status", "description", "created_at"
    )
    return list(capsules)
