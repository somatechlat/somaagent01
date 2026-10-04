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
    durable = max(src.find("durable"), src.find("OutboxMessage"))
    # Either the gateway itself owns pre-hop durability, or the caller records first.
    gw_src = inspect.getsource(mg.FanoutMemoryGateway.remember_text)
    pre_hop_in_gateway = "durable_accept_memory" in gw_src
    assert (durable != -1 and durable < hop) or pre_hop_in_gateway


def test_the_memory_wal_outbox_is_the_only_replay_authority():
    """One authority: the seam's outbox. No ORM queue, no second WAL writer."""
    co_src = inspect.getsource(co.V3ChatOrchestrator._remember_via_gateway)
    assert "PendingMemory" not in co_src
    assert "publish_degraded_memory" not in co_src
    gw_src = inspect.getsource(mg.FanoutMemoryGateway.remember_text)
    assert "durable_accept_memory" in gw_src


def test_publisher_has_a_local_durable_buffer():
    """DurablePublisher.publish must not raise into nowhere on a Kafka blip."""
    src = inspect.getsource(pub.DurablePublisher.publish)
    assert "OutboxMessage" in src or "outbox" in src.lower()
    # On failure it returns enqueued, it does not only raise.
    assert "enqueued" in src


def test_degraded_memory_queue_module_does_not_publish():
    """That module is status only; a queue writer there would be authority two."""
    src = inspect.getsource(dmq)
    assert "publish" not in src.split('"""')[-1].lower() or "does not publish" in src.lower()
    assert "def publish" not in src


# ---------------------------------------------------------------------------
# One degraded path for every memory write (the seam's outbox is THE entry).
# ---------------------------------------------------------------------------


def _read(rel: str) -> str:
    from pathlib import Path

    return (Path(__file__).resolve().parents[2] / rel).read_text(encoding="utf-8")


def test_api_router_does_not_own_a_second_degraded_queue():
    """create_memory must not call publish_degraded_memory — that is path two."""
    src = _read("admin/somabrain/api_router.py")
    assert "publish_degraded_memory" not in src, (
        "api_router still queues degraded memories outside the MemoryGateway outbox"
    )


def test_publish_degraded_memory_second_entry_point_is_gone():
    """There is one degraded-queue entry point; the direct-Kafka one is retired."""
    assert not hasattr(dmq, "publish_degraded_memory"), (
        "publish_degraded_memory is a second degraded path (Kafka-direct) — delete it"
    )


def test_every_memory_write_degrades_through_one_entry_point():
    """The gateway seam and the REST memory surface share the same outbox accept."""
    gw_src = inspect.getsource(mg.FanoutMemoryGateway.remember_text)
    api_src = _read("admin/somabrain/api_router.py")
    entry = "durable_accept_memory"
    assert entry in gw_src, "the gateway must accept writes through the shared entry"
    assert entry in api_src, "api_router must degrade through the same shared entry"


# ---------------------------------------------------------------------------
# PendingMemory was a second replay authority (OutboxMessage is THE one).
# ---------------------------------------------------------------------------


def test_pending_memory_second_replay_authority_is_gone():
    """Two replay authorities is split-brain; the ORM model must not survive."""
    from admin.core.models import zdl
    from admin.core import models as models_pkg

    assert not hasattr(zdl, "PendingMemory"), "zdl.PendingMemory is the second replay authority"
    assert not hasattr(models_pkg, "PendingMemory"), "PendingMemory still exported from admin.core.models"


def test_sync_memories_command_is_gone():
    """The command drove the orphan queue; a replay authority has no second driver."""
    from pathlib import Path

    cmd = (
        Path(__file__).resolve().parents[2]
        / "admin"
        / "core"
        / "management"
        / "commands"
        / "sync_memories.py"
    )
    assert not cmd.exists(), f"{cmd} still drives the deleted PendingMemory queue"


def test_a_migration_drops_the_pending_memory_table():
    """The table is dropped by a real migration, not left as an orphan."""
    import re
    from pathlib import Path

    mig_dir = Path(__file__).resolve().parents[2] / "admin" / "core" / "migrations"
    found = False
    for path in sorted(mig_dir.glob("*.py")):
        src = path.read_text(encoding="utf-8")
        if re.search(r'DeleteModel\([^)]*name=["\']PendingMemory["\']', src):
            found = True
            break
    assert found, "no migration drops the PendingMemory model/table"


def test_no_production_code_writes_pending_memory():
    """A leftover reference is how a second authority comes back."""
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    offenders: list[str] = []
    for rel in (
        "admin/core/chat_orchestrator.py",
        "services/common/memory_gateway.py",
        "admin/core/models/zdl.py",
        "admin/core/models/__init__.py",
    ):
        src = (root / rel).read_text(encoding="utf-8")
        if re.search(r"PendingMemory", src):
            offenders.append(rel)
    assert not offenders, f"PendingMemory still referenced: {offenders}"
