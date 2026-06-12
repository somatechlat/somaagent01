# TASK-RLM-ENGINE: Recursive Language Model Implementation

**Module:** RLM Engine
**SRS Source:** SRS-RLM-ENGINE-2026-01-16
**Sprint:** 9 (Wave 3)
**Applied Personas:** ALL 10 ✅

---

## 📌 PERSONA CONTRIBUTIONS

### 🎓 PhD Developer
- Mind-Body architecture from MIT CSAIL
- brain.ask() → SomaBrain recall integration

### 🔍 PhD Analyst
- FC-STOMP loop implementation
- V3 theory: IDBD, UCB equations

### 🧪 PhD QA
- Test Mind-Body loop isolation
- Test brain.ask() fallback

### 🔒 Security Auditor
- RLM iterations bounded by intelligence
- No infinite loops

### ⚡ Performance
- Temporal orchestration for durability
- Async execution

---

## 📁 FILE STRUCTURE

```
admin/agents/services/
└── mind_body.py        # Mind-Body loop (if implemented)

aaas/brain.py           # BrainBridge — current SomaBrain access layer
admin/core/somabrain_client.py  # HTTP SomaBrain client
```

**Note:** `brain_bridge.py` was removed during consolidation. Current Brain access is via `BrainBridge` in `aaas/brain.py` or `SomaBrainClient` in `admin/core/somabrain_client.py`.

---

## 🎯 TASKS

### Day 1: RLMEngine Class
- [ ] Create RLMEngine with capsule integration
- [ ] derive_rlm_settings from intelligence knob

### Day 2: Mind-Body Loop
- [ ] Implement Mind (propose action)
- [ ] Implement Body (execute tool/observe)
- [ ] Loop with max_iterations

### Day 3: Brain.ask() Integration
- [ ] brain.ask() → SomaBrain.recall()
- [ ] Use when uncertain (Sub-LM pattern)

### Day 4: Temporal Integration
- [ ] Wrap in ConversationWorkflow
- [ ] SAGA compensation
- [ ] Dead Letter Queue

---

## 🔗 DEPENDENCIES

| Depends On | Status |
|------------|--------|
| AgentIQ (derive_rlm_settings) | ⏳ Sprint 4 |
| SomaBrain.recall() | ✅ EXISTS |
| Temporal worker | ✅ EXISTS |

---

## Status: BLOCKED ON AgentIQ
