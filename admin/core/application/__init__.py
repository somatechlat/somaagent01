"""Application layer - use cases.

Each use case encapsulates one business operation and receives its
dependencies via constructor injection.

Live use cases:
- ``use_cases.conversation`` - consumed by ``services.conversation_worker``.
"""

from . import use_cases

__all__ = ["use_cases"]
