"""Auth endpoints extracted from gateway monolith (login/callback/logout stubs with real responses)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.get("/login")
async def login() -> JSONResponse:
    # In real deployments, redirect to identity provider; here we return a stub token.
    return JSONResponse(
        {"status": "ok", "message": "login placeholder; integrate IdP"}, status_code=200
    )


@router.get("/callback")
async def callback(code: str | None = None, state: str | None = None) -> JSONResponse:
    if not code:
        raise HTTPException(status_code=400, detail="missing_code")
    return JSONResponse({"status": "ok", "code": code, "state": state})


@router.post("/logout")
async def logout() -> JSONResponse:
    return JSONResponse({"status": "logged_out"})
