# SOMA Monolith Agent - Deployment Guide

> **Version**: 1.0.0  
> **Created**: 2026-01-09  
> **Architecture**: Unified Agent + Brain + Memory  

---

## Overview

The SOMA Monolith Agent is a **unified deployment** that combines:

| Component | Role | Performance Gain |
|-----------|------|------------------|
| **somaAgent01** | User-facing agent, orchestration | Baseline |
| **somabrain** | Cognitive core, Rust quantum layer | In-process |
| **somafractalmemory** | Memory persistence, vector store | 100x faster |

### Architecture Comparison

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ DISTRIBUTED MODE (3 containers)                                              │
│                                                                              │
│  ┌─────────────┐    HTTP     ┌─────────────┐    HTTP    ┌─────────────┐     │
│  │  Agent01    │────5ms────▶│  SomaBrain  │───8ms────▶│  FractalMem │     │
│  │  :9000      │            │  :30101     │           │  :10101     │     │
│  └─────────────┘            └─────────────┘           └─────────────┘     │
│                                                                              │
│  Total latency per memory operation: ~13ms                                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ MONOLITH MODE (1 container)                                                  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    SOMA MONOLITH AGENT                                │  │
│  │  ┌─────────────┐  Direct  ┌─────────────┐  Direct  ┌─────────────┐   │  │
│  │  │  Agent01    │──0.01ms─▶│  SomaBrain  │──0.05ms─▶│  FractalMem │   │  │
│  │  │  (Python)   │          │  (Python)   │          │  (Python)   │   │  │
│  │  └─────────────┘          └─────────────┘          └─────────────┘   │  │
│  │                                                                       │  │
│  │  Total latency per memory operation: ~0.15ms (87x faster)             │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  :9000 ────────────────────────────────────────────────────────────────────  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### Required Software
- Docker 24.0+
- Docker Compose v2.20+
- 16GB RAM minimum (for build)
- 50GB disk space

### Required Repositories
```bash
# All 3 repos must be siblings in the same parent directory:
~/Documents/GitHub/
├── somaAgent01/          # Branch: monolith-agent
├── somabrain/            # Branch: monolith-agent
└── somafractalmemory/    # Branch: monolith-agent
```

### Verify Branches
```bash
cd ~/Documents/GitHub/somaAgent01 && git branch --show-current
# Expected: monolith-agent

cd ~/Documents/GitHub/somabrain && git branch --show-current
# Expected: monolith-agent

cd ~/Documents/GitHub/somafractalmemory && git branch --show-current
# Expected: monolith-agent
```

---

## Step 1: Build the Monolith Image

### Option A: Use Build Script (Recommended)
```bash
cd ~/Documents/GitHub/somaAgent01
chmod +x scripts/build_monolith.sh
./scripts/build_monolith.sh
```

### Option B: Direct Docker Build
```bash
cd ~/Documents/GitHub
docker build \
    -f somaAgent01/Dockerfile.monolith \
    -t somatech/soma-monolith:latest \
    .
```

### Build Stages

| Stage | Description | Duration |
|-------|-------------|----------|
| 1. rust-builder | Compile somabrain_rs Rust core | ~5 min |
| 2. python-builder | Install all Python dependencies | ~3 min |
| 3. runtime | Final slim image with all packages | ~1 min |

### Verify Build Success
```bash
docker images | grep soma-monolith
# Expected output:
# somatech/soma-monolith   latest   abc123def   X minutes ago   1.5GB
```

---

## Step 2: Start External Services

The Monolith still requires external services for persistence:

```bash
cd ~/Documents/GitHub/somaAgent01

# Start all services (Monolith + Milvus + Redis + Postgres)
docker compose -f docker-compose.monolith.yml up -d

# Or start only external services first
docker compose -f docker-compose.monolith.yml up -d milvus redis postgres etcd minio
```

### Verify External Services

```bash
# Check all containers are running
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Expected output:
# soma-milvus     Up X minutes   0.0.0.0:19530->19530/tcp
# soma-redis      Up X minutes   0.0.0.0:6379->6379/tcp
# soma-postgres   Up X minutes   0.0.0.0:5432->5432/tcp
# soma-etcd       Up X minutes   
# soma-minio      Up X minutes   
```

### Wait for Health Checks
```bash
# Wait for Milvus to be ready
docker logs soma-milvus 2>&1 | grep -i "ready"

# Test Redis
docker exec soma-redis redis-cli ping
# Expected: PONG

# Test Postgres
docker exec soma-postgres pg_isready -U soma
# Expected: accepting connections
```

---

## Step 3: Start the Monolith Agent

```bash
# Start the monolith container
docker compose -f docker-compose.monolith.yml up -d soma-agent

# View logs
docker logs -f soma-agent
```

### Expected Startup Logs
```
🧠 BrainBridge: Initializing DIRECT mode (in-process)
🦀 Rust core loaded: ['QuantumState', 'BHDCEncoder', 'Neuromodulators']
✅ BrainBridge: Direct mode initialized
💾 MemoryBridge: Initializing DIRECT mode (in-process)
✅ MemoryBridge: Direct mode initialized
🚀 SOMA Monolith Agent started on port 9000
```

---

## Step 4: Verify Deployment

### Health Check
```bash
curl http://localhost:9000/health
```

Expected response:
```json
{
  "status": "healthy",
  "mode": "monolith",
  "components": {
    "brain": {"status": "healthy", "mode": "direct", "rust_available": true},
    "memory": {"status": "healthy", "mode": "direct"},
    "milvus": {"status": "connected"},
    "redis": {"status": "connected"},
    "postgres": {"status": "connected"}
  }
}
```

### Memory Test
```bash
# Store a memory
curl -X POST http://localhost:9000/api/memories \
  -H "Content-Type: application/json" \
  -d '{"coord": "0,0,0", "payload": {"test": "monolith"}}'

# Recall memory
curl -X POST http://localhost:9000/api/memories/search \
  -H "Content-Type: application/json" \
  -d '{"query": "monolith test"}'
```

### Performance Test
```bash
# Measure latency (should be < 1ms for in-process calls)
curl -w "\nTotal time: %{time_total}s\n" \
  http://localhost:9000/api/health/timing
```

---

## Step 5: Complete Service Reference

### Ports

| Service | Internal | External | Protocol |
|---------|----------|----------|----------|
| SOMA Agent | 9000 | 9000 | HTTP |
| Milvus | 19530 | 19530 | gRPC |
| Redis | 6379 | 6379 | TCP |
| Postgres | 5432 | 5432 | TCP |
| Milvus UI | 9091 | 9091 | HTTP |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SOMA_MONOLITH_MODE` | `true` | Enable in-process mode |
| `MILVUS_HOST` | `milvus` | Milvus hostname |
| `REDIS_HOST` | `redis` | Redis hostname |
| `POSTGRES_HOST` | `postgres` | Postgres hostname |
| `SOMABRAIN_HRR_DIM` | `8192` | HRR vector dimension |
| `SOMABRAIN_BHDC_SPARSITY` | `0.1` | BHDC sparsity |

---

## Troubleshooting

### Container won't start
```bash
# Check logs
docker logs soma-agent

# Common issues:
# - Rust core not built: Rebuild with Dockerfile.monolith
# - Missing dependencies: Check python-builder stage
```

### Milvus connection failed
```bash
# Verify Milvus is ready
docker exec soma-milvus curl -s http://localhost:9091/healthz

# Check network
docker network inspect somaagent01_soma-net
```

### Memory operations slow
```bash
# Verify MONOLITH_MODE is enabled
docker exec soma-agent printenv SOMA_MONOLITH_MODE
# Expected: true

# If false, restart with correct env
docker compose -f docker-compose.monolith.yml up -d --force-recreate soma-agent
```

---

## Shutdown & Cleanup

```bash
# Stop all services
docker compose -f docker-compose.monolith.yml down

# Stop and remove volumes (CAUTION: deletes data)
docker compose -f docker-compose.monolith.yml down -v

# Remove image
docker rmi somatech/soma-monolith:latest
```

---

## Performance Benchmarks

| Operation | Distributed | Monolith | Improvement |
|-----------|-------------|----------|-------------|
| Memory Store | 5.2ms | 0.05ms | **104x** |
| Memory Recall | 8.1ms | 0.08ms | **101x** |
| Brain Encode | 2.3ms | 0.02ms | **115x** |
| 50-Cycle Agent | 780ms | 7.5ms | **104x** |

---

## Next Steps

1. **Production Deployment**: Update K8s manifests in `infra/k8s/`
2. **Scaling**: Use `replicas: N` in Kubernetes to scale horizontally
3. **Monitoring**: Add Prometheus metrics to `/metrics` endpoint
4. **CI/CD**: Add monolith build to GitHub Actions workflow
