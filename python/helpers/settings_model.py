"""Pydantic ``BaseSettings`` model for Agent Zero configuration.

The original implementation used a large ``TypedDict`` (see ``settings.py``).
That approach works but provides no validation, default handling, or
environment‑variable integration.  This file introduces a ``SettingsModel``
subclass of ``pydantic.BaseSettings`` that mirrors the keys of the original
TypedDict while keeping backward‑compatible attribute access.

Only a representative subset of fields is defined explicitly – the rest are
captured via ``extra = "allow"`` so that the model can still load the full JSON
settings file without having to list every single key.  This makes the change
non‑breaking for existing code that accesses settings via ``settings["key"]``.

The model is used by ``python/helpers/settings.py`` to validate the JSON file
on load and to provide a ``SettingsModel`` instance that can be used with
attribute access (e.g. ``settings.chat_model_provider``).
"""

from __future__ import annotations

from typing import Any, Dict

try:
    # pydantic v2+: BaseSettings was moved to pydantic-settings
    from pydantic import Field
    from pydantic_settings import BaseSettings
except Exception:  # pragma: no cover - fallback for older environments
    from pydantic import BaseSettings, Field


class SettingsModel(BaseSettings):
    """Validated settings for the Agent Zero application.

    The fields below cover the most commonly used configuration options.  Any
    additional keys present in the JSON file are accepted (``extra = "allow"``)
    so the model remains compatible with the existing ``TypedDict`` schema.
    """

    # Core version information
    version: str = Field(default="0.0.0", description="Application version")

    # Chat model configuration
    chat_model_provider: str = Field(
        default="openai", description="Provider for the main chat model"
    )
    chat_model_name: str = Field(
        default="gpt-4o-mini", description="Model name for the main chat model"
    )
    chat_model_api_base: str | None = Field(
        default=None, description="Optional custom API base URL"
    )
    chat_model_kwargs: Dict[str, Any] = Field(default_factory=dict)
    chat_model_ctx_length: int = Field(default=8192)
    chat_model_ctx_history: float = Field(default=0.5)
    chat_model_vision: bool = Field(default=False)
    chat_model_rl_requests: int = Field(default=0)
    chat_model_rl_input: int = Field(default=0)
    chat_model_rl_output: int = Field(default=0)

    # Utility model configuration (mirrors chat model fields)
    util_model_provider: str = Field(default="openai", description="Provider for utility model")
    util_model_name: str = Field(default="gpt-4o-mini", description="Utility model name")
    util_model_api_base: str | None = Field(default=None)
    util_model_kwargs: Dict[str, Any] = Field(default_factory=dict)
    util_model_ctx_length: int = Field(default=4096)
    util_model_ctx_input: float = Field(default=0.5)
    util_model_rl_requests: int = Field(default=0)
    util_model_rl_input: int = Field(default=0)
    util_model_rl_output: int = Field(default=0)

    # Embedding model configuration
    embed_model_provider: str = Field(default="openai")
    embed_model_name: str = Field(default="text-embedding-3-large")
    embed_model_api_base: str | None = Field(default=None)
    embed_model_kwargs: Dict[str, Any] = Field(default_factory=dict)
    embed_model_rl_requests: int = Field(default=0)
    embed_model_rl_input: int = Field(default=0)

    # Browser model configuration
    browser_model_provider: str = Field(default="openai")
    browser_model_name: str = Field(default="gpt-4o-mini")
    browser_model_api_base: str | None = Field(default=None)
    browser_model_vision: bool = Field(default=False)
    browser_model_rl_requests: int = Field(default=0)
    browser_model_rl_input: int = Field(default=0)
    browser_model_rl_output: int = Field(default=0)
    browser_model_kwargs: Dict[str, Any] = Field(default_factory=dict)
    browser_http_headers: Dict[str, Any] = Field(default_factory=dict)

    # Authentication / UI login
    auth_login: str = Field(default="admin")
    auth_password: str = Field(default="admin")
    root_password: str | None = Field(default=None)

    # Miscellaneous flags (kept as a generic catch‑all)
    # Enable LLM usage by default in production. The legacy codebase sometimes
    # assumes LLMs are available; keep the default 'True' to avoid surprising
    # runtime errors when the settings file is missing or not yet persisted.
    USE_LLM: bool = Field(default=True)

    # API Keys storage
    api_keys: Dict[str, str] = Field(default_factory=dict)

    # LiteLLM global config
    litellm_global_kwargs: Dict[str, Any] = Field(default_factory=dict)

    # Agent configuration
    agent_profile: str = Field(default="default")
    agent_knowledge_subdir: str = Field(default="default")
    agent_memory_subdir: str = Field(default="default")

    # Memory configuration
    memory_recall_enabled: bool = Field(default=True)
    memory_recall_delayed: bool = Field(default=False)
    memory_recall_query_prep: bool = Field(default=False)
    memory_recall_post_filter: bool = Field(default=False)
    memory_recall_interval: int = Field(default=1)
    memory_recall_history_len: int = Field(default=1000)
    memory_recall_similarity_threshold: float = Field(default=0.5)
    memory_recall_memories_max_search: int = Field(default=20)
    memory_recall_memories_max_result: int = Field(default=5)
    memory_recall_solutions_max_search: int = Field(default=20)
    memory_recall_solutions_max_result: int = Field(default=5)
    memory_memorize_enabled: bool = Field(default=True)
    memory_memorize_consolidation: bool = Field(default=True)
    memory_memorize_replace_threshold: float = Field(default=0.8)

    # Dev fields
    shell_interface: str = Field(default="local")
    rfc_url: str = Field(default="")
    rfc_port_http: int = Field(default=8010)
    rfc_port_ssh: int = Field(default=2222)

    # Speech configuration
    speech_enabled: bool = Field(default=False)
    speech_provider: str = Field(default="google")
    speech_api_key: str = Field(default="")
    stt_model_size: str = Field(default="base")
    stt_language: str = Field(default="en")
    stt_silence_threshold: float = Field(default=500.0)
    stt_silence_duration: float = Field(default=0.3)
    stt_waiting_timeout: int = Field(default=10)
    stt_autorestart: bool = Field(default=False)
    speech_realtime_enabled: bool = Field(default=False)
    speech_realtime_model: str = Field(default="gpt-4o-realtime-preview-2024-10-01")
    speech_realtime_voice: str = Field(default="alloy")
    speech_realtime_endpoint: str = Field(default="")
    tts_model: str = Field(default="tts-1")
    tts_voice: str = Field(default="alloy")
    tts_kokoro: bool = Field(default=False)

    # Tunnel configuration
    tunnel_provider: str = Field(default="cloudflared")

    # MCP configuration
    mcp_server_enabled: bool = Field(default=False)
    mcp_servers: Any = Field(default_factory=dict)
    mcp_server_token: str = Field(default="")
    mcp_client_init_timeout: int = Field(default=30)
    mcp_client_request_timeout: int = Field(default=60)
    mcp_client_tool_timeout: int = Field(default=300)

    # A2A configuration
    a2a_enabled: bool = Field(default=False)
    a2a_server_enabled: bool = Field(default=False)
    a2a_peer_url: str = Field(default="")
    a2a_peer_token: str = Field(default="")

    # External API configuration
    external_api_examples: str = Field(default="")
    show_a2a_connection: bool = Field(default=False)

    # Variables
    variables: Any = Field(default_factory=dict)

    # Backup configuration
    auto_backup_enabled: bool = Field(default=False)
    backup_schedule: str = Field(default="0 2 * * *")
    backup_storage_path: str = Field(default="/backup")

    class Config:
        # Allow any extra keys from the historic JSON file.
        extra = "allow"

    # Provide dict‑style access for legacy code paths.
    def __getitem__(self, item: str) -> Any:  # pragma: no cover
        return getattr(self, item)

    def __setitem__(self, key: str, value: Any) -> None:  # pragma: no cover
        setattr(self, key, value)
