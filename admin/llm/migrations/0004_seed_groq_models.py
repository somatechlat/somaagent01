# Seed data migration: live Groq chat models (Wave 2 — REAL GROQ CHAT).
# Upserts the Groq OSS models into LLMModelConfig so select_model can route
# chat traffic to them. Idempotent: update_or_create keyed on unique `name`,
# never blind-inserts.
#
# Model-string contract (LiteLLM) — CRITICAL:
#   provider = "groq"  +  name = "openai/gpt-oss-120b"
#   -> get_chat_model() builds "groq/openai/gpt-oss-120b" (three segments).
#   `name` holds Groq's own model id ("openai/gpt-oss-120b") — the "openai/"
#   segment is part of the model id, NOT a provider. A bare "gpt-oss-120b"
#   would build "groq/gpt-oss-120b" and Groq returns model_not_found.
#
# Capability flags (schema has no dedicated tool columns):
#   capabilities "tools"      -> tool-calling capable (true)
#   kwargs.parallel_tool_calls -> Groq OSS models do NOT support parallel
#                                 tool calls; also a valid Groq API parameter.

from django.db import migrations

# Specs verified against Groq model docs (2026-09):
#   openai/gpt-oss-120b: 131072 context / 65536 max completion, tools, no parallel tools
#   openai/gpt-oss-20b:  131072 context / 65536 max completion, tools, no parallel tools
#   (llama-3.3-70b / llama-3.1-8b are shut down for Free/Developer tiers and are
#    deliberately NOT seeded)
GROQ_MODELS = [
    {
        "name": "openai/gpt-oss-120b",
        "display_name": "GPT-OSS 120B (Groq)",
        "model_type": "chat",
        "provider": "groq",
        "api_base": "https://api.groq.com/openai/v1",
        # "text" is mandatory for the select_model capability-superset filter;
        # "tools" marks tool-calling support for tool-aware routing.
        "capabilities": ["text", "code", "tools", "long_context"],
        "priority": 90,
        "cost_tier": "standard",
        "domains": [],
        "ctx_length": 131072,
        "limit_requests": 0,
        "limit_input": 65536,
        "limit_output": 65536,
        "vision": False,
        "kwargs": {"parallel_tool_calls": False},
        "is_active": True,
    },
    {
        "name": "openai/gpt-oss-20b",
        "display_name": "GPT-OSS 20B (Groq)",
        "model_type": "chat",
        "provider": "groq",
        "api_base": "https://api.groq.com/openai/v1",
        "capabilities": ["text", "code", "tools", "long_context"],
        "priority": 70,
        "cost_tier": "low",
        "domains": [],
        "ctx_length": 131072,
        "limit_requests": 0,
        "limit_input": 65536,
        "limit_output": 65536,
        "vision": False,
        "kwargs": {"parallel_tool_calls": False},
        "is_active": True,
    },
]


def seed_groq_models(apps, schema_editor):
    """Upsert the live Groq chat models. Safe on existing rows (update, not insert)."""
    LLMModelConfig = apps.get_model("llm", "LLMModelConfig")
    for row in GROQ_MODELS:
        defaults = {key: value for key, value in row.items() if key != "name"}
        LLMModelConfig.objects.update_or_create(name=row["name"], defaults=defaults)


def remove_groq_models(apps, schema_editor):
    """Remove only the rows this migration seeded on reverse."""
    LLMModelConfig = apps.get_model("llm", "LLMModelConfig")
    LLMModelConfig.objects.filter(
        provider="groq", name__in=[row["name"] for row in GROQ_MODELS]
    ).delete()


class Migration(migrations.Migration):
    """Seed live Groq models into the LLM catalog."""

    dependencies = [
        (
            "llm",
            "0003_rename_llm_model_c_is_acti_routing_idx_llm_model_c_is_acti_1e0095_idx_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(seed_groq_models, remove_groq_models),
    ]
