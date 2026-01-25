"""
AAAS Admin API Schemas
Django Ninja/Pydantic schemas for request/response validation.

All schemas follow SRS Section 5.1 - AAAS Super Admin specifications.
"""

from datetime import datetime
from typing import Any, Optional

from ninja import Schema


# =============================================================================
# DASHBOARD SCHEMAS
# =============================================================================
class DashboardMetrics(Schema):
    """Core platform metrics for AAAS dashboard."""

    total_tenants: int
    active_tenants: int
    trial_tenants: int
    total_agents: int
    active_agents: int
    total_users: int
    mrr: float
    mrr_growth: float
    uptime: float
    active_alerts: int
    tokens_this_month: int
    storage_used_gb: float


class TopTenant(Schema):
    """Top tenant summary for dashboard."""

    id: str
    name: str
    tier: str
    agents: int
    users: int
    mrr: float
    status: str


class RecentEvent(Schema):
    """Recent platform event for dashboard feed."""

    id: str
    type: str
    message: str
    timestamp: str


class DashboardResponse(Schema):
    """Complete dashboard response."""

    metrics: DashboardMetrics
    top_tenants: list[TopTenant]
    recent_events: list[RecentEvent]


# =============================================================================
# TENANT SCHEMAS
# =============================================================================
class TenantOut(Schema):
    """Tenant response schema."""

    id: str
    name: str
    slug: str
    status: str
    tier: str
    created_at: datetime
    agents: int = 0
    users: int = 0
    mrr: float = 0.0
    email: Optional[str] = None


class TenantCreate(Schema):
    """Create tenant request."""

    name: str
    email: str
    tier: str = "starter"


class TenantUpdate(Schema):
    """Update tenant request."""

    name: Optional[str] = None
    status: Optional[str] = None
    tier: Optional[str] = None


class TenantListResponse(Schema):
    """Paginated tenant list response."""

    items: list[TenantOut]
    total: int
    page: int
    per_page: int


# =============================================================================
# SUBSCRIPTION TIER SCHEMAS
# =============================================================================
class TierLimits(Schema):
    """Tier resource limits."""

    agents: int
    users: int
    tokens_per_month: int
    storage_gb: float


class SubscriptionTierOut(Schema):
    """Subscription tier response."""

    id: str
    name: str
    slug: str
    price: float
    billing_period: str
    limits: TierLimits
    features: list[str]
    popular: bool = False
    active_count: int = 0


class TierCreate(Schema):
    """Create tier request."""

    name: str
    slug: str
    price_cents: int
    billing_interval: str = "monthly"
    limits: dict[str, Any]
    features: list[str] = []


class TierUpdate(Schema):
    """Update tier request."""

    name: Optional[str] = None
    price_cents: Optional[int] = None
    limits: Optional[dict[str, Any]] = None
    features: Optional[list[str]] = None
    is_active: Optional[bool] = None


# =============================================================================
# BILLING SCHEMAS
# =============================================================================
class BillingMetrics(Schema):
    """Billing dashboard metrics."""

    mrr: float
    mrr_growth: float
    arpu: float
    churn_rate: float
    paid_tenants: int
    total_tenants: int


class RevenueByTier(Schema):
    """Revenue breakdown by subscription tier."""

    tier: str
    mrr: float
    count: int
    percentage: float


class InvoiceOut(Schema):
    """Invoice response schema."""

    id: str
    tenant_id: str
    tenant_name: str
    amount: float
    status: str
    due_date: datetime
    paid_at: Optional[datetime] = None


class BillingResponse(Schema):
    """Complete billing dashboard response."""

    metrics: BillingMetrics
    revenue_by_tier: list[RevenueByTier]
    recent_invoices: list[InvoiceOut]


# =============================================================================
# USAGE SCHEMAS
# =============================================================================
class UsageMetrics(Schema):
    """Usage tracking metrics."""

    tenant_id: Optional[str] = None
    period: str
    tokens_used: int
    storage_used_gb: float
    api_calls: int
    agents_active: int
    users_active: int


# =============================================================================
# FEATURE SCHEMAS
# =============================================================================
class FeatureOut(Schema):
    """AAAS feature response."""

    id: str
    code: str
    name: str
    description: str
    category: str
    icon: str
    enabled: bool = True
    default_config: dict[str, Any] = {}


class FeatureFlagOut(Schema):
    """Feature flag response."""

    id: str
    name: str
    description: str
    enabled: bool
    rollout_percentage: int
    created_at: datetime
    updated_at: datetime


class FeatureFlagUpdate(Schema):
    """Update feature flag request."""

    enabled: Optional[bool] = None
    rollout_percentage: Optional[int] = None


# =============================================================================
# AGENT SCHEMAS
# =============================================================================
class AgentOut(Schema):
    """Agent response schema."""

    id: str
    name: str
    tenant_id: str
    status: str
    mode: str
    created_at: datetime
    last_active: Optional[datetime] = None
    conversations: int = 0


# =============================================================================
# USER SCHEMAS
# =============================================================================
class UserOut(Schema):
    """User response schema."""

    id: str
    email: str
    name: str
    role: str
    tenant_id: str
    status: str
    created_at: datetime
    last_login: Optional[datetime] = None


# =============================================================================
# API KEY SCHEMAS
# =============================================================================
class ApiKeyOut(Schema):
    """API key response schema."""

    id: str
    name: str
    prefix: str
    tenant_id: Optional[str] = None
    created_at: datetime
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class ApiKeyCreate(Schema):
    """Create API key request."""

    name: str
    tenant_id: Optional[str] = None
    expires_in_days: Optional[int] = None


# =============================================================================
# MODEL CONFIG SCHEMAS
# =============================================================================
class ModelConfigOut(Schema):
    """LLM model configuration response."""

    id: str
    provider: str
    model_name: str
    display_name: str
    enabled: bool
    default_for_chat: bool = False
    default_for_completion: bool = False
    rate_limit: Optional[int] = None


class ModelConfigUpdate(Schema):
    """Update model configuration request."""

    enabled: Optional[bool] = None
    default_for_chat: Optional[bool] = None
    default_for_completion: Optional[bool] = None
    rate_limit: Optional[int] = None


# =============================================================================
# ROLE SCHEMAS
# =============================================================================
class RoleOut(Schema):
    """Role response schema."""

    id: str
    name: str
    description: str
    permissions: list[str]
    user_count: int = 0


class RoleUpdate(Schema):
    """Update role request."""

    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[list[str]] = None


# =============================================================================
# SSO SCHEMAS
# =============================================================================
class SsoConfig(Schema):
    """SSO configuration."""

    provider: str  # 'okta', 'azure_ad', 'google'
    client_id: str
    client_secret: str
    domain: Optional[str] = None
    tenant_id: Optional[str] = None


class SsoTestResponse(Schema):
    """SSO connection test response."""

    success: bool
    message: str
    provider: str


# =============================================================================
# COMMON SCHEMAS
# =============================================================================
class MessageResponse(Schema):
    """Generic message response."""

    message: str
    success: bool = True


class ErrorResponse(Schema):
    """Error response schema."""

    detail: str
    code: Optional[str] = None
