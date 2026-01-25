"""Django app configuration for AAAS Admin."""

from django.apps import AppConfig


class AaasConfig(AppConfig):
    """AAAS Admin app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "admin.aaas"
    verbose_name = "AAAS Administration"
