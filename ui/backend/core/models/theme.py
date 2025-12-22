"""
Eye of God Core Models - Theme
Per Eye of God UIX Design Section 2.1

VIBE COMPLIANT:
- Real Django model  
- XSS-validated variables
- Approval workflow
"""

import uuid
from django.db import models


class Theme(models.Model):
    """
    Custom UI theme with CSS variables.
    
    Themes must be approved before becoming generally available.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, related_name='themes')
    owner = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Theme metadata
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    version = models.CharField(max_length=20, default='1.0.0')
    author = models.CharField(max_length=100, default='Anonymous')
    
    # CSS variables (validated for XSS on save)
    variables = models.JSONField(default=dict)
    
    # Approval workflow
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        'User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_themes'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Usage tracking
    downloads = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'themes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'name']),
            models.Index(fields=['is_approved']),
        ]
    
    def __str__(self) -> str:
        status = '✓' if self.is_approved else '○'
        return f"{self.name} v{self.version} [{status}]"
    
    @property
    def tenant_id(self) -> uuid.UUID:
        return self.tenant.id
    
    def validate_variables(self) -> bool:
        """Check for XSS patterns in variables."""
        xss_patterns = ['<script', 'javascript:', 'url(', 'expression(']
        for key, value in self.variables.items():
            if isinstance(value, str):
                value_lower = value.lower()
                for pattern in xss_patterns:
                    if pattern in value_lower:
                        return False
        return True
    
    def save(self, *args, **kwargs):
        if not self.validate_variables():
            raise ValueError("XSS pattern detected in theme variables")
        super().save(*args, **kwargs)
