# TASK-SOMABRAIN: L3 Cognitive Engine Integration

## Document Control

| Field | Value |
|---|---|
| Document Title | TASK-SOMABRAIN: L3 Cognitive Engine Integration |
| Document Identifier | SOMA-TASK-SOMABRAIN-001 |
| Version | 1.0.0 |
| Date | 2026-09-28 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2026-12-28 |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-09-28 | SomaTech Engineering | Initial issue. Brought under ISO document control. |


**Module:** SomaBrain Integration
**SRS Source:** SRS-SOMABRAIN-INTEGRATION-2026-01-16
**Sprint:** 3 (Wave 1)
**Applied Personas:** ALL 10 ✅

---

## 📌 CORE OPERATIONS

| Operation | Purpose | Code Location |
|-----------|---------|---------------|
| **recall** | Get memories | somabrain/services/recall_service.py ✅ |
| **memorize** | Store memories | somabrain/services/memory_service.py ✅ |
| **learn** | Update preferences | somabrain/cognitive_loop_service.py ✅ |

---

## 📁 AAAS BRIDGE REQUIRED

```
admin/somabrain/
├── __init__.py
├── client.py           # SomaBrainClient
├── cognitive.py        # CognitiveCore wrapper
└── core_brain.py       # Direct import bridge
```

---

## 🎯 TASKS

### Day 1: Direct Import Bridge
- [ ] Create SomaBrainClient for AAAS mode
- [ ] Import CognitiveCore directly (0ms)
- [ ] Fallback to HTTP for standalone

### Day 2: Capsule Integration
- [ ] Read config from capsule.body.persona.memory
- [ ] Apply recall_limit, similarity_threshold

### Day 3: Learn Integration
- [ ] Update capsule.body.learned after success
- [ ] lane_preferences updates
- [ ] neuromodulator_state updates

---

## ✅ CODE EXISTS

| Component | Location | Status |
|-----------|----------|--------|
| recall() | somabrain/services/recall_service.py | ✅ |
| UCB1Bandit | somabrain/attention.py | ✅ |
| Neuromodulators | somabrain/neuromodulators.py | ✅ |
| Amygdala | somabrain/amygdala.py | ✅ |

---

## Status: DEPENDENCIES MET → READY
