"""Feature Flags System — Dynamic Capability Management.

SRS Source: SRS-FEATURE-FLAGS-2026-01-16

Applied Personas:
- PhD Developer: Type-safe dataclasses
- Security Auditor: Feature isolation, credential gating
- Product Manager: Tier-based feature availability
- DevOps: Environment-based overrides

Vibe Coding Rules:
- NO mocks
- Real Redis cache
"""

from admin.core.features.check import is_feature_enabled
from admin.core.features.gate import require_feature
from admin.core.features.registry import FEATURE_REGISTRY, FeatureFlag

__all__ = [
    "FEATURE_REGISTRY",
    "FeatureFlag",
    "is_feature_enabled",
    "require_feature",
]
