"""Router bundle for the decomposed gateway.

These routers are lightweight, fully functional stubs that can be mounted by
the main gateway ASGI app as decomposition progresses. They avoid placeholders
by providing real, minimal endpoints for their domains.
"""

from __future__ import annotations

from fastapi import APIRouter

# Import all sub‑routers that compose the gateway API. The ``health`` router
# provides a minimal liveness check, while ``health_full`` offers the detailed
# health aggregation. Both are included in the final router.
from . import (
    admin,
    chat,
    chat_full,
    health,
    health_full,
    admin_memory,
    admin_migrate,
    constitution,
    admin_kafka,
    uploads_full,
    tools_full,
    sse,
    sessions_full,
    sessions_events,
    attachments,
    memory_exports,
    tool_catalog,
    notifications,
    auth,
    keys,
    workdir,
    tool_request,
    ui_settings,
    llm,
    requeue,
    dlq,
    memory_mutations,
    capsules,
    route,
    profiles,
    speech,
    av,
    websocket,
    celery_api,
    memory,
    sessions,
    tools,
    uploads,
    runtime_config,
    tasks,
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
        tool_catalog.router,
        notifications.router,
        auth.router,
        keys.router,
        workdir.router,
        tool_request.router,
        ui_settings.router,
        llm.router,
        requeue.router,
        dlq.router,
        memory_mutations.router,
        capsules.router,
        route.router,
        profiles.router,
        speech.router,
        av.router,
        websocket.router,
        celery_api.router,
        memory.router,
        sessions.router,
        tools.router,
        uploads.router,
        runtime_config.router,
        tasks.router,
    ):
        router.include_router(sub)
    return router


__all__ = ["build_router"]
