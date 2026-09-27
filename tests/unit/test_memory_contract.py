"""Seam memory contract unit tests — PLAN-TRIAD-SEAMLESS.md §1 ("THE SEAM").

Proves the single-authority contract in services/common/memory_contract.py and
the fan-out gateway in services/common/memory_gateway.py:

  * make_coord() is deterministic: same (tenant, kind, ts, text) → same coord,
    and a different tenant (or text) yields a different coord.
  * embed_text() has fixed dimensionality: always get_mem_embed_dim()
    (settings.MEM_EMBED_DIM, default 768), unless an explicit dim is passed.
  * MemoryGateway fan-out: remember() returns exactly one ack per store; one
    store down yields ok=False with an error on that ack while the other store
    still acks ok=True; recall() merges both stores, dedupes by coord and
    ranks by score.

No network, no DB, no secrets: store legs are injected fakes that implement
the adapter surface (async remember/recall/forget/close). The gateway under
test is the real FanoutMemoryGateway.

Run:
    pytest tests/unit/test_memory_contract.py -v
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from config import settings
from services.common.memory_contract import (
    MemoryAck,
    MemoryGateway,
    MemoryHit,
    MemoryWrite,
    embed_text,
    get_mem_embed_dim,
    make_coord,
)
from services.common.memory_gateway import FanoutMemoryGateway


# ---------------------------------------------------------------------------
# Fake store legs — adapter-shaped, injected into the real gateway
# ---------------------------------------------------------------------------


class FakeStore:
    """Minimal store double implementing the adapter call surface."""

    def __init__(
        self,
        store_name: str,
        *,
        down: bool = False,
        hits: list[MemoryHit] | None = None,
    ) -> None:
        self.store_name = store_name
        self.down = down
        self.hits = list(hits or [])
        self.writes: list[MemoryWrite] = []

    async def remember(self, w: MemoryWrite) -> MemoryAck:
        if self.down:
            raise ConnectionError(f"{self.store_name} is down")
        self.writes.append(w)
        return MemoryAck(coord=w.coord, store=self.store_name, ok=True)

    async def recall(self, query: str, k: int, tenant_id: str) -> list[MemoryHit]:
        if self.down:
            raise ConnectionError(f"{self.store_name} is down")
        return list(self.hits)

    async def forget(self, coord: str, tenant_id: str) -> bool:
        return False

    async def close(self) -> None:
        return None


def _hit(coord: str, score: float, store: str, text: str = "memory") -> MemoryHit:
    return MemoryHit(
        text=text,
        coord=coord,
        score=score,
        store=store,  # type: ignore[arg-type]
        created_at="2026-01-01T00:00:00+00:00",
    )


def _write(text: str = "the quick brown fox", tenant: str = "tenant-a") -> MemoryWrite:
    ts = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
    return MemoryWrite(
        text=text,
        kind="episodic",
        tenant_id=tenant,
        coord=make_coord(tenant, "episodic", ts, text),
    )


# ---------------------------------------------------------------------------
# make_coord — one coordinate scheme, deterministic
# ---------------------------------------------------------------------------


class TestMakeCoord:
    """make_coord() is the single coordinate authority (PLAN §1)."""

    def test_make_coord_is_deterministic_for_same_inputs(self):
        """Same tenant/kind/ts/text always produces the identical coord string."""
        ts = datetime(2026, 3, 1, 12, 0, 0, tzinfo=UTC)
        first = make_coord("tenant-a", "episodic", ts, "hello seam")
        second = make_coord("tenant-a", "episodic", ts, "hello seam")
        assert first == second
        assert isinstance(first, str)
        assert first  # non-empty

    def test_make_coord_separates_tenants(self):
        """A different tenant_id produces a different coord for the same memory."""
        ts = datetime(2026, 3, 1, 12, 0, 0, tzinfo=UTC)
        coord_a = make_coord("tenant-a", "episodic", ts, "shared text")
        coord_b = make_coord("tenant-b", "episodic", ts, "shared text")
        assert coord_a != coord_b

    def test_make_coord_separates_text(self):
        """A different text produces a different coord within one tenant."""
        ts = datetime(2026, 3, 1, 12, 0, 0, tzinfo=UTC)
        coord_a = make_coord("tenant-a", "episodic", ts, "alpha")
        coord_b = make_coord("tenant-a", "episodic", ts, "beta")
        assert coord_a != coord_b


# ---------------------------------------------------------------------------
# embed_text — one vector space, fixed dimensionality
# ---------------------------------------------------------------------------


class TestEmbedText:
    """embed_text() produces one shared vector space of fixed size (PLAN §1)."""

    def test_embed_text_default_dimensionality(self):
        """Vector length equals get_mem_embed_dim(), sourced from settings."""
        dim = get_mem_embed_dim()
        vec = embed_text("seam embedding dimensionality")
        assert len(vec) == dim
        assert all(isinstance(x, float) for x in vec)

    def test_embed_text_honors_explicit_dim(self):
        """An explicit dim argument fixes the vector length."""
        assert len(embed_text("anything", dim=32)) == 32
        assert len(embed_text("anything", dim=8)) == 8

    def test_mem_embed_dim_comes_from_django_settings(self, monkeypatch):
        """settings.MEM_EMBED_DIM is the authority — not a hardcoded constant."""
        monkeypatch.setattr(settings, "MEM_EMBED_DIM", 64, raising=False)
        assert get_mem_embed_dim() == 64
        assert len(embed_text("settings-controlled dim")) == 64

    def test_mem_embed_dim_falls_back_to_env_without_settings(self, monkeypatch):
        """Env is the fallback only when the Django setting is ABSENT.

        Setting it to 0 is not absence — 0 is an invalid dim and the constant
        wins. Only a missing attribute lets the env layer speak.
        """
        monkeypatch.delattr(settings, "MEM_EMBED_DIM", raising=False)
        monkeypatch.setenv("MEM_EMBED_DIM", "32")
        assert get_mem_embed_dim() == 32


# ---------------------------------------------------------------------------
# MemoryGateway fan-out — one write path, one read path
# ---------------------------------------------------------------------------


class TestMemoryGatewayFanout:
    """FanoutMemoryGateway implements the MemoryGateway protocol semantics."""

    def test_gateway_satisfies_protocol(self):
        """FanoutMemoryGateway is a runtime MemoryGateway."""
        gateway = FanoutMemoryGateway(FakeStore("somabrain"), FakeStore("somafractalmemory"))
        assert isinstance(gateway, MemoryGateway)

    @pytest.mark.asyncio
    async def test_remember_returns_one_ack_per_store(self):
        """remember() yields exactly one MemoryAck per store, both ok."""
        brain = FakeStore("somabrain")
        sfm = FakeStore("somafractalmemory")
        gateway = FanoutMemoryGateway(brain, sfm)

        w = _write()
        acks = await gateway.remember(w)

        assert len(acks) == 2
        by_store = {a.store: a for a in acks}
        assert set(by_store) == {"somabrain", "somafractalmemory"}
        for ack in acks:
            assert ack.ok is True
            assert ack.error is None
            assert ack.coord == w.coord
        # One write path: both stores received the same write (coord + embedding).
        assert len(brain.writes) == 1 and len(sfm.writes) == 1
        assert brain.writes[0].coord == sfm.writes[0].coord == w.coord
        assert brain.writes[0].embedding is not None
        assert brain.writes[0].embedding == sfm.writes[0].embedding

    @pytest.mark.asyncio
    async def test_remember_isolates_one_store_down(self):
        """One store down → that ack ok=False with error; the other still ok=True."""
        brain = FakeStore("somabrain", down=True)
        sfm = FakeStore("somafractalmemory")
        gateway = FanoutMemoryGateway(brain, sfm)

        w = _write()
        acks = await gateway.remember(w)  # must not raise

        assert len(acks) == 2
        by_store = {a.store: a for a in acks}

        failed = by_store["somabrain"]
        assert failed.ok is False
        assert failed.error  # non-empty error carried on the failed ack
        assert failed.coord == w.coord

        healthy = by_store["somafractalmemory"]
        assert healthy.ok is True
        assert healthy.error is None

    @pytest.mark.asyncio
    async def test_recall_merges_and_dedupes_by_coord(self):
        """recall() merges both stores, dedupes by coord (keeps higher score), ranks desc."""
        shared = "1.0,0.0,0.0"
        brain = FakeStore(
            "somabrain",
            hits=[
                _hit(shared, 0.5, "somabrain", text="from-brain"),
                _hit("2.0,0.0,0.0", 0.4, "somabrain", text="brain-only"),
            ],
        )
        sfm = FakeStore(
            "somafractalmemory",
            hits=[
                _hit(shared, 0.9, "somafractalmemory", text="from-sfm"),
                _hit("3.0,0.0,0.0", 0.8, "somafractalmemory", text="sfm-only"),
            ],
        )
        gateway = FanoutMemoryGateway(brain, sfm)

        hits = await gateway.recall("query", k=10, tenant_id="tenant-a")

        coords = [h.coord for h in hits]
        assert len(coords) == len(set(coords)) == 3  # deduped by coord
        # The duplicated coord keeps the higher score (0.9) and ranks first.
        assert coords[0] == shared
        assert hits[0].score == 0.9
        assert [h.score for h in hits] == sorted((h.score for h in hits), reverse=True)
        assert {h.coord for h in hits} == {shared, "2.0,0.0,0.0", "3.0,0.0,0.0"}
