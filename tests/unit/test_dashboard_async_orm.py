"""AAAS API handlers must not touch the ORM from an async context.

Regression: three handlers in ``admin/aaas/api/`` were declared ``async def``
but their bodies called the synchronous ORM directly (``Tenant.objects.count()``
and friends). Django's ``async_unsafe`` guard raises
``SynchronousOnlyOperation`` the moment a queryset runs under a live event
loop, so every one of those routes 500'd on request. ``admin/aaas/api/billing.py``
also stacked ``@transaction.atomic`` on an ``async def``, which is meaningless
for the same reason.

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
    """Invoke ``fn`` the way django-ninja would, inside a live event loop."""
    result = fn(*args, **kwargs)
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

    def test_get_dashboard_is_not_async_unsafe(self):
        """The exact 500 ``GET /api/v2/aaas/dashboard`` raised."""
        from django.test import RequestFactory

        from admin.aaas.api.dashboard import get_dashboard

        request = RequestFactory().get("/api/v2/aaas/dashboard")
        _run_expecting_no_async_unsafe(get_dashboard, request)

    def test_add_payment_method_is_not_async_unsafe(self):
        """``@transaction.atomic`` + ``async def`` + sync ORM, all wrong."""
        from django.test import RequestFactory

        from admin.aaas.api.billing import add_payment_method

        request = RequestFactory().post("/api/v2/aaas/billing/tenant/x/payment-methods")
        payload = type("P", (), {"token": "tok_test", "set_default": False})()
        _run_expecting_no_async_unsafe(add_payment_method, request, "missing", payload)

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
        """The extracted ORM helper is a plain sync callable, not a coroutine."""
        from admin.aaas.api.users import _load_user_bundle

        assert not inspect.iscoroutinefunction(_load_user_bundle)
        # sync_to_async wraps it, so it is awaitable, but the underlying work is sync.
        assert hasattr(_load_user_bundle, "__wrapped__") or callable(_load_user_bundle)

    def test_handlers_using_async_orm_may_stay_async(self):
        """Counter-example: real async ORM API is the one valid way to stay async."""
        from admin.aaas.api.integrations import get_integration

        assert inspect.iscoroutinefunction(get_integration)
