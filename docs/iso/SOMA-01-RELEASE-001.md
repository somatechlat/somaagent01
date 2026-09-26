# SOMAAGENT01 v2.0.0 — RELEASE NOTES

## Document Control

| Field | Value |
|-------|-------|
| Document Title | SomaAgent01 v2.0.0 Release Notes |
| Document Identifier | SOMA-01-RELEASE-001 |
| Version | 2.0.0 |
| Release Date | 2026-06-15 |
| Status | Release Candidate |
| Classification | Internal |

---

## 1. RELEASE SUMMARY

SomaAgent01 v2.0.0 is a major release focused on production readiness, security hardening, and comprehensive documentation. This release brings the system from pre-production (D+, ~45%) to release candidate (B, ~75%).

---

## 2. WHAT'S NEW

### 2.1 Security Hardening
- **Permissions check wired to real OPA + SpiceDB** — `/permissions/check` endpoint now calls real policy engines instead of returning stub `allowed: true`
- **Registration via Keycloak** — User registration creates real users in Keycloak via admin API
- **Password change via Keycloak** — Password change verifies current password and updates via Keycloak admin API
- **CSP headers** — Content-Security-Policy header added to all responses
- **RoleRequired returns 403** — Insufficient roles now returns 403 Forbidden (was 401 Unauthorized)
- **TenantRequired returns 403** — Missing tenant context now returns 403 Forbidden
- **Rate limiter fail-closed** — Rate limiter denies requests when Redis is unavailable (was fail-open)

### 2.2 Architecture Improvements
- **Adapters use DeploymentMode singleton** — Memory adapters use canonical `DeploymentMode.is_aaas()` instead of raw `SOMA_AAAS_MODE` env var
- **Tool call extraction** — Chat orchestrator tries native LLM `tool_calls` format first, with regex fallback
- **BrainBridge URL** — Uses `settings.SOMABRAIN_URL` instead of hardcoded Docker hostname
- **Rate limiter Redis URL** — Checks `SA01_REDIS_URL` first (canonical env var)
- **WebSocket auto-resolve** — ChatConsumer auto-resolves user's first active agent when URL has no `agent_id`

### 2.3 Testing
- **GitHub Actions CI pipeline** — 5 jobs: lint, typecheck, unit tests, security scan, docker build
- **5 new unit test files** — DeploymentMode (7 tests), CircuitBreaker (8 tests), UnifiedGate (8 tests), RateLimiter (4 tests), Auth (6 tests)
- **E2E integration tests** — 15 tests for full triad health, auth, memory flow, degradation
- **21 test files total** with 190 test functions

### 2.4 Infrastructure
- **Production-grade K8s manifests** — 2 replicas, 3 probes (liveness/readiness/startup), resource limits (500m-2CPU, 512Mi-2Gi), HPA (2-10), PDB (minAvailable: 1), topology spread
- **NetworkPolicy** — Ingress/egress rules for all service dependencies
- **ServiceMonitor** — Prometheus scraping every 15s
- **PrometheusRules** — 4 alerts: SomaAgentDown, HighLatency, HighErrorRate, CircuitBreakerOpen

### 2.5 Documentation
- **39 ISO-compliant documentation files** across 3 repos
- **169 formal requirements** (REQ-XXX-NNN) with traceability
- **10 ISO standards** covered per repo (42010, 29148, 12207, 16085, 27001, 19011, 31000, 9001, 25010)
- **7 project management documents** (charter, WBS, milestones, RACI, etc.)
- **Security pentest checklist** — 37 test cases
- **DR procedures** — 6 recovery scenarios
- **UAT checklist** — 22 acceptance test cases
- **Version compatibility matrix** — Synced across SomaAgent01, SomaBrain, SomaFractalMemory

---

## 3. BUG FIXES

| Fix | File | Description |
|-----|------|-------------|
| Permissions stub | `admin/permissions/api.py:332` | `/check` now calls real UnifiedGate |
| BrainBridge URL | `aaas/brain.py:92` | Uses settings instead of hardcoded hostname |
| Rate limiter URL | `services/common/rate_limiter.py:67` | Checks SA01_REDIS_URL first |
| RoleRequired | `admin/common/auth.py:278` | Returns 403 for insufficient roles |
| TenantRequired | `admin/common/auth.py:314` | Returns 403 for missing tenant |
| WebSocket agent_id | `services/gateway/consumers/chat.py:147` | Auto-resolves agent when missing |
| Tool calls | `admin/core/chat_orchestrator.py:490` | Native LLM format + regex fallback |

---

## 4. BREAKING CHANGES

| Change | Impact | Migration |
|--------|--------|-----------|
| `SOMA_AAAS_MODE` env var deprecated in adapters | Use `SA01_DEPLOYMENT_MODE` instead | Update environment configuration |
| Rate limiter fail-closed | Requests denied when Redis down | Ensure Redis is highly available |
| RoleRequired returns 403 | Clients expecting 401 for forbidden will get 403 | Update error handling |

---

## 5. KNOWN ISSUES

| Issue | Severity | Workaround |
|-------|----------|------------|
| MFA persistence not implemented | Medium | MFA endpoints return 503 |
| Password reset email not sent | Medium | Use password change instead |
| Frontend JWT in localStorage | Medium | Migrate to httpOnly cookies in next release |
| Conversation worker uses separate pipeline | Low | Documented, both pipelines work |
| Pyright type errors (~1400) | Low | Gradual reduction over next releases |

---

## 6. UPGRADE PATH

### From v1.1.0 to v2.0.0

1. Update environment variables:
   - Replace `SOMA_AAAS_MODE` with `SA01_DEPLOYMENT_MODE=AAAS` or `STANDALONE`
   - Ensure `SA01_REDIS_URL` is set (not just `REDIS_URL`)

2. Run migrations:
   ```bash
   python manage.py migrate
   ```

3. Update K8s manifests:
   - Apply new `deployment.yaml` with probes and limits
   - Apply `networkpolicy.yaml`
   - Apply `servicemonitor.yaml` and `prometheusrules.yaml`

4. Verify:
   ```bash
   curl http://localhost:63900/api/health/
   ```

---

## 7. COMPATIBILITY

| Component | Required Version |
|-----------|-----------------|
| SomaBrain | >= 0.2.0, < 0.3.0 |
| SomaFractalMemory | >= 0.2.0, < 0.3.0 |
| Python | >= 3.12, < 3.14 |
| PostgreSQL | >= 15 |
| Redis | >= 7.0 |
| Keycloak | >= 24 |

---

End of Document
