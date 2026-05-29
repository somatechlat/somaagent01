# MASTER FIX TODO — SOMA Agent 01

> VIBE Coding Rules enforced: NO mocks, NO placeholders, NO TODOs in code, NO hardcoded secrets
> 7 Personas: PhD Dev, PhD Analyst, PhD QA, ISO Documenter, Security Auditor, Performance Engineer, UX Consultant

## RULES
- LLM unavailable = **HARD FAIL** (user must know)
- SomaBrain unavailable = **SOFT DEGRADE** (agent works 100%, no cognitive functions)
- Every fix must compile and be production-grade
- No new files unless absolutely unavoidable

---

## PHASE 1: FIX BROKEN CODE (Import/Startup Crashes)

| # | Item | File(s) | Status | Notes |
|---|------|---------|--------|-------|
| 1.7 | Add OPA to simple AAAS docker-compose | `infra/aaas/docker-compose.yml` | 🔲 | Missing service, causes startup crash |
| 1.8 | Add Temporal + SpiceDB to full AAAS docker-compose | `infra/aaas/aaas/docker-compose.yml` | 🔲 | Code expects them, no services |
| 1.9 | Add Kafka workers to supervisord.conf | `infra/aaas/aaas/supervisord.conf` | 🔲 | Production deploy has no consumers |
| 1.10 | Add Kafka topic provisioning script | `infra/scripts/` | 🔲 | Auto-create disabled, no topics = crash |

## PHASE 2: WIRE DEGRADATION INTO CHAT PIPELINE

| # | Item | File(s) | Status | Notes |
|---|------|---------|--------|-------|
| 2.1 | Wire SomaFractalMemory as Brain fallback | `admin/core/chat_orchestrator.py` | ✅ DONE | SFM store + recall fallback when Brain down |
| 2.2 | Wire SFM into ContextBuilder memory lane | `admin/core/context/builder.py` | ✅ DONE | `memory_client` param + `_build_memory_lane` fallback |
| 2.3 | Wire HealthMonitor into V3ChatOrchestrator | `admin/core/chat_orchestrator.py` | 🔲 | Check `is_degraded()` at start of turn |
| 2.4 | Wire SimpleGovernor token budgets | `admin/core/chat_orchestrator.py` | 🔲 | Replace hardcoded budgets with governor |
| 2.5 | SomaBrain memory → PendingMemory queue | `admin/core/chat_orchestrator.py` | 🔲 | Queue to `PendingMemory` when Brain down |
| 2.6 | EventPublisher persist failed events | `admin/core/observability/event_publisher.py` | 🔲 | File deleted from working tree — needs restore or alternative implementation |

## PHASE 3: INFRASTRUCTURE HARDENING

| # | Item | File(s) | Status | Notes |
|---|------|---------|--------|-------|
| 3.1 | Create shared Redis connection pool factory | `services/common/redis_client.py` | 🔲 | 6+ modules reinvent singleton |
| 3.2 | Wire `max_connections: 20` from config loader | `admin/core/config/loader.py` | 🔲 | Phantom config never applied |
| 3.3 | Fix `.env.example` — remove dead variables | `.env.example` | 🔲 | ~14 dead variables |
| 3.4 | Remove stale CI workflow references | `.github/workflows/` | ✅ DONE | Directory removed; stale references cleaned up |
| 3.6 | Unify Kafka libraries → `aiokafka` only | Multiple files | 🔲 | 3 libraries used inconsistently |
| 3.7 | Add Prometheus + Grafana to docker-compose | `infra/aaas/aaas/docker-compose.yml` | 🔲 | Metrics orphaned without scraper |
| 3.8 | Milvus direct health check | `services/common/health_monitor.py` | 🔲 | Only monitored via SomaBrain proxy |

## PHASE 4: ARCHITECTURE CLEANUP

| # | Item | File(s) | Status | Notes |
|---|------|---------|--------|-------|
| 4.1 | Memory system 9 entry points → single MemoryPort | Multiple files | 🔲 | Large refactor |
| 4.2 | Health/Degradation 8 impls → single model | Multiple files | 🔲 | Medium refactor |
| 4.3 | Rate limiter 3 impls → single limiter | Multiple files | 🔲 | Medium refactor |
| 4.4 | WebSocket token query string → httpOnly cookie | `webui/src/services/websocket-client.ts` | 🔲 | Security hardening |
| 4.5 | Frontend JWT localStorage → httpOnly cookie | `webui/src/stores/auth-store.ts` | 🔲 | Security hardening |
| 4.6 | Chat orchestrator test suite | `tests/unit/` | 🔲 | No mocks — real infra |
| 4.7 | Inconsistent error response formats | Multiple API files | 🔲 | API standardization |
| 4.8 | Missing OpenAPI schema annotations | `admin/*/api.py` | 🔲 | Documentation |

---

## PROGRESS TRACKER

**Phase 1**: 0/10  
**Phase 2**: 2/6  
**Phase 3**: 0/8  
**Phase 4**: 0/8  

**Total**: 2/32

### Code Verification Status (2026-05-28)
- **Pyright:** 1 error (`services/gateway/django_setup.py:53` — missing `import secrets`)
- **Tests:** 13 failed, 43 passed, 63 skipped, 5 errors
  - 8 Django tests fail: `admin.llm.models.LLMModelConfig` missing `app_label`/not in `INSTALLED_APPS`
  - 3 deployment tests fail: missing `browser_use_monkeypatch` export from `admin.core.helpers`
  - 2 Docker proof tests fail: containers not running (expected)
  - 5 SomaBrain integration errors: `somabrain` module not installed
- **Working tree:** 76 files changed (43 deleted, 33 modified) — significant drift from HEAD
