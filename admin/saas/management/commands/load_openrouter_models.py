"""
Django Management Command: load_openrouter_models
Load OpenRouter FREE and PAID models into GlobalDefault.defaults["models"].


- Pure Django ORM via GlobalDefault model
- Idempotent (safe to re-run)
- NO raw SQL, NO mocks
- Follows SRS model configuration structure

Usage:
    python manage_agent.py load_openrouter_models [--free-only] [--paid-only]
"""

import logging

from django.core.management.base import BaseCommand
from django.db import transaction

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Command class implementation."""

    help = "Load OpenRouter models into GlobalDefault defaults"

    def add_arguments(self, parser):
        """Execute add arguments.

        Args:
            parser: The parser.
        """

        parser.add_argument(
            "--free-only",
            action="store_true",
            help="Only load FREE models (no API key required)",
        )
        parser.add_argument(
            "--paid-only",
            action="store_true",
            help="Only load PAID models (require API key)",
        )
        parser.add_argument(
            "--clear-existing",
            action="store_true",
            help="Clear existing models before loading",
        )

    def get_openrouter_models(self):
        """Return complete OpenRouter model catalog.

        Returns:
            List of model dictionaries matching SRS ModelConfig structure
        """
        # FREE Models (No API key required)
        free_models = [
            {
                "id": "google/gemma-2-9b-it:free",
                "provider": "openrouter",
                "model_name": "google/gemma-2-9b-it",
                "display_name": "Gemma 2 9B (Free)",
                "enabled": True,
                "default_for_chat": False,
                "default_for_completion": False,
                "rate_limit": 200,
                "ctx_length": 8192,
                "vision": False,
                "capabilities": ["text"],
                "priority": 30,
                "cost_tier": "free",
            },
            {
                "id": "meta-llama/llama-3.1-8b-instruct:free",
                "provider": "openrouter",
                "model_name": "meta-llama/llama-3.1-8b-instruct",
                "display_name": "Llama 3.1 8B (Free)",
                "enabled": True,
                "default_for_chat": False,
                "default_for_completion": False,
                "rate_limit": 200,
                "ctx_length": 8192,
                "vision": False,
                "capabilities": ["text", "code"],
                "priority": 35,
                "cost_tier": "free",
            },
            {
                "id": "mistralai/mistral-7b-instruct:free",
                "provider": "openrouter",
                "model_name": "mistralai/mistral-7b-instruct",
                "display_name": "Mistral 7B (Free)",
                "enabled": True,
                "default_for_chat": False,
                "default_for_completion": False,
                "rate_limit": 200,
                "ctx_length": 32768,
                "vision": False,
                "capabilities": ["text", "code"],
                "priority": 40,
                "cost_tier": "free",
            },
            {
                "id": "microsoft/wizardlm-2-7b:free",
                "provider": "openrouter",
                "model_name": "microsoft/wizardlm-2-7b",
                "display_name": "WizardLM 2 7B (Free)",
                "enabled": True,
                "default_for_chat": False,
                "default_for_completion": False,
                "rate_limit": 200,
                "ctx_length": 128000,
                "vision": False,
                "capabilities": ["text", "long_context"],
                "priority": 35,
                "cost_tier": "free",
            },
            {
                "id": "qwen/qwen-2-7b-instruct:free",
                "provider": "openrouter",
                "model_name": "qwen/qwen-2-7b-instruct",
                "display_name": "Qwen 2 7B (Free)",
                "enabled": True,
                "default_for_chat": False,
                "default_for_completion": False,
                "rate_limit": 200,
                "ctx_length": 32768,
                "vision": False,
                "capabilities": ["text", "code"],
                "priority": 35,
                "cost_tier": "free",
            },
            {
                "id": "deepseek/deepseek-chat:free",
                "provider": "openrouter",
                "model_name": "deepseek/deepseek-chat",
                "display_name": "DeepSeek Chat (Free)",
                "enabled": True,
                "default_for_chat": False,
                "default_for_completion": False,
                "rate_limit": 200,
                "ctx_length": 32768,
                "vision": False,
                "capabilities": ["text", "code"],
                "priority": 45,
                "cost_tier": "free",
            },
            {
                "id": "openai/gpt-4.1-mini:free",
                "provider": "openrouter",
                "model_name": "openai/gpt-4.1-mini",
                "display_name": "GPT-4.1 Mini (Free)",
                "enabled": True,
                "default_for_chat": True,  # DEFAULT for free tier
                "default_for_completion": False,
                "rate_limit": 200,
                "ctx_length": 128000,
                "vision": True,
                "capabilities": ["text", "vision", "code", "long_context", "function_calling"],
                "priority": 60,
                "cost_tier": "free",
            },
        ]

        # PAID Models (Require API key)
        paid_models = [
            {
                "id": "anthropic/claude-3.5-sonnet",
                "provider": "openrouter",
                "model_name": "anthropic/claude-3.5-sonnet",
                "display_name": "Claude 3.5 Sonnet",
                "enabled": False,  # Disabled by default (requires API key)
                "default_for_chat": True,
                "default_for_completion": False,
                "rate_limit": 100,
                "ctx_length": 200000,
                "vision": True,
                "capabilities": [
                    "text",
                    "vision",
                    "code",
                    "long_context",
                    "function_calling",
                    "structured_output",
                ],
                "priority": 95,
                "cost_tier": "premium",
                "domains": ["code", "legal"],
            },
            {
                "id": "openai/gpt-4o",
                "provider": "openrouter",
                "model_name": "openai/gpt-4o",
                "display_name": "GPT-4o",
                "enabled": False,
                "default_for_chat": False,
                "default_for_completion": False,
                "rate_limit": 100,
                "ctx_length": 128000,
                "vision": True,
                "capabilities": [
                    "text",
                    "vision",
                    "code",
                    "audio",
                    "long_context",
                    "function_calling",
                    "structured_output",
                ],
                "priority": 90,
                "cost_tier": "premium",
            },
            {
                "id": "openai/gpt-4.1",
                "provider": "openrouter",
                "model_name": "openai/gpt-4.1",
                "display_name": "GPT-4.1",
                "enabled": False,
                "default_for_chat": False,
                "default_for_completion": True,
                "rate_limit": 100,
                "ctx_length": 1000000,
                "vision": True,
                "capabilities": [
                    "text",
                    "vision",
                    "code",
                    "long_context",
                    "function_calling",
                    "structured_output",
                ],
                "priority": 92,
                "cost_tier": "premium",
            },
            {
                "id": "anthropic/claude-3-opus",
                "provider": "openrouter",
                "model_name": "anthropic/claude-3-opus",
                "display_name": "Claude 3 Opus",
                "enabled": False,
                "default_for_chat": False,
                "default_for_completion": False,
                "rate_limit": 100,
                "ctx_length": 200000,
                "vision": True,
                "capabilities": [
                    "text",
                    "vision",
                    "code",
                    "long_context",
                    "function_calling",
                    "structured_output",
                ],
                "priority": 98,
                "cost_tier": "premium",
                "domains": ["scientific", "legal"],
            },
            {
                "id": "google/gemini-pro",
                "provider": "openrouter",
                "model_name": "google/gemini-pro",
                "display_name": "Gemini Pro",
                "enabled": False,
                "default_for_chat": False,
                "default_for_completion": False,
                "rate_limit": 100,
                "ctx_length": 1000000,
                "vision": True,
                "capabilities": [
                    "text",
                    "vision",
                    "video",
                    "audio",
                    "code",
                    "long_context",
                    "function_calling",
                ],
                "priority": 88,
                "cost_tier": "standard",
            },
            {
                "id": "perplexity/pplx-7b-online",
                "provider": "openrouter",
                "model_name": "perplexity/pplx-7b-online",
                "display_name": "Perplexity PPLX 7B Online",
                "enabled": False,
                "default_for_chat": False,
                "default_for_completion": False,
                "rate_limit": 100,
                "ctx_length": 8192,
                "vision": False,
                "capabilities": ["text"],
                "priority": 50,
                "cost_tier": "low",
            },
        ]

        return free_models + paid_models

    @transaction.atomic
    def handle(self, *args, **options):
        """Load models into LLMModelConfig (SINGLE SOURCE OF TRUTH).

        Models are stored in Django ORM, NOT GlobalDefault.
        """
        from admin.llm.models import LLMModelConfig

        self.stdout.write(
            self.style.HTTP_INFO("\n🔄 Loading OpenRouter Models into LLMModelConfig...\n")
        )

        # Filter models by flags
        all_models = self.get_openrouter_models()

        if options["free_only"]:
            models_to_load = [m for m in all_models if ":free" in m["id"]]
            self.stdout.write(self.style.WARNING("  ⚠️  Loading FREE models only\n"))
        elif options["paid_only"]:
            models_to_load = [m for m in all_models if ":free" not in m["id"]]
            self.stdout.write(self.style.WARNING("  ⚠️  Loading PAID models only\n"))
        else:
            models_to_load = all_models
            self.stdout.write(self.style.HTTP_INFO("  📦 Loading ALL models (FREE + PAID)\n"))

        if not models_to_load:
            self.stdout.write(self.style.WARNING("  ❌ No models to load!\n"))
            return

        # Clear existing models if requested
        if options["clear_existing"]:
            old_count = LLMModelConfig.objects.count()
            LLMModelConfig.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"  🗑️  Cleared {old_count} existing models\n"))

        added_count = 0
        updated_count = 0

        for model_data in models_to_load:
            # Map JSON fields to ORM fields
            name = model_data["model_name"]
            defaults = {
                "display_name": model_data.get("display_name", ""),
                "provider": model_data.get("provider", "openrouter"),
                "model_type": "chat",
                "ctx_length": model_data.get("ctx_length", 0),
                "limit_requests": model_data.get("rate_limit", 0),
                "vision": model_data.get("vision", False),
                "capabilities": model_data.get("capabilities", ["text"]),
                "priority": model_data.get("priority", 50),
                "cost_tier": model_data.get("cost_tier", "standard"),
                "domains": model_data.get("domains", []),
                "is_active": model_data.get("enabled", True),
            }

            obj, created = LLMModelConfig.objects.update_or_create(
                name=name,
                defaults=defaults,
            )

            if created:
                added_count += 1
            else:
                updated_count += 1

        total_count = LLMModelConfig.objects.count()
        self.stdout.write(self.style.SUCCESS("\n  ✅ Models loaded to LLMModelConfig!\n"))
        self.stdout.write(self.style.HTTP_INFO(f"     • Added: {added_count}\n"))
        self.stdout.write(self.style.HTTP_INFO(f"     • Updated: {updated_count}\n"))
        self.stdout.write(self.style.HTTP_INFO(f"     • Total in DB: {total_count}\n"))

        # Show model breakdown
        free_enabled = LLMModelConfig.objects.filter(is_active=True, name__contains=":free").count()
        paid_enabled = (
            LLMModelConfig.objects.filter(is_active=True).exclude(name__contains=":free").count()
        )
        default_chat = LLMModelConfig.objects.filter(is_active=True).order_by("-priority").first()

        self.stdout.write(self.style.HTTP_INFO("\n  📊 Model Summary:\n"))
        self.stdout.write(self.style.HTTP_INFO(f"     • FREE enabled: {free_enabled}\n"))
        self.stdout.write(self.style.HTTP_INFO(f"     • PAID enabled: {paid_enabled}\n"))
        if default_chat:
            self.stdout.write(
                self.style.SUCCESS(
                    f"     • Top Priority Model: {default_chat.display_name or default_chat.name} (priority={default_chat.priority})\n"
                )
            )
        else:
            self.stdout.write(self.style.WARNING("     • No active models!\n"))


__all__ = ["Command"]
