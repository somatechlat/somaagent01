"""Multimodal Django app configuration."""

from django.apps import AppConfig


class MultimodalConfig(AppConfig):
    """Multimodalconfig class implementation."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "admin.multimodal"
    verbose_name = "Multimodal"