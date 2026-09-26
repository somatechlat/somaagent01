# SOMA AAAS — AGENT AS A SERVICE DEPLOYMENT SPECIFICATION

## Document Control

| Field | Value |
|-------|-------|
| Document Title | Soma AAAS Deployment Specification |
| Document Identifier | SOMA-01-AAAS-001 |
| Version | 1.0.0 |
| Date | 2026-06-15 |
| Status | Active |
| Author | SomaTech Engineering |
| Classification | Internal |

## Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-06-15 | SomaTech Engineering | Initial AAAS deployment specification |

---

## 1. Purpose

This document specifies the **Agent As A Service (AAAS) deployment model** — a single-click deployment of the complete Soma Cognitive Triad as an integrated, production-ready AI agent platform.

AAAS is the mechanism by which a user deploys **SomaAgent01 + SomaBrain + SomaFractalMemory** as a single unit, selecting versions from the compatibility matrix.

---

## 2. Deployment Models Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT MODES                         │
├──────────────────────┬──────────────────────────────────────┤
│     STANDALONE       │              AAAS                    │
│                      │                                      │
│  Single component    │  All three as one unit               │
│  Own infrastructure  │  Shared infrastructure               │
│  No cross-repo deps  │  Version-matched deployment          │
│  Dev/testing use     │  Production cognitive agent          │
│                      │                                      │
│  somaAgent01:20020   │  SomaAgent01:63900                   │
│  somabrain:9696      │  SomaBrain:63996                     │
│  somafractalmemory:10101 │  SomaFractalMemory:63901         │
└──────────────────────┴──────────────────────────────────────┘
```

---

## 3. AAAS Architecture

### 3.1 System Topology (AAAS Mode)

```
┌──────────────────────────────────────────────────────────────────┐
│                         USER / CLIENT                             │
│                   (Web UI, SDK, API, WebSocket)                   │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                      SOMAAGENT01 (Gateway)                        │
│                      Port 63900                                   │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌───────────────────┐  │
│  │ Auth     │ │ Chat API │ │ WebSocket │ │ Agent Management  │  │
│  │ Keycloak │ │ REST     │ │ Streaming │ │ Tenant/Quota      │  │
│  └──────────┘ └──────────┘ └───────────┘ └───────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │              V3 Chat Orchestrator (12-phase)              │    │
│  │  Capsule→IQ→Gate→Health→Context→Model→Tools→LLM→Store    │    │
│  └──────────────────────────────────────────────────────────┘    │
└───────┬───────────────────────────┬──────────────────────────────┘
        │                           │
        ▼                           ▼
┌──────────────────────┐  ┌──────────────────────────┐
│    SOMABRAIN          │  │  SOMAFRACTALMEMORY        │
│    Port 63996         │  │  Port 63901               │
│                      │  │                           │
│  ┌────────────────┐  │  │  ┌─────────────────────┐  │
│  │ Cognitive Loop  │  │  │  │ Vector Store (Milvus)│  │
│  │ Predictors     │  │  │  │ Graph Store (PG)     │  │
│  │ Integrator     │  │  │  │ Search Engine        │  │
│  │ Segmentation   │  │  │  │ Multi-Tenant Isolate │  │
│  └────────────────┘  │  │  └─────────────────────┘  │
│  ┌────────────────┐  │  └──────────┬────────────────┘
│  │ Working Memory  │  │             │
│  │ HRR/SDR Engine │  │             │
│  │ Neuromodulators│  │             │
│  │ Adaptation     │  │             │
│  └────────────────┘  │             │
│  ┌────────────────┐  │             │
│  │ Sleep/Consolid.│──│─────────────┘ (Brain stores to SFM)
│  └────────────────┘  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────┐
│                    SHARED INFRASTRUCTURE                          │
│  ┌──────────┐ ┌──────┐ ┌───────┐ ┌─────────┐ ┌──────┐ ┌──────┐│
│  │PostgreSQL│ │Redis │ │Kafka  │ │Keycloak │ │Vault │ │ OPA  ││
│  │ :63932   │ │:63979│ │:9092  │ │ :63980  │ │:63982│ │:8181 ││
│  └──────────┘ └──────┘ └───────┘ └─────────┘ └──────┘ └──────┘│
│  ┌──────────┐ ┌──────────┐                                      │
│  │ Milvus   │ │ SpiceDB  │                                      │
│  │ :19530   │ │ :50051   │                                      │
│  └──────────┘ └──────────┘                                      │
└──────────────────────────────────────────────────────────────────┘
```

### 3.2 Data Flow: Chat Message (AAAS Mode)

```
1. User sends message via WebSocket (ws://host:63900/ws/v2/chat/{agent_id})
2. ChatConsumer authenticates via Keycloak JWT
3. ChatConsumer loads Capsule, derives AgentIQ, builds ToolRegistry (cached)
4. ChatConsumer calls V3ChatOrchestrator.stream_turn()
5. Phase 1-4: Capsule loaded, IQ derived, UnifiedGate checks OPA+SpiceDB
6. Phase 4.5: SomaBrain context evaluation (confidence, suggested tools)
7. Phase 5: Context built (5-lane: system, history, memory, tools, personality)
   - Memory recall: SomaBrain.primary → SomaFractalMemory.fallback
8. Phase 6: Model selection via LiteLLM (OpenAI, Anthropic, Groq, etc.)
9. Phase 7: Tool discovery from Capsule registry
10. Phase 8: LLM invocation with streaming
11. Phase 9: Tool execution (if requested by LLM)
12. Phase 10: Response formatting
13. Phase 11: Memory storage
    - PostgreSQL trace (always)
    - SomaBrain remember (primary cognitive memory)
    - SomaFractalMemory store (fallback if Brain unavailable)
    - PendingMemory queue (for later sync)
    - Episodic memory (background task)
14. Phase 12: Django signals emitted, metrics recorded
15. Tokens streamed back to user via WebSocket deltas
```

---

## 4. Version Selection

### 4.1 User-Facing Version Selector

When deploying AAAS, the user selects versions from the compatibility matrix:

```
╔══════════════════════════════════════════════════╗
║         SOMA AAAS — DEPLOYMENT WIZARD            ║
╠══════════════════════════════════════════════════╣
║                                                  ║
║  SomaAgent01          [v2.0.0 ▼]                 ║
║  SomaBrain            [v0.2.0 ▼]                 ║
║  SomaFractalMemory    [v0.2.0 ▼]                 ║
║                                                  ║
║  Compatibility: ✓ M-001 (Tested, Current)        ║
║                                                  ║
║  Deployment Name: [my-agent________]             ║
║  Tenant:          [my-company_____]              ║
║  Tier:            [Starter ▼]                    ║
║                                                  ║
║  [ DEPLOY ]                                      ║
╚══════════════════════════════════════════════════╝
```

### 4.2 Compatibility Validation

The deployer validates selected versions against the compatibility matrix:

1. Read `SOMA-COMPAT-001.md` (or `soma-compatibility.json`) from each repo
2. Check that the combination exists in the tested matrix
3. Check that per-component requirements are satisfied
4. If incompatible, show which version to adjust

### 4.3 Version Pinning

After selection, the deployer generates pinned image references:

```yaml
images:
  somaagent: somatech/soma-agent:v2.0.0
  somabrain: somatech/soma-brain:v0.2.0
  somafractalmemory: somatech/soma-memory:v0.2.0
```

---

## 5. Deployment Procedure

### 5.1 Prerequisites

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Docker Engine | 24.0+ | 25.0+ |
| Docker Compose | 2.20+ | 2.24+ |
| RAM | 8 GB | 16 GB |
| CPU | 4 cores | 8 cores |
| Disk | 50 GB SSD | 100 GB NVMe |
| Network | 100 Mbps | 1 Gbps |

### 5.2 Deployment Steps

```
STEP 1: Deployer validates selected versions against SOMA-COMPAT-001
STEP 2: Deployer generates docker-compose.aaas.yml with:
  - Versioned image tags
  - Shared infrastructure (PostgreSQL, Redis, Kafka, Keycloak, Vault, OPA, SpiceDB, Milvus)
  - Network configuration (shared network between all services)
  - Volume mounts for persistence
  - Health checks for all services
STEP 3: Deployer generates environment files:
  - .env.somaagent (DB DSN, Redis URL, Keycloak URL, SomaBrain URL, SFM URL, OPA URL, SpiceDB)
  - .env.somabrain (DB DSN, Redis URL, Kafka URL, SFM endpoint, OPA URL)
  - .env.somafractalmemory (DB DSN, Redis URL, Milvus URL, Vault URL, OPA URL)
  - .env.shared (PostgreSQL creds, Redis creds, Keycloak admin, Vault token)
STEP 4: docker compose -f docker-compose.aaas.yml --env-file .env.shared up -d
STEP 5: Health check loop (wait for all services healthy, timeout 120s):
  - curl http://localhost:63900/api/health/ → {"status": "ok"}
  - curl http://localhost:63996/health → {"status": "healthy"}
  - curl http://localhost:63901/healthz → {"kv_store": true, "vector_store": true}
STEP 6: Run database migrations:
  - docker compose exec somaagent python manage.py migrate
  - docker compose exec somabrain python manage.py migrate
  - docker compose exec somafractalmemory python manage.py migrate
STEP 7: Create admin user:
  - docker compose exec somaagent python manage.py createsuperuser
STEP 8: Report success with URLs:
  - Agent API: http://localhost:63900
  - Web UI: http://localhost:63900/
  - Keycloak: http://localhost:63980
  - Brain API: http://localhost:63996/docs
  - Memory API: http://localhost:63901/docs
```

### 5.3 Teardown

```
docker compose -f docker-compose.aaas.yml down -v
```

---

## 6. Configuration Wiring

### 6.1 Environment Variables (AAAS Mode)

**NOTE**: Container-to-container communication uses Docker service names with **internal** ports (e.g., `somabrain:9696`). External host access uses **AAAS namespace** ports (e.g., `localhost:63996`). The port mapping is: 63996→9696 (SomaBrain), 63901→10101 (SFM), 63900→8010 (Agent).

**SomaAgent01 (Gateway):**
```bash
SA01_DEPLOYMENT_MODE=AAAS
SA01_DB_DSN=postgresql://***REMOVED***@postgres:5432/somaagent
SA01_REDIS_URL=redis://redis:6379/0
SA01_KEYCLOAK_URL=http://keycloak:8080
SA01_SOMA_BASE_URL=http://somabrain:9696
SA01_OPA_URL=http://opa:8181
SPICEDB_HOST=spicedb
SPICEDB_PORT=50051
SPICEDB_TOKEN=<generated>
SECRET_KEY=<generated>
```

**SomaBrain:**
```bash
SOMABRAIN_MODE=production
SOMABRAIN_POSTGRES_DSN=postgresql://***REMOVED***@postgres:5432/somabrain
SOMABRAIN_REDIS_URL=redis://redis:6379/1
SOMABRAIN_KAFKA_URL=kafka:9092
SOMABRAIN_MEMORY_HTTP_ENDPOINT=http://somafractalmemory:10101
SOMABRAIN_MEMORY_HTTP_TOKEN=<shared-sfm-token>
SOMABRAIN_OPA_URL=http://opa:8181
```

**SomaFractalMemory:**
```bash
SOMA_DB_HOST=postgres
SOMA_DB_PORT=5432
SOMA_DB_USER=soma
SOMA_DB_PASSWORD=<from-vault>
SOMA_REDIS_HOST=redis
SOMA_REDIS_PORT=6379
SOMA_MILVUS_HOST=milvus
SOMA_MILVUS_PORT=19530
SOMA_API_PORT=10101
SOMA_API_TOKEN=<shared-sfm-token>
VAULT_ADDR=http://vault:8200
VAULT_TOKEN=<from-env>
SOMA_OPA_URL=http://opa:8181
```

### 6.2 Shared Secrets

| Secret | Generated By | Consumers |
|--------|-------------|-----------|
| `POSTGRES_PASSWORD` | Deployer | All three (via Vault or env) |
| `SOMA_API_TOKEN` | Deployer | SomaAgent01 → SomaBrain, SomaBrain → SFM |
| `SPICEDB_TOKEN` | Deployer | SomaAgent01 → SpiceDB |
| `VAULT_ROOT_TOKEN` | Deployer | All three (for secret retrieval) |
| `KEYCLOAK_ADMIN_PASSWORD` | Deployer | Keycloak admin |
| `SECRET_KEY` | Deployer | SomaAgent01 Django secret |

---

## 7. Health and Monitoring

### 7.1 Health Check Endpoints

| Service | Endpoint | Expected Response |
|---------|----------|-------------------|
| SomaAgent01 | `GET /api/health/` | `{"status": "ok", "service": "somaagent-gateway", "version": "2.0.0"}` |
| SomaBrain | `GET /health` | `{"status": "healthy", "mode": "production"}` |
| SomaFractalMemory | `GET /healthz` | `{"kv_store": true, "vector_store": true, "graph_store": true}` |

### 7.2 Metrics Endpoints

| Service | Endpoint | Format |
|---------|----------|--------|
| SomaAgent01 | `GET /metrics` | Prometheus |
| SomaBrain | `GET /metrics` | Prometheus |
| SomaFractalMemory | `GET /metrics` | Prometheus |

### 7.3 Dashboard URLs (Grafana)

| Dashboard | Purpose |
|-----------|---------|
| Soma Overview | Cross-service request flow, latency, error rates |
| Chat Pipeline | V3 orchestrator phase timings, token counts |
| Cognitive Load | Brain predictor accuracy, neuromodulator levels |
| Memory Operations | SFM store/recall latency, Milvus index stats |

---

## 8. Scaling

### 8.1 Horizontal Scaling

| Component | Scaling Strategy | Min | Max |
|-----------|------------------|-----|-----|
| SomaAgent01 | HPA on CPU/request rate | 2 | 10 |
| SomaBrain | HPA on cognitive queue depth | 2 | 6 |
| SomaFractalMemory | HPA on search request rate | 2 | 8 |

### 8.2 Vertical Scaling

| Component | Minimum | Recommended (Prod) |
|-----------|---------|-------------------|
| SomaAgent01 | 1 CPU, 2 GB RAM | 4 CPU, 8 GB RAM |
| SomaBrain | 2 CPU, 4 GB RAM | 8 CPU, 16 GB RAM |
| SomaFractalMemory | 1 CPU, 2 GB RAM | 4 CPU, 8 GB RAM |
| PostgreSQL | 2 CPU, 4 GB RAM | 8 CPU, 32 GB RAM |
| Redis | 1 CPU, 2 GB RAM | 2 CPU, 8 GB RAM |
| Kafka | 2 CPU, 4 GB RAM | 4 CPU, 16 GB RAM |
| Milvus | 4 CPU, 8 GB RAM | 16 CPU, 64 GB RAM |

---

## 9. Backup and Recovery

| Component | Backup Method | Frequency | Retention |
|-----------|--------------|-----------|-----------|
| PostgreSQL | pg_dump + WAL archiving | Hourly incremental, daily full | 30 days |
| Redis | RDB snapshots + AOF | Every 5 minutes | 7 days |
| Kafka | Topic replication (factor=3) | Continuous | 7 days |
| Milvus | Milvus backup tool | Daily | 30 days |
| Vault | Vault snapshot | Daily | 90 days |

---

## 10. Security (AAAS Mode)

### 10.1 Network Isolation

All services communicate on an internal Docker network. Only the following ports are exposed to the host:

| Port | Service | Reason |
|------|---------|--------|
| 63900 | SomaAgent01 API | User-facing gateway |
| 63980 | Keycloak | User login (optional, can proxy through gateway) |

All other ports (Brain, SFM, PostgreSQL, Redis, etc.) are **internal only**.

### 10.2 Inter-Service Authentication

| From | To | Auth Method |
|------|-----|-------------|
| SomaAgent01 | SomaBrain | Bearer token (`SOMA_API_TOKEN`) |
| SomaAgent01 | SomaFractalMemory | Bearer token (`SOMA_API_TOKEN`) |
| SomaAgent01 | SpiceDB | Pre-shared key (`SPICEDB_TOKEN`) |
| SomaAgent01 | OPA | No auth (internal network) |
| SomaBrain | SomaFractalMemory | Bearer token (sbk_* prefix) |
| All | PostgreSQL | Username/password (from Vault) |
| All | Redis | Password (from Vault, optional) |
| All | Vault | Token authentication |

---

End of Document
