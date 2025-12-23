# SomaAgent01 Development Guide

> **CRITICAL**: This guide documents the exact Docker build process, dependency management, and development workflow to prevent configuration errors.

## Table of Contents
1. [Docker Image Build Process](#docker-image-build-process)
2. [Dependency Management](#dependency-management)
3. [Development Workflow](#development-workflow)
4. [Deployment Guide](#deployment-guide)
5. [Troubleshooting](#troubleshooting)

---

## Docker Image Build Process

### Image Architecture

SomaAgent01 uses a **multi-stage Docker build**:

```
┌─────────────────────────────────────────────────────────┐
│             STAGE 1: Builder (python:3.11-slim)         │
│  - Installs build tools (gcc, git, build-essential)    │
│  - Creates virtual environment at /opt/venv             │
│  - Installs Python dependencies                         │
│  - Uses: requirements-dev.txt (NOT requirements.txt!)   │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│           STAGE 2: Runtime (python:3.11-slim)           │
│  - Copies /opt/venv from builder stage                 │
│  - Installs runtime system packages                     │
│  - Copies application code                              │
│  - Creates non-root 'agent' user                        │
└─────────────────────────────────────────────────────────┘
```

### Critical Build Configuration

**File**: `Dockerfile` (lines 47-60)

```dockerfile
# IMPORTANT: Dockerfile uses requirements-dev.txt for DEV builds
# NOT requirements.txt!
RUN if [ "${INCLUDE_ML_DEPS}" = "true" ]; then \
        # ML build uses requirements.txt + requirements-ml.txt
        pip install -r requirements.txt && \
        pip install -r requirements-ml.txt; \
    else \
        # DEV build (default) uses requirements-dev.txt ONLY
        pip install -r requirements-dev.txt; \
    fi
```

### Build Command

```bash
# Standard development build (uses requirements-dev.txt)
docker build -t somaagent-gateway:latest .

# Production ML build (uses requirements.txt + requirements-ml.txt)
docker build --build-arg INCLUDE_ML_DEPS=true -t somaagent-gateway:latest .
```

---

## Dependency Management

### Requirements Files Overview

| File | Purpose | Used By | When |
|------|---------|---------|------|
| `requirements-dev.txt` | **Lightweight dev dependencies** | Dockerfile (default) | Development builds |
| `requirements.txt` | Core production dependencies | Dockerfile (ML mode) | Production ML builds |
| `requirements-ml.txt` | Heavy ML/document processing | Dockerfile (ML mode) | Production ML builds |
| `constraints-ml.txt` | Version constraints for ML deps | Dockerfile (ML mode) | Production ML builds |

### ⚠️ CRITICAL RULE

> **When adding ANY dependency that affects runtime (not just development tools like `black` or `pytest`), you MUST add it to BOTH:**
> 1. `requirements-dev.txt` (for development builds)
> 2. `requirements.txt` (for production builds)

### Common Dependencies Checklist

#### Runtime Dependencies (Add to BOTH files)
- ✅ Kafka libraries (`aiokafka`, `kafka-python`, `lz4`)
- ✅ Database drivers (`psycopg`, `asyncpg`, `redis`)
- ✅ Web frameworks (`fastapi`, `uvicorn`)
- ✅ LLM clients (`litellm`, `openai`, `anthropic`)
- ✅ Observability (`opentelemetry-*`, `prometheus-client`)

#### Development-Only Dependencies (Add ONLY to requirements-dev.txt)
- ✅ Linters (`ruff`, `black`)
- ✅ Testing (`pytest`, `pytest-asyncio`)
- ✅ Documentation generators

### Adding a New Dependency

**Step-by-Step Process:**

1. **Identify dependency type**:
   - Is it needed at runtime? → Add to BOTH `requirements-dev.txt` AND `requirements.txt`
   - Is it dev-only (linter/test)? → Add ONLY to `requirements-dev.txt`

2. **Add to appropriate file(s)**:
   ```bash
   # Example: Adding lz4 for Kafka compression (runtime dependency)
   echo "lz4==4.3.3" >> requirements-dev.txt
   echo "lz4==4.3.3" >> requirements.txt
   ```

3. **Rebuild image**:
   ```bash
   docker build -t somaagent-gateway:latest .
   ```

4. **Restart affected services**:
   ```bash
   docker restart somaagent-conversation-worker
   docker restart somaagent-tool-executor
   # etc.
   ```

---

## Development Workflow

### Initial Setup

```bash
# 1. Clone repository
git clone <repo-url>
cd somaAgent01

# 2. Create environment file
cp .env.example .env

# 3. Build Docker image (uses requirements-dev.txt)
docker build -t somaagent-gateway:latest .

# 4. Start infrastructure services
make up PROFILES=core,app,auth,dev,security
```

### Code Change Workflow

#### Making Code Changes

**When to rebuild:**

| Change Type | Rebuild Required? | Command |
|-------------|-------------------|---------|
| Python code changes in `services/` | ❌ No (if using volume mounts) | `docker restart <service>` |
| Python code changes in `src/` | ❌ No (if using volume mounts) | `docker restart <service>` |
| Dependency changes (`requirements-*.txt`) | ✅ YES | `docker build -t somaagent-gateway:latest .` |
| Configuration changes (`docker-compose.yml`) | ❌ No | `docker compose up -d` |
| Entrypoint script changes (`scripts/entrypoints/`) | ✅ YES | `docker build` + `docker restart` |

#### Quick Development Loop

```bash
# 1. Make code changes to Python files
vim services/conversation_worker/main.py

# 2. Restart specific service (picks up new code via volume mount)
docker restart somaagent-conversation-worker

# 3. Check logs
docker logs -f somaagent-conversation-worker
```

#### Adding New Dependencies

```bash
# 1. Add to requirements-dev.txt (and requirements.txt if runtime dep)
echo "lz4==4.3.3" >> requirements-dev.txt

# 2. Rebuild image (takes ~20-30 minutes)
docker build -t somaagent-gateway:latest .

# 3. Restart all services using this image
docker restart somaagent-gateway somaagent-conversation-worker somaagent-tool-executor

# 4. Verify dependency is installed
docker exec somaagent-conversation-worker pip list | grep lz4
```

---

## Deployment Guide

### Production Deployment

1. **Build production image with ML dependencies**:
   ```bash
   docker build --build-arg INCLUDE_ML_DEPS=true -t somaagent-gateway:prod .
   ```

2. **Tag and push to registry**:
   ```bash
   docker tag somaagent-gateway:prod <registry>/somaagent-gateway:v1.0.0
   docker push <registry>/somaagent-gateway:v1.0.0
   ```

3. **Deploy with production compose**:
   ```bash
   docker compose -f docker-compose.prod.yml up -d
   ```

### Environment-Specific Configuration

| Environment | Image Tag | Requirements Files | Profiles |
|-------------|-----------|-------------------|----------|
| **Development** | `latest` | `requirements-dev.txt` | `core,app,auth,dev,security` |
| **Staging** | `staging` | `requirements.txt` + `requirements-ml.txt` | `core,app,auth,security` |
| **Production** | `v1.x.x` | `requirements.txt` + `requirements-ml.txt` | `core,app,auth,security,observability` |

---

## Troubleshooting

### Common Issues

#### 1. "ModuleNotFoundError" after adding dependency

**Symptom**: Container crashes with `ModuleNotFoundError: No module named 'lz4'`

**Cause**: Dependency added to wrong requirements file

**Solution**:
```bash
# 1. Verify which requirements file Dockerfile uses
grep "requirements-" Dockerfile

# 2. Add dependency to correct file (requirements-dev.txt for dev builds)
echo "lz4==4.3.3" >> requirements-dev.txt

# 3. Rebuild image
docker build -t somaagent-gateway:latest .

# 4. Restart service
docker restart somaagent-conversation-worker
```

#### 2. Code changes not reflected after restart

**Symptom**: Changes to Python files don't appear in running container

**Possible Causes**:
1. Volume mounts not configured in `docker-compose.yml`
2. Image rebuild needed (for entry points / Dockerfile changes)
3. Python bytecode cache (`.pyc` files)

**Solution**:
```bash
# Option 1: Force rebuild without cache
docker build --no-cache -t somaagent-gateway:latest .

# Option 2: Clear Python cache and restart
docker exec somaagent-conversation-worker find /app -name "*.pyc" -delete
docker restart somaagent-conversation-worker
```

#### 3. Kafka LZ4 Compression Error

**Symptom**: `UnsupportedCodecError: Libraries for lz4 compression codec not found`

**Cause**: `lz4` library missing from image

**Solution**:
```bash
# 1. Add lz4 to requirements-dev.txt
echo "lz4==4.3.3" >> requirements-dev.txt

# 2. Rebuild image (required!)
docker build -t somaagent-gateway:latest .

# 3. Restart all Kafka consumers
docker restart somaagent-conversation-worker somaagent-tool-executor somaagent-memory-replicator
```

---

## Quick Reference

### Build Commands
```bash
# Dev build (fast, lightweight)
docker build -t somaagent-gateway:latest .

# Production build (full ML dependencies)
docker build --build-arg INCLUDE_ML_DEPS=true -t somaagent-gateway:prod .

# No-cache rebuild (when debugging)
docker build --no-cache -t somaagent-gateway:latest .
```

### Verification Commands
```bash
# Check installed packages
docker exec somaagent-conversation-worker pip list

# Check specific package
docker exec somaagent-conversation-worker pip show lz4

# Verify Python path
docker exec somaagent-conversation-worker which python

# Check requirements files in image
docker exec somaagent-conversation-worker cat /opt/build/requirements-dev.txt
```

### Service Management
```bash
# Restart single service
docker restart somaagent-conversation-worker

# Restart all core services
docker restart somaagent-gateway somaagent-conversation-worker somaagent-tool-executor somaagent-memory-replicator

# View logs
docker logs -f somaagent-conversation-worker

# Health check
docker ps --filter "name=somaagent"
```

---

## Dependency Update Checklist

Before committing dependency changes:

- [ ] Added to `requirements-dev.txt` (if dev dependency or runtime dependency)
- [ ] Added to `requirements.txt` (if runtime dependency for production)
- [ ] Pinned exact version (e.g., `lz4==4.3.3`, not `lz4>=4.3.3`)
- [ ] Rebuilt Docker image: `docker build -t somaagent-gateway:latest .`
- [ ] Tested in development environment
- [ ] Verified service starts without errors: `docker logs <service>`
- [ ] Documented in CHANGELOG if major dependency

---

**Last Updated**: 2025-12-23  
**Maintained By**: SomaTech LAT Development Team
