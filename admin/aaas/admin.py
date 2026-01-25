"""AAAS Django Admin - Main entry point.

Split into modules for 650-line compliance:
- admin_tenants.py: SubscriptionTier, Tenant, TenantUser admins
- admin_agents.py: Agent, AgentUser, Feature, Usage, Audit admins
"""

# Import all admin classes to register with Django admin
from admin.aaas.admin_agents import (
    AgentAdmin,
    AgentInline,
    AgentUserAdmin,
    AgentUserInline,
    AuditLogAdmin,
    FeatureProviderAdmin,
    AaasFeatureAdmin,
    TierFeatureAdmin,
    UsageRecordAdmin,
)
from admin.aaas.admin_tenants import (
    SubscriptionTierAdmin,
    TenantAdmin,
    TenantUserAdmin,
    TenantUserInline,
    TierFeatureInline,
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
    "AaasFeatureAdmin",
    "TierFeatureAdmin",
    "FeatureProviderAdmin",
    "UsageRecordAdmin",
    "AuditLogAdmin",
]
