"""TG-03 — `soma_agent_id` readers in webui must have a setItem writer.

ADV-2 (SOMA-RPT-STATUS-001): the cognitive panel read ``soma_agent_id`` from
storage while *nothing ever wrote it* — the panel was structurally dead,
always rendering "No agent selected". W1.8 added the writer in
``soma-chat.ts``. This gate fails if a reader exists while no ``setItem``
writer for the same key exists anywhere in webui again.

Pure source scan of webui TypeScript: no imports, no Django, no Vault.

Run (no Vault needed):

    python3 -m pytest -c /dev/null --noconftest -p no:cacheprovider \\
        tests/unit/test_webui_agent_id_storage.py -v

Run with the full stack up (Vault reachable), like the rest of the suite:

    pytest tests/unit/test_webui_agent_id_storage.py -v
"""

from __future__ import annotations

import re
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
WEBUI_SRC = REPO / "webui" / "src"

KEY = "soma_agent_id"

READER = re.compile(
    r"(?:sessionStorage|localStorage)\s*\.\s*getItem\(\s*['\"]" + KEY + r"['\"]"
)
WRITER = re.compile(
    r"(?:sessionStorage|localStorage)\s*\.\s*setItem\(\s*['\"]" + KEY + r"['\"]"
)


def _hits_in(root: Path, pattern: re.Pattern[str]) -> list[str]:
    """Paths under `root` whose text matches `pattern`."""
    if not root.exists():
        return []
    files = sorted(list(root.rglob("*.ts")) + list(root.rglob("*.js")))
    return [p.as_posix() for p in files if pattern.search(p.read_text(encoding="utf-8"))]


def test_webui_sources_exist():
    assert WEBUI_SRC.exists(), f"{WEBUI_SRC} missing — gate scope moved?"
    sources = sorted(list(WEBUI_SRC.rglob("*.ts")) + list(WEBUI_SRC.rglob("*.js")))
    assert sources, f"no TypeScript sources under {WEBUI_SRC} — gate scope moved?"


def _require_writer_for_readers(readers: list[str], writers: list[str]) -> None:
    """The gate rule, in one place: readers without writers is dead UI."""
    if not readers:
        # No readers → nothing can be dead. (If the panel disappears the
        # reader vanishes with it; the gate is about readers-without-writers.)
        return
    if not writers:
        raise AssertionError(
            "webui reads 'soma_agent_id' from storage but nothing ever writes it — "
            "the cognitive panel is structurally dead, always 'No agent selected' "
            f"(readers: {readers}). A setItem('{KEY}', ...) writer is required "
            "(ADV-2 / W1.8 regression)."
        )


def test_agent_id_readers_have_a_writer():
    _require_writer_for_readers(
        _hits_in(WEBUI_SRC, READER),
        _hits_in(WEBUI_SRC, WRITER),
    )


def test_gate_fails_when_writers_are_absent():
    """Meta: run the production gate rule against a synthetic reader-only tree.

    Proves the gate flips red when the writer disappears — a gate that has
    never been seen to fail is not evidence of anything. The synthetic tree
    is a temp directory, not a mutation of webui/.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "reader.ts").write_text(
            f"const id = sessionStorage.getItem('{KEY}');\n", encoding="utf-8"
        )
        readers = _hits_in(root, READER)
        writers = _hits_in(root, WRITER)
        assert readers, "reader probe not detected by the production scan"
        assert not writers, "writer probe unexpectedly detected"
        with pytest.raises(AssertionError, match="structurally dead"):
            _require_writer_for_readers(readers, writers)
