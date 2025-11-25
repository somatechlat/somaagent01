"""Router assembly for the gateway – single point of inclusion."""
from __future__ import annotations

from fastapi import APIRouter

# Core/public routers
from services.gateway.routers import (
    attachments,
    chat,
    health,
    llm,
    llm_credentials,
    # New notifications API used by the UI toast/notification system
    notifications,
    ops_status,
    root_ui,
    sessions,
    sessions_events,
    sse,
    ui_settings_sections,
    ui_static,
    uploads,
    websocket,
    # tunnel router removed to avoid duplicate endpoint definitions
)


def build_router() -> APIRouter:
    # Local import avoids circular import; metrics endpoints live at package root
    from services.gateway import metrics_endpoints

    router = APIRouter()
    router.include_router(health.router)
    router.include_router(ops_status.router)
    # API routers (order matters: keep catch-alls last)
    router.include_router(chat.router)
    router.include_router(llm.router)
    router.include_router(llm_credentials.router)
    router.include_router(sessions.router)
    router.include_router(sessions_events.router)
    router.include_router(uploads.router)
    router.include_router(attachments.router)
    router.include_router(sse.router)
    router.include_router(websocket.router)
    router.include_router(metrics_endpoints.router)
    router.include_router(ui_settings_sections.router)
    router.include_router(notifications.router)
    # Tunnel management endpoint is provided via the dedicated tunnel_proxy router
    # (included explicitly in services.gateway.main). The legacy tunnel router
    # caused duplicate route definitions and resulted in 405 errors for POST.
    # It has been removed.
    # Include scheduler router to serve task management endpoints
    try:
        from services.gateway.routers import scheduler as _scheduler_router
        router.include_router(_scheduler_router.router)
    except Exception as e:
        # If the scheduler module fails to import, log the error but do not break the app.
        import logging
        logging.getLogger(__name__).warning("Scheduler router not loaded: %s", e)
    # Feature flags endpoint (optional; skip if module absent)
    try:
        from services.gateway.routers import features as _features_router
    except ImportError:
        _features_router = None
    if _features_router:
        router.include_router(_features_router.router)
    # Static/UI catch-alls last so they do not shadow API prefixes
    router.include_router(root_ui.router)
    router.include_router(ui_static.router)
    return router


__all__ = ["build_router"]
