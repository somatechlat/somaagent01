"""MRR aggregation — one implementation, one field name.

Regression: ``admin/aaas/api/dashboard.py`` and ``admin/aaas/api/tenants.py``
computed MRR with ``tier__price_cents`` / ``tier.price_cents``. The model
declares ``base_price_cents`` (``admin/aaas/models/tiers.py``), so
``/api/v2/aaas/dashboard`` and ``/api/v2/aaas/tenants`` raised
``FieldError`` / ``AttributeError`` at request time. ``admin/aaas/api/billing.py``
had the correct name — the metric had been copied between handlers and
drifted.

The guard here is behavioural, not a source-text grep: the aggregation must
resolve against real model fields and must return the tier's price.

VIBE Rule 91: no hardcoded values; no mocks — real models, real rows.
"""

from __future__ import annotations

import pytest


class TestMrrFieldResolution:
    """Field-name regression — needs no database, only model meta."""

    def test_unknown_tier_field_does_not_resolve(self):
        """A field name the model lacks must fail at resolve time.

        This is the exact failure /aaas/dashboard used to hit per request.
        """
        from django.core.exceptions import FieldError
        from django.db.models import Sum

        from admin.aaas.models import Tenant

        with pytest.raises(FieldError):
            Sum("tier__price_cents").resolve_expression(Tenant.objects.all().query)


@pytest.mark.django_db(transaction=True)
class TestMrrAggregation:
    """compute_mrr_and_arpu is the single owner of the MRR metric."""

    def test_mrr_counts_a_paid_tenant_at_its_tier_price(self):
        from admin.aaas.models import SubscriptionTier, Tenant
        from admin.aaas.services.billing import compute_mrr_and_arpu

        tier = SubscriptionTier.objects.create(
            name="Pro",
            slug=f"pro-{__import__('uuid').uuid4().hex[:8]}",
            base_price_cents=4900,
        )
        Tenant.objects.create(
            name="Paid Tenant",
            slug=f"paid-{__import__('uuid').uuid4().hex[:8]}",
            tier=tier,
            status="active",
        )

        result = compute_mrr_and_arpu()

        assert result.paid_count == 1
        assert result.total_count == 1
        assert result.mrr == pytest.approx(49.0)
        assert result.arpu == pytest.approx(49.0)

    def test_free_tiers_do_not_contribute_to_mrr(self):
        from admin.aaas.models import SubscriptionTier, Tenant
        from admin.aaas.services.billing import compute_mrr_and_arpu

        free = SubscriptionTier.objects.create(
            name="Free",
            slug=f"free-{__import__('uuid').uuid4().hex[:8]}",
            base_price_cents=0,
        )
        Tenant.objects.create(
            name="Free Tenant",
            slug=f"free-{__import__('uuid').uuid4().hex[:8]}",
            tier=free,
            status="active",
        )

        result = compute_mrr_and_arpu()

        assert result.paid_count == 0
        assert result.total_count == 1
        assert result.mrr == pytest.approx(0.0)

    def test_inactive_tenants_are_excluded(self):
        from admin.aaas.models import SubscriptionTier, Tenant
        from admin.aaas.services.billing import compute_mrr_and_arpu

        tier = SubscriptionTier.objects.create(
            name="Pro",
            slug=f"pro-{__import__('uuid').uuid4().hex[:8]}",
            base_price_cents=4900,
        )
        Tenant.objects.create(
            name="Suspended Tenant",
            slug=f"susp-{__import__('uuid').uuid4().hex[:8]}",
            tier=tier,
            status="suspended",
        )

        result = compute_mrr_and_arpu()

        assert result.paid_count == 0
        assert result.mrr == pytest.approx(0.0)
