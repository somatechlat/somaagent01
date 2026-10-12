"""T-2 golden-vector parity — one coordinate hash, frozen outputs.

Guards the cross-repo shared module ``soma_memory_contract`` (W3 of
SOMA-A0-PARITY-001). Every consumer must agree with these frozen vectors;
any drift re-keys every stored memory and is a hard failure.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.no_django

from services.common.memory_contract import (
    coord_from_key_material,
    coord_key_material,
    make_coord,
)
from soma_memory_contract import _stable_coord, make_coord as shared_make_coord

# Frozen outputs of blake2b digest_size=12 → [-1,1]^3. Do not regenerate to
# "fix" a failure — a mismatch means the hash math changed and must be reverted.
STABLE_COORD_GOLDEN = [
    (
        "real::tenant-a|episodic|2026-10-03T00:00:00Z|hello seam",
        0.24714936409145594,
        0.09493384370580316,
        -0.9746199166402221,
    ),
    (
        "real::tenant-b|semantic|2026-10-03T00:01:00Z|shared text",
        -0.6081309374421835,
        -0.8184258714318275,
        0.9730786420404911,
    ),
    ("", 0.44439287623390555, 0.3440746674314141, -0.9154480644501746),
    ("x", -0.6184049095027149, -0.82011533761397, -0.012718055862933397),
    (
        "idempotency:mem:0.41,0.42,0.43",
        -0.9963827859610319,
        0.32875058613717556,
        0.37231292948126793,
    ),
    (
        "real::a|b|c|d",
        0.568278412334621,
        -0.906532492954284,
        0.34637327026575804,
    ),
]

MAKE_COORD_GOLDEN = [
    (
        ("tenant-a", "episodic", "2026-10-03T00:00:00Z", "hello seam"),
        "0.24714936409145594,0.09493384370580316,-0.9746199166402221",
    ),
    (
        ("tenant-b", "semantic", "2026-10-03T00:01:00Z", "shared text"),
        "-0.6081309374421835,-0.8184258714318275,0.9730786420404911",
    ),
    (
        ("tenant-a", "episodic", "2026-10-03T00:00:00Z", "different"),
        "0.917473510839045,-0.24300087103620172,0.5297011323273182",
    ),
    (
        ("t", "belief", "2026-01-01T00:00:00+00:00", "x"),
        "-0.2778128404170275,0.15481597185134888,-0.5356837827712297",
    ),
]

# 32-seed cross-repo vector (W3 exit criterion).
SEEDS_32 = [
    (f"tenant{i}", "episodic", f"2026-10-03T00:{i:02d}:00Z", f"text {i}")
    for i in range(32)
]


class TestGoldenVectors:
    """Frozen hash outputs — the contract cannot drift."""

    @pytest.mark.parametrize(
        "seed,x,y,z", STABLE_COORD_GOLDEN, ids=[s for s, *_ in STABLE_COORD_GOLDEN]
    )
    def test_stable_coord_matches_golden(self, seed, x, y, z):
        assert _stable_coord(seed) == (x, y, z)

    @pytest.mark.parametrize(
        "args,expected", MAKE_COORD_GOLDEN, ids=[str(a) for a, _ in MAKE_COORD_GOLDEN]
    )
    def test_make_coord_matches_golden(self, args, expected):
        assert make_coord(*args) == expected

    def test_agent_reexports_shared_make_coord(self):
        assert make_coord is shared_make_coord

    def test_coord_from_key_material_matches_make_coord(self):
        material = coord_key_material("t1", "episodic", "2026-10-03T00:00:00Z", "hi")
        assert coord_from_key_material(material) == make_coord(
            "t1", "episodic", "2026-10-03T00:00:00Z", "hi"
        )


class TestCrossRepoParity:
    """Agent contract and shared module must be one authority."""

    @pytest.mark.parametrize(
        "tenant,kind,ts,text", SEEDS_32, ids=[t for t, *_ in SEEDS_32]
    )
    def test_make_coord_matches_shared_module(self, tenant, kind, ts, text):
        assert make_coord(tenant, kind, ts, text) == shared_make_coord(
            tenant, kind, ts, text
        )


class TestOneDefinition:
    """T-2 exit criterion: one definition of the coord hash across the triad."""

    def test_exactly_one_stable_coord_definition_in_triad(self):
        roots = [
            Path(__file__).resolve().parents[2],  # somaAgent01
            Path(__file__).resolve().parents[2].parent / "somabrain",
            Path(__file__).resolve().parents[2].parent / "somafractalmemory",
            Path(__file__).resolve().parents[2].parent / "soma-memory-contract",
        ]
        pattern = "def " + "_stable_coord"
        hits: list[str] = []
        for root in roots:
            if not root.is_dir():
                continue
            proc = subprocess.run(
                ["grep", "-rn", "--include=*.py", pattern, str(root)],
                capture_output=True,
                text=True,
                check=False,
            )
            for line in proc.stdout.splitlines():
                if ".venv" in line or "__pycache__" in line:
                    continue
                hits.append(line)
        assert len(hits) == 1, f"expected 1 definition, found {len(hits)}:\n" + "\n".join(
            hits
        )
