"""LLM models - migrated from root models.py to Django ORM."""

from django.db import models as django_models
from dataclasses import dataclass, field
from enum import Enum


class ModelType(Enum):
    """Model type enumeration."""

    CHAT = "Chat"
    EMBEDDING = "Embedding"


@dataclass
class ModelConfig:
    """Model configuration dataclass - will be Django model in future refactor.

    Currently maintaining backward compatibility as dataclass.
    TODO: Convert to full Django ORM model with database persistence.
    """

    type: ModelType
    provider: str
    name: str
    api_base: str = ""
    ctx_length: int = 0
    limit_requests: int = 0
    limit_input: int = 0
    limit_output: int = 0
    vision: bool = False
    kwargs: dict = field(default_factory=dict)

    def build_kwargs(self):
        """Build kwargs dict with api_base if configured."""
        kwargs = self.kwargs.copy() or {}
        if self.api_base and "api_base" not in kwargs:
            kwargs["api_base"] = self.api_base
        return kwargs
