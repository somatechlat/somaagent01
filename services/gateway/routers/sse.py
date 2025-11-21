"""SSE and runtime/config helpers (extracted)."""

from __future__ import annotations

from fastapi import APIRouter

from src.core.config import cfg

router = APIRouter(prefix="/v1", tags=["sse"])


def _flag_truthy(val: str | None, default: bool = False) -> bool:
    if val is None:
        return default
    return str(val).lower() in {"true", "1", "yes", "on"}


def sse_enabled() -> bool:
    return not _flag_truthy(cfg.env("GATEWAY_DISABLE_SSE"), False)


@router.get("/sse/enabled")
async def sse_enabled_endpoint() -> dict[str, bool]:
    return {"enabled": sse_enabled()}
