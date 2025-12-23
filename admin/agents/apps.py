from django.apps import AppConfig


class AgentsConfig(AppConfig):
    """Django app config for agents."""
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "admin.agents"
    label = "admin_agents"
    verbose_name = "Agent Management"
