# TASK-SOMABRAIN: L3 Cognitive Engine Integration

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

## 📁 SaaS BRIDGE REQUIRED

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
- [ ] Create SomaBrainClient for SaaS mode
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
