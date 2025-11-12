# SomaAgent01 Canonical Roadmap - Zero Legacy Edition
**Version:** 2025-11-12 - **Zero Legacy Mandate**
**Branch:** fallback-purge-2025-11-12
**Status:** ACTIVE PURGE IN PROGRESS

---

## 🎯 ZERO-LEGACY MANIFESTO

### **NON-NEGOTIABLE PRINCIPLES**
1. **NO LEGACY CODE EXISTS** - Every file touched gets canonical rewrite
2. **NO FALLBACKS** - Zero compatibility shims, zero migration paths
3. **NO PLACEHOLDERS** - Every implementation is production-grade
4. **NO ENVIRONMENT LEAKS** - Configuration flows through Feature Registry only
5. **NO COMPETING SOURCES** - Somabrain is the single authority

---

## 🔥 IMMEDIATE HARD DELETE TARGETS

### **LEGACY PATTERNS - ZERO TOLERANCE**

#### **Direct Environment Access (CRITICAL)**
- [ ] `os.getenv()` calls → **HARD DELETE**
- [ ] Env-based feature flags → **HARD DELETE**
- [ ] Config file fallbacks → **HARD DELETE**

#### **Competing Endpoints (CRITICAL)**
- [ ] `/healthz` (duplicates) → **HARD DELETE**
- [ ] `/ready` (non-v1) → **HARD DELETE**
- [ ] `/scheduler_*` (non-v1) → **HARD DELETE**
- [ ] `/poll` → **HARD DELETE**

#### **Stub Integrations (CRITICAL)**
- [ ] Fake postgres clients → **HARD DELETE**
- [ ] Stubbed OPA middleware → **HARD DELETE**
- [ ] Mock learning behaviors → **HARD DELETE**
- [ ] TODO/FIXME comments → **HARD DELETE**

#### **Local Configurations (CRITICAL)**
- [ ] Local prompt files → **HARD DELETE**
- [ ] Local persona definitions → **HARD DELETE**
- [ ] Local tool catalogs → **HARD DELETE**

---

## 🏗️ CANONICAL ARCHITECTURE

### **Single Source of Truth**
```
Client → Gateway (21016) → /v1/* → Somabrain (9696)
          └── All integrations ↗
```

### **Deterministic Data Flow**
```
User → Gateway → Policy Check → Conversation Worker → Somabrain
           ↓                     ↓                        ↓
     Audit Trail           Persona Fetch      Weights/Context
           ↓                     ↓                        ↓
      Metrics/Logs         Tool Execution     Memory Write
```

---

## 📋 PURGE EXECUTION PLAN

### **Phase 1: Security Critical (Days 1-2)**
**Target:** All direct env access and competing endpoints

#### **Files to Hard Delete**
- `python/helpers/dotenv.py` → **COMPLETE REMOVAL**
- `observability/log_redaction.py` → **REWRITE FROM SCRATCH**
- `services/common/readiness.py` → **COMPLETE REMOVAL**

#### **Files to Rewrite**
- `services/gateway/main.py` → **Remove all legacy endpoints**
- `python/helpers/circuit_breaker.py` → **Remove env access**
- `bin/rotate-secrets.py` → **Rewrite with VaultAdapter**

### **Phase 2: Configuration Centralization (Days 2-3)**
**Target:** All configuration flows through Feature Registry

#### **Files to Rewrite**
- `services/common/runtime_config.py` → **Complete canonical implementation**
- `tests/utils.py` → **Remove env access**
- `tests/chaos/test_memory_recovery.py` → **Use mock configuration**

### **Phase 3: Persona Integration (Days 3-4)**
**Target:** Local persona/prompt management → Somabrain

#### **Files to Hard Delete**
- `prompts/` directory → **COMPLETE REMOVAL**
- `agent.py` lines 510-524 → **REWRITE with Somabrain personas**
- All local prompt files → **HARD DELETE**

### **Phase 4: Stub Elimination (Days 4-5)**
**Target:** Remove all fake integrations

#### **Files to Rewrite**
- `integrations/postgres.py` → **Remove stub comments**
- `services/common/learning.py` → **Remove LOCAL mode stubs**
- `services/common/health_checks.py` → **Remove stub factories**

---

## 🛡️ VERIFICATION PROTOCOL

### **Zero-Legacy Verification**
```bash
# Run after each phase
find . -type f -name "*.py" -exec grep -l "os.getenv\|getenv\|TODO\|FIXME\|HACK\|LEGACY\|DEPRECATED" {} \; | wc -l
# MUST return 0

find . -type f -name "*.py" -exec grep -l "/healthz\|/ready\|/scheduler_" {} \; | wc -l
# MUST return 0
```

### **Canonical Verification**
```bash
# Ensure only /v1/* endpoints
find . -type f -name "*.py" -exec grep -l "app\.[^/]" {} \; | xargs grep -v "/v1/" | wc -l
# MUST return 0

# Ensure no local configurations
grep -r "prompts/" . | wc -l
# MUST return 0
```

---

## 🔍 CODE AUDIT CHECKLIST

### **Before Any Change**
- [ ] **Read the complete file context** (VIBE Rule #6)
- [ ] **Understand the data flow** (VIBE Rule #4)
- [ ] **Verify against real Somabrain API** (VIBE Rule #7)
- [ ] **Document the canonical replacement** (VIBE Rule #5)

### **During Implementation**
- [ ] **No TODO/FIXME comments** (VIBE Rule #1)
- [ ] **No fake implementations** (VIBE Rule #1)
- [ ] **Complete error handling** (VIBE Rule #4)
- [ ] **Real documentation references** (VIBE Rule #5)

### **After Implementation**
- [ ] **All tests pass with real data** (VIBE Rule #7)
- [ ] **No legacy patterns remain** (Zero-Legacy Rule)
- [ ] **Production-grade implementation** (VIBE Rule #4)

---

## 📊 METRICS & MONITORING

### **Legacy Detection Metrics**
- `legacy_env_access_total` (target: 0)
- `legacy_endpoint_usage` (target: 0)
- `legacy_stub_count` (target: 0)

### **Canonical Validation Metrics**
- `feature_registry_access_total` (monitor usage)
- `somabrain_api_calls_total` (verify integration)
- `canonical_endpoint_requests_total` (monitor adoption)

---

## ⚡ IMMEDIATE ACTION ITEMS

### **Start Today**
1. **Delete `python/helpers/dotenv.py` completely**
2. **Delete `services/common/readiness.py` completely**
3. **Rewrite `observability/log_redaction.py` without env access**
4. **Remove all `/healthz` duplicates from gateway**

### **Tomorrow's Targets**
1. **Delete entire `prompts/` directory**
2. **Rewrite `agent.py` persona integration**
3. **Remove all stub implementations**

---

## 🎯 SUCCESS CRITERIA

### **Phase 1 Complete When**
- [ ] Zero `os.getenv()` calls outside runtime_config
- [ ] Zero non-/v1/* endpoints
- [ ] Zero TODO/FIXME comments
- [ ] All tests pass with real Somabrain

### **Phase 2 Complete When**
- [ ] Zero local persona files
- [ ] Zero stub integrations
- [ ] Zero local tool catalogs
- [ ] Complete Somabrain integration

### **Final Verification**
```bash
# Complete hard delete verification
find . -type f \( -name "*.py" -o -name "*.js" -o -name "*.yaml" \) -exec grep -l "TODO\|FIXME\|HACK\|LEGACY\|DEPRECATED\|os\.getenv\|getenv\|/healthz\|/ready\|/scheduler_" {} \; | wc -l
# MUST EQUAL: 0

# Canonical verification
grep -r "prompts/" . | wc -l
# MUST EQUAL: 0

# Somabrain integration verification
grep -r "from somabrain" . | wc -l
# MUST BE: > 0
```

---

## 🚨 ZERO-TOLERANCE ENFORCEMENT

**ANY CODE NOT MEETING THESE CRITERIA GETS HARD DELETED**

- **No legacy patterns** → **HARD DELETE**
- **No competing endpoints** → **HARD DELETE**
- **No fake implementations** → **HARD DELETE**
- **No environment leaks** → **HARD DELETE**
- **No stub behaviors** → **HARD DELETE**

**This branch will become the canonical, zero-legacy source of truth.**

---

**Status Indicator:** 🔥 **PURGE IN PROGRESS** - Legacy code is being systematically eliminated