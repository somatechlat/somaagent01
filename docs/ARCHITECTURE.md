# SomaAgent01 Architecture

> **SOMA Stack Agent Core** — Django Ninja API for AI agent orchestration, SaaS multi-tenancy, and user interface.

## Overview

SomaAgent01 is the agent orchestration layer of the SOMA Stack. It provides:

- **Agent Orchestration** — AI agent lifecycle, capsule management
- **SaaS Platform** — Multi-tenant subscription management, API keys
- **User Interface** — Web UI for agent interaction
- **Gateway Service** — External API routing

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      SOMAAGENT01                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Django Ninja│  │  SaaS Module │  │  Gateway Service    │  │
│  │  API         │  │  (Tenants)   │  │  (Routing)          │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                 │                      │              │
│  ┌──────▼─────────────────▼──────────────────────▼───────────┐  │
│  │                    ADMIN CORE                             │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │  │
│  │  │Helpers      │ │Settings     │ │Infrastructure       │  │  │
│  │  │(settings.py)│ │(defaults)   │ │(API)                │  │  │
│  │  └─────────────┘ └─────────────┘ └─────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                  │
│  ┌───────────────────────────▼───────────────────────────────┐  │
│  │                    SERVICES                               │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │  │
│  │  │Agent        │ │Capsule      │ │Brain Bridge         │  │  │
│  │  │Service      │ │Manager      │ │(In-Process)         │  │  │
│  │  └─────────────┘ └─────────────┘ └─────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  PostgreSQL   │    │    Redis      │    │   SomaBrain   │
│  (Django ORM) │    │   (Sessions)  │    │  (In-Process) │
└───────────────┘    └───────────────┘    └───────────────┘
```

## Deployment Model

**SaaS Only** — Deployed as part of the unified `somastack_saas` container.

```yaml
# docker-compose.yml
somastack_saas:
  ports:
    - "20020:20020"  # Gateway API
    - "20042:20042"  # Admin API
```

### Port Namespace (SomaAgent01)

| Port | Service | Description |
|------|----------|-------------|
| 20020 | Gateway | Main entry point, WebSocket traffic |
| 20042 | Admin | Django Ninja admin APIs |
| 20880 | Keycloak | OIDC authentication (external) |
| 20051 | SpiceDB | Zanzibar-style permissions (external) |
| 20181 | OPA | Open Policy Agent (external) |
| 5432 | PostgreSQL | Primary database |
| 6379 | Redis | Cache, sessions |

## Technology Stack

**100% Django Compliant - NO FastAPI, NO SQLAlchemy (VIBE Rule 105: Tech Stack Purity)**

| Component | Technology | Version |
|-----------|------------|----------|
| **Web Framework** | Django | 5.0+ |
| **API Framework** | Django Ninja | 1.3+ |
| **ORM** | Django ORM | Built-in (Django) |
| **Settings** | Pydantic + django-environ | Latest |
| **Database** | PostgreSQL | 16+ |
| **Cache/Sessions** | Redis | 7+ |
| **Authentication** | Keycloak (OIDC) | Latest |
| **Authorization** | SpiceDB (Zanzibar) | Latest |
| **Message Broker** | Kafka | 3.7+ |
| **Task Queue** | Temporal | Latest |
| **Frontend Build** | Bun | Latest |
| **Frontend Components** | Lit Web Components | 3.x (VIBE Rule 95) |

## Directory Structure

```
somaAgent01/
├── admin/
│   ├── core/
│   │   ├── helpers/
│   │   │   ├── settings.py       # Settings facade
│   │   │   ├── settings_defaults.py
│   │   │   └── settings_model.py
│   │   └── infrastructure/
│   │       └── settings_api.py   # Settings API
│   ├── saas/
│   │   ├── api/
│   │   │   └── settings.py       # SaaS settings API
│   │   ├── models/               # Tenant models
│   │   └── services/             # SaaS services
│   └── migrations/               # 13 Django migrations
├── services/
│   └── gateway/
│       └── settings.py           # Gateway configuration
├── infra/
│   └── saas/
│       ├── docker-compose.yml    # SaaS deployment
│       ├── .env.example          # Environment template
│       ├── init-db.sh            # Database initialization
│       └── supervisord.conf      # Process supervisor
└── package.json                  # Bun dependencies
```

## API Endpoints

**All APIs use Django Ninja with Pydantic schemas - NO FastAPI, NO SQLAlchemy**

### SaaS Admin (`admin/saas/api/`)

| Module | Endpoints | File |
|--------|-----------|-------|
| **Dashboard** | `GET /api/v2/saas/dashboard` | `dashboard.py` |
| **Tenants** | `GET/POST/PUT/DELETE /api/v2/saas/tenants` | `tenants.py` |
| **Tenant Agents** | `GET /api/v2/saas/tenant-agents` | `tenant_agents.py` |
| **Users** | `GET/POST/PUT/DELETE /api/v2/saas/users` | `users.py` |
| **User Invite** | `POST/DELETE /api/v2/saas/users/{id}/invite` | `users.py` |
| **User Password** | `POST /api/v2/saas/users/{id}/reset-password` | `users.py` |
| **User Impersonate** | `PUT /api/v2/saas/users/{id}/impersonate` | `users.py` |
| **Tiers** | `GET/POST/PATCH/DELETE /api/v2/saas/tiers` | `tiers.py` |
| **Features** | `GET/POST /api/v2/saas/features` | `features.py` |
| **Settings** | `GET/PUT /api/v2/saas/settings` | `settings.py` |
| **API Keys** | `GET/POST/DELETE /api/v2/saas/settings/api-keys` | `settings.py` |
| **SSO** | `GET/PUT/POST /api/v2/saas/settings/sso` | `settings.py` |
| **Integrations** | `GET/PUT /api/v2/saas/integrations` | `integrations.py` |
| **Billing** | `GET /api/v2/saas/billing` | `billing.py` |
| **Invoices** | `GET /api/v2/saas/billing/invoices` | `billing.py` |
| **Audit** | `GET /api/v2/saas/audit` | `audit.py` |

**Authentication:** Bearer token (ApiKey) + OIDC (Keycloak)

### Core API (`admin/core/api/`)

| Module | Endpoints | File |
|--------|-----------|-------|
| **Health** | `GET /api/v2/core/health`, `/health/quick`, `/health/ready` | `health.py` |
| **Ping** | `GET /api/v2/core/ping` | `general.py` |
| **Settings** | `GET/PUT /api/v2/api/settings/*` | `ui_settings.py` |
| **Sessions** | `GET/POST /api/v2/api/sessions/*` | `sessions.py` |
| **Memory** | `GET/POST /api/v2/api/memory/*` | `memory.py` |
| **Kafka** | `GET/POST /api/v2/api/kafka/*` | `kafka.py` |

### Gateway API (`admin/gateway/api/`)

| Module | Endpoints | File |
|--------|-----------|-------|
| **A2A** | `POST /api/v2/gateway/a2a/execute` | `gateway.py` |
| **A2A Terminate** | `POST /api/v2/gateway/a2a/terminate/{id}` | `gateway.py` |
| **Workflow Describe** | `GET /api/v2/gateway/describe/{id}` | `gateway.py` |

### Authentication

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/login` | User login |
| POST | `/auth/oauth/callback` | OAuth callback |
| GET | `/auth/session` | Get session |

## Configuration

**All configuration uses Django settings pattern with environment variables. NO FastAPI or SQLAlchemy.**

### Database Configuration

```bash
# PostgreSQL (Django settings DATABASES)
SA01_DB_DSN=postgresql://soma:soma@postgres:5432/somaagent
DATABASE_URL=postgresql://soma:soma@postgres:5432/somaagent
```

### Redis Configuration

```bash
SA01_REDIS_URL=redis://redis:6379/0
REDIS_URL=redis://redis:6379/0
```

### Keycloak (Authentication - Port 20880)

```bash
KEYCLOAK_URL=http://keycloak:20880
KEYCLOAK_REALM=somastack
KEYCLOAK_CLIENT_ID=soma-agent
```

### SpiceDB (Authorization - Port 20051)

```bash
SPICEDB_URL=http://spicedb:20051
SPICEDB_API_KEY=spicedb-secret-key
```

### OPA (Policy Engine - Port 20181)

```bash
OPA_URL=http://opa:20181
```

### SaaS Mode Configuration

```bash
# Deployment Modes
SA01_DEPLOYMENT_MODE=DEV
SOMASTACK_SOFTWARE_MODE=SomaStackClusterMode
SOMA_SAAS_MODE=true
SA01_DEPLOYMENT_TARGET=LOCAL
```

### Core Django Settings

```bash
DJANGO_SECRET_KEY=your-secret-key
DEBUG=false
ALLOWED_HOSTS=localhost,api.somastack.io
```

### Model Provider Configuration

```bash
# These are defaults - can be overridden per-tenant in GlobalDefault
# Code default: "openrouter" (settings_model.py:23)
# Platform default: "openai" (profiles.py:79)
SAAS_DEFAULT_CHAT_MODEL=openai/gpt-4.1
SA01_CHAT_PROVIDER=openai
```

### Cross-Service Integration (SomaStackClusterMode)

```bash
SOMABRAIN_API_URL=http://somabrain:30101
SOMAMEMORY_API_URL=http://somafractalmemory:10101
SOMA_MEMORY_API_TOKENyour-memory-token
MILVUS_HOST=milvus
MILVUS_PORT=19530
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
```

### Environment Variable Priority

Configuration follows this precedence:

```
1. Environment Variables (highest priority) - for dev/ops control
2. Django Settings (settings.py) - defaults per environment
3. Code Defaults (models) - ultimate fallback
```

## SaaS Multi-Tenancy

### Tenant Model

```python
class Tenant(models.Model):
    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    subscription_tier = models.CharField()
    api_key_hash = models.CharField()
    created_at = models.DateTimeField(auto_now_add=True)
```

### API Key Authentication

```python
# Bearer token in header
Authorization: Bearer <api_key>
```

## Integration

### With SomaBrain
- In-process bridge via `ENABLE_IN_PROCESS_BRIDGE=true`
- Direct Python imports in SaaS mode
- Shared PostgreSQL database

### With SomaFractalMemory
- In-process bridge in SaaS mode
- HTTP fallback for external deployment

## Frontend (Bun + Lit)

Per **VIBE Rule 95** (Zero npm Policy):

```bash
# Install dependencies
bun install

# Development
bun run dev

# Build
bun run build
```

## Infrastructure

### Docker Compose (SaaS)

```bash
cd infra/saas
docker-compose up -d
```

### Port Mapping (639xx Range)

| Service | Port |
|---------|------|
| Agent API | 63900 |
| Brain API | 63996 |
| Memory API | 63901 |
| PostgreSQL | 63932 |
| Redis | 63979 |
| Kafka | 63992 |
| Milvus | 63953 |
| MinIO | 63902 |

## VIBE Compliance

- **Rule 82**: Modularity — Proper package structure
- **Rule 84**: No Stubs — Full implementations only
- **Rule 86**: Purity — Django Ninja only
- **Rule 95**: Bun Mandate — Zero npm
- **Rule 103**: Real Infrastructure — Docker Compose for tests

## Development

```bash
# Run locally with Django
cd admin
python manage.py runserver 0.0.0.0:9000

# Run via Docker (SaaS mode)
cd infra/saas
docker-compose up -d
```

## License

Proprietary — SomaTech.lat
