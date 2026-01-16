# SOMA Stack: Unified SaaS (Direct Mode) Deployment Guide
> **Version**: 1.0.0 (Jan 2026)
> **Compliance**: ISO/IEC 29148:2018
> **Architecture**: Unified SaaS / Direct Integration

## 1. Overview
This guide routes the deployment of the **Unified SaaS (Direct Mode)**, where `somaAgent01`, `somabrain`, and `somafractalmemory` run within the **same Python process** (or shared runtime space) to achieve sub-millisecond memory operations.

### Key Architecture Differences
| Feature | Standard SaaS (HTTP) | Unified SaaS (Direct) |
| :--- | :--- | :--- |
| **Memory Access** | HTTP (`http://sfm:10101`) | **Direct Python Call** (`MemoryService`) |
| **Brain Integration** | HTTP (`http://brain:9696`) | **Hybrid** (Memory=Direct, Logic=HTTP) |
| **Latency** | ~10-50ms | **< 0.1ms** |
| **Config** | `SOMA_SAAS_MODE=true` | `SOMA_SAAS_MODE=direct` |

---

## 2. Prerequisites
1.  **Repository Siblings**: Ensure the designated repositories are checked out side-by-side:
    ```bash
    ~/workspace/
    ├── somaAgent01/      # Current Repo
    ├── somabrain/        # L3 Cognitive Layer
    └── somafractalmemory/ # L2 Storage Layer
    ```
2.  **Docker & Docker Compose**: Installed and running (v2.20+).
3.  **Port Availability**: Ensure ports `63900`-`63999` are free.

---

## 3. Configuration Step-by-Step

### Step 3.1: Configure Environment Variables
Create or update `infra/saas_deployment/.env` with the specific Direct Mode flags.

```bash
# infra/saas_deployment/.env

# --- CORE ARCHITECTURE MODES ---
SOMA_SAAS_MODE=direct                 # <--- ENABLES DIRECT MEMORY INTEGRATION
SOMABRAIN_ALLOW_LOCAL_MEMORY=true     # <--- ALLOWS BRAIN TO IMPORT SFM DIRECTLY

# --- NETWORK SETTINGS ---
SAGENTA_HOST=0.0.0.0
SAGENTA_PORT=9000

# --- SHARED INFRASTRUCTURE (Docker Internal) ---
SA01_DB_DSN=postgresql://soma:soma@somastack_postgres:5432/soma
SA01_REDIS_URL=redis://somastack_redis:6379/0
SA01_KAFKA_BOOTSTRAP_SERVERS=somastack_kafka:9092
```

### Step 3.2: Verify Codebase State
Ensure `somaAgent01` has the `BrainMemoryFacade` installed (verified present in `soma_core/`).

---

## 4. Deployment

### Step 4.1: Build the Unified SaaS
Use the unified build script which respects the sibling directory structure.

```bash
cd infra/saas_deployment
./build_saas.sh
```
*Note: This script mounts the sibling `somabrain` and `somafractalmemory` directories into the build context if not explicitly provided.*

### Step 4.2: Start Services
Launch the stack in detached mode.

```bash
docker compose up -d
```

### Step 4.3: Initialization (First Run Only)
The `start_saas.sh` script automatically handles:
1.  Waiting for Postgres/Redis/Kafka/Milvus.
2.  Running Migrations for all three services.
3.  Direct Mode validation.

Check logs to confirm "Direct Mode" activation:
```bash
docker compose logs -f somastack_saas | grep "Direct Mode"
```
*Expected Output:*
> `INFO somabrain.memory_client: Direct Mode: Linked to SomaFractalMemory (namespace=somabrain:default)`
> `INFO soma_core.memory_client: BrainMemoryFacade initialized in DIRECT mode`

---

## 5. Verification
Run the verification script included in `somaAgent01` to prove the persistence chain is unbroken.

```bash
# From the root of somaAgent01
python3 scripts/verify_persistence_chain.py
```

### Expected Results
- **Phase 1 (SFM Direct)**: ✅ GREEN (Row + AuditLog found)
- **Phase 2 (Brain Direct)**: ✅ GREEN (Row found via Brain wrapper)
- **Phase 3 (Agent Facade)**: ✅ GREEN (Row found via Agent Facade)

---

## 6. Troubleshooting

### "MemoryClient did not initialize _local backend!"
- **Cause**: `SOMABRAIN_ALLOW_LOCAL_MEMORY` is missing or false.
- **Fix**: Check `.env` and restart.

### "OperationalError: no such table"
- **Cause**: Migrations failed or database volume persisted old state.
- **Fix**:
    ```bash
    docker compose down -v
    docker compose up -d
    ```

### "ModuleNotFoundError: No module named 'somafractalmemory'"
- **Cause**: Docker volume bind mount for `somafractalmemory` is broken or path incorrect.
- **Fix**: Verify `docker-compose.yml` volumes section maps `../../../somafractalmemory:/app/somafractalmemory`.
