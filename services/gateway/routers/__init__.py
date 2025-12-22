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
    chat_full,
    constitution,
    a2a,
    dlq,
    feature_flags,
    features,
    describe,
    health,
    keys,
    llm,
    memory_exports,
    memory_mutations,
    multimodal,
    notifications,
    profiles,
    requeue,
    route,
    runtime_config,
    sessions,
    skins,
    speech,
    sse,
    tool_catalog,
    tool_request,
    tools_full,
    ui_settings,
    uploads_full,
    websocket,
    weights,
    workdir,
)


def build_router() -> APIRouter:
    router = APIRouter()
    for sub in (
        admin.router,
        chat_full.router,
        health.router,
        admin_memory.router,
        admin_migrate.router,
        constitution.router,
        admin_kafka.router,
        uploads_full.router,
        tools_full.router,
        sse.router,
        attachments.router,
        attachments.internal_router,
        memory_exports.router,
        tool_catalog.router,
        notifications.router,
        keys.router,
        workdir.router,
        feature_flags.router,
        features.router,
        describe.router,
        weights.router,
        tool_request.router,
        ui_settings.router,
        llm.router,
        requeue.router,
        dlq.router,
        memory_mutations.router,
        capsules.router,
        skins.router,
        a2a.router,
        route.router,
        profiles.router,
        speech.router,
        av.router,
        websocket.router,
        sessions.router,
        runtime_config.router,
        multimodal.router,
    ):
        router.include_router(sub)
    return router


__all__ = ["build_router"]
