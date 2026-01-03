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

## See Also

- `.env.template` - Complete environment variable reference
- `scripts/validate_env.py` - Environment validation script
- `AGENT.md` - Service architecture documentation
