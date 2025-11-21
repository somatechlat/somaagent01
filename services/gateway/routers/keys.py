"""API key management endpoints extracted from gateway monolith."""
from __future__ import annotations

import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.common.api_key_store import InMemoryApiKeyStore, ApiKeyMetadata

router = APIRouter(prefix="/v1/keys", tags=["auth"])
STORE = InMemoryApiKeyStore()


class ApiKeyCreateRequest(BaseModel):
    name: str
    permissions: list[str] | None = None


class ApiKeyCreateResponse(BaseModel):
    key_id: str
    token: str
    name: str
    permissions: list[str] | None = None


class ApiKeyResponse(BaseModel):
    key_id: str
    name: str
    permissions: list[str] | None = None
    created_at: float
    created_by: str | None = None
    prefix: str
    last_used_at: float | None = None
    revoked: bool


@router.post("", response_model=ApiKeyCreateResponse)
async def create_api_key(body: ApiKeyCreateRequest) -> ApiKeyCreateResponse:
    key = await STORE.create_key(label=body.name, created_by=None)
    return ApiKeyCreateResponse(
        key_id=key.key_id,
        token=key.secret,
        name=body.name,
        permissions=body.permissions or [],
    )


@router.get("", response_model=list[ApiKeyResponse])
async def list_api_keys() -> list[ApiKeyResponse]:
    records = await STORE.list_keys()
    return [
        ApiKeyResponse(
            key_id=r.key_id,
            name=r.label,
            permissions=None,
            created_at=r.created_at,
            created_by=r.created_by,
            prefix=r.prefix,
            last_used_at=r.last_used_at,
            revoked=r.revoked,
        )
        for r in records
    ]


@router.delete("/{key_id}", status_code=204)
async def delete_api_key(key_id: str):
    # InMemory store: revoke acts as delete for now
    await STORE.revoke_key(key_id)
    # verify existence
    records = await STORE.list_keys()
    if not any(r.key_id == key_id for r in records):
        raise HTTPException(status_code=404, detail="key_not_found")
    return None
