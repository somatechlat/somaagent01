"""Settings model for Agent Zero front‑end/runtime helpers.

This is a real, minimal Pydantic model that matches the fields used across the
python.helpers package (history, MCP server, runtime, etc.).  It supports both
attribute and dict-style access to keep backward compatibility with existing
call sites.
"""

from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, Field


def _dj(name: str, default: Any = None) -> Any:
    """Resolve one tunable from Django settings (authority), else schema default."""
    try:
        from django.conf import settings

        value = getattr(settings, name, None)
        if value is not None and value != "":
            return value
    except Exception:
        pass
    return default


class SettingsModel(BaseModel):
    # Core identity/versioning
    """Settingsmodel class implementation."""

    version: str = "unknown"

    # Chat / util / embed model settings — defaults from Django settings / env
    # (SA01_DEFAULT_*). Stored per-agent in the agent settings model at runtime.
    chat_model_provider: str = Field(
        default_factory=lambda: _dj("DEFAULT_CHAT_MODEL_PROVIDER", "openrouter")
    )
    chat_model_name: str = Field(default_factory=lambda: _dj("DEFAULT_CHAT_MODEL_NAME", ""))
    chat_model_api_base: str = ""
    chat_model_kwargs: Dict[str, Any] = {}
    chat_model_ctx_length: int = Field(
        default_factory=lambda: int(_dj("DEFAULT_CHAT_CTX_LENGTH", 100000))
    )
    chat_model_ctx_history: float = Field(
        default_factory=lambda: float(_dj("DEFAULT_CHAT_CTX_HISTORY", 0.7))
    )
    chat_model_vision: bool = True
    chat_model_rl_requests: int = 0
    chat_model_rl_input: int = 0
    chat_model_rl_output: int = 0

    util_model_provider: str = Field(
        default_factory=lambda: _dj("DEFAULT_UTIL_MODEL_PROVIDER", "openrouter")
    )
    util_model_name: str = Field(default_factory=lambda: _dj("DEFAULT_UTIL_MODEL_NAME", ""))
    util_model_api_base: str = ""
    util_model_ctx_length: int = Field(
        default_factory=lambda: int(_dj("DEFAULT_UTIL_CTX_LENGTH", 100000))
    )
    util_model_ctx_input: float = Field(
        default_factory=lambda: float(_dj("DEFAULT_UTIL_CTX_INPUT", 0.7))
    )
    util_model_kwargs: Dict[str, Any] = {}
    util_model_rl_requests: int = 0
    util_model_rl_input: int = 0
    util_model_rl_output: int = 0

    embed_model_provider: str = Field(
        default_factory=lambda: _dj("DEFAULT_EMBED_MODEL_PROVIDER", "huggingface")
    )
    embed_model_name: str = Field(default_factory=lambda: _dj("DEFAULT_EMBED_MODEL_NAME", ""))
    embed_model_api_base: str = ""
    embed_model_kwargs: Dict[str, Any] = {}
    embed_model_rl_requests: int = 0
    embed_model_rl_input: int = 0
    embed_model_rl_output: int = 0

    # Browser / tool model settings
    browser_model_provider: str = Field(
        default_factory=lambda: _dj("DEFAULT_CHAT_MODEL_PROVIDER", "openrouter")
    )
    browser_model_name: str = Field(default_factory=lambda: _dj("DEFAULT_CHAT_MODEL_NAME", ""))
    browser_model_api_base: str = ""
    browser_model_vision: bool = True
    browser_model_rl_requests: int = 0
    browser_model_rl_input: int = 0
    browser_model_rl_output: int = 0
    browser_model_kwargs: Dict[str, Any] = {}
    browser_http_headers: Dict[str, str] = {}

    # Memory / recall controls — Django settings MEM_* is the authority.
    memory_recall_enabled: bool = Field(default_factory=lambda: _dj("MEM_RECALL_ENABLED", True))
    memory_recall_delayed: bool = Field(default_factory=lambda: _dj("MEM_RECALL_DELAYED", False))
    memory_recall_interval: int = Field(default_factory=lambda: int(_dj("MEM_HISTORY_LIMIT", 20)))
    memory_recall_history_len: int = Field(
        default_factory=lambda: int(_dj("MEM_RECALL_HISTORY_LEN", 10000))
    )
    memory_recall_memories_max_search: int = Field(
        default_factory=lambda: int(_dj("MEM_RECALL_TOP_K", 8))
    )
    memory_recall_solutions_max_search: int = Field(
        default_factory=lambda: int(_dj("MEM_PROXIMITY_TOP_K", 10))
    )
    memory_recall_memories_max_result: int = Field(
        default_factory=lambda: int(_dj("MEM_RECALL_TOP_K", 8))
    )
    memory_recall_solutions_max_result: int = Field(
        default_factory=lambda: int(_dj("MEM_PROXIMITY_TOP_K", 10))
    )
    memory_recall_similarity_threshold: float = Field(
        default_factory=lambda: float(_dj("MEM_SIMILARITY_THRESHOLD", 0.7))
    )
    memory_recall_query_prep: bool = Field(
        default_factory=lambda: _dj("MEM_RECALL_QUERY_PREP", True)
    )
    memory_recall_post_filter: bool = Field(
        default_factory=lambda: _dj("MEM_RECALL_POST_FILTER", True)
    )
    memory_memorize_enabled: bool = Field(default_factory=lambda: _dj("MEM_MEMORIZE_ENABLED", True))
    memory_memorize_consolidation: bool = Field(
        default_factory=lambda: _dj("MEM_MEMORIZE_CONSOLIDATION", True)
    )
    memory_memorize_replace_threshold: float = Field(
        default_factory=lambda: float(_dj("MEM_REPLACE_THRESHOLD", 0.9))
    )

    # Auth. `auth_login` is a username, not a credential.
    #
    # There are deliberately no password / api-key / token fields on this
    # model. `api_keys`, `auth_password`, `root_password`, `rfc_password`,
    # `mcp_server_token` and `secrets` used to live here and were filled from
    # the AgentSetting table — making Postgres a second secret store. None of
    # them was ever read: provider keys go through
    # `UnifiedSecretManager.get_provider_key()`, the RFC password through
    # `runtime._get_rfc_password()`, and the MCP token was generated and
    # dropped. A field that holds a credential and is never read is still a
    # credential the day this model is serialised, so the fields are gone
    # rather than left empty (VIBE Rule 164).
    auth_login: str = ""

    # Agent profile
    agent_profile: str = Field(default_factory=lambda: str(_dj("AGENT_PROFILE", "agent0")))
    agent_memory_subdir: str = Field(
        default_factory=lambda: str(_dj("AGENT_MEMORY_SUBDIR", "default"))
    )
    agent_knowledge_subdir: str = Field(
        default_factory=lambda: str(_dj("AGENT_KNOWLEDGE_SUBDIR", "custom"))
    )

    # RFC / Docker tunnel defaults. Topology only — the RFC password is a
    # credential and is read from Vault at use by `runtime._get_rfc_password`.
    rfc_auto_docker: bool = Field(default_factory=lambda: _dj("RFC_AUTO_DOCKER", True))
    rfc_url: str = Field(default_factory=lambda: str(_dj("RFC_URL", "localhost")))
    rfc_port_http: int = Field(default_factory=lambda: int(_dj("RFC_PORT_HTTP", 55080)))
    rfc_port_ssh: int = Field(default_factory=lambda: int(_dj("RFC_PORT_SSH", 55022)))

    # Shell selection
    shell_interface: str = "local"

    # Speech / audio settings
    stt_model_size: str = Field(default_factory=lambda: str(_dj("STT_MODEL_SIZE", "base")))
    stt_language: str = Field(default_factory=lambda: str(_dj("STT_LANGUAGE", "en")))
    stt_silence_threshold: float = Field(
        default_factory=lambda: float(_dj("STT_SILENCE_THRESHOLD", 0.3))
    )
    stt_silence_duration: int = Field(
        default_factory=lambda: int(_dj("STT_SILENCE_DURATION", 1000))
    )
    stt_waiting_timeout: int = Field(default_factory=lambda: int(_dj("STT_WAITING_TIMEOUT", 2000)))
    speech_provider: str = "browser"
    speech_realtime_enabled: bool = False
    speech_realtime_model: str = Field(default_factory=lambda: _dj("SPEECH_REALTIME_MODEL", ""))
    speech_realtime_voice: str = Field(default_factory=lambda: _dj("SPEECH_REALTIME_VOICE", ""))
    speech_realtime_endpoint: str = Field(
        default_factory=lambda: _dj("SPEECH_REALTIME_ENDPOINT", "")
    )
    tts_kokoro: bool = False

    # Service endpoints. Every deployment URL resolves here; nothing in the
    # codebase may name a host. A URL a caller invents is a URL an operator
    # cannot change and a reviewer cannot see.
    service_somabrain_url: str = Field(default_factory=lambda: str(_dj("SOMABRAIN_URL", "")))
    service_somafractalmemory_url: str = Field(
        default_factory=lambda: str(_dj("SOMAFRACTALMEMORY_URL", ""))
    )
    service_opa_url: str = Field(default_factory=lambda: str(_dj("OPA_URL", "")))
    service_llm_api_url: str = Field(default_factory=lambda: str(_dj("LLM_API_URL", "")))
    service_image_gen_url: str = Field(default_factory=lambda: str(_dj("IMAGE_GEN_URL", "")))
    service_diagram_url: str = Field(default_factory=lambda: str(_dj("DIAGRAM_URL", "")))
    service_mermaid_cli_url: str = Field(
        default_factory=lambda: str(_dj("MERMAID_CLI_URL", ""))
    )
    service_whisper_url: str = Field(default_factory=lambda: str(_dj("WHISPER_URL", "")))
    service_whisper_api_url: str = Field(
        default_factory=lambda: str(_dj("WHISPER_API_URL", ""))
    )
    service_kokoro_url: str = Field(default_factory=lambda: str(_dj("KOKORO_URL", "")))
    service_kokoro_tts_url: str = Field(
        default_factory=lambda: str(_dj("KOKORO_TTS_URL", ""))
    )
    service_agentvoicevox_base_url: str = Field(
        default_factory=lambda: str(_dj("AGENTVOICEVOX_BASE_URL", ""))
    )
    service_keycloak_url: str = Field(default_factory=lambda: str(_dj("KEYCLOAK_URL", "")))
    service_bridge_base_url: str = Field(
        default_factory=lambda: str(_dj("BRIDGE_BASE_URL", ""))
    )
    service_prometheus_url: str = Field(
        default_factory=lambda: str(_dj("PROMETHEUS_URL", ""))
    )
    service_vault_addr: str = Field(default_factory=lambda: str(_dj("VAULT_ADDR", "")))
    service_google_redirect_uri: str = Field(
        default_factory=lambda: str(_dj("GOOGLE_REDIRECT_URI", ""))
    )
    service_google_javascript_origin: str = Field(
        default_factory=lambda: str(_dj("GOOGLE_JAVASCRIPT_ORIGIN", ""))
    )
    service_kafka_bootstrap_servers: str = Field(
        default_factory=lambda: str(_dj("KAFKA_BOOTSTRAP_SERVERS", ""))
    )
    service_smtp_host: str = Field(default_factory=lambda: str(_dj("SMTP_HOST", "")))
    service_smtp_port: str = Field(default_factory=lambda: str(_dj("SMTP_PORT", "")))

    # AuthN / login hardening. Tunable behaviour, not a literal at the gate.
    login_rate_limit: int = Field(
        default_factory=lambda: int(_dj("LOGIN_RATE_LIMIT", 10))
    )
    login_rate_window: int = Field(
        default_factory=lambda: int(_dj("LOGIN_RATE_WINDOW", 60))
    )

    # Voice payload ceiling. A size limit that lives in source cannot be
    # raised for a deployment that accepts longer clips.
    voice_max_audio_bytes: int = Field(
        default_factory=lambda: int(_dj("VOICE_MAX_AUDIO_BYTES", 10 * 1024 * 1024))
    )
    voice_llm_max_tokens: int = Field(
        default_factory=lambda: int(_dj("VOICE_LLM_MAX_TOKENS", 150))
    )

    # Multimodal request bounds.
    multimodal_prompt_max_chars: int = Field(
        default_factory=lambda: int(_dj("MULTIMODAL_PROMPT_MAX_CHARS", 4000))
    )
    multimodal_image_timeout_s: float = Field(
        default_factory=lambda: float(_dj("MULTIMODAL_IMAGE_TIMEOUT_S", 60.0))
    )
    multimodal_diagram_timeout_s: float = Field(
        default_factory=lambda: float(_dj("MULTIMODAL_DIAGRAM_TIMEOUT_S", 30.0))
    )

    # Tool loop. Bounded execution of model tool calls: how many
    # model->tool->model rounds a turn may take, how long one tool may run,
    # and how much of a result goes back to the model.
    tool_max_iterations: int = Field(
        default_factory=lambda: int(_dj("TOOL_MAX_ITERATIONS", 8))
    )
    tool_exec_timeout_s: float = Field(
        default_factory=lambda: float(_dj("TOOL_EXEC_TIMEOUT_S", 30.0))
    )
    tool_result_max_chars: int = Field(
        default_factory=lambda: int(_dj("TOOL_RESULT_MAX_CHARS", 12000))
    )
    tool_approval_timeout_s: float = Field(
        default_factory=lambda: float(_dj("TOOL_APPROVAL_TIMEOUT_S", 120.0))
    )

    # WebSocket stream coalescing. Tokens are buffered and flushed together;
    # both values must stay far below human perception (~100ms).
    ws_stream_flush_interval_s: float = Field(
        default_factory=lambda: float(_dj("WS_STREAM_FLUSH_INTERVAL_S", 0.02))
    )
    ws_stream_flush_max_chars: int = Field(
        default_factory=lambda: int(_dj("WS_STREAM_FLUSH_MAX_CHARS", 512))
    )

    # MCP / A2A
    mcp_servers: str = Field(default_factory=lambda: str(_dj("MCP_SERVERS", '{"mcpServers": {}}')))
    mcp_client_init_timeout: int = Field(
        default_factory=lambda: int(_dj("MCP_CLIENT_INIT_TIMEOUT", 10))
    )
    mcp_client_tool_timeout: int = Field(
        default_factory=lambda: int(_dj("MCP_CLIENT_TOOL_TIMEOUT", 120))
    )
    mcp_server_enabled: bool = False
    a2a_server_enabled: bool = False

    # Misc runtime state. `variables` is agent state (names → text), not
    # credentials. There is deliberately no `secrets` field: a field by that
    # name in a settings store is a secret store, whatever its type. Real
    # secrets are in Vault (VIBE Rule 164).
    variables: str = ""
    litellm_global_kwargs: Dict[str, Any] = {}
    USE_LLM: bool = True

    class Config:
        """Config class implementation."""

        extra = "allow"

    def __getitem__(self, item: str) -> Any:
        """Execute getitem  .

        Args:
            item: The item.
        """

        return self.model_dump()[item]


__all__ = ["SettingsModel"]
