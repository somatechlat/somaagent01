"""
URL configuration for the agent in AAAS deployment mode.

This is the agent's own URL conf and nothing else. SomaBrain and
somafractalmemory are separate containers reached over the transport
(T-1: agent -> SomaBrain only; SomaBrain -> SFM; the agent never talks to
SFM). They were previously mounted here in-process, which was both broken
and wrong:

- ``include("somabrain.urls")`` and ``include("somafractalmemory.urls")``
  named modules that do not exist in either repository.
- ``from somabrain.api import api`` named a module that is an empty
  package with no ``api`` attribute.
- Mounting SFM routers into the agent's URLconf is a direct T-1 violation.

A cross-repo mount is not a faster transport. It is a second, silent
coupling that hides the real one.

VIBE Compliance:
- Rule 8: Django Ninja only for APIs
- Rule 100: Centralized configuration
"""

from __future__ import annotations

from django.contrib import admin
from django.urls import include, path
from ninja import NinjaAPI

# =============================================================================
# AGENT NINJA API
# =============================================================================

unified_api = NinjaAPI(
    title="Soma Agent API",
    version="2.0.0",
    description="Agent API. SomaBrain and SFM are separate services reached over the transport.",
)

# =============================================================================
# MOUNT AGENT ROUTERS
# =============================================================================

# Fail closed. A router the URLconf cannot import is not a degraded mode — it
# is a broken deployment, and logging at INFO while serving an empty surface
# is the stub this codebase forbids.
from admin.aaas.api import router as aaas_router
from admin.agents.api import router as agents_router
from admin.chat.api import router as chat_router
from admin.core.api import router as core_router
from admin.gateway.api import router as gateway_router

unified_api.add_router("/agents/", agents_router, tags=["agents"])
unified_api.add_router("/chat/", chat_router, tags=["chat"])
unified_api.add_router("/core/", core_router, tags=["core"])
unified_api.add_router("/aaas/", aaas_router, tags=["aaas"])
unified_api.add_router("/gateway/", gateway_router, tags=["gateway"])


# =============================================================================
# HEALTH ENDPOINT
# =============================================================================


@unified_api.get("/health", tags=["system"])
def health_check(request):
    """Report this process's own health.

    The agent cannot see SomaBrain or SFM from here, and it must not claim to.
    A diagnostics response that prints ``"ok"`` for a peer it never asked is a
    constant dressed as a reading. Peer health is the peer's own endpoint.
    """
    return {
        "status": "healthy",
        "mode": "aaas",
        "service": "agent",
    }


# =============================================================================
# URL PATTERNS
# =============================================================================

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # Agent API v2
    path("api/v2/", unified_api.urls),
    # Agent API (was :9000)
    path("api/v1/", include("services.gateway.urls")),
]
