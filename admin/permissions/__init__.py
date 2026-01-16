"""Permissions module - RBAC access control."""

from admin.permissions.granular import router as granular_router

__all__ = ["granular_router"]
