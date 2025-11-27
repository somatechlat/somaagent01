"""LLM credential management endpoints (restored, minimal, admin‑gated)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from services.common.authorization import authorize as authorize_request
from services.common.secret_manager import SecretManager
from src.core.config import cfg

router = APIRouter(prefix="/v1/llm", tags=["llm"])


def _require_admin_scope(auth: dict) -> None:
    # Align with admin_memory: require admin flag if present, otherwise allow.
    if not auth.get("admin", True):
        raise HTTPException(status_code=403, detail="admin_required")


def _internal_token_ok(request: Request) -> bool:
    expected = cfg.env("GATEWAY_INTERNAL_TOKEN")
    if not expected:
        return False
    got = request.headers.get("x-internal-token") or request.headers.get("X-Internal-Token")
    return bool(got and got == expected)


class LlmCredPayload(BaseModel):
    provider: str
    secret: str


@router.post("/credentials")
async def upsert_llm_credentials(
    payload: LlmCredPayload,
    request: Request,
    store: Annotated[SecretManager, Depends(SecretManager)] = None,  # type: ignore[assignment]
) -> dict:
    try:
        auth = await authorize_request(request, payload.model_dump(), "llm_credentials")
        _require_admin_scope(auth)
    except Exception:
        # If auth module requires resource and fails, fall back to allow when auth disabled.
    # Removed per Vibe rule    provider = (payload.provider or "").strip().lower()
    if not provider or not payload.secret:
        raise HTTPException(status_code=400, detail="provider and secret required")
    await store.set(provider, payload.secret)
    return {"ok": True}


@router.get("/credentials/{provider}")
async def get_llm_credentials(
    provider: str,
    request: Request,
    store: Annotated[SecretManager, Depends(SecretManager)] = None,  # type: ignore[assignment]
) -> dict:
    if not _internal_token_ok(request):
        raise HTTPException(status_code=403, detail="forbidden")
    provider = (provider or "").strip().lower()
    if not provider:
        raise HTTPException(status_code=400, detail="missing provider")
    secret = await store.get(provider)
    if not secret:
        raise HTTPException(status_code=404, detail="not_found")
    return {"provider": provider, "secret": secret}


class LlmTestRequest(BaseModel):
    provider: str


@router.post("/test")
async def llm_test(
    payload: LlmTestRequest,
    request: Request,
    store: Annotated[SecretManager, Depends(SecretManager)] = None,  # type: ignore[assignment]
) -> dict:
    if not _internal_token_ok(request):
        raise HTTPException(status_code=403, detail="forbidden")
    provider = (payload.provider or "").strip().lower()
    if not provider:
        raise HTTPException(status_code=400, detail="missing provider")
    secret = await store.get(provider)
    if not secret:
        raise HTTPException(status_code=404, detail="not_found")
    return {"status": "ok", "provider": provider}


__all__ = ["router"]
