import json
import time
import uuid

from kafka import KafkaProducer


def produce_message():
    producer = KafkaProducer(
        bootstrap_servers=["kafka:9092"], value_serializer=lambda x: json.dumps(x).encode("utf-8")
    )

    session_id = f"e2e-mem-{uuid.uuid4()}"
    msg = {
        "type": "conversation.user_message",
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "tenant": "default",
        "content": "Please remember this fact: The Golden Eagle flies at midnight.",
        "role": "user",
        "created_at": time.time(),
        "metadata": {"source": "e2e_verification"},
    }

    topic = "conversation.inbound"
    print(f"Sending message to {topic}: {msg}")
    future = producer.send(topic, value=msg)
    result = future.get(timeout=10)
    print(f"Message sent to partition {result.partition} at offset {result.offset}")
    print(f"Session ID to check: {session_id}")


if __name__ == "__main__":
    produce_message()
