"""Features API routers - Django Ninja.


"""

from ninja import Router

router = Router(tags=["features"])


@router.get("/health")
def features_health(request):
    """Features module health check endpoint."""
    return {"status": "ok", "module": "features"}
