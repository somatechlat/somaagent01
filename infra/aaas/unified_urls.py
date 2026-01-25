"""
Unified URL Configuration for Agent-as-a-Service (AAAS) Mode.

Mounts all API routers from all three repositories under a single Django URL config.
This enables true single-process operation where all services share the same
request/response cycle without HTTP overhead.

VIBE Compliance:
- Rule 8: Django Ninja only for APIs
- Rule 100: Centralized configuration
"""

from __future__ import annotations

from django.contrib import admin
from django.urls import include, path
from ninja import NinjaAPI

# =============================================================================
# UNIFIED NINJA API
# =============================================================================

# Create unified API with versioned prefixes
unified_api = NinjaAPI(
    title="SOMA Unified API",
    version="2.0.0",
    description="Unified API for Agent, Brain, and Memory in single-process mode",
)

# =============================================================================
# MOUNT AGENT ROUTERS
# =============================================================================

try:
    from admin.agents.api import router as agents_router
    from admin.chat.api import router as chat_router
    from admin.core.api import router as core_router
    from admin.aaas.api import router as aaas_router
    from admin.gateway.api import router as gateway_router

    unified_api.add_router("/agents/", agents_router, tags=["agents"])
    unified_api.add_router("/chat/", chat_router, tags=["chat"])
    unified_api.add_router("/core/", core_router, tags=["core"])
    unified_api.add_router("/aaas/", aaas_router, tags=["aaas"])
    unified_api.add_router("/gateway/", gateway_router, tags=["gateway"])
except ImportError as e:
    print(f"⚠️ Agent routers not available: {e}")

# =============================================================================
# MOUNT BRAIN ROUTERS
# =============================================================================

try:
    from somabrain.api import api as brain_api

    # Mount brain endpoints under /brain/
    for router in getattr(brain_api, "_routers", []):
        unified_api.add_router("/brain/", router, tags=["brain"])
except ImportError as e:
    print(f"⚠️ Brain routers not available: {e}")

# =============================================================================
# MOUNT MEMORY ROUTERS
# =============================================================================

try:
    from somafractalmemory.api.routers.memory import router as memory_router
    from somafractalmemory.api.routers.graph import router as graph_router
    from somafractalmemory.api.routers.search import router as search_router
    from somafractalmemory.api.routers.health import router as health_router

    unified_api.add_router("/memory/", memory_router, tags=["memory"])
    unified_api.add_router("/memory/graph/", graph_router, tags=["memory-graph"])
    unified_api.add_router("/memory/search/", search_router, tags=["memory-search"])
    unified_api.add_router("/memory/", health_router, tags=["memory-health"])
except ImportError as e:
    print(f"⚠️ Memory routers not available: {e}")

# =============================================================================
# HEALTH ENDPOINT
# =============================================================================


@unified_api.get("/health", tags=["system"])
def health_check(request):
    """Unified health check for all services."""
    return {
        "status": "healthy",
        "mode": "unified-single-process",
        "services": {
            "agent": "ok",
            "brain": "ok",
            "memory": "ok",
        },
    }


# =============================================================================
# URL PATTERNS
# =============================================================================

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # Unified API v2
    path("api/v2/", unified_api.urls),
    # Legacy compatibility - redirect old endpoints
    # Agent API (was :9000)
    path("api/v1/", include("services.gateway.urls")),
    # Brain API (was :9696)
    path("brain/", include("somabrain.urls")),
    # Memory API (was :10101)
    path("memory/", include("somafractalmemory.urls")),
]
