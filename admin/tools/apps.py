"""Tools Django app configuration."""

from django.apps import AppConfig


class ToolsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "admin.tools"
    verbose_name = "Tool Management"
