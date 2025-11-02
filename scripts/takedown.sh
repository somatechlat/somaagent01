#!/usr/bin/env bash
# scripts/takedown.sh
# Safely stop the somaagent01 compose stack and remove leftover containers that cause port conflicts.
# Usage:
#   ./scripts/takedown.sh         # stop compose stack and remove orphan containers
#   ./scripts/takedown.sh --dry   # show what would be removed without actually removing
#   ./scripts/takedown.sh --project <name>  # use custom compose project name

set -euo pipefail

DRY_RUN=0
PROJECT_NAME="somaagent01"
COMPOSE_FILE="infra/docker-compose.somaagent01.yaml"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry) DRY_RUN=1; shift ;;
    --project) PROJECT_NAME="$2"; shift 2 ;;
    --file) COMPOSE_FILE="$2"; shift 2 ;;
    -h|--help)
      sed -n '1,120p' "$0"
      exit 0
      ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

echo "Takedown script: project=$PROJECT_NAME compose-file=$COMPOSE_FILE dry_run=$DRY_RUN"

# 1) Try docker compose down for the given compose file/project
DC_CMD=(docker compose -f "$COMPOSE_FILE" --project-name "$PROJECT_NAME")

if [[ $DRY_RUN -eq 1 ]]; then
  echo "DRY RUN: would run: ${DC_CMD[*]} down --volumes --remove-orphans"
else
  echo "Running: ${DC_CMD[*]} down --volumes --remove-orphans"
  "${DC_CMD[@]}" down --volumes --remove-orphans || true
fi

# 2) Identify containers that have the same name prefix and remove them if they are leftovers
# We'll look for container names that start with the project name or the known somaAgent01_ prefix
MAP_PREFIXES=("${PROJECT_NAME}_" "somaAgent01_")

# List all containers that match prefixes
TO_REMOVE=()
while IFS= read -r cid; do
  [[ -z "$cid" ]] && continue
  # get container name
  name=$(docker ps -a --format '{{.ID}} {{.Names}}' | awk -v id="$cid" '$1==id {print $2}')
  TO_REMOVE+=("$cid:$name")
done < <(docker ps -a --format '{{.ID}}' | xargs -r -n1 -I{} bash -c 'n=$(docker ps -a --filter id={} --format "{{.Names}}" ); if [[ "$n" == ${PROJECT_NAME}_* || "$n" == somaAgent01_* ]]; then echo {}; fi')

if [[ ${#TO_REMOVE[@]} -eq 0 ]]; then
  echo "No leftover compose containers found matching prefixes."
else
  echo "Found leftover containers:"
  for pair in "${TO_REMOVE[@]}"; do
    cid=${pair%%:*}
    name=${pair#*:}
    echo "  $cid -> $name"
  done

  if [[ $DRY_RUN -eq 1 ]]; then
    echo "DRY RUN: would remove the above containers and their networks/volumes"
  else
    echo "Removing leftover containers..."
    for pair in "${TO_REMOVE[@]}"; do
      cid=${pair%%:*}
      name=${pair#*:}
      echo "Stopping and removing $name ($cid)"
      docker rm -f "$cid" || true
    done
  fi
fi

# 3) Cleanup named volumes used by the compose project (optional, only remove known volumes)
KNOWN_VOLUMES=("postgres_data" "kafka_data" "redis_data")
for v in "${KNOWN_VOLUMES[@]}"; do
  full="${PROJECT_NAME}_${v}"
  if docker volume ls --format '{{.Name}}' | grep -q "^${full}$"; then
    if [[ $DRY_RUN -eq 1 ]]; then
      echo "DRY RUN: would remove volume: $full"
    else
      echo "Removing volume: $full"
      docker volume rm "$full" || true
    fi
  fi
done

echo "Takedown complete."
