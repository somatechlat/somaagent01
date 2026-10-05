"""AAAS Admin Model Choices (Enums).

``TenantRole`` is the **vocabulary** of the one role store. What a role
*grants* lives in ``admin.core.authz.ROLE_PERMISSIONS`` and nowhere else; this
enum only names the roles a ``TenantUser`` row may hold. The two are pinned
together at import (below) so a mismatch fails at boot rather than at request
time — a request-time mismatch is how one call site allowed what another
denied.
"""

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
    AGENT_OWNER = "agent_owner", "Agent Owner"
    AGENT_OPERATOR = "agent_operator", "Agent Operator"
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


# =============================================================================
# IMPORT-TIME VOCABULARY PIN
# =============================================================================
#
# The stored role vocabulary and the permission catalog must name the same
# roles. A mismatch here used to surface at request time as "this membership
# row holds a role the catalog has never heard of" — which is denial for the
# person who was provisioned, and a silent hole for anyone who provisioned a
# role the gate cannot see. Failing at import means the product does not boot
# with a drifted vocabulary. This is not a gate loosening: it is the gate
# refusing to run without its own vocabulary.
from admin.core.authz import ROLE_PERMISSIONS  # noqa: E402

_TENANT_ROLE_NAMES = {member.value for member in TenantRole}
_CATALOG_ROLE_NAMES = set(ROLE_PERMISSIONS)

if _TENANT_ROLE_NAMES != _CATALOG_ROLE_NAMES:
    _missing_in_catalog = sorted(_TENANT_ROLE_NAMES - _CATALOG_ROLE_NAMES)
    _missing_in_store = sorted(_CATALOG_ROLE_NAMES - _TENANT_ROLE_NAMES)
    raise RuntimeError(
        "TenantRole vocabulary and admin.core.authz.ROLE_PERMISSIONS disagree. "
        f"roles in TenantRole but not the catalog: {_missing_in_catalog}; "
        f"roles in the catalog but not TenantRole: {_missing_in_store}. "
        "A membership row can only hold a role the catalog defines, and the "
        "catalog can only grant to a role the store can hold. Fix both sides "
        "or neither; do not patch one."
    )
