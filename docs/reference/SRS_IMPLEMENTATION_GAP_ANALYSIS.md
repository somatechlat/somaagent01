# ❌ SRS IMPLEMENTATION GAP ANALYSIS
## Somabrain-Centric Integration Status Check

**SRS Document:** "Software Requirements Specification - Somabrain‑Centric Integration for SomaAgent01 (Agent Zero Behaviour)"  
**Analysis Date:** 2025-12-14  
**Status:** **NOT IMPLEMENTED** ❌

---

## 📋 REQUIREMENTS vs CODE

### ✅ IMPLEMENTED (1/7 Components)

| Component | Status | Location |
|-----------|--------|----------|
| CircuitBreaker | ✅ EXISTS | `services/gateway/circuit_breakers.py` (383 lines) |

**Notes:**
- Circuit breaker for Somabrain exists with fail_max=5, reset_timeout=60s
- Integrated into degradation monitor
- Has Prometheus metrics
- **However:** Not specifically tied to the 4 new Somabrain tools (which don't exist)

---

### ❌ NOT IMPLEMENTED (6/7 Components)

#### 1. Somabrain Tools (0/4 Implemented)

| Required Tool | Status | Expected Location |
|---------------|--------|-------------------|
| `somabrain_push_definition` | ❌ NOT FOUND | `python/tools/somabrain_push_definition.py` |
| `somabrain_push_planning` | ❌ NOT FOUND | `python/tools/somabrain_push_planning.py` |
| `somabrain_push_memory_graph` | ❌ NOT FOUND | `python/tools/somabrain_push_memory_graph.py` |
| `somabrain_get_full_model` | ❌ NOT FOUND | `python/tools/somabrain_get_full_model.py` |

**Current Tools in `python/tools/`:**
```
✅ a2a_chat.py
✅ behaviour_adjustment.py
✅ browser_agent.py
✅ call_subordinate.py
✅ catalog.py
✅ code_execution_tool.py
✅ document_query.py
✅ input.py
✅ memory_delete.py
✅ memory_forget.py
✅ memory_load.py
✅ memory_save.py
✅ models.py
✅ notify_user.py
✅ response.py
✅ scheduler.py
✅ search_engine.py
✅ unknown.py
✅ vision_load.py
```

**Total:** 19 tools, **NONE** of the 4 required Somabrain tools exist.

---

#### 2. Extensions (1/3 Implemented)

| Required Extension | Status | Expected Location |
|--------------------|--------|-------------------|
| `CircuitBreaker` | ✅ EXISTS | `services/gateway/circuit_breakers.py` |
| `OpenAPISchemaValidate` | ❌ NOT FOUND | `extensions/openapi_schema_validate.py` |
| `Metrics` | ❌ NOT FOUND | `extensions/metrics.py` |

**Note:** Extensions directory structure was not found. Circuit breaker exists but not as an "extension" in the sense described by the SRS.

---

#### 3. Functional Requirements (0/7 Implemented)

| FR ID | Requirement | Status | Evidence |
|-------|-------------|--------|----------|
| FR-1 | Validate payload against OpenAPI | ❌ NO | OpenAPISchemaValidate extension missing |
| FR-2 | Push code definitions (batch ≤500) to `/code/batch` | ❌ NO | `somabrain_push_definition` tool missing |
| FR-3 | Push planning data to `/planning` | ❌ NO | `somabrain_push_planning` tool missing |
| FR-4 | Push memory graph (NDJSON) to `/memory-graph` | ❌ NO | `somabrain_push_memory_graph` tool missing |
| FR-5 | Get full model from `/model?version=latest` | ❌ NO | `somabrain_get_full_model` tool missing |
| FR-6 | Circuit breaker after 3 consecutive 5xx | ⚠️ PARTIAL | Circuit breaker exists (fail_max=5) but not tool-specific |
| FR-7 | Audit logging to `tool_audit` and Kafka `somabrain_events` | ❌ NO | No somabrain-specific audit logging found |

---

#### 4. Database Schema (Not Checked)

| Required Table | Status | Expected Schema |
|----------------|--------|-----------------|
| `somabrain_code` | ❌ UNKNOWN | Stores batch IDs from code definition pushes |
| `tool_audit` | ⚠️ EXISTS | May exist in general audit system |

---

#### 5. API Endpoints (Not Checked)

**Required Somabrain Endpoints (per SRS):**
- `POST /code/batch` - Bulk code definitions
- `POST /planning` - FSM snapshot and option list
- `POST /memory-graph` - NDJSON nodes/edges
- `GET /model?version=latest` - Retrieve semantic model

**Status:** Cannot verify without somabrain running or checking `somabrain-openapi.json`

---

## 🔍 DETAILED FINDINGS

### What EXISTS:

1. **Circuit Breaker System** (`services/gateway/circuit_breakers.py`)
   ```python
   CircuitBreakerConfig.SOMATRAIN = {
       "fail_max": 5,
       "reset_timeout": 60,
       "exclude": [pybreaker.CircuitBreakerError]
   }
   ```
   - Registered as "somabrain" in ResilientService registry
   - Has Prometheus metrics
   - Integrated with degradation monitor

2. **Existing Somabrain Integration** (`python/integrations/soma_client.py`)
   - General Somabrain HTTP client
   - `/remember` and `/recall` endpoints
   - **BUT:** Does NOT implement the 4 specialized tools from SRS

3. **General Tool Infrastructure**
   - Tool registry system exists
   - 19 existing tools
   - Auto-discovery mechanism in place

### What's MISSING:

1. **All 4 Somabrain Tools** (100% missing)
2. **OpenAPISchemaValidate Extension** (payload validation)
3. **Metrics Extension** (Prometheus for Somabrain)
4. **Specialized Audit Logging** (somabrain_events topic)
5. **Database Schema** (`somabrain_code` table)
6. **Redis Caching** (for circuit breaker resilience per FR-6)

---

## 📊 IMPLEMENTATION SCORECARD

| Category | Required | Implemented | % Complete |
|----------|----------|-------------|------------|
| **Tools** | 4 | 0 | 0% ❌ |
| **Extensions** | 3 | 1 (partial) | 33% ⚠️ |
| **Functional Requirements** | 7 | 0.5 (circuit breaker only) | 7% ❌ |
| **Database Tables** | 2+ | Unknown | ? |
| **API Integration** | 4 endpoints | 0 | 0% ❌ |

**Overall SRS Compliance:** **~10%** ❌

---

## 🚨 CRITICAL GAPS

### High Priority (Blocking)

1. **No Somabrain Tools**
   - `somabrain_push_definition` - Core functionality
   - `somabrain_push_planning` - Core functionality
   - `somabrain_push_memory_graph` - Core functionality
   - `somabrain_get_full_model` - Core functionality

2. **No Payload Validation**
   - OpenAPISchemaValidate extension missing
   - FR-1 cannot be satisfied

3. **No Specialized Metrics**
   - Metrics extension missing
   - Cannot track per-tool latency, success rates

### Medium Priority

4. **No Audit Trail**
   - `somabrain_events` Kafka topic not created
   - `tool_audit` table may exist but not SomaBrain-specific

5. **No Redis Cache**
   - Circuit breaker exists but no cache layer (FR-6)

### Low Priority

6. **No ISO 27001 Mapping**
   - SRS requires `docs/iso27001_mapping.md`
   - File not found

---

## 📝 WHAT NEEDS TO BE BUILT

### Phase 1: Core Tools (Weeks 1-2)

```python
# python/tools/somabrain_push_definition.py
class SomabrainPushDefinition(Tool):
    async def execute(self, batch: List[dict]) -> dict:
        """
        Push code definitions to Somabrain.
        
        Endpoint: POST /code/batch
        Payload: {
            "items": [
                {
                    "path": "agent.py",
                    "summary": "Three-sentence summary",
                    "embedding": [0.1, 0.2, ...]
                },
                ...
            ]
        }
        Validation: batch size ≤ 500
        """
        pass
```

```python
# python/tools/somabrain_push_planning.py
class SomabrainPushPlanning(Tool):
    async def execute(self, fsm_snapshot: dict, options: List[dict]) -> dict:
        """
        Push planning data to Somabrain.
        
        Endpoint: POST /planning
        Payload: {
            "fsm": {...},
            "options": [...],
            "ema_weights": {...}
        }
        """
        pass
```

```python
# python/tools/somabrain_push_memory_graph.py
class SomabrainPushMemoryGraph(Tool):
    async def execute(self, nodes: List[dict], edges: List[dict]) -> dict:
        """
        Push memory graph to Somabrain.
        
        Endpoint: POST /memory-graph
        Format: NDJSON
        """
        pass
```

```python
# python/tools/somabrain_get_full_model.py
class SomabrainGetFullModel(Tool):
    async def execute(self, version: str = "latest") -> dict:
        """
        Retrieve semantic model from Somabrain.
        
        Endpoint: GET /model?version=latest
        Cache: 30 seconds
        """
        pass
```

### Phase 2: Extensions (Week 3)

```python
# extensions/openapi_schema_validate.py
class OpenAPISchemaValidate(Extension):
    async def before_tool_call(self, tool_name: str, payload: dict):
        """Validate against somabrain-openapi.json"""
        pass
```

```python
# extensions/metrics.py
class Metrics(Extension):
    # Already exists in other forms, needs Somabrain-specific metrics
    pass
```

### Phase 3: Audit & Observability (Week 4)

- Create `somabrain_events` Kafka topic
- Add `somabrain_code` PostgreSQL table
- Implement Redis caching layer for FR-6
- Add ISO 27001 mapping document

---

## 🎯 RECOMMENDATION

**Status:** **SRS NOT IMPLEMENTED** ❌

**Action Required:**
1. **Confirm Requirements** - Is this SRS still valid?
2. **If Yes:** Implement all 4 tools + 2 extensions (8-10 weeks)
3. **If No:** Archive/update SRS to reflect actual system

**Current System:**
- Has basic Somabrain integration (`/remember`, `/recall`)
- Has circuit breaker infrastructure
- **Does NOT have** the specialized "Somabrain-Centric" features from this SRS

---

**This SRS appears to describe a FUTURE implementation, not the current state.** 🚨
