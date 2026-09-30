"""Tenant and TenantUser models.

``Tenant`` is the **data-partition boundary**: every child resource carries
``tenant_id`` so one organisation's memories, agents and audit rows cannot be
read by another. That isolation is a security property and it stays.

It is not a product tenancy. There is no subscription tier, no billing
contact, no trial clock and no churn lifecycle: SomaBrain and the agent are
HTTP + containers, not a commercial offering.

``TenantUser`` is the org role-assignment record that
``admin.core.permission_matrix`` and ``admin.core.agentiq.unified_gate`` read
fail-closed to decide what a principal may do. It is RBAC state, not a seat.
"""

import uuid
from typing import TYPE_CHECKING

from django.db import models

from admin.aaas.models.choices import TenantRole, TenantStatus

if TYPE_CHECKING:
    from django.db.models import Manager

    from admin.aaas.models.agents import Agent


class Tenant(models.Model):
    """Organisation boundary. One row per partition.

    ``id`` is the partition key referenced as ``tenant_id`` across agents,
    capsules, bridges and audit rows.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=100, help_text="Organisation name")

    slug = models.SlugField(max_length=100, unique=True, help_text="URL-safe identifier for tenant")

    status = models.CharField(
        max_length=20,
        choices=TenantStatus.choices,
        default=TenantStatus.ACTIVE,
        db_index=True,
    )

    # Identity-provider realm for this partition's principals.
    keycloak_realm = models.CharField(
        max_length=100, blank=True, help_text="Keycloak realm for this tenant"
    )

    # Per-partition behaviour knobs. Any ceiling that used to live on a plan
    # row is a deployment setting (Django settings), not a tenant column.
    feature_overrides = models.JSONField(
        default=dict, blank=True, help_text="Per-tenant feature configuration overrides"
    )

    metadata = models.JSONField(
        default=dict, blank=True, help_text="Arbitrary metadata for integrations"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    if TYPE_CHECKING:
        agents: Manager["Agent"]
        users: Manager["TenantUser"]

    class Meta:
        """Meta class implementation."""

        db_table = "tenants"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["status"]),
            models.Index(fields=["-created_at"]),
        ]
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"

    def __str__(self):
        """Return string representation."""

        return f"{self.name} ({self.status})"

    def to_dict(self):
        """Serialize for API response."""
        return {
            "id": str(self.id),
            "name": self.name,
            "slug": self.slug,
            "status": self.status,
            "keycloak_realm": self.keycloak_realm,
            "feature_overrides": self.feature_overrides,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class TenantUser(models.Model):
    """Org role assignment: which principal holds which catalog role.

    This row is what RBAC reads. It is not a seat, not an invitation and not
    a product membership.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="users")

    user_id = models.UUIDField(db_index=True, help_text="Principal ID in the identity provider")

    email = models.EmailField(help_text="User email")

    display_name = models.CharField(max_length=200, blank=True, help_text="User display name")

    role = models.CharField(max_length=20, choices=TenantRole.choices, default=TenantRole.MEMBER)

    is_active = models.BooleanField(default=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Meta class implementation."""

        db_table = "tenant_users"
        ordering = ["-created_at"]
        unique_together = [["tenant", "user_id"]]
        indexes = [
            models.Index(fields=["user_id"]),
            models.Index(fields=["email"]),
            models.Index(fields=["role"]),
            models.Index(fields=["is_active"]),
        ]
        verbose_name = "Tenant User"
        verbose_name_plural = "Tenant Users"

    def __str__(self):
        """Return string representation."""

        return f"{self.email} ({self.role} in {self.tenant.name})"

    def to_dict(self):
        """Serialize for API response."""
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),  # type: ignore[reportAttributeAccessIssue]
            "user_id": str(self.user_id),
            "email": self.email,
            "display_name": self.display_name,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }
