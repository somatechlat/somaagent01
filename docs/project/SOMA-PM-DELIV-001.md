# SOMA COGNITIVE TRIAD — DELIVERABLES REGISTER

## Document Control

| Field | Value |
|-------|-------|
| Document Title | Deliverables Register |
| Document Identifier | SOMA-PM-DELIV-001 |
| Version | 1.0.0 |
| Date | 2026-06-15 |
| Status | Active |

---

## DELIVERABLES

| ID | Deliverable | Phase | Owner | Due Date | Status | Acceptance Criteria |
|----|-------------|-------|-------|----------|--------|---------------------|
| D-001 | App starts without crash | 1 | Backend | Jun 17 | OPEN | `python manage.py check` returns 0 |
| D-002 | Django migrations committed | 1 | Backend | Jun 16 | OPEN | `makemigrations --check --dry-run` clean |
| D-003 | Permissions check wired | 1 | Security | Jun 18 | OPEN | /check returns real SpiceDB result |
| D-004 | Chat flow E2E working | 1 | Frontend+Backend | Jun 23 | OPEN | WS → V3 → LLM → stream → client |
| D-005 | Standalone Docker verified | 1 | DevOps | Jun 25 | OPEN | `docker compose up -d` all healthy |
| D-006 | AAAS Docker verified | 1 | DevOps | Jun 27 | OPEN | Full triad starts, health checks pass |
| D-007 | Auth features functional | 2 | Backend | Jul 7 | OPEN | Login/register/MFA/reset/logout work |
| D-008 | Frontend security hardened | 2 | Frontend | Jul 10 | OPEN | httpOnly cookies, CSP, CSRF tokens |
| D-009 | K8s credentials secured | 2 | DevOps | Jul 9 | OPEN | No hardcoded passwords in manifests |
| D-010 | Security scan clean | 2 | Security | Jul 12 | OPEN | Bandit -lll + Safety pass |
| D-011 | DeploymentMode unified | 3 | Backend | Jul 16 | OPEN | All files use DeploymentMode singleton |
| D-012 | MemoryPort adopted | 3 | Backend | Jul 21 | OPEN | Single memory interface across codebase |
| D-013 | Single chat pipeline | 3 | Backend | Jul 24 | OPEN | V3 only, conversation worker wired |
| D-014 | Pyright errors < 500 | 3 | Backend | Jul 31 | OPEN | Pyright report shows < 500 |
| D-015 | CI pipeline active | 4 | DevOps | Aug 6 | OPEN | GitHub Actions runs on PR |
| D-016 | 50%+ test coverage | 4 | QA | Aug 24 | OPEN | Coverage report ≥ 50% |
| D-017 | Contract tests | 4 | QA | Aug 22 | OPEN | Cross-repo API compatibility verified |
| D-018 | K8s production manifests | 5 | DevOps | Aug 29 | OPEN | Probes, limits, HPA, PDB, NetworkPolicy |
| D-019 | Grafana dashboards | 5 | DevOps | Sep 8 | OPEN | Dashboards as code committed |
| D-020 | Load test baseline | 5 | QA | Sep 14 | OPEN | p95 latency < 200ms for chat |
| D-021 | Full AAAS E2E test | 6 | QA | Sep 18 | OPEN | Cognitive agent works end-to-end |
| D-022 | Single-click deploy | 6 | DevOps | Sep 22 | OPEN | AAAS deploy in one command |
| D-023 | Security pentest passed | 6 | Security | Sep 30 | OPEN | No critical/high findings |
| D-024 | DR drill successful | 6 | DevOps | Oct 2 | OPEN | Restore within RTO |
| D-025 | UAT signed off | 6 | QA | Oct 5 | OPEN | Stakeholders approve |
| D-026 | Production deployment | 7 | DevOps | Oct 10 | OPEN | Production environment live |
| D-027 | Operations runbook | 7 | Ops | Oct 15 | OPEN | Runbook complete, team trained |
| D-028 | Project closure report | 7 | PM | Oct 19 | OPEN | Lessons learned documented |

---

End of Document
