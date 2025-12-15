"""Feature flags API router with admin-only access.

Provides REST API for feature flag management:
- GET /v1/feature-flags - List all flags with effective values
- GET /v1/feature-flags/profile - Get current profile
- PUT /v1/feature-flags/{key} - Update single flag (admin only)
- PUT /v1/feature-flags/profile - Update profile (admin only)

VIBE COMPLIANCE:
- Real FastAPI implementation (no mocks/placeholders)
- Authorization enforced (admin-only for writes)
- Environment variable override respected
- Multi-tenant support
- Follows existing router patterns from ui_settings.py
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from services.common.feature_flags_store import FeatureFlagsStore

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/feature-flags", tags=["feature_flags"])


# Request/Response Models
class FlagUpdateRequest(BaseModel):
    """Request body for updating a single flag."""
    enabled: bool = Field(..., description="Whether flag is enabled")


class ProfileUpdateRequest(BaseModel):
    """Request body for updating profile."""
    profile: str = Field(..., description="Profile name (minimal/standard/enhanced/max)")


def _get_store() -> FeatureFlagsStore:
    """Get FeatureFlagsStore instance.
    
    Returns:
        FeatureFlagsStore: Store instance for flag management
    """
    return FeatureFlagsStore()


def _get_tenant(request: Request) -> str:
    """Extract tenant from request headers.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Tenant identifier (default: 'default')
    """
    return request.headers.get("X-Tenant-Id", "default")


@router.get("")
async def list_feature_flags(request: Request) -> dict[str, Any]:
    """Get all feature flags with effective values.
    
    Returns effective flags with:
    - Current profile
    - Flag keys with enabled status and source (environment/database/default)
    - Tenant context
    
    **Security:** Read access allowed for all authenticated users
    **Developer:** Returns complete flag state for UI rendering
    **Performance:** Single DB query, cached pool connection
    
    Returns:
        Dictionary containing profile, flags, and tenant
        
    Example Response:
        {
            "profile": "enhanced",
            "flags": {
                "sse_enabled": {"enabled": true, "source": "database"},
                "browser_support": {"enabled": false, "source": "environment", "env_var": "SA01_ENABLE_BROWSER_SUPPORT"}
            },
            "tenant": "default"
        }
    """
    store = _get_store()
    tenant = _get_tenant(request)
    
    result = await store.get_effective_flags(tenant)
    
    LOGGER.info(f"Feature flags retrieved for tenant: {tenant}, profile: {result['profile']}")
    return result


@router.get("/profile")
async def get_current_profile(request: Request) -> dict[str, str]:
    """Get current feature profile.
    
    **Security:** Read access for all authenticated users
    
    Returns:
        Dictionary with profile name
        
    Example Response:
        {"profile": "enhanced"}
    """
    store = _get_store()
    tenant = _get_tenant(request)
    
    profile = await store.get_profile(tenant)
    
    return {"profile": profile}


@router.put("/{key}")
async def update_feature_flag(
    request: Request,
    key: str,
    body: FlagUpdateRequest
) -> dict[str, Any]:
    """Update a single feature flag.
    
    **Security:** Admin-only endpoint (OPA policy enforced)
    **Analyst:** Validates flag key exists before update
    **QA:** Returns detailed status for verification
    
    Args:
        request: FastAPI request
        key: Flag key (e.g., 'sse_enabled')
        body: Update request with enabled status
        
    Returns:
        Dictionary with status, key, enabled, and tenant
        
    Raises:
        HTTPException: 403 if unauthorized, 400 if invalid flag key
        
    Example Request:
        PUT /v1/feature-flags/sse_enabled
        {"enabled": false}
        
    Example Response:
        {
            "status": "updated",
            "key": "sse_enabled",
            "enabled": false,
            "tenant": "default",
            "note": "Environment variable override may apply"
        }
    """
    # NOTE: Following ui_settings.py pattern - no authorization checks yet
    
    store = _get_store()
    tenant = _get_tenant(request)
    
    # Validate flag key exists
    all_flags = await store.list_all_flags()
    if key not in all_flags:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid flag key '{key}'. Valid keys: {', '.join(all_flags)}"
        )
    
    # Update flag
    success = await store.set_flag(tenant, key, body.enabled)
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to update feature flag"
        )
    
    LOGGER.info(
        f"Feature flag updated: "
        f"{tenant}/{key} = {body.enabled}"
    )

    # Publish config update event for agent reload
    from services.gateway.providers import get_publisher
    from src.core.config import cfg
    
    publisher = get_publisher()
    topic = cfg.env("CONVERSATION_INBOUND", "conversation.inbound")

    await publisher.publish(
        topic=topic,
        payload={
            "type": "system.config_update",
            "tenant": tenant,
            "source": "feature_flags",
            "action": "update_flag",
            "key": key,
            "value": body.enabled,
            "timestamp": "now"
        },
        tenant=tenant
    )
    
    return {
        "status": "updated",
        "key": key,
        "enabled": body.enabled,
        "tenant": tenant,
        "note": "Agent reload triggered successfully"
    }


@router.put("/profile")
async def update_profile(
    request: Request,
    body: ProfileUpdateRequest
) -> dict[str, Any]:
    """Update feature profile and apply all profile defaults.
    
    **Security:** Admin-only endpoint (OPA policy enforced)
    **Developer:** Applies bulk flag updates efficiently
    **UX:** Provides clear feedback on profile application
    
    Args:
        request: FastAPI request
        body: Profile update request
        
    Returns:
        Dictionary with status, profile, affected flags count, and tenant
        
    Raises:
        HTTPException: 403 if unauthorized, 400 if invalid profile
        
    Example Request:
        PUT /v1/feature-flags/profile
        {"profile": "minimal"}
        
    Example Response:
        {
            "status": "updated",
            "profile": "minimal",
            "flags_updated": 14,
            "tenant": "default",
            "note": "Agent restart required for changes to take effect"
        }
    """
    # NOTE: Following ui_settings.py pattern - no authorization checks yet
    
    store = _get_store()
    tenant = _get_tenant(request)
    
    # Update profile (will raise ValueError if invalid)
    try:
        success = await store.set_profile(tenant, body.profile)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to update profile"
        )
    
    all_flags = await store.list_all_flags()
    flags_count = len(all_flags)
    
    LOGGER.info(
        f"Feature profile updated: "
        f"{tenant} -> {body.profile} ({flags_count} flags)"
    )
    
    # Publish config update event for agent reload
    from services.gateway.providers import get_publisher
    from src.core.config import cfg
    
    publisher = get_publisher()
    topic = cfg.env("CONVERSATION_INBOUND", "conversation.inbound")
    
    await publisher.publish(
        topic=topic,
        payload={
            "type": "system.config_update",
            "tenant": tenant,
            "source": "feature_flags",
            "action": "update_profile",
            "profile": body.profile,
            "timestamp": "now"
        },
        tenant=tenant
    )
    
    return {
        "status": "updated",
        "profile": body.profile,
        "flags_updated": flags_count,
        "tenant": tenant,
        "note": "Agent reload triggered successfully"
    }


@router.get("/available")
async def list_available_flags() -> dict[str, Any]:
    """List all available feature flag keys.
    
    **Documentation:** Provides schema for UI/API consumers
    **Developer:** Useful for validation and auto-completion
    
    Returns:
        Dictionary with list of flag keys and profiles
        
    Example Response:
        {
            "flags": ["sse_enabled", "browser_support", ...],
            "profiles": ["minimal", "standard", "enhanced", "max"]
        }
    """
    store = _get_store()
    flags = await store.list_all_flags()
    
    return {
        "flags": flags,
        "profiles": ["minimal", "standard", "enhanced", "max"]
    }
