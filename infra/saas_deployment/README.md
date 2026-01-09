# SomaStack SaaS Deployment

> **Architecture**: True Monolith (Unified Process)
> **Stack**: Agent01 (Orchestrator), SomaBrain (Cognitive), FractalMemory (Vector Store)
> **Ports**: 63900 - 63999 (Strict Isolation)

## Overview
This directory contains the infrastructure-as-code (IaC) for the **SomaStack SaaS** deployment. This deployment packages the entire Cognitive Triad into a single Docker container (`somastack_saas`) managed by `supervisord`.

## Directory Structure
- **`docker-compose.yml`**: Defines the `somastack_saas` service and its 639xx infrastructure dependencies (Postgres, Redis, Kafka, Milvus/MinIO/Etcd).
- **`Dockerfile`**: A multi-stage build (Rust -> Python -> Runtime) that assembles the unified container.
- **`start_saas.sh`**: The centralized entrypoint script.
    1.  Waits for Infrastructure (639xx ports).
    2.  Runs Django Migrations sequentially (Brain -> Memory -> Agent).
    3.  Starts `supervisord`.
- **`supervisord.conf`**: Process manager configuration for running the 3 internal services (Brain :9696, Memory :10101, Agent :9000).
- **`.env.example`**: Canonical configuration template for `SOMA_SAAS_MODE`.
- **`init-db.sh`**: Postgres initialization script creating the 3 logical databases.

## Naming Conventions
- **Container Name**: `somastack_saas`
- **Environment Mode**: `SOMA_SAAS_MODE=true`
- **Infrastructure Prefix**: `somastack_` (e.g., `somastack_postgres`)

## Usage

### Prerequisites
- Docker & Docker Compose
- Ports 63900-63999 free

### Start
```bash
# Build and Start
docker compose up --build -d

# Check Logs
docker compose logs -f somastack_saas
```

### Access
- **SomaBrain**: http://localhost:63996
- **FractalMemory**: http://localhost:63901
- **Agent01**: http://localhost:63900
