#!/usr/bin/env bash
set -euo pipefail
BS="${SA01_KAFKA_BOOTSTRAP_SERVERS:-kafka:9092}"

topics=(
  conversation.inbound:3
  conversation.outbound:3
  tool.requests:3
  tool.results:3
  memory.wal:3
  config_updates:1
)

MAX_RETRIES=12
SLEEP=5

function ensure_topic() {
  local name="$1"
  local parts="$2"
  echo "Ensuring topic: $name partitions=$parts"

  # Use the kafka-topics CLI available in the Confluent image
  kafka-topics \
    --bootstrap-server "$BS" \
    --create --if-not-exists \
    --topic "$name" \
    --partitions "$parts" \
    --replication-factor 1
}

for t in "${topics[@]}"; do
  name="${t%%:*}"
  parts="${t##*:}"

  attempt=0
  until ensure_topic "$name" "$parts"; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge "$MAX_RETRIES" ]; then
      echo "Failed to ensure topic $name after $MAX_RETRIES attempts" >&2
      exit 1
    fi
    echo "Retrying topic creation for $name after ${SLEEP}s (attempt $attempt/$MAX_RETRIES)"
    sleep "$SLEEP"
  done
done

echo "Kafka topics ensured"

