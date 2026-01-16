# Software Deployment Modes (SomaStack)

**Purpose:** Define software-level modes for the three services when run
standalone or as a unified SaaS.

**Last Updated:** 2026-01-13 by SOMA Collective Intelligence Audit

---

## 1. The Four Deployment Dimensions

> **CRITICAL**: SomaStack has **4 orthogonal deployment dimensions** that MUST be 
> understood before making any code changes.

| Dimension | Environment Variable | Values | Purpose |
|-----------|---------------------|--------|---------|
| **Software Mode** | `SOMASTACK_SOFTWARE_MODE` | `StandAlone` / `SomaStackClusterMode` | Service coupling |
| **Environment** | `SA01_DEPLOYMENT_MODE` | `DEV` / `PROD` | Debug vs production (fail-fast) |
| **SaaS Bridge** | `SOMA_SAAS_MODE` | `true` / `false` | In-process vs HTTP calls |
| **Infrastructure** | Tilt / K8s / Docker | Varies | Orchestration target |

### 1.1 Dimension Relationships

```
SA01_DEPLOYMENT_MODE=PROD
├── All localhost fallbacks FAIL-FAST (VIBE Rule 91)
├── All secrets required from Vault (VIBE Rule 164)
└── No dev defaults allowed

SOMA_SAAS_MODE=true
├── saas/brain.py → Direct Python import of somabrain
├── saas/memory.py → Direct Python import of fractal_memory
└── 100x performance (0.05ms vs 5ms per operation)

SOMA_SAAS_MODE=false
├── SomaBrainClient → HTTP to somabrain:30101
├── MemoryBridge → HTTP to somafractalmemory:10101
└── Requires SOMA_MEMORY_API_TOKEN for auth
```

---

## 2. Mode Names (Canonical)

- **StandAlone**: Each service runs independently with its own auth, storage,
  and configuration.
- **SomaStackClusterMode**: All three services run as a unified SaaS with shared
  tenant identity, shared authorization, and coupled Brain+Memory runtime.

These names are canonical for documentation and future configuration flags.

---

## 3. Behavior by Mode

### 3.1 StandAlone

- Each service must boot and operate without dependencies on the other two.
- Local auth and storage must be sufficient for basic operation.
- Cross-service calls are disabled by default or use local stubs.

### 3.2 SomaStackClusterMode

- SomaAgent01 is the control plane (tenants, users, agents, billing).
- SomaBrain and SomaFractalMemory are inseparable and must run as a paired
  runtime for memory-backed cognition.
- Cross-service calls require service-to-service auth and shared tenant claims.
- Fine-grained permissions must be enforced via the unified authorization model
  (SpiceDB in the control plane, policy enforcement in downstream services).

---

## 4. VIBE Compliance Rules

### Rule 91: Zero-Fallback Mandate

In `SA01_DEPLOYMENT_MODE=PROD`:
- **NO** localhost defaults allowed
- All service URLs MUST be explicitly configured
- Missing configuration MUST crash on startup

**Implementation**: See `saas/config.py` function `_get_required_host()`

### Rule 164: Zero-Hardcode Mandate

- **NO** hardcoded passwords, tokens, or secrets in source code
- All secrets MUST come from Vault or environment variables
- Dev defaults allowed ONLY in `SA01_DEPLOYMENT_MODE=DEV` with warnings

**Implementation**: See `saas/config.py` function `_get_secret()`

---

## 5. Configuration Contract

### 5.1 SomaAgent01 Configuration

| Variable | Environment Variable | Values | Purpose |
|----------|----------------------|--------|----------|
| **Deployment Mode** | `SA01_DEPLOYMENT_MODE` | `DEV` / `PROD` | Controls fail-fast behavior, localhost fallbacks |
| **Software Mode** | `SOMASTACK_SOFTWARE_MODE` | `StandAlone` / `SomaStackClusterMode` | Service coupling and dependencies |
| **SaaS Mode** | `SOMA_SAAS_MODE` | `true` / `false` | In-process imports vs HTTP calls |
| **Target Platform** | `SA01_DEPLOYMENT_TARGET` | `LOCAL`, `FARGATE`, `EKS`, `ECS_EC2`, `EC2`, `APP_RUNNER` | Infrastructure target |
| **Chat Provider** | `SA01_CHAT_PROVIDER` | `openrouter` (code) / `openai` / `anthropic` | Default chat_model_provider |
| **Default Model** | `SA01_CHAT_MODEL` | `openai/gpt-4.1` / `gpt-4o` / etc. | Default chat_model_name |
| **Debug Mode** | `DEBUG` | `true` / `false` | Django DEBUG flag |
| **Allowed Hosts** | `ALLOWED_HOSTS` | Comma-separated domains | Django ALLOWED_HOSTS |
| **Secret Key** | `SECRET_KEY`, `DJANGO_SECRET_KEY`, `SOMA_SECRET_KEY` | String | Django SECRET_KEY |

**Example PROD Configuration**:
```bash
SA01_DEPLOYMENT_MODE=PROD
SOMASTACK_SOFTWARE_MODE=SomaStackClusterMode
SOMA_SAAS_MODE=true
SA01_DEPLOYMENT_TARGET=FARGATE
SA01_CHAT_PROVIDER=openai
SA01_CHAT_MODEL=openai/gpt-4.1
DEBUG=false
ALLOWED_HOSTS=api.somastack.io,www.somastack.io
SECRET_KEY=$VAULT_SECRET_KEY
```

**Example DEV Configuration**:
```bash
SA01_DEPLOYMENT_MODE=DEV
SOMASTACK_SOFTWARE_MODE=StandAlone
SOMA_SAAS_MODE=false
SA01_DEPLOYMENT_TARGET=LOCAL
DEBUG=true
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 5.2 SomaBrain Configuration

| Variable | Environment Variable | Values | Purpose |
|----------|----------------------|--------|----------|
| **Deployment Mode** | `SOMA_DEPLOYMENT_MODE`, `SA01_DEPLOYMENT_MODE` | `prod` / `staging` / `dev` | Production vs development mode |
| **Port** | `SOMABRAIN_PORT`, `SOMA_API_PORT` | Integer (default: 30101) | HTTP API server port |
| **PostgreSQL URL** | `SOMA_DB_URL`, `DATABASE_URL` | `postgresql://...` | Database connection |
| **Redis URL** | `SOMA_REDIS_URL`, `REDIS_URL` | `redis://...` | Cache connection |
| **Kafka Brokers** | `SOMA_KAFKA_BROKERS` | Comma-separated hosts | Kafka bootstrap servers |
| **Milvus Host** | `SOMA_MILVUS_HOST` | Hostname or IP | Vector DB location |
| **Milvus Port** | `SOMA_MILVUS_PORT` | Integer (default: 19530) | Vector DB port |

### 5.3 SomaFractalMemory Configuration

| Variable | Environment Variable | Values | Purpose |
|----------|----------------------|--------|----------|
| **Software Mode** | `SOMASTACK_SOFTWARE_MODE` | `StandAlone` / `SomaStackClusterMode` | Service coupling |
| **Auth Mode** | `SFM_AUTH_MODE` | `api_token` / `oidc` | Authentication method |
| **API Token** | `SOMA_API_TOKEN` | String | API token for HTTP mode |
| **DB Name** | `SOMA_DB_NAME` | String (default: `somafractalmemory`) | PostgreSQL database name |
| **DB Host** | `SOMA_DB_HOST`, `SOMA_INFRA__POSTGRES` | Hostname (default: `postgres`) | PostgreSQL host |
| **DB Port** | `SOMA_DB_PORT` | Integer (default: 5432) | PostgreSQL port |
| **Milvus Host** | `SOMA_MILVUS_HOST`, `SOMA_INFRA__MILVUS` | Hostname (default: `milvus`) | Vector DB host |
| **Milvus Port** | `SOMA_MILVUS_PORT` | Integer (default: 19530) | Vector DB port |
| **Memory Mode** | `SOMA_MEMORY_MODE` | `evented_enterprise` / `simple` | Memory system mode |
| **API Port** | `SOMA_API_PORT` | Integer (default: 10101) | HTTP API server port |

**Example StandAlone Configuration**:
```bash
SOMASTACK_SOFTWARE_MODE=StandAlone
SFM_AUTH_MODE=api_token
SOMA_API_TOKEN=$(openssl rand -hex 32)
SOMA_DB_HOST=postgres
SOMA_DB_NAME=somafractalmemory
SOMA_MILVUS_HOST=milvus
```

**Example SomaStackClusterMode Configuration**:
```bash
SOMASTACK_SOFTWARE_MODE=SomaStackClusterMode
SFM_AUTH_MODE=oidc
SOMA_DB_NAME=soma_shared
SOMA_MILVUS_HOST=shared-milvus
```

### 5.4 Shared Infrastructure Variables

| Variable | Applies To | Values | Purpose |
|----------|-------------|--------|----------|
| **PostgreSQL Host** | All 3 repos | `SOMA_DB_HOST`, `SOMA_INFRA__POSTGRES` | Shared database server |
| **PostgreSQL Port** | All 3 repos | `SOMA_DB_PORT` (default: 5432) | Database port |
| **Redis Host** | All 3 repos | `SOMA_REDIS_HOST`, `SOMA_INFRA__REDIS` | Shared Redis server |
| **Redis Port** | All 3 repos | `SOMA_REDIS_PORT` (default: 6379) | Redis port |
| **Kafka Brokers** | All 3 repos | `SOMA_KAFKA_BROKERS`, `SOMA_INFRA__KAFKA` | Event streaming |
| **Milvus Host** | All 3 repos | `SOMA_MILVUS_HOST`, `SOMA_INFRA__MILVUS` | Vector DB server |
| **Secrets Backend** | All 3 repos | `VAULT_ADDR`, `VAULT_TOKEN` | Vault integration for secrets |
| `SOMASTACK_SOFTWARE_MODE` | All | `StandAlone` / `SomaStackClusterMode` | Cross-repo |

---

## 6. Topology Export (SomaStack)

In SomaStackClusterMode, the platform must export a deterministic topology tree
labeled `SomaStack` with grouped planes:

- Control Plane: SomaAgent01 (Layer 4)
- Cognitive Plane: SomaBrain (Layer 3)
- Memory Plane: SomaFractalMemory (Layer 2)
- Infrastructure: PostgreSQL, Redis, Milvus (Layer 1)

---

## 7. Operational Rules

- StandAlone mode must never depend on other services for auth or memory.
- SomaStackClusterMode must fail closed if cross-service auth or memory is
  unavailable.
- Brain+Memory pairing is mandatory in SomaStackClusterMode.
- **PROD mode MUST fail-fast** on missing configuration (VIBE Rule 91).
- **Secrets MUST NOT be hardcoded** (VIBE Rule 164).

---

## 8. Audit Trail

| Date | Change | Author |
|------|--------|--------|
| 2026-01-13 | Added 4-dimension model, VIBE compliance section | SOMA Collective |
| 2025-12-30 | Initial version | Team |
