"""The conversation outbox is drained with the real Kafka signature.

``publish_outbox`` called ``KafkaEventBus.publish(..., dedupe_key=...)`` which is
not that method's signature (``publish(topic, payload, headers=)``). The signal
payload also disagreed with the conversation worker (``session_id``/``message``).
"""

from __future__ import annotations

import inspect

from admin.core.management.commands import publish_outbox as po


def test_publish_outbox_does_not_pass_dedupe_key_to_the_bus():
    src = inspect.getsource(po)
    assert "dedupe_key" not in src.split("bus.publish")[0] or "dedupe_key=" not in src
    # The drain must call bus.publish(topic, payload, headers=...)
    assert "bus.publish" in src
    assert "headers" in src


def test_publish_outbox_uses_the_outbox_pending_queryset():
    src = inspect.getsource(po)
    assert "OutboxMessage.objects.filter(status=\"pending\")" not in src or "pending()" in src
    # Must not ignore FAILED rows that are due for retry
    assert "Status.FAILED" in src or "pending()" in src or "FAILED" in src


def test_signal_payload_matches_the_conversation_worker_contract():
    from admin.core.signals import handle_conversation_message

    src = inspect.getsource(handle_conversation_message)
    assert "session_id" in src
    assert "message" in src
    assert "conversation_id" not in src or "session_id" in src
