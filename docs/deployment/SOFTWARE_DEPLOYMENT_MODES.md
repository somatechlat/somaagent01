# Software Deployment Modes

## Overview

SomaAgent01 supports two canonical deployment modes across all services:

| Mode | Description | Use Case |
|------|-------------|----------|
| **Standalone** | Each service runs independently with local auth/storage. No required cross-service calls. | Local development, single-node deployments |
| **SomaStackClusterMode (AAAS)** | All services run as one unified cluster. SomaBrain + SomaFractalMemory are inseparable and run as a paired runtime with shared tenant identity and auth. | Production, multi-node Kubernetes |

## Configuration

Deployment mode is controlled by the `SA01_DEPLOYMENT_MODE` environment variable:

```bash
# Standalone mode
SA01_DEPLOYMENT_MODE=STANDALONE

# AAAS / Cluster mode
SA01_DEPLOYMENT_MODE=AAAS
```

**Legacy variables** (`SOMA_DEPLOY_MODE`, `SOMA_AAAS_MODE`, `AAAS_ENABLED`) are deprecated and should not be used.

## Standalone Mode

In Standalone mode:
- Each service (SomaAgent01, SomaBrain, SomaFractalMemory) runs independently
- Services communicate via HTTP APIs only
- Local SQLite or PostgreSQL can be used for persistence
- No shared container or in-process memory access

### Required Environment Variables

```bash
SA01_DEPLOYMENT_MODE=STANDALONE
SA01_DB_DSN=postgresql://user:pass@localhost:5432/somaagent
SA01_REDIS_URL=redis://localhost:6379/0
SA01_SOMA_BASE_URL=http://localhost:30101
SA01_KEYCLOAK_URL=http://localhost:20880
```

## AAAS Mode (SomaStackClusterMode)

In AAAS mode:
- All services run in the same process space or tightly coupled cluster
- SomaBrain and SomaFractalMemory share tenant identity and authentication
- Direct in-process memory access via `BrainBridge` is available
- Requires all infrastructure services (PostgreSQL, Redis, Kafka, Milvus, Keycloak, SpiceDB, OPA)

### Required Environment Variables

```bash
SA01_DEPLOYMENT_MODE=AAAS
SA01_DB_DSN=postgresql://user:pass@localhost:5432/somaagent
SA01_REDIS_URL=redis://localhost:6379/0
SA01_KAFKA_BOOTSTRAP_SERVERS=localhost:20092
SA01_SOMA_BASE_URL=http://localhost:30101
SA01_KEYCLOAK_URL=http://localhost:20880
SA01_OPA_URL=http://localhost:20181
```

## Migration Between Modes

There is no automatic migration path between Standalone and AAAS modes. To migrate:

1. Export data from the standalone database
2. Set up AAAS infrastructure (see DEPLOYMENT.md)
3. Import data into the AAAS database
4. Update environment variables
5. Restart services

## Development vs Production

The `SA01_ENVIRONMENT` variable controls development-specific behavior:

```bash
SA01_ENVIRONMENT=dev    # Development: debug mode, relaxed auth, auto-reload
SA01_ENVIRONMENT=prod   # Production: strict auth, no debug, full observability
```

**Security note:** Never set `DEBUG=true` or `SA01_ENVIRONMENT=dev` in production. The `ALLOW_INSECURE_AUTH_BYPASS` flag has been removed from production code.
