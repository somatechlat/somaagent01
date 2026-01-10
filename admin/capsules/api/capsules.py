"""Module capsules."""

from ninja import Router

router = Router(tags=["Capsules"])

@router.get("/")
def list_capsules(request):
    """List all capsules (Placeholder)."""
    return []
