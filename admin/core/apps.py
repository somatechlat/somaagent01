from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Django app config for core admin."""
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "admin.core"
    label = "admin_core"
    verbose_name = "Core Administration"
