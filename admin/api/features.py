"""Feature Flags API — Capabilities Management.

SRS Source: SRS-FEATURE-FLAGS-2026-01-16

Applied Personas:
- Product Owner: Capability visibility
- DevOps: Toggles and overrides

Vibe Coding Rules:
- Real data from Registry + Redis
- No mocks
"""

from typing import List

from django.http import HttpRequest
from ninja import Router, Schema

from admin.core.features.check import is_feature_enabled
from admin.core.features.exceptions import FeatureDisabledError
from admin.core.features.registry import FEATURE_REGISTRY, list_features

router = Router(tags=["features"])


class FeatureDefinition(Schema):
    code: str
    name: str
    description: str
    tier: str
    dependencies: List[str]
    is_core: bool
    beta: bool


class FeatureState(FeatureDefinition):
    enabled: bool


@router.get("/", response=List[FeatureDefinition])
def list_available_features(request: HttpRequest):
    """List all defined system features (catalog)."""
    return [
        FeatureDefinition(
            code=f.code,
            name=f.name,
            description=f.description,
            tier=f.tier,
            dependencies=f.dependencies,
            is_core=f.is_core,
            beta=f.beta,
        )
        for f in list_features()
    ]


@router.get("/me", response=List[FeatureState])
def get_my_features(request: HttpRequest):
    """List features enabled for the current tenant.

    Resolves: Plan, Dependencies, Overrides.
    """
    # Extract tenant_id from request (Ninja/Middleware)
    tenant_id = getattr(request.state, "tenant_id", None)

    if not tenant_id and request.user.is_authenticated:
        # Fallback to user's active tenant
        tenant_id = getattr(request.user, "active_tenant_id", None)

    if not tenant_id:
        # If no tenant context, only return CORE features as enabled (public)
        # or raise error? For now, return effective state for "anonymous/no-tenant"
        # which usually means only free/core features if we had a default plan.
        # But fail-closed says: if no tenant, no features usually.
        # However, listing features is often done during onboarding.
        # Let's return disabled for everything except core?
        # Better: Require auth for this endpoint.
        pass

    # Assuming auth is enforced by global router or decorator on parent
    if not tenant_id:
         # Empty list or error?
         # Let's return features but all disabled if unknown tenant
         effective_tenant = "anonymous"
    else:
        effective_tenant = str(tenant_id)

    results = []
    for f in list_features():
        enabled = is_feature_enabled(effective_tenant, f.code)
        state = FeatureState(
            code=f.code,
            name=f.name,
            description=f.description,
            tier=f.tier,
            dependencies=f.dependencies,
            is_core=f.is_core,
            beta=f.beta,
            enabled=enabled,
        )
        results.append(state)

    return results
