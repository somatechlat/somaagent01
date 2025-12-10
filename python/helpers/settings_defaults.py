"""Default settings values.

Contains the get_default_settings() function with all default configuration values.
"""

from python.helpers import runtime

from .settings_model import SettingsModel as Settings


def _get_version() -> str:
    """Get current version from git."""
    try:
        from python.helpers import git

        git_info = git.get_git_info()
        return str(git_info.get("short_tag", "")).strip() or "unknown"
    except Exception:
        return "unknown"


def get_default_settings(auth_token_fn=None) -> Settings:
    """Return default settings configuration.

    Args:
        auth_token_fn: Optional function to generate auth token. If None, uses empty string.
    """
    mcp_token = auth_token_fn() if auth_token_fn else ""

    return Settings(
        version=_get_version(),
        chat_model_provider="openrouter",
        chat_model_name="openai/gpt-4.1",
        chat_model_api_base="",
        chat_model_kwargs={"temperature": "0"},
        chat_model_ctx_length=100000,
        chat_model_ctx_history=0.7,
        chat_model_vision=True,
        chat_model_rl_requests=0,
        chat_model_rl_input=0,
        chat_model_rl_output=0,
        util_model_provider="openrouter",
        util_model_name="openai/gpt-4.1-mini",
        util_model_api_base="",
        util_model_ctx_length=100000,
        util_model_ctx_input=0.7,
        util_model_kwargs={"temperature": "0"},
        util_model_rl_requests=0,
        util_model_rl_input=0,
        util_model_rl_output=0,
        embed_model_provider="huggingface",
        embed_model_name="sentence-transformers/all-MiniLM-L6-v2",
        embed_model_api_base="",
        embed_model_kwargs={},
        embed_model_rl_requests=0,
        embed_model_rl_input=0,
        browser_model_provider="openrouter",
        browser_model_name="openai/gpt-4.1",
        browser_model_api_base="",
        browser_model_vision=True,
        browser_model_rl_requests=0,
        browser_model_rl_input=0,
        browser_model_rl_output=0,
        browser_model_kwargs={"temperature": "0"},
        browser_http_headers={},
        memory_recall_enabled=True,
        memory_recall_delayed=False,
        memory_recall_interval=3,
        memory_recall_history_len=10000,
        memory_recall_memories_max_search=12,
        memory_recall_solutions_max_search=8,
        memory_recall_memories_max_result=5,
        memory_recall_solutions_max_result=3,
        memory_recall_similarity_threshold=0.7,
        memory_recall_query_prep=True,
        memory_recall_post_filter=True,
        memory_memorize_enabled=True,
        memory_memorize_consolidation=True,
        memory_memorize_replace_threshold=0.9,
        api_keys={},
        auth_login="",
        auth_password="",
        root_password="",
        agent_profile="agent0",
        agent_memory_subdir="default",
        agent_knowledge_subdir="custom",
        rfc_auto_docker=True,
        rfc_url="localhost",
        rfc_password="",
        rfc_port_http=55080,
        rfc_port_ssh=55022,
        shell_interface="local" if runtime.is_dockerized() else "ssh",
        stt_model_size="base",
        stt_language="en",
        stt_silence_threshold=0.3,
        stt_silence_duration=1000,
        stt_waiting_timeout=2000,
        speech_provider="browser",
        speech_realtime_enabled=False,
        speech_realtime_model="gpt-4o-realtime-preview",
        speech_realtime_voice="verse",
        speech_realtime_endpoint="https://api.openai.com/v1/realtime/sessions",
        tts_kokoro=False,
        mcp_servers='{\n    "mcpServers": {}\n}',
        mcp_client_init_timeout=10,
        mcp_client_tool_timeout=120,
        mcp_server_enabled=False,
        mcp_server_token=mcp_token,
        a2a_server_enabled=False,
        variables="",
        secrets="",
        litellm_global_kwargs={},
        USE_LLM=True,
    )
