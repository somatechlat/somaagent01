"""AAAS Admin API Package.

Django Ninja routers for complete AAAS platform management.
"""

from ninja import Router

from .audit import router as audit_router
from .billing import router as billing_router
from .dashboard import router as dashboard_router
from .features import router as features_router
from .health import router as health_router
from .integrations import router as integrations_router
from .settings import router as settings_router
from .tenant_agents import router as tenant_agents_router
from .tenants import router as tenants_router
from .tiers import router as tiers_router
from .users import router as users_router

# Main AAAS router - mounts all sub-routers
router = Router(tags=["AAAS Platform"])

# AAAS Super Admin endpoints
router.add_router("/dashboard", dashboard_router, tags=["Dashboard"])
router.add_router("/tenants", tenants_router, tags=["Tenants"])
router.add_router("/tiers", tiers_router, tags=["Subscription Tiers"])
router.add_router("/billing", billing_router, tags=["Billing"])
router.add_router("/features", features_router, tags=["Features"])
router.add_router("/settings", settings_router, tags=["Settings"])
router.add_router("/integrations", integrations_router, tags=["Integrations"])
router.add_router("/audit", audit_router, tags=["Audit Trail"])
router.add_router("/health", health_router, tags=["Platform Health"])

# Tenant Admin endpoints
router.add_router("/admin", users_router, tags=["Tenant Users"])
router.add_router("/admin", tenant_agents_router, tags=["Tenant Agents"])

__all__ = ["router"]
