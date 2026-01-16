"""
SomaBrain Models.
Defines configuration for Memory subsystems.
"""

import uuid
from django.db import models

class MemoryConfig(models.Model):
    """Configuration for Agent Memory Retention & Retrieval.

    Rule 91: Database-driven memory sovereignty.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)

    # Retention Policy
    retention_days = models.IntegerField(default=30, help_text="Days to keep ephemeral memories")
    archival_days = models.IntegerField(default=365, help_text="Days to keep archival memories")

    # Vector DB Settings (Override defaults)
    vector_db_collection = models.CharField(max_length=255, blank=True, help_text="Specific collection/namespace")

    # Snapshotting
    snapshot_frequency_hours = models.IntegerField(default=24)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "somabrain_memory_config"
        verbose_name = "Memory Configuration"

    def __str__(self):
        return f"MemoryConfig({self.name})"
