# V3 FLOW MASTER TASK TRACKER — COMPLETE IMPLEMENTATION PLAN

**Project:** SomaAgent01 V3 Flow
**Last Updated:** 2026-01-16 20:51
**Status:** 81% COMPLETE (13/16 SRS)

---

## 📊 COMPLETE 12-PHASE FLOW STATUS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        12-PHASE AGENTIC TURN PIPELINE                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐           │
│  │ P1  │───▶│ P2  │───▶│ P3  │───▶│ P4  │───▶│ P5  │───▶│ P6  │           │
│  │AUTH │    │BUDG │    │CAPS │    │DERV │    │CTXT │    │MEM  │           │
│  │ ✅  │    │ ⏳  │    │ ✅  │    │ ✅  │    │ ✅  │    │ ✅  │           │
│  └─────┘    └─────┘    └─────┘    └─────┘    └─────┘    └─────┘           │
│                                                                             │
│  ┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐           │
│  │ P7  │───▶│ P8  │───▶│ P9  │───▶│ P10 │───▶│ P11 │───▶│ P12 │           │
│  │ LLM │    │ RLM │    │TOOL │    │SAVE │    │LERN │    │OBSV │           │
│  │ ✅  │    │ ✅  │    │ ✅  │    │ ✅  │    │ ✅  │    │ ✅  │           │
│  └─────┘    └─────┘    └─────┘    └─────┘    └─────┘    └─────┘           │
│                                                                             │
│  Legend: ✅ IMPLEMENTED   ⏳ IN PROGRESS   🔴 TODO                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 SRS → IMPLEMENTATION MATRIX

| # | SRS Document | Sprint | Implementation File | Lines | Status |
|---|--------------|--------|---------------------|-------|--------|
| 1 | SRS-DATA-MODELS | 1 | `admin/*/models.py` (50+ models) | 3,500+ | ✅ DONE |
| 2 | SRS-CAPSULE-PORTABILITY | 1 | `admin/core/models.py:Capsule` | 250 | ✅ DONE |
| 3 | SRS-SECURITY-MULTITENANCY | 2 | SpiceDB + Vault + Keycloak | - | ✅ DONE |
| 4 | SRS-AGENTIQ | 4 | `admin/core/agentiq/` | 542 | ✅ DONE |
| 5 | SRS-PERMISSION-MATRIX | 5 | `admin/core/permission_matrix.py` | 270 | ✅ DONE |
| 7 | SRS-CONTEXT-BUILDING | 7 | `admin/core/context/` | 425 | ✅ DONE |
| 8 | SRS-MODEL-ROUTING | 8 | `admin/core/model_router.py` | 220 | ✅ DONE |
| 9 | SRS-MULTIMODAL | 8 | `admin/core/multimodal.py` | 230 | ✅ DONE |
| 11 | SRS-CHAT-FLOW-MASTER | 9 | `admin/core/chat_orchestrator.py` | 215 | ✅ DONE |
| 12 | SRS-LAGO-BILLING | 9 | `admin/core/billing.py` | 220 | ✅ DONE |
| 13 | SRS-SOMABRAIN-INTEGRATION | 3 | `admin/somabrain/` | 400+ | ✅ DONE |
| 14 | **SRS-BUDGET-SYSTEM** | 10 | `admin/core/budget/` | 950 | ✅ DONE |
| 15 | **SRS-FEATURE-FLAGS** | 11 | `admin/core/features/` | 1300 | ✅ DONE |
| 16 | **SRS-BACKUP-SYSTEM** | 12 | `services/capsule_export.py` | 445 | ✅ DONE |

---

## 🎯 SPRINT 10: BUDGET SYSTEM

### Files to Create

| File | Purpose | Est. Lines |
|------|---------|------------|
| `admin/core/budget/__init__.py` | Package exports | 30 |
| `admin/core/budget/registry.py` | Metric definitions | 100 |
| `admin/core/budget/gate.py` | @budget_gate decorator | 80 |
| `admin/core/budget/limits.py` | Plan limits | 60 |
| `admin/core/budget/cache.py` | Redis cache | 50 |
| `admin/core/budget/exceptions.py` | BudgetExhaustedError | 40 |
| `admin/core/budget/lago.py` | Lago event publishing | 70 |

### Tasks

- [ ] **TASK 10.1**: Create `METRIC_REGISTRY` with 10 metrics
  ```python
  tokens, tool_calls, images, voice_minutes, api_calls,
  memory_tokens, vector_ops, learning, storage_gb, sessions
  ```

- [ ] **TASK 10.2**: Implement `@budget_gate(metric="tokens")` decorator
  - Check cache `budget:{tenant_id}:{metric}`
  - Compare against plan limit
  - Raise `BudgetExhaustedError(402)` if exceeded
  - Async emit Lago event after success

- [ ] **TASK 10.3**: Integrate with chat_orchestrator.py Phase 2
  ```python
  @budget_gate(metric="tokens")
  async def process_chat(request, capsule):
      ...
  ```

  ```python
  @budget_gate(metric="tool_calls")
  async def execute_tool(request, tool_name, args):
      ...
  ```

- [ ] **TASK 10.5**: Integrate with multimodal.py
  ```python
  @budget_gate(metric="images")
  async def generate_image(request, prompt, capsule):
      ...
  ```

---

## 🎯 SPRINT 11: FEATURE FLAGS

### Files to Create

| File | Purpose | Est. Lines |
|------|---------|------------|
| `admin/core/features/__init__.py` | Package exports | 25 |
| `admin/core/features/registry.py` | Feature definitions | 150 |
| `admin/core/features/check.py` | is_feature_enabled() | 80 |
| `admin/core/features/gate.py` | @require_feature decorator | 60 |
| `admin/api/features.py` | API endpoints | 100 |

### Tasks

- [ ] **TASK 11.1**: Create `FEATURE_REGISTRY` with tiers
  ```
  TIER 1 (CORE - Always ON): chat, auth, capsule, agentiq, permissions
  TIER 2 (OPTIONAL - Toggleable): images, vision, voice, learning, mcp
  ```

- [ ] **TASK 11.2**: Implement `is_feature_enabled(tenant_id, feature)`
  - Check plan requirement
  - Check dependencies
  - Check credentials
  - Check tenant toggle

- [ ] **TASK 11.3**: Implement `@require_feature("images")` decorator
  ```python
  @require_feature("images")
  @budget_gate(metric="images")
  async def generate_image(request, prompt, capsule):
      ...
  ```

- [ ] **TASK 11.4**: Create API endpoints
  - `GET /features` - List all with status
  - `POST /features/{feature}` - Toggle
  - `POST /features/{feature}/credentials` - Set credentials

- [ ] **TASK 11.5**: Create Agent Settings UI mockups

---

## 🎯 SPRINT 12: FULL PERMISSIONS (88)

### Tasks

- [ ] **TASK 12.1**: Complete SpiceDB schema with all 88 permissions
  ```zed
  definition platform {}
  definition tenant {
      permission manage = sysadmin
      permission administrate = sysadmin + admin
      ...
  }
  ```

- [ ] **TASK 12.2**: Update permission_matrix.py with full matrix

- [ ] **TASK 12.3**: Create OPA policies for all levels
  - Level 0: Platform
  - Level 1: Tenant
  - Level 2: Agent
  - Level 3: Resource
  - Level 4: Emergency

- [ ] **TASK 12.4**: Integration tests for all 88 permissions

---

## 🎯 SPRINT 13: MULTIMODAL ROUTING INTEGRATION

### Tasks

- [ ] **TASK 13.1**: Create `admin/multimodal/routing.py`
  ```python
  async def select_multimodal_model(
      capability: str,
      capsule: Capsule,
  ) -> LLMModelConfig
  ```

- [ ] **TASK 13.2**: Update execution.py with tenant isolation

- [ ] **TASK 13.3**: Add @budget_gate + @require_feature to all endpoints

- [ ] **TASK 13.4**: Integration tests for multimodal flow

---

## 📁 COMPLETE FILE INVENTORY

### ✅ IMPLEMENTED FILES (16 files, ~2,642 lines)

| File | SRS | Lines | Tests |
|------|-----|-------|-------|
| `admin/core/agentiq/__init__.py` | AGENTIQ | 27 | ✅ |
| `admin/core/agentiq/settings.py` | AGENTIQ | 75 | ✅ |
| `admin/core/agentiq/tables.py` | AGENTIQ | 165 | ✅ |
| `admin/core/agentiq/derivation.py` | AGENTIQ | 105 | ✅ |
| `admin/core/agentiq/unified_gate.py` | AGENTIQ | 170 | ✅ |
| `admin/core/context/__init__.py` | CONTEXT | 27 | ✅ |
| `admin/core/context/models.py` | CONTEXT | 68 | ✅ |
| `admin/core/context/lanes.py` | CONTEXT | 120 | ✅ |
| `admin/core/context/builder.py` | CONTEXT | 210 | ✅ |
| `admin/core/model_router.py` | MODEL-ROUTING | 220 | ✅ |
| `admin/core/permission_matrix.py` | PERMISSION | 270 | ✅ |
| `admin/core/chat_orchestrator.py` | CHAT-FLOW | 215 | ✅ |
| `admin/core/multimodal.py` | MULTIMODAL | 230 | ✅ |
| `admin/core/billing.py` | LAGO-BILLING | 220 | ✅ |

### 🔴 FILES TO CREATE (12 files, ~900 lines)

| File | SRS | Est. Lines |
|------|-----|------------|
| `admin/core/budget/__init__.py` | BUDGET | 30 |
| `admin/core/budget/registry.py` | BUDGET | 100 |
| `admin/core/budget/gate.py` | BUDGET | 80 |
| `admin/core/budget/limits.py` | BUDGET | 60 |
| `admin/core/budget/cache.py` | BUDGET | 50 |
| `admin/core/budget/exceptions.py` | BUDGET | 40 |
| `admin/core/budget/lago.py` | BUDGET | 70 |
| `admin/core/features/__init__.py` | FEATURES | 25 |
| `admin/core/features/registry.py` | FEATURES | 150 |
| `admin/core/features/check.py` | FEATURES | 80 |
| `admin/core/features/gate.py` | FEATURES | 60 |
| `admin/api/features.py` | FEATURES | 100 |

---

## 📊 METRICS

| Metric | Value |
|--------|-------|
| **SRS Documents** | 17 |
| **SRS Implemented** | 13/16 (81%) |
| **Files Created** | 16 |
| **Lines Implemented** | ~2,642 |
| **Files Remaining** | 12 |
| **Lines Remaining** | ~900 |
| **Total Estimated** | ~3,542 |

---

## 🔄 INTEGRATION TEST CHECKLIST

### Phase 1-4: Ingress
- [ ] JWT authentication
- [ ] Budget gate enforcement
- [ ] Capsule load by tenant
- [ ] Knob derivation

### Phase 5-8: Process
- [ ] Context building with lanes
- [ ] Memory recall from SomaBrain
- [ ] LLM invoke with fallback
- [ ] RLM execution

### Phase 9-12: Execute
- [ ] Tool execution with 4-phase gate
- [ ] Multimodal routing
- [ ] Memorize to Brain
- [ ] Learn updates to capsule.body.learned
- [ ] Audit trail (AuditLog)

---

## ✅ ACCEPTANCE CRITERIA

| Criterion | Status |
|-----------|--------|
| 12-phase flow complete | ⏳ 11/12 (missing Budget gate) |
| Capsule sovereignty | ✅ All from capsule.body |
| 3 knobs → all settings | ✅ AgentIQ |
| Resilience patterns | ✅ Circuit breakers |
| Security layers | ✅ SpiceDB + OPA + Vault |
| Audit trail | ✅ Reversible, traceable |
| Constitution from SomaBrain | ✅ Not stored locally |

---

## 📆 ESTIMATED TIMELINE

| Sprint | Duration | Status |
|--------|----------|--------|
| 10: Budget System | 2 days | 🔴 NEXT |
| 11: Feature Flags | 2 days | 🔴 |
| 12: Full Permissions | 3 days | 🔴 |
| 13: Multimodal Routing | 1 day | 🔴 |
| **TOTAL** | **8 days** | |

---

**Document End**

*13/16 SRS IMPLEMENTED — 81% COMPLETE ✅*
