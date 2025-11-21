"""Constitution admin proxy endpoints extracted from monolith."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from services.common.authorization import authorize_request, _require_admin_scope
from python.integrations.somabrain_client import SomaBrainClient

router = APIRouter(prefix="/constitution", tags=["constitution"])


@router.get("/version")
async def constitution_version(request: Request) -> JSONResponse:
    auth = await authorize_request(request, {})
    _require_admin_scope(auth)
    client = SomaBrainClient.get()
    result = await client.constitution_version()
    return JSONResponse(result)


@router.post("/validate")
async def constitution_validate(payload: dict, request: Request) -> JSONResponse:
    auth = await authorize_request(request, {})
    _require_admin_scope(auth)
    client = SomaBrainClient.get()
    result = await client.constitution_validate(payload)
    return JSONResponse(result)


@router.post("/load")
async def constitution_load(payload: dict, request: Request) -> JSONResponse:
    auth = await authorize_request(request, {})
    _require_admin_scope(auth)
    client = SomaBrainClient.get()
    result = await client.constitution_load(payload)
    try:
        await client.update_opa_policy()
    except Exception:
        pass
    return JSONResponse(result)
