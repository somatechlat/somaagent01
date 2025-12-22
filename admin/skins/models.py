"""AgentSkin Models for Django Admin.

VIBE COMPLIANT:
- Real Django model (no stubs)
- JSONB for variables storage
- Multi-tenant isolation via tenant_id

Per AgentSkin UIX T8 (TR-AGS-005)
"""

import uuid
from django.db import models
from django.core.validators import RegexValidator

# Semver pattern validator
semver_validator = RegexValidator(
    regex=r'^\d+\.\d+\.\d+$',
    message='Version must follow semantic versioning (e.g., 1.0.0)'
)


class AgentSkin(models.Model):
    """Theme/skin definition with CSS variables."""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the skin"
    )
    
    tenant_id = models.UUIDField(
        db_index=True,
        help_text="Tenant this skin belongs to (for multi-tenancy)"
    )
    
    name = models.CharField(
        max_length=50,
        help_text="Display name for the skin"
    )
    
    description = models.CharField(
        max_length=200,
        blank=True,
        help_text="Brief description of the skin"
    )
    
    version = models.CharField(
        max_length=20,
        validators=[semver_validator],
        default="1.0.0",
        help_text="Semantic version (e.g., 1.0.0)"
    )
    
    author = models.CharField(
        max_length=100,
        blank=True,
        help_text="Author or creator of the skin"
    )
    
    variables = models.JSONField(
        default=dict,
        help_text="CSS custom properties as key-value pairs"
    )
    
    changelog = models.JSONField(
        default=list,
        blank=True,
        help_text="Version history with changes"
    )
    
    is_approved = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether skin is approved for general use"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the skin was created"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When the skin was last updated"
    )
    
    class Meta:
        db_table = 'agent_skins'
        ordering = ['-created_at']
        unique_together = [['tenant_id', 'name']]
        indexes = [
            models.Index(fields=['tenant_id']),
            models.Index(fields=['is_approved']),
            models.Index(fields=['name']),
            models.Index(fields=['-created_at']),
        ]
        verbose_name = 'Agent Skin'
        verbose_name_plural = 'Agent Skins'
    
    def __str__(self):
        return f"{self.name} v{self.version}"
    
    def to_dict(self):
        """Serialize to dictionary for API response."""
        return {
            'id': str(self.id),
            'tenant_id': str(self.tenant_id),
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'author': self.author,
            'variables': self.variables,
            'changelog': self.changelog,
            'is_approved': self.is_approved,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
