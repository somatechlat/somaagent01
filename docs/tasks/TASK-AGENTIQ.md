# TASK-AGENTIQ: Governor Control Loop Implementation

**Module:** AgentIQ
**SRS Source:** SRS-AGENTIQ-2026-01-16
**Priority:** FIRST (All settings derive from this)
**Applied Personas:** ALL 10 ✅

---

## 📌 PERSONA CONTRIBUTIONS

### 🎓 PhD Software Developer
- Implement `derive_all_settings()` with pure Python (0ms latency)
- No external calls in derivation logic
- Immutable DerivedSettings dataclass

### 🔍 PhD Software Analyst
- Map 3 knobs → all downstream settings
- Document derivation ratios mathematically
- Validate against V3 theory equations

### 🧪 PhD QA Engineer
- Unit tests for each derivation table row
- Property-based tests for edge cases (knobs 0, 1, 10)
- Integration tests with real capsule

### 🔒 Security Auditor
- UnifiedGate fail-closed principle
- No permission = DENY
- Audit log all permission checks

### ⚡ Performance Engineer
- 0ms derivation target
- No database calls in derive_all_settings()
- Cache OPA policy results

### 🎨 UX Consultant
- Clear error messages for permission denial
- Meaningful governance feedback to user

### 📚 ISO Documenter
- Complete docstrings
- Type hints on all functions
- Update SRS on implementation

### 🏗️ Django Architect
- Location: `admin/core/agentiq/`
- Use Pydantic for DerivedSettings
- Protocol-based design

### 🔧 Django Infra
- No migrations needed (pure logic)
- Settings from capsule.body only

### 📣 Django Evangelist
- Follow Django Ninja patterns
- Integrate with existing handlers

---

## 📁 FILE STRUCTURE

```
admin/core/agentiq/
├── __init__.py
├── derivation.py      # derive_all_settings()
├── unified_gate.py    # UnifiedGate class
├── settings.py        # DerivedSettings dataclass
└── tables.py          # Derivation lookup tables
```

---

## 🎯 SPRINT 4 TASKS

### Day 1: Settings Dataclass
- [ ] Create `DerivedSettings` Pydantic model
- [ ] Define all derived fields
- [ ] Add validation

### Day 2: Derivation Tables
- [ ] INTELLIGENCE table (temperature, tokens, rlm_iter)
- [ ] AUTONOMY table (hitl, tool_approval, egress)
- [ ] RESOURCE table (token_limit, cost_tier)

### Day 3: Core Function
- [ ] Implement `derive_all_settings(capsule)`
- [ ] Pure Python, no external calls
- [ ] Return DerivedSettings

### Day 4: UnifiedGate
- [ ] Implement `UnifiedGate.check(capsule, action)`
- [ ] OPA check (cached)
- [ ] SpiceDB check (with fallback)
- [ ] Scope check from capsule

---

## 📊 DERIVATION TABLES

### From INTELLIGENCE (1-10)

| Level | temperature | max_tokens | rlm_iter | recall_limit | model_tier |
|-------|-------------|------------|----------|--------------|------------|
| 1-3   | 0.3         | 512        | 1        | 5            | budget     |
| 4-6   | 0.7         | 2048       | 2        | 15           | standard   |
| 7-8   | 0.8         | 4096       | 3        | 25           | premium    |
| 9-10  | 0.9         | 8192       | 5        | 50           | flagship   |

### From AUTONOMY (1-10)

| Level | require_hitl | tool_approval | egress_allowed |
|-------|--------------|---------------|----------------|
| 1-3   | all_actions  | all_tools     | none           |
| 4-6   | dangerous    | dangerous     | whitelist      |
| 7-8   | none         | none          | expanded       |
| 9-10  | none         | none          | unrestricted   |

### From RESOURCE ($/turn)

| Budget     | token_limit | cost_tier | thinking_budget |
|------------|-------------|-----------|-----------------|
| 0.01-0.10  | 1K          | budget    | 256             |
| 0.10-0.50  | 10K         | standard  | 1024            |
| 0.50-2.00  | 50K         | premium   | 2048            |
| 2.00+      | 100K        | flagship  | 4096            |

---

## ✅ ACCEPTANCE CRITERIA

| Criterion | Verification |
|-----------|--------------|
| Settings from 3 knobs | No hardcoded values |
| UnifiedGate for permissions | OPA + SpiceDB + Scope |
| Hot-reload from capsule | No restart needed |
| OTEL traced | All derivations logged |
| 0ms latency | Pure Python only |
| Fail-closed | DENY on any error |

---

## 🔗 DEPENDENCIES

| Depends On | Status |
|------------|--------|
| Capsule model | ✅ EXISTS |
| capsule.body schema | ✅ DEFINED |
| OPA integration | ✅ EXISTS |
| SpiceDB client | ✅ EXISTS |

---

## Status: READY FOR IMPLEMENTATION
