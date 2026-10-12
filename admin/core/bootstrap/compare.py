"""Compare-before-write helpers.

Idempotent bootstrap means: write when the row is missing or empty, skip when
the operator already owns the value. These helpers are the single place that
decides "is this a write or a skip", so every phase behaves the same way.

The rule is deliberately conservative: a non-empty existing value that differs
from the seed is **operator-owned** and is left alone. The phase reports the
skip; it never silently reverts an admin edit.
"""

from __future__ import annotations

from typing import Any, Tuple

__all__ = ["WriteOutcome", "decide_write", "fill_if_empty"]


class WriteOutcome:
    """Result of a compare-before-write decision."""

    __slots__ = ("action", "reason")

    def __init__(self, action: str, reason: str) -> None:
        self.action = action  # "create" | "update" | "skip"
        self.reason = reason

    @property
    def wrote(self) -> bool:
        return self.action in ("create", "update")

    def __repr__(self) -> str:  # pragma: no cover - diagnostic
        return f"WriteOutcome({self.action!r}, {self.reason!r})"


def decide_write(
    *,
    exists: bool,
    current: Any,
    desired: Any,
    fill_only: bool,
) -> WriteOutcome:
    """Decide whether a write is allowed.

    Args:
        exists: row already present.
        current: existing value (None / "" / {} / [] all count as empty).
        desired: seed value.
        fill_only: True for operator-owned rows (infra keys, capsule fields) —
            never overwrite a non-empty current value. False for catalog rows
            the seed fully owns (LLM models, slot bindings when unset).

    Returns:
        WriteOutcome. Never raises on "skip".
    """

    def _empty(v: Any) -> bool:
        return v is None or v == "" or v == {} or v == [] or v == ()

    if not exists:
        return WriteOutcome("create", "row absent")

    if _empty(current) and not _empty(desired):
        return WriteOutcome("update", "existing value empty; filling")

    if current == desired:
        return WriteOutcome("skip", "already at seed value")

    if fill_only and not _empty(current):
        return WriteOutcome("skip", "operator-owned value differs; left alone")

    return WriteOutcome("update", "seed owns this row")


def fill_if_empty(
    current: Any,
    desired: Any,
) -> Tuple[Any, WriteOutcome]:
    """Return (value_to_write, outcome) for a single field.

    Used when a row is created/updated field-by-field (Capsule JSON blobs).
    """
    decision = decide_write(
        exists=True,
        current=current,
        desired=desired,
        fill_only=True,
    )
    if decision.wrote:
        return desired, decision
    return current, decision
