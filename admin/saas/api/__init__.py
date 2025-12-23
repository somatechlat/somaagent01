# SAAS Admin API Package
# Django Ninja routers and schemas for SAAS platform management

from ninja import Router

from .billing import router as billing_router
from .dashboard import router as dashboard_router
from .features import router as features_router
from .settings import router as settings_router
from .tenants import router as tenants_router
from .tiers import router as tiers_router

# Main SAAS router - mounts all sub-routers
router = Router(tags=["SAAS Platform"])
router.add_router("/dashboard", dashboard_router, tags=["Dashboard"])
router.add_router("/tenants", tenants_router, tags=["Tenants"])
router.add_router("/tiers", tiers_router, tags=["Subscription Tiers"])
router.add_router("/billing", billing_router, tags=["Billing"])
router.add_router("/features", features_router, tags=["Features"])
router.add_router("/settings", settings_router, tags=["Settings"])

__all__ = ["router"]
