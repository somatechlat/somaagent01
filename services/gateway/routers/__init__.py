"""Router bundle for the gateway API."""

from __future__ import annotations

from fastapi import APIRouter

from . import (
    admin,
    admin_kafka,
    admin_memory,
    admin_migrate,
    attachments,
    av,
    capsules,
    celery_api,
    chat,
    chat_full,
    constitution,
    dlq,
    health,
    health_full,
    keys,
    llm,
    memory,
    memory_exports,
    memory_mutations,
    notifications,
    profiles,
    requeue,
    route,
    runtime_config,
    sessions,
    sessions_events,
    sessions_full,
    speech,
    sse,
    tasks,
    tool_catalog,
    tool_request,
    tools_full,
    ui_settings,
    uploads,
    uploads_full,
    websocket,
    workdir,
    features,
    weights,
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
        keys.router,
        workdir.router,
        features.router,
        weights.router,
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
        uploads.router,
        runtime_config.router,
        tasks.router,
    ):
        router.include_router(sub)
    return router


__all__ = ["build_router"]
