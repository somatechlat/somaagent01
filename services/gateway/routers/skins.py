"""AgentSkin theme endpoints per AgentSkin UIX Task 8.

Implements TR-AGS-004.1 - TR-AGS-004.6:
- GET /v1/skins - List themes for tenant (approved only for non-admin)
- GET /v1/skins/{id} - Get theme details
- POST /v1/skins - Upload new theme (admin only)
- DELETE /v1/skins/{id} - Delete theme (admin only)
- PATCH /v1/skins/{id}/approve - Approve theme (admin only)

Security:
- XSS validation rejects url(), <script>, javascript: patterns (SEC-AGS-002)
- Admin operations gated by OPA policy (SEC-AGS-001)
- All queries scoped by tenant_id (SEC-AGS-003)
"""

from __future__ import annotations

import re
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from services.common.authorization import authorize
from services.common.skins_store import SkinRecord, SkinsStore, validate_no_xss

router = APIRouter(prefix="/v1/skins", tags=["skins"])
STORE = SkinsStore()


# =============================================================================
# Request/Response Models
# =============================================================================

class SkinCreateRequest(BaseModel):
    """Request body for creating a skin (TR-AGS-004.3)."""
    
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    author: Optional[str] = Field(None, max_length=100)
    variables: Dict[str, str] = Field(default_factory=dict)
    changelog: List[Dict[str, Any]] = Field(default_factory=list)
    
    @field_validator("variables")
    @classmethod
    def validate_variables_no_xss(cls, v: Dict[str, str]) -> Dict[str, str]:
        """Validate no XSS patterns in CSS variables (SEC-AGS-002)."""
        try:
            validate_no_xss(v)
        except ValueError as e:
            raise ValueError(str(e))
        return v
    
    @field_validator("version")
    @classmethod
    def validate_semver(cls, v: str) -> str:
        """Validate semantic versioning format."""
        if not re.match(r"^\d+\.\d+\.\d+$", v):
            raise ValueError("Version must be in semver format (X.Y.Z)")
        return v


class SkinUpdateRequest(BaseModel):
    """Request body for updating a skin."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    version: Optional[str] = Field(None, pattern=r"^\d+\.\d+\.\d+$")
    author: Optional[str] = Field(None, max_length=100)
    variables: Optional[Dict[str, str]] = None
    changelog: Optional[List[Dict[str, Any]]] = None
    
    @field_validator("variables")
    @classmethod
    def validate_variables_no_xss(cls, v: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:
        """Validate no XSS patterns in CSS variables."""
        if v is not None:
            try:
                validate_no_xss(v)
            except ValueError as e:
                raise ValueError(str(e))
        return v


class SkinResponse(BaseModel):
    """Response model for a single skin."""
    
    id: str
    tenant_id: str
    name: str
    description: str
    version: str
    author: str
    variables: Dict[str, str]
    changelog: List[Dict[str, Any]]
    is_approved: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SkinListResponse(BaseModel):
    """Response model for listing skins."""
    
    skins: List[SkinResponse]
    count: int


# =============================================================================
# Helper Functions
# =============================================================================

def _record_to_response(rec: SkinRecord) -> SkinResponse:
    """Convert SkinRecord to SkinResponse."""
    return SkinResponse(
        id=rec.skin_id,
        tenant_id=rec.tenant_id,
        name=rec.name,
        description=rec.description,
        version=rec.version,
        author=rec.author,
        variables=rec.variables,
        changelog=rec.changelog,
        is_approved=rec.is_approved,
        created_at=rec.created_at.isoformat() if rec.created_at else None,
        updated_at=rec.updated_at.isoformat() if rec.updated_at else None,
    )


async def _get_tenant_id(request: Request) -> str:
    """Extract tenant ID from request headers."""
    tenant_id = request.headers.get("X-Tenant-Id")
    if not tenant_id:
        # Default tenant for development
        tenant_id = "00000000-0000-0000-0000-000000000000"
    return tenant_id


async def _is_admin(request: Request) -> bool:
    """Check if request is from an admin user.
    
    Uses OPA policy evaluation via authorize().
    Returns True if admin, False otherwise.
    """
    try:
        await authorize(request, action="skin:upload", resource="skins")
        return True
    except HTTPException:
        return False


# =============================================================================
# Endpoints
# =============================================================================

@router.get("", response_model=SkinListResponse)
async def list_skins(request: Request) -> SkinListResponse:
    """List available skins for the tenant (TR-AGS-004.1).
    
    Non-admin users only see approved skins.
    Admin users see all skins including unapproved.
    
    Tenant isolation enforced via X-Tenant-Id header (SEC-AGS-003).
    """
    await STORE.ensure_schema()
    
    tenant_id = await _get_tenant_id(request)
    is_admin = await _is_admin(request)
    
    skins = await STORE.list(tenant_id=tenant_id, include_unapproved=is_admin)
    
    return SkinListResponse(
        skins=[_record_to_response(s) for s in skins],
        count=len(skins),
    )


@router.get("/{skin_id}", response_model=SkinResponse)
async def get_skin(request: Request, skin_id: str) -> SkinResponse:
    """Get a single skin by ID (TR-AGS-004.2).
    
    Returns 404 if skin not found or not accessible to tenant.
    """
    await STORE.ensure_schema()
    
    tenant_id = await _get_tenant_id(request)
    is_admin = await _is_admin(request)
    
    skin = await STORE.get(skin_id)
    if not skin:
        raise HTTPException(status_code=404, detail="skin_not_found")
    
    # Tenant isolation check (SEC-AGS-003)
    global_tenant = "00000000-0000-0000-0000-000000000000"
    if skin.tenant_id != tenant_id and skin.tenant_id != global_tenant:
        raise HTTPException(status_code=404, detail="skin_not_found")
    
    # Non-admin can only see approved skins
    if not is_admin and not skin.is_approved:
        raise HTTPException(status_code=404, detail="skin_not_found")
    
    return _record_to_response(skin)


@router.post("", response_model=SkinResponse, status_code=201)
async def create_skin(request: Request, payload: SkinCreateRequest) -> SkinResponse:
    """Upload a new skin (TR-AGS-004.3).
    
    Admin only - requires skin:upload permission (SEC-AGS-001).
    Validates JSON schema and rejects XSS patterns (SEC-AGS-002).
    """
    await STORE.ensure_schema()
    
    # Admin authorization via OPA
    auth = await authorize(request, action="skin:upload", resource="skins")
    tenant_id = auth.get("tenant", await _get_tenant_id(request))
    
    # Check for duplicate name within tenant
    existing = await STORE.get_by_name(tenant_id, payload.name)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Skin '{payload.name}' already exists for this tenant"
        )
    
    # Create skin record
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
        is_approved=False,  # New skins start unapproved
    )
    
    try:
        await STORE.create(record)
    except ValueError as e:
        # XSS validation error
        raise HTTPException(status_code=400, detail=str(e))
    
    # Fetch the created record to get timestamps
    created = await STORE.get(skin_id)
    if not created:
        raise HTTPException(status_code=500, detail="Failed to create skin")
    
    return _record_to_response(created)


@router.put("/{skin_id}", response_model=SkinResponse)
async def update_skin(
    request: Request,
    skin_id: str,
    payload: SkinUpdateRequest,
) -> SkinResponse:
    """Update an existing skin (admin only).
    
    Validates XSS patterns in variables (SEC-AGS-002).
    """
    await STORE.ensure_schema()
    
    # Admin authorization via OPA
    await authorize(request, action="skin:update", resource="skins")
    tenant_id = await _get_tenant_id(request)
    
    # Verify skin exists and belongs to tenant
    skin = await STORE.get(skin_id)
    if not skin:
        raise HTTPException(status_code=404, detail="skin_not_found")
    
    global_tenant = "00000000-0000-0000-0000-000000000000"
    if skin.tenant_id != tenant_id and skin.tenant_id != global_tenant:
        raise HTTPException(status_code=404, detail="skin_not_found")
    
    # Build updates dict from non-None fields
    updates = {}
    if payload.name is not None:
        updates["name"] = payload.name
    if payload.description is not None:
        updates["description"] = payload.description
    if payload.version is not None:
        updates["version"] = payload.version
    if payload.author is not None:
        updates["author"] = payload.author
    if payload.variables is not None:
        updates["variables"] = payload.variables
    if payload.changelog is not None:
        updates["changelog"] = payload.changelog
    
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    try:
        success = await STORE.update(skin_id, updates)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not success:
        raise HTTPException(status_code=404, detail="skin_not_found")
    
    updated = await STORE.get(skin_id)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to retrieve updated skin")
    
    return _record_to_response(updated)


@router.delete("/{skin_id}", status_code=200)
async def delete_skin(request: Request, skin_id: str) -> None:
    """Delete a skin (TR-AGS-004.4).
    
    Admin only - requires skin:delete permission (SEC-AGS-001).
    """
    await STORE.ensure_schema()
    
    # Admin authorization via OPA
    await authorize(request, action="skin:delete", resource="skins")
    tenant_id = await _get_tenant_id(request)
    
    # Verify skin exists and belongs to tenant
    skin = await STORE.get(skin_id)
    if not skin:
        raise HTTPException(status_code=404, detail="skin_not_found")
    
    global_tenant = "00000000-0000-0000-0000-000000000000"
    if skin.tenant_id != tenant_id and skin.tenant_id != global_tenant:
        raise HTTPException(status_code=404, detail="skin_not_found")
    
    success = await STORE.delete(skin_id)
    if not success:
        raise HTTPException(status_code=404, detail="skin_not_found")


@router.patch("/{skin_id}/approve", response_model=SkinResponse)
async def approve_skin(request: Request, skin_id: str) -> SkinResponse:
    """Approve a skin (TR-AGS-004.5).
    
    Admin only - requires skin:approve permission (SEC-AGS-001).
    Makes the skin visible to all users in the tenant.
    """
    await STORE.ensure_schema()
    
    # Admin authorization via OPA
    await authorize(request, action="skin:approve", resource="skins")
    tenant_id = await _get_tenant_id(request)
    
    # Verify skin exists and belongs to tenant
    skin = await STORE.get(skin_id)
    if not skin:
        raise HTTPException(status_code=404, detail="skin_not_found")
    
    global_tenant = "00000000-0000-0000-0000-000000000000"
    if skin.tenant_id != tenant_id and skin.tenant_id != global_tenant:
        raise HTTPException(status_code=404, detail="skin_not_found")
    
    success = await STORE.approve(skin_id)
    if not success:
        raise HTTPException(status_code=404, detail="skin_not_found")
    
    approved = await STORE.get(skin_id)
    if not approved:
        raise HTTPException(status_code=500, detail="Failed to retrieve approved skin")
    
    return _record_to_response(approved)


@router.patch("/{skin_id}/reject", response_model=SkinResponse)
async def reject_skin(request: Request, skin_id: str) -> SkinResponse:
    """Reject a skin (set is_approved = FALSE).
    
    Admin only - requires skin:reject permission (SEC-AGS-001).
    Hides the skin from non-admin users.
    """
    await STORE.ensure_schema()
    
    # Admin authorization via OPA
    await authorize(request, action="skin:reject", resource="skins")
    tenant_id = await _get_tenant_id(request)
    
    # Verify skin exists and belongs to tenant
    skin = await STORE.get(skin_id)
    if not skin:
        raise HTTPException(status_code=404, detail="skin_not_found")
    
    global_tenant = "00000000-0000-0000-0000-000000000000"
    if skin.tenant_id != tenant_id and skin.tenant_id != global_tenant:
        raise HTTPException(status_code=404, detail="skin_not_found")
    
    success = await STORE.reject(skin_id)
    if not success:
        raise HTTPException(status_code=404, detail="skin_not_found")
    
    rejected = await STORE.get(skin_id)
    if not rejected:
        raise HTTPException(status_code=500, detail="Failed to retrieve rejected skin")
    
    return _record_to_response(rejected)
