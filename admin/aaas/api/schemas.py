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
    """Core platform metrics for AAAS dashboard.

    Fields this system can actually measure are plain values. Fields that
    have no instrument behind them are Optional and report ``None`` rather
    than a number that was made up.
    """

    total_tenants: int
    active_tenants: int
    trial_tenants: int
    total_agents: int
    active_agents: int
    total_users: int
    mrr: float
    # No prior-period MRR is stored, so growth cannot be computed.
    mrr_growth: Optional[float] = None
    # Process uptime in seconds. There is no availability prober, so an
    # uptime *percentage* cannot be measured and is not reported.
    uptime_seconds: float
    # No alert store exists in this system.
    active_alerts: Optional[int] = None
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
    # The billing contact is editable. It used to be absent here, so the
    # settings screen offered a billing-email field and dropped it on save.
    email: Optional[str] = None


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
    """Billing dashboard metrics.

    ``mrr_growth`` and ``churn_rate`` need historical snapshots this system
    does not keep, so they report ``None`` rather than a fabricated 0.0.
    """

    mrr: float
    mrr_growth: Optional[float] = None
    arpu: float
    churn_rate: Optional[float] = None
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
    number: str = ""
    amount_cents: int = 0
    currency: str = "USD"
    status: str
    created_at: str = ""
    customer: Optional[dict] = None
    due_date: Optional[str] = None
    paid_at: Optional[str] = None


class BillingResponse(Schema):
    """Complete billing dashboard response."""

    metrics: BillingMetrics
    revenue_by_tier: list[RevenueByTier]
    recent_invoices: list[InvoiceOut]


# =============================================================================
# USAGE SCHEMAS
# =============================================================================
class UsageMetrics(Schema):
    """Usage tracking metrics.

    ``storage_used_gb`` is summed from real asset bytes. ``api_calls`` and
    ``users_active`` have no meter behind them yet and report ``None``.
    """

    tenant_id: Optional[str] = None
    period: str
    tokens_used: int
    storage_used_gb: float
    api_calls: Optional[int] = None
    agents_active: int
    users_active: Optional[int] = None


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
    """Feature flag response.

    Mirrors ``AaasFeature``. There is no rollout-percentage column on that
    model, so none is reported.
    """

    id: str
    code: str
    name: str
    description: str
    enabled: bool
    created_at: datetime
    updated_at: datetime


class FeatureFlagUpdate(Schema):
    """Update feature flag request."""

    enabled: Optional[bool] = None


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
