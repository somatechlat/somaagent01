"""T-2 cross-repo shared coordinate contract.

ONE definition of the coordinate hash for the whole Soma triad
(somabrain / somaAgent01 / somafractalmemory). Pure stdlib.

Kept in-tree at ``services/common/soma-memory-contract/`` so the package is
always importable inside somaAgent01 (Operator law: no out-of-project packages).
Math is byte-identical to somabrain's in-tree ``soma_memory_contract``.
"""

from __future__ import annotations

import hashlib

__all__ = [
    "COORD_UNIVERSE",
    "DEFAULT_MEM_EMBED_DIM",
    "_stable_coord",
    "make_coord",
    "coord_key_material",
    "coord_from_key_material",
    "coord_to_str",
]

# Namespace prefix for the coordinate seed. SOMA-ARCH-INVARIANTS-001 §1.3:
# seeded f"{COORD_UNIVERSE}::{tenant}|{kind}|{ts}|{text}". The implementation
# below uses the literal ``real::`` prefix — that IS this constant.
COORD_UNIVERSE = "real"

# Embedding dimension shared by agent seam and SFM SOMA_VECTOR_DIM (ADR-001).
# Declaration-site constant; keep lockstep with MEM_EMBED_DIM schema default.
DEFAULT_MEM_EMBED_DIM = 768


def _stable_coord(seed: str) -> tuple[float, float, float]:
    """Deterministic hash of *seed* into [-1, 1]^3.

    blake2b digest_size=12 -> four bytes per axis, normalised to [-1, 1].
    """
    digest = hashlib.blake2b(seed.encode("utf-8"), digest_size=12).digest()
    out: list[float] = []
    for i in range(3):
        raw = int.from_bytes(digest[i * 4 : (i + 1) * 4], "big")
        out.append((raw / 0x100000000) * 2.0 - 1.0)
    return (out[0], out[1], out[2])


def coord_key_material(tenant: str, kind: str, ts: str, text: str) -> str:
    """Canonical key material string for a memory identity."""
    return f"{tenant}|{kind}|{ts}|{text}"


def coord_from_key_material(material: str) -> str:
    """Return the ``x,y,z`` string for *material* (prefixed with ``real::``)."""
    x, y, z = _stable_coord(f"{COORD_UNIVERSE}::{material}")
    return f"{x},{y},{z}"


def make_coord(tenant: str, kind: str, ts: str, text: str) -> str:
    """Return the ``x,y,z`` string for a (tenant, kind, ts, text) identity."""
    material = coord_key_material(tenant, kind, ts, text)
    return coord_from_key_material(material)


def coord_to_str(coord: tuple[float, ...]) -> str:
    """String form of a coordinate tuple (6 decimal places)."""
    return ",".join(f"{c:.6f}" for c in coord)
