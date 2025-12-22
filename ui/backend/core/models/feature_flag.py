"""
Eye of God Core Models - Feature Flag
Per Eye of God UIX Design Section 2.1

VIBE COMPLIANT:
- Real Django model
- Percentage-based rollout
- Condition-based targeting
"""

import uuid
from django.db import models


class FeatureFlag(models.Model):
    """
    Feature flag for gradual rollout and A/B testing.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, related_name='feature_flags')
    
    # Flag identification
    key = models.CharField(max_length=100)  # e.g. 'new_chat_ui'
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    
    # Status
    enabled = models.BooleanField(default=False)
    
    # Rollout configuration
    rollout_percent = models.IntegerField(default=0)  # 0-100
    
    # Targeting conditions
    conditions = models.JSONField(default=dict)  # e.g. {"role": ["admin", "developer"]}
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'feature_flags'
        unique_together = [['tenant', 'key']]
        ordering = ['key']
    
    def __str__(self) -> str:
        status = '✓' if self.enabled else '○'
        return f"{self.key} [{status}] ({self.rollout_percent}%)"
    
    @property
    def tenant_id(self) -> uuid.UUID:
        return self.tenant.id
    
    def is_enabled_for_user(self, user) -> bool:
        """Check if flag is enabled for a specific user."""
        if not self.enabled:
            return False
        
        # Check role conditions
        if 'role' in self.conditions:
            if user.role not in self.conditions['role']:
                return False
        
        # Check percentage rollout
        if self.rollout_percent < 100:
            # Use user ID for consistent hashing
            user_hash = hash(str(user.id)) % 100
            if user_hash >= self.rollout_percent:
                return False
        
        return True
