"""SAAS Django Admin - Main entry point.

Split into modules for 650-line compliance:
- admin_tenants.py: SubscriptionTier, Tenant, TenantUser admins
- admin_agents.py: Agent, AgentUser, Feature, Usage, Audit admins
"""

# Import all admin classes to register with Django admin
from admin.saas.admin_tenants import (
    SubscriptionTierAdmin,
    TenantAdmin,
    TenantUserAdmin,
    TenantUserInline,
    TierFeatureInline,
)
from admin.saas.admin_agents import (
    AgentAdmin,
    AgentUserAdmin,
    AgentInline,
    AgentUserInline,
    SaasFeatureAdmin,
    TierFeatureAdmin,
    FeatureProviderAdmin,
    UsageRecordAdmin,
    AuditLogAdmin,
)

__all__ = [
    # Tenant admins
    "SubscriptionTierAdmin",
    "TenantAdmin",
    "TenantUserAdmin",
    "TenantUserInline",
    "TierFeatureInline",
    # Agent admins
    "AgentAdmin",
    "AgentUserAdmin",
    "AgentInline",
    "AgentUserInline",
    "SaasFeatureAdmin",
    "TierFeatureAdmin",
    "FeatureProviderAdmin",
    "UsageRecordAdmin",
    "AuditLogAdmin",
]
