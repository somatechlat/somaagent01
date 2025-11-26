"""Development Authentication Endpoints.

Provides a mechanism for the UI to obtain a valid internal token for testing
and development purposes. This is NOT a production authentication service.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from services.common.internal_token import get_token
from src.core.config import cfg

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.get("/login")
async def login() -> JSONResponse:
    """Obtain a development authentication token.

    Returns the configured internal service token (SA01_AUTH_INTERNAL_TOKEN)
    if available. This allows the Web UI to authenticate against protected
    endpoints in a development environment.
    """
    token = await get_token()
    if not token:
        # Fallback to config if not yet in Redis (e.g. early startup)
        token = cfg.env("SA01_AUTH_INTERNAL_TOKEN")

    if not token:
        return JSONResponse(
            {"status": "error", "message": "no_internal_token_configured"}, status_code=500
        )

    return JSONResponse({"status": "ok", "token": token}, status_code=200)


@router.get("/callback")
async def callback(code: str | None = None, state: str | None = None) -> JSONResponse:
    """Mock OAuth callback for development flows."""
    if not code:
        raise HTTPException(status_code=400, detail="missing_code")
    return JSONResponse({"status": "ok", "code": code, "state": state})


@router.post("/logout")
async def logout() -> JSONResponse:
    """Clear the session (client-side only in dev mode)."""
    return JSONResponse({"status": "logged_out"})
