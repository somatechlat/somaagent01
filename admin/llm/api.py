"""LLM Models / Providers / Presets / Slots API.

Real Django ORM-backed LLMModelConfig management for C5 (MD-01…MD-06).
- Provider registry presets (OpenAI, Anthropic, Google, Groq, Ollama, custom)
- LLMModelConfig CRUD
- Chat / Utility / Embedding slot bindings (Capsule or tenant defaults)
- Named model presets
- Live connection test via LiteLLM
- Model setup gate status

API keys are never returned. Secrets live in Vault via admin.secrets / UnifiedSecretManager.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Literal, Optional

from ninja import Router, Schema
from ninja.errors import HttpError

from admin.common.auth import AuthBearer
from admin.core.models.core import AgentSetting, Capsule
from services.common.authorization import authorize, authorize_sync

logger = logging.getLogger(__name__)
router = Router(tags=["llm"])

# Tenant-default settings namespace (agent_id for AgentSetting rows)
DEFAULTS_AGENT_ID = "default"

# Known provider registry (UI presets). Custom OpenAI-compatible is free-form.
# Base URLs are vendor *protocol* constants from admin.core.helpers.vendor_api_bases
# — the effective base an operator calls is LLMModelConfig.api_base (or the
# preset shown here as a starting point), never a host invented in this file.
from admin.core.helpers.vendor_api_bases import (
    ANTHROPIC_API_BASE,
    GOOGLE_GENERATIVE_LANGUAGE_API_BASE,
    GROQ_API_BASE,
    OPENAI_API_BASE,
)

PROVIDER_PRESETS: dict[str, dict[str, str]] = {
    "openai": {
        "label": "OpenAI",
        "default_base_url": OPENAI_API_BASE,
        "default_model": "gpt-4o-mini",
    },
    "anthropic": {
        "label": "Anthropic",
        "default_base_url": ANTHROPIC_API_BASE,
        "default_model": "claude-3-5-haiku-latest",
    },
    "google": {
        "label": "Google",
        "default_base_url": GOOGLE_GENERATIVE_LANGUAGE_API_BASE,
        "default_model": "gemini-2.0-flash",
    },
    "groq": {
        "label": "Groq",
        "default_base_url": GROQ_API_BASE,
        "default_model": "openai/gpt-oss-120b",
    },
    "ollama": {
        "label": "Ollama",
        # Ollama is a deployment endpoint, not a vendor cloud. The operator
        # names it (LLMModelConfig.api_base / InfrastructureConfig); there is
        # no local-install default to fall back to.
        "default_base_url": "",
        "default_model": "llama3.1",
    },
    "custom": {
        "label": "Custom (OpenAI-compatible)",
        "default_base_url": "",
        "default_model": "",
    },
}

# Default LiteLLM model prefixes used for connection tests per provider
_TEST_MODEL_FALLBACK = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-haiku-latest",
    "google": "gemini-2.0-flash",
    "groq": "openai/gpt-oss-20b",
    "ollama": "llama3.1",
    "custom": "",
}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ProviderOut(Schema):
    """Provider registry row."""

    id: str
    label: str
    enabled: bool
    base_url: str
    model_name: str
    is_custom: bool
    has_api_key: bool


class ProviderUpdate(Schema):
    """Provider enable / base URL / default model name."""

    enabled: Optional[bool] = None
    base_url: Optional[str] = None
    model_name: Optional[str] = None
    label: Optional[str] = None


class ModelIn(Schema):
    """LLMModelConfig create payload."""

    name: str
    display_name: str = ""
    model_type: Literal["chat", "embedding"] = "chat"
    provider: str
    api_base: str = ""
    capabilities: list[str] = []
    priority: int = 50
    cost_tier: Literal["free", "low", "standard", "premium"] = "standard"
    domains: list[str] = []
    ctx_length: int = 0
    limit_requests: int = 0
    limit_input: int = 0
    limit_output: int = 0
    vision: bool = False
    kwargs: dict[str, Any] = {}
    is_active: bool = True


class ModelPatch(Schema):
    """LLMModelConfig partial update. API keys are never accepted here."""

    name: Optional[str] = None
    display_name: Optional[str] = None
    model_type: Optional[Literal["chat", "embedding"]] = None
    provider: Optional[str] = None
    api_base: Optional[str] = None
    capabilities: Optional[list[str]] = None
    priority: Optional[int] = None
    cost_tier: Optional[Literal["free", "low", "standard", "premium"]] = None
    domains: Optional[list[str]] = None
    ctx_length: Optional[int] = None
    limit_requests: Optional[int] = None
    limit_input: Optional[int] = None
    limit_output: Optional[int] = None
    vision: Optional[bool] = None
    kwargs: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None


class ModelOut(Schema):
    """LLMModelConfig response."""

    id: str
    name: str
    display_name: str
    model_type: str
    provider: str
    api_base: str
    capabilities: list[str]
    priority: int
    cost_tier: str
    domains: list[str]
    ctx_length: int
    limit_requests: int
    limit_input: int
    limit_output: int
    vision: bool
    kwargs: dict[str, Any]
    is_active: bool
    created_at: str
    updated_at: str


class SlotsOut(Schema):
    """Three model slots: Chat / Utility / Embedding."""

    chat_model_id: Optional[str] = None
    utility_model_id: Optional[str] = None
    embedding_model_id: Optional[str] = None
    capsule_id: Optional[str] = None
    scope: str  # "capsule" | "tenant"


class SlotsUpdate(Schema):
    """Slot binding update. Null clears a slot."""

    chat_model_id: Optional[str] = None
    utility_model_id: Optional[str] = None
    embedding_model_id: Optional[str] = None
    capsule_id: Optional[str] = None


class PresetIn(Schema):
    """Named model preset (slot bundle)."""

    name: str
    chat_model_id: Optional[str] = None
    utility_model_id: Optional[str] = None
    embedding_model_id: Optional[str] = None
    notes: str = ""


class PresetOut(Schema):
    """Model preset response."""

    id: str
    name: str
    chat_model_id: Optional[str] = None
    utility_model_id: Optional[str] = None
    embedding_model_id: Optional[str] = None
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""


class TestConnectionIn(Schema):
    """Live provider connectivity test.

    api_key is write-only for pre-save tests; if omitted the Vault key is used.
    """

    provider: str
    model: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model_id: Optional[str] = None


class TestConnectionOut(Schema):
    """Connection test result."""

    success: bool
    latency_ms: Optional[int] = None
    detail: str = ""


class SetupGateOut(Schema):
    """Model setup gate status (MD-05)."""

    needs_setup: bool
    active_models: int
    chat_ready: bool
    utility_ready: bool
    embedding_ready: bool
    message: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _model_to_out(obj) -> ModelOut:
    return ModelOut(
        id=str(obj.id),
        name=obj.name,
        display_name=obj.display_name or obj.name,
        model_type=obj.model_type,
        provider=obj.provider,
        api_base=obj.api_base or "",
        capabilities=list(obj.capabilities or []),
        priority=obj.priority,
        cost_tier=obj.cost_tier,
        domains=list(obj.domains or []),
        ctx_length=obj.ctx_length,
        limit_requests=obj.limit_requests,
        limit_input=obj.limit_input,
        limit_output=obj.limit_output,
        vision=bool(obj.vision),
        kwargs=dict(obj.kwargs or {}),
        is_active=obj.is_active,
        created_at=obj.created_at.isoformat() if obj.created_at else "",
        updated_at=obj.updated_at.isoformat() if obj.updated_at else "",
    )


def _get_setting(agent_id: str, key: str, default: Any = None) -> Any:
    try:
        row = AgentSetting.objects.filter(agent_id=agent_id, key=key).first()
        if row is not None:
            return row.value
    except Exception:
        logger.debug("AgentSetting read failed for %s/%s", agent_id, key, exc_info=True)
    return default


def _set_setting(agent_id: str, key: str, value: Any) -> None:
    AgentSetting.objects.update_or_create(
        agent_id=agent_id,
        key=key,
        defaults={"value": value, "is_secret": False},
    )


def _get_llm_model(model_id: Optional[str]):
    from admin.llm.models import LLMModelConfig

    if not model_id:
        return None
    try:
        return LLMModelConfig.objects.get(id=model_id)
    except Exception:
        return None


def _provider_key_configured(provider: str) -> bool:
    """True if Vault holds a key for this provider. Never returns the key."""
    try:
        from services.common.unified_secret_manager import get_secret_manager

        sm = get_secret_manager()
        return bool(sm.get_provider_key(provider))
    except Exception:
        logger.warning("Vault key check failed for %s", provider, exc_info=True)
        return False


def _load_provider_configs() -> dict[str, dict[str, Any]]:
    raw = _get_setting(DEFAULTS_AGENT_ID, "llm_provider_configs", {}) or {}
    return raw if isinstance(raw, dict) else {}


def _resolve_test_model(provider: str, model: Optional[str], model_id: Optional[str]) -> str:
    if model:
        return model
    if model_id:
        obj = _get_llm_model(model_id)
        if obj:
            # LiteLLM often expects provider/model; prefer raw name when already prefixed
            if "/" in obj.name and not obj.name.startswith(obj.provider):
                return obj.name
            return (
                f"{obj.provider}/{obj.name}" if not obj.name.startswith(obj.provider) else obj.name
            )
    configs = _load_provider_configs()
    cfg = configs.get(provider, {})
    if cfg.get("model_name"):
        return f"{provider}/{cfg['model_name']}" if provider != "custom" else cfg["model_name"]
    fallback = _TEST_MODEL_FALLBACK.get(provider, "")
    if fallback:
        return f"{provider}/{fallback}" if provider not in ("custom",) else fallback
    raise HttpError(400, "model_required: provide model or model_id for connection test")


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------


@router.get("/providers", response=list[ProviderOut], auth=AuthBearer(), summary="List providers")
def list_providers(request) -> list[ProviderOut]:
    """Provider registry with enable/base URL/model and key presence (never the key)."""
    # Integrations, not ordinary config: this reports which provider credentials
    # exist. An inventory of where the keys are is not a `system:view`.
    authorize_sync(request, action="system:manage_integrations", resource="llm")
    configs = _load_provider_configs()
    result: list[ProviderOut] = []
    for pid, preset in PROVIDER_PRESETS.items():
        cfg = configs.get(pid, {}) if isinstance(configs.get(pid), dict) else {}
        result.append(
            ProviderOut(
                id=pid,
                label=cfg.get("label") or preset["label"],
                enabled=bool(cfg.get("enabled", False)),
                base_url=cfg.get("base_url", preset["default_base_url"]) or "",
                model_name=cfg.get("model_name", preset["default_model"]) or "",
                is_custom=pid == "custom",
                has_api_key=_provider_key_configured(pid),
            )
        )
    # Include custom provider rows beyond the preset id (extra OpenAI-compatible endpoints)
    for pid, cfg in configs.items():
        if pid in PROVIDER_PRESETS or not isinstance(cfg, dict):
            continue
        result.append(
            ProviderOut(
                id=pid,
                label=cfg.get("label") or pid,
                enabled=bool(cfg.get("enabled", False)),
                base_url=cfg.get("base_url") or "",
                model_name=cfg.get("model_name") or "",
                is_custom=True,
                has_api_key=_provider_key_configured(pid),
            )
        )
    return result


@router.put(
    "/providers/{provider_id}", response=ProviderOut, auth=AuthBearer(), summary="Update provider"
)
def update_provider(request, provider_id: str, body: ProviderUpdate) -> ProviderOut:
    """Enable/disable provider, set base URL and default model name."""
    authorize_sync(request, action="system:manage_integrations", resource="llm")
    configs = _load_provider_configs()
    preset = PROVIDER_PRESETS.get(provider_id, {})
    cfg = configs.get(provider_id)
    if not isinstance(cfg, dict):
        cfg = {
            "label": preset.get("label", provider_id),
            "enabled": False,
            "base_url": preset.get("default_base_url", ""),
            "model_name": preset.get("default_model", ""),
        }
    if body.enabled is not None:
        cfg["enabled"] = body.enabled
    if body.base_url is not None:
        cfg["base_url"] = body.base_url.strip()
    if body.model_name is not None:
        cfg["model_name"] = body.model_name.strip()
    if body.label is not None and provider_id == "custom":
        cfg["label"] = body.label.strip() or provider_id
    configs[provider_id] = cfg
    _set_setting(DEFAULTS_AGENT_ID, "llm_provider_configs", configs)
    return ProviderOut(
        id=provider_id,
        label=cfg.get("label") or preset.get("label", provider_id),
        enabled=bool(cfg.get("enabled", False)),
        base_url=cfg.get("base_url") or "",
        model_name=cfg.get("model_name") or "",
        is_custom=provider_id not in PROVIDER_PRESETS or provider_id == "custom",
        has_api_key=_provider_key_configured(provider_id),
    )


# ---------------------------------------------------------------------------
# LLMModelConfig CRUD
# ---------------------------------------------------------------------------


@router.get("/models", response=list[ModelOut], auth=AuthBearer(), summary="List model configs")
def list_models(
    request,
    provider: Optional[str] = None,
    model_type: Optional[str] = None,
    active_only: bool = False,
) -> list[ModelOut]:
    """List LLMModelConfig rows (real ORM)."""
    authorize_sync(request, action="system:view", resource="llm")
    from admin.llm.models import LLMModelConfig

    qs = LLMModelConfig.objects.all()
    if provider:
        qs = qs.filter(provider=provider)
    if model_type:
        qs = qs.filter(model_type=model_type)
    if active_only:
        qs = qs.filter(is_active=True)
    return [_model_to_out(m) for m in qs]


@router.post("/models", response=ModelOut, auth=AuthBearer(), summary="Create model config")
def create_model(request, body: ModelIn) -> ModelOut:
    """Create an LLMModelConfig. Does not accept API keys."""
    authorize_sync(request, action="system:configure", resource="llm")
    from django.db import IntegrityError

    from admin.llm.models import LLMModelConfig

    if LLMModelConfig.objects.filter(name=body.name).exists():
        raise HttpError(409, f"model_name_exists: {body.name}")
    try:
        obj = LLMModelConfig.objects.create(
            name=body.name,
            display_name=body.display_name or body.name,
            model_type=body.model_type,
            provider=body.provider,
            api_base=body.api_base,
            capabilities=body.capabilities,
            priority=body.priority,
            cost_tier=body.cost_tier,
            domains=body.domains,
            ctx_length=body.ctx_length,
            limit_requests=body.limit_requests,
            limit_input=body.limit_input,
            limit_output=body.limit_output,
            vision=body.vision,
            kwargs=body.kwargs,
            is_active=body.is_active,
        )
    except IntegrityError as exc:
        raise HttpError(409, f"model_name_exists: {body.name}") from exc
    return _model_to_out(obj)


@router.get("/models/{model_id}", response=ModelOut, auth=AuthBearer(), summary="Get model config")
def get_model(request, model_id: str) -> ModelOut:
    authorize_sync(request, action="system:view", resource="llm")
    obj = _get_llm_model(model_id)
    if obj is None:
        raise HttpError(404, f"model_not_found: {model_id}")
    return _model_to_out(obj)


@router.patch(
    "/models/{model_id}", response=ModelOut, auth=AuthBearer(), summary="Update model config"
)
def update_model(request, model_id: str, body: ModelPatch) -> ModelOut:
    authorize_sync(request, action="system:configure", resource="llm")
    obj = _get_llm_model(model_id)
    if obj is None:
        raise HttpError(404, f"model_not_found: {model_id}")
    data = body.dict(exclude_unset=True)
    for field, value in data.items():
        setattr(obj, field, value)
    obj.save()
    return _model_to_out(obj)


@router.delete("/models/{model_id}", auth=AuthBearer(), summary="Delete model config")
def delete_model(request, model_id: str) -> dict:
    authorize_sync(request, action="system:configure", resource="llm")
    obj = _get_llm_model(model_id)
    if obj is None:
        raise HttpError(404, f"model_not_found: {model_id}")
    # PROTECT FKs (Capsule.chat_model) will raise; surface as 409
    try:
        obj.delete()
    except Exception as exc:
        raise HttpError(409, f"model_in_use: {exc}") from exc
    return {"deleted": True, "id": model_id}


# ---------------------------------------------------------------------------
# Slots (MD-06) — Chat / Utility / Embedding
# ---------------------------------------------------------------------------


@router.get("/slots", response=SlotsOut, auth=AuthBearer(), summary="Get model slots")
def get_slots(request, capsule_id: Optional[str] = None) -> SlotsOut:
    """Three slots bound to an active Capsule or tenant defaults."""
    authorize_sync(request, action="system:view", resource="llm")
    if capsule_id:
        cap = Capsule.objects.filter(id=capsule_id).select_related("chat_model").first()
        if cap is None:
            raise HttpError(404, f"capsule_not_found: {capsule_id}")
        # Relation object, not the FK attname: pyright cannot see chat_model_id.
        # select_related keeps this to the same single query.
        chat = cap.chat_model
        chat_id = str(chat.pk) if chat else None
        utility_id = _get_setting(str(cap.id), "utility_model_id")
        embedding_id = _get_setting(str(cap.id), "embedding_model_id")
        return SlotsOut(
            chat_model_id=chat_id,
            utility_model_id=str(utility_id) if utility_id else None,
            embedding_model_id=str(embedding_id) if embedding_id else None,
            capsule_id=str(cap.id),
            scope="capsule",
        )
    return SlotsOut(
        chat_model_id=str(_get_setting(DEFAULTS_AGENT_ID, "chat_model_id") or "") or None,
        utility_model_id=str(_get_setting(DEFAULTS_AGENT_ID, "utility_model_id") or "") or None,
        embedding_model_id=str(_get_setting(DEFAULTS_AGENT_ID, "embedding_model_id") or "") or None,
        capsule_id=None,
        scope="tenant",
    )


@router.put("/slots", response=SlotsOut, auth=AuthBearer(), summary="Set model slots")
def set_slots(request, body: SlotsUpdate) -> SlotsOut:
    """Persist Chat/Utility/Embedding slot bindings.

    With capsule_id: chat binds Capsule.chat_model FK; utility/embedding via AgentSetting.
    Without: tenant defaults under agent_id=default.
    """
    authorize_sync(request, action="system:configure", resource="llm")
    data = body.dict(exclude_unset=True)
    capsule_id = data.pop("capsule_id", None)

    if capsule_id:
        cap = Capsule.objects.filter(id=capsule_id).first()
        if cap is None:
            raise HttpError(404, f"capsule_not_found: {capsule_id}")
        if "chat_model_id" in data:
            if data["chat_model_id"]:
                model = _get_llm_model(data["chat_model_id"])
                if model is None:
                    raise HttpError(400, f"chat_model_not_found: {data['chat_model_id']}")
                if model.model_type != "chat":
                    raise HttpError(400, "chat_slot_requires_chat_model")
                cap.chat_model = model
            else:
                cap.chat_model = None
            cap.save(update_fields=["chat_model"])
        if "utility_model_id" in data:
            if data["utility_model_id"] and _get_llm_model(data["utility_model_id"]) is None:
                raise HttpError(400, f"utility_model_not_found: {data['utility_model_id']}")
            _set_setting(str(cap.id), "utility_model_id", data["utility_model_id"])
        if "embedding_model_id" in data:
            if data["embedding_model_id"]:
                emb = _get_llm_model(data["embedding_model_id"])
                if emb is None:
                    raise HttpError(400, f"embedding_model_not_found: {data['embedding_model_id']}")
                if emb.model_type != "embedding":
                    raise HttpError(400, "embedding_slot_requires_embedding_model")
            _set_setting(str(cap.id), "embedding_model_id", data["embedding_model_id"])
        return get_slots(request, capsule_id=str(cap.id))

    for key in ("chat_model_id", "utility_model_id", "embedding_model_id"):
        if key in data:
            if data[key] and _get_llm_model(data[key]) is None:
                raise HttpError(400, f"{key}_not_found: {data[key]}")
            _set_setting(DEFAULTS_AGENT_ID, key, data[key])
    return get_slots(request)


# ---------------------------------------------------------------------------
# Presets (MD-02)
# ---------------------------------------------------------------------------


def _load_presets() -> list[dict[str, Any]]:
    raw = _get_setting(DEFAULTS_AGENT_ID, "model_presets", []) or []
    return raw if isinstance(raw, list) else []


@router.get("/presets", response=list[PresetOut], auth=AuthBearer(), summary="List model presets")
def list_presets(request) -> list[PresetOut]:
    """Named slot bundles persisted via AgentSetting (LLMModelConfig-backed ids)."""
    authorize_sync(request, action="system:view", resource="llm")
    return [
        PresetOut(
            id=str(p.get("id", "")),
            name=p.get("name", ""),
            chat_model_id=p.get("chat_model_id"),
            utility_model_id=p.get("utility_model_id"),
            embedding_model_id=p.get("embedding_model_id"),
            notes=p.get("notes", ""),
            created_at=p.get("created_at", ""),
            updated_at=p.get("updated_at", ""),
        )
        for p in _load_presets()
    ]


@router.post("/presets", response=PresetOut, auth=AuthBearer(), summary="Save model preset")
def create_preset(request, body: PresetIn) -> PresetOut:
    authorize_sync(request, action="system:configure", resource="llm")
    presets = _load_presets()
    from django.utils import timezone

    now = timezone.now().isoformat()
    preset = {
        "id": str(uuid.uuid4()),
        "name": body.name.strip(),
        "chat_model_id": body.chat_model_id,
        "utility_model_id": body.utility_model_id,
        "embedding_model_id": body.embedding_model_id,
        "notes": body.notes,
        "created_at": now,
        "updated_at": now,
    }
    if not preset["name"]:
        raise HttpError(400, "preset_name_required")
    if any(p.get("name") == preset["name"] for p in presets):
        raise HttpError(409, f"preset_name_exists: {preset['name']}")
    presets.append(preset)
    _set_setting(DEFAULTS_AGENT_ID, "model_presets", presets)
    return PresetOut(
        id=preset["id"],
        name=preset["name"],
        chat_model_id=preset["chat_model_id"],
        utility_model_id=preset["utility_model_id"],
        embedding_model_id=preset["embedding_model_id"],
        notes=preset["notes"],
        created_at=preset["created_at"],
        updated_at=preset["updated_at"],
    )


@router.post(
    "/presets/{preset_id}/apply", response=SlotsOut, auth=AuthBearer(), summary="Apply preset"
)
def apply_preset(request, preset_id: str, capsule_id: Optional[str] = None) -> SlotsOut:
    """Load a preset into the active slots (Capsule or tenant defaults)."""
    authorize_sync(request, action="system:configure", resource="llm")
    presets = _load_presets()
    preset = next((p for p in presets if str(p.get("id")) == preset_id), None)
    if preset is None:
        raise HttpError(404, f"preset_not_found: {preset_id}")
    payload = SlotsUpdate(
        chat_model_id=preset.get("chat_model_id"),
        utility_model_id=preset.get("utility_model_id"),
        embedding_model_id=preset.get("embedding_model_id"),
        capsule_id=capsule_id,
    )
    return set_slots(request, payload)


@router.delete("/presets/{preset_id}", auth=AuthBearer(), summary="Delete model preset")
def delete_preset(request, preset_id: str) -> dict:
    authorize_sync(request, action="system:configure", resource="llm")
    presets = _load_presets()
    remaining = [p for p in presets if str(p.get("id")) != preset_id]
    if len(remaining) == len(presets):
        raise HttpError(404, f"preset_not_found: {preset_id}")
    _set_setting(DEFAULTS_AGENT_ID, "model_presets", remaining)
    return {"deleted": True, "id": preset_id}


# ---------------------------------------------------------------------------
# Test connection + setup gate
# ---------------------------------------------------------------------------


@router.post(
    "/test-connection",
    response=TestConnectionOut,
    auth=AuthBearer(),
    summary="Test LLM provider connection",
)
async def test_connection(request, body: TestConnectionIn) -> TestConnectionOut:
    """Live LiteLLM ping. Uses provided api_key (write-only) or Vault key."""
    # Gate before any field is read out of the body. This is the one route here
    # that spends a credential against a caller-supplied base_url — a live
    # outbound call, not a read of configuration.
    await authorize(request, action="system:manage_integrations", resource="llm")
    import time

    import litellm

    provider = body.provider.lower().strip()
    api_key = body.api_key
    if not api_key:
        try:
            from services.common.unified_secret_manager import get_secret_manager

            api_key = get_secret_manager().get_provider_key(provider)
        except Exception:
            api_key = None

    needs_key = provider not in ("ollama", "custom")
    if needs_key and not api_key:
        return TestConnectionOut(
            success=False,
            detail=f"api_key_missing: no key in Vault for provider '{provider}'",
        )

    try:
        model = _resolve_test_model(provider, body.model, body.model_id)
    except HttpError as exc:
        return TestConnectionOut(success=False, detail=str(exc))

    # Prefer explicit base_url, then model config, then provider preset
    base_url = body.base_url
    if not base_url and body.model_id:
        obj = _get_llm_model(body.model_id)
        if obj and obj.api_base:
            base_url = obj.api_base
    if not base_url:
        configs = _load_provider_configs()
        cfg = configs.get(provider, {})
        if isinstance(cfg, dict):
            base_url = cfg.get("base_url") or None
        if not base_url and provider in PROVIDER_PRESETS:
            base_url = PROVIDER_PRESETS[provider]["default_base_url"] or None
        if not base_url and provider == "ollama":
            return TestConnectionOut(
                success=False,
                detail="api_base_missing: Ollama has no default host. "
                "Set api_base on the model row (or an InfrastructureConfig "
                "entry) to the Ollama endpoint.",
            )

    started = time.perf_counter()
    try:
        await litellm.acompletion(
            model=model,
            messages=[{"role": "user", "content": "ping"}],
            api_key=api_key,
            api_base=base_url,
            timeout=8,
        )
        latency = int((time.perf_counter() - started) * 1000)
        return TestConnectionOut(success=True, latency_ms=latency, detail="ok")
    except Exception as exc:
        logger.info("test-connection failed for %s/%s: %s", provider, model, exc)
        return TestConnectionOut(
            success=False,
            latency_ms=int((time.perf_counter() - started) * 1000),
            detail=str(exc)[:500],
        )


@router.get(
    "/setup-gate",
    response=SetupGateOut,
    auth=AuthBearer(),
    summary="Model setup gate status",
)
def setup_gate(request, capsule_id: Optional[str] = None) -> SetupGateOut:
    """MD-05: gate when zero models are configured / slots empty."""
    authorize_sync(request, action="system:view", resource="llm")
    from admin.llm.models import LLMModelConfig

    active_models = LLMModelConfig.objects.filter(is_active=True).count()
    slots = get_slots(request, capsule_id=capsule_id)
    chat_ready = bool(slots.chat_model_id) or active_models > 0
    utility_ready = bool(slots.utility_model_id) or active_models > 0
    embedding_ready = bool(slots.embedding_model_id) or (
        LLMModelConfig.objects.filter(is_active=True, model_type="embedding").exists()
    )
    needs_setup = active_models == 0
    message = (
        "No models configured yet. Add at least one provider model, save its API key, "
        "then bind Chat / Utility / Embedding slots before chatting."
        if needs_setup
        else "Models configured."
    )
    return SetupGateOut(
        needs_setup=needs_setup,
        active_models=active_models,
        chat_ready=chat_ready,
        utility_ready=utility_ready,
        embedding_ready=embedding_ready,
        message=message,
    )
