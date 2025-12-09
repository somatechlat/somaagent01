# Standard library imports
import base64
import hashlib
import json
import subprocess
from typing import Any

# Third-party imports
from python.helpers import defer, git, runtime, whisper
from python.helpers.print_style import PrintStyle

# Local imports
from .secrets import SecretsManager
from .settings_model import SettingsModel as Settings

# Import types from extracted module
from .settings_types import (
    API_KEY_PLACEHOLDER,
    PASSWORD_PLACEHOLDER,
    FieldOption,
    SettingsField,
    SettingsOutput,
    SettingsSection,
)

# Import section builders from extracted modules
from .settings_sections_external import (
    build_api_keys_section,
    build_auth_section,
    build_external_api_section,
    build_litellm_section,
    build_secrets_section,
)
from .settings_sections_mcp import (
    build_a2a_section,
    build_mcp_client_section,
    build_mcp_server_section,
)
from .settings_sections_memory import build_memory_section
from .settings_sections_misc import (
    build_agent_section,
    build_backup_section,
    build_dev_section,
    build_speech_section,
)
from .settings_sections_models import (
    build_browser_model_section,
    build_chat_model_section,
    build_embed_model_section,
    build_util_model_section,
)


# ``PartialSettings`` kept for compatibility
class PartialSettings(Settings):
    pass


# File-based SETTINGS_FILE removed - using AgentSettingsStore (PostgreSQL + Vault)
_settings: Settings | None = None


def convert_out(settings: Settings) -> SettingsOutput:
    """Convert settings to UI output format.
    
    Delegates to section builders in settings_sections_* modules.
    """
    default_settings = get_default_settings()

    return {
        "sections": [
            build_agent_section(settings),
            build_chat_model_section(settings),
            build_util_model_section(settings),
            build_browser_model_section(settings),
            build_embed_model_section(settings, default_settings["embed_model_name"]),
            build_memory_section(settings),
            build_speech_section(settings),
            build_api_keys_section(settings),
            build_litellm_section(settings),
            build_secrets_section(settings),
            build_auth_section(),
            build_mcp_client_section(settings),
            build_mcp_server_section(settings),
            build_a2a_section(settings),
            build_external_api_section(),
            build_backup_section(),
            build_dev_section(settings),
        ]
    }


def convert_in(settings: dict) -> Settings:
    current = get_settings()
    for section in settings["sections"]:
        if "fields" in section:
            for field in section["fields"]:
                # Skip saving if value is a placeholder
                should_skip = (
                    field["value"] == PASSWORD_PLACEHOLDER or field["value"] == API_KEY_PLACEHOLDER
                )

                if not should_skip:
                    # Special handling for browser_http_headers
                    if field["id"] == "browser_http_headers" or field["id"].endswith("_kwargs"):
                        current[field["id"]] = _env_to_dict(field["value"])
                    elif field["id"].startswith("api_key_"):
                        provider = field["id"][len("api_key_") :]
                        if isinstance(current, dict):
                            existing = current.get("api_keys")
                        else:
                            existing = getattr(current, "api_keys", None)
                        if not isinstance(existing, dict):
                            existing = {}
                        existing[provider] = field["value"]
                        current["api_keys"] = existing
                    else:
                        current[field["id"]] = field["value"]
    return current


def get_settings() -> Settings:
    """Get settings from AgentSettingsStore (PostgreSQL + Vault)."""
    global _settings
    if not _settings:
        try:
            import asyncio

            from services.common.agent_settings_store import get_agent_settings_store

            store = get_agent_settings_store()

            async def _load():
                await store.ensure_schema()
                return await store.get_settings()

            try:
                loop = asyncio.get_running_loop()
                # Running in async context - use defaults, will be loaded async elsewhere
                _settings = get_default_settings()
            except RuntimeError:
                # No running loop - safe to run sync
                _settings = asyncio.run(_load())
        except Exception:
            _settings = None

    if not _settings:
        _settings = get_default_settings()
    norm = normalize_settings(_settings)
    return norm


def set_settings(settings: Settings, apply: bool = True):
    """Save settings to AgentSettingsStore (PostgreSQL + Vault)."""
    global _settings
    previous = _settings
    _settings = normalize_settings(settings)

    try:
        import asyncio

        from services.common.agent_settings_store import get_agent_settings_store

        store = get_agent_settings_store()

        async def _save():
            await store.ensure_schema()
            await store.set_settings(dict(_settings))

        try:
            loop = asyncio.get_running_loop()
            # Running in async context - schedule task
            asyncio.create_task(_save())
        except RuntimeError:
            # No running loop - safe to run sync
            asyncio.run(_save())
    except Exception as exc:
        import logging

        logging.getLogger(__name__).error(f"Failed to save settings: {exc}")

    if apply:
        _apply_settings(previous)


def set_settings_delta(delta: dict, apply: bool = True):
    current = get_settings()
    new = {**current, **delta}
    set_settings(new, apply)  # type: ignore


def normalize_settings(settings: Settings) -> Settings:
    # Work with plain dicts to avoid depending on pydantic BaseModel internals
    if hasattr(settings, "model_dump"):
        copy = settings.model_dump()
    elif isinstance(settings, dict):
        copy = dict(settings)
    else:
        try:
            copy = dict(settings)
        except Exception:
            copy = {}

    default_model = get_default_settings()
    default = (
        default_model.model_dump() if hasattr(default_model, "model_dump") else dict(default_model)
    )

    # adjust settings values to match current version if needed
    if "version" not in copy or copy["version"] != default["version"]:
        _adjust_to_version(copy, default)
        copy["version"] = default["version"]  # sync version

    # remove keys that are not in default
    keys_to_remove = [key for key in copy if key not in default]
    for key in keys_to_remove:
        del copy[key]

    # add missing keys and normalize types
    for key, value in default.items():
        if key not in copy:
            copy[key] = value
        else:
            try:
                copy[key] = type(value)(copy[key])  # type: ignore
                if isinstance(copy[key], str):
                    copy[key] = copy[key].strip()  # strip strings
            except (ValueError, TypeError):
                copy[key] = value  # make default instead

    # mcp server token is set automatically
    copy["mcp_server_token"] = create_auth_token()

    return copy


def _adjust_to_version(settings: Settings, default: Settings):
    # starting with 0.9, the default prompt subfolder for agent no. 0 is agent0
    # switch to agent0 if the old default is used from v0.8
    if "version" not in settings or settings["version"].startswith("v0.8"):
        if "agent_profile" not in settings or settings["agent_profile"] == "default":
            settings["agent_profile"] = "agent0"


# File-based storage removed - using AgentSettingsStore (PostgreSQL + Vault)


def _remove_sensitive_settings(settings: Settings):
    settings["api_keys"] = {}
    settings["auth_login"] = ""
    settings["auth_password"] = ""
    settings["rfc_password"] = ""
    settings["root_password"] = ""
    settings["mcp_server_token"] = ""
    settings["secrets"] = ""


def _write_sensitive_settings(settings: Settings):
    """Write sensitive settings to Vault via UnifiedSecretManager.

    Single source of truth - no .env files for secrets.
    """
    from services.common.unified_secret_manager import get_secret_manager

    secrets = get_secret_manager()

    # Save API keys to Vault
    for key, val in settings["api_keys"].items():
        if not isinstance(key, str):
            continue
        provider = key.strip()
        if provider.startswith("api_key_"):
            provider = provider[len("api_key_") :]
        if not provider:
            continue
        if not isinstance(val, str) or val.strip() in {"", "None", API_KEY_PLACEHOLDER}:
            continue
        secrets.set_provider_key(provider, val.strip())

    # Save credentials to Vault
    if settings.get("auth_login"):
        secrets.set_credential("auth_login", settings["auth_login"])
    if settings.get("auth_password") and settings["auth_password"] != PASSWORD_PLACEHOLDER:
        secrets.set_credential("auth_password", settings["auth_password"])
    if settings.get("rfc_password") and settings["rfc_password"] != PASSWORD_PLACEHOLDER:
        secrets.set_credential("rfc_password", settings["rfc_password"])
    if settings.get("root_password") and settings["root_password"] != PASSWORD_PLACEHOLDER:
        secrets.set_credential("root_password", settings["root_password"])
        set_root_password(settings["root_password"])


def get_default_settings() -> Settings:
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
        mcp_server_token=create_auth_token(),
        a2a_server_enabled=False,
        variables="",
        secrets="",
        litellm_global_kwargs={},
        USE_LLM=True,
    )


def _apply_settings(previous: Settings | None):
    global _settings
    if _settings:
        from agent import AgentContext
        from initialize import initialize_agent

        config = initialize_agent()
        for ctx in AgentContext._contexts.values():
            ctx.config = config  # reinitialize context config with new settings
            # apply config to agents
            agent = ctx.agent0
            while agent:
                agent.config = ctx.config
                agent = agent.get_data(agent.DATA_NAME_SUBORDINATE)

        # reload whisper model if necessary
        if not previous or _settings["stt_model_size"] != previous["stt_model_size"]:
            defer.DeferredTask().start_task(
                whisper.preload, _settings["stt_model_size"]
            )  # Async task ensures model preloading without blocking main thread

        # force memory reload on embedding model change
        if not previous or (
            _settings["embed_model_name"] != previous["embed_model_name"]
            or _settings["embed_model_provider"] != previous["embed_model_provider"]
            or _settings["embed_model_kwargs"] != previous["embed_model_kwargs"]
        ):
            from python.helpers.memory import reload as memory_reload

            memory_reload()

        # update mcp settings if necessary
        if not previous or _settings["mcp_servers"] != previous["mcp_servers"]:
            from python.helpers.mcp_handler import MCPConfig

            async def update_mcp_settings(mcp_servers: str):
                PrintStyle(background_color="black", font_color="white", padding=True).print(
                    "Updating MCP config..."
                )
                AgentContext.log_to_all(type="info", content="Updating MCP settings...", temp=True)

                mcp_config = MCPConfig.get_instance()
                try:
                    MCPConfig.update(mcp_servers)
                except Exception as e:
                    AgentContext.log_to_all(
                        type="error",
                        content=f"Failed to update MCP settings: {e}",
                        temp=False,
                    )
                    (
                        PrintStyle(background_color="red", font_color="black", padding=True).print(
                            "Failed to update MCP settings"
                        )
                    )
                    (
                        PrintStyle(background_color="black", font_color="red", padding=True).print(
                            f"{e}"
                        )
                    )

                PrintStyle(background_color="#6734C3", font_color="white", padding=True).print(
                    "Parsed MCP config:"
                )
                (
                    PrintStyle(background_color="#334455", font_color="white", padding=False).print(
                        mcp_config.model_dump_json()
                    )
                )
                AgentContext.log_to_all(
                    type="info", content="Finished updating MCP settings.", temp=True
                )

            defer.DeferredTask().start_task(
                update_mcp_settings, config.mcp_servers
            )  # Async task ensures MCP settings update without blocking main thread

        # update token in mcp server
        current_token = (
            create_auth_token()
        )  # Token generation uses environment variables with fallback to dotenv
        if not previous or current_token != previous["mcp_server_token"]:

            async def update_mcp_token(token: str):
                from python.helpers.mcp_server import DynamicMcpProxy

                DynamicMcpProxy.get_instance().reconfigure(token=token)

            defer.DeferredTask().start_task(
                update_mcp_token, current_token
            )  # Async task ensures MCP token update without blocking main thread

        # update token in a2a server
        if not previous or current_token != previous["mcp_server_token"]:

            async def update_a2a_token(token: str):
                from python.helpers.fasta2a_server import DynamicA2AProxy

                DynamicA2AProxy.get_instance().reconfigure(token=token)

            defer.DeferredTask().start_task(
                update_a2a_token, current_token
            )  # Async task ensures A2A token update without blocking main thread

        # Notify admin/UI when LLM is not enabled or chat model provider is not configured.
        try:
            llm_enabled = bool(_settings.get("USE_LLM", False))
            chat_provider = _settings.get("chat_model_provider", "").strip()
            chat_model = _settings.get("chat_model_name", "").strip()
            if not llm_enabled or not chat_provider or not chat_model:
                # Use neutral wording and rely on the existing notification transport
                AgentContext.log_to_all(
                    type="warning",
                    content=(
                        "Model provider not configured. Open Admin → Settings → Model and set a provider and API key to enable chat functionality."
                    ),
                    temp=True,
                )
        except Exception:
            # best-effort notification; do not raise during settings application
            pass


def _env_to_dict(data: str):
    result = {}
    for line in data.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        # If quoted, treat as string
        if value.startswith('"') and value.endswith('"'):
            result[key] = value[1:-1].replace('\\"', '"')  # Unescape quotes
        elif value.startswith("'") and value.endswith("'"):
            result[key] = value[1:-1].replace("\\'", "'")  # Unescape quotes
        else:
            # Not quoted, try JSON parse
            try:
                result[key] = json.loads(value)
            except (json.JSONDecodeError, ValueError):
                result[key] = value

    return result


def _dict_to_env(data_dict):
    lines = []
    for key, value in data_dict.items():
        if isinstance(value, str):
            # Quote strings and escape internal quotes
            escaped_value = value.replace('"', '\\"')
            lines.append(f'{key}="{escaped_value}"')
        elif isinstance(value, (dict, list, bool)) or value is None:
            # Serialize as unquoted JSON
            lines.append(f'{key}={json.dumps(value, separators=(",", ":"))}')
        else:
            # Numbers and other types as unquoted strings
            lines.append(f"{key}={value}")

    return "\n".join(lines)


def set_root_password(password: str):
    """Set root password in Docker container and save to Vault."""
    if not runtime.is_dockerized():
        raise Exception("root password can only be set in dockerized environments")
    _result = subprocess.run(
        ["chpasswd"],
        input=f"root:{password}".encode(),
        capture_output=True,
        check=True,
    )
    # Save to Vault
    from services.common.unified_secret_manager import get_secret_manager

    get_secret_manager().set_credential("root_password", password)


def get_runtime_config(set: Settings):
    if runtime.is_dockerized():
        return {
            "code_exec_ssh_enabled": set["shell_interface"] == "ssh",
            "code_exec_ssh_addr": "localhost",
            "code_exec_ssh_port": 22,
            "code_exec_ssh_user": "root",
        }
    else:
        host = set["rfc_url"]
        if "//" in host:
            host = host.split("//")[1]
        if ":" in host:
            host, port = host.split(":")
        if host.endswith("/"):
            host = host[:-1]
        return {
            "code_exec_ssh_enabled": set["shell_interface"] == "ssh",
            "code_exec_ssh_addr": host,
            "code_exec_ssh_port": set["rfc_port_ssh"],
            "code_exec_ssh_user": "root",
        }


def create_auth_token() -> str:
    """Create auth token using credentials from Vault."""
    from services.common.unified_secret_manager import get_secret_manager

    _auth_secrets = get_secret_manager()

    runtime_id = runtime.get_persistent_id()
    username = _auth_secrets.get_credential("auth_login") or ""
    password = _auth_secrets.get_credential("auth_password") or ""
    # use base64 encoding for a more compact token with alphanumeric chars
    hash_bytes = hashlib.sha256(f"{runtime_id}:{username}:{password}".encode()).digest()
    # encode as base64 and remove any non-alphanumeric chars (like +, /, =)
    b64_token = base64.urlsafe_b64encode(hash_bytes).decode().replace("=", "")
    return b64_token[:16]


def _get_version():
    try:
        git_info = git.get_git_info()
        return str(git_info.get("short_tag", "")).strip() or "unknown"
    except Exception:
        return "unknown"
