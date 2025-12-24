"""LLM Django app configuration."""

from django.apps import AppConfig


class LlmConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "admin.llm"
    verbose_name = "LLM Management"
