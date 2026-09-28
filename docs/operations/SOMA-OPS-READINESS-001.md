# SomaAgent01 Deployment Readiness Plan

## Document Control

| Field | Value |
|-------|-------|
| Document Title | SomaAgent01 Deployment Readiness Plan |
| Document Identifier | SOMA-PLN-001 |
| Version | 1.0.0 |
| Date | 2026-06-01 |
| Status | Pre-Production |
| Author | SomaTech Engineering |
| Classification | Internal |

## Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-06-01 | SomaTech Engineering | Initial deployment readiness assessment and plan |

---

## 1. Purpose and Scope

### 1.1 Purpose

This document provides a comprehensive assessment of the SomaAgent01 system's deployment readiness, identifies blockers, and defines the plan to achieve a testable standalone deployment.

### 1.2 Scope

This plan covers:
- Current system state assessment
- Docker deployment verification steps
- Testing strategy
- Blocker identification and resolution
- Required actions to reach testable state

This plan does not cover:
- Production deployment procedures
- Kubernetes production deployment
- AAAS mode deployment (requires external repositories)

---

## 2. Normative References

| Document | Identifier | Location |
|----------|------------|----------|
| Project Overview | SOMA-DOC-001 | `README.md` |
| Agent Knowledge Base | SOMA-DOC-002 | `AGENT.md` |
| Comprehensive Audit Report | SOMA-AUDIT-001 | `SOMA_AGENT01_COMPREHENSIVE_AUDIT_REPORT.md` |
| Standalone Docker Compose | SOMA-INF-001 | `infra/standalone/docker-compose.yml` |
| Standalone Dockerfile | SOMA-INF-002 | `infra/standalone/Dockerfile` |

---

## 3. Current System State

### 3.1 Maturity Assessment

| Category | Score | Maximum | Notes |
|----------|-------|---------|-------|
| Architecture | 7.0 | 10 | Clean separation, good patterns |
| Implementation | 5.5 | 10 | Many stubs and bypasses |
| Test Coverage | 2.0 | 10 | 1.6% test-to-source ratio |
| Documentation | 4.0 | 10 | Severe drift from code (being corrected) |
| Security | 5.5 | 10 | Auth works; `UnifiedGate` authz now makes real OPA/SpiceDB calls; some RBAC endpoints still stubbed |
| Deployment | 6.0 | 10 | Standalone works; Makefile broken |
| **Overall** | **5.1** | **10** | **Pre-production** |

### 3.2 What Works Now

1. **Standalone Docker Compose** (`infra/standalone/docker-compose.yml`)
   - Builds and runs Agent-only stack
   - Includes PostgreSQL, Redis, Keycloak, Vault
   - Health checks configured
   - Non-root container user

2. **Authentication**
   - Keycloak OIDC integration is functional
   - JWT validation works
   - Login page implemented

3. **Core API**
   - 40+ Django Ninja routers mounted
   - Health endpoint responds
   - WebSocket consumer exists

4. **Infrastructure Code**
   - Event bus with Kafka tracing
   - Circuit breaker implementation
   - Health monitor
   - Settings registry

### 3.3 What Is Broken or Missing

1. **Makefile** -- References non-existent Dockerfiles (`Dockerfile.gateway`, `Dockerfile.worker`, `Dockerfile.analyzer`)
2. **Root docker-compose.yml exists** -- `docker-compose.yml` is present at project root
3. **Authorization** -- `UnifiedGate` now makes real OPA/SpiceDB calls; some high-level RBAC API endpoints still return stubs
4. **Chat Pipeline** -- V3 orchestrator is the WebSocket/REST production path; conversation worker still uses a separate use-case pipeline
5. **BrainBridge** -- `recall()` is implemented for direct and HTTP modes
6. **Test Coverage** -- 24 test files for ~570 source files
7. **pyproject.toml** -- References `somabrain` as `../somabrain` path dependency
8. **WebUI** -- `webui/Dockerfile` exists; `DEV_MODE = false` in `webui/src/main.ts`
9. **Image Generation Scripts** -- Fixed; generate documentation-only PNGs
10. **Frontend chat blockers** -- WebSocket URL omits required `agent_id`; chat view lacks agent selector

---

## 4. Deployment Verification

### 4.1 Standalone Stack Verification

Step 1: Build and start the stack

```bash
cd infra/standalone
cp .env.example .env
# Edit .env and set required passwords
docker compose up -d
```

Step 2: Verify service health

```bash
docker compose ps
```

Expected: All services show status `healthy` or `up`.

Step 3: Verify Agent API health

```bash
curl http://localhost:20020/api/health/
```

Expected response: `{"status": "ok", "service": "somaagent-gateway", "version": "1.0.0"}`

Step 4: Run database migrations

```bash
docker compose exec somaagent_standalone python manage.py migrate
```

Expected: Migrations apply successfully for all apps.

Step 5: Run Django system check

```bash
docker compose exec somaagent_standalone python manage.py check
```

Expected: `System check identified no issues`.

### 4.2 Test Execution Plan

Phase 1: Pure Python Unit Tests (no infrastructure)

```bash
pytest tests/unit/ -v
```

Phase 2: Django Tests (requires database)

```bash
cd infra/standalone
docker compose up -d postgres redis
cd ../..
DJANGO_SETTINGS_MODULE=services.gateway.settings pytest tests/django/ -v
```

Phase 3: Integration Tests (requires full standalone stack)

```bash
cd infra/standalone
docker compose up -d
# Wait for health
cd ../..
pytest tests/integration/ -v
```

Phase 4: SaaS Tests (requires AAAS stack -- will skip without it)

```bash
pytest tests/saas/ -v
```

---

## 5. Required Actions

### 5.1 Immediate (Required for Testing)

| ID | Action | Owner | Effort |
|----|--------|-------|--------|
| ACT-001 | Fix Makefile to reference correct paths | Engineering | 30 min |
| ACT-002 | Create `.env` from `.env.example` with test values | Operator | 15 min |
| ACT-003 | Run standalone stack and verify health | Operator | 10 min |
| ACT-004 | Run migrations inside container | Operator | 5 min |
| ACT-005 | Execute unit tests | Engineering | 5 min |
| ACT-006 | Fix `generate_somabrain_image.py` and `generate_somafractal_image.py` logger bug | Engineering | 15 min |

### 5.2 Short Term (Required for Development)

| ID | Action | Owner | Effort |
|----|--------|-------|--------|
| ACT-007 | ~~Remove `ALLOW_INSECURE_AUTH_BYPASS` from settings~~ | Security | **Done** |
| ACT-008 | ~~Remove `DEV_MODE = true` hardcoding from `webui/src/main.ts`~~ | Frontend | **Done** |
| ACT-009 | ~~Wire V3 ChatOrchestrator as production path~~ | Backend | **Done for WebSocket/REST** |
| ACT-010 | ~~Fix `BrainBridge.recall()` NotImplementedError~~ | Backend | **Done** |
| ACT-011 | ~~Containerize WebUI with nginx~~ | DevOps | **Done** |
| ACT-012 | Synchronize `requirements.txt` and `pyproject.toml` | Engineering | 1 hour |
| ACT-013 | Fix frontend WebSocket URL to include `agent_id` | Frontend | 2 hours |
| ACT-014 | Add agent selector to chat view | Frontend | 2 hours |

### 5.3 Medium Term (Required for Pre-Production)

| ID | Action | Owner | Effort |
|----|--------|-------|--------|
| ACT-013 | Implement real OPA integration | Security | 8 hours |
| ACT-014 | Implement real SpiceDB integration | Security | 8 hours |
| ACT-015 | Wire audit outbox to all endpoints | Backend | 4 hours |
| ACT-016 | Implement account lockout | Security | 2 hours |
| ACT-017 | Add PKCE to OAuth flow | Security | 2 hours |
| ACT-018 | Increase test coverage to 50% | QA | 40 hours |
| ACT-019 | Fix Pyright type errors | Engineering | 16 hours |

---

## 6. Docker Image Status

### 6.1 Existing Images

| Image Name | Dockerfile | Status | Notes |
|------------|------------|--------|-------|
| `somaagent_standalone` | `infra/standalone/Dockerfile` | Buildable | Agent-only; works |
| `somatech/soma-aaas:latest` | `infra/aaas/aaas/Dockerfile` | Buildable with siblings | Requires `../somabrain` and `../somafractalmemory` |
| `somaagent-webui` | `webui/Dockerfile` | Buildable | Nginx-served Lit frontend; `DEV_MODE=false` |

### 6.2 Missing Images

| Image Name | Required For | Blocker |
|------------|--------------|---------|
| `somatech/soma-brain:latest` | AAAS / K8s | No Dockerfile in this repo |
| `somatech/soma-memory:latest` | AAAS / K8s | No Dockerfile in this repo |
| `somaagent-gateway:latest` | Makefile target | Dockerfile does not exist |
| `somaagent-worker:latest` | Makefile target | Dockerfile does not exist |
| `somaagent-analyzer:latest` | Makefile target | Dockerfile does not exist |

### 6.3 SomaBrain and SomaFractalMemory Image Clarification

The terms "SomaBrain image" and "SomaFractalMemory image" in documentation refer to:

1. **Documentation PNG images**: `docs/deployment/images/somabrain_cognitive_dashboard.png` and `docs/deployment/images/somafractal_memory_3d_space.png`. These are static visualization assets generated by `scripts/generate_somabrain_image.py` and `scripts/generate_somafractal_image.py`. They are NOT Docker images.

2. **Docker images**: `somatech/soma-brain:latest` and `somatech/soma-memory:latest`. These are referenced in Kubernetes manifests but have no Dockerfiles in this repository. They are built from separate repositories (`somabrain` and `somafractalmemory`).

**Conclusion**: For standalone testing, only the `somaagent_standalone` image is required and available. AAAS testing requires the external repositories.

---

## 7. Success Criteria

### 7.1 Testing Success Criteria

1. Standalone stack starts with all services healthy
2. Health endpoint returns HTTP 200 with valid JSON
3. Migrations apply without errors
4. Unit tests pass: `pytest tests/unit/ -v` returns 0 exit code
5. Django tests pass: `pytest tests/django/ -v` returns 0 exit code

### 7.2 Deployment Success Criteria

1. `make up` starts the standalone stack
2. `make health` returns gateway status
3. `make test` executes tests
4. `make down` stops all services cleanly

---

## 8. Risks

| ID | Risk | Probability | Impact | Mitigation |
|----|------|-------------|--------|------------|
| RISK-001 | Standalone stack fails to start due to missing env vars | Medium | High | Provide `.env` template with clear instructions |
| RISK-002 | Tests fail due to Django settings mismatch | Medium | Medium | Standardize on `services.gateway.settings` |
| RISK-003 | Keycloak startup delays cause health check failures | Medium | Low | Health checks have retries configured |
| RISK-004 | Port conflicts on 20xxx range | Low | Medium | Document port namespace; allow override |
| RISK-005 | Missing sibling repos block AAAS testing | High | High | Clearly document standalone as primary test path |

---

## 9. Appendices

### Appendix A: Environment Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SA01_DEPLOYMENT_MODE` | Yes | `DEV` | Deployment mode: STANDALONE, AAAS, DEV |
| `SA01_DB_DSN` | Yes | None | PostgreSQL connection string |
| `SA01_REDIS_URL` | Yes | None | Redis connection string |
| `SA01_KEYCLOAK_URL` | Yes | None | Keycloak base URL |
| `SA01_JWT_SECRET` | Yes | None | JWT signing secret |
| `POSTGRES_PASSWORD` | Yes | None | PostgreSQL password |
| `KEYCLOAK_ADMIN_PASSWORD` | Yes | None | Keycloak admin password |
| `VAULT_DEV_ROOT_TOKEN_ID` | Yes | None | Vault dev root token |

### Appendix B: Port Reference

| Service | Standalone Port | AAAS Port | Protocol |
|---------|----------------|-----------|----------|
| SomaAgent API | 20020 | 63900 | HTTP |
| PostgreSQL | 20432 | 63932 | TCP |
| Redis | 20379 | 63979 | TCP |
| Keycloak | 20880 | 63980 | HTTP |
| Vault | 20882 | 63982 | HTTP |
| SomaBrain | N/A | 63996 | HTTP |
| SomaFractalMemory | N/A | 63901 | HTTP |

---

End of Document
