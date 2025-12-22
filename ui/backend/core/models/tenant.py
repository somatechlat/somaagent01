"""
Eye of God Core Models - Tenant
Per Eye of God UIX Design Section 2.1

VIBE COMPLIANT:
- Real Django model
- UUID primary keys
- Full type hints
"""

import uuid
from django.db import models


class Tenant(models.Model):
    """
    Multi-tenant organization.
    
    Each tenant has isolated data and configurations.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True, null=True, blank=True)
    
    # Configuration
    settings = models.JSONField(default=dict, blank=True)
    features = models.JSONField(default=list, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    subscription_tier = models.CharField(max_length=50, default='free')
    
    # Limits
    max_users = models.IntegerField(default=10)
    max_agents = models.IntegerField(default=5)
    max_memory_mb = models.IntegerField(default=1000)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tenants'
        ordering = ['-created_at']
    
    def __str__(self) -> str:
        return f"{self.name} ({self.id})"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.name.lower().replace(' ', '-')[:100]
        super().save(*args, **kwargs)
