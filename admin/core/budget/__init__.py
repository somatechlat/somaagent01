"""Budget System Package — Universal Resource Budgeting.

SRS Source: SRS-BUDGET-SYSTEM-2026-01-16

Applied Personas:
- PhD Developer: Type-safe dataclasses, async patterns
- PhD Analyst: Metrics registry design
- QA Engineer: 100% testable, no hardcoding
- Security Auditor: Fail-closed enforcement
- Performance Engineer: Redis cache, async Lago
- UX Consultant: Clear error messages
- ISO Documenter: Comprehensive docstrings
- Django Architect: Django cache integration
- Django Infra: Redis-backed cache
- Django Evangelist: Django-native patterns

Vibe Coding Rules Compliance:
- NO mocks, NO stubs, NO placeholders
- Real Redis cache
- Real Lago integration
"""

from admin.core.budget.exceptions import BudgetExhaustedError
from admin.core.budget.gate import budget_gate
from admin.core.budget.registry import BudgetedMetric, METRIC_REGISTRY

__all__ = [
    "budget_gate",
    "BudgetExhaustedError",
    "METRIC_REGISTRY",
    "BudgetedMetric",
]
