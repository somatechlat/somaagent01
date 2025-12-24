"""Django app config for admin.agents."""

from django.apps import AppConfig


class AgentsConfig(AppConfig):
    """Agents application config."""
    
    name = "admin.agents"
    verbose_name = "Agent Management"
    default_auto_field = "django.db.models.BigAutoField"
