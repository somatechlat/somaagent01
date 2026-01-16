"""Django app configuration for Orchestrator."""

from django.apps import AppConfig


class OrchestratorConfig(AppConfig):
    """Orchestratorconfig class implementation."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "admin.orchestrator"
    verbose_name = "Service Orchestrator"
