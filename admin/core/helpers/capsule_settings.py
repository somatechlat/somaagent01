"""Capsule-bound categorized settings (ISO-style layers).

Resolution order (highest wins) — no hardcoded product behavior:

    1. Capsule.persona_config["settings"][CATEGORY][key]   (agent identity)
    2. AgentSetting ORM (agent_id, key)                     (runtime overrides)
    3. Django settings                                      (infra authority)
    4. Schema default only when the key is optional

Env is for URLs/hosts/ports only. Vault owns secrets (is_secret=True on
AgentSetting). Categories follow the ISO settings-model taxonomy documented
in ``docs/iso/SOMA-SETTINGS-MODEL-001.md``.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

# ISO-style categories (normative — keep in sync with SOMA-SETTINGS-MODEL-001).
CATEGORY_INFRA = "INFRA"
CATEGORY_SECURITY = "SECURITY"
CATEGORY_MEMORY = "MEMORY"
CATEGORY_LLM = "LLM"
CATEGORY_AGENT = "AGENT"
CATEGORY_PERSONALITY = "PERSONALITY"
CATEGORY_UI = "UI"
CATEGORY_GOVERNANCE = "GOVERNANCE"
CATEGORY_OBSERVABILITY = "OBSERVABILITY"
CATEGORY_INTEGRATION = "INTEGRATION"

CATEGORIES: tuple[str, ...] = (
    CATEGORY_INFRA,
    CATEGORY_SECURITY,
    CATEGORY_MEMORY,
    CATEGORY_LLM,
    CATEGORY_AGENT,
    CATEGORY_PERSONALITY,
    CATEGORY_UI,
    CATEGORY_GOVERNANCE,
    CATEGORY_OBSERVABILITY,
    CATEGORY_INTEGRATION,
)

# Which category each known Django/Agent key belongs to (exported for the ISO doc).
KEY_CATEGORY: Dict[str, str] = {
    # INFRA
    "SOMABRAIN_URL": CATEGORY_INFRA,
    "SOMAFRACTALMEMORY_URL": CATEGORY_INFRA,
    "PROMETHEUS_URL": CATEGORY_INFRA,
    "VAULT_ADDR": CATEGORY_INFRA,
    "VAULT_MOUNT": CATEGORY_INFRA,
    "KAFKA_BOOTSTRAP_SERVERS": CATEGORY_INFRA,
    "MEM_HTTP_TIMEOUT": CATEGORY_INFRA,
    "MEM_WRITE_TIMEOUT_S": CATEGORY_INFRA,
    "MEM_RECALL_TIMEOUT_S": CATEGORY_INFRA,
    "MEM_HISTORY_TIMEOUT_S": CATEGORY_INFRA,
    "HTTP_CONNECT_TIMEOUT_S": CATEGORY_INFRA,
    "HTTP_READ_TIMEOUT_S": CATEGORY_INFRA,
    "HTTP_SLOW_READ_TIMEOUT_S": CATEGORY_INFRA,
    "CB_FAILURE_THRESHOLD": CATEGORY_INFRA,
    "CB_RESET_TIMEOUT_S": CATEGORY_INFRA,
    # SECURITY (Vault)
    "SOMABRAIN_MEMORY_HTTP_TOKEN": CATEGORY_SECURITY,
    "SOMA_API_TOKEN": CATEGORY_SECURITY,
    "VAULT_TOKEN": CATEGORY_SECURITY,
    "SECRET_KEY": CATEGORY_SECURITY,
    # MEMORY
    "MEM_EMBED_DIM": CATEGORY_MEMORY,
    "MEM_RECALL_TOP_K": CATEGORY_MEMORY,
    "MEM_PROXIMITY_TOP_K": CATEGORY_MEMORY,
    "MEM_HISTORY_LIMIT": CATEGORY_MEMORY,
    "MEM_CHAT_NAMESPACE": CATEGORY_MEMORY,
    "MEM_DEFAULT_KIND": CATEGORY_MEMORY,
    "MEM_DEFAULT_SALIENCE": CATEGORY_MEMORY,
    "MEM_DEFAULT_SOURCE": CATEGORY_MEMORY,
    "MEMORY_WAL_TOPIC": CATEGORY_MEMORY,
    "MEMORY_DEGRADED_TOPIC": CATEGORY_MEMORY,
    # LLM
    "LLM_CONNECT_TIMEOUT_S": CATEGORY_LLM,
    "LLM_READ_TIMEOUT_S": CATEGORY_LLM,
    "LLM_MAX_RETRIES": CATEGORY_LLM,
    "LLM_RETRY_BASE_DELAY_S": CATEGORY_LLM,
    "LLM_RETRY_BACKOFF_CAP_S": CATEGORY_LLM,
    "LLM_RETRY_AFTER_CAP_S": CATEGORY_LLM,
    "DEFAULT_VOICE_MODEL": CATEGORY_LLM,
    "DEFAULT_CHAT_MODEL_NAME": CATEGORY_LLM,
    "DEFAULT_UTIL_MODEL_NAME": CATEGORY_LLM,
    "DEFAULT_EMBED_MODEL_NAME": CATEGORY_LLM,
    "chat_model_name": CATEGORY_LLM,
    "util_model_name": CATEGORY_LLM,
    "embed_model_name": CATEGORY_LLM,
    # AGENT
    "TOOL_REWARD_SUCCESS": CATEGORY_AGENT,
    "TOOL_REWARD_FAILURE": CATEGORY_AGENT,
    "TOOL_MAX_ITERATIONS": CATEGORY_AGENT,
    "TOOL_EXEC_TIMEOUT_S": CATEGORY_AGENT,
    "TOOL_RESULT_MAX_CHARS": CATEGORY_AGENT,
    "TOOL_APPROVAL_TIMEOUT_S": CATEGORY_AGENT,
    "LOGIN_RATE_LIMIT": CATEGORY_SECURITY,
    "LOGIN_RATE_WINDOW": CATEGORY_SECURITY,
    "VOICE_MAX_AUDIO_BYTES": CATEGORY_AGENT,
    "VOICE_LLM_MAX_TOKENS": CATEGORY_AGENT,
    "MULTIMODAL_PROMPT_MAX_CHARS": CATEGORY_AGENT,
    "MULTIMODAL_IMAGE_TIMEOUT_S": CATEGORY_INFRA,
    "MULTIMODAL_DIAGRAM_TIMEOUT_S": CATEGORY_INFRA,
    "WS_STREAM_FLUSH_INTERVAL_S": CATEGORY_INFRA,
    "WS_STREAM_FLUSH_MAX_CHARS": CATEGORY_INFRA,
    # Temporal async cycle — schedule cadence (R-BEH: administrable behaviour).
    "SA01_SLEEP_CYCLE_HOURS": CATEGORY_INFRA,
    "SA01_JOB_ADVANCE_SECONDS": CATEGORY_INFRA,
    "SA01_OUTBOX_REPLAY_SECONDS": CATEGORY_INFRA,
    "OPA_URL": CATEGORY_INFRA,
    "LLM_API_URL": CATEGORY_INFRA,
    "IMAGE_GEN_URL": CATEGORY_INFRA,
    "DIAGRAM_URL": CATEGORY_INFRA,
    "MERMAID_CLI_URL": CATEGORY_INFRA,
    "WHISPER_URL": CATEGORY_INFRA,
    "WHISPER_API_URL": CATEGORY_INFRA,
    "KOKORO_URL": CATEGORY_INFRA,
    "KOKORO_TTS_URL": CATEGORY_INFRA,
    "AGENTVOICEVOX_BASE_URL": CATEGORY_INFRA,
    "KEYCLOAK_URL": CATEGORY_INFRA,
    "BRIDGE_BASE_URL": CATEGORY_INFRA,
    "SMTP_HOST": CATEGORY_INFRA,
    "SMTP_PORT": CATEGORY_INFRA,
    "ROUTER_URL": CATEGORY_INFRA,
    "GOOGLE_REDIRECT_URI": CATEGORY_INFRA,
    "GOOGLE_JAVASCRIPT_ORIGIN": CATEGORY_INFRA,
    "SOMABRAIN_CONTEXT_CONFIDENCE_DEFAULT": CATEGORY_AGENT,
    # Object storage / quality evaluation — operator parameters, not literals.
    "AWS_REGION": CATEGORY_INFRA,
    "AWS_S3_BUCKET": CATEGORY_INFRA,
    "QUALITY_EVAL_MODEL": CATEGORY_LLM,
    "memory_recall_enabled": CATEGORY_MEMORY,
    "memory_recall_memories_max_search": CATEGORY_MEMORY,
    "memory_recall_similarity_threshold": CATEGORY_MEMORY,
    # PERSONALITY
    "system_prompt": CATEGORY_PERSONALITY,
    "personality_traits": CATEGORY_PERSONALITY,
    "neuromodulator_baseline": CATEGORY_PERSONALITY,
    "learning_config": CATEGORY_PERSONALITY,
    # GOVERNANCE
    "AAAS_DEFAULT_TENANT_ID": CATEGORY_GOVERNANCE,
}


def category_of(key: str) -> str:
    """ISO category for a settings key (INFRA when unknown)."""
    return KEY_CATEGORY.get(key, CATEGORY_INFRA)


def capsule_settings_bucket(capsule: Any) -> Dict[str, Any]:
    """Return the categorized settings dict stored on a Capsule (copy)."""
    body: Mapping[str, Any] = {}
    if capsule is not None:
        raw = getattr(capsule, "persona_config", None)
        if isinstance(raw, Mapping):
            body = raw
        else:
            try:
                body = raw or {}
            except Exception:
                body = {}
    settings_block = body.get("settings") if isinstance(body, Mapping) else None
    if not isinstance(settings_block, Mapping):
        return {c: {} for c in CATEGORIES}
    out: Dict[str, Any] = {}
    for cat in CATEGORIES:
        section = settings_block.get(cat)
        out[cat] = dict(section) if isinstance(section, Mapping) else {}
    return out


def resolve_setting(
    key: str,
    *,
    capsule: Any = None,
    agent_id: Optional[str] = None,
    default: Any = None,
) -> Any:
    """Resolve one setting: Capsule → AgentSetting → Django settings → default."""
    cat = category_of(key)

    # 1. Capsule identity defaults (persona_config.settings).
    bucket = capsule_settings_bucket(capsule)
    section = bucket.get(cat) or {}
    if key in section and section[key] is not None:
        return section[key]

    # 2. AgentSetting ORM runtime override.
    if agent_id:
        try:
            from admin.core.models import AgentSetting

            row = AgentSetting.objects.filter(agent_id=agent_id, key=key).first()
            if row is not None and row.value is not None:
                return row.value
        except Exception:
            pass

    # 3. Django settings (infra authority).
    try:
        from django.conf import settings as django_settings

        value = getattr(django_settings, key, None)
        if value is not None and value != "":
            return value
    except Exception:
        pass

    return default


def save_capsule_setting(
    capsule: Any,
    key: str,
    value: Any,
) -> Any:
    """Persist one categorized setting onto the Capsule (persona_config.settings)."""
    if capsule is None:
        raise ValueError("capsule is required to save capsule-bound settings")
    cat = category_of(key)
    persona = getattr(capsule, "persona_config", None)
    if not isinstance(persona, Mapping):
        persona = {}
    persona = dict(persona)
    settings_block = dict(persona.get("settings") or {})
    section = dict(settings_block.get(cat) or {})
    section[key] = value
    settings_block[cat] = section
    persona["settings"] = settings_block
    capsule.persona_config = persona
    return capsule


def save_agent_setting(
    agent_id: str,
    key: str,
    value: Any,
    *,
    is_secret: bool = False,
) -> Any:
    """Persist one runtime override in the AgentSetting ORM (Vault owns secrets)."""
    from admin.core.models import AgentSetting

    obj, _ = AgentSetting.objects.update_or_create(
        agent_id=agent_id,
        key=key,
        defaults={"value": value, "is_secret": bool(is_secret)},
    )
    return obj


def merge_settings_model(
    *,
    capsule: Any = None,
    agent_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a flat settings dict for SettingsModel from Capsule + AgentSetting + Django."""
    flat: Dict[str, Any] = {}
    for key in KEY_CATEGORY:
        value = resolve_setting(key, capsule=capsule, agent_id=agent_id)
        if value is not None:
            flat[key] = value
    return flat


__all__ = [
    "CATEGORIES",
    "KEY_CATEGORY",
    "CATEGORY_INFRA",
    "CATEGORY_SECURITY",
    "CATEGORY_MEMORY",
    "CATEGORY_LLM",
    "CATEGORY_AGENT",
    "CATEGORY_PERSONALITY",
    "CATEGORY_UI",
    "CATEGORY_GOVERNANCE",
    "CATEGORY_OBSERVABILITY",
    "CATEGORY_INTEGRATION",
    "category_of",
    "capsule_settings_bucket",
    "resolve_setting",
    "save_capsule_setting",
    "save_agent_setting",
    "merge_settings_model",
]
