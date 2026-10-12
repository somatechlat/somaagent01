"""Seed mimo-flash as the default chat model (priority 100).

Idempotent clone of ``0004_seed_groq_models``: ``update_or_create`` keyed on
the unique ``name``, never blind-inserts. ``provider='mimo'`` is a FIELD on
the row — there is no separate provider registry (operator mandate).

``api_base`` is left empty on purpose: Mimo is a *deployment* endpoint
(R-VEN-02). The operator names it through the settings chain
(``LLMModelConfig.api_base`` / InfrastructureConfig). A host invented here is
a host nobody chose.

Note on numbering: ``0005_model_type_decision`` already occupies the 0005
slot. This file deliberately keeps the operator-requested name
``0005_seed_mimo_flash``; Django keys migrations by module name, so the two
leaves coexist. Re-run ``makemigrations`` only after one of them is folded
into the graph as a dependency.
"""

from django.db import migrations

MIMO_FLASH = {
    "name": "mimo-flash",
    "display_name": "MiMo Flash",
    "model_type": "chat",
    "provider": "mimo",
    "api_base": "",
    "capabilities": ["text", "code", "tools", "long_context"],
    "priority": 100,
    "cost_tier": "free",
    "domains": [],
    "ctx_length": 131072,
    "limit_requests": 0,
    "limit_input": 0,
    "limit_output": 0,
    "vision": False,
    "kwargs": {},
    "is_active": True,
}


def seed_mimo_flash(apps, schema_editor):
    """Upsert mimo-flash at priority 100 so select_model routes to it first."""
    LLMModelConfig = apps.get_model("llm", "LLMModelConfig")
    defaults = {k: v for k, v in MIMO_FLASH.items() if k != "name"}
    LLMModelConfig.objects.update_or_create(name=MIMO_FLASH["name"], defaults=defaults)


def remove_mimo_flash(apps, schema_editor):
    """Remove only the row this migration seeded on reverse."""
    LLMModelConfig = apps.get_model("llm", "LLMModelConfig")
    LLMModelConfig.objects.filter(provider="mimo", name=MIMO_FLASH["name"]).delete()


class Migration(migrations.Migration):
    """Seed the mimo-flash default chat model."""

    dependencies = [
        ("llm", "0005_model_type_decision"),
    ]

    operations = [
        migrations.RunPython(seed_mimo_flash, remove_mimo_flash),
    ]
