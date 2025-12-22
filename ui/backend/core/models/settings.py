"""
Eye of God Core Models - Settings
Per Eye of God UIX Design Section 2.1

VIBE COMPLIANT:
- Real Django model
- Version-based optimistic locking
- Tab-based organization
"""

import uuid
from django.db import models


class Settings(models.Model):
    """
    Tenant settings organized by tab.
    
    Supports optimistic locking via version field.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, related_name='settings')
    created_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Tab identification
    TAB_CHOICES = [
        ('agent', 'Agent Settings'),
        ('external', 'External Services'),
        ('connectivity', 'Connectivity'),
        ('system', 'System'),
    ]
    tab = models.CharField(max_length=20, choices=TAB_CHOICES)
    
    # Settings data
    data = models.JSONField(default=dict)
    
    # Optimistic locking
    version = models.IntegerField(default=1)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'settings'
        unique_together = [['tenant', 'tab']]
        ordering = ['tab']
    
    def __str__(self) -> str:
        return f"{self.tenant.name} - {self.tab} (v{self.version})"
    
    @property
    def tenant_id(self) -> uuid.UUID:
        return self.tenant.id
