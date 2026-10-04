"""A service URL is an operator-editable parameter, not an ENV contract.

Owner's ruling: *"SOMABRAIN_URL should be an editable parameter."*
`docs/iso/SOMA-SETTINGS-MODEL-001.md` marks service URLs `Owner: Env (L3)`.
That is the defect: an operator must be able to point the agent at another
SomaBrain from the admin UI - no `.env` edit, no container recreate.

So the chain is:
    Capsule > AgentSetting > InfrastructureConfig (the operator's layer)
        > SettingsModel > schema default
and **process environment is not in it**. ENV carries bootstrap only
(`SA01_DEPLOYMENT_MODE`, `VAULT_ADDR`, the database that holds the settings).
"""

from __future__ import annotations

import inspect

import pytest

from admin.core.helpers import service_urls


def test_env_is_not_in_the_url_chain():
    """A value sourced from ENV is one an operator cannot edit."""
    src = inspect.getsource(service_urls.require_service_url)
    assert "_from_env" not in src, "ENV still resolves a service URL"
    assert "os.environ" not in src


def test_infraconfig_is_the_operator_layer():
    """The ORM an administrator edits must be consulted before the schema."""
    src = inspect.getsource(service_urls.require_service_url)
    assert "_from_infraconfig" in src
    # and it must come before the SettingsModel fallback
    assert src.index("_from_infraconfig") < src.index("get_settings"), (
        "the operator's layer must outrank the schema default"
    )


@pytest.mark.django_db
def test_operator_value_wins_over_schema():
    """An administrator setting the URL in InfrastructureConfig wins."""
    from asgiref.sync import sync_to_async

    from admin.core.infrastructure.models import InfrastructureConfig, ServiceHealth

    def _seed():
        svc, _ = ServiceHealth.objects.get_or_create(
            service_name="somabrain", defaults={"status": "healthy"}
        )
        InfrastructureConfig.objects.update_or_create(
            service=svc, key="SOMABRAIN_URL",
            defaults={"value": "http://operator-set-brain:30101"},
        )

    __import__('asyncio').run(sync_to_async(_seed)())
    resolved = service_urls.require_service_url("SOMABRAIN_URL")
    assert resolved == "http://operator-set-brain:30101"


def test_missing_url_refuses(monkeypatch):
    """An unconfigured endpoint is a refusal, never a guessed host."""
    # Blank every layer so only the refusal can happen.
    monkeypatch.setattr(service_urls, "_from_infraconfig", lambda _n: None)
    import admin.core.helpers.settings as _s

    monkeypatch.setattr(_s, "get_settings", lambda **_k: type("M", (), {})())
    with pytest.raises(Exception):
        service_urls.require_service_url("NOT_A_REAL_SERVICE_URL")
