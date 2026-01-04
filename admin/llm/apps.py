"""LLM Django app configuration."""

from django.apps import AppConfig


class LlmConfig(AppConfig):
    """Llmconfig class implementation."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "admin.llm"
    verbose_name = "LLM Management"