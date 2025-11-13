# 🚨 PRODUCTION CLEANUP ANALYSIS - FOLDER BY FOLDER

## 🔴 CRITICAL ISSUES FOUND

### SPRINT 1: BROKEN IMPORTS & DEAD CODE
**Priority: P0 - BLOCKS PRODUCTION**

#### `/integrations/` vs `/python/integrations/` - DUPLICATE ARCHITECTURE
- **ISSUE**: Two separate integration folders with overlapping functionality
- **FILES**: 
  - `integrations/postgres.py` imports `python.integrations.postgres_client` (DELETED FILE)
  - `integrations/opa.py` vs `python/integrations/opa_middleware.py` (DUPLICATE)
  - `integrations/somabrain.py` vs `python/integrations/somabrain_client.py` (DUPLICATE)
- **ACTION**: Consolidate into single `/python/integrations/` folder

#### BROKEN IMPORTS - DELETED postgres_client.py
- **BROKEN FILES**:
  - `tests/unit/test_canonical_sse_routes.py:from python.integrations.postgres_client import postgres_pool`
  - `integrations/postgres.py:from python.integrations.postgres_client import postgres_pool as pool`
  - `services/gateway/health.py:from python.integrations.postgres_client import postgres_pool`
  - `services/gateway/circuit_breakers.py:from python.integrations.postgres_client import postgres_pool`
- **ACTION**: Fix all imports or create real postgres client

### SPRINT 2: UNUSED SERVICES & DEAD ARCHITECTURE
**Priority: P0 - RESOURCE WASTE**

#### UNUSED SERVICES IN DOCKER-COMPOSE
- **RUNNING**: conversation-worker, tool-executor, memory-replicator, memory-sync, gateway, outbox-sync
- **DEAD CODE**: 
  - `services/celery_worker/main.py` (493 bytes - minimal stub)
  - `services/delegation_gateway/main.py` (378 bytes - minimal stub)
  - `services/delegation_worker/main.py` (2.7KB but not in docker-compose)
- **ACTION**: Delete unused services or add to docker-compose

#### TEST UTILITIES IN PRODUCTION CODE
- **FILE**: `python/integrations/test_utils.py`
- **ISSUE**: Test utilities mixed with production integrations
- **ACTION**: Move to tests/ folder or delete

### SPRINT 3: CONFIGURATION CHAOS
**Priority: P1 - MAINTENANCE NIGHTMARE**

#### MULTIPLE ENV FILES
- `.env` (369 bytes)
- `.env.example` (1 byte - EMPTY)
- `.env.memory` (861 bytes)
- **ACTION**: Consolidate or document purpose

#### ROOT-LEVEL PYTHON FILES
- `agent.py` - Main entry point (KEEP)
- `models.py` - Pydantic models (KEEP)
- `initialize.py` - Setup script (VERIFY USAGE)
- `preload.py` - Preload script (VERIFY USAGE)  
- `prepare.py` - Preparation script (VERIFY USAGE)
- **ACTION**: Move utilities to proper folders

### SPRINT 4: SCRIPT BLOAT
**Priority: P2 - CLEANUP**

#### 20 SCRIPTS - MANY UNUSED
```
constitution_admin.py - Admin tool
e2e_quick.py - Testing
ensure_outbox_schema.py - DB setup
generate_missing_webui_files.py - Build tool
golden_trace.py - Testing
kafka_partition_scaler.py - Ops tool
memory_migrate.py - Migration
memory_monitor.py - Monitoring
migrate_profiles_to_gateway.py - Migration
persona_admin.py - Admin tool
persona_training.py - Training
preflight.py - Validation (FIXED)
prune_audit_repo.py - Cleanup
replay_session.py - Debug tool
run_webui_diff.py - Testing
runstack.py - Stack management
schema_smoke_test.py - Testing
session_backfill.py - Migration
test_memory_system.py - Testing
```
- **ACTION**: Categorize into /scripts/{admin,migration,testing,ops}/

## 🟡 ARCHITECTURAL ISSUES

### GATEWAY PATTERN VIOLATIONS
- Multiple services accessing databases directly
- No centralized authentication/authorization
- Mixed responsibilities in services

### MEMORY SYSTEM COMPLEXITY
- 3 separate memory services (replicator, sync, outbox-sync)
- Unclear data flow and dependencies
- Potential race conditions

## 📊 FILE COUNT BY DIRECTORY
```
python/     124 files (tools, integrations, helpers)
services/    85 files (9 services)
tests/       78 files (comprehensive test suite)
scripts/     20 files (admin, migration, testing)
integrations/ 6 files (DUPLICATE of python/integrations)
observability/ 3 files (logging, monitoring)
```

## 🎯 SPRINT BREAKDOWN

### SPRINT 1 (CRITICAL - 2 days)
1. Fix broken postgres_client imports
2. Consolidate integration folders
3. Remove dead services (celery_worker, delegation_gateway)

### SPRINT 2 (HIGH - 3 days)  
1. Organize scripts into categories
2. Move test utilities out of production code
3. Clean up root-level Python files

### SPRINT 3 (MEDIUM - 2 days)
1. Consolidate environment configuration
2. Document service dependencies
3. Remove unused configuration files

### SPRINT 4 (LOW - 1 day)
1. Final cleanup and documentation
2. Verify all imports work
3. Test production deployment

## 🚀 READY FOR DELETION

### IMMEDIATE DELETE
- `services/celery_worker/` (unused stub)
- `services/delegation_gateway/` (unused stub)
- `integrations/` folder (duplicate)
- `.env.example` (empty file)

### VERIFY THEN DELETE
- `services/delegation_worker/` (not in docker-compose)
- Multiple migration scripts (if migrations complete)
- Test-only scripts in production

## ✅ PRODUCTION READINESS CHECKLIST

- [ ] All imports resolve correctly
- [ ] No duplicate functionality
- [ ] Services match docker-compose
- [ ] Configuration is consolidated
- [ ] No test code in production paths
- [ ] Scripts are organized by purpose
- [ ] Dead code is removed
- [ ] Architecture is clean and documented

**TOTAL ESTIMATED CLEANUP TIME: 8 days**
**CRITICAL PATH: Fix imports first (blocks everything)**