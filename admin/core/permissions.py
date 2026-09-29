"""
Read-side view over the permission catalog.

Answers "what does this principal hold" for conditional UI and payload
shaping. It never decides whether a request may proceed — that is
``services.common.authorization.authorize``, the one place a request is
allowed or refused. Keeping the question and the decision apart is what stops
a second authorization path from growing here again.

- No wildcards. Every granted authority is named.
- An unknown permission is held by nobody.

The permission names and the role grants live in ``admin.core.authz`` and
nowhere else. This module is the enforcement surface; it does not define
authority.

A wildcard permission (``"*"``) used to be supported here so that a super
admin role could grant everything. It cannot be audited — a permission trace
of "everything" is not a trace — so it is gone. There is no bypass path in
this module and there must never be one.
"""

import logging
from functools import wraps
from typing import Callable, List

from ninja.errors import HttpError

from admin.core.authz import (
    ROLE_PERMISSIONS,
    is_known_permission,
    permissions_for_roles,
)

logger = logging.getLogger(__name__)


def get_user_permissions(auth) -> List[str]:
    """Extract permissions from auth context.

    Resolves in this order, stopping at the first that yields authority:

    - JWT claims carrying an explicit ``permissions`` array
    - A user object exposing a ``permissions`` attribute
    - A user object exposing ``roles``, expanded through the role catalog
    - A user object exposing ``role_name``, expanded through the role catalog

    Returns an empty list when nothing is known about the subject. Absence of
    identity is absence of authority.
    """
    if auth is None:
        return []

    # If auth is a dict (JWT claims)
    if isinstance(auth, dict):
        declared = auth.get("permissions")
        if declared is not None:
            return [p for p in declared if is_known_permission(p)]
        return sorted(permissions_for_roles(auth.get("roles") or []))

    # If auth has permissions attribute
    if hasattr(auth, "permissions"):
        return [p for p in list(auth.permissions) if is_known_permission(p)]

    # If auth has roles, expand to permissions
    if hasattr(auth, "roles"):
        return sorted(permissions_for_roles(list(auth.roles)))

    # If auth is a user object with role_name
    if hasattr(auth, "role_name"):
        return sorted(permissions_for_roles([auth.role_name]))

    return []


def has_permission(auth, permission: str) -> bool:
    """Check if auth context has a specific permission.

    Useful for conditional logic in views. An unknown permission is never
    held.
    """
    if not is_known_permission(permission):
        return False
    return permission in get_user_permissions(auth)


def has_any_permission(auth, *permissions: str) -> bool:
    """Check if auth context has any of the specified permissions."""
    return any(has_permission(auth, p) for p in permissions)


def has_all_permissions(auth, *permissions: str) -> bool:
    """Check if auth context has all specified permissions.

    An empty requirement is not a grant of everything; it is a missing
    requirement and is denied.
    """
    if not permissions:
        return False
    return all(has_permission(auth, p) for p in permissions)


__all__ = [
    "ROLE_PERMISSIONS",
    "get_user_permissions",
    "has_all_permissions",
    "has_any_permission",
    "has_permission",
]
