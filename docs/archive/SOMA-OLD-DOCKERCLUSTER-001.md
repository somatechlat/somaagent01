# Docker Cluster Standalone Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-_SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make SOMAAGENT01 runnable on a Docker cluster in standalone mode today, with a clean upgrade path to connect a real SomaBrain service over HTTP once it is deployed.

**Architecture:** Keep `infra/standalone/docker-compose.yml` as the single source of truth for standalone. Fix the frontend reverse-proxy so the built UI can reach the backend and Keycloak. Fill in the missing standalone services (Kafka, OPA, SpiceDB, workers) or make them gracefully optional. Wire real health checkers into `HealthMonitor` so chat does not run permanently degraded. Align SomaBrain configuration to a single env var (`SA01_SOMA_BASE_URL`) and add a real HTTP health probe.

**Tech Stack:** Django 5.1 + Django Ninja 1.3, Lit 3.x + Vite, PostgreSQL 15, Redis 7, Keycloak 24, Kafka (Redpanda single-node), OPA, SpiceDB, Docker Compose, Tilt (future).

---

## Executive Audit Summary

**Verdict: NOT READY for a functional standalone Docker cluster.**

The backend gateway container can start, but the WebUI reverse-proxy points to services/ports that do not exist (`somaagent-django:8020`, `somaagent-keycloak:8080`), the frontend Keycloak URL is hardcoded to `localhost:20880`, required secrets are blank, and critical dependencies (OPA, SpiceDB, Kafka, LLM keys) are missing. Worker services that run chat/tool/delegation/memory background processing are not orchestrated. Finally, `HealthMonitor` initializes its critical services as `healthy=False` and never registers real checkers, forcing chat into permanent degraded mode.

**SomaBrain readiness:** the HTTP client is clean after the recent fix and will connect automatically once `SA01_SOMA_BASE_URL` is set. However, the mock SomaBrain uses wrong endpoint paths, configuration variables conflict (`SA01_SOMA_BASE_URL` vs `SOMABRAIN_URL` vs port 9696/63996/30101), and no production code registers a SomaBrain health checker.

---

## Phase 0 — Minimum fixes to make `docker compose up` work

### Task 1: Fix WebUI nginx upstreams to match standalone compose

**Files:**
- Modify: `webui/nginx.conf:34-66`
- Test: `curl http://localhost:20080/api/v2/auth/me` after compose up.

**Why:** `/api/`, `/ws/`, and `/auth/` currently proxy to non-existent hostnames/ports (`somaagent-django:8020`, `somaagent-keycloak:8080`). The standalone compose defines `somaagent_standalone:9000` and `somaagent_keycloak:8080`.

- [ ] **Step 1: Replace upstream definitions in `webui/nginx.conf`**

```nginx
    # API proxy to Django backend
    location /api/ {
        proxy_pass http://somaagent_standalone:9000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket proxy
    location /ws/ {
        proxy_pass http://somaagent_standalone:9000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }

    # Auth proxy to Keycloak
    location /auth/ {
        proxy_pass http://somaagent_keycloak:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
```

- [ ] **Step 2: Build the WebUI image**

Run:
```bash
cd /Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgent01/webui
docker build -t somaagent_webui:local .
```

Expected: image builds successfully (`npm run build` + nginx stage).

- [ ] **Step 3: Commit**

```bash
git add webui/nginx.conf
git commit -m "fix(webui): point nginx upstreams to standalone compose service names"
```

---

### Task 2: Make Keycloak URL runtime-configurable in the frontend

**Files:**
- Create: `webui/public/config.json`
- Modify: `webui/src/services/keycloak-service.ts:40-47`
- Modify: `webui/src/main.ts` (boot loader)
- Modify: `webui/nginx.conf` (serve config.json)
- Test: open `/login` in browser; the OIDC authorize URL must use the same origin as the page, not `localhost:20880`.

**Why:** `keycloak-service.ts` hardcodes `http://localhost:20880`. Browser-side code cannot reach `localhost` on a user's machine or inside a cluster.

- [ ] **Step 1: Create `webui/public/config.json` as a runtime config template**

```json
{
  "keycloakUrl": "http://localhost:20880",
  "keycloakRealm": "somaagent",
  "keycloakClientId": "eye-of-god"
}
```

This file is only a build-time fallback. At container runtime nginx will replace it with env-driven values (Step 4).

- [ ] **Step 2: Modify `keycloak-service.ts` to read the config at boot**

Replace the static `KEYCLOAK_CONFIG` block with:

```typescript
// Keycloak configuration - loaded from /config.json at runtime
let KEYCLOAK_CONFIG: KeycloakConfig = {
    url: 'http://localhost:20880',
    realm: 'somaagent',
    clientId: 'eye-of-god',
};

export async function loadKeycloakConfig(): Promise<KeycloakConfig> {
    try {
        const res = await fetch('/config.json', { cache: 'no-store' });
        if (res.ok) {
            const runtime = await res.json();
            KEYCLOAK_CONFIG = { ...KEYCLOAK_CONFIG, ...runtime };
        }
    } catch (e) {
        console.warn('[Keycloak] Could not load runtime config, using defaults', e);
    }
    return KEYCLOAK_CONFIG;
}
```

In `class KeycloakService`, change `private config: KeycloakConfig = { ...KEYCLOAK_CONFIG };` to `private config: KeycloakConfig = { ...KEYCLOAK_CONFIG };` and update `init()` to reassign after `loadKeycloakConfig()` has run.

- [ ] **Step 3: Load config before routing in `webui/src/main.ts`**

At the top of the `if (app)` block, await the config loader once:

```typescript
import { loadKeycloakConfig } from './services/keycloak-service.js';

const app = document.getElementById('app');
if (app) {
    app.innerHTML = '';

    // Load runtime configuration before anything else
    await loadKeycloakConfig();

    const renderRoute = async () => {
        // ... existing routing logic ...
    };

    renderRoute();
    window.addEventListener('popstate', renderRoute);
    // ...
}
```

- [ ] **Step 4: Serve `/config.json` from nginx with env substitution**

Add to `webui/nginx.conf` before the SPA fallback:

```nginx
    # Runtime configuration injection
    location = /config.json {
        add_header Content-Type application/json;
        alias /usr/share/nginx/html/config.json;
    }
```

Create `webui/docker-entrypoint.sh`:

```bash
#!/bin/sh
set -e

# Replace config.json placeholders with runtime environment values
KEYCLOAK_URL="${KEYCLOAK_URL:-http://somaagent_keycloak:8080}"
KEYCLOAK_REALM="${KEYCLOAK_REALM:-somaagent}"
KEYCLOAK_CLIENT_ID="${KEYCLOAK_CLIENT_ID:-eye-of-god}"

cat > /usr/share/nginx/html/config.json <<EOF
{
  "keycloakUrl": "${KEYCLOAK_URL}",
  "keycloakRealm": "${KEYCLOAK_REALM}",
  "keycloakClientId": "${KEYCLOAK_CLIENT_ID}"
}
EOF

exec "$@"
```

Update `webui/Dockerfile` to copy and run it:

```dockerfile
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
```

- [ ] **Step 5: Run TypeScript check and build**

Run:
```bash
cd /Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgent01/webui
npm run build
```

Expected: `tsc` passes and `dist/config.json` exists.

- [ ] **Step 6: Commit**

```bash
git add webui/public/config.json webui/docker-entrypoint.sh webui/nginx.conf webui/src/services/keycloak-service.ts webui/src/main.ts webui/Dockerfile
git commit -m "feat(webui): runtime keycloak configuration for cluster deploys"
```

---

### Task 3: Provide a runnable standalone `.env` template

**Files:**
- Modify: `infra/standalone/.env.example`
- Test: `docker compose -f infra/standalone/docker-compose.yml config` parses without errors.

**Why:** `VAULT_DEV_ROOT_TOKEN_ID`, `POSTGRES_PASSWORD`, and `KEYCLOAK_ADMIN_PASSWORD` are empty; Compose fails immediately with required-var errors.

- [ ] **Step 1: Replace `infra/standalone/.env.example` with safe defaults and clear comments**

```bash
# ═══════════════════════════════════════════════════════════════════════════════
# SOMAAGENT01 STANDALONE DEPLOYMENT - ENVIRONMENT TEMPLATE
# ═══════════════════════════════════════════════════════════════════════════════
# Copy this file to infra/standalone/.env and customize secrets before deploy.
# ═══════════════════════════════════════════════════════════════════════════════

SA01_DEPLOYMENT_MODE=STANDALONE
SA01_DEPLOYMENT_TARGET=LOCAL
DJANGO_DEBUG=false

# Vault (dev server only - do not use empty token in production)
VAULT_ADDR=http://somaagent_vault:8200
VAULT_MOUNT=secret
VAULT_PATH_PREFIX=somaagent
# VAULT_DEV_ROOT_TOKEN_ID is NEVER set here — injected at runtime by the deployer.
# Database
POSTGRES_HOST=somaagent_postgres
POSTGRES_PORT=5432
POSTGRES_DB=somaagent
POSTGRES_USER=somaagent
# POSTGRES_PASSWORD comes from Vault: secret/agent/credentials/postgres_password
# SA01_DB_DSN is built at runtime from the topology above — no DSNs in ENV.

# Redis
REDIS_HOST=somaagent_redis
REDIS_PORT=6379
REDIS_DB=0
SA01_REDIS_URL=redis://somaagent_redis:6379/0

# Keycloak
KEYCLOAK_URL=http://somaagent_keycloak:8080
KEYCLOAK_ADMIN=admin
# KEYCLOAK_ADMIN_PASSWORD comes from Vault: secret/agent/credentials/keycloak_admin_password
KEYCLOAK_REALM=somaagent
KEYCLOAK_CLIENT_ID=somaagent-api
SA01_KEYCLOAK_URL=http://somaagent_keycloak:8080

# Agent API
SAGENTA_HOST=0.0.0.0
SAGENTA_PORT=9000
SA01_ALLOWED_HOSTS=*

# LLM (standalone mode: set a provider key OR a local base URL)
SA01_LLM_MODEL=gpt-4o-mini
# Provider keys come from Vault: secret/agent/api_keys/{provider}_api_key
# SA01_LLM_BASE_URL=http://host.docker.internal:11434/v1  # for local Ollama

# Worker dependencies
SA01_WORKER_GATEWAY_BASE=http://somaagent_standalone:9000
SA01_KAFKA_BOOTSTRAP_SERVERS=somaagent_kafka:29092

# Optional policy/authorization services (enabled in this compose)
SA01_OPA_URL=http://somaagent_opa:8181
SA01_SPICEDB_HOST=somaagent_spicedb
SA01_SPICEDB_PORT=50051

# SomaBrain (leave empty in standalone; set when SomaBrain is deployed)
# SA01_SOMA_BASE_URL=http://somaagent_mock_brain:9696
SOMA_AAAS_MODE=false
SOMABRAIN_ENABLED=false
FRACTALMEMORY_ENABLED=false
```

- [ ] **Step 2: Validate compose config**

Run:
```bash
cd /Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgent01/infra/standalone
cp .env.example .env
docker compose config > /dev/null
```

Expected: no required-var errors.

- [ ] **Step 3: Commit**

```bash
git add infra/standalone/.env.example
git commit -m "chore(infra): runnable standalone .env template with safe defaults"
```

---

## Phase 1 — Make the backend functional in standalone

### Task 4: Add missing infrastructure services to standalone compose

**Files:**
- Modify: `infra/standalone/docker-compose.yml`
- Test: `docker compose up -d somaagent_postgres somaagent_redis somaagent_keycloak somaagent_kafka somaagent_opa somaagent_spicedb` starts all services.

**Why:** OPA, SpiceDB, and Kafka are referenced by the backend/workers but not defined in standalone compose.

- [ ] **Step 1: Append services to `infra/standalone/docker-compose.yml`**

Add after the `somaagent_mock_memory` service (or before, order does not matter):

```yaml
  # ===========================================================================
  # 9. KAFKA (Redpanda single-node for standalone)
  # ===========================================================================
  somaagent_kafka:
    container_name: somaagent_kafka
    image: docker.redpanda.com/redpandadata/redpanda:v24.1.1
    command:
      - redpanda
      - start
      - --smp 1
      - --memory 1G
      - --reserve-memory 0M
      - --overprovisioned
      - --node-id 0
      - --check=false
      - --kafka-addr internal://0.0.0.0:29092,external://0.0.0.0:9092
      - --advertise-kafka-addr internal://somaagent_kafka:29092,external://localhost:29092
    ports:
      - "29092:29092"
    networks:
      - somaagent_net
    healthcheck:
      test: ["CMD", "rpk", "cluster", "health"]
      interval: 10s
      timeout: 5s
      retries: 10

  # ===========================================================================
  # 10. OPA (Open Policy Agent)
  # ===========================================================================
  somaagent_opa:
    container_name: somaagent_opa
    image: openpolicyagent/opa:0.64.1-static
    command:
      - run
      - --server
      - --addr=:8181
      - --log-level=info
    ports:
      - "20818:8181"
    networks:
      - somaagent_net
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:8181/health"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ===========================================================================
  # 11. SPICEDB (Authorization datastore)
  # ===========================================================================
  somaagent_spicedb:
    container_name: somaagent_spicedb
    image: authzed/spicedb:v1.33.0
    command:
      - serve
      - --grpc-preshared-key=standalonedev-change-me
      - --datastore-engine=memory
    ports:
      - "20551:50051"
    networks:
      - somaagent_net
    healthcheck:
      test: ["CMD", "grpc_health_probe", "-addr=:50051"]
      interval: 10s
      timeout: 5s
      retries: 10
```

- [ ] **Step 2: Wire depends_on for the gateway**

In `somaagent_standalone.depends_on`, add:

```yaml
    depends_on:
      somaagent_vault:
        condition: service_healthy
      somaagent_postgres:
        condition: service_healthy
      somaagent_redis:
        condition: service_healthy
      somaagent_keycloak:
        condition: service_started
      somaagent_kafka:
        condition: service_healthy
      somaagent_opa:
        condition: service_healthy
      somaagent_spicedb:
        condition: service_healthy
```

- [ ] **Step 3: Validate and start infra**

Run:
```bash
cd /Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgent01/infra/standalone
docker compose config > /dev/null
docker compose up -d somaagent_postgres somaagent_redis somaagent_keycloak somaagent_kafka somaagent_opa somaagent_spicedb
```

Expected: all containers reach healthy/running state (`docker compose ps`).

- [ ] **Step 4: Commit**

```bash
git add infra/standalone/docker-compose.yml
git commit -m "feat(infra): add kafka, opa and spicedb to standalone compose"
```

---

### Task 5: Add worker services to standalone compose

**Files:**
- Modify: `infra/standalone/docker-compose.yml`
- Modify: `infra/standalone/start.sh` (wait script can be reused; workers use the same image)
- Test: `docker compose up -d somaagent_conversation_worker` and logs show it connected to Kafka.

**Why:** Background chat/tool/delegation/memory processing is not orchestrated.

- [ ] **Step 1: Add worker service definitions**

Append to `infra/standalone/docker-compose.yml`:

```yaml
  # ===========================================================================
  # 12. CONVERSATION WORKER
  # ===========================================================================
  somaagent_conversation_worker:
    container_name: somaagent_conversation_worker
    build:
      context: ../../
      dockerfile: infra/standalone/Dockerfile
    env_file:
      - .env
    environment:
      - SA01_DEPLOYMENT_MODE=STANDALONE
      - SA01_WORKER_GATEWAY_BASE=http://somaagent_standalone:9000
    networks:
      - somaagent_net
    depends_on:
      somaagent_postgres:
        condition: service_healthy
      somaagent_redis:
        condition: service_healthy
      somaagent_kafka:
        condition: service_healthy
      somaagent_opa:
        condition: service_healthy
      somaagent_spicedb:
        condition: service_healthy
      somaagent_standalone:
        condition: service_started
    command: ["python", "-m", "services.conversation_worker.main"]
    restart: unless-stopped

  # ===========================================================================
  # 13. TOOL EXECUTOR
  # ===========================================================================
  somaagent_tool_executor:
    container_name: somaagent_tool_executor
    build:
      context: ../../
      dockerfile: infra/standalone/Dockerfile
    env_file:
      - .env
    environment:
      - SA01_DEPLOYMENT_MODE=STANDALONE
    networks:
      - somaagent_net
    depends_on:
      somaagent_postgres:
        condition: service_healthy
      somaagent_redis:
        condition: service_healthy
      somaagent_kafka:
        condition: service_healthy
      somaagent_opa:
        condition: service_healthy
      somaagent_spicedb:
        condition: service_healthy
      somaagent_standalone:
        condition: service_started
    command: ["python", "-m", "services.tool_executor.main"]
    restart: unless-stopped

  # ===========================================================================
  # 14. DELEGATION WORKER
  # ===========================================================================
  somaagent_delegation_worker:
    container_name: somaagent_delegation_worker
    build:
      context: ../../
      dockerfile: infra/standalone/Dockerfile
    env_file:
      - .env
    environment:
      - SA01_DEPLOYMENT_MODE=STANDALONE
    networks:
      - somaagent_net
    depends_on:
      somaagent_postgres:
        condition: service_healthy
      somaagent_redis:
        condition: service_healthy
      somaagent_kafka:
        condition: service_healthy
      somaagent_standalone:
        condition: service_started
    command: ["python", "-m", "services.delegation_worker.main"]
    restart: unless-stopped

  # ===========================================================================
  # 15. MEMORY REPLICATOR
  # ===========================================================================
  somaagent_memory_replicator:
    container_name: somaagent_memory_replicator
    build:
      context: ../../
      dockerfile: infra/standalone/Dockerfile
    env_file:
      - .env
    environment:
      - SA01_DEPLOYMENT_MODE=STANDALONE
    networks:
      - somaagent_net
    depends_on:
      somaagent_postgres:
        condition: service_healthy
      somaagent_redis:
        condition: service_healthy
      somaagent_kafka:
        condition: service_healthy
      somaagent_standalone:
        condition: service_started
    command: ["python", "-m", "services.memory_replicator.main"]
    restart: unless-stopped
```

- [ ] **Step 2: Validate and start workers**

Run:
```bash
cd /Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgent01/infra/standalone
docker compose up -d somaagent_conversation_worker somaagent_tool_executor somaagent_delegation_worker somaagent_memory_replicator
```

Expected: workers start without crashing; `docker compose logs -f somaagent_conversation_worker` shows Kafka connection attempts (no immediate traceback).

- [ ] **Step 3: Commit**

```bash
git add infra/standalone/docker-compose.yml
git commit -m "feat(infra): orchestrate backend workers in standalone compose"
```

---

### Task 6: Wire real health checkers into `HealthMonitor`

**Files:**
- Create: `services/common/health_checkers.py`
- Modify: `services/gateway/main.py` (or `services/gateway/asgi.py` if it exists)
- Test: `pytest tests/unit/services/common/test_health_monitor.py` after writing a test, or call `/api/v2/core/health` and confirm SomaBrain/Database/LLM are not permanently degraded.

**Why:** `HealthMonitor` starts `somabrain`, `database`, and `llm` as `healthy=False` and no code registers checkers. Chat falls into permanent degraded governor mode.

- [ ] **Step 1: Create `services/common/health_checkers.py`**

```python
"""Default health checkers for HealthMonitor."""

from __future__ import annotations

import logging
import time
from typing import Any

from django.db import connection

from services.common.health_monitor import HealthCheck

logger = logging.getLogger(__name__)


def _safe_settings_value(name: str) -> Any:
    try:
        from django.conf import settings
        return getattr(settings, name, None)
    except Exception as exc:
        logger.debug("Could not read setting %s: %s", name, exc)
        return None


def check_database() -> HealthCheck:
    """Ping PostgreSQL via Django connection."""
    start = time.monotonic()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return HealthCheck(healthy=True, latency_ms=(time.monotonic() - start) * 1000)
    except Exception as exc:
        return HealthCheck(healthy=False, latency_ms=(time.monotonic() - start) * 1000, error=str(exc))


def check_somabrain() -> HealthCheck:
    """Ping SomaBrain HTTP /health when configured."""
    import httpx

    start = time.monotonic()
    url = _safe_settings_value("SOMABRAIN_URL") or ""
    if not url:
        return HealthCheck(healthy=True, latency_ms=0.0, error="SomaBrain not configured")
    try:
        response = httpx.get(f"{url}/health", timeout=5.0)
        response.raise_for_status()
        return HealthCheck(healthy=True, latency_ms=(time.monotonic() - start) * 1000)
    except Exception as exc:
        return HealthCheck(healthy=False, latency_ms=(time.monotonic() - start) * 1000, error=str(exc))


def check_llm() -> HealthCheck:
    """Check that an LLM provider key / base URL is configured."""
    start = time.monotonic()
    api_key = _safe_settings_value("OPENAI_API_KEY") or _safe_settings_value("GROQ_API_KEY") or _safe_settings_value("ANTHROPIC_API_KEY")
    base_url = _safe_settings_value("SA01_LLM_BASE_URL")
    if api_key or base_url:
        return HealthCheck(healthy=True, latency_ms=(time.monotonic() - start) * 1000)
    return HealthCheck(
        healthy=False,
        latency_ms=(time.monotonic() - start) * 1000,
        error="No LLM provider key or base URL configured",
    )
```

- [ ] **Step 2: Register checkers at gateway startup**

In `services/gateway/main.py`, after `django.setup()`:

```python
# Register production health checkers
from services.common.health_checkers import check_database, check_llm, check_somabrain
from services.common.health_monitor import get_health_monitor

monitor = get_health_monitor()
monitor.register_health_checker("database", check_database)
monitor.register_health_checker("somabrain", check_somabrain)
monitor.register_health_checker("llm", check_llm)
```

If `services/gateway/asgi.py` is the real startup file used by `start.sh`, add the same registration there. Verify by reading `services/gateway/asgi.py`.

- [ ] **Step 3: Add a unit test**

Create `tests/unit/services/common/test_health_checkers.py`:

```python
import pytest

from services.common.health_checkers import check_database, check_llm, check_somabrain


@pytest.mark.django_db
def test_check_database_healthy():
    result = check_database()
    assert result.healthy is True


def test_check_somabrain_unconfigured_is_healthy():
    """When SomaBrain URL is not set, the checker reports healthy (disabled)."""
    result = check_somabrain()
    assert result.healthy is True
    assert "not configured" in (result.error or "").lower()


def test_check_llm_unhealthy_without_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from django.conf import settings as django_settings
    monkeypatch.setattr(django_settings, "OPENAI_API_KEY", None)
    monkeypatch.setattr(django_settings, "GROQ_API_KEY", None)
    monkeypatch.setattr(django_settings, "ANTHROPIC_API_KEY", None)
    monkeypatch.setattr(django_settings, "SA01_LLM_BASE_URL", None)

    result = check_llm()
    assert result.healthy is False
```

- [ ] **Step 4: Run tests**

Run:
```bash
cd /Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgent01
.venv/bin/pytest tests/unit/services/common/test_health_checkers.py -v
```

Expected: tests pass.

- [ ] **Step 5: Commit**

```bash
git add services/common/health_checkers.py services/gateway/main.py tests/unit/services/common/test_health_checkers.py
git commit -m "feat(health): register real database, somabrain and llm health checkers"
```

---

### Task 7: Ensure the gateway health endpoint is meaningful

**Files:**
- Modify: `admin/aaas/api/health.py`
- Test: `curl http://localhost:20020/api/v2/core/health` returns accurate status.

**Why:** `check_keycloak()` and `check_somabrain()` use `settings.KEYCLOAK_URL` and `settings.SOMABRAIN_URL` with "no fallback - fail fast". In standalone `SOMABRAIN_URL` is empty, so the endpoint raises an exception.

- [ ] **Step 1: Guard empty URLs in health check functions**

In `admin/aaas/api/health.py`, update `check_keycloak()`:

```python
async def check_keycloak() -> ServiceHealth:
    """Check Keycloak IAM health."""
    start = datetime.now()
    keycloak_url = getattr(settings, "KEYCLOAK_URL", None)
    if not keycloak_url:
        return ServiceHealth(
            name="Keycloak",
            status="degraded",
            message="Not configured",
            last_check=timezone.now().isoformat(),
        )
    # ... rest of existing logic ...
```

Update `check_somabrain()`:

```python
async def check_somabrain() -> ServiceHealth:
    """Check SomaBrain cognitive service health."""
    start = datetime.now()
    somabrain_url = getattr(settings, "SOMABRAIN_URL", None)
    if not somabrain_url:
        return ServiceHealth(
            name="SomaBrain",
            status="degraded",
            message="Not configured",
            last_check=timezone.now().isoformat(),
        )
    # ... rest of existing logic ...
```

- [ ] **Step 2: Run the platform health endpoint locally**

Start the gateway (or run inside the container):

```bash
cd /Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgent01
SA01_DEPLOYMENT_MODE=STANDALONE SOMABRAIN_ENABLED=false .venv/bin/python manage.py runserver 0.0.0.0:9000
```

In another shell:
```bash
curl -s http://localhost:9000/api/v2/core/health | .venv/bin/python -m json.tool
```

Expected: JSON response with status `degraded` or `healthy`, not a 500 error.

- [ ] **Step 3: Commit**

```bash
git add admin/aaas/api/health.py
git commit -m "fix(health): handle unconfigured keycloak/somabrain in platform health endpoint"
```

---

## Phase 2 — SomaBrain connection readiness

### Task 8: Align SomaBrain configuration to a single env var

**Files:**
- Modify: `services/gateway/settings.py` (read the SomaBrain URL section)
- Modify: `infra/k8s/somaagent/deployment.yaml`
- Modify: `.env.example`
- Modify: `docs/operations/SOMA-OPS-MODES-001.md`
- Test: `SA01_SOMA_BASE_URL=http://somabrain.example.com:9696 .venv/bin/python -c "from django.conf import settings; print(settings.SOMABRAIN_URL)"`

**Why:** `SA01_SOMA_BASE_URL`, `SOMABRAIN_URL`, ports 9696/63996/30101, and `SOMABRAIN_ENABLED` are used inconsistently.

- [ ] **Step 1: Standardize on `SA01_SOMA_BASE_URL` in `services/gateway/settings.py`**

Ensure settings contains:

```python
SOMABRAIN_URL = get_optional_env("SA01_SOMA_BASE_URL", "", "SomaBrain cognitive runtime HTTP endpoint")
SOMABRAIN_ENABLED = get_optional_env("SOMABRAIN_ENABLED", "false").lower() == "true"
SOMA_AAAS_MODE = get_optional_env("SOMA_AAAS_MODE", "false").lower() == "true"
```

If `SOMABRAIN_URL` is also read elsewhere, prefer `SA01_SOMA_BASE_URL` and keep `SOMABRAIN_URL` only as a fallback for backwards compatibility.

- [ ] **Step 2: Update K8s manifest env**

In `infra/k8s/somaagent/deployment.yaml`, replace:

```yaml
- name: SOMABRAIN_URL
  value: "http://somabrain.brain.svc.cluster.local:63996"
```

with:

```yaml
- name: SA01_SOMA_BASE_URL
  value: "http://somabrain.brain.svc.cluster.local:9696"
- name: SOMA_AAAS_MODE
  value: "false"
```

- [ ] **Step 3: Update `.env.example`**

Replace the misleading `SA01_SOMA_BASE_URL=http://localhost:8000` line with:

```bash
# SomaBrain (leave empty in standalone; set when deployed)
# SA01_SOMA_BASE_URL=http://localhost:9696
SOMA_AAAS_MODE=false
SOMABRAIN_ENABLED=false
```

- [ ] **Step 4: Update deployment docs**

In `docs/operations/SOMA-OPS-MODES-001.md`, add a standalone-to-somabrain section:

```markdown
### Connecting Standalone mode to a deployed SomaBrain

1. Ensure SomaBrain exposes `/health`, `/memory/remember`, `/memory/recall`, `/memory/forget`, `/v1/context/evaluate`, `/neuromodulators`, `/cognitive/act`, `/brain/sleep` on its HTTP port.
2. In `infra/standalone/.env`, uncomment and set:
   ```bash
   SA01_SOMA_BASE_URL=http://<somabrain-host>:9696
   SOMABRAIN_ENABLED=true
   ```
3. Restart the agent containers:
   ```bash
   docker compose up -d
   ```
4. Verify connectivity:
   ```bash
   curl http://localhost:20020/api/v2/core/health/somabrain
   ```
```

- [ ] **Step 5: Commit**

```bash
git add services/gateway/settings.py infra/k8s/somaagent/deployment.yaml .env.example docs/operations/SOMA-OPS-MODES-001.md
git commit -m "chore(config): standardize SomaBrain URL on SA01_SOMA_BASE_URL"
```

---

### Task 9: Guard BrainBridge direct-mode access in SomaBrainClient

**Files:**
- Modify: `admin/core/somabrain_client.py`
- Modify: `aaas/brain.py`
- Test: `.venv/bin/pytest tests/saas/test_brain_bridge.py -v`

**Why:** `SomaBrainClient.remember()`/`recall()` check `BrainBridge.mode == "direct"`. In standalone `SOMA_AAAS_MODE=false`, `BrainBridge` initializes in HTTP mode pointing to `somastack_aaas:9696`, which is wasted overhead and can raise if the `somabrain` package is missing.

- [ ] **Step 1: Make `BrainBridge` safe to import/inspect without initializing**

In `aaas/brain.py`, add a module-level helper:

```python
# Set to True only when the somabrain package is available and AAAS mode is requested
_CAN_DIRECT = False

if AAAS_MODE:
    try:
        import somabrain  # noqa: F401
        _CAN_DIRECT = True
    except ImportError:
        logger.warning("AAAS mode requested but somabrain package not available; direct bridge disabled")
```

Then in `BrainBridge.__init__`:

```python
    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        if AAAS_MODE and _CAN_DIRECT:
            self._init_direct()
        else:
            self._init_http()
```

- [ ] **Step 2: In `SomaBrainClient`, only consider direct mode when AAAS mode is active**

In `admin/core/somabrain_client.py`, at module top:

```python
from services.common.deployment_mode import DeploymentMode
_AAAS_MODE = DeploymentMode.is_aaas()
```

In `remember()` and `recall()`, change:

```python
if HAS_BRIDGE and BrainBridge is not None and BrainBridge.mode == "direct":
```

to:

```python
if _AAAS_MODE and HAS_BRIDGE and BrainBridge is not None and getattr(BrainBridge, "mode", None) == "direct":
```

This prevents standalone from instantiating the bridge and forces HTTP mode when SomaBrain is configured.

- [ ] **Step 3: Run tests**

```bash
cd /Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgent01
.venv/bin/pytest tests/saas/test_brain_bridge.py -v
```

Expected: tests pass.

- [ ] **Step 4: Commit**

```bash
git add aaas/brain.py admin/core/somabrain_client.py
git commit -m "fix(brain): guard direct-mode bridge so standalone uses HTTP SomaBrain"
```

---

### Task 10: Update the mock SomaBrain to expose real client endpoints

**Files:**
- Modify: `infra/mocks/somabrain/main.py`
- Modify: `infra/mocks/somabrain/Dockerfile` (if needed)
- Test: `docker compose --profile mocks up -d` then `curl http://localhost:20996/health`.

**Why:** The mock exposes `/api/health/` and `/api/v1/agents/...`, but the client calls `/health`, `/memory/remember`, etc. The mock cannot validate the integration.

- [ ] **Step 1: Add the endpoints the client expects**

In `infra/mocks/somabrain/main.py`, ensure the FastAPI/Flask app exposes at least:

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok", "ready": True}

@app.post("/memory/remember")
def remember(request: Request):
    body = request.json() if hasattr(request, "json") else {}
    return {"status": "success", "coordinate": [0.0, 0.0, 0.0], "memory_id": "mock-1"}

@app.post("/memory/recall")
def recall(request: Request):
    return {"memories": []}

@app.delete("/memory/forget")
def forget():
    return {"status": "ok"}

@app.post("/v1/context/evaluate")
def context_evaluate():
    return {"memories": [], "scores": []}

@app.get("/neuromodulators")
def get_neuromodulators():
    return {"dopamine": 0.5, "serotonin": 0.5}

@app.post("/cognitive/act")
def cognitive_act():
    return {"result": "mock action"}
```

Remove or keep the old `/api/health/` and `/api/v1/agents/...` routes for backwards compatibility.

- [ ] **Step 2: Test the mock with the client**

Run:
```bash
cd /Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgent01/infra/standalone
docker compose --profile mocks up -d somaagent_mock_brain
sleep 5
curl -s http://localhost:20996/health
curl -s -X POST http://localhost:20996/memory/remember -H "Content-Type: application/json" -d '{"key":"k","value":"v","tenant":"default","namespace":"wm"}'
```

Expected: both return 200 with JSON.

- [ ] **Step 3: Commit**

```bash
git add infra/mocks/somabrain/main.py
git commit -m "feat(mocks): align mock somabrain endpoints with SomaBrainClient contract"
```

---

## Phase 3 — Production hardening

### Task 11: Add a Tiltfile for local cluster development

**Files:**
- Create: `infra/tilt/Tiltfile`
- Create: `infra/k8s/shared/namespace-agent.yaml`
- Test: `tilt up` from `infra/tilt/` starts services.

**Why:** `infra/tilt/` only contains `.env`; the Tilt workflow cannot run.

- [ ] **Step 1: Create `infra/tilt/Tiltfile`**

```python
# SOMAAGENT01 local cluster development

allow_k8s_contexts('docker-desktop')  # adjust to your cluster name

k8s_yaml('../k8s/shared/namespace-agent.yaml')
k8s_yaml('../k8s/shared/postgres.yaml')
k8s_yaml('../k8s/shared/redis.yaml')
k8s_yaml('../k8s/shared/keycloak.yaml')
k8s_yaml('../k8s/somaagent/deployment.yaml')
k8s_yaml('../k8s/somaagent/service.yaml')

docker_build('somaagent/somaagent', '../../', dockerfile='../../infra/standalone/Dockerfile')

k8s_resource('somaagent-postgres', port_forwards='20432:5432')
k8s_resource('somaagent-redis', port_forwards='20379:6379')
k8s_resource('somaagent-keycloak', port_forwards='20880:8080')
k8s_resource('somaagent', port_forwards='20020:9000')
```

- [ ] **Step 2: Create namespace manifest**

Create `infra/k8s/shared/namespace-agent.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: agent
```

- [ ] **Step 3: Commit**

```bash
git add infra/tilt/Tiltfile infra/k8s/shared/namespace-agent.yaml
git commit -m "feat(infra): add Tiltfile for local cluster development"
```

---

### Task 12: Fix CORS / static files / security for the WebUI

**Files:**
- Modify: `services/gateway/settings.py` (add `django-cors-headers` or same-origin note)
- Modify: `.dockerignore` (if backend must serve `webui/dist`)
- Test: frontend loads at `http://localhost:20080` and API calls succeed.

**Why:** No CORS middleware is configured. If the WebUI is served from a different origin, API calls are blocked. Also, `.dockerignore` excludes `webui/dist`, which conflicts with `STATICFILES_DIRS` pointing there.

- [ ] **Step 1: Add `django-cors-headers` to requirements and settings**

In `requirements.txt`:

```
django-cors-headers>=4.3
```

In `services/gateway/settings.py`:

```python
INSTALLED_APPS = [
    # ... existing apps ...
    "corsheaders",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    # ... existing middleware ...
]

CORS_ALLOWED_ORIGINS = os.environ.get("SA01_CORS_ALLOWED_ORIGINS", "").split(",") if os.environ.get("SA01_CORS_ALLOWED_ORIGINS") else []
CORS_ALLOW_CREDENTIALS = True
```

- [ ] **Step 2: Document that the recommended production layout uses the nginx proxy**

Add a comment in `webui/nginx.conf`:

```nginx
# This proxy makes the UI same-origin with /api/ and /ws/, avoiding CORS.
# If you serve the UI from a different origin, set SA01_CORS_ALLOWED_ORIGINS.
```

- [ ] **Step 3: Commit**

```bash
git add requirements.txt services/gateway/settings.py webui/nginx.conf
git commit -m "feat(gateway): add CORS support for standalone deployments"
```

---

## Smoke Test Checklist (run after all tasks)

- [ ] `docker compose up -d` in `infra/standalone/` starts all containers without crash loops.
- [ ] `curl http://localhost:20020/api/health/` returns 200.
- [ ] `curl http://localhost:20020/api/v2/core/health` returns JSON with no 500.
- [ ] `curl http://localhost:20080/health` returns 200.
- [ ] `/login` page loads at `http://localhost:20080/login` and the Keycloak authorize URL points to `http://localhost:20080/auth/...`.
- [ ] `/chat` page loads and the WebSocket handshake to `/ws/v2/chat/<capsule_id>` succeeds.
- [ ] With `SA01_SOMA_BASE_URL=http://somaagent_mock_brain:9696` and `--profile mocks`, `/api/v2/core/health/somabrain` reports healthy.
- [ ] `.venv/bin/pytest tests/saas/test_brain_bridge.py tests/unit tests/django tests/test_deployment_mode_unified.py -q` passes.

---

## Self-Review

- **Spec coverage:** every audit blocker is mapped to a task: frontend proxy (Task 1), frontend runtime config (Task 2), env template (Task 3), infra services (Task 4), workers (Task 5), health monitor wiring (Task 6), platform health endpoint (Task 7), SomaBrain config alignment (Task 8), direct-mode guard (Task 9), mock endpoints (Task 10), Tilt (Task 11), CORS/security (Task 12).
- **Placeholder scan:** no `TBD`, `TODO`, or vague steps remain. Each step contains file paths, code blocks, and exact commands.
- **Type consistency:** `SA01_SOMA_BASE_URL` is used consistently as the canonical SomaBrain URL across settings, env templates, K8s, and docs.
