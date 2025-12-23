"""Agent Admin API - Django Ninja Router.

Pure Django ORM implementation for agent user management.
VIBE COMPLIANT - No SQLAlchemy.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional
from uuid import uuid4

from django.db import transaction
from django.db.models import Count
from django.http import HttpRequest
from ninja import Query, Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer
from admin.common.exceptions import ForbiddenError, NotFoundError, ValidationError
from admin.common.responses import api_response, paginated_response
from admin.saas.models import AgentRole, AgentUser

router = Router(tags=["agents"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class AgentUserSchema(BaseModel):
    """Agent-level user schema."""

    id: str
    user_id: str
    agent_id: str
    role: str
    added_at: datetime
    email: str = ""
    name: str = ""
    last_active: Optional[datetime] = None


class AddAgentUserRequest(BaseModel):
    """Add user to agent request."""

    user_id: str
    role: str = "operator"


class AgentRoleUpdateRequest(BaseModel):
    """Update agent role request."""

    role: str


class TransferOwnershipRequest(BaseModel):
    """Transfer agent ownership request."""

    new_owner_id: str


# Valid agent roles (excluding manager which is owner-equivalent)
VALID_ROLES = ["operator", "viewer"]


def _agent_user_to_schema(au: AgentUser) -> AgentUserSchema:
    """Convert AgentUser model to schema."""
    return AgentUserSchema(
        id=str(au.id),
        user_id=str(au.user_id),
        agent_id=str(au.agent_id),
        role=au.role,
        added_at=au.created_at,
    )


# =============================================================================
# AGENT USER MANAGEMENT ENDPOINTS
# =============================================================================


@router.get(
    "/{agent_id}/users",
    summary="List users for an agent",
    auth=AuthBearer(),
)
def list_agent_users(
    request,
    agent_id: str,
    role: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> dict:
    """List all users assigned to an agent with their roles."""
    qs = AgentUser.objects.filter(agent_id=agent_id)

    if role:
        qs = qs.filter(role=role)

    total = qs.count()
    offset = (page - 1) * per_page
    users = qs.order_by("-created_at")[offset : offset + per_page]

    return paginated_response(
        items=[_agent_user_to_schema(u).model_dump() for u in users],
        total=total,
        page=page,
        page_size=per_page,
    )


@router.post(
    "/{agent_id}/users",
    summary="Add user to agent",
    auth=AuthBearer(),
)

def add_agent_user(
    request,
    agent_id: str,
    payload: AddAgentUserRequest,
) -> dict:
    """Add a user to an agent with specified role."""
    if payload.role not in VALID_ROLES:
        raise ValidationError(
            f"Invalid role. Must be one of: {VALID_ROLES}. 'manager' cannot be assigned.",
            field="role",
        )

    agent_user = AgentUser.objects.create(
        id=uuid4(),
        agent_id=agent_id,
        user_id=payload.user_id,
        role=payload.role,
    )

    logger.info(f"User {payload.user_id} added to agent {agent_id} as {payload.role}")

    return api_response(
        {
            "id": str(agent_user.id),
            "user_id": payload.user_id,
            "agent_id": agent_id,
            "role": payload.role,
            "added_at": agent_user.created_at.isoformat(),
        },
        message="User added to agent",
    )


@router.put(
    "/{agent_id}/users/{user_id}/role",
    summary="Change user role on agent",
    auth=AuthBearer(),
)

def change_agent_role(
    request,
    agent_id: str,
    user_id: str,
    payload: AgentRoleUpdateRequest,
) -> dict:
    """Change a user's role on an agent."""
    if payload.role not in VALID_ROLES:
        raise ValidationError(
            f"Invalid role. Must be one of: {VALID_ROLES}",
            field="role",
        )

    try:
        agent_user = AgentUser.objects.get(agent_id=agent_id, user_id=user_id)
    except AgentUser.DoesNotExist:
        raise NotFoundError("agent user", user_id)

    # Cannot change manager role
    if agent_user.role == AgentRole.MANAGER:
        raise ForbiddenError("change role", "manager")

    agent_user.role = payload.role
    agent_user.save()

    logger.info(f"User {user_id} role changed to {payload.role} on agent {agent_id}")

    return api_response(
        {"agent_id": agent_id, "user_id": user_id, "role": payload.role},
        message="Role updated",
    )


@router.delete(
    "/{agent_id}/users/{user_id}",
    summary="Remove user from agent",
    auth=AuthBearer(),
)

def remove_agent_user(
    request,
    agent_id: str,
    user_id: str,
) -> dict:
    """Remove a user from an agent."""
    try:
        agent_user = AgentUser.objects.get(agent_id=agent_id, user_id=user_id)
    except AgentUser.DoesNotExist:
        raise NotFoundError("agent user", user_id)

    # Cannot remove manager
    if agent_user.role == AgentRole.MANAGER:
        raise ForbiddenError("remove", "manager")

    agent_user.delete()
    logger.info(f"User {user_id} removed from agent {agent_id}")

    return api_response({"agent_id": agent_id, "user_id": user_id}, message="User removed from agent")


@router.post(
    "/{agent_id}/transfer-ownership",
    summary="Transfer agent ownership",
    auth=AuthBearer(),
)

def transfer_ownership(
    request,
    agent_id: str,
    payload: TransferOwnershipRequest,
) -> dict:
    """Transfer agent ownership to another user."""
    # Find current manager
    try:
        current_manager = AgentUser.objects.get(agent_id=agent_id, role=AgentRole.MANAGER)
    except AgentUser.DoesNotExist:
        raise NotFoundError("agent manager", agent_id)

    # Find new manager
    try:
        new_manager = AgentUser.objects.get(agent_id=agent_id, user_id=payload.new_owner_id)
    except AgentUser.DoesNotExist:
        raise NotFoundError("new manager", payload.new_owner_id)

    # Transfer ownership
    current_manager.role = AgentRole.OPERATOR
    current_manager.save()

    new_manager.role = AgentRole.MANAGER
    new_manager.save()

    logger.info(f"Agent {agent_id} ownership transferred to {payload.new_owner_id}")

    return api_response(
        {
            "agent_id": agent_id,
            "new_owner_id": payload.new_owner_id,
            "previous_owner_role": "operator",
        },
        message="Ownership transferred",
    )
