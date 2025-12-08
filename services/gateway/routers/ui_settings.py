"""Agent settings endpoints with Vault-based secret management.

Single source of truth:
- Non-sensitive settings → PostgreSQL via AgentSettingsStore
- Secrets/API keys → Vault via UnifiedSecretManager

No Redis secrets, no .env files, no fallbacks.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from python.helpers.settings import get_default_settings
from services.common.agent_settings_store import get_agent_settings_store

router = APIRouter(prefix="/v1/settings", tags=["settings"])
# Legacy compatibility router – exposes the original `/v1/settings_save`
# and `/v1/test_connection` endpoints expected by the UI before the
# refactor. These simply delegate to the canonical handlers above.
legacy_router = APIRouter(prefix="/v1", tags=["settings"])


class SettingsUpdate(BaseModel):
    data: dict


def _get_store():
    """Get AgentSettingsStore instance."""
    return get_agent_settings_store()


@router.get("")
async def get_settings() -> dict:
    """Return agent settings with UI schema."""
    store = _get_store()
    await store.ensure_schema()

    settings = await store.get_settings()
    if not settings:
        settings = get_default_settings()

    # Import here to avoid circular imports
    from python.helpers.settings import convert_out

    ui_data = convert_out(settings)

    if not ui_data.get("sections"):
        raise HTTPException(status_code=500, detail="Settings schema generation failed")
    return ui_data


@router.get("/sections")
async def get_settings_sections() -> dict:
    """Return UI settings sections for frontend."""
    data = await get_settings()
    return {"sections": data.get("sections", [])}


@router.put("/sections")
async def put_settings(body: SettingsUpdate):
    """Save settings from UI."""
    store = _get_store()
    await store.ensure_schema()

    # Import here to avoid circular imports
    from python.helpers.settings import convert_in

    settings = convert_in(body.data)

    await store.set_settings(settings)
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
    """Get single settings field."""
    store = _get_store()
    await store.ensure_schema()
    value = await store.get_field(key)
    return {"key": key, "value": value}


@router.put("/{key}")
async def put_setting_field(key: str, body: dict):
    """Set single settings field."""
    store = _get_store()
    await store.ensure_schema()
    await store.set_field(key, body.get("value"))
    return {"status": "ok"}


@legacy_router.post("/settings_save")
async def legacy_settings_save(body: SettingsUpdate):
    """Backward-compatible alias for `/v1/settings` PUT."""
    return await put_settings(body)


@legacy_router.post("/test_connection")
async def legacy_test_connection(body: TestConnectionRequest):
    """Backward-compatible alias for `/v1/settings/test_connection`."""
    return await test_connection(body)
