# SomaAgent01 Architecture Onboarding Document

**Version:** 2.0.0  
**Date:** 2025-12-22  
**Purpose:** Cross-project synchronization and agent onboarding

---

## 🎯 VIBE CODING RULES (MANDATORY)

Every agent working on SomaStack projects MUST follow these rules:

1. **No Mocks, No Stubs** - Real implementations only
2. **Production-Grade Code** - Every line must be deployable
3. **7 Personas** - Think as: PhD Dev, Analyst, QA, Documenter, Security Auditor, Performance Engineer, UX Consultant
4. **Test on Real Infra** - Except unit tests, all tests run against real services
5. **Fail Fast** - No silent fallbacks, explicit errors with context

---

## 🏗️ STACK ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│                      EYE OF GOD UI (Port 8020)                  │
│                   Django Ninja + Lit Web Components             │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                     API GATEWAY / AUTH                          │
│              Keycloak SSO (20880) + JWT Bearer                  │
└─────────────────────────────────────────────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│  SomaAgent01  │       │   SomaBrain   │       │ SomaFractalMem│
│  FastAPI 8010 │       │  Memory API   │       │  Memory Graph │
└───────────────┘       └───────────────┘       └───────────────┘
        │                        │                        │
        └────────────────────────┼────────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE LAYER                         │
│ PostgreSQL | Redis | Kafka | Milvus | MinIO | SpiceDB | OPA     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🐳 DOCKER INFRASTRUCTURE

All services use **unique 20xxx port namespace** to avoid conflicts.

### Core Profile (`--profile core`)
| Service | Port | Memory | Purpose |
|---------|------|--------|---------|
| PostgreSQL | 20432 | 1G | Primary database (5 DBs) |
| Redis | 20379 | 512M | Cache + sessions |
| Kafka | 20092 | 1G | Event streaming |

### Vectors Profile (`--profile vectors`)
| Service | Port | Memory | Purpose |
|---------|------|--------|---------|
| etcd | internal | 512M | Milvus metadata |
| MinIO | 20900/01 | 512M | S3-compatible storage |
| Milvus | 20530 | 2G | Vector database |

### Auth Profile (`--profile auth`)
| Service | Port | Memory | Purpose |
|---------|------|--------|---------|
| Keycloak | 20880 | 768M | SSO / OIDC / SAML |

### Security Profile (`--profile security`)
| Service | Port | Memory | Purpose |
|---------|------|--------|---------|
| SpiceDB | 20051 | 256M | Fine-grained authz |
| OPA | 20181 | 256M | Policy engine |

### Observability Profile (`--profile observability`)
| Service | Port | Memory | Purpose |
|---------|------|--------|---------|
| Prometheus | 20090 | 512M | Metrics collection |
| Grafana | 20300 | 256M | Dashboards |

### Startup Command
```bash
# Start all core services
docker compose --profile core --profile vectors --profile auth up -d

# Check health
docker ps --format "table {{.Names}}\t{{.Status}}" | grep somaagent
```

---

## 📁 PROJECT STRUCTURE

```
somaAgent01/
├── ui/
│   ├── frontend/src/
│   │   ├── components/     # 12 Lit web components
│   │   ├── views/          # 10 page views
│   │   ├── stores/         # 5 Lit context stores
│   │   └── services/       # 6 API/WebSocket services
│   └── backend/
│       ├── api/
│       │   ├── endpoints/  # 9 Django Ninja routers (47 routes)
│       │   ├── schemas/    # Pydantic models
│       │   └── router.py   # Main API configuration
│       ├── core/models/    # 6 Django ORM models
│       ├── realtime/       # WebSocket consumers
│       └── services/       # Backend service clients
├── infrastructure/
│   ├── postgres/init/      # Database initialization
│   ├── prometheus/         # Prometheus config
│   └── grafana/            # Grafana provisioning
└── docker-compose.yml      # Production-grade config
```

---

## 🔌 API ENDPOINTS

### Base URL: `/api/v2/`

| Prefix | Routes | Description |
|--------|--------|-------------|
| `/auth` | 5 | JWT token, refresh, me, logout, register |
| `/settings` | 4 | CRUD + optimistic locking |
| `/themes` | 7 | CRUD + approve + XSS validation |
| `/modes` | 3 | Agent mode switching |
| `/memory` | 6 | CRUD + semantic search |
| `/cognitive` | 8 | LLM params + prompt templates |
| `/tools` | 6 | 9 built-in tools + invoke |
| `/admin` | 8 | Metrics + users + feature flags |

### WebSocket Endpoints: `/ws/v2/`
| Path | Purpose |
|------|---------|
| `/events` | Tenant-wide real-time events |
| `/chat` | Streaming chat with LLM |
| `/voice` | Voice input/output |

---

## 🔐 AUTHENTICATION FLOW

```
1. User → /login → eog-login.ts
2. Click "Keycloak SSO" → redirect to Keycloak (20880)
3. Keycloak authenticates → redirects to /auth/callback
4. eog-auth-callback.ts exchanges code for tokens
5. Store access_token in localStorage
6. All API calls include: Authorization: Bearer <token>
7. WebSocket includes: ?token=<token> in query string
```

---

## 💾 DATABASES

PostgreSQL hosts 5 databases:

| Database | Purpose |
|----------|---------|
| `somaagent` | Core agent data, events, receipts |
| `somabrain` | Memory storage with embeddings |
| `somamemory` | Fractal memory graph |
| `keycloak` | SSO user/realm data |
| `postgres` | System database |

---

## 🔄 CROSS-PROJECT SYNC REQUIREMENTS

When modifying any SomaStack project, ensure:

### 1. Port Consistency
```
SomaAgent01:  20xxx ports
SomaBrain:    30xxx ports (TBD)
VoiceBox:     40xxx ports (TBD)
```

### 2. Shared Infrastructure
All projects connect to the SAME Docker network: `somaagent-network`

### 3. Environment Variables
Copy from `.env.example`:
```bash
POSTGRES_USER=postgres
POSTGRES_PASSWORD=somastack2024
REDIS_PASSWORD=somastack2024
JWT_SECRET=<shared-secret>
KEYCLOAK_HOSTNAME=localhost
```

### 4. API Contracts
- Version prefix: `/api/v2/`
- Auth: Bearer JWT tokens
- Errors: `{detail, code, path}` format

### 5. Event Schema
Kafka topics follow: `somaagent.<domain>.<event>`
Example: `somaagent.memory.created`

---

## 🚀 DEVELOPMENT WORKFLOW

```bash
# 1. Clone and setup
git clone <repo>
cd somaAgent01
cp .env.example .env

# 2. Start infrastructure
docker compose --profile core --profile vectors --profile auth up -d

# 3. Wait for healthy
docker ps | grep healthy

# 4. Install frontend
cd ui/frontend && npm install

# 5. Install backend
cd ui/backend && pip install -r requirements.txt

# 6. Run development servers
# Frontend: npm run dev (port 5173)
# Backend: python manage.py runserver 0.0.0.0:8020
```

---

## ⚠️ MISSING SERVICES (TO BE IMPLEMENTED)

The following application services are NOT YET deployed:

| Service | Purpose | Status |
|---------|---------|--------|
| `somaagent-api` | FastAPI core agent (8010) | Dockerfile exists, not in compose |
| `somaagent-django` | Django Ninja UI API (8020) | In development |
| `kafka-consumer` | Event stream processor | Not implemented |
| `temporal-worker` | Workflow orchestration | In other project |
| `somabrain-api` | Memory service | Separate repo |

These are infrastructure services only. Application services require building Docker images from the codebase.

---

## 📋 ALIGNMENT CHECKLIST

When onboarding to this project, verify:

- [ ] Docker services on 20xxx ports
- [ ] All 7 services healthy
- [ ] PostgreSQL has 5 databases
- [ ] Redis responds to PING (with password)
- [ ] Milvus healthz returns OK
- [ ] Keycloak admin console accessible
- [ ] Environment variables set from .env.example
- [ ] VIBE Coding Rules understood and followed
