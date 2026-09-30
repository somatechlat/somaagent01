"""AAAS Admin Model Choices (Enums)."""

from django.db import models


class TenantStatus(models.TextChoices):
    """Tenant lifecycle status."""

    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"


class AgentStatus(models.TextChoices):
    """Agent instance status."""

    ACTIVE = "active", "Active"
    PAUSED = "paused", "Paused"
    ARCHIVED = "archived", "Archived"


class TenantRole(models.TextChoices):
    """Roles within a tenant organization.

    These are exactly the organization-scoped authorization roles defined in
    ``admin.core.authz``. The stored value is the role name the permission
    catalog is keyed on, so a membership record resolves to authority without
    a translation table — a translation table is where the old vocabulary
    drifted and a subject could be denied by one call site and allowed by
    another.

    ``SYSADMIN`` is provisioned at install or by break-glass procedure and is
    never offered in a role-assignment control. See
    ``authz.PROVISIONED_ROLES``.
    """

    SYSADMIN = "sysadmin", "System Administrator"
    ORG_ADMIN = "org_admin", "Organization Administrator"
    DEVELOPER = "developer", "Developer"
    TRAINER = "trainer", "Trainer"
    MEMBER = "member", "Member"
    AUDITOR = "auditor", "Auditor"


class AgentRole(models.TextChoices):
    """Roles for agent access.

    Exactly the agent-scoped authorization roles from ``admin.core.authz``.
    ``AGENT_OWNER`` is established by an ownership transfer, not by a role
    edit, so it is not in ``authz.AGENT_ASSIGNABLE_ROLES``.
    """

    AGENT_OWNER = "agent_owner", "Agent Owner"
    AGENT_OPERATOR = "agent_operator", "Agent Operator"
    TRAINER = "trainer", "Trainer"
    MEMBER = "member", "Member"
