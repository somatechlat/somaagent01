#!/usr/bin/env bash
set -euo pipefail

# Build a slim image and bring up the CI compose, then run the smoke check.
# Usage: ./scripts/ci_build_and_up.sh

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

IMAGE_NAME=${IMAGE_NAME:-somaagent01:slim}

echo "Building slim image (${IMAGE_NAME})..."
docker build --build-arg INCLUDE_ML_DEPS=false -t "${IMAGE_NAME}" -f Dockerfile .

echo "Bringing up CI compose..."
docker network create somaagent01 || true
docker compose -f docker-compose.ci.yaml --profile core up -d kafka redis postgres opa
docker compose -f docker-compose.ci.yaml --profile dev up -d gateway

echo "Waiting 5s for services to settle..."
sleep 5

echo "Running smoke checks..."
./scripts/check_stack.sh || {
  echo "Smoke check failed. Dumping docker compose ps and logs for debugging..."
  docker compose -f docker-compose.ci.yaml ps
  docker compose -f docker-compose.ci.yaml logs --tail=200
  exit 1
}

echo "CI compose up and smoke checks passed."
