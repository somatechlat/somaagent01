"""Degradation doctrine — T-6 durable-before-hop, one replay authority, breaker.

VIBE: no mocks. These tests pin *source shape* and pure helpers so they run
without Kafka/SomaBrain. Behavioural replay against live services is the
integration suite's job.
"""

from __future__ import annotations

import inspect

from admin.core import chat_orchestrator as co
from services.common import degraded_memory_queue as dmq
from services.common import memory_gateway as mg
from services.common import publisher as pub


def test_no_double_queue_synthesizes_one_ack_not_two():
    """The gateway returns one somabrain ack; timeout must not invent two stores."""
    src = inspect.getsource(co.V3ChatOrchestrator._remember_via_gateway)
    assert "_MEMORY_STORES" not in src
    # The except path must queue once, not once per synthetic store.
    assert 'for store in _MEMORY_STORES' not in src


def test_memory_gateway_remember_text_is_circuit_broken():
    src = inspect.getsource(mg.FanoutMemoryGateway.remember_text)
    assert "circuit" in src.lower() or "breaker" in src.lower() or "_cb" in src


def test_memory_gateway_recall_is_circuit_broken():
    src = inspect.getsource(mg.FanoutMemoryGateway.recall)
    assert "circuit" in src.lower() or "breaker" in src.lower() or "_cb" in src


def test_durable_before_hop_records_before_the_network_call():
    """T-6: the durable record is written BEFORE remember_text's hop."""
    src = inspect.getsource(co.V3ChatOrchestrator._remember_via_gateway)
    # A durable accept must appear before the gateway call in the source.
    hop = src.find("remember_text")
    durable = max(
        src.find("PendingMemory"),
        src.find("publish_degraded_memory"),
        src.find("durable"),
        src.find("OutboxMessage"),
    )
    # Either the gateway itself owns pre-hop durability, or the caller records first.
    gw_src = inspect.getsource(mg.FanoutMemoryGateway.remember_text)
    pre_hop_in_gateway = (
        gw_src.find("PendingMemory") != -1
        or gw_src.find("publish_degraded_memory") != -1
        or gw_src.find("durable") != -1
    )
    assert (durable != -1 and durable < hop) or pre_hop_in_gateway


def test_one_replay_authority_kafka_wal_not_pending_memory_and_vice_versa():
    """Kafka WAL *or* PendingMemory+sync_memories — never both as writers."""
    co_src = inspect.getsource(co.V3ChatOrchestrator._remember_via_gateway)
    writes_pending = "PendingMemory.objects" in co_src or "PendingMemory(" in co_src
    writes_wal = "publish_degraded_memory" in co_src
    assert not (writes_pending and writes_wal), (
        "both Kafka WAL and PendingMemory are written for one failed memory"
    )


def test_publisher_has_a_local_durable_buffer():
    """DurablePublisher.publish must not raise into nowhere on a Kafka blip."""
    src = inspect.getsource(pub.DurablePublisher.publish)
    assert "OutboxMessage" in src or "outbox" in src.lower()
    # On failure it returns enqueued, it does not only raise.
    assert "enqueued" in src


def test_degraded_memory_queue_is_not_a_second_authority_when_wal_is_primary():
    """If chat_orchestrator uses Kafka WAL, PendingMemory must not also be written there."""
    src = inspect.getsource(co)
    if "publish_degraded_memory" in src:
        assert "PendingMemory.objects.create" not in src
        assert "PendingMemory(" not in src or "import" in src.split("PendingMemory")[0][-40:]
