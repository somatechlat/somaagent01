"""Files V2 Django Models.

VIBE COMPLIANT - Django ORM, no SQLAlchemy.
Enhanced file management with versioning and metadata.
"""

from __future__ import annotations

import uuid

from django.db import models
from django.utils import timezone


class File(models.Model):
    """File record with versioning support.

    Stores file metadata with S3/local storage backend.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    user_id = models.UUIDField(db_index=True)

    # File metadata
    name = models.CharField(max_length=255)
    original_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100)
    size_bytes = models.BigIntegerField()

    # Storage
    storage_key = models.CharField(max_length=512)  # S3 key or local path
    storage_backend = models.CharField(max_length=50, default="s3")

    # Version tracking
    version = models.IntegerField(default=1)
    parent_id = models.UUIDField(null=True, blank=True, db_index=True)

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    tags = models.JSONField(default=list, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "files_v2"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant_id", "user_id"]),
            models.Index(fields=["storage_key"]),
        ]

    def __str__(self):
        return f"File({self.id}:{self.name})"
