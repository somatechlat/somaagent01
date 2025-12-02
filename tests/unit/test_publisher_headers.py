import asyncio

import pytest

pytestmark = pytest.mark.asyncio


class DummyProducer:
    def __init__(self):
        self.sent = []

    async def start(self):
        return None

    async def send_and_wait(self, topic, message, headers=None):
        self.sent.append((topic, message, headers))

    async def stop(self):
        return None


class DummyKafkaBus:
    def __init__(self):
        from services.common.event_bus import KafkaEventBus

        self._producer = DummyProducer()
        # Reuse settings but bypass start logic
        self._bus = KafkaEventBus()
        self._bus._producer = self._producer  # inject dummy

    async def publish(self, topic, payload, headers=None):
        await self._bus.publish(topic, payload, headers=headers)

    @property
    def sent(self):
        return self._producer.sent


class DummyOutbox:
    async def enqueue(self, **kwargs):  # noqa: D401
        # Store headers for assertion
        self.last = kwargs
        return 1


async def test_durable_publisher_header_injection_success(monkeypatch):
    from services.common.publisher import DurablePublisher

    bus = DummyKafkaBus()
    outbox = DummyOutbox()
    pub = DurablePublisher(bus=bus._bus, outbox=outbox)  # pass underlying bus

    payload = {
        "event_id": "e123",
        "type": "assistant.final",
        "session_id": "s123",
        "persona_id": "p456",
        "version": "sa01-v1",
        "metadata": {"tenant": "tenantA"},
        "message": "Hello",
    }
    res = await pub.publish(
        "conversation.outbound",
        payload,
        session_id="s123",
        tenant="tenantA",
    )
    assert res["published"] is True
    assert bus.sent, "No messages sent"
    topic, msg_bytes, hdrs = bus.sent[0]
    assert topic == "conversation.outbound"
    # Headers list contains tuples; convert
    hdr_map = {k: v.decode("utf-8", errors="ignore") for k, v in hdrs}
    for key in ["tenant_id", "session_id", "persona_id", "event_type", "event_id", "schema"]:
        assert key in hdr_map, f"missing header {key}"
    # Trace headers optional but if present must have proper lengths
    if "trace_id" in hdr_map:
        assert len(hdr_map["trace_id"]) == 32

    from services.common.publisher import DurablePublisher

    class FailingBus:
        async def publish(self, topic, payload, headers=None):
            await asyncio.sleep(0)
            raise RuntimeError("broker down")

    outbox = DummyOutbox()
    failing_bus = FailingBus()
    pub = DurablePublisher(bus=failing_bus, outbox=outbox)
    payload = {
        "event_id": "e999",
        "type": "system.event",
        "session_id": "sX",
        "metadata": {"tenant": "tY"},
    }
    # Trigger publish on the failing bus to exercise fallback logic
    res = await pub.publish(
        "conversation.outbound",
        payload,
        session_id="sX",
        tenant="tY",
    )
    assert res["published"] is False and res["enqueued"] is True
    # Headers persisted to outbox
    hdrs = outbox.last.get("headers")
    assert hdrs.get("tenant_id") == "tY"
    assert hdrs.get("session_id") == "sX"
    assert hdrs.get("event_id") == "e999"
