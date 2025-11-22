"""Router assembly for the gateway – single point of inclusion."""
from __future__ import annotations

from fastapi import APIRouter

# Core/public routers
from services.gateway.routers import (
    health,
    ops_status,
    chat,
    llm,
    llm_credentials,
    sessions,
    sessions_events,
    uploads,
    attachments,
    sse,
    websocket,
    root_ui,
    ui_static,
    ui_settings_sections,
)


def build_router() -> APIRouter:
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
    router.include_router(ui_settings_sections.router)
    # Static/UI catch-alls last so they do not shadow API prefixes
    router.include_router(root_ui.router)
    router.include_router(ui_static.router)
    return router


__all__ = ["build_router"]
