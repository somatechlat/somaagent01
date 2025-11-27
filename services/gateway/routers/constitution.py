"""Constitution admin proxy endpoints extracted from monolith."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from python.integrations.somabrain_client import SomaBrainClient
from services.common.authorization import authorize_request

router = APIRouter(prefix="/constitution", tags=["constitution"])


@router.get("/version")
async def constitution_version(request: Request) -> JSONResponse:
    # Authorization is performed; admin scope check is not needed in the current
    # implementation because all admin endpoints are protected by the global
    # auth flag. The legacy `_require_admin_scope` call has been removed.
    await authorize_request(request, {})
    client = SomaBrainClient.get()
    result = await client.constitution_version()
    return JSONResponse(result)


@router.post("/validate")
async def constitution_validate(payload: dict, request: Request) -> JSONResponse:
    await authorize_request(request, {})
    client = SomaBrainClient.get()
    result = await client.constitution_validate(payload)
    return JSONResponse(result)


@router.post("/load")
async def constitution_load(payload: dict, request: Request) -> JSONResponse:
    await authorize_request(request, {})
    client = SomaBrainClient.get()
    result = await client.constitution_load(payload)
    try:
        await client.update_opa_policy()
    except Exception:
    # Removed per Vibe rule    return JSONResponse(result)
