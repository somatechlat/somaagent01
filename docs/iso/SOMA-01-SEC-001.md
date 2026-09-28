# SOMA-01-SEC-001 — Security Assessment Report

## Document Control

| Field | Value |
|-------|-------|
| Document Title | SomaAgent01 Security Assessment Report |
| Document Identifier | SOMA-01-SEC-001 |
| Version | 2.0.0 |
| Date | 2026-06-15 |
| Status | Active |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Confidential |
| ISO Reference | ISO/IEC 27001:2022 — Information Security Management Systems |

## Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2025-12-30 | SomaTech Engineering | Initial security assessment |
| 1.1.0 | 2026-06-01 | SomaTech Engineering | Updated findings; documented initial remediations |
| 2.0.0 | 2026-06-15 | SomaTech Engineering | Code-verified deep analysis; mapped controls to ISO 27001 Annex A; verified security fixes |

---

## 1. Executive Summary

This security assessment evaluates the SomaAgent01 platform against ISO/IEC 27001:2022 Annex A controls. The system demonstrates significant security improvements since the May 2026 audit, with critical controls now implemented (fail-closed rate limiting, real OPA/SpiceDB authorization, hardened secret key management). However, critical gaps remain: an authorization bypass in the permissions API endpoint, insufficient test coverage, and missing CI/CD security scanning.

**Overall Security Posture: C+ (60%)**

---

## 2. ISO 27001 Annex A Control Mapping

### 2.1 A.5 — Organizational Controls

| Control | ID | Requirement | Status | Evidence |
|---------|----|-------------|--------|----------|
| Policies for information security | A.5.1 | Documented security policies | Partial | VIBE coding rules exist (`docs/standards/SOMA-STD-CODING-001.md`); no formal ISMS policy |
| Roles and responsibilities | A.5.2 | Defined security roles | Partial | `admin/aaas/models.py` defines tenant roles; no formal security role assignments |
| Segregation of duties | A.5.3 | Duty separation enforced | Partial | Multi-tenant isolation via Django ORM; no formal segregation matrix |
| Management responsibilities | A.5.4 | Management direction for security | Partial | Documented in audit reports; no formal management review records |
| Contact with authorities | A.5.5 | Incident reporting procedures | Gap | No documented incident response procedure |
| Threat intelligence | A.5.7 | Threat monitoring | Gap | No threat intelligence integration |
| Information security in project management | A.5.8 | Security in SDLC | Partial | Audit process exists; no automated security gates |
| Inventory of information assets | A.5.9 | Asset inventory | Partial | Component inventory exists (`docs/reports/SOMA-RPT-INVENTORY-001.md`); not maintained as formal asset register |
| Acceptable use of information | A.5.10 | Acceptable use policies | Gap | No formal acceptable use policy |
| Access control | A.5.15 | Access control policy | Partial | SpiceDB schema defined; RBAC API endpoints partially stubbed |
| Authentication | A.5.17 | Strong authentication | **Implemented** | Keycloak OIDC, JWT RS256, MFA support |
| Information transfer | A.5.14 | Secure data transfer | Partial | HTTPS assumed via reverse proxy; no TLS at application layer |

### 2.2 A.6 — People Controls

| Control | ID | Requirement | Status | Evidence |
|---------|----|-------------|--------|----------|
| Screening | A.6.1 | Background verification | N/A | Internal platform; personnel screening is organizational |
| Terms of employment | A.6.2 | Security responsibilities | N/A | Organizational responsibility |
| Information security awareness | A.6.3 | Security training | Gap | No security training program documented |
| Disciplinary process | A.6.4 | Sanction policy | N/A | Organizational responsibility |
| Responsibilities after termination | A.6.5 | Post-employment duties | N/A | Organizational responsibility |
| Confidentiality agreements | A.6.6 | NDA requirements | N/A | Organizational responsibility |
| Remote working | A.6.7 | Remote work security | Partial | API access is authenticated; no VPN or network segmentation requirements documented |
| Information security event reporting | A.6.8 | Event reporting | Gap | No security event reporting mechanism beyond audit logs |

### 2.3 A.7 — Physical Controls

| Control | ID | Requirement | Status | Evidence |
|---------|----|-------------|--------|----------|
| Physical security perimeters | A.7.1 | Facility security | N/A | Cloud/Docker deployment; infrastructure provider responsibility |
| Physical entry controls | A.7.2 | Access restrictions | N/A | Infrastructure provider responsibility |
| Securing offices and facilities | A.7.3 | Facility security | N/A | Infrastructure provider responsibility |
| Physical security monitoring | A.7.4 | Surveillance | N/A | Infrastructure provider responsibility |
| Protecting against physical threats | A.7.5 | Environmental controls | N/A | Infrastructure provider responsibility |

### 2.4 A.8 — Technical Controls

| Control | ID | Requirement | Status | Evidence |
|---------|----|-------------|--------|----------|
| User endpoint devices | A.8.1 | Endpoint security | N/A | Client responsibility |
| Privileged access rights | A.8.2 | Privileged access management | Partial | Keycloak admin roles; no formal PAM process |
| Information access restriction | A.8.3 | Access control enforcement | **Implemented** | `UnifiedGate` (OPA + SpiceDB + Scope), fail-closed |
| Access to source code | A.8.4 | Source code protection | Partial | Git repository access control; no branch protection rules verified |
| Secure authentication | A.8.5 | Authentication mechanisms | **Implemented** | Keycloak OIDC, JWT RS256, PKCE, account lockout (5 attempts/15 min) |
| Capacity management | A.8.6 | Resource monitoring | Partial | Prometheus + Grafana partially wired; no capacity alerts |
| Protection against malware | A.8.7 | Malware protection | Gap | No container image scanning; no dependency vulnerability scanning |
| Management of technical vulnerabilities | A.8.8 | Vulnerability management | **Implemented** | Settings.py:37 hardened SECRET_KEY; settings.py:142 no SQLite fallback; rate_limiter.py:186–196 fail-closed |
| Configuration management | A.8.9 | Secure configuration | Partial | `config/settings_registry.py` centralizes settings; `ALLOW_INSECURE_AUTH_BYPASS` removed |
| Information deletion | A.8.10 | Data disposal | Gap | No data retention or deletion policies implemented |
| Data masking | A.8.11 | Data anonymization | Gap | No PII masking in logs or responses |
| Data leakage prevention | A.8.12 | DLP measures | Gap | No DLP controls |
| Information backup | A.8.13 | Backup procedures | Gap | No backup procedures documented or automated |
| Redundancy of information processing | A.8.14 | Redundancy | Gap | Single-instance deployments; no failover |
| Logging | A.8.15 | Audit logging | Partial | `OutboxMessage` model exists; not wired to all endpoints |
| Monitoring activities | A.8.16 | Security monitoring | Partial | Health monitor exists; no SIEM integration |
| Clock synchronization | A.8.17 | Time synchronization | Gap | No NTP configuration documented |
| Use of privileged utility programs | A.8.18 | Privileged tool access | N/A | Container-based deployment |
| Installation of software | A.8.19 | Software control | Partial | `pyproject.toml` + `requirements.txt` define dependencies; no lock file verification |
| Networks security | A.8.20 | Network controls | Partial | Docker networking; no network segmentation policy |
| Security of network services | A.8.21 | Service security | Partial | Port namespace separation (20xxx/63xxx); no network policies |
| Segregation of networks | A.8.22 | Network segmentation | Gap | No network segmentation between services |
| Web filtering | A.8.23 | Outbound filtering | Gap | No outbound traffic filtering |
| Use of cryptography | A.8.24 | Cryptographic controls | **Implemented** | JWT RS256, `secrets.token_urlsafe(50)` for SECRET_KEY |
| Secure development lifecycle | A.8.25 | SDLC security | Partial | VIBE rules prohibit mocks/stubs; no SAST/DAST integration |
| Application security requirements | A.8.26 | App security | Partial | Django security middleware; `ALLOW_INSECURE_AUTH_BYPASS` removed |
| Secure system architecture | A.8.27 | Architecture security | **Implemented** | `UnifiedGate` fail-closed; rate limiter fail-closed; circuit breakers |
| Secure coding | A.8.28 | Coding standards | Partial | VIBE rules define standards; 2.8% test coverage undermines verification |
| Security testing in development | A.8.29 | Security testing | Gap | No security testing in development pipeline |
| Outsourced development | A.8.30 | Third-party development | N/A | In-house development |
| Separation of environments | A.8.31 | Environment isolation | Partial | Standalone/AAAS mode separation; no formal dev/staging/prod separation |
| Change management | A.8.32 | Change control | Gap | No formal change management process |
| Test information | A.8.33 | Test data protection | Gap | No test data anonymization |
| Protection during audit testing | A.8.34 | Audit safeguards | Partial | Audit testing uses real infrastructure per VIBE rules |

---

## 3. Vulnerability List

### 3.1 Critical Vulnerabilities

| ID | Vulnerability | CVSS (est.) | File:Line | Status |
|----|--------------|-------------|-----------|--------|
| VULN-001 | Authorization bypass: permissions API returns `allowed:true` unconditionally | 9.1 | `admin/permissions/api.py:336` | **Open** |
| VULN-002 | WebSocket routing broken: `agent_id` not provided by frontend | 8.6 | `services/gateway/consumers/chat.py:136` | **Open** |
| VULN-003 | Django migrations out of sync | 8.1 | `admin/aaas/migrations/`, `admin/core/migrations/` | **Open** |

### 3.2 High Vulnerabilities

| ID | Vulnerability | CVSS (est.) | File:Line | Status |
|----|--------------|-------------|-----------|--------|
| VULN-004 | No CI/CD security scanning | 7.5 | N/A (`.github/workflows/` missing) | **Open** |
| VULN-005 | 2.8% test coverage undermines security verification | 7.0 | 15 test files / 528+ source files | **Open** |
| VULN-006 | Path dependency on `somabrain` | 6.5 | `pyproject.toml:21` | **Open** |
| VULN-007 | RoleRequired returns 401 instead of 403 | 6.0 | `admin/common/auth.py:277` | **Open** |

### 3.3 Medium Vulnerabilities

| ID | Vulnerability | CVSS (est.) | File:Line | Status |
|----|--------------|-------------|-----------|--------|
| VULN-008 | Hardcoded Docker hostname fallback | 5.0 | `aaas/brain.py:92` | **Open** |
| VULN-009 | Inconsistent Redis env var (`REDIS_URL` vs `SA01_REDIS_URL`) | 4.5 | `services/common/rate_limiter.py:67` | **Open** |
| VULN-010 | Regex-based tool call extraction | 4.0 | `admin/core/chat_orchestrator.py:750` | **Open** |
| VULN-011 | No TLS at application layer | 5.5 | N/A | **Open** |
| VULN-012 | No dependency vulnerability scanning | 5.0 | N/A | **Open** |
| VULN-013 | No data retention/deletion policy | 4.5 | N/A | **Open** |

### 3.4 Resolved Vulnerabilities

| ID | Vulnerability | Resolution | File:Line | Status |
|----|--------------|------------|-----------|--------|
| VULN-R01 | Hardcoded SECRET_KEY | `secrets.token_urlsafe(50)` + ValueError in prod | `settings.py:37` | **Fixed** |
| VULN-R02 | SQLite fallback | ValueError on bad DSN | `settings.py:142` | **Fixed** |
| VULN-R03 | Rate limiter fail-open | Returns `allowed=False` on Redis error | `rate_limiter.py:186–196` | **Fixed** |
| VULN-R04 | JSON blob authorization | Real OPA/SpiceDB calls via UnifiedGate | `unified_gate.py:130–207` | **Fixed** |
| VULN-R05 | NotImplementedError in recall() | Implemented for direct + HTTP modes | `brain.py:132–161` | **Fixed** |
| VULN-R06 | No JWT audience verification | Controlled by JWT_ISSUER_STRICT | `auth.py:195–210` | **Fixed** |
| VULN-R07 | ALLOW_INSECURE_AUTH_BYPASS | Removed entirely | `settings.py:235–236` | **Fixed** |
| VULN-R08 | Rate limiter fail-open | Fail-closed on Redis error | `rate_limiter.py:186–196` | **Fixed** |
| VULN-R09 | Inaccurate token counting | tiktoken integration | `chat_orchestrator.py:52–59` | **Fixed** |
| VULN-R10 | No circuit breakers | Circuit breakers on SomaBrain + LLM | `chat_orchestrator.py:149–152` | **Fixed** |

---

## 4. Security Architecture Assessment

### 4.1 Authentication Chain

```
Client → Login Endpoint → Keycloak OIDC → JWT RS256 → decode_token() → AuthBearer
                                        ↑                                    ↓
                              PKCE implemented                      UnifiedGate (OPA + SpiceDB)
                              Account lockout (5/15min)             require_permission()
                              JWT_ISSUER_STRICT (verify_aud)
```

**Assessment:** Authentication chain is well-implemented. Key fixes verified: PKCE, account lockout, audience verification, insecure bypass removal.

### 4.2 Authorization Chain

```
Request → AuthBearer → UnifiedGate → PolicyClient (HTTP/OPA)
                                 └→ SpiceDBClient (gRPC/SpiceDB)
                                 └→ Scope validation
                                 └→ Fail-closed on any error
```

**Assessment:** UnifiedGate is correctly implemented with real policy engine calls and fail-closed behavior. However, the permissions API endpoint (`admin/permissions/api.py:336`) bypasses this entire chain by returning `allowed:true` unconditionally. This is a **critical gap** that undermines the authorization architecture.

### 4.3 Data Protection

| Layer | Protection | Status |
|-------|-----------|--------|
| In Transit | TLS (reverse proxy assumed) | Not enforced at app level |
| At Rest | PostgreSQL native encryption | Not configured |
| In Processing | Django ORM parameterized queries | Implemented |
| Session | Redis-backed, 15-min TTL | Implemented |
| Tokens | httpOnly cookies, RS256 | Implemented |
| Secrets | Vault + secrets.token_urlsafe | Implemented |

### 4.4 Security Monitoring

| Capability | Implementation | Status |
|-----------|---------------|--------|
| Health monitoring | `services/common/health_monitor.py` | Implemented |
| Audit logging | `OutboxMessage` model | Partial — not wired to all endpoints |
| Rate limiting | `RedisRateLimiter` (fail-closed) | Implemented |
| Circuit breaking | `CircuitBreaker` on SomaBrain + LLM | Implemented |
| Prometheus metrics | Partially wired | Partial |
| SIEM integration | None | Gap |
| Alerting | None | Gap |

---

## 5. Compliance Status Summary

| Domain | Controls Assessed | Implemented | Partial | Gap | Compliance |
|--------|------------------|-------------|---------|-----|------------|
| A.5 Organizational | 11 | 1 | 7 | 3 | 23% |
| A.6 People | 8 | 0 | 1 | 1 | 6% |
| A.7 Physical | 5 | 0 | 0 | 0 | N/A (cloud) |
| A.8 Technical | 34 | 6 | 12 | 16 | 35% |
| **Total** | **58** | **7** | **20** | **20** | **~25%** |

**Note:** Many A.6 (People) and A.7 (Physical) controls are organizational or infrastructure-provider responsibilities and are marked N/A for this software assessment. Technical controls (A.8) compliance at 35% is the primary concern.

---

## 6. Recommendations

### 6.1 Immediate (Critical)

1. **Fix authorization bypass** (`admin/permissions/api.py:336`) — Wire to UnifiedGate
2. **Fix WebSocket routing** — Add `agent_id` to frontend WebSocket URL
3. **Generate and commit Django migrations** — Sync `admin/aaas` and `admin/core`

### 6.2 Short-Term (High)

4. **Establish CI/CD security scanning** — Add SAST (bandit), dependency scanning (safety/pip-audit), container scanning
5. **Increase test coverage** — Target 40% within 6 weeks, focusing on security-critical paths
6. **Implement TLS at application layer** or document reverse proxy TLS requirements
7. **Add dependency vulnerability scanning** to build pipeline

### 6.3 Medium-Term (Moderate)

8. **Wire audit logging** to all API endpoints via outbox pattern
9. **Implement data retention and deletion** policies
10. **Add SIEM integration** for security event aggregation
11. **Document incident response** procedures
12. **Implement network segmentation** policies for K8s deployment

---

End of Document
