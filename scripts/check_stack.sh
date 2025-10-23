#!/usr/bin/env bash
#set -euo pipefail

# Simple smoke-check for core services: gateway, postgres, redis, kafka
# Usage: ./scripts/check_stack.sh [gateway_port] [postgres_port] [redis_port] [kafka_port]

GATEWAY_PORT=${1:-8010}
POSTGRES_PORT=${2:-20002}
REDIS_PORT=${3:-20001}
KAFKA_PORT=${4:-20000}

OK=0

echo "Checking gateway at http://localhost:${GATEWAY_PORT}/health"
if curl -fsS "http://localhost:${GATEWAY_PORT}/health" >/dev/null 2>&1; then
  echo "  gateway: OK"
else
  echo "  gateway: FAIL"
  OK=1
fi

echo "Checking Postgres at localhost:${POSTGRES_PORT}"
if pg_isready -h localhost -p "${POSTGRES_PORT}" -U soma >/dev/null 2>&1; then
  echo "  postgres: OK"
else
  echo "  postgres: FAIL"
  OK=1
fi

echo "Checking Redis at localhost:${REDIS_PORT}"
if redis-cli -h localhost -p "${REDIS_PORT}" ping >/dev/null 2>&1; then
  echo "  redis: OK"
else
  echo "  redis: FAIL"
  OK=1
fi

echo "Checking Kafka TCP at localhost:${KAFKA_PORT}"
if timeout 1 bash -c "</dev/tcp/localhost/${KAFKA_PORT}" >/dev/null 2>&1; then
  echo "  kafka: OK"
else
  echo "  kafka: FAIL"
  OK=1
fi

exit ${OK}
