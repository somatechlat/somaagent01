"""Django app config for admin.core."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Core application config."""
    
    name = "admin.core"
    verbose_name = "Core Domain"
    default_auto_field = "django.db.models.BigAutoField"
