#!/usr/bin/env bash
set -euo pipefail

# -------------------------------------------------------------------
# 1️⃣  Expected argument – deployment mode
# -------------------------------------------------------------------
MODE=${1:-dev_full}   # allowed values: dev_full | dev_prod | prod | prod_ha

# -------------------------------------------------------------------
# 2️⃣  Helper to convert boolean to lower‑case string for env files
# -------------------------------------------------------------------
bool() {
  case "$1" in
    true|True|TRUE) echo true ;;
    false|False|FALSE) echo false ;;
    *) echo "$1" ;;
  esac
}

# -------------------------------------------------------------------
# 3️⃣  Derive mode‑specific flags
# -------------------------------------------------------------------
case "$MODE" in
  dev_full)
    JWT_ENABLED=$(bool false)
    OPA_ENABLED=$(bool false)
    MTLS_ENABLED=$(bool false)
    ENABLE_REAL_EMBEDDINGS=$(bool false)
    USE_REAL_INFRA=$(bool false)
    REPLICA_COUNT=1
    ISTIO_INJECTION=$(bool false)
    VAULT_AGENT_INJECT=$(bool false)
    ;;
  dev_prod)
    JWT_ENABLED=$(bool true)
    OPA_ENABLED=$(bool true)
    MTLS_ENABLED=$(bool true)
    ENABLE_REAL_EMBEDDINGS=$(bool true)
    USE_REAL_INFRA=$(bool true)
    REPLICA_COUNT=1
    ISTIO_INJECTION=$(bool true)
    VAULT_AGENT_INJECT=$(bool true)
    ;;
  prod)
    JWT_ENABLED=$(bool true)
    OPA_ENABLED=$(bool true)
    MTLS_ENABLED=$(bool true)
    ENABLE_REAL_EMBEDDINGS=$(bool true)
    USE_REAL_INFRA=$(bool true)
    REPLICA_COUNT=2
    ISTIO_INJECTION=$(bool true)
    VAULT_AGENT_INJECT=$(bool true)
    ;;
  prod_ha)
    JWT_ENABLED=$(bool true)
    OPA_ENABLED=$(bool true)
    MTLS_ENABLED=$(bool true)
    ENABLE_REAL_EMBEDDINGS=$(bool true)
    USE_REAL_INFRA=$(bool true)
    REPLICA_COUNT=3
    ISTIO_INJECTION=$(bool true)
    VAULT_AGENT_INJECT=$(bool true)
    ;;
  *)
    echo "Unsupported mode: $MODE" >&2
    exit 1
    ;;
esac

# -------------------------------------------------------------------
# 4️⃣  Write the .env file – values are identical for Docker‑Compose and Helm
# -------------------------------------------------------------------
cat > /root/soma-global.env <<EOF
# ---------------------------------------------------------------
# Unified global environment – generated for mode: $MODE
# ---------------------------------------------------------------
DEPLOY_MODE=$MODE

# Security flags
JWT_ENABLED=$JWT_ENABLED
OPA_ENABLED=$OPA_ENABLED
MTLS_ENABLED=$MTLS_ENABLED

# Feature toggles
ENABLE_REAL_EMBEDDINGS=$ENABLE_REAL_EMBEDDINGS
USE_REAL_INFRA=$USE_REAL_INFRA

# Replicas (used by Helm only)
REPLICA_COUNT=$REPLICA_COUNT

# Resource hints (used by Helm only)
CPU_REQUEST=100m
CPU_LIMIT=200m
MEM_REQUEST=128Mi
MEM_LIMIT=256Mi

# Istio & Vault side‑car injection (Helm only)
ISTIO_INJECTION=$ISTIO_INJECTION
VAULT_AGENT_INJECT=$VAULT_AGENT_INJECT

# Static infrastructure ports (same across all modes)
POSTGRES_PORT=5432
REDIS_PORT=6379
QDRANT_PORT=6333
KAFKA_PORT=9092
API_PORT=9595

# Database credentials – in prod/prod_ha they will be overridden by Vault
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=somamemory

# Observability flags
PROMETHEUS_SCRAPE=true
OTEL_ENABLED=true
EOF

echo "✅ Global env generated at /root/soma-global.env for mode '$MODE'"