"""Voice Django app configuration."""

from django.apps import AppConfig


class VoiceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "admin.voice"
    verbose_name = "Voice Services"
