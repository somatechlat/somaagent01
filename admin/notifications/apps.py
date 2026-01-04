"""Notifications Django app configuration."""

from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    """Notificationsconfig class implementation."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "admin.notifications"
    verbose_name = "Notifications"