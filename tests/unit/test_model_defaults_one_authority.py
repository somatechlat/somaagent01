"""Model selection has one authority: the catalog.

There were two. ``LLMModelConfig`` rows carry ``provider`` and ``select_model``
routes on them; meanwhile ``DEFAULT_*_MODEL_PROVIDER`` named a provider
outright - and named the wrong one (``openrouter`` while every catalog row
said ``groq``). A setting that disagrees with the catalog and is never read
for routing is a second vocabulary for one concept, which is the defect
class this project keeps hitting.

Design criteria for the decision:
  rules            - one concept, one name
  thin             - a knob with no reader is a lie
  security         - a default pointing at nothing silently degrades routing
  transactions     - routing stays catalog-driven, no per-request lookup added
"""

from __future__ import annotations

import pytest

from admin.core.helpers.settings_model import SettingsModel


def test_no_provider_knob_exists():
    """Provider is a property of the model row, not a separate setting."""
    fields = set(SettingsModel.model_fields)
    for name in (
        "chat_model_provider",
        "util_model_provider",
        "embed_model_provider",
        "browser_model_provider",
    ):
        assert name not in fields, f"{name} is a second vocabulary for model.provider"


def test_model_name_pin_still_exists():
    """An operator may pin a specific model. That is a real, useful knob."""
    fields = set(SettingsModel.model_fields)
    assert "chat_model_name" in fields
    assert "util_model_name" in fields
    assert "embed_model_name" in fields


def test_provider_names_are_not_registered_keys():
    """KEY_CATEGORY must not carry a key nothing reads."""
    from admin.core.helpers.capsule_settings import KEY_CATEGORY

    for name in (
        "DEFAULT_CHAT_MODEL_PROVIDER",
        "DEFAULT_UTIL_MODEL_PROVIDER",
        "DEFAULT_EMBED_MODEL_PROVIDER",
        "chat_model_provider",
        "util_model_provider",
        "embed_model_provider",
    ):
        assert name not in KEY_CATEGORY, f"{name} is registered but never read"


@pytest.mark.django_db
def test_pinned_model_name_must_exist_or_refuse():
    """An operator pin names a catalog row or it is a refusal.

    Silent fall-through is how a typo in a setting becomes a routing change
    nobody can see. Fail-closed: an unresolvable pin raises.
    """
    import asyncio

    from admin.core.model_router import NoCapableModelError, resolve_model_pin

    # A name that is not in the catalog must not quietly resolve to something
    # else.
    try:
        asyncio.run(resolve_model_pin("nonexistent/model-xyz"))
    except NoCapableModelError:
        return
    raise AssertionError("an unresolvable model pin must raise, not fall through")


def test_empty_pin_is_not_an_error():
    """No pin means 'route by capability and priority' - the normal path."""
    import asyncio

    from admin.core.model_router import resolve_model_pin

    assert asyncio.run(resolve_model_pin("")) is None
    assert asyncio.run(resolve_model_pin(None)) is None
