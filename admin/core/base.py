"""Shared base models for Django ORM.

This module contains abstract base classes used across multiple apps.
Import from here to avoid duplication.
"""

from django.db import models


class TimestampedModel(models.Model):
    """Abstract base class that adds created_at and updated_at fields.

    Use this as a mixin for models that need timestamp tracking:

        class MyModel(TimestampedModel):
            name = models.CharField(max_length=100)
    """

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TenantScopedModel(models.Model):
    """Abstract base class for models that belong to a tenant.

    Provides a proper ForeignKey to Tenant for referential integrity.
    """

    tenant = models.ForeignKey(
        "saas.Tenant",
        on_delete=models.CASCADE,
        related_name="%(class)ss",
        db_index=True,
    )

    class Meta:
        abstract = True


class UUIDPrimaryKeyModel(models.Model):
    """Abstract base class with UUID primary key.

    Standard pattern for distributed-safe primary keys.
    """

    import uuid

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True
