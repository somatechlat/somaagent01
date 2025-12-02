"""Kafka Partition Scaler Utility.

This script provides a command‑line interface to ensure that a given Kafka
topic has at least the desired number of partitions. It uses ``kafka-python``
`KafkaAdminClient` to query the current partition count and, if necessary,
creates additional partitions.

Typical usage::

    python kafka_partition_scaler.py my-topic 12

If the topic already has 12 or more partitions the script exits silently.
"""

import sys
from typing import Optional

from kafka.admin import KafkaAdminClient, NewPartitions

from services.common import env


def get_admin_client() -> KafkaAdminClient:
    """Create and return a ``KafkaAdminClient``.

    The bootstrap servers are taken from the ``SA01_KAFKA_BOOTSTRAP_SERVERS``
    environment variable, defaulting to ``localhost:9092``.
    """
    bootstrap = env.get("SA01_KAFKA_BOOTSTRAP_SERVERS", "localhost:9092") or "localhost:9092"
    return KafkaAdminClient(bootstrap_servers=bootstrap)


def get_current_partitions(admin: KafkaAdminClient, topic: str) -> Optional[int]:
    """Return the current partition count for ``topic`` or ``None`` if it does not exist.

    Parameters
    ----------
    admin: KafkaAdminClient
        The admin client instance.
    topic: str
        Name of the Kafka topic.
    """
    metadata = admin.describe_topics([topic])
    if not metadata:
        return None
    return metadata[0].partition_count


def ensure_partitions(topic: str, desired: int) -> None:
    """Ensure ``topic`` has at least ``desired`` partitions.

    If the topic does not exist the function aborts with an error message.
    If the current number of partitions is greater than or equal to ``desired``
    the function prints a short informational message and returns.
    Otherwise it creates the missing partitions using ``admin.create_partitions``.
    """
    admin = get_admin_client()
    current = get_current_partitions(admin, topic)
    if current is None:
        print(f"Topic '{topic}' does not exist.")
        sys.exit(1)
    if current >= desired:
        print(f"Topic '{topic}' already has {current} partitions (>= {desired}). No action needed.")
        return
    print(f"Increasing partitions for '{topic}' from {current} to {desired}...")
    new_part = NewPartitions(total_count=desired)
    admin.create_partitions({topic: new_part})
    print("Partitions increased successfully.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python kafka_partition_scaler.py <topic> <desired_partitions>")
        sys.exit(1)
    topic_name = sys.argv[1]
    try:
        target = int(sys.argv[2])
    except ValueError:
        print("desired_partitions must be an integer")
        sys.exit(1)
    ensure_partitions(topic_name, target)
