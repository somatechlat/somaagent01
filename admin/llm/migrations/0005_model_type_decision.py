"""Add decision model type (Clef / System One) to LLMModelConfig.choices."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("llm", "0004_seed_groq_models"),
    ]

    operations = [
        migrations.AlterField(
            model_name="llmmodelconfig",
            name="model_type",
            field=models.CharField(
                choices=[
                    ("chat", "Chat"),
                    ("embedding", "Embedding"),
                    ("decision", "Decision"),
                ],
                default="chat",
                max_length=20,
            ),
        ),
    ]
