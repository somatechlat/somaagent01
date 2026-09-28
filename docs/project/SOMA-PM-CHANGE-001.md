# SOMA COGNITIVE TRIAD — CHANGE CONTROL LOG

## Document Control

| Field | Value |
|---|---|
| Document Title | Change Control Log |
| Document Identifier | SOMA-PM-CHANGE-001 |
| Version | 1.0.0 |
| Date | 2026-06-15 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2026-12-28 |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-09-28 | SomaTech Engineering | Brought under ISO document control: Document Control block normalised and this Revision History added. |

## 1. PURPOSE

This document tracks all changes to project scope, schedule, budget, and deliverables. Every change must be logged here with impact assessment and approval status.

---

## 2. CHANGE REQUESTS

| CR ID | Date | Requestor | Description | Impact | Priority | Status | Approved By |
|-------|------|-----------|-------------|--------|----------|--------|-------------|
| CR-001 | 2026-06-15 | Engineering | Initial ISO documentation suite created across all 3 repos (25 files) | Scope addition, no schedule impact | Medium | APPROVED | PM |
| CR-002 | 2026-06-15 | Engineering | Added compatibility matrix (SOMA-COMPAT-001) and AAAS deployment spec (SOMA-01-AAAS-001) | Scope addition, no schedule impact | Medium | APPROVED | PM |
| CR-003 | 2026-06-15 | Engineering | Version bump: somaAgent01 README/AGENT.md to v2.0.0 | Documentation update | Low | APPROVED | PM |

---

## 3. CHANGE REQUEST TEMPLATE

```
CR-[NNN] | [DATE]

REQUESTOR: [Name/Role]
DESCRIPTION: [What is changing]
REASON: [Why the change is needed]
IMPACT:
  - Scope: [Increase/Decrease/No change]
  - Schedule: [Days added/removed]
  - Budget: [Hours/cost added/removed]
  - Risk: [New risks introduced]
PRIORITY: [Critical/High/Medium/Low]
APPROVAL:
  - PM: [Name] [Date] [Approved/Rejected]
  - Sponsor: [Name] [Date] [Approved/Rejected] (if budget impact > 40 hours)
```

---

## 4. SCOPE CHANGE THRESHOLDS

| Change Size | Approval Required | Turnaround |
|-------------|-------------------|------------|
| < 8 hours | Team Lead | Same day |
| 8-40 hours | Project Manager | 2 business days |
| > 40 hours | Engineering Director | 5 business days |
| Schedule impact > 1 week | Sponsor | 5 business days |
| Budget impact > 10% | Sponsor + Finance | 10 business days |

---

## 5. FROZEN ITEMS (Cannot Change Without Sponsor Approval)

1. **Technology stack**: Django + Django Ninja + Lit 3.x + PostgreSQL + Milvus (VIBE mandate)
2. **Deployment modes**: Standalone (20xxx) and AAAS (63xxx) — both must be supported
3. **Repo structure**: Three independent repos (somaAgent01, somabrain, somafractalmemory)
4. **Production date**: October 19, 2026 (project closure)
5. **Minimum test coverage**: 50% for somaAgent01

---

End of Document
