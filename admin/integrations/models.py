"""Stub integration model for type-checking."""

import uuid

from django.db import models


class Integration(models.Model):
    """Stub for Integration model."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=50)
    provider = models.CharField(max_length=50)
    status = models.CharField(max_length=50)
    config = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    last_sync = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "integrations"
