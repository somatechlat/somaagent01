"""
Django URL Configuration for SomaAgent01.


- Admin interface at /admin/
- API at /api/v2/
- SPA frontend catch-all (serves index.html for client-side routing)
"""

from django.conf import settings
from django.contrib import admin
from django.http import FileResponse, JsonResponse
from django.urls import path, re_path

from admin.api import api


def health_check(request):
    """Health check endpoint for Docker and load balancers."""
    return JsonResponse(
        {
            "status": "ok",
            "service": "somaagent-gateway",
            "version": "1.0.0",
        }
    )


def serve_spa(request, path=""):
    """
    Serve the SPA index.html for all client-side routes.

    Django handles:
    - /admin/ → Django Admin
    - /api/v2/ → Django Ninja API
    - Everything else → SPA (React/Lit frontend)

    
    """
    index_path = settings.BASE_DIR / "webui" / "dist" / "index.html"
    if index_path.exists():
        return FileResponse(open(index_path, "rb"), content_type="text/html")
    return JsonResponse({"error": "Frontend not built. Run: cd webui && npm run build"}, status=404)


urlpatterns = [
    # Django Admin
    path("admin/", admin.site.urls),
    # Django Ninja API
    path("api/v2/", api.urls),
    # Health endpoints
    path("api/health/", health_check),
    path("health/", health_check),
    # SPA catch-all (must be last)
    re_path(r"^(?!admin/|api/).*$", serve_spa, name="spa"),
]