# SRS-650-LINE-SOVEREIGNTY

## Software Requirements Specification
### VIBE Rule 245 Enforcement Project

| **Document ID** | SRS-650-LINE-SOVEREIGNTY-2026-001 |
|-----------------|-----------------------------------|
| **Version** | 1.0.0 |
| **Date** | 2026-01-21 |
| **Status** | DRAFT — PENDING APPROVAL |
| **Classification** | Internal |
| **Standard** | ISO/IEC 29148:2018 |

---

## 1. Introduction

### 1.1 Purpose
This SRS defines requirements for enforcing **VIBE Rule 245 (Linear Sovereignty)** — the 650-line maximum per Python module — across the SOMA ecosystem.

### 1.2 Scope
| Repository | Violations | Lines Over |
|------------|------------|------------|
| SomaBrain | 14 files | +8,547 |
| SomaAgent01 | 8 files | +1,088 |
| SomaFractalMemory | 0 | ✅ COMPLIANT |

### 1.3 Definitions

| Term | Definition |
|------|------------|
| **Linear Sovereignty** | VIBE Rule 245: No module exceeds 650 lines |
| **Pattern-Based Split** | Decomposition following named design patterns |
| **Backward Compatibility** | Original import paths continue working |

---

## 2. Current Architecture Analysis

### 2.1 SomaBrain Repository Structure

```
somabrain/
├── app.py                    # 4,242 lines ❌ CRITICAL
├── memory_client.py          # 2,420 lines ❌ CRITICAL
├── settings.py               # 980 lines ❌
├── schemas.py                # 977 lines ❌
├── api/
│   └── endpoints/            # 65 files (well-organized)
│       ├── aaas_admin.py     # 796 lines ❌
│       ├── users.py          # 695 lines ❌
│       └── sso.py            # 690 lines ❌
├── aaas/
│   ├── models.py             # 1,190 lines ❌
│   ├── admin.py              # 1,040 lines ❌
│   └── auth.py               # 662 lines ❌
├── learning/
│   └── adaptation.py         # 790 lines ❌
├── settings/
│   └── base.py               # 893 lines ❌
└── common/config/
    └── settings.py           # 1,483 lines ❌
```

### 2.2 SomaAgent01 Repository Structure

```
somaAgent01/
├── admin/
│   ├── core/
│   │   ├── models.py         # 907 lines ❌
│   │   └── helpers/
│   │       ├── scheduler_models.py  # 674 lines ❌
│   │       └── memory_stores.py     # 657 lines ❌
│   ├── conversations/
│   │   └── api.py            # 756 lines ❌
│   ├── permissions/
│   │   └── granular.py       # 749 lines ❌
│   ├── voice/
│   │   └── api.py            # 681 lines ❌
│   └── flink/
│       └── api.py            # 666 lines ❌
└── services/
    └── common/
        └── chat_service.py   # DELETED
```

---

## 3. Functional Requirements

### FR-001: SomaBrain app.py Decomposition

**Current State:** 4,242 lines, 139 outline items

| Component | Lines | Target Module |
|-----------|-------|---------------|
| SimpleOPAEngine | 65-88 | `app/opa.py` |
| CognitiveMiddleware | 658-725 | `app/middleware.py` |
| CognitiveInputValidator | 728-804 | `app/validators.py` |
| SecurityMiddleware | 807-867 | `app/middleware.py` |
| UnifiedBrainCore | 2126-2247 | `core/unified_brain.py` |
| AutoScalingFractalIntelligence | 2290-2440 | `core/auto_scaling.py` |
| ComplexityDetector | 2443-2473 | `core/complexity.py` |
| Admin endpoints (20+) | 1065-1542 | `api/endpoints/admin_internal.py` |
| Memory endpoints | 2925-3599 | Already in `api/endpoints/memory*.py` |
| Health endpoints | 2549-2809 | `api/endpoints/health.py` |
| Lifecycle handlers | 4019-4242 | `app/lifecycle.py` |
| Scoring functions | 173-506 | `scoring/candidate_scoring.py` |

**Acceptance Criteria:**
- [ ] Each new module < 650 lines
- [ ] `from somabrain.app import app` still works
- [ ] All 65 existing API endpoints functional
- [ ] Health check passes: `GET /health`

---

### FR-002: SomaBrain memory_client.py Decomposition

**Current State:** 2,420 lines

| Component | Target Module |
|-----------|---------------|
| Base client class | `memory_client/base.py` |
| HTTP transport | `memory_client/http.py` |
| Batch operations | `memory_client/batch.py` |
| Tenant isolation | `memory_client/tenant.py` |
| Circuit breaker | `memory_client/resilience.py` |

---

### FR-003: SomaAgent01 chat_service.py Decomposition (DELETED)

**Current State:** 897 lines, single ChatService class

| Method Group | Lines | Target Module |
|--------------|-------|---------------|
*Module was deleted; decomposition no longer applicable.*

**Acceptance Criteria:**
- [ ] `ChatService.send_message()` produces identical output
- [ ] E2E test `verify_e2e_chat.py` passes
- [ ] Metrics still published to Prometheus

---

### FR-004: SomaAgent01 core/models.py Decomposition

**Current State:** 907 lines, 73 outline items (19 Django models)

| Model Group | Target Module |
|-------------|---------------|
| Session, SessionEvent | `models/session.py` |
| Capability | `models/capability.py` |
| UISetting, FeatureFlag | `models/settings.py` |
| Job, SystemTask | `models/jobs.py` |
| Notification | `models/notification.py` |
| Prompt | `models/prompt.py` |
| AuditLog | `models/audit.py` |

**Acceptance Criteria:**
- [ ] `from admin.core.models import Capsule` still works
- [ ] Django migrations detect model moves correctly
- [ ] All ForeignKey relationships preserved

---

## 4. Non-Functional Requirements

### NFR-001: Backward Compatibility
All original import paths MUST continue working via `__init__.py` re-exports.

### NFR-002: Zero Downtime
Refactoring MUST NOT require service restart during deployment.

### NFR-003: Test Coverage
Each split module MUST have corresponding unit tests.

---

## 5. Verification Procedures

### 5.1 Line Count Verification
```bash
find . -name "*.py" -not -path "*/migrations/*" \
  -exec wc -l {} \; | awk '$1 > 650 {print}'
# Expected: No output
```

### 5.2 Import Verification
```python
# somabrain
from somabrain.app import app
from somabrain.memory_client import MemoryClient

# somaAgent01
from admin.core.models import Capsule, Session
from services.common.chat_service import ChatService
```

### 5.3 E2E Verification
```bash
# Start Docker infrastructure
docker compose -f infra/aaas/docker-compose.yml up -d

# Run E2E tests
pytest tests/e2e/ -v --tb=short
```

---

## 6. Traceability Matrix

| Requirement | Source | Test Case | Priority |
|-------------|--------|-----------|----------|
| FR-001 | VIBE-245 | test_app_imports | 🔴 P0 |
| FR-002 | VIBE-245 | test_memory_client | 🔴 P0 |
| FR-003 | VIBE-245 | test_chat_flow_e2e | 🔴 P0 |
| FR-004 | VIBE-245 | test_models_import | 🔴 P0 |
| NFR-001 | VIBE-102 | test_backward_compat | 🟠 P1 |

---

## 7. Risk Analysis

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Circular imports | High | Critical | Use TYPE_CHECKING, lazy imports |
| Broken migrations | Medium | High | Run makemigrations after each model move |
| Missing re-exports | Medium | Medium | Automated import test suite |
| Performance regression | Low | Medium | Benchmark before/after |

---

## 8. Implementation Schedule

### Phase 1: SomaAgent01 Critical Path (Day 1)
- [ ] `chat_service.py` → DELETED
- [ ] `core/models.py` → 9 modules
- [ ] Verify E2E chat flow

### Phase 2: SomaAgent01 Remaining (Day 2)
- [ ] `conversations/api.py`
- [ ] `permissions/granular.py`
- [ ] `voice/api.py`, `flink/api.py`
- [ ] `scheduler_models.py`, `memory_stores.py`

### Phase 3: SomaBrain Critical (Days 3-4)
- [ ] `app.py` → 7+ modules
- [ ] `memory_client.py` → 5 modules
- [ ] Verify health endpoints

### Phase 4: SomaBrain Remaining (Day 5)
- [ ] Remaining 10 files
- [ ] Full regression test

---

## 9. Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Technical Lead | - | - | PENDING |
| QA Lead | - | - | PENDING |
| Project Owner | - | - | PENDING |

---

**Document End**

*Generated by SOMA COLLECTIVE INTELLIGENCE per ISO/IEC 29148:2018*
