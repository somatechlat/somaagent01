# SRS: Permission-Gated Journey Map

**Document ID:** SA01-SRS-PERMISSION-JOURNEYS-2025-12
**Purpose:** Connect EVERY screen and action to required permissions
**Status:** CANONICAL REFERENCE

---

## 1. Permission Matrix Integration

This document ensures **every screen, API endpoint, and action** is gated by the correct permission from our 78-permission matrix.

---

## 2. Platform Admin Screens — Permission Requirements

### 2.1 Dashboard & Overview

| Route | Required Permissions | Fallback |
|-------|---------------------|----------|
| `/platform` | `platform:read_metrics` | Redirect to login |
| `/platform/tenants` | `tenant:read` | 403 Forbidden |
| `/platform/tenants/:id` | `tenant:read` | 403 Forbidden |
| `/platform/tenants/create` | `tenant:create` | Button hidden |
| `/platform/subscriptions` | `platform:manage_billing` | 403 Forbidden |
| `/platform/subscriptions/:id` | `platform:manage_billing` | 403 Forbidden |
| `/platform/subscriptions/:id/quotas` | `platform:manage_billing` | 403 Forbidden |

### 2.2 Permissions & Roles

| Route | Required Permissions | Fallback |
|-------|---------------------|----------|
| `/platform/permissions` | `platform:manage` | 403 Forbidden |
| `/platform/roles` | `platform:manage` | 403 Forbidden |
| `/platform/roles/create` | `platform:manage` | Button hidden |

### 2.3 Infrastructure

| Route | Required Permissions | Fallback |
|-------|---------------------|----------|
| `/platform/infrastructure` | `infra:view` | 403 Forbidden |
| `/platform/infrastructure/*` (view) | `infra:view` | 403 Forbidden |
| `/platform/infrastructure/*` (edit) | `infra:configure` | Edit disabled |
| `/platform/infrastructure/redis/ratelimits` | `infra:ratelimit` | 403 Forbidden |

### 2.4 Metrics & Observability

| Route | Required Permissions | Fallback |
|-------|---------------------|----------|
| `/platform/metrics` | `platform:read_metrics` | 403 Forbidden |
| `/platform/metrics/llm` | `platform:read_metrics` | 403 Forbidden |
| `/platform/metrics/tools` | `platform:read_metrics` | 403 Forbidden |
| `/platform/metrics/memory` | `platform:read_metrics` | 403 Forbidden |
| `/platform/metrics/sla` | `platform:read_metrics` | 403 Forbidden |

### 2.5 Features & Models

| Route | Required Permissions | Fallback |
|-------|---------------------|----------|
| `/platform/features` | `platform:manage_features` | 403 Forbidden |
| `/platform/models` | `platform:manage` | 403 Forbidden |

### 2.6 Audit

| Route | Required Permissions | Fallback |
|-------|---------------------|----------|
| `/platform/audit` | `audit:read` | 403 Forbidden |

---

## 3. Tenant Admin Screens — Permission Requirements

### 3.1 Dashboard & Users

| Route | Required Permissions | Fallback |
|-------|---------------------|----------|
| `/admin` | `tenant:read` | Redirect to login |
| `/admin/users` | `user:read` | 403 Forbidden |
| `/admin/users/:id` | `user:read` | 403 Forbidden |
| `/admin/users/invite` | `user:create` | Button hidden |
| Edit user | `user:update` | Edit disabled |
| Delete user | `user:delete` | Button hidden |
| Assign role | `user:assign_roles` | Action hidden |

### 3.2 Agents

| Route | Required Permissions | Fallback |
|-------|---------------------|----------|
| `/admin/agents` | `agent:read` | 403 Forbidden |
| `/admin/agents/:id` | `agent:read` | 403 Forbidden |
| `/admin/agents/create` | `agent:create` | Button hidden |
| Start agent | `agent:start` | Button hidden |
| Stop agent | `agent:stop` | Button hidden |
| Delete agent | `agent:delete` | Button hidden |

### 3.3 Usage & Billing

| Route | Required Permissions | Fallback |
|-------|---------------------|----------|
| `/admin/usage` | `billing:view_usage` | 403 Forbidden |
| `/admin/billing` | `billing:view_invoices` | 403 Forbidden |
| Change plan | `billing:change_plan` | Button hidden |
| Manage payment | `billing:manage_payment` | Button hidden |

### 3.4 Settings

| Route | Required Permissions | Fallback |
|-------|---------------------|----------|
| `/admin/settings` | `tenant:update` | 403 Forbidden |
| `/admin/settings/api-keys` | `apikey:read` | 403 Forbidden |
| Create API key | `apikey:create` | Button hidden |
| Revoke API key | `apikey:revoke` | Button hidden |
| `/admin/settings/integrations` | `integration:read` | 403 Forbidden |

### 3.5 Audit

| Route | Required Permissions | Fallback |
|-------|---------------------|----------|
| `/admin/audit` | `audit:read` | 403 Forbidden |

### 3.6 Metrics

| Route | Required Permissions | Fallback |
|-------|---------------------|----------|
| `/admin/metrics` | `tenant:read` | 403 Forbidden |
| `/admin/metrics/agents` | `agent:read` | 403 Forbidden |

---

## 4. Agent User Screens — Permission Requirements

### 4.1 Chat

| Route | Required Permissions | Fallback |
|-------|---------------------|----------|
| `/chat` | `conversation:read` | 403 Forbidden |
| `/chat/:conversationId` | `conversation:read` | 403 Forbidden |
| Send message | `conversation:send_message` | Input disabled |
| Create conversation | `conversation:create` | Button hidden |
| Delete conversation | `conversation:delete` | Button hidden |
| Export conversation | `conversation:export` | Button hidden |

### 4.2 Memory

| Route | Required Permissions | Fallback |
|-------|---------------------|----------|
| `/memory` | `memory:read` | 403 Forbidden |
| `/memory/:id` | `memory:read` | 403 Forbidden |
| Search memory | `memory:search` | Search hidden |
| Delete memory | `memory:delete` | Button hidden |
| Export memory | `memory:export` | Button hidden |

### 4.3 Settings

| Route | Required Permissions | Fallback |
|-------|---------------------|----------|
| `/settings` | `agent:read` | 403 Forbidden |
| `/settings/models` | `agent:configure_*` OR `agent:update` | 403 Forbidden |
| `/settings/memory` | `agent:configure_*` OR `agent:update` | 403 Forbidden |
| `/settings/voice` | `agent:configure_*` OR `agent:update` | 403 Forbidden |
| `/settings/tools` | `agent:configure_tools` | 403 Forbidden |
| `/settings/multimodal` | `agent:update` | 403 Forbidden |
| Save settings | `agent:update` | Save disabled |

### 4.4 Profile

| Route | Required Permissions | Fallback |
|-------|---------------------|----------|
| `/profile` | `user:read` (self) | 403 Forbidden |
| Update profile | `user:update` (self) | Save disabled |

---

## 5. Developer Mode — Permission Requirements

| Route | Required Permissions | Additional |
|-------|---------------------|------------|
| `/dev/console` | `agent:view_logs` | DEV mode enabled |
| `/dev/mcp` | `tool:read` | DEV mode enabled |
| `/dev/logs` | `agent:view_logs` | DEV mode enabled |
| `/dev/metrics` | `agent:read` | DEV mode enabled |

---

## 6. Trainer Mode — Permission Requirements

| Route | Required Permissions | Additional |
|-------|---------------------|------------|
| `/trn/cognitive` | `agent:configure_personality` | TRN mode enabled |
| `/trn/memory` | `memory:update` | TRN mode enabled |

---

## 7. API Endpoint Permission Matrix

### 7.1 Infrastructure APIs

| Endpoint | Method | Permission |
|----------|--------|------------|
| `/api/v2/infrastructure/health` | GET | `infra:view` |
| `/api/v2/infrastructure/{service}/config` | GET | `infra:view` |
| `/api/v2/infrastructure/{service}/config` | PUT | `infra:configure` |
| `/api/v2/infrastructure/ratelimits` | GET | `infra:view` |
| `/api/v2/infrastructure/ratelimits` | POST | `infra:ratelimit` |
| `/api/v2/infrastructure/ratelimits/{key}` | PUT | `infra:ratelimit` |
| `/api/v2/infrastructure/ratelimits/{key}` | DELETE | `infra:ratelimit` |

### 7.2 Tenant APIs

| Endpoint | Method | Permission |
|----------|--------|------------|
| `/api/v2/tenants` | GET | `tenant:read` |
| `/api/v2/tenants` | POST | `tenant:create` |
| `/api/v2/tenants/{id}` | GET | `tenant:read` |
| `/api/v2/tenants/{id}` | PUT | `tenant:update` |
| `/api/v2/tenants/{id}` | DELETE | `tenant:delete` |
| `/api/v2/tenants/{id}/suspend` | POST | `tenant:suspend` |
| `/api/v2/tenants/{id}/usage` | GET | `billing:view_usage` |

### 7.3 User APIs

| Endpoint | Method | Permission |
|----------|--------|------------|
| `/api/v2/users` | GET | `user:read` |
| `/api/v2/users` | POST | `user:create` |
| `/api/v2/users/{id}` | GET | `user:read` |
| `/api/v2/users/{id}` | PUT | `user:update` |
| `/api/v2/users/{id}` | DELETE | `user:delete` |
| `/api/v2/users/{id}/roles` | PUT | `user:assign_roles` |

### 7.4 Agent APIs

| Endpoint | Method | Permission |
|----------|--------|------------|
| `/api/v2/agents` | GET | `agent:read` |
| `/api/v2/agents` | POST | `agent:create` |
| `/api/v2/agents/{id}` | GET | `agent:read` |
| `/api/v2/agents/{id}` | PUT | `agent:update` |
| `/api/v2/agents/{id}` | DELETE | `agent:delete` |
| `/api/v2/agents/{id}/start` | POST | `agent:start` |
| `/api/v2/agents/{id}/stop` | POST | `agent:stop` |
| `/api/v2/agents/{id}/config` | GET | `agent:read` |
| `/api/v2/agents/{id}/config` | PUT | `agent:update` |
| `/api/v2/agents/{id}/config/models` | PUT | `agent:configure_*` |
| `/api/v2/agents/{id}/multimodal` | PUT | `agent:update` |

### 7.5 Conversation APIs

| Endpoint | Method | Permission |
|----------|--------|------------|
| `/api/v2/conversations` | GET | `conversation:read` |
| `/api/v2/conversations` | POST | `conversation:create` |
| `/api/v2/conversations/{id}` | GET | `conversation:read` |
| `/api/v2/conversations/{id}` | DELETE | `conversation:delete` |
| `/api/v2/conversations/{id}/messages` | POST | `conversation:send_message` |
| `/api/v2/conversations/{id}/export` | GET | `conversation:export` |

### 7.6 Memory APIs

| Endpoint | Method | Permission |
|----------|--------|------------|
| `/api/v2/memory` | GET | `memory:read` |
| `/api/v2/memory/search` | POST | `memory:search` |
| `/api/v2/memory/{id}` | GET | `memory:read` |
| `/api/v2/memory/{id}` | DELETE | `memory:delete` |
| `/api/v2/memory/export` | GET | `memory:export` |

### 7.7 Observability APIs

| Endpoint | Method | Permission |
|----------|--------|------------|
| `/api/v2/observability/health` | GET | `platform:read_metrics` |
| `/api/v2/observability/metrics/*` | GET | `platform:read_metrics` |
| `/api/v2/observability/sla` | GET | `platform:read_metrics` |

---

## 8. Role → Permission → Screen Mapping

### 8.1 SAAS Super Admin

```
Permissions: * (ALL)
Screens: ALL 66 screens accessible
```

### 8.2 Tenant Admin

```
Permissions:
  - tenant:read, tenant:update
  - user:*, agent:*, conversation:*, memory:*
  - tool:*, file:*, apikey:*, integration:*
  - audit:read, backup:read, billing:view_*

Screens:
  ✅ /admin/* (all)
  ✅ /chat, /memory, /settings (all)
  ❌ /platform/* (none)
```

### 8.3 Agent Owner

```
Permissions:
  - agent:read, agent:update, agent:start, agent:stop
  - agent:configure_*, agent:view_logs, agent:export
  - conversation:*, memory:*
  - tool:read, tool:execute
  - file:upload, file:read

Screens:
  ✅ /chat, /memory (all)
  ✅ /settings (all, edit enabled)
  ❌ /admin/* (none)
  ❌ /platform/* (none)
```

### 8.4 Agent Operator

```
Permissions:
  - agent:read, agent:start, agent:stop, agent:view_logs
  - conversation:*, memory:read, memory:search
  - tool:read, tool:execute
  - file:upload, file:read

Screens:
  ✅ /chat (full)
  ✅ /memory (read-only)
  ⚠️ /settings (read-only)
  ❌ /admin/*
  ❌ /platform/*
```

### 8.5 Standard User

```
Permissions:
  - agent:read
  - conversation:create, conversation:read, conversation:send_message, conversation:view_history
  - memory:read
  - file:upload, file:read

Screens:
  ✅ /chat (limited)
  ⚠️ /memory (read-only)
  ❌ /settings
  ❌ /admin/*
  ❌ /platform/*
```

### 8.6 Viewer

```
Permissions:
  - agent:read
  - conversation:read
  - memory:read
  - file:read

Screens:
  ⚠️ /chat (read-only, no send)
  ⚠️ /memory (read-only)
  ❌ /settings
  ❌ /admin/*
  ❌ /platform/*
```

---

## 9. Frontend Permission Enforcement

### 9.1 Route Guard

```typescript
// webui/src/guards/permission-guard.ts

const ROUTE_PERMISSIONS = {
  '/platform': ['platform:read_metrics'],
  '/platform/infrastructure': ['infra:view'],
  '/platform/infrastructure/redis/ratelimits': ['infra:ratelimit'],
  '/admin': ['tenant:read'],
  '/admin/users': ['user:read'],
  '/settings': ['agent:read'],
  // ... all routes
};

function checkRoute(route: string, userPermissions: string[]): boolean {
  const required = ROUTE_PERMISSIONS[route];
  return required.some(p => userPermissions.includes(p) || userPermissions.includes('*'));
}
```

### 9.2 Action Guard

```typescript
// webui/src/guards/action-guard.ts

function canPerformAction(action: string, userPermissions: string[]): boolean {
  const actionPermissions = {
    'create_tenant': 'tenant:create',
    'delete_user': 'user:delete',
    'configure_ratelimits': 'infra:ratelimit',
    // ... all actions
  };
  const required = actionPermissions[action];
  return userPermissions.includes(required) || userPermissions.includes('*');
}
```

---

## 10. Backend Permission Enforcement

### 10.1 Django Ninja Auth

```python
# admin/core/permissions.py

from functools import wraps
from ninja import Router
from ninja.errors import HttpError

def require_permission(*permissions):
    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            user_perms = get_user_permissions(request.auth)
            if '*' in user_perms:
                return await func(request, *args, **kwargs)
            if not any(p in user_perms for p in permissions):
                raise HttpError(403, "Permission denied")
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

# Usage:
@router.get("/infrastructure/health")
@require_permission("infra:view")
async def get_health(request):
    ...
```

---

## 11. Implementation Checklist

- [ ] Frontend route guards with permission checks
- [ ] Backend API permission decorators
- [ ] Permission caching (Redis)
- [ ] Permission inheritance (role → permissions)
- [ ] Permission UI (conditionally show/hide buttons)
- [ ] Permission audit logging
