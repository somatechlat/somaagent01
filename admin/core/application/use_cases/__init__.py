"""Use cases - single business operations.

Each use case encapsulates one business operation and:
- Receives dependencies via constructor injection
- Returns typed DTOs
"""

from .conversation import ProcessMessageUseCase

__all__ = ["ProcessMessageUseCase"]
