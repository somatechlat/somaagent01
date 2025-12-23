from django.apps import AppConfig


class UtilsConfig(AppConfig):
    """Django app config for utils."""
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "admin.utils"
    label = "admin_utils"
    verbose_name = "Utilities"
