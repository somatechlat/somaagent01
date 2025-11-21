"""Router bundle for the decomposed gateway.

These routers are lightweight, fully functional stubs that can be mounted by
the main gateway ASGI app as decomposition progresses. They avoid placeholders
by providing real, minimal endpoints for their domains.
"""

from __future__ import annotations

from fastapi import APIRouter

from . import admin, chat, health, memory, sessions, tools, uploads


def build_router() -> APIRouter:
    router = APIRouter()
    for sub in (
        admin.router,
        chat.router,
        health.router,
        memory.router,
        sessions.router,
        tools.router,
        uploads.router,
    ):
        router.include_router(sub)
    return router


__all__ = ["build_router"]
