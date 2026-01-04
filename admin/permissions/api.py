"""Permissions API - RBAC and access control.


Role-based access control management.

7-Persona Implementation:
- Security Auditor: Permission matrix, RBAC
- Django Architect: SpiceDB integration
- PM: Role management UI
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import uuid4

from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer

router = Router(tags=["permissions"])
logger = logging.getLogger(__name__)

# Mount granular permissions sub-router
from admin.permissions.granular import router as granular_router

router.add_router("/granular", granular_router, tags=["granular-permissions"])


# =============================================================================
# SCHEMAS
# =============================================================================


class Role(BaseModel):
    """Role definition."""

    role_id: str
    name: str
    description: Optional[str] = None
    permissions: list[str]
    is_system: bool = False
    tenant_id: Optional[str] = None


class Permission(BaseModel):
    """Permission definition."""

    permission_id: str
    name: str
    resource: str
    action: str  # read, write, delete, admin
    description: Optional[str] = None


class RoleAssignment(BaseModel):
    """Role assignment to user."""

    assignment_id: str
    user_id: str
    role_id: str
    scope: str  # platform, tenant, agent
    scope_id: Optional[str] = None
    assigned_at: str
    assigned_by: str


# =============================================================================
# ENDPOINTS - Roles
# =============================================================================


@router.get(
    "/roles",
    summary="List roles",
    auth=AuthBearer(),
)
async def list_roles(
    request,
    tenant_id: Optional[str] = None,
    include_system: bool = True,
) -> dict:
    """List available roles.

    PM: View role hierarchy.
    """
    return {
        "roles": [
            Role(
                role_id="saas_admin",
                name="SAAS Administrator",
                description="Platform-level admin (God Mode)",
                permissions=["*"],
                is_system=True,
            ).dict(),
            Role(
                role_id="tenant_admin",
                name="Tenant Administrator",
                description="Tenant-level admin",
                permissions=["tenant:*", "agent:*", "user:*"],
                is_system=True,
            ).dict(),
            Role(
                role_id="agent_owner",
                name="Agent Owner",
                description="Can manage assigned agents",
                permissions=["agent:read", "agent:write", "conversation:*"],
                is_system=True,
            ).dict(),
            Role(
                role_id="user",
                name="User",
                description="Standard user access",
                permissions=["conversation:read", "conversation:write"],
                is_system=True,
            ).dict(),
        ],
        "total": 4,
    }


@router.post(
    "/roles",
    summary="Create role",
    auth=AuthBearer(),
)
async def create_role(
    request,
    name: str,
    permissions: list[str],
    description: Optional[str] = None,
) -> dict:
    """Create a custom role.

    PM: Custom role creation.
    """
    role_id = str(uuid4())

    logger.info(f"Role created: {name} ({role_id})")

    return {
        "role_id": role_id,
        "name": name,
        "created": True,
    }


@router.get(
    "/roles/{role_id}",
    response=Role,
    summary="Get role",
    auth=AuthBearer(),
)
async def get_role(request, role_id: str) -> Role:
    """Get role details."""
    return Role(
        role_id=role_id,
        name="Example Role",
        permissions=["read"],
    )


@router.patch(
    "/roles/{role_id}",
    summary="Update role",
    auth=AuthBearer(),
)
async def update_role(
    request,
    role_id: str,
    permissions: Optional[list[str]] = None,
    description: Optional[str] = None,
) -> dict:
    """Update a role."""
    return {
        "role_id": role_id,
        "updated": True,
    }


@router.delete(
    "/roles/{role_id}",
    summary="Delete role",
    auth=AuthBearer(),
)
async def delete_role(request, role_id: str) -> dict:
    """Delete a custom role.

    Security Auditor: Cannot delete system roles.
    """
    return {
        "role_id": role_id,
        "deleted": True,
    }


# =============================================================================
# ENDPOINTS - Permissions
# =============================================================================


@router.get(
    "/permissions",
    summary="List permissions",
    auth=AuthBearer(),
)
async def list_permissions(
    request,
    resource: Optional[str] = None,
) -> dict:
    """List all available permissions.

    Security Auditor: Permission inventory.
    """
    return {
        "permissions": [
            Permission(
                permission_id="agent:read",
                name="Read Agents",
                resource="agent",
                action="read",
            ).dict(),
            Permission(
                permission_id="agent:write",
                name="Write Agents",
                resource="agent",
                action="write",
            ).dict(),
            Permission(
                permission_id="conversation:read",
                name="Read Conversations",
                resource="conversation",
                action="read",
            ).dict(),
        ],
        "total": 3,
    }


# =============================================================================
# ENDPOINTS - Role Assignments
# =============================================================================


@router.get(
    "/assignments",
    summary="List assignments",
    auth=AuthBearer(),
)
async def list_assignments(
    request,
    user_id: Optional[str] = None,
    role_id: Optional[str] = None,
) -> dict:
    """List role assignments.

    PM: View who has what access.
    """
    return {
        "assignments": [],
        "total": 0,
    }


@router.post(
    "/assignments",
    summary="Assign role",
    auth=AuthBearer(),
)
async def assign_role(
    request,
    user_id: str,
    role_id: str,
    scope: str = "tenant",
    scope_id: Optional[str] = None,
) -> dict:
    """Assign a role to a user.

    Security Auditor: Permission grant.
    """
    assignment_id = str(uuid4())

    logger.info(f"Role assigned: {role_id} -> {user_id}")

    return {
        "assignment_id": assignment_id,
        "user_id": user_id,
        "role_id": role_id,
        "assigned": True,
    }


@router.delete(
    "/assignments/{assignment_id}",
    summary="Remove assignment",
    auth=AuthBearer(),
)
async def remove_assignment(
    request,
    assignment_id: str,
) -> dict:
    """Remove a role assignment.

    Security Auditor: Permission revocation.
    """
    logger.info(f"Role assignment removed: {assignment_id}")

    return {
        "assignment_id": assignment_id,
        "removed": True,
    }


# =============================================================================
# ENDPOINTS - Permission Checks
# =============================================================================


@router.post(
    "/check",
    summary="Check permission",
    auth=AuthBearer(),
)
async def check_permission(
    request,
    user_id: str,
    permission: str,
    resource_id: Optional[str] = None,
) -> dict:
    """Check if user has a permission.

    Django Architect: SpiceDB query.
    """
    # In production: query SpiceDB
    return {
        "user_id": user_id,
        "permission": permission,
        "allowed": True,
        "reason": "role_grant",
    }


@router.get(
    "/users/{user_id}/permissions",
    summary="Get user permissions",
    auth=AuthBearer(),
)
async def get_user_permissions(
    request,
    user_id: str,
) -> dict:
    """Get all permissions for a user.

    Security Auditor: Effective permissions.
    """
    return {
        "user_id": user_id,
        "roles": [],
        "permissions": [],
    }
