"""Chat router skeleton.

Implements a minimal echo endpoint to keep the router functional while the
full chat flow is extracted from the monolith.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/v1/chat", tags=["chat"])


@router.post("/echo")
async def echo(message: str) -> dict[str, str]:
    return {"message": message}
