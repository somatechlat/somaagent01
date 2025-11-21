"""LLM invoke endpoints extracted from gateway monolith (minimal functional)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/v1/llm", tags=["llm"])


class LlmInvokeRequest(BaseModel):
    prompt: str
    metadata: dict | None = None


@router.post("/invoke")
async def invoke(req: LlmInvokeRequest) -> dict:
    if not req.prompt:
        raise HTTPException(status_code=400, detail="prompt_required")
    # Placeholder real behaviour: echo prompt with metadata
    return {"result": req.prompt, "metadata": req.metadata or {}}


@router.post("/invoke/stream")
async def invoke_stream(req: LlmInvokeRequest) -> dict:
    if not req.prompt:
        raise HTTPException(status_code=400, detail="prompt_required")
    # Streaming stub: return a tagged response; real streaming would be SSE
    return {"stream": [req.prompt], "metadata": req.metadata or {}}
