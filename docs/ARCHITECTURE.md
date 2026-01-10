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
    - "63900:9000"  # Agent API
```

## Technology Stack

| Component | Technology |
|-----------|------------|
| **API Framework** | Django Ninja |
| **ORM** | Django ORM |
| **Settings** | Pydantic + django-environ |
| **Database** | PostgreSQL 15 |
| **Cache/Sessions** | Redis 7.2 |
| **UI** | Bun + Lit (VIBE Rule 95) |
| **Message Queue** | Kafka 3.7 |

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

### SaaS Admin

| Method | Path | Description |
|--------|------|-------------|
| GET | `/saas/tenants` | List tenants |
| POST | `/saas/tenants` | Create tenant |
| GET | `/saas/subscriptions` | List subscriptions |
| POST | `/saas/api-keys` | Generate API key |

### Agent Management

| Method | Path | Description |
|--------|------|-------------|
| GET | `/agents` | List agents |
| POST | `/agents` | Create agent |
| GET | `/agents/{id}/capsule` | Get agent capsule |
| POST | `/agents/{id}/execute` | Execute agent action |

### Authentication

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/login` | User login |
| POST | `/auth/oauth/callback` | OAuth callback |
| GET | `/auth/session` | Get session |

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://soma:soma@somastack_postgres:5432/somaagent

# Redis
REDIS_URL=redis://somastack_redis:6379/0

# Agent Identity
AGENT_NAME=SomaStack_SaaS_Root
AGENT_ID=00000000-0000-0000-0000-000000000001

# Debug
DJANGO_DEBUG=True
LOG_LEVEL=INFO

# SaaS Mode
SOMA_SAAS_MODE=true
ENABLE_IN_PROCESS_BRIDGE=true
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
