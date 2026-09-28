"""Governance Django ORM models (Constitution & Capability)."""

from __future__ import annotations

import uuid

from django.db import models


# =============================================================================
# CONSTITUTION MODELS (The Supreme Law)
# =============================================================================


class Constitution(models.Model):
    """The Supreme Regulatory Document.

    IMMUTABLE: Once signed, this record cannot be changed.
    All Capsules must reference a valid, active Constitution.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version = models.CharField(max_length=50, help_text="Semantic Version (e.g., 1.0.0)")

    # Cryptographic Proof
    content_hash = models.CharField(
        max_length=64, unique=True, help_text="SHA-256 Hash of normalized content"
    )
    signature = models.TextField(help_text="Ed25519 Signature of the content_hash")

    # The Law
    content = models.JSONField(help_text="The ")

    # Metadata
    is_active = models.BooleanField(default=False, help_text="Only one can be active at a time")
    created_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Meta class implementation."""

        db_table = "constitutions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["content_hash"]),
        ]

    def __str__(self):
        """Return string representation."""

        return f"Constitution(v{self.version}:{self.content_hash[:8]})"


# =============================================================================
# CAPABILITY MODELS (replaces capability_registry.py)
# =============================================================================


class Capability(models.Model):
    """Agent capability - replaces CapabilityRegistry."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, db_index=True)
    schema = models.JSONField(default=dict)
    config = models.JSONField(default=dict)
    policy = models.JSONField(
        default=dict,
        blank=True,
        help_text="""
        Tool execution policy: {
            "requires_approval": false,
            "timeout_seconds": 30,
            "max_retries": 3
        }
        """,
    )
    implementation = models.JSONField(
        default=dict,
        blank=True,
        help_text="""
        Tool implementation mapping: {
            "type": "python",
            "module": "tools.echo",
            "class": "EchoTool"
        }
        """,
    )
    is_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta class implementation."""

        db_table = "capabilities"
        verbose_name_plural = "capabilities"

    def __str__(self):
        """Return string representation."""

        return f"Capability({self.name})"
