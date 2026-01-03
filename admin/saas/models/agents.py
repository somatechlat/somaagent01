"""Agent and AgentUser Models.

VIBE COMPLIANT - Multi-tenant isolation, flexible config via JSONB.
Per SAAS_ADMIN_SRS.md Section 4.5, 4.6
"""

import uuid

from django.db import models

from admin.saas.models.choices import AgentRole, AgentStatus
from admin.saas.models.tenants import Tenant


class Agent(models.Model):
    """AI Agent instance within a tenant.

    Each agent has its own configuration, capabilities, and user assignments.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="agents")

    name = models.CharField(max_length=100, help_text="Agent display name")

    slug = models.SlugField(max_length=100, help_text="URL-safe identifier within tenant")

    description = models.TextField(blank=True, help_text="Agent purpose/description")

    status = models.CharField(
        max_length=20, choices=AgentStatus.choices, default=AgentStatus.ACTIVE, db_index=True
    )

    # Configuration (JSONB for flexible agent settings)
    config = models.JSONField(default=dict, blank=True, help_text="Agent-specific configuration")

    # Feature settings specific to this agent
    feature_settings = models.JSONField(
        default=dict, blank=True, help_text="Feature configuration for this agent"
    )

    # Skin/Theme
    skin_id = models.UUIDField(null=True, blank=True, help_text="Associated skin/theme ID")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "agents"
        ordering = ["-created_at"]
        unique_together = [["tenant", "slug"]]
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["status"]),
            models.Index(fields=["-created_at"]),
        ]
        verbose_name = "Agent"
        verbose_name_plural = "Agents"

    def __str__(self):
        return f"{self.name} ({self.tenant.name})"

    def to_dict(self):
        """Serialize for API response."""
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "status": self.status,
            "config": self.config,
            "feature_settings": self.feature_settings,
            "skin_id": str(self.skin_id) if self.skin_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AgentUser(models.Model):
    """User assignment to an agent with role-based access."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="agent_users")

    user_id = models.UUIDField(db_index=True, help_text="Keycloak user ID")

    role = models.CharField(max_length=20, choices=AgentRole.choices, default=AgentRole.OPERATOR)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "agent_users"
        ordering = ["-created_at"]
        unique_together = [["agent", "user_id"]]
        indexes = [
            models.Index(fields=["user_id"]),
            models.Index(fields=["role"]),
        ]
        verbose_name = "Agent User"
        verbose_name_plural = "Agent Users"

    def __str__(self):
        return f"User {self.user_id} as {self.role} on {self.agent.name}"

    def to_dict(self):
        """Serialize for API response."""
        return {
            "id": str(self.id),
            "agent_id": str(self.agent_id),
            "user_id": str(self.user_id),
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
