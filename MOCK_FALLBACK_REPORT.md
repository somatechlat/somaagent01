# MOCK, FALLBACK, SHIM & BYPASS REMOVAL REPORT

**Generated:** $(date)
**Repository:** somaAgent01
**Scan Scope:** Entire repository (excluding node_modules, .git, vendor files)

---

## EXECUTIVE SUMMARY

This report identifies ALL instances of mocks, fallbacks, shims, bypasses, and fake implementations across the codebase. These patterns violate the "REAL DATA, REAL SERVERS, REAL EVERYTHING" principle.

**Total Candidates Found:** 15 critical areas

---

## 🔴 CRITICAL REMOVALS REQUIRED

### 1. **Postgres Client Stub** 
**File:** `python/integrations/postgres_client.py`
**Lines:** 28-90
**Type:** Test stub/mock
**Issue:** Contains `_StubConn`, `_StubAcquire`, `_StubPool` classes that fake database operations during tests
**Code:**
```python
class _StubConn:
    async def execute(self, *args, **kwargs):
        raise RuntimeError("postgres_client stub: attempted DB operation in test mode")
    async def fetchval(self, *args, **kwargs):
        return 1  # FAKE RETURN VALUE
```
**Action:** REMOVE ALL stub classes. Use real Postgres in tests.

---

### 2. **Vision Tool Dummy Response**
**File:** `python/tools/vision_load.py`
**Type:** Fake/dummy data
**Issue:** Returns dummy response instead of real data
**Code:**
```python
return Response(message=\"dummy\", break_loop=False)
```
**Action:** REMOVE dummy return. Implement real vision processing or fail explicitly.

---

### 3. **MCP Handler Dummy Exceptions**
**File:** `python/helpers/mcp_handler.py`
**Type:** Fake exception handling
**Issue:** Creates dummy exceptions to break async flow
**Code:**
```python
# Store the original exception and raise a dummy exception
raise RuntimeError(\"Dummy exception to break out of async block\")
# Check if this is our dummy exception
```
**Action:** REMOVE dummy exception pattern. Use proper async control flow.

---

### 4. **Browser Use Lightweight Stub**
**File:** `python/helpers/browser_use_monkeypatch.py`
**Type:** Developer stub
**Issue:** Contains lightweight developer stub
**Code:**
```python
else:  # lightweight developer stub
```
**Action:** REMOVE stub. Use real browser automation or fail.

---

### 5. **FAISS Fake Module**
**File:** `python/helpers/faiss_monkey_patch.py`
**Type:** Fake module/monkey patch
**Issue:** Creates fake numpy.distutils and cpuinfo packages
**Code:**
```python
# for python 3.12 on arm, faiss needs a fake cpuinfo module
# fake numpy.distutils and numpy.distutils.cpuinfo packages
```
**Action:** REMOVE fake modules. Fix FAISS dependencies properly or use alternative.

---

### 6. **Test Policy Bypass**
**File:** `scripts/preflight.py`
**Type:** Policy bypass
**Issue:** Environment variable to bypass policy checks
**Code:**
```python
\"ENABLE_TEST_POLICY_BYPASS\",
```
**Action:** REMOVE bypass. Enforce policy in all environments.

---

### 7. **Policy Integration Bypass (DELETED)**
**File:** `services/conversation_worker/policy_integration.py`
**Type:** LOCAL bypass
**Issue:** Comment indicates removed bypass
**Code:**
```python
# Hard delete of LOCAL bypass: always enforce policy
```
**Action:** VERIFY complete removal. Ensure no bypass remains.

---

### 8. **Health Check Stub Factory**
**File:** `services/common/health_checks.py`
**Type:** Optional stub
**Issue:** Accepts stub_factory parameter for fake health checks
**Code:**
```python
def check_grpc_health(
    target: str, stub_factory: Optional[Any] = None, timeout: float = 1.5
):
    if stub_factory is None:
        # real check
    else:
        # use stub
```
**Action:** REMOVE stub_factory parameter. Always use real gRPC health checks.

---

### 9. **Conversation Worker Dummy Attribute**
**File:** `services/conversation_worker/main.py`
**Type:** Fallback/dummy
**Issue:** Last resort dummy attribute
**Code:**
```python
# Last resort: dummy attr
```
**Action:** REMOVE dummy fallback. Fail explicitly if attribute missing.

---

### 10. **Log Redaction Bypass**
**File:** `observability/log_redaction.py`
**Type:** Bypass
**Issue:** Formatter bypasses message construction
**Code:**
```python
formatter bypasses message construction. Structured logging in this
```
**Action:** REVIEW and ensure no security bypasses exist.

---

## 🟡 FALLBACK PATTERNS TO REMOVE

### 11. **Publisher Fallback Comments**
**File:** `services/common/publisher.py`
**Type:** Fallback logic
**Issue:** Comments about "no fallback" suggest fallback was removed but verify
**Code:**
```python
# No outbox fallback – surface the failure directly.
\"Kafka publish failed – no fallback enabled\",
```
**Action:** VERIFY no fallback code remains. Ensure failures surface immediately.

---

### 12. **Registry Fallback Logic**
**File:** `services/common/registry.py`
**Type:** Fallback pattern
**Issue:** Documentation mentions "without any fallback logic"
**Code:**
```python
without any fallback logic, environment variable access, or legacy patterns.
- Fallback logic
```
**Action:** VERIFY no fallback code exists. Documentation suggests it's clean.

---

### 13. **Conversation Worker Fallback**
**File:** `services/conversation_worker/main.py`
**Type:** Fallback comment
**Issue:** Comment about "no silent fallback"
**Code:**
```python
# Return the most recent user message; raise if none found (no silent fallback).
```
**Action:** VERIFY implementation raises on missing data. No silent failures.

---

## 🟢 TEST FILES (ACCEPTABLE MOCKS)

### 14. **Test Utilities Mock Request**
**File:** `python/integrations/test_utils.py`
**Type:** Test mock
**Issue:** Creates mock requests for testing
**Code:**
```python
\"\"\"Create a mock request for testing.\"\"\"
```
**Action:** ACCEPTABLE - This is in test utilities. Keep for test purposes only.

---

### 15. **Test Files with "no mocks" Claims**
**Files:** Multiple test files
**Type:** Test assertions
**Issue:** Tests claim "no mocks" but need verification
**Examples:**
- `tests/unit/test_canonical_sse_routes.py`: "testing real SSE endpoints with no mocks"
- `tests/unit/test_canonical_backend_real.py`: "testing real integrations with no mocks"
- `tests/agent/tools/test_tool_catalog.py`: "testing real tool catalog with no mocks"

**Action:** VERIFY these tests actually use real services. If they don't, FIX THEM.

---

## 📊 SUMMARY BY CATEGORY

| Category | Count | Action Required |
|----------|-------|-----------------|
| Database Stubs | 1 | REMOVE |
| Dummy Returns | 2 | REMOVE |
| Fake Modules | 1 | REMOVE |
| Policy Bypasses | 2 | REMOVE |
| Stub Factories | 1 | REMOVE |
| Fallback Logic | 3 | VERIFY REMOVED |
| Test Mocks | 2 | KEEP (test-only) |
| **TOTAL** | **12** | **10 MUST REMOVE** |

---

## 🎯 PRIORITY REMOVAL ORDER

1. **IMMEDIATE (P0):**
   - Postgres stub (`postgres_client.py`)
   - Policy bypasses (`preflight.py`, `policy_integration.py`)
   - FAISS fake modules (`faiss_monkey_patch.py`)

2. **HIGH (P1):**
   - Vision dummy response (`vision_load.py`)
   - MCP dummy exceptions (`mcp_handler.py`)
   - Browser stub (`browser_use_monkeypatch.py`)

3. **MEDIUM (P2):**
   - Health check stub factory (`health_checks.py`)
   - Conversation worker dummy attr (`main.py`)

4. **VERIFICATION (P3):**
   - Verify fallback removals in `publisher.py`, `registry.py`
   - Verify test files actually use real services

---

## 🔧 RECOMMENDED ACTIONS

### For Each Mock/Stub/Fallback:

1. **REMOVE** the fake implementation completely
2. **REPLACE** with real service calls
3. **ADD** proper error handling (fail fast, fail loud)
4. **UPDATE** tests to use real services (Docker, test databases, etc.)
5. **DOCUMENT** why the real implementation is required

### Testing Strategy:

- Use Docker Compose for real service dependencies
- Use test databases (not stubs)
- Use real API endpoints (not mocks)
- If a service is unavailable, the test should FAIL (not pass with fake data)

---

## ✅ VERIFICATION CHECKLIST

After removal, verify:

- [ ] No `mock`, `stub`, `fake`, `dummy` in production code
- [ ] No `bypass` flags in any environment
- [ ] All tests use real services
- [ ] Failures are explicit (no silent fallbacks)
- [ ] Documentation updated to reflect real-only approach

---

## 📝 NOTES

- **Test files** in `tests/` directory may contain mocks - this is ACCEPTABLE for unit tests
- **Vendor files** (ace-min, etc.) contain "mock" in comments - IGNORE these
- **Comments** claiming "no mocks" need verification - don't trust, verify
- **Fallback comments** suggesting removal need code inspection to confirm

---

**END OF REPORT**

Generated by: Amazon Q Developer
Scan Date: $(date)
Repository: somaAgent01
