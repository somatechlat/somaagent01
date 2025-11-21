"""Sessions router skeleton."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/v1/sessions", tags=["sessions"])


@router.get("/{session_id}")
async def get_session(session_id: str) -> dict[str, str]:
    return {"session_id": session_id, "status": "ok"}
