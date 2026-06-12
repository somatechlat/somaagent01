# SomaAgent01 - Enterprise Multi-Agent Cognitive Platform

## Document Control

| Field | Value |
|-------|-------|
| Document Title | SomaAgent01 Project Overview and Deployment Guide |
| Document Identifier | SOMA-DOC-001 |
| Version | 1.1.0 |
| Date | 2026-06-01 |
| Status | Pre-Production |
| Author | SomaTech Engineering |
| Classification | Internal |

## Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2025-12-30 | SomaTech Engineering | Initial release |
| 1.1.0 | 2026-06-01 | SomaTech Engineering | Updated to reflect pre-production status; corrected deployment instructions; removed inaccurate production readiness claims |

---

## 1. Purpose and Scope

### 1.1 Purpose

This document provides an overview of the SomaAgent01 enterprise multi-agent cognitive platform, including architecture, deployment procedures, and operational guidelines.

### 1.2 Scope

This document covers:
- System architecture and technology stack
- Deployment modes (Standalone and AAAS)
- Quick start procedures for development and testing
- Security considerations and known issues
- Project structure and component inventory

This document does not cover:
- Detailed API specifications (see individual SRS documents)
- Frontend component-level documentation
- Operational runbooks and incident response procedures

### 1.3 Intended Audience

- Software engineers
- DevOps and platform operators
- Quality assurance personnel
- Technical project managers

---

## 2. Normative References

The following documents are referenced in this specification:

| Document | Identifier | Location |
|----------|------------|----------|
| SomaAgent01 Comprehensive Audit Report | SOMA-AUDIT-001 | `SOMA_AGENT01_COMPREHENSIVE_AUDIT_REPORT.md` |
| VIBE Coding Rules | SOMA-STD-001 | `docs/development/VIBE_CODING_RULES.md` |
| Software Deployment Modes | SOMA-DEP-001 | `docs/deployment/SOFTWARE_DEPLOYMENT_MODES.md` |
| Deployment Guide | SOMA-DEP-002 | `docs/deployment/DEPLOYMENT.md` |
| Component Inventory | SOMA-DES-001 | `docs/design/INVENTORY.md` |
| Software Requirements Specifications | Various | `docs/srs/` |

---

## 3. Terms and Definitions

| Term | Definition |
|------|------------|
| AAAS | Agent-As-A-Service: deployment mode where Agent, Brain, and Memory run as an integrated stack |
| Standalone | Deployment mode where only the Agent service runs, without Brain or Memory dependencies |
| SomaBrain | Cognitive runtime service for agent neuromodulation and reasoning |
| SomaFractalMemory | Vector memory storage service with fractal coordinate indexing |
| VIBE | Verification, Integration, Build, and Enforcement: internal coding standard |
| OPA | Open Policy Agent: policy engine for authorization decisions |
| SpiceDB | Zanzibar-style authorization database |
| SSO | Single Sign-On |
| OIDC | OpenID Connect |

---

## 4. System Overview

### 4.1 Status Declaration

**The SomaAgent01 system is classified as PRE-PRODUCTION.**

System maturity score: 5.1 out of 10.

This system shall not be deployed to production workloads without addressing critical gaps documented in SOMA-AUDIT-001.

### 4.2 System Description

SomaAgent01 is an enterprise-grade multi-agent cognitive platform built on Django 5.1 and Django Ninja. The platform provides:

- Multi-tenant architecture with data isolation
- Keycloak-based OIDC authentication
- SpiceDB schema for fine-grained authorization (`UnifiedGate` makes real gRPC calls; some RBAC API endpoints still stubbed)
- Real-time chat via WebSocket
- Integration hooks for SomaBrain cognitive runtime and SomaFractalMemory storage
- Event-driven architecture using Kafka and Redis
- Observability stack using Prometheus, Grafana, and OpenTelemetry

### 4.3 Technology Stack

| Layer | Technology | Constraint |
|-------|------------|------------|
| API Framework | Django 5.1 + Django Ninja 1.3 | FastAPI prohibited |
| ORM | Django ORM | SQLAlchemy prohibited |
| Frontend | Lit 3.x Web Components | React and Alpine.js prohibited |
| Database | PostgreSQL 16 | SQLite prohibited in production |
| Cache | Redis 7 | |
| Message Broker | Kafka 3.7 (KRaft mode) | Optional in Standalone |
| Vector Database | Milvus 2.3 | Qdrant prohibited |
| Identity | Keycloak 24 | |
| Authorization | SpiceDB 1.29 | Schema defined; `UnifiedGate` makes real gRPC calls; some RBAC API endpoints remain stubbed |
| Policy Engine | OPA | Policy files exist; `UnifiedGate` and `PolicyClient` make real HTTP calls to OPA |
| Observability | Prometheus + Grafana + OpenTelemetry | Partially wired |
| Memory System | SomaFractalMemory + SomaBrain | Requires sibling repositories in AAAS mode |

---

## 5. Architecture

### 5.1 High-Level Architecture

The system comprises three primary layers:

1. **Presentation Layer**: Lit 3.x Web Components frontend (`webui/`)
2. **Application Layer**: 55 Django apps (`admin/`) and service implementations (`services/`)
3. **Infrastructure Layer**: PostgreSQL, Redis, Kafka, Milvus, Keycloak, Vault

### 5.2 Service Components

| Component | Path | Function |
|-----------|------|----------|
| API Gateway | `services/gateway/` | ASGI entrypoint, Django settings, URL routing, WebSocket consumers |
| Conversation Worker | `services/conversation_worker/` | Kafka consumer for inbound conversation events |
| Tool Executor | `services/tool_executor/` | Tool execution engine with sandbox management |
| Delegation Gateway | `services/delegation_gateway/` | A2A protocol handling |
| Memory Replicator | `services/memory_replicator/` | Memory synchronization |
| Multimodal Service | `services/multimodal/` | Multi-modal processing |
| Common Services | `services/common/` | 40+ shared modules including event bus, circuit breaker, rate limiter |

### 5.3 Deployment Modes

#### 5.3.1 Standalone Mode

- Agent service only
- No SomaBrain or SomaFractalMemory dependencies
- Uses port namespace 20xxx
- Suitable for development and agent-only deployments

#### 5.3.2 AAAS Mode

- Integrated stack: Agent + SomaBrain + SomaFractalMemory
- Uses port namespace 63xxx
- Requires sibling repositories (`../somabrain`, `../somafractalmemory`)
- Suitable for full cognitive platform deployments

### 5.4 Port Namespaces

**Standalone Namespace (20xxx)**

| Service | Port |
|---------|------|
| SomaAgent API | 20020 |
| PostgreSQL | 20432 |
| Redis | 20379 |
| Keycloak | 20880 |
| Vault | 20882 |

**AAAS Namespace (63xxx)**

| Service | Port |
|---------|------|
| SomaAgent API | 63900 |
| PostgreSQL | 63932 |
| Redis | 63979 |
| Keycloak | 63980 |
| SomaBrain | 63996 |
| SomaFractalMemory | 63901 |

---

## 6. Deployment Procedures

### 6.1 Prerequisites

- Python 3.12 or higher
- Docker Engine 24.0 or higher
- Docker Compose 2.20 or higher
- Minimum 4 GB RAM
- Minimum 2 CPU cores

### 6.2 Standalone Deployment

#### 6.2.1 Environment Preparation

```bash
git clone https://github.com/somatechlat/somaagent01.git
cd somaagent01

# Install Python dependencies
poetry install
# OR
pip install -r requirements.txt

# Prepare environment file
cp infra/standalone/.env.example infra/standalone/.env
```

Edit `infra/standalone/.env` and set the following required values:
- `POSTGRES_PASSWORD`
- `KEYCLOAK_ADMIN_PASSWORD`
- `VAULT_DEV_ROOT_TOKEN_ID`

#### 6.2.2 Stack Initialization

```bash
cd infra/standalone
docker compose up -d
```

Wait approximately 60 seconds for all services to report healthy status:

```bash
docker compose ps
```

Verify the Agent API health endpoint:

```bash
curl http://localhost:20020/api/health/
```

#### 6.2.3 Database Migration

Execute migrations inside the running container:

```bash
docker compose exec somaagent_standalone python manage.py migrate
```

Create an administrative user:

```bash
docker compose exec somaagent_standalone python manage.py createsuperuser
```

### 6.3 AAAS Deployment

**Warning**: AAAS deployment requires the SomaBrain and SomaFractalMemory repositories as sibling directories. These repositories are not included in this distribution.

```bash
# From a parent directory containing somaAgent01/, somabrain/, and somafractalmemory/
cd somaAgent01/infra/aaas/aaas
./build_saas.sh
```

### 6.4 Development Mode (Non-Docker)

For local development with hot reload:

```bash
# Ensure PostgreSQL, Redis, and Keycloak are running
cp .env.example .env
# Edit .env with local configuration

make dev
```

Equivalent manual command:

```bash
DJANGO_SETTINGS_MODULE=services.gateway.settings \
  python -m uvicorn services.gateway.main:django_asgi \
  --reload --host 0.0.0.0 --port 8010
```

---

## 7. Security

### 7.1 Security Architecture

- **Authentication**: Keycloak OIDC with JWT token validation
- **Authorization**: SpiceDB schema defined for Zanzibar-style permissions
- **Session Management**: Redis-backed sessions with 15-minute TTL
- **Secret Management**: HashiCorp Vault integration
- **Data Isolation**: Multi-tenant separation via Django ORM query filtering

### 7.2 Known Security Issues

The following historical issues were documented in SOMA-AUDIT-001 and have since been fixed in code:

1. ~~`ALLOW_INSECURE_AUTH_BYPASS` flag existed in `services/gateway/settings.py`~~ — **Removed**
2. ~~Rate limiter fails open on Redis connection errors~~ — **Now fail-closed**
3. ~~OPA/SpiceDB runtime checks inspect JSON blobs rather than calling policy engines~~ — **`UnifiedGate` now makes real OPA/SpiceDB calls**
4. ~~`DEV_MODE = true` is hardcoded in `webui/src/main.ts`~~ — **`DEV_MODE = false`**
5. ~~Account lockout mechanism not implemented~~ — **Implemented via Redis (5 attempts / 15 min)**
6. ~~PKCE for OAuth not implemented~~ — **Implemented in `admin/auth/api_oauth.py`**

Remaining issues before production deployment include: uncommitted Django migrations, OPA/SpiceDB policy/schema loading in deployment manifests, incomplete K8s manifests, and the frontend chat flow blockers documented in the latest plan.

---

## 8. Testing

### 8.1 Test Infrastructure

Tests require real infrastructure. Mocks are prohibited by VIBE standard SOMA-STD-001.

### 8.2 Test Execution

```bash
# Unit tests (no external infrastructure required)
pytest tests/unit/ -v

# Integration tests (requires PostgreSQL, Redis)
pytest tests/integration/ -v

# SaaS tests (requires full stack; tests skip if infrastructure unavailable)
pytest tests/saas/ -v

# Django tests
pytest tests/django/ -v

# Full test suite
make test
```

### 8.3 Test Coverage

- Test files: 24
- Source files: ~570
- Ratio: approximately 4.2%
- Target for new features: 80%

---

## 9. Project Structure

```
somaagent01/
├── admin/                    # 55 Django applications
│   ├── api.py               # Master Django Ninja API router
│   ├── auth/                # Authentication and authorization
│   ├── core/               # Core models and business logic
│   ├── aaas/               # Multi-tenant features
│   ├── chat/               # Chat API endpoints
│   └── [50+ additional apps]
├── services/                 # Service layer implementations
│   ├── gateway/             # ASGI entrypoint and Django configuration
│   ├── common/              # Shared service modules
│   ├── conversation_worker/ # Conversation event processing
│   ├── tool_executor/       # Tool execution engine
│   ├── delegation_gateway/  # A2A delegation
│   ├── memory_replicator/   # Memory synchronization
│   └── multimodal/          # Multi-modal processing
├── webui/                   # Lit 3.x Web Components frontend
│   └── src/
│       ├── views/           # Page-level components
│       ├── components/      # Reusable components
│       └── stores/          # State management
├── schemas/                 # JSON schemas and SpiceDB Zed schema
├── policy/                  # OPA Rego policy files
├── infra/                   # Infrastructure configurations
│   ├── standalone/          # Standalone deployment
│   ├── aaas/                # AAAS deployment
│   └── k8s/                 # Kubernetes manifests
├── tests/                   # Test suite
├── docs/                    # Documentation
├── scripts/                 # Automation scripts
├── config/                  # Centralized configuration
└── core/                    # Cross-service data models
```

---

## 10. Known Limitations and Gaps

| ID | Limitation | Impact | Status |
|----|------------|--------|--------|
| LIM-001 | Chat orchestrator V3 pipeline exists but is bypassed in production | Medium | **Fixed — V3 is the WebSocket/REST production path** |
| LIM-002 | BrainBridge.recall() raises NotImplementedError in some paths | Medium | **Fixed — implemented for direct and HTTP modes** |
| LIM-003 | SpiceDB API endpoints are stubs | High | Partial — `UnifiedGate` uses real SpiceDB; some RBAC endpoints still stubbed |
| LIM-004 | OPA runtime checks use JSON blobs, not policy engine calls | High | **Fixed — `UnifiedGate`/`PolicyClient` make real OPA calls** |
| LIM-005 | Audit outbox publisher not wired to all endpoints | Medium | Open |
| LIM-006 | 1,402 Pyright type errors | Low | Open |
| LIM-007 | Makefile references missing Dockerfiles (gateway, worker, analyzer) | Medium | Open |
| LIM-008 | No root-level docker-compose.yml | Low | **Fixed — `docker-compose.yml` exists at project root** |
| LIM-009 | pyproject.toml references somabrain as local path dependency | High | Open |
| LIM-010 | WebUI not containerized | Medium | **Fixed — `webui/Dockerfile` exists** |
| LIM-011 | Frontend WebSocket URL omits required `agent_id` | High | Open |
| LIM-012 | Frontend chat view lacks agent selector | High | Open |

---

## 11. Support and References

- Primary documentation: `docs/` directory
- Audit report: `SOMA_AGENT01_COMPREHENSIVE_AUDIT_REPORT.md`
- Issue tracking: [GitHub Issues](https://github.com/somatechlat/somaagent01/issues)

---

## 12. License

This project is proprietary software licensed by SomaTech LAT.
See LICENSE file for details.

---

End of Document
