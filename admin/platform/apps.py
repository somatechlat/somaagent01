"""Django app configuration for Soma Platform Admin."""

from django.apps import AppConfig


class SomaPlatformConfig(AppConfig):
    """Soma Platform Admin app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "admin.platform"
    verbose_name = "Soma Platform Administration"
