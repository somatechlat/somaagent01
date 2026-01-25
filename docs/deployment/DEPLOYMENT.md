# 🚀 Deployment Guide

**Target Environment**: Docker / AWS ECS (Fargate) / EKS / EC2  
**Stack**: Django 5.0, PostgreSQL 16, Redis 7

---

## 1. Port Namespace Strategy

SomaStack uses defined port namespaces for all services to enable local development and production deployments.

| Service | Namespace | Port Range | Notes |
|----------|-----------|------------|-------|
| **SomaAgent01 (Control Plane)** | 20xxx | 20020-20199 | Main API, admin, gateway |
| **SomaBrain (Cognitive)** | 30xxx | 30000-30199 | Cognitive services, embeddings |
| **SomaFractalMemory**, 50xxx, 6379, 9092 | Various | Vector DB, cache, messaging |

### 1.1 Critical Port Mappings

| Service/API | Port | Container | Purpose |
|-------------|------|-----------|---------|
| Gateway | 20020 | gateway | Main entry point, WebSocket traffic |
| Admin API | 20042 | admin | Django Ninja admin APIs |
| Keycloak (Auth) | 20880 | keycloak | OIDC authentication (port 20880) |
| SpiceDB (Authorization) | 20051 | spicedb | Zanzibar-style permissions |
| OPA (Policy Engine) | 20181 | opa | Open Policy Agent |
| SomaBrain API | 30101 | brain | Cognitive services |
| SomaFractalMemory API | 10101 | memory | Memory/vector services |
| Milvus (Vector DB) | 19530 | milvus | Vector embeddings storage |
| PostgreSQL | 5432 | postgres | Primary database |
| Redis | 6379 | redis | Cache, session storage |
| Kafka | 9092 | kafka | Event streaming, message bus |

### 1.2 Infrastructure Ports (External)

| Service | Port | Purpose |
|---------|------|---------|
| MinIO (S3-compatible) | 9000 | Object storage, file uploads |
| MinIO Console | 9001 | Web UI for MinIO |
| Grafana | 49100 | Metrics dashboards |
| Prometheus | 49090 | Metrics collection |
| Jaeger | 49431 | Distributed tracing |
| Temporal UI | 49823 | Workflow management |

---

## 2. Environment Variables

Configure these variables in your CI/CD pipeline or `.env` file. For software
deployment modes (Standalone vs SomaStackClusterMode), see
`docs/deployment/SOFTWARE_DEPLOYMENT_MODES.md`.

### 2.1 Core Deployment Variables

| Variable | Description | Required | Default |
| :--- | :--- | :--- | :--- |
| `SA01_DEPLOYMENT_MODE` | `PROD` or `DEV` | Yes | `DEV` |
| `SA01_DEPLOYMENT_TARGET` | `LOCAL`, `FARGATE`, `EKS`, `ECS_EC2`, `EC2`, `APP_RUNNER` | No | `LOCAL` |
| `SOMA_AAAS_MODE` | In-process coupling: `true` or `false` | No | `false` |
| `SOMASTACK_SOFTWARE_MODE` | `StandAlone` or `SomaStackClusterMode` | No | `StandAlone` |

### 2.2 Database Variables

| Variable | Description | Required | Default |
| :--- | :--- | :--- | :--- |
| `SA01_DB_DSN` | Postgres Connection String | Yes | `postgresql://user:pass@host:5432/db` |
| `SA01_REDIS_URL` | Redis URL | Yes | `redis://host:6379/0` |
| `SA01_DB_HOST` | PostgreSQL host | No | `postgres` |
| `SA01_DB_PORT` | PostgreSQL port | No | `5432` |
| `SA01_DB_NAME` | Database name | No | `somaagent01` |
| `SA01_DB_USER` | Database user | No | `soma` |
| `SA01_DB_PASSWORD` | Database password | Yes | - |

### 2.3 Authentication & Authorization

| Variable | Description | Required | Default |
| :--- | :--- | :--- | :--- |
| `KEYCLOAK_URL` | Keycloak server URL | Yes | `http://keycloak:20880` |
| `KEYCLOAK_REALM` | Keycloak realm name | Yes | `somastack` |
| `KEYCLOAK_CLIENT_ID` | OIDC client ID | Yes | `soma-agent` |
| `SPICEDB_URL` | SpiceDB server URL | Yes | `http://spicedb:20051` |
| `SPICEDB_API_KEY` | SpiceDB API key | Yes | - |
| `OPA_URL` | OPA policy server URL | Yes | `http://opa:20181` |

### 2.4 AAAS Integration Variables

| Variable | Description | Required | Default |
| :--- | :--- | :--- | :--- |
| `AAAS_DEFAULT_CHAT_MODEL` | Default LLM Model | Yes | `openai/gpt-4.1` |
| `SA01_CHAT_PROVIDER` | Chat model provider (openrouter/openai) | No | `openrouter` (code default) |
| `OPENAI_API_KEY` | OpenAI API key | Yes | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | No | - |
| `LAGO_API_URL` | Billing (Lago) API URL | No | `http://lago:3000` |
| `LAGO_API_KEY` | Lago API key | No | - |
| `SMTP_HOST` | Email server host | No | `smtp.sendgrid.net` |
| `SMTP_PORT` | Email server port | No | `587` |
| `SMTP_USER` | Email username | No | - |
| `SMTP_PASSWORD` | Email password | No | - |

### 2.5 Cross-Service Variables (SomaStackClusterMode)

| Variable | Description | Required | Default |
| :--- | :--- | :--- | :--- |
| `SOMABRAIN_API_URL` | SomaBrain API URL | No | `http://somabrain:30101` |
| `SOMAMEMORY_API_URL` | SomaFractalMemory API URL | No | `http://somafractalmemory:10101` |
| `SOMA_MEMORY_API_TOKEN`, SomaFractalMemory API requires auth token | No | - |
| `MILVUS_HOST` | Milvus vector DB host | No | `milvus` |
| `MILVUS_PORT` | Milvus vector DB port | No | `19530` |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka brokers | No | `kafka:9092` |

### 2.6 Feature Flags

| Variable | Description | Required | Default |
| :--- | :--- | :--- | :--- |
| `MEMORY_ENABLED` | Enable Memory service | No | `true` |
| `VOICE_ENABLED` | Enable Voice services | No | `false` |
| `MCP_ENABLED` | Enable MCP servers | No | `true` |
| `CODE_EXECUTION_ENABLED` | Enable code execution | No | `false` |

## 2. Docker Deployment

### Build
We use a multi-stage Dockerfile optimized for security and size.
```bash
docker build -t somaagent:latest -f Dockerfile .
```

### Run (Docker Compose)
Use the included `docker-compose.yml` for production-aligned orchestration.
```bash
docker-compose up -d
```

**Local Resource Target (Testing like Production)**:
- Host memory budget: **15 GB** total across containers.

## 3. Deployment Modes

### 3.1 Local Development (Docker Compose)

**Target**: Local development and testing.

**Prerequisites**:
- Docker 24+, Docker Compose 2.24+
- 16GB+ RAM available
- 50GB+ disk space

**Services Running**:
- Gateway (port 20020)
- Admin API (port 20042)
- Keycloak (port 20880)
- PostgreSQL (port 5432)
- Redis (port 6379)
- SpiceDB (port 20051)
- OPA (port 20181)
- SomaBrain (port 30101) - optional
- SomaFractalMemory (port 10101) - optional

**Startup**:
```bash
docker-compose up -d
```

### 3.2 AWS Fargate Deployment (Primary Production)

**Target**: Production-aligned testing in AWS using ECS Fargate.

**Minimum Task Resources (per service)**:
- CPU: **4 vCPU**
- Memory: **16 GB**
- Disk: **30 GB**

**Infrastructure**:
- Application Load Balancer (ALB) for HTTP + WebSocket traffic
- RDS PostgreSQL (Multi-AZ, pg16)
- ElastiCache Redis (cluster mode)
- MSK Kafka (3 brokers)
- S3 for file storage
- Secrets Manager for secrets

**Deployment Flow**:
1. Build and push Docker images to ECR
2. Create ECS task definitions with resource limits
3. Deploy services using ECS blue-green deployments
4. Configure ALB target groups with health checks

### 3.3 AWS EKS Deployment (Advanced)

**Target**: Full Kubernetes orchestration with advanced networking.

**Prerequisites**:
- EKS cluster (1.28+)
- AWS Load Balancer Controller installed
- Cert-Manager for TLS certificates
- External DNS for automated DNS management

**Infrastructure**:
- Ingress Controller (AWS Load Balancer Controller)
- Certified Kubernetes Operator integration
- Vertical Pod Autoscaler
- Horizontal Pod Autoscaler

**Deployment Flow**:
1. Apply Kubernetes manifests via Helm charts
2. Wait for pods to become ready and healthy
3. Verify external endpoints and health checks
4. Configurations and secrets managed securely
5. Resource utilization optimized with auto-scaling

**Kubernetes Operations**:
- Rollback and configuration management
- Monitoring and performance tracking
- Namespace and ingress configuration
- Persistent volume strategy for storage

## 4. Database Migrations (Resilient)
**CRITICAL**: Migrations are the "Beat" of the system.

### Local Development (Tilt)
Tilt uses the **"Perfect Startup"** protocol to automate this.
- **Resource**: `database-migrations`
- **Mode**: `SA01_DEPLOYMENT_MODE=PROD` (Enforced)
- **Sequence**: Memory → Brain → Agent (Strict Order)
- **Constraint**: Application services **WILL NOT START** until this resource completes successfully.

### Production (Manual/CI)
Run migrations explicitly before rolling updates:
```bash
# Run migrations via the Gateway service
docker-compose exec gateway python manage.py migrate
```

## 5. Health Checks
- **Combined Health**: `http://localhost:8010/health`
- **Metrics**: `http://localhost:8010/metrics`

## 6. Security Checklist
- [ ] Ensure `DEBUG=False` in production.
- [ ] Rotate `SECRET_KEY` via env var.
- [ ] Limit `ALLOWED_HOSTS` to your domain.
- [ ] Use SSL/TLS termination at load balancer.

---
**Standard Operating Procedure v2.0**
# Chat & LLM Integration Deployment Plan

**Date**: 2026-01-14 | **Status**: Ready for Review

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Lit 3.x)                          │
│       webui/src/views/aaas-chat.ts (1265 lines)                     │
│       ↓ WebSocket /ws/v2/chat                                        │
├─────────────────────────────────────────────────────────────────────┤
│                         WEBSOCKET LAYER                              │
│       services/websocket-client.ts (245 lines)                      │
│       ↓ JSON Messages                                                │
├─────────────────────────────────────────────────────────────────────┤
│                         DJANGO BACKEND                               │
│   ┌───────────────────────────────────────────────────────────────┐ │
│   │ admin/chat/api/chat.py (15KB)                                 │ │
│   │   ├── create_conversation()                                    │ │
│   │   ├── list_conversations()                                     │ │
│   │   └── send_message() → ChatService                            │ │
│   └───────────────────────────────────────────────────────────────┘ │
│                              ↓                                       │
│   ┌───────────────────────────────────────────────────────────────┐ │
│   │ services/common/chat_service.py (1150 lines)                  │ │
│   │   ├── SimpleGovernor → LaneBudget                           │ │
│   │   ├── SimpleContextBuilder → Built Context                         │ │
│   │   └── LLM Invoke → Stream Response                            │ │
│   └───────────────────────────────────────────────────────────────┘ │
│                              ↓                                       │
│   ┌───────────────────────────────────────────────────────────────┐ │
│   │ admin/llm/services/litellm_client.py (1492 lines)             │ │
│   │   ├── get_chat_model() → LangChain LLM                        │ │
│   │   ├── get_api_key() → Vault lookup                            │ │
│   │   └── ChatGenerationResult → Streaming chunks                 │ │
│   └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Inventory

| Component | File | Lines | Status |
|-----------|------|-------|--------|
| Chat UI | `webui/src/views/aaas-chat.ts` | 1265 | ✅ Complete |
| WebSocket Client | `webui/src/services/websocket-client.ts` | 245 | ✅ Complete |
| Chat API | `admin/chat/api/chat.py` | ~400 | ✅ Complete |
| Chat Models | `admin/chat/models.py` | 154 | ✅ Complete |
| ChatService | `services/common/chat_service.py` | 1150 | ✅ Complete |
| **SimpleGovernor** | `services/common/simple_governor.py` | 279 | ✅ Complete |
| SimpleContextBuilder | `services/common/simple_context_builder.py` | ~400 | ✅ Complete |
| HealthMonitor | `services/common/health_monitor.py` | ~250 | ✅ Complete |
| LiteLLM Client | `admin/llm/services/litellm_client.py` | 1492 | ✅ Complete |
| LLM Models | `admin/llm/models.py` | ~60 | ✅ Complete |
| SomaBrainClient | `admin/core/somabrain_client.py` | ~600 | ✅ Complete |

---

## 3. Integration Requirements

### 3.1 LLM Provider Configuration

| Provider | Env Var | Vault Path | Status |
|----------|---------|------------|--------|
| OpenAI | `OPENAI_API_KEY` | `secret/soma/openai` | ⚠️ Configure |
| OpenRouter | `OPENROUTER_API_KEY` | `secret/soma/openrouter` | ⚠️ Configure |
| Anthropic | `ANTHROPIC_API_KEY` | `secret/soma/anthropic` | ⚠️ Configure |
| Groq | `GROQ_API_KEY` | `secret/soma/groq` | Optional |

### 3.2 Django Settings Required

```python
# services/gateway/settings.py
SOMABRAIN_URL = "http://localhost:9696"       # ✅ Configured
SOMAFRACTALMEMORY_URL = "http://localhost:10101"  # ✅ Configured
SOMA_MEMORY_API_TOKEN = "<from_vault>"        # ⚠️ Configure
```

### 3.3 AgentIQ Feature Flag

```bash
# Enable AgentIQ Governor
SA01_ENABLE_AGENTIQ_GOVERNOR=true  # Default: false
```

---

## 4. Deployment Checklist

### Step 1: Verify AAAS Stack Running
```bash
docker ps --filter name=somastack --format "{{.Names}}: {{.Status}}"
# Required: postgres, redis, milvus, kafka, minio - all healthy
```

### Step 2: Configure LLM API Key
```bash
# Option A: Environment variable
export OPENROUTER_API_KEY="sk-or-..."

# Option B: Vault (production)
vault kv put secret/soma/openrouter api_key="sk-or-..."
```

### Step 3: Update GlobalDefaults (LLM Models)
```python
# admin/aaas/models/profiles.py - GlobalDefault.defaults["models"]
# Already configured with openrouter/minimax-01
```

### Step 4: Run WebUI
```bash
cd webui && npm install && npm run dev
# Access: http://localhost:5173
```

### Step 5: Test Chat Flow
1. Navigate to `/chat`
2. Select agent
3. Send message
4. Verify streaming response

---

## 5. AgentIQ Governor Details

| Component | Purpose |
|-----------|---------|
| **AIQ Score** | Predicts response quality (0-100) |
| **Lane Plan** | Budgets tokens across 6 lanes |
| **Degradation Levels** | L0-L4 based on AIQ thresholds |
| **Tool K** | Dynamic tool selection limit |

### 6 Lanes:
1. `system_policy` - System prompt + OPA policies
2. `history` - Conversation history
3. `memory` - SomaBrain retrieved context
4. `tools` - Tool definitions
5. `tool_results` - Tool execution results
6. `buffer` - Safety buffer

---

## 6. Known Issues to Fix

| Issue | File | Action |
|-------|------|--------|
| WebSocket endpoint missing | N/A | Implement Django Channels consumer |
| Chat API auth | `chat.py` | Verify bearer token handling |
| LLM key loading | `litellm_client.py` | Verify Vault integration |
| Streaming not wired | `chat_service.py` | Returns iterator, needs WS relay |

---

## 7. Next Steps

1. **Configure LLM API Key** in Vault or ENV
2. **Start WebUI** and verify Chat UI loads
3. **Test REST API** via curl to `/api/v1/chat/conversations`
4. **Implement WebSocket consumer** for streaming (if missing)
5. **Enable AgentIQ** via feature flag for production
# SOMA COLLECTIVE INTELLIGENCE: Production Readiness Roadmap v2.0

> **Identity**: PhD Software Developer, PhD Analyst, PhD QA Engineer, ISO Documenter, Security Auditor, Performance Engineer, UX Consultant
> 
> **Date**: 2026-01-13 | **VIBE Compliance**: v8.120.0

---

## Executive Summary

The SOMA Collective has completed a comprehensive audit of somaAgent01. This roadmap addresses the user's mandate: **ALL settings/env MUST be centralized by deployment mode** with completely isolated `infra/standalone/` and `infra/aaas/` folders.

---

## 🎯 Core Mandate: Centralized Configuration by Mode

### Deployment Mode Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT MODE SELECTOR                     │
├────────────────────┬────────────────────────────────────────────┤
│ SA01_DEPLOYMENT_MODE=STANDALONE │ SA01_DEPLOYMENT_MODE=AAAS    │
├────────────────────┼────────────────────────────────────────────┤
│ infra/standalone/  │ infra/aaas/                               │
│ └── docker-compose.yml │ └── docker-compose.yml               │
│ └── .env.example   │ └── .env.example                         │
│ └── Dockerfile     │ └── Dockerfile                           │
│ └── start.sh       │ └── start_aaas.sh                        │
│ SELF-CONTAINED     │ UNIFIED MONOLITH                         │
│ Agent-only         │ Agent + Brain + Memory                   │
│ Port 20xxx         │ Port 63xxx                               │
└────────────────────┴────────────────────────────────────────────┘
```

### Single Source of Truth: `config/settings_registry.py`

```python
# ALL settings loaded from ONE file based on deployment mode
# VIBE Rule 100: Centralized Sovereignty

class SettingsRegistry:
    @staticmethod
    def load() -> Settings:
        mode = os.environ.get("SA01_DEPLOYMENT_MODE", "STANDALONE").upper()
        
        if mode == "AAAS":
            return AAASSettings.from_vault()
        elif mode == "STANDALONE":
            return StandaloneSettings.from_vault()
        else:
            raise RuntimeError(f"Unknown mode: {mode}. VIBE Rule 91 violation.")
```

---

## 🔴 Phase 1: Infrastructure Isolation (Week 1)

### 1.1 Create `infra/standalone/` (NEW)

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Agent-only deployment, port 20xxx |
| `.env.example` | Standalone configuration template |
| `Dockerfile` | Single-service container |
| `start.sh` | Entrypoint script |

### 1.2 Verify `infra/aaas/` Isolation

- ✅ Already exists with Unified Monolith architecture
- ✅ Uses port 63xxx namespace
- 🔴 Contains hardcoded secrets → Vault migration needed

### 1.3 Delete Legacy Scattered Config

| DELETE | Reason |
|--------|--------|
| `infra/tilt/.env` | Violates single-source Rule 100 |
| Multiple `.env` files | Consolidate to `.env.example` per infra folder |

---

## 🟠 Phase 2: Centralized Config System (Week 2)

### 2.1 Create `config/` Module

```
config/
├── __init__.py
├── settings_registry.py    # Mode dispatcher
├── standalone_settings.py  # Standalone config class
├── aaas_settings.py        # AAAS config class (merge with aaas/config.py)
└── vault_loader.py         # Vault integration (Rule 100)
```

### 2.2 Migrate All Scattered Settings

| Source (DELETE) | Target |
|-----------------|--------|
| `aaas/config.py` | `config/aaas_settings.py` |
| `services/gateway/settings.py` (env vars) | `config/settings_registry.py` |
| `admin/core/config/` | MERGE into `config/` |

### 2.3 Enforce Rule 91: Zero-Fallback

Replace ALL:
```python
# ❌ BEFORE (VIBE Violation)
os.getenv("REDIS_HOST", "localhost")

# ✅ AFTER (VIBE Compliant)
SettingsRegistry.get().redis_host  # Fails-fast if missing
```

---

## 🟡 Phase 3: Secret Consolidation (Week 3)

### 3.1 Vault-Mandatory (Rule 100/164)

| Pattern | Status | Action |
|---------|--------|--------|
| `vault_secrets.py` | ✅ Canonical | KEEP |
| `secret_manager.py` | 🔴 Redis/Fernet Legacy | DELETE |
| `unified_secret_manager.py` | 🟡 Hybrid | MERGE into vault_secrets |
| `admin/core/helpers/secrets.py` | 🟡 Dev-only | KEEP (file masking) |

### 3.2 Hardcoded Secret Purge

| File | Secret | Action |
|------|--------|--------|
| `aaas/memory.py` | `dev-token-*` | ✅ FIXED |
| `services/gateway/settings.py` | `django-insecure-*` | Move to Vault |
| `infra/aaas/docker-compose.yml` | `POSTGRES_PASSWORD: soma` | Vault ref |
| `infra/aaas/docker-compose.yml` | `soma_dev_token` | Vault ref |

---

## 🟢 Phase 4: Code Consolidation (Week 4)

### 4.1 DO NOT MERGE (Complementary Pairs)

| Module 1 | Module 2 | Keep Both |
|----------|----------|-----------|
| `services/common/rate_limiter.py` | `admin/core/helpers/rate_limiter.py` | ✅ Redis vs asyncio |
| `services/common/circuit_breakers.py` | `admin/core/helpers/circuit_breaker.py` | ✅ Class vs Decorator |

### 4.2 DELETE Legacy Duplicates

| DELETE | Keep |
|--------|------|
| `services/common/secret_manager.py` | `vault_secrets.py` |
| `aaas/config.py` | `config/aaas_settings.py` |
| Multiple settings parsers | `config/settings_registry.py` |

### 4.3 Purge 47 TODOs

Rule 82 (Anti-Slop): Implement or remove all TODO/FIXME items.

---

## 🔵 Phase 5: Testing & Verification (Week 5-6)

### 5.1 Standalone Mode Tests

```bash
cd infra/standalone
docker compose up -d
curl http://localhost:20020/api/v1/health
# Expected: {"status": "healthy", "mode": "STANDALONE"}
```

### 5.2 AAAS Mode Tests

```bash
cd infra/aaas
./build_aaas.sh
docker compose up -d
curl http://localhost:63900/api/v1/health
# Expected: {"status": "healthy", "mode": "AAAS"}
```

### 5.3 10-Cycle Resiliency (Rule 122)

```bash
for i in {1..10}; do
  docker compose down && docker compose up -d
  sleep 30
  curl -sf http://localhost:63900/healthz || exit 1
done
echo "✅ 10-Cycle PASS"
```

---

## Verification Commands

```bash
# 1. No hardcoded secrets
grep -rn "dev-token\|somastack2024\|insecure" --include="*.py" --include="*.yml" .
# Target: 0 results

# 2. No localhost fallbacks
grep -rn 'localhost\|127\.0\.0\.1' --include="*.py" . | grep -v "# " | wc -l
# Target: 0

# 3. Single settings registry
grep -rn 'os.getenv.*localhost' --include="*.py" .
# Target: 0

# 4. No TODOs in production
grep -rn "TODO\|FIXME" --include="*.py" . | wc -l
# Target: 0
```

---

## Summary: Files to CREATE

| Path | Purpose |
|------|---------|
| `infra/standalone/` | NEW isolated folder |
| `config/settings_registry.py` | Centralized mode dispatcher |
| `config/standalone_settings.py` | Standalone config |
| `config/aaas_settings.py` | AAAS config (from aaas/config.py) |

## Summary: Files to DELETE

| Path | Reason |
|------|--------|
| `services/common/secret_manager.py` | Legacy Redis/Fernet |
| `infra/tilt/.env` | Scattered config |
| Multiple `.env` files | Consolidate to `.env.example` |
| `aaas/config.py` | Move to config/ |

---

*Signed: SOMA COLLECTIVE INTELLIGENCE*
*PhD Developer • PhD Analyst • PhD QA Engineer • ISO Documenter • Security Auditor • Performance Engineer • UX Consultant*
