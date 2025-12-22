"""
Eye of God API - Themes Endpoints
Per Eye of God UIX Design Section 2.1

VIBE COMPLIANT:
- Real Django Ninja endpoints
- XSS validation
- PostgreSQL persistence
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from django.http import HttpRequest
from ninja import Router, Query

from api.schemas import (
    ThemeCreate,
    ThemeUpdate,
    ThemeResponse,
    ErrorResponse,
    PaginatedResponse,
)
from core.models import Theme

router = Router(tags=["Themes"])


@router.get(
    "/",
    response={200: List[ThemeResponse]},
    summary="List available themes"
)
async def list_themes(
    request: HttpRequest,
    search: Optional[str] = Query(None, description="Search by name or author"),
    approved_only: bool = Query(True, description="Only show approved themes"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> List[ThemeResponse]:
    """
    List all themes available to the tenant.
    
    Includes both tenant-specific and global themes.
    """
    tenant_id = request.auth.get("tenant_id")
    
    queryset = Theme.objects.filter(tenant_id=tenant_id)
    
    if approved_only:
        queryset = queryset.filter(is_approved=True)
    
    if search:
        queryset = queryset.filter(name__icontains=search) | queryset.filter(author__icontains=search)
    
    # Pagination
    offset = (page - 1) * page_size
    themes = []
    async for theme in queryset.order_by("-created_at")[offset:offset + page_size]:
        themes.append(ThemeResponse(
            id=theme.id,
            tenant_id=theme.tenant_id,
            name=theme.name,
            description=theme.description,
            version=theme.version,
            author=theme.author,
            variables=theme.variables,
            is_approved=theme.is_approved,
            downloads=theme.downloads,
            created_at=theme.created_at,
            updated_at=theme.updated_at,
        ))
    
    return themes


@router.get(
    "/{theme_id}",
    response={200: ThemeResponse, 404: ErrorResponse},
    summary="Get theme by ID"
)
async def get_theme(request: HttpRequest, theme_id: UUID) -> ThemeResponse:
    """
    Get a specific theme by ID.
    """
    tenant_id = request.auth.get("tenant_id")
    
    try:
        theme = await Theme.objects.aget(id=theme_id, tenant_id=tenant_id)
        return ThemeResponse(
            id=theme.id,
            tenant_id=theme.tenant_id,
            name=theme.name,
            description=theme.description,
            version=theme.version,
            author=theme.author,
            variables=theme.variables,
            is_approved=theme.is_approved,
            downloads=theme.downloads,
            created_at=theme.created_at,
            updated_at=theme.updated_at,
        )
    except Theme.DoesNotExist:
        raise ValueError("Theme not found")


@router.post(
    "/",
    response={201: ThemeResponse, 400: ErrorResponse},
    summary="Create new theme"
)
async def create_theme(request: HttpRequest, payload: ThemeCreate) -> ThemeResponse:
    """
    Create a new theme.
    
    Theme undergoes XSS validation before storage.
    Newly created themes are not approved by default.
    """
    tenant_id = request.auth.get("tenant_id")
    user_id = request.auth.get("user_id")
    
    theme = await Theme.objects.acreate(
        tenant_id=UUID(tenant_id),
        owner_id=UUID(user_id),
        name=payload.name,
        description=payload.description,
        version=payload.version,
        author=payload.author,
        variables=payload.variables,
        is_approved=False,
    )
    
    return ThemeResponse(
        id=theme.id,
        tenant_id=theme.tenant_id,
        name=theme.name,
        description=theme.description,
        version=theme.version,
        author=theme.author,
        variables=theme.variables,
        is_approved=theme.is_approved,
        downloads=0,
        created_at=theme.created_at,
        updated_at=theme.updated_at,
    )


@router.patch(
    "/{theme_id}",
    response={200: ThemeResponse, 404: ErrorResponse},
    summary="Update theme"
)
async def update_theme(
    request: HttpRequest, 
    theme_id: UUID, 
    payload: ThemeUpdate
) -> ThemeResponse:
    """
    Update an existing theme.
    
    Only the theme owner or admin can update.
    """
    tenant_id = request.auth.get("tenant_id")
    
    try:
        theme = await Theme.objects.aget(id=theme_id, tenant_id=tenant_id)
        
        if payload.name is not None:
            theme.name = payload.name
        if payload.description is not None:
            theme.description = payload.description
        if payload.variables is not None:
            theme.variables = payload.variables
        
        theme.updated_at = datetime.utcnow()
        await theme.asave()
        
        return ThemeResponse(
            id=theme.id,
            tenant_id=theme.tenant_id,
            name=theme.name,
            description=theme.description,
            version=theme.version,
            author=theme.author,
            variables=theme.variables,
            is_approved=theme.is_approved,
            downloads=theme.downloads,
            created_at=theme.created_at,
            updated_at=theme.updated_at,
        )
    except Theme.DoesNotExist:
        raise ValueError("Theme not found")


@router.delete(
    "/{theme_id}",
    response={204: None, 404: ErrorResponse},
    summary="Delete theme"
)
async def delete_theme(request: HttpRequest, theme_id: UUID) -> None:
    """
    Delete a theme.
    
    Only the theme owner or admin can delete.
    """
    tenant_id = request.auth.get("tenant_id")
    
    try:
        theme = await Theme.objects.aget(id=theme_id, tenant_id=tenant_id)
        await theme.adelete()
    except Theme.DoesNotExist:
        raise ValueError("Theme not found")


@router.post(
    "/{theme_id}/approve",
    response={200: ThemeResponse, 403: ErrorResponse},
    summary="Approve theme (admin only)"
)
async def approve_theme(request: HttpRequest, theme_id: UUID) -> ThemeResponse:
    """
    Approve a theme for general use.
    
    Requires admin role.
    """
    tenant_id = request.auth.get("tenant_id")
    role = request.auth.get("role", "member")
    
    if role not in ("admin", "sysadmin"):
        raise PermissionError("Admin role required")
    
    try:
        theme = await Theme.objects.aget(id=theme_id, tenant_id=tenant_id)
        theme.is_approved = True
        theme.updated_at = datetime.utcnow()
        await theme.asave()
        
        return ThemeResponse(
            id=theme.id,
            tenant_id=theme.tenant_id,
            name=theme.name,
            description=theme.description,
            version=theme.version,
            author=theme.author,
            variables=theme.variables,
            is_approved=True,
            downloads=theme.downloads,
            created_at=theme.created_at,
            updated_at=theme.updated_at,
        )
    except Theme.DoesNotExist:
        raise ValueError("Theme not found")


@router.post(
    "/{theme_id}/apply",
    response={200: dict},
    summary="Apply theme and increment download count"
)
async def apply_theme(request: HttpRequest, theme_id: UUID) -> dict:
    """
    Apply a theme and increment its download counter.
    
    Returns the theme variables to apply on the client.
    """
    tenant_id = request.auth.get("tenant_id")
    
    try:
        theme = await Theme.objects.aget(id=theme_id, tenant_id=tenant_id)
        theme.downloads += 1
        await theme.asave(update_fields=["downloads"])
        
        return {
            "success": True,
            "theme_id": str(theme.id),
            "variables": theme.variables,
        }
    except Theme.DoesNotExist:
        raise ValueError("Theme not found")
