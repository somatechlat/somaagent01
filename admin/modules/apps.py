"""Capsule Modules Django app configuration."""

from django.apps import AppConfig


class ModulesConfig(AppConfig):
    """Capsule Module host app config."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "admin.modules"
    verbose_name = "Capsule Modules"
