"""Settings section builders for speech, dev, agent config, and backup."""

from typing import Any

from python.helpers import files, runtime
from python.helpers.settings_types import PASSWORD_PLACEHOLDER, SettingsField, SettingsSection


def build_agent_section(settings: Any) -> SettingsSection:
    """Build the agent config settings section."""
    return {
        "id": "agent",
        "title": "Agent Config",
        "description": "Agent parameters.",
        "fields": [
            {
                "id": "agent_profile",
                "title": "Default agent profile",
                "description": "Subdirectory of /agents folder.",
                "type": "select",
                "value": settings["agent_profile"],
                "options": [
                    {"value": s, "label": s}
                    for s in files.get_subdirectories("agents")
                    if s != "_example"
                ],
            },
            {
                "id": "agent_knowledge_subdir",
                "title": "Knowledge subdirectory",
                "type": "select",
                "value": settings["agent_knowledge_subdir"],
                "options": [
                    {"value": s, "label": s}
                    for s in files.get_subdirectories("knowledge", exclude="default")
                ],
            },
        ],
        "tab": "agent",
    }


def build_speech_section(settings: Any) -> SettingsSection:
    """Build the speech settings section."""
    selected = settings["speech_provider"]
    fields: list[SettingsField] = [
        {
            "id": "speech_provider",
            "title": "Speech provider",
            "type": "select",
            "value": selected,
            "options": [
                {"value": "browser", "label": "Browser (built-in)"},
                {"value": "kokoro", "label": "Kokoro (server)"},
                {"value": "openai_realtime", "label": "Realtime (server)"},
            ],
        },
        {
            "id": "INGEST_OFFLOAD_THRESHOLD_MB",
            "title": "Ingestion Offload Threshold (MB)",
            "type": "number",
            "min": 1,
            "max": 512,
            "step": 1,
            "value": getattr(settings, "INGEST_OFFLOAD_THRESHOLD_MB", 5),
        },
        {
            "id": "stt_model_size",
            "title": "Speech-to-text model size",
            "type": "select",
            "value": settings["stt_model_size"],
            "options": [
                {"value": "tiny", "label": "Tiny (39M)"},
                {"value": "base", "label": "Base (74M)"},
                {"value": "small", "label": "Small (244M)"},
                {"value": "medium", "label": "Medium (769M)"},
                {"value": "large", "label": "Large (1.5B)"},
                {"value": "turbo", "label": "Turbo"},
            ],
        },
        {
            "id": "stt_language",
            "title": "Speech-to-text language code",
            "type": "text",
            "value": settings["stt_language"],
        },
        {
            "id": "stt_silence_threshold",
            "title": "Microphone silence threshold",
            "type": "range",
            "min": 0,
            "max": 1,
            "step": 0.01,
            "value": settings["stt_silence_threshold"],
        },
        {
            "id": "stt_silence_duration",
            "title": "Silence duration (ms)",
            "type": "text",
            "value": settings["stt_silence_duration"],
        },
        {
            "id": "stt_waiting_timeout",
            "title": "Waiting timeout (ms)",
            "type": "text",
            "value": settings["stt_waiting_timeout"],
        },
        {
            "id": "speech_realtime_enabled",
            "title": "Enable realtime speech",
            "type": "switch",
            "value": settings["speech_realtime_enabled"],
            "hidden": selected != "openai_realtime",
        },
        {
            "id": "speech_realtime_model",
            "title": "Realtime model",
            "type": "text",
            "value": settings["speech_realtime_model"],
            "hidden": selected != "openai_realtime",
        },
        {
            "id": "speech_realtime_voice",
            "title": "Realtime voice",
            "type": "text",
            "value": settings["speech_realtime_voice"],
            "hidden": selected != "openai_realtime",
        },
        {
            "id": "speech_realtime_endpoint",
            "title": "Realtime endpoint",
            "type": "text",
            "value": settings["speech_realtime_endpoint"],
            "hidden": selected != "openai_realtime",
        },
        {
            "id": "tts_kokoro",
            "title": "Enable Kokoro TTS",
            "type": "switch",
            "value": settings["tts_kokoro"],
            "hidden": selected != "kokoro",
        },
    ]
    return {
        "id": "speech",
        "title": "Speech",
        "description": "Voice transcription and synthesis.",
        "fields": fields,
        "tab": "agent",
    }


def build_dev_section(settings: Any) -> SettingsSection:
    """Build the development settings section."""
    from services.common.unified_secret_manager import get_secret_manager

    _secrets = get_secret_manager()

    fields: list[SettingsField] = [
        {
            "id": "shell_interface",
            "title": "Shell Interface",
            "type": "select",
            "value": settings["shell_interface"],
            "options": [
                {"value": "local", "label": "Local Python TTY"},
                {"value": "ssh", "label": "SSH"},
            ],
        },
    ]

    if runtime.is_development():
        fields.append(
            {
                "id": "rfc_url",
                "title": "RFC Destination URL",
                "type": "text",
                "value": settings["rfc_url"],
            }
        )

    fields.append(
        {
            "id": "rfc_password",
            "title": "RFC Password",
            "type": "password",
            "value": PASSWORD_PLACEHOLDER if _secrets.get_credential("rfc_password") else "",
        }
    )

    if runtime.is_development():
        fields.extend(
            [
                {
                    "id": "rfc_port_http",
                    "title": "RFC HTTP port",
                    "type": "text",
                    "value": settings["rfc_port_http"],
                },
                {
                    "id": "rfc_port_ssh",
                    "title": "RFC SSH port",
                    "type": "text",
                    "value": settings["rfc_port_ssh"],
                },
            ]
        )

    return {
        "id": "dev",
        "title": "Development",
        "description": "Development and RFC parameters.",
        "fields": fields,
        "tab": "developer",
    }


def build_backup_section() -> SettingsSection:
    """Build the backup & restore section."""
    return {
        "id": "backup_restore",
        "title": "Backup & Restore",
        "description": "Backup and restore data.",
        "fields": [
            {
                "id": "backup_create",
                "title": "Create Backup",
                "type": "button",
                "value": "Create Backup",
            },
            {
                "id": "backup_restore",
                "title": "Restore from Backup",
                "type": "button",
                "value": "Restore Backup",
            },
        ],
        "tab": "backup",
    }
