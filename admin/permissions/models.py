"""Django ORM Permission Models.


Granular RBAC stored in PostgreSQL.
Keycloak integration for authentication.

- Django Architect: ORM models, migrations
- Security Auditor: Least privilege, audit trail
- DevOps: DB performance, indexes
"""

from __future__ import annotations

import uuid

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

# =============================================================================
# ABSTRACT BASE
# =============================================================================


class TimestampedModel(models.Model):
    """Abstract base with timestamps."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta class implementation."""

        abstract = True


class TenantScopedModel(TimestampedModel):
    """Abstract base with tenant isolation."""

    tenant_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Tenant ID for multi-tenancy isolation",
    )

    class Meta:
        """Meta class implementation."""

        abstract = True


# =============================================================================
# PERMISSION RESOURCE
# =============================================================================


class PermissionResource(TimestampedModel):
    """A resource type that can be protected.

    Examples: agent, conversation, tenant, user, billing

    Django Architect: Maps to ContentType pattern.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)  # e.g., "agent"
    display_name = models.CharField(max_length=100)  # e.g., "Agents"
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=50, default="general"
    )  # e.g., "core", "admin", "billing"
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Optional link to Django model",
    )

    class Meta:
        """Meta class implementation."""

        db_table = "permissions_resource"
        ordering = ["category", "name"]

    def __str__(self):
        """Return string representation."""

        return self.name


# =============================================================================
# PERMISSION ACTION
# =============================================================================


class PermissionAction(TimestampedModel):
    """An action that can be performed on a resource.

    Examples: create, read, update, delete, execute, approve

    Security Auditor: Granular action definitions.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)  # e.g., "create"
    display_name = models.CharField(max_length=100)  # e.g., "Create"
    description = models.TextField(blank=True)
    is_destructive = models.BooleanField(default=False)  # For audit highlighting

    class Meta:
        """Meta class implementation."""

        db_table = "permissions_action"
        ordering = ["name"]

    def __str__(self):
        """Return string representation."""

        return self.name


# =============================================================================
# GRANULAR PERMISSION (resource:action)
# =============================================================================


class GranularPermission(TimestampedModel):
    """A specific permission = resource + action.

    Examples: agent:create, conversation:read, billing:manage

    Django Architect: ForeignKey to Resource and Action.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resource = models.ForeignKey(
        PermissionResource,
        on_delete=models.CASCADE,
        related_name="permissions",
    )
    action = models.ForeignKey(
        PermissionAction,
        on_delete=models.CASCADE,
        related_name="permissions",
    )
    codename = models.CharField(max_length=100, unique=True)  # e.g., "agent:create"
    description = models.TextField(blank=True)

    class Meta:
        """Meta class implementation."""

        db_table = "permissions_granular"
        unique_together = [["resource", "action"]]
        ordering = ["resource__name", "action__name"]

    def __str__(self):
        """Return string representation."""

        return self.codename

    def save(self, *args, **kwargs):
        """Execute save."""

        if not self.codename:
            self.codename = f"{self.resource.name}:{self.action.name}"
        super().save(*args, **kwargs)


# =============================================================================
# ROLE (Collection of Permissions)
# =============================================================================


class Role(TenantScopedModel):
    """A named collection of permissions.

    Can be system-defined (immutable) or custom (tenant-created).

    PM: Role builder interface.
    """

    SCOPE_CHOICES = [
        ("platform", "Platform-wide"),
        ("tenant", "Tenant-scoped"),
        ("agent", "Agent-scoped"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    description = models.TextField(blank=True)
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default="tenant")
    permissions = models.ManyToManyField(
        GranularPermission,
        related_name="roles",
        blank=True,
    )
    is_system = models.BooleanField(
        default=False,
        help_text="System roles cannot be modified or deleted",
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Default role for new users",
    )

    class Meta:
        """Meta class implementation."""

        db_table = "permissions_role"
        unique_together = [["tenant_id", "slug"]]
        ordering = ["name"]

    def __str__(self):
        """Return string representation."""

        return f"{self.name} ({self.tenant_id})"

    def has_permission(self, codename: str) -> bool:
        """Check if role has a specific permission."""
        return self.permissions.filter(codename=codename).exists()


# =============================================================================
# USER ROLE ASSIGNMENT
# =============================================================================


class UserRoleAssignment(TenantScopedModel):
    """Assigns a role to a user within a scope.

    Security Auditor: Who has what role, when, where.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=255, db_index=True)  # Keycloak user ID
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    scope_type = models.CharField(max_length=20, default="tenant")  # tenant, agent
    scope_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        help_text="ID of specific resource (e.g., agent_id)",
    )
    granted_by = models.CharField(max_length=255)  # Keycloak user ID of granter
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Meta class implementation."""

        db_table = "permissions_user_role"
        indexes = [
            models.Index(fields=["user_id", "tenant_id"]),
            models.Index(fields=["user_id", "scope_type", "scope_id"]),
        ]

    def __str__(self):
        """Return string representation."""

        return f"{self.user_id} -> {self.role.name}"

    @property
    def is_expired(self) -> bool:
        """Check if expired."""

        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at


# =============================================================================
# DIRECT PERMISSION GRANT
# =============================================================================


class PermissionGrant(TenantScopedModel):
    """Direct permission grant to a user (bypasses role).

    Security Auditor: For exceptions and temporary access.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=255, db_index=True)  # Keycloak user ID
    permission = models.ForeignKey(
        GranularPermission,
        on_delete=models.CASCADE,
        related_name="grants",
    )
    scope_type = models.CharField(max_length=20, default="tenant")
    scope_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    granted_by = models.CharField(max_length=255)
    reason = models.TextField(blank=True)  # Audit trail
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Meta class implementation."""

        db_table = "permissions_grant"
        indexes = [
            models.Index(fields=["user_id", "tenant_id"]),
            models.Index(fields=["user_id", "permission"]),
        ]

    def __str__(self):
        """Return string representation."""

        return f"{self.user_id} -> {self.permission.codename}"


# =============================================================================
# PERMISSION CHECK LOG (Audit)
# =============================================================================


class PermissionCheckLog(models.Model):
    """Audit log for permission checks.

    Security Auditor: Who tried to access what, when.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    user_id = models.CharField(max_length=255, db_index=True)
    tenant_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    permission_codename = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=255, blank=True, null=True)
    allowed = models.BooleanField()
    reason = models.CharField(max_length=50)  # role, direct_grant, denied
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        """Meta class implementation."""

        db_table = "permissions_check_log"
        indexes = [
            models.Index(fields=["user_id", "timestamp"]),
            models.Index(fields=["tenant_id", "timestamp"]),
            models.Index(fields=["allowed", "timestamp"]),
        ]

    def __str__(self):
        """Return string representation."""

        status = "✓" if self.allowed else "✗"
        return f"{status} {self.user_id} -> {self.permission_codename}"


# =============================================================================
# PERMISSION SERVICE (Business Logic)
# =============================================================================


class PermissionService:
    """Django-based permission checking service.

    Django Architect: All logic in Django ORM.
    """

    @staticmethod
    def check_permission(
        user_id: str,
        permission_codename: str,
        tenant_id: str,
        scope_type: str = "tenant",
        scope_id: str | None = None,
    ) -> tuple[bool, str]:
        """Check if user has permission.

        Returns (allowed, reason).
        """
        # 1. Check direct grants first
        grant_query = PermissionGrant.objects.filter(
            user_id=user_id,
            tenant_id=tenant_id,
            permission__codename=permission_codename,
        ).filter(models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now()))

        if scope_id:
            grant_query = grant_query.filter(
                models.Q(scope_id=scope_id) | models.Q(scope_id__isnull=True)
            )

        if grant_query.exists():
            return (True, "direct_grant")

        # 2. Check role-based permissions
        role_query = UserRoleAssignment.objects.filter(
            user_id=user_id,
            tenant_id=tenant_id,
            role__permissions__codename=permission_codename,
        ).filter(models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now()))

        if scope_id:
            role_query = role_query.filter(
                models.Q(scope_id=scope_id) | models.Q(scope_id__isnull=True)
            )

        if role_query.exists():
            return (True, "role")

        return (False, "denied")

    @staticmethod
    def get_effective_permissions(
        user_id: str,
        tenant_id: str,
        scope_type: str = "tenant",
        scope_id: str | None = None,
    ) -> list[str]:
        """Get all permissions for a user."""
        permissions = set()

        # From roles
        roles = (
            UserRoleAssignment.objects.filter(
                user_id=user_id,
                tenant_id=tenant_id,
            )
            .filter(models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now()))
            .select_related("role")
            .prefetch_related("role__permissions")
        )

        for assignment in roles:
            for perm in assignment.role.permissions.all():
                permissions.add(perm.codename)

        # From direct grants
        grants = (
            PermissionGrant.objects.filter(
                user_id=user_id,
                tenant_id=tenant_id,
            )
            .filter(models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now()))
            .select_related("permission")
        )

        for grant in grants:
            permissions.add(grant.permission.codename)

        return sorted(permissions)
