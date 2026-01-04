"""Django app config for admin.features."""

from django.apps import AppConfig


class FeaturesConfig(AppConfig):
    """Features application config."""

    name = "admin.features"
    verbose_name = "Feature Flags"
    default_auto_field = "django.db.models.BigAutoField"