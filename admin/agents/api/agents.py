"""Agent Admin API - Django Ninja Router.

Pure Django ORM implementation for agent user management.

"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional
from uuid import uuid4

from ninja import Query, Router
from pydantic import BaseModel

from admin.aaas.models import AgentRole, AgentUser
from admin.common.auth import AuthBearer
from admin.core.authz import AGENT_ASSIGNABLE_ROLES
from admin.common.exceptions import ForbiddenError, NotFoundError, ValidationError
from admin.common.responses import api_response, paginated_response
from services.common.authorization import authorize_sync

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


# Roles assignable on an agent. Ownership is transferred, not assigned, so
# `agent_owner` is deliberately absent — see authz.AGENT_ASSIGNABLE_ROLES.
VALID_ROLES = list(AGENT_ASSIGNABLE_ROLES)


def _agent_user_to_schema(au: AgentUser) -> AgentUserSchema:
    """Convert AgentUser model to schema."""
    return AgentUserSchema(
        id=str(au.id),
        user_id=str(au.user_id),
        agent_id=str(au.agent_id),  # type: ignore[attr-defined]
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
    authorize_sync(request, action="agent:manage_users", resource="agents")
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
    authorize_sync(request, action="agent:manage_users", resource="agents")
    if payload.role not in VALID_ROLES:
        raise ValidationError(
            f"Invalid role. Must be one of: {VALID_ROLES}. 'agent_owner' is established by ownership transfer, not assignment.",
            field="role",
        )

    agent_user = AgentUser.objects.create(
        id=uuid4(),
        agent_id=agent_id,
        user_id=payload.user_id,
        role=payload.role,
    )

    logger.info("User %s added to agent %s as %s", payload.user_id, agent_id, payload.role)

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
    authorize_sync(request, action="agent:manage_users", resource="agents")
    if payload.role not in VALID_ROLES:
        raise ValidationError(
            f"Invalid role. Must be one of: {VALID_ROLES}",
            field="role",
        )

    try:
        agent_user = AgentUser.objects.get(agent_id=agent_id, user_id=user_id)
    except AgentUser.DoesNotExist:
        raise NotFoundError("agent user", user_id)

    # Cannot change the owner's role
    if agent_user.role == AgentRole.AGENT_OWNER:
        raise ForbiddenError("change role", "agent_owner")

    agent_user.role = payload.role
    agent_user.save()

    logger.info("User %s role changed to %s on agent %s", user_id, payload.role, agent_id)

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
    authorize_sync(request, action="agent:manage_users", resource="agents")
    try:
        agent_user = AgentUser.objects.get(agent_id=agent_id, user_id=user_id)
    except AgentUser.DoesNotExist:
        raise NotFoundError("agent user", user_id)

    # Cannot remove the owner
    if agent_user.role == AgentRole.AGENT_OWNER:
        raise ForbiddenError("remove", "agent_owner")

    agent_user.delete()
    logger.info("User %s removed from agent %s", user_id, agent_id)

    return api_response(
        {"agent_id": agent_id, "user_id": user_id}, message="User removed from agent"
    )


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
    authorize_sync(request, action="agent:manage_users", resource="agents")
    # Find current owner
    try:
        current_owner = AgentUser.objects.get(agent_id=agent_id, role=AgentRole.AGENT_OWNER)
    except AgentUser.DoesNotExist:
        raise NotFoundError("agent owner", agent_id)

    # Find new owner
    try:
        new_owner = AgentUser.objects.get(agent_id=agent_id, user_id=payload.new_owner_id)
    except AgentUser.DoesNotExist:
        raise NotFoundError("new owner", payload.new_owner_id)

    # Transfer ownership
    current_owner.role = AgentRole.AGENT_OPERATOR
    current_owner.save()

    new_owner.role = AgentRole.AGENT_OWNER
    new_owner.save()

    logger.info("Agent %s ownership transferred to %s", agent_id, payload.new_owner_id)

    return api_response(
        {
            "agent_id": agent_id,
            "new_owner_id": payload.new_owner_id,
            "previous_owner_role": "operator",
        },
        message="Ownership transferred",
    )
