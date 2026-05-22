"""Remove legacy fields from Capsule (schema, config, capabilities_whitelist).

These fields were superseded by:
- Capability M2M (replaces capabilities_whitelist)
- LLMModelConfig FKs (replaces config)
- Capability.schema (replaces capsule.schema)
"""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0006_add_capsule_persona_and_capability_fields"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="capsule",
            name="schema",
        ),
        migrations.RemoveField(
            model_name="capsule",
            name="config",
        ),
        migrations.RemoveField(
            model_name="capsule",
            name="capabilities_whitelist",
        ),
    ]
