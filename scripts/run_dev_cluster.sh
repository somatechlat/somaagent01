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
#   Web UI 50002 (exposed by run_ui container)

# Track reserved ports to avoid duplicates during assignment.
declare -A RESERVED_PORTS=()

# Function to find a free port starting from a base value.
find_free_port() {
  local port=$1
  while true; do
    if lsof -iTCP -sTCP:LISTEN -P | grep -q "\b$port\b"; then
      ((port++))
      continue
    fi
    if [[ -n "${RESERVED_PORTS[$port]}" ]]; then
      ((port++))
      continue
    fi
    RESERVED_PORTS[$port]=1
    echo $port
    return
  done
}

# Map of environment variable names to preferred starting ports.
declare -A PORT_MAP=(
  [KAFKA_PORT]=29092
  [REDIS_PORT]=26379
  [POSTGRES_PORT]=25432
  [QDRANT_HTTP_PORT]=26666
  [QDRANT_GRPC_PORT]=26667
  [CLICKHOUSE_HTTP_PORT]=28181
  [CLICKHOUSE_NATIVE_PORT]=28190
  [PROMETHEUS_PORT]=29090
  [VAULT_PORT]=29200
  [OPA_PORT]=29181
  [OPENFGA_GRPC_PORT]=28281
  [OPENFGA_HTTP_PORT]=28280
  [WHISPER_PORT]=29901
  [DELEGATION_GATEWAY_PORT_PRIMARY]=28015
  [DELEGATION_GATEWAY_PORT_SECONDARY]=9697
  [WEB_UI_PORT]=50001
)

# Detect and assign ports (override defaults if occupied).
for var in "${!PORT_MAP[@]}"; do
  export "$var"="$(find_free_port "${PORT_MAP[$var]}")"
done

# Print chosen ports for verification.
cat <<EOF
Port assignments:
  Kafka:          $KAFKA_PORT
  Redis:          $REDIS_PORT
  Postgres:       $POSTGRES_PORT
  Qdrant (HTTP):  $QDRANT_HTTP_PORT
  Qdrant (gRPC):  $QDRANT_GRPC_PORT
  ClickHouse HTTP:$CLICKHOUSE_HTTP_PORT
  ClickHouse TCP: $CLICKHOUSE_NATIVE_PORT
  Prometheus:     $PROMETHEUS_PORT
  Vault:          $VAULT_PORT
  OPA:            $OPA_PORT
  OpenFGA gRPC:   $OPENFGA_GRPC_PORT
  OpenFGA HTTP:   $OPENFGA_HTTP_PORT
  Whisper:        $WHISPER_PORT
  Delegation GW A:$DELEGATION_GATEWAY_PORT_PRIMARY
  Delegation GW B:$DELEGATION_GATEWAY_PORT_SECONDARY
  Web UI:         $WEB_UI_PORT
EOF

# Export variables for Docker Compose substitution.
# The compose file uses the environment variables directly.
# Ensure the compose file references these variables (e.g., ${KAFKA_PORT}).

# Start the stack.
cd infra
docker compose -f docker-compose.somaagent01.yaml up -d
