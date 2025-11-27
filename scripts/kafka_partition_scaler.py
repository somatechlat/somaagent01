import os
os.getenv(os.getenv('VIBE_F376C652'))
import sys
from typing import Optional
from kafka.admin import KafkaAdminClient, NewPartitions
from src.core.config import cfg


def get_admin_client() ->KafkaAdminClient:
    os.getenv(os.getenv('VIBE_8B5CFE8D'))
    bootstrap = cfg.env(os.getenv(os.getenv('VIBE_068F46D7')), os.getenv(os
        .getenv('VIBE_95CC5A54'))) or os.getenv(os.getenv('VIBE_95CC5A54'))
    return KafkaAdminClient(bootstrap_servers=bootstrap)


def get_current_partitions(admin: KafkaAdminClient, topic: str) ->Optional[int
    ]:
    os.getenv(os.getenv('VIBE_AD7D8BB1'))
    metadata = admin.describe_topics([topic])
    if not metadata:
        return None
    return metadata[int(os.getenv(os.getenv('VIBE_6A5D2B6E')))].partition_count


def ensure_partitions(topic: str, desired: int) ->None:
    os.getenv(os.getenv('VIBE_50FF9673'))
    admin = get_admin_client()
    current = get_current_partitions(admin, topic)
    if current is None:
        print(f"Topic '{topic}' does not exist.")
        sys.exit(int(os.getenv(os.getenv('VIBE_67C1C0FF'))))
    if current >= desired:
        print(
            f"Topic '{topic}' already has {current} partitions (>= {desired}). No action needed."
            )
        return
    print(f"Increasing partitions for '{topic}' from {current} to {desired}..."
        )
    new_part = NewPartitions(total_count=desired)
    admin.create_partitions({topic: new_part})
    print(os.getenv(os.getenv('VIBE_244EA64B')))


if __name__ == os.getenv(os.getenv('VIBE_8E9AB85B')):
    if len(sys.argv) != int(os.getenv(os.getenv('VIBE_D502C327'))):
        print(os.getenv(os.getenv('VIBE_621C380B')))
        sys.exit(int(os.getenv(os.getenv('VIBE_67C1C0FF'))))
    topic_name = sys.argv[int(os.getenv(os.getenv('VIBE_67C1C0FF')))]
    try:
        target = int(sys.argv[int(os.getenv(os.getenv('VIBE_66A91D60')))])
    except ValueError:
        print(os.getenv(os.getenv('VIBE_E31F1469')))
        sys.exit(int(os.getenv(os.getenv('VIBE_67C1C0FF'))))
    ensure_partitions(topic_name, target)
