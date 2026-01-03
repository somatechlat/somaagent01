# SomaAgent01 — Merged Tasks & Requirements

**Document:** TASKS-MERGED-SOMAAGENT01.md  
**Version:** 1.0.0  
**Date:** 2026-01-03  
**Source:** Merged from all SRS files in somaAgent01

---

## Quick Reference

| Metric | Value |
|--------|-------|
| Total SRS Files | 35+ |
| Total UI Screens | 66 |
| Implemented | 12 (18%) |
| VIBE Compliance | 98% |
| Priority P0 Tasks | 18 |

---

## 1. Capsule System Tasks (P0)

### 1.1 AgentCapsuleCreator UI
| Task | Effort | Status |
|------|--------|--------|
| Create `<agent-capsule-creator>` root component | 1d | ❌ |
| Create `<capsule-identity-panel>` (Soul editor) | 1d | ❌ |
| Create `<capsule-capability-panel>` (Body editor) | 1d | ❌ |
| Create `<capsule-governance-panel>` (Constitution) | 0.5d | ❌ |
| Create `<capsule-preview-card>` (Summary) | 0.5d | ❌ |

### 1.2 Registry Service Tests
| Task | Effort | Status |
|------|--------|--------|
| Unit tests for `certify_capsule()` | 0.5d | ❌ |
| Unit tests for `verify_capsule_integrity()` | 0.5d | ❌ |
| Integration test: full signing flow | 1d | ❌ |

### 1.3 Security Improvements
| Task | Effort | Status |
|------|--------|--------|
| Vault integration for SOMA_REGISTRY_PRIVATE_KEY | 0.5d | ❌ |
| Add `parent_id` FK for version lineage | 0.5d | ❌ |
| Key rotation mechanism | 2d | ❌ |

---

## 2. Authentication Tasks (P0)

### 2.1 From SRS-AUTHENTICATION.md
| Task | Effort | Status |
|------|--------|--------|
| Complete SpiceDB permission decorators | 2h | ⚠️ Partial |
| Account lockout after 5 failures | 2h | ❌ |
| PKCE for OAuth code exchange | 2h | ❌ |
| Token blacklist on logout | 1h | ⚠️ Partial |

### 2.2 Session Management
| Task | Effort | Status |
|------|--------|--------|
| Redis-backed SessionManager | 3h | ❌ |
| Session statistics endpoint | 1h | ⚠️ Placeholder |
| Force logout all sessions | 1h | ⚠️ Placeholder |

---

## 3. Chat & Conversation Tasks (P0)

| Task | Effort | Status |
|------|--------|--------|
| Real ChatService with SomaBrain integration | 1d | ❌ |
| WebSocket consumer (Django Channels) | 2d | ❌ |
| Conversation persistence to PostgreSQL | 0.5d | ⚠️ Partial |
| Message streaming via SSE | 1d | ❌ |

---

## 4. Infrastructure UI Tasks (P1)

### 4.1 From SRS-MASTER-INDEX.md
| Screen | Route | Status |
|--------|-------|--------|
| Infrastructure Dashboard | `/platform/infrastructure` | ❌ |
| Redis Admin | `/platform/infrastructure/redis` | ❌ |
| Rate Limit Editor | `/platform/infrastructure/redis/ratelimits` | ❌ |
| Temporal Admin | `/platform/infrastructure/temporal` | ❌ |
| MCP Registry | `/platform/infrastructure/mcp` | ❌ |

### 4.2 Metrics Screens
| Screen | Route | Status |
|--------|-------|--------|
| Platform Metrics | `/platform/metrics` | ❌ |
| LLM Metrics | `/platform/metrics/llm` | ❌ |
| Tool Metrics | `/platform/metrics/tools` | ❌ |
| Memory Metrics | `/platform/metrics/memory` | ❌ |

---

## 5. Voice WebSocket (P1)

| Task | Effort | Status |
|------|--------|--------|
| Voice WebSocket consumer | 2d | ❌ Placeholder |
| Real-time audio streaming | 1d | ❌ |
| Whisper STT integration | 0.5d | ⚠️ |
| Kokoro TTS integration | 0.5d | ⚠️ |

---

## 6. Multi-tenant SaaS (P1)

### 6.1 From SRS-SAAS-TENANT-CREATION.md
| Task | Effort | Status |
|------|--------|--------|
| Tenant creation wizard (5 steps) | 2d | ⚠️ Partial |
| TenantSettings model | 0.5d | ❌ |
| Tenant usage tracking | 1d | ❌ |

### 6.2 From SRS-UNIFIED-SAAS.md
| Task | Effort | Status |
|------|--------|--------|
| StandAlone mode toggle | 0.5d | ✅ |
| SomaStackClusterMode detection | 0.5d | ✅ |
| Tenant isolation middleware | 1d | ✅ |

---

## 7. Implementation Phases

### Phase 1: Capsule System (Week 1-2)
- [ ] AgentCapsuleCreator UI components
- [ ] RegistryService tests
- [ ] Vault integration

### Phase 2: Auth Completion (Week 2-3)
- [ ] SessionManager
- [ ] SpiceDB decorators
- [ ] Account lockout

### Phase 3: Chat & Voice (Week 3-4)
- [ ] ChatService + WebSocket
- [ ] Voice streaming

### Phase 4: Infrastructure UI (Week 4-5)
- [ ] All `/platform/infrastructure/*` screens
- [ ] Metrics dashboards

---

## 8. Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `webui/src/views/agent-capsule-creator.ts` | CREATE | Main UI |
| `admin/capsules/api/capsules.py` | IMPLEMENT | REST endpoints |
| `tests/unit/test_registry_service.py` | CREATE | Unit tests |
| `admin/common/session_manager.py` | CREATE | Redis sessions |
| `services/common/chat_service.py` | IMPLEMENT | SomaBrain integration |

---

**Total Effort Estimate:** 15-20 developer days

---

*END OF MERGED TASKS — SOMAAGENT01*
