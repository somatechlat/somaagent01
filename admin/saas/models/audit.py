"""Audit Log Model.


Per SAAS_ADMIN_SRS.md Section 4.8
"""

import uuid

from django.db import models

from admin.saas.models.tenants import Tenant


class AuditLog(models.Model):
    """Immutable audit trail for SAAS admin actions.

    Records all significant actions for compliance and debugging.
    This table is append-only - no updates or deletes.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Who
    actor_id = models.UUIDField(db_index=True, help_text="User ID who performed the action")

    actor_email = models.EmailField(blank=True, help_text="Actor email (denormalized for query)")

    # What tenant (null for super admin actions)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs"
    )

    # What action
    action = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Action type (e.g., 'tenant.created', 'tier.updated')",
    )

    # Target resource
    resource_type = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Resource type affected (e.g., 'tenant', 'agent', 'tier')",
    )

    resource_id = models.UUIDField(
        null=True, blank=True, db_index=True, help_text="ID of affected resource"
    )

    # Changes
    old_value = models.JSONField(null=True, blank=True, help_text="Previous state (for updates)")

    new_value = models.JSONField(null=True, blank=True, help_text="New state (for creates/updates)")

    # Context
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="Request IP address")

    user_agent = models.TextField(blank=True, help_text="Request user agent")

    request_id = models.CharField(
        max_length=100, blank=True, db_index=True, help_text="Correlation ID for request tracing"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        """Meta class implementation."""

        db_table = "audit_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["actor_id", "created_at"]),
            models.Index(fields=["tenant", "created_at"]),
            models.Index(fields=["action", "created_at"]),
            models.Index(fields=["resource_type", "resource_id"]),
            models.Index(fields=["-created_at"]),
        ]
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"

    def __str__(self):
        """Return string representation."""

        return f"{self.action} by {self.actor_email or self.actor_id} at {self.created_at}"

    def to_dict(self):
        """Serialize for API response."""
        return {
            "id": str(self.id),
            "actor_id": str(self.actor_id),
            "actor_email": self.actor_email,
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": str(self.resource_id) if self.resource_id else None,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "request_id": self.request_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
