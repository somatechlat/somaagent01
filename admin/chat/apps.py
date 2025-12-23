from django.apps import AppConfig


class ChatConfig(AppConfig):
    """Django app config for chat."""
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "admin.chat"
    label = "admin_chat"
    verbose_name = "Chat & AI"
