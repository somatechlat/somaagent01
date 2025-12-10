"""Celery Canvas pattern helpers.

The VIBE compliance report requires support for complex workflow patterns using
Celery's ``chain``, ``group`` and ``chord`` primitives.  This module provides thin
wrappers that create the appropriate ``Signature`` objects for a list of task
callables defined in ``python.tasks``.  The helpers avoid any hidden side‑effects
and rely solely on the Celery app instance imported from ``python.tasks.celery_app``.

Usage examples (from within a Celery task or regular code)::

    from services.common.canvas_helpers import chain_tasks, group_tasks, chord_tasks
    from python.tasks.core_tasks import delegate, build_context

    # Chain two tasks – the output of the first is passed as the first argument
    # to the second.
    result = chain_tasks([
        delegate.s(payload={"action": "foo"}, tenant_id="t1", request_id="r1"),
        build_context.s(tenant_id="t1", session_id="s1"),
    ]).apply_async()

    # Group runs tasks in parallel and aggregates results.
    result = group_tasks([
        delegate.s(payload={"action": "a"}, tenant_id="t2", request_id="r2"),
        delegate.s(payload={"action": "b"}, tenant_id="t2", request_id="r3"),
    ]).apply_async()

    # Chord combines a header group with a callback.
    result = chord_tasks(
        header=[delegate.s(payload={"action": "c"}, tenant_id="t3", request_id="r4")],
        body=build_context.s(tenant_id="t3", session_id="s2"),
    ).apply_async()

These helpers construct signatures and return ``Signature`` objects so callers
can decide when to ``apply_async`` or ``delay``.
"""

from __future__ import annotations

from typing import Iterable, List

from celery import chain, chord, group
from celery.canvas import Signature

__all__: List[str] = ["chain_tasks", "group_tasks", "chord_tasks"]


def _ensure_signatures(tasks: Iterable[Signature]) -> List[Signature]:
    """Validate that each element is a Celery ``Signature``.

    The VIBE rules forbid implicit conversions or magic; callers must provide
    ``.s()`` signatures.  If a plain callable is supplied, we raise a clear
    ``TypeError`` rather than silently wrapping it.
    """
    signatures: List[Signature] = []
    for t in tasks:
        if not isinstance(t, Signature):
            raise TypeError(
                "Canvas helpers expect Celery Signature objects. "
                f"Got {type(t)!r} – use task_name.s(...) to create a signature."
            )
        signatures.append(t)
    return signatures


def chain_tasks(tasks: Iterable[Signature]) -> Signature:
    """Create a Celery ``chain`` from a sequence of task signatures.

    Parameters
    ----------
    tasks:
        An iterable of Celery ``Signature`` objects representing the tasks to
        execute sequentially.

    Returns
    -------
    Signature
        The chain signature which can be executed with ``apply_async`` or
        ``delay``.
    """
    signatures = _ensure_signatures(tasks)
    return chain(*signatures)


def group_tasks(tasks: Iterable[Signature]) -> Signature:
    """Create a Celery ``group`` from a sequence of task signatures.

    The returned signature executes all tasks in parallel and aggregates the
    results into a list.
    """
    signatures = _ensure_signatures(tasks)
    return group(*signatures)


def chord_tasks(header: Iterable[Signature], body: Signature) -> Signature:
    """Create a Celery ``chord`` with a header group and a callback body.

    Parameters
    ----------
    header:
        An iterable of signatures that will run in parallel.
    body:
        A single signature that receives the list of results from the header.
    """
    header_sigs = _ensure_signatures(header)
    if not isinstance(body, Signature):
        raise TypeError("Chord body must be a Celery Signature. Use task_name.s(...) to create it.")
    return chord(header_sigs, body)
