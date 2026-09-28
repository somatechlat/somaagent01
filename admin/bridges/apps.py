"""Bridges Django app configuration."""

from django.apps import AppConfig


class BridgesConfig(AppConfig):
    """Bridge data model app config."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "admin.bridges"
    verbose_name = "Bridges"
