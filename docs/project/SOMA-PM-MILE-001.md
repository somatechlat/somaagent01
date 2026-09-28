# SOMA COGNITIVE TRIAD — MILESTONE TRACKER

## Document Control

| Field | Value |
|---|---|
| Document Title | Milestone Tracker |
| Document Identifier | SOMA-PM-MILE-001 |
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

## MILESTONES

| ID | Milestone | Date | Phase | Gate Criteria | Status |
|----|-----------|------|-------|---------------|--------|
| M-001 | Project Kickoff | Jun 16, 2026 | — | Charter approved, team assigned | PENDING |
| M-002 | Phase 1 Gate: System Starts | Jun 29, 2026 | 1 | App starts, chat works, Docker verified | PENDING |
| M-003 | Phase 2 Gate: Security Hardened | Jul 13, 2026 | 2 | All auth features work, security scan clean | PENDING |
| M-004 | Phase 3 Gate: Architecture Unified | Aug 3, 2026 | 3 | Single pipeline, single memory, <500 type errors | PENDING |
| M-005 | Phase 4 Gate: Tested | Aug 24, 2026 | 4 | CI active, 50%+ coverage, contract tests | PENDING |
| M-006 | Phase 5 Gate: Hardened | Sep 14, 2026 | 5 | K8s ready, monitoring, load test baseline | PENDING |
| M-007 | Phase 6 Gate: Validated | Oct 5, 2026 | 6 | E2E validated, pentest clean, UAT passed | PENDING |
| M-008 | Production Release | Oct 10, 2026 | 7 | Production live, 72h monitoring clean | PENDING |
| M-009 | Project Closure | Oct 19, 2026 | 7 | Runbook complete, team trained, lessons learned | PENDING |

---

## GATE REVIEW TEMPLATE

Each phase gate requires sign-off from:

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Project Manager | | | |
| Phase Owner | | | |
| Security Lead | | | |
| Engineering Director | | | |

### Gate Decision: ☐ PASS  ☐ CONDITIONAL PASS  ☐ FAIL

**Conditions (if conditional):**
1. 
2. 

**Notes:**


---

## CRITICAL PATH

```
M-001 → T1.1 (startup fix) → T1.4 (WebSocket fix) → T1.10 (Docker verify) → M-002
      → T2.1-T2.5 (auth fixes) → T2.10 (security scan) → M-003
      → T3.4 (unify chat) → T3.8 (type errors) → M-004
      → T4.1 (CI setup) → T4.9 (coverage) → M-005
      → T5.1 (K8s) → T5.9 (load test) → M-006
      → T6.1 (E2E) → T6.6 (pentest) → T6.8 (UAT) → M-007
      → T7.3 (prod deploy) → M-008 → T7.7 (closure) → M-009
```

**Critical path duration: 18 weeks**
**Float: 0 days (no slack on critical path)**

---

End of Document
