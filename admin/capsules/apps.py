"""Capsules Django app configuration."""

from django.apps import AppConfig


class CapsulesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "admin.capsules"
    verbose_name = "Capsules"
