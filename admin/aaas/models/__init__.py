"""AAAS Admin Models Package.

Django-style models package - import all models here for Django's model discovery.
This follows Django's recommended pattern for splitting large models.py files.

Usage:
    from admin.aaas.models import Tenant, Agent, SubscriptionTier
"""

# Import all choices first (no dependencies)
from admin.aaas.models.agents import Agent, AgentUser
from admin.aaas.models.audit import AuditLog
from admin.aaas.models.choices import (
    AgentRole,
    AgentStatus,
    BillingInterval,
    FeatureCategory,
    QuotaEnforcementPolicy,
    TenantRole,
    TenantStatus,
)
from admin.aaas.models.features import FeatureProvider, AaasFeature, TierFeature

# Profile models
from admin.aaas.models.profiles import (
    AdminProfile,
    ApiKey,
    TenantSettings,
    UserPreferences,
    UserSession,
)
from admin.aaas.models.tenants import Tenant, TenantUser

# Import models in dependency order
from admin.aaas.models.tiers import SubscriptionTier
from admin.aaas.models.usage import UsageRecord

# Django model discovery - all models must be listed here
__all__ = [
    # Choices
    "TenantStatus",
    "AgentStatus",
    "TenantRole",
    "AgentRole",
    "BillingInterval",
    "QuotaEnforcementPolicy",
    "FeatureCategory",
    # Models
    "SubscriptionTier",
    "Tenant",
    "TenantUser",
    "Agent",
    "AgentUser",
    "UsageRecord",
    "AaasFeature",
    "TierFeature",
    "FeatureProvider",
    "AuditLog",
    # Profile Models
    "AdminProfile",
    "TenantSettings",
    "UserPreferences",
    "UserSession",
    "ApiKey",
]
