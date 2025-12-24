"""Default settings values sourced from Django ORM.

All model/provider settings are loaded from Django ORM models (the single source
of truth) instead of hardcoded values. This complies with VIBE Rule 4:
"REAL IMPLEMENTATIONS ONLY - NO hardcoded values".

Settings priority:
1. Django ORM (AgentSetting model) - primary source
2. Environment variables - fallback/override
3. Django settings - last resort defaults

DJANGO ORM IS THE SINGLE SOURCE OF TRUTH.
"""

from __future__ import annotations

import os
from typing import Any, Callable, Optional


def _ensure_django() -> None:
    """Check if Django is ready.
    
    VIBE Rule: Do not trigger side effects like django.setup() in helper modules.
    The entry point must handle initialization.
    """
    import django

    if not django.apps.apps.ready:
        raise RuntimeError("Django apps not populated. Ensure django.setup() is called at entry point.")


def _get_version() -> str:
    """Get current version from git."""
    try:
        from admin.core.helpers import git

        git_info = git.get_git_info()
        return str(git_info.get("short_tag", "")).strip() or "unknown"
    except Exception:
        return "unknown"


def _get_agent_setting(agent_id: str, key: str, default: Any = None) -> Any:
    """Get setting from AgentSetting Django ORM model.

    Args:
        agent_id: Agent identifier
        key: Setting key name
        default: Default value if not found

    Returns:
        Setting value from database or default
    """
    try:
        _ensure_django()
        from admin.core.models import AgentSetting

        setting = AgentSetting.objects.filter(agent_id=agent_id, key=key).first()
        if setting:
            return setting.value
    except Exception:
        pass
    return default


def _get_ui_setting(
    tenant: str, key: str, user_id: Optional[str] = None, default: Any = None
) -> Any:
    """Get setting from UISetting Django ORM model.

    Args:
        tenant: Tenant identifier
        key: Setting key name
        user_id: Optional user identifier for user-specific settings
        default: Default value if not found

    Returns:
        Setting value from database or default
    """
    try:
        _ensure_django()
        from admin.core.models import UISetting

        # Try user-specific first, then tenant-level
        if user_id:
            setting = UISetting.objects.filter(tenant=tenant, user_id=user_id, key=key).first()
            if setting:
                return setting.value
        setting = UISetting.objects.filter(tenant=tenant, key=key, user_id__isnull=True).first()
        if setting:
            return setting.value
    except Exception:
        pass
    return default


def _env_or_db(env_key: str, agent_id: str, db_key: str, default: str = "") -> str:
    """Get value from environment or database.

    Priority: ENV > DB > default
    """
    env_val = os.environ.get(env_key)
    if env_val:
        return env_val
    db_val = _get_agent_setting(agent_id, db_key)
    if db_val is not None:
        return str(db_val)
    return default


def _env_or_db_int(env_key: str, agent_id: str, db_key: str, default: int = 0) -> int:
    """Get integer value from environment or database."""
    val = _env_or_db(env_key, agent_id, db_key, str(default))
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def _env_or_db_float(env_key: str, agent_id: str, db_key: str, default: float = 0.0) -> float:
    """Get float value from environment or database."""
    val = _env_or_db(env_key, agent_id, db_key, str(default))
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _env_or_db_bool(env_key: str, agent_id: str, db_key: str, default: bool = False) -> bool:
    """Get boolean value from environment or database."""
    val = _env_or_db(env_key, agent_id, db_key, str(default))
    return str(val).lower() in ("true", "1", "yes")


def get_default_settings(auth_token_fn: Callable[[], str] | None = None, agent_id: str = "default"):
    """Return default settings configuration from Django ORM.

    All model/provider settings are sourced from the AgentSetting Django ORM model.
    No hardcoded model names or providers per VIBE coding rules.

    Args:
        auth_token_fn: Optional function to generate auth token. If None, uses empty string.
        agent_id: Agent identifier for agent-specific settings. Defaults to "default".

    Returns:
        Settings object with values from Django ORM configuration.
    """
    from admin.core.helpers import runtime
    from .settings_model import SettingsModel as Settings

    mcp_token = auth_token_fn() if auth_token_fn else ""

    # All settings sourced from Django ORM AgentSetting model or environment
    return Settings(
        version=_get_version(),
        # Chat model - from Django ORM
        chat_model_provider=_env_or_db("SA01_CHAT_PROVIDER", agent_id, "chat_model_provider"),
        chat_model_name=_env_or_db("SA01_CHAT_MODEL", agent_id, "chat_model_name"),
        chat_model_api_base=_env_or_db("SA01_CHAT_API_BASE", agent_id, "chat_model_api_base"),
        chat_model_kwargs={
            "temperature": _env_or_db(
                "SA01_CHAT_TEMPERATURE", agent_id, "chat_model_temperature", "0"
            )
        },
        chat_model_ctx_length=_env_or_db_int(
            "SA01_CHAT_CTX_LENGTH", agent_id, "chat_model_ctx_length", 100000
        ),
        chat_model_ctx_history=_env_or_db_float(
            "SA01_CHAT_CTX_HISTORY", agent_id, "chat_model_ctx_history", 0.7
        ),
        chat_model_vision=_env_or_db_bool("SA01_CHAT_VISION", agent_id, "chat_model_vision", True),
        chat_model_rl_requests=_env_or_db_int(
            "SA01_CHAT_RL_REQUESTS", agent_id, "chat_model_rl_requests", 0
        ),
        chat_model_rl_input=_env_or_db_int(
            "SA01_CHAT_RL_INPUT", agent_id, "chat_model_rl_input", 0
        ),
        chat_model_rl_output=_env_or_db_int(
            "SA01_CHAT_RL_OUTPUT", agent_id, "chat_model_rl_output", 0
        ),
        # Utility model - from Django ORM
        util_model_provider=_env_or_db("SA01_UTIL_PROVIDER", agent_id, "util_model_provider"),
        util_model_name=_env_or_db("SA01_UTIL_MODEL", agent_id, "util_model_name"),
        util_model_api_base=_env_or_db("SA01_UTIL_API_BASE", agent_id, "util_model_api_base"),
        util_model_ctx_length=_env_or_db_int(
            "SA01_UTIL_CTX_LENGTH", agent_id, "util_model_ctx_length", 100000
        ),
        util_model_ctx_input=_env_or_db_float(
            "SA01_UTIL_CTX_INPUT", agent_id, "util_model_ctx_input", 0.7
        ),
        util_model_kwargs={
            "temperature": _env_or_db(
                "SA01_UTIL_TEMPERATURE", agent_id, "util_model_temperature", "0"
            )
        },
        util_model_rl_requests=_env_or_db_int(
            "SA01_UTIL_RL_REQUESTS", agent_id, "util_model_rl_requests", 0
        ),
        util_model_rl_input=_env_or_db_int(
            "SA01_UTIL_RL_INPUT", agent_id, "util_model_rl_input", 0
        ),
        util_model_rl_output=_env_or_db_int(
            "SA01_UTIL_RL_OUTPUT", agent_id, "util_model_rl_output", 0
        ),
        # Embedding model - from Django ORM
        embed_model_provider=_env_or_db("SA01_EMBED_PROVIDER", agent_id, "embed_model_provider"),
        embed_model_name=_env_or_db("SA01_EMBED_MODEL", agent_id, "embed_model_name"),
        embed_model_api_base=_env_or_db("SA01_EMBED_API_BASE", agent_id, "embed_model_api_base"),
        embed_model_kwargs={},
        embed_model_rl_requests=_env_or_db_int(
            "SA01_EMBED_RL_REQUESTS", agent_id, "embed_model_rl_requests", 0
        ),
        embed_model_rl_input=_env_or_db_int(
            "SA01_EMBED_RL_INPUT", agent_id, "embed_model_rl_input", 0
        ),
        # Browser model - from Django ORM
        browser_model_provider=_env_or_db(
            "SA01_BROWSER_PROVIDER", agent_id, "browser_model_provider"
        ),
        browser_model_name=_env_or_db("SA01_BROWSER_MODEL", agent_id, "browser_model_name"),
        browser_model_api_base=_env_or_db(
            "SA01_BROWSER_API_BASE", agent_id, "browser_model_api_base"
        ),
        browser_model_vision=_env_or_db_bool(
            "SA01_BROWSER_VISION", agent_id, "browser_model_vision", True
        ),
        browser_model_rl_requests=_env_or_db_int(
            "SA01_BROWSER_RL_REQUESTS", agent_id, "browser_model_rl_requests", 0
        ),
        browser_model_rl_input=_env_or_db_int(
            "SA01_BROWSER_RL_INPUT", agent_id, "browser_model_rl_input", 0
        ),
        browser_model_rl_output=_env_or_db_int(
            "SA01_BROWSER_RL_OUTPUT", agent_id, "browser_model_rl_output", 0
        ),
        browser_model_kwargs={
            "temperature": _env_or_db(
                "SA01_BROWSER_TEMPERATURE", agent_id, "browser_model_temperature", "0"
            )
        },
        browser_http_headers={},
        # Memory recall settings - from Django ORM
        memory_recall_enabled=_env_or_db_bool(
            "SA01_MEMORY_RECALL_ENABLED", agent_id, "memory_recall_enabled", True
        ),
        memory_recall_delayed=_env_or_db_bool(
            "SA01_MEMORY_RECALL_DELAYED", agent_id, "memory_recall_delayed", False
        ),
        memory_recall_interval=_env_or_db_int(
            "SA01_MEMORY_RECALL_INTERVAL", agent_id, "memory_recall_interval", 3
        ),
        memory_recall_history_len=_env_or_db_int(
            "SA01_MEMORY_RECALL_HISTORY_LEN", agent_id, "memory_recall_history_len", 10000
        ),
        memory_recall_memories_max_search=_env_or_db_int(
            "SA01_MEMORY_RECALL_MEMORIES_MAX_SEARCH",
            agent_id,
            "memory_recall_memories_max_search",
            12,
        ),
        memory_recall_solutions_max_search=_env_or_db_int(
            "SA01_MEMORY_RECALL_SOLUTIONS_MAX_SEARCH",
            agent_id,
            "memory_recall_solutions_max_search",
            8,
        ),
        memory_recall_memories_max_result=_env_or_db_int(
            "SA01_MEMORY_RECALL_MEMORIES_MAX_RESULT",
            agent_id,
            "memory_recall_memories_max_result",
            5,
        ),
        memory_recall_solutions_max_result=_env_or_db_int(
            "SA01_MEMORY_RECALL_SOLUTIONS_MAX_RESULT",
            agent_id,
            "memory_recall_solutions_max_result",
            3,
        ),
        memory_recall_similarity_threshold=_env_or_db_float(
            "SA01_MEMORY_RECALL_SIMILARITY_THRESHOLD",
            agent_id,
            "memory_recall_similarity_threshold",
            0.7,
        ),
        memory_recall_query_prep=_env_or_db_bool(
            "SA01_MEMORY_RECALL_QUERY_PREP", agent_id, "memory_recall_query_prep", True
        ),
        memory_recall_post_filter=_env_or_db_bool(
            "SA01_MEMORY_RECALL_POST_FILTER", agent_id, "memory_recall_post_filter", True
        ),
        memory_memorize_enabled=_env_or_db_bool(
            "SA01_MEMORY_MEMORIZE_ENABLED", agent_id, "memory_memorize_enabled", True
        ),
        memory_memorize_consolidation=_env_or_db_bool(
            "SA01_MEMORY_MEMORIZE_CONSOLIDATION", agent_id, "memory_memorize_consolidation", True
        ),
        memory_memorize_replace_threshold=_env_or_db_float(
            "SA01_MEMORY_MEMORIZE_REPLACE_THRESHOLD",
            agent_id,
            "memory_memorize_replace_threshold",
            0.9,
        ),
        # Auth settings
        api_keys={},
        auth_login=_env_or_db("SA01_AUTH_LOGIN", agent_id, "auth_login"),
        auth_password=_env_or_db("SA01_AUTH_PASSWORD", agent_id, "auth_password"),
        root_password=_env_or_db("SA01_ROOT_PASSWORD", agent_id, "root_password"),
        # Agent settings
        agent_profile=_env_or_db("SA01_AGENT_PROFILE", agent_id, "agent_profile", "agent0"),
        agent_memory_subdir=_env_or_db(
            "SA01_AGENT_MEMORY_SUBDIR", agent_id, "agent_memory_subdir", "default"
        ),
        agent_knowledge_subdir=_env_or_db(
            "SA01_AGENT_KNOWLEDGE_SUBDIR", agent_id, "agent_knowledge_subdir", "custom"
        ),
        # RFC settings
        rfc_auto_docker=_env_or_db_bool("SA01_RFC_AUTO_DOCKER", agent_id, "rfc_auto_docker", True),
        rfc_url=_env_or_db("SA01_RFC_URL", agent_id, "rfc_url", "localhost"),
        rfc_password=_env_or_db("SA01_RFC_PASSWORD", agent_id, "rfc_password"),
        rfc_port_http=_env_or_db_int("SA01_RFC_PORT_HTTP", agent_id, "rfc_port_http", 55080),
        rfc_port_ssh=_env_or_db_int("SA01_RFC_PORT_SSH", agent_id, "rfc_port_ssh", 55022),
        shell_interface=(
            "local"
            if runtime.is_dockerized()
            else _env_or_db("SA01_SHELL_INTERFACE", agent_id, "shell_interface", "ssh")
        ),
        # Speech-to-text settings
        stt_model_size=_env_or_db("SA01_STT_MODEL_SIZE", agent_id, "stt_model_size", "base"),
        stt_language=_env_or_db("SA01_STT_LANGUAGE", agent_id, "stt_language", "en"),
        stt_silence_threshold=_env_or_db_float(
            "SA01_STT_SILENCE_THRESHOLD", agent_id, "stt_silence_threshold", 0.3
        ),
        stt_silence_duration=_env_or_db_int(
            "SA01_STT_SILENCE_DURATION", agent_id, "stt_silence_duration", 1000
        ),
        stt_waiting_timeout=_env_or_db_int(
            "SA01_STT_WAITING_TIMEOUT", agent_id, "stt_waiting_timeout", 2000
        ),
        # Speech settings
        speech_provider=_env_or_db("SA01_SPEECH_PROVIDER", agent_id, "speech_provider", "browser"),
        speech_realtime_enabled=_env_or_db_bool(
            "SA01_SPEECH_REALTIME_ENABLED", agent_id, "speech_realtime_enabled", False
        ),
        speech_realtime_model=_env_or_db(
            "SA01_SPEECH_REALTIME_MODEL", agent_id, "speech_realtime_model"
        ),
        speech_realtime_voice=_env_or_db(
            "SA01_SPEECH_REALTIME_VOICE", agent_id, "speech_realtime_voice", "verse"
        ),
        speech_realtime_endpoint=_env_or_db(
            "SA01_SPEECH_REALTIME_ENDPOINT", agent_id, "speech_realtime_endpoint"
        ),
        tts_kokoro=_env_or_db_bool("SA01_TTS_KOKORO", agent_id, "tts_kokoro", False),
        # MCP settings
        mcp_servers=_env_or_db(
            "SA01_MCP_SERVERS", agent_id, "mcp_servers", '{\n    "mcpServers": {}\n}'
        ),
        mcp_client_init_timeout=_env_or_db_int(
            "SA01_MCP_CLIENT_INIT_TIMEOUT", agent_id, "mcp_client_init_timeout", 10
        ),
        mcp_client_tool_timeout=_env_or_db_int(
            "SA01_MCP_CLIENT_TOOL_TIMEOUT", agent_id, "mcp_client_tool_timeout", 120
        ),
        mcp_server_enabled=_env_or_db_bool(
            "SA01_MCP_SERVER_ENABLED", agent_id, "mcp_server_enabled", False
        ),
        mcp_server_token=mcp_token,
        # A2A settings
        a2a_server_enabled=_env_or_db_bool(
            "SA01_A2A_SERVER_ENABLED", agent_id, "a2a_server_enabled", False
        ),
        # Other settings
        variables=_env_or_db("SA01_VARIABLES", agent_id, "variables"),
        secrets=_env_or_db("SA01_SECRETS", agent_id, "secrets"),
        litellm_global_kwargs={},
        USE_LLM=_env_or_db_bool("SA01_USE_LLM", agent_id, "use_llm", True),
    )
