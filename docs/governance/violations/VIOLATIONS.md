# VIOLATIONS REGISTRY - somaAgent01

## Document Control
| Field | Value |
|-------|-------|
| **Created** | 2026-01-01 |
| **Auditor** | Kiro (All 7 Personas Active) |
| **Status** | IN_PROGRESS |

---

## Violation Categories

| Code | Category | Severity |
|------|----------|----------|
| V-MOCK | Mock/Stub/Placeholder | CRITICAL |
| V-TODO | TODO/FIXME/Incomplete | CRITICAL |
| V-HARD | Hardcoded Values | HIGH |
| V-FAKE | Fake Implementation | CRITICAL |
| V-FRAME | Wrong Framework (Alpine.js) | HIGH |
| V-MSG | Hardcoded User Strings | MEDIUM |
| V-DOC | Missing/Wrong Documentation | LOW |
| V-SEC | Security Issue | CRITICAL |

---

## Violations Found

| ID | File | Line | Code | Description | Status |
|----|------|------|------|-------------|--------|
| SA01-001 | `webui/src/views/saas-entity-views.ts` | 46-47 | V-TODO | `// TODO: Load from auth context or API` - Incomplete implementation | OPEN |
| SA01-002 | `webui/src/views/saas-entity-views.ts` | 48 | V-FAKE | `// For now, grant full permissions for demo` - Fake permissions | OPEN |
| SA01-003 | `webui/src/views/soma-enterprise-settings.ts` | 412 | V-TODO | `// Show success toast (TODO)` | OPEN |
| SA01-004 | `webui/src/views/soma-enterprise-settings.ts` | 415 | V-TODO | `// Show error toast (TODO)` | OPEN |
| SA01-005 | `webui/src/views/soma-tenants.ts` | 545-547 | V-TODO | `// TODO: Open edit modal` - Incomplete implementation | OPEN |
| SA01-006 | `admin/saas/api/users.py` | 292-294 | V-MOCK | `# Mock agent access (would query AgentUser model)` - Mock data | OPEN |
| SA01-007 | `admin/saas/api/users.py` | 302-304 | V-MOCK | `# Mock activity log (would query AuditLog)` - Mock data | OPEN |
| SA01-008 | `admin/saas/api/users.py` | 313-315 | V-MOCK | `# Mock sessions` - Mock data | OPEN |
| SA01-009 | `admin/auth/invitations.py` | 185-187 | V-FAKE | `return placeholder` - Placeholder response | OPEN |
| SA01-010 | `tests/django/test_infrastructure.py` | 9 | V-MOCK | `from unittest.mock import patch, MagicMock` - Mocks in tests | OPEN |
| SA01-011 | `tests/django/test_infrastructure.py` | 212-213 | V-MOCK | `request = MagicMock()` - Mock request object | OPEN |
| SA01-012 | `tests/django/test_admin_domain.py` | 9 | V-MOCK | `from unittest.mock import MagicMock, AsyncMock, patch` - Mocks in tests | OPEN |
| SA01-013 | `docker-compose.yml` | 618-619 | V-TODO | `# python manage.py run_conversation_worker (TODO)` | OPEN |
| SA01-014 | `admin/voice/api.py` | 299-305 | V-FAKE | `"""Placeholder for streaming transcription."""` - Placeholder endpoint | OPEN |
| SA01-015 | `admin/saas/api/settings.py` | 43-45 | V-FAKE | `# This is a placeholder - real implementation would use Django model` | OPEN |
| SA01-016 | `admin/saas/api/billing.py` | 313-315 | V-MOCK | `# For now, return mock confirmation` - Mock response | OPEN |
| SA01-017 | `webui/src/views/saas-billing.ts` | 7-9 | V-FAKE | `Lago API integration placeholders` - Placeholder integration | OPEN |
| SA01-018 | `docs/specs/somastack-unified-ui/tasks.md` | 355-357 | V-FRAME | Alpine.js component references (FORBIDDEN) | OPEN |
| SA01-019 | `docs/specs/somastack-unified-ui/tasks.md` | 373-375 | V-FRAME | Alpine.js component references (FORBIDDEN) | OPEN |
| SA01-020 | `docs/specs/somastack-unified-ui/tasks.md` | 398-400 | V-FRAME | Alpine.js component references (FORBIDDEN) | OPEN |
| SA01-021 | `docs/specs/agentskin-uix/design.md` | 26-27 | V-FRAME | `js/stores/theme-store.js (Alpine Store)` - Alpine.js reference | OPEN |
| SA01-022 | `docs/specs/agentskin-uix/design.md` | 93-95 | V-FRAME | `// Alpine.js store for theme state` - Alpine.js code | OPEN |
| SA01-023 | `docs/specs/agentskin-uix/design.md` | 112-114 | V-FRAME | `x-data="themeGallery"` - Alpine.js directive | OPEN |
| SA01-024 | `docs/legacy/CANONICAL_DESIGN.md` | 154-156 | V-FRAME | `Vanilla JS + Alpine.js (Reactive State)` - Alpine.js reference | OPEN |
| SA01-025 | `docs/legacy/CANONICAL_DESIGN.md` | 162-164 | V-FRAME | `Alpine.js x-data="$store.feature"` - Alpine.js directive | OPEN |
| SA01-026 | `prompts/memory.consolidation.sys.md` | 89-91 | V-FRAME | Alpine.js form validation example | OPEN |
| SA01-027 | `prompts/memory.keyword_extraction.sys.md` | 48-54 | V-FRAME | Alpine.js x-data example | OPEN |
| SA01-028 | `webui/src/views/saas-audit-log.ts` | 334 | V-HARD | `actor_email: 'hacker@suspicious.com'` - Hardcoded test data in production | OPEN |

---

## Summary

- **Total Violations:** 28
- **Critical (V-MOCK, V-TODO, V-FAKE):** 17
- **High (V-FRAME, V-HARD):** 10
- **Medium (V-MSG):** 0
- **Low (V-DOC):** 1

---

## Required Actions

### CRITICAL - Must Fix Immediately

1. **Remove all mocks from tests** - Tests MUST use real infrastructure (Redis, PostgreSQL, Keycloak)
2. **Replace placeholder implementations** - All `placeholder`, `mock`, `fake` code must be real
3. **Complete TODO items** - No TODOs allowed in production code

### HIGH - Fix Before Release

1. **Remove all Alpine.js references** - Lit 3.x Web Components ONLY
2. **Remove hardcoded test data** - Use proper test fixtures

### Documentation Updates Required

1. Update `docs/legacy/CANONICAL_DESIGN.md` - Remove Alpine.js, document Lit 3.x
2. Update `docs/specs/somastack-unified-ui/tasks.md` - Convert Alpine.js tasks to Lit
3. Update `docs/specs/agentskin-uix/design.md` - Remove Alpine.js examples

