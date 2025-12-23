from django.apps import AppConfig


class FeaturesConfig(AppConfig):
    """Django app config for features."""
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "admin.features"
    label = "admin_features"
    verbose_name = "Features & Configuration"
