# CRITICAL: Django Compliance Audit Report

## ❌ MAJOR VIOLATIONS FOUND

### Root-Level Python Files (CRITICAL VIOLATION)

These files bypass Django framework entirely and must be migrated to Django apps:

| File | Lines | Issue | Migration Target |
|------|-------|-------|------------------|
| **models.py** | 1,247 | Custom LLM wrapper, bypasses Django ORM | `admin/llm/` Django app |
| **agent.py** | 560 | Agent orchestrator outside Django | `admin/agents/` Django app |
| **initialize.py** | 169 | Custom initialization bypassing Django | Django management command |
| **preload.py** | ? | Custom preload logic | Django `AppConfig.ready()` |

**VIBE Rule Violated:** Rule 8 - Django capabilities ONLY  
**Impact:** Entire agent system operates outside Django framework

---

### python/ Directory Structure (145 Files - CRITICAL)

Custom framework that duplicates Django functionality:

#### python/somaagent/ (19 files)
**Entire agent logic outside Django - should be Django app:**
- `agent_context.py` - Should use Django ORM models
- `conversation_orchestrator.py` - Should be Django service
- `input_processor.py` - Should be Django Ninja endpoint
- `response_generator.py` - Should be Django service
- `tool_selector.py` - Should use Django ORM
- `context_builder.py` - Should be Django middleware
- `error_handler.py` - Should use Django exception handling
- `cognitive.py` - Should be Django service
- `agentiq_*.py` - Should be Django metrics/signals

**Migration:** Create `admin/agents/` Django app with proper models/services

#### python/tools/ (19 files)
**Custom tool implementations outside Django:**
- Should be Django Ninja API endpoints in `admin/tools/api.py`
- Tool models should be Django ORM models
- Tool execution should use Django services

#### python/helpers/ (67 files)  
**Custom helpers bypassing Django utilities:**
- `log.py` - Use Django logging
- `settings.py`, `settings_defaults.py` - Use Django settings/ORM ✅ PARTIALLY FIXED
- `dotenv.py` - Use Django environ
- Many utils should be Django utilities or removed

**Files to Review:**
- 67 helper files need individual Django migration assessment
- Many may duplicate Django functionality

#### python/observability/ (3 files)
- `metrics.py` - Should use Django signals + prometheus_client
- `event_publisher.py` - Should use Django signals
- Should integrate with Django middleware

#### python/extensions/ (32 files)
- Custom hook system - Should use Django signals
- Hook files in subdirectories should be Django signal receivers

---

### src/ Directory (51 Files - CRITICAL)

Non-Django code structure:

#### src/core/ (38 files estimated)
**Core domain logic outside Django**
- Should be Django apps in `admin/core/`
- Needs complete restructure to Django patterns

#### src/voice/ (10 files estimated)  
**Voice services outside Django**
- Should be Django app: `admin/voice/`
- Voice endpoints should be Django Ninja APIs

#### src/context_client.py (4,237 bytes)
**Custom HTTP client**
- Should use Django's HTTP clients or requests library
- If API client, should be Django Ninja client

---

## ✅ POSITIVE FINDINGS

### What IS Django-Compliant

| Area | Status |
|------|--------|
| No Flask imports | ✅ CLEAN |
| No FastAPI imports | ✅ CLEAN |
| No SQLAlchemy imports | ✅ CLEAN |
| `admin/` directory | ✅ Proper Django apps structure |
| `services/` directory | ✅ Uses Django (with some violations fixed) |
| Django ORM models | ✅ 23 models in `admin/core/models.py`, `admin/saas/models/` |
| Django Ninja APIs | ✅ APIs in `admin/*/api.py` |

---

## Migration Priority Rankings

### PRIORITY 1: BLOCKING (Must fix immediately)
1. **Root-level files** - `models.py`, `agent.py`, `initialize.py`, `preload.py`
2. **python/somaagent/** - Core agent logic outside Django
3. **python/tools/** - Tool implementations outside Django

### PRIORITY 2: HIGH (Major framework violations)
4. **python/helpers/** - 67 files bypassing Django utilities
5. **src/core/** - Domain logic outside Django
6. **src/voice/** - Voice services outside Django

### PRIORITY 3: MEDIUM (Infrastructure)
7. **python/observability/** - Metrics/events should use Django signals
8. **python/extensions/** - Hook system should use Django signals
9. **orchestrator/** directory - Needs Django review

---

## Migration Strategy

### Phase 1: Root Files → Django Apps (IMMEDIATE)
```
models.py → admin/llm/models.py + admin/llm/services.py
agent.py → admin/agents/models.py + admin/agents/services.py
initialize.py → admin/agents/management/commands/initialize.py
preload.py → admin/agents/apps.py (AppConfig.ready())
```

### Phase 2: python/somaagent → admin/agents Django App
```
python/somaagent/* → admin/agents/
  - agent_context.py → admin/agents/models.py
  - conversation_orchestrator.py → admin/agents/services/orchestrator.py
  - tool_selector.py → admin/agents/services/tools.py
  - etc.
```

### Phase 3: python/tools → admin/tools Django App
```
python/tools/* → admin/tools/
  - catalog.py → admin/tools/registry.py
  - *.py → admin/tools/api.py (Django Ninja endpoints)
```

### Phase 4: Clean Up python/helpers
- Review all 67 files
- Migrate to Django equivalents or delete
- Keep only truly custom utilities

### Phase 5: src/ → admin/ Django Apps
```
src/core/* → admin/core/*
src/voice/* → admin/voice/*
src/context_client.py → DELETE or integrate properly
```

---

## Estimated Effort

| Phase | Files | Lines of Code | Effort |
|-------|-------|---------------|--------|
| Phase 1 | 4 | ~2,000 | 2-3 days |
| Phase 2 | 19 | ~5,000 | 3-5 days |
| Phase 3 | 19 | ~3,000 | 2-3 days |
| Phase 4 | 67 | ~15,000 | 5-7 days |
| Phase 5 | 51 | ~8,000 | 4-6 days |
| **TOTAL** | **160** | **~33,000** | **16-24 days** |

---

## IMMEDIATE ACTION REQUIRED

The repository has a **complete custom framework running parallel to Django**. This violates VIBE Rule 8: "Django capabilities ONLY".

**Recommended:**
1. Stop all new feature development
2. Complete Django migration immediately  
3. Delete all non-Django code after migration
4. Establish strict code review process

**Current State:** ~20% Django compliant  
**Target State:** 100% Django compliant per VIBE rules
