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

# Track reserved ports to avoid duplicates during assignment (portable implementation).
RESERVED_PORTS=""

reserve_port() {
  RESERVED_PORTS="$RESERVED_PORTS $1"
}

is_reserved() {
  case " $RESERVED_PORTS " in
    *" $1 "*) return 0 ;;
    *) return 1 ;;
  esac
}

# Reserve the agent UI port up-front so no other service grabs it.
AGENT_UI_PORT=7002
reserve_port "$AGENT_UI_PORT"

# Function to find a free port starting from a base value.
find_free_port() {
  local port=$1
  while true; do
    if lsof -iTCP -sTCP:LISTEN -P | grep -q "\b$port\b"; then
      ((port++))
      continue
    fi
    if is_reserved "$port"; then
      ((port++))
      continue
    fi
    reserve_port "$port"
    echo $port
    return
  done
}

# Map of environment variable names to preferred starting ports.
PORT_VARS=(
  KAFKA_PORT
  REDIS_PORT
  POSTGRES_PORT
  QDRANT_HTTP_PORT
  QDRANT_GRPC_PORT
  CLICKHOUSE_HTTP_PORT
  CLICKHOUSE_NATIVE_PORT
  PROMETHEUS_PORT
  VAULT_PORT
  OPA_PORT
  OPENFGA_GRPC_PORT
  OPENFGA_HTTP_PORT
  WHISPER_PORT
  DELEGATION_GATEWAY_PORT_PRIMARY
  DELEGATION_GATEWAY_PORT_SECONDARY
)

PORT_BASES=(
  29092
  26379
  25432
  26666
  26667
  28181
  28190
  29090
  29200
  29181
  28281
  28280
  29901
  28015
  9697
)

# Detect and assign ports (override defaults if occupied).
for idx in "${!PORT_VARS[@]}"; do
  var=${PORT_VARS[$idx]}
  base=${PORT_BASES[$idx]}
  export "$var"="$(find_free_port "$base")"
done

# Enforce static agent UI port (7002) and fail fast if unavailable.
if lsof -iTCP -sTCP:LISTEN -P | grep -q "\b$AGENT_UI_PORT\b"; then
  echo "Error: Required agent UI port $AGENT_UI_PORT is already in use." >&2
  echo "Please free the port or stop the process using it, then rerun this script." >&2
  exit 1
fi
export WEB_UI_PORT=$AGENT_UI_PORT

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
  Web UI:         $WEB_UI_PORT (static)
EOF

# Export variables for Docker Compose substitution.
# The compose file uses the environment variables directly.
# Ensure the compose file references these variables (e.g., ${KAFKA_PORT}).

# Start the stack.
cd infra
docker compose -f docker-compose.somaagent01.yaml up -d
