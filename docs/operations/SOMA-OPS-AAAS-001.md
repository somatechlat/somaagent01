# AAAS Standalone Deployment Guide

## Document Control

| Field | Value |
|---|---|
| Document Title | AAAS Standalone Deployment Guide |
| Document Identifier | SOMA-OPS-AAAS-001 |
| Version | 1.0.0 |
| Date | 2026-09-28 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2026-12-28 |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-09-28 | SomaTech Engineering | Initial issue. Brought under ISO document control. |


**Deployment Pattern:** Independent Repository Orchestration
**Status:** PRODUCTION READY

---

## 1. Overview
The SOMA AAAS Deployment is a **"Repository-Agnostic"** infrastructure. It enables the deployment of the entire SOMA Triad (Agent, Brain, Memory) from a single directory, treating the application repositories as interchangeable modules.

## 2. Deployment Structure

```
infra/aaas/
├── docker-compose.yml       # Infrastructure Definition
├── start_aaas.sh            # Startup Orchestrator
├── supervisord.conf         # Process Manager Config
├── build_aaas.sh            # Optimized Build Script
└── .env                     # Configuration (Git-Ignored)
```

## 3. The "Brain-First" Startup Logic
The `start_aaas.sh` script is the core intelligence of the deployment. It handles the critical "Brain-First" initialization sequence required for cognitive integrity.

```bash
# Pseudocode of start_aaas.sh logic
detect_hardware()
wait_for_ports(postgres, redis, kafka)

# CRITICAL: Recursive Schema Dependency Order
migrate(SomaBrain)          # Source of Truth
migrate(SomaFractalMemory)  # Dependent on Brain
migrate(SomaAgent01)        # Dependent on Brain + Memory

start_supervisor()          # Launch all processes
```

## 4. Isolation Strategy
- **Network Isolation**: All services run on the `soma_stack_net` bridge network.
- **Port Isolation**: External access is mapped to the `639xx` block to prevent conflicts with development tools running on default ports (e.g., local Postgres on 5432).
- **Process Isolation**: `supervisord` ensures that a crash in the Agent Runtime does not bring down the Cognitive Core (Brain) or Memory Store.

## 5. Build Optimization
The `build_aaas.sh` script creates a "Clean Context" for Docker builds. It explicitly filters out heavy artifacts:
- `.venv/`
- `node_modules/`
- `target/` (Rust builds)
- `__pycache__/`

This reduces the build context typically from >3GB to <200MB, ensuring rapid deployment cycles.
