"""AgentSkin Theme API Router.

Migrated from: services/gateway/routers/skins.py
Pure Django Ninja with XSS validation and OPA authorization.


"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

from django.http import HttpRequest
from ninja import Router
from pydantic import BaseModel, Field, field_validator

from admin.common.exceptions import NotFoundError, ValidationError

router = Router(tags=["skins"])
logger = logging.getLogger(__name__)


def _get_store():
    """Execute get store.
        """

    from services.common.skins_store import SkinsStore

    return SkinsStore()


def _validate_no_xss(variables: dict) -> dict:
    """Validate no XSS patterns in CSS variables."""
    from services.common.skins_store import validate_no_xss

    try:
        validate_no_xss(variables)
    except ValueError as e:
        raise ValidationError(str(e))
    return variables


# === Request/Response Models ===


class SkinCreateRequest(BaseModel):
    """Skin creation request."""

    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    author: Optional[str] = Field(None, max_length=100)
    variables: dict[str, str] = Field(default_factory=dict)
    changelog: list[dict[str, Any]] = Field(default_factory=list)

    @field_validator("variables")
    @classmethod
    def validate_variables(cls, v):
        """Execute validate variables.

            Args:
                v: The v.
            """

        return _validate_no_xss(v)


class SkinUpdateRequest(BaseModel):
    """Skin update request."""

    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    version: Optional[str] = Field(None, pattern=r"^\d+\.\d+\.\d+$")
    author: Optional[str] = Field(None, max_length=100)
    variables: Optional[dict[str, str]] = None
    changelog: Optional[list[dict[str, Any]]] = None

    @field_validator("variables")
    @classmethod
    def validate_variables(cls, v):
        """Execute validate variables.

            Args:
                v: The v.
            """

        if v is not None:
            return _validate_no_xss(v)
        return v


class SkinResponse(BaseModel):
    """Skin response."""

    id: str
    tenant_id: str
    name: str
    description: str
    version: str
    author: str
    variables: dict[str, str]
    changelog: list[dict[str, Any]]
    is_approved: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SkinListResponse(BaseModel):
    """Skin list response."""

    skins: list[SkinResponse]
    count: int


def _record_to_response(rec) -> dict:
    """Execute record to response.

        Args:
            rec: The rec.
        """

    return {
        "id": rec.skin_id,
        "tenant_id": rec.tenant_id,
        "name": rec.name,
        "description": rec.description,
        "version": rec.version,
        "author": rec.author,
        "variables": rec.variables,
        "changelog": rec.changelog,
        "is_approved": rec.is_approved,
        "created_at": rec.created_at.isoformat() if rec.created_at else None,
        "updated_at": rec.updated_at.isoformat() if rec.updated_at else None,
    }


def _get_tenant_id(request: HttpRequest) -> str:
    """Execute get tenant id.

        Args:
            request: The request.
        """

    return request.headers.get("X-Tenant-Id", "00000000-0000-0000-0000-000000000000")


async def _is_admin(request: HttpRequest) -> bool:
    """Execute is admin.

        Args:
            request: The request.
        """

    try:
        from services.common.authorization import authorize

        await authorize(request, action="skin:upload", resource="skins")
        return True
    except Exception:
        return False


@router.get("", response=SkinListResponse, summary="List skins")
async def list_skins(request: HttpRequest) -> dict:
    """List available skins for the tenant."""
    store = _get_store()
    await store.ensure_schema()

    tenant_id = _get_tenant_id(request)
    is_admin = await _is_admin(request)

    skins = await store.list(tenant_id=tenant_id, include_unapproved=is_admin)

    return {
        "skins": [_record_to_response(s) for s in skins],
        "count": len(skins),
    }


@router.get("/{skin_id}", response=SkinResponse, summary="Get skin")
async def get_skin(request: HttpRequest, skin_id: str) -> dict:
    """Get a single skin by ID."""
    store = _get_store()
    await store.ensure_schema()

    tenant_id = _get_tenant_id(request)
    is_admin = await _is_admin(request)

    skin = await store.get(skin_id)
    if not skin:
        raise NotFoundError("skin", skin_id)

    # Tenant isolation
    global_tenant = "00000000-0000-0000-0000-000000000000"
    if skin.tenant_id != tenant_id and skin.tenant_id != global_tenant:
        raise NotFoundError("skin", skin_id)

    if not is_admin and not skin.is_approved:
        raise NotFoundError("skin", skin_id)

    return _record_to_response(skin)


@router.post("", response=SkinResponse, summary="Create skin")
async def create_skin(request: HttpRequest, payload: SkinCreateRequest) -> dict:
    """Upload a new skin (admin only)."""
    from services.common.skins_store import SkinRecord

    from services.common.authorization import authorize

    store = _get_store()
    await store.ensure_schema()

    auth = await authorize(request, action="skin:upload", resource="skins")
    tenant_id = auth.get("tenant", _get_tenant_id(request))

    existing = await store.get_by_name(tenant_id, payload.name)
    if existing:
        raise ValidationError(f"Skin '{payload.name}' already exists")

    skin_id = str(uuid.uuid4())
    record = SkinRecord(
        skin_id=skin_id,
        tenant_id=tenant_id,
        name=payload.name,
        description=payload.description or "",
        version=payload.version,
        author=payload.author or "",
        variables=payload.variables,
        changelog=payload.changelog,
        is_approved=False,
    )

    await store.create(record)
    created = await store.get(skin_id)

    return _record_to_response(created)


@router.put("/{skin_id}", response=SkinResponse, summary="Update skin")
async def update_skin(request: HttpRequest, skin_id: str, payload: SkinUpdateRequest) -> dict:
    """Update an existing skin (admin only)."""
    from services.common.authorization import authorize

    store = _get_store()
    await store.ensure_schema()
    await authorize(request, action="skin:update", resource="skins")

    skin = await store.get(skin_id)
    if not skin:
        raise NotFoundError("skin", skin_id)

    updates = {}
    for field in ["name", "description", "version", "author", "variables", "changelog"]:
        value = getattr(payload, field, None)
        if value is not None:
            updates[field] = value

    if not updates:
        raise ValidationError("No fields to update")

    await store.update(skin_id, updates)
    updated = await store.get(skin_id)

    return _record_to_response(updated)


@router.delete("/{skin_id}", summary="Delete skin")
async def delete_skin(request: HttpRequest, skin_id: str) -> dict:
    """Delete a skin (admin only)."""
    from services.common.authorization import authorize

    store = _get_store()
    await store.ensure_schema()
    await authorize(request, action="skin:delete", resource="skins")

    skin = await store.get(skin_id)
    if not skin:
        raise NotFoundError("skin", skin_id)

    await store.delete(skin_id)
    return {"deleted": skin_id}


@router.patch("/{skin_id}/approve", response=SkinResponse, summary="Approve skin")
async def approve_skin(request: HttpRequest, skin_id: str) -> dict:
    """Approve a skin (admin only)."""
    from services.common.authorization import authorize

    store = _get_store()
    await store.ensure_schema()
    await authorize(request, action="skin:approve", resource="skins")

    skin = await store.get(skin_id)
    if not skin:
        raise NotFoundError("skin", skin_id)

    await store.approve(skin_id)
    approved = await store.get(skin_id)

    return _record_to_response(approved)


@router.patch("/{skin_id}/reject", response=SkinResponse, summary="Reject skin")
async def reject_skin(request: HttpRequest, skin_id: str) -> dict:
    """Reject a skin (admin only)."""
    from services.common.authorization import authorize

    store = _get_store()
    await store.ensure_schema()
    await authorize(request, action="skin:reject", resource="skins")

    skin = await store.get(skin_id)
    if not skin:
        raise NotFoundError("skin", skin_id)

    await store.reject(skin_id)
    rejected = await store.get(skin_id)

    return _record_to_response(rejected)