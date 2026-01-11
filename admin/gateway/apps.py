"""Gateway Django app configuration."""

from django.apps import AppConfig


class GatewayConfig(AppConfig):
    """Gatewayconfig class implementation."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "admin.gateway"
    verbose_name = "Gateway"
