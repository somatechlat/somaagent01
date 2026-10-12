"""Soma Platform Admin Models Package.

Django-style models package - import all models here for Django's model discovery.
This follows Django's recommended pattern for splitting large models.py files.

Usage:
    from admin.platform.models import Tenant, Agent
"""

from admin.platform.models.agents import Agent, AgentUser
from admin.platform.models.audit import AuditLog
from admin.platform.models.choices import (
    AgentRole,
    AgentStatus,
    TenantRole,
    TenantStatus,
)
# Local identity (Standalone credential record)
from admin.platform.models.identity import LocalIdentity
from admin.platform.models.session import LocalSession
# Profile models
from admin.platform.models.profiles import (
    AdminProfile,
    ApiKey,
    TenantSettings,
    UserPreferences,
    UserSession,
)
from admin.platform.models.tenants import Tenant, TenantUser


# Django model discovery - all models must be listed here
__all__ = [
    # Choices
    "TenantStatus",
    "AgentStatus",
    "TenantRole",
    "AgentRole",
    # Models
    "Tenant",
    "TenantUser",
    "Agent",
    "AgentUser",
    "AuditLog",
    # Profile Models
    "AdminProfile",
    "TenantSettings",
    "UserPreferences",
    "UserSession",
    "ApiKey",
    "LocalIdentity",
    "LocalSession",
]
