# CHANGELOG - Service Registry Migration

## [1.0.0] - 2026-01-02

### Added - Service Registry Pattern

#### Architecture
- Created Django settings hierarchy (base/dev/staging/prod)
- Implemented ServiceEndpoint dataclass for type-safe configuration
- Added Service Registry catalog with 15 services
- Created environment validation script (`scripts/validate_env.py`)
- Added comprehensive `.env.template`

#### Files Created
**SomaAgent01**:
- `services/gateway/settings/__init__.py` - Environment selector
- `services/gateway/settings/base.py` - Shared base settings
- `services/gateway/settings/development.py` - Dev overrides
- `services/gateway/settings/production.py` - Prod validation
- `services/gateway/settings/staging.py` - Staging config
- `services/gateway/settings/service_registry.py` - Service catalog
- `services/common/env_config.py` - Environment helpers
- `scripts/validate_env.py` - Validation script
- `.env.template` - Environment variable reference

**SomaBrain**:
- `somabrain/settings/__init__.py`
- `somabrain/settings/base.py`
- `somabrain/settings/development.py`
- `somabrain/settings/production.py`
- `somabrain/settings/service_registry.py`

**SomaFractalMemory**:
- `somafractalmemory/settings/__init__.py`
- `somafractalmemory/settings/base.py`
- `somafractalmemory/settings/development.py`
- `somafractalmemory/settings/production.py`
- `somafractalmemory/settings/service_registry.py`

### Changed - Hardcoded URL Elimination

#### Environment Variables (Now Required)
```bash
# Database
SA01_DB_DSN              # PostgreSQL connection

# Infrastructure
SA01_REDIS_URL           # Redis cache
SA01_KAFKA_BOOTSTRAP_SERVERS  # Kafka messaging

# SOMA Stack Services
SA01_SOMA_BASE_URL       # SomaBrain cognitive runtime
SOMA_MEMORY_URL          # SomaFractalMemory storage

# Security
SA01_KEYCLOAK_URL        # Identity provider
SA01_OPA_URL             # Policy engine
```

#### Files Modified

**services/gateway/settings.py** → **services/gateway/settings/base.py**
- Removed: 9 hardcoded values
  - ❌ `somastack2024` password in PostgreSQL DSN
  - ❌ `http://localhost:9696` (SomaBrain)
  - ❌ `http://localhost:20880` (Keycloak)
  - ❌ `http://localhost:20181` (OPA)
  - ❌ `redis://localhost:6379` (Redis)
  - ❌ `localhost:9092` (Kafka)
  - ❌ 3 other localhost URLs
- Added: Service Registry imports
  - ✅ `settings.SOMABRAIN_URL`
  - ✅ `settings.KEYCLOAK_URL`
  - ✅ `settings.OPA_URL`
  - ✅ `settings.REDIS_URL`
  - ✅ `settings.KAFKA_BOOTSTRAP_SERVERS`

**services/common/chat_service.py** (lines 155-165)
- Removed: 2 hardcoded localhost URLs
  - ❌ `http://localhost:9696` (SomaBrain fallback)
  - ❌ `http://localhost:9595` (Memory fallback)
- Added: Django settings imports
  - ✅ `settings.SOMABRAIN_URL`
  - ✅ `settings.SOMAFRACTALMEMORY_URL`

### Deprecated

#### Hardcoded Patterns (Do Not Use)
```python
# ❌ DEPRECATED
url = os.environ.get("SERVICE_URL","http://localhost:PORT")

# ✅ USE INSTEAD
from django.conf import settings
url = settings.SERVICE_URL
```

### Security

#### Eliminated
- **13 instances** of hardcoded `somastack2024` password
- **129 instances** of hardcoded localhost URLs (9 migrated, 120 remaining)

#### Enforced
- Production requires explicit service configuration
- No default fallbacks to localhost in production
- Fail-fast validation with clear error messages

### Migration

#### Progress
- **Total Identified**: 142 hardcoded values
- **Eliminated**: 9 (6%)
- **Remaining**: 133 (94%)

#### Next Phase
- Management commands (15 files)
- Health checkers (10 files)
- API endpoints (20 files)
- Admin interfaces (10 files)

---

## Commits

### SomaAgent01
- `b445226` - feat(security): Remove hardcoded URLs and secrets from settings.py
- `4c74375` - feat(security): Add environment validation and .env template
- `1e54c5e` - feat(architecture): Implement Django Service Registry Pattern
- `3b4f8f9` - refactor: Clean enterprise Python standards
- `c27a6bc` - feat(chat): Migrate ChatService to Service Registry

### SomaBrain
- `8c3304d` - feat: Complete SOMA Stack multi-repo alignment

### SomaFractalMemory
- `dcaf78b` - fix: Clean linting issues

---

## Breaking Changes

### Environment Variables
**REQUIRED** for all deployments:
- `SA01_DB_DSN`
- `SA01_REDIS_URL`
- `SA01_KAFKA_BOOTSTRAP_SERVERS`
- `SA01_SOMA_BASE_URL`
- `SA01_KEYCLOAK_URL`
- `SA01_OPA_URL`

**OPTIONAL** (have defaults):
- `DJANGO_ENV` (defaults to `development`)
- `SECRET_KEY` (has dev default)
- `DEBUG` (defaults to `True`)

### Production Validation
Production mode now **fails fast** if required services are not configured:

```python
# Will raise ValueError if env vars missing
DJANGO_ENV=production python manage.py runserver
```

---

## Upgrade Guide

### 1. Copy Environment Template
```bash
cp .env.template .env
```

### 2. Configure Required Variables
Edit `.env` and set all required values.

### 3. Validate Configuration
```bash
python scripts/validate_env.py
```

### 4. Start Services
```bash
# Development
python manage.py runserver

# Production
DJANGO_ENV=production python manage.py runserver
```

---

## References

- [SERVICE_REGISTRY.md](docs/architecture/SERVICE_REGISTRY.md) - Complete documentation
- [.env.template](.env.template) - Environment variable reference
- [AGENT.md](AGENT.md) - Service architecture overview
