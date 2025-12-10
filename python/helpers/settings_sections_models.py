"""Settings section builders for LLM model configurations.

Contains: Chat Model, Utility Model, Embedding Model, Browser Model sections.
"""

from typing import Any, cast

from python.helpers.providers import get_providers
from python.helpers.settings_types import FieldOption, SettingsField, SettingsSection


def _dict_to_env(data_dict: dict[str, Any]) -> str:
    """Convert dict to .env format string."""
    import json

    lines = []
    for key, value in data_dict.items():
        if isinstance(value, str):
            escaped_value = value.replace('"', '\\"')
            lines.append(f'{key}="{escaped_value}"')
        elif isinstance(value, (dict, list, bool)) or value is None:
            lines.append(f'{key}={json.dumps(value, separators=(",", ":"))}')
        else:
            lines.append(f"{key}={value}")
    return "\n".join(lines)


def build_chat_model_section(settings: Any) -> SettingsSection:
    """Build the chat model settings section."""
    fields: list[SettingsField] = [
        {
            "id": "chat_model_provider",
            "title": "Chat model provider",
            "description": "Select provider for main chat model",
            "type": "select",
            "value": settings["chat_model_provider"],
            "options": cast(list[FieldOption], get_providers("chat")),
        },
        {
            "id": "chat_model_name",
            "title": "Chat model name",
            "description": "Exact name of model from selected provider",
            "type": "text",
            "value": settings["chat_model_name"],
        },
        {
            "id": "chat_model_api_base",
            "title": "Chat model API base URL",
            "description": "API base URL for main chat model. Leave empty for default.",
            "type": "text",
            "value": settings["chat_model_api_base"],
        },
        {
            "id": "chat_model_ctx_length",
            "title": "Chat model context length",
            "description": "Maximum tokens in context window.",
            "type": "number",
            "value": settings["chat_model_ctx_length"],
        },
        {
            "id": "chat_model_ctx_history",
            "title": "Context window for chat history",
            "description": "Portion of context for chat history.",
            "type": "range",
            "min": 0.01,
            "max": 1,
            "step": 0.01,
            "value": settings["chat_model_ctx_history"],
        },
        {
            "id": "chat_model_vision",
            "title": "Supports Vision",
            "description": "Model can see image attachments.",
            "type": "switch",
            "value": settings["chat_model_vision"],
        },
        {
            "id": "chat_model_rl_requests",
            "title": "Requests per minute limit",
            "description": "Set to 0 to disable.",
            "type": "number",
            "value": settings["chat_model_rl_requests"],
        },
        {
            "id": "chat_model_rl_input",
            "title": "Input tokens per minute limit",
            "type": "number",
            "value": settings["chat_model_rl_input"],
        },
        {
            "id": "chat_model_rl_output",
            "title": "Output tokens per minute limit",
            "type": "number",
            "value": settings["chat_model_rl_output"],
        },
        {
            "id": "chat_model_kwargs",
            "title": "Chat model additional parameters",
            "description": "LiteLLM parameters in KEY=VALUE format.",
            "type": "textarea",
            "value": _dict_to_env(settings["chat_model_kwargs"]),
        },
    ]
    return {
        "id": "chat_model",
        "title": "Chat Model",
        "description": "Main chat model settings",
        "fields": fields,
        "tab": "agent",
    }


def build_util_model_section(settings: Any) -> SettingsSection:
    """Build the utility model settings section."""
    fields: list[SettingsField] = [
        {
            "id": "util_model_provider",
            "title": "Utility model provider",
            "type": "select",
            "value": settings["util_model_provider"],
            "options": cast(list[FieldOption], get_providers("chat")),
        },
        {
            "id": "util_model_name",
            "title": "Utility model name",
            "type": "text",
            "value": settings["util_model_name"],
        },
        {
            "id": "util_model_api_base",
            "title": "Utility model API base URL",
            "type": "text",
            "value": settings["util_model_api_base"],
        },
        {
            "id": "util_model_rl_requests",
            "title": "Requests per minute limit",
            "type": "number",
            "value": settings["util_model_rl_requests"],
        },
        {
            "id": "util_model_rl_input",
            "title": "Input tokens per minute limit",
            "type": "number",
            "value": settings["util_model_rl_input"],
        },
        {
            "id": "util_model_rl_output",
            "title": "Output tokens per minute limit",
            "type": "number",
            "value": settings["util_model_rl_output"],
        },
        {
            "id": "util_model_kwargs",
            "title": "Utility model additional parameters",
            "type": "textarea",
            "value": _dict_to_env(settings["util_model_kwargs"]),
        },
    ]
    return {
        "id": "util_model",
        "title": "Utility model",
        "description": "Smaller model for utility tasks",
        "fields": fields,
        "tab": "agent",
    }


def build_embed_model_section(settings: Any, default_embed_name: str) -> SettingsSection:
    """Build the embedding model settings section."""
    fields: list[SettingsField] = [
        {
            "id": "embed_model_provider",
            "title": "Embedding model provider",
            "type": "select",
            "value": settings["embed_model_provider"],
            "options": cast(list[FieldOption], get_providers("embedding")),
        },
        {
            "id": "embed_model_name",
            "title": "Embedding model name",
            "type": "text",
            "value": settings["embed_model_name"],
        },
        {
            "id": "embed_model_api_base",
            "title": "Embedding model API base URL",
            "type": "text",
            "value": settings["embed_model_api_base"],
        },
        {
            "id": "embed_model_rl_requests",
            "title": "Requests per minute limit",
            "type": "number",
            "value": settings["embed_model_rl_requests"],
        },
        {
            "id": "embed_model_rl_input",
            "title": "Input tokens per minute limit",
            "type": "number",
            "value": settings["embed_model_rl_input"],
        },
        {
            "id": "embed_model_kwargs",
            "title": "Embedding model additional parameters",
            "type": "textarea",
            "value": _dict_to_env(settings["embed_model_kwargs"]),
        },
    ]
    return {
        "id": "embed_model",
        "title": "Embedding Model",
        "description": f"Default {default_embed_name} runs locally.",
        "fields": fields,
        "tab": "agent",
    }


def build_browser_model_section(settings: Any) -> SettingsSection:
    """Build the browser model settings section."""
    fields: list[SettingsField] = [
        {
            "id": "browser_model_provider",
            "title": "Web Browser model provider",
            "type": "select",
            "value": settings["browser_model_provider"],
            "options": cast(list[FieldOption], get_providers("chat")),
        },
        {
            "id": "browser_model_name",
            "title": "Web Browser model name",
            "type": "text",
            "value": settings["browser_model_name"],
        },
        {
            "id": "browser_model_api_base",
            "title": "Web Browser model API base URL",
            "type": "text",
            "value": settings["browser_model_api_base"],
        },
        {
            "id": "browser_model_vision",
            "title": "Use Vision",
            "type": "switch",
            "value": settings["browser_model_vision"],
        },
        {
            "id": "browser_model_rl_requests",
            "title": "Rate limit requests",
            "type": "number",
            "value": settings["browser_model_rl_requests"],
        },
        {
            "id": "browser_model_rl_input",
            "title": "Rate limit input",
            "type": "number",
            "value": settings["browser_model_rl_input"],
        },
        {
            "id": "browser_model_rl_output",
            "title": "Rate limit output",
            "type": "number",
            "value": settings["browser_model_rl_output"],
        },
        {
            "id": "browser_model_kwargs",
            "title": "Additional parameters",
            "type": "textarea",
            "value": _dict_to_env(settings["browser_model_kwargs"]),
        },
        {
            "id": "browser_http_headers",
            "title": "HTTP Headers",
            "type": "textarea",
            "value": _dict_to_env(settings["browser_http_headers"]),
        },
    ]
    return {
        "id": "browser_model",
        "title": "Web Browser Model",
        "description": "Settings for browser-use framework.",
        "fields": fields,
        "tab": "agent",
    }
