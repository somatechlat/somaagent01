# Code vs Roadmap Comparison Report

**Generated:** December 9, 2025
**Status:** Architecture Refactor COMPLETE, Canonical Cleanup IN PROGRESS

---

## Architecture Refactor Results (COMPLETE ✅)

| File | Original | Current | Target | Reduction | Status |
|------|----------|---------|--------|-----------|--------|
| `agent.py` | 4092 | 400 | < 500 | 90% | ✅ COMPLETE |
| `services/conversation_worker/main.py` | 3022 | 178 | < 200 | 94% | ✅ COMPLETE |
| `python/helpers/settings.py` | 1793 | 610 | < 700 | 66% | ✅ COMPLETE |
| `python/helpers/task_scheduler.py` | 1276 | 284 | < 300 | 78% | ✅ COMPLETE |
| `python/helpers/mcp_handler.py` | 1087 | 319 | < 350 | 71% | ✅ COMPLETE |
| `python/helpers/memory.py` | 1010 | 348 | < 400 | 66% | ✅ COMPLETE |
| `python/tasks/core_tasks.py` | 764 | 215 | < 300 | 72% | ✅ COMPLETE |
| `services/tool_executor/main.py` | 748 | 147 | < 150 | 80% | ✅ COMPLETE |
| `services/gateway/main.py` | 438 | 97 | < 100 | 78% | ✅ COMPLETE |
| **TOTAL** | **14,230** | **2,598** | - | **82%** | ✅ |

---

## VIBE Violations Cleanup (COMPLETE ✅)

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Delete voice stub files | ✅ | `src/voice/openai_client.py` DELETED |
| Delete OPA placeholder | ✅ | `integrations/opa.py` DELETED |
| Delete gateway router placeholders | ✅ | `routers/tools.py`, `routers/auth.py` DELETED |
| Delete degradation monitor shim | ✅ | `services/common/degradation_monitor.py` DELETED |
| Remove RequeueStore in-memory fallback | ✅ | Uses Redis only |
| Fix speech router fake transcription | ✅ | Returns 501 Not Implemented |
| Fix circuit breaker NotImplementedError | ✅ | Real PostgreSQL implementation |
| Fix DLQ store stub methods | ✅ | Real Kafka reprocessing |

---

## Canonical Architecture Cleanup Status

### persist_chat Cleanup

| File | Roadmap Says | Actual Code | Status |
|------|--------------|-------------|--------|
| `python/helpers/persist_chat.py` | DELETE | DELETED | ✅ |
| `python/helpers/task_scheduler.py` | Remove import | Uses `session_store_adapter` | ✅ |
| `python/tools/browser_agent.py` | Remove import | Uses `session_store_adapter` | ✅ |
| `python/tools/scheduler.py` | Remove import | Uses `session_store_adapter` | ✅ |

### Skeleton Router Cleanup (JUST COMPLETED)

| File | Roadmap Says | Action Taken | Status |
|------|--------------|--------------|--------|
| `services/gateway/routers/chat.py` | DELETE (skeleton) | DELETED | ✅ |
| `services/gateway/routers/memory.py` | DELETE (skeleton) | DELETED | ✅ |
| `services/gateway/routers/uploads.py` | DELETE (skeleton) | DELETED | ✅ |
| `services/gateway/routers/__init__.py` | Update imports | UPDATED | ✅ |

### Dead Code Cleanup (JUST COMPLETED)

| File | Issue | Action Taken | Status |
|------|-------|--------------|--------|
| `clean_agent.py` | 904 lines, never imported | DELETED | ✅ |

---

## Celery Architecture Status

| Requirement | Roadmap Target | Actual Code | Status |
|-------------|----------------|-------------|--------|
| Celery app location | `python/tasks/celery_app.py` | ✅ Exists | ✅ |
| Beat schedule | Configure in celery_app.py | ✅ Configured | ✅ |
| Task routes | Define queue routing | ✅ Configured | ✅ |
| Visibility timeout | 7200 seconds | ✅ Set | ✅ |
| Core tasks | build_context, evaluate_policy, etc. | ✅ All exist | ✅ |
| Prometheus metrics | Task counters/histograms | ✅ Implemented | ✅ |
| OPA integration | Policy checks in tasks | ✅ `_enforce_policy()` | ✅ |
| Dedupe pattern | Redis SETNX | ✅ `_dedupe_once()` | ✅ |

---

## Files Still Over 500 Lines (Need Decomposition)

| File | Lines | Priority | Notes |
|------|-------|----------|-------|
| `models.py` | 1245 | P2 | Data models - may be acceptable |
| `python/helpers/backup.py` | 920 | P2 | Backup logic |
| `python/integrations/soma_client.py` | 908 | P1 | SomaBrain client |
| `python/helpers/memory_consolidation.py` | 805 | P2 | Memory consolidation |
| `observability/metrics.py` | 778 | P2 | Metrics definitions |
| `services/common/session_repository.py` | 681 | P2 | Session store |
| `python/helpers/document_query.py` | 648 | P2 | Document querying |
| `python/helpers/settings.py` | 610 | P3 | Already decomposed |
| `python/helpers/rfc_files.py` | 603 | P2 | RFC file handling |
| `python/observability/metrics.py` | 592 | P2 | Duplicate metrics? |
| `services/gateway/circuit_endpoints.py` | 581 | P2 | Circuit breaker endpoints |
| `python/helpers/history.py` | 555 | P2 | History management |

---

## Summary

### Completed Today
1. ✅ Deleted skeleton routers: `chat.py`, `memory.py`, `uploads.py`
2. ✅ Updated `routers/__init__.py` to remove deleted imports
3. ✅ Deleted dead code: `clean_agent.py` (904 lines, never imported)
4. ✅ Updated `test_file_sizes.py` to remove clean_agent.py reference

### Architecture Refactor: 100% COMPLETE
- 82% total code reduction achieved
- All target files under limits
- Domain ports and adapters created
- Use cases implemented
- Pre-commit hook for file sizes

### Canonical Cleanup: ~70% COMPLETE
- persist_chat fully removed
- Skeleton routers deleted
- Celery architecture configured
- Settings consolidation partial (5→1 still in progress)
- 12 files still over 500 lines

### Next Priority Tasks
1. Settings consolidation (5 systems → 1 `cfg` facade)
2. Decompose `soma_client.py` (908 lines)
3. Decompose `models.py` (1245 lines)
4. UI-Backend endpoint alignment
