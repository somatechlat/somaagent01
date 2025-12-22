"""AgentSkin admin app configuration."""

from django.apps import AppConfig


class SkinsConfig(AppConfig):
    """Configuration for the skins admin app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admin.skins'
    verbose_name = 'Agent Skins'
