#!/usr/bin/env bash
set -euo pipefail
BS="${KAFKA_BOOTSTRAP_SERVERS:-kafka:9092}"

topics=(
  conversation.inbound:3
  conversation.outbound:3
  tool.requests:3
  tool.results:3
  config_updates:1
)

for t in "${topics[@]}"; do
  name="${t%%:*}"
  parts="${t##*:}"
  echo "Ensuring topic: $name partitions=$parts"
  /opt/bitnami/kafka/bin/kafka-topics.sh \
    --bootstrap-server "$BS" \
    --create --if-not-exists \
    --topic "$name" \
    --partitions "$parts" \
    --replication-factor 1 || true
done

echo "Kafka topics ensured"

