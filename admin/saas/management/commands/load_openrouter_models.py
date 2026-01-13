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
            },
        ]

        return free_models + paid_models

    @transaction.atomic
    def handle(self, *args, **options):
        """Execute handle."""

        self.stdout.write(self.style.HTTP_INFO("\n🔄 Loading OpenRouter Models...\n"))

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

        # Get or create GlobalDefault instance
        from admin.saas.models.profiles import GlobalDefault

        gd = GlobalDefault.get_instance()
        defaults = dict(gd.defaults)

        # Clear existing models if requested
        if options["clear_existing"]:
            old_count = len(defaults.get("models", []))
            defaults["models"] = []
            self.stdout.write(self.style.WARNING(f"  🗑️  Cleared {old_count} existing models\n"))

        # Merge/update models
        existing_models = {m.get("id"): m for m in defaults.get("models", [])}

        added_count = 0
        updated_count = 0

        for model in models_to_load:
            model_id = model["id"]
            if model_id in existing_models:
                # Update existing
                existing_models[model_id].update(model)
                updated_count += 1
            else:
                # Add new
                existing_models[model_id] = model
                added_count += 1

        # Save updated defaults
        defaults["models"] = list(existing_models.values())
        gd.defaults = defaults
        gd.save()

        self.stdout.write(self.style.SUCCESS(f"\n  ✅ Models loaded successfully!\n"))
        self.stdout.write(self.style.HTTP_INFO(f"     • Added: {added_count}\n"))
        self.stdout.write(self.style.HTTP_INFO(f"     • Updated: {updated_count}\n"))
        self.stdout.write(self.style.HTTP_INFO(f"     • Total: {len(defaults['models'])}\n"))

        # Show model breakdown
        free_enabled = len([m for m in defaults["models"] if m.get("enabled", False) and ":free" in m["id"]])
        paid_enabled = len([m for m in defaults["models"] if m.get("enabled", False) and ":free" not in m["id"]])
        default_chat = next((m for m in defaults["models"] if m.get("default_for_chat", False)), None)

        self.stdout.write(self.style.HTTP_INFO("\n  📊 Model Summary:\n"))
        self.stdout.write(self.style.HTTP_INFO(f"     • FREE enabled: {free_enabled}\n"))
        self.stdout.write(self.style.HTTP_INFO(f"     • PAID enabled: {paid_enabled}\n"))
        if default_chat:
            self.stdout.write(self.style.SUCCESS(f"     • Default Chat Model: {default_chat['display_name']}\n"))
        else:
            self.stdout.write(self.style.WARNING("     • Default Chat Model: NONE\n"))

__all__ = ["Command"]
