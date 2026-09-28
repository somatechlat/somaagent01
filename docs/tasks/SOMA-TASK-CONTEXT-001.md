# TASK-CONTEXT-BUILDING: 5-Lane Context Assembly

## Document Control

| Field | Value |
|---|---|
| Document Title | TASK-CONTEXT-BUILDING: 5-Lane Context Assembly |
| Document Identifier | SOMA-TASK-CONTEXT-001 |
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


**Module:** Context Building
**SRS Source:** SRS-CONTEXT-BUILDING-2026-01-16
**Sprint:** 7 (Wave 3)
**Applied Personas:** ALL 10 ✅

---

## 📌 5 CONTEXT LANES

| Lane | Content | Allocation |
|------|---------|------------|
| **system** | System prompt | 15% |
| **history** | Conversation history | 30% |
| **memory** | SomaBrain recall | 25% |
| **tools** | Tool descriptions | 20% |
| **buffer** | User message | 10% |

---

## 📁 FILE STRUCTURE

```
admin/core/context/
├── __init__.py
├── builder.py          # ContextBuilder class
├── lanes.py            # Lane allocation
└── compression.py      # Token management
```

---

## 🎯 TASKS

### Day 1: Lane Allocation
- [ ] Read lane_preferences from capsule.body.learned
- [ ] Default if not present
- [ ] Normalize to 100%

### Day 2: ContextBuilder
- [ ] Assemble 5 lanes
- [ ] Token budgeting per lane
- [ ] PII redaction (Presidio)

### Day 3: SomaBrain Integration
- [ ] Call brain.recall() for memory lane
- [ ] Apply similarity_threshold

---

## 🔗 DEPENDENCIES

| Depends On | Status |
|------------|--------|
| Capsule.body.learned | ✅ SCHEMA |
| SomaBrain.recall() | ✅ EXISTS |

---

## Status: BLOCKED ON SomaBrain Bridge
