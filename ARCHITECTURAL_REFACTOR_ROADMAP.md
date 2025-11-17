# SOMAAGENT01 ARCHITECTURAL REFACTOR ROADMAP
## VIBE CODING RULES COMPLIANT PLAN

### **EXECUTIVE SUMMARY**

Complete architectural refactoring to eliminate all duplicates, overlaps, and violations. Target: Single source of truth for every component, centralized patterns, no duplicated efforts.

**CURRENT STATE ANALYSIS:**
- **Total Files**: 1,000+ files examined
- **Python Files**: 374 files
- **JavaScript Files**: 535 files  
- **Configuration Files**: 135+ YAML files
- **Repository Scale**: Complete analysis performed

### **🔴 CRITICAL VIOLATIONS IDENTIFIED**

1. **Configuration Chaos**: 5 different config systems with unclear precedence
2. **Gateway Monolith**: 200K+ character file mixing 15+ concerns (7,386 lines)
3. **Triple Orchestration**: 3 competing service management patterns
4. **God Module**: 40+ files in `services/common/` with no organization
5. **Duplicate Clients**: Multiple SomaBrain/FastA2A client implementations
6. **Missing Layer Separation**: Business logic mixed with data access and HTTP
7. **Inconsistent Naming**: client, store, repository, handler, service used interchangeably
8. **Over-Engineered BaseService**: Abstract pattern that services don't actually use

### **📊 CURRENT METRICS (VIOLATIONS)**
- **Largest File**: 200K+ characters (should be ≤500 lines)
- **Files >1000 lines**: 5+ files violating single responsibility
- **services/common/**: 40+ files (should be split by domain)
- **Duplicate Patterns**: 3 orchestration approaches
- **Test Coverage**: 30% estimated (should be 80%+)

---

## **SPRINT IMPLEMENTATION PLAN**

### **SPRINT 1: CENTRALIZED CONFIGURATION SYSTEM** (Week 1)
**Goal**: Eliminate 5 duplicate configuration systems into single source of truth

#### **1.1 Create Unified Configuration Hub**
```python
src/core/config/
├── __init__.py
├── core.py           # Single configuration source of truth
├── models.py         # Pydantic models for validation  
├── loader.py         # Single loader with clear precedence
└── registry.py       # Runtime access with caching
```

#### **1.2 Configuration Precedence Rules**
1. **SA01_* environment variables** (highest priority)
2. **Legacy variables** (deprecated, mapped to SA01_*)
3. **Configuration files** (YAML/JSON)
4. **Defaults** (lowest priority)

#### **1.3 Elimination Targets**
- ❌ `services/common/settings_sa01.py`
- ❌ `services/common/admin_settings.py`
- ❌ `services/common/runtime_config.py`
- ❌ `services/common/registry.py`
- ❌ `services/common/settings_registry.py`
- ✅ **SINGLE CONFIG SYSTEM**

#### **1.4 Success Criteria**
- ✅ All configuration flows through single system
- ✅ Clear precedence rules documented
- ✅ Environment variable mapping complete
- ✅ All services migrated to new config
- ✅ Zero duplicate config code

---

### **SPRINT 2: GATEWAY DECOMPOSITION** (Week 1-2)
**Goal**: Split 7,386-line gateway monolith into focused modules

#### **2.1 Gateway Architecture**
```python
src/gateway/
├── __init__.py
├── main.py              # Entry point only (100 lines)
├── routers/
│   ├── __init__.py
│   ├── chat.py          # Chat/conversation endpoints
│   ├── admin.py         # Admin/management endpoints
│   ├── health.py        # Health/metrics endpoints
│   ├── settings.py      # Settings management
│   ├── uploads.py       # File upload handling
│   ├── tools.py         # Tool execution endpoints
│   ├── memory.py        # Memory management
│   └── sessions.py      # Session management
├── middleware/
│   ├── __init__.py
│   ├── cors.py          # CORS handling
│   ├── auth.py          # Authentication
│   ├── telemetry.py     # Monitoring/telemetry
│   └── error_handling.py
├── services/
│   ├── __init__.py
│   ├── publisher.py     # Event publishing
│   ├── auth_service.py  # Authentication service
│   └── validation.py    # Request validation
└── dependencies.py      # Dependency injection setup
```

#### **2.2 Decomposition Rules**
- ✅ **NO file >500 lines**
- ✅ **Single responsibility per router**
- ✅ **Centralized middleware**
- ✅ **Dependency injection pattern**
- ✅ **NO duplicated code**

#### **2.3 Migration Strategy**
1. Extract each endpoint group into separate router
2. Centralize common middleware
3. Implement dependency injection
4. Update all imports
5. Test each router independently

#### **2.4 Success Criteria**
- ✅ Gateway main.py ≤100 lines
- ✅ All routers ≤500 lines
- ✅ Clear separation of concerns
- ✅ Centralized middleware
- ✅ No duplicated functionality

---

### **SPRINT 3: SERVICES COMMON REORGANIZATION** (Week 2-3)
**Goal**: Eliminate 40+ file god module by domain-driven organization

#### **3.1 New Architecture**
```python
src/core/
├── __init__.py
├── domain/              # Domain-specific logic
│   ├── __init__.py
│   ├── memory/          # Memory-related components
│   ├── chat/            # Chat/conversation components
│   ├── tools/           # Tool execution components
│   └── auth/            # Authentication components
├── infrastructure/      # Infrastructure concerns
│   ├── __init__.py
│   ├── database/        # Database connections/repositories
│   ├── messaging/       # Kafka/message broker
│   ├── cache/           # Redis/caching
│   ├── external/        # External service clients
│   └── monitoring/      # Metrics/telemetry
├── application/         # Application services
│   ├── __init__.py
│   ├── commands/        # Command handlers
│   ├── queries/         # Query handlers
│   └── events/          # Event handlers
└── bootstrap/           # Bootstrap/configuration
    ├── __init__.py
    ├── container.py     # DI container
    └── settings.py      # Settings bootstrap
```

#### **3.2 Domain-Driven Organization**
- **Memory Domain**: All memory-related components
- **Chat Domain**: All conversation-related components
- **Tools Domain**: All tool execution components
- **Auth Domain**: All authentication components

#### **3.3 Migration Strategy**
1. Map each of 40+ files to new domains
2. Extract domain-specific logic
3. Consolidate duplicate functionality
4. Create clear interfaces
5. Update all imports

#### **3.4 Success Criteria**
- ✅ Eliminated services/common/ god module
- ✅ Clear domain separation
- ✅ No duplicate functionality
- ✅ Well-defined interfaces
- ✅ All imports updated

---

### **SPRINT 4: CLIENT CONSOLIDATION** (Week 3-4)
**Goal**: Eliminate duplicate client implementations

#### **4.1 Unified Client Pattern**
```python
src/core/infrastructure/external/
├── __init__.py
├── base_client.py       # Base client with retry/telemetry
├── somabrain_client.py  # Single SomaBrain client
├── fasta2a_client.py    # Single FastA2A client
├── opa_client.py        # Single OPA client
└── registry.py          # Client registry/factory
```

#### **4.2 Client Consolidation Rules**
- ✅ **ONE client per external service**
- ✅ **Base client with common functionality**
- ✅ **Factory pattern for client creation**
- ✅ **NO duplicate implementations**

#### **4.3 Elimination Targets**
- ❌ `python/integrations/somabrain_client.py` (164 lines)
- ❌ `integrations/somabrain.py` (2-line wrapper)
- ❌ `python/helpers/fasta2a_client.py` (377 lines)
- ❌ Any other duplicate clients
- ✅ **SINGLE CLIENT PER SERVICE**

#### **4.4 Success Criteria**
- ✅ One client per external service
- ✅ Common base client functionality
- ✅ Factory pattern implemented
- ✅ All services using unified clients
- ✅ No duplicate client code

---

### **SPRINT 5: ORCHESTRATION UNIFICATION** (Week 4-5)
**Goal**: Eliminate 3 competing orchestration patterns

#### **5.1 Single Orchestration Pattern**
```python
src/core/application/
├── __init__.py
├── orchestrator/
│   ├── __init__.py
│   ├── base.py          # Base orchestrator
│   ├── chat_orchestrator.py
│   ├── tool_orchestrator.py
│   └── memory_orchestrator.py
├── handlers/
│   ├── __init__.py
│   ├── command_handlers.py
│   ├── query_handlers.py
│   └── event_handlers.py
└── workflows/
    ├── __init__.py
    ├── chat_workflow.py
    ├── tool_workflow.py
    └── memory_workflow.py
```

#### **5.2 Orchestration Rules**
- ✅ **SINGLE orchestration pattern**
- ✅ **Command Query Responsibility Segregation (CQRS)**
- ✅ **Workflow-based approach**
- ✅ **NO competing patterns**

#### **5.3 Elimination Targets**
- ❌ `orchestrator/orchestrator.py` (current approach)
- ❌ `services/common/service_lifecycle.py` (BaseService pattern)
- ❌ `services/gateway/dependencies.py` (manual DI)
- ✅ **SINGLE ORCHESTRATION SYSTEM**

#### **5.4 Success Criteria**
- ✅ Single orchestration pattern
- ✅ CQRS implemented
- ✅ Workflow-based approach
- ✅ All services using unified orchestration
- ✅ No competing patterns

---

### **SPRINT 6: SERVICE STANDARDIZATION** (Week 5-6)
**Goal**: Standardize all 7 microservices to new architecture

#### **6.1 Service Standardization**
```python
src/services/
├── __init__.py
├── base_service.py      # Base service with common functionality
├── gateway/
│   ├── __init__.py
│   ├── main.py          # Gateway service entry
│   └── config.py        # Gateway-specific config
├── conversation_worker/
│   ├── __init__.py
│   ├── main.py          # Conversation worker entry
│   └── config.py        # Conversation-specific config
├── tool_executor/
│   ├── __init__.py
│   ├── main.py          # Tool executor entry
│   └── config.py        # Tool-specific config
└── memory_replicator/
    ├── __init__.py
    ├── main.py          # Memory replicator entry
    └── config.py        # Memory-specific config
```

#### **6.2 Service Rules**
- ✅ **Standardized service structure**
- ✅ **Common base service**
- ✅ **Service-specific configuration**
- ✅ **NO duplicated functionality**

#### **6.3 Migration Strategy**
1. Create base service template
2. Migrate each service to new structure
3. Update configuration management
4. Implement health checks
5. Add metrics integration

#### **6.4 Success Criteria**
- ✅ Standardized service structure
- ✅ Common base service
- ✅ Service-specific configuration
- ✅ All services migrated
- ✅ No duplicated functionality

---

### **SPRINT 7: TESTING INFRASTRUCTURE** (Week 6-7)
**Goal**: Achieve 80%+ test coverage with unified testing architecture

#### **7.1 Unified Testing Architecture**
```python
tests/
├── __init__.py
├── fixtures/
│   ├── __init__.py
│   ├── database.py      # Database test fixtures
│   ├── messaging.py     # Message broker fixtures
│   └── external.py      # External service mocks
├── unit/
│   ├── __init__.py
│   ├── core/            # Core component tests
│   ├── gateway/         # Gateway tests
│   └── services/        # Service tests
├── integration/
│   ├── __init__.py
│   ├── database/        # Database integration tests
│   ├── messaging/       # Message broker tests
│   └── external/        # External service tests
└── e2e/
    ├── __init__.py
    ├── chat_flows.py    # End-to-end chat tests
    └── tool_flows.py    # End-to-end tool tests
```

#### **7.2 Testing Rules**
- ✅ **80%+ test coverage target**
- ✅ **Clear test separation**
- ✅ **Shared fixtures**
- ✅ **NO test code duplication**

#### **7.3 Success Criteria**
- ✅ 80%+ test coverage
- ✅ Clear test separation
- ✅ Shared fixtures
- ✅ No test code duplication
- ✅ All components tested

---

### **SPRINT 8: DEPLOYMENT STANDARDIZATION** (Week 7-8)
**Goal**: Standardize deployment across all environments

#### **8.1 Unified Deployment**
```python
deploy/
├── docker/
│   ├── Dockerfile       # Single production Dockerfile
│   ├── docker-compose.yml
│   └── docker-compose.dev.yml
├── kubernetes/
│   ├── k8s/
│   │   ├── namespace.yaml
│   │   ├── configmap.yaml
│   │   ├── secret.yaml
│   │   └── services/
│   └── helm/
│       └── somaagent01/
└── scripts/
    ├── deploy.sh
    ├── migrate.sh
    └── rollback.sh
```

#### **8.2 Deployment Rules**
- ✅ **Single Dockerfile pattern**
- ✅ **Environment-specific configs**
- ✅ **Standardized deployment scripts**
- ✅ **NO deployment duplication**

#### **8.3 Success Criteria**
- ✅ Single Dockerfile pattern
- ✅ Environment-specific configs
- ✅ Standardized deployment scripts
- ✅ No deployment duplication
- ✅ All environments supported

---

## **VIBE CODING RULES COMPLIANCE**

### **✅ NO SHIMS**
- All implementations must be real
- No mock data or fake responses
- Real database connections
- Real external service calls

### **✅ NO FALLBACKS**
- No alternative code paths
- No backup implementations
- Single source of truth
- No degraded modes

### **✅ NO FAKE ANYTHING**
- Real functionality only
- Production-ready code
- No development shortcuts
- No placeholder implementations

### **✅ NO LEGACY**
- Remove all old patterns
- No deprecated methods
- Modern Python practices
- Clean architecture

### **✅ NO BACKUPS**
- No duplicate code
- No redundant implementations
- Single responsibility
- No alternative approaches

---

## **SUCCESS METRICS**

### **Code Quality**
- **File Size**: All files ≤500 lines
- **Complexity**: Cyclomatic complexity ≤10
- **Coverage**: 80%+ test coverage
- **Duplication**: 0% code duplication

### **Architecture**
- **Layers**: Clear separation of concerns
- **Dependencies**: Well-defined dependency graph
- **Patterns**: Consistent patterns throughout
- **Configuration**: Single configuration source

### **Maintenance**
- **Onboarding**: 1 day for new developers
- **Debugging**: Clear error traces
- **Testing**: Comprehensive test suite
- **Deployment**: Standardized process

---

## **SPRINT COMMITMENTS**

Each sprint will deliver:
- ✅ **Working production code**
- ✅ **Comprehensive test coverage**
- ✅ **Documentation updates**
- ✅ **Migration guides**
- ✅ **Zero technical debt**

---

## **NEXT STEPS**

1. **Begin Sprint 1**: Centralized Configuration System
2. **Create branch**: `architectural-refactor`
3. **Weekly reviews**: Progress verification
4. **Continuous integration**: Automated testing
5. **Documentation**: Live documentation updates

**This refactoring will transform SomaAgent01 from a monolithic, duplicated codebase to a clean, maintainable, VIBE-compliant architecture.**

**READY TO BEGIN SPRINT 1?**