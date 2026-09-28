"""Phase D — zero-drift settings conformance (SOMA-SETTINGS-MODEL-001.md).

The settings model has one resolution order and one category taxonomy. This
suite is the conformance gate: if drift reappears anywhere in the model, it
fails here.

    Capsule.persona_config["settings"][CAT][KEY]
        → AgentSetting ORM
            → Django settings
                → schema default

Run:
    pytest tests/unit/test_settings_conformance.py -v
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


class CapsuleDouble:
    """Recording stand-in for a Capsule row with persona_config settings."""

    def __init__(self, settings_by_category: dict) -> None:
        self.persona_config = {"settings": settings_by_category}


class RecordingAgentSetting:
    """Recording stand-in for the AgentSetting ORM row."""

    def __init__(self, value):
        self.value = value


class RecordingQuerySet:
    """Recording stand-in for AgentSetting.objects.filter(...)."""

    def __init__(self, row):
        self._row = row

    def first(self):
        return self._row


class RecordingManager:
    """Recording stand-in for the AgentSetting model manager."""

    def __init__(self, row):
        self._row = row

    def filter(self, **kwargs):  # noqa: ANN003 - mirrors Django manager
        return RecordingQuerySet(self._row)


def _install_agent_setting(monkeypatch, value) -> list[dict]:
    import admin.core.models as models

    calls: list[dict] = []

    class _Model:
        class objects:  # noqa: N801 - mimics Django manager attribute
            @staticmethod
            def filter(**kwargs):
                calls.append(kwargs)
                return RecordingQuerySet(RecordingAgentSetting(value))

    monkeypatch.setattr(models, "AgentSetting", _Model)
    return calls


class TestResolutionOrder:
    """Capsule → AgentSetting → Django → schema default, in that order."""

    def test_capsule_beats_agent_setting_and_django(self, monkeypatch):
        from admin.core.helpers.capsule_settings import resolve_setting

        _install_agent_setting(monkeypatch, "from-agent-setting")
        monkeypatch.setattr(
            "django.conf.settings.SOMABRAIN_URL", "http://from-django", raising=False
        )

        capsule = CapsuleDouble({"INFRA": {"SOMABRAIN_URL": "http://from-capsule"}})
        assert (
            resolve_setting("SOMABRAIN_URL", capsule=capsule, agent_id="a1")
            == "http://from-capsule"
        )

    def test_agent_setting_beats_django(self, monkeypatch):
        from admin.core.helpers.capsule_settings import resolve_setting

        _install_agent_setting(monkeypatch, "from-agent-setting")
        monkeypatch.setattr(
            "django.conf.settings.SOMABRAIN_URL", "http://from-django", raising=False
        )

        assert resolve_setting("SOMABRAIN_URL", agent_id="a1") == "from-agent-setting"

    def test_django_beats_schema_default(self, monkeypatch):
        from admin.core.helpers.capsule_settings import resolve_setting

        monkeypatch.setattr(
            "django.conf.settings.SOMABRAIN_URL", "http://from-django", raising=False
        )
        assert resolve_setting("SOMABRAIN_URL") == "http://from-django"

    def test_schema_default_when_nothing_configured(self, monkeypatch):
        from admin.core.helpers.capsule_settings import resolve_setting

        monkeypatch.delattr("django.conf.settings.SOMABRAIN_URL", raising=False)
        assert resolve_setting("SOMABRAIN_URL", default="schema-fallback") == "schema-fallback"

    def test_agent_setting_layer_queried_with_key(self, monkeypatch):
        from admin.core.helpers.capsule_settings import resolve_setting

        calls = _install_agent_setting(monkeypatch, "v")
        resolve_setting("MEM_RECALL_TOP_K", agent_id="agent-9")
        assert calls and calls[0].get("agent_id") == "agent-9"
        assert calls[0].get("key") == "MEM_RECALL_TOP_K"

    def test_capsule_save_round_trips(self):
        """save_capsule_setting then resolve_setting returns the saved value."""
        from admin.core.helpers.capsule_settings import resolve_setting, save_capsule_setting

        capsule = CapsuleDouble({})
        save_capsule_setting(capsule, "MEM_RECALL_TOP_K", 42)
        assert resolve_setting("MEM_RECALL_TOP_K", capsule=capsule) == 42


class TestCategoryTaxonomy:
    """Every settings key used by the model has exactly one category."""

    def test_known_keys_are_categorized(self):
        from admin.core.helpers.capsule_settings import category_of, KEY_CATEGORY

        for key in (
            "MEM_EMBED_DIM",
            "SOMABRAIN_URL",
            "SOMABRAIN_MEMORY_HTTP_TOKEN",
            "LLM_MAX_RETRIES",
            "DEFAULT_CHAT_MODEL_NAME",
        ):
            assert key in KEY_CATEGORY, f"{key} missing from KEY_CATEGORY"
            assert category_of(key) == KEY_CATEGORY[key]

    def test_settings_model_dj_keys_are_categorized_or_documented(self):
        """Every _dj key in settings_model.py resolves to a known category."""
        from admin.core.helpers.capsule_settings import CATEGORY_LLM, CATEGORY_MEMORY, category_of

        src = _read("admin/core/helpers/settings_model.py")
        keys = sorted(set(re.findall(r'_dj\(\s*"([A-Z0-9_]+)"', src)))
        assert keys, "expected _dj keys in settings_model.py"
        uncategorized = []
        for key in keys:
            cat = category_of(key)
            if cat in (CATEGORY_LLM, CATEGORY_MEMORY):
                continue
            # Remaining keys are INFRA/UI/AGENT/… — anything resolved is fine;
            # what is NOT allowed is a silent fall-through to a wrong bucket.
            if cat is None:
                uncategorized.append(key)
        assert not uncategorized, f"uncategorized keys: {uncategorized}"


class TestNoSecretsInEnv:
    """ENV is non-secret topology only — this is the standing contract."""

    SETTINGS_MODULES = [
        "config/settings.py",
        "services/gateway/settings.py",
        "infra/aaas/unified_settings.py",
        "admin/core/helpers/settings_model.py",
        "admin/core/helpers/settings_defaults.py",
        "admin/core/helpers/capsule_settings.py",
        "services/common/object_store.py",
    ]

    SECRET_SHAPED = re.compile(
        r"os\.(?:environ\.get|getenv|environ\[)\s*\(\s*['\"]"
        r"([A-Z0-9_]*(?:SECRET|PASSWORD|PASSWD|API_KEY|ACCESS_KEY)[A-Z0-9_]*"
        r"|[A-Z0-9_]*TOKEN(?!S)[A-Z0-9_]*)['\"]"
    )

    # Known secret-in-ENV reads awaiting the Vault migration (tracked in
    # pending-vault-secret-migration.md, owner: secrets/Vault lane). This list
    # may only shrink — a new entry is drift and fails the suite.
    PENDING_VAULT_MIGRATION = {
        "config/settings.py": {
            "SECRET_KEY",
            "KEYCLOAK_CLIENT_SECRET",
            "VAULT_TOKEN",
            "SOMABRAIN_MEMORY_HTTP_TOKEN",
            "SOMA_API_TOKEN",
            "TEST_DB_PASSWORD",
        },
        "services/gateway/settings.py": {
            "SECRET_KEY",
            "SA01_SOMABRAIN_API_KEY",
            "SOMA_API_TOKEN",
            "SA01_LLM_API_KEY",
            "SA01_KEYCLOAK_CLIENT_SECRET",
            "GOOGLE_CLIENT_SECRET",
        },
        "infra/aaas/unified_settings.py": {
            "SECRET_KEY",
            "DJANGO_SECRET_KEY",
            "SOMA_DB_PASSWORD",
            "POSTGRES_PASSWORD",
            "SOMA_API_TOKEN",
        },
    }

    def test_settings_modules_do_not_read_secret_keys_from_env(self):
        offenders = []
        for rel in self.SETTINGS_MODULES:
            path = REPO / rel
            if not path.exists():
                continue
            allowed = self.PENDING_VAULT_MIGRATION.get(rel, set())
            for match in self.SECRET_SHAPED.finditer(path.read_text(encoding="utf-8")):
                key = match.group(1)
                if key in allowed:
                    continue
                offenders.append(f"{rel}: ENV read of {key}")
        assert not offenders, (
            "secret material must come from Vault via UnifiedSecretManager, "
            "never ENV (new entries are drift; only the pending Vault-migration "
            "list is tolerated):\n  " + "\n  ".join(offenders)
        )

    def test_pending_list_only_shrinks(self):
        """Guard: the pending list must never grow — only shrink to empty."""
        allowed = self.PENDING_VAULT_MIGRATION
        # The sealed baseline at Phase D time. Removing a module here is fine
        # (it shrinks); adding a new module or key is drift and must fail.
        SEALED = {
            "config/settings.py": 6,
            "services/gateway/settings.py": 7,
            "infra/aaas/unified_settings.py": 5,
        }
        for rel, keys in allowed.items():
            assert rel in SEALED, f"new module added to pending list: {rel}"
            assert len(keys) <= SEALED[rel], f"pending list grew for {rel}"
        assert set(allowed) <= set(SEALED)

    def test_object_store_never_reads_credential_keys_from_env(self):
        src = _read("services/common/object_store.py")
        for key in ("MINIO_ACCESS_KEY", "MINIO_SECRET_KEY", "minioadmin"):
            assert f'os.environ.get("{key}"' not in src
            assert f"os.environ.get('{key}'" not in src
            assert "minioadmin" not in src, "no default MinIO credentials permitted"


class TestSeamStillHolds:
    """The 768 embedding seam contracts stay closed (D-01..D-06, D-15)."""

    def test_mem_embed_dim_default_is_768(self):
        src = _read("config/settings.py")
        assert re.search(r'MEM_EMBED_DIM["\']\s*,\s*["\']768["\']', src)

    def test_somabrain_embed_dim_seam_contract(self):
        src = _read("somabrain/settings/cognitive.py") if (REPO / "somabrain").exists() else ""
        # Cross-repo file may not exist in this checkout; the agent-side seam is
        # enforced here: gateway and config must agree on 768.
        gw = _read("services/gateway/settings.py")
        cf = _read("config/settings.py")
        for src in (gw, cf):
            assert re.search(r'MEM_EMBED_DIM["\']\s*,\s*["\']768["\']', src)
