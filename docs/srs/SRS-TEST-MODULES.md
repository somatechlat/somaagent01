# SRS-TEST-MODULES — Module-Based Test Suite Design

**System:** SomaAgent01
**Document ID:** SRS-TEST-MODULES-2026-01-17
**Version:** 1.0
**Status:** DRAFT

---

## Overview

This document defines the **test suites by module**, following the 12-Phase Chat Flow architecture. Each module has:
- **Unit Tests**: Pure logic verification
- **SaaS Direct Tests**: Real infra (Postgres/Redis/Milvus)
- **Integration Tests**: Cross-module verification

---

## Module Test Matrix

| Module | Location | Unit | SaaS | Integration |
|--------|----------|------|------|-------------|
| AgentIQ | `admin/core/agentiq/` | ✅ | ✅ | ✅ |
| Context Builder | `admin/core/context/` | ✅ | ✅ | ✅ |
| Chat Orchestrator | `admin/core/chat_orchestrator.py` | ⬜ | ✅ | ✅ |
| Budget System | `admin/core/budget/` | ✅ | ✅ | ⬜ |
| Feature Flags | `admin/core/features/` | ✅ | ✅ | ⬜ |
| Model Router | `admin/core/model_router.py` | ✅ | ✅ | ⬜ |
| Multimodal | `admin/core/multimodal.py` | ⬜ | ✅ | ✅ |
| Tool System | `admin/core/tool_system.py` | ✅ | ✅ | ✅ |
| SomaBrain Client | `admin/core/somabrain_client.py` | ⬜ | ✅ | ✅ |
| Billing (Lago) | `admin/core/billing.py` | ⬜ | ✅ | ⬜ |
| Permission Matrix | `admin/core/permission_matrix.py` | ✅ | ✅ | ⬜ |

---

## 1. AgentIQ (SimpleGovernor)

### Location
`tests/saas_direct/agentiq/`

### Test Cases

#### Unit: `test_agentiq_unit.py`
```python
def test_governor_derives_autonomy_from_knobs():
    """Verify autonomy level derived from capsule.body.persona.knobs.autonomy_level"""
    pass

def test_governor_derives_intelligence_from_knobs():
    """Verify intelligence level affects tool permissions"""
    pass

def test_resource_budget_calculation():
    """Verify budget ratios (tokens, tools, images) from knobs"""
    pass
```

#### SaaS Direct: `test_agentiq_saas.py`
```python
@pytest.mark.saas
def test_unified_gate_permission_check(real_tenant, real_capsule):
    """UnifiedGate checks permission against real SpiceDB"""
    pass

@pytest.mark.saas
def test_governor_budget_enforcement(real_tenant):
    """Governor denies action when budget exhausted"""
    pass
```

---

## 2. Context Builder

### Location
`tests/saas_direct/context/`

### Test Cases

#### Unit: `test_context_builder_unit.py`
```python
def test_lane_allocation_percentages():
    """Verify default lane allocation: system=15%, history=30%, memory=25%, tools=20%, buffer=10%"""
    pass

def test_context_window_respects_limit():
    """Verify total tokens <= model.context_window"""
    pass

def test_learned_preferences_override_defaults():
    """Verify capsule.body.learned.lane_preferences takes precedence"""
    pass
```

#### SaaS Direct: `test_context_builder_saas.py`
```python
@pytest.mark.saas
def test_memory_recall_populates_lane(real_tenant, real_capsule):
    """SomaBrain.recall() results populate memory lane"""
    pass

@pytest.mark.saas
def test_tool_discovery_populates_lane(real_tenant):
    """Available tools populate tools lane"""
    pass

@pytest.mark.saas
def test_history_truncation(real_session):
    """History lane truncates oldest messages when over limit"""
    pass
```

---

## 3. Chat Orchestrator (12-Phase Flow)

### Location
`tests/saas_direct/orchestrator/`

### Test Cases

#### SaaS Direct: `test_chat_orchestrator_saas.py`
```python
@pytest.mark.saas
def test_phase_1_tenant_resolution(real_request):
    """Phase 1: Tenant resolved from token"""
    pass

@pytest.mark.saas
def test_phase_2_capsule_load(real_tenant):
    """Phase 2: Capsule loaded from DB"""
    pass

@pytest.mark.saas
def test_phase_3_budget_gate(real_tenant):
    """Phase 3: Budget checked before processing"""
    pass

@pytest.mark.saas
def test_phase_4_agentiq_derivation(real_capsule):
    """Phase 4: AgentIQ derives settings from knobs"""
    pass

@pytest.mark.saas
def test_phase_5_context_building(real_capsule):
    """Phase 5: Context assembled from lanes"""
    pass

@pytest.mark.saas
def test_phase_6_model_selection(real_capsule):
    """Phase 6: Model selected based on task complexity"""
    pass

@pytest.mark.saas
def test_phase_7_llm_inference(real_context):
    """Phase 7: LLM called with built context"""
    pass

@pytest.mark.saas
def test_phase_8_tool_execution(real_tool_call):
    """Phase 8: Tool executed if requested"""
    pass

@pytest.mark.saas
def test_phase_9_multimodal_handling(real_image_request):
    """Phase 9: Image/Audio processed"""
    pass

@pytest.mark.saas
def test_phase_10_memory_update(real_response):
    """Phase 10: SomaBrain.memorize() called"""
    pass

@pytest.mark.saas
def test_phase_11_billing_event(real_tenant, real_response):
    """Phase 11: Lago event emitted"""
    pass

@pytest.mark.saas
def test_phase_12_response_delivery(real_session):
    """Phase 12: Response streamed to client"""
    pass
```

---

## 4. Budget System

### Location
`tests/saas_direct/budget/` (EXISTING: `test_budget.py`)

### Test Cases (Already Implemented)
- ✅ `test_get_current_usage_starts_at_zero`
- ✅ `test_increment_usage_increases_count`
- ✅ `test_check_budget_available_true`
- ✅ `test_check_budget_available_false_when_exceeded`
- ✅ `test_get_budget_remaining`

---

## 5. Feature Flags

### Location
`tests/saas_direct/features/` (EXISTING: `test_features.py`)

### Test Cases (Already Implemented)
- ✅ `test_core_feature_enabled_by_default`
- ✅ `test_high_tier_feature_disabled_for_default_tenant`
- ✅ `test_redis_override_enables_feature`
- ✅ `test_dependency_chain_enforcement`

---

## 6. Model Router

### Location
`tests/saas_direct/model_router/`

### Test Cases

#### Unit: `test_model_router_unit.py`
```python
def test_complexity_classification():
    """Verify task complexity (simple/moderate/complex) detection"""
    pass

def test_fallback_chain_order():
    """Verify fallback: Primary -> Secondary -> Tertiary"""
    pass

def test_model_capability_matching():
    """Verify model selected supports required capabilities (vision, tools)"""
    pass
```

#### SaaS Direct: `test_model_router_saas.py`
```python
@pytest.mark.saas
def test_model_config_from_db(real_tenant):
    """LLMModelConfig loaded from real DB"""
    pass

@pytest.mark.saas
def test_circuit_breaker_on_model_failure():
    """Failed model triggers circuit breaker"""
    pass
```

---

## 7. Multimodal

### Location
`tests/saas_direct/multimodal/`

### Test Cases

#### SaaS Direct: `test_multimodal_saas.py`
```python
@pytest.mark.saas
def test_image_generation_budget_check(real_tenant):
    """Image generation checks budget first"""
    pass

@pytest.mark.saas
def test_vision_processing_model_routing():
    """Vision tasks route to vision-capable model"""
    pass

@pytest.mark.saas
def test_voice_synthesis_feature_gate(real_tenant):
    """TTS requires voice_synthesis feature enabled"""
    pass
```

---

## 8. Tool System

### Location
`tests/saas_direct/tools/`

### Test Cases

#### Unit: `test_tool_system_unit.py`
```python
def test_tool_registry_discovery():
    """All registered tools discoverable"""
    pass

def test_tool_schema_validation():
    """Tool parameters validated against schema"""
    pass
```

#### SaaS Direct: `test_tool_system_saas.py`
```python
@pytest.mark.saas
def test_tool_permission_check(real_tenant, real_tool):
    """SpiceDB permission check before execution"""
    pass

@pytest.mark.saas
def test_tool_execution_audit(real_tenant, real_tool):
    """Tool execution logged to AuditLog"""
    pass

@pytest.mark.saas
def test_tool_budget_increment(real_tenant):
    """Tool call increments usage counter"""
    pass
```

---

## 9. SomaBrain Client (SaaS Direct Bridge)

### Location
`tests/saas_direct/somabrain/`

### Test Cases

#### SaaS Direct: `test_somabrain_client_saas.py`
```python
@pytest.mark.saas
def test_direct_import_mode():
    """Verify SomaBrain imported directly (not HTTP)"""
    from admin.core.somabrain_client import SomaBrainClient
    client = SomaBrainClient()
    assert client.mode == "direct"

@pytest.mark.saas
def test_recall_returns_memories(real_tenant, real_capsule):
    """SomaBrain.recall() returns semantic memories"""
    pass

@pytest.mark.saas
def test_memorize_stores_memory(real_tenant, real_capsule, real_message):
    """SomaBrain.memorize() persists to vector store"""
    pass

@pytest.mark.saas
def test_learn_updates_capsule(real_tenant, real_capsule):
    """SomaBrain.learn() updates capsule.body.learned"""
    pass
```

---

## 10. Billing (Lago)

### Location
`tests/saas_direct/billing/`

### Test Cases

#### SaaS Direct: `test_billing_saas.py`
```python
@pytest.mark.saas
def test_lago_event_emission(real_tenant, real_usage):
    """Billing event sent to Lago after request"""
    pass

@pytest.mark.saas
def test_subscription_tier_resolution(real_tenant):
    """Tenant subscription tier resolved from Lago"""
    pass
```

---

## 11. Permission Matrix

### Location
`tests/saas_direct/permissions/`

### Test Cases

#### Unit: `test_permission_matrix_unit.py`
```python
def test_permission_inheritance():
    """Role permissions inherit correctly"""
    pass

def test_deny_overrides_allow():
    """Explicit deny takes precedence"""
    pass
```

#### SaaS Direct: `test_permission_matrix_saas.py`
```python
@pytest.mark.saas
def test_spicedb_check_permission(real_tenant, real_resource):
    """SpiceDB check_permission returns correct result"""
    pass
```

---

## File Structure

```text
tests/
├── unit/
│   ├── test_agentiq_unit.py
│   ├── test_context_builder_unit.py
│   ├── test_model_router_unit.py
│   ├── test_tool_system_unit.py
│   ├── test_permission_matrix_unit.py
│   ├── test_budget_system.py (existing)
│   └── test_features_system.py (existing)
│
├── saas_direct/
│   ├── agentiq/
│   │   └── test_agentiq_saas.py
│   ├── context/
│   │   └── test_context_builder_saas.py
│   ├── orchestrator/
│   │   └── test_chat_orchestrator_saas.py
│   ├── model_router/
│   │   └── test_model_router_saas.py
│   ├── multimodal/
│   │   └── test_multimodal_saas.py
│   ├── tools/
│   │   └── test_tool_system_saas.py
│   ├── somabrain/
│   │   └── test_somabrain_client_saas.py
│   ├── billing/
│   │   └── test_billing_saas.py
│   ├── permissions/
│   │   └── test_permission_matrix_saas.py
│   ├── test_budget.py (existing)
│   └── test_features.py (existing)
│
└── api_e2e/
    ├── test_chat_endpoint.py
    ├── test_agent_endpoint.py
    └── test_voice_endpoint.py
```

---

## Priority Order

1. **Chat Orchestrator** (12-Phase Flow) - Core business logic
2. **AgentIQ** - Governance/Security
3. **Context Builder** - Memory/History integration
4. **Tool System** - External integrations
5. **Model Router** - LLM selection
6. **SomaBrain Client** - Memory bridge
7. **Multimodal** - Assets
8. **Billing** - Revenue
9. **Permission Matrix** - Security audit

---

## Execution Command

```bash
# Start infrastructure
docker compose -f infra/saas/docker-compose.yml up -d

# Run all SaaS Direct tests
SA01_INFRA_AVAILABLE=1 pytest tests/saas_direct/ -v --tb=short

# Run specific module
SA01_INFRA_AVAILABLE=1 pytest tests/saas_direct/orchestrator/ -v
```

---
