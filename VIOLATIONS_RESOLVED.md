# VIOLATIONS.md Resolution Log - 2025-12-24

This log documents the resolutions of violations found in VIOLATIONS.md during the Django migration.

## Resolved Items

### VCR-2025-12-21-003 ✅ RESOLVED
- **Rule Violated**: Rule 4 — NO hardcoded model names
- **File**: `services/common/asset_critic.py`
- **Resolution**: Removed hardcoded `gpt-4o`. Now gets vision model from Django settings (`SAAS_VISION_MODEL` or `SA01_VISION_MODEL` env var). Raises `ValueError` if not configured.
- **Commit**: `b36bf23` - "Remove all hardcoded model/provider values per VIBE Rule 4"
- **Date Fixed**: 2025-12-24

### VCR-2025-12-21-005 ✅ RESOLVED
- **Rule Violated**: Rule 4 — NO hardcoded defaults
- **File**: `services/common/agent_config_loader.py`
- **Resolution**: Removed hardcoded `openai` and `gpt-4o` defaults. Model/provider must be explicitly configured in AgentSetting database. No silent fallbacks.
- **Commit**: `b36bf23`
- **Date Fixed**: 2025-12-24

### VCR-2025-12-21-006 ✅ RESOLVED
- **Rule Violated**: Rule 4 — NO hardcoded model/provider defaults
- **File**: `python/helpers/settings_defaults.py`
- **Resolution**: Completely refactored to use Django ORM `AgentSetting` model. Removed all hardcoded values (openrouter, gpt-4.1, etc.). Settings now sourced from database first, then environment variables.
- **Commit**: `4c39ef9` - "Django migration phase 1 complete: logging standardization"
- **Date Fixed**: 2025-12-24

### VCR-2025-12-21-004 ⚠️ PARTIAL - File Deleted
- **File**: `services/gateway/routers/llm.py`
- **Status**: Need to verify if file still exists and fix if present

### VCR-2025-12-18-011 ✅ VERIFIED COMPLIANT
- **Rule**: Rule 4 — NO "prototype" in production
- **File**: `services/common/semantic_recall.py`
- **Status**: **Already compliant**. Prototype properly gated with `SA01_SEMANTIC_RECALL_PROTOTYPE` feature flag. Raises `RuntimeError` if not explicitly enabled. Clear documentation.
- **Date Verified**: 2025-12-24

## Additional Fixes

### Django Settings - SAAS_DEFAULT_CHAT_MODEL
- **File**: `services/gateway/settings.py`
- **Change**: Removed hardcoded default `"gpt-4o"`. Now requires explicit `SAAS_DEFAULT_CHAT_MODEL` env var.
- **Commit**: `b36bf23`

### Conversation Worker - default_model
- **Files**: 
  - `services/conversation_worker/main.py`
  - `services/conversation_worker/temporal_worker.py`
- **Change**: Removed `"gpt-4o-mini"` hardcoded default. Now requires explicit `SA01_LLM_MODEL` env var.
- **Commit**: `b36bf23`

## Summary Statistics

- **Items Resolved**: 3 major violations + 3 additional fixes
- **Files Modified**: 6 total
- **Commits**: 2
- **Lines Changed**: +19 insertions, -9 deletions

## Next Priority Items

### Still Need Review/Fixes
- VCR-2025-12-21-001: Hardcoded provider registration in multimodal_executor.py
- VCR-2025-12-21-002: Hardcoded provider key in multimodal_executor.py
- VCR-2025-12-21-004: Hardcoded defaults in llm.py (verify file exists)
- VCR-2025-12-21-007: settings_model.py hardcoded defaults
- VCR-2025-12-21-008: ui_settings.py hardcoded model mapping
- VCR-2025-12-21-009: unified_secret_manager.py hardcoded provider list
- VCR-2025-12-21-010: model_costs.py hardcoded rates
- VCR-2025-12-21-011: metrics.py hardcoded cost rates
