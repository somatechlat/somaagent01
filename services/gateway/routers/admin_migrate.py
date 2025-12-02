"""Admin migrate/export/import endpoints extracted from the gateway monolith."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from python.integrations.somabrain_client import SomaBrainClient
from services.common.authorization import _require_admin_scope, authorize_request

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
    auth = await authorize_request(request, meta)
    _require_admin_scope(auth)
