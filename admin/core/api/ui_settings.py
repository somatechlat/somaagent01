"""UI Settings API Router.

Migrated from: services/gateway/routers/ui_settings.py
Pure Django Ninja with Django ORM and signals.

VIBE COMPLIANT - Django patterns, observable, verifiable.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from django.conf import settings
from django.dispatch import Signal
from django.http import HttpRequest
from ninja import Router
from pydantic import BaseModel

from admin.common.exceptions import ServiceError

router = Router(tags=["settings"])
logger = logging.getLogger(__name__)

# Django signals for observability
settings_updated = Signal()  # args: tenant, section_id
agent_reload_requested = Signal()  # args: tenant


class SettingsUpdate(BaseModel):
    """Settings update request."""
    
    data: dict


class TestConnectionRequest(BaseModel):
    """Connection test request."""
    
    service: str
    api_key: str
    base_url: Optional[str] = None
    model: Optional[str] = None


def _get_store():
    """Get UiSettingsStore instance."""
    from services.common.ui_settings_store import UiSettingsStore
    return UiSettingsStore()


def _get_tenant(request: HttpRequest) -> str:
    """Extract tenant from request headers."""
    return request.headers.get("X-Tenant-Id", "default")


@router.get("", summary="Get UI settings")
async def get_settings(request: HttpRequest) -> dict:
    """Return UI settings schema/payload with enriched feature flags."""
    store = _get_store()
    await store.ensure_schema()
    
    data = await store.get()
    if not data or not data.get("sections"):
        raise ServiceError("Settings schema generation failed")
    
    # Enrich with feature flags
    try:
        from services.common.feature_flags_store import FeatureFlagsStore
        
        tenant = _get_tenant(request)
        ff_store = FeatureFlagsStore()
        effective = await ff_store.get_effective_flags(tenant)
        
        sections = data.get("sections", [])
        ff_section = next((s for s in sections if s["id"] == "feature_flags"), None)
        
        if ff_section and "fields" in ff_section:
            # Update profile
            profile_field = next((f for f in ff_section["fields"] if f["id"] == "profile"), None)
            if profile_field:
                profile_field["value"] = effective["profile"]
            
            # Update flags
            flags_map = effective.get("flags", {})
            for field in ff_section["fields"]:
                fid = field["id"]
                if fid in flags_map:
                    verdict = flags_map[fid]
                    field["value"] = verdict["enabled"]
                    if verdict["source"] == "environment":
                        field["hint"] = f"(Overridden by {verdict['env_var']}) {field.get('hint', '')}"
    except Exception as exc:
        logger.warning("Failed to enrich settings with feature flags", extra={"error": str(exc)})
    
    return data


@router.get("/sections", summary="Get settings sections")
async def get_settings_sections(request: HttpRequest) -> dict:
    """Return UI settings sections for frontend."""
    data = await get_settings(request)
    return {"sections": data.get("sections", [])}


@router.put("/sections", summary="Save settings")
async def put_settings(request: HttpRequest, body: SettingsUpdate) -> dict:
    """Save settings from UI.
    
    Persists settings, updates feature flags, and triggers agent reload.
    """
    from services.common.feature_flags_store import FeatureFlagsStore
    from services.common.agent_config_loader import reload_agent_config
    
    store = _get_store()
    await store.ensure_schema()
    
    # 1. Persist settings
    await store.set(body.data)
    
    # 2. Persist feature flags
    tenant = _get_tenant(request)
    sections = body.data.get("sections", [])
    ff_section = next((s for s in sections if s["id"] == "feature_flags"), None)
    
    if ff_section and "fields" in ff_section:
        ff_store = FeatureFlagsStore()
        
        # Update profile
        profile_field = next((f for f in ff_section["fields"] if f["id"] == "profile"), None)
        if profile_field:
            try:
                await ff_store.set_profile(tenant, profile_field["value"])
            except ValueError:
                pass
        
        # Update flags
        for field in ff_section["fields"]:
            fid = field["id"]
            if fid == "profile":
                continue
            if "value" in field and isinstance(field["value"], bool):
                await ff_store.set_flag(tenant, fid, field["value"])
    
    # 3. Trigger agent reload with Django signal
    settings_updated.send(sender=None, tenant=tenant, section_id="feature_flags")
    await reload_agent_config(tenant)
    agent_reload_requested.send(sender=None, tenant=tenant)
    
    return {"status": "ok"}


@router.post("/test_connection", summary="Test LLM connection")
async def test_connection(body: TestConnectionRequest) -> dict:
    """Validate connectivity to LLM provider."""
    import litellm
    
    # Model defaults from Django settings
    default_models = getattr(settings, "LLM_DEFAULT_MODELS", {
        "openai": "gpt-3.5-turbo-0125",
        "anthropic": "claude-3-haiku-20240307",
        "google": "gemini-pro",
    })
    
    model = body.model or default_models.get(body.service.lower(), "gpt-3.5-turbo")
    
    try:
        await litellm.acompletion(
            model=model,
            messages=[{"role": "user", "content": "ping"}],
            api_key=body.api_key,
            api_base=body.base_url,
            timeout=5,
        )
        return {"success": True}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


@router.get("/{key}", summary="Get single setting")
async def get_setting_field(key: str) -> dict:
    """Get single settings field (top-level key)."""
    store = _get_store()
    await store.ensure_schema()
    value = await store.get()
    return {"key": key, "value": value.get(key)}


@router.put("/{key}", summary="Set single setting")
async def put_setting_field(key: str, body: dict) -> dict:
    """Set single settings field (top-level key)."""
    store = _get_store()
    await store.ensure_schema()
    current = await store.get()
    current[key] = body.get("value")
    await store.set(current)
    return {"status": "ok"}
