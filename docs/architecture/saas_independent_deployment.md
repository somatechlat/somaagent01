# SaaS Standalone Deployment Guide

**Deployment Pattern:** Independent Repository Orchestration
**Status:** PRODUCTION READY

---

## 1. Overview
The SOMA SaaS Deployment is a **"Repository-Agnostic"** infrastructure. It enables the deployment of the entire SOMA Triad (Agent, Brain, Memory) from a single directory, treating the application repositories as interchangeable modules.

## 2. Deployment Structure

```
infra/saas/
├── docker-compose.yml       # Infrastructure Definition
├── start_saas.sh            # Startup Orchestrator
├── supervisord.conf         # Process Manager Config
├── build_saas.sh            # Optimized Build Script
└── .env                     # Configuration (Git-Ignored)
```

## 3. The "Brain-First" Startup Logic
The `start_saas.sh` script is the core intelligence of the deployment. It handles the critical "Brain-First" initialization sequence required for cognitive integrity.

```bash
# Pseudocode of start_saas.sh logic
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
The `build_saas.sh` script creates a "Clean Context" for Docker builds. It explicitly filters out heavy artifacts:
- `.venv/`
- `node_modules/`
- `target/` (Rust builds)
- `__pycache__/`

This reduces the build context typically from >3GB to <200MB, ensuring rapid deployment cycles.
