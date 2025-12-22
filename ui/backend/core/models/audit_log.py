"""
Eye of God Core Models - Audit Log
Per Eye of God UIX Design Section 2.1

VIBE COMPLIANT:
- Real Django model
- Immutable records
- Comprehensive tracking
"""

import uuid
from django.db import models


class AuditLog(models.Model):
    """
    Immutable audit log for security and compliance.
    
    Records all significant actions in the system.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Action details
    action = models.CharField(max_length=100)  # e.g. 'mode.changed', 'theme.approved'
    resource_type = models.CharField(max_length=50)  # e.g. 'user', 'theme', 'settings'
    resource_id = models.CharField(max_length=100)  # UUID or other identifier
    
    # Additional context
    details = models.JSONField(default=dict)
    
    # Request metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    # Status
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failure', 'Failure'),
        ('warning', 'Warning'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='success')
    error_message = models.TextField(null=True, blank=True)
    
    # Timestamp (immutable)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]
    
    def __str__(self) -> str:
        return f"{self.action} by user {self.user_id} at {self.created_at}"
    
    @property
    def tenant_id(self) -> uuid.UUID:
        return self.tenant.id
    
    @property
    def user_id(self) -> uuid.UUID:
        return self.user.id if self.user else None
    
    def save(self, *args, **kwargs):
        # Prevent updates to existing records (immutable)
        if self.pk and AuditLog.objects.filter(pk=self.pk).exists():
            raise ValueError("Audit logs are immutable and cannot be modified")
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        raise ValueError("Audit logs cannot be deleted")
