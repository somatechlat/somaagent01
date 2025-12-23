"""Django app configuration for SAAS Admin."""

from django.apps import AppConfig


class SaasConfig(AppConfig):
    """SAAS Admin app configuration."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admin.saas'
    verbose_name = 'SAAS Administration'
