"""Memory router skeleton."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/v1/memory", tags=["memory"])


@router.get("/ping")
async def ping() -> dict[str, str]:
    return {"status": "ok"}
