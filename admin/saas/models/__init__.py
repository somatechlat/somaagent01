"""SAAS Admin Models Package.

Django-style models package - import all models here for Django's model discovery.
This follows Django's recommended pattern for splitting large models.py files.

Usage:
    from admin.saas.models import Tenant, Agent, SubscriptionTier
"""

# Import all choices first (no dependencies)
from admin.saas.models.choices import (
    TenantStatus,
    AgentStatus,
    TenantRole,
    AgentRole,
    BillingInterval,
    QuotaEnforcementPolicy,
    FeatureCategory,
)

# Import models in dependency order
from admin.saas.models.tiers import SubscriptionTier
from admin.saas.models.tenants import Tenant, TenantUser
from admin.saas.models.agents import Agent, AgentUser
from admin.saas.models.usage import UsageRecord
from admin.saas.models.features import SaasFeature, TierFeature, FeatureProvider
from admin.saas.models.audit import AuditLog


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
    "SaasFeature",
    "TierFeature",
    "FeatureProvider",
    "AuditLog",
]
