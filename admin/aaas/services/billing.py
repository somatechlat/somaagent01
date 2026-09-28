"""Billing metrics — the single owner of MRR and ARPU.

These aggregates used to be computed inline in three separate handlers
(``admin/aaas/api/dashboard.py``, ``admin/aaas/api/tenants.py``,
``admin/aaas/api/billing.py``) and they had already drifted apart: two of
them referenced ``SubscriptionTier.price_cents``, a field the model never
declared, so ``/aaas/dashboard`` and ``/aaas/tenants`` raised
``FieldError`` / ``AttributeError`` on every request while
``admin/aaas/api/billing.py`` used the real name.

Anything that needs the revenue metric calls here, so the metric cannot
fork again.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.db.models import Sum

from admin.aaas.models import Tenant


@dataclass(frozen=True)
class MrrSnapshot:
    """Revenue over the current set of active tenants.

    Attributes:
        mrr: Monthly recurring revenue in USD.
        arpu: Average revenue per paying tenant, in USD/month.
        paid_count: Active tenants on a tier with a non-zero base price.
        total_count: All active tenants, paying or not.
    """

    mrr: float
    arpu: float
    paid_count: int
    total_count: int


def compute_mrr_and_arpu() -> MrrSnapshot:
    """Compute MRR and ARPU from ``SubscriptionTier.base_price_cents``.

    A tenant counts toward revenue only when it is active and its tier has
    a non-zero base price. Tenants with no tier at all are counted in
    ``total_count`` but never in ``paid_count``.
    """
    active = Tenant.objects.filter(status="active")
    total_count = active.count()

    paid = active.filter(tier__isnull=False).exclude(tier__base_price_cents=0)
    paid_count = paid.count()
    mrr_cents = paid.aggregate(total=Sum("tier__base_price_cents"))["total"] or 0

    mrr = mrr_cents / 100.0
    arpu = (mrr / paid_count) if paid_count else 0.0
    return MrrSnapshot(
        mrr=mrr,
        arpu=arpu,
        paid_count=paid_count,
        total_count=total_count,
    )
