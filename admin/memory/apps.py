"""Memory Django app configuration."""

from django.apps import AppConfig


class MemoryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "admin.memory"
    verbose_name = "Memory"
