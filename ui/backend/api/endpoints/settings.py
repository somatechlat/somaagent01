"""
Eye of God API - Settings Endpoints
Per Eye of God UIX Design Section 2.1

VIBE COMPLIANT:
- Real Django Ninja endpoints
- PostgreSQL persistence
- Version control for optimistic locking
"""

from datetime import datetime
from typing import List
from uuid import UUID

from django.http import HttpRequest
from ninja import Router

from api.schemas import (
    SettingsTab,
    SettingsCreate,
    SettingsUpdate,
    SettingsResponse,
    ErrorResponse,
)
from core.models import Settings

router = Router(tags=["Settings"])


@router.get(
    "/",
    response={200: List[SettingsResponse], 401: ErrorResponse},
    summary="List all settings tabs"
)
async def list_settings(request: HttpRequest) -> List[SettingsResponse]:
    """
    Get all settings for the current tenant.
    
    Returns settings grouped by tab (agent, external, connectivity, system).
    """
    tenant_id = request.auth.get("tenant_id")
    
    settings_list = []
    async for setting in Settings.objects.filter(tenant_id=tenant_id):
        settings_list.append(SettingsResponse(
            tab=setting.tab,
            data=setting.data,
            updated_at=setting.updated_at,
            version=setting.version,
        ))
    
    return settings_list


@router.get(
    "/{tab}",
    response={200: SettingsResponse, 404: ErrorResponse},
    summary="Get settings by tab"
)
async def get_settings(request: HttpRequest, tab: SettingsTab) -> SettingsResponse:
    """
    Get settings for a specific tab.
    
    Args:
        tab: Settings tab identifier (agent, external, connectivity, system)
    """
    tenant_id = request.auth.get("tenant_id")
    
    try:
        setting = await Settings.objects.aget(tenant_id=tenant_id, tab=tab.value)
        return SettingsResponse(
            tab=setting.tab,
            data=setting.data,
            updated_at=setting.updated_at,
            version=setting.version,
        )
    except Settings.DoesNotExist:
        # Return empty settings with defaults
        return SettingsResponse(
            tab=tab,
            data={},
            updated_at=datetime.utcnow(),
            version=1,
        )


@router.put(
    "/{tab}",
    response={200: SettingsResponse, 409: ErrorResponse},
    summary="Update settings by tab"
)
async def update_settings(
    request: HttpRequest, 
    tab: SettingsTab, 
    payload: SettingsUpdate
) -> SettingsResponse:
    """
    Update settings for a specific tab.
    
    Uses optimistic locking via version field to prevent concurrent overwrites.
    
    Args:
        tab: Settings tab identifier
        payload: New settings data with version
    """
    tenant_id = request.auth.get("tenant_id")
    user_id = request.auth.get("user_id")
    
    try:
        setting = await Settings.objects.aget(tenant_id=tenant_id, tab=tab.value)
        
        # Optimistic locking check
        if setting.version != payload.version:
            raise ValueError("Version conflict - settings were modified")
        
        setting.data = payload.data
        setting.version += 1
        setting.updated_at = datetime.utcnow()
        await setting.asave()
        
    except Settings.DoesNotExist:
        # Create new settings
        setting = await Settings.objects.acreate(
            tenant_id=UUID(tenant_id),
            created_by_id=UUID(user_id),
            tab=tab.value,
            data=payload.data,
            version=1,
        )
    
    return SettingsResponse(
        tab=setting.tab,
        data=setting.data,
        updated_at=setting.updated_at,
        version=setting.version,
    )


@router.post(
    "/{tab}/reset",
    response={200: SettingsResponse},
    summary="Reset settings to defaults"
)
async def reset_settings(request: HttpRequest, tab: SettingsTab) -> SettingsResponse:
    """
    Reset settings for a tab to their default values.
    
    Args:
        tab: Settings tab identifier
    """
    tenant_id = request.auth.get("tenant_id")
    
    # Default settings per tab
    defaults = {
        SettingsTab.AGENT: {
            "chat_provider": "openai",
            "chat_model": "gpt-4",
            "recall_interval": 30,
            "max_memories": 100,
        },
        SettingsTab.EXTERNAL: {},
        SettingsTab.CONNECTIVITY: {
            "api_base_url": "/api/v2",
            "ws_url": "/ws/v2/events",
        },
        SettingsTab.SYSTEM: {
            "log_level": "INFO",
        },
    }
    
    try:
        setting = await Settings.objects.aget(tenant_id=tenant_id, tab=tab.value)
        setting.data = defaults.get(tab, {})
        setting.version += 1
        setting.updated_at = datetime.utcnow()
        await setting.asave()
    except Settings.DoesNotExist:
        setting = await Settings.objects.acreate(
            tenant_id=UUID(tenant_id),
            tab=tab.value,
            data=defaults.get(tab, {}),
            version=1,
        )
    
    return SettingsResponse(
        tab=setting.tab,
        data=setting.data,
        updated_at=setting.updated_at,
        version=setting.version,
    )
