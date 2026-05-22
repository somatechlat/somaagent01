# Generated manually for Capsule-Centric Architecture v2
# Adds persona_config, tool_policy, memory_pointer, neuromodulator_state to Capsule
# Adds policy, implementation to Capability

from django.db import migrations, models


def backfill_capsule_persona_config(apps, schema_editor):
    """Backfill persona_config from legacy fields and set sensible defaults."""
    Capsule = apps.get_model("core", "Capsule")
    for capsule in Capsule.objects.all():
        if not capsule.persona_config:
            persona_config = {}
            # Migrate resource_limits into persona.memory if present
            if capsule.resource_limits:
                persona_config["memory"] = {
                    "recall_limit": capsule.resource_limits.get("recall_limit", 10),
                    "similarity_threshold": capsule.resource_limits.get("similarity_threshold", 0.7),
                }
            # Set default knobs
            persona_config.setdefault("knobs", {
                "intelligence_level": 5,
                "autonomy_level": 5,
                "resource_budget": 0.10,
            })
            # Set default memory if not already set
            persona_config.setdefault("memory", {
                "recall_limit": 10,
                "similarity_threshold": 0.7,
            })
            # Set default prompts
            persona_config.setdefault("prompts", {
                "injection_prompts": [],
                "tool_prompts": {},
            })
            capsule.persona_config = persona_config
        # Set default memory_pointer if empty
        if not capsule.memory_pointer:
            capsule.memory_pointer = {
                "tenant": str(capsule.tenant_id) if capsule.tenant_id else "default",
                "namespace": f"agent_{str(capsule.id)[:8]}_chat_history",
                "recall_limit": 10,
                "similarity_threshold": 0.7,
            }
        # Set default tool_policy if empty
        if not capsule.tool_policy:
            capsule.tool_policy = {
                "auto_execute": [],
                "approval_required": [],
                "denied": [],
            }
        # Set default neuromodulator_state if empty
        if not capsule.neuromodulator_state:
            capsule.neuromodulator_state = {
                "dopamine": 0.5,
                "serotonin": 0.6,
                "norepinephrine": 0.4,
                "acetylcholine": 0.5,
                "last_synced_at": None,
            }
        capsule.save(update_fields=[
            "persona_config", "memory_pointer", "tool_policy", "neuromodulator_state"
        ])


def reverse_backfill(apps, schema_editor):
    """No-op reverse — new fields are simply dropped on reverse migration."""
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0005_capsule_certified_at_capsule_constitution_ref_and_more"),
    ]

    operations = [
        # Capsule new fields
        migrations.AddField(
            model_name="capsule",
            name="persona_config",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Agent persona configuration: {"knobs": {...}, "prompts": {...}, "memory": {...}, "learned": {...}}',
            ),
        ),
        migrations.AddField(
            model_name="capsule",
            name="tool_policy",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Tool execution policy: {"auto_execute": [...], "approval_required": [...], "denied": [...]}',
            ),
        ),
        migrations.AddField(
            model_name="capsule",
            name="memory_pointer",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Memory namespace pointer: {"tenant": ..., "namespace": ..., "recall_limit": ..., "similarity_threshold": ...}',
            ),
        ),
        migrations.AddField(
            model_name="capsule",
            name="neuromodulator_state",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Last-synced neuromodulator state from SomaBrain: {"dopamine": ..., "serotonin": ..., "last_synced_at": ...}',
            ),
        ),
        # Capability new fields
        migrations.AddField(
            model_name="capability",
            name="policy",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Tool execution policy: {"requires_approval": false, "timeout_seconds": 30, "max_retries": 3}',
            ),
        ),
        migrations.AddField(
            model_name="capability",
            name="implementation",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Tool implementation mapping: {"type": "python", "module": "tools.echo", "class": "EchoTool"}',
            ),
        ),
        # Backfill existing capsules with sensible defaults
        migrations.RunPython(backfill_capsule_persona_config, reverse_backfill),
    ]
