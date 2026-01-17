"""Feature Checking Logic — The Decision Engine.

SRS Source: SRS-FEATURE-FLAGS-2026-01-16

Applied Personas:
- PhD Architect: Robust toggle logic
- Security Auditor: Fail-closed dependency chains
- DevOps: Cache-first resolution

Vibe Coding Rules:
- Real Redis (via Django cache)
- Recursion protection for dependencies
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

from django.core.cache import cache

from admin.core.budget.limits import get_tenant_plan
from admin.core.features.registry import FEATURE_REGISTRY, get_feature

logger = logging.getLogger(__name__)

# Plan hierarchy check
TIER_RANKS = {
    "free": 10,
    "starter": 20,
    "team": 30,
    "enterprise": 40,
}


def is_feature_enabled(
    tenant_id: str,
    feature_code: str,
    _recursion_depth: int = 0,
) -> bool:
    """Check if a feature is enabled for a tenant.

    Resolution Order:
    1. Feature Existence Check (Fail Closed)
    2. Dependency Check (Recursive)
    3. Plan Requirement Check
    4. Tenant Override Check (Redis)
    5. Global Defaut Check

    Args:
        tenant_id: UUID of the tenant
        feature_code: Code of the feature to check
        _recursion_depth: Internal guard against cyclic dependencies

    Returns:
        bool: True if feature is fully enabled
    """
    # 0. Recursion Guard
    if _recursion_depth > 5:
        logger.error(f"Feature dependency cycle detected for {feature_code}")
        return False

    # 1. Feature Existence
    try:
        feature = get_feature(feature_code)
    except KeyError:
        logger.warning(f"Check for unknown feature: {feature_code}")
        return False

    # 2. Dependency Check (Fail Closed)
    for dep in feature.dependencies:
        if not is_feature_enabled(tenant_id, dep, _recursion_depth + 1):
            return False

    # 3. Plan Requirement Check
    # Get tenant plan (cached)
    tenant_plan = get_tenant_plan(tenant_id)

    tenant_rank = TIER_RANKS.get(tenant_plan, 0)
    required_rank = TIER_RANKS.get(feature.tier, 999)

    # 4. Tenant Override (Redis)
    # Key: feature:override:{tenant_id}:{code} -> "true" | "false"
    # This allows:
    # - Granting "beta" features to specific tenants
    # - Disabling broken features for specific tenants
    # - Granting higher-tier features to lower-tier tenants (bonus)
    override_key = f"feature:override:{tenant_id}:{feature_code}"
    override_val = cache.get(override_key)

    if override_val is not None:
        # Explicit override takes precedence over Plan
        # But NOT over dependencies (dependencies are physical constraints usually)
        return str(override_val).lower() in ("1", "true", "on", "yes")

    # If no override, enforce Plan
    if tenant_rank < required_rank:
        return False

    # 5. Beta Gate
    # If feature is beta, it requires an explicit override to be ON
    # unless it's strictly a core feature (which beta shouldn't be)
    if feature.beta:
        return False

    # Default: Enabled if plan allows
    return True
