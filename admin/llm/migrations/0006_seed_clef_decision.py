"""Seed the Clef decision LLMModelConfig row (System One / Workers AI).

Idempotent: update_or_create keyed on unique ``name``='clef-decision'.

``api_base`` is read from Django settings (``CLEF_API_BASE``) at migrate time -
never a host invented in this file. When the operator layer has not been
bootstrapped yet the row is still created with an empty ``api_base``;
``manage.py bootstrap_clef`` fills the real settings-chain value afterwards.
"""

from django.conf import settings
from django.db import migrations

DECISION_ROW_NAME = "clef-decision"
DECISION_CAPABILITIES = ["decision", "score", "noul"]
DECISION_PRIORITY = 95


def seed_clef_decision_model(apps, schema_editor):
    LLMModelConfig = apps.get_model("llm", "LLMModelConfig")
    api_base = str(getattr(settings, "CLEF_API_BASE", "") or "").rstrip("/")
    defaults = {
        "display_name": "Clef Decision (Workers AI)",
        "model_type": "decision",
        "provider": "cloudflare",
        "api_base": api_base,
        "capabilities": list(DECISION_CAPABILITIES),
        "priority": DECISION_PRIORITY,
        "cost_tier": "low",
        "is_active": True,
    }
    LLMModelConfig.objects.update_or_create(name=DECISION_ROW_NAME, defaults=defaults)


def remove_clef_decision_model(apps, schema_editor):
    LLMModelConfig = apps.get_model("llm", "LLMModelConfig")
    LLMModelConfig.objects.filter(
        provider="cloudflare", name=DECISION_ROW_NAME, model_type="decision"
    ).delete()


class Migration(migrations.Migration):
    """Seed the clef-decision model row."""

    dependencies = [
        ("llm", "0005_model_type_decision"),
        ("llm", "0005_seed_mimo_flash"),
    ]

    operations = [
        migrations.RunPython(seed_clef_decision_model, remove_clef_decision_model),
    ]
