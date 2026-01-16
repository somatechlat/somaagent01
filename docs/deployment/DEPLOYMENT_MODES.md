# Deployment Modes - SAAS vs STANDALONE

**Last Updated**: January 15, 2026  
**Status**: ✅ Production-Grade

---

## Overview

SomaAgent01 supports two deployment modes that determine how components interact with external services:

| Mode | Environment Variable | Description |
|-------|-------------------|-------------|
| **SAAS** | `SA01_DEPLOYMENT_MODE="SAAS"` | Full multi-tenant SaaS deployment with HTTP service calls |
| **STANDALONE** | `SA01_DEPLOYMENT_MODE="STANDALONE"` | Single-instance deployment with embedded modules |

**Default**: SAAS  
**Detection**: Checked from `DEPLOYMENT_MODE` environment variable at startup

---

## Component Behavior by Mode

### 1. ChatService (`services/common/chat_service.py`)

| Feature | SAAS Mode | STANDALONE Mode |
|----------|-------------|-----------------|
| **SomaBrain Integration** | HTTP client (`SomaBrainClient.get_async()`) to `http://localhost:9696` | Embedded Python modules (direct imports) |
| **LLM Timeout** | 60 seconds (network calls) | 30 seconds (local/embedded) |
| **Context Builder** | HTTP API calls to SomaBrain endpoints | Direct PostgreSQL via embedded modules |
| **Database** | PostgreSQL via Django ORM (Port 63932) | PostgreSQL via Django ORM (Port 63932) |

**Code Reference**:
```python
# services/common/chat_service.py

SAAS_MODE = DEPLOYMENT_MODE == "SAAS"
STANDALONE_MODE = DEPLOYMENT_MODE == "STANDALONE"

# Timeout configuration
LLM_TIMEOUT_SAAS = 60  # seconds
LLM_TIMEOUT_STANDALONE = 30  # seconds
```

---

### 2. SimpleGovernor (`services/common/simple_governor.py`)

| Feature | SAAS Mode | STANDALONE Mode |
|----------|-------------|-----------------|
| **Budget Allocation** | Same in both modes (fixed ratios) | Same in both modes (fixed ratios) |
| **Health Decision** | Binary: HEALTHY vs DEGRADED | Binary: HEALTHY vs DEGRADED |
| **Source of Truth** | `LLMModelConfig` ORM table | `LLMModelConfig` ORM table |

**Production Ratios (Field-Tested)**:

| Lane | NORMAL Mode | DEGRADED Mode |
|-------|-------------|----------------|
| **system_policy** | 15% | 40% (prioritized) |
| **history** | 25% | 10% (minimal) |
| **memory** | 25% | 15% (limited) |
| **tools** | 20% | 0% (disabled) |
| **tool_results** | 10% | 0% (disabled) |
| **buffer** | 5% | 35% (safety margin) |

**Governance Logic** (From `simple_governor.py` line 142):
```python
def allocate_budget(
    self,
    max_tokens: int,
    is_degraded: bool
) -> GovernorDecision:
    """Allocate token budget across 6 lanes based on health status.
    Returns GovernorDecision with lane_budget, health_status, mode.
    
    Ratios are FIELD-TESTED in production environments.
    No AIQ scoring or dynamic ratios (simplified from deprecated AgentIQ).
    """
```

**NO AGENTIQ**: SimpleGovernor (279 lines) replaced AgentIQ (1,300+ lines).  
**See**: `docs/srs/SRS-UNIFIED-LAYERS-PRODUCTION-READY.md` for migration history.

---

### 3. SimpleContextBuilder (`services/common/simple_context_builder.py`)

| Feature | SAAS Mode | STANDALONE Mode |
|----------|-------------|-----------------|
| **Memory Retrieval** | HTTP POST `/v1/context/evaluate` to SomaBrain | Direct embedded module calls |
| **Connection** | `SomaBrainClient.get_async()` (HTTP client) | Embedded Python imports (somabrain package) |
| **Error Handling** | Graceful degradation (fallback minimal context) | Graceful degradation (fallback minimal context) |

**Memory Retrieval Flow**:

```
SAAS Mode:
  ChatService → SomaBrainClient.get_async()
           → HTTP POST to http://localhost:9696/v1/context/evaluate
           → JSON response: {"snippets": [...]}
           → BuildContext with memory snippets

STANDALONE Mode:
  ChatService → Embedded module (somabrain)
           → Direct Python function calls
           → BuildContext with memory snippets
```

**Circuit Breaker Protection** (Both modes):
- Threshold: 5 consecutive failures
- Reset: 30 seconds
- Action: Fallback to minimal context (no memory)

---

### 4. SomaBrain Client

**SAAS Mode**:
- Location: `admin/core/somabrain_client.py`
- Initialization: `SomaBrainClient.get_async()`
- Endpoints:
  - `GET /health` - Health check
  - `POST /v1/context/evaluate` - Memory retrieval
  - `POST /v1/memory/recall` - Alternative recall endpoint
- Timeout: 30 seconds (default)
- Error Handling: Returns `None` on failure (graceful degradation)

**STANDALONE Mode**:
- Location: Embedded modules (somabrain package)
- Initialization: Direct Python imports
- No HTTP calls - module resolution at runtime
- Same memory retrieval interface (polymorphic)

---

### 5. HealthMonitor (`services/common/health_monitor.py`)

| Component Checked | SAAS Mode | STANDALONE Mode |
|-----------------|-------------|-----------------|
| **SomaBrain** | HTTP endpoint reachability | Module import availability |
| **PostgreSQL** | Database response time | Database response time |
| **LLM Provider** | API endpoint availability | API endpoint availability |

**Health States**:
- `HEALTHY` - All components operational
- `DEGRADED` - At least one component degraded

**Binary Model**:
```python
# services/common/health_monitor.py

class HealthStatus:
    HEALTHY = "healthy"
    DEGRADED = "degraded"

def get_overall_health() -> OverallHealth:
    """Returns binary health status (no multi-level degradation).
    Over-engineered AgentIQ had L0-L4 levels - removed in Unified Layers.
    """
```

---

### 6. Infrastructure Connections

| Component | SAAS Mode | STANDALONE Mode | Source |
|-----------|-------------|-----------------|--------|
| **PostgreSQL** | Port 63932 (Docker Compose) | Port 63932 (Docker Compose) | `DJANGO_DATABASES` |
| **Redis** | Port 63979 (session store) | Port 63979 (session store) | Django channels settings |
| **Kafka** | Port 63932 (async events) | Port 63932 (async events) | Background memory store |
| **SomaBrain** | Port 63996 (HTTP) | Embedded (no port) | `SA01_SOMA_BASE_URL` or module resolution |
| **MinIO/S3** | Port 63938 (object storage) | Port 63938 (object storage) | Attachments storage |
| **Prometheus** | Metrics push | Metrics push | `unified_metrics.py` |
| **Grafana** | Dashboard access | Dashboard access | Metrics visualization |
| **Keycloak** | Port 63980 (OIDC auth) | Port 63980 (OIDC auth) | JWT token validation |

---

## Configuration

### Required Environment Variables

**Both Modes**:
```bash
# Deployment mode (REQUIRED)
export SA01_DEPLOYMENT_MODE="SAAS"  # OR "STANDALONE"

# Database
export SA01_DB_HOST="localhost"
export SA01_DB_PORT="63932"
export SA01_DB_NAME="somaagent"
export SA01_DB_USER="soma"
export SA01_DB_PASSWORD="soma"

# SomaBrain
export SA01_SOMA_BASE_URL="http://localhost:63996"  # SAAS only

# LLM Provider
export OPENAI_API_KEY="sk-..."  # from Vault
export ANTHROPIC_API_KEY="sk-ant-..."  # from Vault
```

**SAAS Mode Only**:
```bash
# Additional SAAS-specific vars
export SA01_KAFKA_BROKERS="localhost:63932"
export SA01_REDIS_HOST="localhost"
export SA01_REDIS_PORT="63979"
export SA01_MINIO_ENDPOINT="http://localhost:63938"
```

**STANDALONE Mode Only**:
```bash
# No additional infrastructure required
# Embedded modules handle memory and context directly
```

---

## Docker Compose Configuration

### SAAS Mode (`infra/saas/docker-compose.yml`)
```yaml
services:
  postgres:
    image: postgres:15
    ports: ["63932:5432"]
    environment:
      POSTGRES_DB: somaagent
  
  redis:
    image: redis:7
    ports: ["63979:6379"]

  kafka:
    image: confluentinc/cp-kafka:7.4.0
    ports: ["63932:9092"]

  somabrain:
    image: somatechlat/somabrain:latest
    ports: ["63996:9696"]
    environment:
      DEPLOYMENT_MODE: "SAAS"
  
  saas:
    image: somatechlat/somaagent01:latest
    ports: ["63900:9000"]
    environment:
      SA01_DEPLOYMENT_MODE: "SAAS"
      SA01_SOMA_BASE_URL: "http://somabrain:9696"
```

### STANDALONE Mode
```yaml
services:
  postgres:
    image: postgres:15
    ports: ["63932:5432"]
    environment:
      POSTGRES_DB: somaagent
  
  standalone:
    image: somatechlat/somaagent01:latest
    ports: ["63900:9000"]
    environment:
      SA01_DEPLOYMENT_MODE: "STANDALONE"
      # No SomaBrain URL (embedded modules)
```

---

## Degradation Scenarios

### Scenario 1: SomaBrain Unreachable

**SAAS Mode Behavior**:
1. HealthMonitor detects SomaBrain down
2. SimpleGovernor uses DEGRADED ratios (40% system, no tools)
3. SomaBrainClient.get_async() returns `None`
4. SimpleContextBuilder uses minimal context (no memory)
5. LLM invoked with capsule prompt only (fallback)
6. Memory storage queues to OutboxMessage table
7. Background worker replays when SomaBrain recovers

**STANDALONE Mode Behavior**:
1. ImportError during embedded module load
2. HealthMonitor sets DEGRADED flag
3. SimpleGovernor uses DEGRADED ratios
4. SimpleContextBuilder uses minimal context
5. LLM invoked with capsule prompt only
6. Memory storage fails gracefully (no Outbox needed)

**Result**: Chat works in both modes (graceful degradation)

---

### Scenario 2: PostgreSQL Degraded

**Both Modes**:
1. HealthMonitor detects slow database (>5s response time)
2. SimpleGovernor allocates minimal history (10% budget)
3. ContextBuilder limits history retrieval
4. LLM generates response with less context
5. Metrics record degraded state

**Result**: Reduced context quality, but service functional

---

### Scenario 3: All Systems Healthy

**Both Modes**:
1. HealthMonitor confirms all components HEALTHY
2. SimpleGovernor allocates NORMAL ratios (25% history, 25% memory, 20% tools)
3. SomaBrain retrieves relevant memory snippets
4. ContextBuilder builds rich prompt (system + memory + history + user)
5. LLM generates contextual response
6. Memory stores interaction (SomaBrain + PostgreSQL)

**Result**: Full context, highest quality responses

---

## Mode Selection Guidelines

### Choose SAAS Mode When:
- Multi-tenant SaaS deployment
- Separate SomaBrain service required
- External services (Kafka, Redis, MinIO) available
- Production environment with infrastructure team
- Need for independent scaling (scale components separately)

### Choose STANDALONE Mode When:
- Single-instance deployment
- Development or testing environment
- Quick prototyping without external dependencies
- Low-latency requirements (no HTTP overhead)
- Embedded memory sufficient

---

## Migration Between Modes

### SAAS → STANDALONE
```bash
# 1. Change environment variable
export SA01_DEPLOYMENT_MODE="STANDALONE"

# 2. Remove SomaBrain URL
unset SA01_SOMA_BASE_URL

# 3. Restart service
docker compose restart saas

# 4. Verify embedded module imports
# Check logs for "SomaBrain embedded modules loaded"
```

### STANDALONE → SAAS
```bash
# 1. Change environment variable
export SA01_DEPLOYMENT_MODE="SAAS"

# 2. Set SomaBrain URL
export SA01_SOMA_BASE_URL="http://localhost:63996"

# 3. Start infrastructure
docker compose -f infra/saas/docker-compose.yml up -d

# 4. Restart service
docker compose restart saas

# 5. Verify HTTP connection
# Check logs for "SomaBrainClient connected: http://localhost:63996"
```

---

## Troubleshooting

### Issue: "SomaBrain connection timeout"

**SAAS Mode**:
```bash
# Check SomaBrain service
docker ps | grep somabrain  # Should be "up"
docker logs somabrain  # Check for errors

# Test HTTP endpoint
curl http://localhost:63996/health
# Should return: {"status": "healthy"}
```

**STANDALONE Mode**:
```bash
# Check embedded module imports
# Look for logs: "Failed to import somabrain embedded modules"
# This indicates module path issue, not connectivity

# Verify somabrain package is installed
pip show somabrain  # Should show version
```

---

### Issue: "Governor using DEGRADED ratios (not expected)"

**Both Modes**:
```bash
# Check health status
curl http://localhost:63900/api/v2/health
# Verify all components show "healthy"

# Check SimpleGovernor logs
docker logs saas | grep "is_degraded"
# Should show: "is_degraded: False" (when healthy)
```

---

## References

- **SimpleGovernor Implementation**: `services/common/simple_governor.py` (279 lines)
- **SimpleContextBuilder**: `services/common/simple_context_builder.py` (~400 lines)
- **HealthMonitor**: `services/common/health_monitor.py` (~250 lines)
- **Migration History**: `docs/srs/SRS-UNIFIED-LAYERS-PRODUCTION-READY.md`
- **Architecture Diagram**: `docs/architecture/chat_architecture.md`
- **Component Tests**: `tests/test_deployment_mode_unified.py`

---

**Document Version**: 1.0  
**Author**: Technical Documentation Team  
**Maintained By**: Infrastructure Team
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
