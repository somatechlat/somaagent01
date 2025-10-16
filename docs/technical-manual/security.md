---
title: Security & Compliance Baseline
slug: technical-security
version: 1.0.0
last-reviewed: 2025-10-15
audience: security, platform-engineers
owner: security-engineering
reviewers:
  - platform-architecture
  - compliance
prerequisites:
  - Access to Vault policies
  - Familiarity with Soma SOC2 controls
verification:
  - Security controls validated in quarterly audit
  - Secrets rotation logged in change log
---

# Security & Compliance Baseline

This document defines the authentication, authorization, secrets, and compliance expectations for SomaAgent01. It aligns with Soma's SOC2 roadmap and internal control framework.

## 1. Authentication

- **User-facing UI:** Basic auth configurable in **Settings → Authentication**. Enforce strong passwords and rotate quarterly.
- **Service-to-service:** JWT tokens issued by the Auth service. Tokens validated by gateway middleware and OPA policies.
- **CLI/API clients:** Support personal access tokens derived from the Auth service.

## 2. Authorization

- OPA policies stored in `policy/` and distributed via bundles.
- Default stance: deny unless policy grants access.
- Policies include:
  - Route-based access controls.
  - Tool execution scopes.
  - Audit log retention rules.

## 3. Secrets Management

- Vault stores API keys, database credentials, and signing keys.
- Helm charts inject secrets using Vault Agent sidecars.
- Local development uses `.env`; never commit secrets to version control.
- Rotation cadence: 90 days for API keys, 180 days for signing keys.

## 4. Data Protection

- **Data in transit:** TLS enforced for external endpoints; mTLS configurable between services.
- **Data at rest:**
  - Redis backed by encrypted volumes in production.
  - Kafka topics using disk encryption on managed clusters.
  - Qdrant snapshots stored in encrypted object storage.
- **Backups:** Stored encrypted, with access limited to SRE.

## 5. Logging & Monitoring

- Audit logs emitted for authentication events, policy decisions, and tool executions.
- Logs shipped to Loki with retention policy of 30 days (dev) and 180 days (prod).
- Alert thresholds defined in `infra/observability/alerts.yml`.

## 6. Vulnerability Management

- Container image scans via Trivy integrated into CI.
- Dependency scans for Python (`pip-audit`) and Node (`npm audit`) run weekly.
- Critical CVEs trigger immediate patch cycle; log details in [`docs/changelog.md`](../changelog.md).

## 7. Compliance Mapping

| Control | Implementation |
| ------- | -------------- |
| SOC2 CC6.1 (Logical Access) | Auth + OPA policy enforcement |
| SOC2 CC7.2 (Change Management) | GitHub PR reviews + CI workflows |
| SOC2 CC8.1 (System Operations) | Observability stack, alerts, runbooks |
| SOC2 CC9.2 (Risk Mitigation) | Vulnerability scans + patch policy |

## 8. Incident Response

1. Detect via alerts or reports.
2. Create incident ticket with severity and impact.
3. Contain (revoke keys, scale down services).
4. Eradicate (patch, redeploy).
5. Recover (validate health, inform stakeholders).
6. Post-incident review within 5 business days; capture actions in change log.

## 9. Verification Checklist

- [ ] Vault tokens rotated.
- [ ] Auth service keys rotated.
- [ ] Policy bundles validated with `opa test`.
- [ ] Trivy scans clear of critical CVEs.
- [ ] Incident response drills executed within SLA.
