#!/bin/bash
# =============================================================================
# VAULT INITIALIZATION SCRIPT - VIBE Rule 164
# =============================================================================
# Seeds Vault with initial secrets for SomaStack AAAS deployment.
# Run this AFTER Vault container is healthy.
# =============================================================================

set -e

VAULT_ADDR=${VAULT_ADDR:-http://localhost:63982}
if [ -z "${VAULT_TOKEN}" ]; then
    echo "❌ VAULT_TOKEN is required. Set it via environment variable."
    exit 1
fi

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

# Postgres credentials (from environment - fail if not set)
if [ -z "${SOMA_POSTGRES_USER}" ] || [ -z "${SOMA_POSTGRES_PASSWORD}" ]; then
    echo "❌ SOMA_POSTGRES_USER and SOMA_POSTGRES_PASSWORD are required."
    exit 1
fi
curl -s -X POST \
    -H "X-Vault-Token: $VAULT_TOKEN" \
    -d "{\"data\": {\"password\": \"$SOMA_POSTGRES_PASSWORD\", \"user\": \"$SOMA_POSTGRES_USER\"}}" \
    "$VAULT_ADDR/v1/secret/data/soma/postgres"

# MinIO credentials (from environment - fail if not set)
if [ -z "${MINIO_ACCESS_KEY}" ] || [ -z "${MINIO_SECRET_KEY}" ]; then
    echo "❌ MINIO_ACCESS_KEY and MINIO_SECRET_KEY are required."
    exit 1
fi
curl -s -X POST \
    -H "X-Vault-Token: $VAULT_TOKEN" \
    -d "{\"data\": {\"access_key\": \"$MINIO_ACCESS_KEY\", \"secret_key\": \"$MINIO_SECRET_KEY\"}}" \
    "$VAULT_ADDR/v1/secret/data/soma/minio"

# SOMA API token (cryptographically random)
SOMA_API_TOKEN="$(openssl rand -hex 32 2>/dev/null || python3 -c 'import secrets; print(secrets.token_hex(32))')"
curl -s -X POST \
    -H "X-Vault-Token: $VAULT_TOKEN" \
    -d "{\"data\": {\"token\": \"$SOMA_API_TOKEN\"}}" \
    "$VAULT_ADDR/v1/secret/data/soma/api"

# Milvus token (empty for local dev)
curl -s -X POST \
    -H "X-Vault-Token: $VAULT_TOKEN" \
    -d '{"data": {"token": ""}}' \
    "$VAULT_ADDR/v1/secret/data/soma/milvus"

# =============================================================================
# LLM PROVIDER API KEYS - VIBE Rule 164 (Vault-Mandatory)
# =============================================================================
# Path: secret/agent/api_keys/{provider}_api_key
# Used by: UnifiedSecretManager.get_provider_key()
# =============================================================================

echo "🤖 Initializing LLM provider API keys path..."

# Create agent/api_keys path with placeholder structure
# Actual keys should be set via Admin UI or CLI, NOT hardcoded here
curl -s -X POST \
    -H "X-Vault-Token: $VAULT_TOKEN" \
    -d '{"data": {"_initialized": "true"}}' \
    "$VAULT_ADDR/v1/secret/data/agent/api_keys"

# Create agent/credentials path for other secrets
curl -s -X POST \
    -H "X-Vault-Token: $VAULT_TOKEN" \
    -d '{"data": {"_initialized": "true"}}' \
    "$VAULT_ADDR/v1/secret/data/agent/credentials"

echo ""
echo "✅ Vault initialization complete!"
echo "   Infrastructure secrets: secret/soma/*"
echo "   LLM Provider keys:      secret/agent/api_keys/*"
echo "   Agent credentials:      secret/agent/credentials/*"
echo ""
echo "   To add LLM provider key:"
echo "   curl -X POST -H 'X-Vault-Token: $VAULT_TOKEN' \\"
echo "     -d '{\"data\": {\"openrouter_api_key\": \"sk-or-...\"}}'  \\"
echo "     $VAULT_ADDR/v1/secret/data/agent/api_keys"
echo ""
echo "   To verify:"
echo "   curl -H 'X-Vault-Token: $VAULT_TOKEN' $VAULT_ADDR/v1/secret/data/agent/api_keys"
