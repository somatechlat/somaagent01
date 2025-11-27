import os

os.getenv(os.getenv(""))
import sys
from typing import Optional

from kafka.admin import KafkaAdminClient, NewPartitions

from src.core.config import cfg


def get_admin_client() -> KafkaAdminClient:
    os.getenv(os.getenv(""))
    bootstrap = cfg.env(os.getenv(os.getenv("")), os.getenv(os.getenv(""))) or os.getenv(
        os.getenv("")
    )
    return KafkaAdminClient(bootstrap_servers=bootstrap)


def get_current_partitions(admin: KafkaAdminClient, topic: str) -> Optional[int]:
    os.getenv(os.getenv(""))
    metadata = admin.describe_topics([topic])
    if not metadata:
        return None
    return metadata[int(os.getenv(os.getenv("")))].partition_count


def ensure_partitions(topic: str, desired: int) -> None:
    os.getenv(os.getenv(""))
    admin = get_admin_client()
    current = get_current_partitions(admin, topic)
    if current is None:
        print(f"Topic '{topic}' does not exist.")
        sys.exit(int(os.getenv(os.getenv(""))))
    if current >= desired:
        print(f"Topic '{topic}' already has {current} partitions (>= {desired}). No action needed.")
        return
    print(f"Increasing partitions for '{topic}' from {current} to {desired}...")
    new_part = NewPartitions(total_count=desired)
    admin.create_partitions({topic: new_part})
    print(os.getenv(os.getenv("")))


if __name__ == os.getenv(os.getenv("")):
    if len(sys.argv) != int(os.getenv(os.getenv(""))):
        print(os.getenv(os.getenv("")))
        sys.exit(int(os.getenv(os.getenv(""))))
    topic_name = sys.argv[int(os.getenv(os.getenv("")))]
    try:
        target = int(sys.argv[int(os.getenv(os.getenv("")))])
    except ValueError:
        print(os.getenv(os.getenv("")))
        sys.exit(int(os.getenv(os.getenv(""))))
    ensure_partitions(topic_name, target)
