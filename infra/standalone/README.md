# SomaAgent01 Standalone Deployment

> **Architecture**: Agent-Only (No Brain, No Memory)
> **Port Namespace**: 20xxx (Strict Isolation from SaaS 63xxx)
> **Mode**: `SA01_DEPLOYMENT_MODE=STANDALONE`

## Overview

This directory contains the infrastructure-as-code (IaC) for the **Standalone Agent** deployment.
The Agent runs independently without SomaBrain or SomaFractalMemory dependencies.

## Directory Structure

- **`docker-compose.yml`**: Defines standalone Agent service and 20xxx dependencies
- **`Dockerfile`**: Single-service container for Agent only
- **`.env.example`**: Configuration template for Standalone mode
- **`start.sh`**: Entrypoint script with migration and health checks

## Port Mapping (20xxx Namespace)

| Service | Internal | External |
|---------|----------|----------|
| Agent API | 9000 | 20020 |
| PostgreSQL | 5432 | 20432 |
| Redis | 6379 | 20379 |
| Keycloak | 8080 | 20880 |

## Usage

### Prerequisites
- Docker & Docker Compose
- Ports 20xxx free

### Start
```bash
docker compose up --build -d
docker compose logs -f somaagent_standalone
```

### Access
- **Agent API**: http://localhost:20020
- **Health Check**: http://localhost:20020/api/v1/health

## Differences from SaaS Mode

| Feature | Standalone | SaaS |
|---------|------------|------|
| SomaBrain | ❌ Not included | ✅ In-process |
| FractalMemory | ❌ Not included | ✅ In-process |
| Port Range | 20xxx | 63xxx |
| Mode Variable | `STANDALONE` | `SAAS` |
