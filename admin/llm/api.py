"""LLM Models / Providers / Presets / Roles API.

Real Django ORM-backed LLMModelConfig management for C5 (MD-01…MD-06).
- Provider registry presets (OpenAI, Anthropic, Google, Groq, Ollama, custom)
- LLMModelConfig CRUD
- Chat / Utility / Embedding role bindings (Capsule or tenant defaults)
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

# Known provider registry (UI presets). Custom OpenAI-compatible is free-form.
# Ids come from admin.llm.providers.KNOWN_PROVIDER_IDS. Base URLs are vendor
# *protocol* constants from admin.core.helpers.vendor_api_bases — the effective
# base an operator calls is LLMModelConfig.api_base (or the preset shown here as
# a starting point), never a host invented in this file. Mimo / Ollama /
# Cloudflare are deployment endpoints (empty default base).
from admin.llm.providers import (
    ANTHROPIC_API_BASE,
    DEFAULTS_AGENT_ID,
    DEEPSEEK_API_BASE,
    GOOGLE_GENERATIVE_LANGUAGE_API_BASE,
    GROQ_API_BASE,
    HUGGINGFACE_API_BASE,
    MODEL_ROLES,
    OPENAI_API_BASE,
    ROLE_SETTING_KEYS,
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
    "deepseek": {
        "label": "DeepSeek",
        "default_base_url": DEEPSEEK_API_BASE,
        "default_model": "deepseek-chat",
    },
    "huggingface": {
        "label": "Hugging Face",
        "default_base_url": HUGGINGFACE_API_BASE,
        "default_model": "sentence-transformers/all-MiniLM-L6-v2",
    },
    "mimo": {
        "label": "MiMo",
        # Deployment endpoint, not a vendor cloud. Operator names it on the
        # model row / InfrastructureConfig; empty is honest (R-VEN-02).
        "default_base_url": "",
        "default_model": "mimo-v2.6-flash",
    },
    "ollama": {
        "label": "Ollama",
        # Ollama is a deployment endpoint, not a vendor cloud. The operator
        # names it (LLMModelConfig.api_base / InfrastructureConfig); there is
        # no local-install default to fall back to.
        "default_base_url": "",
        "default_model": "llama3.1",
    },
    "cloudflare": {
        "label": "Cloudflare (Clef)",
        # Clef / Workers AI is a deployment endpoint: CLEF_API_BASE on
        # SettingsModel. No protocol default (R-VEN-02).
        "default_base_url": "",
        "default_model": "clef-decision",
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
    "deepseek": "deepseek-chat",
    "huggingface": "sentence-transformers/all-MiniLM-L6-v2",
    "mimo": "mimo-v2.6-flash",
    "ollama": "llama3.1",
    "cloudflare": "clef-decision",
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
    model_type: Literal["chat", "embedding", "decision"] = "chat"
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
    model_type: Optional[Literal["chat", "embedding", "decision"]] = None
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


class RolesOut(Schema):
    """Five model roles: Chat / Utility / Embedding / Vision / Decision (Clef).

    Five model roles. ``chat_role`` binds ``Capsule.chat_model`` FK and
    ``vision_role`` binds ``Capsule.image_model`` FK; the rest are AgentSetting
    keys (see ``admin.llm.providers.ROLE_SETTING_KEYS``).

    ``decision_role_id`` is the AgentSetting key name (``decision_role_id``)
    and is the canonical decision binding; ``decision_role`` is the same value
    under the role-named field.
    """

    chat_role: Optional[str] = None
    utility_role: Optional[str] = None
    embedding_role: Optional[str] = None
    vision_role: Optional[str] = None
    decision_role: Optional[str] = None
    decision_role_id: Optional[str] = None
    capsule_id: Optional[str] = None
    scope: str  # "capsule" | "tenant"


class RolesUpdate(Schema):
    """Role binding update. Null clears a role."""

    chat_role: Optional[str] = None
    utility_role: Optional[str] = None
    embedding_role: Optional[str] = None
    vision_role: Optional[str] = None
    decision_role: Optional[str] = None
    decision_role_id: Optional[str] = None
    capsule_id: Optional[str] = None


class PresetIn(Schema):
    """Named model preset (role bundle)."""

    name: str
    chat_model_id: Optional[str] = None
    utility_model_id: Optional[str] = None
    embedding_model_id: Optional[str] = None
    vision_role_id: Optional[str] = None
    decision_role_id: Optional[str] = None
    is_bundled: bool = False
    scope: Literal["global", "agent", "chat"] = "global"
    notes: str = ""


class PresetOut(Schema):
    """Model preset response."""

    id: str
    name: str
    chat_model_id: Optional[str] = None
    utility_model_id: Optional[str] = None
    embedding_model_id: Optional[str] = None
    vision_role_id: Optional[str] = None
    decision_role_id: Optional[str] = None
    is_bundled: bool = False
    scope: str = "global"
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""


class RestoreBundledOut(Schema):
    """Result of POST /llm/presets/restore-bundled."""

    restored: list[str] = []
    skipped: list[str] = []
    total: int = 0


class ModelSearchIn(Schema):
    """List models from a live provider endpoint (key + custom URL).

    api_key is write-only (form → Vault). api_base is the custom URL; empty
    uses the provider default. model_type filters chat vs embedding names.
    """

    provider: str
    query: str = ""
    model_type: str = "chat"
    api_base: Optional[str] = None
    api_key: Optional[str] = None


class ModelSearchOut(Schema):
    """Live model list from the provider (or registry fallback)."""

    models: list[str] = []
    source: str = "none"  # live | registry | none | error
    detail: str = ""


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
# Model roles (MD-06) — Chat / Utility / Embedding / Vision / Decision (Clef)
# ---------------------------------------------------------------------------

# Capsule FK fields for roles that are model sovereignty columns (Rule 91).
# Remaining roles live in AgentSetting under ROLE_SETTING_KEYS.
_CAPSULE_FK_FIELDS = {
    "chat_role": ("chat_model", "chat"),
    "vision_role": ("image_model", None),
}


def _role_model_type_required(role: str) -> Optional[str]:
    """model_type a role accepts. None = any type (utility is free)."""
    if role == "embedding_role":
        return "embedding"
    if role == "decision_role":
        return "decision"
    if role in ("chat_role", "vision_role"):
        return "chat"
    return None


def _read_roles(scope_key: str, cap: Optional[Capsule] = None) -> RolesOut:
    def _setting(role: str) -> Optional[str]:
        return str(_get_setting(scope_key, ROLE_SETTING_KEYS[role]) or "") or None

    if cap is not None:
        chat = cap.chat_model
        vision = cap.image_model
        decision = _setting("decision_role")
        return RolesOut(
            chat_role=str(chat.pk) if chat else None,
            utility_role=_setting("utility_role"),
            embedding_role=_setting("embedding_role"),
            vision_role=str(vision.pk) if vision else None,
            decision_role=decision,
            decision_role_id=decision,
            capsule_id=str(cap.id),
            scope="capsule",
        )
    decision = _setting("decision_role")
    return RolesOut(
        chat_role=str(_get_setting(scope_key, "chat_model_id") or "") or None,
        utility_role=_setting("utility_role"),
        embedding_role=_setting("embedding_role"),
        vision_role=str(_get_setting(scope_key, "vision_model_id") or "") or None,
        decision_role=decision,
        decision_role_id=decision,
        capsule_id=None,
        scope="tenant",
    )


@router.get("/roles", response=RolesOut, auth=AuthBearer(), summary="Get model roles")
def get_roles(request, capsule_id: Optional[str] = None) -> RolesOut:
    """Five roles bound to an active Capsule or tenant defaults."""
    authorize_sync(request, action="system:view", resource="llm")
    if capsule_id:
        cap = (
            Capsule.objects.filter(id=capsule_id)
            .select_related("chat_model", "image_model")
            .first()
        )
        if cap is None:
            raise HttpError(404, f"capsule_not_found: {capsule_id}")
        return _read_roles(str(cap.id), cap=cap)
    return _read_roles(DEFAULTS_AGENT_ID)


@router.put("/roles", response=RolesOut, auth=AuthBearer(), summary="Set model roles")
def set_roles(request, body: RolesUpdate) -> RolesOut:
    """Persist role bindings.

    With capsule_id: chat_role binds Capsule.chat_model FK; vision_role binds
    Capsule.image_model FK; utility/embedding/decision via AgentSetting.
    Without: tenant defaults under agent_id=default.
    """
    authorize_sync(request, action="system:configure", resource="llm")
    data = body.dict(exclude_unset=True)
    capsule_id = data.pop("capsule_id", None)
    # Canonical decision binding name; role-named field is accepted as alias.
    if "decision_role_id" in data and "decision_role" not in data:
        data["decision_role"] = data.pop("decision_role_id")
    else:
        data.pop("decision_role_id", None)

    if capsule_id:
        cap = Capsule.objects.filter(id=capsule_id).first()
        if cap is None:
            raise HttpError(404, f"capsule_not_found: {capsule_id}")
        for role, value in data.items():
            if role not in MODEL_ROLES:
                continue
            required = _role_model_type_required(role)
            if value:
                model = _get_llm_model(value)
                if model is None:
                    raise HttpError(400, f"{role}_not_found: {value}")
                if required and model.model_type != required:
                    raise HttpError(400, f"{role}_requires_{required}_model")
            if role in _CAPSULE_FK_FIELDS:
                fk_name = _CAPSULE_FK_FIELDS[role][0]
                setattr(cap, fk_name, _get_llm_model(value) if value else None)
                cap.save(update_fields=[fk_name])
            else:
                _set_setting(str(cap.id), ROLE_SETTING_KEYS[role], value)
        return _read_roles(str(cap.id), cap=cap)

    for role, value in data.items():
        if role not in MODEL_ROLES:
            continue
        required = _role_model_type_required(role)
        if value:
            model = _get_llm_model(value)
            if model is None:
                raise HttpError(400, f"{role}_not_found: {value}")
            if required and model.model_type != required:
                raise HttpError(400, f"{role}_requires_{required}_model")
        _set_setting(DEFAULTS_AGENT_ID, ROLE_SETTING_KEYS[role], value)
    return _read_roles(DEFAULTS_AGENT_ID)


# ---------------------------------------------------------------------------
# Presets (MD-02) — role bundles; bundled catalog + restore
# ---------------------------------------------------------------------------


def _preset_to_out(p: dict[str, Any]) -> PresetOut:
    return PresetOut(
        id=str(p.get("id", "")),
        name=p.get("name", ""),
        chat_model_id=p.get("chat_model_id"),
        utility_model_id=p.get("utility_model_id"),
        embedding_model_id=p.get("embedding_model_id"),
        vision_role_id=p.get("vision_role_id"),
        decision_role_id=p.get("decision_role_id"),
        is_bundled=bool(p.get("is_bundled", False)),
        scope=p.get("scope", "global"),
        notes=p.get("notes", ""),
        created_at=p.get("created_at", ""),
        updated_at=p.get("updated_at", ""),
    )


def _load_presets() -> list[dict[str, Any]]:
    raw = _get_setting(DEFAULTS_AGENT_ID, "model_presets", []) or []
    return raw if isinstance(raw, list) else []


# Bundled presets reference models by catalog `name` (stable across DBs);
# restore-bundled resolves names -> LLMModelConfig ids at call time.
BUNDLED_PRESETS: list[dict[str, Any]] = [
    {
        "name": "Soma Default",
        "notes": "Free first: MiMo Flash for chat/utility, local embed, Clef decision.",
        "chat_model_name": "mimo-v2.6-flash",
        "utility_model_name": "mimo-v2.6-flash",
        "embedding_model_name": "sentence-transformers/all-MiniLM-L6-v2",
        "vision_model_name": "openai/gpt-4o-mini",
        "decision_model_name": "clef-decision",
    },
    {
        "name": "Groq Fast",
        "notes": "Lowest latency chat via Groq OSS.",
        "chat_model_name": "openai/gpt-oss-120b",
        "utility_model_name": "openai/gpt-oss-20b",
        "embedding_model_name": "sentence-transformers/all-MiniLM-L6-v2",
        "vision_model_name": "openai/gpt-4o-mini",
        "decision_model_name": "clef-decision",
    },
    {
        "name": "OpenAI Balanced",
        "notes": "GPT-4o chat + vision, OpenAI embeddings.",
        "chat_model_name": "openai/gpt-4o",
        "utility_model_name": "openai/gpt-4o-mini",
        "embedding_model_name": "openai/text-embedding-3-small",
        "vision_model_name": "openai/gpt-4o-mini",
        "decision_model_name": "clef-decision",
    },
    {
        "name": "DeepSeek Reason",
        "notes": "DeepSeek reasoner for deep work, chat for utility.",
        "chat_model_name": "deepseek-reasoner",
        "utility_model_name": "deepseek-chat",
        "embedding_model_name": "sentence-transformers/all-MiniLM-L6-v2",
        "vision_model_name": "openai/gpt-4o-mini",
        "decision_model_name": "clef-decision",
    },
    {
        "name": "Anthropic Careful",
        "notes": "Claude Haiku chat — careful, cheap, fast.",
        "chat_model_name": "claude-3-5-haiku-latest",
        "utility_model_name": "claude-3-5-haiku-latest",
        "embedding_model_name": "sentence-transformers/all-MiniLM-L6-v2",
        "vision_model_name": "openai/gpt-4o-mini",
        "decision_model_name": "clef-decision",
    },
]


def _resolve_model_id_by_name(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    from admin.llm.models import LLMModelConfig

    obj = LLMModelConfig.objects.filter(name=name, is_active=True).first()
    return str(obj.pk) if obj else None


@router.get("/presets", response=list[PresetOut], auth=AuthBearer(), summary="List model presets")
def list_presets(request) -> list[PresetOut]:
    """Named role bundles persisted via AgentSetting (LLMModelConfig-backed ids)."""
    authorize_sync(request, action="system:view", resource="llm")
    return [_preset_to_out(p) for p in _load_presets()]


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
        "vision_role_id": body.vision_role_id,
        "decision_role_id": body.decision_role_id,
        "is_bundled": body.is_bundled,
        "scope": body.scope,
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
    return _preset_to_out(preset)


@router.post(
    "/presets/restore-bundled",
    response=RestoreBundledOut,
    auth=AuthBearer(),
    summary="Restore bundled model presets",
)
def restore_bundled_presets(request) -> RestoreBundledOut:
    """Upsert the five bundled presets from the catalog (idempotent by name).

    Model ids are resolved from LLMModelConfig by catalog name at call time so
    the bundles work on any database. Presets whose models are not yet seeded
    are skipped with their names listed — never invented ids.
    """
    authorize_sync(request, action="system:configure", resource="llm")
    from django.utils import timezone

    presets = _load_presets()
    by_name = {p.get("name"): p for p in presets if p.get("name")}
    now = timezone.now().isoformat()
    restored: list[str] = []
    skipped: list[str] = []

    for spec in BUNDLED_PRESETS:
        chat_id = _resolve_model_id_by_name(spec.get("chat_model_name"))
        if chat_id is None:
            skipped.append(spec["name"])
            continue
        payload = {
            "chat_model_id": chat_id,
            "utility_model_id": _resolve_model_id_by_name(spec.get("utility_model_name")),
            "embedding_model_id": _resolve_model_id_by_name(spec.get("embedding_model_name")),
            "vision_role_id": _resolve_model_id_by_name(spec.get("vision_model_name")),
            "decision_role_id": _resolve_model_id_by_name(spec.get("decision_model_name")),
            "is_bundled": True,
            "scope": "global",
            "notes": spec.get("notes", ""),
            "updated_at": now,
        }
        existing = by_name.get(spec["name"])
        if existing is not None:
            existing.update(payload)
        else:
            entry = {
                "id": str(uuid.uuid4()),
                "name": spec["name"],
                "created_at": now,
                **payload,
            }
            presets.append(entry)
            by_name[spec["name"]] = entry
        restored.append(spec["name"])

    _set_setting(DEFAULTS_AGENT_ID, "model_presets", presets)
    return RestoreBundledOut(
        restored=restored,
        skipped=skipped,
        total=len(BUNDLED_PRESETS),
    )


@router.post(
    "/presets/{preset_id}/apply", response=RolesOut, auth=AuthBearer(), summary="Apply preset"
)
def apply_preset(request, preset_id: str, capsule_id: Optional[str] = None) -> RolesOut:
    """Load a preset into the active roles (Capsule or tenant defaults)."""
    authorize_sync(request, action="system:configure", resource="llm")
    presets = _load_presets()
    preset = next((p for p in presets if str(p.get("id")) == preset_id), None)
    if preset is None:
        raise HttpError(404, f"preset_not_found: {preset_id}")
    payload = RolesUpdate(
        chat_role=preset.get("chat_model_id"),
        utility_role=preset.get("utility_model_id"),
        embedding_role=preset.get("embedding_model_id"),
        vision_role=preset.get("vision_role_id"),
        decision_role_id=preset.get("decision_role_id"),
        capsule_id=capsule_id,
    )
    return set_roles(request, payload)


@router.patch("/presets/{preset_id}", response=PresetOut, auth=AuthBearer(), summary="Edit model preset")
def update_preset(request, preset_id: str, body: PresetIn) -> PresetOut:
    """Edit a user preset in place. Bundled presets are catalog rows — restore
    them with POST /presets/restore-bundled instead of editing."""
    authorize_sync(request, action="system:configure", resource="llm")
    presets = _load_presets()
    existing = next((p for p in presets if str(p.get("id")) == preset_id), None)
    if existing is None:
        raise HttpError(404, f"preset_not_found: {preset_id}")
    if existing.get("is_bundled"):
        raise HttpError(409, "preset_is_bundled: use restore-bundled to reset catalog presets")
    from django.utils import timezone

    name = body.name.strip()
    if not name:
        raise HttpError(400, "preset_name_required")
    if any(
        p.get("name") == name and str(p.get("id")) != preset_id for p in presets
    ):
        raise HttpError(409, f"preset_name_exists: {name}")
    existing.update(
        {
            "name": name,
            "chat_model_id": body.chat_model_id,
            "utility_model_id": body.utility_model_id,
            "embedding_model_id": body.embedding_model_id,
            "vision_role_id": body.vision_role_id,
            "decision_role_id": body.decision_role_id,
            "scope": body.scope,
            "notes": body.notes,
            "updated_at": timezone.now().isoformat(),
        }
    )
    _set_setting(DEFAULTS_AGENT_ID, "model_presets", presets)
    return _preset_to_out(existing)


@router.delete("/presets/{preset_id}", auth=AuthBearer(), summary="Delete model preset")
def delete_preset(request, preset_id: str) -> dict:
    authorize_sync(request, action="system:configure", resource="llm")
    presets = _load_presets()
    target = next((p for p in presets if str(p.get("id")) == preset_id), None)
    if target is None:
        raise HttpError(404, f"preset_not_found: {preset_id}")
    if target.get("is_bundled"):
        raise HttpError(409, "preset_is_bundled: bundled presets cannot be deleted")
    remaining = [p for p in presets if str(p.get("id")) != preset_id]
    _set_setting(DEFAULTS_AGENT_ID, "model_presets", remaining)
    return {"deleted": True, "id": preset_id}


# ---------------------------------------------------------------------------
# Live model list (Load models button)
# ---------------------------------------------------------------------------


@router.post(
    "/models/search",
    response=ModelSearchOut,
    auth=AuthBearer(),
    summary="List models from provider (key + optional custom URL)",
)
async def search_models(request, body: ModelSearchIn) -> ModelSearchOut:
    """Fetch model IDs from the provider's /models (OpenAI-compatible) or Ollama.

    Uses write-only api_key if given, else Vault. Custom api_base (e.g. MiMo
    gateway) overrides the vendor default. Falls back to LiteLLM registry names
    when the endpoint cannot list models.
    """
    await authorize(request, action="system:manage_integrations", resource="llm")
    import re as _re

    import httpx

    provider = (body.provider or "").lower().strip()
    if not provider:
        return ModelSearchOut(models=[], source="none", detail="provider_required")

    api_key = body.api_key
    if not api_key:
        try:
            from services.common.unified_secret_manager import get_secret_manager

            api_key = get_secret_manager().get_provider_key(provider)
        except Exception:
            api_key = None

    base_url = (body.api_base or "").strip().rstrip("/")
    if not base_url:
        cfg = _load_provider_configs().get(provider, {})
        if isinstance(cfg, dict):
            base_url = (cfg.get("base_url") or "").rstrip("/")
        if not base_url:
            base_url = (PROVIDER_PRESETS.get(provider, {}).get("default_base_url") or "").rstrip("/")

    exclude = _re.compile(
        r"dall-e|gpt-image|tts|whisper|audio|transcri|speech|realtime|embed|moderation",
        _re.I,
    )
    want_embed = (body.model_type or "chat").lower() == "embedding"
    query = (body.query or "").strip().lower()

    names: list[str] = []
    source = "none"
    detail = ""
    if base_url:
        headers = {"Accept": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        timeout = httpx.Timeout(8.0, connect=4.0)
        try:
            if provider == "ollama":
                url = f"{base_url}/api/tags"
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                payload = resp.json()
                raw = payload.get("models") or payload.get("names") or []
                for item in raw:
                    if isinstance(item, dict):
                        names.append(str(item.get("name") or item.get("model") or ""))
                    else:
                        names.append(str(item))
            else:
                url = f"{base_url}/models"
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                payload = resp.json()
                raw = payload.get("data") or payload.get("models") or []
                for item in raw:
                    if isinstance(item, dict):
                        mid = item.get("id") or item.get("name") or ""
                        names.append(str(mid))
                    else:
                        names.append(str(item))
            source = "live"
        except Exception as exc:
            source = "error"
            detail = str(exc)[:300]

    names = [n.strip() for n in names if isinstance(n, str) and n.strip()]
    if names:
        if want_embed:
            names = [n for n in names if exclude.search(n)] or names
        else:
            names = [n for n in names if not exclude.search(n)]
        if query:
            names = [n for n in names if query in n.lower()]
    elif source != "error":
        # LiteLLM registry names — availability not verified
        try:
            import litellm

            reg = list(getattr(litellm, "model_list", []) or [])
            names = [str(n) for n in reg if isinstance(n, str)]
            if query:
                names = [n for n in names if query in n.lower()]
            if names:
                source = "registry"
        except Exception:
            pass

    return ModelSearchOut(models=sorted(set(names))[:200], source=source, detail=detail)


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
    """MD-05: gate when zero models are configured / role bindings empty."""
    authorize_sync(request, action="system:view", resource="llm")
    from admin.llm.models import LLMModelConfig

    active_models = LLMModelConfig.objects.filter(is_active=True).count()
    roles = get_roles(request, capsule_id=capsule_id)
    chat_ready = bool(roles.chat_role) or active_models > 0
    utility_ready = bool(roles.utility_role) or active_models > 0
    embedding_ready = bool(roles.embedding_role) or (
        LLMModelConfig.objects.filter(is_active=True, model_type="embedding").exists()
    )
    needs_setup = active_models == 0
    message = (
        "No models configured yet. Add at least one provider model, save its API key, "
        "then bind Chat / Utility / Embedding roles before chatting."
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
