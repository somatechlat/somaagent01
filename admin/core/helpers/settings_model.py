"""Settings model for Agent Zero front‑end/runtime helpers.

This is a real, minimal Pydantic model that matches the fields used across the
python.helpers package (history, MCP server, runtime, etc.).  It supports both
attribute and dict-style access to keep backward compatibility with existing
call sites.
"""

from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel


class SettingsModel(BaseModel):
    # Core identity/versioning
    """Settingsmodel class implementation."""

    version: str = "unknown"

    # Chat / util / embed model settings
    chat_model_provider: str = "openrouter"
    chat_model_name: str = "xiaomi/mimo-v2-flash:free"
    chat_model_api_base: str = ""
    chat_model_kwargs: Dict[str, Any] = {}
    chat_model_ctx_length: int = 100000
    chat_model_ctx_history: float = 0.7
    chat_model_vision: bool = True
    chat_model_rl_requests: int = 0
    chat_model_rl_input: int = 0
    chat_model_rl_output: int = 0

    util_model_provider: str = "openrouter"
    util_model_name: str = "xiaomi/mimo-v2-flash:free"
    util_model_api_base: str = ""
    util_model_ctx_length: int = 100000
    util_model_ctx_input: float = 0.7
    util_model_kwargs: Dict[str, Any] = {}
    util_model_rl_requests: int = 0
    util_model_rl_input: int = 0
    util_model_rl_output: int = 0

    embed_model_provider: str = "huggingface"
    embed_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    embed_model_api_base: str = ""
    embed_model_kwargs: Dict[str, Any] = {}
    embed_model_rl_requests: int = 0
    embed_model_rl_input: int = 0
    embed_model_rl_output: int = 0

    # Browser / tool model settings
    browser_model_provider: str = "openrouter"
    browser_model_name: str = "openai/gpt-4.1"
    browser_model_api_base: str = ""
    browser_model_vision: bool = True
    browser_model_rl_requests: int = 0
    browser_model_rl_input: int = 0
    browser_model_rl_output: int = 0
    browser_model_kwargs: Dict[str, Any] = {}
    browser_http_headers: Dict[str, str] = {}

    # Memory / recall controls
    memory_recall_enabled: bool = True
    memory_recall_delayed: bool = False
    memory_recall_interval: int = 3
    memory_recall_history_len: int = 10000
    memory_recall_memories_max_search: int = 12
    memory_recall_solutions_max_search: int = 8
    memory_recall_memories_max_result: int = 5
    memory_recall_solutions_max_result: int = 3
    memory_recall_similarity_threshold: float = 0.7
    memory_recall_query_prep: bool = True
    memory_recall_post_filter: bool = True
    memory_memorize_enabled: bool = True
    memory_memorize_consolidation: bool = True
    memory_memorize_replace_threshold: float = 0.9

    # Credentials / auth
    api_keys: Dict[str, str] = {}
    auth_login: str = ""
    auth_password: str = ""
    root_password: str = ""

    # Agent profile
    agent_profile: str = "agent0"
    agent_memory_subdir: str = "default"
    agent_knowledge_subdir: str = "custom"

    # RFC / Docker tunnel defaults
    rfc_auto_docker: bool = True
    rfc_url: str = "localhost"
    rfc_password: str = ""
    rfc_port_http: int = 55080
    rfc_port_ssh: int = 55022

    # Shell selection
    shell_interface: str = "local"

    # Speech / audio settings
    stt_model_size: str = "base"
    stt_language: str = "en"
    stt_silence_threshold: float = 0.3
    stt_silence_duration: int = 1000
    stt_waiting_timeout: int = 2000
    speech_provider: str = "browser"
    speech_realtime_enabled: bool = False
    speech_realtime_model: str = "gpt-4o-realtime-preview"
    speech_realtime_voice: str = "verse"
    speech_realtime_endpoint: str = "https://api.openai.com/v1/realtime/sessions"
    tts_kokoro: bool = False

    # MCP / A2A
    mcp_servers: str = '{"mcpServers": {}}'
    mcp_client_init_timeout: int = 10
    mcp_client_tool_timeout: int = 120
    mcp_server_enabled: bool = False
    mcp_server_token: str = ""
    a2a_server_enabled: bool = False

    # Misc runtime state
    variables: str = ""
    secrets: str = ""
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
