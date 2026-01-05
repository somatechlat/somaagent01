# Implementation Tasks — Phase 1: Foundation

**Phase:** 1 of 4  
**Priority:** P0 (Critical Path)  
**Duration:** 2-3 weeks

---

## 1. Database Schema (Django Models)

### 1.1 Core Models

| Task | Priority | Estimated | Dependencies |
|------|----------|-----------|--------------|
| Create `Tenant` model | P0 | 2h | None |
| Create `User` model extension | P0 | 2h | Tenant |
| Create `Agent` model | P0 | 3h | Tenant |
| Create `Subscription` model | P0 | 2h | Tenant |
| Create `SubscriptionTier` model | P0 | 1h | None |
| Create `AuditLog` model | P0 | 2h | User, Tenant |

### 1.2 Model Specifications

```python
# core/models.py

class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    status = models.CharField(choices=TENANT_STATUS, default='active')
    subscription = models.ForeignKey('SubscriptionTier', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    settings = models.JSONField(default=dict)

class TenantUser(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE)
    role = models.CharField(choices=TENANT_ROLES)
    status = models.CharField(choices=USER_STATUS)
    invited_by = models.ForeignKey('User', null=True)
    joined_at = models.DateTimeField(null=True)

class Agent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    owner = models.ForeignKey('User', on_delete=models.PROTECT)
    status = models.CharField(choices=AGENT_STATUS)
    config = models.JSONField(default=dict)
    features = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['tenant', 'slug']

class SubscriptionTier(models.Model):
    name = models.CharField(max_length=50)  # free, starter, team, enterprise
    max_agents = models.IntegerField()
    max_users = models.IntegerField()
    max_tokens_per_month = models.BigIntegerField()
    max_storage_gb = models.IntegerField()
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2)
    lago_plan_code = models.CharField(max_length=50)
```

### 1.3 Migrations

| Task | Priority | Files |
|------|----------|-------|
| Initial migration | P0 | `0001_initial.py` |
| Add indexes | P0 | `0002_add_indexes.py` |
| Add constraints | P0 | `0003_add_constraints.py` |

---

## 2. SpiceDB Schema

### 2.1 Schema Definition

| Task | Priority | Estimated |
|------|----------|-----------|
| Define platform schema | P0 | 1h |
| Define tenant schema | P0 | 2h |
| Define agent schema | P0 | 2h |
| Test permission checks | P0 | 3h |

### 2.2 Schema File

```zed
// spicedb/schema.zed

definition platform {}

definition saas_admin {
    relation platform: platform
    permission manage = platform
    permission manage_tenants = platform
    permission view_billing = platform
    permission configure = platform
    permission impersonate = platform
}

definition tenant {
    relation sysadmin: user
    relation admin: user
    relation developer: user
    relation trainer: user
    relation member: user
    relation viewer: user
    relation subscription: subscription_tier
    
    permission manage = sysadmin
    permission administrate = sysadmin + admin
    permission create_agent = sysadmin + admin
    permission develop = sysadmin + admin + developer
    permission train = sysadmin + admin + trainer
    permission use = develop + train + member
    permission view = use + viewer
}

definition agent {
    relation tenant: tenant
    relation owner: user
    relation admin: user
    relation developer: user
    relation trainer: user
    relation user: user
    relation viewer: user
    
    permission configure = owner + admin + tenant->administrate
    permission activate_adm = owner + admin
    permission activate_dev = configure + developer
    permission activate_trn = configure + trainer
    permission activate_std = activate_dev + activate_trn + user
    permission activate_ro = activate_std + viewer
    permission view = activate_ro
}
```

### 2.3 Integration

| Task | Priority | Estimated |
|------|----------|-----------|
| Create SpiceDB client wrapper | P0 | 2h |
| Create permission middleware | P0 | 3h |
| Create permission decorators | P0 | 2h |
| Write integration tests | P0 | 4h |

---

## 3. Keycloak Configuration

### 3.1 Realm Setup

| Task | Priority | Estimated |
|------|----------|-----------|
| Create `somaagent` realm | P0 | 1h |
| Configure Google OAuth | P0 | 1h |
| Configure GitHub OAuth | P0 | 1h |
| Enable MFA (TOTP) | P0 | 1h |
| Configure token lifetimes | P0 | 30m |
| Create client for Django | P0 | 1h |

### 3.2 Realm JSON

```json
{
  "realm": "somaagent",
  "enabled": true,
  "sslRequired": "external",
  "registrationAllowed": false,
  "loginWithEmailAllowed": true,
  "duplicateEmailsAllowed": false,
  "bruteForceProtected": true,
  "permanentLockout": false,
  "maxFailureWaitSeconds": 900,
  "minimumQuickLoginWaitSeconds": 60,
  "waitIncrementSeconds": 60,
  "quickLoginCheckMilliSeconds": 1000,
  "maxDeltaTimeSeconds": 43200,
  "failureFactor": 5,
  "accessTokenLifespan": 900,
  "accessTokenLifespanForImplicitFlow": 900,
  "ssoSessionIdleTimeout": 1800,
  "ssoSessionMaxLifespan": 36000,
  "offlineSessionIdleTimeout": 2592000,
  "accessCodeLifespan": 60,
  "accessCodeLifespanUserAction": 300,
  "accessCodeLifespanLogin": 1800,
  "requiredCredentials": ["password"],
  "otpPolicyType": "totp",
  "otpPolicyAlgorithm": "HmacSHA1",
  "otpPolicyDigits": 6,
  "otpPolicyPeriod": 30
}
```

---

## 4. Base Lit Components

### 4.1 Component Library

| Component | Priority | Estimated |
|-----------|----------|-----------|
| `saas-shell` (app shell) | P0 | 4h |
| `saas-nav` (navigation) | P0 | 3h |
| `saas-card` (stat card) | P0 | 2h |
| `saas-table` (data table) | P0 | 4h |
| `saas-modal` (dialog) | P0 | 3h |
| `saas-form` (form wrapper) | P0 | 3h |
| `saas-input` (form input) | P0 | 2h |
| `saas-button` (buttons) | P0 | 1h |
| `saas-toast` (notifications) | P0 | 2h |
| `saas-badge` (status badges) | P0 | 1h |

### 4.2 Design Tokens

> **Canonical Source:** [tokens.css](file:///Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgent01/webui/src/styles/tokens.css)

```css
/* somastack-tokens.css — aligned with canonical tokens.css */

:root {
  /* Backgrounds - Light Theme */
  --saas-bg-page: #f5f5f5;
  --saas-bg-card: #ffffff;
  --saas-bg-hover: #fafafa;
  
  /* Text - Light Theme */  
  --saas-text-primary: #1a1a1a;
  --saas-text-secondary: #666666;
  --saas-text-muted: #999999;
  
  /* Accent - Primary Action */
  --saas-accent: #1a1a1a;
  --saas-accent-hover: #333333;
  
  /* Status Colors */
  --saas-status-success: #22c55e;
  --saas-status-warning: #f59e0b;
  --saas-status-danger: #ef4444;
  --saas-status-info: #3b82f6;
  
  /* Spacing */
  --saas-space-xs: 4px;
  --saas-space-sm: 8px;
  --saas-space-md: 16px;
  --saas-space-lg: 24px;
  --saas-space-xl: 32px;
  
  /* Typography */
  --saas-font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --saas-font-mono: 'JetBrains Mono', monospace;
  
  /* Borders */
  --saas-radius-sm: 4px;
  --saas-radius-md: 8px;
  --saas-radius-lg: 12px;
  --saas-radius-full: 9999px;
  --saas-border-color: #e2e8f0;
  
  /* Shadows */
  --saas-shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --saas-shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  --saas-shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
}
```

---

## 5. API Foundation

### 5.1 Django Ninja Setup

| Task | Priority | Estimated |
|------|----------|-----------|
| Create API app | P0 | 1h |
| Configure routers | P0 | 1h |
| Create auth middleware | P0 | 3h |
| Create error handlers | P0 | 2h |
| Create base schemas | P0 | 2h |
| Setup OpenAPI docs | P0 | 1h |

### 5.2 Base Configuration

```python
# api/main.py
from ninja import NinjaAPI
from ninja.security import HttpBearer

class JWTAuth(HttpBearer):
    async def authenticate(self, request, token):
        # Verify Keycloak JWT
        pass

api = NinjaAPI(
    title="SomaAgent API",
    version="2.0.0",
    auth=JWTAuth(),
    docs_url="/api/v2/docs",
)

# Include routers
api.add_router("/saas/", saas_router, tags=["Platform Admin"])
api.add_router("/admin/", admin_router, tags=["Tenant Admin"])
api.add_router("/agent/", agent_router, tags=["Agent Config"])
api.add_router("/chat/", chat_router, tags=["Chat"])
api.add_router("/memory/", memory_router, tags=["Memory"])
api.add_router("/voice/", voice_router, tags=["Voice"])
api.add_router("/auth/", auth_router, tags=["Authentication"])
```

---

## 6. Checklist

### Week 1
- [ ] Django project setup
- [ ] All models defined
- [ ] Initial migrations
- [ ] SpiceDB schema written
- [ ] SpiceDB client wrapper

### Week 2
- [ ] Keycloak realm configured
- [ ] OAuth providers setup
- [ ] JWT validation middleware
- [ ] Base API routers
- [ ] Error handling

### Week 3
- [ ] Base Lit components
- [ ] Design tokens CSS
- [ ] App shell component
- [ ] Navigation component
- [ ] Integration tests

---

**Next Phase:** [TASKS-PHASE2-AUTH.md](./TASKS-PHASE2-AUTH.md)
