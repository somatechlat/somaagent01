# SRS-AAAS-INFRASTRUCTURE: AAAS Deployment Architecture
**Version:** 2.0.0 (Standardized)
**Date:** 2026-01-21

---

## 1. Introduction
This specification defines the architecture for the **SOMA AAAS Infrastructure**, a completely independent deployment artifact designed to orchestrate the SOMA Triad (Agent, Brain, Memory) in a zero-dependency container environment.

## 2. Independence Strategy
The AAAS infrastructure is designed as a **Standalone Deployment Unit**. It does not inherently contain application code. Instead, it defines the runtime environment, network topology, and backing services required to execute the SOMA Stack.

### 2.1 Decoupling Principles
- **Source Code Injection**: Application code is injected at runtime via Docker volumes (Development) or COPY directives (Production).
- **Environment Abstraction**: All configuration variables are injected via `.env` files or HashiCorp Vault. No hardcoded configuration exists within the repository.
- **Orchestrator Isolation**: The startup logic (`start_aaas.sh`) is self-contained and versioned independently of the application logic.

## 3. Startup Sequence Architecture
The system enforces a rigorous, sequential initialization process to prevent race conditions and ensure data integrity.

### 3.1 Phase 1: Hardware & Infrastructure
1.  **Hardware Detection**: The `start_aaas.sh` orchestrator detects CUDA availability and sets `SOMA_HARDWARE_MODE`.
2.  **Infrastructure Wait-Loop**: The system polls TCP ports for backing services (Postgres:5432, Redis:6379, Kafka:9092) and blocks execution until all are confirmed ready.

### 3.2 Phase 2: Sequential Schema Migration (The "Brain-First" Strategy)
The migration order is strictly enforced to respect dependency hierarchies:
1.  **SomaBrain (Layer 3)**: Migrates first. Defines the cognitive schema and embedding spaces.
2.  **FractalMemory (Layer 2)**: Migrates second. Depends on Brain definitions for vector indexing.
3.  **Agent01 (Layer 4)**: Migrates last. Depends on both Brain and Memory persistence layers.

### 3.3 Phase 3: Process Management
- **Supervisor D**: The container executes `supervisord` as PID 1.
- **Process Isolation**: Each component (Agent, Brain, Memory) runs as a distinct `uvicorn`/`gunicorn` process, configured via `supervisord.conf`.

## 4. Network Topology & Port Authority
The AAAS environment uses a dedicated internal bridge network (`soma_stack_net`) with strict port forwarding for external access.

| Service | Host Port | Internal Port | Description |
|---------|-----------|---------------|-------------|
| **SomaAgent01** | 63900 | 9000 | Agent API |
| **SomaBrain** | 63996 | 9696 | Cognitive API |
| **SomaMemory** | 63901 | 10101 | Fractal Memory API |
| **Postgres** | 63932 | 5432 | Primary Persistence |
| **Redis** | 63979 | 6379 | Async Queue |
| **Milvus** | 63953 | 19530 | Vector Storage |
| **Kafka** | 63992 | 9092 | Event Bus |
| **Keycloak** | 63980 | 8080 | Identity Provider |
| **Vault** | 63982 | 8200 | Secrets Management |
