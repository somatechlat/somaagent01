# SOMA COGNITIVE TRIAD — COMMUNICATION PLAN

## Document Control

| Field | Value |
|-------|-------|
| Document Title | Communication Plan |
| Document Identifier | SOMA-PM-COMM-001 |
| Version | 1.0.0 |
| Date | 2026-06-15 |
| Status | Active |

---

## 1. COMMUNICATION MATRIX

| Event | Frequency | Audience | Medium | Owner | Purpose |
|-------|-----------|----------|--------|-------|---------|
| Daily Standup | Daily 9:00 AM | Core team (5) | Video call | PM | Blockers, progress, plan |
| Sprint Planning | Bi-weekly Monday | Core team | Video call | PM | Plan next sprint |
| Sprint Review | Bi-weekly Friday | Core team + stakeholders | Video call + demo | PM | Show progress, get feedback |
| Gate Review | End of phase | PM + leads + sponsor | Document + meeting | PM | Go/no-go decision |
| Stakeholder Update | Monthly | Sponsor + directors | Written report (email) | PM | Status, risks, budget |
| Risk Review | Bi-weekly Wednesday | PM + leads | Spreadsheet + call | PM | Update risk register |
| Cross-Repo Sync | Weekly Thursday | Agent + Brain + SFM leads | Video call | PM | Integration status, API changes |
| ISO Doc Review | Monthly | PM + quality lead | Document review | PM | Documentation currency |
| Security Review | Monthly | Security lead + PM | Report + meeting | Security | Vulnerability status |
| Retrospective | End of each phase | Core team | Video call | PM | Lessons learned |

---

## 2. ESCALATION PATH

| Level | Who | When | Response Time |
|-------|-----|------|---------------|
| Level 1 | Team Lead | Task blocked < 2 days | 4 hours |
| Level 2 | Project Manager | Task blocked > 2 days, phase at risk | 2 hours |
| Level 3 | Engineering Director | Phase gate failure, budget issue | 1 hour |
| Level 4 | CEO/Sponsor | Project at risk, major blocker | Immediate |

---

## 3. TOOLS

| Purpose | Tool | Access |
|---------|------|--------|
| Task tracking | GitHub Issues (per repo) | All team members |
| Communication | Slack #soma-triad | All team members |
| Documentation | docs/iso/ and docs/project/ (in repo) | All team members |
| CI/CD | GitHub Actions | DevOps + leads |
| Monitoring | Grafana dashboards | All team members |
| Code review | GitHub PRs | All team members |

---

## 4. REPORTING TEMPLATES

### 4.1 Weekly Status Report

```
WEEK: [N] | DATE: [YYYY-MM-DD] | PHASE: [N]

COMPLETED THIS WEEK:
- [Task ID]: [Description] — [Owner]

IN PROGRESS:
- [Task ID]: [Description] — [Owner] — [% complete]

BLOCKED:
- [Task ID]: [Description] — [Blocker] — [Escalation level]

RISKS/MITIGATIONS:
- [Risk ID]: [Description] — [Mitigation status]

NEXT WEEK:
- [Planned tasks]

BUDGET STATUS:
- Hours consumed: [N] / [Total]
- Phase hours consumed: [N] / [Phase total]
```

### 4.2 Gate Review Report

```
PHASE: [N] | GATE DATE: [YYYY-MM-DD]

DELIVERABLES STATUS:
- [D-XXX]: [COMPLETE/INCOMPLETE/BLOCKED]

EXIT CRITERIA:
- [Criterion]: [MET/NOT MET]

QUALITY METRICS:
- Test coverage: [N]%
- Type errors: [N]
- Security findings: [N critical, N high, N medium, N low]

DECISION: ☐ PASS  ☐ CONDITIONAL PASS  ☐ FAIL

CONDITIONS:
1. [Condition]

SIGN-OFF:
- PM: _____________ Date: _______
- Lead: ____________ Date: _______
- Director: ________ Date: _______
```

---

End of Document
