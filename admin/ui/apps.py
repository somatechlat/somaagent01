"""UI Django app configuration."""

from django.apps import AppConfig


class UiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "admin.ui"
    verbose_name = "UI"
