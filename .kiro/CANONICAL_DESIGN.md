# Canonical Design Specification

## 1. Introduction
This document defines the unified architectural design for SomaAgent01. It enforces Clean Architecture (DDD), specifies the integration of security components (OPA, TUS, ClamAV), and details the modern Web UI implementation.

---

## 2. High-Level Architecture

### 2.1. Layered Architecture (Clean Architecture)
The system obeys the Dependency Rule: *Source code dependencies can only point inwards.*

```mermaid
graph TD
    subgraph Infrastructure ["Infrastructure (Outer)"]
        Web[FastAPI Controllers]
        DB[Postgres/Chroma Adapter]
        Bus[Kafka Adapter]
        Ext[SomaBrain/OPA Client]
    end

    subgraph Application ["Application (Middle)"]
        UC[Use Cases / Interactors]
        Services[Domain Services]
    end

    subgraph Domain ["Domain (Inner)"]
        Entities[Entities & Aggregates]
        VO[Value Objects]
        Ports[Repository Interfaces]
    end

    Web --> UC
    UC --> Ports
    UC --> Entities
    Infrastructure -.-> Ports : implements
```

### 2.2. Directory Structure
```
src/
├── core/
│   ├── domain/               # Pure business logic
│   │   ├── entities/
│   │   ├── value_objects/
│   │   ├── ports/            # Interfaces for repos/gateways
│   │   └── exceptions.py
│   ├── application/          # Use Cases
│   │   ├── use_cases/
│   │   └── dtos/
│   ├── infrastructure/       # Implementations
│   │   ├── persistence/
│   │   ├── adapters/         # OPA, SomaBrain, FileSystem adapters
│   │   └── config/           # ConfigFacade
│   └── main.py              # App Assembly
├── services/                 # Microservices/Modules (Gradually migrating to Core)
│   ├── gateway/              # API Gateway
│   ├── conversation_worker/  # Message Processor
│   └── ...
```

---

## 3. Component Design

### 3.1. Configuration System
**Pattern:** Singleton Facade
*   **Class:** `ConfigFacade`
*   **Responsibility:** Aggregates environment variables (`SA01_` prefix), CLI args, and Secrets (Vault).
*   **Usage:** `cfg.env("KEY")` everywhere. No direct `os.getenv`.

### 3.2. Security Subsystems

#### A. Authorization (OPA)
*   **Integration:** `OPAPolicyAdapter` implements `PolicyPort`.
*   **Flow:**
    1.  Agent attempts tool execution.
    2.  `ToolExecutor` calls `PolicyPort.evaluate(action, resource, context)`.
    3.  Adapter queries OPA Service via HTTP.
    4.  If `allow: false`, execution halts.

#### B. File Security (Uploads)
*   **Protocol:** TUS (Resumable Uploads)
*   **Storage:** `UploadsRepository` (Metadata in DB, content in implementation-specific store).
*   **Scanning Pipeline:**
    1.  User Uploads -> `temp_storage`.
    2.  `ClamAVScanner` scans stream.
    3.  If Clean -> Move to `permanent_storage`.
    4.  If Malware -> Quarantine & Alert.

### 3.3. Web UI Architecture

#### A. Frontend Stack
*   **Framework:** Vanilla JS + Alpine.js (Reactive State).
*   **Design System:** CSS Variables (Glassmorphism theme).
*   **Build:** Vite (optional, mostly ESM).

#### B. State Management (Store Pattern)
*   Each feature (Chat, Settings, Memory) has a `store.js`.
*   **Pattern:** `createStore(initialState, actions)`.
*   **Reactivity:** Alpine.js `x-data="$store.feature"`.

#### C. Communication
*   **REST:** Standard JSON APIs for CRUD.
*   **SSE:** `/v1/sessions/{id}/events` for chat streaming and live updates.

---

## 4. Interfaces & Contracts

### 4.1. Domain Ports (Examples)

**SessionRepositoryPort:**
```python
class SessionRepositoryPort(ABC):
    @abstractmethod
    async def get_session(self, session_id: str) -> Session: ...
    @abstractmethod
    async def save_session(self, session: Session) -> None: ...
```

**PolicyAdapterPort:**
```python
class PolicyAdapterPort(ABC):
    @abstractmethod
    async def check_tool_access(self, tenant_id: str, tool_name: str) -> bool: ...
```

---

## 5. Deployment & Operations

### 5.1. Containers
*   **Service:** Python 3.11 Slim.
*   **Security:** Non-root user, multi-stage builds.
*   **Sidecars:** Fluentd (Logs), Envoy (Mesh - optional).

### 5.2. Observability
*   **Metrics:** Prometheus (`/metrics`).
*   **Tracing:** OpenTelemetry (propagated via Kafka headers).
*   **Health:** `DegradationMonitor` checks dependencies periodically.
