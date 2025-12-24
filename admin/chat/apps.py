"""Django app config for admin.chat."""

from django.apps import AppConfig


class ChatConfig(AppConfig):
    """Chat application config."""
    
    name = "admin.chat"
    verbose_name = "Chat Sessions"
    default_auto_field = "django.db.models.BigAutoField"
