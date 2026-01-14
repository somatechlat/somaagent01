"""LLM models - 100% Django ORM.

Supports capability-based routing for intelligent model selection.
"""

from enum import Enum

from django.db import models


class ModelType(Enum):
    """Model type enumeration."""

    CHAT = "Chat"
    EMBEDDING = "Embedding"


class LLMModelConfig(models.Model):
    """LLM Model configuration - Django ORM.

    Production-grade model for storing LLM provider configurations.
    Supports capability-based routing for intelligent model selection.
    """

    MODEL_TYPE_CHOICES = [
        ("chat", "Chat"),
        ("embedding", "Embedding"),
    ]

    COST_TIER_CHOICES = [
        ("free", "Free"),
        ("low", "Low Cost"),
        ("standard", "Standard"),
        ("premium", "Premium"),
    ]

    # Core identification
    name = models.CharField(max_length=255, unique=True, db_index=True)
    display_name = models.CharField(max_length=255, blank=True, default="")
    model_type = models.CharField(max_length=20, choices=MODEL_TYPE_CHOICES, default="chat")
    provider = models.CharField(max_length=100, db_index=True)
    api_base = models.URLField(blank=True, default="")

    # Capability-based routing (NEW)
    capabilities = models.JSONField(
        default=list,
        blank=True,
        help_text="List of capabilities: text, vision, video, audio, code, long_context, etc.",
    )
    priority = models.IntegerField(
        default=50,
        help_text="Routing priority (0-100). Higher = preferred when multiple models match.",
    )
    cost_tier = models.CharField(
        max_length=20,
        choices=COST_TIER_CHOICES,
        default="standard",
        help_text="Cost tier for budget-aware routing.",
    )
    domains = models.JSONField(
        default=list,
        blank=True,
        help_text="Specialized domains: medical, legal, code, scientific, etc.",
    )

    # Limits and constraints
    ctx_length = models.IntegerField(default=0, help_text="Max context length in tokens")
    limit_requests = models.IntegerField(default=0, help_text="Rate limit: requests/min")
    limit_input = models.IntegerField(default=0, help_text="Max input tokens per request")
    limit_output = models.IntegerField(default=0, help_text="Max output tokens per request")

    # Legacy field (kept for backward compat, derived from capabilities)
    vision = models.BooleanField(default=False)

    # Configuration
    kwargs = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta class implementation."""

        db_table = "llm_model_configs"
        verbose_name = "LLM Model Configuration"
        verbose_name_plural = "LLM Model Configurations"
        ordering = ["-priority", "provider", "name"]
        indexes = [
            models.Index(fields=["is_active", "priority"]),
            models.Index(fields=["provider", "is_active"]),
        ]

    def __str__(self):
        """Return string representation."""
        return f"{self.provider}/{self.name}"

    def build_kwargs(self) -> dict:
        """Build kwargs dict with api_base if configured."""
        kwargs = dict(self.kwargs) if self.kwargs else {}
        if self.api_base and "api_base" not in kwargs:
            kwargs["api_base"] = self.api_base
        return kwargs

    def has_capability(self, capability: str) -> bool:
        """Check if model has a specific capability."""
        return capability in (self.capabilities or [])

    def has_all_capabilities(self, required: set) -> bool:
        """Check if model has all required capabilities."""
        return required.issubset(set(self.capabilities or []))

    def save(self, *args, **kwargs):
        """Sync vision field with capabilities for backward compat."""
        if self.capabilities:
            self.vision = "vision" in self.capabilities
        super().save(*args, **kwargs)


# Backward compatibility alias for migration period
ModelConfig = LLMModelConfig
