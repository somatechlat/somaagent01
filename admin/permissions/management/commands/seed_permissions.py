"""Permission Seed Data - Default permissions and roles.


Seeds 65+ granular permissions and 8 predefined roles.

- Django Architect: Management command pattern
- Security Auditor: Least-privilege defaults
- PM: Role definitions for UI
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from admin.permissions.models import (
    GranularPermission,
    PermissionAction,
    PermissionResource,
    Role,
)

# =============================================================================
# SEED DATA DEFINITIONS
# =============================================================================


RESOURCES = {
    # Core Resources
    "platform": {"display_name": "Platform", "category": "admin"},
    "tenant": {"display_name": "Tenant", "category": "admin"},
    "user": {"display_name": "User", "category": "core"},
    # Agent Resources
    "agent": {"display_name": "Agent", "category": "core"},
    "conversation": {"display_name": "Conversation", "category": "core"},
    "memory": {"display_name": "Memory", "category": "core"},
    "tool": {"display_name": "Tool", "category": "core"},
    # Data Resources
    "file": {"display_name": "File", "category": "data"},
    "knowledge": {"display_name": "Knowledge Base", "category": "data"},
    "embedding": {"display_name": "Embedding", "category": "data"},
    # Operations Resources
    "apikey": {"display_name": "API Key", "category": "ops"},
    "webhook": {"display_name": "Webhook", "category": "ops"},
    "integration": {"display_name": "Integration", "category": "ops"},
    "workflow": {"display_name": "Workflow", "category": "ops"},
    # Admin Resources
    "audit": {"display_name": "Audit Log", "category": "admin"},
    "backup": {"display_name": "Backup", "category": "admin"},
    "billing": {"display_name": "Billing", "category": "admin"},
    "secrets": {"display_name": "Secrets", "category": "admin"},
}


ACTIONS = {
    # CRUD Actions
    "create": {"display_name": "Create", "is_destructive": False},
    "read": {"display_name": "Read", "is_destructive": False},
    "update": {"display_name": "Update", "is_destructive": False},
    "delete": {"display_name": "Delete", "is_destructive": True},
    # Lifecycle Actions
    "start": {"display_name": "Start", "is_destructive": False},
    "stop": {"display_name": "Stop", "is_destructive": False},
    "suspend": {"display_name": "Suspend", "is_destructive": True},
    "activate": {"display_name": "Activate", "is_destructive": False},
    # Management Actions
    "manage": {"display_name": "Manage", "is_destructive": False},
    "configure": {"display_name": "Configure", "is_destructive": False},
    "assign": {"display_name": "Assign", "is_destructive": False},
    "revoke": {"display_name": "Revoke", "is_destructive": True},
    # Data Actions
    "export": {"display_name": "Export", "is_destructive": False},
    "import": {"display_name": "Import", "is_destructive": False},
    "search": {"display_name": "Search", "is_destructive": False},
    "execute": {"display_name": "Execute", "is_destructive": False},
    # Special Actions
    "impersonate": {"display_name": "Impersonate", "is_destructive": True},
    "approve": {"display_name": "Approve", "is_destructive": False},
    "restore": {"display_name": "Restore", "is_destructive": False},
}


# Which actions apply to which resources
RESOURCE_ACTIONS = {
    "platform": ["manage", "read", "configure", "impersonate"],
    "tenant": ["create", "read", "update", "delete", "suspend", "activate", "manage"],
    "user": ["create", "read", "update", "delete", "assign", "revoke", "manage"],
    "agent": ["create", "read", "update", "delete", "start", "stop", "configure", "export"],
    "conversation": ["create", "read", "update", "delete", "search", "export"],
    "memory": ["create", "read", "update", "delete", "search", "export", "configure"],
    "tool": ["create", "read", "update", "delete", "execute", "approve"],
    "file": ["create", "read", "update", "delete", "export", "import"],
    "knowledge": ["create", "read", "update", "delete", "search", "import"],
    "embedding": ["create", "read", "delete", "search"],
    "apikey": ["create", "read", "revoke", "manage"],
    "webhook": ["create", "read", "update", "delete", "manage"],
    "integration": ["create", "read", "update", "delete", "configure"],
    "workflow": ["create", "read", "update", "delete", "execute", "manage"],
    "audit": ["read", "export", "configure"],
    "backup": ["create", "read", "delete", "restore", "configure"],
    "billing": ["read", "manage", "configure"],
    "secrets": ["create", "read", "update", "delete", "manage"],
}


PREDEFINED_ROLES = {
    "saas_super_admin": {
        "name": "SAAS Super Administrator",
        "description": "Full platform access (God Mode)",
        "scope": "platform",
        "permissions": ["*"],  # All permissions
    },
    "tenant_admin": {
        "name": "Tenant Administrator",
        "description": "Full tenant management",
        "scope": "tenant",
        "permissions": [
            "tenant:read",
            "tenant:update",
            "user:*",
            "agent:*",
            "conversation:*",
            "memory:*",
            "tool:*",
            "file:*",
            "apikey:*",
            "webhook:*",
            "integration:*",
            "audit:read",
            "backup:read",
            "billing:read",
        ],
    },
    "agent_owner": {
        "name": "Agent Owner",
        "description": "Full control of assigned agents",
        "scope": "agent",
        "permissions": [
            "agent:read",
            "agent:update",
            "agent:start",
            "agent:stop",
            "agent:configure",
            "agent:export",
            "conversation:*",
            "memory:*",
            "tool:read",
            "tool:execute",
            "file:create",
            "file:read",
        ],
    },
    "agent_operator": {
        "name": "Agent Operator",
        "description": "Operate agents, no config changes",
        "scope": "agent",
        "permissions": [
            "agent:read",
            "agent:start",
            "agent:stop",
            "conversation:*",
            "memory:read",
            "memory:search",
            "tool:read",
            "tool:execute",
            "file:create",
            "file:read",
        ],
    },
    "user": {
        "name": "Standard User",
        "description": "Chat and basic access",
        "scope": "tenant",
        "permissions": [
            "agent:read",
            "conversation:create",
            "conversation:read",
            "memory:read",
            "file:create",
            "file:read",
        ],
    },
    "viewer": {
        "name": "Viewer",
        "description": "Read-only access",
        "scope": "tenant",
        "permissions": [
            "agent:read",
            "conversation:read",
            "memory:read",
            "file:read",
        ],
    },
    "billing_admin": {
        "name": "Billing Administrator",
        "description": "Manage billing only",
        "scope": "tenant",
        "permissions": [
            "billing:*",
            "tenant:read",
        ],
    },
    "security_auditor": {
        "name": "Security Auditor",
        "description": "Read-only security access",
        "scope": "tenant",
        "permissions": [
            "audit:read",
            "audit:export",
            "user:read",
            "apikey:read",
            "backup:read",
        ],
    },
}


class Command(BaseCommand):
    """Seed permission data.

    Usage:
        python manage.py seed_permissions
    """

    help = "Seed default permissions and roles"

    @transaction.atomic
    def handle(self, *args, **options):
        """Execute handle."""

        self.stdout.write("Seeding permissions...")

        # 1. Create resources
        resources = {}
        for name, data in RESOURCES.items():
            resource, created = PermissionResource.objects.get_or_create(
                name=name,
                defaults=data,
            )
            resources[name] = resource
            if created:
                self.stdout.write(f"  Created resource: {name}")

        # 2. Create actions
        actions = {}
        for name, data in ACTIONS.items():
            action, created = PermissionAction.objects.get_or_create(
                name=name,
                defaults=data,
            )
            actions[name] = action
            if created:
                self.stdout.write(f"  Created action: {name}")

        # 3. Create granular permissions
        perm_count = 0
        for resource_name, action_names in RESOURCE_ACTIONS.items():
            resource = resources[resource_name]
            for action_name in action_names:
                action = actions[action_name]
                codename = f"{resource_name}:{action_name}"
                perm, created = GranularPermission.objects.get_or_create(
                    resource=resource,
                    action=action,
                    defaults={"codename": codename},
                )
                if created:
                    perm_count += 1

        self.stdout.write(f"  Created {perm_count} granular permissions")

        # 4. Create system roles (tenant_id = "*" for system roles)
        for slug, data in PREDEFINED_ROLES.items():
            role, created = Role.objects.get_or_create(
                tenant_id="*",  # System-wide
                slug=slug,
                defaults={
                    "name": data["name"],
                    "description": data["description"],
                    "scope": data["scope"],
                    "is_system": True,
                },
            )

            if created:
                # Add permissions to role (skip * wildcards for now)
                for perm_pattern in data["permissions"]:
                    if perm_pattern == "*":
                        # Add all permissions
                        role.permissions.add(*GranularPermission.objects.all())
                    elif perm_pattern.endswith(":*"):
                        # Add all actions for resource
                        resource_name = perm_pattern[:-2]
                        role.permissions.add(
                            *GranularPermission.objects.filter(resource__name=resource_name)
                        )
                    else:
                        # Add specific permission
                        try:
                            perm = GranularPermission.objects.get(codename=perm_pattern)
                            role.permissions.add(perm)
                        except GranularPermission.DoesNotExist:
                            pass

                self.stdout.write(f"  Created role: {data['name']}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded: {len(RESOURCES)} resources, "
                f"{len(ACTIONS)} actions, {perm_count}+ permissions, "
                f"{len(PREDEFINED_ROLES)} roles"
            )
        )
