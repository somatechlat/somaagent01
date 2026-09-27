#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# SOMA FULL STACK — Agent + SomaBrain + SomaFractalMemory on one Docker network
# ═══════════════════════════════════════════════════════════════════════════════
# Brings up the real triad so the WebUI can be tested end to end:
#   1. external network  soma-stack-net
#   2. somafractalmemory (real, with Postgres+Milvus+MinIO+Vault+OPA)
#   3. somabrain         (real, with Kafka+Postgres+Vault+OPA)
#   4. somaagent01       (agent API + WebUI + Keycloak, wired to both)
#
# Usage:
#   ./up-cluster.sh            # build + start everything, wait for health
#   ./up-cluster.sh --no-build # skip image builds (fast restart)
#   ./up-cluster.sh --down     # tear the whole cluster down
#   ./up-cluster.sh --status   # print health + URLs
#
# Each repo keeps its own secrets in its own gitignored .env — never here.
# ═══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

NETWORK="soma-stack-net"
ROOT="/Users/macbookpro201916i964gb1tb/Documents/GitHub"
AGENT_DIR="$ROOT/somaAgent01/infra/standalone"
BRAIN_DIR="$ROOT/somabrain/infra/standalone"
SFM_DIR="$ROOT/somafractalmemory/infra/standalone"

# Service DNS names on soma-stack-net (set by each stack's container_name)
BRAIN_URL="http://somabrain_standalone_app:30101"
SFM_URL="http://somafractalmemory-standalone-api:10101"

# Host ports published by each stack (agent 20xxx, brain 30xxx, sfm 10xxx)
UI_URL="http://localhost:20080"
API_URL="http://localhost:20020"
BRAIN_HOST_URL="http://localhost:30101"
SFM_HOST_URL="http://localhost:10101"

log()  { printf '\033[1;36m▸ %s\033[0m\n' "$*"; }
ok()   { printf '\033[1;32m✓ %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m! %s\033[0m\n' "$*"; }
die()  { printf '\033[1;31m✗ %s\033[0m\n' "$*" >&2; exit 1; }

require_env_file() {
  local f="$1" service="$2"
  [[ -f "$f" ]] || die "$service needs $f (copy the .env.example and fill it in)"
}

# Read one KEY=value from an env file without echoing the value. Used to hand a
# store's bearer token to the agent so all three stacks agree on one secret per
# store, with the secret never appearing in a committed file (INVARIANTS §6).
read_env_var() {
  local file="$1" key="$2"
  [[ -f "$file" ]] || return 1
  local line
  line="$(grep -E "^${key}=" "$file" | tail -n 1)" || return 1
  [[ -n "$line" ]] || return 1
  local val="${line#*=}"
  val="${val%$'\r'}"
  val="${val#\"}"; val="${val%\"}"
  val="${val#\'}"; val="${val%\'}"
  [[ -n "$val" ]] || return 1
  printf '%s' "$val"
}

# Export the store bearer tokens the agent needs. Prefers values already in the
# environment, falls back to each store's own .env.
export_store_tokens() {
  if [[ -z "${SOMA_API_TOKEN:-}" ]]; then
    SOMA_API_TOKEN="$(read_env_var "$SFM_DIR/.env" SOMA_API_TOKEN)" \
      || die "SOMA_API_TOKEN not set and not found in $SFM_DIR/.env"
  fi
  if [[ -z "${SOMABRAIN_MEMORY_HTTP_TOKEN:-}" ]]; then
    SOMABRAIN_MEMORY_HTTP_TOKEN="$(read_env_var "$BRAIN_DIR/.env" SOMABRAIN_MEMORY_HTTP_TOKEN)" \
      || die "SOMABRAIN_MEMORY_HTTP_TOKEN not set and not found in $BRAIN_DIR/.env"
  fi
  export SOMA_API_TOKEN SOMABRAIN_MEMORY_HTTP_TOKEN
  ok "store bearer tokens resolved (values not printed)"
}

wait_http() {
  local name="$1" url="$2" timeout="${3:-180}" waited=0
  log "waiting for $name ($url)"
  while (( waited < timeout )); do
    if curl -fsS -o /dev/null --max-time 3 "$url" 2>/dev/null; then
      ok "$name healthy after ${waited}s"
      return 0
    fi
    sleep 3; waited=$((waited + 3))
  done
  warn "$name not healthy after ${timeout}s — continuing, check: docker logs <container>"
  return 0
}

cmd_down() {
  log "tearing down the cluster (network $NETWORK last)"
  (cd "$AGENT_DIR" && docker compose -f docker-compose.yml -f docker-compose.shared-network.yml down --remove-orphans) || true
  (cd "$BRAIN_DIR" && docker compose -f docker-compose.yml -f docker-compose.shared-network.yml down --remove-orphans) || true
  (cd "$SFM_DIR"   && docker compose -f docker-compose.yml -f docker-compose.shared-network.yml down --remove-orphans) || true
  docker network rm "$NETWORK" 2>/dev/null && ok "network removed" || warn "network already gone"
  ok "cluster down"
}

cmd_status() {
  log "cluster status"
  docker ps --filter "network=$NETWORK" --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' || true
  echo
  for probe in "SomaAgent API|$API_URL/health" "SomaAgent WebUI|$UI_URL/" "SomaBrain|$BRAIN_HOST_URL/health" "SomaFractalMemory|$SFM_HOST_URL/healthz"; do
    name="${probe%%|*}"; url="${probe#*|}"
    if curl -fsS -o /dev/null --max-time 3 "$url" 2>/dev/null; then ok "$name  $url"
    else warn "$name  $url  (no response)"; fi
  done
}

cmd_up() {
  local build_flag="--build"
  [[ "${1:-}" == "--no-build" ]] && build_flag=""

  command -v docker >/dev/null || die "docker is not installed or not running"
  docker info >/dev/null 2>&1 || die "docker daemon is not running"

  require_env_file "$SFM_DIR/.env"   "SomaFractalMemory"
  require_env_file "$BRAIN_DIR/.env" "SomaBrain"
  require_env_file "$AGENT_DIR/.env" "SomaAgent01"
  export_store_tokens

  if docker network inspect "$NETWORK" >/dev/null 2>&1; then
    ok "network $NETWORK already exists"
  else
    log "creating external network $NETWORK"
    docker network create "$NETWORK" >/dev/null
    ok "network created"
  fi

  log "starting SomaFractalMemory (real: Postgres + Milvus + MinIO + Vault + OPA)"
  (cd "$SFM_DIR" && docker compose -f docker-compose.yml -f docker-compose.shared-network.yml \
    up -d --remove-orphans $build_flag)

  log "starting SomaBrain (real: Kafka + Postgres + Vault + OPA)"
  # Point brain's memory HTTP endpoint at the SFM service on the shared network
  (cd "$BRAIN_DIR" && SOMABRAIN_MEMORY_HTTP_ENDPOINT="$SFM_URL" \
    docker compose -f docker-compose.yml -f docker-compose.shared-network.yml \
    up -d --remove-orphans $build_flag)

  log "starting SomaAgent01 (API + WebUI + Keycloak), wired to both stores"
  (cd "$AGENT_DIR" && SOMABRAIN_URL="$BRAIN_URL" SOMAFRACTALMEMORY_URL="$SFM_URL" \
    docker compose -f docker-compose.yml -f docker-compose.shared-network.yml \
    up -d --remove-orphans $build_flag)

  wait_http "SomaFractalMemory" "$SFM_HOST_URL/healthz" 240
  wait_http "SomaBrain"         "$BRAIN_HOST_URL/health" 240
  wait_http "SomaAgent API"     "$API_URL/health"        240
  wait_http "SomaAgent WebUI"   "$UI_URL/"               120

  echo
  ok "SOMA CLUSTER IS UP"
  cat <<EOF

  ┌──────────────────────────────────────────────────────────────┐
  │  WebUI (test here)   $UI_URL
  │  Agent API           $API_URL          /health
  │  SomaBrain           $BRAIN_HOST_URL         /health
  │  SomaFractalMemory   $SFM_HOST_URL         /healthz
  ├──────────────────────────────────────────────────────────────┤
  │  network: $NETWORK
  │  brain  → memory: $SFM_URL
  │  agent  → brain:  $BRAIN_URL
  │  agent  → memory: $SFM_URL
  └──────────────────────────────────────────────────────────────┘

  Status:   ./up-cluster.sh --status
  Logs:     docker logs -f somaagent_standalone
  Tear down: ./up-cluster.sh --down

EOF
}

case "${1:-}" in
  --down)    cmd_down ;;
  --status)  cmd_status ;;
  --no-build) cmd_up --no-build ;;
  *)         cmd_up ;;
esac
