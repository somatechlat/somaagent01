"""Router bundle for the decomposed gateway.

These routers are lightweight, fully functional stubs that can be mounted by
the main gateway ASGI app as decomposition progresses. They avoid placeholders
by providing real, minimal endpoints for their domains.
"""

from __future__ import annotations

from fastapi import APIRouter

from . import (
    admin,
    chat,
    chat_full,
    health,
    health_full,
    memory,
    sessions,
    tools,
    uploads,
    runtime_config,
    admin_memory,
    admin_migrate,
    constitution,
    admin_kafka,
    uploads_full,
    tools_full,
    sse,
    sessions_full,
    celery_api,
    sessions_events,
    attachments,
    memory_exports,
)


def build_router() -> APIRouter:
    router = APIRouter()
    for sub in (
        admin.router,
        chat.router,
        chat_full.router,
        health.router,
        health_full.router,
        admin_memory.router,
        admin_migrate.router,
        constitution.router,
        admin_kafka.router,
        uploads_full.router,
        tools_full.router,
        sse.router,
        sessions_full.router,
        sessions_events.router,
        attachments.router,
        memory_exports.router,
        celery_api.router,
        memory.router,
        sessions.router,
        tools.router,
        uploads.router,
        runtime_config.router,
    ):
        router.include_router(sub)
    return router


__all__ = ["build_router"]
