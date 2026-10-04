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

# Service DNS names on soma-stack-net. The brain is addressed by its RFC 1035
# alias `somabrain` (an underscore name is rejected by Django host_validation_re
# as HTTP_HOST before any route runs). REQUIRED — a default is a hardcoded value.
BRAIN_URL="${SOMABRAIN_URL:?set SOMABRAIN_URL to the brain service URL on soma-stack-net}"
SFM_URL="${SOMAFRACTALMEMORY_URL:?set SOMAFRACTALMEMORY_URL to the SFM service URL on soma-stack-net}"

# Host-bound probe URLs (operator status only). REQUIRED — no localhost default.
UI_URL="${SA01_WEBUI_HOST_URL:?set SA01_WEBUI_HOST_URL}"
API_URL="${SA01_API_HOST_URL:?set SA01_API_HOST_URL}"
BRAIN_HOST_URL="${SOMABRAIN_HOST_URL:?set SOMABRAIN_HOST_URL}"
SFM_HOST_URL="${SOMAFRACTALMEMORY_HOST_URL:?set SOMAFRACTALMEMORY_HOST_URL}"

log()  { printf '\033[1;36m▸ %s\033[0m\n' "$*"; }
ok()   { printf '\033[1;32m✓ %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m! %s\033[0m\n' "$*"; }
die()  { printf '\033[1;31m✗ %s\033[0m\n' "$*" >&2; exit 1; }

require_env_file() {
  local f="$1" service="$2"
  [[ -f "$f" ]] || die "$service needs $f (copy the .env.example and fill it in)"
}

# Store bearer tokens (somabrain_memory_http_token, soma_api_token) are NOT
# read from .env and NOT exported into the compose environment (Rule 164). They
# live in Vault at secret/agent/credentials/, seeded once from the agent's
# t=0 material by init_vault.py. A token in ENV is visible in `ps`, in
# /proc/*/environ and in every crash dump — exporting one to "share" it between
# stacks is exactly the two-independent-values failure this design forbids.

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
