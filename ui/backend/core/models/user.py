"""
Eye of God Core Models - User
Per Eye of God UIX Design Section 2.1

VIBE COMPLIANT:
- Real Django model
- Password hashing
- Role-based access
"""

import uuid
from django.db import models


class User(models.Model):
    """
    User account within a tenant.
    
    Implements role-based access control with 6 role levels.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, related_name='users')
    
    # Authentication
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(null=True, blank=True)
    password_hash = models.CharField(max_length=128)
    salt = models.CharField(max_length=64)
    
    # Authorization
    ROLE_CHOICES = [
        ('sysadmin', 'System Administrator'),
        ('admin', 'Administrator'),
        ('developer', 'Developer'),
        ('trainer', 'Trainer'),
        ('member', 'Member'),
        ('viewer', 'Viewer'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    
    # Agent mode
    MODE_CHOICES = [
        ('STD', 'Standard'),
        ('TRN', 'Training'),
        ('ADM', 'Admin'),
        ('DEV', 'Developer'),
        ('RO', 'Read Only'),
        ('DGR', 'Danger'),
    ]
    current_mode = models.CharField(max_length=3, choices=MODE_CHOICES, default='STD')
    mode_changed_at = models.DateTimeField(null=True, blank=True)
    
    # Profile
    display_name = models.CharField(max_length=255, null=True, blank=True)
    avatar_url = models.URLField(null=True, blank=True)
    preferences = models.JSONField(default=dict, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'username']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self) -> str:
        return f"{self.username} ({self.role})"
    
    @property
    def tenant_id(self) -> uuid.UUID:
        return self.tenant.id
