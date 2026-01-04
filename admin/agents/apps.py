"""Agents Django app configuration."""

from django.apps import AppConfig


class AgentsConfig(AppConfig):
    """Agentsconfig class implementation."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "admin.agents"
    verbose_name = "Agent Management"

    def ready(self):
        """Initialize agent services when Django starts."""
        # Import signals here if needed
        pass