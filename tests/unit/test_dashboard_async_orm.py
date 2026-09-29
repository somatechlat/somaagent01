"""AAAS API handlers must not touch the ORM from an async context.

Regression: handlers in ``admin/aaas/api/`` were declared ``async def`` but
their bodies called the synchronous ORM directly. Django's ``async_unsafe``
guard raises ``SynchronousOnlyOperation`` the moment a queryset runs under a
live event loop, so those routes 500'd on request.

django-ninja dispatches ``async def`` handlers on an event loop and plain
``def`` handlers on a thread. A handler that only does ORM work has no reason
to be async. A handler that genuinely awaits external I/O — like
``get_user_detail``, which awaits the Redis session manager — must stay
``async def`` and push its ORM half through ``sync_to_async``.

``admin/aaas/api/integrations.py`` is the other valid shape: it stays async
because it uses the real async ORM API (``afirst``/``asave``).

These tests assert on the failure *class*, not on a successful response, so
they run with or without a database. Django's ``async_unsafe`` guard fires
before any connection is opened, so the bug reproduces with no infrastructure
at all; the fix is proven by the guard no longer firing.

VIBE Rule 91: no mocks — real handlers, real models, real event loop.
"""

from __future__ import annotations

import asyncio
import inspect


async def _call_under_loop(fn, *args, **kwargs):
    """Invoke ``fn`` the way django-ninja does, inside a live event loop.

    ``async def`` endpoints run on the loop. Plain ``def`` endpoints are
    dispatched by the ASGI handler onto a worker thread (``sync_to_async``),
    which is exactly why a sync ORM body is safe in them. Calling a sync
    handler inline here would sit it on the loop and manufacture the
    ``SynchronousOnlyOperation`` this suite exists to detect — it would fire
    on every sync handler, correct or not.
    """
    if inspect.iscoroutinefunction(fn):
        result = fn(*args, **kwargs)
    else:
        result = await asyncio.to_thread(fn, *args, **kwargs)
    if inspect.isawaitable(result):
        result = await result
    return result


def _run_expecting_no_async_unsafe(fn, *args, **kwargs):
    """Run ``fn`` under an event loop; fail only on SynchronousOnlyOperation.

    Any other outcome — a clean return, or a legitimate error such as
    NotFound / DatabaseOperationForbidden when no database is attached —
    means the handler is not reading the ORM on the event loop.
    """
    try:
        return asyncio.run(_call_under_loop(fn, *args, **kwargs))
    except Exception as exc:  # noqa: BLE001 - the assertion is on the class
        name = type(exc).__name__
        assert name != "SynchronousOnlyOperation", (
            f"{getattr(fn, '__name__', fn)} touched the ORM from an async "
            f"context: {name}: {exc}"
        )
        return exc


class TestAaasApiAsyncSafety:
    """No ORM-backed route may run its queries on the event loop."""

    def test_get_user_detail_is_not_async_unsafe(self):
        """Async handler that also awaits Redis: its ORM half must be threaded."""
        from django.test import RequestFactory

        from admin.aaas.api.users import get_user_detail

        request = RequestFactory().get("/api/v2/aaas/users/missing/detail")
        _run_expecting_no_async_unsafe(get_user_detail, request, "missing")

    def test_get_user_detail_stays_async_for_redis(self):
        """It must remain a coroutine function — the session manager is awaited."""
        from admin.aaas.api.users import get_user_detail

        assert inspect.iscoroutinefunction(get_user_detail)

    def test_orm_half_of_user_detail_is_off_the_event_loop(self):
        """The ORM work runs on a worker thread, not on the event loop.

        ``@sync_to_async`` makes the *callable* awaitable — the wrapper is a
        coroutine function so the view can ``await`` it. The property under
        test is the one that matters for loop safety: the function it runs is
        ordinary sync ORM code, so Django never issues a blocking query on
        the loop. Asserting the wrapper is not a coroutine function asserted
        the opposite of that and could never pass.
        """
        from admin.aaas.api.users import _load_user_bundle

        # Awaitable from the async view.
        assert inspect.iscoroutinefunction(_load_user_bundle)

        # ...and the work it runs is sync, so it cannot block the loop.
        inner = getattr(_load_user_bundle, "__wrapped__", None) or getattr(
            _load_user_bundle, "func", None
        )
        assert inner is not None, "sync_to_async should expose the wrapped function"
        assert not inspect.iscoroutinefunction(inner)
        assert callable(inner)

    def test_handlers_using_async_orm_may_stay_async(self):
        """Counter-example: real async ORM API is the one valid way to stay async."""
        from admin.aaas.api.integrations import get_integration

        assert inspect.iscoroutinefunction(get_integration)
