"""AV test endpoint extracted from gateway monolith."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/v1", tags=["av"])


@router.get("/av/test")
async def av_test():
    return {"status": "ok"}
