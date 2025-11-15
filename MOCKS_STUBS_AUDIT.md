# Mocks, Stubs, Bypasses, and Shims Audit

## Critical Issues Found

### 1. **Conversation Worker - SLM Shim** ❌
**File**: `services/conversation_worker/main.py:295`
```python
self.slm = type("_Shim", (), {"api_key": None})()
```
**Issue**: Creates a fake shim object for backward compatibility with tests
**Action Required**: Remove this shim. Tests should not expect `self.slm.api_key`

### 2. **LLM Credentials Store - Compatibility Shim** ⚠️
**File**: `services/common/llm_credentials_store.py`
**Issue**: Entire file is a "compatibility shim" wrapping SecretManager
**Action Required**: 
- Remove this shim file completely
- Update all imports to use `SecretManager` directly
- No backward compatibility layers allowed

### 3. **Learning Module - Stub Fallbacks** ❌
**File**: `services/common/learning.py:66-69`
```python
# returned a stub when the deployment mode was "LOCAL", causing the
# public /v1/weights endpoint to surface a 502 in the test suite.
# For the purpose of these canonical tests we provide a deterministic
# stub regardless of the deployment mode.
```
**Issue**: Returns fake stub data when Somabrain fails
**Action Required**: Remove stub fallback. Let it fail properly or return empty dict with clear error logging

### 4. **Models.py - Browser-Use Shim** ⚠️
**File**: `models.py:28-39`
```python
# is not installed (e.g., in CI). The repository includes a lightweight shim
# the shim if it fails.
except Exception:  # pragma: no cover – fallback for CI/test environments
    # Import the shim module itself
```
**Issue**: Fallback shim for missing browser-use library
**Action Required**: Either require the library or fail cleanly - no shims

### 5. **Test Bypasses** ⚠️
**File**: `conftest.py:72,79`
```python
# No override is set here; tests rely on local fixtures and bypass gating.
# Ensure test mode flag is set so selective authorization uses bypass logic
```
**Issue**: Tests bypass authorization
**Action Required**: Tests should use real auth with test credentials, not bypasses

## Legitimate Uses (Keep These)

### ✅ Placeholder String Replacement
- `python/helpers/files.py` - Template variable replacement ({{variable}})
- `python/extensions/*` - Placeholder replacement in tool args
- These are legitimate template/variable substitution, not mocks

### ✅ Fallback for Missing Optional Dependencies
- `models.py:46` - Fallback for slim builds using langchain-core only
- This is acceptable for optional features

### ✅ Health Check Stub Factory Pattern
- `services/common/health_checks.py:36` - `stub_factory` parameter for gRPC health checks
- This is a legitimate factory pattern, not a mock

### ✅ TODO Variables (Not Stubs)
- `python/helpers/task_scheduler.py` - `todo` is a legitimate variable name for task lists
- Not a stub or placeholder

## Action Plan

### Immediate (Critical)
1. **Remove `self.slm` shim** from conversation_worker/main.py
2. **Delete `llm_credentials_store.py`** and update all imports to use SecretManager
3. **Remove stub fallback** from learning.py get_weights()

### Short-term (Important)
4. **Remove test bypasses** from conftest.py - use real auth with test tokens
5. **Fix browser-use shim** - either require it or fail cleanly

### Verification
```bash
# After fixes, verify no mocks/stubs remain:
grep -r -i -n --include="*.py" -E "(mock|stub|fake|bypass|shim)" . | \
  grep -v "node_modules" | \
  grep -v ".git" | \
  grep -v "__pycache__" | \
  grep -v "test" | \
  grep -v "placeholder" | \
  grep -v "# TODO" | \
  grep -v "stub_factory"
```

## Summary
- **3 Critical issues** requiring immediate removal
- **2 Important issues** requiring short-term fixes
- **4 Legitimate patterns** that should remain

**Status**: ❌ NOT COMPLIANT - Mocks and shims present in production code
