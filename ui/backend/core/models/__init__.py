"""Core Django models for Eye of God.

Per Eye of God UIX Design Section 2.1

VIBE COMPLIANT:
- Real Django models (no stubs)
- Multi-tenant support
- Audit logging
"""

import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class Tenant(models.Model):
    """Multi-tenant organization."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Settings overrides
    settings_override = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'eog_tenants'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class User(AbstractUser):
    """Extended user with tenant membership."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='users',
        null=True,
        blank=True,
    )
    
    # Role within tenant
    ROLE_CHOICES = [
        ('sysadmin', 'System Administrator'),
        ('admin', 'Administrator'),
        ('developer', 'Developer'),
        ('trainer', 'Trainer'),
        ('member', 'Member'),
        ('viewer', 'Viewer'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    
    # Profile
    avatar_url = models.URLField(blank=True)
    preferences = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'eog_users'
    
    def __str__(self):
        return self.email or self.username


class AgentMode(models.Model):
    """Agent operating mode definition."""
    
    MODE_CHOICES = [
        ('STD', 'Standard'),
        ('TRN', 'Training'),
        ('ADM', 'Admin'),
        ('DEV', 'Developer'),
        ('RO', 'Read-Only'),
        ('DGR', 'Degraded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=10, choices=MODE_CHOICES)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=20, blank=True)
    
    # Mode capabilities
    capabilities = models.JSONField(default=list)
    restrictions = models.JSONField(default=list)
    
    # Required role to activate
    required_role = models.CharField(max_length=20, default='member')
    
    class Meta:
        db_table = 'eog_agent_modes'
    
    def __str__(self):
        return f"{self.code}: {self.name}"


class Settings(models.Model):
    """Tenant-scoped settings."""
    
    TAB_CHOICES = [
        ('agent', 'Agent'),
        ('external', 'External'),
        ('connectivity', 'Connectivity'),
        ('system', 'System'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='settings')
    tab = models.CharField(max_length=20, choices=TAB_CHOICES)
    data = models.JSONField(default=dict)
    version = models.IntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    
    class Meta:
        db_table = 'eog_settings'
        unique_together = [['tenant', 'tab']]
    
    def __str__(self):
        return f"{self.tenant.name}: {self.tab}"


class Theme(models.Model):
    """User-created theme."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='themes')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='themes')
    
    name = models.CharField(max_length=50)
    version = models.CharField(max_length=20, default='1.0.0')
    description = models.TextField(blank=True)
    
    # CSS custom properties
    variables = models.JSONField(default=dict)
    
    # Stats
    downloads = models.IntegerField(default=0)
    rating = models.FloatField(default=0.0)
    tags = models.JSONField(default=list)
    
    # Status
    is_approved = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'eog_themes'
        unique_together = [['tenant', 'name']]
    
    def __str__(self):
        return f"{self.name} v{self.version}"


class FeatureFlag(models.Model):
    """Feature flag for gradual rollout."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Global state
    enabled = models.BooleanField(default=False)
    
    # Rollout percentage (0-100)
    rollout_percentage = models.IntegerField(default=0)
    
    # Tenant overrides
    tenant_overrides = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'eog_feature_flags'
    
    def __str__(self):
        return f"{self.key}: {'ON' if self.enabled else 'OFF'}"


class AuditLog(models.Model):
    """Audit log for security and compliance."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='audit_logs',
        null=True,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
    )
    
    # Action details
    action = models.CharField(max_length=50)
    resource_type = models.CharField(max_length=50)
    resource_id = models.CharField(max_length=100)
    
    # Request context
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)
    
    # Payload
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'eog_audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]
    
    def __str__(self):
        return f"{self.action} on {self.resource_type}/{self.resource_id}"
