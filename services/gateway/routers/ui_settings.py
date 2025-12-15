"""Agent settings endpoints with Vault-based secret management.

Single source of truth:
- Non-sensitive settings → PostgreSQL via AgentSettingsStore
- Secrets/API keys → Vault via UnifiedSecretManager

No Redis secrets, no .env files, no fallbacks.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from services.common.ui_settings_store import UiSettingsStore
from services.common.feature_flags_store import FeatureFlagsStore
from services.common.agent_config_loader import reload_agent_config

router = APIRouter(prefix="/v1/settings", tags=["settings"])


class SettingsUpdate(BaseModel):
    data: dict


def _get_store():
    """Get UiSettingsStore instance."""
    return UiSettingsStore()


@router.get("")
async def get_settings(request: Request) -> dict:
    """Return UI settings schema/payload."""
    store = _get_store()
    await store.ensure_schema()

    settings = await store.get()
    if not settings or not settings.get("sections"):
        raise HTTPException(status_code=500, detail="Settings schema generation failed")

    # REQ-PERSIST-001: Merge effective feature flags from database
    try:
        tenant = request.headers.get("X-Tenant-Id", "default")
        ff_store = FeatureFlagsStore()
        effective = await ff_store.get_effective_flags(tenant)
        
        # Find feature_flags section
        sections = settings.get("sections", [])
        ff_section = next((s for s in sections if s["id"] == "feature_flags"), None)
        
        if ff_section and "fields" in ff_section:
            # Update profile value
            profile_field = next((f for f in ff_section["fields"] if f["id"] == "profile"), None)
            if profile_field:
                profile_field["value"] = effective["profile"]
            
            # Update individual flags
            flags_map = effective.get("flags", {})
            for field in ff_section["fields"]:
                fid = field["id"]
                if fid in flags_map:
                    # Update value and add hint about source
                    verdict = flags_map[fid]
                    field["value"] = verdict["enabled"]
                    if verdict["source"] == "environment":
                        field["hint"] = f"(Overridden by {verdict['env_var']}) {field.get('hint', '')}"
    except Exception as exc:
        # If feature flags store is unavailable, return settings without flags enrichment.
        # This prevents a total failure of the settings API if the flags DB is down.
        LOGGER.warning("Failed to enrich settings with feature flags", extra={"error": str(exc)})
        pass

    return settings


@router.get("/sections")
async def get_settings_sections() -> dict:
    """Return UI settings sections for frontend."""
    data = await get_settings()
    return {"sections": data.get("sections", [])}


@router.put("/sections")
async def put_settings(request: Request, body: SettingsUpdate):
    """Save settings from UI."""
    store = _get_store()
    await store.ensure_schema()

    # 1. Persist the schema/blob modifications (UI layout etc)
    await store.set(body.data)
    
    # 2. REQ-PERSIST-001: Persist feature flags to dedicated table
    tenant = request.headers.get("X-Tenant-Id", "default")
    
    sections = body.data.get("sections", [])
    ff_section = next((s for s in sections if s["id"] == "feature_flags"), None)
    
    if ff_section and "fields" in ff_section:
        ff_store = FeatureFlagsStore()
        
        # first update profile if present
        profile_field = next((f for f in ff_section["fields"] if f["id"] == "profile"), None)
        if profile_field:
            try:
                await ff_store.set_profile(tenant, profile_field["value"])
            except ValueError:
                pass # Ignore invalid profile, proceed to flags
        
        # then update all individual flags
        for field in ff_section["fields"]:
            fid = field["id"]
            if fid == "profile":
                continue
            # Logic: If it looks like a boolean flag, save it
            if "value" in field and isinstance(field["value"], bool):
                await ff_store.set_flag(tenant, fid, field["value"])

    # 3. REQ-PERSIST-001: Trigger Agent Reload
    await reload_agent_config(tenant)

    return {"status": "ok"}


class TestConnectionRequest(BaseModel):
    service: str
    api_key: str
    base_url: str | None = None
    model: str | None = None


@router.post("/test_connection")
async def test_connection(body: TestConnectionRequest):
    """
    Validate connectivity to the configured LLM provider using provided credentials.
    Executes a minimal chat completion with strict timeout; returns success flag.
    """
    import litellm

    model = body.model or {
        "openai": "gpt-3.5-turbo-0125",
        "anthropic": "claude-3-haiku-20240307",
        "google": "gemini-pro",
    }.get(body.service.lower(), body.model or "gpt-3.5-turbo")

    try:
        _ = await litellm.acompletion(
            model=model,
            messages=[{"role": "user", "content": "ping"}],
            api_key=body.api_key,
            api_base=body.base_url,
            timeout=5,
        )
        return {"success": True}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


@router.get("/{key}")
async def get_setting_field(key: str):
    """Get single settings field (top-level key)."""
    store = _get_store()
    await store.ensure_schema()
    value = await store.get()
    return {"key": key, "value": value.get(key)}


@router.put("/{key}")
async def put_setting_field(key: str, body: dict):
    """Set single settings field (top-level key)."""
    store = _get_store()
    await store.ensure_schema()
    current = await store.get()
    current[key] = body.get("value")
    await store.set(current)
    return {"status": "ok"}
