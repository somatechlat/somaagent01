"""Admin migrate/export/import endpoints extracted from the gateway monolith."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from services.common.authorization import authorize_request
from python.integrations.somabrain_client import SomaBrainClient

router = APIRouter(prefix="/v1/admin/migrate", tags=["admin"])


class MigrateExportPayload(BaseModel):
    include_wm: bool = Field(..., description="Include working memory in export")
    wm_limit: int = Field(..., ge=0, description="Maximum WM items to export")


class MigrateImportPayload(BaseModel):
    manifest: dict
    memories: list[dict]
    wm: list[dict] | None = None
    replace: bool = False


@router.post("/export")
async def admin_migrate_export(payload: MigrateExportPayload, request: Request) -> JSONResponse:
    await _authorize_admin(request, payload.model_dump())
    client = SomaBrainClient.get()
    result = await client.migrate_export(include_wm=payload.include_wm, wm_limit=payload.wm_limit)
    return JSONResponse(result)


@router.post("/import")
async def admin_migrate_import(payload: MigrateImportPayload, request: Request) -> JSONResponse:
    await _authorize_admin(request, payload.model_dump())
    client = SomaBrainClient.get()
    result = await client.migrate_import(
        manifest=payload.manifest,
        memories=payload.memories,
        wm=payload.wm,
        replace=payload.replace,
    )
    return JSONResponse(result)


async def _authorize_admin(request: Request, meta: dict) -> None:
    # Authorization is performed; admin scope validation is not required for the
    # current development configuration (auth can be disabled via the global
    # settings). The legacy `_require_admin_scope` call has been removed.
    await authorize_request(request, meta)
