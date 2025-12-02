"""API key management endpoints extracted from gateway monolith."""

from __future__ import annotations

import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.common.api_key_store import ApiKeyStore, ApiKeyResponse
from services.common.admin_settings import ADMIN_SETTINGS

router = APIRouter(prefix="/v1/keys", tags=["auth"])
STORE = ApiKeyStore(ADMIN_SETTINGS.postgres_dsn)


class ApiKeyCreateRequest(BaseModel):
    name: str
    permissions: list[str] | None = None


class ApiKeyCreateResponse(BaseModel):
    key_id: str
    token: str
    name: str
    permissions: list[str] | None = None


@router.post("", response_model=ApiKeyCreateResponse)
async def create_api_key(body: ApiKeyCreateRequest) -> ApiKeyCreateResponse:
    token = uuid.uuid4().hex
    key = await STORE.create(name=body.name, token=token, permissions=body.permissions or [])
    return ApiKeyCreateResponse(
        key_id=key.id, token=token, name=key.name, permissions=key.permissions
    )


@router.get("", response_model=list[ApiKeyResponse])
async def list_api_keys() -> list[ApiKeyResponse]:
    return await STORE.list()


@router.delete("/{key_id}", status_code=204)
async def delete_api_key(key_id: str):
    deleted = await STORE.delete(key_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="key_not_found")
    return None
