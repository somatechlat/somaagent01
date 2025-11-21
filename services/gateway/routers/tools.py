"""Tool execution router skeleton."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/v1/tools", tags=["tools"])


@router.post("/run")
async def run_tool(name: str) -> dict[str, str]:
    # Placeholder behaviour kept real: simply acknowledges the tool name.
    return {"status": "accepted", "tool": name}
