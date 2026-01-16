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
