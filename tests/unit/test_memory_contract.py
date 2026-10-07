"""Seam memory contract — the genuinely pure claims (TRIAD R-04 step 3).

``make_coord`` is the one coordinate authority and ``embed_text`` the one
vector-space authority of the seam (``SOMA-PM-PLAN-TRIAD-001`` §1). Both are
pure functions: no network, no DB, no secrets, no store leg. A unit test is the
right home for them precisely because nothing has to be substituted to call
them.

The gateway's behavioural claims — one write lane, score ranking, failure
isolation — are NOT here. They need a real SomaBrain, and a stand-in store
would only prove that the stand-in agrees with its author. Those live in
``tests/integration/test_memory_seam.py`` against live ``:30101``, skipping
when unreachable (R-04 step 2).

There is no ``FakeStore`` in this file and there must never be one again.
``FanoutMemoryGateway.__init__`` is typed for ``SomaBrainAdapter``; passing a
duck-typed stand-in into that slot is the substitution R-04 exists to remove.

Run:
    pytest tests/unit/test_memory_contract.py -v
"""

from __future__ import annotations

import inspect
from datetime import datetime, UTC

from config import settings
from services.common.memory_contract import (
    DEFAULT_MEM_EMBED_DIM,
    coord_from_key_material,
    coord_key_material,
    embed_text,
    get_mem_embed_dim,
    make_coord,
    MemoryGateway,
)
from services.common.memory_gateway import FanoutMemoryGateway

TS = datetime(2026, 3, 1, 12, 0, 0, tzinfo=UTC)


# ---------------------------------------------------------------------------
# make_coord — one coordinate scheme, deterministic
# ---------------------------------------------------------------------------


class TestMakeCoord:
    """make_coord() is the single coordinate authority (PLAN §1)."""

    def test_make_coord_is_deterministic_for_same_inputs(self):
        """Same tenant/kind/ts/text always produces the identical coord string."""
        first = make_coord("tenant-a", "episodic", TS, "hello seam")
        second = make_coord("tenant-a", "episodic", TS, "hello seam")
        assert first == second
        assert isinstance(first, str)
        assert first  # non-empty

    def test_make_coord_separates_tenants(self):
        """A different tenant_id produces a different coord for the same memory.

        Tenant isolation is a security boundary, not a nicety: two tenants
        storing the same text must never converge on one coordinate.
        """
        coord_a = make_coord("tenant-a", "episodic", TS, "shared text")
        coord_b = make_coord("tenant-b", "episodic", TS, "shared text")
        assert coord_a != coord_b

    def test_make_coord_separates_text(self):
        """A different text produces a different coord within one tenant."""
        coord_a = make_coord("tenant-a", "episodic", TS, "alpha")
        coord_b = make_coord("tenant-a", "episodic", TS, "beta")
        assert coord_a != coord_b

    def test_make_coord_separates_kind_and_time(self):
        """Kind and timestamp are part of the identity, not decoration."""
        base = make_coord("tenant-a", "episodic", TS, "same text")
        other_kind = make_coord("tenant-a", "semantic", TS, "same text")
        other_time = make_coord(
            "tenant-a", "episodic", datetime(2026, 3, 1, 12, 0, 1, tzinfo=UTC), "same text"
        )
        assert base != other_kind
        assert base != other_time

    def test_make_coord_agrees_with_the_key_material_path(self):
        """The two derivations must be the same derivation.

        A caller that keeps the key material (so SomaBrain places the record at
        this very point) recomputes the coord via ``coord_from_key_material``.
        If the two ever disagree the record lands somewhere no reader looks.
        """
        material = coord_key_material("tenant-a", "episodic", TS, "hello seam")
        assert make_coord("tenant-a", "episodic", TS, "hello seam") == coord_from_key_material(
            material
        )

    def test_coord_is_a_parseable_point_in_the_unit_cube(self):
        """The coord is SomaBrain/SFM's comma-separated float triple, not an opaque id.

        ``somafractalmemory`` parses this string back into a float tuple. A
        string that will not parse is a write that cannot be read.
        """
        parts = make_coord("tenant-a", "episodic", TS, "hello seam").split(",")
        assert len(parts) == 3
        for part in parts:
            value = float(part)
            assert -1.0 <= value <= 1.0


# ---------------------------------------------------------------------------
# embed_text — one vector space, fixed dimensionality
# ---------------------------------------------------------------------------


class TestEmbedText:
    """embed_text() produces one shared vector space of fixed size (PLAN §1)."""

    def test_embed_text_default_dimensionality(self):
        """Vector length equals get_mem_embed_dim() — the configured dim."""
        dim = get_mem_embed_dim()
        vec = embed_text("seam embedding dimensionality")
        assert len(vec) == dim
        assert all(isinstance(x, float) for x in vec)

    def test_embed_text_honors_explicit_dim(self):
        """An explicit dim argument fixes the vector length."""
        assert len(embed_text("anything", dim=32)) == 32
        assert len(embed_text("anything", dim=8)) == 8

    def test_embed_text_is_deterministic(self):
        """Same text, same dimension, same vector. Both stores must agree."""
        assert embed_text("stable text") == embed_text("stable text")

    def test_embed_text_separates_different_text(self):
        """Different text must not collapse to one vector."""
        assert embed_text("alpha content") != embed_text("beta content")

    def test_embed_text_is_unit_length(self):
        """L2-normalised, so scores are comparable across stores."""
        vec = embed_text("normalise me")
        norm = sum(x * x for x in vec) ** 0.5
        assert abs(norm - 1.0) < 1e-9

    def test_mem_embed_dim_is_a_sane_dimension(self):
        """Whatever the deployment configured, it is a usable width."""
        dim = get_mem_embed_dim()
        assert isinstance(dim, int)
        assert dim > 0
        assert len(embed_text("check width")) == dim


# ---------------------------------------------------------------------------
# Settings resolution — the authority order, without substituting anything
# ---------------------------------------------------------------------------


class TestEmbedDimResolution:
    """Django settings is the authority; env is only a fallback layer.

    These claims need no ``monkeypatch.setattr``. Where the Django setting is
    present it is simply *used as is* and the environment is pointed somewhere
    else — which proves the setting outranks the environment. Where it is
    absent, removing it (``delattr``) and setting the environment proves the
    fallback speaks. Substituting a stand-in settings object would prove
    nothing about either layer.
    """

    def test_the_django_setting_outranks_the_environment(self, monkeypatch):
        configured = getattr(settings, "MEM_EMBED_DIM", None)
        if configured is None:
            # Nothing to outrank. The fallback claim below covers this shape.
            return
        # Point the env layer somewhere disagreeable. The Django setting must
        # still win — that is the whole of the authority order.
        monkeypatch.setenv("MEM_EMBED_DIM", "8")
        assert get_mem_embed_dim() == int(configured)

    def test_the_environment_is_the_fallback_when_the_setting_is_absent(self, monkeypatch):
        monkeypatch.delattr(settings, "MEM_EMBED_DIM", raising=False)
        monkeypatch.setenv("MEM_EMBED_DIM", "32")
        assert get_mem_embed_dim() == 32

    def test_an_unset_dimension_falls_back_to_the_documented_default(self, monkeypatch):
        """No setting, no env → the documented default, not a guess of 0.

        ``DEFAULT_MEM_EMBED_DIM`` is 768 because that is SFM's
        ``SOMA_VECTOR_DIM``. A zero or negative width would produce an empty
        vector and silently no-op every write.
        """
        monkeypatch.delattr(settings, "MEM_EMBED_DIM", raising=False)
        monkeypatch.delenv("MEM_EMBED_DIM", raising=False)
        assert get_mem_embed_dim() == DEFAULT_MEM_EMBED_DIM
        assert get_mem_embed_dim() == 768

    def test_a_zero_dimension_is_not_accepted_as_configured(self, monkeypatch):
        """0 is an invalid width, not an absence — the default must win.

        ``get_mem_embed_dim`` treats a non-positive value as unusable rather
        than honouring it and returning an empty vector.
        """
        monkeypatch.delattr(settings, "MEM_EMBED_DIM", raising=False)
        monkeypatch.setenv("MEM_EMBED_DIM", "0")
        assert get_mem_embed_dim() == DEFAULT_MEM_EMBED_DIM


# ---------------------------------------------------------------------------
# Gateway shape — structural, no store leg involved
# ---------------------------------------------------------------------------


class TestGatewayShape:
    """The one-write-lane contract is in the signature, not a runtime check."""

    def test_the_gateway_takes_exactly_one_store(self):
        """Brain-only is structural: there is no second store parameter at all.

        Asserting the shape is the honest claim. Constructing the gateway with
        two objects and expecting ``TypeError`` would only be testing Python's
        arity check — which passes for any callable with one parameter and
        proves nothing about the seam. There is deliberately no ``sfm``
        parameter to weaken.
        """
        params = inspect.signature(FanoutMemoryGateway.__init__).parameters
        positional = [
            p.name
            for name, p in params.items()
            if name != "self"
            and p.kind
            in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )
        ]
        assert positional == ["brain"]

    def test_no_keyword_can_smuggle_a_second_store(self):
        """Var-keyword catch-alls would let a caller pass ``sfm=...`` silently."""
        params = inspect.signature(FanoutMemoryGateway.__init__).parameters
        assert not any(
            p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values()
        ), "a **kwargs would accept a second store and ignore it"
        assert "sfm" not in params
        assert "stores" not in params

    def test_the_gateway_declares_the_protocol(self):
        """FanoutMemoryGateway is a runtime MemoryGateway — no store needed.

        ``MemoryGateway`` is ``@runtime_checkable``, so this is a genuine
        structural check of the real class, not of a double.
        """
        assert issubclass(FanoutMemoryGateway, MemoryGateway)


# ---------------------------------------------------------------------------
# MemoryDurability — one vocabulary, matching the brain's StrEnum (AP-06)
# ---------------------------------------------------------------------------


class TestMemoryDurability:
    """The durability vocabulary is shared verbatim with the brain (AP-06)."""

    def test_durability_has_exactly_the_brain_vocabulary(self):
        from services.common.memory_contract import MemoryDurability

        values = {d.value for d in MemoryDurability}
        assert values == {"persisted_ltm", "durable_outbox", "degraded_journal"}

    def test_durability_is_strenum(self):
        from enum import StrEnum

        from services.common.memory_contract import MemoryDurability

        assert issubclass(MemoryDurability, StrEnum)

    def test_durability_members_are_the_brain_names(self):
        from services.common.memory_contract import MemoryDurability

        assert MemoryDurability.PERSISTED_LTM == "persisted_ltm"
        assert MemoryDurability.DURABLE_OUTBOX == "durable_outbox"
        assert MemoryDurability.DEGRADED_JOURNAL == "degraded_journal"


class TestMemoryAckDurability:
    """MemoryAck carries durability — ok alone is never enough (T-6)."""

    def test_ack_has_durability_field(self):
        from services.common.memory_contract import MemoryAck, MemoryDurability

        ack = MemoryAck(
            coord="0.1,0.2,0.3",
            store="somabrain",
            ok=True,
            durability=MemoryDurability.DURABLE_OUTBOX,
            outbox_event_id=42,
        )
        assert ack.durability == MemoryDurability.DURABLE_OUTBOX
        assert ack.outbox_event_id == 42

    def test_ack_durability_defaults_to_none(self):
        from services.common.memory_contract import MemoryAck

        ack = MemoryAck(coord="0.1,0.2,0.3", store="somabrain", ok=False)
        assert ack.durability is None
        assert ack.outbox_event_id is None

    def test_ack_durability_accepts_all_three_states(self):
        from services.common.memory_contract import MemoryAck, MemoryDurability

        for state in MemoryDurability:
            ack = MemoryAck(
                coord="0.1,0.2,0.3", store="somabrain", ok=True, durability=state
            )
            assert ack.durability is state


# ---------------------------------------------------------------------------
# Adapter reads durability — fail closed when the brain omits it (C1-6)
# ---------------------------------------------------------------------------


class TestAdapterDurabilityMapping:
    """SomaBrainAdapter.remember reads durability; omitted field fails closed.

    Source-text contract checks: the adapter must map the brain's durability
    field into MemoryAck and must NOT silently claim ok when it is absent.
    """

    @staticmethod
    def _adapter_src() -> str:
        from pathlib import Path

        return (
            Path(__file__).resolve().parents[2]
            / "services/common/adapters/somabrain_adapter.py"
        ).read_text(encoding="utf-8")

    def test_adapter_reads_durability_from_response(self):
        src = self._adapter_src()
        assert 'data.get("durability")' in src
        assert "MemoryDurability" in src

    def test_adapter_fails_closed_when_durability_missing(self):
        src = self._adapter_src()
        # The None branch must set ok=False, never ok=True
        none_branch = src[src.find("if raw_durability is None:") :]
        none_branch = none_branch[: none_branch.find("durability = MemoryDurability")]
        assert "ok=False" in none_branch
        assert "ok=True" not in none_branch

    def test_adapter_maps_outbox_event_id(self):
        src = self._adapter_src()
        assert 'data.get("outbox_event_id")' in src
        assert "outbox_event_id=" in src
