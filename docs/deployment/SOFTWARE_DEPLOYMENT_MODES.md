# Software Deployment Modes (SomaStack)

**Purpose:** Define software-level modes for the three services when run
standalone or as a unified SaaS.

---

## 1. Mode Names (Canonical)

- **StandAlone**: Each service runs independently with its own auth, storage,
  and configuration.
- **SomaStackClusterMode**: All three services run as a unified SaaS with shared
  tenant identity, shared authorization, and coupled Brain+Memory runtime.

These names are canonical for documentation and future configuration flags.

---

## 2. Behavior by Mode

### 2.1 StandAlone

- Each service must boot and operate without dependencies on the other two.
- Local auth and storage must be sufficient for basic operation.
- Cross-service calls are disabled by default or use local stubs.

### 2.2 SomaStackClusterMode

- SomaAgent01 is the control plane (tenants, users, agents, billing).
- SomaBrain and SomaFractalMemory are inseparable and must run as a paired
  runtime for memory-backed cognition.
- Cross-service calls require service-to-service auth and shared tenant claims.
- Fine-grained permissions must be enforced via the unified authorization model
  (SpiceDB in the control plane, policy enforcement in downstream services).

---

## 3. Configuration Contract (Proposed)

This contract is a shared, future-facing requirement (not fully implemented
across all repos yet):

- `SOMASTACK_SOFTWARE_MODE` = `StandAlone` | `SomaStackClusterMode`
- `SOMASTACK_CLUSTER_LABEL` = `SomaStack`

Repo-specific alignment:
- **SomaAgent01**: continue using `SA01_DEPLOYMENT_MODE` (DEV/PROD) and
  `SA01_DEPLOYMENT_TARGET` (LOCAL/EKS/etc). Add `SOMASTACK_SOFTWARE_MODE` for
  software-level behavior.
- **SomaBrain**: keep `SOMABRAIN_MODE` (dev/staging/prod). Add
  `SOMASTACK_SOFTWARE_MODE` to enforce external auth + memory coupling.
- **SomaFractalMemory**: map `SFM_AUTH_MODE` to `StandAlone`/`SomaStackClusterMode`
  and enforce tenant claims for integrated calls.

---

## 4. Topology Export (SomaStack)

In SomaStackClusterMode, the platform must export a deterministic topology tree
labeled `SomaStack` with grouped planes:

- Control Plane: SomaAgent01
- Cognitive Plane: SomaBrain
- Memory Plane: SomaFractalMemory

---

## 5. Operational Rules

- StandAlone mode must never depend on other services for auth or memory.
- SomaStackClusterMode must fail closed if cross-service auth or memory is
  unavailable.
- Brain+Memory pairing is mandatory in SomaStackClusterMode.
