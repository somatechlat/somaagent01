"""AgentIQ HTTP surface and the operator settings chain.

Two seams this suite pins:

1. ``Capsule.persona_config.knobs`` / ``DerivedSettings`` have a real Django
   Ninja surface. The UI may not invent either.
2. Settings writes land under the canonical chain name (``SOMABRAIN_URL``),
   so ``require_service_url`` sees the operator's edit and the memory lane
   repoints without a rebuild.
"""

from __future__ import annotations

import inspect

import pytest

from admin.core.agentiq.derivation import derive_all_settings, resolve_knobs
from admin.core.api import agentiq as agentiq_api
from admin.core.api import settings_v2


def test_agentiq_router_exposes_get_and_put():
    src = inspect.getsource(agentiq_api)
    assert '@router.get(' in src
    assert '@router.put(' in src
    assert "persona_config" in src


def test_derived_values_are_computed_on_the_server():
    """The API never ships knobs as derived values; derivation runs here."""
    src = inspect.getsource(agentiq_api)
    assert "derive_all_settings" in src
    # No client-side table in this module.
    assert "temperature=" not in src.split("def _derived_to_dict")[0]


def test_resolve_knobs_is_the_single_knob_reader():
    """derive_all_settings and the API both go through resolve_knobs."""
    derive_src = inspect.getsource(derive_all_settings)
    assert "resolve_knobs" in derive_src
    api_src = inspect.getsource(agentiq_api)
    assert "resolve_knobs" in api_src


def test_somabrain_url_is_stored_under_the_canonical_chain_name():
    """The operator layer must be keyed as require_service_url looks it up."""
    assert settings_v2.setting_name_for("somabrain", "url") == "SOMABRAIN_URL"
    assert settings_v2.setting_name_for("keycloak", "url") == "KEYCLOAK_URL"
    assert settings_v2.setting_name_for("memory", "url") == "SOMAFRACTALMEMORY_URL"


def test_entity_specs_carry_no_secret_material():
    """A secret-shaped key in the catalog may hold a Vault path, never a value."""
    for entity, spec in settings_v2.ENTITY_SPECS.items():
        for key, meta in spec.items():
            default = meta.get("default")
            if default is None:
                continue
            assert not isinstance(default, (bytes, bytearray))
            text = str(default)
            assert "BEGIN " not in text
            assert not text.startswith("sk-")


@pytest.mark.django_db
def test_settings_write_uses_canonical_key(monkeypatch):
    """Saving somabrain.url must write InfrastructureConfig(key=SOMABRAIN_URL)."""
    from admin.core.infrastructure.models import InfrastructureConfig, ServiceHealth

    saved = settings_v2.save_settings_to_db("somabrain", {"url": "http://brain.invalid"})
    assert saved is True

    row = InfrastructureConfig.objects.get(
        service__service_name="somabrain", key="SOMABRAIN_URL"
    )
    assert row.value == "http://brain.invalid"
    # The local alias must not be the row key — that is the bug this pins.
    assert not InfrastructureConfig.objects.filter(
        service__service_name="somabrain", key="url"
    ).exists()


@pytest.mark.django_db
def test_settings_read_maps_canonical_key_back_to_local():
    from admin.core.infrastructure.models import InfrastructureConfig, ServiceHealth

    ServiceHealth.objects.get_or_create(
        service_name="somabrain", defaults={"status": "healthy"}
    )
    InfrastructureConfig.objects.update_or_create(
        service=ServiceHealth.objects.get(service_name="somabrain"),
        key="SOMABRAIN_URL",
        defaults={"value": "http://brain.invalid"},
    )
    out = settings_v2.get_settings_from_db("somabrain")
    assert out is not None
    assert out.get("url") == "http://brain.invalid"
