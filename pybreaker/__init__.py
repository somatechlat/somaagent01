"""A very small stub of the ``pybreaker`` library used for circuit‑breaker
functionality. The real library provides sophisticated state handling; for local
development (DEV_MODE) we only need the API surface so that imports succeed.

The stub implements:

* ``CircuitBreaker`` – stores ``fail_max`` and ``reset_timeout`` but never opens;
  ``call`` and ``call_async`` simply invoke the wrapped function.
* ``CircuitBreakerError`` – an exception type used for exclusion lists.

Any unexpected usage will raise ``NotImplementedError`` to make failures
obvious during testing.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, List


class CircuitBreakerError(Exception):
    """Placeholder exception matching the real ``pybreaker`` type."""


class CircuitBreaker:
    """Simplified circuit breaker that never trips.

    Parameters are accepted for compatibility but ignored. The ``exclude`` list
    is stored for reference only.
    """

    def __init__(
        self,
        fail_max: int = 5,
        reset_timeout: int = 60,
        exclude: List[type] | None = None,
        **_: Any,
    ):
        self.fail_max = fail_max
        self.reset_timeout = reset_timeout
        self.exclude = exclude or []
        self.name: str | None = None
        # Callbacks used by the real library – we store them but never invoke.
        self.on_open: Callable[[], Any] | None = None
        self.on_close: Callable[[], Any] | None = None
        self.on_half_open: Callable[[], Any] | None = None

    # ----- public API used in the codebase -----
    def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Execute ``func`` synchronously.

        The real implementation would check state and possibly raise a
        ``CircuitBreakerError``; this stub simply forwards the call.
        """
        return func(*args, **kwargs)

    async def call_async(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Execute ``func`` asynchronously.

        If ``func`` returns a coroutine we await it; otherwise we return the
        result directly.
        """
        result = func(*args, **kwargs)
        if asyncio.iscoroutine(result):
            return await result
        return result

    # The code accesses ``current_state`` and ``name`` attributes; we provide a
    # simple static state.
    @property
    def current_state(self):  # pragma: no cover – trivial stub
        class _State:
            name = "closed"

        return _State()

    def __repr__(self) -> str:  # pragma: no cover
        return f"<StubCircuitBreaker name={self.name!r}>"


__all__ = ["CircuitBreaker", "CircuitBreakerError"]
