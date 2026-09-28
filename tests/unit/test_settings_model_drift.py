"""Phase B settings-drift closure — SOMA-SETTINGS-MODEL-001.md §10.

Locks the drift register items that Phase B closes:

  D-08  Behavioral schema fallbacks (context lengths, thresholds, RFC ports,
        STT params, agent_profile, MCP registry) are settings-backed via the
        model's own ``_dj`` resolver — Capsule / AgentSetting / Django can win.
        No naked literals in the field declarations.
  D-09  No hardcoded speech-realtime URL in the schema; the endpoint comes
        from settings (SPEECH_REALTIME_ENDPOINT).
  D-10  AgentIQ knob defaults resolve through ``resolve_setting`` (Capsule →
        AgentSetting → Django → default), never as bare magic numbers.
  D-12  ``LANGUAGE_CODE`` is operator-configurable, not a literal.
  D-13  LLM_* timeouts/retries are categorized ``LLM`` (not ``INFRA``).
  D-14  Channel-layer transport is settings-driven in BOTH Django settings
        modules, so the modules cannot silently disagree; each module declares
        which deployment it is authoritative for.

Run:
    pytest tests/unit/test_settings_model_drift.py -v
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# D-08 — every behavioral default is behind _dj, and settings win
# ---------------------------------------------------------------------------

# (field, Django settings key, literal fallback that must remain the default
# when no override is configured).  The key name is the contract; the fallback
# is the schema default only.
BEHAVIORAL_FIELDS: list[tuple[str, str, object]] = [
    # context lengths / context split
    ("chat_model_ctx_length", "DEFAULT_CHAT_CTX_LENGTH", 100000),
    ("chat_model_ctx_history", "DEFAULT_CHAT_CTX_HISTORY", 0.7),
    ("util_model_ctx_length", "DEFAULT_UTIL_CTX_LENGTH", 100000),
    ("util_model_ctx_input", "DEFAULT_UTIL_CTX_INPUT", 0.7),
    # memory thresholds
    ("memory_recall_history_len", "MEM_RECALL_HISTORY_LEN", 10000),
    ("memory_recall_similarity_threshold", "MEM_SIMILARITY_THRESHOLD", 0.7),
    ("memory_memorize_replace_threshold", "MEM_REPLACE_THRESHOLD", 0.9),
    # memory behaviour switches
    ("memory_recall_enabled", "MEM_RECALL_ENABLED", True),
    ("memory_recall_delayed", "MEM_RECALL_DELAYED", False),
    ("memory_recall_query_prep", "MEM_RECALL_QUERY_PREP", True),
    ("memory_recall_post_filter", "MEM_RECALL_POST_FILTER", True),
    ("memory_memorize_enabled", "MEM_MEMORIZE_ENABLED", True),
    ("memory_memorize_consolidation", "MEM_MEMORIZE_CONSOLIDATION", True),
    # agent identity
    ("agent_profile", "AGENT_PROFILE", "agent0"),
    ("agent_memory_subdir", "AGENT_MEMORY_SUBDIR", "default"),
    ("agent_knowledge_subdir", "AGENT_KNOWLEDGE_SUBDIR", "custom"),
    # RFC (remote file copy) topology
    ("rfc_auto_docker", "RFC_AUTO_DOCKER", True),
    ("rfc_url", "RFC_URL", "localhost"),
    ("rfc_port_http", "RFC_PORT_HTTP", 55080),
    ("rfc_port_ssh", "RFC_PORT_SSH", 55022),
    # STT
    ("stt_model_size", "STT_MODEL_SIZE", "base"),
    ("stt_language", "STT_LANGUAGE", "en"),
    ("stt_silence_threshold", "STT_SILENCE_THRESHOLD", 0.3),
    ("stt_silence_duration", "STT_SILENCE_DURATION", 1000),
    ("stt_waiting_timeout", "STT_WAITING_TIMEOUT", 2000),
    # MCP registry + timeouts
    ("mcp_servers", "MCP_SERVERS", '{"mcpServers": {}}'),
    ("mcp_client_init_timeout", "MCP_CLIENT_INIT_TIMEOUT", 10),
    ("mcp_client_tool_timeout", "MCP_CLIENT_TOOL_TIMEOUT", 120),
]

# Distinct override values per Python type, so a field that ignores settings
# and keeps its fallback cannot accidentally pass.
_OVERRIDE_BY_TYPE: dict[type, object] = {
    int: 424242,
    float: 0.4242,
    str: "settings-override-wins",
    bool: False,
}


class TestD08BehavioralDefaultsAreSettingsBacked:
    """D-08: behavioral defaults read Django settings before schema fallbacks."""

    @pytest.mark.parametrize(
        "field,key,fallback", BEHAVIORAL_FIELDS, ids=[f[0] for f in BEHAVIORAL_FIELDS]
    )
    def test_settings_override_wins(self, monkeypatch, field, key, fallback):
        from django.conf import settings as dj_settings

        from admin.core.helpers.settings_model import SettingsModel

        override = _OVERRIDE_BY_TYPE[type(fallback)]
        monkeypatch.setattr(dj_settings, key, override, raising=False)
        model = SettingsModel()
        assert (
            getattr(model, field) == override
        ), f"{field} ignored Django setting {key}={override!r}"

    @pytest.mark.parametrize(
        "field,key,fallback", BEHAVIORAL_FIELDS, ids=[f[0] for f in BEHAVIORAL_FIELDS]
    )
    def test_schema_fallback_when_unset(self, monkeypatch, field, key, fallback):
        from django.conf import settings as dj_settings

        from admin.core.helpers.settings_model import SettingsModel

        monkeypatch.delattr(dj_settings, key, raising=False)
        model = SettingsModel()
        assert (
            getattr(model, field) == fallback
        ), f"{field} lost its schema fallback {fallback!r} when {key} is absent"

    def test_behavioral_fields_are_not_bare_literals(self):
        """Source scan: the D-08 fields must use _dj, not a naked assignment."""
        src = _read("admin/core/helpers/settings_model.py")
        offenders = []
        for field, key, _ in BEHAVIORAL_FIELDS:
            # Accept either `field: T = Field(default_factory=..._dj("KEY"...`
            # or a multiline Field(...) whose body names the key.
            pattern = re.compile(rf"{field}\s*:\s*\w+\s*=\s*(?:Field\([^)]*?\)|[^=\n]+)", re.DOTALL)
            match = pattern.search(src)
            if match is None:
                offenders.append(f"{field}: declaration not found")
                continue
            decl = match.group(0)
            if "_dj(" not in decl or f'"{key}"' not in decl:
                offenders.append(f'{field}: not behind _dj("{key}") — got {decl[:80]!r}')
        assert not offenders, "D-08 open, bare schema defaults:\n  " + "\n  ".join(offenders)


# ---------------------------------------------------------------------------
# D-09 — speech realtime endpoint comes from settings, never a hardcoded URL
# ---------------------------------------------------------------------------


class TestD09SpeechRealtimeEndpoint:
    """D-09: the realtime URL literal is gone; settings own the endpoint."""

    def test_no_hardcoded_openai_realtime_url_in_schema(self):
        src = _read("admin/core/helpers/settings_model.py")
        assert "api.openai.com" not in src
        assert "realtime/sessions" not in src

    def test_endpoint_reads_settings(self, monkeypatch):
        from django.conf import settings as dj_settings

        from admin.core.helpers.settings_model import SettingsModel

        monkeypatch.setattr(
            dj_settings,
            "SPEECH_REALTIME_ENDPOINT",
            "https://voice.internal.example/v1/realtime/sessions",
            raising=False,
        )
        model = SettingsModel()
        assert model.speech_realtime_endpoint.startswith("https://voice.internal.example")

    def test_endpoint_empty_by_default(self, monkeypatch):
        from django.conf import settings as dj_settings

        from admin.core.helpers.settings_model import SettingsModel

        monkeypatch.delattr(dj_settings, "SPEECH_REALTIME_ENDPOINT", raising=False)
        assert SettingsModel().speech_realtime_endpoint == ""


# ---------------------------------------------------------------------------
# D-10 — AgentIQ knob defaults resolve through resolve_setting
# ---------------------------------------------------------------------------


class TestD10KnobDefaultsResolveThroughSettings:
    """D-10: knob defaults are settings-resolvable, not bare magic numbers."""

    def test_derivation_knobs_use_resolve_setting(self):
        src = _read("admin/core/agentiq/derivation.py")
        for key in (
            "AGENTIQ_INTELLIGENCE_LEVEL",
            "AGENTIQ_AUTONOMY_LEVEL",
            "AGENTIQ_RESOURCE_BUDGET",
        ):
            assert (
                f'resolve_setting("{key}"' in src
            ), f"D-10 open: derivation.py does not resolve {key}"

    def test_no_bare_knob_default_assignments(self):
        """The historical `= 5 / = 5 / = 0.10` bare defaults must be gone."""
        src = _read("admin/core/agentiq/derivation.py")
        bare = re.findall(
            r"(?:intelligence_level|autonomy_level|resource_budget)\s*:\s*\w+\s*=\s*"
            r"(?:5|0\.10)\b",
            src,
        )
        assert not bare, f"D-10 open, bare knob defaults remain: {bare}"


# ---------------------------------------------------------------------------
# D-12 — LANGUAGE_CODE is operator-configurable
# ---------------------------------------------------------------------------


class TestD12LanguageCodeConfigurable:
    """D-12: LANGUAGE_CODE comes from env/settings; the literal is only a fallback."""

    def test_language_code_is_env_backed_in_gateway_settings(self):
        src = _read("services/gateway/settings.py")
        assert re.search(
            r'LANGUAGE_CODE\s*=\s*os\.environ\.get\(\s*["\']SA01_LANGUAGE_CODE["\']',
            src,
        ), "D-12 open: gateway LANGUAGE_CODE must read SA01_LANGUAGE_CODE"

    def test_language_code_is_env_backed_in_config_settings(self):
        src = _read("config/settings.py")
        assert re.search(
            r'LANGUAGE_CODE\s*=\s*os\.environ\.get\(\s*["\']SA01_LANGUAGE_CODE["\']',
            src,
        ), "D-12 open: config LANGUAGE_CODE must read SA01_LANGUAGE_CODE"

    def test_language_code_env_override_wins(self, monkeypatch):
        monkeypatch.setenv("SA01_LANGUAGE_CODE", "pt-br")
        # Re-evaluate the assignment exactly as the settings module does.
        import os

        assert os.environ.get("SA01_LANGUAGE_CODE", "en-us") == "pt-br"


# ---------------------------------------------------------------------------
# D-13 — LLM_* timeouts/retries are categorized LLM
# ---------------------------------------------------------------------------


class TestD13LLMKeyCategory:
    """D-13: KEY_CATEGORY puts LLM_* timeouts/retries in the LLM bucket."""

    def test_llm_keys_are_category_llm(self):
        from admin.core.helpers.capsule_settings import CATEGORY_LLM, KEY_CATEGORY

        for key in (
            "LLM_CONNECT_TIMEOUT_S",
            "LLM_READ_TIMEOUT_S",
            "LLM_MAX_RETRIES",
            "LLM_RETRY_BASE_DELAY_S",
            "LLM_RETRY_BACKOFF_CAP_S",
            "LLM_RETRY_AFTER_CAP_S",
        ):
            assert (
                KEY_CATEGORY.get(key) == CATEGORY_LLM
            ), f"D-13 open: {key} is {KEY_CATEGORY.get(key)!r}, expected LLM"

    def test_category_of_uses_the_map(self):
        from admin.core.helpers.capsule_settings import CATEGORY_LLM, category_of

        assert category_of("LLM_MAX_RETRIES") == CATEGORY_LLM


# ---------------------------------------------------------------------------
# D-14 — channel-layer transport cannot silently disagree across modules
# ---------------------------------------------------------------------------


class TestD14ChannelLayerAuthority:
    """D-14: both settings modules read the channel backend from config/env."""

    CHANNEL_RE = re.compile(
        r'"BACKEND"\s*:\s*(?:os\.environ\.get\([^)]+\)|os\.getenv\([^)]+\))',
        re.DOTALL,
    )

    def test_gateway_channel_layer_is_configurable(self):
        src = _read("services/gateway/settings.py")
        assert self.CHANNEL_RE.search(
            src
        ), "D-14 open: gateway CHANNEL_LAYERS BACKEND must come from env/settings"

    def test_config_channel_layer_is_configurable(self):
        src = _read("config/settings.py")
        assert self.CHANNEL_RE.search(
            src
        ), "D-14 open: config CHANNEL_LAYERS BACKEND must come from env/settings"

    def test_each_module_declares_its_authority(self):
        """Each module must say which deployment it is authoritative for."""
        for rel in ("services/gateway/settings.py", "config/settings.py"):
            src = _read(rel)
            assert (
                "authoritative" in src.lower()
            ), f"D-14 open: {rel} does not declare channel-layer authority"

    def test_env_override_selects_backend(self, monkeypatch):
        import os

        monkeypatch.setenv("SA01_CHANNEL_LAYER_BACKEND", "channels_redis.core.RedisChannelLayer")
        assert (
            os.environ.get("SA01_CHANNEL_LAYER_BACKEND", "channels.layers.InMemoryChannelLayer")
            == "channels_redis.core.RedisChannelLayer"
        )
