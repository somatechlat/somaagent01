# SomaStack AAAS Deployment

> **Architecture**: True Monolith (Unified Process)
> **Stack**: Agent01 (Orchestrator), SomaBrain (Cognitive), FractalMemory (Vector Store)
> **Ports**: 63900 - 63999 (Strict Isolation)
> **Direct Mode**: Supported (See [GUIDE_AAAS_DIRECT.md](./GUIDE_AAAS_DIRECT.md))

## Overview
This directory contains the infrastructure-as-code (IaC) for the **SomaStack AAAS** deployment. This deployment packages the entire Cognitive Triad into a single Docker container (`somastack_aaas`) managed by `supervisord`.

## Directory Structure
- **`docker-compose.yml`**: Defines the `somastack_aaas` service and its 639xx infrastructure dependencies (Postgres, Redis, Kafka, Milvus/MinIO/Etcd).
- **`Dockerfile`**: A multi-stage build (Rust -> Python -> Runtime) that assembles the unified container.
- **`start_aaas.sh`**: The centralized entrypoint script.
    1.  Waits for Infrastructure (639xx ports).
    2.  Runs Django Migrations sequentially (Brain -> Memory -> Agent).
    3.  Starts `supervisord`.
- **`supervisord.conf`**: Process manager configuration for running the 3 internal services (Brain :9696, Memory :10101, Agent :9000).
- **`.env.example`**: Canonical configuration template for `SOMA_AAAS_MODE`.
- **`init-db.sh`**: Postgres initialization script creating the 3 logical databases.

## Naming Conventions
- **Container Name**: `somastack_aaas`
- **Environment Mode**: `SOMA_AAAS_MODE=true`
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
docker compose logs -f somastack_aaas
```

### Access
- **SomaBrain**: http://localhost:63996
- **FractalMemory**: http://localhost:63901
- **Agent01**: http://localhost:63900

## Milvus Vector Store Configuration

> **Critical**: Milvus v2.4.17 requires specific version combinations and network configuration.

### Required Versions
| Component | Version | Notes |
|-----------|---------|-------|
| etcd | v3.5.5 | Official Milvus release version |
| MinIO | RELEASE.2023-03-20T20-16-18Z | S3 API compatible |
| Milvus | v2.4.17 | Standalone mode |

### Network Alias (Required)
MinIO S3 API rejects hostnames with underscores. The `somastack_minio` container requires a network alias:

```yaml
somastack_minio:
  networks:
    soma_stack_net:
      aliases:
        - minio  # Critical: alias without underscore
```

Set `MINIO_ADDRESS: minio:9000` (not `somastack_minio:9000`).

### Key Settings
- `security_opt: seccomp:unconfined` required for Milvus
- `start_period: 90s` in healthcheck for coordinator startup
- `ETCD_ENDPOINTS: somastack_etcd:2379`
- etcd advertise-url: `http://127.0.0.1:2379`

### Verification
```bash
python3 -c "from pymilvus import connections; connections.connect('test', host='localhost', port='63953'); print('OK')"
```
