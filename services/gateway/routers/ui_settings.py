"""Agent settings endpoints with Vault-based secret management.

Single source of truth:
- Non-sensitive settings → PostgreSQL via AgentSettingsStore
- Secrets/API keys → Vault via UnifiedSecretManager

No Redis secrets, no .env files, no fallbacks.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.common.ui_settings_store import UiSettingsStore

router = APIRouter(prefix="/v1/settings", tags=["settings"])


class SettingsUpdate(BaseModel):
    data: dict


def _get_store():
    """Get UiSettingsStore instance."""
    return UiSettingsStore()


@router.get("")
async def get_settings() -> dict:
    """Return UI settings schema/payload."""
    store = _get_store()
    await store.ensure_schema()

    settings = await store.get_settings()
    if not settings or not settings.get("sections"):
        raise HTTPException(status_code=500, detail="Settings schema generation failed")
    return settings


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

    await store.set_settings(body.data)
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
    value = await store.get_settings()
    return {"key": key, "value": value.get(key)}


@router.put("/{key}")
async def put_setting_field(key: str, body: dict):
    """Set single settings field (top-level key)."""
    store = _get_store()
    await store.ensure_schema()
    current = await store.get_settings()
    current[key] = body.get("value")
    await store.set_settings(current)
    return {"status": "ok"}
