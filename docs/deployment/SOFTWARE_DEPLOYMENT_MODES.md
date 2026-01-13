# Software Deployment Modes (SomaStack)

**Purpose:** Define software-level modes for the three services when run
standalone or as a unified SaaS.

**Last Updated:** 2026-01-13 by SOMA Collective Intelligence Audit

---

## 1. The Four Deployment Dimensions

> **CRITICAL**: SomaStack has **4 orthogonal deployment dimensions** that MUST be 
> understood before making any code changes.

| Dimension | Environment Variable | Values | Purpose |
|-----------|---------------------|--------|---------|
| **Software Mode** | `SOMASTACK_SOFTWARE_MODE` | `StandAlone` / `SomaStackClusterMode` | Service coupling |
| **Environment** | `SA01_DEPLOYMENT_MODE` | `DEV` / `PROD` | Debug vs production (fail-fast) |
| **SaaS Bridge** | `SOMA_SAAS_MODE` | `true` / `false` | In-process vs HTTP calls |
| **Infrastructure** | Tilt / K8s / Docker | Varies | Orchestration target |

### 1.1 Dimension Relationships

```
SA01_DEPLOYMENT_MODE=PROD
├── All localhost fallbacks FAIL-FAST (VIBE Rule 91)
├── All secrets required from Vault (VIBE Rule 164)
└── No dev defaults allowed

SOMA_SAAS_MODE=true
├── saas/brain.py → Direct Python import of somabrain
├── saas/memory.py → Direct Python import of fractal_memory
└── 100x performance (0.05ms vs 5ms per operation)

SOMA_SAAS_MODE=false
├── SomaBrainClient → HTTP to somabrain:30101
├── MemoryBridge → HTTP to somafractalmemory:10101
└── Requires SOMA_MEMORY_API_TOKEN for auth
```

---

## 2. Mode Names (Canonical)

- **StandAlone**: Each service runs independently with its own auth, storage,
  and configuration.
- **SomaStackClusterMode**: All three services run as a unified SaaS with shared
  tenant identity, shared authorization, and coupled Brain+Memory runtime.

These names are canonical for documentation and future configuration flags.

---

## 3. Behavior by Mode

### 3.1 StandAlone

- Each service must boot and operate without dependencies on the other two.
- Local auth and storage must be sufficient for basic operation.
- Cross-service calls are disabled by default or use local stubs.

### 3.2 SomaStackClusterMode

- SomaAgent01 is the control plane (tenants, users, agents, billing).
- SomaBrain and SomaFractalMemory are inseparable and must run as a paired
  runtime for memory-backed cognition.
- Cross-service calls require service-to-service auth and shared tenant claims.
- Fine-grained permissions must be enforced via the unified authorization model
  (SpiceDB in the control plane, policy enforcement in downstream services).

---

## 4. VIBE Compliance Rules

### Rule 91: Zero-Fallback Mandate

In `SA01_DEPLOYMENT_MODE=PROD`:
- **NO** localhost defaults allowed
- All service URLs MUST be explicitly configured
- Missing configuration MUST crash on startup

**Implementation**: See `saas/config.py` function `_get_required_host()`

### Rule 164: Zero-Hardcode Mandate

- **NO** hardcoded passwords, tokens, or secrets in source code
- All secrets MUST come from Vault or environment variables
- Dev defaults allowed ONLY in `SA01_DEPLOYMENT_MODE=DEV` with warnings

**Implementation**: See `saas/config.py` function `_get_secret()`

---

## 5. Configuration Contract

| Variable | Repo | Values | Notes |
|----------|------|--------|-------|
| `SA01_DEPLOYMENT_MODE` | SomaAgent01 | `DEV` / `PROD` | Controls fail-fast behavior |
| `SOMA_SAAS_MODE` | SomaAgent01 | `true` / `false` | In-process vs HTTP |
| `SOMABRAIN_MODE` | SomaBrain | `dev` / `staging` / `prod` | Brain-specific |
| `SFM_AUTH_MODE` | SomaFractalMemory | Maps to StandAlone/Cluster | Memory auth |
| `SOMASTACK_SOFTWARE_MODE` | All | `StandAlone` / `SomaStackClusterMode` | Cross-repo |

---

## 6. Topology Export (SomaStack)

In SomaStackClusterMode, the platform must export a deterministic topology tree
labeled `SomaStack` with grouped planes:

- Control Plane: SomaAgent01 (Layer 4)
- Cognitive Plane: SomaBrain (Layer 3)
- Memory Plane: SomaFractalMemory (Layer 2)
- Infrastructure: PostgreSQL, Redis, Milvus (Layer 1)

---

## 7. Operational Rules

- StandAlone mode must never depend on other services for auth or memory.
- SomaStackClusterMode must fail closed if cross-service auth or memory is
  unavailable.
- Brain+Memory pairing is mandatory in SomaStackClusterMode.
- **PROD mode MUST fail-fast** on missing configuration (VIBE Rule 91).
- **Secrets MUST NOT be hardcoded** (VIBE Rule 164).

---

## 8. Audit Trail

| Date | Change | Author |
|------|--------|--------|
| 2026-01-13 | Added 4-dimension model, VIBE compliance section | SOMA Collective |
| 2025-12-30 | Initial version | Team |
