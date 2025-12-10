"""Settings section builders for external services and authentication."""

from typing import Any

from python.helpers import runtime
from python.helpers.providers import get_providers
from python.helpers.settings_types import (
    API_KEY_PLACEHOLDER,
    PASSWORD_PLACEHOLDER,
    SettingsField,
    SettingsSection,
)


def build_auth_section() -> SettingsSection:
    """Build the authentication settings section."""
    from services.common.unified_secret_manager import get_secret_manager

    _secrets = get_secret_manager()

    fields: list[SettingsField] = [
        {
            "id": "auth_login",
            "title": "UI Login",
            "description": "Set user name for web UI",
            "type": "text",
            "value": _secrets.get_credential("auth_login") or "",
        },
        {
            "id": "auth_password",
            "title": "UI Password",
            "type": "password",
            "value": PASSWORD_PLACEHOLDER if _secrets.get_credential("auth_password") else "",
        },
    ]

    if runtime.is_dockerized():
        fields.append(
            {
                "id": "root_password",
                "title": "root Password",
                "description": "Change linux root password.",
                "type": "password",
                "value": "",
            }
        )

    return {
        "id": "auth",
        "title": "Authentication",
        "description": "Web UI authentication settings.",
        "fields": fields,
        "tab": "external",
    }


def build_api_keys_section(settings: Any) -> SettingsSection:
    """Build the API keys settings section."""
    fields: list[SettingsField] = []
    providers_seen: set[str] = set()

    for p_type in ("chat", "embedding"):
        for provider in get_providers(p_type):
            pid_lower = provider["value"].lower()
            if pid_lower in providers_seen:
                continue
            providers_seen.add(pid_lower)
            key = settings["api_keys"].get(pid_lower, "")
            has_secret = isinstance(key, str) and key.strip() not in {"", "None"}
            fields.append(
                {
                    "id": f"api_key_{pid_lower}",
                    "title": provider["label"],
                    "type": "password",
                    "value": API_KEY_PLACEHOLDER if has_secret else "",
                }
            )

    return {
        "id": "api_keys",
        "title": "API Keys",
        "description": "API keys for model providers.",
        "fields": fields,
        "tab": "external",
    }


def build_secrets_section(settings: Any) -> SettingsSection:
    """Build the secrets management section."""
    from python.helpers.secrets import SecretsManager

    secrets_manager = SecretsManager.get_instance()
    try:
        secrets = secrets_manager.get_masked_secrets()
    except Exception:
        secrets = ""

    return {
        "id": "secrets",
        "title": "Secrets Management",
        "description": "Manage secrets and credentials.",
        "fields": [
            {
                "id": "variables",
                "title": "Variables Store",
                "description": "Non-sensitive variables in .env format.",
                "type": "textarea",
                "value": settings["variables"].strip(),
                "style": "height: 20em",
            },
            {
                "id": "secrets",
                "title": "Secrets Store",
                "description": "Secrets in .env format (masked).",
                "type": "textarea",
                "value": secrets,
                "style": "height: 20em",
            },
        ],
        "tab": "external",
    }


def build_external_api_section() -> SettingsSection:
    """Build the external API section."""
    return {
        "id": "external_api",
        "title": "External API",
        "description": "Agent Zero external API endpoints.",
        "fields": [
            {
                "id": "external_api_examples",
                "title": "API Examples",
                "type": "button",
                "value": "Show API Examples",
            }
        ],
        "tab": "external",
    }


def build_litellm_section(settings: Any) -> SettingsSection:
    """Build the LiteLLM global settings section."""
    import json

    def _dict_to_env(data_dict: dict) -> str:
        lines = []
        for key, value in data_dict.items():
            if isinstance(value, str):
                lines.append(f'{key}="{value.replace(chr(34), chr(92)+chr(34))}"')
            elif isinstance(value, (dict, list, bool)) or value is None:
                lines.append(f'{key}={json.dumps(value, separators=(",", ":"))}')
            else:
                lines.append(f"{key}={value}")
        return "\n".join(lines)

    return {
        "id": "litellm",
        "title": "LiteLLM Global Settings",
        "description": "Global LiteLLM parameters.",
        "fields": [
            {
                "id": "litellm_global_kwargs",
                "title": "LiteLLM global parameters",
                "description": "KEY=VALUE format.",
                "type": "textarea",
                "value": _dict_to_env(settings["litellm_global_kwargs"]),
                "style": "height: 12em",
            }
        ],
        "tab": "external",
    }
