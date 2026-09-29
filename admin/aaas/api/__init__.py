"""AAAS Admin API Package.

Django Ninja routers for administering this agent: its users, its agents,
its settings, its audit trail and its health.

There is no SaaS or billing administration in this product. It is a
standalone agent — subscription tiers, invoices, payment methods, plan
feature gating and multi-tenant org lifecycle are not administered here
and have no router. See AGENT.md §1.1 (Scope).
"""

from ninja import Router

from .audit import router as audit_router
from .health import router as health_router
from .integrations import router as integrations_router
from .settings import router as settings_router
from .tenant_agents import router as tenant_agents_router
from .users import router as users_router

# Main AAAS router - mounts all sub-routers
router = Router(tags=["Agent Administration"])

router.add_router("/settings", settings_router, tags=["Settings"])
router.add_router("/integrations", integrations_router, tags=["Integrations"])
router.add_router("/audit", audit_router, tags=["Audit Trail"])
router.add_router("/health", health_router, tags=["Health"])

# Agent administration
router.add_router("/admin", users_router, tags=["Users"])
router.add_router("/admin", tenant_agents_router, tags=["Agents"])

__all__ = ["router"]
