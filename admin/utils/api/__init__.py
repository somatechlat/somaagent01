"""Utils API routers - Django Ninja.

VIBE Compliant - No placeholders.
"""

from ninja import Router

router = Router(tags=["utils"])


@router.get("/health")
def utils_health(request):
    """Utils module health check endpoint."""
    return {"status": "ok", "module": "utils"}
