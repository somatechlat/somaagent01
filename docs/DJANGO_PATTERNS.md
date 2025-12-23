# Django + Django Ninja Patterns Reference

**VIBE COMPLIANT** — All 7 personas applied. Max 600 lines.

---

## 1. Project Structure

```
somaAgent01/
├── admin/                          # Django apps live here
│   ├── skins/                      # Skin theming app
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py              # Django ORM models
│   │   ├── views.py               # Django Ninja endpoints
│   │   └── urls.py
│   ├── saas/                       # SAAS admin app
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   └── models.py              # ALL SAAS models here
│   └── <new_app>/                  # Future apps follow same pattern
├── services/gateway/
│   ├── django_setup.py            # Django config & Ninja API
│   └── routers/
│       ├── saas.py                # Django Ninja router
│       ├── tenant_admin.py
│       └── agent_admin.py
└── migrations/                     # LEGACY Alembic (multimodal only)
```

---

## 2. Model Patterns (Django ORM)

### 2.1 Base Model Template

```python
"""Model template - VIBE compliant."""

import uuid
from django.db import models


class MyModel(models.Model):
    """Model docstring with purpose.
    
    Per [SRS Section Reference]
    """
    
    # Primary key - always UUID
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier"
    )
    
    # Multi-tenant isolation
    tenant_id = models.UUIDField(
        db_index=True,
        help_text="Tenant this belongs to"
    )
    
    # Core fields with help_text
    name = models.CharField(
        max_length=100,
        help_text="Display name"
    )
    
    # JSONB for flexible settings
    settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Flexible configuration"
    )
    
    # Timestamps - always include
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'my_models'           # Explicit table name
        ordering = ['-created_at']        # Default ordering
        indexes = [                       # Performance indexes
            models.Index(fields=['tenant_id']),
            models.Index(fields=['-created_at']),
        ]
        verbose_name = 'My Model'
        verbose_name_plural = 'My Models'
    
    def __str__(self):
        return self.name
    
    def to_dict(self):
        """API serialization - keeps response code clean."""
        return {
            'id': str(self.id),
            'tenant_id': str(self.tenant_id),
            'name': self.name,
            'settings': self.settings,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
```

### 2.2 Choices (Django Enums)

```python
class Status(models.TextChoices):
    """Status choices with DB value and display label."""
    ACTIVE = 'active', 'Active'
    PENDING = 'pending', 'Pending'
    SUSPENDED = 'suspended', 'Suspended'

# Usage in model
status = models.CharField(
    max_length=20,
    choices=Status.choices,
    default=Status.PENDING,
    db_index=True
)
```

### 2.3 Relationships

```python
# ForeignKey with proper cascade
tier = models.ForeignKey(
    'SubscriptionTier',
    on_delete=models.PROTECT,      # Prevent accidental deletion
    related_name='tenants',
    help_text="Current subscription tier"
)

# One-to-Many reverse access
tenant.agents.all()  # Get all agents for tenant
```

---

## 3. API Patterns (Django Ninja)

### 3.1 Router Setup

```python
"""Router in services/gateway/routers/saas.py"""

from ninja import Router

router = Router(tags=["saas"])

@router.get("/tenants")
def list_tenants(request):
    """List all tenants."""
    from admin.saas.models import Tenant
    tenants = Tenant.objects.filter(status='active')
    return [t.to_dict() for t in tenants]

@router.post("/tenants")
def create_tenant(request, payload: TenantCreateSchema):
    """Create new tenant."""
    from admin.saas.models import Tenant
    tenant = Tenant.objects.create(**payload.dict())
    return tenant.to_dict()
```

### 3.2 Schema Definitions

```python
from ninja import Schema
from typing import Optional
from uuid import UUID

class TenantCreateSchema(Schema):
    """Request body schema."""
    name: str
    slug: str
    tier_id: UUID
    billing_email: Optional[str] = None

class TenantResponseSchema(Schema):
    """Response schema."""
    id: UUID
    name: str
    slug: str
    status: str
    created_at: str
```

### 3.3 Registration in django_setup.py

```python
from ninja import NinjaAPI
from services.gateway.routers.saas import router as saas_router

ninja_api = NinjaAPI(
    title="SomaAgent SaaS API",
    version="1.0.0",
)

ninja_api.add_router("", saas_router)           # /api/v2/saas/*
ninja_api.add_router("/admin", tenant_router)   # /api/v2/saas/admin/*
```

---

## 4. Migration Patterns

### 4.1 Create Migrations

```bash
# From project root
cd /Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgent01

# Generate migrations for specific app
python3 -c "
import os
os.environ.setdefault('SA01_DB_DSN', 'postgresql://soma:soma@localhost:5432/somaagent01')
import django
from services.gateway.django_setup import settings
from django.core.management import execute_from_command_line
execute_from_command_line(['manage.py', 'makemigrations', 'saas'])
"

# Apply migrations
python3 -c "
import os
os.environ.setdefault('SA01_DB_DSN', 'postgresql://soma:soma@localhost:5432/somaagent01')
from services.gateway.django_setup import settings
from django.core.management import execute_from_command_line
execute_from_command_line(['manage.py', 'migrate'])
"
```

---

## 5. Field Type Mappings

| Use Case | Django Field | SQLAlchemy Equivalent |
|----------|--------------|----------------------|
| UUID PK | `UUIDField(primary_key=True)` | `UUID(as_uuid=False)` |
| Text | `CharField(max_length=N)` | `String(N)` |
| Long Text | `TextField()` | `Text` |
| Integer | `IntegerField()` | `Integer` |
| Big Integer | `BigIntegerField()` | `BigInteger` |
| Decimal | `DecimalField(max_digits, decimal_places)` | `Numeric(M, D)` |
| Boolean | `BooleanField()` | `Boolean` |
| DateTime | `DateTimeField()` | `DateTime(timezone=True)` |
| JSON/JSONB | `JSONField()` | `JSONB` |
| Email | `EmailField()` | `String(255)` |
| URL | `URLField()` | `String(2048)` |
| IP Address | `GenericIPAddressField()` | `String(45)` |
| Slug | `SlugField()` | `String + unique` |
| Foreign Key | `ForeignKey(Model, on_delete=X)` | `ForeignKey("table.id")` |

---

## 6. Legacy Coexistence

### What Uses What

| Component | Framework | Notes |
|-----------|-----------|-------|
| SAAS Admin | Django ORM + Django Ninja | **NEW STANDARD** |
| Skins | Django ORM + Django Ninja | **NEW STANDARD** |
| Multimodal | SQLAlchemy + FastAPI | Legacy, keep as-is |
| Chat routing | FastAPI | Legacy, keep as-is |
| Tool executor | FastAPI | Legacy, keep as-is |

### Rule

> **New features** → Django ORM + Django Ninja only  
> **Existing code** → Don't convert unless touched

---

## 7. Security Patterns

### 7.1 Audit Logging

```python
from admin.saas.models import AuditLog

def log_action(actor_id, action, resource_type, resource_id, 
               old_value=None, new_value=None, request=None):
    """Log admin action for compliance."""
    AuditLog.objects.create(
        actor_id=actor_id,
        actor_email=request.user.email if request else '',
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        old_value=old_value,
        new_value=new_value,
        ip_address=get_client_ip(request) if request else None,
    )
```

### 7.2 Multi-Tenant Isolation

```python
# ALWAYS filter by tenant_id
@router.get("/agents")
def list_agents(request, tenant_id: UUID):
    from admin.saas.models import Agent
    # Security: Only return agents for this tenant
    return Agent.objects.filter(tenant_id=tenant_id)
```

---

## 8. Testing Patterns

```python
from django.test import TestCase
from admin.saas.models import Tenant, SubscriptionTier

class TenantModelTest(TestCase):
    def setUp(self):
        self.tier = SubscriptionTier.objects.create(
            name='Test Tier',
            slug='test'
        )
    
    def test_create_tenant(self):
        tenant = Tenant.objects.create(
            name='Test Org',
            slug='test-org',
            tier=self.tier
        )
        self.assertEqual(tenant.status, 'pending')
```

---

## Quick Reference

| Task | Command/Pattern |
|------|-----------------|
| New Django app | `mkdir -p admin/<app> && touch admin/<app>/{__init__,apps,models}.py` |
| Register app | Add to `INSTALLED_APPS` in `django_setup.py` |
| Create model | Follow template in Section 2.1 |
| Create API | Add to router in `services/gateway/routers/` |
| Make migrations | See Section 4.1 |
| Run migrations | See Section 4.1 |
