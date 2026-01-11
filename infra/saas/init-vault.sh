#!/bin/bash
# =============================================================================
# VAULT INITIALIZATION SCRIPT - VIBE Rule 164
# =============================================================================
# Seeds Vault with initial secrets for SomaStack SaaS deployment.
# Run this AFTER Vault container is healthy.
# =============================================================================

set -e

VAULT_ADDR=${VAULT_ADDR:-http://localhost:63982}
VAULT_TOKEN=${VAULT_TOKEN:-soma_dev_token}

echo "🔒 Initializing Vault secrets..."
echo "   VAULT_ADDR: $VAULT_ADDR"

# Wait for Vault to be ready
until curl -s "$VAULT_ADDR/v1/sys/health" | grep -q '"sealed":false'; do
    echo "⏳ Waiting for Vault to be ready..."
    sleep 2
done

echo "✅ Vault is ready"

# Enable KV v2 secrets engine
curl -s -X POST \
    -H "X-Vault-Token: $VAULT_TOKEN" \
    -d '{"type": "kv", "options": {"version": "2"}}' \
    "$VAULT_ADDR/v1/sys/mounts/secret" 2>/dev/null || true

# Seed secrets
echo "📝 Seeding secrets..."

# Redis password (empty for local dev Redis without auth)
curl -s -X POST \
    -H "X-Vault-Token: $VAULT_TOKEN" \
    -d '{"data": {"password": ""}}' \
    "$VAULT_ADDR/v1/secret/data/soma/redis"

# Postgres password
curl -s -X POST \
    -H "X-Vault-Token: $VAULT_TOKEN" \
    -d '{"data": {"password": "soma", "user": "soma"}}' \
    "$VAULT_ADDR/v1/secret/data/soma/postgres"

# MinIO credentials
curl -s -X POST \
    -H "X-Vault-Token: $VAULT_TOKEN" \
    -d '{"data": {"access_key": "minioadmin", "secret_key": "minioadmin"}}' \
    "$VAULT_ADDR/v1/secret/data/soma/minio"

# SOMA API token
curl -s -X POST \
    -H "X-Vault-Token: $VAULT_TOKEN" \
    -d '{"data": {"token": "soma_saas_api_token_$(date +%s)"}}' \
    "$VAULT_ADDR/v1/secret/data/soma/api"

# Milvus token (empty for local dev)
curl -s -X POST \
    -H "X-Vault-Token: $VAULT_TOKEN" \
    -d '{"data": {"token": ""}}' \
    "$VAULT_ADDR/v1/secret/data/soma/milvus"

echo ""
echo "✅ Vault initialization complete!"
echo "   Secrets seeded at path: secret/soma/*"
echo ""
echo "   To verify:"
echo "   curl -H 'X-Vault-Token: $VAULT_TOKEN' $VAULT_ADDR/v1/secret/data/soma/postgres"
