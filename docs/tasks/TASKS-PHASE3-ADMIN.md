# Implementation Tasks — Phase 3: Admin Interfaces

**Phase:** 3 of 4  
**Priority:** P0  
**Duration:** 2-3 weeks  
**Dependencies:** Phase 1-2 complete

---

## 1. SAAS Platform Admin

### 1.1 Endpoints

| Endpoint | Method | Task | Estimated |
|----------|--------|------|-----------|
| `/saas/stats` | GET | Platform statistics | 2h |
| `/saas/tenants` | GET | List tenants | 2h |
| `/saas/tenants` | POST | Create tenant | 4h |
| `/saas/tenants/{id}` | GET | Get tenant | 1h |
| `/saas/tenants/{id}` | PUT | Update tenant | 2h |
| `/saas/tenants/{id}` | DELETE | Delete tenant | 3h |
| `/saas/tenants/{id}/suspend` | POST | Suspend tenant | 2h |
| `/saas/tenants/{id}/impersonate` | POST | Impersonate | 3h |
| `/saas/subscriptions` | GET/PUT | Manage tiers | 3h |
| `/saas/billing/revenue` | GET | Revenue report | 3h |
| `/saas/health` | GET | System health | 2h |

### 1.2 Components

| Component | Screens | Estimated |
|-----------|---------|-----------|
| `saas-platform-dashboard.ts` | Dashboard | 6h |
| `saas-tenant-list.ts` | Tenant list | 4h |
| `saas-tenant-create.ts` | Create modal | 3h |
| `saas-tenant-detail.ts` | Tenant detail | 4h |
| `saas-subscription-tiers.ts` | Tier config | 4h |
| `saas-platform-health.ts` | Health dashboard | 4h |
| `saas-revenue-dashboard.ts` | Revenue charts | 5h |

---

## 2. Tenant Admin

### 2.1 Endpoints

| Endpoint | Method | Task | Estimated |
|----------|--------|------|-----------|
| `/admin/stats` | GET | Tenant stats | 2h |
| `/admin/users` | GET | List users | 2h |
| `/admin/users/invite` | POST | Invite user | 4h |
| `/admin/users/{id}` | GET/PUT/DELETE | User CRUD | 3h |
| `/admin/users/{id}/resend` | POST | Resend invite | 1h |
| `/admin/agents` | GET | List agents | 2h |
| `/admin/agents` | POST | Create agent | 5h |
| `/admin/agents/{id}` | GET/PUT | Agent config | 3h |
| `/admin/agents/{id}` | DELETE | Delete agent | 3h |
| `/admin/agents/{id}/start` | POST | Start agent | 2h |
| `/admin/agents/{id}/stop` | POST | Stop agent | 2h |
| `/admin/agents/{id}/users` | GET/POST/DELETE | Agent users | 3h |
| `/admin/settings` | GET/PUT | Tenant settings | 2h |
| `/admin/audit` | GET | Audit log | 3h |
| `/admin/usage` | GET | Usage stats | 3h |
| `/admin/billing` | GET | Billing info | 2h |
| `/admin/billing/upgrade` | POST | Upgrade plan | 4h |

### 2.2 Components

| Component | Screens | Estimated |
|-----------|---------|-----------|
| `saas-tenant-dashboard.ts` | Dashboard | 5h |
| `saas-users.ts` | User list | 4h |
| `saas-user-invite.ts` | Invite modal | 3h |
| `saas-user-detail.ts` | User detail | 3h |
| `saas-agents.ts` | Agent grid | 5h |
| `saas-agent-create.ts` | Create modal | 4h |
| `saas-agent-config.ts` | Config page | 6h |
| `saas-agent-users.ts` | Agent users | 3h |
| `saas-tenant-settings.ts` | Settings tabs | 5h |
| `saas-tenant-audit.ts` | Audit log | 4h |
| `saas-usage.ts` | Usage charts | 4h |
| `saas-tenant-billing.ts` | Billing page | 5h |

---

## 3. Quota Enforcement

### 3.1 Implementation

```python
# services/quota.py

class QuotaService:
    async def check_quota(
        self,
        tenant_id: str,
        resource: str,  # 'users', 'agents', 'tokens', 'storage'
    ) -> QuotaStatus:
        """Check if tenant is within quota limits."""
        tenant = await Tenant.objects.select_related('subscription').get(id=tenant_id)
        tier = tenant.subscription
        
        if resource == 'users':
            current = await TenantUser.objects.filter(tenant=tenant).count()
            limit = tier.max_users
        elif resource == 'agents':
            current = await Agent.objects.filter(tenant=tenant).count()
            limit = tier.max_agents
        elif resource == 'tokens':
            current = await self._get_token_usage(tenant_id)
            limit = tier.max_tokens_per_month
        elif resource == 'storage':
            current = await self._get_storage_usage(tenant_id)
            limit = tier.max_storage_gb * 1024 * 1024 * 1024  # bytes
        
        return QuotaStatus(
            resource=resource,
            current=current,
            limit=limit,
            exceeded=current >= limit,
            percentage=min(100, int(current / limit * 100)),
        )
    
    async def enforce_quota(self, tenant_id: str, resource: str):
        """Raise if quota exceeded."""
        status = await self.check_quota(tenant_id, resource)
        if status.exceeded:
            raise QuotaExceededError(
                f"{resource.title()} limit reached for your plan",
                current=status.current,
                limit=status.limit,
                upgrade_url="/admin/billing/upgrade",
            )
```

### 3.2 Tasks

| Task | Priority | Estimated |
|------|----------|-----------|
| QuotaService implementation | P0 | 4h |
| Integrate into user invite | P0 | 1h |
| Integrate into agent create | P0 | 1h |
| Quota warning UI component | P0 | 3h |
| Upgrade prompt modal | P0 | 2h |

---

## 4. Audit Logging

### 4.1 Implementation

```python
# services/audit.py

class AuditService:
    async def log(
        self,
        user_id: str,
        tenant_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: dict = None,
        ip_address: str = None,
    ):
        """Log an audit event."""
        await AuditLog.objects.create(
            id=uuid.uuid4(),
            user_id=user_id,
            tenant_id=tenant_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            timestamp=timezone.now(),
        )
        
        # Also emit to Kafka for real-time processing
        await kafka_producer.send(
            "audit-events",
            {
                "user_id": user_id,
                "tenant_id": tenant_id,
                "action": action,
                "resource": f"{resource_type}:{resource_id}",
                "timestamp": timezone.now().isoformat(),
            }
        )
```

### 4.2 Audit Actions

| Action | Trigger |
|--------|---------|
| `user.invite` | User invite sent |
| `user.accept` | User accepted invite |
| `user.remove` | User removed |
| `user.role_change` | Role changed |
| `agent.create` | Agent created |
| `agent.delete` | Agent deleted |
| `agent.configure` | Agent config changed |
| `agent.start` | Agent started |
| `agent.stop` | Agent stopped |
| `settings.update` | Settings changed |
| `billing.upgrade` | Plan upgraded |
| `billing.downgrade` | Plan downgraded |

---

## 5. Lago Billing Integration

### 5.1 Tasks

| Task | Priority | Estimated |
|------|----------|-----------|
| Lago API client | P0 | 4h |
| Create customer on tenant create | P0 | 2h |
| Subscribe to plan | P0 | 3h |
| Usage metering | P0 | 4h |
| Webhook receiver | P0 | 4h |
| Invoice display | P1 | 3h |
| Payment method update | P1 | 4h |

### 5.2 Webhook Handler

```python
# api/routers/webhooks.py

@router.post("/lago/webhook")
async def lago_webhook(request, data: dict):
    """Handle Lago billing events."""
    event_type = data.get("webhook_type")
    
    if event_type == "invoice.created":
        invoice = data["invoice"]
        tenant = await get_tenant_by_lago_customer(invoice["customer"]["external_id"])
        # Store invoice, send notification
        
    elif event_type == "invoice.payment_failed":
        invoice = data["invoice"]
        tenant = await get_tenant_by_lago_customer(invoice["customer"]["external_id"])
        # Send payment failed email
        # Start grace period
        
    elif event_type == "subscription.terminated":
        subscription = data["subscription"]
        tenant = await get_tenant_by_lago_customer(subscription["customer"]["external_id"])
        # Suspend tenant
        
    return {"status": "ok"}
```

---

## 6. Checklist

### Week 1
- [ ] SAAS platform dashboard
- [ ] Tenant list/create/edit
- [ ] Tenant suspend/delete
- [ ] Impersonation flow
- [ ] Health dashboard

### Week 2
- [ ] Tenant dashboard
- [ ] User management (list/invite/roles)
- [ ] Agent management (list/create)
- [ ] Agent config page
- [ ] Quota enforcement

### Week 3
- [ ] Tenant settings
- [ ] Audit log
- [ ] Billing page
- [ ] Lago integration
- [ ] Usage dashboard

---

**Next Phase:** [TASKS-PHASE4-AGENT.md](./TASKS-PHASE4-AGENT.md)
