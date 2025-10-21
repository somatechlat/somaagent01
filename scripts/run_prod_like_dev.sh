#!/usr/bin/env bash
# Run the stack in a prod-like configuration for local development.
# Starts services detached and persists logs under ./logs/<service>.log using nohup.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

COMPOSE_FILES=( -f docker-compose.yaml -f docker-compose.prod-local.yaml )

echo "Ensuring logs directory exists..."
mkdir -p logs

echo "Bringing up core infra and services (detached)..."
docker compose "${COMPOSE_FILES[@]}" up -d kafka postgres redis opa || true
docker compose "${COMPOSE_FILES[@]}" up -d --build gateway conversation-worker tool-executor agent-ui memory-service || true

echo "Starting background log followers (nohup)"
for svc in gateway conversation-worker tool-executor agent-ui memory-service kafka redis postgres opa; do
  logfile="$ROOT_DIR/logs/${svc}.log"
  # If a follower is already running, skip
  if pgrep -f "docker compose.*logs.*${svc}" >/dev/null 2>&1; then
    echo "Log follower already running for ${svc}, skipping"
    continue
  fi
  nohup sh -c "docker compose ${COMPOSE_FILES[@]} logs -f ${svc} >> \"${logfile}\" 2>&1" >/dev/null 2>&1 &
  echo "Tailing logs for ${svc} -> ${logfile}"
done

echo "Ensure default agent profile exists..."
./scripts/ensure_agent_profile.sh

echo "All services started (detached). Logs are being written to ./logs/."
echo "To follow logs interactively run: docker compose ${COMPOSE_FILES[@]} logs -f gateway conversation-worker"
