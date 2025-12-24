"""LLM models - 100% Django ORM.

VIBE Compliant - Real Django models, no placeholders, no TODOs.
"""

from django.db import models
from enum import Enum


class ModelType(Enum):
    """Model type enumeration."""

    CHAT = "Chat"
    EMBEDDING = "Embedding"


class LLMModelConfig(models.Model):
    """LLM Model configuration - Django ORM.
    
    Production-grade model for storing LLM provider configurations.
    Replaces legacy dataclass with real database persistence.
    """

    MODEL_TYPE_CHOICES = [
        ("chat", "Chat"),
        ("embedding", "Embedding"),
    ]

    name = models.CharField(max_length=255, unique=True, db_index=True)
    model_type = models.CharField(max_length=20, choices=MODEL_TYPE_CHOICES, default="chat")
    provider = models.CharField(max_length=100, db_index=True)
    api_base = models.URLField(blank=True, default="")
    ctx_length = models.IntegerField(default=0)
    limit_requests = models.IntegerField(default=0)
    limit_input = models.IntegerField(default=0)
    limit_output = models.IntegerField(default=0)
    vision = models.BooleanField(default=False)
    kwargs = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "llm_model_configs"
        verbose_name = "LLM Model Configuration"
        verbose_name_plural = "LLM Model Configurations"
        ordering = ["provider", "name"]

    def __str__(self):
        return f"{self.provider}/{self.name}"

    def build_kwargs(self) -> dict:
        """Build kwargs dict with api_base if configured."""
        kwargs = dict(self.kwargs) if self.kwargs else {}
        if self.api_base and "api_base" not in kwargs:
            kwargs["api_base"] = self.api_base
        return kwargs


# Backward compatibility alias for migration period
ModelConfig = LLMModelConfig
