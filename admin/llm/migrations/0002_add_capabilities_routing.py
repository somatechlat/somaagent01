# Generated migration for capability-based routing
# admin/llm/migrations/0002_add_capabilities_routing.py

from django.db import migrations, models


class Migration(migrations.Migration):
    """Add capability-based routing fields to LLMModelConfig."""

    dependencies = [
        ("llm", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="llmmodelconfig",
            name="capabilities",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="List of capabilities: text, vision, video, audio, code, long_context, etc.",
            ),
        ),
        migrations.AddField(
            model_name="llmmodelconfig",
            name="priority",
            field=models.IntegerField(
                default=50,
                help_text="Routing priority (0-100). Higher = preferred when multiple models match.",
            ),
        ),
        migrations.AddField(
            model_name="llmmodelconfig",
            name="cost_tier",
            field=models.CharField(
                choices=[
                    ("free", "Free"),
                    ("low", "Low Cost"),
                    ("standard", "Standard"),
                    ("premium", "Premium"),
                ],
                default="standard",
                help_text="Cost tier for budget-aware routing.",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="llmmodelconfig",
            name="domains",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="Specialized domains: medical, legal, code, scientific, etc.",
            ),
        ),
        migrations.AddField(
            model_name="llmmodelconfig",
            name="display_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddIndex(
            model_name="llmmodelconfig",
            index=models.Index(
                fields=["is_active", "priority"],
                name="llm_model_c_is_acti_routing_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="llmmodelconfig",
            index=models.Index(
                fields=["provider", "is_active"],
                name="llm_model_c_provide_active_idx",
            ),
        ),
        migrations.AlterModelOptions(
            name="llmmodelconfig",
            options={
                "ordering": ["-priority", "provider", "name"],
                "verbose_name": "LLM Model Configuration",
                "verbose_name_plural": "LLM Model Configurations",
            },
        ),
    ]
