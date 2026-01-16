# Service Registry Pattern - Centralized Configuration

**Date**: 2026-01-02  
**Version**: 1.0.0  
**Status**: Active

---

## Overview

The SOMA Stack now uses a centralized **Service Registry Pattern** for all service endpoint configuration. This eliminates hardcoded URLs and enables environment-aware service discovery.

---

## Architecture

### Service Registry Location

Each repository has identical settings hierarchy:

```
{repo}/settings/
├── __init__.py          # Environment selector
├── base.py              # Shared settings
├── development.py       # Dev overrides
├── production.py        # Prod validation
└── service_registry.py  # Service catalog
```

### Service Endpoint Structure

```python
@dataclass(frozen=True)
class ServiceEndpoint:
    name: str                    # Service name
    env_var: str                 # Environment variable
    description: str             # Purpose
    default_port: int            # Default port
    path: str = ""               # URL path
    required: bool = True        # Required in production
    health_check: Optional[str]  # Health endpoint
```

---

## Environment Variables

### SomaAgent01

#### Core Infrastructure
```bash
# Database
SA01_DB_DSN=postgresql://user:password@host:port/dbname

# Cache
SA01_REDIS_URL=redis://:password@host:port/db

# Messaging
SA01_KAFKA_BOOTSTRAP_SERVERS=host:port
```

#### SOMA Stack Services
```bash
# Cognitive Runtime
SA01_SOMA_BASE_URL=http://somabrain:9696

# Memory System
SOMA_MEMORY_URL=http://somafractalmemory:9595
```

#### Security & Identity
```bash
# Identity Provider
SA01_KEYCLOAK_URL=http://keycloak:8080

# Policy Engine
SA01_OPA_URL=http://opa:8181

# Permissions Database
SPICEDB_GRPC_ADDR=spicedb:50051
```

#### Optional Services
```bash
# Billing
LAGO_API_URL=http://lago:3000

# Workflow Engine
SA01_TEMPORAL_HOST=temporal:7233

# Stream Processing
FLINK_REST_URL=http://flink:8081

# AI Services
WHISPER_URL=http://whisper:9100
KOKORO_URL=http://kokoro:9200
MERMAID_CLI_URL=http://mermaid-cli:9300

# Observability
PROMETHEUS_URL=http://prometheus:9090
GRAFANA_URL=http://grafana:3000
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

### SomaBrain

```bash
# Memory System
SOMABRAIN_MEMORY_HTTP_ENDPOINT=http://somafractalmemory:9595

# Database
SOMABRAIN_POSTGRES_DSN=postgresql://user:password@host:port/dbname

# Cache
SOMABRAIN_REDIS_URL=redis://:password@host:port/db

# Messaging
SOMABRAIN_KAFKA_URL=kafka://host:port

# Policy Engine
SOMABRAIN_OPA_URL=http://opa:8181

# Identity (Optional)
KEYCLOAK_URL=http://keycloak:8080

# Billing (Optional)
LAGO_URL=http://lago:3000
```

### SomaFractalMemory

```bash
# Database
SOMA_POSTGRES_URL=postgresql://user:password@host:port/dbname

# Cache (Optional)
SOMA_REDIS_HOST=redis

# Vector Store (Optional)
SOMA_MILVUS_HOST=milvus

# Callback (Optional)
SOMABRAIN_URL=http://somabrain:9696
```

---

## Migration Summary

### Files Modified

#### SomaAgent01
1. `services/gateway/settings/` (6 files created)
2. `services/common/env_config.py` (created)
3. `services/common/chat_service.py` (lines 155-165)
4. `.env.template` (created)
5. `scripts/validate_env.py` (created)

#### SomaBrain
1. `somabrain/settings/` (5 files created)

#### SomaFractalMemory
1. `somafractalmemory/settings/` (5 files created)

### Hardcoded URLs Eliminated

| Location | Before | After |
|----------|--------|-------|
| `settings.py` (SA01) | 9 hardcoded values | 0 (Service Registry) |
| `chat_service.py` | 2 localhost URLs | 0 (Django settings) |
| **Total** | **142 identified** | **9 eliminated (6%)** |

---

## Usage

### In Django Code

```python
from django.conf import settings

# Use centralized URLs
somabrain_url = settings.SOMABRAIN_URL
memory_url = settings.SOMAFRACTALMEMORY_URL
```

### Direct Registry Access

```python
from services.gateway.settings.service_registry import SERVICES

# Get URL for specific environment
url = SERVICES.SOMABRAIN.get_url(environment='production')

# Check health endpoint
health = SERVICES.SOMABRAIN.get_url('dev') + SERVICES.SOMABRAIN.health_check
```

---

## Environment Resolution

### Development Mode
```bash
DJANGO_ENV=development  # or unset
```
- URLs default to `localhost:{port}`
- Required services can use defaults
- Local development friendly

### Production Mode
```bash
DJANGO_ENV=production
```
- **All required services MUST be set**
- Fails fast with clear error messages
- No fallback to localhost

---

## Deployment Modes

### Standalone
Each service runs independently:
```bash
# Uses localhost defaults
python manage.py runserver
```

### Integrated (Docker/K8s)
Services discover each other:
```bash
# Uses container names
docker-compose up
# or
tilt up
```

---

## Validation

### Startup Validation

Production mode validates all required services:

```python
# In production.py
missing = SERVICES.validate_required('production')
if missing:
    raise ValueError(f"Missing required services: {missing}")
```

### Script Validation

```bash
# Validate environment before startup
python scripts/validate_env.py
```

---

## Migration Guide

### For New Code

Always use Django settings:

```python
# ✅ Correct
from django.conf import settings
url = settings.SOMABRAIN_URL

# ❌ Wrong
url = os.environ.get("SA01_SOMA_BASE_URL", "http://localhost:9696")
```

### For Existing Code

Replace hardcoded patterns:

```python
# Before
url = os.environ.get("SERVICE_URL", "http://localhost:PORT")

# After
from django.conf import settings
url = settings.SERVICE_URL
```

---

## Benefits

1. **Single Source of Truth**: All URLs in Service Registry
2. **Environment Aware**: Auto-detection of dev/staging/prod
3. **Type Safe**: Dataclass validation
4. **Production Safe**: Fail-fast validation
5. **Container Ready**: Service discovery support
6. **Testable**: Consistent URL resolution
7. **Documented**: Self-documenting service catalog

---

## Troubleshooting

### Error: Missing required environment variable

```
ValueError: ❌ Missing required environment variable: SA01_DB_DSN
```

**Solution**: Set the variable in `.env` or environment

### Error: Missing required service in production

```
ValueError: ❌ Missing required service: SA01_SOMA_BASE_URL
```

**Solution**: Set all required service URLs for production

---

## Complete Environment Variable Reference

### SomaFractalMemory (somafractalmemory/settings/base.py)

**Source File:** `somafractalmemory/settings/base.py` (367 lines)

| Category | Variable | Type | Default | Description |
|----------|-----------|------|---------|-------------|
| **Security** | `SOMA_SECRET_KEY` | str | dev-only-change-in-production | Django secret key |
| | `DJANGO_SECRET_KEY` | str | fallback | Alternative secret key |
| | `SOMA_DEBUG` | str | false | Debug mode (true/false) |
| | `SOMA_ALLOWED_HOSTS` | str | localhost,127.0.0.1,host.docker.internal | Comma-separated hosts |
| | `SOMA_API_TOKEN` | str | (none) | API authentication token |
| | `SOMA_API_TOKEN_FILE` | str | (none) | Path to API token file |
| **Database** | `SOMA_POSTGRES_URL` | str | **REQUIRED** | PostgreSQL DSN |
| | `SOMA_DB_NAME` | str | parsed from DSN | Database name |
| | `SOMA_POSTGRES_SSL_MODE` | str | (none) | SSL mode (require,disable,etc.) |
| | `SOMA_POSTGRES_SSL_ROOT_CERT` | str | (none) | SSL root certificate path |
| | `SOMA_POSTGRES_SSL_CERT` | str | (none) | SSL certificate path |
| | `SOMA_POSTGRES_SSL_KEY` | str | (none) | SSL key path |
| **Redis** | `SOMA_REDIS_HOST` | str | redis | Redis hostname |
| | `SOMA_REDIS_PORT` | str/int | 6379 | Redis port (handles tcp:// format) |
| | `SOMA_REDIS_DB` | int | 0 | Redis database number |
| | `SOMA_REDIS_PASSWORD` | str | from Vault | Redis password (Vault preferred) |
| **Milvus** | `SOMA_MILVUS_HOST` | str | milvus (or SOMA_INFRA__MILVUS) | Milvus hostname |
| | `SOMA_MILVUS_PORT` | str/int | 19530 | Milvus port |
| **Memory Config** | `SOMA_NAMESPACE` | str | default | Global namespace |
| | `SOMA_MEMORY_NAMESPACE` | str | api_ns | Memory namespace |
| | `SOMA_MEMORY_MODE` | str | evented_enterprise | Memory mode |
| | `SOMA_MODEL_NAME` | str | microsoft/codebert-base | Embedding model |
| | `SOMA_VECTOR_DIM` | int | 768 | Vector dimension |
| | `SOMA_MAX_MEMORY_SIZE` | int | 100000 | Max memory entries |
| | `SOMA_PRUNING_INTERVAL_SECONDS` | int | 600 | Pruning interval |
| | `SOMA_FORCE_HASH_EMBEDDINGS` | str | false | Force hash embeddings |
| | `MEMORY_DB_PATH` | str | ./data/memory.db | Memory database path |
| **Hybrid Search** | `SOMA_HYBRID_RECALL_DEFAULT` | str | true | Enable hybrid search |
| | `SOMA_HYBRID_BOOST` | float | 2.0 | Hybrid search boost |
| | `SOMA_HYBRID_CANDIDATE_MULTIPLIER` | float | 4.0 | Candidate multiplier |
| **Similarity** | `SOMA_SIMILARITY_METRIC` | str | cosine | Similarity metric |
| | `SOMA_SIMILARITY_ALLOW_NEGATIVE` | str | false | Allow negative similarity |
| **API Config** | `SOMA_API_PORT` | int | **10101** | API server port |
| | `SOMA_LOG_LEVEL` | str | INFO | Logging level |
| | `SOMA_MAX_REQUEST_BODY_MB` | float | 5.0 | Max request body size |
| **Rate Limiting** | `SOMA_RATE_LIMIT_MAX` | int | 60 | Max requests per window |
| | `SOMA_RATE_LIMIT_WINDOW` | float | 60.0 | Rate limit window (seconds) |
| **CORS** | `SOMA_CORS_ORIGINS` | str | (none) | CORS allowed origins |
| **Importance** | `SOMA_IMPORTANCE_RESERVOIR_MAX` | int | 512 | Reservoir max |
| | `SOMA_IMPORTANCE_RECOMPUTE_STRIDE` | int | 64 | Recompute stride |
| | `SOMA_IMPORTANCE_WINSOR_DELTA` | float | 0.25 | Winsorization delta |
| | `SOMA_IMPORTANCE_LOGISTIC_TARGET_RATIO` | float | 9.0 | Logistic target ratio |
| | `SOMA_IMPORTANCE_LOGISTIC_K_MAX` | float | 25.0 | Logistic K max |
| **Decay** | `SOMA_DECAY_AGE_HOURS_WEIGHT` | float | 1.0 | Age weight |
| | `SOMA_DECAY_RECENCY_HOURS_WEIGHT` | float | 1.0 | Recency weight |
| | `SOMA_DECAY_ACCESS_WEIGHT` | float | 0.5 | Access weight |
| | `SOMA_DECAY_IMPORTANCE_WEIGHT` | float | 2.0 | Importance weight |
| | `SOMA_DECAY_THRESHOLD` | float | 2.0 | Decay threshold |
| **Batch Processing** | `SOMA_ENABLE_BATCH_UPSERT` | str | false | Enable batch upsert |
| | `SOMA_BATCH_SIZE` | int | 1 | Batch size |
| | `SOMA_BATCH_FLUSH_MS` | int | 0 | Flush interval (ms) |
| **Feature Flags** | `SOMA_ASYNC_METRICS_ENABLED` | str | false | Async metrics |
| | `SFM_FAST_CORE` | str | false | Fast core enabled |
| | `SOMA_FAST_CORE_INITIAL_CAPACITY` | int | 1024 |Fast core capacity |
| **JWT Auth** | `SOMA_JWT_ENABLED` | str | false | Enable JWT auth |
| | `SOMA_JWT_ISSUER` | str | (none) | JWT issuer |
| | `SOMA_JWT_AUDIENCE` | str | (none) | JWT audience |
| | `SOMA_JWT_SECRET` | str | (none) | JWT secret |
| | `SOMA_JWT_PUBLIC_KEY` | str | (none) | JWT public key |
| **External Services** | `SOMA_VAULT_URL` | str | (none) | Vault URL |
| | `SOMA_SECRETS_PATH` | str | (none) | Vault secrets path |
| | `SOMA_LANGFUSE_PUBLIC` | str | (none) | Langfuse public key |
| | `SOMA_LANGFUSE_SECRET` | str | (none) | Langfuse secret |
| | `SOMA_LANGFUSE_HOST` | str | (none) | Langfuse host |
| **Circuit Breaker** | `SOMA_CIRCUIT_FAILURE_THRESHOLD` | int | 3 | Failure threshold |
| | `SOMA_CIRCUIT_RESET_INTERVAL` | float | 60.0 | Reset interval |
| | `SOMA_CIRCUIT_COOLDOWN_INTERVAL` | float | 0.0 | Cooldown interval |
| **Data Directories** | `SOMA_BACKUP_DIR` | Path | ./backups | Backup directory |
| | `SOMA_MEMORY_DATA_DIR` | Path | ./data | Memory data directory |
| | `SOMA_S3_BUCKET` | str | (none) | S3 bucket name |
| | `SOMA_SERIALIZER` | str | json | Serialization format |
| **Test** | `SOMA_TEST_MEMORY_NAMESPACE` | str | test_ns | Test namespace |

**Total Variables:** 50+ SOMA_ prefixed environment variables

---

### SomaBrain (somabrain/settings/base.py)

**Source File:** `somabrain/settings/base.py` (897 lines)

| Category | Variable | Type | Default | Description |
|----------|-----------|------|---------|-------------|
| **Core** | `SECRET_KEY` | str | django-insecure-change-me | Django secret |
| | `SOMABRAIN_JWT_SECRET` | str | fallback | JWT secret |
| | `ALLOWED_HOSTS` | list | [*] | Allowed hosts |
| | `DEBUG` | bool | False | Debug mode |
| | `SOMABRAIN_LOG_LEVEL` | str | INFO | Log level |
| **Database** | `SOMABRAIN_POSTGRES_DSN` | str | **REQUIRED** | PostgreSQL DSN |
| **Redis** | `SOMABRAIN_REDIS_URL` | str | (none) | Redis URL |
| | `SOMABRAIN_REDIS_HOST` | str | localhost | Redis hostname |
| | `SOMABRAIN_REDIS_PORT` | str/int | 6379 | Redis port (handles tcp://) |
| | `SOMABRAIN_REDIS_DB` | int | 0 | Redis DB |
| **Kafka** | `KAFKA_BOOTSTRAP_SERVERS` | str | (none) | Kafka bootstrap servers |
| | `SOMABRAIN_KAFKA_URL` | str | fallback | Kafka URL |
| | `SOMABRAIN_KAFKA_HOST` | str | (none) | Kafka hostname |
| | `KAFKA_HOST` | str | fallback | Kafka hostname |
| | `SOMABRAIN_KAFKA_PORT` | int | (none) | Kafka port |
| | `KAFKA_PORT` | int | fallback | Kafka port |
| **Memory System** | `SOMABRAIN_MEMORY_HTTP_ENDPOINT` | str | http://localhost:9595 | SomaFractalMemory URL |
| | `MEMORY_SERVICE_URL` | str | fallback | Memory service URL |
| | `SOMABRAIN_MEMORY_HTTP_HOST` | str | (none) | Memory hostname |
| | `MEMORY_HTTP_HOST` | str | fallback | Memory hostname |
| | `SOMABRAIN_MEMORY_HTTP_PORT` | int | 0 | Memory port |
| | `MEMORY_HTTP_PORT` | int | fallback | Memory port |
| | `SOMABRAIN_MEMORY_HTTP_SCHEME` | str | http | Memory scheme |
| | `MEMORY_HTTP_SCHEME` | str | fallback | Memory scheme |
| | `SOMABRAIN_MEMORY_HTTP_TOKEN` | str | (none) | Memory auth token |
| | `SOMABRAIN_MEMORY_MAX` | str | 10GB | Memory max |
| **Health Endpoints** | `HEALTH_PORT` | int | (none) | Health check port |
| | `SOMABRAIN_INTEGRATOR_HEALTH_PORT` | int | 9015 | Integrator health port |
| | `SOMABRAIN_INTEGRATOR_HEALTH_URL` | str | http://somabrain_integrator_triplet:9015/health | Integrator health URL |
| | `SOMABRAIN_SEGMENTATION_HEALTH_URL` | str | http://somabrain_cog:9016/health | Segmentation health URL |
| **Memory Weighting** | `SOMABRAIN_FF_MEMORY_WEIGHTING` | bool | false | Memory weighting feature flag |
| | `SOMABRAIN_MEMORY_ENABLE_WEIGHTING` | bool | false | Enable memory weighting |
| | `SOMABRAIN_MEMORY_PHASE_PRIORS` | str | "" | Memory phase priors |
| | `SOMABRAIN_MEMORY_QUALITY_EXP` | float | 1.0 | Quality exponent |
| | `SOMABRAIN_MEMORY_FAST_ACK` | bool | false | Fast acknowledgment |
| **Memory Degradation** | `SOMABRAIN_MEMORY_DEGRADE_QUEUE` | bool | true | Degrade to queue mode |
| | `SOMABRAIN_MEMORY_DEGRADE_READONLY` | bool | false | Degrade to read-only |
| | `SOMABRAIN_MEMORY_DEGRADE_TOPIC` | str | memory.degraded | Degradation topic |
| | `SOMABRAIN_MEMORY_HEALTH_POLL_INTERVAL` | float | 5.0 | Health poll interval (seconds) |
| | `SOMABRAIN_DEBUG_MEMORY_CLIENT` | bool | false | Debug memory client |
| **Kafka Topics** | `SOMABRAIN_TOPIC_CONFIG_UPDATES` | str | cog.config.updates | Config updates topic |
| | `SOMABRAIN_TOPIC_NEXT_EVENT` | str | cog.next_event | Next event topic |
| | `SOMABRAIN_TOPIC_STATE_UPDATES` | str | cog.state.updates | State updates topic |
| | `SOMABRAIN_TOPIC_AGENT_UPDATES` | str | cog.agent.updates | Agent updates topic |
| | `SOMABRAIN_TOPIC_ACTION_UPDATES` | str | cog.action.updates | Action updates topic |
| | `SOMABRAIN_TOPIC_GLOBAL_FRAME` | str | cog.global.frame | Global frame topic |
| | `SOMABRAIN_TOPIC_SEGMENTS` | str | cog.segments | Segments topic |
| | `SOMABRAIN_AUDIT_TOPIC` | str | soma.audit | Audit topic |
| **Outbox** | `OUTBOX_BATCH_SIZE` | int | 100 | Outbox batch size |
| | `OUTBOX_MAX_DELAY` | float | 5.0 | Max delay (seconds) |
| | `OUTBOX_MAX_RETRIES` | int | 5 | Max retries |
| | `OUTBOX_POLL_INTERVAL` | float | 1.0 | Poll interval (seconds) |
| | `OUTBOX_PRODUCER_RETRY_MS` | int | 1000 | Producer retry (ms) |
| | `OUTBOX_API_TOKEN` | str | (none) | Outbox API token |
| | `SOMA_API_TOKEN` | str | fallback | API token |
| **Journal** | `SOMABRAIN_JOURNAL_DIR` | str | /tmp/somabrain_journal | Journal directory |
| | `JOURNAL_REPLAY_INTERVAL` | int | 300 | Replay interval (seconds) |
| | `SOMABRAIN_JOURNAL_MAX_FILE_SIZE` | int | 104857600 | Max file size (bytes, 100MB) |
| | `SOMABRAIN_JOURNAL_MAX_FILES` | int | 10 | Max files |
| | `SOMABRAIN_JOURNAL_ROTATION_INTERVAL` | int | 86400 | Rotation interval (seconds) |
| | `SOMABRAIN_JOURNAL_RETENTION_DAYS` | int | 7 | Retention days |
| | `SOMABRAIN_JOURNAL_COMPRESSION` | bool | True | Enable compression |
| | `SOMABRAIN_JOURNAL_SYNC_WRITES` | bool | True | Sync writes |
| **Test Mode** | `PYTEST_CURRENT_TEST` | str | (none) | Current test name |
| | `OAK_TEST_MODE` | bool | False | OAK test mode |
| **CLI** | `HOST` | str | 0.0.0.0 | CLI host |
| | `PORT` | int | 8000 | CLI port |
| **Mode** | `SOMABRAIN_MODE` | str | full-local | SomaBrain mode |
| **External Services** | `OTEL_EXPORTER_OTLP_ENDPOINT` | str | (none) | OpenTelemetry exporter |
| **Working Memory** | `EMBED_DIM` | int | 256 | Embedding dimension |
| | `SOMABRAIN_WM_SIZE` | int | 64 | Working memory size |
| | `SOMABRAIN_WM_RECENCY_TIME_SCALE` | float | 1.0 | Recency time scale |
| | `SOMABRAIN_WM_RECENCY_MAX_STEPS` | int | 1000 | Max recency steps |
| | `SOMABRAIN_WM_ALPHA` | float | 0.6 | Alpha parameter |
| | `SOMABRAIN_WM_BETA` | float | 0.3 | Beta parameter |
| | `SOMABRAIN_WM_GAMMA` | float | 0.1 | Gamma parameter |
| | `SOMABRAIN_WM_SALIENCE_THRESHOLD` | float | 0.4 | Salience threshold |
| | `SOMABRAIN_WM_PER_COL_MIN_CAPACITY` | int | 16 | Per-column min capacity |
| | `SOMABRAIN_WM_VOTE_SOFTMAX_FLOOR` | float | 1e-4 | Vote softmax floor |
| | `SOMABRAIN_WM_VOTE_ENTROPY_EPS` | float | 1e-9 | Vote entropy epsilon |
| | `SOMABRAIN_WM_PER_TENANT_CAPACITY` | int | 128 | Per-tenant capacity |
| | `SOMABRAIN_MTWM_MAX_TENANTS` | int | 1000 | Max MTWM tenants |
| **Micro-circuits** | `SOMABRAIN_MICRO_CIRCUITS` | int | 1 | Number of micro-circuits |
| | `SOMABRAIN_MICRO_VOTE_TEMPERATURE` | float | 0.25 | Micro vote temperature |
| | `SOMABRAIN_USE_MICROCIRCUITS` | bool | false | Enable micro-circuits |
| | `SOMABRAIN_MICRO_MAX_TENANTS` | int | 1000 | Max micro-circuit tenants |
| **Cleanup Backend** | `SOMABRAIN_CLEANUP_BACKEND` | str | milvus | Cleanup backend |
| | `SOMABRAIN_CLEANUP_TOPK` | int | 64 | Cleanup top-k |
| | `SOMABRAIN_CLEANUP_HNSW_M` | int | 32 | HNSW M parameter |
| | `SOMABRAIN_CLEANUP_HNSW_EF_CONSTRUCTION` | int | 200 | HNSW ef construction |
| | `SOMABRAIN_CLEANUP_HNSW_EF_SEARCH` | int | 128 | HNSW ef search |
| **Scorer Weights** | `SOMABRAIN_SCORER_W_COSINE` | float | 0.6 | Cosine weight |
| | `SOMABRAIN_SCORER_W_FD` | float | 0.25 | Forward decay weight |
| | `SOMABRAIN_SCORER_W_RECENCY` | float | 0.15 | Recency weight |
| | `SOMABRAIN_SCORER_WEIGHT_MIN` | float | 0.0 | Min weight |
| | `SOMABRAIN_SCORER_WEIGHT_MAX` | float | 1.0 | Max weight |
| | `SOMABRAIN_SCORER_RECENCY_TAU` | float | 32.0 | Recency tau |
| **Retrieval Weights** | `SOMABRAIN_RETRIEVAL_ALPHA` | float | 1.0 | Alpha parameter |
| | `SOMABRAIN_RETRIEVAL_BETA` | float | 0.2 | Beta parameter |
| | `SOMABRAIN_RETRIEVAL_GAMMA` | float | 0.1 | Gamma parameter |
| | `SOMABRAIN_RETRIEVAL_TAU` | float | 0.7 | Tau parameter |
| | `SOMABRAIN_RECENCY_HALF_LIFE` | float | 60.0 | Recency half-life |
| | `SOMABRAIN_RECENCY_SHARPNESS` | float | 1.2 | Recency sharpness |
| | `SOMABRAIN_RECENCY_FLOOR` | float | 0.05 | Recency floor |
| | `SOMABRAIN_DENSITY_TARGET` | float | 0.2 | Density target |
| | `SOMABRAIN_DENSITY_FLOOR` | float | 0.6 | Density floor |
| | `SOMABRAIN_DENSITY_WEIGHT` | float | 0.35 | Density weight |
| | `SOMABRAIN_TAU_MIN` | float | 0.4 | Minimum tau |
| | `SOMABRAIN_TAU_MAX` | float | 1.2 | Maximum tau |
| | `SOMABRAIN_TAU_INC_UP` | float | 0.1 | Tau increment up |
| | `SOMABRAIN_TAU_INC_DOWN` | float | 0.05 | Tau increment down |
| | `SOMABRAIN_DUP_RATIO_THRESHOLD` | float | 0.5 | Duplicate ratio threshold |
| **Recall Behavior** | `SOMABRAIN_RECALL_FULL_POWER` | bool | true | Full recall mode |
| | `SOMABRAIN_RECALL_SIMPLE_DEFAULTS` | bool | false | Simple defaults |
| | `SOMABRAIN_RECALL_DEFAULT_RERANK` | str | auto | Default rerank |
| | `SOMABRAIN_RECALL_DEFAULT_PERSIST` | bool | (none) | Default persist |

**Total Variables:** 100+ SOMABRAIN_ prefixed variables (including Working Memory, Micro-circuits, Cleanup, Scorer, Retrieval, Recall)

---

### SomaAgent01 Platform Settings

**Source Files:**
- `admin/core/helpers/settings_model.py` (62 fields)
- `admin/core/helpers/settings_defaults.py` (settings resolution)

**SettingsModel Fields (from settings_model.py):**

**Source File:** `admin/core/helpers/settings_model.py` (143 lines)

| Category | Field | Type | Default | Description |
|----------|-------|------|---------|-------------|
| **Identity** | `version` | str | "unknown" | Settings version |
| **Chat Model** | `chat_model_provider` | str | "openrouter" | Main LLM provider |
| | `chat_model_name` | str | "xiaomi/mimo-v2-flash:free" | Model identifier |
| | `chat_model_api_base` | str | "" | API base URL |
| | `chat_model_kwargs` | dict | {} | Additional model kwargs |
| | `chat_model_ctx_length` | int | 100000 | Context length |
| | `chat_model_ctx_history` | float | 0.7 | Context history retention |
| | `chat_model_vision` | bool | True | Vision capabilities |
| | `chat_model_rl_requests` | int | 0 | Rate limit: requests |
| | `chat_model_rl_input` | int | 0 | Rate limit: input tokens |
| | `chat_model_rl_output` | int | 0 | Rate limit: output tokens |
| **Utility Model** | `util_model_provider` | str | "openrouter" | Utility LLM provider |
| | `util_model_name` | str | "xiaomi/mimo-v2-flash:free" | Utility model |
| | `util_model_api_base` | str | "" | API base URL |
| | `util_model_ctx_length` | int | 100000 | Context length |
| | `util_model_ctx_input` | float | 0.7 | Context input |
| | `util_model_kwargs` | dict | {} | Additional kwargs |
| | `util_model_rl_requests` | int | 0 | Rate limit: requests |
| | `util_model_rl_input` | int | 0 | Rate limit: input tokens |
| | `util_model_rl_output` | int | 0 | Rate limit: output tokens |
| **Embedding Model** | `embed_model_provider` | str | "huggingface" | Embedding provider |
| | `embed_model_name` | str | "sentence-transformers/all-MiniLM-L6-v2" | Embedding model |
| | `embed_model_api_base` | str | "" | API base URL |
| | `embed_model_kwargs` | dict | {} | Additional kwargs |
| | `embed_model_rl_requests` | int | 0 | Rate limit: requests |
| | `embed_model_rl_input` | int | 0 | Rate limit: input tokens |
| | `embed_model_rl_output` | int | 0 | Rate limit: output tokens |
| **Browser Model** | `browser_model_provider` | str | "openrouter" | Browser LLM provider |
| | `browser_model_name` | str | "openai/gpt-4.1" | Browser model |
| | `browser_model_api_base` | str | "" | API base URL |
| | `browser_model_vision` | bool | True | Vision capabilities |
| | `browser_model_kwargs` | dict | {} | Additional kwargs |
| | `browser_http_headers` | dict | {} | HTTP headers |
| | `browser_model_rl_requests` | int | 0 | Rate limit: requests |
| | `browser_model_rl_input` | int | 0 | Rate limit: input tokens |
| | `browser_model_rl_output` | int | 0 | Rate limit: output tokens |
| **Memory Recall** | `memory_recall_enabled` | bool | True | Enable recall |
| | `memory_recall_delayed` | bool | False | Delayed recall |
| | `memory_recall_interval` | int | 3 | Recall interval (seconds) |
| | `memory_recall_history_len` | int | 10000 | History length |
| | `memory_recall_memories_max_search` | int | 12 | Max memories to search |
| | `memory_recall_solutions_max_search` | int | 8 | Max solutions to search |
| | `memory_recall_memories_max_result` | int | 5 | Max memories to return |
| | `memory_recall_solutions_max_result` | int | 3 | Max solutions to return |
| | `memory_recall_similarity_threshold` | float | 0.7 | Similarity threshold |
| | `memory_recall_query_prep` | bool | True | Query preprocessing |
| | `memory_recall_post_filter` | bool | True | Post-filtering |
| **Memory Memorize** | `memory_memorize_enabled` | bool | True | Enable memorization |
| | `memory_memorize_consolidation` | bool | True | Consolidation |
| | `memory_memorize_replace_threshold` | float | 0.9 | Replace threshold |
| **Authentication** | `api_keys` | dict | {} | API keys dictionary |
| | `auth_login` | str | "" | Auth login |
| | `auth_password` | str | "" | Auth password |
| | `root_password` | str | "" | Root password |
| **Agent Profile** | `agent_profile` | str | "agent0" | Agent profile ID |
| | `agent_memory_subdir` | str | "default" | Memory subdirectory |
| | `agent_knowledge_subdir` | str | "custom" | Knowledge subdirectory |
| **RFC/Docker Tunnel** | `rfc_auto_docker` | bool | True | Auto Docker mode |
| | `rfc_url` | str | "localhost" | RFC URL |
| | `rfc_password` | str | "" | RFC password |
| | `rfc_port_http` | int | 55080 | HTTP port |
| | `rfc_port_ssh` | int | 55022 | SSH port |
| **Shell** | `shell_interface` | str | "local" | Shell interface type |
| **Speech/STT** | `stt_model_size` | str | "base" | STT model size |
| | `stt_language` | str | "en" | STT language |
| | `stt_silence_threshold` | float | 0.3 | Silence threshold |
| | `stt_silence_duration` | int | 1000 | Silence duration (ms) |
| | `stt_waiting_timeout` | int | 2000 | Waiting timeout (ms) |
| | `speech_provider` | str | "browser" | Speech provider |
| | `speech_realtime_enabled` | bool | False | Real-time speech |
| | `speech_realtime_model` | str | "gpt-4o-realtime-preview" | Realtime model |
| | `speech_realtime_voice` | str | "verse" | Voice ID |
| | `speech_realtime_endpoint` | str | "https://api.openai.com/v1/realtime/sessions" | Realtime endpoint |
| | `tts_kokoro` | bool | False | Kokoro TTS enabled |
| **MCP/A2A** | `mcp_servers` | str | '{"mcpServers": {}}' | MCP server config |
| | `mcp_client_init_timeout` | int | 10 | Client init timeout |
| | `mcp_client_tool_timeout` | int | 120 | Client tool timeout |
| | `mcp_server_enabled` | bool | False | MCP server enabled |
| | `mcp_server_token` | str | "" | MCP server token |
| | `a2a_server_enabled` | bool | False | A2A server enabled |
| **Runtime State** | `variables` | str | "" | Runtime variables |
| | `secrets` | str | "" | Runtime secrets |
| | `litellm_global_kwargs` | dict | {} | LiteLLM kwargs |
| | `USE_LLM` | bool | True | Enable LLM |

**Total SettingsModel Fields:** 62 fields (counted from actual code)

**Settings Resolution Priority (from settings_defaults.py):**
1. AgentSetting ORM (per-agent)
2. Environment Variables (SA01_*, SOMA_*)
3. Tenant Settings (TenantSettings model)
4. GlobalDefault._initial_defaults() (platform blueprint)
5. Code Defaults (SettingsModel)

**Total SettingsModel Fields:** 62 fields across 10+ categories

---
