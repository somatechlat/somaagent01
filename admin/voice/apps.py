"""Voice Django app configuration."""

from django.apps import AppConfig


class VoiceConfig(AppConfig):
    """Voiceconfig class implementation."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "admin.voice"
    verbose_name = "Voice Services"