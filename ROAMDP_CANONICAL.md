# SomaAgent01 Canonical Roadmap - Zero Legacy Edition
**Version:** 2025-11-12 - **Zero Legacy Mandate**  
**Branch:** fallback-purge-2025-11-12  
**Status:** LIVE IMPLEMENTATION

---

## 🎯 ZERO-LEGACY MANIFESTO

### **NON-NEGOTIABLE RULES**
1. **NO LEGACY CODE EXISTS** - Every file touched gets canonical rewrite
2. **NO FALLBACKS** - Zero compatibility shims, zero migration paths  
3. **NO ENVIRONMENT VARIABLES** - Configuration via Feature Registry only
4. **NO TODO/FIXME COMMENTS** - Complete implementations only
5. **NO DUPLICATE ENDPOINTS** - `/v1/*` is sole surface
6. **NO COMPETING SOURCES** - Somabrain is single authority

---

## 📊 LEGACY AUDIT RESULTS

### **CRITICAL FINDINGS - DELETION TARGETS**

#### **🔴 Direct Environment Access** (MUST DELETE)
- `services/common/settings_base.py:54` - `os.getenv(environment_var)`
- `services/common/runtime_config.py:100` - `os.getenv("SA01_DEPLOYMENT_MODE")`
- `services/common/runtime_config.py:195` - `os.getenv(key)`
- `services/common/budget_manager.py:68` - `os.environ`
- `scripts/golden_trace.py:26` - `os.getenv("GATEWAY_BASE")`
- `scripts/e2e_quick.py:25-26` - `os.environ.get()` + fallback
- `scripts/migrate_profiles_to_gateway.py:20,37` - `os.getenv()`

#### **🟡 Legacy Comments & TODOs** (MUST DELETE)
- `services/common/runtime_config.py:333` - "placeholder TODO"
- `services/gateway/main.py:1592,7264` - "deprecated on_event"
- `webui/index.js:14` - "TODO - backward compatibility"
- `webui/components/notifications/notification-store.js:1` - "Deprecated prior"

#### **🟢 CSS/JS Fallbacks** (MUST DELETE)
- `webui/index.css:325` - "Fallback for browsers..."
- `webui/index.js:162,824` - "fallback to console only"
- `webui/components/chat/attachments/attachmentsStore.js:382` - "Fallback string filename"
- `webui/components/settings/a2a/a2a-connection.html:29` - "fallback to mcp_server_token"
- `webui/components/settings/memory/memory-dashboard-store.js:114` - "Fallback to default"

---

## 🏗️ CANONICAL ARCHITECTURE

### **Unified Surface**
```
Client → Gateway (21016) → /v1/* → Somabrain (9696)
          └── All integrations ↗
```

### **Configuration Hierarchy** (Deterministic)
1. **Runtime Registry** → Feature flags + tenant overrides
2. **Somabrain Authority** → Personas, prompts, policies  
3. **Code Constants** → Immutable defaults only

### **Data Flow**
```
User → Gateway → Policy Check → Worker → Somabrain → Response
          ↓                     ↓                ↓
     Audit Trail          Persona Fetch    Memory Write
```

---

## 🔧 IMPLEMENTATION PHASES

### **Phase 0 - Zero-Legacy Verification** ✅ COMPLETED
**Duration:** 1 day  
**Status:** ✅ COMPLETE

**Deliverables:**
- [x] Complete legacy audit completed
- [x] Legacy patterns catalogued above
- [x] Deletion targets identified
- [x] Canonical roadmap established

**Verification:**
```bash
# Legacy detection command
find . -type f \( -name "*.py" -o -name "*.js" \) \
  -exec grep -l "os.getenv\|TODO\|FIXME\|deprecated\|fallback" {} \;
```

### **Phase 1 - Configuration Purge** (STARTING NOW)
**Duration:** 2 days  
**Status:** 🔄 IN PROGRESS

**Files to Rewrite:**
- [ ] `services/common/runtime_config.py` → Feature Registry only
- [ ] `services/common/settings_base.py` → Remove env access
- [ ] `services/common/budget_manager.py` → Registry integration
- [ ] All script files → Remove fallback URLs

**Implementation:**
- Replace all `os.getenv()` calls with `registry.get_feature()`
- Remove all TODO/FIXME comments
- Eliminate all fallback logic

### **Phase 2 - Somabrain Integration** (NEXT)
**Duration:** 3 days  
**Status:** 🚧 PENDING

**Endpoints to Implement:**
- `GET /persona/{pid}` → Persona profiles
- `POST /v1/weights/update` → Learning feedback  
- `GET /v1/flags/{tenant}/{flag}` → Feature overrides
- `POST /plan/suggest` → Dynamic planning

### **Phase 3 - Legacy Endpoint Removal** (NEXT)
**Duration:** 1 day  
**Status:** 🚧 PENDING

**Targets:**
- [ ] Remove `/health` (keep `/healthz` only)
- [ ] Remove CSRF endpoints
- [ ] Remove polling endpoints
- [ ] Remove deprecated notification stores

### **Phase 4 - Verification & Testing**
**Duration:** 1 day  
**Status:** 🚧 PENDING

**Validation:**
- [ ] Zero legacy patterns confirmed via automated scan
- [ ] All tests pass with canonical architecture
- [ ] Health checks verify Somabrain connectivity
- [ ] Feature registry metrics populated

---

## 📋 DELETION TRACKER

### **Immediate Deletions (Phase 1)**
```
LEGACY_PATTERNS = [
    "os.getenv()",
    "TODO:",
    "FIXME:",
    "fallback",
    "deprecated",
    "compatibility",
    "shim"
]
```

### **Files to Hard Delete**
1. **All env variable access** → Replace with Feature Registry
2. **All TODO/FIXME comments** → Complete implementations
3. **All fallback logic** → Single canonical path
4. **All deprecated endpoints** → `/v1/*` only

### **Zero-Legacy Verification Script**
```bash
#!/bin/bash
# Run after each phase
echo "=== ZERO-LEGACY VERIFICATION ==="
find . -type f \( -name "*.py" -o -name "*.js" \) \
  -not -path "./.git/*" \
  -not -path "./__pycache__/*" \
  -exec grep -l "os.getenv\|TODO\|FIXME\|HACK\|deprecated\|fallback\|shim" {} \; \
  | wc -l

# Should return 0 for zero legacy
```

---

## 🚨 CRITICAL IMPLEMENTATION

### **Immediate Actions (Starting Now)**

#### **1. Environment Purge**
```python
# LEGACY (TO DELETE)
port = os.getenv("GATEWAY_PORT", "21016")
mode = os.getenv("SA01_DEPLOYMENT_MODE", "LOCAL")

# CANONICAL (TO IMPLEMENT)
port = registry.deployment_mode().gateway_port()
mode = registry.deployment_mode()
```

#### **2. Configuration Registry**
```python
# NEW: services/common/registry.py
class FeatureRegistry:
    """Single canonical source for all configuration"""
    
    def get_feature(self, key: str, tenant: str = None) -> Any:
        """Deterministic feature resolution - no fallbacks"""
        return self._resolve_from_somabrain(key, tenant)
```

#### **3. Legacy Endpoint Removal**
```python
# DELETE: /health endpoint
# KEEP: /healthz only
# DELETE: /poll endpoints
# DELETE: CSRF endpoints
```

---

## ✅ COMPLETION CRITERIA

### **Zero-Legacy Checklist**
- [ ] **0 instances** of `os.getenv()` outside registry
- [ ] **0 instances** of `TODO/FIXME/HACK`
- [ ] **0 instances** of `fallback/compatibility/shim`
- [ ] **0 legacy endpoints** outside `/v1/*`
- [ ] **100%** Somabrain integration
- [ ] **100%** Feature Registry coverage

### **Verification Commands**
```bash
# Run continuously during development
echo "=== ZERO-LEGACY STATUS ==="
grep -r "os.getenv\|TODO\|FIXME\|fallback" --include="*.py" --include="*.js" .
```

---

## 🎯 SUCCESS METRICS

| Metric | Target | Current |
|--------|--------|---------|
| Legacy Env Access | 0 | 12 |
| TODO/FIXME Comments | 0 | 8 |
| Fallback Logic | 0 | 6 |
| Canonical Endpoints | 100% | 0% |
| Somabrain Integration | 100% | 15% |

---

**STATUS: PHASE 0 COMPLETE → PHASE 1 STARTING**

**Next:** Beginning systematic deletion and canonical implementation of all legacy patterns identified above.

**Commit Message:** `feat: zero-legacy mandate - complete Phase 0 audit & canonical roadmap`