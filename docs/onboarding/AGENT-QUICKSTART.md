# 🤖 SomaAgent01 - Agent Context Guide

> **For AI Agents** - Essential context before working on this codebase

---

## Before You Code

**Read these files FIRST:**

1. `AGENT.md` - Complete knowledge base (1000+ lines)
2. `docs/development/VIBE_CODING_RULES.md` - Non-negotiable rules
3. Check existing code before creating new files

---

## VIBE Coding Rules Summary

| Rule | Description |
|------|-------------|
| **Rule 1** | NO BULLSHIT - No mocks, no placeholders, no TODOs |
| **Rule 2** | CHECK FIRST, CODE SECOND - Review architecture before coding |
| **Rule 3** | NO UNNECESSARY FILES - Modify existing files when possible |
| **Rule 4** | REAL IMPLEMENTATIONS ONLY - Production-grade code always |
| **Rule 5** | DOCUMENTATION = TRUTH - Verify from official docs |
| **Rule 6** | COMPLETE CONTEXT REQUIRED - Understand full flow first |
| **Rule 7** | REAL DATA, REAL SERVERS - Use actual services |

---

## Technology Stack (STRICT)

| Layer | Technology | Forbidden |
|-------|------------|-----------|
| API | Django 5.0 + Django Ninja | ❌ FastAPI |
| ORM | Django ORM | ❌ SQLAlchemy |
| Migrations | Django Migrations | ❌ Alembic |
| Frontend | Lit 3.x Web Components | ❌ React, Alpine.js |
| Vector DB | Milvus | ❌ Qdrant |

---

## Key Files Reference

### Backend (Python/Django)

| File | Purpose |
|------|---------|
| `admin/api.py` | Master API router - all endpoints registered here |
| `admin/auth/api.py` | Auth endpoints: `/token`, `/login`, `/refresh`, `/logout` |
| `admin/common/auth.py` | JWT validation: `AuthBearer`, `RoleRequired`, `decode_token()` |
| `admin/core/models.py` | Django ORM models: `Session`, `Capsule`, etc. |
| `services/gateway/auth.py` | Gateway JWT + OPA policy integration |
| `services/common/audit.py` | Kafka audit publisher |

### Frontend (TypeScript/Lit)

| File | Purpose |
|------|---------|
| `webui/src/views/saas-login.ts` | Login page (888 lines, full OAuth/SSO) |
| `webui/src/views/saas-chat.ts` | Chat view (1063 lines, WebSocket) |
| `webui/src/services/keycloak-service.ts` | Keycloak OIDC client |
| `webui/src/stores/auth-store.ts` | Auth state management |

---

## Port Namespace - DEPLOYMENT MODES

**⚠️ CRITICAL: Port numbers vary by deployment mode**

### SAAS Deployment (Primary - ./infra/saas/)
```
Internal (Container) → External (Host)
├── PostgreSQL:  5432 → 63932
├── Redis:       6379 → 63979
├── Kafka:       9092 → 63992
├── Vault:       8200 → 63982  (Secrets - NO ENV VARS!)
├── Agent API:   9000 → 63900
├── Brain API:   9696 → 63996
├── Memory API:  10101 → 63901
├── Milvus:      19530 → 63953
├── OPA:         8181 → 63904
├── Prometheus:  9090 → 63905
└── Grafana:     3000 → 63906
```

### Kubernetes Deployment (./infra/k8s/)
```
Service → NodePort
├── PostgreSQL:  5432 → 32432
├── Redis:       6379 → 32379
├── Kafka:       9092 → 32092
├── Agent API:   9000 → 32900 (LoadBalancer)
└── Vault:       8200 → 32982
```

### Local Development
```
Standard defaults:
├── PostgreSQL:  5432
├── Redis:       6379
├── Kafka:       9092
└── Vault:       8200
```

**⚠️ DEPRECATED: Port 20432 is NEVER used in current codebase.**

---

## Common Tasks

### Add API Endpoint

1. Find the relevant app in `admin/{app}/api.py`
2. Add the endpoint using Django Ninja decorators
3. Register in `admin/api.py` if new router

```python
# Example: admin/agents/api.py
@router.get("/{agent_id}")
def get_agent(request, agent_id: str):
    """Get agent by ID."""
    return {"id": agent_id}
```

### Add Django Model

1. Edit `admin/{app}/models.py`
2. Run `python manage.py makemigrations`
3. Run `python manage.py migrate`

### Add Frontend View

1. Create `webui/src/views/{name}.ts`
2. Use Lit 3.x component syntax
3. Register route in app router

---

## Authentication Flow

```
User → Login Page → Django API → Keycloak → SpiceDB → Redis → PostgreSQL
```

### JWT Token Structure

```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "tenant_id": "tenant-uuid",
  "realm_access": {
    "roles": ["saas_admin", "tenant_admin"]
  }
}
```

### User Roles (Priority Order)

1. `saas_admin` → `/platform`
2. `tenant_sysadmin` → `/admin`
3. `tenant_admin` → `/admin`
4. `agent_owner` → `/chat`
5. `developer` → `/chat` (DEV mode)
6. `trainer` → `/chat` (TRN mode)
7. `user` → `/chat`
8. `viewer` → `/chat` (read-only)

---

## Testing Requirements

**CRITICAL: No Mocks!**

```bash
# Start test infrastructure
docker compose --profile core up -d

# Run tests
pytest

# Run specific test
pytest tests/test_auth.py -v
```

---

## Related Documentation

- [Implementation Plan](./docs/sphinx/index.rst)
- [Deployment Guide](./docs/deployment/DEPLOYMENT.md)
- [Software Modes](./docs/deployment/SOFTWARE_DEPLOYMENT_MODES.md)

---

**Version**: 1.0.0 | **Last Updated**: 2026-01-04
