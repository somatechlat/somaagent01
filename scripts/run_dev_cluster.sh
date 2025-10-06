#!/usr/bin/env bash
# Auto-detect free ports for the SomaAgent01 development stack and start Docker Compose.
# Ports used by the default compose file (infra/docker-compose.somaagent01.yaml):
#   Kafka   9095
#   Redis   6380
#   Postgres5434
#   ClickHouse8123
#   Qdrant 6333
#   Prometheus9090
#   Vault   8200
#   OPA     8181
#   Whisper 9001
#   Delegation Gateway 8015
#   UI (gateway) 8001
#   Web UI 50001 (exposed by run_ui container)

# Function to find a free port starting from a base value.
find_free_port() {
  local port=$1
  while lsof -iTCP -sTCP:LISTEN -P | grep -q "\b$port\b"; do
    ((port++))
  done
  echo $port
}

# Detect and assign ports (override defaults if occupied).
export KAFKA_PORT=$(find_free_port 9095)
export REDIS_PORT=$(find_free_port 6380)
export POSTGRES_PORT=$(find_free_port 5434)
export CLICKHOUSE_PORT=$(find_free_port 8123)
export QDRANT_PORT=$(find_free_port 6333)
export PROMETHEUS_PORT=$(find_free_port 9090)
export VAULT_PORT=$(find_free_port 8200)
export OPA_PORT=$(find_free_port 8181)
export WHISPER_PORT=$(find_free_port 9001)
export DELEGATION_GATEWAY_PORT=$(find_free_port 8015)
export GATEWAY_PORT=$(find_free_port 8001)
export UI_PORT=$(find_free_port 50001)
export WEB_UI_PORT=$UI_PORT

# Print chosen ports for verification.
cat <<EOF
Port assignments:
  Kafka:          $KAFKA_PORT
  Redis:          $REDIS_PORT
  Postgres:       $POSTGRES_PORT
  ClickHouse:     $CLICKHOUSE_PORT
  Qdrant:         $QDRANT_PORT
  Prometheus:     $PROMETHEUS_PORT
  Vault:          $VAULT_PORT
  OPA:            $OPA_PORT
  Whisper:        $WHISPER_PORT
  Delegation GW:  $DELEGATION_GATEWAY_PORT
  Gateway API:    $GATEWAY_PORT
  UI (web):       $UI_PORT
EOF

# Export variables for Docker Compose substitution.
# The compose file uses the environment variables directly.
# Ensure the compose file references these variables (e.g., ${KAFKA_PORT}).

# Start the stack.
cd infra
docker compose -f docker-compose.somaagent01.yaml up -d
