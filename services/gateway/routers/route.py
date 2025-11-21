"""Route decision endpoint extracted from gateway monolith."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/v1", tags=["route"])


class RouteRequest(BaseModel):
    intent: str
    metadata: dict | None = None


class RouteResponse(BaseModel):
    target: str
    reason: str | None = None


@router.post("/route", response_model=RouteResponse)
async def route(req: RouteRequest) -> RouteResponse:
    # Minimal routing logic: map intent keywords
    intent = req.intent.lower()
    if "tool" in intent:
        return RouteResponse(target="tool_executor", reason="intent contains 'tool'")
    if "memory" in intent:
        return RouteResponse(target="memory", reason="intent contains 'memory'")
    return RouteResponse(target="gateway", reason="default")
